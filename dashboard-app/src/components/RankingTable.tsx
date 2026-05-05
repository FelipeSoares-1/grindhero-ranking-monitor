// components/RankingTable.tsx — Tabela completa Top 50 com cross-filter highlight
import { useMemo } from 'react';
import type { DashboardData } from '../types';
import { useDashboardStore } from '../store/useDashboardStore';
import { SKILL_COLORS, fmtXP } from '../utils/colors';
import './RankingTable.css';

interface Props { data: DashboardData; }

export function RankingTable({ data }: Props) {
  const { selectedPlayer, toggleSelectedPlayer, activeSkill, setActiveSkill } = useDashboardStore();
  const { metadata, latest_snapshot, deltas } = data;
  const { ranking_types, watched } = metadata;

  const tableRows = useMemo(() => {
    return latest_snapshot
      .filter(s => s.ranking_type === activeSkill)
      .sort((a, b) => a.rank - b.rank);
  }, [latest_snapshot, activeSkill]);

  const skillColor = SKILL_COLORS[activeSkill] ?? '#d4af37';

  function getDelta(pid: string, rt: string) {
    return deltas[`${pid}_${rt}`] ?? null;
  }

  function rankClass(rank: number) {
    if (rank === 1) return 'td-rank top1';
    if (rank <= 3)  return 'td-rank top3';
    return 'td-rank';
  }

  function deltaEl(v: number | null | undefined, isRank = false) {
    if (v == null || v === 0) return <span className="delta-neutral">±0</span>;
    const cls = v > 0 ? 'delta-up' : 'delta-down';
    const sign = v > 0 ? '+' : '';
    const text = isRank ? `${sign}${v}` : `${sign}${fmtXP(v)}`;
    return <span className={cls}>{text}</span>;
  }

  return (
    <div>
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

      <div className="rank-table-wrap">
        <div className="rank-table-header" style={{ '--rt-clr': skillColor } as React.CSSProperties}>
          <span style={{ color: skillColor, fontFamily: 'Anton', fontSize: '0.95rem', letterSpacing: 1, textTransform: 'uppercase' }}>
            {activeSkill}
          </span>
          <span className="rt-count">{tableRows.length} jogadores</span>
        </div>
        <table className="rank-table">
          <thead>
            <tr>
              <th>Rank</th><th>Nome</th><th>Level</th>
              <th>XP Total</th><th>XP +/-</th><th>Pos +/-</th>
            </tr>
          </thead>
          <tbody>
            {tableRows.map(row => {
              const isWatched = watched.some(w => w.toLowerCase() === row.name.toLowerCase());
              const dimmed = selectedPlayer !== null && selectedPlayer !== row.name && !isWatched;
              const delta = getDelta(row.player_id, row.ranking_type);
              return (
                <tr
                  key={`${row.player_id}-${row.ranking_type}`}
                  className={isWatched ? 'tr-highlight' : ''}
                  style={{ opacity: dimmed ? 0.35 : 1, transition: 'opacity 0.25s', cursor: 'pointer' }}
                  onClick={() => toggleSelectedPlayer(row.name)}
                >
                  <td className={rankClass(row.rank)}>#{row.rank}</td>
                  <td className="td-name">
                    {row.name}
                    {isWatched && (
                      <img
                        src="https://redskull.space/images/red-skull-logo.webp"
                        alt=""
                        className="skull-badge"
                        onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                      />
                    )}
                  </td>
                  <td className="td-num">Lv {row.level}</td>
                  <td className="td-num">{fmtXP(row.experience)}</td>
                  <td className="td-delta">{deltaEl(delta?.xp_delta)}</td>
                  <td className="td-delta">{deltaEl(delta?.rank_delta, true)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
