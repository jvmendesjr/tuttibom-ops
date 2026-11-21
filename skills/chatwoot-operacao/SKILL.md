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
"TuttiBom" (id 2), versão 4.20.1-ce, em `http://100.73.22.64:3001`
(serviço em `/home/pc/chatwoot/`, 4 contêineres: rails, sidekiq,
postgres, redis). O Deskcomm continua existindo, mas NÃO atende mais:
a IA dele está pausada no WhatsApp e no Messenger — nada do Deskcomm
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
- **Volta DESATIVADA por enquanto:** a ponte não tem a chave da API
  do Zernio (`ZERNIO_API_KEY` vazia no `.env`). Sem ela, a resposta
  do agente fica registrada no log como "outbound DESATIVADO" e NÃO
  chega ao Messenger. Para ativar, o usuário provê a chave (do painel
  do Zernio) e ela vai para o `.env` da ponte — nunca para o repo.
- O endpoint do Zernio no Deskcomm continua registrado como reserva
  até a migração completar; não o remova.
- **URL pública pendente:** o Zernio precisa alcançar a ponte pela
  internet. Hoje a ponte só é alcançável na tailnet/local. Registrar
  o endpoint no Zernio exige um hostname público novo no túnel
  `cloudflared-ponte` (DNS + regra de ingress + reinício do túnel) —
  decisão do usuário, ainda não tomada. Sem ela, o teste real do
  Messenger continua pelo Deskcomm (V4).

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

- `curl http://127.0.0.1:3001/` → 200 (Chatwoot no ar).
- `curl http://127.0.0.1:3020/health` → `{"ok": true, ...}` (ponte).
- `GET /api/v1/accounts/2/inboxes` → inboxes 1 e 2.
- `sudo systemctl is-active zernio-bridge` → `active`.
- `sudo journalctl -u zernio-bridge --since '10 minutes ago'` →
  sem `ERROR` novo.
- Contatos: `GET /api/v1/accounts/2/contacts` → total esperado
  (16 importados do Deskcomm + 1 contato de sistema
  `whatsapp.integration`).
