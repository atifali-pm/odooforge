from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    odooforge_ai_groq_api_key = fields.Char(
        string="Groq API Key",
        config_parameter="odooforge_ai.groq_api_key",
    )
    odooforge_ai_groq_model = fields.Char(
        string="Groq Model",
        default="llama-3.3-70b-versatile",
        config_parameter="odooforge_ai.groq_model",
    )
