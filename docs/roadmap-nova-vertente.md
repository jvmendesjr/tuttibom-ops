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

## Onde estamos (2026-11-21, 22:15)

| Peça | Status |
|---|---|
| D-012 + 8 setores (`docs/setores/`) | **feito** — commit `c6b1c1d`, branch `exp/setores-nova-vertente` |
| Skill da Ana (`skills/ana-atendimento/`) | **feita** — commit `c918ea0`, branch `exp/atendimento-ana` |
| CRM próprio mínimo (V2) | **feito** — commit `54f271c`, branch `exp/crm-proprio` |
| Laboratório (V3) | **feito** — commit `5b345d1`, 45/45 checagens |
| Teste real supervisionado (V4) | **FECHADO 2026-11-21 — veredito: PASSA** — relatório `docs/v4-teste-real-relatorio.md`, commit `ac8b851` |
| Chatwoot como inbox (D-013) | **no ar** — `https://chatwoot.petemcasa.com`, HTTPS + SMTP provados; atendimento ligado 22:12 com vigília `chatwoot-watch-ana` |
| Promoção para a `main` (V5) | **em andamento** — inbox promovido na prática; setores promovem um por vez |

## Worktrees e branches

| Worktree no PC | Branch | Contém |
|---|---|---|
| `tuttibom-ops-setores` | `exp/setores-nova-vertente` | D-012, 8 setores, este roadmap |
| `tuttibom-ops-atendimento` | `exp/atendimento-ana` | Skill da Ana (base: setores) |
| `tuttibom-ops-crm` | `exp/crm-proprio` | CRM mínimo, laboratório, teste real, Chatwoot (base: setores) |
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

### V2 — CRM próprio mínimo — FEITO 2026-11-21

- Modelo mínimo em `src/tuttibom/crm/` + `db/crm.sql` (o rascunho
  original dizia `db/schema.sql`; o schema efetivo é `db/crm.sql`),
  na worktree `exp/crm-proprio`: lead, conversa, etapa, produto,
  follow-up, memória por contato. SQLite local.
- Funil Vendas com 7 etapas, 18 SKUs com preço só do catálogo,
  follow-up com cancelar-ao-responder, memória por contato só com
  rótulo (nunca PII).
- Critério de saída: um lead vai de Novo contato a Pedido pago, e
  outro a Não comprou com motivo, sem pular etapa e sem perder
  registro; um contato que volta e diz "olá" é reconhecido pelo
  interesse anterior. **Cumprido** — 7/7 testes, demo 4/4, commit
  `54f271c`.
- Divergência registrada em `src/tuttibom/crm/README.md`: o
  vocabulário do funil Vendas não é o de `contratos/lead.py` do F4 —
  alinhar o F4 é decisão aberta.

### V3 — Laboratório (conversa simulada, ponta a ponta) — FEITO 2026-11-21

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
  **Cumprido** — `scripts/lab_v3.py` + `docs/lab-v3-relatorio.md`,
  **45/45 checagens**, commit `5b345d1`. Valida o fluxo, não a
  geração ao vivo do LLM.

### V4 — Teste real supervisionado — FECHADO 2026-11-21 — VEREDITO: PASSA

- Uma conversa real, com o usuário acompanhando, no canal onde a
  pessoa escreveu (Messenger, via Zernio → Deskcomm, IA pausada).
  Cliente de teste: Gleiciane, que pediu o preço da fita de 10 m com
  impressão dourada e não respondeu após o preço.
- Relatório completo: `docs/v4-teste-real-relatorio.md`, commit
  `ac8b851`. Mecânica provada ponta a ponta (transporte, leitura via
  MCP, 2 turnos da Ana pelo painel com o texto da skill, registro no
  CRM próprio) e comportamento da Ana provado (saudação fechada,
  preço só do catálogo, uma pergunta por turno, sem frete, sem
  endereço, sem desconto).
- **Fraqueza principal:** latência de 11 e 16 min por turno (meta
  1–2 min), estrutural do polling de 5 min + navegação no painel.
  O conserto é o Chatwoot por webhook — já provado (ida e volta nos
  dois canais, HTTPS, SMTP).
- Desfecho: lead fechado no CRM próprio como "Não comprou /
  sem_resposta" (cliente de teste, não perda comercial); vigília
  `v4-watch-gleiciane` e follow-up de 2026-11-22 removidos.
- Critério de saída: o turno real completa sem intervenção de
  emergência, com o lead registrado corretamente e a aprovação da
  imagem/texto exatos respeitada. Se falhar, volta para a V3 — não se
  "ajeita em produção". **Cumprido, com a latência registrada como
  correção da V5.**

### V5 — Promoção por setor — EM ANDAMENTO (2026-11-21)

- Um setor por vez, quando passar no seu teste: o documento dele
  substitui o equivalente do caminho Deskcomm, e o código dele é
  promovido para a `main` (merge da branch `exp/*`, com revisão).
- **O inbox já foi promovido na prática (D-013, 2026-11-21):** o
  Chatwoot é o inbox da nova vertente. Ana do Deskcomm pausada
  (WhatsApp em modo de teste desde 19:19, Messenger pausado desde
  16/11). Chatwoot em `https://chatwoot.petemcasa.com` (DNS + túnel,
  `FRONTEND_URL` atualizado, 21:57), SMTP via Gmail provado (e-mail
  de teste recebido 22:06), WhatsApp e Messenger com ida e volta
  provadas (21:34–21:53). Atendimento ligado 22:12: o Muse atende
  como Ana nos inboxes 1 e 2, com vigília `chatwoot-watch-ana` a
  cada 5 min (só leitura; a vigília nunca responde sozinha).
- **Configuração da Ana no Chatwoot (2026-11-21 ~23:00, detalhe em
  `docs/ana-chatwoot-configuracao.md`):** ouvinte `ana-listener`
  (porta 3021, webhook de conta id 1) + hook `chatwoot-ana-watch`
  (poll 60 s, acorda o atendimento na hora) + runner de follow-up
  (cron `chatwoot-followup-ana` a cada 2 h, só rascunhos) + handoff
  humano (etiqueta `handoff-humano`, agente `tutibom`). Código em
  `services/chatwoot-ana/`, 35/35 testes. Teste vivo com mensagem
  real ainda pendente; textos-modelo de follow-up aguardam aprovação
  do usuário. Regra nova: empresas conhecidas são ignoradas (lista
  em `services/chatwoot-ana/ignorados.json` — ex.: Mercado Livre;
  conversa 8 sem resposta, sem lead; resolve na prática a P8).
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
- [x] V2 — CRM próprio mínimo (`54f271c`)
- [x] V3 — Laboratório: conversa simulada ponta a ponta (`5b345d1`, 45/45)
- [x] V4 — Teste real supervisionado (`ac8b851`, veredito: PASSA)
- [ ] V5 — Promoção por setor (1, 2, 3 e 7 primeiro) — em andamento: inbox Chatwoot no ar, atendimento ligado e pacote ouvinte/follow-up/handoff implementado (teste vivo e aprovação dos textos pendentes)

## Decisões relacionadas

- D-012 (2026-11-21) — a decisão-mãe desta vertente.
- D-013 (2026-11-21) — migração para o Chatwoot como inbox da
  vertente + pausa da Ana viva; Chatwoot no ar em
  `https://chatwoot.petemcasa.com` (HTTPS + SMTP) e atendimento
  ligado 22:12.
- D-011 (2026-11-17) — atendimento no canal onde a pessoa escreveu.
- D-010 (2026-11-17) — todo fluxo tem sua skill canônica.
- D-004 (2026-11-16) — Camofox é o navegador único; S10/ADB pausado.
- D-002 (2026-11-09) — roteador por modelo descartado; permanece o
  roteamento da resposta.
