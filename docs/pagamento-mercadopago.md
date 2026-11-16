# Pagamento via Mercado Pago — link de pagamento (RASCUNHO)

> **RASCUNHO — pesquisa + proposta, 2026-11-06.** Nada aqui foi aplicado:
> nada no pacote, na FAQ, no prompt do agente, na persona ou no
> Deskcomm; nenhum link, produto ou conta foi criado. O usuário
> decide primeiro.
>
> **BLOQUEIO:** o preço do Facebook ainda está **indeciso** — nenhum
> link real pode ser criado com valor até o preço ser decidido.
> Nenhum valor aparece neste documento.

## 0. Ponto de partida (decidido)

- Pagamento decidido até aqui: **Pix** (direto, chave Pix).
- O usuário **já tem conta no Mercado Pago**.
- Ideia do usuário (2026-11-06): oferecer um **link de pagamento**
  do Mercado Pago, com produtos criados lá, para pagamentos
  diversificados oferecidos pela plataforma (Pix, cartão, boleto).
- **Boleto FORA das formas de pagamento — DECIDIDO 2026-11-06 ~14:30:** só Pix e cartão (via link Mercado Pago). As menções a boleto neste documento são referência da plataforma Mercado Pago, não oferta da TuttiBom.
- O relógio da produção começa na **aprovação da prova +
  pagamento confirmado — o que ocorrer por último**
  (docs/prazos.md §2.0).

## 1. O que a pesquisa encontrou (com fontes)

### 1.1 Dois tipos de link — não são a mesma coisa

**Link individual por cobrança ("Cobrar com link")** — o padrão
para venda com preço fechado:

- Criado no app (Cobrar → Link de pagamento) ou no site
  (Cobranças/Receber → Link de pagamento).
- O vendedor define **valor, título/descrição do produto ou
  serviço, foto (opcional), meios de pagamento aceitos e data de
  expiração**. O link é único para aquela cobrança.
- O comprador abre o link, vê o valor e o nome da loja, escolhe
  como pagar. **Não precisa ter conta no Mercado Pago.**
- Se o comprador cancelar ou não concluir, o link continua ativo
  e pode ser usado de novo.
- Para produtos com preço fixo, é o mais seguro: o valor já vem
  definido e o cliente não digita nada errado.

**"Seu link" (link fixo personalizado)** — um endereço só para o
negócio:

- Endereço fixo, algo como
  `link.mercadopago.com.br/nomedoseunegocio`, definido uma única
  vez e compartilhado sempre que precisar cobrar.
- **Quem paga informa o valor.** Bom para negociação por mensagem
  com preço combinado na hora; ruim para preço fixo, porque o
  cliente pode digitar o valor errado.
- Para a TuttiBom, é alternativa, não padrão: o preço é fechado
  por pedido.

**"Produtos no Mercado Pago":** o fluxo de link **não tem um
catálogo de produtos como uma loja** — cada link é uma cobrança
com título, valor, foto e descrição. O equivalente prático a
"criar produtos" é criar **um link por produto/preço** (ex.: fita
15 mm × 10 m, fita 22 mm × 50 m) e reutilizá-lo enquanto o preço
valer, ou criar um link por pedido. Se o app tiver alguma forma
de catálogo salvo, é a confirmar na conta do usuário — não foi
afirmado aqui como recurso existente.

**Custos para criar:** nenhum. Não há mensalidade nem custo para
gerar ou enviar o link. Só se paga taxa por venda concluída.
Não precisa de maquininha nem de conta jurídica.

### 1.2 O que o comprador vê e como pode pagar

- Página de checkout do Mercado Pago com o valor, o nome da loja
  e a escolha do meio de pagamento.
- Meios aceitos no link: **cartão de crédito (todas as bandeiras,
  à vista ou parcelado em até 12x, inclusive dividir em dois
  cartões), Cartão de Débito Virtual CAIXA, saldo no Mercado
  Pago, linha de crédito, Pix, boleto à vista ou parcelado,
  dinheiro em casas lotéricas e PayPal**.
- O link pode ser enviado por **WhatsApp, e-mail, redes sociais**,
  ou fixado na bio do Instagram.
- Dica das fontes: **sempre configurar a data de expiração**
  quando a venda tem prazo — um link sem validade pode ser usado
  fora do contexto original.

### 1.3 Taxas do link de pagamento (referências de julho de 2026 — conferir no app)

| Meio de pagamento | Taxa | Recebimento |
|---|---|---|
| Pix | 0,99% | Na hora |
| Cartão de crédito à vista — na hora (D0) | 4,98% | Na hora |
| Cartão de crédito à vista — 14 dias (D14) | 4,49% | 14 dias |
| Cartão de crédito à vista — 30 dias (D30) | 3,99% | 30 dias |
| Parcelamento 2x | 4,59% | (conforme prazo escolhido) |
| Parcelamento 3x | 5,97% | (conforme prazo escolhido) |
| Parcelamento 4x | 7,22% | (conforme prazo escolhido) |
| Parcelamento 8x | 12,5% | (conforme prazo escolhido) |
| Parcelamento 12x | 17,28% | (conforme prazo escolhido) |
| Boleto | R$ 3,49 fixo | Até 3 dias úteis |
| Cartão de Débito Virtual CAIXA | 3,99% | Na hora |
| Saldo no Mercado Pago / linha de crédito | 4,99% | Na hora |

Atenção:

- As taxas **variam por conta e perfil** e mudam periodicamente.
  O valor exato aparece no app, no **Simulador de Taxas**, antes
  de fechar a venda — usar o simulador antes de criar o link.
- **DIVERGÊNCIA NAS FONTES (boleto):** a página oficial de FAQ
  do link cita boleto a **3,99%**, enquanto o blog do Mercado
  Pago e fontes secundárias citam **R$ 3,49 fixo**. Conferir no
  app antes de usar boleto.
- **Vendedores novos podem não ter "recebimento na hora"** logo
  que se cadastram — alguns recebem em 7 dias no início, e a
  opção na hora aparece depois de algumas vendas.
- O prazo de recebimento do cartão é **configurável no app**
  (Taxas e parcelas): na hora, 14 ou 30 dias — quanto menor o
  prazo, maior a taxa.
- **Pix direto (chave Pix, fora do Mercado Pago) não tem taxa de
  plataforma.** Pix **via link** custa 0,99%. A diferença é
  pequena, mas existe — é o custo de oferecer o link.

### 1.4 Prazos de recebimento

- **Pix:** instantâneo, 24/7 (inclusive fins de semana e
  feriados).
- **Cartão de crédito:** na hora, em 14 ou em 30 dias, conforme a
  escolha do vendedor no app.
- **Boleto:** 1 a 3 dias úteis após o pagamento, por compensação
  bancária. O valor só fica disponível depois da compensação
  confirmada.

### 1.5 Confirmação do pagamento

- O vendedor acompanha a **confirmação em tempo real no app**.
- Boleto: consultar o status no app antes de cancelar ou
  reembolsar — atraso acima de 3 dias úteis é sinal de alerta.
- Cartão: a venda é aprovada na hora; o dinheiro cai conforme o
  prazo escolhido (D0/D14/D30).

## 2. Proposta — fluxo para a TuttiBom

### 2.1 Opinião: vale a pena?

**Sim — como complemento do Pix, não como substituto.** O Pix
direto continua sendo o padrão (grátis, instantâneo). O link do
Mercado Pago resolve o caso do comprador que **não pode pagar
por Pix ou quer parcelar no cartão**. Sem o link,
esses compradores não têm como pagar — ou o usuário teria que
improvisar outra forma na hora. Com o link, o agente tem uma
resposta pronta, com valor fechado e confirmação no app.

O custo é a taxa: 0,99% no Pix via link, 4,98% no crédito à vista
na hora, mais no parcelamento. É o preço de aceitar cartão — e é descontado do valor recebido, não cobrado do
comprador à parte.

### 2.2 Qual formato usar

- **Padrão: link individual por pedido, com valor fixo.** Cada
  pedido tem valor fechado (produto + entrega, ou só o produto);
  o link carrega o valor exato, o nome do produto e a descrição;
  o comprador só escolhe como pagar. Evita erro de digitação e
  deixa claro o que está sendo pago.
- **"Seu link" (valor digitado pelo comprador): não usar como
  padrão.** Só faria sentido se o preço fosse combinado na hora,
  sem valor fechado — hoje não é o caso. Risco de o cliente
  digitar o valor errado.
- **Links por produto (reutilizáveis):** quando os preços forem
  decididos, o usuário pode criar um link por variação
  (ex.: fita 15 mm × 10 m; fita 22 mm × 50 m) e reutilizá-lo
  enquanto o preço valer. Para pedidos com entrega, o link do
  pedido é criado com o valor total (produto + entrega) — ver §4.

### 2.3 Quem cria, quando, como

- **Quem cria: o usuário, na própria conta Mercado Pago dele**
  (app ou site). O Muse não precisa de acesso à conta; o agente
  nunca cria link, nunca vê senha, código ou credencial.
- **Quando: só depois que o preço for decidido E o usuário
  aprovar o valor exato do pedido.** Sem preço aprovado, sem
  link — a mesma trava de sempre.
- **Validade:** configurar a validade do link conforme o prazo da
  venda (ex.: até a data do evento, ou poucos dias), para evitar
  pagamento fora do contexto.
- **O agente envia o link na conversa** (WhatsApp/Messenger) com
  o texto aprovado pelo usuário, dizendo o que o valor cobre e
  qual o meio preferido (Pix direto quando o comprador puder).

### 2.4 Confirmação e o relógio da produção

- O relógio começa na **aprovação da prova + pagamento
  confirmado — o que ocorrer por último** (docs/prazos.md §2.0).
- **Pix (direto ou via link):** confirmação instantânea — o
  relógio pode começar na hora.
- **Cartão:** a venda é **aprovada na hora** (o dinheiro pode cair
  depois, conforme D0/14/30). **DECIDIDO 2026-11-06 ~14:30:** a produção começa na
  **aprovação** do cartão, não no recebimento do dinheiro.
- **Boleto: SUPERADO — boleto fora das formas de pagamento (decidido 2026-11-06 ~14:30).** A regra abaixo fica só como referência da plataforma e não se aplica: NÃO iniciar a produção antes da compensação (1 a 3 dias úteis); o pagamento por boleto só está confirmado depois de compensado.
- O agente só confirma o recebimento quando o usuário (ou a
  notificação do app) confirmar. O agente nunca afirma pagamento
  sem confirmação.

### 2.5 Pix direto vs link — como coexistem

- **Pix direto (chave Pix): padrão, sem taxa.** Oferecer primeiro
  quando o comprador puder pagar por Pix.
- **Link Mercado Pago: alternativa diversificada.** Quando o
  comprador quer cartão (à vista ou parcelado) ou não
  consegue pagar por Pix. O comprador escolhe o meio dentro do
  link.
- **Taxa do cartão — DECIDIDO 2026-11-06: vai para o cliente.**
  No pagamento por cartão, há uma taxa equivalente, acrescida ao
  valor, e o comprador é informado disso antes de fechar. O
  recebimento é feito o mais breve possível (prazo de
  recebimento mais rápido — D0 — a confirmar no app).
- **Pix: a vantagem é não pagar essas taxas.** Isso é esclarecido
  ao comprador: no Pix não há taxa; no cartão, há.
- **Atenção à margem:** como a taxa vai para o cliente, o preço
  não precisa absorvê-la — mas o acréscimo e o limite de
  parcelamento precisam ser definidos (ver §4). Nunca inventar
  acréscimo ou limite.

### 2.6 Quem paga o entregador — DECIDIDO 2026-11-06

- **Quem chama o aplicativo paga a corrida.** Se a TuttiBom
  chama o motoqueiro (Uber/99), o comprador paga a taxa de
  envio **antecipadamente** — o vendedor não adianta o valor
  da corrida. Sem o pagamento da taxa, não há chamada do
  motorista.
- **O comprador pode chamar o aplicativo ele mesmo**, informando
  o endereço — aí ele paga a corrida direto no aplicativo.
- Isso é **combinado com o comprador antes de fechar**: ou ele
  chama o app, ou a gente entrega (chama o motoqueiro) com a
  taxa paga antecipadamente. A entrega vai no mesmo link ou é
  paga à parte — ver §4 (em aberto).

## 3. Guardrails (para o prompt do agente, quando aplicar)

1. **Nunca enviar link sem aprovação do usuário do valor exato.**
2. O valor do link tem que ser o **preço combinado**; se incluir
   a entrega, dizer isso; se não incluir, dizer que a entrega é
   à parte.
3. **Nunca inventar** preço, valor de link, taxa ou prazo de
   recebimento.
4. **Preferir Pix direto** quando o comprador puder pagar por Pix;
   oferecer o link como alternativa (cartão).
5. **Nunca afirmar que o pagamento foi recebido** sem confirmação
   (app/notificação do usuário).
6. **SUPERADO — boleto fora (decidido 2026-11-06 ~14:30):** a regra de nunca iniciar produção por boleto antes da compensação não se aplica mais, porque boleto não é forma de pagamento da TuttiBom.
7. Sempre dizer **o que o valor cobre** (produto, metragem, cor,
   entrega incluída ou não).
8. O agente **nunca cria link, nunca acessa a conta Mercado Pago,
   nunca pede senha ou código**.

## 4. O que só o usuário decide (não inventar)

- [ ] **Preços** — ainda em aberto. Bloqueia qualquer link real
  com valor.
- [ ] **Quais produtos/variações ganham link** (15/22 mm ×
  10/25/50 m; itens 3D).
- [ ] **A entrega vai no mesmo link ou é paga à parte?**
  (Se no mesmo link, o valor do link é produto + entrega; se à
  parte, o link é só o produto e a entrega segue por Pix direto
  ou outro meio.)
- [ ] **Quem cria os links e quando** — o usuário cria um link por
  pedido, ou links salvos por produto para reutilizar?
- [ ] **Preferir Pix direto sempre que possível?** (Proposta: sim.)
- [ ] **Parcelamento** — até quantas vezes? Taxa DECIDIDA: vai
  para o cliente (acréscimo ao valor, informado antes de
  fechar). Falta: o limite de parcelas.
- [ ] **Prazo de recebimento do cartão** — DECIDIDO 2026-11-06:
  o mais breve possível (D0 — a confirmar no app). Afeta a
  taxa: 4,98% / 4,49% / 3,99%.
- [x] **Produção começa na aprovação do cartão** — DECIDIDO 2026-11-06 ~14:30: na aprovação, não quando o dinheiro cai.
- [ ] **Validade padrão dos links** (ex.: até a data do evento,
  ou poucos dias).
- [x] **Boleto: aceitar?** — DECIDIDO 2026-11-06 ~14:30: NÃO. Boleto fora das formas de pagamento; só Pix e cartão (via link Mercado Pago).

## Fontes

- Mercado Pago — "Como receber pagamentos remotamente com Link de
  Pagamento do Mercado Pago":
  https://www.mercadopago.com.br/blog/receber-link-de-pagamento-mercado-pago
- Mercado Pago — "Venda pelas redes sociais com Link de pagamento":
  https://www.mercadopago.com.br/ferramentas-para-vender/link-de-pagamento?code=KTTAA
- Mercado Pago — "Prazo de recebimento do Link de Pagamento":
  https://www.mercadopago.com.br/blog/prazo-recebimento-link-de-pagamento
- Mercado Pago — "Links de pagamento: o que são, como funcionam":
  https://www.mercadopago.com.br/blog/links-pagamento-o-que-sao-vantagens
- Mercado Pago — "Seu link Mercado Pago: como criar e usar":
  https://www.mercadopago.com.br/blog/seu-link
- Mercado Pago — "Como gerar link de pagamento com Mercado Pago?":
  https://www.mercadopago.com.br/blog/gerar-link-pagamento-mercado-pago
- Mercado Pago — "Gere seu link de pagamento em poucos minutos":
  https://www.mercadopago.com.br/blog/criar-compartilhar-link-de-pagamento
- Mercado Pago — "Simulador de gastos do negócio":
  https://www.mercadopago.com.br/blog/simulador-e-gestao-de-custos
- Mercado Pago — "Como gerar links de pagamento":
  https://www.mercadopago.com.br/blog/como-gerar-link-de-pagamento
- Serasa — "Link de pagamento: como gerar e escolher a melhor opção":
  https://www.serasa.com.br/blog/link-pagamento/
- InfinitePay — "As 7 Melhores Plataformas de Pagamento Online (2026)"
  (taxas de referência, julho de 2026):
  http://infinitepay.io/blog/plataformas-de-pagamento-online
