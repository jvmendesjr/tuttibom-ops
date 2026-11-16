# Rascunho — funções do agente externo via MCP (revisão)

Data: 2026-11-14. Levantamento direto do código do DeskcommCRM
(`lib/mcp/tools/`, catálogo em `lib/mcp/tools/catalogo/`).

## Como funciona

- **Endpoint:** `app/api/mcp/route.ts`. Qualquer agente com cliente MCP
  se conecta; o servidor não distingue qual agente é — só o token e o papel.
- **Autenticação:** token bearer `dsk_<prefixo>_<segredo>`, hash SHA256,
  tabela `api_tokens`, com papéis (`role:*`, inclui "gerente").
- **Checagem por ferramenta:** o servidor verifica papel + escopo em cada
  chamada (`ensureRole`). Auditoria existe (`lib/mcp/audit.ts`).
- **Pacotes:** as ferramentas são agrupadas em 6 jornadas
  (`lib/mcp/tools/pacotes.ts`), porque 60+ ferramentas num prompt degradam
  a escolha do modelo. O humano liga pacotes; o detalhe por ferramenta
  existe em "modo avançado".
- **Teto por agente:** `TETO_TOOLS_POR_AGENTE` (hoje 25; já foi 20). Um
  agente externo NUNCA vê as ~75 ferramentas de uma vez — no máximo 25.
- **Risco por ferramenta** (`seguro` / `atencao` / `critico`):
  - `seguro` (40): só consulta, nada muda.
  - `atencao` (25): altera dados, reversível pela tela.
  - `critico` (10): efeito que não dá para desfazer ou sai do sistema
    (falar com o cliente de verdade). **Nunca entra ligado por pacote** —
    exige marcação explícita do humano, uma a uma
    (`entraPorPacote` retorna falso para `critico`).

## Inventário por pacote (75 ferramentas)

### 1. Atender e responder (`atender`)

Lê a conversa, entende o histórico e responde ao cliente.

| Ferramenta | Risco | O que faz |
|---|---|---|
| crm_search_contacts | seguro | Procurar cliente por nome/telefone/e-mail |
| crm_get_contact | seguro | Ver ficha do cliente (CPF sempre mascarado) |
| crm_list_conversations | seguro | Listar conversas (com preview da última msg) |
| crm_get_conversation | seguro | Ver uma conversa (status, atribuição) |
| crm_get_conversation_history | seguro | Ler o histórico de mensagens |
| crm_list_contact_orders | seguro | Ver as compras do cliente |
| crm_search_products | seguro | Procurar produto: preço exato, disponibilidade, código |
| crm_list_privacy_requests | seguro | Ver pedidos de privacidade (LGPD) |
| crm_list_available_attendants | seguro | Ver quem pode assumir agora |
| crm_search_knowledge | seguro | Consultar o que a empresa já sabe (RAG) |
| crm_get_org_memory | seguro | Consultar regras e combinados da empresa |
| crm_get_queue_status | seguro | Ver a fila de atendimento |
| crm_list_honorarios_parcelas | seguro | Ver parcelas de honorários |
| crm_get_honorarios_contrato | seguro | Ver contrato de honorários do caso |
| crm_list_stages | seguro | Ver as etapas de um funil |
| crm_list_tags | seguro | Ver os marcadores em uso |
| crm_list_message_templates | seguro | Ver as respostas prontas |
| crm_render_message_template | seguro | Preencher uma resposta pronta (não envia) |
| crm_assign_conversation | atencao | Direcionar conversa para alguém |
| crm_manage_tags | atencao | Aplicar/remover marcadores |
| crm_set_conversation_sector | atencao | Colocar a conversa num setor (fila) |
| crm_send_whatsapp_message | **critico** | **Enviar mensagem no WhatsApp** (idempotency_key, TTL 24h) |

### 2. Vender e mover o funil (`vender`)

Registra a oportunidade, atualiza o negócio, move de etapa.

| Ferramenta | Risco | O que faz |
|---|---|---|
| crm_list_event_types | seguro | Ver o que a empresa atende |
| crm_find_free_slots | seguro | Ver horários livres na agenda |
| crm_list_appointments | seguro | Ver os compromissos marcados |
| crm_search_contacts | seguro | (idem pacote atender) |
| crm_get_contact | seguro | (idem) |
| crm_list_contact_orders | seguro | (idem) |
| crm_search_products | seguro | (idem) |
| crm_preparar_proposta | seguro | Preparar a proposta com o cliente |
| crm_list_leads | seguro | Listar oportunidades do funil |
| crm_get_lead | seguro | Ver uma oportunidade |
| crm_list_pipelines | seguro | Listar funis |
| crm_list_stages | seguro | (idem) |
| crm_find_and_book_appointment | atencao | Ver se o horário está livre e já marcar |
| crm_book_appointment | atencao | Marcar consulta/sessão |
| crm_reschedule_appointment | atencao | Remarcar um compromisso |
| crm_confirm_appointment | atencao | Confirmar um horário combinado |
| crm_set_appointment_outcome | atencao | Registrar comparecimento/falta |
| crm_draft_proposal | atencao | Rascunhar proposta comercial |
| crm_propose_contact_field | atencao | Anotar dado que o cliente informou (como proposta) |
| crm_create_lead | atencao | Criar oportunidade no funil |
| crm_update_lead | atencao | Atualizar uma oportunidade |
| crm_move_lead_stage | atencao | Mover oportunidade de etapa |
| crm_cancel_appointment | **critico** | **Desmarcar um compromisso** (libera o horário) |
| crm_start_conversation_and_send | **critico** | **Iniciar conversa com cliente novo e enviar mensagem** |

### 3. Não perder o cliente (`reter`)

Agenda retornos e acompanha quem esfriou.

| Ferramenta | Risco | O que faz |
|---|---|---|
| crm_list_followups | seguro | Ver os retornos de um cliente |
| crm_list_at_risk_leads | seguro | Ver quem esfriou / sem próximo passo |
| crm_get_prospecting_site_audit | seguro | Consultar análise do site da empresa prospectada |
| crm_schedule_followup | atencao | Agendar um retorno para o cliente |
| crm_enroll_followup_flow | atencao | Inscrever o cliente num acompanhamento (fluxo) |
| crm_cancel_followup | atencao | Cancelar um retorno agendado |
| crm_propose_reactivation | atencao | Sugerir retomar contato com quem sumiu |
| crm_retomar_lead | atencao | Retomar negócio encerrado como novo |
| crm_propose_lead_fields_from_document | atencao | Propor dados de um documento para o card |
| crm_close_demand | **critico** | **Encerrar o negócio como ganho ou perdido** |

### 4. Passar para um humano (`escalar`)

Reconhece quando não é o caso dele, chama uma pessoa.

| Ferramenta | Risco | O que faz |
|---|---|---|
| crm_list_available_attendants | seguro | (idem) |
| crm_list_human_cases | seguro | Ver os chamados em aberto |
| crm_get_human_case | seguro | Ler um chamado e o que a pessoa decidiu |
| crm_list_conversations | seguro | (idem) |
| crm_get_conversation | seguro | (idem) |
| crm_get_queue_status | seguro | (idem) |
| crm_list_team_members | seguro | Ver quem trabalha na empresa |
| crm_add_case_note | atencao | Registrar o que aconteceu num chamado |
| crm_assign_conversation | atencao | (idem) |
| crm_set_conversation_sector | atencao | (idem) |
| crm_create_conversation_draft | atencao | Deixar texto sugerido para a pessoa revisar (não envia) |
| crm_request_human_handoff | atencao | Chamar um atendente humano |
| crm_close_human_case | **critico** | **Encerrar um chamado com o desfecho** |
| crm_resume_ai_attendance | **critico** | **Devolver o atendimento ao agente** (solta o dono humano) |

### 5. Organizar a operação (`organizar`)

Mantém a casa em ordem: marcadores, etapas, avisos, distribuição.

| Ferramenta | Risco | O que faz |
|---|---|---|
| crm_list_privacy_requests | seguro | (idem) |
| crm_query_external_data | seguro | Buscar dados no banco conectado |
| crm_describe_external_data | seguro | Ver as tabelas do banco conectado |
| crm_get_pipeline_forecast | seguro | Ver a previsão do funil |
| crm_list_pipelines | seguro | (idem) |
| crm_list_stages | seguro | (idem) |
| crm_list_tags | seguro | (idem) |
| crm_list_message_templates | seguro | (idem) |
| crm_render_message_template | seguro | (idem) |
| crm_list_webhook_sources | seguro | Ver as entradas automáticas de contatos |
| crm_list_webhook_source_events | seguro | Ver o que chegou por uma entrada |
| crm_list_automation_rules | seguro | Ver as regras automáticas |
| crm_list_automation_runs | seguro | Ver o que as regras dispararam |
| crm_list_team_members | seguro | (idem) |
| crm_consultar_receita | seguro | Consultar receitas prontas do banco conectado |
| crm_manage_tags | atencao | (idem) |
| crm_create_stage | atencao | Criar etapa no funil |
| crm_update_stage | atencao | Renomear/reordenar etapa |
| crm_archive_stage | **critico** | **Arquivar uma etapa do funil** |
| crm_create_webhook_source | **critico** | **Criar uma entrada automática de contatos** |
| crm_set_webhook_source_active | **critico** | **Ligar/desligar uma entrada de contatos** |
| crm_set_automation_rule_active | **critico** | **Ligar/desligar uma regra automática** |

### 6. Aprender e evoluir (`evoluir`)

Consulta o que a empresa já sabe, aprende, sugere melhorias.

| Ferramenta | Risco | O que faz |
|---|---|---|
| crm_search_knowledge | seguro | (idem) |
| crm_list_knowledge_sources | seguro | Ver os materiais cadastrados |
| crm_list_improvement_proposals | seguro | Ver sugestões de melhoria |
| crm_get_org_memory | seguro | (idem) |
| crm_save_org_memory | atencao | Anotar uma regra aprendida (vale p/ toda a operação) |

## As 10 críticas (exigem marcação explícita do humano, uma a uma)

1. `crm_send_whatsapp_message` — enviar mensagem no WhatsApp
2. `crm_start_conversation_and_send` — iniciar conversa e enviar
3. `crm_cancel_appointment` — desmarcar compromisso
4. `crm_close_demand` — encerrar negócio como ganho/perdido
5. `crm_close_human_case` — encerrar chamado
6. `crm_resume_ai_attendance` — devolver atendimento ao agente
7. `crm_archive_stage` — arquivar etapa do funil
8. `crm_create_webhook_source` — criar entrada automática de contatos
9. `crm_set_webhook_source_active` — ligar/desligar entrada de contatos
10. `crm_set_automation_rule_active` — ligar/desligar regra automática

## O que NÃO existe no MCP (lacunas para o gestor)

- Publicar versão de agente (Ana) ou de fluxo (Fluxo A/B) — hoje é clique
  humano no painel.
- Gerenciar roteadores (criar/alterar membros, ligar/desligar).
- Gerenciar os próprios tokens MCP (criar/revogar token de outro agente).
- Criar/editar produtos no catálogo (só busca: `crm_search_products`).
- Configurar a organização (setores, funis além de etapas, canais).
- Ler/escrever a memória por contato (`contact_interests`) — não há
  ferramenta; a memória é lida pelo turno, não pelo agente externo.

## Leitura para o TuttiBom (loja, sem agendamento)

- **Agendamento (9 ferramentas) não serve para a loja** — decisão
  registrada: a loja não tem agendamento, só follow-ups. O pacote
  `vender` carrega essas 9 junto; ligar `vender` inteiro gasta o teto
  com coisa que a loja não usa.
- **Honorários (2 ferramentas) é de escritório de advocacia** — fora do
  contexto da loja.
- **Dados externos / receitas (3 ferramentas)** exigem um banco externo
  conectado — a loja não tem.
- **O núcleo útil para o gestor da loja:** `atender` (ler + responder),
  `vender` sem a parte de agenda (leads, produtos, pedidos),
  `reter` (follow-ups, risco) e `escalar` (handoff, chamados).
- **Atenção ao teto:** só o pacote `atender` já exige 18 vagas das 25.
  Ligar `atender` + `vender` + `reter` + `escalar` inteiros estoura o
  teto — o gestor da loja precisa de uma seleção enxuta, não dos
  pacotes inteiros.

## Próximo passo (a decidir com o usuário)

1. Definir o escopo do gestor da loja: quais pacotes e quais das 10
   críticas ficam ligadas (ex.: enviar WhatsApp é o coração do gestor;
   arquivar etapa e ligar regra automática provavelmente não).
2. Confirmar o papel do token ("gerente") e a auditoria por agente.
3. Emitir o primeiro token (Muse, primeiro gestor) e provar com uma
   tarefa real de gestão.

## Correção: o catálogo é da Ana também (não só do agente externo)

Levantado 2026-11-14, a partir da pergunta do usuário: as funções NÃO
são só do agente externo. O catálogo (`lib/mcp/tools/catalogo/`) é o
vocabulário único de capacidades da plataforma, com DOIS consumidores:

- **Agente interno (Ana):** o motor monta as ferramentas do turno a
  partir do mesmo catálogo (`lib/agent-engine/edge/crm/mcp-tools.ts`,
  `buildMcpTurnTools`), com duas subtrações:
  - **Harness (`BLOCKED_TOOL_IDS`):** `crm_send_whatsapp_message` e
    `crm_request_human_handoff` NUNCA são oferecidas à Ana como
    ferramentas — o sistema já envia pelo caminho seguro (opt-out,
    anti-ban) e já passa para humano pelo caminho seguro (silencia o
    automático). "Não há nada a ligar aqui."
  - **Coberta pela nativa (`COBERTA_PELA_NATIVA`):** `crm_search_knowledge`
    e `crm_schedule_followup` saem do turno quando a ferramenta nativa
    do agente está presente — duas ferramentas para a mesma coisa são
    peso e mais uma escolha para o modelo errar.
- **Agente externo (via `/api/mcp`):** recebe as ferramentas conforme o
  papel do token + pacotes, com as críticas exigindo marcação explícita.
- **Direção reversa:** a Ana também consome ferramentas de servidores
  MCP externos (`carregarServidorMcpExternoDoTurno`,
  `carregarServidoresDoAgenteNoTurno`, token efêmero) — o agente interno
  é cliente de MCP, não só o servidor.

Consequência para o desenho do gestor: o que a Ana faz pelo caminho do
sistema (enviar, handoff) o gestor externo só faz se a ferramenta
crítica correspondente estiver explicitamente ligada no token dele.

## Definição: o MCP é previsto na documentação do Deskcomm? SIM

Definido 2026-11-14, verificado nos arquivos do repo:

- **Spec 11 — Internal MCP Server (Tool Catalog)** (2026-05-05, status
  draft pré-implementação, owner Rafael Melgaço): "Servidor MCP
  interno que expõe as operações já existentes do CRM como tools
  consumíveis por agentes (Spec 10) e, futuramente, por clientes
  externos MCP (Cursor, Claude Desktop)." §1.1 prevê os DOIS
  consumidores desde o início: (a) agentes internos — o ToolLoopAgent
  da Spec 10 consome via `createMCPClient` HTTP/SSE; (b) clientes
  externos — "lojista pode plugar Cursor/Claude Desktop ao próprio
  CRM via API key. Out of MVP, mas o design não fecha porta."
- **Spec 14 — Contrato de Governança para Agentes Externos (MCP)**
  (verificado 2026-07-18 contra gov/G6 @ ddcc511): documento
  autocontido escrito para ser lido por UM agente externo — o
  **Vendaval**, runtime de agentes de IA 1:N, fora deste repo. Define:
  servidor MCP org-scoped; bearer token com org + scopes
  (`mcp:read`/`mcp:write`) + papel (`viewer` < `agent` < `manager` <
  `admin`); `organization_id` sempre do contexto de autenticação,
  nunca do input; RLS + filtro manual; auditoria do ator não-humano;
  idempotência; e `ai_dispatch_mode` (`native` | `external`) — no modo
  externo, o dispatcher nativo para de tocar os eventos da org e o
  Vendaval os consome.
- **Spec 13** — doutrina de governança do atendimento (complementa a 14).
- `docs/mcp/` em si só tem um arquivo (`derivados-do-historico.md`,
  escopo `messages:derived:read` para ler transcrições/texto derivado
  de mídia via MCP). A documentação do MCP mora em `docs/specs/`.

Ressalvas: a spec 11 estava como draft de maio/2026 — a implementação
existe hoje (rota `/api/mcp` verificada no código). A spec 14 foi
verificada em julho contra um catálogo menor ("as 8 tools de
governança que o Vendaval consome") — a lista atual de 75 ferramentas
é o código, não a spec; a doutrina de governança da spec continua
valendo. O papel **gerente** (`manager`) é um nível documentado, não
uma invenção deste projeto.
