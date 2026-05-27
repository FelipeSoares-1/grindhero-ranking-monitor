// components/charts/EvolutionChart.tsx
// Evolução Temporal — com abas de skill, um card por jogador monitorado
import { useState, useMemo } from 'react';
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import type { DashboardData, SkillPoint } from '../../types';
import { useDashboardStore } from '../../store/useDashboardStore';
import { SKILL_COLORS, hexToRgba, fmtXP } from '../../utils/colors';
import './Charts.css';

interface Props { data: DashboardData; }

interface EvoCard {
  playerName: string;
  playerIndex: number;
  skill: string;
  points: SkillPoint[];
}

const PERIODS = [
  { label: '7d', days: 7 }, { label: '15d', days: 15 },
  { label: '30d', days: 30 }, { label: '3m', days: 90 },
  { label: '6m', days: 180 }, { label: '1a', days: 365 },
  { label: 'Tudo', days: 0 },
];

function EvoCardChart({ card, dimmed }: { card: EvoCard; dimmed: boolean }) {
  const skillColor = SKILL_COLORS[card.skill] ?? '#d4af37';
  const syncId = `evo-${card.playerName}-${card.skill}`;

  const chartData = card.points.map(p => ({
    date: p.date.slice(5),
    xp: p.experience,
    rank: p.rank,
    level: p.level,
  }));

  const xpTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    const d = payload[0]?.payload;
    const idx = chartData.findIndex(p => p.date === label);
    const xpDelta = idx > 0 ? (d?.xp ?? 0) - (chartData[idx - 1]?.xp ?? 0) : 0;
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
    <div className="chart-card evo-card" style={{ opacity: dimmed ? 0.25 : 1, transition: 'opacity 0.25s' }}>
      <div className="chart-title" style={{ color: skillColor }}>
        {card.playerName}
      </div>

      <div style={{ fontSize: '0.62rem', color: skillColor, textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 700, margin: '8px 0 4px' }}>
        XP Acumulado
      </div>
      <ResponsiveContainer width="100%" height={150}>
        <AreaChart data={chartData} syncId={syncId} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="date" tick={{ fill: 'var(--muted)', fontSize: 9 }} axisLine={false} tickLine={false} />
          <YAxis tickFormatter={v => fmtXP(v)} tick={{ fill: 'var(--muted)', fontSize: 9 }} axisLine={false} tickLine={false} width={44} />
          <Tooltip content={xpTooltip} />
          <Area type="monotone" dataKey="xp" stroke={skillColor} strokeWidth={2.5}
            fill={hexToRgba(skillColor, 0.18)} dot={false}
            activeDot={{ r: 4, fill: skillColor, strokeWidth: 0 }} />
        </AreaChart>
      </ResponsiveContainer>

      <div style={{ fontSize: '0.62rem', color: '#d4af37', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 700, margin: '10px 0 4px' }}>
        Posição no Ranking
      </div>
      <ResponsiveContainer width="100%" height={110}>
        <LineChart data={chartData} syncId={syncId} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="date" tick={{ fill: 'var(--muted)', fontSize: 9 }} axisLine={false} tickLine={false} />
          <YAxis reversed tick={{ fill: 'var(--muted)', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `#${v}`} width={32} />
          <Tooltip content={rankTooltip} />
          <Line type="monotone" dataKey="rank" stroke="#d4af37" strokeWidth={2}
            dot={{ r: 3, fill: '#d4af37', stroke: 'var(--bg)', strokeWidth: 1.5 }}
            activeDot={{ r: 5, fill: '#d4af37', strokeWidth: 0 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function EvolutionChart({ data }: Props) {
  const { periodDays, setPeriodDays, selectedPlayer } = useDashboardStore();
  const { metadata, history } = data;
  const { watched, ranking_types } = metadata;

  const [activeSkill, setActiveSkill] = useState(ranking_types[0] ?? 'Experience');

  const cutoff = useMemo(() => {
    if (periodDays === 0) return null;
    const d = new Date();
    d.setDate(d.getDate() - periodDays);
    return d.toISOString().split('T')[0];
  }, [periodDays]);

  // Apenas jogadores com dados na skill ativa
  const cards = useMemo<EvoCard[]>(() => {
    return watched.flatMap((name, playerIndex) => {
      const entry = history.find(
        h => h.name.toLowerCase() === name.toLowerCase() && h.ranking_type === activeSkill
      );
      if (!entry || entry.points.length < 2) return [];

      const filtered = cutoff
        ? entry.points.filter(p => p.date >= cutoff)
        : entry.points;
      if (filtered.length < 2) return [];

      return [{ playerName: name, playerIndex, skill: activeSkill, points: filtered }];
    });
  }, [watched, history, activeSkill, cutoff]);

  return (
    <div>
      {/* Abas de skill */}
      <div className="tabs-bar">
        {ranking_types.map(rt => (
          <button
            key={rt}
            className={`tab-btn ${activeSkill === rt ? 'active' : ''}`}
            onClick={() => setActiveSkill(rt)}
            style={activeSkill === rt ? { borderColor: SKILL_COLORS[rt], backgroundColor: `${SKILL_COLORS[rt]}22` } : {}}
          >
            {rt}
          </button>
        ))}
      </div>

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

      {cards.length === 0 ? (
        <div className="chart-card">
          <div className="chart-empty">
            Sem dados de {activeSkill} para o período selecionado.
          </div>
        </div>
      ) : (
        <div className="chart-grid-2">
          {cards.map((card, i) => (
            <EvoCardChart
              key={`${card.playerName}-${i}`}
              card={card}
              dimmed={selectedPlayer !== null && selectedPlayer !== card.playerName}
            />
          ))}
        </div>
      )}
    </div>
  );
}
