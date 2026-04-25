import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384


def post_init_hook(env_or_cr, registry=None):
    if hasattr(env_or_cr, "execute"):
        cr = env_or_cr
    else:
        cr = env_or_cr.cr
    cr.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cr.execute(
        "ALTER TABLE kb_article "
        "ADD COLUMN IF NOT EXISTS embedding vector(%s)" % EMBEDDING_DIM
    )
    _logger.info("pgvector extension ensured; kb_article.embedding column ready (dim=%d)", EMBEDDING_DIM)
