// utils/colors.ts — Paleta de cores Red Skull Guild
export const SKILL_COLORS: Record<string, string> = {
  Experience: '#d4af37',
  Melee:      '#c0392b',
  Shielding:  '#ca6f1e',
  Magic:      '#7d3c98',
  Distance:   '#1a8a6e',
  Taming:     '#b7950b',
};

export const PLAYER_COLORS = [
  '#d4af37', '#c0392b', '#2ecc71', '#e67e22', '#7d3c98', '#1a8a6e', '#ff6b6b',
];

export function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

export function fmtXP(v: number | null | undefined): string {
  if (v == null) return '—';
  const abs = Math.abs(v);
  if (abs >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000)     return `${(v / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000)         return `${(v / 1_000).toFixed(1)}K`;
  return String(v);
}

export function fmtDelta(v: number | null | undefined): string {
  if (v == null || v === 0) return '±0';
  return v > 0 ? `+${fmtXP(v)}` : fmtXP(v);
}
