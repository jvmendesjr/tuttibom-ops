# Acesso às ferramentas (agentes)

Arquivo único de variáveis, compartilhado por todos os agentes no PC:

- Caminho: `/home/pc/Workspace/tuttibom-ops/.env.ferramentas`
- Permissão `600` (dono `pc`), ignorado pelo git (`.env.*` no `.gitignore`).
- Modelo sem valores: `.env.example` (seção "Acesso às ferramentas").

## Variáveis

| Variável | Ferramenta | Uso |
|---|---|---|
| `PANGRAM_API_KEY` | Pangram | detector de texto IA (D-007) antes da aprovação do José |
| `MAGIC_PATTERNS_API_KEY` | Magic Patterns | logo, site e criativos (D-009) |
| `GAMMA_API_KEY` | Gamma | ferramenta auxiliar paga (D-004) |
| `FRAMER_API_KEY` | Framer | publicação do site |
| `FRAMER_PROJECT_URL` | Framer | projeto alvo da publicação |

Fora deste arquivo, porque já estão integrados no app Deskcomm: Zernio (canal `zernio_social`) e o próprio Deskcomm (`.env` do DeskcommCRM).

## Como carregar

```bash
set -a; . /home/pc/Workspace/tuttibom-ops/.env.ferramentas; set +a
```

## Regras

- Nunca imprimir, logar, commitar ou colar valor no chat; conferir só presença (`[ -n "$VAR" ]`).
- Um token por agente quando a ferramenta permitir; trocar chave = editar só este arquivo.
- Variável vazia = ferramenta sem acesso; o agente avisa e não improvisa outra via.

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

Abrir o agente com as variáveis carregadas:

```bash
scripts/com-ferramentas.sh claude        # ou cursor-agent, gemini
scripts/com-ferramentas.sh mcporter list
```

Se uma ferramenta passar a aceitar chave no MCP, troca-se só a entrada dela nesses quatro arquivos.
