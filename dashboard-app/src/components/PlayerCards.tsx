// components/PlayerCards.tsx — Cards dos jogadores monitorados com stats e digest
import { useEffect, useState } from 'react';
import type { DashboardData } from '../types';
import { useDashboardStore } from '../store/useDashboardStore';
import { SKILL_COLORS, fmtXP } from '../utils/colors';
import { TrendingUp, TrendingDown, Minus, X, Expand, ChevronDown } from 'lucide-react';
import './PlayerCards.css';

interface Props {
  data: DashboardData;
  watchedPlayers: string[];
  onRemovePlayer: (name: string) => void;
  onOpenDrawer: (name: string) => void;   // ← drawer global do App
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
  name, data, onRemove, isSelected, onClick, onOpenDrawer,
}: {
  name: string;
  data: DashboardData;
  onRemove: () => void;
  isSelected: boolean;
  onClick: () => void;      // cross-filter
  onOpenDrawer: () => void; // abre o drawer de detalhe
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

  // Hint visual quando selecionado (cross-filter ativo)
  const selectedHint = isSelected ? ' · filtro ativo' : '';

  return (
    <div
      className={`player-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}        /* clique no card = cross-filter */
      title={`Clique para filtrar${selectedHint}`}
    >
      <div className="pc-header">
        <span className="pc-name">{name}</span>
        <div className="pc-badges">
          <span className="badge badge--red">{rows.length} rankings</span>
          {bestRank && <span className="badge badge--gold">#{bestRank} melhor</span>}
          {/* Botão de detalhe — abre o Drawer sem interferir no cross-filter */}
          <button
            className="detail-btn"
            onClick={(e) => { e.stopPropagation(); onOpenDrawer(); }}
            title="Ver detalhes do jogador"
          >
            <Expand size={12} />
          </button>
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

// Exportada para uso global no App.tsx (qualquer jogador, não só monitorados)
export function PlayerDrawer({ name, data, onClose }: {
  name: string; data: DashboardData; onClose: () => void;
}) {
  const { latest_snapshot, deltas, history, velocity } = data;
  const [farmDaysShown, setFarmDaysShown] = useState(7);
  const [rankDaysShown, setRankDaysShown] = useState(7);

  const rows = latest_snapshot
    .filter(s => s.name.toLowerCase() === name.toLowerCase())
    .sort((a, b) => a.rank - b.rank);

  const bestRow = rows.reduce<typeof rows[0] | null>(
    (best, r) => (!best || r.rank < best.rank ? r : best), null
  );

  const playerHistory = history.filter(h => h.name.toLowerCase() === name.toLowerCase());

  const daysMonitored = (() => {
    const allDates = new Set<string>();
    playerHistory.forEach(h => h.points.forEach(p => allDates.add(p.date)));
    return allDates.size;
  })();

  // XP Médio por dia
  const avgXpPerDay = (() => {
    const diffs: number[] = [];
    playerHistory
      .filter(h => h.ranking_type === 'Experience')
      .forEach(h => {
        for (let i = 1; i < h.points.length; i++) {
          const d = h.points[i].experience - h.points[i - 1].experience;
          if (d > 0) diffs.push(d);
        }
      });
    if (diffs.length === 0) return null;
    return Math.round(diffs.reduce((a, b) => a + b, 0) / diffs.length);
  })();

  // Rank Farm do Dia: posição no velocity
  function getFarmRank(rt: string): string {
    const vel = velocity[rt];
    if (!vel) return '—';
    const idx = vel.findIndex(v => v.name.toLowerCase() === name.toLowerCase());
    if (idx === -1) return '—';
    return `#${idx + 1} de ${vel.length}`;
  }

  // ── Farm do Dia: XP ganho por dia — só skills com histórico real do jogador ──
  const farmSkills = data.metadata.ranking_types.filter(
    skill => playerHistory.some(h => h.ranking_type === skill && h.points.length >= 2)
  );
  const farmDates = (() => {
    const dates = new Set<string>();
    playerHistory.forEach(h => h.points.forEach(p => dates.add(p.date)));
    return [...dates].sort().reverse(); // mais recente primeiro
  })();
  // Para cada data e skill: calcula delta de XP e nível
  function getFarmForDate(skill: string, date: string): { xpDelta: number; level: number; lvDelta: number } | null {
    const h = playerHistory.find(h => h.ranking_type === skill);
    if (!h) return null;
    const idx = h.points.findIndex(p => p.date === date);
    if (idx <= 0) return null;
    const cur  = h.points[idx];
    const prev = h.points[idx - 1];
    return {
      xpDelta: cur.experience - prev.experience,
      level:   cur.level,
      lvDelta: cur.level - prev.level,
    };
  }
  const farmHistory = farmDates; // usamos farmDates diretamente

  // ── Histórico de Rank: só skills com dados reais do jogador ──
  const rankSkills = data.metadata.ranking_types.filter(
    skill => playerHistory.some(h => h.ranking_type === skill && h.points.length > 0)
  );
  const rankDates = (() => {
    const dates = new Set<string>();
    playerHistory.forEach(h => h.points.forEach(p => dates.add(p.date)));
    return [...dates].sort().reverse();
  })();

  function getRankAtDate(skill: string, date: string): number | null {
    const h = playerHistory.find(h => h.ranking_type === skill);
    return h?.points.find(p => p.date === date)?.rank ?? null;
  }
  function getPrevRankAtDate(skill: string, date: string): number | null {
    const h = playerHistory.find(h => h.ranking_type === skill);
    if (!h) return null;
    const idx = h.points.findIndex(p => p.date === date);
    if (idx <= 0) return null;
    return h.points[idx - 1].rank;
  }

  function fmtDate(d: string) {
    const [y, m, day] = d.split('-');
    return `${day}/${m}/${y.slice(2)}`;
  }

  // Fechar com Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />
      <div className="drawer drawer--wide">
        {/* ── Header ── */}
        <div className="drawer-header">
          <div>
            <div className="drawer-name">{name}</div>
            <div className="drawer-sub">
              Em {rows.length} ranking(s) · Acompanhado há {daysMonitored} dia(s)
            </div>
          </div>
          <button className="drawer-close" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="drawer-body">
          {/* ── VISÃO GERAL ── */}
          <div className="drawer-section-title">Visão Geral</div>
          <div className="drawer-stat-grid drawer-stat-grid--4">
            <div className="drawer-stat">
              <div className="drawer-stat-label">Melhor Posição</div>
              <div className="drawer-stat-value">{bestRow ? `#${bestRow.rank}` : '—'}</div>
              {bestRow && <div className="drawer-stat-sub">em {bestRow.ranking_type}</div>}
            </div>
            <div className="drawer-stat">
              <div className="drawer-stat-label">XP Médio / Dia</div>
              <div className="drawer-stat-value drawer-stat-value--sm">
                {avgXpPerDay ? fmtXP(avgXpPerDay) : '—'}
              </div>
              <div className="drawer-stat-sub">Experience</div>
            </div>
            <div className="drawer-stat">
              <div className="drawer-stat-label">Rankings Ativos</div>
              <div className="drawer-stat-value drawer-stat-value--sm">
                {rows.length} / {data.metadata.ranking_types.length}
              </div>
            </div>
            <div className="drawer-stat">
              <div className="drawer-stat-label">Dias Monitorado</div>
              <div className="drawer-stat-value">{daysMonitored}</div>
            </div>
          </div>

          {/* ── POSIÇÕES ATUAIS ── */}
          {rows.length > 0 && (
            <div>
              <div className="drawer-section-title">Posições Atuais</div>
              <div className="drawer-skill-grid">
                {rows.map(row => {
                  const clr = SKILL_COLORS[row.ranking_type] ?? '#d4af37';
                  const icon = SKILL_ICONS[row.ranking_type] ?? '•';
                  const delta = deltas[`${row.player_id}_${row.ranking_type}`] ?? null;
                  const xpDelta = delta?.xp_delta ?? 0;
                  const rkDelta = delta?.rank_delta ?? 0;
                  const farmRank = getFarmRank(row.ranking_type);
                  const hasFarm = farmRank !== '—';
                  return (
                    <div key={row.ranking_type} className="drawer-skill-card"
                      style={{ '--skill-clr': clr } as React.CSSProperties}>
                      <div className="dsc-header">
                        <div>
                          <div className="dsc-name"><span>{icon}</span> {row.ranking_type}</div>
                          <div className="dsc-lvxp">Lv {row.level} · {fmtXP(row.experience)} XP total</div>
                        </div>
                        <div className="dsc-rank">#{row.rank}</div>
                      </div>
                      <div className="dsc-deltas">
                        <div className="dsc-delta-block">
                          <div className="dsc-delta-label">Ganhou no Dia</div>
                          <div className={`dsc-delta-value ${xpDelta > 0 ? 'delta-up' : xpDelta < 0 ? 'delta-down' : 'delta-neutral'}`}>
                            {xpDelta !== 0 ? (xpDelta > 0 ? '+' : '') : ''}{fmtXP(xpDelta)} XP
                          </div>
                        </div>
                        <div className="dsc-delta-block">
                          <div className="dsc-delta-label">Variação de Posição</div>
                          <div className={`dsc-delta-value ${rkDelta > 0 ? 'delta-up' : rkDelta < 0 ? 'delta-down' : 'delta-neutral'}`}>
                            {rkDelta === 0 ? '· sem mudança' : `${rkDelta > 0 ? '+' : ''}${rkDelta} pos`}
                          </div>
                        </div>
                        {hasFarm && (
                          <div className="dsc-delta-block">
                            <div className="dsc-delta-label">🔥 Rank Farm do Dia</div>
                            <div className="dsc-delta-value" style={{ color: '#ff9500' }}>{farmRank}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── FARM DO DIA (todos os skills por data) ── */}
          {farmHistory.length > 0 && (
            <div>
              <div className="drawer-section-title">📅 Farm do Dia — Histórico</div>
              <div className="dh-rank-wrap">
                <div className="dh-farm-table">
                  {/* Header dinâmico com todos os skills presentes */}
                  <div className="dh-farm-header"
                    style={{ gridTemplateColumns: `72px repeat(${farmSkills.length}, 1fr)` }}>
                    <span className="dh-rank-date-col">Data</span>
                    {farmSkills.map(s => (
                      <span key={s} className="dh-rank-skill-col"
                        style={{ color: SKILL_COLORS[s] ?? 'var(--muted)' }}>
                        {s.slice(0, 4)}
                      </span>
                    ))}
                  </div>
                  {farmHistory.slice(0, farmDaysShown).map(date => (
                    <div key={date} className="dh-farm-row"
                      style={{ gridTemplateColumns: `72px repeat(${farmSkills.length}, 1fr)` }}>
                      <span className="dh-rank-date-col">{fmtDate(date)}</span>
                      {farmSkills.map(s => {
                        const f = getFarmForDate(s, date);
                        if (!f) return <span key={s} className="dh-farm-cell" style={{ color: 'var(--muted)' }}>—</span>;
                        const isGreat = f.xpDelta > (avgXpPerDay ?? 0) * 1.3;
                        const isLow   = f.xpDelta > 0 && f.xpDelta < (avgXpPerDay ?? 0) * 0.4;
                        const clr = isGreat ? '#2ecc71' : isLow ? 'var(--muted)' : (SKILL_COLORS[s] ?? 'var(--text)');
                        return (
                          <span key={s} className="dh-farm-cell" style={{ color: clr }}>
                            {f.xpDelta > 0 ? `+${fmtXP(f.xpDelta)}` : f.xpDelta === 0 ? '—' : fmtXP(f.xpDelta)}
                            {f.lvDelta > 0 && <span className="dh-lv-up"> ↑{f.lvDelta}</span>}
                          </span>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
              {farmHistory.length > farmDaysShown && (
                <button className="dh-more-btn" onClick={() => setFarmDaysShown(n => n + 7)}>
                  <ChevronDown size={13} /> Ver mais {Math.min(7, farmHistory.length - farmDaysShown)} dias
                </button>
              )}
            </div>
          )}

          {/* ── HISTÓRICO DE RANK (todas as skills por data) ── */}
          {rankDates.length > 0 && (
            <div>
              <div className="drawer-section-title">📊 Histórico de Rank por Skill</div>
              <div className="dh-rank-wrap">
                <div className="dh-rank-table">
                  <div className="dh-rank-header"
                    style={{ gridTemplateColumns: `72px repeat(${rankSkills.length}, 1fr)` }}>
                    <span className="dh-rank-date-col">Data</span>
                    {rankSkills.map(s => (
                      <span key={s} className="dh-rank-skill-col"
                        style={{ color: SKILL_COLORS[s] ?? 'var(--muted)' }}>
                        {s.slice(0, 4)}
                      </span>
                    ))}
                  </div>
                  {rankDates.slice(0, rankDaysShown).map(date => (
                    <div key={date} className="dh-rank-row"
                      style={{ gridTemplateColumns: `72px repeat(${rankSkills.length}, 1fr)` }}>
                      <span className="dh-rank-date-col">{fmtDate(date)}</span>
                      {rankSkills.map(s => {
                        const rank = getRankAtDate(s, date);
                        const prev = getPrevRankAtDate(s, date);
                        const delta = rank != null && prev != null ? prev - rank : null;
                        return (
                          <span key={s} className="dh-rank-skill-col">
                            {rank != null ? (
                              <>
                                <span style={{ color: SKILL_COLORS[s] ?? 'var(--text)', fontWeight: 600 }}>
                                  #{rank}
                                </span>
                                {delta != null && delta !== 0 && (
                                  <span className={`dh-rank-arrow ${delta > 0 ? 'delta-up' : 'delta-down'}`}>
                                    {delta > 0 ? '▲' : '▼'}
                                  </span>
                                )}
                              </>
                            ) : (
                              <span style={{ color: 'var(--muted)' }}>—</span>
                            )}
                          </span>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
              {rankDates.length > rankDaysShown && (
                <button className="dh-more-btn" onClick={() => setRankDaysShown(n => n + 7)}>
                  <ChevronDown size={13} /> Ver mais {Math.min(7, rankDates.length - rankDaysShown)} dias
                </button>
              )}
            </div>
          )}

          {rows.length === 0 && (
            <div style={{ color: 'var(--muted)', fontSize: '0.83rem', textAlign: 'center', padding: '24px 0' }}>
              {name} não aparece no top 50 em nenhum ranking hoje.
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export function PlayerCards({ data, watchedPlayers, onRemovePlayer, onOpenDrawer }: Props) {
  const { selectedPlayer, toggleSelectedPlayer } = useDashboardStore();
  // Sem estado local de drawer — controlado pelo App.tsx

  return (
    <div>
      <DigestBox data={data} watchedPlayers={watchedPlayers} />

      {/* Dica de UX: clique no card = cross-filter | botão ⤢ = detalhes */}
      <div style={{ fontSize: '0.65rem', color: 'var(--muted)', marginBottom: 10, letterSpacing: '0.4px' }}>
        Clique no card para ativar filtro cruzado nos gráficos &nbsp;·&nbsp;
        Clique em <Expand size={10} style={{ verticalAlign: 'middle' }} /> para ver detalhes
      </div>

      <div className="player-grid">
        {watchedPlayers.map(name => (
          <PlayerCard
            key={name}
            name={name}
            data={data}
            isSelected={selectedPlayer === name}
            onClick={() => toggleSelectedPlayer(name)}
            onOpenDrawer={() => onOpenDrawer(name)}
            onRemove={() => onRemovePlayer(name)}
          />
        ))}
        {watchedPlayers.length === 0 && (
          <div style={{ color: 'var(--muted)', fontSize: '0.85rem', padding: '24px 0' }}>
            Nenhum jogador monitorado. Use o gerenciador acima para adicionar.
          </div>
        )}
      </div>

    </div>
  );
}

