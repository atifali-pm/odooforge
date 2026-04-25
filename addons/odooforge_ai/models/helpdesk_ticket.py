import json
import logging
from html import escape

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..services import agent, providers

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ai_draft_reply = fields.Html(string="AI Draft Reply", copy=False)
    ai_audit_ids = fields.One2many(
        "odooforge_ai.audit_log", "ticket_id", string="AI Audit Log"
    )

    def action_ai_draft_reply(self):
        self.ensure_one()
        icp = self.env["ir.config_parameter"].sudo()
        provider_name = icp.get_param("odooforge_ai.provider", "groq")
        provider_kwargs = _provider_kwargs(icp, provider_name)

        Audit = self.env["odooforge_ai.audit_log"].sudo()

        try:
            result = agent.run(self.env, self, provider_name, provider_kwargs)
        except providers.ProviderError as exc:
            Audit.create({
                "ticket_id": self.id,
                "provider": provider_name,
                "model": provider_kwargs.get("model") or "",
                "user_prompt": self.description or "",
                "outcome": "error",
                "error_message": str(exc),
            })
            raise UserError(str(exc)) from exc

        outcome = "success" if result.get("reply") else (
            "no_reply" if not result.get("error") else "error"
        )
        Audit.create({
            "ticket_id": self.id,
            "provider": provider_name,
            "model": provider_kwargs.get("model") or "",
            "user_prompt": self.description or "",
            "final_reply": result.get("reply") or "",
            "tool_calls_json": json.dumps(result.get("tool_calls") or [], default=str, indent=2),
            "iterations": result.get("iterations") or 0,
            "input_tokens": result.get("input_tokens") or 0,
            "output_tokens": result.get("output_tokens") or 0,
            "latency_ms": result.get("latency_ms") or 0,
            "outcome": outcome,
            "error_message": result.get("error") or "",
        })

        if not result.get("reply"):
            raise UserError(_(
                "AI agent did not produce a reply. %s"
            ) % (result.get("error") or ""))

        self.ai_draft_reply = _wrap_paragraphs(result["reply"])

        n_tools = len(result.get("tool_calls") or [])
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("AI Draft Reply"),
                "message": _(
                    "Draft generated using %(prov)s in %(iter)s iteration(s) "
                    "and %(n)s tool call(s). Review the AI Draft Reply tab."
                ) % {"prov": provider_name, "iter": result.get("iterations") or 1, "n": n_tools},
                "type": "success",
                "sticky": False,
            },
        }


def _provider_kwargs(icp, provider_name):
    if provider_name == "groq":
        return {
            "api_key": icp.get_param("odooforge_ai.groq_api_key", ""),
            "model": icp.get_param("odooforge_ai.groq_model", ""),
        }
    if provider_name == "claude":
        return {
            "api_key": icp.get_param("odooforge_ai.claude_api_key", ""),
            "model": icp.get_param("odooforge_ai.claude_model", ""),
        }
    if provider_name == "ollama":
        return {
            "base_url": icp.get_param("odooforge_ai.ollama_base_url", ""),
            "model": icp.get_param("odooforge_ai.ollama_model", ""),
        }
    return {}


def _wrap_paragraphs(text):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{escape(p)}</p>" for p in paragraphs)
