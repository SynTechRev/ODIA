import json
from collections import Counter
from pathlib import Path

p = Path("_questys_local_ingest_log.json")
if not p.exists():
    print("no log yet")
    raise SystemExit
data = json.loads(p.read_text(encoding="utf-8-sig"))
print(f"log entries: {len(data)}")

status = Counter(m.get("status") for m in data.values())
print("status:", dict(status))

ext_status = Counter()
for m in data.values():
    ext_status[(m.get("ext", "?"), m.get("status", "?"))] += 1
print("\nby ext x status:")
for (e, s), c in sorted(ext_status.items()):
    print(f"  .{e:<6} {s:<25} {c}")

completed = [m for m in data.values() if m.get("status") == "completed"]
total_findings = sum(m.get("findings", 0) for m in completed)
total_bytes = sum(m.get("bytes", 0) for m in completed)
print(
    f"\ncompleted: {len(completed)}  findings={total_findings}  bytes={total_bytes:,}"
)

print("\ndocs WITH findings:")
for did, m in data.items():
    f = m.get("findings", 0)
    if f > 0:
        fn = m.get("filename", "")[:60]
        b = m.get("bytes", 0)
        print(f"  id={did} fn={fn}  findings={f} bytes={b:,}")
