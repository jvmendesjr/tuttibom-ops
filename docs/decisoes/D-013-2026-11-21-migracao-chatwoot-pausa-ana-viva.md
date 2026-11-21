# D-013 — Migração para o Chatwoot e pausa da Ana viva (com plano)

**Data:** 2026-11-21. **Status:** decisão tomada pelo usuário em
2026-11-21 18:58 (migrar) e 19:06 (pausar a Ana viva também, com
plano). **Nada neste documento já foi executado** — ele é o plano;
a pausa acontece depois da aprovação deste plano, na janela
definida no §4.

**Decisão-mãe:** D-012 (2026-11-21) — CRM próprio + atendimento pelo
Muse, produção Deskcomm/Ana v12-B intocada até a promoção por setor.
**Esta decisão muda o D-012 num ponto:** a promoção deixa de ser
"quando os setores passarem" e passa a ter um caminho concreto
(Chatwoot) e uma pausa programada da Ana viva. O resto do D-012
continua valendo — inclusive que nada publica, envia ou combina
preço sem aprovação do usuário ao texto exato.

## 1. O que foi decidido

1. **Migrar para o Chatwoot na nova vertente.** O Chatwoot vira o
   inbox da vertente: WhatsApp pelo WAHA (app oficial) e Messenger
   direto pelo app da Meta. Testar; se aprovado, promover por setor
   (V5).
2. **Congelar a main.** Nenhum trabalho novo no caminho Deskcomm;
   o foco total vai para a vertente.
3. **Pausar a Ana viva também — com este plano.** A IA da Ana no
   WhatsApp (número 558881022939) é pausada, e o atendimento do
   WhatsApp passa a ser coberto como descreve o §3, até o Chatwoot
   assumir.

## 2. O que pausa e o que não pausa

**Pausa:**

- A IA da Ana **no canal WhatsApp** (558881022939). As mensagens
  passam a cair na caixa de entrada como atendimento humano, sem
  resposta automática.

**Não pausa:**

- WAHA (sessão do número continua conectada), Zernio, Deskcomm,
  número, página do Facebook.
- O Messenger: a IA já está pausada lá desde 2026-11-16 — nada muda.
- A rotina do gestor (3 varreduras/dia via MCP, 08:00/14:00/20:00)
  — o gestor trabalha sobre o Deskcomm, não depende da Ana.
- A V4 (Gleiciane, Messenger): continua até a conversa terminar;
  o relatório e a remoção da vigília acontecem no fechamento dela
  (§4, passo 1).

## 3. Cobertura durante a pausa

Sem a Ana, uma mensagem no WhatsApp fica sem resposta até alguém
atender. A cobertura tem duas fases:

**Fase A — até o WhatsApp no Chatwoot estar provado: cobertura
humana.** O usuário (ou o responsável) responde no inbox do
Deskcomm. O Muse vigia o WhatsApp via MCP (mesma vigília da V4,
estendida ao canal WhatsApp, a cada 5 min) e avisa quando chegar
mensagem — não responde ninguém sozinho nessa fase. Volume
esperado: baixo; nenhuma mensagem nova desde 2026-11-19 e a equipe
só volta segunda, 2026-11-23.

**Fase B — WhatsApp no Chatwoot provado: cobertura pela vertente.**
O atendimento do WhatsApp passa a ser feito no Chatwoot, pelo Muse
como Ana (skill + CRM próprio + Jev), via API. A Fase A termina
quando o teste do WhatsApp no Chatwoot passar.

**Leads abertos no momento da pausa:**

- Junior (WhatsApp, em risco, 26 h de silêncio em 2026-11-20):
  segue no Deskcomm; se voltar a escrever, cai na cobertura da
  fase vigente.
- P8 (golpe do Mercado Livre, decisão pendente): a decisão continua
  pendente do usuário; a pausa não muda nada nele.
- Gleiciane (Messenger, V4): não é afetada — outro canal, outra
  vigília.

## 4. Sequência (ordem — não pular passo)

1. **Fechar a V4** (relatório + remover a vigília
   `v4-watch-gleiciane` + fechar o lead no CRM próprio), quando a
   conversa da Gleiciane terminar. A V4 é no Messenger; a migração
   não a cancela, só a sucede.
2. **Aprovar este plano (D-013)** — é o passo atual.
3. **Subir o Chatwoot** (decidir hospedagem: PC ou Railway,
   ~US$ 15–25/mês; 4 contêineres, mínimo 4 GB RAM / 2 CPU) +
   conectar o WAHA (app oficial) + o Facebook direto.
4. **Testar no Messenger** (canal já com IA pausada; teste
   supervisionado, com o usuário acompanhando).
5. **Testar no WhatsApp** (número de teste ou o número vivo numa
   janela acompanhada, com o usuário por perto).
6. **Pausar a Ana viva no WhatsApp** — só depois do passo 5 passar.
   Se o usuário quiser pausar antes, vale a Fase A (cobertura
   humana) e a pausa é registrada como antecipada, com o motivo.
7. **Promoção por setor (V5)**, um setor por vez, quando passar no
   seu teste.

**Janela proposta para a pausa:** assim que o teste do WhatsApp no
Chatwoot passar (passo 5). Não há data fixa neste documento — a
data é o teste, não o calendário. Se o teste atrasar, a pausa
atrasa junto; a Ana viva não é pausada no escuro.

## 5. Execução da pausa (passo 6, a verificar no painel antes)

1. Abrir o painel do Deskcomm → canal WhatsApp → pausar a IA
   (o mesmo controle que hoje mostra "IA aberta ao público" no
   WhatsApp e "IA pausada" no Messenger).
2. Confirmar no cartão do canal: "IA pausada — As mensagens chegam
   para atendimento humano."
3. Enviar uma mensagem de teste do próprio telefone para o número
   da loja e confirmar: chega como caso humano, **sem resposta da
   Ana**.
4. Ativar a vigília do WhatsApp (Fase A) ou confirmar que a
   Fase B está ativa.
5. Registrar a pausa (data, hora, quem executou, resultado do
   teste) no `docs/v4-teste-real-relatorio.md` ou no documento de
   acompanhamento da migração — e na memória.

## 6. Volta atrás (rollback)

1. No painel, reativar a IA no canal WhatsApp (mesmo controle).
2. Confirmar no cartão: "IA aberta ao público".
3. Enviar uma mensagem de teste e confirmar que a Ana responde
   (ack em ~30 s, turno completo em ~2 min).
4. Desativar a vigília do WhatsApp (se a Fase A estava ativa) e
   registrar a volta.
5. Tempo estimado: minutos. A volta atrás não depende do Chatwoot
   nem da vertente — é só o controle do canal.

**Quando voltar atrás:** se o Chatwoot cair, se o teste do
WhatsApp falhar, ou se o usuário decidir — sem precisar justificar.
A volta é sempre permitida e sempre registrada.

## 7. Riscos

- **Mensagem sem resposta na janela** entre a pausa e a cobertura:
  mitigado pela Fase A (vigília + aviso) e pelo volume baixo no
  fim de semana.
- **Confusão de canal:** pausar o canal errado (Messenger em vez
  de WhatsApp) — mitigado pelo passo de confirmação do cartão (§5,
  passo 2) e pelo teste (§5, passo 3).
- **Sessão do WAHA:** a pausa não toca na sessão — mas se o WAHA
  cair, nem a Ana nem a cobertura recebem nada. A saúde do WAHA
  entra na verificação do passo 5.
- **A Ana responder depois de pausada:** o teste do §5, passo 3,
  existe para pegar exatamente isso; se responder, a pausa não
  valeu e o passo é repetido com verificação.

## 8. Checklist de execução

- [ ] D-013 aprovado pelo usuário
- [ ] V4 fechada (relatório + vigília removida + lead fechado)
- [ ] Chatwoot no ar (hospedagem decidida e verificada)
- [ ] WAHA conectado ao Chatwoot (app oficial)
- [ ] Facebook conectado ao Chatwoot (direto)
- [ ] Teste no Messenger passou
- [ ] Teste no WhatsApp passou
- [ ] Pausa executada (§5) e testada
- [ ] Cobertura ativa (Fase A ou B) e registrada
- [ ] Rollback testado (volta e volta atrás, §6)

## 9. Decisões em aberto (antes de executar)

- Hospedagem do Chatwoot: PC ou Railway?
- A vigília do WhatsApp na Fase A é ativada, ou a cobertura é só
  humana sem vigília?
- Quem é o responsável humano na Fase A (o usuário ou outra
  pessoa)?
- O teste do WhatsApp usa o número vivo ou um número de teste?

## 10. Relação com as decisões anteriores

- D-012 — a decisão-mãe; esta decisão dá a ela um caminho
  (Chatwoot) e uma pausa programada.
- D-011 — atendimento no canal onde a pessoa escreveu; continua
  valendo na vertente (Chatwoot atende no canal de origem).
- D-006 — Ana 24/7; esta decisão a suspende no WhatsApp, com
  cobertura e volta atrás definidos aqui.
- D-004 — Camofox é o navegador único; a operação do painel na
  execução da pausa segue o trinômio (Camofox + Jev, display
  virtual).
