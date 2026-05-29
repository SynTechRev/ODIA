"""Deeper diagnostic: look for the 'List of Meetings' panel + check if the
postback is even reaching the server (via network monitoring)."""
import re
from playwright.sync_api import sync_playwright

BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
SEARCH = BASE + "Search/Default.aspx"
AGENDA = BASE + "Agenda/Default.aspx"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0")
    page = ctx.new_page()

    # Capture all network requests
    network = []
    page.on("request", lambda req: network.append(("REQ", req.method, req.url[:120])))
    page.on("response", lambda r: network.append(("RES", r.status, r.url[:120])))

    print("warmup search...")
    page.goto(SEARCH, wait_until="domcontentloaded", timeout=120_000)
    print("agenda...")
    page.goto(AGENDA, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(3000)

    # Look at the main page DOM — specifically for "Meeting" lists and panels
    html = page.content()
    print(f"\n=== agenda page bytes={len(html)} ===")

    # Find anything mentioning 'meeting' in element IDs or text
    print("\n=== elements with 'Meeting' in id/class ===")
    for m in re.finditer(r'(?:id|class)="([^"]*[Mm]eeting[^"]*)"', html):
        print(f"  {m.group(1)}")

    # Find divs/panels that might be the meeting list
    print("\n=== meetingList / panelMeetings / etc ===")
    for m in re.finditer(r'id="([^"]*(?:Meeting|panelM|MeetingList|meetings)[^"]*)"', html, re.I):
        print(f"  {m.group(1)}")

    # Reset network capture, then trigger postback
    network.clear()
    print("\n=== POSTBACK for May 12 2026 (Tuesday, day 9628) ===")
    page.evaluate("__doPostBack('ctl00$DefaultContent$agendaCalendar', '9628')")
    page.wait_for_timeout(8000)

    print("\n=== network during postback ===")
    for kind, code_or_method, url in network[:40]:
        print(f"  {kind} {code_or_method} {url}")

    # Inspect main page DOM after postback
    html2 = page.content()
    print(f"\n=== agenda page bytes after postback: {len(html2)} (was {len(html)}) ===")

    # Look for any newly-appeared 'meeting' content
    print("\n=== post-postback: text matching 'meeting' ===")
    for m in re.finditer(r"[Mm]eeting[A-Za-z _]{0,40}", html2)[:10]:
        print(f"  {m.group()[:80]}")

    # Click handler search: how does the calendar normally trigger files?
    # Let me look for any JS that handles File loading
    print("\n=== JS that mentions iframe / ifrmFiles ===")
    for m in re.finditer(r"ifrmFiles[^<]{0,120}", html):
        print(f"  {m.group()[:160]}")

    browser.close()
