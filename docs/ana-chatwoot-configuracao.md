# Configuração da Ana no Chatwoot — ouvinte, follow-up e handoff

**Vertente:** nova (D-012/D-013) · **Data:** 2026-11-21 · **Status:**
implementado e verificado; teste vivo com mensagem real pendente.
**Código:** `services/chatwoot-ana/` (branch `exp/crm-proprio`).
**Docs relacionados:** `skills/chatwoot-operacao/SKILL.md` (mecânica),
`skills/ana-atendimento/SKILL.md` (comportamento — outro branch,
`exp/atendimento-ana`), `docs/followup-textos-modelo.md` (textos para
aprovação), `docs/roadmap-nova-vertente.md` (V5).

## O problema que isto resolve

A V4 provou o atendimento, mas com latência de 11–16 min por turno
(meta 1–2 min), estrutural do polling de 5 min + navegação no painel.
Este pacote troca o polling pelo webhook do Chatwoot e liga as duas
automaçães que faltavam: follow-up e handoff.

## Arquitetura (o que existe agora)

```
WhatsApp (WAHA) ─┐
                 ├─► Chatwoot (conta 2) ── webhook message_created ──► ana-listener :3021
Messenger (Zernio)┘         │                                        (fila + handoff)
                            │   GET /pending (hook, a cada 60 s)
                            │         ▲
                            └─────────┘  (o hook acorda o Muse, que responde como Ana)
Muse responde como Ana via API do Chatwoot e registra no CRM próprio.
Follow-up: runner a cada 2 h escreve RASCUNHOS — nunca envia sozinho.
```

| Peça | Onde vive | Estado |
|---|---|---|
| `ana-listener` (ouvinte) | PC, `/home/pc/chatwoot/ana-listener/`, systemd, porta 3021 | `active`, `/health` 200 |
| Webhook de conta | Chatwoot, id 1, `http://100.73.22.64:3021/webhooks/chatwoot`, `message_created` | registrado 2026-11-21 |
| Hook `chatwoot-ana-watch` | runtime, `~/hooks/scripts/chatwoot-ana-watch.sh`, poll 60 s | habilitado 2026-11-21 |
| Cron `chatwoot-followup-ana` | runtime, a cada 2 h, dono `goal:crm-pr-prio-e-atendimento-pelo-muse` | criado 2026-11-21 |
| Runner `followup.py` | `services/chatwoot-ana/`, rascunhos em `/home/pc/chatwoot/ana-listener/followup-drafts/` | pronto, modo propor-primeiro |
| Handoff | `services/chatwoot-ana/handoff.py` (detecção + ação) | verificado na API real |
| Vigília `chatwoot-watch-ana` (5 min) | runtime | mantida como rede de segurança |

## 1. Ouvinte de webhook

- Recebe `message_created` do Chatwoot (formato de conta e de inbox),
  dedupe por id da mensagem, só processa `incoming`.
- Fila em `listener.db` (tabela `events`): `pendente` → `entregue`
  (via `POST /ack`, feito pelo agente acordado) ou `ignorado`.
- `GET /pending`, `POST /ack`, `GET /health`, `GET /stats`.
- Nunca responde ninguém, nunca loga texto de cliente (só ids).
- O Chatwoot gerou um secret para o webhook; verificação de
  assinatura **não** implementada nesta versão — o endpoint só existe
  na tailnet (mesmo critério da ponte com secret vazio). Seguir depois
  se o usuário quiser.
- Se o `handoff.py` mudar no disco, reiniciar:
  `sudo systemctl restart ana-listener` (o ouvinte importa o módulo
  uma vez e guarda em cache).

## 2. Hook (acordar na hora)

- `chatwoot-ana-watch`, poll a cada 60 s: consulta `/pending` via
  `ssh` (a VM não alcança a tailnet por HTTP direto) e acorda o
  agente quando há ids novos. Estado em
  `~/hooks/state/chatwoot-ana/seen-ids.txt`; dry-run não consome.
- Ciclo provado: `silent` (fila vazia) → `wake` (evento falso) →
  `wake` de novo (dry-run não consome) → `ack` → `silent`.
- O worker acordado verifica o evento na API, reporta neste chat
  (conversa, inbox, contato, texto, hora), dá `/ack` e o Muse
  responde como Ana. Teste vivo com mensagem real de cliente ainda
  pendente (o usuário envia "Olá" no WhatsApp; o hook deve acordar
  em ~60 s).
- Latência esperada: detecção ~1 min + tempo de resposta do Muse
  (meta total 1–2 min, contra 11–16 min da V4).

## 3. Follow-up automático (propor-primeiro)

- Runner `followup.py` a cada 2 h (cron `chatwoot-followup-ana`):
  lê CRM + conversas abertas, escreve rascunhos JSON, **nunca envia**.
- Teto: máx. 3 toques em 2 dias por lead (contagem oficial: follow-up
  marcado `enviado` no CRM — quem enviar o rascunho marca com
  `CRM.marcar_followup`); pagamento tem 1 toque só.
- Cancelar-ao-responder: inbound após o agendamento cancela o
  follow-up e o rascunho não é gerado.
- Textos-modelo e cadência (12 h / 24 h / 40 h) em
  `docs/followup-textos-modelo.md` — **aguardam aprovação do usuário**;
  a aprovação é pré-condição do envio, não do rascunho.
- CRM vivo: `/home/pc/chatwoot/crm.sqlite3` (ainda não existe — criado
  no primeiro uso via classe CRM). Convenção: o `contato_ref` do lead
  precisa conter o identifier exato ou os dígitos do telefone, senão
  o runner não acha a conversa (ver docstring do `followup.py`).

## 4. Handoff humano

- Humano: agente id 2 (`tutibom`, administrador, tutibom10@gmail.com),
  único agente da conta.
- Detecção determinística (`detectar_handoff`): humano-explicito,
  amostra-física, suspeita-golpe, pós-venda. Sentimento negativo,
  "não sei responder", fora de escopo genérico e assunto sensível
  ficam para o julgamento do agente — sem adivinhação por palavra-chave.
- Ação (`aplicar_handoff`): etiqueta `handoff-humano` (id 1, criada
  2026-11-21) + atribuição ao `tutibom` + nota privada com motivo e
  hora. Verificado na conversa 6 (atribuição desfeita depois).
- Descoberta: o endpoint `/notes` dá 404 no Chatwoot 4.20.1-ce; nota
  privada é `POST /messages` com `private: true` (corrigido no
  `chatwoot_client.py`).
- A Ana nunca diz que vai transferir para um humano nem que é
  robô/virtual — ao passar, diz com naturalidade que o assunto cabe
  ao produtor/equipe no horário comercial.

## 5. Empresas conhecidas — IGNORAR (regra do usuário, 2026-11-21)

Contatos de empresas conhecidas são canais de comunicação e alerta,
NÃO clientes: sem resposta, sem lead, sem follow-up, sem handoff.
Vale para o ouvinte, o runner, o handoff e a vigília (que marca como
vista e segue em silêncio).

- Lista: `services/chatwoot-ana/ignorados.json` (hoje: Mercado Livre
  +5511978832287, identifier `eab057e8-...`). Para acrescentar uma
  empresa: telefone (E.164) e/ou identifier no JSON + reiniciar o
  `ana-listener`. Nunca bloquear, apagar ou alterar esses contatos —
  o do Mercado Livre também é usado por outra operação do usuário.
- Caso concreto: conversa 8 do Chatwoot, 4ª mensagem idêntica de
  "Alerta de segurança" (22:33) — sem resposta, sem lead. Isso resolve
  na prática a P8.

## Verificação feita (2026-11-21)

- Testes: `python3 -m unittest discover -s services/chatwoot-ana` →
  **35/35 OK** (10 ouvinte + 15 handoff + 10 follow-up).
- Ouvinte ao vivo: `/health` 200; incoming falso enfileirado;
  duplicado descartado; ignorado fora do `/pending`; `/ack` marca
  entregue; `zernio-bridge` segue `active`.
- Handoff ao vivo: etiqueta criada, atribuição confirmada por GET e
  desfeita, nota privada criada; nada enviado ao cliente; conversa 8
  não tocada.
- Follow-up ao vivo: contra o CRM da V4, `sem-rascunhos` e banco
  intacto (md5 idêntico); caminho completo com CRM de rascunho gerou
  o rascunho do toque 1 para a conversa 6 e nenhum para a 8.

## Pendente

1. **Teste vivo com mensagem real** (usuário envia "Olá" no WhatsApp):
   o hook deve acordar em ~60 s e a resposta da Ana deve chegar no
   canal. Sem ele, a latência de 1–2 min é projetada, não provada.
2. **Aprovação do usuário:** os 4 textos-modelo de follow-up, a
   cadência (12 h / 24 h / 40 h) e a convenção de contagem do teto
   (`enviado` como registro oficial). Sem isso, nada é enviado.
3. **Skill da Ana:** registrar a regra de ignorados em
   `skills/ana-atendimento/SKILL.md` (branch `exp/atendimento-ana`) —
   aqui só a mecânica foi atualizada (`chatwoot-operacao`).
4. **Opcional:** verificação de assinatura do webhook de conta
   (secret gerado pelo Chatwoot, valor nunca registrado em chat ou
   arquivo).
5. **Depois que o hook provar:** avaliar desligar a vigília de 5 min
   (`chatwoot-watch-ana`) — por enquanto ela fica como rede de
   segurança.
