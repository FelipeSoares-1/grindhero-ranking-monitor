// components/GoalTracker.tsx — Fazedor de Metas com meta diária dinâmica
import { useState, useEffect } from 'react';
import type { DashboardData, SnapshotEntry } from '../types';
import { fmtXP } from '../utils/colors';
import { X, Target } from 'lucide-react';
import './GoalTracker.css';

interface Goal {
  id: string;
  player: string;
  skill: string;
  targetRank: number;
  targetDate: string;   // "YYYY-MM-DD" — prazo final
  xpAtCreation: number; // XP do jogador no momento em que a meta foi criada
  createdAt: string;    // ISO timestamp
}

interface Props { data: DashboardData; }

function loadGoals(): Goal[] {
  try { return JSON.parse(localStorage.getItem('gh_goals') ?? '[]'); } catch { return []; }
}

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function addDays(dateStr: string, n: number): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

function daysBetween(a: string, b: string): number {
  return Math.round((new Date(b).getTime() - new Date(a).getTime()) / 86_400_000);
}

function fmtDateBR(d: string) {
  const [y, m, day] = d.split('-');
  return `${day}/${m}/${y}`;
}

export function GoalTracker({ data }: Props) {
  const { metadata, latest_snapshot, history } = data;
  const { ranking_types, watched } = metadata;

  const [goals, setGoals]       = useState<Goal[]>(loadGoals);
  const [player, setPlayer]     = useState(watched[0] ?? '');
  const [skill, setSkill]       = useState(ranking_types[0] ?? 'Experience');
  const [targetRank, setTargetRank] = useState('');
  const [targetDate, setTargetDate] = useState(addDays(todayStr(), 30));

  useEffect(() => {
    localStorage.setItem('gh_goals', JSON.stringify(goals));
  }, [goals]);

  function getPlayerRow(playerName: string, skillType: string): SnapshotEntry | null {
    return latest_snapshot.find(
      s => s.name.toLowerCase() === playerName.toLowerCase() && s.ranking_type === skillType
    ) ?? null;
  }

  function addGoal() {
    const rank = parseInt(targetRank);
    if (!player || !rank || rank < 1 || !targetDate) return;
    const row = getPlayerRow(player, skill);
    const goal: Goal = {
      id: Date.now().toString(),
      player,
      skill,
      targetRank: rank,
      targetDate,
      xpAtCreation: row?.experience ?? 0,
      createdAt: new Date().toISOString(),
    };
    setGoals(prev => [...prev, goal]);
    setTargetRank('');
  }

  function removeGoal(id: string) {
    setGoals(prev => prev.filter(g => g.id !== id));
  }

  function getTargetRankXP(skillType: string, targetRankNum: number): number | null {
    return latest_snapshot.find(
      s => s.ranking_type === skillType && s.rank === targetRankNum
    )?.experience ?? null;
  }

  // Histórico diário de XP do jogador para um skill
  function getDailyXpHistory(playerName: string, skillType: string): Map<string, number> {
    const h = history.find(
      h => h.name.toLowerCase() === playerName.toLowerCase() && h.ranking_type === skillType
    );
    const map = new Map<string, number>();
    if (!h || h.points.length < 2) return map;
    for (let i = 1; i < h.points.length; i++) {
      const delta = h.points[i].experience - h.points[i - 1].experience;
      if (delta >= 0) map.set(h.points[i].date, delta);
    }
    return map;
  }

  return (
    <div className="goal-tracker">
      {/* ── Formulário ── */}
      <div className="gt-form">
        <select value={player} onChange={e => setPlayer(e.target.value)} className="gt-select">
          {watched.map(w => <option key={w} value={w}>{w}</option>)}
        </select>

        <select value={skill} onChange={e => setSkill(e.target.value)} className="gt-select">
          {ranking_types.map(rt => <option key={rt} value={rt}>{rt}</option>)}
        </select>

        <div className="gt-rank-input-wrap">
          <span className="gt-rank-label">Rank alvo #</span>
          <input
            type="number" min="1" max="500" placeholder="ex: 10"
            value={targetRank}
            onChange={e => setTargetRank(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addGoal()}
            className="gt-input"
          />
        </div>

        <div className="gt-date-wrap">
          <span className="gt-rank-label">Prazo</span>
          <input
            type="date"
            value={targetDate}
            min={addDays(todayStr(), 1)}
            onChange={e => setTargetDate(e.target.value)}
            className="gt-input gt-input--date"
          />
        </div>

        <button onClick={addGoal} disabled={!targetRank || !player || !targetDate} className="gt-add-btn">
          <Target size={13} /> Adicionar Meta
        </button>
      </div>

      {/* ── Metas ── */}
      {goals.length === 0 ? (
        <div className="gt-empty">
          <Target size={28} style={{ color: 'var(--muted)', opacity: 0.4 }} />
          <p>Nenhuma meta definida. Selecione um jogador, skill, rank alvo e prazo.</p>
        </div>
      ) : (
        <div className="gt-goals">
          {goals.map(goal => {
            const row      = getPlayerRow(goal.player, goal.skill);
            const targetXP = getTargetRankXP(goal.skill, goal.targetRank);
            const dailyXpH = getDailyXpHistory(goal.player, goal.skill);
            return (
              <GoalCard
                key={goal.id}
                goal={goal}
                playerRow={row}
                targetXP={targetXP}
                dailyXpHistory={dailyXpH}
                onRemove={() => removeGoal(goal.id)}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────
function GoalCard({ goal, playerRow, targetXP, dailyXpHistory, onRemove }: {
  goal: Goal;
  playerRow: SnapshotEntry | null;
  targetXP: number | null;
  dailyXpHistory: Map<string, number>;
  onRemove: () => void;
}) {
  const today        = todayStr();
  const createdDay   = goal.createdAt.slice(0, 10);
  const daysTotal    = Math.max(1, daysBetween(createdDay, goal.targetDate));
  const daysElapsed  = Math.max(0, Math.min(daysTotal, daysBetween(createdDay, today)));
  const daysRemain   = Math.max(0, daysBetween(today, goal.targetDate));

  const cardHead = (
    <div className="gt-card-head">
      <div className="gt-card-title">
        <span className="gt-player">{goal.player}</span>
        <span className="gt-skill">{goal.skill}</span>
        <span className="gt-arrow">→ #{goal.targetRank}</span>
        <span className="gt-deadline">até {fmtDateBR(goal.targetDate)}</span>
      </div>
      <button className="gt-remove" onClick={onRemove}><X size={13} /></button>
    </div>
  );

  if (!playerRow) {
    return (
      <div className="gt-card gt-card--warn">
        {cardHead}
        <div className="gt-msg">Jogador não encontrado no ranking atual de {goal.skill}.</div>
      </div>
    );
  }

  const currentXP  = playerRow.experience;
  const currentRnk = playerRow.rank;
  const achieved   = currentRnk <= goal.targetRank;

  if (achieved) {
    return (
      <div className="gt-card gt-card--done">
        {cardHead}
        <div className="gt-msg gt-msg--done">✅ Meta atingida! Posição atual: <strong>#{currentRnk}</strong></div>
      </div>
    );
  }

  if (daysRemain <= 0) {
    return (
      <div className="gt-card gt-card--warn">
        {cardHead}
        <div className="gt-msg">⏰ Prazo expirado. Posição atual: #{currentRnk} (meta: #{goal.targetRank})</div>
      </div>
    );
  }

  // XP necessário total (baseado no XP de quem está no rank alvo agora)
  const xpNeededTotal = targetXP ? targetXP - goal.xpAtCreation : null;
  const xpNeededNow   = targetXP ? targetXP - currentXP        : null;

  // XP ideal por dia (divisão linear)
  const idealXpPerDay = xpNeededTotal ? Math.ceil(xpNeededTotal / daysTotal) : null;

  // Acumulado real: soma XP ganho desde criação usando o histórico
  let xpEarnedSoFar = 0;
  if (daysElapsed > 0) {
    for (let d = 0; d < daysElapsed; d++) {
      const date = addDays(createdDay, d + 1);
      xpEarnedSoFar += dailyXpHistory.get(date) ?? 0;
    }
  }

  // XP ideal esperado até hoje
  const xpIdealSoFar = idealXpPerDay ? idealXpPerDay * daysElapsed : null;

  // Saldo (+ = excedente, - = déficit)
  const saldo = xpIdealSoFar != null ? xpEarnedSoFar - xpIdealSoFar : null;

  // Meta diária ajustada: (XP ainda faltando) / dias restantes
  const xpAdjustedPerDay = xpNeededNow && daysRemain > 0
    ? Math.ceil(xpNeededNow / daysRemain)
    : null;

  // Progresso em % do XP necessário total
  const progress = xpNeededTotal && xpNeededTotal > 0
    ? Math.min(99.9, (xpEarnedSoFar / xpNeededTotal) * 100)
    : null;

  const rankGap = currentRnk - goal.targetRank;

  return (
    <div className="gt-card">
      {cardHead}

      <div className="gt-stats-row">
        <div className="gt-stat">
          <div className="gt-stat-label">Posição Atual</div>
          <div className="gt-stat-value">#{currentRnk}</div>
          <div className="gt-stat-sub">{rankGap} pos. a subir</div>
        </div>
        <div className="gt-stat">
          <div className="gt-stat-label">XP Faltando</div>
          <div className="gt-stat-value">{xpNeededNow != null ? fmtXP(xpNeededNow) : '—'}</div>
          <div className="gt-stat-sub">para alcançar #{goal.targetRank}</div>
        </div>
        <div className="gt-stat">
          <div className="gt-stat-label">Meta / dia</div>
          <div className="gt-stat-value">{xpAdjustedPerDay ? fmtXP(xpAdjustedPerDay) : '—'}</div>
          <div className="gt-stat-sub">ajustada ({daysRemain}d restantes)</div>
        </div>
        <div className="gt-stat">
          <div className="gt-stat-label">Saldo Acumulado</div>
          <div className={`gt-stat-value ${saldo == null ? '' : saldo >= 0 ? 'gt-val--up' : 'gt-val--down'}`}>
            {saldo == null ? '—' : saldo >= 0 ? `+${fmtXP(saldo)}` : fmtXP(saldo)}
          </div>
          <div className="gt-stat-sub">
            {saldo == null ? '' : saldo >= 0 ? 'adiantado ✓' : 'déficit ⚠'}
          </div>
        </div>
      </div>

      {progress != null && (
        <div className="gt-progress-wrap">
          <div className="gt-progress-track">
            <div className="gt-progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <div className="gt-progress-info">
            <span>{progress.toFixed(1)}% do caminho percorrido</span>
            <span>{daysElapsed}d / {daysTotal}d · {daysRemain}d restantes</span>
          </div>
        </div>
      )}
    </div>
  );
}
