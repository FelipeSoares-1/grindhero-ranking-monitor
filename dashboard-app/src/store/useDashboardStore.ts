// store/useDashboardStore.ts — Estado global de cross-filtering (Zustand)
import { create } from 'zustand';

const LS_KEY = 'grindhero_watched_v1';

interface DashboardStore {
  /** Jogador atualmente em foco (cross-filter). null = todos */
  selectedPlayer: string | null;
  /** Skill/tab ativa nos gráficos de velocity e ranking */
  activeSkill: string;
  /** Período de tempo selecionado (dias). 0 = tudo */
  periodDays: number;
  /** Lista de jogadores monitorados (persistida no localStorage) */
  watchedPlayers: string[];

  setSelectedPlayer: (name: string | null) => void;
  toggleSelectedPlayer: (name: string) => void;
  setActiveSkill: (skill: string) => void;
  setPeriodDays: (days: number) => void;
  initWatched: (defaultList: string[]) => void;
  addWatchedPlayer: (name: string) => void;
  removeWatchedPlayer: (name: string) => void;
}

function loadFromLS(): string[] | null {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function saveToLS(list: string[]) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(list)); } catch {}
}

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  selectedPlayer: null,
  activeSkill: 'Experience',
  periodDays: 0,
  watchedPlayers: [],

  setSelectedPlayer: (name) => set({ selectedPlayer: name }),

  /** Clicou no mesmo → limpa. Clicou em outro → seleciona. */
  toggleSelectedPlayer: (name) => {
    const current = get().selectedPlayer;
    set({ selectedPlayer: current === name ? null : name });
  },

  setActiveSkill: (skill) => set({ activeSkill: skill }),
  setPeriodDays:  (days)  => set({ periodDays: days }),

  /** Inicializa watched com a lista salva no localStorage ou usa o padrão do data.json */
  initWatched: (defaultList) => {
    const saved = loadFromLS();
    set({ watchedPlayers: saved ?? defaultList });
  },

  addWatchedPlayer: (name) => {
    const list = get().watchedPlayers;
    if (list.map(w => w.toLowerCase()).includes(name.toLowerCase())) return;
    const updated = [...list, name];
    set({ watchedPlayers: updated });
    saveToLS(updated);
  },

  removeWatchedPlayer: (name) => {
    const updated = get().watchedPlayers.filter(w => w.toLowerCase() !== name.toLowerCase());
    // Se o removido estava selecionado, limpa o filtro
    if (get().selectedPlayer?.toLowerCase() === name.toLowerCase()) {
      set({ selectedPlayer: null });
    }
    set({ watchedPlayers: updated });
    saveToLS(updated);
  },
}));
