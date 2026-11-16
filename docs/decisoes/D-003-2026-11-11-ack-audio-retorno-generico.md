# D-003 — 2026-11-11 — Ack para áudio + retorno genérico (Fluxo A)

**Data:** 2026-11-11 ~20:03 -03
**Decisor:** usuário ("Sim, aprova o desenho")
**Status:** decidido; aplicado em parte (ver "O que foi feito")

## Decisão

1. **Ack para áudio.** Quando chegar um áudio, a Ana manda o ack curto
   ("Só um instante" / "Vou verificar" / "Ok, só um instante", variando
   como já faz para texto) antes ou durante a transcrição; só depois vem
   a resposta completa. A correção é no código do DeskcommCRM, após a
   investigação da causa — nada commita nem faz deploy sem aprovação
   separada, como antes.
2. **Retorno genérico (opção A, agora).** O texto fixo do Fluxo A
   ("Silêncio — escolhendo o produto") deixa de presumir fita e passa
   a ser genérico, sem presumir o produto. A opção B — o retorno ler o
   histórico/transcrição antes de mandar — fica como investigação
   seguinte, não agora.
3. **Pausar a pessoa das letras.** A inscrição ativa de follow-up da
   pessoa que pediu letras de MDF é pausada/retirada, para não mandar
   uma quarta mensagem sobre fita.

## Contexto

- **Teste de transcrição 2026-11-11:** o ElevenLabs Scribe (`scribe_v1`)
  acertou os dois áudios (preço 10 m/15 mm dourada → R$ 19,00 certo;
  dados Joãozinho/3 anos/aniversário/fita preta/sexta → entendeu, disse
  que sexta não fecha). O usuário achou o atraso aceitável, mas notou
  que o ack NÃO disparou para áudio — a Ana deveria ter pedido para
  aguardar no instante, como já está programado para mensagens
  convencionais.
- **Causa raiz do ack (confirmada no código 2026-11-11 ~20:10):** a
  decisão do ack (`decidirReconhecimento`) usa
  `textoDoClienteNaUltimaMensagem`, que devolve vazio para mídia por
  desenho (R4 — a pergunta de manipulação só vê o que o cliente
  digitou); como as 5 perguntas do reconhecimento vão na MESMA chamada
  Jev da manipulação, e `perguntarManipulacaoAoJev` retorna `null`
  quando a mensagem está vazia, o ack nunca é perguntado para áudio.
  A hipótese do usuário (demora da transcrição) NÃO é o mecanismo.
  **Direção da correção:** separar — a manipulação segue só-texto (R4
  preservada), e o reconhecimento recebe a transcrição via
  `falaDoClienteSemMoldura` (que devolve `[áudio] <transcrição>`).
  Vale só para áudio: para imagem/vídeo/documento/figurinha, a função
  devolve só rótulo + legenda (o conteúdo derivado é descrição da IA,
  não fala do cliente).
- **Defeito do retorno:** uma pessoa pediu letras de MDF (A–C, 50–60 cm)
  em 17/10 por áudio (conversa `5a0274d9`); a transcrição EXISTIA e estava
  correta. O Fluxo A mandou o texto fixo "Oi! Ficou alguma dúvida sobre
  a fita?" 3× (06/11, 09/11, 11/11); em 09/11 ela respondeu por áudio
  que não pediu fita — e o retorno mandou de novo em 11/11. **Causa: o
  Fluxo A manda texto fixo de fita a qualquer lead silencioso, sem ler
  o histórico nem a transcrição.** Não é falta de transcrição.

## O que foi feito

- **(A) Fluxo A genérico — APLICADO e VERIFICADO 2026-11-11 ~20:20.**
  Nova versão `1df069fe-c418-4ce6-8d77-409ae50667ae`, ponteiro
  `active_version_id` movido; versão anterior `06245a1b` intacta para
  rollback. Msg1: "Oi! Ficou alguma dúvida sobre o que você perguntou?
  Se quiser, me conta de novo o que você está buscando que eu te ajudo."
  Msg2 adaptada no mesmo padrão, sem presumir fita (redação adaptada
  pelo Muse; o usuário pode pedir outra).
- **(B) Inscrição da pessoa das letras — CANCELADA e VERIFICADA.**
  Inscrição ativa `fb225191-0428-42b2-a2fa-2809a4131b4e` (Fluxo A, nó
  `wait-3`, msg2 marcada para 14/11 15:11 UTC) → `status=cancelled`,
  `next_eval_at=NULL`, `cancel_reason` registrado. A 4ª mensagem NÃO
  será enviada.
- **(C) Correção do ack para áudio — PENDENTE.** É mudança de código
  no DeskcommCRM; precisa de autorização para delegar ao Cursor, como
  antes. O Muse perguntou ao usuário e aguarda a resposta.
- **(D) Investigação B — PENDENTE.** O retorno ler histórico/transcrição
  antes de mandar (passo "Classificar (IA)" no fluxo, ou a tarefa Jev
  `followup`, hoje "Não roda"). Viabilidade não verificada.

## Alternativas consideradas

- **Opção B já (retorno ler o histórico):** melhor no longo prazo, mas
  precisa de investigação (não se sabe se o passo "Classificar (IA)"
  ou o Jev `followup` resolve); por isso A agora + B depois.
- **Manter o texto de fita e só pausar a pessoa das letras:** resolve o
  caso dela, mas o texto fixo continuaria errando com qualquer outro
  lead que não quer fita (já atingiu pelo menos outra conversa, de spam
  de Mercado Pago). Descartado.

## Referências

- Rascunho: `docs/rascunho-ajustes-audio-retorno.md`
- ESTADO.md: seções "Teste de transcrição" e "Ajustes de áudio/retorno"
  (2026-11-11)
- Scripts: `~/workspace/aplicar-fluxo-a-generico.py` (VM),
  `~/workspace/ler-log-audio.py`, `~/workspace/ler-log-audio-2.py`
