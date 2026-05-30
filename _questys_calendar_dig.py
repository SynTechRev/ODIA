"""Dig into the agenda calendar: postback target + date format + iframe URL."""

import re

from bs4 import BeautifulSoup

text = open("_questys_agenda_root.html", encoding="utf-8").read()
soup = BeautifulSoup(text, "html.parser")

# 1. Find the calendar table + show all clickable cells
cal = soup.find("table", id="ctl00_DefaultContent_agendaCalendar")
print(f"calendar table: {cal.get('id')}")

# Walk every <td> + <a> in calendar
print("\n=== calendar cells with hrefs/onclicks ===")
seen_callbacks = set()
for td in cal.find_all("td"):
    for a in td.find_all("a", href=True):
        href = a.get("href", "")
        if "javascript:" in href:
            # Extract __doPostBack call signature
            m = re.search(
                r"__doPostBack\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]*)['\"]\)", href
            )
            if m:
                tgt, arg = m.groups()
                key = (tgt, arg[:30])
                if key not in seen_callbacks:
                    seen_callbacks.add(key)
                    print(
                        f"  __doPostBack target={tgt!r}  arg={arg!r}  label={a.get_text(strip=True)!r}"
                    )

print(f"\n  unique calendar postback targets: {len({c[0] for c in seen_callbacks})}")
print(f"  unique (target, arg) pairs: {len(seen_callbacks)}")

# 2. Show all distinct postback targets across the WHOLE page (not just calendar)
print("\n=== all unique __doPostBack targets on Agenda page ===")
post_pat = re.compile(r"__doPostBack\(['\"]([^'\"]+)['\"]")
tgts = sorted(set(post_pat.findall(text)))
print(f"  count: {len(tgts)}")
for t in tgts:
    print(f"    {t}")

# 3. Find the JS that sets the iframe src after a date pick (UpdatePanel + JS)
print("\n=== iframe src setters ===")
for m in re.finditer(
    r"(?:ifrmFiles|Files_ifrmFiles)[^;]*?(?:src|location)\s*=\s*['\"]?([^'\";\s]+)",
    text,
    re.I,
):
    print(f"  iframe src assignment: {m.group()[:200]}")

# 4. Look for the iframe URL format anywhere in the page
print("\n=== aspx-ish URLs in inline JS ===")
for m in re.finditer(r"['\"](\.\.?/[\w/]+\.aspx[^'\"]*?)['\"]", text):
    url = m.group(1)
    if "Agenda" in url or "File" in url or "Folder" in url:
        print(f"  {url}")

# 5. Look at the iframe's initial state — sometimes it has src='Files.aspx' pre-set
ifr = soup.find("iframe", id="ctl00_DefaultContent_Files_ifrmFiles")
if ifr:
    print(f"\n  iframe attrs: {dict(ifr.attrs)}")

# 6. Get sample VIEWSTATE for the next step
vs = re.search(r"id=\"__VIEWSTATE\"\s+value=\"([^\"]+)\"", text)
vsg = re.search(r"id=\"__VIEWSTATEGENERATOR\"\s+value=\"([^\"]+)\"", text)
print(f"\n  __VIEWSTATE: {len(vs.group(1)) if vs else 0} chars")
print(f"  __VIEWSTATEGENERATOR: {vsg.group(1) if vsg else 'none'}")
