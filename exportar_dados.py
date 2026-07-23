"""
exportar_dados.py — GrindHero Monitor
Lê o banco SQLite, processa os dados e exporta data.json para o app React.
Roda toda vez que você quiser atualizar o dashboard.
"""
import sqlite3, os, json
import pandas as pd
from datetime import datetime

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DB_PATH       = os.path.join(BASE_DIR, os.environ.get("RANKING_DB", "ranking.db"))
CONFIG_PATH   = os.path.join(BASE_DIR, "config.json")
PUBLIC_DIR    = os.path.join(BASE_DIR, "dashboard-app", "public")
OUTPUT_PATH   = os.path.join(PUBLIC_DIR, "data.json")
FARM_PATH     = os.path.join(PUBLIC_DIR, "farm.json")


# ── helpers duplicados do gerar_dashboard para manter independência ──────────
def load(conn, server_id: int) -> pd.DataFrame:
    """
    Lê todos os snapshots e mantém apenas UMA coleta por dia:
    a ÚLTIMA do dia (maior collected_at). Assim, com 4 extrações/dia,
    a curva de evolução fica com 1 ponto por dia.
    """
    df = pd.read_sql_query(
        "SELECT * FROM snapshots WHERE server_id = ? ORDER BY collected_at, ranking_type, rank",
        conn, params=(server_id,), parse_dates=["collected_at"],
    )
    if df.empty:
        return df
    df["_date"] = df["collected_at"].dt.date
    latest_per_day = df.groupby("_date")["collected_at"].max().rename("_keep")
    df = df.join(latest_per_day, on="_date")
    df = df[df["collected_at"] == df["_keep"]].drop(columns=["_date", "_keep"]).reset_index(drop=True)
    return df


def latest(df: pd.DataFrame) -> pd.DataFrame:
    """Snapshot mais recente (última coleta do último dia disponível)."""
    return df[df["collected_at"] == df["collected_at"].max()]


def prev(df: pd.DataFrame) -> pd.DataFrame:
    """
    Snapshot de comparação = última coleta do DIA CALENDÁRIO anterior ao de latest.

    Com 4 extrações/dia o df já deduplica para 1 ponto/dia em load().
    Mas aqui usamos a data calendário para garantir que a comparação
    seja sempre dia-a-dia mesmo que latest seja 00:50 e o snapshot
    anterior seja 23:55 do mesmo dia.

    Ex.: latest = 05/05 00:50  →  prev = última coleta de 04/05 (23:55)
         delta = ~24h, correto.
    """
    if df.empty:
        return pd.DataFrame()

    latest_date = df["collected_at"].max().date()

    # Pega todos os snapshots de DIAS ANTERIORES ao dia do latest
    df_before = df[df["collected_at"].dt.date < latest_date]

    if df_before.empty:
        return pd.DataFrame()

    # Última coleta do dia imediatamente anterior
    prev_ts = df_before["collected_at"].max()
    return df[df["collected_at"] == prev_ts]


def fmt_xp(v):
    if v is None:
        return "—"
    v = int(v)
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"{v/1_000:.1f}K"
    return str(v)


# ── exportação ───────────────────────────────────────────────────────────────
def exportar_servidor(conn, cfg: dict, server: dict) -> dict | None:
    """Monta o payload completo de UM servidor. Retorna None se nao ha dados."""
    watched = cfg.get("watched_players", [])
    server_id = server["id"]

    df = load(conn, server_id)
    total_registros = conn.execute(
        "SELECT COUNT(*) FROM snapshots WHERE server_id = ?", (server_id,)
    ).fetchone()[0]

    if df.empty:
        print(f"[AVISO] {server['name']}: sem dados no banco ainda.")
        return None

    # Skills REAIS deste servidor, na ordem canonica do config.
    # Servidores podem nao expor o mesmo conjunto (ex.: Taming/Magic).
    ordem = cfg.get("ranking_types", [])
    presentes = set(df["ranking_type"].unique())
    ranking_types = [rt for rt in ordem if rt in presentes]
    ranking_types += sorted(presentes - set(ordem))   # skill nova na API, nao perde
    faltando = [rt for rt in ordem if rt not in presentes]
    if faltando:
        print(f"[INFO] {server['name']}: sem dados para {faltando} — abas omitidas.")

    df_lat = latest(df)
    df_prv = prev(df)

    ultima_coleta   = df_lat["collected_at"].iloc[0].strftime("%d/%m/%Y %H:%M")
    dias_coletando  = df["collected_at"].dt.date.nunique()
    total_jogadores = df["player_id"].nunique()

    # Informações do snapshot de comparação (prev)
    if not df_prv.empty:
        prev_ts    = df_prv["collected_at"].iloc[0]
        latest_ts  = df_lat["collected_at"].iloc[0]
        delta_horas = round((latest_ts - prev_ts).total_seconds() / 3600, 1)
        prev_info = {
            "data": prev_ts.strftime("%d/%m/%Y %H:%M"),
            "delta_horas": delta_horas,
        }
        print(f"[INFO] Comparativo: {ultima_coleta} vs {prev_info['data']} ({delta_horas}h de diferenca)")
    else:
        prev_info = None
        print("[AVISO] Sem snapshot anterior — deltas nao disponiveis")

    # ── metadata ──
    metadata = {
        "server": server["name"],
        "server_id": server_id,
        "slug": server["slug"],
        "label": server["label"],
        "ultima_coleta": ultima_coleta,
        "dashboard_gerado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "dias_coletando": dias_coletando,
        "total_jogadores": total_jogadores,
        "total_registros": total_registros,
        "watched": watched,
        "ranking_types": ranking_types,
        "prev_snapshot": prev_info,   # informa ao frontend o que está sendo comparado
    }

    # ── snapshot mais recente: todas as posições ──
    def row_to_dict(r):
        return {
            "player_id": r["player_id"],
            "name":      r["name"],
            "rank":      int(r["rank"]),
            "level":     int(r["level"]),
            "experience": int(r["experience"]),
            "ranking_type": r["ranking_type"],
            "collected_at": r["collected_at"].strftime("%Y-%m-%dT%H:%M:%S"),
        }

    latest_snapshot = [row_to_dict(r) for _, r in df_lat.iterrows()]

    # ── deltas (comparação com o snapshot anterior) ──
    deltas = {}
    if not df_prv.empty:
        now_idx = df_lat.set_index(["server_id", "player_id", "ranking_type"])
        old_idx = df_prv.set_index(["server_id", "player_id", "ranking_type"])
        for key in now_idx.index:
            if key in old_idx.index:
                xp_now  = int(now_idx.loc[key, "experience"])
                xp_old  = int(old_idx.loc[key, "experience"])
                rk_now  = int(now_idx.loc[key, "rank"])
                rk_old  = int(old_idx.loc[key, "rank"])
                sid, pid, rt = key
                deltas[f"{pid}_{rt}"] = {
                    "xp_delta":   xp_now - xp_old,
                    "rank_delta": rk_old - rk_now,  # positivo = subiu
                }

    # ── histórico completo por jogador × skill ──
    history = []
    for name in df["name"].unique():
        for rt in ranking_types:
            sub = df[
                (df["name"].str.lower() == name.lower()) &
                (df["ranking_type"] == rt)
            ].sort_values("collected_at")
            if sub.empty:
                continue
            history.append({
                "name": name,
                "ranking_type": rt,
                "points": [
                    {
                        "date":       row["collected_at"].strftime("%Y-%m-%d"),
                        "rank":       int(row["rank"]),
                        "experience": int(row["experience"]),
                        "level":      int(row["level"]),
                    }
                    for _, row in sub.iterrows()
                ],
            })

    # ── velocity (farm do dia): top 15 por skill ──
    velocity = {}
    if not df_prv.empty:
        for rt in ranking_types:
            lat_rt  = df_lat[df_lat["ranking_type"] == rt].set_index(["server_id", "player_id"])[["name", "experience", "rank"]]
            prev_rt = df_prv[df_prv["ranking_type"] == rt].set_index(["server_id", "player_id"])[["experience"]]
            comuns  = lat_rt.index.intersection(prev_rt.index)
            if len(comuns) == 0:
                continue
            gains = (lat_rt.loc[comuns, "experience"] - prev_rt.loc[comuns, "experience"]).astype(int)
            merged = lat_rt.loc[comuns].copy()
            merged["xp_day"] = gains
            merged = merged.sort_values("xp_day", ascending=False).head(15)
            velocity[rt] = [
                {
                    "name":    row["name"],
                    "rank":    int(row["rank"]),
                    "xp_day":  int(row["xp_day"]),
                    "label":   fmt_xp(int(row["xp_day"])),
                }
                for _, row in merged.iterrows()
            ]

    print(f"[OK] {server['name']}: {dias_coletando} dia(s) | {total_jogadores} jogadores | {total_registros} registros")

    return {
        "metadata":        metadata,
        "latest_snapshot": latest_snapshot,
        "deltas":          deltas,
        "history":         history,
        "velocity":        velocity,
    }


def build_farm_entry(payload: dict) -> dict:
    """
    Recorte minimo que o widget publico consome.

    O data.json completo tem ~3,6 MB por servidor — 99% e `history`, que o
    farm.html nunca le. Servir o payload completo num embed publico e
    desperdicio de banda a cada pageview.
    """
    md = payload["metadata"]
    return {
        "server":        md["server"],
        "label":         md["label"],
        "ultima_coleta": md["ultima_coleta"],
        "janela_horas":  (md.get("prev_snapshot") or {}).get("delta_horas"),
        "ranking_types": md["ranking_types"],
        "velocity":      payload["velocity"],
    }


def exportar() -> None:
    cfg = json.load(open(CONFIG_PATH, encoding="utf-8"))
    servers = cfg.get("servers") or [
        {**cfg["server"], "slug": "pvp", "label": "PvP", "primary": True}
    ]

    conn = sqlite3.connect(DB_PATH)
    try:
        payloads = {s["slug"]: exportar_servidor(conn, cfg, s) for s in servers}
    finally:
        conn.close()

    os.makedirs(PUBLIC_DIR, exist_ok=True)

    # ── data.json: dashboard privado. Contrato inalterado = so o servidor primario.
    primario = next((s for s in servers if s.get("primary")), servers[0])
    principal = payloads.get(primario["slug"])
    if principal is None:
        print("[ERRO] Servidor primario sem dados — data.json nao gerado.")
    else:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(principal, f, ensure_ascii=False, indent=2)
        print(f"[OK] data.json -> {OUTPUT_PATH}")

    # ── farm.json: widget publico, TODOS os servidores, payload enxuto.
    farm = {
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "servidores": [
            {"slug": s["slug"], **build_farm_entry(payloads[s["slug"]])}
            for s in servers if payloads.get(s["slug"]) is not None
        ],
    }
    if not farm["servidores"]:
        print("[ERRO] Nenhum servidor com dados — farm.json nao gerado.")
        return

    with open(FARM_PATH, "w", encoding="utf-8") as f:
        json.dump(farm, f, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(FARM_PATH) / 1024
    print(f"[OK] farm.json -> {FARM_PATH} ({kb:.1f} KB, {len(farm['servidores'])} servidor(es))")


if __name__ == "__main__":
    exportar()
