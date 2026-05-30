"""Diagnostic: pick a known Tuesday and inspect what actually lands in
the ifrmFiles iframe after the postback."""

import re

from playwright.sync_api import sync_playwright

BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
SEARCH = BASE + "Search/Default.aspx"
AGENDA = BASE + "Agenda/Default.aspx"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0")
    page = ctx.new_page()

    print("warmup search...")
    page.goto(SEARCH, wait_until="domcontentloaded", timeout=120_000)
    print("agenda...")
    page.goto(AGENDA, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(2000)

    # Snapshot all iframes / frame names
    print("\n=== frames after agenda load ===")
    for f in page.frames:
        print(f"  name={f.name!r}  url={f.url[:100]!r}")

    # Click May 12 2026 (Tuesday) — day_id 9628
    print("\n=== invoking postback for May 12 2026 (day 9628) ===")
    page.evaluate("__doPostBack('ctl00$DefaultContent$agendaCalendar', '9628')")
    page.wait_for_timeout(8000)  # generous wait for UpdatePanel + iframe re-set

    # Re-snapshot frames
    print("\n=== frames after postback ===")
    for f in page.frames:
        print(f"  name={f.name!r}  url={f.url[:120]!r}")

    # Look at the main page DOM for any new File.ashx hrefs
    main_html = page.content()
    print(f"\n=== main page bytes={len(main_html)} ===")
    file_ids = sorted(set(re.findall(r"File\.ashx\?id=(\d+)", main_html)))
    print(f"  File.ashx IDs in main page: {file_ids}")

    # Look INSIDE the iframe by name
    ifr = page.frame(name="ifrmFiles")
    if ifr is None:
        print("\n  no ifrmFiles frame named 'ifrmFiles'")
    else:
        print("\n=== ifrmFiles ===")
        print(f"  url: {ifr.url}")
        try:
            content = ifr.content()
            print(f"  bytes: {len(content)}")
            iframe_ids = sorted(set(re.findall(r"File\.ashx\?id=(\d+)", content)))
            print(f"  File.ashx IDs in iframe: {iframe_ids}")
            # Dump first 1500 chars
            print("  --- first 1500 chars ---")
            print(content[:1500])
        except Exception as exc:
            print(f"  content err: {exc}")

    # Also check the iframe by element selector
    print("\n=== iframe via selector lookup ===")
    iframe_el = page.locator("iframe#ctl00_DefaultContent_Files_ifrmFiles")
    print(f"  element count: {iframe_el.count()}")
    if iframe_el.count():
        src = iframe_el.first.get_attribute("src")
        print(f"  src attribute: {src!r}")

    browser.close()
