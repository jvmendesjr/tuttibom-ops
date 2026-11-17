# AGENTS.md — TuttiBom (PC)

Ponto de entrada para qualquer agente que trabalhe neste diretório.
Em conflito: **blueprint** > **decisões** > **roadmap** > este arquivo.
Estado curto: `docs/ESTADO.md`.

## Antes de trabalhar

1. Ler `docs/ESTADO.md`, `docs/blueprint-inicial.md` (§15) e
   `docs/roadmap.md`.
2. Consultar Hindsight bank **`tuttibom`** e `tuttibom-mcp` tools
   `estado` / `onde_esta_tudo` / `decisoes`.
3. O PQBR2 (`/home/pc/Workspace/PQBR2`) é **só modelo/referência** —
   não editar, não copiar às cegas; descartar o que não faz sentido
   para o TuttiBom (ex.: character-bible, Remotion, Flow, NotebookLM,
   workflow de Shorts).

## Onde ficam código e dados

| O quê | Onde |
|---|---|
| Código Python | `src/tuttibom/` (`agents`, `contratos`, `mcp`, `qa`, `workflows`) |
| Config versionada | `config/` (sem segredos) |
| Docs | `docs/` (blueprint, roadmap, decisões, operação) |
| Scripts | `scripts/` |
| Testes | `tests/` |
| Trabalho local | `work/` (gitignored) |
| Segredos | nunca em arquivo no repo; só por referência (nome) |
| Paperclip | instância 3110 — empresa TuttiBom ainda não criada (F1) |
| Conta da loja | Camofox (motor) — painel, redes sociais e criativos; S10/ADB pausado (D-004) |

## Acessos de apoio

| Sistema | Uso |
|---|---|
| **Hindsight** `http://127.0.0.1:8890` bank `tuttibom` | memória de decisões/lições; sem segredos e sem dado de comprador |
| **codebase-memory-mcp** projeto `TUTTIBOM` | busca de código/docs; reindex `mode full` |
| **tuttibom-mcp** | stdio só leitura; **só indica**: estado, mapa, checklist, fila, catálogo, roadmap, decisões, árvore, busca, git — `scripts/tuttibom-mcp` |
| **Ferramentas externas** (Magic Patterns, Pangram, Gamma, Framer, Runway, Higgsfield) | já autenticadas no PC: `scripts/com-ferramentas.sh mcporter call <ferramenta>.<ação>`; Higgsfield pela CLI `higgsfield`; chaves só em `.env.ferramentas` — guia `docs/acesso-ferramentas.md` |

Config de clientes MCP: `docs/operacao/mcp-clients.md`.

**Autenticação das ferramentas externas: UMA por ferramenta, já feita no
PC** — ver `docs/acesso-ferramentas.md`. O agente usa como está e NUNCA
pede, cria ou usa token de outro agente; variável ausente no
`.env.ferramentas` não significa sem acesso (a maioria autentica por
OAuth no mcporter). Se uma ferramenta responder sem acesso, registrar
como bloqueio, não improvisar outra via.

## Desenvolvimento por agentes — regra de delegação (2026-11-13)

- **O Muse implementa tudo ele mesmo.** O desenvolvimento/código/debug é feito pelo Muse diretamente; nada vai para o Cursor (nem para o Agy) até o usuário pedir explicitamente para delegar. Quando o usuário pedir, o agente delegado é o Cursor no PC, via terminal `cursor agent`, usando a cota do Cursor do usuário; o Muse escreve os roteiros/tarefas (briefs em `/tmp/brief-*.md`), revisa os resultados e coordena.
- **Atividade fora do ecossistema TuttiBom:** agentes desenvolvendo a aplicação, com o Muse implementando. Não confundir com o atendimento da loja (Deskcomm/Ana), que é outra trilha.
- **Roteador v0 por modelo — DESCARTADO 2026-11-09 (D-002):** o Jev escolher o modelo por dificuldade não faz sentido — a Ana usa um único modelo (`core-medio`, 9Router, v9). O roteador v0 não será construído; o brief `/tmp/brief-roteador-v0.md` fica como registro. **O que permanece é a decisão de roteamento da RESPOSTA** (ack imediato vs turno completo), que é a classificação de risco com Jev — ver D-002.
- **Modelos prioritários (Cursor, só quando o usuário pedir para delegar):** Grok 4.7, Grok 4.6, Composer 2.5. Como modelos do agente Cursor (`cursor agent --model`): `grok-4.7-high`, `cursor-grok-4.6-high`, `composer-2.5`. Via 9Router, o Grok 4.7 do Cursor é `cu/grok-4.7-low/medium/high`; o Grok 4.6 do Cursor NÃO existe no 9Router (só `factory/grok-4.6` e `warp/grok-4-6-*`); o Composer 2.5 NÃO existe no 9Router.
- **Jev:** CLI `/home/pc/.hermes/bin/jev` (v0.25.3). `jev choose` escolhe o id do modelo na tabela de candidatos, com piso de confiança 0,65 e fallback para `core-medio`. Nunca ler/logar/expor a chave do Jev.
- **Cursor via terminal (só quando o usuário pedir para delegar):** `cursor agent` (subcomando `agent` do `cursor`, v3.27.22 no PC). Modo não-interativo: `cursor agent --print --workspace <dir> "<prompt>"`. Listar modelos: `cursor agent --list-models`. O agente usa a cota do Cursor do usuário.
- **tuttibom-mcp:** stdio, só leitura, só indica (estado, mapa, checklist, fila, catálogo, roadmap, decisões, árvore, busca, git). Comando: `/home/pc/Workspace/tuttibom-ops/scripts/tuttibom-mcp`. Config de cliente MCP: `docs/operacao/mcp-clients.md`.

## Como atualizar docs / estado / decisões

1. Código/config primeiro (mudanças pequenas).
2. Decisão nova → `docs/decisoes/D-NNN-YYYY-MM-DD-….md` (OK do usuário
   quando exigido).
3. `docs/ESTADO.md` + blueprint §15 + `docs/roadmap.md`.
4. **Retain no Hindsight `tuttibom`** — obrigatório ao fim da operação
   quando houve decisão, mudança de estado/fase, lição de falha ou
   proposta. Texto sanitizado (sem segredos, sem dado de comprador).
5. Reindex CBM se a árvore mudou de forma relevante.

Atalho: `tuttibom-mcp` tool `checklist_fim_operacao`.

## Regras (não negociar sem OK do usuário)

- **Nada publica** sem aprovação do usuário ao texto exato.
- **Camofox é o navegador único** do TuttiBom OPS (D-004) — painel,
  redes sociais e criativos; S10/ADB pausado.
- **Sem segredos** no git, logs, MCP ou Hindsight.
- **Sem dado de comprador** no repo, no painel ou no Hindsight.
- **Nunca** IP/porta viva de ADB ou código de pareamento em arquivo.
- **Mídia 100% fictícia**; zero foto/vídeo de cliente.
- **Não** expor `tuttibom-mcp` em porta/tailnet (hoje = stdio local).
- **Não** criar empresa/agente no Paperclip sem ordem explícita.
- **Não** tocar no S10/ADB sem decisão nova do usuário (pausado,
  D-004); não tocar no PQBR2.
- Agente decide **o quê**; script faz **o como**.
- Antes de agir, conferir o perfil do navegador
  (profile-fb/profile-panel) e a sessão; todo print passa pelo Jev;
  sem ações em massa; qualquer alerta de bot → pausar e reavaliar.

## Verificação rápida

```bash
make check
```

## Voice

Respostas ao usuário: PT-BR, curtas e diretas. Timezone America/Fortaleza (UTC-3).

## Padrão de skills do projeto (2026-11-09)
- Skills usadas pelo projeto ficam em `skills/`, no escopo do projeto.
- **Vendoring, não symlink:** a skill é COPIADA (não linkada) para `skills/`,
  com nota de origem e versão num `FONTE.md` junto (repo/URL, commit, data,
  licença, como atualizar). O `SKILL.md` original NÃO é editado — ele é a
  cópia fiel do upstream, para continuar atualizável. Os ajustes específicos
  da nossa aplicação vão num arquivo separado (ex.: `TUTTIBOM.md`).
- **Motivo:** um symlink para `~/.hermes/skills` ou `~/.claude/skills` só
  resolve no PC, quebra na VM e no GitHub, e não trava a versão (o upstream
  mudaria por baixo sem revisão). A cópia deixa o projeto autocontido e a
  versão travada; atualiza-se por decisão, após revisar o diff.
- **Hermes fica com o Hermes:** as skills do Jev do Hermes (em
  `~/.hermes/skills/jev/` ou `~/.claude/skills`) NÃO são copiadas nem tocadas
  aqui. A oficial (`typesafe-ai/skills`) é a que foi copiada para
  `skills/typesafe-ai/` (SKILL.md + LICENSE + FONTE.md + TUTTIBOM.md).
- **Cuidado com o caminho das aplicações:** o DeskcommCRM é uma aplicação
  reaproveitada/compartilhada; o TuttiBom é uma instância (org) dentro dele.
  Skills de projeto (playbooks do Muse/agente) vivem em `tuttibom-ops/skills/`,
  NÃO dentro do DeskcommCRM. Código do Deskcomm vive em `/home/pc/DeskcommCRM`
  (workspace separado do Cursor); código do projeto vive em
  `/home/pc/Workspace/tuttibom-ops/`. Conferir o workspace antes de invocar o
  Cursor — ele só escreve dentro do workspace aberto.
