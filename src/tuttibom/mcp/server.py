"""tuttibom-mcp — servidor MCP só leitura via stdio (sem porta de rede).

Adaptado do pqbr2-mcp (PQBR2, modelo), com melhorias para a realidade do
TuttiBom — ver docs/operacao/mcp-clients.md, seção "Diferenças vs PQBR2".

Expõe estado, roadmap, decisões, propostas, fila de publicação, catálogo,
mapa de acessos, checklist de fim de operação, árvore/busca no código e
status git. O MCP só indica; o agente grava (editar + git/commit quando
houver repo). Nada destrutivo. Nada de bind/porta.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(os.environ.get("TUTTIBOM_ROOT", Path(__file__).resolve().parents[3]))
VERSAO = "0.1.1"

mcp = FastMCP(
    "tuttibom-mcp",
    instructions=(
        "tuttibom-mcp — MCP de manutenção do TuttiBom: SÓ LEITURA, stdio. "
        "O MCP só INDICA; quem age e grava é o agente.\n"
        "AO COMEÇAR: 1) `estado` 2) `onde_esta_tudo` (repo, blueprint, roadmap, "
        "decisões, Hindsight bank tuttibom, codebase-memory TUTTIBOM, Paperclip "
        "3110, fila, catálogo) 3) `decisoes`/`propostas`/`ler_doc` conforme a "
        "tarefa 4) recall no Hindsight bank tuttibom.\n"
        "AO TERMINAR: chamar `checklist_fim_operacao` e cumprir: código/config "
        "→ decisão (se houver) → blueprint/roadmap → retain Hindsight tuttibom "
        "(sanitizado) → reindex CBM se a árvore mudou.\n"
        "REGRAS DO TUTTIBOM (não negociar): Camofox é o navegador único "
        "(D-004); S10/ADB pausado — não tocar no S10 sem decisão nova do "
        "usuário; nada é publicado, enviado ou combinado em preço sem "
        "aprovação do usuário ao texto exato; antes de agir no Facebook ou "
        "no painel, conferir o perfil do navegador (profile-fb/profile-panel) "
        "e a sessão; todo print passa pelo Jev; nunca registrar IP/porta viva "
        "de ADB ou código de pareamento em arquivo, doc ou memória; nunca dado "
        "de comprador no repo, no painel ou no Hindsight; imagens reais só com "
        "autorização para demonstrar, amostra personalizada é render fictício "
        "(correção 2026-11-06 — a regra '100% fictícia' como regra geral está "
        "superada); nunca segredos. Regras completas: AGENTS.md.\n"
        "FERRAMENTAS EXTERNAS (Magic Patterns, Pangram, Gamma, Framer, Runway, "
        "Higgsfield): autenticação ÚNICA por ferramenta, JÁ FEITA no PC — usar "
        "como está, via `mcporter call` (config `config/mcporter.json`) e CLI "
        "`higgsfield`; guia em `docs/acesso-ferramentas.md`. O agente NUNCA pede, "
        "cria ou usa token de outro agente; se uma ferramenta responder sem "
        "acesso, registrar como bloqueio, não improvisar outra via. Geração gasta "
        "crédito: só quando a tarefa pedir."
    ),
)


def _ler(rel: str, limite: int = 120_000) -> str:
    path = (ROOT / rel).resolve()
    if not str(path).startswith(str(ROOT.resolve())):
        raise ValueError("caminho fora do repo")
    if not path.is_file():
        raise FileNotFoundError(rel)
    texto = path.read_text(encoding="utf-8", errors="replace")
    if len(texto) > limite:
        return texto[:limite] + f"\n\n…[truncado em {limite} chars]"
    return texto


def _run(cmd: list[str], timeout: int = 30) -> str:
    p = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
    return out.strip() or f"(exit {p.returncode}, sem saída)"


def _eh_git() -> bool:
    return (ROOT / ".git").is_dir()


@mcp.tool()
def estado() -> str:
    """Estado curto do TuttiBom: blueprint + roadmap + git (se houver)."""
    partes = [f"# tuttibom-mcp {VERSAO}", f"ROOT={ROOT}"]
    try:
        partes.append(_ler("docs/ESTADO.md"))
    except FileNotFoundError:
        # docs/ESTADO.md existe no repo canônico; este fallback só vale se
        # o arquivo não estiver neste diretório. Não inventar conteúdo.
        partes.append("(docs/ESTADO.md não encontrado neste diretório; estado curto em "
                      "docs/blueprint-inicial.md §15 e docs/roadmap.md)")
    try:
        partes.append("## roadmap (resumo)\n" + _ler("docs/roadmap.md", 12_000))
    except FileNotFoundError:
        partes.append("(docs/roadmap.md ainda não existe)")
    if _eh_git():
        partes.append("## git HEAD\n" + _run(["git", "log", "-1", "--oneline"]))
        partes.append("## branch\n" + _run(["git", "status", "-sb"]))
    else:
        partes.append("## git\n(este diretório não é um repo git — verificar; o repo "
                      "canônico tem git desde 2026-11, branch main; não inventar branch/commit)")
    return "\n\n".join(partes)


@mcp.tool()
def roadmap() -> str:
    """Roadmap completo (fases F0–F8, decisões, adaptações)."""
    return _ler("docs/roadmap.md")


@mcp.tool()
def decisoes(limite: int = 20) -> str:
    """Lista e conteúdo das decisões em docs/decisoes/ (mais recentes primeiro)."""
    pasta = ROOT / "docs" / "decisoes"
    if not pasta.is_dir():
        return "(docs/decisoes/ ainda não existe — nenhuma decisão registrada aqui)"
    arquivos = sorted(
        [p for p in pasta.glob("D-*.md")],
        key=lambda p: p.name,
        reverse=True,
    )[: max(1, min(limite, 50))]
    blocos: list[str] = []
    try:
        blocos.append(_ler("docs/decisoes/README.md", 8_000))
    except FileNotFoundError:
        blocos.append("(docs/decisoes/README.md ainda não existe)")
    if not arquivos:
        blocos.append("(nenhuma decisão D-*.md registrada ainda)")
    for p in arquivos:
        blocos.append(f"---\n# {p.name}\n" + p.read_text(encoding="utf-8", errors="replace"))
    return "\n\n".join(blocos)


@mcp.tool()
def arvore(max_depth: int = 3) -> str:
    """Árvore de arquivos do repo (sem .git, node_modules, .venv, work/*)."""
    depth = max(1, min(int(max_depth), 6))
    ignore = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
    linhas: list[str] = [str(ROOT)]

    def walk(base: Path, prefix: str, nivel: int) -> None:
        if nivel > depth:
            return
        try:
            filhos = sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return
        for i, filho in enumerate(filhos):
            if filho.name in ignore:
                continue
            if filho.name == "work" and filho.is_dir():
                linhas.append(f"{prefix}{'└── ' if i == len(filhos) - 1 else '├── '}work/  (gitignored)")
                continue
            conector = "└── " if i == len(filhos) - 1 else "├── "
            linhas.append(f"{prefix}{conector}{filho.name}{'/' if filho.is_dir() else ''}")
            if filho.is_dir():
                ext = "    " if i == len(filhos) - 1 else "│   "
                walk(filho, prefix + ext, nivel + 1)

    walk(ROOT, "", 1)
    return "\n".join(linhas)


@mcp.tool()
def buscar_codigo(padrao: str, glob: str = "*.md") -> str:
    """Busca texto no código/docs com ripgrep (só leitura). glob padrão: *.md."""
    if not padrao or len(padrao) > 200:
        raise ValueError("padrao inválido")
    cmd = [
        "rg",
        "-n",
        "--no-heading",
        "-S",
        "-g",
        glob,
        "-g",
        "!.git/**",
        "-g",
        "!node_modules/**",
        "-g",
        "!.venv/**",
        "-g",
        "!work/**",
        "--max-count",
        "50",
        padrao,
        str(ROOT),
    ]
    return _run(cmd, timeout=45)


@mcp.tool()
def git_status() -> str:
    """Status git + remotes + últimos 8 commits (ou aviso claro se não é repo git)."""
    if not _eh_git():
        return ("Este diretório não é um repo git.\n"
                "Verificar: o repo canônico tem git desde 2026-11 (main, remoto "
                "GitHub jvmendesjr/tuttibom-ops). Não criar repo/branch aqui sem "
                "conferir onde está o repo canônico.")
    return "\n\n".join(
        [
            "## status\n" + _run(["git", "status", "-sb"]),
            "## remotes\n" + _run(["git", "remote", "-v"]),
            "## log\n" + _run(["git", "log", "-8", "--oneline", "--decorate"]),
        ]
    )


@mcp.tool()
def ler_doc(caminho: str) -> str:
    """Lê um arquivo de documentação relativo ao root (ex.: docs/roadmap.md)."""
    caminho = caminho.lstrip("./")
    if ".." in Path(caminho).parts:
        raise ValueError("caminho inválido")
    if not (
        caminho.startswith("docs/")
        or caminho in {"README.md", "AGENTS.md", "CHANGELOG.md", "Makefile"}
        or re.match(r"^(src|config|scripts|tests|ops|catalogo|templates)/", caminho)
    ):
        raise ValueError("só docs/, AGENTS/README/CHANGELOG/Makefile, src/, config/, scripts/, tests/, ops/, catalogo/, templates/")
    return _ler(caminho)


@mcp.tool()
def onde_esta_tudo() -> str:
    """Mapa de onde fica cada coisa do TuttiBom (repo, docs, memórias externas, painel). Só leitura."""
    # Mapa calculado, não fixo: o que era texto fixo ("ainda sem git",
    # "ainda não existe no PC") ficou desatualizado e fazia todo agente novo
    # sinalizar uma falha que não existia. Conferir no disco a cada chamada.
    git_txt = "git, branch `main`, remoto GitHub `jvmendesjr/tuttibom-ops`" if _eh_git() else "sem git — verificar"
    fila_txt = "`ops/fila-publicacao.md`" + (" (existe)" if (ROOT / "ops/fila-publicacao.md").is_file() else " (ainda não existe)")
    cat_txt = "`catalogo/produto-fita-cetim.md`" + (" (existe)" if (ROOT / "catalogo/produto-fita-cetim.md").is_file() else " (ainda não existe)")
    return f"""# Onde está tudo — TuttiBom (tuttibom-mcp {VERSAO})

| O quê | Onde | Como acessar |
|---|---|---|
| Repositório (PC) | `{ROOT}` — {git_txt} | `arvore`, `git_status` |
| Blueprint | `docs/blueprint-inicial.md` (§15 = Paperclip) | `ler_doc`, `estado` |
| Roadmap | `docs/roadmap.md` (F0–F8, decisões) | `roadmap` |
| Decisões canônicas | `docs/decisoes/D-*.md` | `decisoes` |
| Propostas (não canônicas) | `docs/propostas/<tema>/` | `propostas` |
| Operação / clientes MCP | `docs/operacao/` | `ler_doc` |
| Fila de publicação | {fila_txt} | `fila_publicacao` |
| Catálogo (fita de cetim) | {cat_txt} | `catalogo` |
| Regras para agentes | `AGENTS.md` | `ler_doc` |
| Memória externa | Hindsight `http://127.0.0.1:8890` bank **`tuttibom`** | recall no início; retain no fim (sanitizado, sem dado de comprador) |
| Memória de código | codebase-memory-mcp projeto **`TUTTIBOM`** | busca/grafo; reindex `mode full` (`docs/operacao/codebase-memory.md` quando existir) |
| Painel / tarefas | Paperclip F1 CANCELADA 2026-11-05 (Deskcomm atende); painel reduzido adiado para após a produção inicial | `docs/plano-painel-v2.md` |
| Modelos (LLM) | 9Router `http://127.0.0.1:20128/v1` (não o :20130 do PQBR2) | `config/modelos_9router.json` |
| Código | `src/tuttibom/`, `config/`, `scripts/`, `tests/` | `arvore`, `buscar_codigo` |
| Trabalho local | `work/` (gitignored) | não versionar |
| Ferramentas externas (Magic Patterns, Pangram, Gamma, Framer, Runway, Higgsfield) | `docs/acesso-ferramentas.md`; autenticação ÚNICA por ferramenta, já feita no PC (Magic Patterns por chave em `.env.ferramentas`; demais por OAuth no mcporter; Higgsfield só pela CLI) | `scripts/com-ferramentas.sh mcporter call <ferramenta>.<ação>`; Higgsfield: `higgsfield` |
| Segredos | nunca em arquivo no repo; só por referência (nome) | NUNCA ler/expor via MCP |
| Conta da loja | Camofox é o navegador único (D-004); S10/ADB pausado | `docs/decisoes/D-004-*.md`; nunca IP/porta/código de pareamento em arquivo |
| PQBR2 (modelo) | `/home/pc/Workspace/PQBR2` | só referência; não editar |

Ao terminar: `checklist_fim_operacao`.
"""


_DOCS_FIM = ("docs/blueprint-inicial.md", "docs/roadmap.md")


@mcp.tool()
def checklist_fim_operacao() -> str:
    """Checklist do que o AGENTE deve atualizar ao fim da operação. Só leitura."""
    linhas = [
        "# Checklist fim de operação — o agente executa; o MCP só indica",
        "1. Código/config alterados (mudanças pequenas, uma por vez).",
        "2. Decisão nova → `docs/decisoes/D-NNN-YYYY-MM-DD-….md` (+ OK do usuário quando exigido).",
        "3. `docs/blueprint-inicial.md` §15 e `docs/roadmap.md` — onde estamos + próximo passo.",
        "4. Retain Hindsight bank `tuttibom` (obrigatório se houve decisão, lição, mudança de estado ou proposta; texto sanitizado, sem segredos e sem dado de comprador).",
        "5. Reindex codebase-memory `TUTTIBOM` se a árvore mudou.",
        "6. Nada publicado/enviado sem aprovação do usuário ao texto exato.",
        "7. Nenhum IP/porta viva de ADB ou código de pareamento registrado.",
    ]
    if _eh_git():
        p = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
        sujos = [l[3:].strip() for l in (p.stdout or "").splitlines() if len(l) > 3]
        alertas: list[str] = []
        if sujos:
            alertas.append(f"⚠ git sujo: {len(sujos)} arquivo(s) não commitados.")
            mexeu_codigo = any(not f.startswith("docs/") for f in sujos)
            faltando = [d for d in _DOCS_FIM if d not in sujos]
            if mexeu_codigo and faltando:
                alertas.append("⚠ código/config mudou mas não foram tocados: " + ", ".join(faltando))
        adiante = _run(["git", "rev-list", "--count", "@{u}..HEAD"])
        if adiante.isdigit() and int(adiante) > 0:
            alertas.append(f"⚠ {adiante} commit(s) locais sem push.")
        linhas.append("\n## Situação atual\n" + ("\n".join(alertas) if alertas else "✓ árvore limpa e sincronizada."))
        if sujos:
            linhas.append("\n```\n" + "\n".join(sujos[:60]) + "\n```")
    else:
        linhas.append("\n## Situação atual\n⚠ diretório sem repo git — "
                      "verificar; o repo canônico tem git desde 2026-11; "
                      "documentar a mudança no blueprint/roadmap e, quando houver repo, commitar.")
    return "\n".join(linhas)


@mcp.tool()
def propostas(tema: str = "") -> str:
    """Lista propostas (não canônicas) em docs/propostas/. Com `tema`, devolve o README do tema e a lista de arquivos."""
    base = ROOT / "docs" / "propostas"
    if not base.is_dir():
        return "(docs/propostas/ não existe ainda)"
    if tema:
        if "/" in tema or ".." in tema:
            raise ValueError("tema inválido")
        pasta = base / tema
        if not pasta.is_dir():
            raise FileNotFoundError(tema)
        arqs = sorted(p.name for p in pasta.iterdir() if p.is_file())
        out = [f"# docs/propostas/{tema}/", *[f"- {a}" for a in arqs]]
        if (pasta / "README.md").is_file():
            out.append("\n---\n" + _ler(f"docs/propostas/{tema}/README.md", 20_000))
        out.append("\nLer um arquivo: `ler_doc docs/propostas/<tema>/<arquivo>`.")
        return "\n".join(out)
    out = ["# docs/propostas/ — proposta ≠ canônico (vira canônico só via decisão)"]
    for pasta in sorted(p for p in base.iterdir() if p.is_dir()):
        arqs = sorted(p.name for p in pasta.iterdir() if p.is_file())
        out.append(f"\n## {pasta.name}/\n" + "\n".join(f"- {a}" for a in arqs))
    return "\n".join(out)


@mcp.tool()
def fila_publicacao() -> str:
    """Fila de publicação (ops/fila-publicacao.md). Sem inventar conteúdo se o arquivo não existe no PC."""
    try:
        return _ler("ops/fila-publicacao.md")
    except FileNotFoundError:
        return ("(ops/fila-publicacao.md não encontrado neste diretório.\n"
                "Não inventar itens de fila.)")


@mcp.tool()
def catalogo() -> str:
    """Catálogo do produto (catalogo/produto-fita-cetim.md). Sem inventar conteúdo se o arquivo não existe no PC."""
    try:
        return _ler("catalogo/produto-fita-cetim.md")
    except FileNotFoundError:
        return ("(catalogo/produto-fita-cetim.md não encontrado neste diretório.\n"
                "Não inventar preços ou especificações.)")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
