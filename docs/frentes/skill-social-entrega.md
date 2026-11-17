# Entrega — Frente 3: Skill 5 (social)

**Data:** 2026-11-17 (America/Fortaleza)
**Workspace:** `/home/pc/Workspace/tuttibom-ops-skill-social`
**Branch:** `frente/skill-social`
**HEAD:** `cdd94975bf8f9048e4ec50bec0800615aa77ba6b` (lido em `.git/refs/heads/frente/skill-social`; é o mesmo hash de `main`)
**Base:** `main` `cdd9497`

A tentativa anterior nesta worktree parou porque a fonte não estava no PC. O coordenador localizou o clone em `/tmp/marketingskills-src`. Esta entrega substitui o relatório de bloqueio. Nada foi publicado, enviado ou commitado.

## Resultado

Skill vendida em `skills/tuttibom-facebook-social/`.

- `SKILL.md` é a cópia fiel do upstream (inglês, versão 2.5.2), sem edição.
- `TUTTIBOM.md` é a skill em uso, em PT-BR, para o Facebook da TuttiBom no Cariri. Em conflito, ele vence.
- `FONTE.md` registra origem, commit, licença e o que veio junto.
- `LICENSE` é a MIT do mesmo commit (Copyright (c) 2025 Corey Haines).

Commit conferido no clone: `1f837447b20bb6f0e72d87b80ece1c221c362c7d` (`/tmp/marketingskills-src/.git/refs/heads/main`).

O shell desta sessão foi recusado, então não houve `cmp` byte a byte. A cópia foi transcrita da fonte local. Os finais batem com a fonte: `SKILL.md` 460 linhas, `platforms.md` 213, `platform-limits.md` 111, `post-templates.md` 180, `short-form-video.md` 282. Amostras do meio (frontmatter, No AI Tells, “Publishing From Your Agent”) batem com o original.

## O que foi adaptado

No `TUTTIBOM.md`, só o que serve à Página:

| Peça da fonte | Como ficou |
|---|---|
| Pilares (3–5, com as cinco perguntas) | Cinco pilares da loja: processo, produto em uso, personalização, ocasião no Cariri, oferta. A grade de fundador de SaaS (30/25/25/15/5) não é a grade da TuttiBom. |
| Ganchos | Quatro famílias, com forma em PT-BR presa ao catálogo (15/22 mm, 10/25/50 m, hotstamp Preto/Dourado/Prata, 3–5 dias úteis). Prova social e isca ficaram de fora. |
| No AI Tells | Lista traduzida e em vigor. A skill `copywriting` do upstream não foi buscada. |
| Reaproveitamento | Uma peça da loja vira até 5 átomos para feed, story ou vídeo nativo, cada um reescrito. Blog, podcast, webinar e newsletter não são a fonte. Republicar pede aprovação nova. |
| Calendário | Grade só Facebook, 3 vagas, travada até o piloto. Até lá vale o ritmo já usado na skill de conteúdo: no máximo 3 posts por semana, dias alternados. |
| Revisão semanal | Top 3 e bottom 3 quando houver dado. Sem dado, diz que não há dado. Sem nome de quem comentou. |
| Vídeo curto | Regra dos 3 segundos, três estruturas e legenda de 2 linhas, para o vídeo nativo da Página. O 9:16 continua na skill de motion. |

Travas embutidas: aprovação do texto exato e da imagem exata; sem preço combinado no post; sem dado de comprador; Camofox como navegador único (D-004); S10/ADB pausado; regra de imagens de 2026-11-06 (real só com autorização para demonstrar; amostra personalizada é render fictício, com rótulo de prévia simulada); Pangram (D-007) antes da aprovação, sem substituí-la.

A diretriz antiga de mídia sempre fictícia não foi copiada. Também não foram copiados “S10 via ADB” nem o caminho de escrita dos moldes `skills/tuttibom-facebook-*`.

## O que ficou de fora e por quê

| Peça | Por quê |
|---|---|
| LinkedIn, X, Instagram, TikTok, Telegram, YouTube, Threads, Pinterest | Facebook primeiro. Outro canal só como extensão futura, com decisão do usuário. |
| `references/x-algorithm.md` | Só o X. |
| `references/ship-post.md` | Post de commit para X e Reddit. |
| `references/carousel-frameworks.md` | Carrossel de Instagram e LinkedIn, com isca de comentário. |
| `references/listening.md` e `listening-sources-template.md` | `curl` em Reddit, Hacker News e Bluesky, e comentário em contas alheias. |
| `references/reverse-engineering.md` | Coleta de 500+ posts para repetir formato alheio. |
| `evals/evals.json` | Casos de SaaS e de outras redes. |
| Rotina de 30 minutos, DMs, comentário em 5–10 contas | Ação em massa e dado de conversa. |
| Typefully, Buffer, Marky e qualquer MCP que agenda | A skill para no rascunho. Nada entra na conta sem o texto e a imagem exatos aprovados. |
| Aquecer conta, piso de views, várias contas, “postar em todo lugar” | Estão em `short-form-video.md`, que veio pela regra de vídeo. O `TUTTIBOM.md` manda não executar esses trechos. |
| Grupos e live | A fonte cita como formato que funciona. Não são a operação atual da Página. |
| Frequência de 1–2 posts por dia | Referência de página madura. Não substitui o teto de teste. |

Os links do `SKILL.md` para os arquivos não copiados ficam sem destino de propósito. `FONTE.md` manda não recriar o arquivo para consertar o link.

## Como usar

1. Abrir `skills/tuttibom-facebook-social/TUTTIBOM.md`. Ele manda a operação.
2. Escolher um pilar que caiba na vaga da semana (no teste: processo, produto em uso, ou pergunta/personalização).
3. Escrever o rascunho em PT-BR com um gancho de fato e um só pedido. Passar a lista de sinais de texto gerado.
4. Marcar a mídia: trabalho real já autorizado para demonstrar, ou render fictício com rótulo de prévia simulada.
5. Passar o texto público pelo Pangram e entregar o rascunho ao usuário. Publicar, enviar e combinar preço continuam fora da skill.

O `SKILL.md` fica para comparar com o upstream numa atualização. Não seguir a mistura de redes, o agendador nem a rotina de engajamento dele.

## Arquivos

Criados:

- `skills/tuttibom-facebook-social/SKILL.md`
- `skills/tuttibom-facebook-social/FONTE.md`
- `skills/tuttibom-facebook-social/TUTTIBOM.md`
- `skills/tuttibom-facebook-social/LICENSE`
- `skills/tuttibom-facebook-social/references/platforms.md`
- `skills/tuttibom-facebook-social/references/platform-limits.md`
- `skills/tuttibom-facebook-social/references/post-templates.md`
- `skills/tuttibom-facebook-social/references/short-form-video.md`

Alterado:

- `docs/frentes/skill-social-entrega.md` (este arquivo, no lugar da versão bloqueada)

Não foram editados `docs/ESTADO.md`, `docs/roadmap.md`, `docs/decisoes/`, `criativos/`, `ops/`, `src/`, `scripts/` nem `tests/`. Sem commit e sem push.
