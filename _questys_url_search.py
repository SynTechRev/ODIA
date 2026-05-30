"""Test Questys Search/Default.aspx?q=<term> URL pattern."""

import re

from bs4 import BeautifulSoup
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
SEARCH = BASE + "Search/Default.aspx"

sess = requests.Session(impersonate=UA)

# First GET to establish session cookies
sess.get(SEARCH, timeout=30)

# Try a few search patterns
for q in ["agenda", "board+of+supervisors", "resolution", "*"]:
    url = f"{SEARCH}?q={q}"
    r = sess.get(url, timeout=60)
    soup = BeautifulSoup(r.text, "html.parser")

    # Hunt for results: Telerik RadGrid uses <table> with class containing "rgMasterTable"
    grids = soup.find_all(
        "table", class_=re.compile(r"(rgMasterTable|results|gvResults)")
    )
    rows = []
    for g in grids:
        rows.extend(g.find_all("tr"))
    # Also count generic data rows
    all_links = soup.find_all("a", href=True)
    doc_links = [
        a
        for a in all_links
        if re.search(r"(GetItem|Document/View|Detail)\.aspx", a.get("href", ""), re.I)
    ]
    id_hits = sorted(set(re.findall(r"(?:id|recordid)=(\d+)", r.text, re.I)))

    # Look for any error banner
    errors = [
        el.get_text(strip=True)
        for el in soup.select(".error, .alert")
        if el.get_text(strip=True)
    ]

    print(
        f"q={q!r:<30} status={r.status_code} bytes={len(r.content):>6}  grids={len(grids)} rows={len(rows)}  doc_links={len(doc_links)}  ids={len(id_hits)}"
    )
    if errors:
        print(f"   error: {errors[0][:80]}")
    if doc_links:
        print(f"   sample doc link: {doc_links[0].get('href')}")
    if id_hits[:5]:
        print(f"   sample ids: {id_hits[:5]}")

# Save the agenda search response for deeper inspection
url = f"{SEARCH}?q=agenda"
r = sess.get(url, timeout=60)
with open("_questys_q_agenda.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print(f"\n  saved _questys_q_agenda.html ({len(r.content)}B)")
