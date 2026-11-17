# Acesso às ferramentas (agentes)

Arquivo único de variáveis, compartilhado por todos os agentes no PC:

- Caminho: `/home/pc/Workspace/tuttibom-ops/.env.ferramentas`
- Permissão `600` (dono `pc`), ignorado pelo git (`.env.*` no `.gitignore`).
- Modelo sem valores: `.env.example` (seção "Acesso às ferramentas").

## Autenticação — uma só por ferramenta (2026-11-17)

Cada ferramenta tem UMA autenticação no PC, já feita. O agente delegado
USA essa autenticação como está — nunca pede, cria ou usa token de outro
agente, nunca inventa chave. Variável ausente no `.env.ferramentas` NÃO
significa sem acesso: a maioria das ferramentas autentica por OAuth no
mcporter, não por chave.

- **Magic Patterns:** chave API em `.env.ferramentas`
  (`MAGIC_PATTERNS_API_KEY`, modo 600, fora do git).
- **Pangram, Gamma, Framer, Runway:** OAuth no mcporter
  (`~/.mcporter/credentials.json`, config `config/mcporter.json`) —
  não há chave API delas no `.env.ferramentas`.
- **Higgsfield:** login da CLI (`higgsfield auth login`, 2026-11-17);
  pelo mcporter pede auth (issuer Clerk) — usar a CLI.
- **Framer:** falta `FRAMER_PROJECT_URL` (projeto alvo da publicação) —
  a definir via Framer MCP ou com o usuário; sem ela, publicar não anda.

Verificado 2026-11-17 ~16:20 (`scripts/com-ferramentas.sh mcporter list`):
pangram 3, gamma 25, framer 8, runway 48, magic-patterns 49 tools — todas
respondendo. Se uma ferramenta responder sem acesso, o agente registra
como bloqueio e para — não improvisa outra via.

## Variáveis

| Variável | Ferramenta | Uso |
|---|---|---|
| `MAGIC_PATTERNS_API_KEY` | Magic Patterns | logo, site e criativos (D-009) |
| `FRAMER_PROJECT_URL` | Framer | projeto alvo da publicação — A DEFINIR |

Pangram, Gamma e Framer (API) não têm chave neste arquivo: autenticam por
OAuth no mcporter (ver seção acima). Não recriar essas variáveis vazias —
variável vazia aqui foi o que fazia todo agente novo sinalizar "falta de
acesso" que não existia.

Fora deste arquivo, porque já estão integrados no app Deskcomm: Zernio (canal `zernio_social`) e o próprio Deskcomm (`.env` do DeskcommCRM).

## Como carregar

```bash
set -a; . /home/pc/Workspace/tuttibom-ops/.env.ferramentas; set +a
```

## Regras

- Nunca imprimir, logar, commitar ou colar valor no chat; conferir só presença (`[ -n "$VAR" ]`).
- **Autenticação única:** uma por ferramenta, já feita no PC (seção acima). O agente usa como está — nunca pede, cria ou usa token de outro agente. Trocar chave = editar só este arquivo.
- Sem acesso = a ferramenta responde sem acesso no mcporter/CLI; o agente registra como bloqueio e não improvisa outra via.

## MCPs (todos os agentes do PC)

Configuração no próprio repo, sem segredo (as chaves vêm do `.env.ferramentas` por variável):

| Cliente | Arquivo |
|---|---|
| Claude Code | `.mcp.json` |
| Cursor / cursor-agent | `.cursor/mcp.json` |
| Gemini CLI | `.gemini/settings.json` |
| mcporter | `config/mcporter.json` |

| MCP | Endereço oficial | Autenticação |
|---|---|---|
| magic-patterns | `https://mcp.magicpatterns.com/mcp` | `MAGIC_PATTERNS_API_KEY` (Bearer) |
| pangram | `https://www.pangram.com/mcp` | OAuth (login uma vez por cliente) |
| gamma | `https://mcp.gamma.app/mcp` | OAuth; a `GAMMA_API_KEY` serve à API REST |
| framer | `https://mcp.framer.com/mcp` | OAuth |
| higgsfield | `https://mcp.higgsfield.ai/mcp` | OAuth; fora do Claude Code o login MCP não completa (issuer Clerk) → usar a CLI |
| runway | `https://mcp.runwayml.com/mcp` | OAuth (créditos do plano) |

Abrir o agente com as variáveis carregadas:

```bash
scripts/com-ferramentas.sh claude        # ou cursor-agent, gemini
scripts/com-ferramentas.sh mcporter list
```

Se uma ferramenta passar a aceitar chave no MCP, troca-se só a entrada dela nesses quatro arquivos.

## Higgsfield pela CLI (caminho oficial para agentes)

- `@higgsfield/cli` 1.2.2 em `~/.local/opt/node22/bin/higgsfield` (o `/usr/local/bin/higgsfield` 1.1.26 é antigo; o `com-ferramentas.sh` põe o novo na frente do PATH).
- Login feito em 2026-11-17 (`higgsfield auth login`); credencial local da CLI, nunca copiar.
- Uso: `scripts/com-ferramentas.sh higgsfield model list`, `... higgsfield generate cost ...` antes de gerar (gera crédito).

## Status dos logins (2026-11-17, verificado ~16:20 via `mcporter list`)

Pangram (3 tools), Gamma (25), Framer (8) e Runway (48) autenticados via
`mcporter auth` (token em `~/.mcporter`) e respondendo; Magic Patterns (49
tools) depende de `MAGIC_PATTERNS_API_KEY`. Higgsfield só pela CLI (login
feito em 2026-11-17; pelo mcporter pede auth). Claude Code, Cursor e
Gemini pedem o próprio login na primeira vez (`/mcp`).
