// components/charts/VelocityChart.tsx
// Barras horizontais do farm do dia — Top 15 por skill.
// Cross-filter: clicar numa barra marca o jogador globalmente.
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer,
} from 'recharts';
import type { DashboardData } from '../../types';
import { useDashboardStore } from '../../store/useDashboardStore';
import { SKILL_COLORS, fmtXP } from '../../utils/colors';
import './Charts.css';

const POS_LABELS = ['🥇', '🥈', '🥉'];

interface Props { data: DashboardData; }


export function VelocityChart({ data }: Props) {
  const { selectedPlayer, toggleSelectedPlayer, activeSkill, setActiveSkill } = useDashboardStore();
  const { metadata, velocity } = data;
  const { ranking_types } = metadata;

  const velData = velocity[activeSkill] ?? [];
  const color = SKILL_COLORS[activeSkill] ?? '#d4af37';

  const chartData = velData.map((v, i) => {
    const pos = i < 3 ? POS_LABELS[i] : `${i + 1}º`;
    return {
      name: `${pos} ${v.name}`,
      rawName: v.name,
      xp_day: v.xp_day,
      label: v.label,
    };
  });

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="custom-tooltip">
        <div className="custom-tooltip-label">{d.rawName}</div>
        <div className="custom-tooltip-row">
          <span>XP ganho</span>
          <span style={{ color }}>{d.label}</span>
        </div>
      </div>
    );
  };

  return (
    <div>
      <div className="tabs-bar">
        {ranking_types.map(rt => (
          <button
            key={rt}
            className={`tab-btn ${activeSkill === rt ? 'active' : ''}`}
            onClick={() => setActiveSkill(rt)}
          >
            {rt}
          </button>
        ))}
      </div>

      {velData.length === 0 ? (
        <div className="chart-card">
          <div className="chart-empty">Disponível a partir da segunda coleta.</div>
        </div>
      ) : (
        <div className="chart-card">
          <div className="chart-title" style={{ color }}>
            Velocidade de Farm — {activeSkill}
            <span style={{ fontSize: '0.65rem', color: 'var(--muted)', marginLeft: 8, fontFamily: 'Ubuntu Condensed' }}>
              clique para filtrar
            </span>
          </div>
          <ResponsiveContainer width="100%" height={420}>
            <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 60, left: 0, bottom: 0 }}>
              <XAxis type="number" hide />
              <YAxis
                type="category" dataKey="name" width={175}
                tick={({ y, payload }: any) => (
                  <text
                    x={4}
                    y={y}
                    dy={4}
                    textAnchor="start"
                    fill="var(--muted)"
                    fontSize={11}
                    fontFamily="Fira Code, monospace"
                  >
                    {payload.value}
                  </text>
                )}
                axisLine={false} tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar
                dataKey="xp_day"
                radius={[0, 3, 3, 0]}
                label={{ position: 'right', formatter: (v: any) => fmtXP(v as number), fill: 'var(--muted)', fontSize: 11, fontFamily: 'Fira Code' }}
                cursor="pointer"
                onClick={(entry: any) => toggleSelectedPlayer(entry.rawName)}
              >
                {chartData.map((entry) => {
                  const isSelected = selectedPlayer === entry.rawName;
                  const isWatched = metadata.watched.some(w => w.toLowerCase() === entry.rawName.toLowerCase());
                  const dimmed = selectedPlayer !== null && selectedPlayer !== entry.rawName;
                  const fillColor = isSelected
                    ? '#d4af37'
                    : isWatched
                    ? color
                    : `rgba(${color.replace('#','').match(/.{2}/g)?.map(c=>parseInt(c,16)).join(',')},0.5)`;
                  return (
                    <Cell
                      key={entry.name}
                      fill={fillColor}
                      opacity={dimmed ? 0.2 : 1}
                      style={{ transition: 'opacity 0.25s, fill 0.25s' }}
                    />
                  );
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
