# Configuração da Ana no Chatwoot — ouvinte, follow-up e handoff

**Vertente:** nova (D-012/D-013) · **Data:** 2026-11-21 · **Status:**
implementado e verificado; teste vivo do hook PROVADO 2026-11-21
23:31 ("Olá" 23:02 → resposta da Ana 23:07, recebimento confirmado
no telefone; 4 min 23 s, acima da meta de 1–2 min).
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
| Webhook de conta | Chatwoot, id 1, `http://<TAILSCALE_IP>:3021/webhooks/chatwoot`, `message_created` | registrado 2026-11-21 |
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

### Cumprimento automático (ack de 10 s, aprovado 2026-11-21 23:45; pausa de 2h, decisão 2026-11-22)

Preliminar antes da resposta da Ana: na abertura da conversa o
ouvinte agenda um cumprimento fixo para **10 s depois** da primeira
mensagem (timer fixo, não deslizante — uma segunda mensagem na
janela não adia). Os 10 s dão tempo de a pessoa terminar a rajada e
parecem humanos; instantâneo demais pareceria robô. O envio NÃO
atrasa o 200 ao Chatwoot nem o enfileiramento.

- **Quando dispara:** incoming, contato não ignorado, e nenhum
  cumprimento para a conversa nos últimos 10 min (máx. 1x a cada
  10 min — guarda rápida contra timers duplicados). Aos 10 s, antes
  de enviar, o ouvinte reavalia: se houve qualquer mensagem real
  (incoming ou outgoing) nas 2h antes do início da rajada,
  SUPRIME — é a pausa de 2h (decisão do usuário 2026-11-22):
  depois da primeira vez, o cumprimento só dispara de novo numa
  abertura nova (primeira mensagem da conversa ou última atividade
  há mais de 2h). Dispara mesmo quando há handoff.
- **Nunca em grupo (trava geral, decisão do usuário 2026-11-22):**
  identifier ou contato_ref terminando em `@g.us` pula o
  agendamento antes do timer — cliente é sempre conversa
  individual. A mensagem segue enfileirada; a lista de ignorados
  continua como segunda camada. Motivo: o cumprimento disparou
  para o grupo GrupoPromocional #01 às 00:03:20 de 2026-11-22
  porque o grupo ainda não estava na lista (o cheque de ignorados
  já acontecia antes do timer — confirmado no código e no log; a
  msg 33 é o próprio cumprimento enviado, não uma segunda
  violação).
- **Textos (dois pools, detecção determinística, sem LLM):**
  saudação pelo horário real (America/Fortaleza: 06–12 "Bom dia",
  12–18 "Boa tarde", 18–06 "Boa noite") + pedido cordial de espera.
  Saudação fechada (só saudação, sem pedido) usa o pool SEM
  "verificar" ("Só um instante que já te atendo." / "Ok, só um
  instante." / "Já te atendo."); com pedido/pergunta usa o pool COM
  "verificar" ("Vou verificar aqui e já te respondo." / "Só um
  instante que já te respondo." / "Ok, vou verificar e já te
  chamo."). Correção do usuário (23:46): "verificar" só cabe quando
  a pessoa já pediu alguma informação.
- **Rajada:** aos 10 s o ouvinte classifica a rajada INTEIRA da
  janela, não só a última mensagem: basta UM pedido na janela para
  usar o pool de pedido ("oi" + "quanto custa" + "oi?" → pedido).
  Só usa o pool sem "verificar" se TODAS as mensagens da janela
  forem saudação fechada.
- **Rotação:** nunca repete a mesma variante duas vezes em sequência
  por conversa (última variante guardada em `listener.db`).
- **O agente sabe:** o cumprimento aparece na conversa como mensagem
  da Ana, é registrado em `listener.db` (tabela `cumprimentos`) e
  vem no item do `GET /pending` (campo `cumprimento`: texto +
  `enviado_em`); `/stats` conta os cumprimentos.
- **Falha nunca bloqueia:** se a leitura da API falhar, só envia
  se a conversa nunca recebeu cumprimento (estado local — não dá
  para provar 2h de silêncio sem a API); se já houve cumprimento,
  suprime. O texto, sem a API, vem só do que disparou o timer.
  Se o envio falhar, só loga e a mensagem segue enfileirada para
  o Muse.
- **Único envio do serviço:** `chatwoot_client.enviar_cumprimento`
  (só textos fixos, nunca texto livre). O resto do serviço continua
  sem enviar nada.

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
  `docs/followup-textos-modelo.md` — **APROVADOS pelo usuário em
  2026-11-21 23:02** (commit `54f2703`), junto com a convenção de
  contagem do teto (`enviado` como registro oficial). O envio passa
  a valer, sempre com revisão do rascunho pelo Muse, como Ana,
  antes de enviar.
- CRM vivo: `/home/pc/chatwoot/crm.sqlite3` (ainda não existe — criado
  no primeiro uso via classe CRM). Convenção: o `contato_ref` do lead
  precisa conter o identifier exato ou os dígitos do telefone, senão
  o runner não acha a conversa (ver docstring do `followup.py`).

## 4. Handoff humano

- Humano: agente id 2 (`tutibom`, administrador, <EMAIL_OPERACIONAL_LOJA>),
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
  <TELEFONE_SINTETICO>, identifier `eab057e8-...`). Para acrescentar uma
  empresa: telefone (E.164) e/ou identifier no JSON + reiniciar o
  `ana-listener`. Nunca bloquear, apagar ou alterar esses contatos —
  o do Mercado Livre também é usado por outra operação do usuário.
- Caso concreto: conversa 8 do Chatwoot, 4ª mensagem idêntica de
  "Alerta de segurança" (22:33) — sem resposta, sem lead. Isso resolve
  na prática a P8.

## 6. Dashboard do CRM — só leitura (decisão do usuário, 2026-11-22)

Página do CRM próprio para embutir no painel do Chatwoot (dashboard
app, iframe): leads agrupados pelas 7 etapas do funil, com produto/SKU
(+ preço), interesse, próxima ação, follow-up, resumos de mensagens e
memória do contato — mais o catálogo (18 produtos) e os follow-ups
pendentes. Serviço `services/crm-dashboard/` (só stdlib), porta 3022,
unit `crm-dashboard.service`, deploy em `/home/pc/chatwoot/crm-dashboard/`.

- **Só leitura:** nenhum botão nem endpoint de escrita; o SQLite é
  aberto sempre em modo read-only (`mode=ro`).
- **Auth por token na URL:** `GET /?token=<TOKEN>`; sem token ou token
  errado → 401. O token vive SÓ no `.env` do deploy (chmod 600, fora
  do git); o serviço se recusa a subir sem ele. `GET /health` é
  aberto, sem token. Quem tiver a URL completa vê o CRM — por isso o
  token é longo/aleatório e a URL só vive no `.env` e no registro do
  dashboard app no Chatwoot. Para trocar: novo token no `.env` +
  atualizar a URL no Chatwoot + `sudo systemctl restart crm-dashboard`.
- Detalhe em `services/crm-dashboard/README.md`.

## Verificação feita (2026-11-21)

- Testes: `python3 -m unittest discover -s services/chatwoot-ana` →
  **61/61 OK** (36 ouvinte — inclui 26 do cumprimento automático
  com atraso de 10 s, rajada e pausa de 2h — + 15 handoff + 10
  follow-up). Versão 0.5.0 (pausa de 2h, 2026-11-22).
- Ouvinte ao vivo: `/health` 200; incoming falso enfileirado;
  duplicado descartado; ignorado fora do `/pending`; `/ack` marca
  entregue; `zernio-bridge` segue `active`.
- Cumprimento ao vivo (2026-11-21 ~23:54, evento falso): enfileirado
  com `cumprimento: null`, ack imediato, timer disparou 11 s depois
  e o envio para a conversa inexistente falhou com log
  (`cumprimento nao enviado`), sem derrubar o enfileiramento;
  `/stats` com `cumprimentos: 0`, fila vazia, serviço `active`.
  Teste vivo com o usuário (cumprimento real no telefone) pendente.
- Handoff ao vivo: etiqueta criada, atribuição confirmada por GET e
  desfeita, nota privada criada; nada enviado ao cliente; conversa 8
  não tocada.
- Follow-up ao vivo: contra o CRM da V4, `sem-rascunhos` e banco
  intacto (md5 idêntico); caminho completo com CRM de rascunho gerou
  o rascunho do toque 1 para a conversa 6 e nenhum para a 8.

## Pendente

1. **Teste vivo do cumprimento com o usuário** (manda "Olá" no
   WhatsApp): o cumprimento deve chegar em ~10 s e a resposta da
   Ana depois. Sem ele, o envio real do cumprimento é projetado,
   não provado.
2. **Teste vivo do hook — PROVADO 2026-11-21 23:31:** o usuário
   mandou "Olá" 23:02:39, o hook acordou, a Ana respondeu 23:07:02
   e o recebimento foi confirmado no telefone às 23:31. Latência
   4 min 23 s — acima da meta de 1–2 min; o gargalo foi o acordar,
   não a resposta.
3. **Skill da Ana:** registrar a regra de ignorados em
   `skills/ana-atendimento/SKILL.md` (branch `exp/atendimento-ana`) —
   aqui só a mecânica foi atualizada (`chatwoot-operacao`).
4. **Opcional:** verificação de assinatura do webhook de conta
   (secret gerado pelo Chatwoot, valor nunca registrado em chat ou
   arquivo).
5. **Depois que o hook provar:** avaliar desligar a vigília de 5 min
   (`chatwoot-watch-ana`) — por enquanto ela fica como rede de
   segurança.
