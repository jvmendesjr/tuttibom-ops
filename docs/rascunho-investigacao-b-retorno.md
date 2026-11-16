# Rascunho — Investigação B: o retorno (Fluxo A) ler o histórico antes de mandar

_Rascunho preparado em 2026-11-13 ~16:35 -03; investigação concluída em
2026-11-13 ~19:50 -03 (Muse direto, regra de delegação 2026-11-13). Nada
aplicado — espera a decisão do usuário. Quando aprovado, o Muse implementa
direto._

## Por que agora

- O usuário perguntou em 2026-11-13 19:03 UTC qual seria a próxima etapa,
  com a parte do ack de áudio encerrada; a sugestão foi a investigação B.
- O que mudou desde o desenho de 11/11: a memória por contato está
  deployada e o roteador está ligado — a B tem um mecanismo que não
  existia quando a opção B foi desenhada.
- O que continua valendo: o ajuste A (texto genérico) já está no ar e a
  inscrição da pessoa das letras foi cancelada — o dano agudo (afirmar o
  produto errado 3×) está parado. O que falta é o retorno retomar o
  produto certo, em vez de ser genérico.

## O que a investigação verificou (código + banco de produção)

### 1. O Fluxo A hoje (verificado no banco, 2026-11-13 ~19:47)

Pointer `ab4a85af-d539-4129-b9a5-245b7f4eb08f`, ativo, versão
`1df069fe` (2026-11-11 23:06), gatilho silêncio 1440 min,
`cancel_on_reply: true`. Nós: trigger → action-2 "Mensagem 1" (texto
fixo genérico) → match_reply-1 ("Casar resposta", ramo `sim`) → wait-3
(3 dias) → action-4 "Mensagem 2" (texto fixo genérico) → end
(exhausted). **Não há nó `ai_classify` nem nó `condition` no Fluxo A.**

Inscrições: 3 ativas, 2 concluídas, 73 canceladas. As 3 ativas já estão
no nó `wait-3` — já receberam a msg1 genérica. Nenhuma das 3 tem sinal
de produto na última inbound (uma saudação "Oi", um pitch de
dropshipping de fornecedor, uma notificação do Mercado Pago). **Não há
caso de prova vivo para o retorno personalizado.**

### 2. O caminho "histórico direto" não existe — e o desenho original entendia errado

- O passo **"Classificar (IA)"** classifica a RESPOSTA do cliente ao
  follow-up (em qual saída do fluxo ela se encaixa), não o texto do
  retorno antes de mandar. Não há passo que leia o histórico antes de
  ENVIAR.
- A tarefa Jev **`followup`** (`lib/ai/decisao/followup.ts`,
  `lib/ai/decisao/tarefas.ts`) só recebe o que o cliente DIGITOU na
  resposta (sem mídia, sem transcrição), **só observa** (`soObserva`)
  por desenho — "a classe move o cliente no fluxo, e deixar o Jev
  movê-lo espera a concordância medida com respostas de verdade" — e só
  roda onde algum follow-up TEM o passo de classificar. O Fluxo A não
  tem → a tarefa nunca rodou para ele.
- O modo **`ai_message`** (o modelo escreve o retorno, com
  `prompt_hint`) existe, mas o texto seria gerado pelo modelo — viola a
  regra do usuário (nada enviado sem aprovação do texto exato). Fora.

### 3. O que o envio fixo JÁ sabe (verificado no código)

- `fixed_body` é interpolado no enfileiramento com o contexto completo
  do contato + negócio (`{{contact.*}}`, `{{lead.*}}` —
  `interpolarVolta` em `lib/followup/engine.ts`, `contextoDoContato` em
  `lib/automation/texto-do-followup.ts`). Mas não há campo de produto
  no negócio para interpolar — e interpolar `{{lead.tags}}` mandaria o
  código cru ao cliente.
- O motor de fluxos **ramifica por etiqueta**: a condição `tag`
  (`evaluateCheck`, `lib/followup/node-handlers.ts`) é igualdade exata
  contra `crm_leads.tags` — `eq`/`contains` viram "está entre as tags".
  As condições são revalidadas imediatamente antes do envio
  (`condicao-antes-do-envio.ts`, campos reavaliados: `lead_stage`,
  `tag`) — o ramo usa o dado fresco, não o da inscrição.
- A etiqueta de produto existe e é determinística
  (`lib/leads/etiqueta-do-produto-apresentado.ts`): o produto APRESENTADO
  vira etiqueta do negócio (o próprio código, em minúsculas, ex.
  `fita-22-50-preto`), gravada quando a Ana envia a mensagem do produto
  (`etiqueta-apos-envio.ts`). O doc dela diz o motivo: "o fluxo de
  acompanhamento escolhe o modelo aprovado pela etiqueta do NEGÓCIO".
- **Mas: zero etiquetas hoje.** Nenhum lead da tutibom tem etiqueta —
  nenhuma apresentação de produto com código aconteceu ainda. E a
  memória (`contact_interests`) NÃO é lida pelo motor de fluxos
  (`loadLeadFacts` / `contextoDoContato` / `dadosParaVariaveis` não a
  leem) e só teria dado após conversa resolvida + lote noturno — zero
  conversas resolvidas até hoje.

## Desenho recomendado (determinístico, sem LLM, sem inferência nova)

O retorno retoma o produto APRESENTADO (fato determinístico), não um
palpite lido do histórico. Duas partes:

### A. Etiqueta de família (código, pequeno)

Quando um produto é apresentado, gravar ALÉM do código a etiqueta da
família (`fita` / `3d`). Motivo: a condição de etiqueta é igualdade
exata, então um ramo por família precisaria de uma condição por
variante (18 só para fita) — frágil; a família deixa uma condição por
família. A família sai do prefixo do código (`FITA-…` → `fita`).
Aproveita as mesmas garantias da etiqueta de código (sem duplicar,
teto de 20, um só negócio aberto). Efeito colateral bom: a derivação
da memória (`familiaDoRotulo`) casa `fita` direto.

Hoje só existiria `fita` (os 18 produtos do catálogo são fita; não há
produto 3D catalogado). O ramo `3d` entra quando houver produto 3D no
catálogo — o desenho já prevê o lugar.

### B. Nova versão do Fluxo A (edição do fluxo, sem código)

Nó `condition` logo após o gatilho, antes da Mensagem 1:

- etiqueta `fita` → **Mensagem 1-fita** (texto fixo, a aprovar):
  "Oi! Ficou alguma dúvida sobre a fita? Se quiser, me conta o que
  você está buscando que eu te ajudo."
- senão → **Mensagem 1 genérica** (texto atual, sem mudança).

O resto do fluxo não muda (match_reply, espera 3 dias, Mensagem 2,
fim). Cada texto é fixo e aprovado exatamente pelo usuário, como a
regra exige. Publicar a nova versão é clique do usuário; inscrições
ativas ficam na versão antiga (estão pinadas nela).

### Prova

Depois de (A) deployado + um produto apresentado a um contato (etiqueta
gravada) + 24 h de silêncio: nova inscrição recebe a Mensagem 1-fita.
Sem apresentação, nada muda (genérica para todos) — o cold start é
honesto: hoje não há dado para ramificar.

### O que isto NÃO faz

Não lê as últimas mensagens nem a transcrição. Um contato cujo
interesse só foi falado (áudio, sem produto apresentado) continua
recebendo a genérica — que é o comportamento seguro. O caso das letras
de MDF (sem produto apresentado) ficaria corretamente na genérica.

## Decisão que falta do usuário

1. Aprovar o desenho (etiqueta de família + nova versão do Fluxo A com
   os dois textos)?
2. Aprovar o texto exato da Mensagem 1-fita acima (ou ditar outro)?
3. Com o desenho aprovado, o Muse implementa (A) e prepara a nova
   versão do fluxo para o usuário publicar — sem commit nem deploy sem
   aprovação separada, como sempre.

## Achado ao preparar a parte B (2026-11-13 ~20:00 — NÃO sobrescrito)

Ao gravar o rascunho da nova versão, a guarda parou: o pointer JÁ TEM
um `draft_graph`, e ele NÃO é cópia do ar — é um rascunho do usuário (ou
de alguém no painel) com as DUAS mensagens reescritas para fita:

- Mensagem 1: "Oi! Ficou alguma dúvida sobre a fita? Se quiser, me diz
  a largura e a metragem que você está pensando e eu já deixo tudo
  anotado. Sem pressa."
- Mensagem 2: "Oi, passando só para saber se você ainda quer a fita
  personalizada. Se preferir, me diz o que ficou faltando para decidir.
  Se não for agora, sem problema — é só me chamar quando quiser."

Diferença para o desenho acima: o rascunho dele NÃO tem ramo — o fluxo
inteiro vira fita para todo mundo que cair nele (inclusive quem não
pediu fita). O desenho com condição mantém a genérica para quem não tem
a etiqueta. O grafo novo validado (estrutura + publish, ok) está em
`/tmp/fluxo-a-novo.json` no PC, NÃO gravado — a decisão é do usuário:
manter os textos dele como ramo-fita (e acrescentar a genérica no outro
ramo), publicar o rascunho dele como está, ou trocar pelo desenho
proposto.

## Desfecho da parte A — commit + deploy (2026-11-13 ~20:56)

- Commit `c1d7efbc2` — `feat(agent): etiqueta de família do produto
  apresentado (Investigação B)` (3 arquivos, +189/−17). Deployado
  junto com o fix do ack/decidindo (`de96f0520`) no mesmo `up -d`;
  health ok, WAHA tutibom WORKING. A partir de agora, todo produto
  apresentado grava também a etiqueta de família (`fita`/`3d`).
- Parte B segue pendente da decisão do usuário sobre o rascunho
  dele no Fluxo A (ver seção acima). O grafo novo validado continua
  em `/tmp/fluxo-a-novo.json` no PC, não gravado.

## Desfecho da parte B — rascunho trocado pela versão proposta (2026-11-13 ~23:09)

- Usuário escolheu a opção (c): "Trocar pela versão proposta".
- O rascunho dele foi salvo antes de sobrescrever:
  `/tmp/rascunho-usuario-fluxo-a.json` no PC e
  `~/workspace/deskcomm-b/rascunho-usuario-fluxo-a.json` na VM
  (6 nós, 7 arestas — as duas mensagens fita-específicas dele
  estão lá, recuperáveis).
- O `draft_graph` do pointer agora é a versão proposta (8 nós,
  10 arestas): condição "Tem etiqueta fita?" → msg1-fita
  ("Oi! Ficou alguma dúvida sobre a fita?...") quando tem a
  etiqueta, msg1 genérica quando não tem; msg2 genérica
  inalterada. Verificado por leitura de volta no banco.
- A versão viva continua `1df069fe` — nada mudou para quem já
  está inscrito. **Falta o usuário publicar o rascunho no
  painel** (um clique); só então a nova versão passa a valer
  para NOVAS inscrições (as 3 ativas continuam presas à 1df069fe).
