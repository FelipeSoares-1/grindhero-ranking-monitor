import sqlite3, pandas as pd

conn = sqlite3.connect(r'C:\Users\Felipe Soares\Documents\grindhero-ranking-monitor\ranking.db')
df = pd.read_sql_query('SELECT * FROM snapshots ORDER BY collected_at', conn, parse_dates=['collected_at'])

# Dedup igual o dashboard faz
df['_date'] = df['collected_at'].dt.date
latest_per_day = df.groupby('_date')['collected_at'].max().rename('_keep')
df = df.join(latest_per_day, on='_date')
df_dedup = df[df['collected_at'] == df['_keep']].drop(columns=['_date', '_keep']).reset_index(drop=True)

print('=== DIAS DISPONÍVEIS (após dedup) ===')
for d in sorted(df_dedup['collected_at'].unique()):
    n = df_dedup[df_dedup['collected_at'] == d]['name'].nunique()
    tipos = sorted(df_dedup[df_dedup['collected_at'] == d]['ranking_type'].unique())
    print(f'  {str(d)[:16]}  ->  {n} jogadores  |  {tipos}')

datas = sorted(df_dedup['collected_at'].unique())

print()
print('=== SNAPSHOT MAIS RECENTE (hoje) ===')
lat = df_dedup[df_dedup['collected_at'] == datas[-1]]
print(f'  Horário   : {datas[-1]}')
print(f'  Jogadores : {lat["name"].nunique()}')

print()
print('=== SNAPSHOT ANTERIOR (ontem) ===')
if len(datas) >= 2:
    prev = df_dedup[df_dedup['collected_at'] == datas[-2]]
    print(f'  Horário   : {datas[-2]}')
    print(f'  Jogadores : {prev["name"].nunique()}')

    print()
    print('=== TOP 10 XP GANHO (Experience) ===')
    lat_exp  = lat[lat['ranking_type']=='Experience'].set_index('player_id')[['name','experience','rank']]
    prev_exp = prev[prev['ranking_type']=='Experience'].set_index('player_id')[['name','experience','rank']]
    comuns = lat_exp.index.intersection(prev_exp.index)
    delta = pd.DataFrame({
        'nome'       : lat_exp.loc[comuns, 'name'],
        'rank_hoje'  : lat_exp.loc[comuns, 'rank'].astype(int),
        'xp_ganho'   : (lat_exp.loc[comuns, 'experience'] - prev_exp.loc[comuns, 'experience']).astype(int),
        'posicoes'   : (prev_exp.loc[comuns, 'rank'] - lat_exp.loc[comuns, 'rank']).astype(int),
    }).sort_values('xp_ganho', ascending=False).head(10)
    print(delta.to_string(index=False))

    print()
    print('=== VERIFICAÇÃO: tem jogadores com XP negativo? ===')
    negativos = delta[delta['xp_ganho'] < 0]
    if negativos.empty:
        print('  Nenhum — dados consistentes.')
    else:
        print(negativos.to_string(index=False))

conn.close()
