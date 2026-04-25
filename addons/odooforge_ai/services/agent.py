import json
import logging
import time

from odoo.tools import html2plaintext

from . import providers, tools

_logger = logging.getLogger(__name__)

MAX_ITERATIONS = 6

SYSTEM_PROMPT = (
    "You are the support agent for the company's helpdesk. "
    "Your job is to draft a polite, accurate reply to the customer ticket. "
    "Use the available tools when they help: search the knowledge base for "
    "how-to and policy questions, look up the customer's record to "
    "personalise the response, check the order status when an order is "
    "referenced, and escalate to a human only when truly necessary. "
    "Do not invent product details, prices, or commitments. "
    "If you don't have enough information after using the tools, ask one "
    "clarifying question. Keep the final reply under 180 words. "
    "Sign as 'Support Team'."
)


def run(env, ticket, provider_name, provider_kwargs):
    provider = providers.get_provider(provider_name, **provider_kwargs)
    tool_specs = tools.tool_specs()

    user_message = (
        f"Ticket subject: {ticket.name or '(no subject)'}\n\n"
        f"Customer message:\n{html2plaintext(ticket.description or '') or '(no body)'}\n\n"
        f"Customer email on file: {ticket.partner_email or '(unknown)'}"
    )

    messages = [{"role": "user", "content": user_message}]
    tool_calls_log = []
    total_input = 0
    total_output = 0
    started = time.time()

    for iteration in range(MAX_ITERATIONS):
        response = provider.chat(SYSTEM_PROMPT, messages, tools=tool_specs)
        total_input += response.input_tokens
        total_output += response.output_tokens

        if not response.tool_calls:
            elapsed_ms = int((time.time() - started) * 1000)
            return {
                "reply": (response.text or "").strip(),
                "tool_calls": tool_calls_log,
                "input_tokens": total_input,
                "output_tokens": total_output,
                "latency_ms": elapsed_ms,
                "iterations": iteration + 1,
            }

        assistant_msg = {
            "role": "assistant",
            "content": response.text or "",
            "tool_calls": [
                {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                for tc in response.tool_calls
            ],
        }
        messages.append(_to_openai_assistant_with_tool_calls(assistant_msg))

        for tc in response.tool_calls:
            result = tools.dispatch(env, ticket, tc.name, tc.arguments)
            tool_calls_log.append({
                "name": tc.name,
                "arguments": tc.arguments,
                "result": result,
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": tc.name,
                "content": json.dumps(result, default=str),
            })

    elapsed_ms = int((time.time() - started) * 1000)
    return {
        "reply": "",
        "tool_calls": tool_calls_log,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "latency_ms": elapsed_ms,
        "iterations": MAX_ITERATIONS,
        "error": "Agent hit max iterations without producing a final reply.",
    }


def _to_openai_assistant_with_tool_calls(msg):
    return {
        "role": "assistant",
        "content": msg.get("content") or None,
        "tool_calls": [
            {
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": json.dumps(tc["arguments"]),
                },
            }
            for tc in msg["tool_calls"]
        ],
    }
