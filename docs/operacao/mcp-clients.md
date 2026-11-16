# Clientes MCP — `tuttibom-mcp`

Servidor **stdio**, só leitura, **sem porta de rede**. O MCP **só indica**;
o agente age e grava (editar + git quando houver repo). Adaptado do
`pqbr2-mcp`, com melhorias — ver "Diferenças vs PQBR2" no fim.

Comando:

```bash
/home/pc/Workspace/tuttibom-ops/scripts/tuttibom-mcp
```

(ou, no diretório: `./scripts/tuttibom-mcp`, com `PYTHONPATH=src` já
definido pelo script; `TUTTIBOM_ROOT` aponta para o diretório do projeto.)

## Ferramentas (12, todas só leitura)

| Tool | Função |
|---|---|
| `estado` | `docs/ESTADO.md` + roadmap (resumo) + git, se houver repo |
| `roadmap` | `docs/roadmap.md` (F0–F8, decisões) |
| `decisoes` | arquivos em `docs/decisoes/` (mais recentes primeiro) |
| `arvore` | árvore de arquivos |
| `buscar_codigo` | ripgrep no repo |
| `git_status` | status + remotes + log — ou aviso claro de que ainda não é repo git |
| `ler_doc` | lê um path permitido (`docs/`, `src/`, `config/`, `scripts/`, `tests/`, `ops/`, `catalogo/`, `templates/`, README/AGENTS/CHANGELOG/Makefile) |
| `onde_esta_tudo` | mapa: repo, blueprint, roadmap, decisões, fila, catálogo, Hindsight `tuttibom`, codebase-memory `TUTTIBOM`, Paperclip 3110, 9Router :20128, S10, segredos (só onde, nunca conteúdo) |
| `checklist_fim_operacao` | o que o agente deve atualizar ao terminar + alerta se não é repo git |
| `propostas` | lista `docs/propostas/`; com `tema`, README + arquivos do tema |
| `fila_publicacao` | lê `ops/fila-publicacao.md` — hoje não existe no PC; a tool avisa isso sem inventar conteúdo |
| `catalogo` | lê `catalogo/produto-fita-cetim.md` — hoje não existe no PC; a tool avisa isso sem inventar conteúdo |

As *instructions* do servidor trazem o roteiro **Ao começar** /
**Ao terminar**, incluindo as travas do TuttiBom: Camofox é o navegador
único (D-004; S10/ADB pausado), nada publica sem aprovação do texto
exato, conferir o perfil/sessão do navegador antes de agir, todo print
passa pelo Jev, sem ações em massa, nunca registrar IP/porta viva de ADB
ou código de pareamento.

## Teste

O MCP não tem endpoint HTTP para checar; o teste é via stdio. Enviar
um `initialize` + `tools/list` JSON-RPC e conferir as 12 tools:

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}' '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | ./scripts/tuttibom-mcp
```

Saída esperada: as 12 tools acima, nenhuma a mais, nenhuma a menos.

## Clientes

```json
{
  "mcpServers": {
    "tuttibom": {
      "command": "/home/pc/Workspace/tuttibom-ops/scripts/tuttibom-mcp",
      "args": []
    }
  }
}
```

Não usar HTTP/SSE até o usuário autorizar porta/tailnet.

## Dependência

Python 3 + pacote `mcp` (FastMCP) no ambiente do usuário do pc
(já presente no host — verificado na instalação).

## Diferenças vs PQBR2 (melhorias e descartes)

**Melhorias:**

1. `estado` lê `docs/ESTADO.md` + resumo do roadmap e avisa quando não
   há repo git, em vez de quebrar ou devolver erro cru de git.
2. `git_status` e `checklist_fim_operacao` detectam que o diretório
   ainda não é repo git e explicam a F0 pendente, em vez de devolver
   saída de erro do git. No PQBR2 isso nunca acontece, porque lá
   sempre houve repo.
3. `decisoes` não quebra se `docs/decisoes/README.md` não existir.
4. `ler_doc` aceita também `ops/`, `catalogo/` e `templates/` — no
   PQBR2, só docs/src/packages/config/scripts/tests.
5. Tools novas `fila_publicacao` e `catalogo`, que respondem com
   honestidade quando o arquivo ainda não existe no PC, sem inventar
   conteúdo.
6. Instructions com as travas do TuttiBom (identidade do aparelho,
   tela acordada, nunca IP/porta/código, nunca publicar sem aprovação
   do texto exato) — o PQBR2 não tem essas regras, porque não opera
   um telefone.
7. `docs/ESTADO.md` criado já na base, para o `estado` funcionar como
   no PQBR2 desde o dia 1.
8. `Makefile` com alvo `check` (sintaxe do MCP) e `mcp-test`.

**Descartes (não trazidos do PQBR2 porque não fazem sentido aqui):**

- `character-bible/` e Folha de Modelo stickman — identidade visual do
  canal Porquê BR, não da loja TuttiBom.
- Remotion (`packages/core`, `packages/themes/theme-pqbr`) — render de
  vídeo do PQBR2; o vídeo do TuttiBom é o reel entregue pelo Muse.
- Templates Flow (`character-bible/prompts/`) — o Muse substitui o Flow.
- Activities NotebookLM — o Muse substitui o NotebookLM.
- Workflow `produzir_short` e activities de Short — o workflow do
  TuttiBom será `publicar_conteudo` (F5), com outra forma e outras
  travas.
- Postgres app do PQBR2 (`:55435`) e suas migrations — o banco local do
  TuttiBom ainda será criado, com schema próprio.
- Regras de Remotion/`.tsx` e de publicação no YouTube — não existem
  neste projeto.
