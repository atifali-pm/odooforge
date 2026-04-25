#!/usr/bin/env python3
"""Seed OdooForge with demo teams, customers, tickets, and run the AI agent.

Usage:
    python3 bin/seed-demo.py

Env overrides:
    ODOOFORGE_URL     (default: http://localhost:8069)
    ODOOFORGE_LOGIN   (default: admin)
    ODOOFORGE_PWD     (default: admin)
    ODOOFORGE_DB      (default: odooforge)

Idempotent: re-running skips records that already exist by name / email.
"""

import os
import sys
import time
import xmlrpc.client


URL = os.environ.get("ODOOFORGE_URL", "http://localhost:8069")
LOGIN = os.environ.get("ODOOFORGE_LOGIN", "admin")
PWD = os.environ.get("ODOOFORGE_PWD", "admin")
DB = os.environ.get("ODOOFORGE_DB", "odooforge")

TEAM_NAMES = ["Tier 1 Support", "Engineering", "Customer Success"]

CUSTOMERS = [
    ("Sam Reilly", "sam@example.com", "+1-555-0101"),
    ("Maria Chen", "maria@example.com", "+1-555-0102"),
    ("Alex Thompson", "alex@example.com", "+1-555-0103"),
    ("Jordan Lee", "jordan@example.com", "+1-555-0104"),
    ("Priya Patel", "priya@example.com", "+1-555-0105"),
]

TICKETS = [
    ("Can I return an item I bought 3 weeks ago?", "Tier 1 Support",
     "<p>Hi, I bought a backpack on April 4th and the strap broke after a week of normal use. "
     "Can I return it for a refund? Also do I have to pay for return shipping? Thanks, Sam.</p>",
     "sam@example.com", "New", "1"),
    ("Order #4291 hasn't shipped yet", "Engineering",
     "<p>Hi, I placed order #4291 nine days ago and the tracking still says 'label created'. "
     "The site said 3-5 business days. Can you check what's going on? Thanks, Maria</p>",
     "maria@example.com", "New", "2"),
    ("App crashes when uploading large CSV files", "Engineering",
     "<p>Whenever I try to upload a CSV larger than ~50MB the app freezes and I have to refresh. "
     "This started happening around two weeks ago. I'm on the latest version of Chrome on macOS. "
     "Can you reproduce?</p>",
     "alex@example.com", "In Progress", "2"),
    ("How do I export my reports to PDF?", "Tier 1 Support",
     "<p>Quick question: I want to email a quarterly report to my team but I only see the option "
     "to view it. Is there an export button I'm missing?</p>",
     "jordan@example.com", "New", "1"),
    ("Refund still not showing up after 10 days", "Tier 1 Support",
     "<p>I returned a defective monitor on April 15 and got the email confirming you received it "
     "on April 17. It's been 10 days and I haven't seen the refund hit my card. Order was #5012. "
     "Can you check?</p>",
     "priya@example.com", "Awaiting", "3"),
    ("Feature request: dark mode for the dashboard", "Customer Success",
     "<p>Would love to see a dark mode option for the dashboard. Eyes get tired late in the day. "
     "Many of your competitors already have this.</p>",
     "alex@example.com", "New", "0"),
    ("Onboarding call follow-up: SSO setup", "Customer Success",
     "<p>Following up on the onboarding call we had on Tuesday. You mentioned SSO with Okta is "
     "supported. Can you send the configuration steps?</p>",
     "jordan@example.com", "In Progress", "1"),
    ("Locked out of my account", "Tier 1 Support",
     "<p>I tried to log in this morning and after three wrong password attempts it says my account "
     "is locked. I can't reset because the email link doesn't arrive. Help?</p>",
     "priya@example.com", "New", "3"),
]

# Tickets to run the agent on after seeding (to populate the audit log).
RUN_AGENT_ON = ["Order #4291 hasn't shipped yet",
                "How do I export my reports to PDF?",
                "Refund still not showing up after 10 days",
                "Locked out of my account"]


def main():
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(DB, LOGIN, PWD, {})
    if not uid:
        print(f"[FAIL] could not authenticate as {LOGIN!r} on {DB!r}")
        sys.exit(1)
    M = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)

    def call(model, method, args, kw=None):
        return M.execute_kw(DB, uid, PWD, model, method, args, kw or {})

    teams = {}
    for name in TEAM_NAMES:
        existing = call("helpdesk.ticket.team", "search", [[("name", "=", name)]])
        teams[name] = existing[0] if existing else call(
            "helpdesk.ticket.team", "create", [{"name": name}])
    print(f"[ok] teams: {len(teams)}")

    customers = {}
    for name, email, phone in CUSTOMERS:
        existing = call("res.partner", "search", [[("email", "=", email)]])
        customers[email] = existing[0] if existing else call(
            "res.partner", "create",
            [{"name": name, "email": email, "phone": phone, "is_company": False}])
    print(f"[ok] customers: {len(customers)}")

    stages = call("helpdesk.ticket.stage", "search_read", [[]],
                  {"fields": ["name"], "order": "sequence"})
    stage_by_name = {s["name"]: s["id"] for s in stages}

    created_ids_by_name = {}
    for name, team_name, body, email, stage_name, priority in TICKETS:
        existing = call("helpdesk.ticket", "search", [[("name", "=", name)]])
        if existing:
            created_ids_by_name[name] = existing[0]
            continue
        tid = call("helpdesk.ticket", "create", [{
            "name": name,
            "description": body,
            "team_id": teams[team_name],
            "partner_id": customers[email],
            "partner_email": email,
            "stage_id": stage_by_name.get(stage_name, list(stage_by_name.values())[0]),
            "priority": priority,
        }])
        created_ids_by_name[name] = tid
    print(f"[ok] tickets: {len(created_ids_by_name)}")

    for ticket_name in RUN_AGENT_ON:
        tid = created_ids_by_name.get(ticket_name)
        if not tid:
            continue
        # Skip if this ticket already has an audit log entry
        existing_audit = call("odooforge_ai.audit_log", "search_count",
                              [[("ticket_id", "=", tid)]])
        if existing_audit:
            print(f"[skip] agent already ran on '{ticket_name}'")
            continue
        try:
            call("helpdesk.ticket", "action_ai_draft_reply", [[tid]])
            print(f"[ok] agent ran on '{ticket_name}'")
        except xmlrpc.client.Fault as exc:
            msg = exc.faultString.splitlines()[-1][:200]
            print(f"[skip] agent failed on '{ticket_name}': {msg}")
        time.sleep(0.5)

    audit_count = call("odooforge_ai.audit_log", "search_count", [[]])
    print(f"\n[done] audit log entries: {audit_count}")


if __name__ == "__main__":
    main()
