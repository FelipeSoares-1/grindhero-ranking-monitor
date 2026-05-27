// components/charts/GapChart.tsx
// Análise Competitiva — Gap dos vizinhos de ranking por skill (com abas)
import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer,
} from 'recharts';
import type { DashboardData } from '../../types';
import { useDashboardStore } from '../../store/useDashboardStore';
import { SKILL_COLORS, hexToRgba, fmtXP } from '../../utils/colors';
import './Charts.css';

interface Props { data: DashboardData; }

interface GapCard {
  playerName: string;
  skill: string;
  rows: Array<{
    label: string;
    name: string;
    experience: number;
    rank: number;
    isTarget: boolean;
  }>;
}

export function GapChart({ data }: Props) {
  const { selectedPlayer } = useDashboardStore();
  const { metadata, latest_snapshot } = data;
  const { watched, ranking_types } = metadata;

  const [activeSkill, setActiveSkill] = useState(ranking_types[0] ?? 'Experience');

  // Gera cards apenas para a skill ativa
  const cards: GapCard[] = [];

  for (const name of watched) {
    const allInSkill = latest_snapshot
      .filter(s => s.ranking_type === activeSkill)
      .sort((a, b) => a.rank - b.rank);

    const playerRow = allInSkill.find(
      s => s.name.toLowerCase() === name.toLowerCase()
    );
    if (!playerRow) continue;

    const rk = playerRow.rank;
    const window = allInSkill.filter(
      s => s.rank >= Math.max(1, rk - 3) && s.rank <= rk + 3
    );

    cards.push({
      playerName: name,
      skill: activeSkill,
      rows: window.map(row => ({
        label: `#${row.rank} ${row.name}`,
        name: row.name,
        experience: row.experience,
        rank: row.rank,
        isTarget: row.name.toLowerCase() === name.toLowerCase(),
      })),
    });
  }

  const color = SKILL_COLORS[activeSkill] ?? '#d4af37';

  const GapTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="custom-tooltip">
        <div className="custom-tooltip-label">{d.name}</div>
        <div className="custom-tooltip-row">
          <span>Posição</span><span>#{d.rank}</span>
        </div>
        <div className="custom-tooltip-row">
          <span>XP</span>
          <span style={{ color: d.isTarget ? '#d4af37' : 'var(--text)' }}>
            {fmtXP(d.experience)}
          </span>
        </div>
      </div>
    );
  };

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

      {cards.length === 0 ? (
        <div className="chart-card">
          <div className="chart-empty">
            Nenhum jogador monitorado encontrado no ranking de {activeSkill}.
          </div>
        </div>
      ) : (
        <div className="chart-grid-2">
          {cards.map((gc, idx) => {
            const dimmed = selectedPlayer !== null && selectedPlayer !== gc.playerName;
            const cardH = Math.max(180, gc.rows.length * 40 + 30);

            return (
              <div
                key={idx}
                className="chart-card"
                style={{ opacity: dimmed ? 0.25 : 1, transition: 'opacity 0.25s' }}
              >
                <div className="chart-title" style={{ color }}>
                  Gap Competitivo — {gc.playerName}
                </div>
                <ResponsiveContainer width="100%" height={cardH}>
                  <BarChart
                    data={gc.rows}
                    layout="vertical"
                    margin={{ top: 4, right: 64, left: 0, bottom: 4 }}
                  >
                    <XAxis type="number" hide />
                    <YAxis
                      type="category"
                      dataKey="label"
                      width={176}
                      tick={({ x, y, payload, index }) => {
                        const entry = gc.rows[index];
                        return (
                          <text
                            x={x} y={y} dy={4}
                            textAnchor="end"
                            fill={entry?.isTarget ? '#d4af37' : 'var(--muted)'}
                            fontFamily="Fira Code, monospace"
                            fontSize={11}
                            fontWeight={entry?.isTarget ? 700 : 400}
                          >
                            {payload.value}
                          </text>
                        );
                      }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip content={<GapTooltip />} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
                    <Bar
                      dataKey="experience"
                      radius={[0, 3, 3, 0]}
                      label={{
                        position: 'right',
                        formatter: (v: any) => fmtXP(v as number),
                        fill: 'var(--muted)',
                        fontSize: 11,
                        fontFamily: 'Fira Code',
                      }}
                    >
                      {gc.rows.map((entry, i) => (
                        <Cell
                          key={i}
                          fill={entry.isTarget ? hexToRgba('#d4af37', 0.35) : hexToRgba(color, 0.15)}
                          stroke={entry.isTarget ? '#d4af37' : 'transparent'}
                          strokeWidth={entry.isTarget ? 2 : 0}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
