import json
import logging

from . import embeddings

_logger = logging.getLogger(__name__)


def tool_specs():
    return [
        {
            "name": "lookup_customer",
            "description": (
                "Look up customer contact records by email or partial name. "
                "Use this to confirm the customer's identity, find their company, "
                "or get their contact details before answering."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Email address or partial name to search.",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "search_kb",
            "description": (
                "Semantic search over the internal knowledge base of help "
                "articles. Use this whenever the customer asks a how-to, "
                "policy, or troubleshooting question. Returns top matches "
                "with their content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural-language search query.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of articles to return (default 3).",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "check_order_status",
            "description": (
                "Look up a sales order by reference number (e.g. 'S00042' or '4291') "
                "and return its status, date, and shipping state."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_ref": {
                        "type": "string",
                        "description": "Order reference such as 'S00042' or '4291'.",
                    },
                },
                "required": ["order_ref"],
            },
        },
        {
            "name": "escalate_to_human",
            "description": (
                "Mark this ticket for human attention. Use this when the customer "
                "is upset, the issue is outside your scope, or the answer needs "
                "human judgement. Bumps priority and adds an internal note."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Short reason for escalation.",
                    },
                },
                "required": ["reason"],
            },
        },
    ]


def dispatch(env, ticket, name, arguments):
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return handler(env, ticket, **arguments)
    except TypeError as exc:
        return {"error": f"Bad arguments for {name}: {exc}"}
    except Exception as exc:
        _logger.exception("Tool %s failed", name)
        return {"error": f"{name} failed: {exc}"}


def _lookup_customer(env, ticket, query):
    Partner = env["res.partner"].sudo()
    domain = ["|", ("email", "ilike", query), ("name", "ilike", query)]
    partners = Partner.search(domain, limit=5)
    if not partners:
        return {"matches": [], "note": "No customer matched."}
    return {
        "matches": [
            {
                "id": p.id,
                "name": p.name,
                "email": p.email or "",
                "phone": p.phone or "",
                "company": p.parent_id.name if p.parent_id else None,
            }
            for p in partners
        ],
    }


def _search_kb(env, ticket, query, limit=3):
    limit = max(1, min(int(limit or 3), 10))
    try:
        vec = embeddings.embed(query)[0]
    except Exception as exc:
        return {"error": f"Embedding failed: {exc}"}

    vec_literal = embeddings.to_pgvector_literal(vec)
    env.cr.execute(
        """
        SELECT id, name, body, 1 - (embedding <=> %s::vector) AS score
        FROM kb_article
        WHERE embedding IS NOT NULL AND active = TRUE
        ORDER BY embedding <=> %s::vector ASC
        LIMIT %s
        """,
        (vec_literal, vec_literal, limit),
    )
    rows = env.cr.fetchall()
    if not rows:
        return {"matches": [], "note": "Knowledge base is empty or no embeddings yet."}

    from odoo.tools import html2plaintext
    return {
        "matches": [
            {
                "id": r[0],
                "title": r[1],
                "body": html2plaintext(r[2] or "")[:2000],
                "score": round(float(r[3]), 4),
            }
            for r in rows
        ],
    }


def _check_order_status(env, ticket, order_ref):
    if "sale.order" not in env:
        return {"error": "Sales module is not installed in this database."}
    Order = env["sale.order"].sudo()

    # Try exact name first, then loose match (handles '4291' -> 'S00004291')
    order = Order.search([("name", "=", order_ref)], limit=1)
    if not order:
        order = Order.search([("name", "ilike", order_ref)], limit=1)
    if not order:
        return {"found": False, "order_ref": order_ref}

    pickings = []
    if hasattr(order, "picking_ids"):
        for p in order.picking_ids:
            pickings.append({
                "name": p.name,
                "state": p.state,
                "scheduled_date": str(p.scheduled_date) if p.scheduled_date else None,
            })

    return {
        "found": True,
        "name": order.name,
        "state": order.state,
        "date_order": str(order.date_order) if order.date_order else None,
        "amount_total": order.amount_total,
        "customer": order.partner_id.name if order.partner_id else None,
        "pickings": pickings,
    }


def _escalate_to_human(env, ticket, reason):
    ticket.sudo().write({"priority": "3"})
    ticket.sudo().message_post(
        body=f"<p><b>AI agent escalated this ticket.</b><br/>Reason: {reason}</p>",
        message_type="comment",
    )
    return {"escalated": True, "ticket_id": ticket.id, "reason": reason}


_HANDLERS = {
    "lookup_customer": _lookup_customer,
    "search_kb": _search_kb,
    "check_order_status": _check_order_status,
    "escalate_to_human": _escalate_to_human,
}
