# Projeto: memória automática por contato + roteador (rascunho)

Objetivo: a Ana (e o roteador) consultam automaticamente o histórico do
contato antes de decidir — para que um "olá" de quem já comprou ou
perguntou vá para o produto certo, sem perguntar de novo o que já se sabe.

## O que já existe (verificado)

- **Embedding:** `text-embedding-3-small`, 1536 dim — no `.env` atual
  (`EMBEDDING_MODEL`) e em `lib/ai/embed.ts` (mesmo modelo para indexar
  e buscar, por contrato).
- **Banco vetorial:** pgvector no Postgres do Deskcomm; tabela
  `ai_chunks` (`vector`, `source_id`); a spec define `kb_chunks`
  (`organization_id, source_type, source_id, kb_version, content,
  embedding, metadata`).
- **Busca:** top-k (top-5) via `search_knowledge`; teto `RAG_MAX_TOKENS`
  (2.000). **O retrieval filtra por `organization_id` (tenant-aware,
  regra A5) — NÃO por contato.** Não há `contact_id` na spec de
  retrieval. O filtro por contato é o gap a desenhar.
- **Tabela de contatos:** `contacts` existe (`phone_number`,
  `phone_whatsapp`, `wa_lid`, etc.) — os dados do contato já estão lá.
- **Isolamento por organização:** `organization_id` nas tabelas +
  filtro por tenant — o desenho do Deskcomm já isola por organização
  mesmo usando o mesmo banco. O filtro por contato segue o mesmo
  princípio, um nível abaixo (`contact_id`).
- **A documentação define o caminho de indexação:** quatro fontes
  alimentam a base vetorial por tenant — FAQ, política da loja,
  catálogo, **conversas resolvidas**. Cada fonte passa por chunker +
  embedder, grava em `ai_chunks` com `vector` e `source_id`.
  Re-indexação por cron `rag-reindex` ou trigger ao atualizar a fonte.
  Consumo por busca top-k. (docs/research/architecture-diagrams.md)
  **Mas:** o cron `rag-reindex` não aparece no código (`lib/`, `app/`)
  e a base "Conversas anteriores" está com 0 chunks — a indexação de
  conversas NÃO está rodando hoje.
- **O roteador Jev (verificado no código):** decide **qual agente
  atende**, entre os membros do roteador de intenção do número
  (`lib/ai/decisao/roteador.ts`, `tarefas.ts`). É `substitui`: decidindo,
  a escolha dele toma o lugar da do classificador de sempre, que vira a
  reserva. **Só roda onde há um roteador de intenção ATIVO no número/
  sessão** (no máximo 1 por `channel_session`; sem ele, o fluxo segue
  sem rotear). **A pergunta ao Jev leva só a última mensagem do cliente
  (R4) + as intenções do roteador (descrição e exemplos, textos da
  empresa) — NÃO leva histórico nem memória do contato.** Por isso, para
  um "olá", o roteador sozinho não sabe o histórico: usar a memória no
  roteador é uma mudança de desenho (alimentar a memória na entrada dele
  ou num passo antes). Há uma decisão registrada (DEC-012, doc 89) sobre
  por que o Jev não roteia sozinho nesta empresa.
- **O roteador é de AGENTES, não de skills.** A escolha de skill dentro
  da Ana é keyword matching determinístico (últimas 6 mensagens), não
  Jev. Um roteador de skills via Jev é uma opção separada, a avaliar.

## O que falta verificar

- O número/sessão do TuttiBom tem um roteador de intenção ATIVO? **SIM,
  desde 2026-11-13 ~13:00** — `ai_routers` `c8c955b5-9a8f-4ba0-bdad-aa5a38627ded`
  "Roteador TuttiBom" (sessão `31436449`, 558881022939), fallback Ana v9,
  3 membros todos Ana (`fita`, `impressao_3d`, `preco`); tarefa Jev
  `roteador` em `decidindo`, modo comparação. Verificado com as funções
  do turno contra o banco de produção.
- O RPC `retrieve_top_k_chunks` aceita filtro por contato, ou só por
  organização? (A spec só mostra `organization_id`.)
- O cron `rag-reindex` existe em algum lugar fora de `lib/`/`app/`
  (scheduler, worker), ou é só aspiração da doc?

## Decisões técnicas (delegadas a Muse pelo usuário, 2026-11-12)

- **O que guardar:** conversas resolvidas, com metadados (contato,
  organização, produto/interesse). Alternativa: um resumo por contato.
  Decidir após a verificação.
- **Como buscar:** top-k semântico filtrado por `organization_id` +
  `contact_id`.
- **O que buscar:** os trechos relevantes do histórico do contato para
  a mensagem atual — o roteador decide com isso.
- **Skill ou agente por baixo do pano:** decisão de Muse quando o
  catálogo 3D existir. Inclinação atual: Ana como rosto único,
  especialistas por trás; skill primeiro, agente se ficar pesado.

## Fases

1. **Verificação** (docs + código) — confirmar os itens acima.
2. **Desenho** — o que guardar, como buscar, onde o roteador consulta.
3. **Indexação automática** — job (cron/trigger) que indexa conversas
   resolvidas.
4. **Roteador + busca por contato** — ligar a tarefa roteador e o
   filtro por contato.
5. **Prova** — contatos de teste (inclusive fictícios; o usuário vai
   trazer a referência do CRM que dá dicas de criar usuários fictícios
   para provar as ações automáticas). "Olá" de quem já comprou vai para
   o produto certo; contato novo, sem histórico, segue o caminho neutro.
6. **Deploy** — com aprovação separada.

## Regras

- Nada de código sem brief aprovado; nada de commit/deploy sem
  aprovação separada.
- Isolamento por organização e por contato é obrigatório.
- Sem dados de comprador no repo.
- Jev: o serviço está ligado e rodando (manipulação, clima, opt-out,
  reconhecimento do ack). A tarefa "roteador" é um julgamento específico
  que hoje não é chamado por nenhum fluxo — é ela que precisa ser ligada,
  não o Jev.
- Seleção de skills hoje: keyword matching determinístico (últimas 6
  mensagens), não Jev. Um roteador de skills via Jev é uma opção real
  (mais preciso que palavra-chave), a avaliar no desenho.

## Implementação (Muse, 2026-11-12 ~22:26–01:52)

**Mudança de condução (usuário, 2026-11-12 22:25):** "o caminho agora é
você mesmo seguir o brief" — o Muse implementou, em vez de delegar ao
Agy. O Agy não escreveu código neste projeto.

Repo `/home/pc/DeskcommCRM`, branch `local/v1.20.0-petemcasa`, baseline
HEAD `80f354895`, árvore limpa no início. **Commit `305e8e124`**
(2026-11-13 ~00:05, 17 arquivos, só a feature) e **deploy concluído**
2026-11-13 ~00:33 — ver "Commit + deploy" abaixo.

### O que foi entregue (contra o brief, item a item)

- **Fase 1a — `contact_interests`** (migration `20261112230000_9223`,
  + apêndice no `baseline.sql`, + entrada em `lib/database.types.ts`):
  um registro por (organização, contato), `produto` (`fita`|`3d`|`ambos`
  |null, sem CHECK — vocabulário em TS), `ocasiao`, `ultimo_produto`,
  `ultimo_stage`, RLS por tenant, triggers de auditoria e `updated_at`.
  Leitura em `lerInteresseDoContato` (nunca joga exceção) e upsert em
  `atualizarInteresseDoContato` (null nunca apaga — `coalesce`).
- **Fase 1b — ingestão por contato** (`lib/ai/rag/ingest/memoria-contato.ts`
  + cron `app/api/v1/cron/kb-memoria-contato-batch/route.ts`, agendado
  03:35 no `docker/scheduler/entrypoint.sh`, 5 min depois do lote
  anonimizado das 03:30): conversas resolvidas → `ai_chunks` com
  `metadata.contact_id`, `source_type='memoria_contato'`, **sem
  anonimizar** (o filtro por contato é a proteção); guarda de PII
  residual bloqueia a conversa inteira; versão ativa ÚNICA e cumulativa
  (não apaga a memória antiga, ao contrário do lote anonimizado, que
  troca a versão a cada run); contatos pessoais/anonimizados fora.
  Depois de indexar, deriva o interesse por regras (etiqueta do produto
  apresentado no negócio + decisões do roteador + estágio) e grava
  `contact_interests`. O pipeline anonimizado (`conversas`,
  `kb-conversations-batch`) **não foi tocado**.
- **Fase 1c — busca por contato** (`buscarMemoriaDoContato` em
  `lib/ai/memoria-do-contato.ts` + `fn_buscar_trechos_do_contato` no
  banco): filtra por organização + contato, fonte `memoria_contato`,
  versão ativa, modelo de embedding; pré-checagem de existência evita
  embeddar quando não há memória; teto de tokens igual ao do RAG.
  No turno (`inbound-turn.ts`), o bloco `## Memória deste contato`
  entra no FIM do system (prefixo cacheável intacto), só quando há
  pergunta e não é prévia; falha de memória nunca derruba o turno.
- **Fase 2 — roteador** (`roteador.ts` + `resolve-turn-agent.ts`):
  a pergunta ao Jev leva o **rótulo do interesse** (`fita de cetim
  personalizada` / `impressão 3D` / ambos, + ocasião quando houver) —
  **nunca PII cru** (sem nome, telefone ou endereço); o `state` continua
  só a mensagem limpa (R4). **Decisão determinística primeiro:** interesse
  em um produto só + saudação fechada (`olá`, `bom dia`...) + sem sticky
  em outro membro → o código decide direto, sem Jev e sem classificador.
  Com conflito, sem registro ou mensagem que não é saudação, o caminho
  normal roda e o Jev recebe o rótulo.

### Provas (container `node:22`, no PC)

- Unitários: `memoria-do-contato` 25 testes, `roteador` 26,
  `resolve-turn-agent` 68 (incl. 6 novos da memória: 3d+olá→3D,
  fita+olá→fita, novo+olá→só mensagem, não-saudação→Jev com rótulo,
  ambos→classifica, sticky em outro membro→não troca) — **119/119**.
- Invariantes (`test:db`, Postgres real, baseline install + update com
  `ON_ERROR_STOP=1`): `tests/invariants/memoria-por-contato.test.ts`
  **6/6** — upsert sem duplicar e sem apagar com null; A vê só o trecho
  dele, B só o dele, contato sem memória vê nada; memória não cruza a
  organização; função não executável por `anon`, sim por
  `authenticated`/`service_role`.
- `gov:verify`: typecheck + lint **verdes** (3 erros meus + 6
  pré-existentes de typecheck corrigidos; os 6 eram mocks sem tipo em
  `saudacao-fechada.test.ts` e `reconhecimento-imediato.test.ts`).
  `test:unit` completo: 34.968 passaram, **108 falharam** — 1 era minha
  (`varredura-anon-e-o-ultimo-bloco`: a função nova estava depois do
  bloco da varredura; apêndice movido para ANTES dele, teste passa
  5/5) e **107 são pré-existentes no HEAD** (verificadas uma por uma:
  nenhuma importa meus módulos; as que leem `inbound-turn.ts` como
  texto falham em marcadores/regiões que meu diff não toca; o crash
  `toolIds.filter` em `sem-agenda.ts` vem do corte das tools de agenda;
  a constraint duplicada é `ai_agent_versions_voz_quando_check`, de
  voz). `checar:colisao-de-migration` OK para o 9223.

### Commit + deploy (2026-11-13 ~00:05–00:33)

- **Commit `305e8e124`** — `feat(agent): memória por contato +
  roteador Jev com rótulo de interesse`, 17 arquivos, 2.176 inserções.
  Fora do commit (não são do projeto): `supabase/migrations/
  20260827220000_0159_contact_channels.sql` (duplicata antiga da
  migration renumerada para 9032 em 2026-11-05 — reapareceu sozinha no
  repo às 23:46), `.freebuff-delegate/`, `.onboard-creds.tmp` e
  `core.*` (dump de crash do vitest, removido antes de commitar).
- **Deploy local no PC** (build local, não PR para a main — branch
  nunca empurrado, main rasa sem ancestral comum): backup do banco
  antes (dump + snapshot WAHA, concluído); build da imagem
  `ghcr.io/melgarafael/deskcommcrm:1.102.0` local (00:21); baseline
  re-aplicado no Supabase cloud em 1 passada (`BASELINE_OK`), tabela
  `contact_interests` e `fn_buscar_trechos_do_contato` conferidas em
  produção; `up -d` com prod+ponte+build e `APP_PULL_POLICY=never`;
  app recriado e **healthy**.
- **Verificação pós-deploy:** `/` → 200, `/app` → 307, health
  `healthy` (supabase/redis/waha ok), WAHA tutibom **WORKING**,
  rota `kb-memoria-contato-batch` no ar (403 sem auth = fail-closed,
  igual à rota antiga).
- **Gotcha de rede (aprendido no deploy):** o host do banco direto do
  Supabase (`db.<ref>.supabase.co`) é **só-IPv6** e a bridge do Docker
  **não tem IPv6** — o `pg_dump`/`psql` do kit morre com "Network
  unreachable". O kit já prevê: `PSQL_DOCKER_NETWORK=host` (o host
  alcança o banco por IPv6). Backup e baseline rodaram assim.

### Gaps honestos (para o relatório ao usuário)

- `ocasiao` existe na tabela, mas **não há fonte estruturada de ocasião
  no código** — fica null na v1 até uma skill registrá-la.
- O interesse é atualizado **pelo lote noturno**, não na resolução da
  conversa (o brief aceitava "na resolução ou por job"; o job foi o
  escolhido para não tocar nos 5+ caminhos de resolução).
- A decisão determinística **não é registrada em `jev_router_decisions`**
  (não há `modo`/`origem` para ela) — só log estruturado.
- A tarefa "roteador" do Jev segue com o estado que estava no banco; a
  ligação dela para o número do TuttiBom é passo de configuração, não de
  código.
- Dois testes ensinaram: o `interesseRotulo` só vai na entrada do Jev
  quando há registro (sem memória, a entrada é byte a byte a de antes);
  e a função só filtra por modelo quando o chamador passa o modelo —
  o chamador real passa, o teste inicial não passava.

## Delegação e estado (2026-11-12)

- **Brief aprovado e escrito:** `~/workspace/briefs/brief-memoria-interna-roteador-jev.md`
  (cópia no PC: `/home/pc/Workspace/tuttibom-ops/briefs/brief-memoria-interna-roteador-jev.md`).
  Repo `/home/pc/DeskcommCRM`, branch `local/v1.20.0-petemcasa`,
  HEAD agora `305e8e124` (memória por contato, commitada e deployada
  2026-11-13).
- **Agente:** Agy (Google Antigravity), por ordem do usuário (2026-11-12
  20:50). **Opus 4.6 primeiro; se acabar o limite, Gemini 3.8 no modo
  high.** IDs: Opus 4.6 = `claude-opus-4-6-thinking`; Gemini 3.8 high =
  `gemini-3.8-flash-high`. CLI `agy` em `/home/pc/.local/bin/agy`
  (só no PATH do terminal interativo/login). Modo headless
  `agy --print="prompt"` (o `--print` consome o próximo argumento como
  prompt — usar a forma com `=` e colocar `--model` em outro lugar),
  com `--add-dir /home/pc/DeskcommCRM` e
  `--dangerously-skip-permissions`.
- **Bloqueio de auth:** o `agy` a partir de sessão SSH não-interativa
  NÃO está autenticado — pede OAuth interativo do Google (timeout 60 s).
  Um `--print` do zero foi lançado e encerrado após travar no login
  (2026-11-12 21:54). O `agy` interativo do usuário (pts/1, desde
  20:54) ESTÁ logado, mas parado esperando o prompt. Caminho que
  funciona: dar o brief para o `agy` interativo já rodando, ou o usuário
  logar o CLI e o Muse relançar o `--print`.
- **Condução:** o Muse conduz e monitora (ordem do usuário, 2026-11-12
  20:57) — verifica cada entrega contra o brief (workspace, travas,
  testes, desenho) e reporta desvios para o usuário repassar ao Agy.
- **Estado 2026-11-12 21:19:** baseline confirmado (HEAD `80f354895`,
  branch `local/v1.20.0-petemcasa`, árvore limpa). **O Agy ainda NÃO
  escreveu código** (nenhum arquivo novo em 2+ h).
- **Travas:** sem `git pull`, sem troca de branch, sem migration direto
  no banco de produção, sem `docker compose down -v`, sem tocar no
  cloudflared; **sem commit nem deploy sem aprovação separada**.
