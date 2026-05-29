"""Inspect Agenda/Default.aspx — the meeting calendar/index for BOS."""
import re
from bs4 import BeautifulSoup
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"

sess = requests.Session(impersonate=UA)
sess.get(BASE + "Search/Default.aspx", timeout=30)  # session establish

# 1. Pull the Agenda main page
r = sess.get(BASE + "Agenda/Default.aspx", timeout=30)
print(f"  GET Agenda/Default.aspx: status={r.status_code} bytes={len(r.content)}")
with open("_questys_agenda_root.html", "w", encoding="utf-8") as f:
    f.write(r.text)
soup = BeautifulSoup(r.text, "html.parser")

# 2. Title + main heading
print(f"  title: {soup.title.get_text(strip=True) if soup.title else 'n/a'}")

# 3. Look for top-level links/anchors that look like meetings or boards
print("\n=== anchors with text + href ===")
anchors = []
for a in soup.find_all("a", href=True):
    label = a.get_text(" ", strip=True)
    href = a.get("href", "")
    if label and href and not href.startswith("#") and "javascript:" not in href[:11]:
        anchors.append((label, href))
unique = sorted(set(anchors))
print(f"  unique label+href pairs: {len(unique)}")
for label, href in unique[:30]:
    print(f"    [{label[:40]:<40}] -> {href[:80]}")

# 4. Look at the iframe(s) — Questys often loads the agenda viewer in an iframe
iframes = soup.find_all("iframe")
print(f"\n  iframes: {len(iframes)}")
for f in iframes:
    print(f"    src={f.get('src')!r} name={f.get('name')!r} id={f.get('id')!r}")

# 5. Look for embedded boards/committees list
print("\n=== select dropdowns ===")
for sel in soup.find_all("select"):
    name = sel.get("name") or sel.get("id") or "?"
    opts = [(o.get("value"), o.get_text(strip=True)) for o in sel.find_all("option")]
    if opts and len(opts) > 1:
        print(f"  {name} ({len(opts)} options):")
        for v, t in opts[:15]:
            print(f"    [{v!s:<15}] {t[:60]}")

# 6. Tabs / panels - look for any data-binding attributes
print("\n=== probable meeting list ===")
tables = soup.find_all("table")
for t in tables:
    rows = t.find_all("tr")
    if len(rows) > 3:
        cls = t.get("class")
        print(f"  table rows={len(rows)} class={cls} id={t.get('id')}")
        # Show first 3 row labels
        for row in rows[:3]:
            cells = [c.get_text(' ', strip=True)[:30] for c in row.find_all(['th', 'td'])[:8]]
            print(f"    {cells}")
