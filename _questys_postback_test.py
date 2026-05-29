"""Simulate calendar __doPostBack for a Tuesday BOS meeting day → harvest files."""
import re
from bs4 import BeautifulSoup
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
AGENDA = BASE + "Agenda/Default.aspx"

sess = requests.Session(impersonate=UA)

# 1. Establish session via Search
sess.get(BASE + "Search/Default.aspx", timeout=30)

# 2. GET Agenda root → extract ViewState
r = sess.get(AGENDA, timeout=30)
soup = BeautifulSoup(r.text, "html.parser")


def hidden(name: str) -> str:
    el = soup.find("input", {"name": name})
    return el.get("value", "") if el else ""


vs = hidden("__VIEWSTATE")
vsg = hidden("__VIEWSTATEGENERATOR")
print(f"  initial __VIEWSTATE len={len(vs)}")

# 3. Try posting back for a few candidate Tuesday day-ids
#    May 19 2026 (today) = 9635; May 12 = 9628; May 5 = 9621
for day_id, label in [(9628, "May 12 2026"), (9621, "May 5 2026"), (9614, "Apr 28 2026")]:
    post_data = {
        "__EVENTTARGET": "ctl00$DefaultContent$agendaCalendar",
        "__EVENTARGUMENT": str(day_id),
        "__VIEWSTATE": vs,
        "__VIEWSTATEGENERATOR": vsg,
        "__LASTFOCUS": "",
    }
    rp = sess.post(AGENDA, data=post_data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": AGENDA,
    }, timeout=60)
    soup2 = BeautifulSoup(rp.text, "html.parser")
    # Re-extract viewstate for next request
    vs = soup2.find("input", {"name": "__VIEWSTATE"})
    vs = vs.get("value", "") if vs else ""

    # Check iframe src
    ifr = soup2.find("iframe", id="ctl00_DefaultContent_Files_ifrmFiles")
    ifr_src = ifr.get("src") if ifr else "(no iframe)"

    # Hunt for File.ashx links AND iframe URLs in the response
    file_ids = sorted(set(re.findall(r"File\.ashx\?id=(\d+)", rp.text)))
    files_links = re.findall(r"(?:src|href)=['\"]([^'\"]*?Files[^'\"]*?\.aspx[^'\"]*)['\"]", rp.text)
    files_links = sorted(set(files_links))

    print(f"\n--- {label} (day_id={day_id}) ---")
    print(f"  status={rp.status_code} bytes={len(rp.content)}")
    print(f"  iframe src: {ifr_src}")
    print(f"  File.ashx IDs in response: {len(file_ids)}  ({file_ids[:10]})")
    print(f"  Files*.aspx links: {len(files_links)}")
    for fl in files_links[:5]:
        print(f"    {fl}")

# 4. Save the last response for inspection
with open("_questys_postback_response.html", "w", encoding="utf-8") as f:
    f.write(rp.text)
print(f"\n  saved _questys_postback_response.html ({len(rp.content)}B)")
