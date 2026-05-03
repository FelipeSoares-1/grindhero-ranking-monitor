"""Move ultimo snapshot para 02/05 23:55:00 (preenche gap)."""
import sqlite3, sys

DB = "ranking.db"
DESTINO = "2026-05-02 23:55:00"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Pega a coleta MAIS RECENTE
ultimo = cur.execute("SELECT MAX(collected_at) FROM snapshots").fetchone()[0]
print(f"Origem  (mais recente)  : {ultimo}")
print(f"Destino                 : {DESTINO}")

n_destino = cur.execute("SELECT COUNT(*) FROM snapshots WHERE collected_at=?", (DESTINO,)).fetchone()[0]
if n_destino > 0:
    print(f"ABORTADO: ja existe snapshot em {DESTINO} ({n_destino} regs).")
    sys.exit(1)

n = cur.execute("UPDATE snapshots SET collected_at=? WHERE collected_at=?", (DESTINO, ultimo)).rowcount
conn.commit()
print(f"OK: {n} registros movidos.")
conn.close()
