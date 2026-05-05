// components/WatchedManager.tsx
// Painel para adicionar/remover jogadores monitorados.
// Persiste no localStorage. Mostra como atualizar o config.json.
import { useState, useMemo, useRef } from 'react';
import { Settings, Plus, X, Copy, Check } from 'lucide-react';
import type { DashboardData } from '../types';
import { fmtXP } from '../utils/colors';
import './WatchedManager.css';

interface Props {
  data: DashboardData;
  watchedPlayers: string[];
  onAddPlayer: (name: string) => void;
  onRemovePlayer: (name: string) => void;
}

export function WatchedManager({ data, watchedPlayers, onAddPlayer, onRemovePlayer }: Props) {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [copied, setCopied] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Todos os jogadores que já apareceram no banco (distinct)
  const allPlayers = useMemo(() => {
    const map = new Map<string, { level: number; xp: number; ranking: string }>();
    data.latest_snapshot.forEach(s => {
      if (!map.has(s.name) || s.ranking_type === 'Experience') {
        map.set(s.name, { level: s.level, xp: s.experience, ranking: s.ranking_type });
      }
    });
    return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [data]);

  const suggestions = useMemo(() => {
    if (!query) return [];
    const q = query.toLowerCase();
    return allPlayers
      .filter(([name]) => name.toLowerCase().includes(q))
      .slice(0, 15);
  }, [query, allPlayers]);

  function addFromInput() {
    const trimmed = query.trim();
    if (!trimmed) return;
    // Tenta encontrar nome exato (case-insensitive)
    const found = allPlayers.find(([n]) => n.toLowerCase() === trimmed.toLowerCase());
    const nameToAdd = found ? found[0] : trimmed;
    if (!watchedPlayers.map(w => w.toLowerCase()).includes(nameToAdd.toLowerCase())) {
      onAddPlayer(nameToAdd);
    }
    setQuery('');
    setShowSuggestions(false);
  }

  function addSuggestion(name: string) {
    if (!watchedPlayers.map(w => w.toLowerCase()).includes(name.toLowerCase())) {
      onAddPlayer(name);
    }
    setQuery('');
    setShowSuggestions(false);
    inputRef.current?.focus();
  }

  // Gera o JSON do config.json atualizado
  const configJson = JSON.stringify(
    {
      watched_players: watchedPlayers,
      server: data.metadata.server.startsWith('{')
        ? JSON.parse(data.metadata.server)
        : { id: 3, name: data.metadata.server },
      ranking_types: data.metadata.ranking_types,
      dashboard_title: 'GrindHero Monitor',
    },
    null,
    2,
  );

  function copyConfig() {
    navigator.clipboard.writeText(configJson).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  }

  return (
    <div className="wm-panel">
      <div className="wm-header">
        <div className="wm-title">
          <Settings size={15} />
          Gerenciar Jogadores Monitorados
        </div>
        <button className="wm-save-btn" onClick={copyConfig}>
          {copied ? <Check size={13} /> : <Copy size={13} />}
          {copied ? 'Copiado!' : 'Copiar config.json'}
        </button>
      </div>

      {/* Chips dos jogadores atuais */}
      <div className="wm-chips">
        {watchedPlayers.length === 0 && (
          <span style={{ color: 'var(--muted)', fontSize: '0.8rem', alignSelf: 'center' }}>
            Nenhum jogador sendo monitorado.
          </span>
        )}
        {watchedPlayers.map(name => (
          <span key={name} className="wm-chip">
            {name}
            <button
              className="wm-chip-remove"
              onClick={() => onRemovePlayer(name)}
              title={`Remover ${name}`}
            >
              <X size={12} />
            </button>
          </span>
        ))}
      </div>

      {/* Input de busca + botão adicionar */}
      <div style={{ position: 'relative' }}>
        <div className="wm-search-row">
          <input
            ref={inputRef}
            className="wm-input"
            placeholder="Buscar jogador pelo nome..."
            value={query}
            autoComplete="off"
            onChange={e => { setQuery(e.target.value); setShowSuggestions(true); }}
            onFocus={() => query && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 180)}
            onKeyDown={e => { if (e.key === 'Enter') addFromInput(); }}
          />
          <button
            className="wm-add-btn"
            onClick={addFromInput}
            disabled={!query.trim()}
          >
            <Plus size={14} style={{ verticalAlign: 'middle' }} /> Adicionar
          </button>
        </div>

        <div className={`wm-suggestions ${showSuggestions && suggestions.length > 0 ? 'open' : ''}`}>
          {suggestions.map(([name, meta]) => {
            const already = watchedPlayers.map(w => w.toLowerCase()).includes(name.toLowerCase());
            return (
              <div
                key={name}
                className={`wm-suggestion-item ${already ? 'already' : ''}`}
                onClick={() => !already && addSuggestion(name)}
              >
                <span>{name} {already && <span style={{ color: 'var(--gold)', fontSize: '0.7rem' }}>✓ monitorado</span>}</span>
                <span className="wm-suggestion-meta">
                  Lv {meta.level} · {fmtXP(meta.xp)} ({meta.ranking})
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Instrução para salvar no config.json */}
      <div className="wm-config-box">
        <strong style={{ color: 'var(--text)' }}>💡 Para persistir após o próximo build:</strong>
        <br />
        1. Clique em <strong style={{ color: 'var(--gold)' }}>Copiar config.json</strong> acima.
        <br />
        2. Cole o conteúdo no arquivo <code>config.json</code> na raiz do projeto.
        <br />
        3. Execute <code>python exportar_dados.py</code> para sincronizar os dados.
        <button className="wm-copy-btn" onClick={copyConfig}>
          {copied ? '✓ JSON copiado!' : '📋 Copiar config.json atualizado'}
        </button>
      </div>
    </div>
  );
}
