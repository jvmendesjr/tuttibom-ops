# Prévia — definição (rascunho)

**Status:** rascunho 2026-11-22 ~23:04 — em definição com a usuária.
**Base:** regras ditadas pela usuária 2026-11-22 ~11:41 + Modo A
(2026-11-11/12) + fluxo da Biblioteca de assets (2026-11-12).

## O que já está decidido

1. A prévia é normalmente entregue em **dias úteis**.
2. Excepcionalmente o humano pode entregar **fora do horário
   comercial** — só para registro interno; a Ana **NUNCA** informa
   isso às leads.
3. O agente tem que saber **quando a prévia foi entregue**, porque
   vai para o repositório (registro no CRM).
4. No início, as prévias são **feitas pela usuária**.
5. **Modo A:** a Ana oferece a prévia como pergunta, de forma amena
   ("Quer que eu monte uma prévia para você ver como fica na fita?
   É uma simulação que eu preparo para você visualizar antes de
   confirmar..."), sem dizer "é IA" de forma seca; dispara quando os
   dados da personalização já são conhecidos; monta quando a pessoa
   aceita; a imagem exata é aprovada pela usuária antes de enviar.
   **Inicialmente quem repassa a prévia ao interessado é a humana,
   não a Ana** (decisão 2026-11-22 ~23:38).
6. **Biblioteca:** Muse gera → `Pendentes/` → humano aprova a imagem
   exata → pasta da ocasião + "Aprovado" na planilha + bucket → a
   humana envia ao interessado (inicialmente).

## Fluxo (como está hoje)

1. Lead dá os dados da personalização → Ana oferece a prévia (Modo A).
2. Lead aceita → Muse gera a imagem → vai para `Pendentes/`.
3. Usuária aprova a imagem exata (ou pede outra).
4. A usuária envia a prévia aprovada ao interessado, no canal onde
   a pessoa escreveu (inicialmente a entrega é humana).
5. **Registro da entrega — DECIDIDO (ver Decisão abaixo).**
6. Depois da entrega: a humana acompanha o interessado
   (aprovação, ajustes, pagamento) até devolver a chamada para a
   Ana (ver Decisão — humano no loop).

## Decisão — pergunta 1: AMBOS (2026-11-22 ~23:17)

A usuária propôs o híbrido e é a melhor prática aqui: cada lado
guarda o que ele faz bem — a planilha/biblioteca guarda o ARQUIVO e
a identificação (para reuso); o CRM guarda o ESTÁGIO do lead.

- **Drive / planilha `Biblioteca TuttiBom — Assets`:** novas colunas
  para a prévia — imagem (link), lead/ocasião, solicitada em,
  entregue em. A imagem entregue vai para a biblioteca (pasta da
  ocasião + bucket) com um identificador único (ex.:
  `PREV-<lead>-<ocasião>-<data>`), o mesmo usado na planilha e no
  CRM — um ID amarra os três lugares e permite o reuso em outros
  usos.
- **CRM (lead):** nova coluna de estágio `previa_status`
  (`pendente` → `entregue`) + `previa_entregue_em` (data/hora) +
  `previa_imagem_ref` (o identificador da biblioteca). Quando o lead
  solicita → `pendente`; quando a humana entrega → `entregue` + data.
  Na entrega, um resumo vai para as mensagens da conversa. O painel
  do CRM mostra o estágio. Uma coluna guarda a prévia atual do lead;
  se um lead pedir uma segunda prévia, vira tabela.
- **Por que os dois:** a planilha responde "qual imagem, onde está,
  pode reusar?"; o CRM responde "esse lead já recebeu a prévia?".
  Nenhum dos dois sozinho responde as duas perguntas — e a planilha
  continua sendo o lugar que a usuária vê e edita direto.

## Implementação da pergunta 1 — AMBOS (2026-11-22 ~23:20)

- **CRM vivo:** migração aditiva aplicada (`previa_status`,
  `previa_entregue_em`, `previa_imagem_ref` em `leads`; leads
  existentes ficam com NULL). Esquema versionado em `db/crm.sql`;
  métodos `CRM.marcar_previa_solicitada` (→ `pendente`, limpa
  entrega anterior) e `CRM.marcar_previa_entregue` (→ `entregue` +
  data + ref, e resumo outbound na conversa); migração idempotente
  no `__init__` do store para bancos antigos. Testes:
  `tests/test_crm_minimo.py` 12/12 (5 novos da prévia).
- **Painel:** `services/crm-dashboard/` 0.2.0 — mostra por lead o
  estágio da prévia (`pendente` / `entregue em <data> · <ref>` / `—`
  sem pedido). Testes 8/8. Deploy no PC verificado (md5 repo =
  deployado, `/health` 0.2.0, 401 sem token).
- **Planilha `Biblioteca TuttiBom — Assets` (aba `Assets`):** colunas
  novas P:S — `Imagem (link)`, `Lead/Ocasião`, `Solicitada em`,
  `Entregue em` — confirmadas por leitura de volta; nenhum dado
  existente tocado.
- **Identificador único da imagem:** `PREV-<lead>-<ocasião>-<data>`
  — o mesmo na planilha, no arquivo da biblioteca e no
  `previa_imagem_ref` do CRM. Uma coluna guarda a prévia atual do
  lead; se um lead pedir uma segunda prévia, vira tabela.

## Decisão — entrega humana + handoff (2026-11-22 ~23:38)

- **Inicialmente a prévia é repassada ao interessado pela humana,**
  não pela Ana.
- **Quando o lead solicita a prévia:** o Muse marca o handoff para
  humano no Chatwoot (etiqueta `handoff-humano`, atribuição ao
  agente 2, nota privada "Prévia solicitada — aguardando a usuária
  criar/enviar") e chama a usuária para atender (aviso neste chat);
  marca `previa_status='pendente'` no CRM.
- **A Ana informa ao comprador** que vai solicitar a criação da
  amostra artística e que atenderemos em breve. Fora do horário
  comercial, informa que normalmente atendemos essa solicitação em
  horário comercial e pergunta se pode aguardar. A Ana nunca diz que
  transfere para humano nem que é robô/virtual. O texto de fora do
  horário diz a regra normal sem revelar a exceção (a entrega fora
  do horário continua sendo só registro interno, regra 2).
- **Horário comercial adotado:** 7h–22h (a janela de disparo da Ana)
  — a confirmar/corrigir pela usuária.
- **Textos — APROVADOS pela usuária 2026-11-22 ~23:41:**
  - Em horário comercial: "Perfeito! Vou solicitar a criação da
    amostra artística e já te chamo com a prévia, tá bom?"
  - Fora do horário comercial: "Perfeito! Vou solicitar a criação
    da amostra artística. Normalmente a gente atende essa
    solicitação em horário comercial — você consegue aguardar até
    amanhã? Assim que estiver pronta, eu te chamo aqui."

## Decisão — humano no loop na prévia (2026-11-22 ~23:47)

- **Quando o lead solicita a prévia:** o Muse transfere a chamada
  para a humana no loop (handoff no Chatwoot + aviso neste chat) e a
  humana mantém o contato com o interessado, interagindo com ele
  diretamente no Chatwoot, até devolver a chamada para a Ana.
- **A humana pode continuar até o pagamento** — a venda inteira fica
  com ela enquanto durar o atendimento humano; o pagamento segue a
  regra de sempre (só confirmado pela usuária/produtor; a Ana nunca
  afirma pagamento recebido sem confirmação).
- **Devolver a chamada para a Ana:** a usuária avisa o Muse neste
  chat (ou tira a etiqueta `handoff-humano` / desatribui no Chatwoot)
  e a Ana retoma o atendimento normalmente, de onde a conversa parou.
- **O Muse acompanha e registra:** tudo que for conversado com o
  humano serve para as próximas interações e para a sequência do
  funil — o Muse lê o fio da conversa e atualiza a etapa do lead e
  os resumos no CRM conforme o progresso da venda com o humano.
- **A imagem da prévia** chega ao Muse por um destes caminhos (a
  usuária escolhe na hora):
  - ela envia a imagem aqui neste chat antes;
  - o Muse captura do WhatsApp (anexo da mensagem enviada no
    Chatwoot) — caminho a verificar no primeiro caso real;
  - ela adiciona a imagem na biblioteca e avisa o Muse.

## Perguntas abertas

1. **Onde fica o registro da entrega? — DECIDIDO 2026-11-22 ~23:17:
   AMBOS — IMPLEMENTADO 2026-11-22 ~23:20** (ver seção Decisão e
   Implementação). Alternativas consideradas: tabela própria `previas`
   no CRM; resumo na conversa; só planilha.
2. **O que a Ana diz quando a prévia é solicitada? — TEXTOS
   APROVADOS 2026-11-22 ~23:41** (ver Decisão — entrega humana).
   **O que ela diz depois que o cliente vê? — RESOLVIDO pelo fluxo
   humano no loop (2026-11-22 ~23:47):** a humana cobre o
   pós-prévia; a Ana retoma quando a chamada é devolvida.
3. **Registro retroativo — DECIDIDO 2026-11-22 ~23:39: NÃO.** O
   Junior não ganha registro: o contato é de teste, da dona; a
   entrega de 17/11 não entra no CRM.

## O que NÃO muda

- Nada é enviado sem a aprovação da imagem exata pela usuária.
- A Ana nunca informa às leads que uma prévia pode sair fora do
  horário comercial.
- Sem dado de comprador no repo; o registro da entrega guarda
  data/hora, imagem e lead — nada além do que o CRM já guarda.
