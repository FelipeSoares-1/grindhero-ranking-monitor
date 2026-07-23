// types.ts — Tipos compartilhados do dashboard

export interface SkillPoint {
  date: string;
  rank: number;
  experience: number;
  level: number;
}

export interface HistoryEntry {
  name: string;
  ranking_type: string;
  points: SkillPoint[];
}

export interface SnapshotEntry {
  player_id: string;
  name: string;
  rank: number;
  level: number;
  experience: number;
  ranking_type: string;
  collected_at: string;
}

export interface Delta {
  xp_delta: number;
  rank_delta: number;
}

export interface VelocityEntry {
  name: string;
  rank: number;
  xp_day: number;
  label: string;
}

export interface Metadata {
  server: string;
  ultima_coleta: string;
  dashboard_gerado: string;
  dias_coletando: number;
  total_jogadores: number;
  total_registros: number;
  watched: string[];
  ranking_types: string[];
}

export interface DashboardData {
  metadata: Metadata;
  latest_snapshot: SnapshotEntry[];
  deltas: Record<string, Delta>;
  history: HistoryEntry[];
  velocity: Record<string, VelocityEntry[]>;
}

// Força tratamento como módulo ESM (Vite + verbatimModuleSyntax)
export type {};

// ── Widget público "Top Farmers do Dia" (/farm.json) ──
export interface FarmServer {
  slug: string;              // 'pvp' | 'pve'
  server: string;            // 'Endora (PvP)'
  label: string;             // 'PvP'
  ultima_coleta: string;
  janela_horas: number | null;
  ranking_types: string[];
  velocity: Record<string, VelocityEntry[]>;
}

export interface FarmData {
  gerado_em: string;
  servidores: FarmServer[];
}
