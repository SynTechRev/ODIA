"""Iteratively post calendar __doPostBack; re-fetch fresh ViewState each time."""

import re
from datetime import date

from bs4 import BeautifulSoup
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
AGENDA = BASE + "Agenda/Default.aspx"

# Epoch: May 1 2026 = day_id 9617
# Means epoch day 0 = 2026-05-01 minus 9617 days = 2025-05-01 minus 365 = ... let's just compute
EPOCH_DATE = date(2026, 5, 1)
EPOCH_ID = 9617


def date_to_id(d: date) -> int:
    return EPOCH_ID + (d - EPOCH_DATE).days


def fresh_session_and_viewstate():
    sess = requests.Session(impersonate=UA)
    sess.get(BASE + "Search/Default.aspx", timeout=30)  # establish session
    r = sess.get(AGENDA, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    vs = soup.find("input", {"name": "__VIEWSTATE"}).get("value", "")
    vsg = soup.find("input", {"name": "__VIEWSTATEGENERATOR"}).get("value", "")
    return sess, vs, vsg


def click_calendar(sess, vs, vsg, day_id):
    post_data = {
        "__EVENTTARGET": "ctl00$DefaultContent$agendaCalendar",
        "__EVENTARGUMENT": str(day_id),
        "__VIEWSTATE": vs,
        "__VIEWSTATEGENERATOR": vsg,
        "__LASTFOCUS": "",
    }
    return sess.post(
        AGENDA,
        data=post_data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": AGENDA,
        },
        timeout=60,
    )


# Test 4 recent Tuesdays + last Tuesday of April
test_days = [
    date(2026, 5, 12),  # 9628
    date(2026, 5, 5),  # 9621
    date(2026, 4, 28),  # 9614
    date(2026, 4, 21),  # 9607
    date(2025, 12, 16),  # arbitrary mid-archive
]

for d in test_days:
    sess, vs, vsg = fresh_session_and_viewstate()  # fresh each time
    did = date_to_id(d)
    print(f"\n--- {d.isoformat()} (Tuesday, day_id={did}) ---")
    rp = click_calendar(sess, vs, vsg, did)
    print(f"   status={rp.status_code} bytes={len(rp.content)}")

    if len(rp.content) < 5000:
        # probably error page
        print("   tiny response — likely server error. First 400 chars:")
        print(f"   {rp.text[:400]}")
        continue

    # Parse + look for ANYTHING new vs. baseline
    soup = BeautifulSoup(rp.text, "html.parser")
    ifr = soup.find("iframe", id="ctl00_DefaultContent_Files_ifrmFiles")
    print(f"   iframe src: {ifr.get('src') if ifr else '(none)'}")
    print(
        f"   File.ashx IDs: {sorted(set(re.findall(r'File.ashx.id=(.d+)', rp.text)))[:10]}"
    )

    # Look for the file panel content
    fp = soup.find("div", id="ctl00_DefaultContent_Files_pnlFiles") or soup.find(
        id=re.compile(r"Files|Meeting|Record")
    )
    if fp:
        print(
            f"   files panel: id={fp.get('id')} class={fp.get('class')} text_len={len(fp.get_text(strip=True))}"
        )
        sample = fp.get_text(" ", strip=True)[:300]
        if sample:
            print(f"     content sample: {sample!r}")

    # Save first successful response
    if len(rp.content) > 5000:
        out_name = f"_questys_post_{d.isoformat()}.html"
        with open(out_name, "w", encoding="utf-8") as f:
            f.write(rp.text)
        print(f"   saved {out_name}")
