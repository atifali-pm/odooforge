from odoo import fields, models


class AuditLog(models.Model):
    _name = "odooforge_ai.audit_log"
    _description = "AI Agent Audit Log"
    _order = "create_date desc"

    ticket_id = fields.Many2one("helpdesk.ticket", string="Ticket", ondelete="set null")
    provider = fields.Char(string="Provider", required=True)
    model = fields.Char(string="Model")
    user_prompt = fields.Text(string="User Prompt")
    final_reply = fields.Text(string="Final Reply")
    tool_calls_json = fields.Text(string="Tool Calls (JSON)")
    iterations = fields.Integer(string="Iterations")
    input_tokens = fields.Integer(string="Input Tokens")
    output_tokens = fields.Integer(string="Output Tokens")
    latency_ms = fields.Integer(string="Latency (ms)")
    outcome = fields.Selection([
        ("success", "Success"),
        ("error", "Error"),
        ("no_reply", "No Reply"),
    ], string="Outcome", required=True, default="success")
    error_message = fields.Text(string="Error")
