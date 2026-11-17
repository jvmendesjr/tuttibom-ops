# Fonte — skill `social` (Corey Haines)

## Origem

- **Repositório:** `coreyhaines31/marketingskills` — https://github.com/coreyhaines31/marketingskills
- **Branch:** `main`
- **Commit copiado:** `1f837447b20bb6f0e72d87b80ece1c221c362c7d` (conferido em 2026-11-17 no clone local `/tmp/marketingskills-src`, arquivo `.git/refs/heads/main`)
- **Skill:** `skills/social/` — nome `social`, versão `2.5.2`
- **Licença:** MIT. Copyright (c) 2025 Corey Haines. O arquivo `LICENSE` deste diretório é a cópia do `LICENSE` desse commit.
- **Copiado em:** 2026-11-17 (America/Fortaleza), nesta worktree `frente/skill-social`
- **Cópia local da fonte, só leitura:** `/tmp/marketingskills-src/skills/social/`

O `SKILL.md` deste diretório é a cópia fiel do upstream. Não editar. Os ajustes da TuttiBom estão em `TUTTIBOM.md`.

## Como ler

Ler `TUTTIBOM.md` antes do `SKILL.md`. O `TUTTIBOM.md` é a skill em uso, em PT-BR. Onde os dois divergirem, vale o `TUTTIBOM.md`.

## O que veio junto

Cópias fiéis, não editadas, porque a adaptação usa o trecho indicado:

| Arquivo | Por que veio |
|---|---|
| `SKILL.md` | Corpo da skill, versão 2.5.2 |
| `LICENSE` | Aviso de copyright exigido pela MIT |
| `references/platforms.md` | Seção Facebook (comunidade local, vídeo nativo, conteúdo local, sem link externo) |
| `references/platform-limits.md` | Limites do Facebook: hashtag, tamanho, nota de alcance |
| `references/post-templates.md` | Fórmulas de gancho além das que já estão no `SKILL.md` |
| `references/short-form-video.md` | Gancho de 3 segundos, estruturas e legenda de vídeo curto. A adaptação usa só isso |

O `SKILL.md` upstream também aponta para arquivos que não foram copiados. O link relativo fica sem destino de propósito. Não recriar o arquivo para “consertar” o link e não seguir o link.

## O que não veio

| Arquivo na fonte | Por que ficou de fora |
|---|---|
| `references/x-algorithm.md` | Só o feed For You do X. A loja opera no Facebook. |
| `references/ship-post.md` | Post de commit para X e Reddit. A TuttiBom não publica o log do git. |
| `references/carousel-frameworks.md` | Carrossel de Instagram e documento de LinkedIn, com isca de comentário. Não é o formato da Página. |
| `references/listening.md` | Triagem diária com `curl` em Reddit, Hacker News e Bluesky, e comentário em contas alheias. |
| `references/listening-sources-template.md` | Modelo desse listening. Só serve ao arquivo acima. |
| `references/reverse-engineering.md` | Coleta de 500+ posts de terceiros para copiar o formato. |
| `evals/evals.json` | Casos de teste do upstream (LinkedIn, X, SaaS, fundador). Não são tarefas da loja. |

## Como atualizar

1. Escolher o commit novo e reler o diff do `SKILL.md` e das referências que estão nesta pasta.
2. Substituir só a cópia fiel. Exemplo, com o commit travado (trocar o hash quando houver decisão de atualizar):

```
curl -sL "https://raw.githubusercontent.com/coreyhaines31/marketingskills/1f837447b20bb6f0e72d87b80ece1c221c362c7d/skills/social/SKILL.md" -o skills/tuttibom-facebook-social/SKILL.md
```

3. Atualizar o hash e a data neste arquivo. Não sobrescrever `TUTTIBOM.md` nesse passo: ele é nosso. Se o trecho que a adaptação usa mudou, a revisão do `TUTTIBOM.md` é decisão separada.
4. Não passar a copiar, na atualização, os arquivos da tabela “o que não veio”, a menos que uma decisão nova diga que passaram a servir ao Facebook da loja.

## Por que copiar (e não symlink)

Padrão do projeto (2026-11-09): a skill entra em `skills/` por cópia, com origem, commit, data e licença. Symlink para um clone em `/tmp` ou para a pasta de outro agente quebra fora deste PC e não trava a versão.
