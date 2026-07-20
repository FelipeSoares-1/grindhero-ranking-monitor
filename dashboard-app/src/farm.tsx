// farm.tsx — Página pública standalone "Top Farmers do Dia"
// Mostra apenas a velocidade de farm (XP ganho no dia), sem senha e sem controles pessoais.
import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer,
} from 'recharts';
import type { DashboardData } from './types';
import { SKILL_COLORS, fmtXP } from './utils/colors';
import './index.css';
import './farm.css';

const MEDALS = ['🥇', '🥈', '🥉'];

function hexToRgba(hex: string, a: number): string {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${a})`;
}

function fmtDateHora(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  });
}

function TopFarmers() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeSkill, setActiveSkill] = useState<string>('');

  useEffect(() => {
    fetch(`/data.json?t=${Date.now()}`, { cache: 'no-store' })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() as Promise<DashboardData>; })
      .then((d: DashboardData) => {
        setData(d);
        setActiveSkill(d.metadata.ranking_types[0] ?? 'Experience');
      })
      .catch(e => setError(e.message));
  }, []);

  if (error) return <div className="tf-msg">Erro ao carregar dados</div>;
  if (!data)  return <div className="tf-msg">Carregando…</div>;

  const { metadata, velocity } = data;
  const color = SKILL_COLORS[activeSkill] ?? '#d4af37';
  const velData = (velocity[activeSkill] ?? []).slice(0, 15);

  const chartData = velData.map((v, i) => ({
    name: `${i < 3 ? MEDALS[i] : `${i + 1}º`} ${v.name}`,
    rawName: v.name,
    xp_day: v.xp_day,
    label: v.label,
  }));

  const chartH = Math.max(260, chartData.length * 30 + 20);

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="tf-tooltip">
        <div className="tf-tooltip-name">{d.rawName}</div>
        <div className="tf-tooltip-row">
          <span>XP ganho</span>
          <span style={{ color }}>{d.label}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="tf-wrap">
      {/* Cabeçalho */}
      <div className="tf-header">
        <img
          className="tf-logo" src="/red-skull-logo.webp" alt="Red Skull"
          onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
        />
        <div>
          <div className="tf-title">Top Farmers <span>do Dia</span></div>
          <div className="tf-sub">quem mais farmou nas últimas horas · {metadata.server} · Red Skull</div>
        </div>
      </div>

      {/* Abas de skill */}
      <div className="tf-tabs">
        {metadata.ranking_types.map(rt => {
          const c = SKILL_COLORS[rt] ?? '#d4af37';
          const on = activeSkill === rt;
          return (
            <button
              key={rt}
              className={`tf-tab ${on ? 'active' : ''}`}
              onClick={() => setActiveSkill(rt)}
              style={on ? { borderColor: c, backgroundColor: hexToRgba(c, 0.18), color: '#fff' } : {}}
            >
              {rt}
            </button>
          );
        })}
      </div>

      {/* Gráfico */}
      <div className="tf-card">
        <div className="tf-card-title" style={{ color }}>Velocidade de Farm — {activeSkill}</div>
        {velData.length === 0 ? (
          <div className="tf-msg" style={{ minHeight: 180 }}>Sem dados nesta skill ainda</div>
        ) : (
          <ResponsiveContainer width="100%" height={chartH}>
            <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 62, left: 0, bottom: 0 }}>
              <XAxis type="number" hide />
              <YAxis
                type="category" dataKey="name" width={172}
                tick={({ y, payload }: any) => (
                  <text x={4} y={y} dy={4} textAnchor="start"
                    fill="var(--muted)" fontSize={11} fontFamily="Fira Code, monospace">
                    {payload.value}
                  </text>
                )}
                axisLine={false} tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar
                dataKey="xp_day" radius={[0, 3, 3, 0]}
                label={{ position: 'right', formatter: (v: any) => fmtXP(v as number), fill: 'var(--muted)', fontSize: 11, fontFamily: 'Fira Code' }}
              >
                {chartData.map((entry, i) => (
                  <Cell
                    key={entry.name}
                    fill={i === 0 ? '#d4af37' : hexToRgba(color, i < 3 ? 0.85 : 0.55)}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Rodapé */}
      <div className="tf-footer">
        <span>Atualizado a cada 30 min · última coleta {fmtDateHora(metadata.ultima_coleta)}</span>
      </div>
    </div>
  );
}

createRoot(document.getElementById('farm-root')!).render(
  <StrictMode>
    <TopFarmers />
  </StrictMode>,
);
