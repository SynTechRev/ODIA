"""Playwright-driven Questys Agenda calendar harvester.

Tactic:
  1. Open the BOS Agenda page in headless Chromium.
  2. The agenda calendar is an ASP.NET UpdatePanel — clicking a day issues
     an async postback that re-renders the iframe (`ifrmFiles`) with files
     for that meeting day. Playwright can wait for the iframe to update.
  3. Iterate month-by-month backward from the current month to the
     archive horizon (1974). For each month, find clickable date cells
     and click each one in turn.
  4. For each meeting day with files, harvest File.ashx?id=N URLs from
     the iframe's DOM.
  5. Aggregate unique IDs into a manifest, dedupe against the existing
     harvested set, and append to _questys_harvested_ids.json.

Runtime estimate: ~50 years * ~50 meetings/year * ~3s/click = ~2 hours
for the full archive. Throttled to be polite (1-2s between clicks).
"""

import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
SEARCH = BASE + "Search/Default.aspx"
AGENDA = BASE + "Agenda/Default.aspx"
MANIFEST = "_questys_harvested_ids.json"
NEW_MANIFEST = "_questys_calendar_harvest.json"

PAUSE_SEC = 1.5  # be polite between clicks


def load_existing_ids() -> set[str]:
    if Path(MANIFEST).exists():
        d = json.loads(Path(MANIFEST).read_text(encoding="utf-8-sig"))
        return set(d.get("ids", {}).keys())
    return set()


def harvest():
    existing = load_existing_ids()
    print(f"existing harvested IDs: {len(existing)}")

    harvested = {}  # id_str -> {filename, ext, meeting_date}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131 Safari/537.36"
            )
        )
        page = ctx.new_page()

        # Step 1: warm session via Search/Default.aspx
        print(f"  warmup -> {SEARCH}")
        page.goto(SEARCH, wait_until="domcontentloaded", timeout=120_000)
        print(f"    title: {page.title()}")

        # Step 2: load Agenda page
        print(f"  agenda -> {AGENDA}")
        page.goto(AGENDA, wait_until="domcontentloaded", timeout=120_000)
        print(f"    title: {page.title()}")

        # Confirm calendar present
        cal_present = page.locator("#ctl00_DefaultContent_agendaCalendar").count()
        if not cal_present:
            print("  ERR: agenda calendar not visible after load")
            browser.close()
            return harvested
        print("  calendar visible")

        # Helper to extract current displayed month label
        def current_month_label():
            try:
                hdr = page.locator(
                    "#ctl00_DefaultContent_agendaCalendar td.rcMainHeader, "
                    "#ctl00_DefaultContent_agendaCalendar td[class*='Header']"
                ).first
                return (
                    hdr.text_content()
                    if hdr.count()
                    else page.locator(
                        "#ctl00_DefaultContent_agendaCalendar tr"
                    ).first.text_content()
                )
            except Exception:
                return "?"

        # Helper to extract File.ashx IDs from iframe content
        def harvest_iframe_for_day(meeting_label):
            ids = []
            try:
                iframe = page.frame(name="ifrmFiles")
                if iframe is None:
                    return ids
                # Wait briefly for iframe to settle after postback
                page.wait_for_timeout(800)
                html = iframe.content()
                # Find File.ashx?id=N references
                hits = re.findall(r"File\.ashx\?id=(\d+)", html)
                ids = sorted(set(hits))
                # Also pull filenames from anchor text
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(html, "html.parser")
                fnames = {}
                for a in soup.find_all("a", href=True):
                    m = re.search(r"File\.ashx\?id=(\d+)", a.get("href", ""))
                    if m:
                        fid = m.group(1)
                        txt = a.get_text(" ", strip=True)
                        if txt:
                            fnames[fid] = txt
                for fid in ids:
                    fn = fnames.get(fid, f"questys_{fid}")
                    ext = ""
                    if "." in fn:
                        ext = fn.rsplit(".", 1)[-1].lower()
                    if fid not in harvested:
                        harvested[fid] = {
                            "filename": fn,
                            "ext": ext,
                            "meeting_date": meeting_label,
                        }
            except Exception as exc:
                print(f"     iframe harvest err: {exc}")
            return ids

        # Step 3: walk months backward. Stop when prev nav becomes non-clickable
        # or we hit the year horizon.
        MAX_MONTHS_BACK = 3  # proof-of-concept first; expand if successful
        YEAR_HORIZON = 2024  # don't go before this

        for month_iter in range(MAX_MONTHS_BACK):
            label = current_month_label()
            print(f"\n  === month {month_iter+1}/{MAX_MONTHS_BACK}: {label!r} ===")

            # Find all date cells in this month — they're <a> tags with
            # __doPostBack(...,'<dayid>') hrefs (no V prefix = actual day,
            # V prefix = navigation arrow).
            date_cells = page.eval_on_selector_all(
                "#ctl00_DefaultContent_agendaCalendar a",
                """anchors => anchors.map(a => {
                    const href = a.getAttribute('href') || '';
                    const m = href.match(/__doPostBack\\(['\\"]([^'\\"]+)['\\"],\\s*['\\"]([^'\\"]*)['\\"]\\)/);
                    if (m) return {target: m[1], arg: m[2], text: a.textContent.trim()};
                    return null;
                }).filter(Boolean)""",
            )
            day_cells = [c for c in date_cells if not c["arg"].startswith("V")]
            print(f"     {len(day_cells)} clickable day cells in this month")

            # Invoke each day's postback directly via JS instead of click
            # (Bootstrap grid divs intercept pointer events; the underlying
            # action is just `__doPostBack(target, arg)`, so we call it
            # directly and avoid the click-interception problem).
            for cell in day_cells:
                day_label = cell["text"]
                try:
                    page.evaluate(
                        f"__doPostBack('ctl00$DefaultContent$agendaCalendar', '{cell['arg']}')"
                    )
                    # Wait for AJAX response cycle
                    page.wait_for_load_state("domcontentloaded", timeout=15_000)
                    page.wait_for_timeout(int(PAUSE_SEC * 1000))
                    ids = harvest_iframe_for_day(f"{label} day {day_label}")
                    if ids:
                        print(
                            f"       day {day_label:>2}: {len(ids)} files  ({ids[:3]})"
                        )
                except Exception as exc:
                    print(f"       day {day_label} postback ERR: {str(exc)[:120]}")
                    continue

            # Navigate to previous month via __doPostBack with V-prefix arg
            prev_arrow = next(
                (
                    c
                    for c in date_cells
                    if c["arg"].startswith("V") and c["text"] == "<"
                ),
                None,
            )
            if prev_arrow is None:
                print("     no prev-month arrow — stopping")
                break
            try:
                page.evaluate(
                    f"__doPostBack('ctl00$DefaultContent$agendaCalendar', '{prev_arrow['arg']}')"
                )
                page.wait_for_load_state("networkidle", timeout=15_000)
                page.wait_for_timeout(800)
            except Exception as exc:
                print(f"     prev-month postback ERR: {exc}")
                break

            # Persist running totals
            Path(NEW_MANIFEST).write_text(
                json.dumps(
                    {
                        "harvested_at_unix": int(time.time()),
                        "month_iterations": month_iter + 1,
                        "total_new_ids": len(harvested),
                        "ids": harvested,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

        browser.close()

    print("\n=== DONE ===")
    print(f"  new unique IDs harvested: {len(harvested)}")
    print(f"  already in main manifest: {len(set(harvested.keys()) & existing)}")
    print(f"  truly new (not in main):  {len(set(harvested.keys()) - existing)}")
    print(f"  written to {NEW_MANIFEST}")


if __name__ == "__main__":
    sys.exit(harvest() or 0)
