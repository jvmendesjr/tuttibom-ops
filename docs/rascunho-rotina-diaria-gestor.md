# Rotina diária do gestor — Deskcomm CRM (papel gerente, org tutibom)

**Status: APROVADA 2026-11-15** — os 5 pontos da §7 foram aprovados pelo usuário
(2026-11-15 ~18:39 UTC) e o agendamento foi criado (`gestor-varredura-0800/1400/2000`).
**Escopo unificado — Opção A APROVADA 2026-11-15** (ver §5).

> **RECONSTRUÍDO em 2026-11-16.** O arquivo original se perdeu numa sincronização
> entre a cópia local e o PC — não existia mais na cópia local, no PC
> (`/home/pc/Workspace/tuttibom-ops`) nem no GitHub (`main`, 404), e não tinha
> histórico no git do PC. O conteúdo abaixo foi refeito a partir da versão aprovada
> registrada em memória e na conversa: leitura integral do rascunho em 2026-11-15
> + alinhamento da Opção A (listas conferidas no catálogo do Deskcomm) + as
> correções dos passos 4 e 7. As decisões que governam as varreduras — escopo de
> 25 ferramentas, limiares de 3 e 7 dias, cadência 3×/dia, formato do relatório —
> estão todas aqui e foram conferidas contra essas fontes. Se algum trecho divergir
> do aprovado, corrija neste arquivo: ele é a referência das varreduras.

## §0 — O gestor é um papel, não um agente (agnosticismo)

- **O gestor externo é um papel, não um agente. O Muse é uma possibilidade — a
  primeira instância — não o gestor único.** O TuttiBom Ops é agnóstico quanto ao
  agente externo que opera via MCP.
- **Um token por agente, nunca compartilhado.** Dois agentes com o mesmo token são
  indistinguíveis na auditoria (o servidor só vê token + papel; `actor_api_token_id`
  distingue tokens, nunca nomes).
- **Um gestor ativo por vez.** O Deskcomm não impede dois gerentes ao mesmo tempo;
  a vez é regra nossa, senão dois gestores moveriam o mesmo lead.
- **Escopo e rotina valem para o papel.** Teto de 27, escopo enxuto da v1, críticas
  uma a uma e a rotina 3×/dia valem para o token do gestor, seja ele de quem for.
- **Trocar de agente = trocar token + agendamento, não reescrever a rotina.**
  Revogar o token antigo, emitir um novo com o mesmo escopo, trocar o agendamento.
- **Não confundir com a regra de delegação (2026-11-13):** "o Muse implementa tudo,
  nada vai para o Cursor/Agy até o usuário pedir" é sobre quem faz o trabalho hoje.
  Ela não faz do Muse o gestor único do MCP. As duas regras convivem.
- **Pacotes:** as ferramentas são agrupadas em 6 jornadas
  (`lib/mcp/tools/pacotes.ts`), porque 60+ ferramentas num prompt degradam a
  escolha do modelo. O humano liga pacotes; o detalhe por ferramenta existe em
  "modo avançado".
- **Teto por agente:** `TETO_TOOLS_POR_AGENTE` (hoje 27, corrigido 2026-11-15 — era
  25 no rascunho; ver `lib/mcp/tools/selecao-por-pacote.ts`). Um agente externo
  NUNCA vê as ~75 ferramentas de uma vez — no máximo 27.
- **Risco por ferramenta** (`seguro` / `atencao` / `critico`):
  - `seguro` (41): só consulta, nada muda.
  - `atencao` (25): altera dados, reversível pela tela.
  - `critico` (10): efeito que não dá para desfazer ou sai do sistema (falar com
    o cliente de verdade). **Nunca entra ligado por pacote** — exige marcação
    explícita do humano, uma a uma (`entraPorPacote` retorna falso para `critico`).

## §1 — O loop (3 partes)

A gestão depois da conversa se divide em três:

1. **O motor determinístico do Deskcomm, já rodando 24h** — scheduler/worker,
   fluxos de follow-up, varredura de silêncio (`lib/followup/silence-sweep.ts`),
   regras de automação e crons (`app/api/v1/cron/`: followup-flow-worker,
   case-stale-watcher, proposal-promised-not-created, kb-memoria-contato-batch).
2. **A varredura do gestor via MCP** — o trabalho de julgamento: ler casos, radar,
   follow-ups, funil e promessas, e propor (nunca aplicar o crítico).
3. **O usuário como checkpoint das decisões críticas.**

O modo de despacho continua `native` — em `external` a Ana pararia de atender.
O MCP sozinho não é um loop: é uma API sem estado (`POST /api/mcp`, Streamable
HTTP, Bearer `dsk_...`, papel/org do token, auditado por chamada).
As redes sociais ficam FORA do Deskcomm, no módulo TuttiBom OPS (o Muse operando
via Camofox; Zernio como ponte inicial do Messenger).

## §2 — Cadência

- **3 varreduras por dia, todos os dias da semana — 08:00, 14:00 e 20:00
  America/Fortaleza.** A das 08:00 pega a noite e a madrugada; a das 14:00 pega a
  manhã e os casos esperando gente no horário comercial; a das 20:00 pega a tarde e
  deixa rascunhos e propostas prontos para decidir na manhã seguinte.
- **Revisão semanal na sexta, junto com a varredura das 20:00** — propostas de
  melhoria, higiene de etiquetas/etapas e memória da org. Propor apenas, nunca
  aplicar.
- **Cada varredura relata só o que mudou desde a anterior.** Uma proposta aguardando
  aprovação NÃO volta como novidade sem fato novo; fica em "aguardando" até o
  usuário decidir ou surgir fato novo.
- **O relatório sai mesmo quando não há nada**, para provar que a varredura rodou:
  "nada em risco hoje, N leads abertos, M casos abertos" — nunca um genérico
  "tudo certo".
- **Entrega no chat principal**, sempre no formato Feito / Proposto para aprovar /
  Observado / Bloqueado.
- Se o volume crescer além de ~20 conversas ativas/dia, reavaliar antes de subir a
  frequência (um 4º horário, não varredura contínua).

## §3 — A varredura, em 8 passos e nesta ordem

### Passo 1 — Casos humanos abertos (do mais antigo para o mais novo)

Ler os casos abertos; nota em caso é permitida (`crm_add_case_note`). Fechar caso,
devolver o atendimento ao agente e atribuir conversa são propostas ou críticas —
nunca aplicados direto. Casos abertos há mais de 3 dias sem nota nova são
sinalizados como "parado".

Ferramentas: `crm_list_human_cases`, `crm_get_human_case`, `crm_add_case_note`,
`crm_list_available_attendants`, `crm_assign_conversation`.

### Passo 2 — Radar de risco

Quem esfriou, quem ficou sem próximo passo, retornos vencidos. Limiares na §6.

Ferramentas: `crm_list_at_risk_leads`, `crm_list_leads`, `crm_get_lead`,
`crm_get_conversation_history`.

### Passo 3 — Follow-ups

Cancelar os obsoletos; agendar retorno quando um "volto depois" claro encerrou a
conversa. Sem laço de reagendamento — volta ao passo 2. Regra de no máximo 3
toques em 2 dias para quem perguntou preço e sumiu.

Ferramentas: `crm_list_followups`, `crm_schedule_followup`,
`crm_enroll_followup_flow`, `crm_cancel_followup`.

### Passo 4 — Funil e promessas

Conferir os leads em "Vai levar" e "Aguardando pagamento" contra o histórico.
`crm_update_lead` e `crm_move_lead_stage` só quando o histórico prova — ex.:
pagamento confirmado pelo usuário vira "Pedido pago". Fechar como ganho é proposta,
só com pagamento confirmado pelo usuário, nunca por inferência.

Ferramentas: `crm_list_leads`, `crm_get_lead`, `crm_get_conversation_history`,
`crm_search_products`, `crm_update_lead`, `crm_move_lead_stage`.

> Nota: previsão de funil (`crm_list_pipelines`, `crm_get_pipeline_forecast`) está
> FORA da v1 — aguarda uma vaga livre. O passo 4 trabalha com leads e histórico.

### Passo 5 — Rascunhos

`crm_create_conversation_draft` deixa o texto exato para revisão humana — NUNCA
envia. Preço só do catálogo; frete nunca cotado com valor; endereço só depois de
venda fechada com pagamento confirmado.

Ferramentas: `crm_search_products`, `crm_create_conversation_draft`,
`crm_get_lead`, `crm_get_conversation_history`.

### Passo 6 — Etiquetas e etapas (higiene)

Aplicar/remover etiquetas quando o histórico prova — `fita`, `3d`, `preco`.
Criar/renomear/arquivar etapa está FORA da v1 (mudança estrutural, painel por
enquanto); propor no relatório.

Ferramentas: `crm_manage_tags`, `crm_list_tags`, `crm_list_stages`.

### Passo 7 — Memória da org

Ler a memória; padrões que se repetiram em 2+ conversas vão como proposta de
texto no relatório. Lacuna conhecida: a memória por contato (`contact_interests`)
NÃO tem ferramenta no MCP — a auditoria dela segue por leitura direta no banco ou
pelo turno da Ana, até existir ferramenta nova no Deskcomm.

Ferramentas: `crm_get_org_memory`.

> Nota: busca de conhecimento (`crm_search_knowledge`) e propostas de melhoria
> (`crm_list_improvement_proposals`) estão FORA da v1 — aguardam uma vaga livre.
> A revisão de melhorias de sexta aguarda uma vaga livre.

### Passo 8 — Relatório ao usuário

Sempre no formato **Feito / Proposto para aprovar / Observado / Bloqueado**, no
chat principal. Se nada mudou, dizer apenas que a varredura rodou e nada mudou,
com os números de base.

## §4 — O que a rotina nunca faz (v1)

- Enviar WhatsApp ou iniciar conversa com envio.
- Fechar demanda como ganho/perda sem aprovação (fechar é crítico — só proposta).
- Fechar caso humano ou devolver o atendimento ao agente sem aprovação.
- Arquivar etapa, criar contato automaticamente, ligar/desligar entradas ou regras
  de automação.
- Publicar versões de agente/fluxo, gerenciar roteadores ou tokens, criar produtos,
  configurar a org (nada disso existe no MCP).
- Tocar em dado de comprador fora do CRM, guardar dado de comprador no repo, ou
  agir fora da org tutibom.

## §5 — Escopo: as 25 ferramentas da Opção A

**25 de 27 ferramentas, ZERO críticas ligadas.** Escopo do papel, não do agente —
vale igual para qualquer agente que ocupar o papel depois, com um token próprio.
**2 vagas livres** para depois (ex.: `crm_create_stage` + `crm_update_stage`, se
organizar etapas passar a precisar de criação/renomeação pelo gestor).

### Leitura (14)

`crm_list_at_risk_leads`, `crm_list_leads`, `crm_get_lead`,
`crm_list_conversations`, `crm_get_conversation_history`, `crm_get_contact`,
`crm_list_followups`, `crm_list_human_cases`, `crm_get_human_case`,
`crm_list_stages`, `crm_list_tags`, `crm_get_org_memory`, `crm_search_products`,
`crm_list_available_attendants`.

### Atenção — reversíveis pela tela (11)

`crm_schedule_followup`, `crm_enroll_followup_flow`, `crm_cancel_followup`,
`crm_propose_reactivation`, `crm_update_lead`, `crm_move_lead_stage`,
`crm_manage_tags`, `crm_add_case_note`, `crm_create_conversation_draft`,
`crm_assign_conversation`, `crm_set_conversation_sector`.

### Fora da v1

`crm_search_contacts` (o contato chega pelo lead — nenhum passo usa),
`crm_save_org_memory` (a memória da org entra só como proposta de texto no
relatório; gravar depois usa uma vaga livre), `crm_list_pipelines`,
`crm_get_pipeline_forecast`, `crm_search_knowledge`,
`crm_list_improvement_proposals`, criar/renomear/arquivar etapa, ferramentas de
agenda, honorários, dados externos e todas as 10 críticas.

### Limite honesto

O servidor MCP **NÃO impõe** a lista de 25 nem o zero críticas — cada ferramenta
exige só papel + escopo, e as críticas exigem só papel de agente + `mcp:write`.
O escopo de 25 e o zero críticas são disciplina do cliente + checkpoint humano.
Por isso o token vai para o cofre, um por agente, e é revogado se vazar ou na
troca de gestor.

## §6 — Limiares do radar de risco

- Silêncio < 24h → nada (o Fluxo A age).
- Silêncio de 24h a 3 dias, sem inscrição em fluxo → inscrever no fluxo
  (`crm_enroll_followup_flow`) ou agendar retorno (`crm_schedule_followup`).
- Silêncio > 3 dias após a msg2 do Fluxo A, sem resposta → propor reativação
  (`crm_propose_reactivation` — só sugere, nunca envia).
- Silêncio > 7 dias, sem resposta a nenhuma tentativa → propor fechar como perdido,
  motivo `sem resposta` (`crm_close_demand`, crítico — só proposta).
- Nunca fechar no dia em que a pessoa respondeu; nunca fechar lead em "Aguardando
  pagamento" sem conferir o passo 4.

> Aviso (aprendido 2026-11-15, P1–P6): o motivo "sem resposta" foi recusado pelo
> banco no funil Pedidos — ele só aceita os códigos canônicos. No funil Pedidos
> vale `no_response`; no funil Vendas vale `sem resposta`. Conferir o funil antes
> de propor o motivo.

## §7 — Pontos confirmados (APROVADOS 2026-11-15)

1. **Cadência:** 3 varreduras por dia, todos os dias, às 08:00, 14:00 e 20:00,
   com relatório no chat principal.
2. **Limiares:** 3 dias para propor reativação; 7 dias para propor encerrar como
   perdido.
3. **`crm_move_lead_stage` automático quando o histórico prova** (ex.: pagamento
   confirmado pelo usuário vira "Pedido pago").
4. **`crm_save_org_memory` fora da v1** — a memória da org entra só como proposta
   de texto no relatório; gravar depois usa uma vaga livre.
5. **Token emitido com este escopo e agendamento criado** — token "Agente Externo 3",
   ativo; agendamento 3×/dia criado e ativo.

## §8 — Primeira prova (FEITA 2026-11-15)

A primeira varredura rodada como prova supervisionada, só leitura, em
2026-11-15 ~20:15: 0 casos humanos abertos; 14 leads open em "Carrinho
abandonado", sem follow-up e sem tags; memória da org vazia. Nada foi enviado,
nada foi fechado; as propostas P1–P6 foram aplicadas depois, com aprovação do
usuário (14 leads encerrados como perdido — 13 com `no_response`, 1 spam com
`other`; verificado: 0 leads open). A P7 (marcadores `fita`/`3d`/`preco`) foi
fechada em 2026-11-16 ~09:07, verificada via `crm_list_tags` (11 tags oficiais).

O estado de cada varredura fica em `docs/mcp-ultima-varredura.json` (data/hora,
casos abertos, leads por etapa/status/última atividade, follow-ups, propostas
pendentes com status). Cada varredura lê esse arquivo ANTES de varrer e relata
só o que mudou desde ele.

## §9 — Saúde do sistema (roadmap, a discutir depois)

Ação do agente FORA do Deskcomm, mas relacionada a ele: disponibilidade dos
modelos, 9Router, alertas de saúde/riscos, disco, RAM, CPU, tokens TypeSafe/Jev.
Escopo, cadência, limiares e para quem alertar NÃO estão decididos. Não entra na
rotina v1, porque o MCP não tem ferramenta de saúde — essa verificação é por SSH
ao PC, com outro agendamento. Item 8 do roadmap.

## Observações

- **Ana 24/7 (user, 2026-11-15) — a conferir:** produção e atendimento humano são
  em horário comercial, mas a Ana atende 24/7. O padrão do Deskcomm é janela de
  resposta 7–22h (`PACING_DEFAULTS`), fora dela o turno era agendado para as
  07:00 (observado 2026-11-06/07). Para o 24/7 valer de fato, falta confirmar ou
  mudar a janela da tutibom. As 3 varreduras funcionam nos dois casos, e a das
  08:00 pega o que foi adiado para as 07:00.
