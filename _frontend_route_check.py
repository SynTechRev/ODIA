"""Walk every query route the frontend uses and confirm shape + counts.

This is a backend-API smoke test for the v3.2.0 routes, exercised against
the live 848-doc / 324-anomaly state after .doc reingest. If any of these
fail, the frontend page that consumes them will show empty / broken.
"""

import json
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read())


def check(name, fn, expected_min=1):
    try:
        d = fn()
        n = len(d.get("items", [])) if isinstance(d, dict) and "items" in d else "?"
        total = d.get("total", "?") if isinstance(d, dict) else "?"
        ok = isinstance(d, dict) and (n == "?" or n >= expected_min)
        print(f"  {'OK ' if ok else 'WARN'} {name:<45} items={n}  total={total}")
        return d
    except Exception as exc:
        print(f"  ERR  {name:<45} {exc}")
        return None


print("=== /api/v1/health ===")
check("/health", lambda: get("/health"), expected_min=0)

print("\n=== /api/v1/jurisdictions ===")
d = check("/jurisdictions", lambda: get("/jurisdictions"))
if d:
    for j in d["items"]:
        print(
            f"     {j['jurisdiction']:<18} docs={j['document_count']:<4} anomalies={j['anomaly_count']}"
        )

print("\n=== /api/v1/documents (paginated) ===")
d = check("/documents?per_page=10", lambda: get("/documents?per_page=10"))
d = check(
    "/documents?jurisdiction=tulare-county&per_page=10",
    lambda: get("/documents?jurisdiction=tulare-county&per_page=10"),
)

print("\n=== /api/v1/anomalies (paginated + filtered) ===")
d = check("/anomalies?per_page=10", lambda: get("/anomalies?per_page=10"))
d = check(
    "/anomalies?severity=critical&per_page=10",
    lambda: get("/anomalies?severity=critical&per_page=10"),
)
d = check(
    "/anomalies?jurisdiction=tulare-county&severity=critical",
    lambda: get("/anomalies?jurisdiction=tulare-county&severity=critical"),
)

print("\n=== /api/v1/analyses (paginated) ===")
d = check("/analyses?per_page=10", lambda: get("/analyses?per_page=10"))

print("\n=== /api/v1/synthesis/aggregates ===")
d = check("/synthesis/aggregates", lambda: get("/synthesis/aggregates"))
if d:
    print(f"     total_documents:  {d['total_documents']}")
    print(f"     total_anomalies:  {d['total_anomalies']}")
    print(f"     by_severity:      {d['by_severity']}")
    print(f"     unique_findings:  {len(d['by_finding_id'])}")
    print(f"     scope:            {d['jurisdictions_scope']}")

print("\n=== Frontend dev server is up at http://localhost:3000 ===")
print("     Open these in browser for visual check:")
for path in ("/dashboard", "/documents", "/anomalies", "/analysis", "/synthesis"):
    print(f"       http://localhost:3000{path}")
