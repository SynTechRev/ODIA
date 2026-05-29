"""Inspect Questys search button + ScriptManager / LongPolling.js to understand
the real submit mechanism (direct postback vs async polling vs RadAjax)."""
from bs4 import BeautifulSoup
from curl_cffi import requests

text = open("_questys_search.html", encoding="utf-8").read()
soup = BeautifulSoup(text, "html.parser")

# 1. Find buttons with "search" in name/id
print("=== Search buttons ===")
for s in soup.find_all("input", {"type": ["submit", "button"]}):
    sid = s.get("id") or ""
    sname = s.get("name") or ""
    if "search" in sid.lower() or "search" in sname.lower():
        onclick = s.get("onclick") or ""
        print(f"  id={sid!r} name={sname!r}")
        print(f"    value={s.get('value')!r}")
        print(f"    onclick={onclick[:200]!r}")

# 2. Telerik / RadAjax / UpdatePanel hints
print("\n=== framework hints ===")
for hint in ["ScriptManager", "RadAjaxManager", "UpdatePanel", "RadAjax", "Telerik",
             "WebForm_DoPostBackWithOptions", "__doPostBack", "ASPx", "PageMethods"]:
    if hint in text:
        print(f"  contains {hint!r}")

# 3. LongPolling.js content
print("\n=== LongPolling.js (first 3000B) ===")
js_url = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/js/LongPolling.js"
r = requests.get(js_url, impersonate="chrome131", timeout=30)
print(f"  status={r.status_code} bytes={len(r.content)}")
print(r.text[:3000])
