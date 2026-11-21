# Setor 6 — Anúncios, Aquisição e Concorrência

**Objetivo:** trazer gente nova para a conversa e saber onde estamos
no preço — sem gastar sem aprovação e sem copiar ninguém.

## Entra / Sai

- **Entra:** produto com preço e foto (setor 3), criativo (setor 4),
  verba aprovada, dúvida de preço de mercado.
- **Sai:** anúncio ou listagem no ar (ou o motivo de não estar), e o
  relatório do que foi visto no mercado — preço, formato e o que
  funciona, sem cópia.

## Faz

- Marketplace: anúncio, triagem e encaminhamento, com a fronteira de
  automação, a memória e o triângulo de preço da skill. Preço para o
  Facebook nunca é inventado — se não há preço decidido, não há anúncio.
- Anúncios pagos: só com verba e texto exato aprovados pelo usuário,
  um por vez, com ritmo humanizado e sem ações em massa. Qualquer
  alerta de suspeita de bot pausa tudo para reavaliar (regra D-004).
- Verificação de concorrência: preço público no Cariri e no nacional
  (ex.: Shopee), quem vende o quê, por quanto, em que formato. Seguir
  formatos que funcionam, com identidade própria — sem copiar texto,
  foto ou cliente. Referência conhecida: nacional 22 mm / 50 m
  R$ 109–140 contra TuttiBom R$ 71,90–88,90 na Shopee (2026-10-30);
  nenhum especialista local no Cariri com preço público.
- Registrar o que aprendeu: preço visto, data, fonte, e o que muda (ou
  não muda) no nosso preço — mudança de preço é decisão do usuário,
  não deste setor.

## Não faz

- Não gasta verba sem aprovação, não promete resultado de anúncio,
  não dispara em massa.
- Não copia texto, foto, cliente ou identidade de concorrente.
- Não responde comprador de anúncio como atendimento — encaminha para
  o setor 1 e registra no setor 2.
- Não usa CLI com cookies replayando GraphQL nem atalho fora do canal
  decidido para tocar a conta (a skill descartada pp-facebook-marketplace
  fica só como referência de desenho).

## Skill e diretório

- `skills/tuttibom-facebook-marketplace/`,
  `docs/pesquisa-concorrencia-preco.md`,
  `docs/pesquisa-produtos-chamativos.md`,
  `docs/pesquisa-publicacao-engajamento.md`.
- Verba, quando houver, é registrada fora do repo, com o usuário.

## Aprovações

- Verba, texto exato e imagem exata de cada anúncio, antes de ir ao ar.
- Qualquer mudança de preço sugerida pela concorrência.

## Como se mede que deu certo

- Anúncio simulado: verba aprovada, texto aprovado, publicado uma vez,
  sem ação em massa e sem alerta de plataforma.
- Pesquisa de concorrência: tabela com preço, fonte e data, sem cópia —
  e nenhuma decisão de preço tomada por este setor sozinho.

## Handoffs

- Interessado do anúncio → setor 1 (Atendimento) e setor 2 (CRM).
- Preço ou produto para anunciar → setor 3 (Produto e Catálogo).
- Criativo do anúncio → setor 4 (Criativos e Mídia).
- Conta, bloqueio ou alerta de bot → setor 8 (Plataforma) e pausa imediata.
