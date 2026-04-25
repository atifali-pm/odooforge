import logging

import requests

from .base import BaseProvider, ChatResponse, ProviderError, ToolCall

_logger = logging.getLogger(__name__)

ENDPOINT = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-5"
ANTHROPIC_VERSION = "2023-06-01"


class ClaudeProvider(BaseProvider):
    name = "claude"

    def chat(self, system_prompt, messages, tools=None):
        if not self.api_key:
            raise ProviderError(
                "Anthropic API key is not configured. "
                "Set it in Settings > General Settings > AI Support Agent."
            )

        anthropic_messages = [_to_anthropic_message(m) for m in messages]

        payload = {
            "model": self.model or DEFAULT_MODEL,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": anthropic_messages,
        }
        if tools:
            payload["tools"] = [_to_anthropic_tool(t) for t in tools]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        try:
            resp = requests.post(ENDPOINT, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ProviderError(f"Claude request failed: {exc}") from exc

        if resp.status_code != 200:
            snippet = (resp.text or "")[:300]
            raise ProviderError(f"Claude returned HTTP {resp.status_code}: {snippet}")

        try:
            data = resp.json()
            content_blocks = data.get("content") or []
            usage = data.get("usage") or {}
        except (KeyError, ValueError) as exc:
            raise ProviderError(f"Unexpected Claude response shape: {exc}") from exc

        text_parts = []
        tool_calls = []
        for block in content_blocks:
            btype = block.get("type")
            if btype == "text":
                text_parts.append(block.get("text", ""))
            elif btype == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.get("id") or "",
                    name=block.get("name") or "",
                    arguments=block.get("input") or {},
                ))

        return ChatResponse(
            text="\n".join(t for t in text_parts if t).strip() or None,
            tool_calls=tool_calls,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            raw=data,
        )


def _to_anthropic_message(msg):
    role = msg["role"]
    if role == "tool":
        return {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": msg["tool_call_id"],
                "content": msg["content"],
            }],
        }
    if role == "assistant" and msg.get("tool_calls"):
        content = []
        if msg.get("content"):
            content.append({"type": "text", "text": msg["content"]})
        for tc in msg["tool_calls"]:
            content.append({
                "type": "tool_use",
                "id": tc["id"],
                "name": tc["name"],
                "input": tc["arguments"],
            })
        return {"role": "assistant", "content": content}
    return {"role": role, "content": msg["content"]}


def _to_anthropic_tool(tool):
    return {
        "name": tool["name"],
        "description": tool["description"],
        "input_schema": tool["parameters"],
    }
