# Handover — DeskcommCRM (resumo para outro agente de desenvolvimento)

> Data: 2026-11-16. Snapshot verificado no código. Quem lê este documento não
> tem a conversa de origem — ele é autocontido. Não contém segredo, token,
> senha, URL com credencial nem dado pessoal de comprador.
>
> Repo: `/home/pc/DeskcommCRM`, branch `local/v1.20.0-petemcasa`.
> Acesso ao PC: `ssh -F ~/.ssh/config pc` (sempre com `-F`).
> Este documento também existe no PC em
> `/home/pc/Workspace/tuttibom-ops/docs/handover-deskcomm-outro-agente.md`.

## 1. O que é a aplicação

O **DeskcommCRM** é um CRM multiempresa open source com agentes de IA
nativos, WhatsApp como canal primário. Ele atende clientes, qualifica,
move o funil, abre casos humanos, agenda follow-ups e expõe o CRM inteiro
via MCP para um gestor externo.

- **Atendimento (Ana v9):** agente com IA que atende no WhatsApp da
  sessão `tutibom` (número da loja), modelo `core-medio` servido pelo
  9Router (provedor `custom`, compatível com OpenAI). Transcrição de
  áudio por ElevenLabs Scribe. Roteador Jev + memória por contato
  (`contact_interests`, lote noturno 03:35) lembram o interesse de cada
  contato.
- **Funil e operação:** Inbox, kanban de leads, fluxos (Fluxo A/B),
  follow-ups, casos humanos (G1–G4), rascunhos com aprovação, regras
  automáticas, crons no `scheduler`/`worker`.
- **Gestor externo via MCP:** servidor em `POST /api/mcp` (Streamable
  HTTP, sem estado), Bearer `dsk_...`, papel por token
  (`viewer < agent < manager < admin`), tudo auditado. Catálogo de 75
  ferramentas no código, 68 expostas em produção. O gestor é um **papel**,
  não um agente: qualquer agente com cliente MCP pode ocupá-lo, um token
  por agente, um gestor ativo por vez. Rotina do gestor: 3 varreduras/dia
  (08:00, 14:00, 20:00) — ver §7, fora do escopo deste handover.
- **A instância TuttiBom é a org `deskcomm-local`**
  (id `92bfe3dd-1117-4b12-8413-95a2e8e143e0`; "tutibom" é o nome de
  exibição, não o slug). Existe outra org, `petemcasa`, que não é a
  loja. Não confundir as duas.

Peças vizinhas, **fora deste repo** (só o papel de cada uma):

- **Ponte** (`/home/pc/ponte`): camada externa de conectores sobre o
  Deskcomm, sem fork. Adapters hoje: `browser`, `checkout`, `crm`,
  `ideation`, `media`. **Não há adapter de Messenger nem de Instagram.**
  A TuttiBom não está registrada na Ponte.
- **9Router:** provedor de modelos compatível com OpenAI. Túnel
  `9router.petemcasa.com` → `127.0.0.1:20130`.
- **WAHA standalone:** WhatsApp HTTP API na porta `3005`, sessão
  `tutibom`. O serviço `waha` do compose **não** deve ser ligado.
- **Facebook/Camofox (`fb_agent.py`):** acesso à conta da loja no
  Facebook via navegador Camoufox + visão do Jev. Fora do escopo
  deste handover (ver §7).

## 2. Stack e onde roda

- **Frontend:** Next.js 16 App Router (Turbopack) + React 19 +
  TypeScript 6 estrito + Tailwind 4 + shadcn/ui.
- **Backend:** Route Handlers Next.js, no mesmo repo. Workers via
  tabela `event_log` + cron (não Inngest/Trigger).
- **Banco:** Supabase (Postgres) na nuvem. RLS em toda tabela
  tenant-aware. Extensions: `uuid-ossp`, `pgcrypto`, `vector`.
  **649 migrations**; `supabase/baseline.sql` (3,9 MB) é a fonte
  canônica do schema.
- **Auth:** Supabase Auth (`@supabase/ssr`), cookie HttpOnly.
- **IA:** Vercel AI Gateway (Anthropic primário; embeddings OpenAI
  ou Google por org); Jev (TypeSafe) para decisões tipadas.
- **Validação:** Zod em todo input externo. **Observabilidade:**
  Sentry com `beforeSend` sanitizado.
- **Gerenciador de pacotes:** pnpm. Scripts principais:
  `gov:verify` = `typecheck + lint + lint:channels + lint:role-rank
  + test:unit`.

Onde roda (PC, instalação local):

- Containers: `deskcommcrm-app-1`, `deskcommcrm-scheduler-1`,
  `deskcommcrm-worker-1` (healthy), `deskcommcrm-redis-1`,
  WAHA standalone. App em `0.0.0.0:3000`.
- Acesso público: `https://deskcomm.petemcasa.com`, via túnel
  `cloudflared-ponte`.
- **Deploy desta instalação é build local, não o fluxo normal
  (PR → CI → GHCR → update.sh).** O branch `local/v1.20.0-petemcasa`
  nunca foi para a origin e a `main` do clone é rasa. O stack sobe
  com 3 composes juntos:
  `docker-compose.prod.yml + docker-compose.ponte.yml + docker-compose.build.yml`,
  com `APP_PULL_POLICY=never`. Ver §5.

## 3. Mapa modular

| Módulo | O que faz | Onde mora | Depende de |
|---|---|---|---|
| Rotas e telas (App Router) | Inbox, kanban, configurações, painel | `app/` — `(admin)`, `(public)`, `app/`, `api/v1/`, `api/mcp/` | `lib/*`, Supabase |
| API REST | Endpoints versionados por path, JSON snake_case, UUID v4 | `app/api/v1/` | `lib/api/wrappers.ts` (`ok`/`fail`), auth por sessão ou Bearer `dsk_` |
| MCP do gestor | Servidor Streamable HTTP, auth por token, catálogo de tools, auditoria | `lib/mcp/` (`server.ts`, `auth.ts`, `tools/`), rota `app/api/mcp/route.ts` | `lib/mcp/tools/*`, `organizations`/`api_tokens` |
| Decisão Jev | Julgamentos atômicos (Noul/Choice/Score) por tarefa, com limiar e disjuntor; nunca gera texto | `lib/ai/decisao/` (`cliente.ts`, `ponto.ts`, `credencial.ts`, `tarefas.ts`, `roteador.ts`, `manipulacao.ts`) | `ai_provider_credentials`, `organizations.settings.jev` |
| Motor do agente (Ana) | Intent Router (um agente por turno), guardrails, RAG, memória da org e do contato, prompts, voz | `lib/agent-engine/`, `lib/ai/` (`agents/`, `guardrails/`, `knowledge/`, `memoria-do-contato.ts`, `memoria-da-org.ts`, `embeddings/`, `prompts/`) | catálogo MCP (`buildMcpTurnTools`), provedores de modelo, Supabase |
| Canais | WhatsApp (WAHA), Zernio (Messenger, código sem configuração), adapters | `lib/channels/` (`waha-server.ts`, `connect-waha.ts`, `zernio/`, `adapters/`, `social/`) | WAHA externo, webhooks |
| Operação (marcadores, time) | Leitura de marcadores em uso + vocabulário oficial, time | `lib/operacao/marcadores-e-time.ts` | `organizations.settings.canonical_conversation_tags`, `conversations.tags` |
| Schemas | Zod de tudo que entra (API, vocabulário, settings) | `lib/schemas/` (`tags.ts`, `settings.ts`) | — |
| Banco | Migrations numeradas + baseline canônico | `supabase/migrations/`, `supabase/baseline.sql` | `checar:colisao-de-migration` |
| Skills do agente | Subsistema de skills da IA (instalar, apontar, empacotar) | `lib/ai/skills/` | — |
| Skills de projeto | Cópias vendored com `FONTE.md` (origem, commit, licença); original nunca editado | `~/workspace/tuttibom-ops/skills/` (fora do repo; ex.: `typesafe-ai/`) | — |
| Docs e doutrina | 149 docs com regra de precedência; 7 invariantes do sistema vivo | `docs/` (`index.md`, `current-state.md`, `harness-audit.md`, `doctrine/sistema-vivo.md`, `mcp/`, `runbooks/`) | — |
| Testes | Unitários, invariantes/cercas, DB, e2e, shell | `tests/`, `vitest.*.config.ts` | Node 22 (ver §5) |

## 4. Modularidade honesta — o que é e o que não é desacoplado

**De fato independente (dá para mexer sem quebrar o resto):**

- **Adapters de canal** (`lib/channels/adapters/`, e na Ponte): um
  canal novo é um adapter novo; o núcleo do agente não muda.
- **Provedores de modelo:** provedor `custom` aponta para qualquer
  endpoint compatível com OpenAI, por organização, por configuração —
  trocar o 9Router não exige fork.
- **A Ponte:** repo separado, arquitetura hexagonal; conectores vivem
  lá, nunca dentro do Deskcomm.
- **Servidor MCP:** stateless, escopado por token; o gestor externo
  não compartilha estado com o app.
- **Skills de projeto:** vendored por projeto, com `FONTE.md`; mexer
  numa skill do TuttiBom não toca o Deskcomm.
- **Workers:** `scheduler`/`worker` consomem `event_log`; fluxos e
  crons rodam fora do request do app.

**Acoplado na prática (não afirmar independência aqui):**

- **Monólito Next.js:** frontend e backend vivem no mesmo repo e no
  mesmo deploy. Não há serviço separado para "só API" ou "só painel".
- **`organizations.settings` (JSONB) é a superfície de config
  compartilhada:** Jev, vocabulário canônico de tags, motivos de
  perda, etc. moram no mesmo JSON. Mudar a forma de uma chave
  atinge todos os leitores dela.
- **Baseline único:** 649 migrations consolidadas num só
  `baseline.sql` (3,9 MB). Schema novo entra por migration +
  apêndice no baseline, com checagem de colisão de número.
- **Funções SQL compartilhadas:** `fn_role_at_least`,
  `fn_vocabulario_de_tags_operar`, etc. são usadas por painel, API
  e MCP ao mesmo tempo — mudar uma muda os três caminhos.
- **O catálogo MCP é o mesmo da Ana:** as ferramentas do turno da
  Ana são montadas do mesmo catálogo (`buildMcpTurnTools`), menos
  o harness e o que a ferramenta nativa já cobre. Mudar uma tool
  afeta a Ana **e** o gestor externo.
- **Multi-tenancy em todo lugar:** toda tabela tenant-aware tem
  `organization_id` + RLS; service role bypassa RLS, então todo
  handler com admin client tem que filtrar `organization_id`
  manualmente, de fonte confiável, nunca do body.
- **Doutrina com testes-cerca:** os 7 invariantes de
  `docs/doctrine/sistema-vivo.md` são cobrados por testes
  (`tests/`, `vitest.cercas.ts`). Quebrar um invariante quebra o CI
  da feature — e é assim por desenho.
- **`gov:verify` não cobre `test:db` nem `test:e2e`** (ver
  `docs/harness-audit.md`): verde no verify não é prova para
  mudança de schema ou de UI.

## 5. Regras duras — NÃO quebrar

- **Nunca `git pull` no branch `local/v1.20.0-petemcasa`.**
- **Nunca migration direto no banco de produção.** A migration
  chega reaplicando o `baseline.sql` (que inclui o apêndice da
  migration), como o `update.sh` faz — com backup conferido antes.
  O apêndice que cria função vai **antes** do bloco da varredura
  anon no baseline (a cerca proíbe `create function` depois dela).
- **Nunca `docker compose down -v`.** Sempre os composes juntos
  (prod + ponte + build).
- **Nunca desligar `cloudflared-ponte` sem aprovação.**
- **Supabase direto é só-IPv6;** a bridge do Docker não tem IPv6.
  Operações do kit com o banco usam `PSQL_DOCKER_NETWORK=host`.
- **vitest e sondas tsx: Node 22** (`/home/pc/.local/opt/node22/bin`).
  No Node 20, o vitest não sobe o worker e o supabase-js falha.
  tsx não carrega `.env` sozinho: `set -a; . ./.env; set +a` antes.
- **`tsc` estoura o heap padrão do Node:** rodar com
  `NODE_OPTIONS=--max-old-space-size=8192`, em background, com log
  em arquivo.
- **Sessões ssh ao PC morrem aos ~20 min:** trabalho longo com
  `nohup bash -c 'cd /repo && ...' > log 2>&1 & disown` (o `cd` tem
  que estar **dentro** do comando backgroundado) e conferência com
  chamada ssh curta e nova. `pkill -f` casa com o próprio ssh —
  usar o truque de colchetes.
- **Verificar antes de afirmar; `gov:verify` julgado por feature:**
  a suíte completa já é vermelha por falhas pré-existentes. O verde
  se julga por feature, com prova — nunca prometer suíte verde.
- **Nunca segredo no chat, no repo, em log ou neste documento.**
  Segredos vão para o cofre seguro. Um token por agente, nunca
  compartilhado.

## 6. Como trabalhar

1. **Ler antes de codar:** `CLAUDE.md` (doutrina, autoridade final),
   `AGENTS.md` (mesmo contrato, portável), `docs/index.md` (índice
   dos 149 docs e regra de precedência quando dois discordam) e
   `docs/current-state.md` (o que está pronto, incompleto e quebrado).
2. **Confirmar o workspace antes de implementar:** o código certo
   mora em `/home/pc/DeskcommCRM` (branch acima). O projeto
   tuttibom-ops é a instância/documentação em
   `/home/pc/Workspace/tuttibom-ops` — não confundir os dois repos.
3. **Skills são cópias vendored com `FONTE.md`** (origem, commit,
   data, licença, como atualizar). O `SKILL.md` original nunca é
   editado; ajustes vão em arquivo separado. Symlink não é o padrão.
4. **Commit só com os arquivos do trabalho.** Não incluir untracked
   alheio (ex.: `.freebuff-delegate/`, `.onboard-creds.tmp`,
   migrations soltas que não são suas).
5. **Nenhum dado pessoal de comprador no repo ou no painel.**
   Notas de trabalho por lead ficam só no Drive privado do usuário.
6. **Publicar nova versão da Ana ou de fluxo é clique do usuário.**
   Nada é publicado, enviado ou combinado em preço sem a aprovação
   do usuário ao texto (ou imagem) exato; o trabalho chega sempre
   como rascunho primeiro.
7. **Com clientes, "produtor" (José), nunca "gestor".** A Ana nunca
   se apresenta como virtual por conta própria.

## 7. Fronteiras — o que é intocável por este outro agente

**A frente P7 está CONCLUÍDA por mim (2026-11-16 ~09:07 — fita, 3d e preco criadas como oficiais) e continua intocável.** É a
superfície de escrita do vocabulário canônico de tags (ação
`adicionar` + tela de Tags + migration `9224`). HEAD atual:
`fc4a4e0b6 feat(agent): adicionar etiqueta ao vocabulário canônico
de tags (P7)`. Arquivos proibidos:

- `lib/schemas/tags.ts`
- `app/api/v1/tags/vocabulario/route.ts`
- a função `fn_vocabulario_de_tags_operar` e sua migration
  (`supabase/migrations/..._9224_adicionar_etiqueta_no_vocabulario.sql`)
  e o apêndice correspondente em `supabase/baseline.sql`
- `app/app/settings/tags/_painel.tsx`
- `lib/operacao/marcadores-e-time.ts`
- `tests/unit/tags-vocabulario.test.ts`,
  `tests/unit/tags-vocabulario-rota.test.ts` e os testes do painel de
  tags (ex.: `tags-vocabulario-painel-em-espanhol.test.tsx`)

Também fora do escopo dele:

- A **varredura agendada do gestor** (3×/dia, 08:00/14:00/20:00) e
  o estado em `~/workspace/tuttibom-ops/docs/mcp-ultima-varredura.json`.
- O **`fb_agent.py`/Camofox** (Facebook logado, rodando no PC).
- A **navegação do painel** (trinômio agente+camofox+jev): `prototype-vision/panel_drive.py`, `panel_camofox_test.py`, `panel_camofox_open.py`, `panel_camofox_validate.py` e o perfil `prototype-vision/profile-panel/` (sessão do painel). Padrão atual: motor Camoufox + Jev; Chromium headless é fallback.
- **Mexer na Ana em produção** (modelo, prompt, roteador, Jev) ou
  em qualquer configuração da org `deskcomm-local` sem passar por mim.

Se o trabalho dele precisar de qualquer um desses pontos, ele fala
comigo antes — não implementa por conta própria.

## 8. Frentes em aberto no roadmap (tarefas distintas — sem prioridade atribuída)

Ordem e dependências registradas em
`~/workspace/tuttibom-ops/docs/roadmap.md` §10 (ordem: 1 validar
9Router → 2 configurar agente Deskcomm → 3 gestor via MCP →
4 Messenger via Zernio → 5 adapter Messenger via ADB →
6 painel reduzido). Itens 1–3 estão feitos; restam:

- **(4) Messenger via Zernio** — ponte inicial do Messenger.
  Falta: conta Zernio (plano gratuito), conectar a página do
  Facebook, webhook, URL pública HTTPS, testar com mensagem real.
  O Zernio é terceiro sobre as APIs da Meta; o código dele já
  existe em `lib/channels/zernio/`, sem configuração.
- **(5) Adapter Messenger via ADB na Ponte** — alvo e fallback do
  Messenger (se o Zernio falhar, o Messenger volta para o ADB).
  É um tipo novo de adapter, ao lado de Browser/CRM, seguindo a
  arquitetura hexagonal da Ponte. Não existe código de adapter.
- **(6) Painel reduzido a Conteúdo + Planos** — a aba Leads está
  cancelada (o kanban do Deskcomm é a visão de leads). Plano em
  `docs/plano-painel-v2.md` (read-only, só o Muse edita).
- **Saúde do sistema / observabilidade** — fora do Deskcomm, a
  discutir depois: disponibilidade dos modelos, 9Router, alertas
  de saúde/riscos, disco, RAM, CPU, tokens TypeSafe/Jev. Escopo,
  cadência, limiares e destino dos alertas a definir. Detalhe em
  `docs/rascunho-rotina-diaria-gestor.md` §9. Não entra na rotina
  do gestor v1 (o MCP não tem ferramenta de saúde).

## 9. Onde ler mais

- Repo: `CLAUDE.md`, `AGENTS.md`, `docs/index.md`,
  `docs/current-state.md`, `docs/harness-audit.md`,
  `docs/doctrine/sistema-vivo.md`, `docs/doctrine/operacao-de-agentes.md`,
  `docs/mcp/`, `docs/runbooks/deploy.md`, `VISION.md`.
- Projeto TuttiBom (docs, fora do repo):
  `~/workspace/tuttibom-ops/docs/roadmap.md` (§10 ordem,
  §12 estado atual),
  `~/workspace/tuttibom-ops/docs/arquitetura.md`,
  `~/workspace/tuttibom-ops/docs/rascunho-rotina-diaria-gestor.md`,
  `~/workspace/tuttibom-ops/docs/rascunho-mcp-gestor-funcoes.md`,
  `~/workspace/tuttibom-ops/docs/mcp-ultima-varredura.json`,
  `~/workspace/tuttibom-ops/docs/plano-painel-v2.md`.
- Ponte: `/home/pc/ponte/AGENTS.md`.
