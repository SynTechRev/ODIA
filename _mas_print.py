import json
from pathlib import Path

d = json.loads(Path("_mas_aggregates.json").read_text(encoding="utf-8"))

print("=== Master Audit Synthesis (MAS) aggregates ===")
print(f"  jurisdictions in scope: {d['jurisdictions_scope']}")
print(f"  total_documents:        {d['total_documents']}")
print(f"  total_anomalies:        {d['total_anomalies']}")
print(f"  by_severity:            {d['by_severity']}")
print()
print(f"=== unique finding IDs ({len(d['by_finding_id'])}) ===")
print(f"  {'count':>6}  {'severity':<10}  {'finding_id':<55}  jurisdictions")
print(f"  {'-'*6}  {'-'*10}  {'-'*55}  {'-'*40}")
for f in d["by_finding_id"]:
    j = ",".join(f["jurisdictions"])
    print(
        f"  {f['count']:>6}  {f['severity']:<10}  {f['anomaly_id']:<55}  [{f['jurisdiction_count']}j] {j}"
    )
