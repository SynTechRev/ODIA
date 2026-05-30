"""Inspect Questys ?q=agenda result grid: row structure + download URL pattern."""

import re

from bs4 import BeautifulSoup

text = open("_questys_q_agenda.html", encoding="utf-8").read()
soup = BeautifulSoup(text, "html.parser")

# Find the results grid table
grids = soup.find_all("table", class_=re.compile(r"rgMasterTable"))
print(f"grids: {len(grids)}")
if not grids:
    grids = soup.find_all("table")
    print(f"  fallback to all tables: {len(grids)}")

grid = grids[0]
rows = grid.find_all("tr")
print(f"grid rows: {len(rows)}")

# Header row
hdr = rows[0]
print("\n=== header ===")
for th in hdr.find_all(["th", "td"]):
    print(f"  [{th.get_text(' ', strip=True)[:60]}]")

# First few data rows — print all cells + links
print("\n=== first 3 data rows ===")
for i, row in enumerate(rows[1:4], 1):
    print(f"\n--- row {i} ---")
    cells = row.find_all(["td", "th"])
    for j, c in enumerate(cells):
        text_content = c.get_text(" ", strip=True)[:80]
        print(f"  cell[{j}]: {text_content!r}")
        for a in c.find_all("a", href=True):
            print(f"    href: {a.get('href')[:120]}")
        for img in c.find_all("img", src=True):
            print(f"    img:  {img.get('src')[:80]}  alt={img.get('alt')}")
        for inp in c.find_all("input"):
            print(
                f"    input: type={inp.get('type')} name={inp.get('name')} value={inp.get('value')}"
            )

# Look for the pagination / "X of Y results" text
print("\n=== pagination hints ===")
for kw in ["of", "Page", "results", "found"]:
    pat = re.compile(rf"\d+\s*{kw}\s*\d+|\d+\s+items", re.I)
    for m in pat.finditer(soup.get_text(" ", strip=True)):
        print(f"  match: {m.group()[:60]}")
        break

# Find all hrefs in the grid that look like detail/download
print("\n=== all unique hrefs in grid (first 20) ===")
hrefs = sorted({a.get("href", "") for a in grid.select("a[href]") if a.get("href")})
for h in hrefs[:20]:
    print(f"  {h[:120]}")

# Also any JS function call patterns we should mimic
print("\n=== onclick/href javascript patterns ===")
for a in grid.select("a[onclick], a[href^='javascript']")[:10]:
    js = a.get("onclick") or a.get("href")
    print(f"  {a.get_text(strip=True)[:30]:<30} -> {js[:100]}")
