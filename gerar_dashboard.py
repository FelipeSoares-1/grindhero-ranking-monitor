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
DASHBOARD_PATH = os.path.join(BASE_DIR, "dashboard.html")

# ── design tokens ──────────────────────────────────────────────────────────
CLR = {
    "bg":        "#080810",
    "surface":   "#0e0e1c",
    "card":      "#12121f",
    "border":    "rgba(0,212,255,0.15)",
    "cyan":      "#00d4ff",
    "pink":      "#ff2d55",
    "green":     "#00ff88",
    "yellow":    "#ffd60a",
    "purple":    "#bf5af2",
    "text":      "#e0e0f0",
    "muted":     "#6b6b8a",
    "Experience":"#00d4ff",
    "Melee":     "#ff6b35",
    "Shielding": "#ff2d55",
    "Magic":     "#bf5af2",
    "Distance":  "#00ff88",
    "Taming":    "#ffd60a",
}

def hex_to_rgba(hex_color: str, alpha: float = 0.08) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Fira Code, monospace", color=CLR["text"], size=12),
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
            colorscale=[[0,"rgba(255,45,85,0.6)"],[0.5,"rgba(0,212,255,0.4)"],[1,CLR["green"]]],
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

    return f"""
    <div class="player-card">
      <div class="pc-header">
        <span class="pc-name">{name}</span>
        <div class="pc-badges">
          <span class="badge badge--blue">{presence} rankings</span>
          <span class="badge badge--cyan">Melhor #{best_rank}</span>
        </div>
      </div>
      <div class="skill-list">{skills_html}</div>
    </div>"""


def build_ranking_table(df_latest: pd.DataFrame, df_prev: pd.DataFrame, rt: str, watched: list) -> str:
    sub = df_latest[df_latest["ranking_type"] == rt].sort_values("rank")
    clr = CLR.get(rt, CLR["cyan"])
    icon = SKILL_ICONS.get(rt, "")
    rows_html = ""
    for _, r in sub.iterrows():
        is_watched = any(r["name"].lower() == w.lower() for w in watched)
        xp_d, rk_d, _ = xp_delta(df_latest, df_prev, r["name"], rt) if not df_prev.empty else (None, None, None)
        hl = ' class="tr-highlight"' if is_watched else ""
        badge = f'<span class="badge badge--cyan">monitorado</span>' if is_watched else ""
        rows_html += f"""<tr{hl}>
          <td class="td-rank">#{int(r['rank'])}</td>
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
            lines.append(f"<li><b>{name}</b>: {' &bull; '.join(parts)}</li>")
    return f"<ul class='digest-list'>{''.join(lines)}</ul>"


# ── main builder ───────────────────────────────────────────────────────────
def build_css() -> str:
    return """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600&display=swap');

      :root {
        --bg:      #080810;
        --surface: #0e0e1c;
        --card:    #12121f;
        --border:  rgba(0,212,255,0.15);
        --cyan:    #00d4ff;
        --pink:    #ff2d55;
        --green:   #00ff88;
        --yellow:  #ffd60a;
        --purple:  #bf5af2;
        --text:    #e0e0f0;
        --muted:   #6b6b8a;
        --radius:  12px;
      }

      *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

      body {
        background: var(--bg);
        color: var(--text);
        font-family: 'Fira Sans', sans-serif;
        font-size: 14px;
        line-height: 1.6;
        min-height: 100vh;
      }

      /* ── scrollbar ── */
      ::-webkit-scrollbar { width: 6px; height: 6px; }
      ::-webkit-scrollbar-track { background: var(--surface); }
      ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

      /* ── layout ── */
      .page { max-width: 1400px; margin: 0 auto; padding: 24px 20px; }

      /* ── header ── */
      .header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 20px 28px;
        background: linear-gradient(135deg, rgba(0,212,255,0.06) 0%, rgba(0,0,0,0) 60%);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        margin-bottom: 28px;
        backdrop-filter: blur(12px);
      }
      .header-brand { display: flex; align-items: center; gap: 14px; }
      .header-logo {
        width: 48px; height: 48px; border-radius: 10px;
        background: linear-gradient(135deg, var(--cyan), var(--purple));
        display: flex; align-items: center; justify-content: center;
        font-family: 'Fira Code', monospace; font-size: 22px; font-weight: 700;
        color: #080810; flex-shrink: 0;
      }
      .header-title { font-family: 'Fira Code', monospace; font-size: 1.4rem; font-weight: 700; color: var(--cyan); letter-spacing: -0.5px; }
      .header-sub { font-size: 0.8rem; color: var(--muted); margin-top: 2px; }
      .header-meta { text-align: right; font-size: 0.78rem; color: var(--muted); line-height: 1.8; }
      .header-meta strong { color: var(--text); }

      /* ── stat bar ── */
      .statbar {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px; margin-bottom: 28px;
      }
      .stat {
        background: var(--card);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: var(--radius);
        padding: 14px 16px;
        transition: border-color 0.2s;
      }
      .stat:hover { border-color: var(--border); cursor: default; }
      .stat-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
      .stat-value { font-family: 'Fira Code', monospace; font-size: 1.4rem; font-weight: 700; color: var(--cyan); }
      .stat-sub { font-size: 0.72rem; color: var(--muted); margin-top: 2px; }

      /* ── section ── */
      .section { margin-bottom: 32px; }
      .section-title {
        font-family: 'Fira Code', monospace; font-size: 0.85rem; font-weight: 600;
        color: var(--muted); text-transform: uppercase; letter-spacing: 1.5px;
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 16px; padding-bottom: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
      }
      .section-title svg { color: var(--cyan); }
      .section-title .st-accent { color: var(--cyan); }

      /* ── player card ── */
      .player-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 16px; }
      .player-card {
        background: linear-gradient(135deg, rgba(0,212,255,0.03) 0%, var(--card) 50%);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 20px;
        transition: border-color 0.25s, box-shadow 0.25s;
      }
      .player-card:hover {
        border-color: rgba(0,212,255,0.4);
        box-shadow: 0 0 24px rgba(0,212,255,0.08);
      }
      .player-card--absent { border-color: rgba(255,255,255,0.05); opacity: 0.6; }
      .pc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
      .pc-name { font-family: 'Fira Code', monospace; font-size: 1.1rem; font-weight: 700; color: var(--cyan); text-shadow: 0 0 12px rgba(0,212,255,0.4); }
      .pc-badges { display: flex; gap: 6px; flex-wrap: wrap; }
      .pc-absent-msg { color: var(--muted); font-size: 0.85rem; }

      .skill-list { display: flex; flex-direction: column; gap: 8px; }
      .skill-row {
        display: grid;
        grid-template-columns: 20px 90px 52px 52px 80px 90px 70px 1fr;
        align-items: center; gap: 8px;
        padding: 8px 10px;
        border-radius: 8px;
        background: rgba(255,255,255,0.02);
        border-left: 2px solid var(--skill-clr);
        transition: background 0.15s;
      }
      .skill-row:hover { background: rgba(255,255,255,0.04); }
      .skill-icon { display: flex; align-items: center; }
      .skill-name { font-size: 0.78rem; font-weight: 500; color: var(--muted); }
      .skill-rank { font-family: 'Fira Code', monospace; font-weight: 700; font-size: 0.9rem; color: var(--skill-clr); }
      .skill-lv   { font-size: 0.75rem; color: var(--muted); }
      .skill-xp   { font-family: 'Fira Code', monospace; font-size: 0.82rem; color: var(--text); }
      .skill-delta, .skill-rank-delta { font-size: 0.75rem; }
      .proj { font-size: 0.7rem; color: var(--yellow); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

      /* ── badges ── */
      .badge {
        font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
        padding: 2px 7px; border-radius: 20px; letter-spacing: 0.6px;
      }
      .badge--cyan   { background: rgba(0,212,255,0.12); color: var(--cyan); border: 1px solid rgba(0,212,255,0.3); }
      .badge--blue   { background: rgba(100,130,255,0.1); color: #8899ff; border: 1px solid rgba(100,130,255,0.25); }
      .badge--yellow { background: rgba(255,214,10,0.1);  color: var(--yellow); border: 1px solid rgba(255,214,10,0.3); }
      .badge--pink   { background: rgba(255,45,85,0.1);   color: var(--pink); border: 1px solid rgba(255,45,85,0.3); }

      /* ── delta ── */
      .delta-up   { color: var(--green); display: inline-flex; align-items: center; gap: 2px; }
      .delta-down { color: var(--pink);  display: inline-flex; align-items: center; gap: 2px; }
      .delta-neutral { color: var(--muted); display: inline-flex; align-items: center; gap: 2px; }

      /* ── chart grid ── */
      .chart-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
      .chart-grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
      .chart-box {
        background: var(--card); border: 1px solid rgba(255,255,255,0.05);
        border-radius: var(--radius); padding: 4px;
        transition: border-color 0.2s;
      }
      .chart-box:hover { border-color: var(--border); }
      .chart-box--full { grid-column: 1 / -1; }
      .chart-empty {
        display: flex; align-items: center; justify-content: center;
        height: 160px; color: var(--muted); font-size: 0.82rem; text-align: center;
        padding: 20px;
      }

      /* ── tabs ── */
      .tabs-bar { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }
      .tab-btn {
        background: var(--card); color: var(--muted);
        border: 1px solid rgba(255,255,255,0.06);
        padding: 6px 14px; border-radius: 6px; cursor: pointer;
        font-family: 'Fira Code', monospace; font-size: 0.78rem;
        transition: all 0.15s; display: flex; align-items: center; gap: 6px;
      }
      .tab-btn:hover { border-color: var(--border); color: var(--text); }
      .tab-btn.active { background: rgba(0,212,255,0.1); border-color: var(--cyan); color: var(--cyan); }
      .tab-panel { display: none; }
      .tab-panel.active { display: block; }

      /* ── ranking table ── */
      .rank-table-wrap {
        background: var(--card); border: 1px solid rgba(255,255,255,0.05);
        border-radius: var(--radius); overflow: hidden;
      }
      .rank-table-header {
        display: flex; justify-content: space-between; align-items: center;
        padding: 12px 16px;
        background: linear-gradient(90deg, rgba(var(--rt-clr-rgb),0.08) 0%, transparent 100%);
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-family: 'Fira Code', monospace; font-size: 0.85rem; font-weight: 600;
      }
      .rt-count { font-size: 0.72rem; color: var(--muted); }
      .rank-table { width: 100%; border-collapse: collapse; }
      .rank-table th {
        padding: 8px 12px; text-align: left; font-size: 0.7rem;
        text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted);
        border-bottom: 1px solid rgba(255,255,255,0.05);
      }
      .rank-table td { padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,0.03); vertical-align: middle; }
      .rank-table tr:last-child td { border-bottom: none; }
      .rank-table tr:hover td { background: rgba(255,255,255,0.02); }
      .tr-highlight td { background: rgba(0,212,255,0.04) !important; }
      .tr-highlight .td-name { color: var(--cyan) !important; font-weight: 600; }
      .td-rank { font-family: 'Fira Code', monospace; font-weight: 700; color: var(--muted); width: 50px; }
      .td-name { display: flex; align-items: center; gap: 6px; font-weight: 500; }
      .td-num  { font-family: 'Fira Code', monospace; font-size: 0.82rem; }
      .td-delta { font-size: 0.78rem; }

      /* ── digest ── */
      .digest-box {
        background: var(--card); border: 1px solid rgba(255,214,10,0.15);
        border-radius: var(--radius); padding: 18px 20px;
      }
      .digest-empty { color: var(--muted); font-size: 0.83rem; }
      .digest-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
      .digest-list li { font-size: 0.85rem; line-height: 1.7; }
      .digest-list b  { color: var(--text); }

      /* ── no data placeholder ── */
      .no-data {
        background: var(--card); border: 1px dashed rgba(255,255,255,0.08);
        border-radius: var(--radius); padding: 32px;
        text-align: center; color: var(--muted); font-size: 0.83rem;
      }
      .no-data strong { display: block; font-size: 1rem; color: var(--text); margin-bottom: 8px; }

      /* ── period selector ── */
      .period-bar {
        display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; align-items: center;
      }
      .period-label {
        font-size: 0.7rem; color: var(--muted); text-transform: uppercase;
        letter-spacing: 0.8px; margin-right: 4px;
      }
      .period-btn {
        background: var(--card); color: var(--muted);
        border: 1px solid rgba(255,255,255,0.06);
        padding: 5px 12px; border-radius: 6px; cursor: pointer;
        font-family: 'Fira Code', monospace; font-size: 0.75rem;
        transition: all 0.15s;
      }
      .period-btn:hover { border-color: var(--border); color: var(--text); }
      .period-btn.active { background: rgba(0,212,255,0.1); border-color: var(--cyan); color: var(--cyan); }

      /* ── responsive ── */
      @media (max-width: 900px) {
        .chart-grid-2, .chart-grid-3 { grid-template-columns: 1fr; }
        .player-grid { grid-template-columns: 1fr; }
        .skill-row { grid-template-columns: 20px 80px 48px 80px 1fr; }
        .skill-lv, .skill-rank-delta { display: none; }
      }
      @media (max-width: 600px) {
        .header { flex-direction: column; gap: 12px; text-align: center; }
        .header-meta { text-align: center; }
        .statbar { grid-template-columns: repeat(2, 1fr); }
      }

      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { transition: none !important; animation: none !important; }
      }
    </style>"""


def build_html(
    cfg, df, df_lat, df_prv,
    watched, ultima_coleta, dias_coletando, total_jogadores, total_registros,
) -> str:

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

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GrindHero Monitor — {cfg['server']['name']}</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  {build_css()}
</head>
<body>
<div class="page">

  <!-- HEADER -->
  <header class="header">
    <div class="header-brand">
      <div class="header-logo">GH</div>
      <div>
        <div class="header-title">GrindHero Monitor</div>
        <div class="header-sub">Ranking competitivo &mdash; {cfg['server']['name']}</div>
      </div>
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

  <p style="text-align:center;color:var(--muted);font-size:0.72rem;margin-top:16px;padding-bottom:24px">
    GrindHero Monitor &bull; Dados coletados de grindhero.online &bull; Endora (PvP) &bull; Atualizado diariamente &agrave;s 00:00
  </p>

</div>

<script>
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

    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] {DASHBOARD_PATH}")


if __name__ == "__main__":
    gerar()
