import logging

import requests

_logger = logging.getLogger(__name__)

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TIMEOUT = 30


class GroqError(Exception):
    pass


def draft_reply(api_key, model, system_prompt, user_prompt, timeout=DEFAULT_TIMEOUT):
    if not api_key:
        raise GroqError(
            "Groq API key is not configured. "
            "Set it in Settings > General Settings > AI Support Agent."
        )

    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(GROQ_ENDPOINT, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise GroqError(f"Groq request failed: {exc}") from exc

    if resp.status_code != 200:
        snippet = (resp.text or "")[:300]
        raise GroqError(f"Groq returned HTTP {resp.status_code}: {snippet}")

    try:
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, ValueError, IndexError) as exc:
        raise GroqError(f"Unexpected Groq response shape: {exc}") from exc
