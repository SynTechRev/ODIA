"""Inspect listMeetings panel after date postback to find meeting click targets."""
import re
from playwright.sync_api import sync_playwright

BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
SEARCH = BASE + "Search/Default.aspx"
AGENDA = BASE + "Agenda/Default.aspx"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0")
    page = ctx.new_page()

    page.goto(SEARCH, wait_until="domcontentloaded", timeout=120_000)
    page.goto(AGENDA, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(3000)

    # Try a few candidate dates — Tuesdays in 2025/early 2026
    # Day-id calculation: May 1 2026 = 9617; day 0 = Jan 1 2000
    # May 12 2026 = 9628 (Tuesday)
    # Jan 14 2025 = 9145 (Tuesday)
    # Oct 1 2024 = 9040 (Tuesday)

    for day_id, label in [(9628, "May 12 2026"), (9145, "Jan 14 2025"), (9040, "Oct 1 2024")]:
        print(f"\n========== POSTBACK for {label} (day_id={day_id}) ==========")
        page.evaluate(f"__doPostBack('ctl00$DefaultContent$agendaCalendar', '{day_id}')")
        page.wait_for_timeout(6000)

        # Inspect the listMeetings panel
        panel_el = page.locator("#ctl00_DefaultContent_listMeetings")
        if panel_el.count() == 0:
            print(f"  no listMeetings panel found")
            continue
        panel_html = panel_el.inner_html()
        print(f"  listMeetings inner_html len: {len(panel_html)}")
        print(f"  visible text: {panel_el.inner_text()[:400]!r}")

        # Extract any postback targets/anchors inside the panel
        hrefs = re.findall(r"href=[\"']([^\"']+)[\"']", panel_html)
        clickable = [h for h in hrefs if "javascript" in h.lower() or "doPostBack" in h]
        print(f"  hrefs in panel: {len(hrefs)}; clickable: {len(clickable)}")
        for h in clickable[:5]:
            print(f"    {h[:160]}")

        # Extract __doPostBack targets
        post_pat = re.compile(r"__doPostBack\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]*)['\"]\)")
        posts = post_pat.findall(panel_html)
        print(f"  __doPostBack calls in panel: {len(posts)}")
        for tgt, arg in posts[:5]:
            print(f"    target={tgt!r}  arg={arg!r}")

    browser.close()
