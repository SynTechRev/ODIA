import sqlite3

conn = sqlite3.connect("oraculus_audit.db")
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM documents")
print("Total docs:", c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM anomalies")
print("Total anomalies:", c.fetchone()[0])

c.execute("SELECT jurisdiction, COUNT(*) FROM documents GROUP BY jurisdiction ORDER BY COUNT(*) DESC")
print("\nDocs by jurisdiction:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

c.execute(
    "SELECT document_id, jurisdiction, title FROM documents "
    "WHERE title LIKE ? OR title LIKE ? OR title LIKE ? OR title LIKE ? OR title LIKE ?",
    ("%MAS%", "%Master Audit%", "%Synthesis%", "%master_audit%", "%_mas_%")
)
mas_docs = c.fetchall()
print(f"\nPotential MAS documents ({len(mas_docs)}):")
for row in mas_docs:
    print(f"  [{row[1]}] id={row[0]} | {row[2][:90]}")

# Also check for TCSO and Visalia specifically
c.execute("SELECT COUNT(*) FROM documents WHERE jurisdiction IN ('tcso','visalia','tcda','tcpd')")
print("\nNew jurisdiction counts:", c.fetchone()[0])

c.execute("SELECT jurisdiction, COUNT(*) FROM documents WHERE jurisdiction IN ('tcso','visalia','tcda','tcpd') GROUP BY jurisdiction")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
