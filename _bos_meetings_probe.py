"""Deep-probe the BOS meetings page for attached agenda/packet/minutes PDFs."""
import json
import re
from collections import Counter
from urllib.parse import urljoin, urlparse

from curl_cffi import requests

UA = "chrome131"
MEETINGS = "https://www.tularecounty.ca.gov/board/board-of-supervisors-meetings"

r = requests.get(MEETINGS, impersonate=UA, timeout=30)
print(f"GET {MEETINGS}")
print(f"  status={r.status_code} bytes={len(r.content)}")

# Save raw for offline inspection
with open("_bos_meetings_raw.html", "w", encoding="utf-8") as f:
    f.write(r.text)

# Hunt for ALL hrefs and bucket by host + extension
all_hrefs = re.findall(r"""href=["']([^"']+)["']""", r.text)
print(f"  total hrefs on page: {len(all_hrefs)}")

# Resolve to absolute + dedupe
absolute = sorted({urljoin(MEETINGS, h) for h in all_hrefs if h.strip() and not h.startswith("#")})
print(f"  unique absolute hrefs: {len(absolute)}")

# Bucket by host
host_counts = Counter(urlparse(u).netloc for u in absolute)
print(f"\n  hosts (top 8):")
for host, count in host_counts.most_common(8):
    print(f"    {count:>4}  {host}")

# Look for document-ish extensions
ext_pat = re.compile(r"\.(pdf|docx?|pptx?|xlsx?)(\?|$)", re.I)
doc_hrefs = [u for u in absolute if ext_pat.search(u)]
print(f"\n  document hrefs (pdf/docx/xlsx/pptx): {len(doc_hrefs)}")
for u in doc_hrefs[:15]:
    print(f"    {u}")

# Look for likely meeting/agenda anchors that aren't direct PDFs
keyword_pat = re.compile(r"(agenda|packet|minute|meeting|action)", re.I)
keyword_hrefs = [u for u in absolute if keyword_pat.search(u) and not ext_pat.search(u)]
print(f"\n  meeting-keyword hrefs (no extension): {len(keyword_hrefs)}")
for u in keyword_hrefs[:15]:
    print(f"    {u}")

# Look for likely iframe/embed (Granicus, Legistar, Civica, etc.)
iframe_srcs = re.findall(r"""<iframe[^>]+src=["']([^"']+)["']""", r.text, re.I)
print(f"\n  iframe srcs: {len(iframe_srcs)}")
for s in iframe_srcs[:5]:
    print(f"    {s}")

# Persist findings
with open("_bos_meetings_links.json", "w", encoding="utf-8") as f:
    json.dump({
        "source": MEETINGS,
        "doc_hrefs": doc_hrefs,
        "keyword_hrefs": keyword_hrefs,
        "iframes": iframe_srcs,
        "hosts": dict(host_counts.most_common(15)),
    }, f, indent=2)
print(f"\n  saved _bos_meetings_links.json")
