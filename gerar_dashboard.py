"""
Dashboard GrindHero Monitor — Cyberpunk Edition
Gera HTML interativo com design dark/neon focado em monitoramento de jogadores.
"""
import sqlite3, os, sys, json, textwrap
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ── paths ──────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DB_PATH        = os.path.join(BASE_DIR, "ranking.db")
CONFIG_PATH    = os.path.join(BASE_DIR, "config.json")
DASHBOARD_DIR  = os.path.join(BASE_DIR, "dashboard")
DASHBOARD_PATH = os.path.join(DASHBOARD_DIR, "index.html")

# ── design tokens (Red Skull Guild) ────────────────────────────────────────
CLR = {
    "bg":        "#0a0a0a",   # preto profundo
    "bg2":       "#141414",   # cinza escuro
    "surface":   "rgba(18,18,18,0.98)",
    "card":      "rgba(13,13,13,0.98)",
    "border":    "rgba(196,18,18,0.25)",
    # compat aliases usados nos charts
    "cyan":      "#d4af37",   # ouro como destaque principal
    "pink":      "#c0392b",   # vermelho escuro
    "green":     "#27ae60",   # verde
    "gold":      "#d4af37",   # ouro
    "amber":     "#e67e22",
    "yellow":    "#d4af37",
    "purple":    "#7d3c98",
    "text":      "#e0e0e0",
    "muted":     "#777777",
    # Cores por skill — paleta Red Skull
    "Experience":"#d4af37",   # ouro — XP é o mais nobre
    "Melee":     "#c0392b",   # vermelho sangue — combate corpo a corpo
    "Shielding": "#ca6f1e",   # ferrugem — defesa
    "Magic":     "#7d3c98",   # roxo profundo — arcano
    "Distance":  "#1a8a6e",   # verde escuro — arqueiro das sombras
    "Taming":    "#b7950b",   # ouro velho — domador
}

def hex_to_rgba(hex_color: str, alpha: float = 0.08) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Ubuntu Condensed, sans-serif", color=CLR["text"], size=12),
    margin=dict(l=16, r=16, t=40, b=16),
)


# ── data loading ───────────────────────────────────────────────────────────
def load(conn) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT * FROM snapshots ORDER BY collected_at, ranking_type, rank",
        conn, parse_dates=["collected_at"],
    )
    # Deduplicar: manter apenas o snapshot mais recente por dia calendario
    df["_date"] = df["collected_at"].dt.date
    latest_per_day = df.groupby("_date")["collected_at"].max().rename("_keep")
    df = df.join(latest_per_day, on="_date")
    df = df[df["collected_at"] == df["_keep"]].drop(columns=["_date", "_keep"]).reset_index(drop=True)
    return df


def latest(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["collected_at"] == df["collected_at"].max()]


def prev(df: pd.DataFrame) -> pd.DataFrame:
    # Retorna snapshot do dia anterior (não do penultimo timestamp do mesmo dia)
    dates = sorted(df["collected_at"].unique())
    if len(dates) < 2:
        return pd.DataFrame()
    return df[df["collected_at"] == dates[-2]]


# ── player helpers ─────────────────────────────────────────────────────────
def player_snapshot(df_snap: pd.DataFrame, name: str) -> pd.DataFrame:
    return df_snap[df_snap["name"].str.lower() == name.lower()]


def xp_delta(df_now: pd.DataFrame, df_old: pd.DataFrame, name: str, rt: str):
    now = df_now[(df_now["name"].str.lower() == name.lower()) & (df_now["ranking_type"] == rt)]
    old = df_old[(df_old["name"].str.lower() == name.lower()) & (df_old["ranking_type"] == rt)]
    if now.empty or old.empty:
        return None, None, None
    xp_n, xp_o = int(now.iloc[0]["experience"]), int(old.iloc[0]["experience"])
    rk_n, rk_o = int(now.iloc[0]["rank"]),       int(old.iloc[0]["rank"])
    return xp_n - xp_o, rk_o - rk_n, now.iloc[0]["level"]


# ── svg icons ──────────────────────────────────────────────────────────────
def svg_sword():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m14.5 17.5 3 3a2.12 2.12 0 0 0 3-3l-3-3"/><path d="M13 13 3 3l4 0 0 4"/><path d="m14 6 3 3"/></svg>'

def svg_shield():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'

def svg_star():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'

def svg_arrow_up():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m18 15-6-6-6 6"/></svg>'

def svg_arrow_down():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>'

def svg_minus():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14"/></svg>'

def svg_users():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'

def svg_trophy():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="8 2 12 6 16 2"/><path d="M17 2H7a5 5 0 0 0 0 10h.5a5.5 5.5 0 0 1 5 5.5V20"/><line x1="8" y1="20" x2="16" y2="20"/></svg>'

def svg_zap():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'

def svg_activity():
    return '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'

SKILL_ICONS = {
    "Experience": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "Melee":      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m14.5 17.5 3 3a2.12 2.12 0 0 0 3-3l-3-3"/><path d="M13 13 3 3l4 0 0 4"/><path d="m14 6 3 3"/></svg>',
    "Shielding":  '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "Magic":      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>',
    "Distance":   '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>',
    "Taming":     '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 5.172C10 3.782 8.423 2.679 6.5 3c-2.823.47-4.113 6.006-4 7 .08.703 1.725 1.722 3.656 1 1.261-.472 1.96-1.45 2.344-2.5"/><path d="M14.267 5.172c0-1.39 1.577-2.493 3.5-2.172 2.823.47 4.113 6.006 4 7-.08.703-1.725 1.722-3.656 1-1.261-.472-1.855-1.45-2.239-2.5"/><path d="M8 14v.5"/><path d="M16 14v.5"/><path d="M11.25 16.25h1.5L12 17l-.75-.75Z"/><path d="M4.42 11.247A13.152 13.152 0 0 0 4 14.556C4 18.728 7.582 21 12 21s8-2.272 8-6.444c0-1.061-.162-2.2-.493-3.309m-9.243-6.082A8.801 8.801 0 0 1 12 5c.78 0 1.5.108 2.161.306"/></svg>',
}


# ── formatters ─────────────────────────────────────────────────────────────
def fmt_xp(v):
    if v is None: return "—"
    v = int(v)
    if abs(v) >= 1_000_000: return f"{v/1_000_000:.2f}M"
    if abs(v) >= 1_000:     return f"{v/1_000:.1f}K"
    return str(v)

def fmt_delta(v, unit=""):
    if v is None or v == 0: return f'<span class="delta-neutral">{svg_minus()} 0{unit}</span>'
    color = "delta-up" if v > 0 else "delta-down"
    icon  = svg_arrow_up() if v > 0 else svg_arrow_down()
    sign  = "+" if v > 0 else ""
    return f'<span class="{color}">{icon} {sign}{fmt_xp(v)}{unit}</span>'

def fmt_rank_delta(v):
    if v is None or v == 0: return f'<span class="delta-neutral">{svg_minus()}</span>'
    color = "delta-up" if v > 0 else "delta-down"
    icon  = svg_arrow_up() if v > 0 else svg_arrow_down()
    sign  = "+" if v > 0 else ""
    return f'<span class="{color}">{icon} {sign}{v}</span>'


# ── charts ─────────────────────────────────────────────────────────────────
def chart_radar(df_latest: pd.DataFrame, watched: list) -> str:
    """Barras horizontais agrupadas por skill — muito mais legível que radar."""
    skills = ["Experience","Melee","Shielding","Magic","Distance","Taming"]
    colors = [CLR["cyan"], CLR["pink"], CLR["green"], CLR["yellow"], CLR["purple"], "#ff9f43"]

    fig = go.Figure()
    for i, name in enumerate(watched):
        ranks, labels = [], []
        for sk in skills:
            sub = df_latest[(df_latest["name"].str.lower() == name.lower()) & (df_latest["ranking_type"] == sk)]
            rank = int(sub.iloc[0]["rank"]) if not sub.empty else None
            ranks.append(rank)
            labels.append(f"#{rank}" if rank else "—")

        color = colors[i % len(colors)]
        fig.add_trace(go.Bar(
            name=name,
            x=skills,
            y=[51 - r if r else 0 for r in ranks],
            text=labels,
            textposition="outside",
            textfont=dict(color=color, size=12, family="Fira Code, monospace"),
            marker=dict(
                color=hex_to_rgba(color, 0.25),
                line=dict(color=color, width=2),
            ),
            hovertemplate="<b>%{x}</b><br>" + name + ": %{text}<extra></extra>",
        ))

    fig.update_layout(
        **PLOTLY_THEME,
        title=dict(text="Posição por Skill  (barra maior = melhor rank)", font=dict(color=CLR["cyan"], size=13)),
        barmode="group",
        bargap=0.25,
        bargroupgap=0.08,
        xaxis=dict(showgrid=False, tickfont=dict(size=12)),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.05)",
            tickvals=list(range(0, 52, 10)),
            ticktext=[str(51-v) if v > 0 else "" for v in range(0, 52, 10)],
            title="Posição no ranking",
            title_font=dict(color=CLR["muted"]),
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=CLR["text"])),
        height=380,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id="chart-radar")


def chart_gap(df_latest: pd.DataFrame, name: str, rt: str) -> str:
    sub = df_latest[df_latest["ranking_type"] == rt].sort_values("rank")
    if sub.empty:
        return ""
    target = sub[sub["name"].str.lower() == name.lower()]
    if target.empty:
        return ""

    rk = int(target.iloc[0]["rank"])
    # Pegar 3 acima e 3 abaixo
    window = sub[(sub["rank"] >= max(1, rk-3)) & (sub["rank"] <= rk+3)].copy()
    window["is_target"] = window["name"].str.lower() == name.lower()

    colors = [CLR["cyan"] if t else "rgba(255,255,255,0.12)" for t in window["is_target"]]
    border = [2 if t else 0 for t in window["is_target"]]

    fig = go.Figure(go.Bar(
        x=window["experience"],
        y=window.apply(lambda r: f"#{int(r['rank'])} {r['name']}", axis=1),
        orientation="h",
        marker=dict(color=colors, line=dict(color=CLR["cyan"], width=border)),
        text=window["experience"].apply(fmt_xp),
        textposition="outside",
        textfont=dict(color=CLR["text"], size=11),
        hovertemplate="<b>%{y}</b><br>XP: %{x:,}<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_THEME,
        title=dict(text=f"Gap Competitivo — {rt}", font=dict(color=CLR[rt], size=13)),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        height=260,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def chart_evolution(df: pd.DataFrame, name: str, rt: str) -> str:
    """Dois gráficos empilhados: XP acumulado em cima, posição no ranking embaixo."""
    sub = df[(df["name"].str.lower() == name.lower()) & (df["ranking_type"] == rt)].sort_values("collected_at")
    if len(sub) < 2:
        return ""

    color = CLR[rt]
    dates = sub["collected_at"].tolist()
    xp_vals = sub["experience"].tolist()
    rank_vals = sub["rank"].tolist()

    # XP delta entre snapshots
    xp_delta = [0] + [xp_vals[i] - xp_vals[i-1] for i in range(1, len(xp_vals))]
    hover_xp = [
        f"<b>{d}</b><br>XP: {fmt_xp(x)}<br>Ganho: {'+' if dx>=0 else ''}{fmt_xp(dx)}"
        for d, x, dx in zip(dates, xp_vals, xp_delta)
    ]
    hover_rank = [f"<b>{d}</b><br>Posição: #{r}" for d, r in zip(dates, rank_vals)]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.4],
        vertical_spacing=0.08,
        subplot_titles=["XP Acumulado", "Posição no Ranking"],
    )

    # XP — área preenchida
    fig.add_trace(go.Scatter(
        x=dates, y=xp_vals,
        mode="lines+markers",
        line=dict(color=color, width=2.5),
        marker=dict(size=7, color=color, line=dict(color=CLR["bg"], width=1.5)),
        fill="tozeroy",
        fillcolor=hex_to_rgba(color, 0.12),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_xp,
        showlegend=False,
    ), row=1, col=1)

    # Rank — linha com marcadores, eixo invertido
    fig.add_trace(go.Scatter(
        x=dates, y=rank_vals,
        mode="lines+markers",
        line=dict(color=CLR["yellow"], width=2),
        marker=dict(size=8, color=CLR["yellow"], symbol="diamond", line=dict(color=CLR["bg"], width=1.5)),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_rank,
        showlegend=False,
    ), row=2, col=1)

    fig.update_yaxes(
        title_text="XP Total", title_font=dict(color=color, size=11),
        gridcolor="rgba(255,255,255,0.05)", row=1, col=1,
    )
    fig.update_yaxes(
        title_text="Posição", title_font=dict(color=CLR["yellow"], size=11),
        autorange="reversed",
        gridcolor="rgba(255,255,255,0.05)",
        tickformat="d",
        row=2, col=1,
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(size=10))

    # Ajustar títulos dos subplots
    fig.layout.annotations[0].font.color = color
    fig.layout.annotations[0].font.size = 12
    fig.layout.annotations[1].font.color = CLR["yellow"]
    fig.layout.annotations[1].font.size = 12

    fig.update_layout(
        **PLOTLY_THEME,
        title=dict(text=f"Evolução — {rt}", font=dict(color=color, size=14)),
        height=420,
        hovermode="x unified",
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def chart_velocity(df_latest: pd.DataFrame, df_prev: pd.DataFrame, rt: str) -> str:
    if df_prev.empty:
        return ""
    now = df_latest[df_latest["ranking_type"] == rt].set_index("player_id")
    old = df_prev[df_prev["ranking_type"] == rt].set_index("player_id")
    comuns = now.index.intersection(old.index)
    if len(comuns) == 0:
        return ""
    vel = pd.DataFrame({
        "name": now.loc[comuns, "name"],
        "xp_day": (now.loc[comuns, "experience"] - old.loc[comuns, "experience"]).astype(int),
        "rank": now.loc[comuns, "rank"].astype(int),
    }).sort_values("xp_day", ascending=False).head(15)

    fig = go.Figure(go.Bar(
        x=vel["xp_day"],
        y=vel.apply(lambda r: f"#{r['rank']} {r['name']}", axis=1),
        orientation="h",
        marker=dict(
            color=vel["xp_day"],
            colorscale=[[0,"rgba(100,10,10,0.7)"],[0.5,"rgba(196,18,18,0.6)"],[1,"rgba(212,175,55,0.85)"]],
            showscale=False,
        ),
        text=vel["xp_day"].apply(fmt_xp),
        textposition="outside",
        textfont=dict(color=CLR["text"], size=10),
    ))
    fig.update_layout(
        **PLOTLY_THEME,
        title=dict(text=f"Velocidade de Farm — {rt}", font=dict(color=CLR[rt], size=13)),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
        height=420,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def chart_rank_history(df: pd.DataFrame, names: list) -> str:
    if df["collected_at"].nunique() < 2:
        return ""
    figs = []
    colors = [CLR["cyan"], CLR["pink"], CLR["green"], CLR["yellow"]]
    fig = go.Figure()
    for i, (name, rt) in enumerate([(n, r) for n in names for r in ["Melee","Shielding","Magic","Distance","Taming","Experience"]]):
        sub = df[(df["name"].str.lower()==name.lower()) & (df["ranking_type"]==rt)].sort_values("collected_at")
        if sub.empty or len(sub) < 2: continue
        fig.add_trace(go.Scatter(
            x=sub["collected_at"], y=sub["rank"],
            name=f"{name} — {rt}",
            line=dict(color=colors[i % len(colors)], width=2),
            mode="lines+markers",
        ))
    if not fig.data:
        return ""
    fig.update_yaxes(autorange="reversed", title_text="Posição no Ranking")
    fig.update_layout(
        **PLOTLY_THEME,
        title=dict(text="Histórico de Posições — Jogadores Monitorados", font=dict(color=CLR["cyan"], size=13)),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=380,
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


# ── html builders ──────────────────────────────────────────────────────────
def build_player_card(name: str, df_latest: pd.DataFrame, df_prev: pd.DataFrame) -> str:
    rows = player_snapshot(df_latest, name)
    if rows.empty:
        return f"""
        <div class="player-card player-card--absent">
          <div class="pc-header"><span class="pc-name">{name}</span></div>
          <p class="pc-absent-msg">Fora do top 50 em todos os rankings hoje.</p>
        </div>"""

    skills_html = ""
    for _, r in rows.sort_values("rank").iterrows():
        rt   = r["ranking_type"]
        clr  = CLR.get(rt, CLR["cyan"])
        icon = SKILL_ICONS.get(rt, "")

        xp_d, rk_d, _ = xp_delta(df_latest, df_prev, name, rt) if not df_prev.empty else (None, None, None)
        days_n = None
        if not df_prev.empty and xp_d and xp_d > 0:
            sub_near = df_latest[(df_latest["ranking_type"]==rt) & (df_latest["rank"] == max(1, int(r["rank"])-1))]
            if not sub_near.empty:
                gap = int(sub_near.iloc[0]["experience"]) - int(r["experience"])
                days_n = round(gap / xp_d, 1) if xp_d > 0 else None

        projection = ""
        if days_n is not None and days_n > 0:
            target_name = df_latest[(df_latest["ranking_type"]==rt) & (df_latest["rank"] == max(1, int(r["rank"])-1))].iloc[0]["name"]
            projection = f'<span class="proj">Ultrapassa <b>{target_name}</b> em ~{days_n}d</span>'

        skills_html += f"""
        <div class="skill-row" style="--skill-clr:{clr}">
          <span class="skill-icon" style="color:{clr}">{icon}</span>
          <span class="skill-name">{rt}</span>
          <span class="skill-rank">#{int(r['rank'])}</span>
          <span class="skill-lv">Lv {int(r['level'])}</span>
          <span class="skill-xp">{fmt_xp(r['experience'])}</span>
          <span class="skill-delta">{fmt_delta(xp_d)}</span>
          <span class="skill-rank-delta">{fmt_rank_delta(rk_d)}</span>
          {projection}
        </div>"""

    presence = len(rows)
    best_rank = int(rows["rank"].min())

    safe_name = name.replace('"', '&quot;')
    return f"""
    <div class="player-card" data-player="{safe_name}" onclick="openPlayerDrawer('{safe_name}')">
      <div class="pc-header">
        <span class="pc-name">{name}</span>
        <div class="pc-badges">
          <span class="badge badge--blue">{presence} rankings</span>
          <span class="badge badge--gold"><img class="skull-badge" src="https://redskull.space/images/red-skull-logo.webp" alt=""> #{best_rank}</span>
        </div>
      </div>
      <div class="skill-list">{skills_html}</div>
    </div>"""


def build_ranking_table(df_latest: pd.DataFrame, df_prev: pd.DataFrame, rt: str, watched: list) -> str:
    sub = df_latest[df_latest["ranking_type"] == rt].sort_values("rank")
    clr = CLR.get(rt, CLR["gold"])
    icon = SKILL_ICONS.get(rt, "")
    rows_html = ""
    for _, r in sub.iterrows():
        is_watched = any(r["name"].lower() == w.lower() for w in watched)
        xp_d, rk_d, _ = xp_delta(df_latest, df_prev, r["name"], rt) if not df_prev.empty else (None, None, None)
        hl = ' class="tr-highlight"' if is_watched else ""
        badge = f'<img class="skull-badge" src="https://redskull.space/images/red-skull-logo.webp" alt="" title="Monitorado">' if is_watched else ""
        rk = int(r["rank"])
        rk_class = "td-rank top1" if rk == 1 else ("td-rank top3" if rk <= 3 else "td-rank")
        safe_name = r["name"].replace('"', '&quot;')
        rows_html += f"""<tr{hl} data-player="{safe_name}" onclick="openPlayerDrawer('{safe_name}')">
          <td class="{rk_class}">#{rk}</td>
          <td class="td-name">{r['name']}{badge}</td>
          <td class="td-num">Lv {int(r['level'])}</td>
          <td class="td-num">{fmt_xp(r['experience'])}</td>
          <td class="td-delta">{fmt_delta(xp_d)}</td>
          <td class="td-delta">{fmt_rank_delta(rk_d)}</td>
        </tr>"""

    return f"""
    <div class="rank-table-wrap" id="tab-{rt.lower()}">
      <div class="rank-table-header" style="--rt-clr:{clr}">
        <span style="color:{clr}">{icon} {rt}</span>
        <span class="rt-count">{len(sub)} jogadores</span>
      </div>
      <table class="rank-table">
        <thead><tr>
          <th>Rank</th><th>Nome</th><th>Level</th><th>XP Total</th>
          <th>XP +/-</th><th>Pos +/-</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>"""


def build_players_data(df: pd.DataFrame, df_lat: pd.DataFrame, df_prv: pd.DataFrame) -> dict:
    """Gera JSON com dados completos de cada jogador para o drawer interativo."""
    data = {}
    skill_icons_map = {
        "Experience": "★", "Melee": "⚔", "Shielding": "🛡",
        "Magic": "✦", "Distance": "🏹", "Taming": "🐾",
    }

    # Pré-calcula ranking de XP ganho no dia por skill (posição no "velocity farm")
    velocity_rank = {}  # {rt: {player_id: posicao}}
    if not df_prv.empty:
        for rt in df_lat["ranking_type"].unique():
            lat_rt  = df_lat[df_lat["ranking_type"] == rt].set_index("player_id")[["name","experience"]]
            prev_rt = df_prv[df_prv["ranking_type"] == rt].set_index("player_id")[["name","experience"]]
            comuns  = lat_rt.index.intersection(prev_rt.index)
            if len(comuns) == 0:
                continue
            gains = (lat_rt.loc[comuns, "experience"] - prev_rt.loc[comuns, "experience"]).astype(int)
            gains_sorted = gains.sort_values(ascending=False)
            velocity_rank[rt] = {pid: pos+1 for pos, pid in enumerate(gains_sorted.index)}

    for name in df_lat["name"].unique():
        rows_now = df_lat[df_lat["name"].str.lower() == name.lower()]
        if rows_now.empty:
            continue
        # Todos os registros históricos do jogador (snapshots dedupados)
        all_rows = df[df["name"].str.lower() == name.lower()]

        # Rankings atuais + histórico diário de posição
        rankings = []
        for _, r in rows_now.sort_values("rank").iterrows():
            rt = r["ranking_type"]
            xp_d, rk_d, _ = xp_delta(df_lat, df_prv, name, rt) if not df_prv.empty else (None, None, None)

            # Histórico de posição por dia (todos os snapshots dedupados)
            hist_rt = all_rows[all_rows["ranking_type"] == rt].sort_values("collected_at")
            rank_history = []
            for _, hr in hist_rt.iterrows():
                rank_history.append({
                    "date": hr["collected_at"].strftime("%d/%m"),
                    "rank": int(hr["rank"]),
                    "xp":   int(hr["experience"]),
                })

            # Posição no ranking de farm do dia
            pid = r["player_id"]
            farm_pos = velocity_rank.get(rt, {}).get(pid, None)
            total_farm = len(velocity_rank.get(rt, {}))

            rankings.append({
                "type": rt,
                "rank": int(r["rank"]),
                "level": int(r["level"]),
                "xp": int(r["experience"]),
                "xp_delta": int(xp_d) if xp_d is not None else None,
                "rank_delta": int(rk_d) if rk_d is not None else None,
                "farm_pos": farm_pos,
                "farm_total": total_farm,
                "color": CLR.get(rt, CLR["gold"]),
                "icon": skill_icons_map.get(rt, "•"),
                "history": rank_history,
            })
        # Melhor rank histórico
        all_rows = df[df["name"].str.lower() == name.lower()]
        best_rank = int(all_rows["rank"].min()) if not all_rows.empty else None
        best_rt = all_rows.loc[all_rows["rank"].idxmin(), "ranking_type"] if not all_rows.empty else None
        # XP médio diário (Experience)
        xp_exp = all_rows[all_rows["ranking_type"] == "Experience"].sort_values("collected_at")
        avg_xp_day = None
        if len(xp_exp) >= 2:
            total_xp_gain = int(xp_exp.iloc[-1]["experience"]) - int(xp_exp.iloc[0]["experience"])
            days = (xp_exp.iloc[-1]["collected_at"] - xp_exp.iloc[0]["collected_at"]).days or 1
            avg_xp_day = total_xp_gain // days
        data[name] = {
            "name": name,
            "rankings": rankings,
            "best_rank": best_rank,
            "best_rank_type": best_rt,
            "presence": len(rankings),
            "avg_xp_day": avg_xp_day,
            "days_tracked": all_rows["collected_at"].nunique(),
        }
    return data


def build_digest(df_latest, df_prev, watched):
    if df_prev.empty:
        return '<p class="digest-empty">Digest disponível a partir da segunda coleta (amanhã).</p>'
    lines = []
    for name in watched:
        rows = player_snapshot(df_latest, name)
        if rows.empty:
            lines.append(f"<li><b>{name}</b>: fora do top 50.</li>")
            continue
        parts = []
        for _, r in rows.sort_values("rank").iterrows():
            rt = r["ranking_type"]
            xp_d, rk_d, _ = xp_delta(df_latest, df_prev, name, rt)
            if xp_d is None: continue
            rk_str = f"pos {'+' if rk_d and rk_d>0 else ''}{rk_d}" if rk_d else "pos ±0"
            parts.append(f"<span style='color:{CLR[rt]}'>{rt} #{int(r['rank'])} ({rk_str}, {fmt_xp(xp_d)} XP)</span>")
        if parts:
            safe_name = name.replace('"', '&quot;')
            lines.append(f"<li><b onclick=\"openPlayerDrawer('{safe_name}')\">{name}</b>: {' &bull; '.join(parts)}</li>")
    return f"<ul class='digest-list'>{''.join(lines)}</ul>"


# ── main builder ───────────────────────────────────────────────────────────
def build_css() -> str:
    return """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Anton&family=Ubuntu+Condensed&family=Fira+Code:wght@400;500&display=swap');

      :root {
        --bg:           #0a0a0a;
        --bg2:          #141414;
        --bg3:          #1a1a1a;
        --surface:      #111111;
        --card:         #0d0d0d;
        --card-hi:      #1c1c1c;
        --border:       rgba(196,18,18,0.22);
        --border-hi:    rgba(196,18,18,0.55);
        --red:          #c41212;
        --red2:         #8c0000;
        --bright:       #ff3030;
        --gold:         #d4af37;
        --green:        #2ecc71;
        --text:         #e0e0e0;
        --muted:        #777777;
        --radius:       3px;
        --radius-sm:    2px;
        --shadow-sm:    0 2px 8px rgba(0,0,0,0.6);
        --shadow-md:    0 5px 20px rgba(0,0,0,0.8);
        --shadow-lg:    0 10px 40px rgba(0,0,0,0.9);
        --shadow-red:   0 0 20px rgba(196,18,18,0.25);
        --gradient-red: linear-gradient(135deg, #8c0000, #c41212);
      }

      *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

      html, body { min-height: 100vh; }
      body {
        color: var(--text);
        font-family: 'Ubuntu Condensed', 'Roboto Condensed', sans-serif;
        font-size: 14px;
        line-height: 1.6;
        background-color: var(--bg);
        background-image: radial-gradient(ellipse 80% 50% at 50% -5%, rgba(140,0,0,0.12) 0%, transparent 65%);
        overflow-x: hidden;
      }

      /* ── scrollbar ── */
      ::-webkit-scrollbar { width: 6px; height: 6px; }
      ::-webkit-scrollbar-track { background: var(--bg2); }
      ::-webkit-scrollbar-thumb { background: var(--red2); border-radius: 0; }
      ::-webkit-scrollbar-thumb:hover { background: var(--red); }

      /* ── layout ── */
      .page { max-width: 1440px; margin: 0 auto; padding: 0 0 80px; }

      /* ── header ── */
      .header {
        position: sticky; top: 0; z-index: 50;
        display: grid; grid-template-columns: auto 1fr auto; align-items: center;
        gap: 24px;
        padding: 14px 28px;
        background: rgba(8,8,8,0.97);
        border-bottom: 2px solid var(--red2);
        box-shadow: 0 2px 20px rgba(0,0,0,0.8), 0 2px 0 var(--red2);
        margin-bottom: 28px;
      }
      .header-brand { display: flex; align-items: center; gap: 14px; }
      .header-logo {
        display: flex; align-items: center; flex-shrink: 0;
      }
      .header-title {
        font-family: 'Anton', sans-serif;
        font-size: 1.55rem; color: var(--text);
        letter-spacing: 1.5px; text-transform: uppercase;
        text-shadow: 0 0 10px rgba(196,18,18,0.2);
      }
      .header-title .accent { color: var(--red); }
      .header-sub { font-size: 0.72rem; color: var(--muted); margin-top: 1px; letter-spacing: 1px; text-transform: uppercase; }
      .header-meta { text-align: right; font-size: 0.73rem; color: var(--muted); line-height: 1.9; }
      .header-meta strong { color: var(--text); }

      /* ── search bar ── */
      .search-wrap { position: relative; max-width: 480px; width: 100%; }
      .search-input {
        width: 100%;
        padding: 10px 16px 10px 42px;
        background: var(--bg2);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        color: var(--text);
        font-size: 0.88rem;
        font-family: inherit;
        transition: all 0.2s;
      }
      .search-input::placeholder { color: var(--muted); }
      .search-input:focus {
        outline: none;
        border-color: var(--red);
        box-shadow: 0 0 0 2px rgba(196,18,18,0.15), var(--shadow-red);
        background: var(--bg3);
      }
      .search-icon {
        position: absolute; left: 13px; top: 50%; transform: translateY(-50%);
        color: var(--muted); pointer-events: none;
      }
      .search-results {
        position: absolute; top: calc(100% + 4px); left: 0; right: 0;
        background: var(--bg3);
        border: 1px solid var(--border-hi);
        border-radius: var(--radius);
        max-height: 340px; overflow-y: auto;
        box-shadow: var(--shadow-lg), 0 0 20px rgba(196,18,18,0.12);
        z-index: 999;
        display: none;
      }
      .search-results.open { display: block; }
      .search-result-item {
        padding: 10px 16px; cursor: pointer;
        border-bottom: 1px solid var(--border);
        display: flex; justify-content: space-between; align-items: center;
        transition: background 0.15s;
      }
      .search-result-item:last-child { border-bottom: none; }
      .search-result-item:hover, .search-result-item.active { background: rgba(196,18,18,0.07); }
      .search-result-name { font-weight: 600; color: var(--text); }
      .search-result-meta { font-size: 0.72rem; color: var(--muted); }

      /* ── stat bar ── */
      .statbar {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr));
        gap: 12px; margin-bottom: 28px; padding: 0 28px;
      }
      .stat {
        background: var(--card);
        border: 1px solid var(--border);
        border-top: 2px solid var(--red2);
        padding: 16px 18px;
        transition: all 0.2s;
      }
      .stat:hover {
        border-color: var(--red);
        border-top-color: var(--red);
        transform: translateY(-2px);
        box-shadow: var(--shadow-md), 0 0 14px rgba(196,18,18,0.12);
      }
      .stat-label { font-size: 0.62rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-weight: 700; }
      .stat-value { font-family: 'Anton', sans-serif; font-size: 1.55rem; color: var(--text); letter-spacing: 0.5px; }
      .stat-sub { font-size: 0.67rem; color: var(--muted); margin-top: 4px; }

      /* ── section ── */
      .section { margin-bottom: 36px; padding: 0 28px; }
      .section-title {
        font-family: 'Anton', sans-serif;
        font-size: 1.25rem; color: var(--red);
        text-transform: uppercase; letter-spacing: 2px;
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 16px; padding-bottom: 10px;
        border-bottom: 2px solid var(--red2);
        text-shadow: 0 0 10px rgba(196,18,18,0.25);
        position: relative;
      }
      .section-title::after {
        content: ''; position: absolute; bottom: -2px; left: 0;
        width: 50px; height: 2px;
        background: var(--red); box-shadow: 0 0 8px var(--red);
      }
      .section-title svg { color: var(--red); }
      .section-title .st-accent { color: var(--text); }

      /* ── player card ── */
      .player-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(460px,1fr)); gap: 14px; }
      .player-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-left: 3px solid var(--red2);
        padding: 18px 20px;
        cursor: pointer;
        transition: all 0.22s;
        position: relative; overflow: hidden;
      }
      .player-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, var(--red), transparent 70%);
        opacity: 0; transition: opacity 0.25s;
      }
      .player-card:hover {
        border-color: var(--red);
        border-left-color: var(--bright);
        transform: translateY(-2px);
        box-shadow: var(--shadow-md), -3px 0 16px rgba(196,18,18,0.18);
      }
      .player-card:hover::before { opacity: 1; }
      .player-card--absent { opacity: 0.45; cursor: default; }
      .player-card--absent:hover { transform: none; box-shadow: none; }
      .pc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; gap: 12px; }
      .pc-name {
        font-family: 'Anton', sans-serif;
        font-size: 1.2rem; color: var(--red);
        text-transform: uppercase; letter-spacing: 1px;
        text-shadow: 0 0 10px rgba(196,18,18,0.35);
      }
      .pc-badges { display: flex; gap: 6px; flex-wrap: wrap; }
      .pc-absent-msg { color: var(--muted); font-size: 0.83rem; }

      .skill-list { display: flex; flex-direction: column; gap: 5px; }
      .skill-row {
        display: grid;
        grid-template-columns: 20px 90px 52px 52px 80px 90px 70px 1fr;
        align-items: center; gap: 8px;
        padding: 7px 10px;
        background: var(--bg2);
        border: 1px solid rgba(196,18,18,0.1);
        border-left: 2px solid var(--skill-clr);
        transition: all 0.15s;
      }
      .skill-row:hover { background: var(--bg3); border-color: rgba(196,18,18,0.28); border-left-color: var(--skill-clr); }
      .skill-icon { display: flex; align-items: center; }
      .skill-name { font-size: 0.72rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
      .skill-rank { font-family: 'Anton', sans-serif; font-size: 0.95rem; color: var(--skill-clr); }
      .skill-lv   { font-size: 0.7rem; color: var(--muted); }
      .skill-xp   { font-family: 'Fira Code', monospace; font-size: 0.78rem; color: var(--text); }
      .skill-delta, .skill-rank-delta { font-size: 0.72rem; }
      .proj { font-size: 0.67rem; color: var(--gold); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

      /* ── badges ── */
      .badge {
        font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
        padding: 2px 7px; border-radius: 0; letter-spacing: 0.8px;
        display: inline-flex; align-items: center; gap: 4px;
      }
      .badge--gold   { background: rgba(212,175,55,0.1);  color: var(--gold);  border: 1px solid rgba(212,175,55,0.4); }
      .badge--cyan   { background: rgba(196,18,18,0.1);   color: var(--red);   border: 1px solid rgba(196,18,18,0.35); }
      .badge--blue   { background: rgba(196,18,18,0.07);  color: #ff6b6b;      border: 1px solid rgba(196,18,18,0.22); }
      .badge--yellow { background: rgba(212,175,55,0.08); color: var(--gold);  border: 1px solid rgba(212,175,55,0.3); }
      .badge--pink   { background: rgba(255,48,48,0.1);   color: var(--bright);border: 1px solid rgba(255,48,48,0.3); }
      .badge--green  { background: rgba(46,204,113,0.1);  color: #2ecc71;      border: 1px solid rgba(46,204,113,0.3); }

      /* ── delta ── */
      .delta-up   { color: #2ecc71; display: inline-flex; align-items: center; gap: 3px; font-weight: 700; }
      .delta-down { color: var(--bright); display: inline-flex; align-items: center; gap: 3px; font-weight: 700; }
      .delta-neutral { color: var(--muted); display: inline-flex; align-items: center; gap: 3px; }

      /* ── chart grid ── */
      .chart-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
      .chart-grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }
      .chart-box {
        background: var(--card);
        border: 1px solid var(--border);
        border-top: 2px solid var(--red2);
        padding: 8px;
        transition: all 0.2s;
      }
      .chart-box:hover { border-color: var(--red); border-top-color: var(--red); }
      .chart-box--full { grid-column: 1 / -1; }
      .chart-empty {
        display: flex; align-items: center; justify-content: center;
        height: 150px; color: var(--muted); font-size: 0.8rem; text-align: center; padding: 20px;
      }

      /* ── tabs ── */
      .tabs-bar { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 14px; }
      .tab-btn {
        background: var(--card); color: var(--muted);
        border: 1px solid var(--border);
        padding: 7px 16px; cursor: pointer;
        font-family: 'Ubuntu Condensed', sans-serif; font-size: 0.82rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.5px;
        transition: all 0.18s; display: flex; align-items: center; gap: 6px;
        border-radius: 0;
      }
      .tab-btn:hover { border-color: var(--red); color: var(--text); }
      .tab-btn.active { background: var(--gradient-red); border-color: var(--red); color: #fff; box-shadow: 0 4px 12px rgba(196,18,18,0.3); }
      .tab-panel { display: none; }
      .tab-panel.active { display: block; }

      /* ── ranking table ── */
      .rank-table-wrap {
        background: var(--card);
        border: 1px solid var(--border);
        overflow: hidden;
      }
      .rank-table-header {
        display: flex; justify-content: space-between; align-items: center;
        padding: 11px 16px;
        background: linear-gradient(90deg, rgba(140,0,0,0.22) 0%, transparent 100%);
        border-bottom: 1px solid var(--border);
        font-family: 'Anton', sans-serif; font-size: 0.95rem; letter-spacing: 1px;
        text-transform: uppercase;
      }
      .rt-count { font-size: 0.65rem; color: var(--muted); font-weight: 700; font-family: 'Ubuntu Condensed', sans-serif; text-transform: uppercase; letter-spacing: 1px; }
      .rank-table { width: 100%; border-collapse: collapse; }
      .rank-table th {
        padding: 9px 14px; text-align: left; font-size: 0.62rem;
        text-transform: uppercase; letter-spacing: 1.5px; color: var(--muted);
        border-bottom: 1px solid var(--border); font-weight: 700;
        background: var(--bg2);
      }
      .rank-table td { padding: 9px 14px; border-bottom: 1px solid rgba(196,18,18,0.07); vertical-align: middle; }
      .rank-table tr:last-child td { border-bottom: none; }
      .rank-table tbody tr { cursor: pointer; transition: background 0.12s; }
      .rank-table tbody tr:hover td { background: rgba(196,18,18,0.05); }
      .tr-highlight td { background: rgba(196,18,18,0.08) !important; }
      .tr-highlight .td-name { color: var(--red) !important; font-weight: 700; }
      .td-rank { font-family: 'Anton', sans-serif; color: var(--muted); width: 50px; font-size: 1rem; }
      .td-rank.top1 { color: var(--gold); text-shadow: 0 0 8px rgba(212,175,55,0.4); }
      .td-rank.top3 { color: var(--red); }
      .td-name { display: flex; align-items: center; gap: 8px; font-weight: 600; }
      .td-num  { font-family: 'Fira Code', monospace; font-size: 0.79rem; }
      .td-delta { font-size: 0.75rem; }

      /* ── digest ── */
      .digest-box {
        background: var(--card);
        border: 1px solid var(--border);
        border-left: 3px solid var(--red);
        padding: 18px 22px;
        box-shadow: -4px 0 16px rgba(196,18,18,0.08);
      }
      .digest-empty { color: var(--muted); font-size: 0.81rem; }
      .digest-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
      .digest-list li { font-size: 0.85rem; line-height: 1.7; }
      .digest-list b  { color: var(--red); font-weight: 700; cursor: pointer; font-family: 'Anton', sans-serif; font-size: 0.95rem; letter-spacing: 0.5px; }
      .digest-list b:hover { color: var(--bright); text-decoration: underline; }

      /* ── no data placeholder ── */
      .no-data {
        background: var(--card);
        border: 1px dashed var(--border);
        padding: 32px; text-align: center; color: var(--muted); font-size: 0.82rem;
      }
      .no-data strong { display: block; font-family: 'Anton', sans-serif; font-size: 1.1rem; color: var(--text); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }

      /* ── period selector ── */
      .period-bar { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 16px; align-items: center; }
      .period-label { font-size: 0.62rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1.5px; margin-right: 6px; font-weight: 700; }
      .period-btn {
        background: var(--card); color: var(--muted);
        border: 1px solid var(--border);
        padding: 5px 12px; cursor: pointer;
        font-family: inherit; font-size: 0.72rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.5px;
        transition: all 0.18s; border-radius: 0;
      }
      .period-btn:hover { border-color: var(--red); color: var(--text); }
      .period-btn.active { background: var(--gradient-red); border-color: var(--red); color: #fff; }

      /* ── DRAWER ── */
      .drawer-backdrop {
        position: fixed; inset: 0; background: rgba(0,0,0,0.78);
        opacity: 0; pointer-events: none; transition: opacity 0.28s; z-index: 200;
      }
      .drawer-backdrop.open { opacity: 1; pointer-events: auto; }
      .drawer {
        position: fixed; top: 0; right: 0; bottom: 0;
        width: min(860px,100%);
        background: #0a0a0a;
        border-left: 2px solid var(--red2);
        box-shadow: -12px 0 40px rgba(0,0,0,0.9), -2px 0 20px rgba(196,18,18,0.12);
        transform: translateX(100%); transition: transform 0.32s cubic-bezier(0.4,0,0.2,1);
        z-index: 201; display: flex; flex-direction: column; overflow: hidden;
      }
      .drawer.open { transform: translateX(0); }
      .drawer-header {
        padding: 18px 24px 14px;
        border-bottom: 2px solid var(--red2);
        background: linear-gradient(135deg, rgba(140,0,0,0.18) 0%, transparent 60%);
        position: relative; flex-shrink: 0;
      }
      .drawer-close {
        position: absolute; top: 16px; right: 16px;
        width: 34px; height: 34px;
        background: rgba(196,18,18,0.08); border: 1px solid var(--border);
        color: var(--muted); cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        transition: all 0.18s; font-size: 18px; line-height: 1; border-radius: 0;
      }
      .drawer-close:hover { background: rgba(196,18,18,0.22); border-color: var(--red); color: var(--bright); }
      .drawer-name {
        font-family: 'Anton', sans-serif;
        font-size: 2rem; letter-spacing: 2px; text-transform: uppercase;
        color: var(--red); text-shadow: 0 0 16px rgba(196,18,18,0.45);
        margin-bottom: 4px;
      }
      .drawer-sub { color: var(--muted); font-size: 0.74rem; text-transform: uppercase; letter-spacing: 1.2px; }
      .drawer-body { padding: 16px 24px 24px; overflow-y: auto; flex: 1; }
      .drawer-section { margin-bottom: 18px; }
      .drawer-section-title {
        font-family: 'Anton', sans-serif;
        font-size: 0.72rem; text-transform: uppercase; letter-spacing: 2px;
        color: var(--red); font-weight: 400; margin-bottom: 10px;
        padding-bottom: 6px; border-bottom: 1px solid var(--border);
      }
      .drawer-stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 8px; }
      .drawer-stat {
        background: var(--bg2);
        border: 1px solid var(--border);
        border-top: 2px solid var(--red2);
        padding: 10px 12px;
      }
      .drawer-stat-label { font-size: 0.58rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }
      .drawer-stat-value { font-family: 'Anton', sans-serif; font-size: 1.3rem; color: var(--text); margin-top: 3px; letter-spacing: 0.5px; }
      .drawer-stat-value.gold { color: var(--gold); text-shadow: 0 0 8px rgba(212,175,55,0.25); }
      .drawer-stat-sub { font-size: 0.64rem; color: var(--muted); margin-top: 1px; }

      .drawer-skill-list { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
      .drawer-skill {
        padding: 12px 14px;
        background: var(--bg2);
        border: 1px solid rgba(196,18,18,0.14);
        border-left: 3px solid var(--skill-clr);
      }
      .drawer-skill-top { display: grid; grid-template-columns: auto 1fr auto; gap: 10px; align-items: center; }
      .drawer-skill-icon { color: var(--skill-clr); font-size: 18px; display: flex; }
      .drawer-skill-info .name { font-family: 'Anton', sans-serif; font-size: 0.95rem; color: var(--skill-clr); text-transform: uppercase; letter-spacing: 0.5px; }
      .drawer-skill-info .meta { font-size: 0.68rem; color: var(--muted); margin-top: 1px; }
      .drawer-skill-rank {
        font-family: 'Anton', sans-serif;
        font-size: 1.9rem; color: var(--skill-clr);
        text-shadow: 0 0 10px var(--skill-clr);
        line-height: 1;
      }
      .drawer-skill-gain {
        display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;
        margin-top: 10px; padding-top: 10px;
        border-top: 1px solid rgba(196,18,18,0.14);
      }
      .drawer-skill-gain-cell { display: flex; flex-direction: column; gap: 2px; }
      .drawer-skill-gain-label { font-size: 0.57rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }
      .drawer-skill-gain-value { font-family: 'Fira Code', monospace; font-size: 0.88rem; font-weight: 700; }
      .drawer-skill-gain-value.up   { color: #2ecc71; }
      .drawer-skill-gain-value.down { color: var(--bright); }
      .drawer-skill-gain-value.flat { color: var(--muted); }


      /* clickable name */
      .clickable-name { cursor: pointer; transition: color 0.15s; }
      .clickable-name:hover { color: var(--red); }

      /* ── responsive ── */
      @media (max-width: 900px) {
        .chart-grid-2, .chart-grid-3 { grid-template-columns: 1fr; }
        .player-grid { grid-template-columns: 1fr; }
        .skill-row { grid-template-columns: 20px 80px 48px 80px 1fr; }
        .skill-lv, .skill-rank-delta { display: none; }
        .header { grid-template-columns: 1fr; gap: 12px; padding: 12px 16px; }
        .header-meta { display: none; }
        .section, .statbar { padding: 0 16px; }
      }
      @media (max-width: 600px) {
        .statbar { grid-template-columns: repeat(2,1fr); }
        .drawer-stats { grid-template-columns: repeat(2,1fr); }
        .drawer-skill-list { grid-template-columns: 1fr; }
      }

      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { transition: none !important; animation: none !important; }
      }

      /* ── preloader ── */
      #preloader {
        position: fixed; inset: 0; background: #0a0a0a;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        z-index: 9999; transition: opacity 0.5s ease, visibility 0.5s ease;
      }
      #preloader.hidden { opacity: 0; visibility: hidden; pointer-events: none; }
      .skull-loader-img {
        width: 110px; height: auto;
        animation: skulPulse 1.4s ease-in-out infinite alternate;
        filter: drop-shadow(0 0 18px rgba(196,18,18,0.7));
      }
      .skull-loader-text {
        margin-top: 22px;
        font-family: 'Anton', sans-serif;
        font-size: 1.1rem; color: var(--red);
        letter-spacing: 3px; text-transform: uppercase;
        text-shadow: 0 0 12px rgba(196,18,18,0.5);
        animation: skulFade 1.4s ease-in-out infinite alternate;
      }
      .skull-loader-bar {
        margin-top: 18px; width: 180px; height: 2px;
        background: rgba(196,18,18,0.15); overflow: hidden;
      }
      .skull-loader-bar::after {
        content: ''; display: block; height: 100%;
        background: var(--gradient-red);
        animation: skulBar 1.6s ease-in-out infinite;
        box-shadow: 0 0 8px var(--red);
      }
      @keyframes skulPulse {
        from { transform: scale(1);    filter: drop-shadow(0 0 12px rgba(196,18,18,0.5)); }
        to   { transform: scale(1.06); filter: drop-shadow(0 0 24px rgba(196,18,18,0.9)); }
      }
      @keyframes skulFade {
        from { opacity: 0.5; } to { opacity: 1; }
      }
      @keyframes skulBar {
        0%   { transform: translateX(-100%); }
        100% { transform: translateX(400%); }
      }

      /* ── header logo img ── */
      .header-logo-img {
        width: 72px; height: 72px; object-fit: contain;
        filter: drop-shadow(0 0 10px rgba(196,18,18,0.6));
        animation: logoGlow 3s ease-in-out infinite alternate;
      }
      @keyframes logoGlow {
        from { filter: drop-shadow(0 0 6px rgba(196,18,18,0.4)); }
        to   { filter: drop-shadow(0 0 18px rgba(196,18,18,0.85)); }
      }
      /* ── skull badge (jogadores monitorados) ── */
      .skull-badge { width: 16px; height: 16px; object-fit: contain; filter: drop-shadow(0 0 3px rgba(196,18,18,0.7)); vertical-align: middle; }
    </style>"""


def build_html(
    cfg, df, df_lat, df_prv,
    watched, ultima_coleta, dias_coletando, total_jogadores, total_registros,
) -> str:

    players_data = build_players_data(df, df_lat, df_prv)
    players_json = json.dumps(players_data, ensure_ascii=False)

    # ── statbar ──
    total_snapshots = df["collected_at"].nunique()
    statbar = f"""
    <div class="statbar">
      <div class="stat"><div class="stat-label">Servidor</div><div class="stat-value" style="font-size:1rem">{cfg['server']['name']}</div></div>
      <div class="stat"><div class="stat-label">Dias coletando</div><div class="stat-value">{dias_coletando}</div><div class="stat-sub">dia(s) com dados</div></div>
      <div class="stat"><div class="stat-label">Jogadores únicos</div><div class="stat-value">{total_jogadores}</div><div class="stat-sub">já monitorados</div></div>
      <div class="stat"><div class="stat-label">Registros totais</div><div class="stat-value">{fmt_xp(total_registros)}</div><div class="stat-sub">no banco</div></div>
      <div class="stat"><div class="stat-label">Última coleta</div><div class="stat-value" style="font-size:0.85rem">{ultima_coleta}</div></div>
    </div>"""

    # ── digest ──
    digest = build_digest(df_lat, df_prv, watched)

    # ── player cards ──
    cards = "".join(build_player_card(n, df_lat, df_prv) for n in watched)

    # ── radar ──
    radar_html = chart_radar(df_lat, watched) if watched else ""

    # ── competitive gap ──
    gap_blocks = ""
    for name in watched:
        for rt in ["Melee","Shielding","Magic","Distance","Taming","Experience"]:
            g = chart_gap(df_lat, name, rt)
            if g: gap_blocks += f'<div class="chart-box">{g}</div>'

    # ── velocity ──
    vel_tabs_btns = ""
    vel_tabs_panels = ""
    for i, rt in enumerate(cfg["ranking_types"]):
        active = "active" if i == 0 else ""
        clr = CLR.get(rt, CLR["cyan"])
        icon = SKILL_ICONS.get(rt, "")
        vel_tabs_btns += f'<button class="tab-btn {active}" onclick="switchTab(\'vel\',\'{rt}\')" id="vel-btn-{rt}">{icon} {rt}</button>'
        vchart = chart_velocity(df_lat, df_prv, rt)
        content = vchart if vchart else '<div class="chart-empty">Disponível a partir da segunda coleta.</div>'
        vel_tabs_panels += f'<div class="tab-panel {active}" id="vel-panel-{rt}">{content}</div>'

    # ── evolution (multi-day) ──
    evo_html = ""
    if df["collected_at"].nunique() >= 2:
        evo_parts = []
        for name in watched:
            for rt in cfg["ranking_types"]:
                e = chart_evolution(df, name, rt)
                if e:
                    evo_parts.append(f'<div class="chart-box evo-chart-box">{e}</div>')
        if evo_parts:
            evo_html = f'<div class="chart-grid-2">{"".join(evo_parts)}</div>'

    hist_html = chart_rank_history(df, watched) or ""

    # ── ranking tables ──
    rt_tabs_btns = ""
    rt_tabs_panels = ""
    for i, rt in enumerate(cfg["ranking_types"]):
        active = "active" if i == 0 else ""
        clr = CLR.get(rt, CLR["cyan"])
        icon = SKILL_ICONS.get(rt, "")
        rt_tabs_btns += f'<button class="tab-btn {active}" style="{"border-color:"+clr+";color:"+clr if active else ""}" onclick="switchTab(\'rt\',\'{rt}\',this)" id="rt-btn-{rt}">{icon} {rt}</button>'
        tbl = build_ranking_table(df_lat, df_prv, rt, watched)
        rt_tabs_panels += f'<div class="tab-panel {active}" id="rt-panel-{rt}">{tbl}</div>'

    no_evo = "" if df["collected_at"].nunique() >= 2 else """
    <div class="no-data">
      <strong>Evolução temporal</strong>
      Os gráficos de evolução, velocidade e histórico ficam completos a partir da segunda coleta (amanhã às 00:00).
    </div>"""

    PWD_HASH = "10a74986775735e7d7873450b8f8e01998d23383cb9e49d52f4f899d657b9ff0"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow">
  <title>GrindHero Monitor — {cfg['server']['name']}</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  {build_css()}
  <style>
    #rs-gate {{
      position:fixed; inset:0; z-index:99999;
      background:#0a0a0a;
      display:flex; flex-direction:column;
      align-items:center; justify-content:center;
      gap:28px;
    }}
    #rs-gate.hidden {{ display:none; }}
    .rs-gate-logo {{
      width:130px; height:130px; object-fit:contain;
      filter: drop-shadow(0 0 18px rgba(196,18,18,0.7));
      animation: gateGlow 2.5s ease-in-out infinite alternate;
    }}
    @keyframes gateGlow {{
      from {{ filter: drop-shadow(0 0 10px rgba(196,18,18,0.5)); }}
      to   {{ filter: drop-shadow(0 0 28px rgba(196,18,18,0.95)); }}
    }}
    .rs-gate-title {{
      font-family: 'Anton', sans-serif;
      font-size: 1.5rem; letter-spacing: 4px;
      color: #c41212; text-transform: uppercase;
      text-shadow: 0 0 12px rgba(196,18,18,0.6);
    }}
    .rs-gate-form {{
      display:flex; flex-direction:column; align-items:center; gap:14px;
      width: 100%; max-width: 320px;
    }}
    .rs-gate-input {{
      width:100%; padding:12px 16px;
      background:#1a1a1a; border:1px solid #3a0a0a;
      border-radius:3px; color:#e0e0e0;
      font-family:'Ubuntu Condensed',sans-serif; font-size:1rem;
      letter-spacing:3px; text-align:center;
      outline:none; transition: border-color .2s, box-shadow .2s;
    }}
    .rs-gate-input:focus {{
      border-color:#c41212;
      box-shadow: 0 0 10px rgba(196,18,18,0.3);
    }}
    .rs-gate-btn {{
      width:100%; padding:12px;
      background:#c41212; border:none; border-radius:3px;
      color:#fff; font-family:'Anton',sans-serif;
      font-size:1rem; letter-spacing:3px; text-transform:uppercase;
      cursor:pointer; transition: background .2s, box-shadow .2s;
    }}
    .rs-gate-btn:hover {{
      background:#e01515;
      box-shadow: 0 0 16px rgba(196,18,18,0.5);
    }}
    .rs-gate-error {{
      color:#e74c3c; font-size:0.85rem;
      font-family:'Ubuntu Condensed',sans-serif;
      letter-spacing:1px; min-height:18px;
    }}
  </style>
  <script>
    (function(){{
      const HASH = "{PWD_HASH}";
      const KEY  = "rs_auth_v1";
      if(sessionStorage.getItem(KEY) === HASH) {{
        document.addEventListener('DOMContentLoaded', function(){{
          var g = document.getElementById('rs-gate');
          if(g) g.classList.add('hidden');
        }});
      }}
    }})();
  </script>
</head>
<body>

<!-- PASSWORD GATE -->
<div id="rs-gate">
  <img class="rs-gate-logo"
       src="https://redskull.space/images/red-skull-logo.webp"
       alt="RED SKULL"
       onerror="this.style.display='none'">
  <div class="rs-gate-title">Red Skull Monitor</div>
  <form class="rs-gate-form" id="rs-gate-form" onsubmit="return rsCheckPwd(event)">
    <input class="rs-gate-input" id="rs-pwd" type="password"
           placeholder="••••••••••••" autocomplete="off" autofocus>
    <div class="rs-gate-error" id="rs-err"></div>
    <button class="rs-gate-btn" type="submit">Entrar</button>
  </form>
</div>

<script>
async function rsCheckPwd(e) {{
  e.preventDefault();
  const pwd   = document.getElementById('rs-pwd').value;
  const err   = document.getElementById('rs-err');
  const HASH  = "{PWD_HASH}";
  const enc   = new TextEncoder().encode(pwd);
  const buf   = await crypto.subtle.digest('SHA-256', enc);
  const hex   = Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
  if(hex === HASH) {{
    sessionStorage.setItem('rs_auth_v1', HASH);
    document.getElementById('rs-gate').classList.add('hidden');
    err.textContent = '';
  }} else {{
    err.textContent = 'Senha incorreta.';
    document.getElementById('rs-pwd').value = '';
    document.getElementById('rs-pwd').focus();
  }}
  return false;
}}
</script>

<!-- PRELOADER -->
<div id="preloader">
  <img class="skull-loader-img" src="https://redskull.space/images/red-skull-logo.webp" alt="RED SKULL" onerror="this.style.display='none'">
  <div class="skull-loader-text">Carregando dados...</div>
  <div class="skull-loader-bar"></div>
</div>

<div class="page">

  <!-- HEADER -->
  <header class="header">
    <div class="header-brand">
      <div class="header-logo">
        <img class="header-logo-img" src="https://redskull.space/images/red-skull-logo.webp" alt="RED SKULL" onerror="this.outerHTML='GH'">
      </div>
      <div>
        <div class="header-title"><span class="accent">GrindHero</span> Monitor</div>
        <div class="header-sub">&#9876; Ranking PvP &mdash; {cfg['server']['name']}</div>
      </div>
    </div>
    <div class="search-wrap">
      <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input id="player-search" class="search-input" placeholder="Buscar qualquer jogador..." autocomplete="off" />
      <div id="search-results" class="search-results"></div>
    </div>
    <div class="header-meta">
      <div>Última coleta: <strong>{ultima_coleta}</strong></div>
      <div>Dashboard: <strong>{datetime.now().strftime('%d/%m/%Y %H:%M')}</strong></div>
      <div>Monitorando: <strong>{', '.join(watched)}</strong></div>
    </div>
  </header>

  <!-- STAT BAR -->
  {statbar}

  <!-- DIGEST -->
  <section class="section">
    <div class="section-title">{svg_zap()} <span class="st-accent">Resumo do Dia</span></div>
    <div class="digest-box">{digest}</div>
  </section>

  <!-- WATCHED PLAYERS -->
  <section class="section">
    <div class="section-title">{svg_users()} <span class="st-accent">Jogadores Monitorados</span></div>
    <div class="player-grid">{cards}</div>
  </section>

  <!-- COMPETITIVE ANALYSIS -->
  <section class="section">
    <div class="section-title">{svg_sword()} <span class="st-accent">Análise Competitiva</span> <span style="color:var(--muted);font-size:0.75rem">&mdash; Gap para os vizinhos de rank</span></div>
    <div class="chart-grid-2">{gap_blocks if gap_blocks else '<div class="chart-empty">Sem dados de jogadores monitorados no top 50.</div>'}</div>
  </section>

  <!-- RADAR -->
  <section class="section">
    <div class="section-title">{svg_star()} <span class="st-accent">Perfil de Skills</span></div>
    <div class="chart-grid-2">
      <div class="chart-box chart-box--full">{radar_html if radar_html else '<div class="chart-empty">Nenhum jogador monitorado encontrado nos rankings.</div>'}</div>
    </div>
  </section>

  <!-- VELOCITY -->
  <section class="section">
    <div class="section-title">{svg_zap()} <span class="st-accent">Velocidade de Farm</span> <span style="color:var(--muted);font-size:0.75rem">&mdash; XP ganho desde a coleta anterior</span></div>
    <div class="tabs-bar" id="vel-tabs">{vel_tabs_btns}</div>
    {vel_tabs_panels}
  </section>

  <!-- EVOLUTION (multi-day) -->
  <section class="section">
    <div class="section-title">{svg_activity()} <span class="st-accent">Evolução Temporal</span></div>
    <div class="period-bar">
      <span class="period-label">Período:</span>
      <button class="period-btn" onclick="setEvoPeriod(1,this)">24h</button>
      <button class="period-btn" onclick="setEvoPeriod(7,this)">7d</button>
      <button class="period-btn" onclick="setEvoPeriod(15,this)">15d</button>
      <button class="period-btn" onclick="setEvoPeriod(30,this)">30d</button>
      <button class="period-btn" onclick="setEvoPeriod(90,this)">3 meses</button>
      <button class="period-btn" onclick="setEvoPeriod(180,this)">6 meses</button>
      <button class="period-btn" onclick="setEvoPeriod(365,this)">1 ano</button>
      <button class="period-btn active" onclick="setEvoPeriod(0,this)">Tudo</button>
    </div>
    {('<div id="evo-charts">' + evo_html + '</div>' + ('<div class="chart-box chart-box--full evo-chart-box">' + hist_html + '</div>' if hist_html else "")) if df["collected_at"].nunique() >= 2 else no_evo}
  </section>

  <!-- RANKINGS -->
  <section class="section">
    <div class="section-title">{svg_trophy()} <span class="st-accent">Rankings Completos</span> <span style="color:var(--muted);font-size:0.75rem">&mdash; Top 50 por tipo</span></div>
    <div class="tabs-bar">{rt_tabs_btns}</div>
    {rt_tabs_panels}
  </section>

  <p style="text-align:center;color:var(--muted);font-size:0.7rem;margin-top:24px;padding-bottom:24px;letter-spacing:1px;text-transform:uppercase;border-top:1px solid var(--border);padding-top:20px;margin:0 28px">
    GrindHero Monitor &bull; Dados coletados de grindhero.online &bull; Endora (PvP) &bull; Atualizado 4x/dia
  </p>

</div>

<!-- DRAWER (player detail) -->
<div id="drawer-backdrop" class="drawer-backdrop" onclick="closePlayerDrawer()"></div>
<aside id="drawer" class="drawer" role="dialog" aria-modal="true">
  <div class="drawer-header">
    <button class="drawer-close" onclick="closePlayerDrawer()" aria-label="Fechar">×</button>
    <div id="drawer-name" class="drawer-name">—</div>
    <div id="drawer-sub" class="drawer-sub">—</div>
  </div>
  <div id="drawer-body" class="drawer-body"></div>
</aside>

<script>
  // ── dados dos jogadores ──
  const PLAYERS = {players_json};

  // ── helpers ──
  function fmtXP(v) {{
    if (v == null) return '—';
    const a = Math.abs(v);
    if (a >= 1e6) return (v/1e6).toFixed(2) + 'M';
    if (a >= 1e3) return (v/1e3).toFixed(1) + 'K';
    return String(v);
  }}
  function fmtDelta(v) {{
    if (v == null || v === 0) return '<span class="delta-neutral">—</span>';
    const cls = v > 0 ? 'delta-up' : 'delta-down';
    const sign = v > 0 ? '+' : '';
    const arrow = v > 0 ? '▲' : '▼';
    return `<span class="${{cls}}">${{arrow}} ${{sign}}${{fmtXP(v)}}</span>`;
  }}
  function fmtRankDelta(v) {{
    if (v == null || v === 0) return '<span class="delta-neutral">—</span>';
    const cls = v > 0 ? 'delta-up' : 'delta-down';
    const sign = v > 0 ? '+' : '';
    const arrow = v > 0 ? '▲' : '▼';
    return `<span class="${{cls}}">${{arrow}} ${{sign}}${{v}}</span>`;
  }}

  // ── drawer ──
  function openPlayerDrawer(name) {{
    if (!name) return;
    const data = PLAYERS[name] || Object.values(PLAYERS).find(p => p.name.toLowerCase() === name.toLowerCase());
    if (!data) return;
    document.getElementById('drawer-name').textContent = data.name;
    document.getElementById('drawer-sub').textContent =
      `Em ${{data.presence}} ranking(s) · Acompanhado há ${{data.days_tracked}} dia(s)`;

    let stats = '';
    if (data.best_rank != null) stats += `
      <div class="drawer-stat">
        <div class="drawer-stat-label">Melhor Posição</div>
        <div class="drawer-stat-value gold">#${{data.best_rank}}</div>
        <div class="drawer-stat-sub">em ${{data.best_rank_type || ''}}</div>
      </div>`;
    if (data.avg_xp_day != null) stats += `
      <div class="drawer-stat">
        <div class="drawer-stat-label">XP médio / dia</div>
        <div class="drawer-stat-value">${{fmtXP(data.avg_xp_day)}}</div>
        <div class="drawer-stat-sub">Experience</div>
      </div>`;
    stats += `
      <div class="drawer-stat">
        <div class="drawer-stat-label">Rankings ativos</div>
        <div class="drawer-stat-value">${{data.presence}} / 6</div>
      </div>
      <div class="drawer-stat">
        <div class="drawer-stat-label">Dias monitorado</div>
        <div class="drawer-stat-value">${{data.days_tracked}}</div>
      </div>`;

    let skills = '';
    for (const s of data.rankings) {{
      const gainCls  = s.xp_delta == null || s.xp_delta === 0 ? 'flat' : (s.xp_delta > 0 ? 'up' : 'down');
      const gainSign = s.xp_delta != null && s.xp_delta > 0 ? '+' : '';
      const gainTxt  = s.xp_delta == null ? '—' : `${{gainSign}}${{fmtXP(s.xp_delta)}}`;
      // Para variação de posição: subir (rank_delta > 0) é VERDE, descer é VERMELHO
      const rkCls    = s.rank_delta == null || s.rank_delta === 0 ? 'flat' : (s.rank_delta > 0 ? 'up' : 'down');


      skills += `
        <div class="drawer-skill" style="--skill-clr:${{s.color}}">
          <div class="drawer-skill-top">
            <div class="drawer-skill-icon">${{s.icon}}</div>
            <div class="drawer-skill-info">
              <div class="name">${{s.type}}</div>
              <div class="meta">Lv ${{s.level}} · ${{fmtXP(s.xp)}} XP total</div>
            </div>
            <div class="drawer-skill-rank">#${{s.rank}}</div>
          </div>
          <div class="drawer-skill-gain">
            <div class="drawer-skill-gain-cell">
              <span class="drawer-skill-gain-label">Ganhou no dia</span>
              <span class="drawer-skill-gain-value ${{gainCls}}">${{gainTxt}} XP</span>
            </div>
            <div class="drawer-skill-gain-cell">
              <span class="drawer-skill-gain-label">Variação de posição</span>
              <span class="drawer-skill-gain-value ${{rkCls}}">${{s.rank_delta == null ? '—' : (s.rank_delta > 0 ? '▲ +' : s.rank_delta < 0 ? '▼ ' : '') + (s.rank_delta !== 0 ? Math.abs(s.rank_delta) + ' pos' : '· sem mudança')}}</span>
            </div>
            <div class="drawer-skill-gain-cell">
              <span class="drawer-skill-gain-label">🔥 Rank farm do dia</span>
              <span class="drawer-skill-gain-value ${{s.farm_pos != null && s.farm_pos <= 3 ? 'up' : ''}}">${{s.farm_pos != null ? '#' + s.farm_pos + ' de ' + s.farm_total : '—'}}</span>
            </div>
          </div>
        </div>`;
    }}

    document.getElementById('drawer-body').innerHTML = `
      <div class="drawer-section">
        <div class="drawer-section-title">Visão geral</div>
        <div class="drawer-stats">${{stats}}</div>
      </div>
      <div class="drawer-section">
        <div class="drawer-section-title">Posições atuais</div>
        <div class="drawer-skill-list">${{skills}}</div>
      </div>`;

    document.getElementById('drawer').classList.add('open');
    document.getElementById('drawer-backdrop').classList.add('open');
    document.body.style.overflow = 'hidden';
  }}
  function closePlayerDrawer() {{
    document.getElementById('drawer').classList.remove('open');
    document.getElementById('drawer-backdrop').classList.remove('open');
    document.body.style.overflow = '';
  }}
  document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closePlayerDrawer(); }});

  // ── search ──
  const searchInput = document.getElementById('player-search');
  const searchResults = document.getElementById('search-results');
  const allPlayerNames = Object.keys(PLAYERS);
  let activeIdx = -1;

  function renderSearch(query) {{
    if (!query) {{ searchResults.classList.remove('open'); return; }}
    const q = query.toLowerCase();
    const matches = allPlayerNames
      .filter(n => n.toLowerCase().includes(q))
      .slice(0, 12);
    if (matches.length === 0) {{
      searchResults.innerHTML = '<div class="search-result-item" style="color:var(--muted);justify-content:center">Nenhum jogador encontrado</div>';
      searchResults.classList.add('open');
      return;
    }}
    searchResults.innerHTML = matches.map((n, i) => {{
      const p = PLAYERS[n];
      const exp = p.rankings.find(r => r.type === 'Experience');
      const meta = exp ? `Lv ${{exp.level}} · #${{exp.rank}} XP` : `${{p.presence}} ranking(s)`;
      return `<div class="search-result-item${{i === activeIdx ? ' active' : ''}}" onclick="selectSearchResult('${{n.replace(/'/g, "\\\\'")}}')"><span class="search-result-name">${{n}}</span><span class="search-result-meta">${{meta}}</span></div>`;
    }}).join('');
    searchResults.classList.add('open');
  }}
  function selectSearchResult(name) {{
    searchInput.value = '';
    searchResults.classList.remove('open');
    openPlayerDrawer(name);
  }}
  searchInput.addEventListener('input', e => {{ activeIdx = -1; renderSearch(e.target.value); }});
  searchInput.addEventListener('keydown', e => {{
    const items = searchResults.querySelectorAll('.search-result-item');
    if (e.key === 'ArrowDown') {{ e.preventDefault(); activeIdx = Math.min(activeIdx + 1, items.length - 1); renderSearch(searchInput.value); }}
    else if (e.key === 'ArrowUp') {{ e.preventDefault(); activeIdx = Math.max(activeIdx - 1, 0); renderSearch(searchInput.value); }}
    else if (e.key === 'Enter' && activeIdx >= 0) {{
      e.preventDefault();
      const name = items[activeIdx].querySelector('.search-result-name').textContent;
      selectSearchResult(name);
    }}
    else if (e.key === 'Escape') {{ searchInput.value = ''; searchResults.classList.remove('open'); }}
  }});
  document.addEventListener('click', e => {{
    if (!e.target.closest('.search-wrap')) searchResults.classList.remove('open');
  }});

  // ── preloader ──
  window.addEventListener('load', () => {{
    const pl = document.getElementById('preloader');
    if (pl) setTimeout(() => pl.classList.add('hidden'), 300);
  }});
  // fallback: esconde após 4s mesmo se load não disparar
  setTimeout(() => {{
    const pl = document.getElementById('preloader');
    if (pl) pl.classList.add('hidden');
  }}, 4000);

  // ── glow follow no player-card ──
  document.querySelectorAll('.player-card').forEach(card => {{
    card.addEventListener('mousemove', e => {{
      const r = card.getBoundingClientRect();
      card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      card.style.setProperty('--my', (e.clientY - r.top) + 'px');
    }});
  }});

  // ── tabs ──
  function switchTab(group, id, btn) {{
    document.querySelectorAll('[id^="' + group + '-panel-"]').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('[id^="' + group + '-btn-"]').forEach(b => b.classList.remove('active'));
    const panel = document.getElementById(group + '-panel-' + id);
    const button = btn || document.getElementById(group + '-btn-' + id);
    if (panel)  panel.classList.add('active');
    if (button) button.classList.add('active');
  }}

  function setEvoPeriod(days, btn) {{
    document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const charts = document.querySelectorAll('.evo-chart-box .js-plotly-plot');
    if (days === 0) {{
      charts.forEach(c => Plotly.relayout(c, {{'xaxis.autorange': true, 'xaxis2.autorange': true}}));
    }} else {{
      const end = new Date();
      const start = new Date(end - days * 864e5);
      const fmt = d => d.toISOString().split('T')[0];
      charts.forEach(c => {{
        const update = {{'xaxis.range': [fmt(start), fmt(end)]}};
        // subplots compartilham xaxis — basta o xaxis principal
        if (c.layout && c.layout.xaxis2) update['xaxis2.range'] = [fmt(start), fmt(end)];
        Plotly.relayout(c, update);
      }});
    }}
  }}
</script>
</body>
</html>"""


# ── entry point ────────────────────────────────────────────────────────────
def gerar():
    if not os.path.exists(DB_PATH):
        print("Banco nao encontrado. Execute coletor_ranking.py primeiro.")
        sys.exit(1)

    cfg = json.load(open(CONFIG_PATH, encoding="utf-8"))
    watched = cfg.get("watched_players", [])

    conn = sqlite3.connect(DB_PATH)
    df   = load(conn)
    total_registros = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
    conn.close()

    if df.empty:
        print("Sem dados no banco.")
        sys.exit(1)

    df_lat = latest(df)
    df_prv = prev(df)

    ultima_coleta   = df_lat["collected_at"].iloc[0].strftime("%d/%m/%Y %H:%M")
    dias_coletando  = df["collected_at"].nunique()  # 1 por dia apos dedup
    total_jogadores = df["player_id"].nunique()

    print(f"Gerando dashboard — {dias_coletando} dia(s), {total_jogadores} jogadores unicos...")

    html = build_html(
        cfg, df, df_lat, df_prv,
        watched, ultima_coleta, dias_coletando, total_jogadores, total_registros,
    )

    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] {DASHBOARD_PATH}")


if __name__ == "__main__":
    gerar()
