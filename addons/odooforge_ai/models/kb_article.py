import logging

from odoo import api, fields, models
from odoo.tools import html2plaintext

from ..services import embeddings

_logger = logging.getLogger(__name__)


class KbArticle(models.Model):
    _name = "kb.article"
    _description = "Knowledge Base Article"
    _order = "name"

    name = fields.Char(string="Title", required=True)
    body = fields.Html(string="Body", required=True, sanitize=True)
    tags = fields.Char(string="Tags", help="Comma-separated tags for filtering")
    active = fields.Boolean(default=True)
    last_embedded_at = fields.Datetime(string="Last Embedded", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._update_embedding()
        return records

    def write(self, vals):
        result = super().write(vals)
        if any(k in vals for k in ("name", "body")):
            for rec in self:
                rec._update_embedding()
        return result

    def _embedding_text(self):
        self.ensure_one()
        plain = html2plaintext(self.body or "")
        return f"{self.name}\n\n{plain}".strip()

    def _update_embedding(self):
        self.ensure_one()
        text = self._embedding_text()
        if not text:
            return
        try:
            vec = embeddings.embed(text)[0]
        except Exception as exc:
            _logger.warning("Embedding failed for kb.article %s: %s", self.id, exc)
            return
        literal = embeddings.to_pgvector_literal(vec)
        self.env.cr.execute(
            "UPDATE kb_article SET embedding = %s::vector WHERE id = %s",
            (literal, self.id),
        )
        self.last_embedded_at = fields.Datetime.now()

    def action_reembed(self):
        for rec in self:
            rec._update_embedding()
        return True

    def action_reembed_all(self):
        for rec in self.search([]):
            rec._update_embedding()
        return True
