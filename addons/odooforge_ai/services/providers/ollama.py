import json
import logging

import requests

from .base import BaseProvider, ChatResponse, ProviderError, ToolCall

_logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama3.1:8b"
DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    name = "ollama"

    def chat(self, system_prompt, messages, tools=None):
        base = (self.base_url or DEFAULT_BASE_URL).rstrip("/")
        endpoint = f"{base}/api/chat"

        full_messages = [{"role": "system", "content": system_prompt}, *messages]
        payload = {
            "model": self.model or DEFAULT_MODEL,
            "messages": full_messages,
            "stream": False,
            "options": {"temperature": 0.3},
        }
        if tools:
            payload["tools"] = [_to_ollama_tool(t) for t in tools]

        try:
            resp = requests.post(endpoint, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ProviderError(
                f"Ollama request to {base} failed: {exc}. "
                f"Is the Ollama server running and reachable?"
            ) from exc

        if resp.status_code != 200:
            snippet = (resp.text or "")[:300]
            raise ProviderError(f"Ollama returned HTTP {resp.status_code}: {snippet}")

        try:
            data = resp.json()
            msg = data.get("message") or {}
        except ValueError as exc:
            raise ProviderError(f"Unexpected Ollama response: {exc}") from exc

        tool_calls = []
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function") or {}
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except ValueError:
                    args = {}
            tool_calls.append(ToolCall(
                id=tc.get("id") or fn.get("name", ""),
                name=fn.get("name", ""),
                arguments=args,
            ))

        return ChatResponse(
            text=msg.get("content") or None,
            tool_calls=tool_calls,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            raw=data,
        )


def _to_ollama_tool(tool):
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"],
        },
    }
