// components/charts/RadarSkillChart.tsx
// Barras agrupadas por skill para todos os watched players.
// Cross-filter: clicar na barra de um jogador o seleciona globalmente.
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts';
import type { DashboardData } from '../../types';
import { useDashboardStore } from '../../store/useDashboardStore';
import { SKILL_COLORS, PLAYER_COLORS, hexToRgba } from '../../utils/colors';
import './Charts.css';

interface Props { data: DashboardData; }

export function RadarSkillChart({ data }: Props) {
  const { selectedPlayer, toggleSelectedPlayer } = useDashboardStore();
  const { metadata, latest_snapshot } = data;
  const { watched, ranking_types } = metadata;

  // Monta: [{skill, Player1: invertedRank, Player2: invertedRank, ...}]
  const chartData = ranking_types.map(rt => {
    const entry: Record<string, string | number> = { skill: rt };
    watched.forEach(name => {
      const snap = latest_snapshot.find(
        s => s.name.toLowerCase() === name.toLowerCase() && s.ranking_type === rt
      );
      entry[name] = snap ? Math.max(0, 51 - snap.rank) : 0;
      entry[`${name}_rank`] = snap?.rank ?? 0;
    });
    return entry;
  });

  function handleBarClick(playerName: string) {
    toggleSelectedPlayer(playerName);
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="custom-tooltip">
        <div className="custom-tooltip-label" style={{ color: SKILL_COLORS[label] || 'var(--gold)' }}>
          {label}
        </div>
        {payload.map((p: any) => {
          const rankKey = `${p.name}_rank`;
          const rank = p.payload[rankKey];
          return (
            <div key={p.name} className="custom-tooltip-row">
              <span style={{ color: p.fill }}>{p.name}</span>
              <span>{rank ? `#${rank}` : '—'}</span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="chart-card chart-card--full">
      <div className="chart-title" style={{ color: 'var(--gold)' }}>
        Posição por Skill
        <span style={{ fontSize: '0.65rem', color: 'var(--muted)', marginLeft: 8, fontFamily: 'Ubuntu Condensed' }}>
          barra maior = melhor rank • clique para filtrar
        </span>
      </div>
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={chartData} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="skill"
            tick={{ fill: 'var(--muted)', fontSize: 12, fontFamily: 'Ubuntu Condensed' }}
            axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={v => v > 0 ? String(51 - v) : ''}
            tick={{ fill: 'var(--muted)', fontSize: 11 }}
            axisLine={false} tickLine={false}
            domain={[0, 50]}
            label={{ value: 'Posição', angle: -90, position: 'insideLeft', fill: 'var(--muted)', fontSize: 11 }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <Legend
            formatter={(value) => (
              <span style={{ color: selectedPlayer === value ? 'var(--text)' : 'var(--muted)', fontWeight: selectedPlayer === value ? 700 : 400, cursor: 'pointer' }}>
                {value}
              </span>
            )}
          />
          {watched.map((name, i) => {
            const color = PLAYER_COLORS[i % PLAYER_COLORS.length];
            const dimmed = selectedPlayer !== null && selectedPlayer !== name;
            return (
              <Bar
                key={name}
                dataKey={name}
                name={name}
                fill={hexToRgba(color, dimmed ? 0.12 : 0.3)}
                stroke={color}
                strokeWidth={dimmed ? 0 : 2}
                radius={[2, 2, 0, 0]}
                cursor="pointer"
                onClick={() => handleBarClick(name)}
                style={{ opacity: dimmed ? 0.25 : 1, transition: 'opacity 0.25s' }}
              />
            );
          })}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
