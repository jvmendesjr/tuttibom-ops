# Skill — Operação no Chatwoot (nova vertente)

**Nome:** `chatwoot-operacao`
**Descrição:** Manual de operação do agente dentro do Chatwoot: ler e
responder conversas dos inboxes WhatsApp e Messenger, resolver e
etiquetar, importar contatos e manter a ponte com o Zernio. O
COMPORTAMENTO da resposta (o que a Ana diz) vive em
`skills/ana-atendimento/SKILL.md` — esta skill é só a mecânica.
**Canal:** Chatwoot (inbox da nova vertente) — WhatsApp via WAHA,
Messenger via ponte Zernio.
**Setor:** 8 — Plataforma e Manutenção (`docs/setores/08-plataforma.md`),
com o atendimento no setor 1.
**Decisão-mãe:** D-013 (2026-11-21).
**Quando usar:** sempre que for ler, responder ou organizar conversas
no Chatwoot, importar contatos, ou mexer na ponte Zernio e no app WAHA.

## O que é o Chatwoot aqui

Inbox único da nova vertente, no PC, fora do Deskcomm. Conta
"TuttiBom" (id 2), versão 4.20.1-ce, em
`https://chatwoot.petemcasa.com` (URL pública, HTTPS terminado no
túnel `cloudflared-ponte`; por dentro, `http://100.73.22.64:3001`
na tailnet). Serviço em `/home/pc/chatwoot/`, 4 contêineres: rails,
sidekiq, postgres, redis. SMTP via Gmail (`tutibom10@gmail.com`)
configurado e provado (e-mail de teste recebido 2026-11-21 22:06).
Atendimento ligado desde 2026-11-21 22:12: o Muse atende como Ana
nos inboxes 1 e 2. Desde 2026-11-21 ~23:00 a detecção é por webhook:
o `ana-listener` recebe `message_created` e o hook
`chatwoot-ana-watch` acorda o atendimento em ~60 s (antes, só a
vigília de 5 min). A vigília `chatwoot-watch-ana` continua como rede
de segurança. O Deskcomm continua existindo, mas NÃO atende mais: a
IA dele está pausada no WhatsApp e no Messenger — nada do Deskcomm
deve voltar a responder sozinho.

Inboxes (conta 2):

| id | Nome | Canal | Origem |
|----|------|-------|--------|
| 1 | WhatsApp | `Channel::Api` | app oficial do Chatwoot no WAHA |
| 2 | Messenger | `Channel::Api` | ponte `zernio-bridge` (webhook Zernio) |

Os dois inboxes têm `lock_to_single_conversation = true`: um contato
tem no máximo UMA conversa aberta por inbox. Não crie conversa
duplicada para o mesmo contato no mesmo inbox.

## Credencial (por referência, nunca o valor)

O acesso à API usa um Personal Access Token do super-admin (id 2),
guardado SÓ no PC em `/home/pc/chatwoot/.pat-clean.txt` (chmod 600).
Nunca copie o token para o repo, para logs, para o chat ou para
relatório. Para chamar a API a partir do PC, leia o arquivo na hora;
a partir da VM, o token não sai do PC — o trabalho que precisa dele
roda no PC.

Base: `http://127.0.0.1:3001` (no PC) ou `http://100.73.22.64:3001`
(na tailnet). Header: `api_access_token: <token>`.

## Operar pela API (o caminho normal)

Nunca opere o atendimento clicando na tela quando a API resolve. As
chamadas abaixo usam a conta 2.

- Listar conversas abertas de um inbox:
  `GET /api/v1/accounts/2/conversations?inbox_id=<id>&status=open`
- Ler mensagens de uma conversa:
  `GET /api/v1/accounts/2/conversations/<id>/messages`
- Responder (como agente):
  `POST /api/v1/accounts/2/conversations/<id>/messages`
  `{"content": "<texto exato aprovado>", "message_type": "outgoing"}`
- Resolver: `POST /api/v1/accounts/2/conversations/<id>/toggle_status`
  `{"status": "resolved"}` (reabrir: `"open"`).
- Buscar contato: `GET /api/v1/accounts/2/contacts/search?q=<nome|telefone>`
- Criar contato: `POST /api/v1/accounts/2/contacts`
  `{"name": ..., "phone_number": "+55...", "identifier": "<id Deskcomm>"}`.
  O `identifier` guarda o id do contato no Deskcomm (uuid) — é o que
  liga as duas bases e evita duplicata. Antes de criar, busque pelo
  telefone e pelo identifier; se existir, não crie de novo.
- Etiquetas: `POST /api/v1/accounts/2/conversations/<id>/labels`
  `{"labels": ["fita"]}`. Use as etiquetas do atendimento (fita, 3d,
  preco) — as mesmas do Deskcomm — e só as que já existem na conta.

Depois de responder, registre no CRM próprio (setor 2): etapa, resumo
do que foi perguntado e combinado, próxima ação com data. O Chatwoot
guarda a conversa; o CRM guarda o funil.

**Regra da rajada (resposta da Ana):** antes de responder, releia a
conversa inteira; se chegaram mensagens novas enquanto você escrevia,
junte TUDO (a rajada inteira) numa resposta só e só então envie —
nunca responda mensagem por mensagem separadamente.

## WhatsApp (inbox 1, via WAHA)

- WAHA standalone na :3005, sessões `tutibom` (número da loja) e
  `petemcasa`, ambas WORKING. Nunca ligue o WAHA interno do compose
  do Deskcomm.
- O app Chatwoot do WAHA (`WAHA_APPS_ON=chatwoot`) recebe as mensagens
  do WhatsApp e as entrega no inbox 1; a resposta do agente volta pelo
  webhook do inbox 1 para o WAHA.
- O app exige no compose do WAHA: `WAHA_APPS_ENABLED=True`,
  `WAHA_APPS_ON=chatwoot`, `REDIS_URL` e `WAHA_API_KEY_PLAIN`.
  **Nunca** defina `WAHA_API_KEY` no WAHA — quebraria as chamadas do
  Deskcomm.
- Se precisar reiniciar o WAHA: confira ANTES que a sessão persiste
  (status via API do WAHA) e DEPOIS que ela voltou WORKING sem novo
  QR. Se a sessão não voltar, PARE e reporte — não force.

## Messenger (inbox 2, via ponte Zernio)

O Messenger não tem app nativo aqui: chega pelo webhook do Zernio e
passa pela ponte `zernio-bridge`.

- Serviço: `zernio-bridge`, systemd no PC
  (`/home/pc/chatwoot/zernio-bridge/`, Python stdlib, porta 3020).
  Config em `.env` no mesmo diretório (chmod 600). Logs:
  `sudo journalctl -u zernio-bridge -f`.
- Ida (Zernio → Chatwoot): o Zernio POSTa `message.received` em
  `/webhooks/zernio` com `X-Zernio-Signature` (HMAC-SHA256 do corpo
  com o secret do endpoint). A ponte verifica a assinatura (401 se
  inválida), dedupe pelo id do evento, cria/acha o contato e a
  conversa no inbox 2 e registra a mensagem como incoming.
- Volta (Chatwoot → Zernio): o Chatwoot POSTa `message_created` e
  `message_updated` em `/webhooks/chatwoot` com `X-Chatwoot-Signature`
  (HMAC-SHA256 de `"<timestamp>.<corpo>"` com o secret do canal API).
  A ponte dedupe pelo id da mensagem e envia pela API do Zernio.
- **Volta ATIVA desde 2026-11-21 21:37:** a chave da API do Zernio
  (`ZERNIO_API_KEY`, 67 caracteres) foi colocada pelo usuário no
  `.env` da ponte e a ponte foi reiniciada (21:37:13). A volta foi
  provada: o envio usa `POST
  /v1/inbox/conversations/{conversationId}/messages` com
  `{"accountId": "6aed2e33335a3fa3818d86cf", "message": "<texto>"}` —
  o formato anterior (`{"text": ...}`) devolvia 400; corrigido
  21:48–21:50 e confirmado com `outbound ok` às 21:49:31 e
  recebimento confirmado pelo usuário no Messenger às 21:53.
  `ZERNIO_ACCOUNT_ID` também está no `.env` da ponte.
- O endpoint do Zernio no Deskcomm continua registrado como reserva
  até a migração completar; não o remova.
- **URL pública no ar desde 2026-11-21 21:13:**
  `https://zernio-chatwoot.petemcasa.com` (CNAME proxied + regra no
  túnel `cloudflared-ponte`, config remota v3, sem reinício;
  `/health` 200). Endpoint registrado no Zernio — id
  `6b0235ced3563c3d930109f5`, "Chatwoot Messenger - TuttiBom",
  eventos `message.received`, ativo; teste `POST /v1/webhooks/test`
  recebido pela ponte às 21:22:42. Ida e volta do Messenger provadas
  ponta a ponta 21:44–21:53.

## Ouvinte de webhook e hook (detecção imediata)

Código em `services/chatwoot-ana/` (detalhe em
`docs/ana-chatwoot-configuracao.md`).

- **Ouvinte `ana-listener`:** systemd no PC
  (`/home/pc/chatwoot/ana-listener/`, porta 3021). Webhook de conta
  id 1 no Chatwoot: `http://100.73.22.64:3021/webhooks/chatwoot`,
  evento `message_created`. Recebe, dedupe por id da mensagem, só
  processa `incoming`, enfileira em `listener.db`. `GET /pending`,
  `POST /ack`, `GET /health`, `GET /stats`. Nunca responde ninguém,
  exceto o cumprimento automático (textos fixos, ver abaixo), e
  nunca loga texto de cliente. Se o `handoff.py` mudar no disco,
  reiniciar: `sudo systemctl restart ana-listener`.
- **Cumprimento automático (ack de 10 s, aprovado 2026-11-21):**
  na abertura da conversa o ouvinte agenda para 10 s depois um
  cumprimento fixo (saudação pelo horário + pedido cordial de
  espera), antes da resposta da Ana. Timer fixo (não deslizante);
  aos 10 s o ouvinte reavalia: classifica a rajada INTEIRA da janela
  (basta um pedido na janela para usar o pool com "verificar") e
  suprime se houve qualquer mensagem (incoming ou outgoing) nas 2h
  antes da rajada — pausa de 2h (decisão 2026-11-22): depois da
  primeira vez, só dispara de novo numa abertura nova (primeira
  mensagem ou última atividade há mais de 2h). Sem a API, só envia
  se a conversa nunca recebeu cumprimento. Máx. 1x a cada 10 min
  por conversa (guarda rápida); nunca para ignorados. O
  cumprimento aparece na conversa como mensagem da Ana e vem no item
  do `GET /pending` (campo `cumprimento`: texto + `enviado_em`) —
  quando você acordar, leia-o: ele diz o que o cliente já recebeu e,
  se o cliente respondeu ao cumprimento, a reação dele está no fio.
  Textos (dois pools, saudação por horário em America/Fortaleza):
  saudação fechada sem "verificar" ("Só um instante que já te
  atendo." / "Ok, só um instante." / "Já te atendo."); com pedido
  com "verificar" ("Vou verificar aqui e já te respondo." / "Só um
  instante que já te respondo." / "Ok, vou verificar e já te
  chamo."). O único envio do serviço é
  `chatwoot_client.enviar_cumprimento` (só textos fixos).
- **Hook `chatwoot-ana-watch`:** runtime, poll a cada 60 s, consulta
  `/pending` via `ssh` (a VM não alcança a tailnet por HTTP direto)
  e acorda o agente quando há mensagem nova. O worker acordado
  verifica o evento na API, reporta no chat (conversa, inbox,
  contato, texto, hora), dá `/ack` e o Muse responde como Ana.
- **Empresas conhecidas — IGNORAR (regra do usuário, 2026-11-21):**
  contatos de empresas conhecidas (Mercado Livre +5511978832287 e
  outras) são canais de comunicação e alerta, NÃO clientes. A Ana
  nunca responde, não cria lead, não faz follow-up nem handoff para
  eles. A lista vive em `services/chatwoot-ana/ignorados.json` e é
  consultada pelo ouvinte, pelo runner e pelo handoff — e pela
  vigília (que marca como vista e segue em silêncio). Nunca bloquear,
  apagar ou alterar esses contatos: o do Mercado Livre também é usado
  por outra operação do usuário. Caso concreto: conversa 8, 4ª
  mensagem idêntica de "Alerta de segurança" (22:33) — sem resposta,
  sem lead (resolve na prática a P8).

## Follow-up automático (só rascunhos)

- Runner `services/chatwoot-ana/followup.py`, cron
  `chatwoot-followup-ana` a cada 2 h. Lê o CRM vivo
  (`/home/pc/chatwoot/crm.sqlite3`) + conversas abertas e escreve
  rascunhos em `/home/pc/chatwoot/ana-listener/followup-drafts/`.
  **Nunca envia sozinho.** Quem envia é o Muse, como Ana, depois de
  revisar o rascunho — e marca o follow-up como `enviado` no CRM
  (`CRM.marcar_followup`).
- Teto: máx. 3 toques em 2 dias por lead; pagamento tem 1 toque só.
  Cancelar-ao-responder: inbound após o agendamento cancela.
- Textos-modelo e cadência (12 h / 24 h / 40 h) em
  `docs/followup-textos-modelo.md` — aguardam aprovação do usuário;
  a aprovação é pré-condição do envio, não do rascunho.
- O `contato_ref` do lead precisa conter o identifier exato ou os
  dígitos do telefone, senão o runner não acha a conversa.

## Prévia (Modo A) — registro AMBOS (2026-11-22)

A prévia é oferecida como pergunta (Modo A, skill da Ana) e só é
enviada depois que a usuária aprova a imagem exata. **Inicialmente
quem envia a prévia ao interessado é a humana.** O registro da
entrega vive nos dois lados (decisão AMBOS):

- **Quando o lead solicita:** marcar `pendente` no CRM (SQL abaixo),
  marcar o handoff para humano no Chatwoot (etiqueta `handoff-humano`,
  atribuição ao agente 2, nota privada "Prévia solicitada —
  aguardando a usuária criar/enviar") e avisar a usuária neste chat.
  A Ana informa que vai solicitar a criação da amostra artística e
  que atenderemos em breve; fora do horário comercial (7h–22h),
  avisa que normalmente atendemos em horário comercial e pergunta se
  pode aguardar (textos exatos aprovados 2026-11-22 ~23:41, na skill
  da Ana e no rascunho).
- **Humano no loop (2026-11-22):** a humana mantém o contato com o
  interessado no Chatwoot e pode continuar até o pagamento; o Muse lê
  o fio e atualiza a etapa do lead e os resumos no CRM conforme o
  progresso da venda. Para devolver a chamada para a Ana, a usuária
  avisa neste chat (ou tira a etiqueta `handoff-humano` / desatribui
  no Chatwoot) e a Ana retoma. A imagem da prévia chega por um destes
  caminhos: a usuária envia aqui neste chat; o Muse captura do anexo
  da mensagem no Chatwoot (a verificar no primeiro caso real); ou a
  usuária adiciona na biblioteca e avisa. Qualquer um dos três
  caminhos termina no mesmo registro consolidado (biblioteca +
  planilha + CRM, amarrados pelo `PREV-...`); nenhum dispensa o
  registro.
- **Planilha/biblioteca:** a imagem entregue vai para a biblioteca
  (pasta da ocasião + bucket) com o identificador único
  `PREV-<lead>-<ocasião>-<data>`; a planilha `Biblioteca TuttiBom —
  Assets` (aba `Assets`) registra `Imagem (link)`, `Lead/Ocasião`,
  `Solicitada em`, `Entregue em`.
- **CRM (o estágio do lead):** quando o lead aceita a prévia, marcar
  `pendente`; quando a humana entrega a imagem aprovada, marcar
  `entregue` + data + referência. O CRM vivo NÃO é aberto pelo store
  aqui (ver o quirk de import no PC) — marcar por SQL direto, stdlib,
  replicando os métodos do store:
  ```sql
  -- pedido aceito:
  UPDATE leads SET previa_status='pendente',
    previa_entregue_em=NULL, previa_imagem_ref=NULL,
    atualizado_em='<ISO -03:00>' WHERE id=<lead>;
  -- entrega (imagem aprovada, já na biblioteca):
  UPDATE leads SET previa_status='entregue',
    previa_entregue_em='<ISO -03:00>',
    previa_imagem_ref='PREV-<lead>-<ocasião>-<data>',
    atualizado_em='<ISO -03:00>' WHERE id=<lead>;
  INSERT INTO mensagens (lead_id, direcao, resumo, criado_em)
    VALUES (<lead>, 'outbound',
    'Prévia entregue — imagem PREV-<lead>-<ocasião>-<data>',
    '<ISO -03:00>');
  ```
  O painel do CRM mostra o estágio por lead (`pendente` / `entregue
  em <data> · <ref>` / `—` sem pedido).
- **Não criar** o registro retroativo da entrega do Junior de
  2026-11-17 — DECIDIDO 2026-11-22 ~23:39: o contato é de teste, da
  dona; o Junior não ganha registro. Os textos da Ana quando a prévia
  é solicitada estão aprovados (pergunta 2, 2026-11-22 ~23:41) e na
  skill da Ana.

## Handoff humano

- Humano: agente id 2 (`tutibom`, administrador) — único agente da
  conta. Código em `services/chatwoot-ana/handoff.py`.
- Detecção determinística: humano-explicito, amostra-física,
  suspeita-golpe, pós-venda. Sentimento negativo, "não sei responder",
  fora de escopo genérico e assunto sensível ficam para o julgamento
  do agente.
- Ação: etiqueta `handoff-humano` + atribuição ao `tutibom` + nota
  privada com motivo e hora. **Nota privada é `POST /messages` com
  `private: true`** — o endpoint `/notes` dá 404 no 4.20.1-ce.
- A Ana nunca diz que vai transferir para um humano nem que é
  robô/virtual.

## Webhooks do Chatwoot e rede privada

O Chatwoot rejeita webhook para IP privado por padrão (SSRF). Para os
webhooks dos inboxes apontarem para o PC/tailnet, o `.env` do Chatwoot
tem `SAFE_FETCH_ALLOW_PRIVATE_NETWORK=true`. **Atenção:**
`docker compose restart` NÃO recarrega o `.env` — para aplicar uma
mudança no `.env`, recrie os contêineres com
`docker compose up -d rails sidekiq` e confira com
`docker compose exec sidekiq printenv SAFE_FETCH_ALLOW_PRIVATE_NETWORK`.

## O que nunca fazer

- Nunca responda como outro agente nem mude o remetente da conversa.
- Nunca altere webhook, inbox, token ou `.env` sem uma decisão
  registrada (D-013 ou nova).
- Nunca desligue o `cloudflared-ponte` nem toque no Deskcomm produção
  (sem `git pull` no branch local, sem migration no banco de produção,
  sem `docker compose down -v`).
- Nunca coloque segredo ou dado de comprador no repo, em log, em
  relatório ou no chat — só contagens e ids internos.
- Nunca duplique contato, conversa ou envio: antes de criar, busque;
  depois de uma falha, leia o estado atual antes de repetir.
- Nunca prometa prazo, preço ou envio sem a aprovação do usuário ao
  texto exato (vale a skill da Ana).

## Verificação rápida (antes de dizer que está pronto)

- `curl https://chatwoot.petemcasa.com/` → 200, e
  `/app/login` → 200 (URL pública, HTTPS).
- `curl http://127.0.0.1:3001/` → 200 (Chatwoot no ar).
- `curl http://127.0.0.1:3020/health` → `{"ok": true, ...}` (ponte).
- `curl http://127.0.0.1:3021/health` → `{"ok": true, "service": "ana-listener", ...}` (ouvinte).
- `curl http://127.0.0.1:3021/pending` → `{"pending": []}` (fila vazia).
- `curl http://127.0.0.1:3021/stats` → inclui `"cumprimentos": <n>` (cumprimentos enviados).
- `sudo systemctl is-active ana-listener` → `active`.
- `GET /api/v1/accounts/2/inboxes` → inboxes 1 e 2.
- `sudo systemctl is-active zernio-bridge` → `active`.
- `sudo journalctl -u zernio-bridge --since '10 minutes ago'` →
  sem `ERROR` novo.
- Contatos: `GET /api/v1/accounts/2/contacts` → total esperado
  (16 importados do Deskcomm + 1 contato de sistema
  `whatsapp.integration`).
