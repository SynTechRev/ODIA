"""Surface C2 stats + sample resolves for user inspection (per handoff protocol)."""

from pathlib import Path

from oraculus_di_auditor.legal.us_code_loader import USCodeLoader

loader = USCodeLoader(Path("data/legal_corpora/us-code"))
stats = loader.initialize()
print("=== loader stats ===")
for k, v in stats.items():
    print(f"  {k}: {v}")
print("\n=== loader.statistics() ===")
for k, v in loader.statistics().items():
    print(f"  {k}: {v}")

print("\n=== sample resolves ===")
for cit in ["34 U.S.C. § 10152", "42 U.S.C. § 1983", "18 U.S.C. § 242"]:
    r = loader.resolve_citation(cit)
    if r is None:
        print(f"\n  {cit}: NOT FOUND")
        continue
    print(f"\n  --- {cit} ---")
    print(f"    title:        {r.title!r}")
    print(f"    source_path:  {r.source_path}")
    print(f"    url:          {r.url}")
    print(f"    text length:  {len(r.text)} chars")
    print("    text preview:")
    for line in r.text.split("\n")[:8]:
        print(f"      {line}")
    if len(r.text.split("\n")) > 8:
        print(f"      ... [+{len(r.text.split(chr(10))) - 8} more lines]")
