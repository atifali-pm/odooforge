import logging

_logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384


def migrate(cr, version):
    cr.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cr.execute(
        "ALTER TABLE kb_article "
        "ADD COLUMN IF NOT EXISTS embedding vector(%s)" % EMBEDDING_DIM
    )
    _logger.info(
        "Migrated odooforge_ai to %s: pgvector enabled, kb_article.embedding ensured",
        version,
    )
