import logging
import threading

_logger = logging.getLogger(__name__)

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_DIM = 384

_model_cache = {}
_lock = threading.Lock()


def _get_model(name):
    with _lock:
        if name not in _model_cache:
            from fastembed import TextEmbedding
            _logger.info("Loading embedding model %s (first call may download weights)", name)
            _model_cache[name] = TextEmbedding(model_name=name)
        return _model_cache[name]


def embed(texts, model_name=None):
    if isinstance(texts, str):
        texts = [texts]
    name = model_name or DEFAULT_MODEL
    model = _get_model(name)
    return [list(map(float, vec)) for vec in model.embed(texts)]


def to_pgvector_literal(vec):
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
