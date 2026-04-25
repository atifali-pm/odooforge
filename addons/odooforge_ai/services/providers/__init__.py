from .base import BaseProvider, ChatResponse, ProviderError, ToolCall
from . import groq, claude, ollama


_REGISTRY = {
    "groq": groq.GroqProvider,
    "claude": claude.ClaudeProvider,
    "ollama": ollama.OllamaProvider,
}


def get_provider(name, **kwargs):
    name = (name or "groq").lower()
    if name not in _REGISTRY:
        raise ProviderError(f"Unknown LLM provider: {name!r}. Choose from: {sorted(_REGISTRY)}.")
    return _REGISTRY[name](**kwargs)
