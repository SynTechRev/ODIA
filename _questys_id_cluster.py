"""Test if IDs near known-good BOS docs are also accessible (clustered) or sparse."""
import re
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
sess = requests.Session(impersonate=UA)
sess.get(BASE + "Search/Default.aspx", timeout=30)


def probe(doc_id):
    try:
        r = sess.get(f"{BASE}File.ashx?id={doc_id}&v=1", timeout=10)
        cd = r.headers.get("content-disposition", "")
        m = re.search(r'filename="([^"]+)"', cd)
        fn = m.group(1) if m else ""
        return (r.status_code, len(r.content), fn)
    except Exception:
        return (-1, 0, "")


# Known anchor IDs
anchors = [2824, 4439, 4752, 5000, 100000, 150000]
print("=== probe ±10 around each anchor ===")
for anchor in anchors:
    print(f"\n  anchor {anchor}:")
    for offset in range(-3, 8):
        did = anchor + offset
        s, b, fn = probe(did)
        is_doc = b > 1000  # real document threshold
        marker = "DOC" if is_doc else "---"
        print(f"    {marker} id={did:>6} bytes={b:>9}  filename={fn[:60]!r}")
