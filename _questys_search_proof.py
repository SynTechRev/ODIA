"""Step 1 of Questys scraper: prove a single Type=Meeting search round-trip
works + harvest the result-row URL pattern.

Approach:
- GET Search/Default.aspx → extract __VIEWSTATE + __VIEWSTATEGENERATOR
- POST same URL with __EVENTTARGET=Search button + filters
- Parse the resulting HTML grid for document download links
"""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
SEARCH = urljoin(BASE, "Search/Default.aspx")

# ---- Persistent session so cookies survive ----
sess = requests.Session(impersonate=UA)

# ---- Step 1: GET the empty search form ----
print(f"[GET] {SEARCH}")
r = sess.get(SEARCH, timeout=30)
print(f"   status={r.status_code} bytes={len(r.content)}")

soup = BeautifulSoup(r.text, "html.parser")


def get_hidden(name: str) -> str:
    el = soup.find("input", {"name": name})
    return el.get("value", "") if el else ""


viewstate = get_hidden("__VIEWSTATE")
viewstate_gen = get_hidden("__VIEWSTATEGENERATOR")
viewstate_enc = get_hidden("__VIEWSTATEENCRYPTED")
event_validation = get_hidden("__EVENTVALIDATION")

print(f"   __VIEWSTATE: {len(viewstate)} chars")
print(f"   __VIEWSTATEGENERATOR: {viewstate_gen!r}")
print(f"   __VIEWSTATEENCRYPTED present: {bool(viewstate_enc)}")
print(
    f"   __EVENTVALIDATION: {len(event_validation)} chars (likely empty — site has it disabled)"
)

# ---- Step 2: POST a Type=Meeting search ----
# Per the dropdown options:
#   DropListType: 6 = Meeting
# We supply a wide-open name filter (LIKE "*") to match everything.
post_data = {
    "__EVENTTARGET": "ctl00$DefaultContent$Search",
    "__EVENTARGUMENT": "",
    "__LASTFOCUS": "",
    "__VIEWSTATE": viewstate,
    "__VIEWSTATEGENERATOR": viewstate_gen,
    "ctl00$DefaultContent$searchFormList": "Basic",
    "ctl00$DefaultContent$DropListType": "6",  # 6 = Meeting
    "ctl00$DefaultContent$TextName": "",
    "ctl00$DefaultContent$DropListName": "LIKE",
    "ctl00$DefaultContent$TextTEXT": "",
    "ctl00$DefaultContent$DropListTEXT": "CONTAINS",
    "ctl00$DefaultContent$TextExtension": "",
    "ctl00$DefaultContent$DropListExtension": "LIKE",
    "ctl00$DefaultContent$DropListState": "",
    "ctl00$DefaultContent$TextID": "",
    "ctl00$DefaultContent$DropListID": "EQ",
    "ctl00$DefaultContent$TextVersion": "",
    "ctl00$DefaultContent$DropListVersion": "EQ",
    "ctl00$DefaultContent$TextDate": "",
    "ctl00$DefaultContent$DropListDate": "GTE",
    "ctl00$DefaultContent$dropListDateTo": "LTE",
    "ctl00$DefaultContent$TextOwner": "",
    "ctl00$DefaultContent$NewSearchFormName": "",
    "ctl00$DefaultContent$Fields$ctrl0$DropListField$Input": "",
    "ctl00$DefaultContent$Fields$ctrl0$DropListField$ClientState": "",
    "ctl00_DefaultContent_NavigationControl_txtNumber": "1",
}
if viewstate_enc:
    post_data["__VIEWSTATEENCRYPTED"] = viewstate_enc

print(f"\n[POST] {SEARCH}  (Type=Meeting, page=1)")
r2 = sess.post(
    SEARCH,
    data=post_data,
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": SEARCH,
    },
    timeout=60,
)
print(f"   status={r2.status_code} bytes={len(r2.content)}")

with open("_questys_results.html", "w", encoding="utf-8") as f:
    f.write(r2.text)

# ---- Step 3: Parse for result rows / download links ----
soup2 = BeautifulSoup(r2.text, "html.parser")

# Look for the results table (Questys typically uses an ASP grid)
tables = soup2.find_all("table")
print(f"\n   tables on results page: {len(tables)}")
for i, t in enumerate(tables):
    rows = t.find_all("tr")
    if len(rows) >= 3:  # plausible data table
        print(
            f"     table[{i}]: {len(rows)} rows, id={t.get('id')!r}, class={t.get('class')}"
        )

# Hunt for any href that looks like a document detail/download
hrefs = sorted({a.get("href", "") for a in soup2.select("a[href]")})
doc_pat = re.compile(r"(GetItem|View|Detail|Download|item\.aspx|document\.aspx)", re.I)
doc_hrefs = [h for h in hrefs if doc_pat.search(h)]
print(f"\n   doc-shaped hrefs in results: {len(doc_hrefs)}")
for h in doc_hrefs[:20]:
    print(f"     {h}")

# Hunt for any tag with a numeric document ID / record marker
id_pat = re.compile(r"(?:id|recordid|documentid)=(\d+)", re.I)
ids = sorted(set(int(m) for m in id_pat.findall(r2.text)))
print(f"\n   numeric IDs found via regex: {len(ids)}  (sample: {ids[:10]})")

# Show any error / message banners
errors = [
    el.get_text(strip=True)
    for el in soup2.select(".error, .alert, [class*=Error], [class*=Message]")
    if el.get_text(strip=True)
]
if errors:
    print(f"\n   error/message banners: {errors[:5]}")
