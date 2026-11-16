# Atualização do Deskcomm — 1.44.0 → 1.102.0 (direta, 2026-11-05/06)

## Decisão

- **2026-11-05 ~23:19** — usuário aprovou começar a atualização pela cópia de teste.
- **2026-11-05 ~23:22 — MUDANÇA DE ESCOPO do usuário:** "não há nada de real na
  produção — tudo lá era só dado de teste. Atualiza sem medo e não precisa nem
  copiar." Ou seja: **sem merge na cópia de teste, sem staging, sem backup de
  dados.** Atualização direta do checkout de produção `~/DeskcommCRM`.
- **2026-11-05 ~23:24 — CORREÇÃO do usuário:** NÃO há conta nova — "nova conta"
  foi erro de ditado. O usuário não criou conta nenhuma nem fez primeiro login.
  Não se procurou conta nova nem se criou uma.

## Merge (produção, branch `local/v1.20.0-petemcasa`)

- Commit do merge: `8e2d91ab2` — "Merge origin/main into local/v1.20.0-petemcasa
  (direct update 2026-11-05)".
- Origem: produção na 1.44.0 (último commit `aacb2841b`, 2026-09-26). Destino:
  **upstream v1.102.0 (2026-11-05)** — 1534 commits no `origin/main` desde o
  merge de 28/10. `package.json` continua "0.1.0" nos dois (não informa versão).
- Conflitos resolvidos (4), documentados no commit: (1) `.env.example` — mantidos
  os dois blocos; (2) `.gitignore` — mantidos os dois; (3)
  `docker-compose.prod.yml` — lado upstream para o serviço `waha:` (interno,
  NOWEB, `:latest-2026.7.2`), mantidas as duas redes, adicionados os volumes
  `waha-data:`/`waha-media:` que o merge tinha derrubado;
  (4) `supabase/baseline.sql` — lado upstream + apêndice da Ponte reinserido
  imediatamente ANTES do bloco VARREDURA anon (linha 69245 do arquivo fundido).
- Ponte trazida para a produção: `docker-compose.ponte.yml` copiado da cópia de
  teste (não existia na produção); migração `contact_channels` renumerada
  0425 → **9032** (arquivo, MANIFEST e apêndice do baseline).
- Imagens 1.102.0 baixadas e presentes localmente (app 1,02 GB, worker 2,09 GB,
  scheduler 22,6 MB, criadas 2026-11-05 ~07:28–08:04). Imagens 1.44.0 e 1.20.0
  seguem locais (rollback disponível).

## Correções de governança da Ponte (antes da virada)

O `test:db` do código fundido reprovou 5 testes, todos sobre `contact_channels`
(dívida de desenho da 9032, não regressão do merge). Correções no commit
`dc68ffb73` — "fix(Ponte): contact_channels passa nas 5 invariantes de
governança (9222)":

1. `rls-completude-varredura` — `contact_channels` entra no TABLES de
   `rls-isolation.test.ts`, com seed por organização no `beforeAll`.
2. `lgpd-redact-unificado` — entrada no catálogo (redigir/cascata) + passo **1c**
   na cascata (nova migration **9222**,
   `20261106033532_9222_lgpd_contact_channels_na_cascata.sql`, a partir da
   ÚLTIMA definição do baseline, linhas 65510–66807) + mesmo passo 1c no
   apêndice do baseline.
3. `rbac-config-ia-canais` — a policy ALL só-tenancy vira o par leitura/escrita
   no molde de `contact_phones` (9043): SELECT só-tenancy; ALL com tenancy E
   `fn_role_at_least(organization_id, 'agent')`.
4. `avisos-do-security-advisor` — `SET search_path TO ''` em
   `fn_contact_channels_updated_at` (migration 9032 e apêndice).
5. `platform-admin-full-so-escreve` — `fn_is_platform_admin()` some da policy
   (consequência do item 3).

A 9032 foi **reescrita** (não uma nova migration) porque a tabela ainda não
existia em nenhuma base de produção no momento do merge — a reescrita mantém
`migration == apêndice do baseline`.

## Verificação (antes da virada)

- Checagem de colisão: **OK** — 9222 livre (próximo livre medido: 9229). Aviso
  não-reprovador: 9032 também está no PR aberto #3637 (quem entrar primeiro
  fica, o outro renumera).
- `test:db` direcionado (8 arquivos): **6/7 verdes** — as 5 invariantes acima +
  `rls-isolation` passaram (294 testes). `case-reply-turn.test.ts` falhou nos 5
  testes por **Node 20** (`WebSocket` nativo exige Node 22+; o PC roda v20.19.2
  e não há outro Node) — falha **pré-existente e alheia ao fix** (o arquivo
  agora carrega e executa; antes falhava em `mysql2`, corrigido pelo
  `corepack pnpm install`). O arquivo `tests/unit/leitura-do-turno-escopo.test.ts`
  não rodou (o `vitest.db.config.ts` só inclui invariantes). Log:
  `~/test-db-fixes-20261106.log` (PC).
- `pnpm install` refeito: `mysql2` presente em `node_modules`.

## Virada (2026-11-06 ~00:46–01:04 -03)

Ordem executada: pins → baseline no banco → recriar containers. (Desvio da
ordem listada antes — baseline antes dos containers — porque código novo contra
banco velho é mais arriscado; o próprio `update.sh` do upstream aplica o
baseline antes de religar.)

1. **Pins** — `.env` linhas 45–47: `1.44.0` → `1.102.0` (APP/WORKER/SCHEDULER).
   Backup em `/tmp/.env.bak-20261106` (PC). Nenhum outro valor lido ou alterado.
2. **Pausa** — `docker compose stop app worker scheduler` (espelha
   `pausar_o_que_fala_com_o_banco` do `update.sh`). Redis, WAHA e kiwify-worker
   não foram parados.
3. **Baseline no banco de produção (Supabase cloud)** — via `postgres:17-alpine`
   efêmero, `psql -v ON_ERROR_STOP=1 -f baseline.sql`, espelhando
   `reaplicar_baseline`/`psql_run` do kit. **APPLY-EXIT: 0, zero erros**
   (a única linha com "ERROR" no log é o texto `ON_ERROR_STOP` do próprio
   cabeçalho). Duração ~15 min (lento, não travado — o `psql` avançou de 3,42 MB
   para 3,88 MB do arquivo durante a observação). Detalhe de rede: o container
   em bridge não alcança o Supabase (IPv6 sem rota); foi preciso
   `--network host`. Log: `~/baseline-apply-20261106.log` (PC).
4. **Recriar** — `docker compose -f docker-compose.prod.yml
   -f docker-compose.ponte.yml up -d app worker scheduler`. O serviço interno
   `waha` **não foi iniciado** (decisão interno-vs-externo segue aberta).

## Verificação (depois da virada)

- Containers: app/worker/scheduler em **1.102.0, (healthy)**; redis, WAHA,
  kiwify-worker e srh intactos (Up 7–9 dias, sem restart).
- App local: `/app` → **307** para `/login?next=%2Fapp`; `/` → 200.
- Túnel: `deskcomm.petemcasa.com/app` → **307** para o login (igual a antes);
  `webhooks.petemcasa.com/` → 404 (esperado, endpoint só-POST).
  `cloudflared-ponte.service` ativo.
- WAHA: sessões **tutibom e petemcasa WORKING** (tutibom com pushName TUTTIBOM
  e webhook para o Deskcomm). Logs de app/worker/scheduler sem erros.
- Banco de produção (só presença/contagem, nenhum dado lido): `contact_channels`
  com as policies novas (`tenant_isolation_contact_channels_read`,
  `tenant_isolation_contact_channels_write` + as 3 `support_write_*`); a policy
  ALL antiga sumiu; cascata com passo 1c; `fn_contact_channels_updated_at` com
  `search_path` em `proconfig`; a contagem exata do teste
  `platform-admin-full-so-escreve` retorna **0**.

## Atenção do CHANGELOG (1.78–1.100, lido antes da virada)

Nada travou a virada. Pontos a conferir **depois** (produção só tinha dado de
teste, então o impacto é comportamental, não de dados):

- **1.91** — número novo: retornos automáticos pausam até liberar o número na
  Central ("Número novo aguardando liberação (go-live)"). Conferir a Central.
- **1.86** — campos personalizados agora dizem se são do contato ou do negócio:
  abrir Configurações › Funis e marcar os de contato como "Contato".
- **1.88** — regras com gatilho "Negócio criado" passam a disparar também para
  negócios da Prospecção (se a regra envia mensagem, revisar; excluir com
  `lead.source != prospecting`).
- **1.87** — filtro de palavras do agente passa a valer (conferir o campo em
  cada agente); condição `neq` em campo ausente não dispara mais.
- **1.85** — custo do provedor personalizado passa a ser calculado pelo preço
  do catálogo — **relevante para o 9Router**: se o teto de gasto de IA estiver
  em modo de bloqueio, conferir o teto antes de ligar o binding.
- **1.97** — campos de seleção recusam valor fora das opções do funil
  (`custom_field_value_not_in_list`) — o agente só pode gravar opções válidas.
- **1.100** — contato tipo Fornecedor sai do rodízio automático (padrão é
  Cliente; nada muda para quem nunca marcou o tipo).
- **1.79** — verificado **não afeta**: o worker do Kiwify posta no webhook
  nativo `/api/v1/webhooks/in/[token]` e não grava `origin` — a nota só vale
  para pontes que gravam pedido com o nome da plataforma.
- **1.78** — ChatGPT por assinatura precisa reconectar (não usado aqui); rota
  global do webhook do WhatsApp só atende a rede interna — o WAHA daqui usa
  webhook local (gateway docker), não a rota global.
- 1.98 (moeda do financeiro), 1.84 (cobrança/planos), 1.83 (agenda de colegas),
  1.81 (Nuvemshop/lembretes): sem uso atual; anotados.

## Preservado

WAHA + sessões, `cloudflared-ponte.service`, caminho do webhook Kiwify
(`webhooks.petemcasa.com` → kiwify-worker:3015 → Deskcomm:3000), os dois
composes juntos. Não foi executado `docker compose down -v`. Nada em
`/root/DeskcommCRM`. Nenhum valor de segredo lido ou registrado.

## Observações de segurança / processo

- O mecanismo do kit passa a URL do banco como argumento do `psql` (visível na
  lista de processos enquanto roda). É o mecanismo do próprio upstream, não um
  desvio — fica registrado para revisar depois, sem reproduzir valores.
- Não foi feito backup do banco antes da virada, **por ordem expressa do usuário**
  ("não precisa nem copiar", produção só com dado de teste). Rollback de código:
  imagens 1.44.0 presentes localmente + commits `8e2d91ab2` e `dc68ffb73` na
  branch `local/v1.20.0-petemcasa`. Rollback de banco exigiria restore (não há
  backup novo; os de 2026-10-28 estão em `~/DeskcommCRM/backups/`).
- A validação do 9Router feita contra o 1.44.0 está defasada (ver abaixo).

## O que falta (depois desta atualização)

1. **Revalidar o 9Router contra a 1.102.0** — a URL pública agora existe (túnel
   nomeado `9router`, `9router.petemcasa.com` → 127.0.0.1:20130, verificado
   2026-11-06 ~00:07, docs/tunel-9router.md §8). Falta: credencial custom no
   Deskcomm + binding com `model_id` core-medio + teste de turno real.
2. Configurar o agente Deskcomm para o TuttiBom (prompt, base, handoff G1–G4,
   orçamento).
3. Muse como gestor via MCP (token, papel manager, rotina de revisão).
4. Messenger via Zernio (conta, página, webhook, teste com mensagem real).
5. Ponte: registrar `tutibom` — o adapter Messenger via ADB está
   POSTO DE LADO (D-004, 2026-11-16; ADB pausado).
6. Painel reduzido (Conteúdo + Planos).
7. Decisão WAHA interno vs externo — segue aberta (serviço interno presente no
   compose fundido, não iniciado).
8. `case-reply-turn` segue vermelho por Node 20 — instalar Node 22 no PC (ou
   aceitar como limitação do ambiente) para a suíte ficar verde.
