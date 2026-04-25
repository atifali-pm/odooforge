#!/usr/bin/env python3
"""Capture OdooForge UI screenshots into ./screenshots/.

Usage:
    python3 bin/capture-screenshots.py

Env overrides:
    ODOOFORGE_URL     (default: http://localhost:8069)
    ODOOFORGE_LOGIN   (default: admin)
    ODOOFORGE_PWD     (default: admin)

Requirements:
    pip install --user playwright && playwright install chromium
"""

import asyncio
import os
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("playwright is not installed. Install:")
    print("  pip install --user playwright && playwright install chromium")
    sys.exit(1)


BASE = os.environ.get("ODOOFORGE_URL", "http://localhost:8069")
LOGIN = os.environ.get("ODOOFORGE_LOGIN", "admin")
PWD = os.environ.get("ODOOFORGE_PWD", "admin")
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "screenshots"
VIEWPORT = {"width": 1440, "height": 900}


async def login(page):
    await page.goto(f"{BASE}/web/login", wait_until="domcontentloaded")
    await page.fill("input[name='login']", LOGIN)
    await page.fill("input[name='password']", PWD)
    await page.click("button[type='submit']")
    await page.wait_for_url(lambda url: "/web/login" not in url, timeout=20000)
    await page.wait_for_timeout(2000)


async def settle(page, ms=2000):
    # Odoo's longpoll keeps networkidle from ever firing; just wait fixed.
    await page.wait_for_timeout(ms)


async def filter_apps(page, search_text):
    await page.goto(f"{BASE}/odoo/apps", wait_until="domcontentloaded")
    await settle(page, 800)
    search_input = page.locator(".o_searchview_input").first
    await search_input.click()
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Delete")
    await page.keyboard.type(search_text)
    await page.keyboard.press("Enter")
    await settle(page, 1200)


async def goto_action(page, action_xmlid):
    """Navigate to an action by its xmlid via the legacy hash URL (stable across versions)."""
    await page.goto(f"{BASE}/web#action={action_xmlid}", wait_until="domcontentloaded")
    await settle(page, 1500)


async def shoot(page, filename):
    # Park the cursor in a corner so list-row hover tooltips don't leak in.
    await page.mouse.move(0, 0)
    await page.wait_for_timeout(300)
    out = SCREENSHOT_DIR / filename
    await page.screenshot(path=str(out))
    print(f"  -> {out.relative_to(SCREENSHOT_DIR.parent)}")


async def main():
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport=VIEWPORT)
        page = await ctx.new_page()

        print(f"[..] login {BASE}")
        await login(page)
        print("[ok] logged in")

        # 02: Apps menu filtered to Helpdesk Management
        print("[..] 02-helpdesk-installed")
        await filter_apps(page, "Helpdesk Management")
        await shoot(page, "02-helpdesk-installed.png")

        # 03: Apps menu filtered to OdooForge AI
        print("[..] 03-odooforge-ai-installed")
        await filter_apps(page, "OdooForge AI")
        await shoot(page, "03-odooforge-ai-installed.png")

        # 04: Helpdesk ticket #1 form view (with AI Draft Reply tab)
        print("[..] 04-draft-reply-button")
        await page.goto(f"{BASE}/web#id=1&model=helpdesk.ticket&view_type=form",
                        wait_until="domcontentloaded")
        await settle(page, 2000)
        # Click the AI Draft Reply notebook tab if present
        try:
            tab = page.get_by_role("tab", name="AI Draft Reply")
            if await tab.count():
                await tab.first.click()
                await page.wait_for_timeout(800)
        except Exception:
            pass
        await shoot(page, "04-draft-reply-button.png")

        # 05: Audit log form (open the most recent entry)
        print("[..] 05-agent-tool-call")
        await goto_action(page, "odooforge_ai.audit_log_action")
        try:
            await page.wait_for_selector(".o_list_view", timeout=8000)
            await page.wait_for_timeout(600)
            first = page.locator(".o_list_view tbody tr").first
            await first.click()
            await page.wait_for_selector(".o_form_view", timeout=8000)
            await settle(page, 1500)
            # Click the Tool Calls tab if present
            try:
                tab = page.get_by_role("tab", name="Tool Calls")
                if await tab.count():
                    await tab.first.click()
                    await page.wait_for_timeout(800)
            except Exception:
                pass
        except PlaywrightTimeout:
            print("     warn: audit log list/form did not render in time")
        await shoot(page, "05-agent-tool-call.png")

        # 06: Audit log list view
        print("[..] 06-audit-log")
        await goto_action(page, "odooforge_ai.audit_log_action")
        await shoot(page, "06-audit-log.png")

        # 07: Helpdesk tickets dashboard (team kanban)
        print("[..] 07-helpdesk-dashboard")
        await goto_action(page, "helpdesk_mgmt.helpdesk_ticket_dashboard_action")
        await settle(page, 2500)
        await shoot(page, "07-helpdesk-dashboard.png")

        # 08: Full helpdesk ticket list (populated)
        print("[..] 08-helpdesk-tickets-list")
        await goto_action(page, "helpdesk_mgmt.helpdesk_ticket_action")
        await settle(page, 2000)
        await shoot(page, "08-helpdesk-tickets-list.png")

        # 09: Knowledge base list (the RAG corpus)
        print("[..] 09-knowledge-base")
        await goto_action(page, "odooforge_ai.kb_article_action")
        await settle(page, 1500)
        await shoot(page, "09-knowledge-base.png")

        await browser.close()
        print(f"\n[ok] all shots in {SCREENSHOT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
