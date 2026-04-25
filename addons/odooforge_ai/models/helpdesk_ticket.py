from html import escape

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

from ..services import groq_provider

SYSTEM_PROMPT = (
    "You are a helpful customer support agent. Draft a polite, concise "
    "reply to the customer ticket below. Address the customer's concern "
    "directly. Do not invent product details or commitments. If you don't "
    "have enough information, ask one clarifying question. Keep the reply "
    "under 150 words. Sign as 'Support Team'."
)


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ai_draft_reply = fields.Html(string="AI Draft Reply", copy=False)

    def action_ai_draft_reply(self):
        self.ensure_one()
        icp = self.env["ir.config_parameter"].sudo()
        api_key = icp.get_param("odooforge_ai.groq_api_key", "")
        model = icp.get_param("odooforge_ai.groq_model", "")

        ticket_text = (
            f"Subject: {self.name or '(no subject)'}\n\n"
            f"Body:\n{html2plaintext(self.description or '') or '(no body)'}"
        )

        try:
            reply = groq_provider.draft_reply(
                api_key=api_key,
                model=model,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=ticket_text,
            )
        except groq_provider.GroqError as exc:
            raise UserError(str(exc)) from exc

        paragraphs = [p.strip() for p in reply.split("\n\n") if p.strip()]
        self.ai_draft_reply = "".join(f"<p>{escape(p)}</p>" for p in paragraphs)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("AI Draft Reply"),
                "message": _("Draft generated. Review it before sending."),
                "type": "success",
                "sticky": False,
            },
        }
