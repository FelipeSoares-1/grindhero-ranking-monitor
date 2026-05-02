import sqlite3, pandas as pd

conn = sqlite3.connect(r'C:\Users\Felipe Soares\Documents\grindhero-ranking-monitor\ranking.db')
df = pd.read_sql_query('SELECT * FROM snapshots ORDER BY collected_at', conn, parse_dates=['collected_at'])

df['_date'] = df['collected_at'].dt.date
latest_per_day = df.groupby('_date')['collected_at'].max().rename('_keep')
df = df.join(latest_per_day, on='_date')
df_dedup = df[df['collected_at'] == df['_keep']].drop(columns=['_date', '_keep']).reset_index(drop=True)

datas = sorted(df_dedup['collected_at'].unique())
lat  = df_dedup[df_dedup['collected_at'] == datas[-1]]
prev = df_dedup[df_dedup['collected_at'] == datas[-2]]

print(f'Comparando: {datas[-2]}  -->  {datas[-1]}')
print(f'Intervalo  : {datas[-1] - datas[-2]}')
print()

for rt in ['Experience','Melee','Shielding','Magic','Distance','Taming']:
    lat_rt  = lat[lat['ranking_type']==rt].set_index('player_id')[['name','rank','experience']]
    prev_rt = prev[prev['ranking_type']==rt].set_index('player_id')[['name','rank','experience']]
    comuns  = lat_rt.index.intersection(prev_rt.index)

    delta = pd.DataFrame({
        'nome'      : lat_rt.loc[comuns,'name'],
        'rank_hoje' : lat_rt.loc[comuns,'rank'].astype(int),
        'rank_ontem': prev_rt.loc[comuns,'rank'].astype(int),
        'variacao'  : (prev_rt.loc[comuns,'rank'] - lat_rt.loc[comuns,'rank']).astype(int),
        'xp_ganho'  : (lat_rt.loc[comuns,'experience'] - prev_rt.loc[comuns,'experience']).astype(int),
    })

    subiu   = (delta['variacao'] > 0).sum()
    desceu  = (delta['variacao'] < 0).sum()
    igual   = (delta['variacao'] == 0).sum()

    print(f'--- {rt} ---')
    print(f'  Subiu  : {subiu} jogadores')
    print(f'  Desceu : {desceu} jogadores')
    print(f'  Igual  : {igual} jogadores')
    quem_subiu = delta[delta['variacao'] > 0].sort_values('variacao', ascending=False).head(5)
    if not quem_subiu.empty:
        print(f'  Top subidas:')
        for _, r in quem_subiu.iterrows():
            print(f'    {r["nome"]:20s}  #{int(r["rank_ontem"])} -> #{int(r["rank_hoje"])}  (+{int(r["variacao"])} pos, +{int(r["xp_ganho"]):,} XP)')
    print()

conn.close()
