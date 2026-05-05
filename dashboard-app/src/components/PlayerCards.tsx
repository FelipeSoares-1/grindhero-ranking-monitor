// components/PlayerCards.tsx — Cards dos jogadores monitorados com stats e digest
import type { DashboardData } from '../types';
import { useDashboardStore } from '../store/useDashboardStore';
import { SKILL_COLORS, fmtXP } from '../utils/colors';
import { TrendingUp, TrendingDown, Minus, X } from 'lucide-react';
import './PlayerCards.css';

interface Props {
  data: DashboardData;
  watchedPlayers: string[];
  onRemovePlayer: (name: string) => void;
}

const SKILL_ICONS: Record<string, string> = {
  Experience: '★', Melee: '⚔', Shielding: '🛡',
  Magic: '✦', Distance: '🏹', Taming: '🐾',
};

function DeltaEl({ v, isRank = false }: { v: number | null | undefined; isRank?: boolean }) {
  if (v == null || v === 0) return <span className="delta-neutral"><Minus size={11} /> 0</span>;
  const cls = v > 0 ? 'delta-up' : 'delta-down';
  const Icon = v > 0 ? TrendingUp : TrendingDown;
  const text = isRank ? `${v > 0 ? '+' : ''}${v}` : fmtXP(v);
  return <span className={cls}><Icon size={11} /> {v > 0 && !isRank ? '+' : ''}{text}</span>;
}

function PlayerCard({
  name, data, onRemove, isSelected, onClick,
}: {
  name: string;
  data: DashboardData;
  onRemove: () => void;
  isSelected: boolean;
  onClick: () => void;
}) {
  const { latest_snapshot, deltas } = data;

  const rows = latest_snapshot
    .filter(s => s.name.toLowerCase() === name.toLowerCase())
    .sort((a, b) => a.rank - b.rank);

  const bestRank = rows.length > 0 ? Math.min(...rows.map(r => r.rank)) : null;

  if (rows.length === 0) {
    return (
      <div className={`player-card player-card--absent ${isSelected ? 'selected' : ''}`}>
        <div className="pc-header">
          <span className="pc-name">{name}</span>
          <button className="remove-player-btn" onClick={(e) => { e.stopPropagation(); onRemove(); }} title="Remover monitoramento">
            <X size={10} /> Remover
          </button>
        </div>
        <p className="pc-absent-msg">Fora do top 50 em todos os rankings hoje.</p>
      </div>
    );
  }

  return (
    <div
      className={`player-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="pc-header">
        <span className="pc-name">{name}</span>
        <div className="pc-badges">
          <span className="badge badge--red">{rows.length} rankings</span>
          {bestRank && <span className="badge badge--gold">#{bestRank} melhor</span>}
          <button
            className="remove-player-btn"
            onClick={(e) => { e.stopPropagation(); onRemove(); }}
            title="Remover do monitoramento"
          >
            <X size={10} /> Remover
          </button>
        </div>
      </div>

      <div className="skill-list">
        {rows.map(row => {
          const clr = SKILL_COLORS[row.ranking_type] ?? '#d4af37';
          const icon = SKILL_ICONS[row.ranking_type] ?? '•';
          const delta = deltas[`${row.player_id}_${row.ranking_type}`] ?? null;

          return (
            <div
              key={row.ranking_type}
              className="skill-row"
              style={{ '--skill-clr': clr } as React.CSSProperties}
            >
              <span className="skill-icon">{icon}</span>
              <span className="skill-name">{row.ranking_type}</span>
              <span className="skill-rank">#{row.rank}</span>
              <span className="skill-lv">Lv {row.level}</span>
              <span className="skill-xp">{fmtXP(row.experience)}</span>
              <span className="skill-delta">
                <DeltaEl v={delta?.xp_delta} />
              </span>
              <span className="skill-rank-delta">
                <DeltaEl v={delta?.rank_delta} isRank />
              </span>
              <span />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DigestBox({ data, watchedPlayers }: { data: DashboardData; watchedPlayers: string[] }) {
  const { toggleSelectedPlayer } = useDashboardStore();
  const { latest_snapshot, deltas } = data;
  const hasDeltas = Object.keys(deltas).length > 0;

  if (!hasDeltas) {
    return (
      <div className="digest-box">
        <p className="digest-empty">Digest disponível a partir da segunda coleta (amanhã).</p>
      </div>
    );
  }

  return (
    <div className="digest-box">
      <ul className="digest-list">
        {watchedPlayers.map(name => {
          const rows = latest_snapshot
            .filter(s => s.name.toLowerCase() === name.toLowerCase())
            .sort((a, b) => a.rank - b.rank);

          if (rows.length === 0) {
            return <li key={name}><b>{name}</b>: fora do top 50.</li>;
          }

          const parts = rows.map(row => {
            const delta = deltas[`${row.player_id}_${row.ranking_type}`];
            if (!delta) return null;
            const clr = SKILL_COLORS[row.ranking_type] ?? '#d4af37';
            const rkSign = delta.rank_delta > 0 ? '+' : '';
            return (
              <span key={row.ranking_type} style={{ color: clr }}>
                {row.ranking_type} #{row.rank} (pos {rkSign}{delta.rank_delta}, {fmtXP(delta.xp_delta)} XP)
              </span>
            );
          }).filter(Boolean);

          return (
            <li key={name}>
              <b onClick={() => toggleSelectedPlayer(name)}>{name}</b>:{' '}
              {parts.reduce<React.ReactNode[]>((acc, el, i) => {
                if (i > 0) acc.push(' • ');
                acc.push(el);
                return acc;
              }, [])}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function PlayerCards({ data, watchedPlayers, onRemovePlayer }: Props) {
  const { selectedPlayer, toggleSelectedPlayer } = useDashboardStore();

  return (
    <div>
      <DigestBox data={data} watchedPlayers={watchedPlayers} />
      <div className="player-grid">
        {watchedPlayers.map(name => (
          <PlayerCard
            key={name}
            name={name}
            data={data}
            isSelected={selectedPlayer === name}
            onClick={() => toggleSelectedPlayer(name)}
            onRemove={() => onRemovePlayer(name)}
          />
        ))}
        {watchedPlayers.length === 0 && (
          <div style={{ color: 'var(--muted)', fontSize: '0.85rem', padding: '24px 0' }}>
            Nenhum jogador monitorado. Use o gerenciador abaixo para adicionar.
          </div>
        )}
      </div>
    </div>
  );
}
