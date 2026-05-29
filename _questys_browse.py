"""Probe Questys for folder/tree/browse endpoints + map the full URL surface."""
import re
from bs4 import BeautifulSoup
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"

sess = requests.Session(impersonate=UA)

# 1. Common Questys page candidates
candidates = [
    "Default.aspx",
    "Home/Default.aspx",
    "Folder/Default.aspx",
    "Folders/Default.aspx",
    "Tree/Default.aspx",
    "Browse/Default.aspx",
    "Document/Default.aspx",
    "Documents/Default.aspx",
    "Folder.aspx",
    "Browse.aspx",
    "Tree.aspx",
    "Records/Default.aspx",
    "Cabinet/Default.aspx",
    "Cabinets/Default.aspx",
    "Login.aspx",  # see if it redirects somewhere useful
]
print("=== probe candidate pages ===")
working = []
for c in candidates:
    try:
        r = sess.get(BASE + c, timeout=15, allow_redirects=False)
        loc = r.headers.get("location", "")[:80]
        print(f"  {r.status_code}  {c:<35}  {len(r.content):>6}B  ->{loc}")
        if r.status_code == 200 and len(r.content) > 2000:
            working.append(c)
    except Exception as exc:
        print(f"  ERR  {c}: {exc}")

print(f"\n  pages with substantive 200 response: {working}")

# 2. Get the root + look at navigation menu
print("\n=== root page navigation ===")
r = sess.get(BASE, timeout=30)
print(f"  GET {BASE}: {r.status_code} {len(r.content)}B")
soup = BeautifulSoup(r.text, "html.parser")
nav_links = []
for a in soup.find_all("a", href=True):
    href = a.get("href", "")
    label = a.get_text(" ", strip=True)
    if href.endswith(".aspx") or "Default" in href or href.startswith("./") or href.startswith("../"):
        nav_links.append((label, href))
unique_links = sorted(set(nav_links), key=lambda x: x[1])
print(f"  unique .aspx-ish nav hrefs: {len(unique_links)}")
for label, href in unique_links[:40]:
    print(f"    [{label[:30]:<30}] -> {href[:80]}")

# 3. Save the root page
with open("_questys_root_full.html", "w", encoding="utf-8") as f:
    f.write(r.text)

# 4. Walk the working browse-like pages
for c in working:
    if "search" in c.lower():
        continue
    r = sess.get(BASE + c, timeout=30)
    print(f"\n=== {c} ({len(r.content)}B) ===")
    s = BeautifulSoup(r.text, "html.parser")
    title = s.title.get_text(strip=True) if s.title else "(none)"
    print(f"  title: {title}")
    # Look for the tree / folder list
    tree_hint = s.find(class_=re.compile(r"tree|folder|nav", re.I))
    if tree_hint:
        print(f"  tree-ish element: {tree_hint.name} class={tree_hint.get('class')}")
        # List children
        for a in tree_hint.find_all("a", href=True)[:20]:
            print(f"    [{a.get_text(strip=True)[:40]}] -> {a.get('href')[:80]}")
