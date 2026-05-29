"""Probe File.ashx?id=N to find the upper bound + characterize the corpus."""
import re
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
sess = requests.Session(impersonate=UA)
sess.get(BASE + "Search/Default.aspx", timeout=30)  # establish session


def probe(doc_id):
    """Return (status, bytes, filename, content_type) or None."""
    try:
        r = sess.get(f"{BASE}File.ashx?id={doc_id}&v=1", timeout=15)
        cd = r.headers.get("content-disposition", "")
        m = re.search(r'filename="([^"]+)"', cd)
        fn = m.group(1) if m else ""
        return (r.status_code, len(r.content), fn, r.headers.get("content-type", "")[:40])
    except Exception as exc:
        return (-1, 0, str(exc)[:40], "")


# 1. Find upper bound — exponential probe
print("=== upper-bound search ===")
for did in [1, 100, 1000, 5000, 10000, 25000, 50000, 100000, 150000, 200000, 300000, 500000, 1000000]:
    s, b, fn, ct = probe(did)
    print(f"  id={did:>7}: status={s} bytes={b:>9}  ct={ct[:35]:<35}  filename={fn[:60]!r}")

# 2. Sample IDs across the range to see what kinds of docs exist
print("\n=== sample at various IDs ===")
import random
random.seed(42)
sample_ids = sorted(random.sample(range(2800, 50000), 25))
counts_by_ext = {}
for did in sample_ids:
    s, b, fn, ct = probe(did)
    if s == 200 and b > 100:
        ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else "(none)"
        counts_by_ext[ext] = counts_by_ext.get(ext, 0) + 1
        print(f"  id={did:>5}: status={s} bytes={b:>9}  filename={fn[:80]!r}")

print(f"\n=== extension distribution in sample ===")
for ext, c in sorted(counts_by_ext.items(), key=lambda x: -x[1]):
    print(f"  {ext:<10} {c}")
