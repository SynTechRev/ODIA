"""Confirm v3.2.4 semantic-container extraction yields real article text."""
import tempfile
from pathlib import Path

from curl_cffi import requests

URL = "https://tularecounty.ca.gov/sheriff/media/news-releases/32-year-old-man-shoots-kills-father-leads-deputies-on-a-chase-then-shoots-himself"

print(f"GET {URL}")
r = requests.get(URL, impersonate="chrome131", timeout=30)
print(f"  raw bytes: {len(r.content)}")

tmp = Path(tempfile.mkdtemp()) / "page.html"
tmp.write_bytes(r.content)

from oraculus_di_auditor.interface.routes.upload import ingest_uploaded_file

normalized = ingest_uploaded_file(tmp)
print(f"\nreturned keys: {sorted(normalized.keys())}")
for k, v in normalized.items():
    if isinstance(v, str):
        print(f"  {k}: str(len={len(v)})  head={v[:120]!r}")
    elif isinstance(v, (dict, list)):
        print(f"  {k}: {type(v).__name__}(len={len(v)})")
    else:
        print(f"  {k}: {type(v).__name__}={v!r}")
