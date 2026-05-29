"""Consolidate the three Tulare labels into one canonical `tulare-county`.

Pre-consolidation state (per /api/v1/jurisdictions):
  tulare-county    88 docs (BOS, Questys, the bulk of value)
  tulare_county     6 docs (TCSO Drupal sheriff scans, underscore label)
  tulare            1 doc  (single Akamai test from v3.1.0)

Post-consolidation:
  tulare-county    95 docs (88 + 6 + 1)

Touches three tables: documents, analyses, anomalies. Wrapped in a
single transaction so the rename is atomic.
"""
import sys

from oraculus_di_auditor.db.session import init_db, get_db

init_db()

from sqlalchemy import text  # noqa: E402

CANONICAL = "tulare-county"
ALIASES = ("tulare_county", "tulare")

with get_db() as session:
    # Show pre-state
    print("=== pre-state ===")
    rows = session.execute(
        text("SELECT jurisdiction, COUNT(*) FROM documents GROUP BY jurisdiction "
             "ORDER BY 2 DESC")
    ).all()
    for j, c in rows:
        print(f"  {j!s:<20}  {c} docs")

    # Update each of the three tables. Document model column is `jurisdiction`;
    # Anomaly is `jurisdiction_id`; Analysis... let me check.
    # Actually the safest path is to introspect: try both column names per table.
    table_columns = [
        ("documents", "jurisdiction"),
        ("analyses",  "jurisdiction"),
        ("anomalies", "jurisdiction"),
        ("seen_hashes", "jurisdiction_id"),
        ("mesh_execution_jobs", None),  # no jurisdiction column
    ]

    print("\n=== updates ===")
    for table, col in table_columns:
        if col is None:
            continue
        # Confirm column exists
        cols = session.execute(text(f"PRAGMA table_info({table})")).all()
        col_names = {c[1] for c in cols}
        if col not in col_names:
            # Try the other naming convention
            alt = "jurisdiction_id" if col == "jurisdiction" else "jurisdiction"
            if alt in col_names:
                col = alt
            else:
                print(f"  {table}: no jurisdiction-like column ({col_names}); skip")
                continue
        for alias in ALIASES:
            r = session.execute(
                text(f"UPDATE {table} SET {col} = :canon WHERE {col} = :alias"),
                {"canon": CANONICAL, "alias": alias},
            )
            if r.rowcount:
                print(f"  {table}.{col}: {alias!r} -> {CANONICAL!r}  ({r.rowcount} rows)")

    session.commit()

    # Post-state
    print("\n=== post-state ===")
    rows = session.execute(
        text("SELECT jurisdiction, COUNT(*) FROM documents GROUP BY jurisdiction "
             "ORDER BY 2 DESC")
    ).all()
    for j, c in rows:
        print(f"  {j!s:<20}  {c} docs")

print("\nDone.")
