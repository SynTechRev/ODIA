"""Test File.ashx?id=N direct download + figure out pagination."""

import re

from bs4 import BeautifulSoup
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"

sess = requests.Session(impersonate=UA)

# 1. Direct download of a known doc
for doc_id in [2824, 2913, 2952]:
    url = f"{BASE}File.ashx?id={doc_id}&v=1"
    r = sess.get(url, timeout=30, allow_redirects=True)
    print(
        f"  File.ashx?id={doc_id}: status={r.status_code} bytes={len(r.content):>8} content-type={r.headers.get('content-type', '')[:50]}"
    )
    # Show content-disposition (gives us filename + extension)
    cd = r.headers.get("content-disposition", "")
    if cd:
        print(f"     disposition: {cd[:120]}")
    # Sniff first 16 bytes
    print(f"     magic: {r.content[:16]!r}")

# 2. Look at pagination on the search results page
text = open("_questys_q_agenda.html", encoding="utf-8").read()
soup = BeautifulSoup(text, "html.parser")

print("\n=== pagination controls ===")
# Telerik RadGrid pager: look for span/div with class "rgPager" or "rgInfoPart"
pagers = soup.find_all(class_=re.compile(r"rgPager|rgInfoPart|rgPaging"))
print(f"  pager elements: {len(pagers)}")
for p in pagers[:3]:
    txt = p.get_text(" ", strip=True)
    print(f"    {txt[:150]}")
    for a in p.find_all("a", href=True):
        href = a.get("href", "")[:100]
        text2 = a.get_text(strip=True)[:20]
        print(f"      [{text2}] -> {href}")

# 3. Count distinct File.ashx IDs in the agenda search page (full regex)
ids = sorted(set(int(m) for m in re.findall(r"File\.ashx\?id=(\d+)", text)))
print(f"\n  unique File.ashx ids on page 1 of q=agenda: {len(ids)}")
print(f"  range: {min(ids)} .. {max(ids)}")
print(f"  full list: {ids}")

# 4. Total result count text
for m in re.finditer(
    r"(\d{1,5})\s+(?:items|results|matches|records|found)", text, re.I
):
    print(f"\n  result count text: '{m.group()}'")
    break
for m in re.finditer(r"Page\s+\d+\s+of\s+\d+|of\s+\d+\s+items", text, re.I):
    print(f"  page-of text: '{m.group()}'")
    break

# 5. Check for total count in pagination
total_count = soup.find(class_=re.compile(r"rgInfo|TotalCount|recordCount"))
if total_count:
    print(f"  total info: {total_count.get_text(' ', strip=True)[:120]}")
