# GrindHero Monitor — Roadmap de Features

Ideias levantadas em sessão com o líder da guild. Implementar conforme prioridade.

---

## ✅ Concluído

- [x] Coleta automática 4x/dia via Claude Routines (09h, 14h, 20h, 23h55 BRT)
- [x] Dashboard com tema Red Skull (Anton + Ubuntu Condensed, preto/vermelho/dourado)
- [x] Gate de senha SHA-256 (sem indexação no Google)
- [x] Domínio customizado: `monitor.redskull.space/dashboard`
- [x] Migração de Plotly → ECharts

---

## 🔜 Próximas Features

### 1. Jogadores Monitorados Personalizável
**Descrição:** Painel dentro do dashboard para adicionar/remover jogadores monitorados sem precisar editar arquivos.
**Como funciona:**
- Campo de busca que filtra jogadores do rank atual
- Botão "Monitorar" adiciona o jogador à lista
- Botão "X" ao lado do nome remove
- Salva via commit automático no GitHub usando o PAT já existente
**Impacto:** Alto — elimina necessidade de mexer em config.json manualmente

---

### 2. Alertas no Discord
**Descrição:** Webhook automático no canal da guild quando eventos relevantes acontecem.
**Eventos sugeridos:**
- Jogador monitorado sobe/desce X posições
- Rival entra no top 10 de uma categoria
- Jogador monitorado atinge novo recorde pessoal
**Como funciona:** Etapa adicional no GitHub Actions workflow após cada coleta.
**Impacto:** Muito alto — informação chega no Discord sem precisar abrir o monitor

---

### 3. Ranking de Crescimento Semanal
**Descrição:** "Quem mais evoluiu nos últimos 7 dias?" — ranking interno por ganho de XP/skill no período.
**Utilidade:** Identificar quem está farmando forte, quem esfriou, comparar evolução entre membros.
**Impacto:** Alto para gestão de guild

---

### 4. Detecção de Rivais Automática
**Descrição:** Monitorar automaticamente os jogadores nas posições imediatamente acima dos players monitorados.
**Como funciona:** Se Sir Black está em #4 no Melee, o sistema passa a acompanhar #3 e #2 automaticamente.
**Impacto:** Médio-alto — útil para estratégia PvP

---

### 5. Heatmap de Atividade
**Descrição:** Calendário visual (estilo GitHub Contributions) mostrando ganho de XP por dia por jogador.
**Utilidade:** Ver quais dias a guild é mais ativa, identificar ausências, padrões de farm.
**Impacto:** Médio

---

### 6. Hall da Fama
**Descrição:** Linha do tempo automática de marcos históricos da guild.
**Exemplos:** "Sir Black entrou no top 5 do Melee — 03/05/2026", "Todmip atingiu #39 no Distance"
**Como funciona:** Detectado automaticamente a cada coleta e registrado em arquivo JSON separado.
**Impacto:** Médio — valor sentimental e histórico para a guild

---

### 7. Modo TV / Stream
**Descrição:** Layout fullscreen rotativo para exibir em stream ou Discord screenshare.
**Como funciona:** Modo especial ativado por parâmetro na URL (`?mode=tv`), sem senha, exibe os rankings dos membros em loop automático estilo placar de torneio.
**Impacto:** Médio — engajamento da comunidade

---

## 💡 Notas Técnicas

- Stack atual: Python + SQLite + GitHub Actions + GitHub Pages + Claude Routines
- Domínio: `redskull.space` (Hostinger DNS)
- PAT GitHub com scope `workflow` — expira **02/08/2026** (renovar antes)
- Coletas armazenadas em `ranking.db` — top 50 por categoria, 4x/dia
- API do jogo expõe apenas: `rank`, `name`, `level`, `experience` (sem guild, sem vocação)
