"""Probe TCSO news-release index for fresh URLs to smoke-test v3.2.4."""
import re
from curl_cffi import requests

INDEX = "https://tularecounty.ca.gov/sheriff/media/news-releases/"
r = requests.get(INDEX, impersonate="chrome131", timeout=30)
print(f"status={r.status_code} bytes={len(r.content)}")

# Match relative or absolute hrefs that look like a news-release item page.
pat = re.compile(r"""href=["']([^"']*?/sheriff/media/news-releases/[^"'?#]+?)["']""")
hrefs = pat.findall(r.text)
unique = sorted({h for h in hrefs if h.rstrip("/") != "/sheriff/media/news-releases"})
print(f"unique candidate hrefs: {len(unique)}")
for h in unique[:15]:
    print(h)
