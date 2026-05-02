import sqlite3, pandas as pd

conn = sqlite3.connect('ranking.db')
df = pd.read_sql_query(
    'SELECT collected_at, COUNT(DISTINCT name) as jogadores FROM snapshots GROUP BY collected_at ORDER BY collected_at',
    conn, parse_dates=['collected_at']
)
conn.close()

print("=== HISTÓRICO DE COLETAS ===")
dia_ant = None
for _, r in df.iterrows():
    dia  = r['collected_at'].strftime('%d/%m')
    hora = r['collected_at'].strftime('%H:%M')
    if dia != dia_ant:
        print(f"\n  [{dia}]")
        dia_ant = dia
    print(f"    {hora}  ->  {int(r['jogadores'])} jogadores")

print("\n=== TAREFAS AGENDADAS ===")
import subprocess
result = subprocess.run(['schtasks', '/query', '/fo', 'TABLE'], capture_output=True, text=True)
for line in result.stdout.splitlines():
    if 'GrindHero' in line:
        print(f"  {line.strip()}")
