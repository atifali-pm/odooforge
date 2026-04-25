import json
import logging

import requests

from .base import BaseProvider, ChatResponse, ProviderError, ToolCall

_logger = logging.getLogger(__name__)

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqProvider(BaseProvider):
    name = "groq"

    def chat(self, system_prompt, messages, tools=None):
        if not self.api_key:
            raise ProviderError(
                "Groq API key is not configured. "
                "Set it in Settings > General Settings > AI Support Agent."
            )

        full_messages = [{"role": "system", "content": system_prompt}, *messages]
        payload = {
            "model": self.model or DEFAULT_MODEL,
            "messages": full_messages,
            "temperature": 0.3,
        }
        if tools:
            payload["tools"] = [_to_openai_tool(t) for t in tools]
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(ENDPOINT, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ProviderError(f"Groq request failed: {exc}") from exc

        if resp.status_code != 200:
            snippet = (resp.text or "")[:300]
            raise ProviderError(f"Groq returned HTTP {resp.status_code}: {snippet}")

        try:
            data = resp.json()
            choice = data["choices"][0]["message"]
            usage = data.get("usage") or {}
        except (KeyError, ValueError, IndexError) as exc:
            raise ProviderError(f"Unexpected Groq response shape: {exc}") from exc

        tool_calls = []
        for tc in choice.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except (ValueError, TypeError):
                args = {}
            tool_calls.append(ToolCall(
                id=tc.get("id") or "",
                name=tc["function"]["name"],
                arguments=args,
            ))

        return ChatResponse(
            text=choice.get("content"),
            tool_calls=tool_calls,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            raw=data,
        )


def _to_openai_tool(tool):
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"],
        },
    }
