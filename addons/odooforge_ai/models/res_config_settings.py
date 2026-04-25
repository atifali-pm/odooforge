from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    odooforge_ai_provider = fields.Selection([
        ("groq", "Groq (free Llama tier)"),
        ("claude", "Anthropic Claude"),
        ("ollama", "Ollama (self-hosted)"),
    ], string="Active LLM Provider",
        default="groq",
        config_parameter="odooforge_ai.provider",
    )
    odooforge_ai_groq_api_key = fields.Char(
        string="Groq API Key",
        config_parameter="odooforge_ai.groq_api_key",
    )
    odooforge_ai_groq_model = fields.Char(
        string="Groq Model",
        default="llama-3.3-70b-versatile",
        config_parameter="odooforge_ai.groq_model",
    )
    odooforge_ai_claude_api_key = fields.Char(
        string="Anthropic API Key",
        config_parameter="odooforge_ai.claude_api_key",
    )
    odooforge_ai_claude_model = fields.Char(
        string="Claude Model",
        default="claude-sonnet-4-5",
        config_parameter="odooforge_ai.claude_model",
    )
    odooforge_ai_ollama_base_url = fields.Char(
        string="Ollama Base URL",
        default="http://host.docker.internal:11434",
        config_parameter="odooforge_ai.ollama_base_url",
    )
    odooforge_ai_ollama_model = fields.Char(
        string="Ollama Model",
        default="llama3.1:8b",
        config_parameter="odooforge_ai.ollama_model",
    )
    odooforge_ai_embedding_model = fields.Char(
        string="Embedding Model",
        default="BAAI/bge-small-en-v1.5",
        config_parameter="odooforge_ai.embedding_model",
        help="fastembed-supported model name. Default produces 384-dim vectors.",
    )
