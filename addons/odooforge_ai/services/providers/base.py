from dataclasses import dataclass, field
from typing import Any


class ProviderError(Exception):
    pass


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class ChatResponse:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    raw: Any = None


class BaseProvider:
    name = "base"

    def __init__(self, api_key=None, model=None, base_url=None, timeout=60):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def chat(self, system_prompt, messages, tools=None) -> ChatResponse:
        raise NotImplementedError
