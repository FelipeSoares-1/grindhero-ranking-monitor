// farm.tsx — Página pública standalone "Top Farmers do Dia"
// Mostra a velocidade de farm (XP ganho na janela) por SERVIDOR e por skill,
// sem senha e sem controles pessoais. Consome /farm.json (payload enxuto).
import { StrictMode, useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer,
} from 'recharts';
import type { FarmData, FarmServer } from './types';
import { SKILL_COLORS, fmtXP } from './utils/colors';
import './index.css';
import './farm.css';

const MEDALS = ['🥇', '🥈', '🥉'];

// ── Google Analytics (GA4) ──
declare global {
  interface Window { gtag?: (...args: any[]) => void; }
}
function ga(event: string, params?: Record<string, unknown>) {
  window.gtag?.('event', event, params);
}

function hexToRgba(hex: string, a: number): string {
  const h = hex.replace('#', '');
  return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`;
}

function fmtDateHora(s: string): string {
  return s || '';
}

/**
 * Publica a altura real do conteudo para a pagina que embeda este widget.
 * Sem isso o iframe precisa de height fixo, que sobra espaco no PvE vazio
 * e corta o grafico quando o top tem 15 linhas.
 */
function useAlturaPublicada(ref: React.RefObject<HTMLDivElement | null>) {
  useEffect(() => {
    const el = ref.current;
    if (!el || window.parent === window) return;

    let ultima = 0;
    const publicar = () => {
      const h = Math.ceil(el.getBoundingClientRect().height);
      if (h > 0 && Math.abs(h - ultima) > 1) {
        ultima = h;
        window.parent.postMessage({ type: 'redskull-farm-height', height: h }, '*');
      }
    };

    publicar();
    const ro = new ResizeObserver(publicar);
    ro.observe(el);
    return () => ro.disconnect();
  });
}

/** Servidor inicial: ?server=pve na URL, senão o primeiro do payload. */
function slugInicial(servidores: FarmServer[]): string {
  const q = new URLSearchParams(window.location.search).get('server');
  return servidores.some(s => s.slug === q) ? q! : servidores[0].slug;
}

function TopFarmers() {
  const [data, setData] = useState<FarmData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [slug, setSlug] = useState<string>('');
  const [skill, setSkill] = useState<string>('');
  const wrapRef = useRef<HTMLDivElement>(null);
  useAlturaPublicada(wrapRef);

  useEffect(() => {
    fetch(`/farm.json?t=${Date.now()}`, { cache: 'no-store' })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() as Promise<FarmData>; })
      .then(d => {
        if (!d.servidores?.length) throw new Error('payload sem servidores');
        const s0 = slugInicial(d.servidores);
        const srv = d.servidores.find(s => s.slug === s0)!;
        setData(d);
        setSlug(s0);
        setSkill(srv.ranking_types[0] ?? 'Experience');
        ga('view_top_farmers', { page_title: 'Top Farmers do Dia', server: s0 });
      })
      .catch(e => setError(e.message));
  }, []);

  const servidor = useMemo(
    () => data?.servidores.find(s => s.slug === slug) ?? null,
    [data, slug],
  );

  function trocarServidor(novo: string) {
    const srv = data!.servidores.find(s => s.slug === novo)!;
    setSlug(novo);
    // preserva a skill se ela existir no outro servidor
    if (!srv.ranking_types.includes(skill)) setSkill(srv.ranking_types[0]);
    ga('select_server', { server: novo });
  }

  if (error)     return <div ref={wrapRef} className="tf-msg">Erro ao carregar dados</div>;
  if (!data || !servidor) return <div ref={wrapRef} className="tf-msg">Carregando…</div>;

  const color = SKILL_COLORS[skill] ?? '#d4af37';
  const velData = (servidor.velocity[skill] ?? []).slice(0, 15);

  const chartData = velData.map((v, i) => ({
    name: `${i < 3 ? MEDALS[i] : `${i + 1}º`} ${v.name}`,
    rawName: v.name,
    xp_day: v.xp_day,
    label: v.label,
  }));

  const chartH = Math.max(260, chartData.length * 30 + 20);
  const janela = servidor.janela_horas;

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="tf-tooltip">
        <div className="tf-tooltip-name">{d.rawName}</div>
        <div className="tf-tooltip-row">
          <span>XP ganho</span>
          <span style={{ color }}>{d.label}</span>
        </div>
      </div>
    );
  };

  /**
   * Estado vazio: distingue "servidor novo, ainda sem 2 coletas" de
   * "essa skill não teve ganho". Sem isso o PvE recém-ligado parece quebrado.
   */
  const vazio = velData.length === 0;
  const semJanela = janela == null;

  return (
    <div className="tf-wrap" ref={wrapRef}>
      <div className="tf-header">
        <img
          className="tf-logo" src="/red-skull-logo.webp" alt="Red Skull"
          onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
        />
        <div>
          <div className="tf-title">Top Farmers <span>do Dia</span></div>
          <div className="tf-sub">quem mais farmou nas últimas horas · {servidor.server} · Red Skull</div>
        </div>
      </div>

      {/* Seletor de servidor — só aparece se houver mais de um */}
      {data.servidores.length > 1 && (
        <div className="tf-servers" role="tablist" aria-label="Servidor">
          {data.servidores.map(s => (
            <button
              key={s.slug}
              role="tab"
              aria-selected={s.slug === slug}
              className={`tf-server ${s.slug === slug ? 'active' : ''}`}
              onClick={() => trocarServidor(s.slug)}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      {/* Abas de skill */}
      <div className="tf-tabs">
        {servidor.ranking_types.map(rt => {
          const c = SKILL_COLORS[rt] ?? '#d4af37';
          const on = skill === rt;
          return (
            <button
              key={rt}
              className={`tf-tab ${on ? 'active' : ''}`}
              onClick={() => { setSkill(rt); ga('select_skill', { skill_name: rt, server: slug }); }}
              style={on ? { borderColor: c, backgroundColor: hexToRgba(c, 0.18), color: '#fff' } : {}}
            >
              {rt}
            </button>
          );
        })}
      </div>

      <div className="tf-card">
        <div className="tf-card-title" style={{ color }}>Velocidade de Farm — {skill}</div>
        {vazio ? (
          <div className="tf-msg" style={{ minHeight: 180 }}>
            {semJanela
              ? 'Coletando dados deste servidor — o ranking aparece após a próxima coleta diária.'
              : 'Sem ganho registrado nesta skill na última janela'}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={chartH}>
            <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 62, left: 0, bottom: 0 }}>
              <XAxis type="number" hide />
              <YAxis
                type="category" dataKey="name" width={172}
                tick={({ y, payload }: any) => (
                  <text x={4} y={y} dy={4} textAnchor="start"
                    fill="var(--muted)" fontSize={11} fontFamily="Fira Code, monospace">
                    {payload.value}
                  </text>
                )}
                axisLine={false} tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar
                dataKey="xp_day" radius={[0, 3, 3, 0]}
                label={{ position: 'right', formatter: (v: any) => fmtXP(v as number), fill: 'var(--muted)', fontSize: 11, fontFamily: 'Fira Code' }}
              >
                {chartData.map((entry, i) => (
                  <Cell key={entry.name} fill={hexToRgba(color, i === 0 ? 1 : i < 3 ? 0.75 : 0.5)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="tf-footer">
        <span>
          XP ganho {janela != null ? `nas últimas ${janela}h` : 'entre as duas últimas coletas'}
          {' · '}última coleta {fmtDateHora(servidor.ultima_coleta)}
        </span>
      </div>
    </div>
  );
}

createRoot(document.getElementById('farm-root')!).render(
  <StrictMode>
    <TopFarmers />
  </StrictMode>,
);
