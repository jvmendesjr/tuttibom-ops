# Setor 7 — Operação, Produção e Pagamento

**Objetivo:** o pedido sair certo, chegar no prazo combinado e ser pago
do jeito combinado — sem a Ana prometer o que só o produtor confirma.

## Entra / Sai

- **Entra:** pedido fechado (setor 2), com produto, personalização,
  endereço e forma de pagamento combinados.
- **Sai:** produção iniciada no momento certo, entrega ou retirada
  combinada, pagamento confirmado — e o registro disso no CRM.

## Faz

- Produção: o produtor é o José, quem faz as fitas. Prazo de 3–5 dias
  úteis, contados a partir da prévia aprovada + pagamento confirmado.
  Para cartão, a produção começa na APROVAÇÃO, não quando o dinheiro cai.
- Pagamento: Pix é o padrão; cartão via link Mercado Pago do usuário,
  com as taxas para o comprador; sem adiantamento. Boleto fora — a Ana
  não oferece boleto. Pagamentos confirmados pelo usuário inicialmente.
- Entrega local (Crato / Juazeiro do Norte / Barbalha): motofrete por
  Uber/99, taxa confirmada no app pelo produtor, paga ANTES pelo
  comprador quando a TuttiBom chama o motoboy. A tabela de frete está
  em construção, completada a cada pedido com o valor exato confirmado
  no app — revisão prevista para ~2026-12-06.
- Retirada no Crato, sem taxa: Av. Pedro Gonçalves Norões 280,
  Grangeiro. O endereço só é informado após a compra fechada E o
  pagamento confirmado pelo produtor (setor 1 aplica a regra na conversa).
- Correios só como exceção, com intervenção humana — não é cotação de
  Uber/99.
- Pós-venda de pedido que não chegou: abrir um caso e passar para uma
  pessoa; dizer ao cliente que não há rastreio e que uma pessoa da
  equipe vai verificar. Não tentar resolver pedindo os dados do pedido.

## Não faz

- Não cita valor de frete ao cliente antes de o produtor confirmar —
  nem a Ana (setor 1), nem este setor por conta própria.
- Não informa endereço antes de pago e fechado.
- Não dá desconto nem muda preço — preço é do setor 3, desconto é
  negado pela regra do setor 1.
- Não oferece amostra física: quando surgir, é handoff humano e
  aprendizado registrado (setor 1).

## Skill e diretório

- `docs/prazos.md`, `docs/entrega-uber99.md`,
  `docs/pagamento-mercadopago.md`, `docs/regras-amostra-fita.md`,
  `catalogo/produto-fita-cetim.md` (prazos e produção).
- O produtor confirma frete, cor e prazo no app e na produção; o Muse
  registra, não confirma por ele.

## Aprovações

- Qualquer exceção — Correios, urgência, endereço informado antes da
  hora, amostra física — passa pelo usuário (e, quando for o caso,
  pelo produtor).
- Pagamento confirmado é sempre confirmado pelo usuário/produtor,
  nunca assumido pelo agente.

## Como se mede que deu certo

- Pedido simulado: prévia aprovada + pagamento confirmado → produção
  no prazo certo, entrega com taxa confirmada no app, retirada só
  após pago e fechado.
- Nenhum valor de frete citado, nenhum endereço informado antes da hora.

## Handoffs

- Cliente perguntando frete, prazo ou pagamento → setor 1 (Atendimento)
  pede os dados e registra; setor 7 confirma com o produtor.
- Pagamento confirmado → setor 2 (CRM) move para Pedido pago.
- Pedido que não chegou → setor 1 escala para humano, setor 2 abre o caso.
- Falta de produto ou cor → setor 3 (Produto e Catálogo).
