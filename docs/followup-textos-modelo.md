# Follow-up automático da Ana — textos-modelo APROVADOS

**Status:** APROVADO pelo usuário em 2026-11-21 23:02 — os 4 textos,
a cadência (12 h / 24 h / 40 h) e a convenção de contagem do teto
(`enviado` como registro oficial do toque).
**Data:** 2026-11-21 · **Vertente:** nova (D-013) · **Código:**
`services/chatwoot-ana/followup.py` + `templates_followup.json`
**O que o usuário aprovou (2026-11-21 23:02):** os 4 textos abaixo,
a cadência proposta e a convenção de contagem do teto. O envio segue
dependendo da revisão do rascunho pelo Muse, como Ana.

## Como funciona (resumo)

O runner (`followup.py`) roda por cron e só escreve **rascunhos** em
`/home/pc/chatwoot/ana-listener/followup-drafts/` — um arquivo JSON por
toque, com o texto pronto. Ele **nunca envia nada sozinho**. Quem envia
é o Muse, como Ana, depois de revisar o rascunho — e marca o follow-up
como `enviado` no CRM. Sem aprovação destes textos, o runner até roda,
mas os rascunhos que ele escreve já são estes textos-modelo: **a
aprovação aqui é pré-condição para o envio, não para o rascunho**.

## Os 4 textos-modelo (na íntegra)

### Silêncio pós-preço — toque 1

> Oi! Tudo bem? Você tinha perguntado sobre a fita personalizada. Quer
> me contar para qual ocasião é, que eu te ajudo a escolher a largura e
> a metragem?

### Silêncio pós-preço — toque 2

> Oi! Só passando para saber se você ainda está pensando na fita. Se
> quiser, me conta o que falta para decidir que eu te ajudo.

### Silêncio pós-preço — toque 3 (último)

> Oi! Vou deixar por aqui, tá? Se quiser retomar depois, é só me chamar
> por aqui. Fico à disposição!

### Pagamento — toque único

> Oi! Tudo bem? Só lembrando do seu pedido: quando você confirmar o
> pagamento, me avisa que eu já deixo tudo encaminhado com o produtor.
> Precisa de alguma coisa?

**Tom:** o da Ana (`skills/ana-atendimento/SKILL.md`) — frases curtas,
uma pergunta por vez, sem pressão, sem citar frete, sem prometer prazo,
sem dizer que é virtual. O toque 3 encerra sem insistir; o de pagamento
nunca afirma que o pagamento foi recebido.

## Cadência APROVADA (2026-11-21 23:02)

Medida a partir da última resposta da Ana (o preço, no caso do
silêncio). Os toques são agendados um de cada vez: o próximo só é
agendado depois que o anterior foi enviado — se a pessoa responder, a
cadeia para (cancelar-ao-responder).

| Toque | Quando | Observação |
|---|---|---|
| Silêncio 1 | 12 h de silêncio | |
| Silêncio 2 | 24 h de silêncio | |
| Silêncio 3 | 40 h de silêncio | Último — depois dele, nada mais |
| Pagamento 1 | quando o lead está em "Aguardando pagamento" e o combinado vence | Toque único |

Todos dentro de 2 dias — é o teto já decidido (máx. 3 toques em 2 dias
para quem pediu preço e sumiu).

## Regras de segurança (já no código)

- **Nunca envia sozinho.** O runner só escreve o rascunho JSON
  (`{lead_ref, conversation_id, inbox_id, tipo, toque_numero, texto,
  agendado_para, gerado_em}`) e imprime uma linha de resumo.
- **Teto de 3 toques em 2 dias por lead e tipo.** Contam os follow-ups
  já `enviado` e os rascunhos já escritos nas últimas 48 h. Pagamento
  tem 1 toque só. Acima do teto, não gera rascunho.
- **Cancelar-ao-responder.** Se houver qualquer mensagem inbound depois
  do agendamento, o follow-up é marcado `cancelado` no CRM e não gera
  rascunho. O runner também só gera rascunho se a última mensagem da
  conversa for outgoing da Ana (silêncio real, verificado na API).
- **Leads fechados nunca recebem toque** ("Pedido pago", "Não comprou").
- **Contatos ignorados nunca recebem toque.** A lista é
  `services/chatwoot-ana/ignorados.json` (ex.: Mercado Livre
  <TELEFONE_SINTETICO>, conversa 8 do Chatwoot — P8). O runner pula em
  silêncio: sem rascunho, sem log.
- **Um rascunho por follow-up.** Se o arquivo já existe, o runner não
  gera outro — o rascunho aguarda decisão humana.
- **Sem conversa aberta, sem rascunho.** O toque precisa de uma
  conversa aberta no Chatwoot para ser enviado depois.
- **Sem dados de comprador no repo.** Nos testes, contatos e textos são
  fictícios; os rascunhos guardam só a referência opaca do lead, ids e
  o texto-modelo.

## Convenção de contagem do teto — CONFIRMADA (2026-11-21 23:02)

O teto de toques conta os follow-ups marcados `enviado` no CRM — esse
é o registro oficial do toque. As mensagens outbound registradas no CRM
são resumos e **não** são contadas, para não contar o mesmo toque duas
vezes. Consequência: quem enviar o rascunho precisa marcar o follow-up
como `enviado` logo após enviar (método `CRM.marcar_followup`).

## Cron CRIADO (2026-11-21 ~23:00, pelo coordenador)

Runtime, id `chatwoot-followup-ana`, a cada 2 h, dono
`goal:crm-pr-prio-e-atendimento-pelo-muse`, entrega neste chat. O
corpo é a instrução do agente (rodar o runner via ssh e entregar os
rascunhos novos para revisão e envio) — não é crontab de sistema.
Primeira rodada ~23:38. Textos e cadência aprovados em 2026-11-21
23:02 — o envio passa a valer, sempre com revisão do rascunho pelo
Muse, como Ana, antes de enviar. O log de cada rodada fica
no histórico do cron; rascunhos, em
`/home/pc/chatwoot/ana-listener/followup-drafts/` (fora do git).

## Verificação feita (2026-11-21)

- Testes unitários (`services/chatwoot-ana/test_followup.py`): 10
  testes, todos passando — followup vencido gera rascunho; inbound
  após agendamento cancela; 3º toque é o último; 4º não gera; lead
  fechado não gera; contato ignorado (<TELEFONE_SINTETICO>) não gera;
  pagamento tem 1 toque só; rascunho existente não duplica.
- Runner rodado contra o CRM de teste da V4 (`/tmp/crm-v4.sqlite3`) e
  a API real só em leitura: `sem-rascunhos` (o lead da V4 está fechado
  como "Não comprou"), sem tocar em nada.
- Caminho completo verificado contra a API real com CRM de rascunho em
  `/tmp`: rascunho gerado para conversa aberta cuja última mensagem é
  outgoing da Ana; conversa 8 (Mercado Livre, ignorada) sem rascunho.

## Decisões do usuário — RESOLVIDO (2026-11-21 23:02)

1. Os 4 textos-modelo acima — **aprovados**.
2. A cadência proposta (12 h / 24 h / 40 h) — **aprovada**.
3. A convenção de contagem do teto (follow-up `enviado` como
   registro oficial do toque) — **confirmada**.
