// components/GoalTracker.tsx — Fazedor de Metas
// Experience → meta por nível (fórmula validada)
// Demais skills → meta por rank (lookup no snapshot)
import { useState, useEffect } from 'react';
import type { DashboardData, SnapshotEntry } from '../types';
import { fmtXP } from '../utils/colors';
import { X, Target } from 'lucide-react';
import './GoalTracker.css';

// XP total acumulado para atingir o nível N — válido apenas para Experience
function totalXpForLevel(n: number): number {
  if (n <= 1) return 0;
  return Math.round((n - 1) * (100 * n * n - 500 * n + 1200) / 6);
}

interface Goal {
  id: string;
  player: string;
  skill: string;
  // Experience: targetLevel definido; demais skills: targetRank definido
  targetLevel?: number;
  targetRank?: number;
  targetDate: string;
  xpAtCreation: number;
  levelAtCreation: number;
  createdAt: string;
}

interface Props { data: DashboardData; }

function loadGoals(): Goal[] {
  try {
    const raw = JSON.parse(localStorage.getItem('gh_goals') ?? '[]') as any[];
    return raw.filter(g =>
      (g.skill === 'Experience' && g.targetLevel != null) ||
      (g.skill !== 'Experience' && g.targetRank != null)
    );
  } catch { return []; }
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
  const { metadata, latest_snapshot } = data;
  const { ranking_types, watched } = metadata;

  const [goals, setGoals]       = useState<Goal[]>(loadGoals);
  const [player, setPlayer]     = useState(watched[0] ?? '');
  const [skill, setSkill]       = useState(ranking_types[0] ?? 'Experience');
  const [targetLevel, setTargetLevel] = useState('');
  const [targetRank,  setTargetRank]  = useState('');
  const [targetDate, setTargetDate]   = useState(addDays(todayStr(), 30));

  const isExp = skill === 'Experience';

  useEffect(() => {
    localStorage.setItem('gh_goals', JSON.stringify(goals));
  }, [goals]);

  function getPlayerRow(playerName: string, skillType: string): SnapshotEntry | null {
    return latest_snapshot.find(
      s => s.name.toLowerCase() === playerName.toLowerCase() && s.ranking_type === skillType
    ) ?? null;
  }

  function addGoal() {
    if (!player || !targetDate) return;
    const row = getPlayerRow(player, skill);

    if (isExp) {
      const lvl = parseInt(targetLevel);
      if (!lvl || lvl < 2) return;
      if (row && lvl <= row.level) return;
      const goal: Goal = {
        id: Date.now().toString(),
        player, skill,
        targetLevel: lvl,
        targetDate,
        xpAtCreation: row?.experience ?? 0,
        levelAtCreation: row?.level ?? 1,
        createdAt: new Date().toISOString(),
      };
      setGoals(prev => [...prev, goal]);
      setTargetLevel('');
    } else {
      const rank = parseInt(targetRank);
      if (!rank || rank < 1) return;
      const goal: Goal = {
        id: Date.now().toString(),
        player, skill,
        targetRank: rank,
        targetDate,
        xpAtCreation: row?.experience ?? 0,
        levelAtCreation: row?.level ?? 1,
        createdAt: new Date().toISOString(),
      };
      setGoals(prev => [...prev, goal]);
      setTargetRank('');
    }
  }

  function removeGoal(id: string) {
    setGoals(prev => prev.filter(g => g.id !== id));
  }

  function getTargetRankXP(skillType: string, targetRankNum: number): number | null {
    return latest_snapshot.find(
      s => s.ranking_type === skillType && s.rank === targetRankNum
    )?.experience ?? null;
  }

  const canAdd = isExp ? !!targetLevel : !!targetRank;

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

        {isExp ? (
          <div className="gt-rank-input-wrap">
            <span className="gt-rank-label">Nível alvo</span>
            <input
              type="number" min="2" max="1000" placeholder="ex: 400"
              value={targetLevel}
              onChange={e => setTargetLevel(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addGoal()}
              className="gt-input"
            />
          </div>
        ) : (
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
        )}

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

        <button onClick={addGoal} disabled={!canAdd || !player || !targetDate} className="gt-add-btn">
          <Target size={13} /> Adicionar Meta
        </button>
      </div>

      {/* ── Metas ── */}
      {goals.length === 0 ? (
        <div className="gt-empty">
          <Target size={28} style={{ color: 'var(--muted)', opacity: 0.4 }} />
          <p>Nenhuma meta definida. Selecione um jogador, skill, alvo e prazo.</p>
        </div>
      ) : (
        <div className="gt-goals">
          {goals.map(goal => {
            const row = getPlayerRow(goal.player, goal.skill);
            const targetXP = goal.targetRank != null
              ? getTargetRankXP(goal.skill, goal.targetRank)
              : null;
            return (
              <GoalCard
                key={goal.id}
                goal={goal}
                playerRow={row}
                rankTargetXP={targetXP}
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
function GoalCard({ goal, playerRow, rankTargetXP, onRemove }: {
  goal: Goal;
  playerRow: SnapshotEntry | null;
  rankTargetXP: number | null; // XP do rank alvo (para skills não-Experience)
  onRemove: () => void;
}) {
  const today       = todayStr();
  const createdDay  = goal.createdAt.slice(0, 10);
  const daysTotal   = Math.max(1, daysBetween(createdDay, goal.targetDate));
  const daysElapsed = Math.max(0, Math.min(daysTotal, daysBetween(createdDay, today)));
  const daysRemain  = Math.max(0, daysBetween(today, goal.targetDate));

  const isExp = goal.skill === 'Experience';

  // XP alvo: fórmula (Experience) ou lookup do rank (demais)
  const targetXP = isExp && goal.targetLevel != null
    ? totalXpForLevel(goal.targetLevel)
    : rankTargetXP;

  // Label do alvo no cabeçalho
  const targetLabel = isExp
    ? `→ Lv ${goal.targetLevel}`
    : `→ #${goal.targetRank}`;

  const cardHead = (
    <div className="gt-card-head">
      <div className="gt-card-title">
        <span className="gt-player">{goal.player}</span>
        <span className="gt-skill">{goal.skill}</span>
        <span className="gt-arrow">{targetLabel}</span>
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
  const currentLvl = playerRow.level;
  const currentRnk = playerRow.rank;

  const achieved = isExp
    ? currentLvl >= (goal.targetLevel ?? 0)
    : currentRnk <= (goal.targetRank ?? 0);

  if (achieved) {
    const achievedMsg = isExp
      ? `✅ Meta atingida! Nível atual: Lv ${currentLvl}`
      : `✅ Meta atingida! Posição atual: #${currentRnk}`;
    return (
      <div className="gt-card gt-card--done">
        {cardHead}
        <div className="gt-msg gt-msg--done">{achievedMsg}</div>
      </div>
    );
  }

  if (daysRemain <= 0) {
    const expiredMsg = isExp
      ? `⏰ Prazo expirado. Nível atual: Lv ${currentLvl} (meta: Lv ${goal.targetLevel})`
      : `⏰ Prazo expirado. Posição atual: #${currentRnk} (meta: #${goal.targetRank})`;
    return (
      <div className="gt-card gt-card--warn">
        {cardHead}
        <div className="gt-msg">{expiredMsg}</div>
      </div>
    );
  }

  const xpNeededTotal = targetXP != null ? targetXP - goal.xpAtCreation : null;
  const xpNeededNow   = targetXP != null ? targetXP - currentXP        : null;
  const idealXpPerDay = xpNeededTotal && xpNeededTotal > 0 ? Math.ceil(xpNeededTotal / daysTotal) : null;

  // Acumulado real desde criação
  const xpEarnedSoFar = Math.max(0, currentXP - goal.xpAtCreation);

  const xpIdealSoFar    = idealXpPerDay ? idealXpPerDay * daysElapsed : null;
  const saldo           = xpIdealSoFar != null ? xpEarnedSoFar - xpIdealSoFar : null;
  const xpAdjustedPerDay = xpNeededNow && xpNeededNow > 0 && daysRemain > 0
    ? Math.ceil(xpNeededNow / daysRemain)
    : null;
  const progress = xpNeededTotal && xpNeededTotal > 0
    ? Math.min(99.9, (xpEarnedSoFar / xpNeededTotal) * 100)
    : null;

  // Stat 1 — posição ou nível atual
  const stat1Label = isExp ? 'Nível Atual' : 'Posição Atual';
  const stat1Value = isExp ? `Lv ${currentLvl}` : `#${currentRnk}`;
  const stat1Sub   = isExp
    ? `${(goal.targetLevel ?? 0) - currentLvl} níveis restantes`
    : `${currentRnk - (goal.targetRank ?? 0)} pos. a subir`;

  // Stat 2 — XP faltando (label de referência)
  const stat2Sub = isExp ? `para Lv ${goal.targetLevel}` : `para #${goal.targetRank}`;

  return (
    <div className="gt-card">
      {cardHead}

      <div className="gt-stats-row">
        <div className="gt-stat">
          <div className="gt-stat-label">{stat1Label}</div>
          <div className="gt-stat-value">{stat1Value}</div>
          <div className="gt-stat-sub">{stat1Sub}</div>
        </div>
        <div className="gt-stat">
          <div className="gt-stat-label">XP Faltando</div>
          <div className="gt-stat-value">{xpNeededNow != null ? fmtXP(xpNeededNow) : '—'}</div>
          <div className="gt-stat-sub">{stat2Sub}</div>
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
