"""Move snapshot 02/05 00:13:17 -> 01/05 23:55:00 (preenche gap do 23:55 de 01/05)."""
import sqlite3, sys

DB = "ranking.db"
ORIGEM = "2026-05-02 00:13:17"
DESTINO = "2026-05-01 23:55:00"

conn = sqlite3.connect(DB)
cur = conn.cursor()

n_origem = cur.execute("SELECT COUNT(*) FROM snapshots WHERE collected_at=?", (ORIGEM,)).fetchone()[0]
n_destino = cur.execute("SELECT COUNT(*) FROM snapshots WHERE collected_at=?", (DESTINO,)).fetchone()[0]
print(f"Origem  {ORIGEM} -> {n_origem} registros")
print(f"Destino {DESTINO} -> {n_destino} registros (deve ser 0)")

if n_origem == 0 or n_destino > 0:
    print("ABORTADO")
    sys.exit(1)

cur.execute("UPDATE snapshots SET collected_at=? WHERE collected_at=?", (DESTINO, ORIGEM))
conn.commit()
print(f"OK: movido")
conn.close()
