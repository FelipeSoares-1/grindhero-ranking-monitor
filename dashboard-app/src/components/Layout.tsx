// components/Layout.tsx — Header, SearchBar, StatBar e estrutura da página
import { useState, useMemo, useRef, useEffect } from 'react';
import { Search, X, Zap, Expand } from 'lucide-react';
import type { DashboardData } from '../types';
import { useDashboardStore } from '../store/useDashboardStore';
import { fmtXP } from '../utils/colors';
import './Layout.css';

interface HeaderProps {
  data: DashboardData;
  onPlayerSelect: (name: string) => void;   // cross-filter
  onOpenDrawer:   (name: string) => void;   // abre drawer
}

export function Header({ data, onPlayerSelect, onOpenDrawer }: HeaderProps) {
  const { metadata } = data;
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  const allNames = useMemo(() => {
    const names = new Set<string>();
    data.latest_snapshot.forEach(s => names.add(s.name));
    return [...names].sort();
  }, [data]);

  const matches = useMemo(() => {
    if (!query) return [];
    const q = query.toLowerCase();
    return allNames.filter(n => n.toLowerCase().includes(q)).slice(0, 12);
  }, [query, allNames]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  function selectPlayer(name: string) {
    onPlayerSelect(name);
    setQuery('');
    setOpen(false);
  }

  function getPlayerMeta(name: string) {
    const exp = data.latest_snapshot.find(s => s.name === name && s.ranking_type === 'Experience');
    if (exp) return `Lv ${exp.level} · #${exp.rank} XP`;
    const any = data.latest_snapshot.find(s => s.name === name);
    return any ? `#${any.rank} ${any.ranking_type}` : '';
  }

  return (
    <header className="header">
      <div className="header-brand">
        <img
          className="header-logo-img"
          src="https://redskull.space/images/red-skull-logo.webp"
          alt="RED SKULL"
          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
        />
        <div>
          <div className="header-title">
            <span className="accent">GrindHero</span> Monitor
          </div>
          <div className="header-sub">⚔ Ranking PvP — {metadata.server}</div>
        </div>
      </div>

      <div className="search-wrap" ref={wrapRef}>
        <Search className="search-icon" size={18} />
        <input
          className="search-input"
          placeholder="Buscar qualquer jogador..."
          value={query}
          autoComplete="off"
          onChange={e => { setQuery(e.target.value); setOpen(true); }}
          onFocus={() => query && setOpen(true)}
        />
        <div className={`search-results ${open && matches.length > 0 ? 'open' : ''}`}>
          {matches.map(name => (
            <div key={name} className="search-result-item">
              {/* Clique no nome = cross-filter */}
              <span
                className="search-result-name"
                onClick={() => selectPlayer(name)}
                style={{ cursor: 'pointer', flex: 1 }}
              >
                {name}
              </span>
              <span className="search-result-meta">{getPlayerMeta(name)}</span>
              {/* Botão ⤢ = abre drawer sem afetar cross-filter */}
              <button
                className="search-detail-btn"
                onClick={(e) => { e.stopPropagation(); setOpen(false); setQuery(''); onOpenDrawer(name); }}
                title="Ver detalhes"
              >
                <Expand size={12} />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="header-meta">
        <div>Última coleta: <strong>{metadata.ultima_coleta}</strong></div>
        <div>Dashboard: <strong>{metadata.dashboard_gerado}</strong></div>
        <div>Monitorando: <strong>{metadata.watched.join(', ')}</strong></div>
      </div>
    </header>
  );
}


export function StatBar({ data }: { data: DashboardData }) {
  const { metadata } = data;
  return (
    <div className="statbar">
      <div className="stat">
        <div className="stat-label">Servidor</div>
        <div className="stat-value" style={{ fontSize: '1rem' }}>{metadata.server}</div>
      </div>
      <div className="stat">
        <div className="stat-label">Dias coletando</div>
        <div className="stat-value">{metadata.dias_coletando}</div>
        <div className="stat-sub">dia(s) com dados</div>
      </div>
      <div className="stat">
        <div className="stat-label">Jogadores únicos</div>
        <div className="stat-value">{metadata.total_jogadores}</div>
        <div className="stat-sub">já monitorados</div>
      </div>
      <div className="stat">
        <div className="stat-label">Registros totais</div>
        <div className="stat-value">{fmtXP(metadata.total_registros)}</div>
        <div className="stat-sub">no banco</div>
      </div>
      <div className="stat">
        <div className="stat-label">Última coleta</div>
        <div className="stat-value" style={{ fontSize: '0.85rem' }}>{metadata.ultima_coleta}</div>
      </div>
    </div>
  );
}


export function SectionTitle({ icon, accent, sub }: { icon: React.ReactNode; accent: string; sub?: string }) {
  return (
    <div className="section-title">
      {icon}
      <span className="st-accent">{accent}</span>
      {sub && <span style={{ color: 'var(--muted)', fontSize: '0.75rem' }}>— {sub}</span>}
    </div>
  );
}

export function CrossFilterBanner() {
  const { selectedPlayer, setSelectedPlayer } = useDashboardStore();
  if (!selectedPlayer) return null;
  return (
    <div className="crossfilter-banner">
      <Zap size={14} color="var(--red)" />
      <span>Filtrando por: {selectedPlayer}</span>
      <button className="crossfilter-clear" onClick={() => setSelectedPlayer(null)}>
        <X size={12} style={{ marginRight: 4, verticalAlign: 'middle' }} />
        Limpar filtro
      </button>
    </div>
  );
}

