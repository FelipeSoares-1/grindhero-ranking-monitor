"""
Corrige o snapshot que disparou atrasado: move 01/05 02:49:05 para 30/04 23:55:00.
A tarefa do 23:55 de 30/04 não disparou no horário (PC ocupado/sleep) e o
StartWhenAvailable só acordou a tarefa às 02:49 do dia 01/05 — fazendo o snapshot
ficar gravado no dia errado.
"""
import sqlite3, sys

DB = "ranking.db"
ORIGEM = "2026-05-01 02:49:05"
DESTINO = "2026-04-30 23:55:00"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Verifica antes
n_origem = cur.execute("SELECT COUNT(*) FROM snapshots WHERE collected_at=?", (ORIGEM,)).fetchone()[0]
n_destino_antes = cur.execute("SELECT COUNT(*) FROM snapshots WHERE collected_at=?", (DESTINO,)).fetchone()[0]
print(f"Origem  : {ORIGEM}  ->  {n_origem} registros")
print(f"Destino : {DESTINO}  ->  {n_destino_antes} registros (deve ser 0)")

if n_origem == 0:
    print("ERRO: snapshot de origem nao encontrado.")
    sys.exit(1)

if n_destino_antes > 0:
    print("ERRO: ja existe snapshot no destino. Abortando para evitar duplicidade.")
    sys.exit(1)

# Aplica o update
cur.execute("UPDATE snapshots SET collected_at=? WHERE collected_at=?", (DESTINO, ORIGEM))
conn.commit()

# Verifica depois
n_destino_depois = cur.execute("SELECT COUNT(*) FROM snapshots WHERE collected_at=?", (DESTINO,)).fetchone()[0]
n_origem_depois  = cur.execute("SELECT COUNT(*) FROM snapshots WHERE collected_at=?", (ORIGEM,)).fetchone()[0]
print(f"\nDepois:")
print(f"  {ORIGEM}  ->  {n_origem_depois} registros (deve ser 0)")
print(f"  {DESTINO}  ->  {n_destino_depois} registros (deve ser 300)")
conn.close()
print("\nOK - snapshot corrigido.")
