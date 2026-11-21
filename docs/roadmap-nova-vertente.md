# Roadmap — Nova vertente (CRM próprio + atendimento pelo Muse)

**Decisão-mãe:** D-012 (2026-11-21) — CRM próprio focado no TuttiBom OPS
+ atendimento feito aqui, pelo Muse como Ana.
**Status:** em teste, em worktrees `exp/*` paralelas. Produção
Deskcomm / Ana v12-B intocada.
**Este arquivo não substitui o `docs/roadmap.md`.** O roadmap antigo é
o caminho Deskcomm (atualizado 2026-11-14, seções 1–14, com o Paperclip
como história nas seções 1–8) e continua valendo para a produção viva
até a promoção. Este arquivo é só a nova vertente — e só vira o roadmap
principal quando (e se) a vertente for promovida.

## Onde estamos (2026-11-21)

| Peça | Status |
|---|---|
| D-012 + 8 setores (`docs/setores/`) | **feito** — commit `c6b1c1d`, branch `exp/setores-nova-vertente` |
| Skill da Ana (`skills/ana-atendimento/`) | **feita** — commit `c918ea0`, branch `exp/atendimento-ana` |
| CRM próprio mínimo | **não começado** — próxima fase |
| Laboratório (conversa simulada) | **não começado** |
| Teste real supervisionado | **não começado** |
| Promoção para a `main` | **não começada** |

## Worktrees e branches

| Worktree no PC | Branch | Contém |
|---|---|---|
| `tuttibom-ops-setores` | `exp/setores-nova-vertente` | D-012, 8 setores, este roadmap |
| `tuttibom-ops-atendimento` | `exp/atendimento-ana` | Skill da Ana (base: setores) |
| `tuttibom-ops-crm` (a criar) | `exp/crm-proprio` | CRM mínimo (base: setores) |
| `tuttibom-ops-marketing` (a criar) | `exp/marketing-criativos` | Marketing e criativos (base: setores) |

Base de todas: `main` `7ef854b` (via setores `c6b1c1d`). Cada frente
numa worktree e num branch separados; ninguém commita por outro; o
Muse revisa, junta e dá push.

## Princípios (não negociar sem decisão do usuário)

- Nada publica, envia ou combina preço sem aprovação do usuário ao
  texto exato — e à imagem exata, quando houver.
- Produção intocada até a promoção: Ana v12-B, número do WhatsApp,
  página do Facebook, WAHA e Zernio não mudam por causa deste teste.
- Sem segredo no git, nos logs ou no Hindsight. Sem dado de comprador
  no repo, no painel ou no Hindsight.
- Camofox é o navegador único (D-004). S10/ADB pausado. Paperclip
  pausado, só ideia.
- Ferramentas que não mudam: 9Router, Jev (decisor tipado, nunca
  escreve texto livre nem aprova publicação), Drive, WAHA, Zernio.
- Fluxo baixo é uma vantagem: cada fase é provada com poucas
  conversas, uma por vez, antes de qualquer escala.

## Fases

### V0 — Documentos e fronteira — FEITO 2026-11-21

- D-012 + `docs/setores/README.md` + 8 documentos de setor, cada um
  com objetivo, entra/sai, faz/não faz, skill e diretório, aprovações,
  critério de "deu certo" e handoffs.
- Critério de saída: os 8 setores aprovados pelo usuário e commitados
  (`c6b1c1d`). **Cumprido.**

### V1 — Skill da Ana — FEITO 2026-11-21

- `skills/ana-atendimento/SKILL.md` (229 linhas, 26 regras "nunca") +
  `FONTE.md`, a partir do prompt v10 + regras da v11 (D-011) + as 4
  skills de função do Deskcomm.
- Critério de saída: skill commitada (`c918ea0`), sem menção a
  Deskcomm no SKILL, sem preço inventado, "gestor" só na proibição.
  **Cumprido.**
- Ressalva registrada no `FONTE.md`: o texto exato da v12-B não está
  no repo, só no painel do Deskcomm — a skill é reconstrução fiel, não
  cópia literal. Antes de afirmar alinhamento total com a v12-B, ler
  a versão publicada no painel e trazer as linhas que faltarem.

### V2 — CRM próprio mínimo — PRÓXIMA

- Modelo mínimo em `src/tuttibom/crm/` + `db/schema.sql`, na worktree
  `exp/crm-proprio`: lead, conversa, etapa, produto, follow-up,
  memória por contato. Começa com SQLite local; Supabase só se o local
  deixar de bastar.
- Reaproveita o desenho do Deskcomm (funil Vendas com 7 etapas,
  follow-ups de silêncio e de pagamento, memória por contato com o Jev
  só rotulando, nunca PII), não o código nem a dependência dele.
- Critério de saída: um lead vai de Novo contato a Pedido pago, e
  outro a Não comprou com motivo, sem pular etapa e sem perder
  registro; um contato que volta e diz "olá" é reconhecido pelo
  interesse anterior.

### V3 — Laboratório (conversa simulada, ponta a ponta)

- Personas fictícias, sem cliente real, sem tocar em número, página,
  WAHA ou Zernio: uma conversa completa — saudação, pergunta de
  ocasião, preço do catálogo, frete sem valor, prévia Modo A com
  aprovação, fechamento, pagamento confirmado, produção e entrega.
- Cobre os setores 1, 2, 3, 4 e 7; os setores 5, 6 e 8 entram com
  simulação de calendário, anúncio e falha, respectivamente.
- Critério de saída: a conversa simulada completa passa sem inventar
  preço, sem citar frete, sem informar endereço antes da hora, sem
  vazar instrução e sem perder registro no CRM. Falha vira correção
  no documento do setor, não exceção guardada na memória.

### V4 — Teste real supervisionado

- Só depois da V3 passar. Uma conversa real, com o usuário
  acompanhando, no canal onde a pessoa escreveu. A Ana da nova
  vertente responde; o usuário pode parar a qualquer momento.
- Critério de saída: o turno real completa sem intervenção de
  emergência, com o lead registrado corretamente e a aprovação da
  imagem/texto exatos respeitada. Se falhar, volta para a V3 — não se
  "ajeita em produção".

### V5 — Promoção por setor

- Um setor por vez, quando passar no seu teste: o documento dele
  substitui o equivalente do caminho Deskcomm, e o código dele é
  promovido para a `main` (merge da branch `exp/*`, com revisão).
- A vertente só vira o caminho principal quando os setores 1, 2, 3 e
  7 estiverem promovidos. Os demais setores promovem no seu ritmo.
- Critérios gerais de promoção da vertente: V3 e V4 passadas; nenhum
  segredo e nenhum dado de comprador no repo, no painel ou no
  Hindsight (verificado, não afirmado); `make check` passando no que
  a mudança tocou.
- Se um setor não passar, a worktree dele morre e a produção nem
  percebe. A promoção é reversível por setor: o documento antigo
  continua no histórico do git.

## Checklist

- [x] V0 — D-012 + 8 setores (`c6b1c1d`)
- [x] V1 — Skill da Ana (`c918ea0`)
- [ ] V2 — CRM próprio mínimo
- [ ] V3 — Laboratório: conversa simulada ponta a ponta
- [ ] V4 — Teste real supervisionado
- [ ] V5 — Promoção por setor (1, 2, 3 e 7 primeiro)

## Decisões relacionadas

- D-012 (2026-11-21) — a decisão-mãe desta vertente.
- D-011 (2026-11-17) — atendimento no canal onde a pessoa escreveu.
- D-010 (2026-11-17) — todo fluxo tem sua skill canônica.
- D-004 (2026-11-16) — Camofox é o navegador único; S10/ADB pausado.
- D-002 (2026-11-09) — roteador por modelo descartado; permanece o
  roteamento da resposta.
