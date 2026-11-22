# Ana no Chatwoot — ouvinte, follow-up e handoff

Serviços da nova vertente (D-013) que fazem a Ana funcionar no
Chatwoot sem polling de 5 min. Tudo em Python stdlib, sem dependência
nova. O comportamento da Ana vive em `skills/ana-atendimento/`; a
mecânica do Chatwoot, em `skills/chatwoot-operacao/` — este diretório
é só o código que as executa.

## Arquitetura

```
WhatsApp (WAHA) ─┐
                 ├─► Chatwoot (conta 2) ── webhook message_created ──► ana-listener :3021
Messenger (Zernio)┘         │                                        (fila + handoff)
                            │   GET /pending (hook, a cada 60 s)
                            │         ▲
                            └─────────┘  (o hook acorda o Muse, que responde como Ana)
Muse responde como Ana via API do Chatwoot e registra no CRM próprio.

Follow-up: runner (cron) lê o CRM + conversas abertas e escreve
RASCUNHOS de toque em followup-drafts/ — nunca envia sozinho.
```

## Componentes

| Arquivo | O que faz | Não faz |
|---|---|---|
| `chatwoot_client.py` | Cliente mínimo da API (ler, etiquetar, atribuir, resolver, nota) | Não envia mensagem ao cliente — não existe função de envio aqui de propósito |
| `ignorados.py` + `ignorados.json` | Lista de empresas conhecidas (não clientes) | Não bloqueia/apaga/altera esses contatos |
| `listener.py` | Recebe o webhook `message_created`, dedupe, enfileira incoming, detecta handoff, expõe `/pending` e `/ack` | Não responde ninguém |
| `handoff.py` | `detectar_handoff(texto)` (puro, testável) + `aplicar_handoff(conversa, motivo)` (etiqueta + atribuição + nota) | Não envia mensagem ao cliente; nunca para ignorados |
| `followup.py` | Runner: lê CRM + conversas abertas, escreve rascunhos de toque | Nunca envia; nunca para ignorados, leads fechados ou sem follow-up vencido |
| `templates_followup.json` | Textos-modelo de follow-up (só entram em vigor após aprovação do usuário — ver `docs/followup-textos-modelo.md`) | — |
| `ana-listener.service` | Unit systemd do ouvinte | — |

## Contratos

- **Porta do ouvinte:** 3021 (a ponte Zernio usa a 3020). Deploy em
  `/home/pc/chatwoot/ana-listener/` (código espelhado do repo; o
  `listener.db` e os rascunhos vivem lá, fora do git).
- **Webhook da conta:** `POST /api/v1/accounts/2/webhooks`
  `{"url": "http://100.73.22.64:3021/webhooks/chatwoot",
  "subscriptions": ["message_created"]}`. Hoje não há webhook de
  conta (lista vazia, verificado 2026-11-21).
- **Fila (`listener.db`, tabela `events`):** `message_id` UNIQUE,
  `conversation_id`, `inbox_id`, `contato_ref`, `handoff` (motivo ou
  NULL), `recebido_em`, `estado` (`pendente`/`entregue`/`ignorado`).
  `GET /pending` devolve os `pendente` (limite 20); `POST /ack`
  `{"message_id": n}` (ou `{"message_ids": [...]}`) marca `entregue`.
  Quem marca `entregue` é o agente acordado pelo hook, depois de
  verificar e entregar o aviso. A vigília de 5 min continua como
  rede de segurança.
- **Humano do handoff:** agente id 2 (`tutibom`, administrador,
  tutibom10@gmail.com) — único agente da conta, verificado 2026-11-21.
- **Etiqueta de handoff:** `handoff-humano` (criada se não existir;
  hoje a conta não tem etiqueta nenhuma).
- **Nota privada:** `POST /conversations/:id/notes` NÃO existe no
  Chatwoot 4.20.1-ce (404, verificado 2026-11-21); a nota privada é
  `POST /conversations/:id/messages` com `private: true` — só
  agentes veem, nada é enviado ao contato.
- **CRM vivo:** `/home/pc/chatwoot/crm.sqlite3` (ainda não existe —
  criado no primeiro uso via `tuttibom.crm.store.CRM`; o banco de
  teste da V4, `/tmp/crm-v4.sqlite3`, não é o vivo). Bancos
  `.sqlite3` nunca vão para o git.
- **Regra de ignorados (usuário, 2026-11-21):** empresas conhecidas
  são canais de alerta, não clientes — sem resposta, sem lead, sem
  follow-up, sem handoff. Caso concreto: Mercado Livre
  +5511978832287, conversa 8 do Chatwoot (4ª mensagem idêntica de
  "Alerta de segurança", 22:33) — sem resposta, sem lead. Isso
  resolve na prática a P8.

## Regras duras

- Nada vai para Cursor/Agy. Não tocar no Deskcomm produção, no WAHA,
  nos webhooks do Zernio nem no `cloudflared-ponte`.
- Não tocar na conversa 8 nem no lead do golpe (P8) — a decisão sobre
  ele é do usuário e já está coberta pela regra de ignorados.
- Nenhum segredo em git, log ou chat. O PAT fica só no PC.
- Nenhum dado de comprador no repo: sem texto de mensagem de cliente
  em código, teste, log ou documento — só ids e contagens. Nos testes,
  usar textos fictícios.
- O ouvinte e o runner NUNCA enviam mensagem ao cliente.

## Testes

```bash
python3 -m unittest discover -s services/chatwoot-ana -p 'test_*.py' -v
```
