"""Probe Questys CMX public document portal for API/endpoint shape."""

import re

from curl_cffi import requests

UA = "chrome131"
PORTAL = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"

print(f"GET {PORTAL}")
r = requests.get(PORTAL, impersonate=UA, timeout=30)
print(
    f"  status={r.status_code} bytes={len(r.content)} content-type={r.headers.get('content-type')}"
)
text = r.text

with open("_questys_root.html", "w", encoding="utf-8") as f:
    f.write(text)

# Hunt for JS endpoints / API roots / search endpoints
api_pat = re.compile(
    r"""["']((?:/[^"'\s]+)?(?:api|service|search|document|folder|cabinet)[^"'\s<>]*?)["']""",
    re.I,
)
api_hits = sorted(set(api_pat.findall(text)))
print(f"\n  api/service/search/document hits: {len(api_hits)}")
for h in api_hits[:30]:
    print(f"    {h}")

# Hunt for JS bundle files we can inspect
js_files = sorted(set(re.findall(r"""src=["']([^"']+\.js[^"']*)["']""", text)))
print(f"\n  JS files: {len(js_files)}")
for j in js_files[:10]:
    print(f"    {j}")

# Hunt for the Questys-specific config / app root pattern
# (Questys CMX commonly uses /api/document, /api/folder, /api/search endpoints
# and serves the SPA shell from /webclient/)
config_pat = re.compile(
    r"""(?:webApiUrl|apiUrl|serviceUrl|endpoint)\s*[:=]\s*["']([^"']+)["']""", re.I
)
config_hits = sorted(set(config_pat.findall(text)))
print(f"\n  inline app config URLs: {len(config_hits)}")
for c in config_hits:
    print(f"    {c}")

# Try common Questys public endpoints directly
common_endpoints = [
    "/questys.cmx.webclient/api/",
    "/questys.cmx.webclient/api/document/",
    "/questys.cmx.webclient/api/folder/",
    "/questys.cmx.webclient/api/search/",
    "/questys.cmx.webclient/api/cabinet/",
    "/questys.cmx.webclient/services/",
    "/questys.cmx.webservice/",
    "/api/",
    "/sitemap.xml",
]
print("\n=== blind probe common endpoints ===")
host = "https://publicdocs.co.tulare.ca.us"
for ep in common_endpoints:
    try:
        rr = requests.get(host + ep, impersonate=UA, timeout=10)
        ct = rr.headers.get("content-type", "")[:40]
        print(f"  {rr.status_code:>3}  {ep:<50} ({len(rr.content):>7}B  {ct})")
    except Exception as exc:
        print(f"  ERR  {ep}: {exc}")
