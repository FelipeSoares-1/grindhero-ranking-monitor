// App.tsx — Entrypoint do Dashboard GrindHero Monitor
import { useEffect, useState } from 'react';
import { Activity, Users, Trophy, Star, Zap, Swords } from 'lucide-react';
import type { DashboardData } from './types';
import { useDashboardStore } from './store/useDashboardStore';
import {
  Header, StatBar, SectionTitle, CrossFilterBanner,
} from './components/Layout';
import { PlayerCards }    from './components/PlayerCards';
import { WatchedManager } from './components/WatchedManager';
import { PlayerDrawer }   from './components/PlayerCards';
import { RadarSkillChart } from './components/charts/RadarSkillChart';
import { GapChart }        from './components/charts/GapChart';
import { VelocityChart }   from './components/charts/VelocityChart';
import { EvolutionChart }  from './components/charts/EvolutionChart';
import { RankingTable }    from './components/RankingTable';
import './index.css';

export default function App() {
  const [
    data, setData,
  ] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Drawer global — qualquer componente pode abrir detalhes de qualquer jogador
  const [drawerPlayer, setDrawerPlayer] = useState<string | null>(null);

  const {
    setSelectedPlayer,
    watchedPlayers, initWatched,
    addWatchedPlayer, removeWatchedPlayer,
  } = useDashboardStore();

  useEffect(() => {
    fetch('/data.json')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status} — data.json não encontrado`);
        return r.json() as Promise<DashboardData>;
      })
      .then(d => {
        setData(d);
        // Inicializa watched players do localStorage (ou usa padrão do config)
        initWatched(d.metadata.watched);
      })
      .catch(e => setError(e.message));
  }, []);

  if (error) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', gap: 16, textAlign: 'center', padding: 32 }}>
        <img src="https://redskull.space/images/red-skull-logo.webp" alt="" style={{ width: 80, filter: 'drop-shadow(0 0 12px rgba(196,18,18,0.8))' }} onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
        <div style={{ fontFamily: 'Anton', fontSize: '1.4rem', color: 'var(--red)', letterSpacing: 2, textTransform: 'uppercase' }}>
          Erro ao carregar dados
        </div>
        <div style={{ color: 'var(--muted)', fontSize: '0.85rem', maxWidth: 420 }}>
          {error}
          <br /><br />
          Execute primeiro:{' '}
          <code style={{ color: 'var(--gold)', background: 'var(--bg2)', padding: '2px 8px', borderRadius: 2 }}>
            python exportar_dados.py
          </code>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', gap: 20 }}>
        <img
          src="https://redskull.space/images/red-skull-logo.webp" alt=""
          style={{ width: 90, filter: 'drop-shadow(0 0 14px rgba(196,18,18,0.7))' }}
          onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
        />
        <div style={{ fontFamily: 'Anton', color: 'var(--red)', letterSpacing: 3, textTransform: 'uppercase' }}>
          Carregando...
        </div>
        <div style={{ width: 180, height: 2, background: 'rgba(196,18,18,0.15)', overflow: 'hidden' }}>
          <div style={{ height: '100%', background: 'linear-gradient(135deg, #8c0000, #c41212)', animation: 'skulBar 1.6s ease-in-out infinite' }} />
        </div>
        <style>{`@keyframes skulBar { 0%{transform:translateX(-100%)} 100%{transform:translateX(400%)} }`}</style>
      </div>
    );
  }

  // Injeta o watched atual no data para passar adiante nos componentes
  const dataWithWatched: DashboardData = {
    ...data,
    metadata: { ...data.metadata, watched: watchedPlayers },
  };

  return (
    <div style={{ maxWidth: 1440, margin: '0 auto', paddingBottom: 80 }}>
      <Header
        data={dataWithWatched}
        onPlayerSelect={name => setSelectedPlayer(name)}
        onOpenDrawer={name => setDrawerPlayer(name)}
      />
      <StatBar data={data} />

      {/* Banner de cross-filter ativo */}
      <div style={{ padding: '0 28px' }}>
        <CrossFilterBanner />
      </div>

      {/* ── JOGADORES MONITORADOS ── */}
      <section className="section">
        <SectionTitle
          icon={<Users size={18} color="var(--red)" />}
          accent="Jogadores Monitorados"
        />
        {/* Gerenciador (adicionar/remover) */}
        <WatchedManager
          data={data}
          watchedPlayers={watchedPlayers}
          onAddPlayer={addWatchedPlayer}
          onRemovePlayer={removeWatchedPlayer}
        />
        {/* Cards + Digest */}
        <PlayerCards
          data={dataWithWatched}
          watchedPlayers={watchedPlayers}
          onRemovePlayer={removeWatchedPlayer}
          onOpenDrawer={name => setDrawerPlayer(name)}
        />
      </section>

      {/* ── PERFIL DE SKILLS ── */}
      <section className="section">
        <SectionTitle icon={<Star size={18} color="var(--red)" />} accent="Perfil de Skills" />
        <RadarSkillChart data={dataWithWatched} />
      </section>

      {/* ── ANÁLISE COMPETITIVA ── */}
      <section className="section">
        <SectionTitle
          icon={<Swords size={18} color="var(--red)" />}
          accent="Análise Competitiva"
          sub="Gap para os vizinhos de rank"
        />
        <GapChart data={dataWithWatched} />
      </section>

      {/* ── VELOCIDADE DE FARM ── */}
      <section className="section">
        <SectionTitle
          icon={<Zap size={18} color="var(--red)" />}
          accent="Velocidade de Farm"
          sub="XP ganho desde a coleta anterior"
        />
        <VelocityChart data={dataWithWatched} />
      </section>

      {/* ── EVOLUÇÃO TEMPORAL ── */}
      <section className="section">
        <SectionTitle icon={<Activity size={18} color="var(--red)" />} accent="Evolução Temporal" />
        <EvolutionChart data={dataWithWatched} />
      </section>

      {/* ── RANKINGS COMPLETOS ── */}
      <section className="section">
        <SectionTitle
          icon={<Trophy size={18} color="var(--red)" />}
          accent="Rankings Completos"
          sub="Top 50 por tipo"
        />
        <RankingTable data={dataWithWatched} onOpenDrawer={name => setDrawerPlayer(name)} />
      </section>

      {/* ── Drawer global (qualquer jogador de qualquer seção) ── */}
      {drawerPlayer && data && (
        <PlayerDrawer
          name={drawerPlayer}
          data={dataWithWatched}
          onClose={() => setDrawerPlayer(null)}
        />
      )}

      <p style={{
        textAlign: 'center', color: 'var(--muted)', fontSize: '0.7rem',
        marginTop: 24, padding: '20px 28px 0',
        borderTop: '1px solid var(--border)',
        textTransform: 'uppercase', letterSpacing: 1,
      }}>
        GrindHero Monitor • {data.metadata.server} • Recharts Edition
      </p>
    </div>
  );
}
