// components/TopMovers.tsx — Quem se destacou no dia (maiores subidas/quedas de rank)
import { useState, useMemo } from 'react';
import type { DashboardData } from '../types';
import { useDashboardStore } from '../store/useDashboardStore';
import './TopMovers.css';

interface Props { data: DashboardData; }

const MEDALS = ['🥇', '🥈', '🥉'];

function getMedal(i: number): string {
  return MEDALS[i] ?? `${i + 1}º`;
}

function fmtDate(d: string) {
  const [y, m, day] = d.split('-');
  return `${day}/${m}/${y.slice(2)}`;
}

export function TopMovers({ data }: Props) {
  const { history, metadata } = data;
  const { ranking_types, watched } = metadata;
  const { toggleSelectedPlayer } = useDashboardStore();

  const [activeSkill, setActiveSkill] = useState(ranking_types[0] ?? 'Experience');

  // Todos os dias disponíveis no history (mais recente primeiro)
  const allDates = useMemo(() => {
    const set = new Set<string>();
    history.forEach(h => h.points.forEach(p => set.add(p.date)));
    return [...set].sort().reverse();
  }, [history]);

  const [selectedDate, setSelectedDate] = useState(allDates[0] ?? '');

  // Calcula movers: rank_delta = rank_anterior - rank_atual (positivo = subiu)
  const movers = useMemo(() => {
    const entries = history.filter(h => h.ranking_type === activeSkill);
    const result: { name: string; delta: number; currRank: number; prevRank: number }[] = [];

    for (const entry of entries) {
      const idx = entry.points.findIndex(p => p.date === selectedDate);
      if (idx <= 0) continue;
      const curr = entry.points[idx];
      const prev = entry.points[idx - 1];
      const delta = prev.rank - curr.rank;
      result.push({ name: entry.name, delta, currRank: curr.rank, prevRank: prev.rank });
    }

    return result;
  }, [history, activeSkill, selectedDate]);

  const gainers = [...movers].filter(m => m.delta > 0).sort((a, b) => b.delta - a.delta).slice(0, 7);
  const losers  = [...movers].filter(m => m.delta < 0).sort((a, b) => a.delta - b.delta).slice(0, 7);
  const stable  = movers.filter(m => m.delta === 0).length;

  const isWatched = (name: string) =>
    watched.some(w => w.toLowerCase() === name.toLowerCase());

  const isToday = selectedDate === allDates[0];

  return (
    <div className="top-movers">
      {/* Skill tabs */}
      <div className="tabs-bar">
        {ranking_types.map(rt => (
          <button
            key={rt}
            className={`tab-btn ${activeSkill === rt ? 'active' : ''}`}
            onClick={() => setActiveSkill(rt)}
          >{rt}</button>
        ))}
      </div>

      {/* Seletor de data + estatística */}
      <div className="tm-controls">
        <div className="tm-date-row">
          <span className="tm-date-label">📅 Data:</span>
          <select
            value={selectedDate}
            onChange={e => setSelectedDate(e.target.value)}
            className="tm-date-select"
          >
            {allDates.map((d, i) => (
              <option key={d} value={d}>
                {fmtDate(d)}{i === 0 ? ' (hoje)' : ''}
              </option>
            ))}
          </select>
        </div>
        <div className="tm-stats">
          <span className="tm-stat-chip tm-stat-up">⬆ {gainers.length} subiram</span>
          <span className="tm-stat-chip tm-stat-down">⬇ {losers.length} caíram</span>
          <span className="tm-stat-chip">= {stable} estáveis</span>
        </div>
      </div>

      {movers.length === 0 ? (
        <div className="tm-empty-full">
          Sem dados suficientes para {fmtDate(selectedDate)} — necessário pelo menos 2 dias consecutivos de coleta.
        </div>
      ) : (
        <div className="tm-grid">
          {/* Maiores Subidas */}
          <div className="tm-col">
            <div className="tm-col-title tm-col-title--up">⬆ Maiores Subidas</div>
            {gainers.length === 0
              ? <div className="tm-empty">Nenhuma subida {isToday ? 'hoje' : 'neste dia'}</div>
              : gainers.map((m, i) => (
                <div
                  key={m.name}
                  className={`tm-row tm-row--up ${isWatched(m.name) ? 'tm-row--watched' : ''}`}
                  onClick={() => toggleSelectedPlayer(m.name)}
                  title="Clique para filtrar"
                >
                  <span className="tm-medal">{getMedal(i)}</span>
                  <span className="tm-name">{m.name}</span>
                  <span className="tm-rank-now">#{m.currRank}</span>
                  <span className="tm-delta tm-delta--up">+{m.delta} pos</span>
                </div>
              ))
            }
          </div>

          {/* Maiores Quedas */}
          <div className="tm-col">
            <div className="tm-col-title tm-col-title--down">⬇ Maiores Quedas</div>
            {losers.length === 0
              ? <div className="tm-empty">Nenhuma queda {isToday ? 'hoje' : 'neste dia'}</div>
              : losers.map((m, i) => (
                <div
                  key={m.name}
                  className={`tm-row tm-row--down ${isWatched(m.name) ? 'tm-row--watched' : ''}`}
                  onClick={() => toggleSelectedPlayer(m.name)}
                  title="Clique para filtrar"
                >
                  <span className="tm-medal">{getMedal(i)}</span>
                  <span className="tm-name">{m.name}</span>
                  <span className="tm-rank-now">#{m.currRank}</span>
                  <span className="tm-delta tm-delta--down">{m.delta} pos</span>
                </div>
              ))
            }
          </div>
        </div>
      )}
    </div>
  );
}
