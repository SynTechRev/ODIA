"""D1 visible payoff: render a real finding through translate_finding
and show the before/after for the user (per handoff communication protocol).

Picks a finding whose narrative cites 34 U.S.C. § 10152 — the JAG anti-
supplanting statute Tulare County BOS actually triggered in our v3.2.5
corpus (2 critical findings). Shows: (a) the rendered finding
WITHOUT the v3.3.0 embed (synthesizes by stripping plain_statute_text),
and (b) the same finding WITH the embed appended. This is the before/
after the user wants to see.
"""

from oraculus_di_auditor.reporting.plain_language import translate_finding


# A representative grant_compliance:jag-without-anti-supplanting finding.
# The narrative TRANSLATIONS for this includes the actual USC citation
# (34 U.S.C. § 10152) which the v3.3.0 embed resolves.
finding = {
    "id": "grant:jag-without-anti-supplanting",
    "layer": "grants",
    "severity": "critical",
    "details": {
        "instrument": "MOU between Tulare County and Department of Justice",
        "amount": "$847,000",
        "missing_certification": "anti-supplanting language",
        "discovery_date": "2026-02-15",
    },
}

print("=" * 70)
print("BEFORE v3.3.0 (no plain_statute_text field)")
print("=" * 70)
out = translate_finding(finding)
for k in ("plain_summary", "plain_impact", "plain_action", "plain_evidence_echo"):
    print(f"\n--- {k} ---")
    print(out.get(k, "(missing)"))

print("\n")
print("=" * 70)
print("AFTER v3.3.0 — plain_statute_text APPENDED")
print("=" * 70)
embed = out.get("plain_statute_text", "")
if embed:
    print(embed)
else:
    print("(no embed produced — falling back to manual narrative)")
    # Force-render via the helper with a known-good narrative containing § 10152
    from oraculus_di_auditor.reporting.plain_language import _embed_statute_text

    forced = _embed_statute_text(
        "The contract violated 34 U.S.C. § 10152 by lacking the "
        "anti-supplanting certification."
    )
    print("\n--- DIRECT INVOCATION on a narrative with the citation ---")
    print(forced)
