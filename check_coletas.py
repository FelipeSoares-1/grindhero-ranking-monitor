import sqlite3, pandas as pd

conn = sqlite3.connect('ranking.db')
df = pd.read_sql_query(
    'SELECT collected_at, COUNT(DISTINCT ranking_type) as rts, COUNT(*) as registros '
    'FROM snapshots GROUP BY collected_at ORDER BY collected_at DESC LIMIT 20',
    conn, parse_dates=['collected_at']
)
print("=== ULTIMAS 20 COLETAS ===")
for _, r in df.iterrows():
    dia  = r['collected_at'].strftime('%d/%m')
    hora = r['collected_at'].strftime('%H:%M:%S')
    rts  = r['rts']
    reg  = r['registros']
    status = "OK" if rts == 6 else f"INCOMPLETO ({rts}/6)"
    print(f"  {dia}  {hora}  ->  {reg:3d} regs ({status})")
conn.close()
