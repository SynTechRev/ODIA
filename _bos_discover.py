"""Discover Tulare County BOS meeting + document URLs.

Strategy:
1. Walk paginated sitemaps for any URL containing /board-of-supervisors/
2. Probe the BOS landing page for direct agenda/packet links (PDFs)
3. Pick a sample meeting page and harvest attached docs to confirm structure
"""

import re
from collections import Counter
from urllib.parse import urljoin

from curl_cffi import requests

UA_IMP = "chrome131"
BASE = "https://tularecounty.ca.gov"

# ---------------------------------------------------------------------------
# 1. Walk paginated sitemaps for BOS URLs
# ---------------------------------------------------------------------------
print("=== sitemap walk ===")
sitemap_index = f"{BASE}/sitemap.xml"
r = requests.get(sitemap_index, impersonate=UA_IMP, timeout=30)
print(f"  index: status={r.status_code} bytes={len(r.content)}")

sub_sitemaps = sorted(set(re.findall(r"<loc>([^<]+sitemap\.xml[^<]*?)</loc>", r.text)))
print(f"  sub-sitemaps: {len(sub_sitemaps)}")
for s in sub_sitemaps[:3]:
    print(f"    {s}")
if len(sub_sitemaps) > 3:
    print(f"    ... +{len(sub_sitemaps) - 3} more")

bos_urls = []
total_walked = 0
for sm in sub_sitemaps:
    try:
        rr = requests.get(sm, impersonate=UA_IMP, timeout=30)
        locs = re.findall(r"<loc>([^<]+)</loc>", rr.text)
        total_walked += len(locs)
        for loc in locs:
            if "/board-of-supervisors" in loc.lower() or "/bos/" in loc.lower():
                bos_urls.append(loc)
    except Exception as exc:
        print(f"  FAIL {sm}: {exc}")

print(f"\n  total URLs walked: {total_walked}")
print(f"  BOS-matching URLs: {len(bos_urls)}")

# Bucket by URL depth to understand the structure
depth_buckets = Counter()
for u in bos_urls:
    rel = u.split("/board-of-supervisors", 1)[-1]
    parts = [p for p in rel.split("/") if p]
    if not parts:
        depth_buckets["_root"] += 1
    else:
        depth_buckets[parts[0]] += 1

print("\n  BOS subpath buckets (top 12):")
for path, count in depth_buckets.most_common(12):
    print(f"    {count:>5}  /{path}")

# ---------------------------------------------------------------------------
# 2. Probe the BOS landing page for PDFs / agenda links
# ---------------------------------------------------------------------------
print("\n=== BOS landing page probe ===")
landing = f"{BASE}/board-of-supervisors"
r = requests.get(landing, impersonate=UA_IMP, timeout=30)
print(f"  {landing}: status={r.status_code} bytes={len(r.content)}")

# Hunt for PDF + Legistar + obvious meeting/agenda hrefs
pdf_hrefs = sorted(
    set(re.findall(r"""href=["']([^"']+\.pdf[^"']*)["']""", r.text, re.I))
)
meeting_hrefs = sorted(
    set(
        re.findall(
            r"""href=["']([^"']*(?:meeting|agenda|packet|minutes)[^"']*?)["']""",
            r.text,
            re.I,
        )
    )
)
print(f"  PDFs on landing: {len(pdf_hrefs)}")
for p in pdf_hrefs[:5]:
    print(f"    {p}")
print(f"  meeting/agenda hrefs: {len(meeting_hrefs)}")
for p in meeting_hrefs[:8]:
    print(f"    {p}")

# ---------------------------------------------------------------------------
# 3. Sample a meeting subpage if we found one, and harvest attachments
# ---------------------------------------------------------------------------
sample_meeting = None
for h in meeting_hrefs:
    full = urljoin(landing, h)
    if "/board-of-supervisors" in full.lower() and "agenda" in full.lower():
        sample_meeting = full
        break

if sample_meeting:
    print(f"\n=== sample meeting page: {sample_meeting} ===")
    r = requests.get(sample_meeting, impersonate=UA_IMP, timeout=30)
    print(f"  status={r.status_code} bytes={len(r.content)}")
    attach_pdfs = sorted(
        set(re.findall(r"""href=["']([^"']+\.pdf[^"']*)["']""", r.text, re.I))
    )
    print(f"  attached PDFs: {len(attach_pdfs)}")
    for p in attach_pdfs[:10]:
        print(f"    {p}")
else:
    print("\n  (no meeting subpage found on landing — will need deeper crawl)")

# Persist for next steps
import json

with open("_bos_urls.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "total_walked": total_walked,
            "bos_urls": bos_urls,
            "landing_pdfs": pdf_hrefs,
            "landing_meeting_hrefs": meeting_hrefs,
        },
        f,
        indent=2,
    )
print(f"\n  saved _bos_urls.json ({len(bos_urls)} BOS urls + landing hrefs)")
