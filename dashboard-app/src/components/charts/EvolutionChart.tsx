// components/charts/EvolutionChart.tsx
// Evolução Temporal — um card por jogador × skill
// Cada card: Area (XP acumulado) + Line (posição no ranking) empilhados com syncId
// Idêntico ao layout Plotly original em grid 2 colunas
import { useMemo } from 'react';
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import type { DashboardData, SkillPoint } from '../../types';
import { useDashboardStore } from '../../store/useDashboardStore';
import { SKILL_COLORS, PLAYER_COLORS, hexToRgba, fmtXP } from '../../utils/colors';
import './Charts.css';

interface Props { data: DashboardData; }

interface EvoCard {
  playerName: string;
  playerIndex: number;
  skill: string;
  points: SkillPoint[];
}

const PERIODS = [
  { label: '24h', days: 1 }, { label: '7d', days: 7 }, { label: '15d', days: 15 },
  { label: '30d', days: 30 }, { label: '3 meses', days: 90 },
  { label: '6 meses', days: 180 }, { label: '1 ano', days: 365 },
  { label: 'Tudo', days: 0 },
];

function EvoCardChart({
  card, dimmed,
}: {
  card: EvoCard;
  dimmed: boolean;
}) {
  const skillColor = SKILL_COLORS[card.skill] ?? '#d4af37';
  const syncId = `evo-${card.playerName}-${card.skill}`;

  const chartData = card.points.map(p => ({
    date: p.date.slice(5),   // "04-23" format
    xp: p.experience,
    rank: p.rank,
    level: p.level,
  }));

  const xpTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    const d = payload[0]?.payload;
    const xpDelta = chartData.findIndex(p => p.date === label) > 0
      ? (d?.xp ?? 0) - (chartData[chartData.findIndex(p => p.date === label) - 1]?.xp ?? 0)
      : 0;
    return (
      <div className="custom-tooltip">
        <div className="custom-tooltip-label">{label}</div>
        <div className="custom-tooltip-row"><span>XP</span><span style={{ color: skillColor }}>{fmtXP(d?.xp)}</span></div>
        {xpDelta !== 0 && (
          <div className="custom-tooltip-row">
            <span>Ganho</span>
            <span style={{ color: xpDelta > 0 ? '#2ecc71' : 'var(--bright)' }}>
              {xpDelta > 0 ? '+' : ''}{fmtXP(xpDelta)}
            </span>
          </div>
        )}
      </div>
    );
  };

  const rankTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="custom-tooltip">
        <div className="custom-tooltip-label">{label}</div>
        <div className="custom-tooltip-row"><span>Posição</span><span>#{payload[0]?.value}</span></div>
      </div>
    );
  };

  return (
    <div
      className="chart-card evo-card"
      style={{ opacity: dimmed ? 0.25 : 1, transition: 'opacity 0.25s' }}
    >
      {/* Título */}
      <div style={{ marginBottom: 4 }}>
        <div className="chart-title" style={{ color: skillColor, marginBottom: 2 }}>
          Evolução — {card.skill}
        </div>
        <div style={{ fontSize: '0.68rem', color: 'var(--muted)', letterSpacing: '0.5px', fontFamily: 'Ubuntu Condensed' }}>
          {card.playerName}
        </div>
      </div>

      {/* XP Acumulado — Área */}
      <div style={{ marginBottom: 2 }}>
        <div style={{ fontSize: '0.62rem', color: skillColor, textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 700, marginBottom: 4 }}>
          XP Acumulado
        </div>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={chartData} syncId={syncId} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fill: 'var(--muted)', fontSize: 9 }} axisLine={false} tickLine={false} />
            <YAxis tickFormatter={v => fmtXP(v)} tick={{ fill: 'var(--muted)', fontSize: 9 }} axisLine={false} tickLine={false} width={44} />
            <Tooltip content={xpTooltip} />
            <Area
              type="monotone"
              dataKey="xp"
              stroke={skillColor}
              strokeWidth={2.5}
              fill={hexToRgba(skillColor, 0.18)}
              dot={false}
              activeDot={{ r: 4, fill: skillColor, strokeWidth: 0 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Posição no Ranking — Linha */}
      <div>
        <div style={{ fontSize: '0.62rem', color: '#d4af37', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 700, marginBottom: 4 }}>
          Posição no Ranking
        </div>
        <ResponsiveContainer width="100%" height={120}>
          <LineChart data={chartData} syncId={syncId} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fill: 'var(--muted)', fontSize: 9 }} axisLine={false} tickLine={false} />
            <YAxis reversed tick={{ fill: 'var(--muted)', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `#${v}`} width={32} />
            <Tooltip content={rankTooltip} />
            <Line
              type="monotone"
              dataKey="rank"
              stroke="#d4af37"
              strokeWidth={2}
              dot={{ r: 4, fill: '#d4af37', stroke: 'var(--bg)', strokeWidth: 1.5 }}
              activeDot={{ r: 6, fill: '#d4af37', strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Gráfico de histórico consolidado: todos os watched players em uma linha cada
function RankHistoryChart({ cards }: { cards: EvoCard[] }) {
  const { selectedPlayer } = useDashboardStore();

  // Uma linha por jogador×skill
  const series = cards.map(c => ({
    key: `${c.playerName}_${c.skill}`,
    label: `${c.playerName} — ${c.skill}`,
    playerName: c.playerName,
    color: PLAYER_COLORS[c.playerIndex % PLAYER_COLORS.length],
    points: c.points,
  }));

  if (series.length === 0) return null;

  // Merge all dates
  const allDates = [...new Set(series.flatMap(s => s.points.map(p => p.date.slice(5))))].sort();
  const chartData = allDates.map(date => {
    const row: Record<string, string | number | null> = { date };
    series.forEach(s => {
      const pt = s.points.find(p => p.date.slice(5) === date);
      row[s.key] = pt ? pt.rank : null;
    });
    return row;
  });

  return (
    <div className="chart-card chart-card--full" style={{ marginTop: 14 }}>
      <div className="chart-title" style={{ color: 'var(--gold)' }}>
        Histórico de Posições — Jogadores Monitorados
      </div>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fill: 'var(--muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis reversed tick={{ fill: 'var(--muted)', fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={v => `#${v}`} />
          <Tooltip
            contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border-hi)', borderRadius: 'var(--radius)', fontSize: 11, fontFamily: 'Fira Code' }}
            labelStyle={{ color: 'var(--text)', fontFamily: 'Anton', marginBottom: 4 }}
          />
          {series.map(s => {
            const dimmed = selectedPlayer !== null && selectedPlayer !== s.playerName;
            return (
              <Line
                key={s.key}
                type="monotone"
                dataKey={s.key}
                name={s.label}
                stroke={s.color}
                strokeWidth={dimmed ? 1 : 2}
                dot={false}
                connectNulls
                style={{ opacity: dimmed ? 0.2 : 1, transition: 'opacity 0.25s' }}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function EvolutionChart({ data }: Props) {
  const { periodDays, setPeriodDays } = useDashboardStore();
  const { selectedPlayer } = useDashboardStore();
  const { metadata, history } = data;
  const { watched, ranking_types } = metadata;

  const cutoff = useMemo(() => {
    if (periodDays === 0) return null;
    const d = new Date();
    d.setDate(d.getDate() - periodDays);
    return d.toISOString().split('T')[0];
  }, [periodDays]);

  // Gera os cards na mesma ordem do Plotly: watched × skills
  const cards = useMemo<EvoCard[]>(() => {
    const result: EvoCard[] = [];
    watched.forEach((name, playerIndex) => {
      ranking_types.forEach(rt => {
        const entry = history.find(
          h => h.name.toLowerCase() === name.toLowerCase() && h.ranking_type === rt
        );
        if (!entry || entry.points.length < 2) return;

        const filtered = cutoff
          ? entry.points.filter(p => p.date >= cutoff)
          : entry.points;
        if (filtered.length < 2) return;

        result.push({ playerName: name, playerIndex, skill: rt, points: filtered });
      });
    });
    return result;
  }, [watched, ranking_types, history, cutoff]);

  if (cards.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-empty">
          Disponível a partir da segunda coleta. Aguarde o próximo dia de dados.
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Filtro de período */}
      <div className="period-bar">
        <span className="period-label">Período:</span>
        {PERIODS.map(p => (
          <button
            key={p.label}
            className={`period-btn ${periodDays === p.days ? 'active' : ''}`}
            onClick={() => setPeriodDays(p.days)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Grid 2 colunas dos cards individuais */}
      <div className="chart-grid-2">
        {cards.map((card, i) => {
          const dimmed = selectedPlayer !== null && selectedPlayer !== card.playerName;
          return (
            <EvoCardChart
              key={`${card.playerName}-${card.skill}-${i}`}
              card={card}
              dimmed={dimmed}
            />
          );
        })}
      </div>

      {/* Gráfico consolidado de histórico */}
      <RankHistoryChart cards={cards} />
    </div>
  );
}
