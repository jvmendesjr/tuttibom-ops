# Fonte — skill `typesafe-ai` (oficial do Jev)

## Origem
- **Repositório oficial:** `typesafe-ai/skills` — https://github.com/typesafe-ai/skills
- **Skill:** `skills/typesafe-ai/SKILL.md` (nome `typesafe-ai`)
- **Licença:** MIT (arquivo `LICENSE` copiado junto)
- **Commit copiado:** `302eea662c54bca6730873fe245bec1d69ebc23d` (HEAD em 2026-11-10, repo com 3 commits)
- **Copiado em:** 2026-11-09/10, por Muse, a pedido do usuário
- **Arquivo original:** `SKILL.md` neste diretório — **não editar**. Ele é a cópia
  fiel do upstream. Os ajustes específicos da nossa aplicação estão em
  `TUTTIBOM.md`, separados, para o original continuar atualizável.

## Como atualizar
Re-baixar o `SKILL.md` do upstream e substituir este arquivo, conferindo o diff:
```
curl -sL "https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md" -o skills/typesafe-ai/SKILL.md
```
Depois atualizar o "Commit copiado" acima com o novo HEAD e a data. Não mexer
em `TUTTIBOM.md` na atualização — ele é nosso e não vem do upstream.

## Por que copiar (e não symlink)
Padrão do projeto (decisão do usuário 2026-11-09): skills usadas pelo projeto
são copiadas (vendoring) para dentro de `skills/`, com nota de origem e versão.
Um symlink para `~/.hermes/skills` ou `~/.claude/skills` só resolve no PC,
quebra na VM e no GitHub, e não trava a versão (o upstream mudaria por baixo
sem revisão). As skills do Hermes ficam com o Hermes — não são copiadas nem
tocadas aqui.
