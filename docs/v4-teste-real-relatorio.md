# V4 — Teste real supervisionado: relatório

**Status:** EXECUTADO E FECHADO em 2026-11-21 (~22:08 -03).
**Decisão após o V4:** ver seção "Veredito" — proposta fundamentada, a
decisão final é do usuário.

## Objetivo e método

Validar, com uma cliente de teste real no Messenger, o fluxo completo
da nova vertente antes de qualquer promoção: transporte da mensagem
(Zernio → Deskcomm), leitura pelo Muse via MCP, resposta como Ana pelo
painel do Deskcomm (navegação Camofox + Jev), e registro do funil no
CRM próprio — sem tocar na Ana viva de produção (que estava pausada).

- **Canal:** Messenger, via Zernio → inbox do Deskcomm. A IA do canal
  estava pausada desde 2026-11-16, então as mensagens chegavam para
  atendimento humano; o Muse lia via MCP e respondia pelo painel.
- **Contato:** participante convidado para o teste, sem intenção de compra.
- **CRM próprio:** banco de teste local, fora do repositório.
- **Vigília:** a cada 5 min, só leitura via MCP. O Muse respondia ao aviso.
- **Janela:** 2026-11-21, 17:09–21:49 (-03). Check final às ~22:08.

## Cronologia (horários em -03)

| Hora | Direção | Mensagem |
|---|---|---|
| 17:09:20 | inbound | Saudação inicial. |
| 17:20:29 | outbound (Ana) | Saudação com pergunta para entender o pedido. |
| 17:36:27 | inbound | Pedido de preço para fita de 10 m com impressão dourada. |
| 17:52:12 | outbound (Ana) | "A fita de 10 m com impressão dourada fica R$ 19,00 na de 15 mm e R$ 21,90 na de 22 mm. Qual largura você quer?" |
| 21:44:28 | inbound | "Olá" — **teste do próprio usuário, não da cliente** |
| 21:49:31 | outbound | "Tentativa 3: agora com o formato certo da API (message em vez de text). Recebeu esta?" — **teste do Chatwoot, não da Ana** (ver nota) |
| 21:49:54 | inbound | "Recebi a 3" — **teste do próprio usuário, não da cliente** |

**Check final (~22:08, via `crm_get_conversation_history`):** nenhuma
mensagem nova depois de 21:49:54. A última mensagem da conversa é o
"Recebi a 3" (inbound, 21:49:54). O contato de teste não respondeu à resposta
de preço desde 17:52 — 4h16 de silêncio até o fechamento.

## Tempos de resposta

- Saudação: **11 min 9 s** (17:09:20 → 17:20:29).
- Preço: **15 min 45 s** (17:36:27 → 17:52:12).
- Meta da vertente: 1–2 min. **Meta não atingida.**

**Causa:** a latência é detecção + navegação, não o modelo. A vigília
só olha a cada 5 min; depois do aviso, o Muse ainda precisa abrir a
conversa no painel (a lista do Inbox veio vazia — ver desvio abaixo),
localizar o campo, digitar e enviar pelo Camofox. Na Ana viva
(orientada a evento) o ack sai em ~30 s e o turno completo em ~2 min;
na V4 o atraso é estrutural da vigília por polling.

## Desvios e incidentes

1. **Lista do Inbox veio vazia.** Na primeira resposta (17:20), a lista
   de conversas do painel não mostrava a conversa do contato de teste da V4; a
   conversa foi aberta pela URL direta
   (`/app/inbox?id=<conversation-id>`). Desvio de operação, sem
   impacto no conteúdo — mas é um ponto de fragilidade do painel que
   a vigília precisa contornar.
2. **Mensagens de teste do usuário com entrega dupla (21:44/21:49).**
   O usuário enviou "Olá" e "Recebi a 3" do lado da cliente para
   testar o Chatwoot. Como os dois webhooks do Zernio estavam ativos
   (Deskcomm e Chatwoot), as mensagens caíram nos dois inboxes. Não
   são retomada da conversa de venda — o contato de teste não voltou a falar
   depois das 17:52. Detalhe: a mensagem de teste do Chatwoot
   ("Tentativa 3", 21:49:31) aparece também na conversa do Deskcomm,
   como outbound com `sent_via: external_device` — artefato da
   entrega dupla, não uma resposta da Ana.
3. **Preço citado foi o do catálogo.** FITA-15-10-DOURADO R$ 19,00 e
   FITA-22-10-DOURADO R$ 21,90 (captura Shopee 2026-10-30). Nenhum
   valor inventado, nenhum frete citado, nenhum endereço informado.

## Resultado

- **Etapa final no CRM próprio:** "Não comprou", motivo
  `sem_resposta` (fechado 2026-11-21 ~22:08, verificado por leitura
  de volta). Resumos finais registrados: as duas mensagens de teste
  do usuário e o fechamento.
- **Motivo:** sem resposta ao preço desde 17:52. **A "perda" não é
  perda comercial:** o contato foi convidado
  para testar, sem intenção de compra. O funil registra o
  desfecho observado, não um fracasso de venda.
- **Memória por contato:** interesse `fita`.
- **Tempo por turno (observado):** 11 min e 16 min (ver acima).
- **Follow-up marcado para 2026-11-22:** cancelado com o fechamento
  — o lead foi encerrado e o cron de follow-up da V4 foi removido
  junto com a vigília. (Ressalva: o campo `data_followup` do lead
  continua com 2026-11-22 no banco — a API do CRM não limpa o campo
  ao fechar; é só um resíduo, o lead está encerrado e sem ação.)

## Checagens

- [x] Preço só do catálogo, nenhum valor inventado.
- [x] Frete sem valor citado sem confirmação do produtor.
- [x] Endereço só após pago e fechado (ou nem informado).
- [x] Nenhuma instrução vazada, nenhuma promessa fora da regra.
- [x] Nenhum dado pessoal guardado no repo.
- [x] Lead registrado corretamente, na etapa certa.
- [x] Memória por contato só com rótulo de interesse (fita), sem PII.

## O que falhou (sem maquiar)

- **Latência (principal):** 11 e 16 min por turno, contra a meta de
  1–2 min. Causa estrutural: polling de 5 min + navegação no painel.
  Volta para o setor 1 (Atendimento) e para o setor 8 (Plataforma):
  o conserto é o atendimento orientado a evento — o Chatwoot, com
  webhook na chegada da mensagem, elimina o polling. É o que motiva
  a promoção para a V5.
- **Lista vazia do Inbox:** contorno por URL direta funcionou, mas o
  painel não é confiável como fonte de detecção. Volta para o setor 8.
- **Lacuna de versionamento:** não há regra `*.sqlite3` no
  `.gitignore` do repo — o DB da V4 (`/tmp/crm-v4.sqlite3`) ficou
  fora do repo por disciplina, não por trava. Adicionar a regra é
  pendência do setor 8 (não foi feito neste fechamento para não
  misturar o commit do relatório com mudança de config).
- **Skill `chatwoot-operacao` desatualizada em 2 pontos** (não
  bloqueiam nada, mas precisam de correção no setor 8): diz que a
  chave da API do Zernio está vazia e a volta desativada — a chave
  foi colocada em 21:37 e a volta foi provada em 21:49; e diz que a
  URL pública da ponte está pendente — `zernio-chatwoot.petemcasa.com`
  está no ar desde 21:13 e o endpoint já está registrado no Zernio.

## Veredito

**Fatos para a decisão:**

- **Mecânica provada, ponta a ponta:** transporte Zernio → Deskcomm
  funcionou; leitura via MCP (`crm_get_conversation_history`) é
  confiável; resposta pelo painel (Camofox + Jev) funcionou duas
  vezes com o texto exato da skill; registro no CRM próprio
  (funil, resumos, memória por contato) funcionou e o fechamento
  foi verificado por leitura de volta.
- **Comportamento da Ana provado:** saudação fechada, preço só do
  catálogo, uma pergunta por turno, sem frete, sem endereço, sem
  desconto, sem vazamento de instrução.
- **Fraqueza principal, conhecida e com conserto:** latência de
  11–16 min por turno (meta 1–2 min). O conserto não é ajustar a
  V4 — é trocar o mecanismo de detecção: o Chatwoot com webhook
  acorda o agente na hora, sem polling. O Chatwoot já está provado
  (WhatsApp e Messenger, ida e volta, domínio com HTTPS e SMTP).
- **Desfecho da conversa não é evidência contra o fluxo:** a cliente
  era de teste e parou de responder depois do preço; não houve erro
  de atendimento, recusa de preço ou handoff mal feito.

**Proposta (não é decisão final — decide o usuário):**

- (x) **Passou — seguir para a V5 (promoção por setor).** A V4
  provou o que tinha de provar: o fluxo funciona e a Ana se comporta
  como a skill manda. A latência fica registrada como a correção da
  V5 (atendimento por webhook no Chatwoot, não por vigília), não
  como motivo para voltar à V3.
- ( ) Não passou — voltar para a V3 com a correção: (descrever).

**Próximo passo se passar:** atendimento no Chatwoot como Ana
(vigília `chatwoot-watch-ana`, a cada 5 min — ainda polling, mas
só até o webhook do Chatwoot acordar o agente; a latência da V4
não se repete no canal novo porque a detecção é por evento no
Chatwoot, não por varredura do Deskcomm), promoção por setor.
