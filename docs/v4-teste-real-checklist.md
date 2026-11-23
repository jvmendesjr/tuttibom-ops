# V4 — Teste real supervisionado: checklist de preparação

**Fase do roadmap:** V4 (`docs/roadmap-nova-vertente.md`). V3 passou
(45/45, commit `5b345d1`).
**Status:** PREPARADO, não executado. Nada aqui liga, pausa ou muda
nenhum canal. O teste só acontece numa janela combinada, com o usuário
presente e podendo parar a qualquer momento.

## Objetivo

Provar, com uma conversa real, o que o laboratório só simulou: a Ana
da nova vertente (skill `c918ea0`) + o CRM próprio (`54f271c`)
atendendo uma pessoa de verdade, do primeiro "oi" até o fechamento ou
a perda — sem intervenção de emergência.

## O ponto mais importante: a Ana viva continua lá

A Ana do Deskcomm (v12-B) atende o WhatsApp 24/7 HOJE, e o canal
Messenger (Zernio) está com a IA pausada, com as mensagens indo para
atendimento humano. Ou seja: **não dá para "ligar" a nova Ana no mesmo
número/página sem decidir o que acontece com a Ana viva**. Por isso o
canal do V4 é uma decisão, não um detalhe — ver "Decisões pendentes".

### Canal recomendado: Messenger (Zernio)

- A IA já está pausada nesse canal — nenhuma Ana responde sozinha lá.
- A página ligada tem só 1 seguidor: o risco de um cliente real cair
  no meio do teste é mínimo.
- Se algo der errado, o usuário assume a conversa na hora, como
  atendimento humano, sem ninguém perceber que era um teste.

### Alternativa: WhatsApp

- Só com a IA do Deskcomm pausada na sessão `tutibom` durante a
  janela, e religada depois — uma ação que muda comportamento ao vivo
  e precisa ser feita (e desfeita) pelo usuário no painel, comigo
  conferindo antes e depois.
- Risco maior: qualquer cliente real que escrever na janela cai no
  teste. Por isso, se for WhatsApp, a janela tem que ser curta e
  combinada com antecedência.

## Quem é o cliente do teste

**Não é um cliente real sorteado.** É uma pessoa conhecida, que sabe
que é um teste e topou participar — de preferência o próprio usuário,
de outra conta/número, ou alguém da família. Ela segue um roteiro
simples (abaixo) e pode desviar dele: o desvio também é dado.

### Roteiro sugerido (a pessoa pode desviar)

1. "oi" (saudação fechada).
2. Perguntar por fita para aniversário (ou casamento — a pessoa escolhe
   uma ocasião).
3. Perguntar o preço da fita 22 mm / 50 m, impressão preta.
4. Perguntar o frete para Juazeiro do Norte.
5. Pedir para ver como fica antes de fechar (prévia).
6. Fechar (ou desistir — os dois finais valem; o da desistência testa
   o motivo de perda).

## Como o Muse recebe e responde (a definir antes — ver pendências)

Hoje não existe um cano automático ligando a mensagem que chega ao
Muse. No V4, o fluxo é manual e supervisionado, e o documento registra
qual dos dois jeitos vai ser usado:

- **Opção 1 — painel Deskcomm via Camofox (recomendado para o V4):**
  o Muse lê a conversa no painel (perfil `profile-panel`, display
  virtual, nunca o :0 real) e responde por ali, como atendimento, a
  cada mensagem. Lento (1–2 min por turno), mas visível e controlável.
- **Opção 2 — leitura direta do canal (WAHA / Zernio):** ler a
  mensagem na origem e responder na origem. Exige verificar antes se
  a leitura/escrita por ali está liberada e sem tocar na sessão viva.

Em qualquer das duas: **o usuário vê cada resposta antes de ela ser
enviada?** Não — no V4 a Ana responde sozinha, é esse o teste. Mas o
usuário acompanha ao vivo e pode mandar parar a qualquer momento, e
nada de preço, prévia ou endereço sai sem a regra da skill (texto
exato aprovado para prévia, endereço só após pago e fechado).

## Pré-requisitos (tudo tem que estar marcado antes da janela)

- [ ] V3 passado (feito, 45/45).
- [ ] Canal decidido (Messenger recomendado).
- [ ] Cliente do teste combinado (quem, de onde escreve).
- [ ] Janela combinada (dia + hora de início e fim, de preferência
      em horário comercial, com o produtor alcançável para confirmar
      frete/prazo se for preciso).
- [ ] Jeito de receber/responder decidido (opção 1 ou 2 acima).
- [ ] Palavra de parada combinada: o que o usuário diz aqui no chat
      para eu parar na hora (sugestão: "para o teste").
- [ ] CRM próprio pronto: banco SQLite novo, vazio, só para o V4
      (nunca reutilizar o banco do laboratório).
- [ ] Confirmado na hora: IA pausada no canal do teste (Messenger)
      ou, se for WhatsApp, IA pausada na sessão `tutibom` e
      confirmação de que nenhuma outra Ana vai responder junto.

## Durante a janela (passo a passo)

1. Usuário confirma "pode começar" aqui no chat.
2. Cliente do teste manda o "oi" no canal combinado.
3. A cada mensagem: Muse lê, responde como Ana seguindo só a skill,
   registra resumo + etapa no CRM próprio.
4. Se a pessoa pedir prévia: Muse gera o rascunho, mostra ao usuário
   aqui, e só envia depois do "pode enviar" com a imagem exata.
5. Se a pessoa perguntar frete: Muse pede o endereço, registra
   `endereco_coletado`, e confirma o valor com o produtor antes de
   responder — nunca cita valor sem confirmar.
6. Se a pessoa fechar e pagar: pagamento confirmado pelo usuário
   (nunca assumido); só então o endereço pode ser informado.
7. Usuário acompanha e pode parar a qualquer momento.

## Critérios de sucesso (todos precisam acontecer)

- [ ] A conversa completa sem intervenção de emergência.
- [ ] Nenhum preço fora do catálogo, nenhum valor de frete citado sem
      confirmação do produtor, nenhum endereço informado antes de pago
      e fechado.
- [ ] Nenhuma instrução vazada, nenhuma promessa de prazo fora da
      regra, nenhum dado pessoal guardado no repo.
- [ ] Lead registrado corretamente no CRM próprio, na etapa certa,
      com motivo quando perdido.
- [ ] Respostas em 1–2 min por turno (o ritmo do teste, não o da
      produção).

## Critérios de abortar (qualquer um para tudo)

- Preço inventado, frete com valor não confirmado, endereço antes da
  hora, dado pessoal guardado, instrução vazada.
- Resposta travada por mais de 5 min sem explicação.
- Cliente real (não o do teste) cai na conversa.
- Usuário diz a palavra de parada — ou simplesmente diz "para".

## Depois da janela

1. Muse para de responder imediatamente; usuário assume a conversa se
   ela continuar.
2. Se foi WhatsApp: religar a IA na sessão `tutibom` e confirmar que
   a Ana viva voltou a responder.
3. Fechar o lead no CRM próprio (pago ou perdido, com motivo).
4. Preencher `docs/v4-teste-real-relatorio.md` com o que aconteceu —
   incluindo o que falhou, sem maquiar.
5. Se falhou: volta para a V3, com a correção no documento do setor.
   Não se "ajeita em produção".

## Decisões pendentes do usuário (sem elas o V4 não começa)

1. **Canal: DECIDIDO 2026-11-21 — Messenger.**
2. **Contato de teste confirmado em 2026-11-21.**
3. **Janela:** a combinar (teste começou a ser ligado 2026-11-21 ~16:51).
4. **Jeito de receber/responder: Zernio (decidido 2026-11-21)** — as
   mensagens chegam na caixa de entrada do painel e o Muse responde
   por ali, como atendimento, seguindo só a skill.
5. **Verificado no painel 2026-11-21 16:51:** canal facebook ·
   TutiBom **Vinculada**, "Recebimento configurado. Novas mensagens
   entram na caixa de entrada." e **"IA pausada — As mensagens chegam
   para atendimento humano. A IA está pausada neste canal."** O número
   de WhatsApp segue com "IA aberta ao público" (Ana viva) e NÃO é
   tocado pelo teste.
