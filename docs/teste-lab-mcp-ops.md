# Matriz de Aceitação e Laboratório de Integração — `tuttibom-ops-mcp` (Frente QA)

> Matriz proposta pela frente QA. IDs, códigos e contagens de exemplo
> não definem a interface executável. Consulte o
> [guia de integração](operacao/mcp-ops-laboratorio.md) e
> `tests/test_mcp_ops_stdio.py` para o comportamento validado.

**Data:** 2026-11-23.  
**Frente:** QA — Matriz de aceitação, cenários portáveis e fixtures de integração e troca de agente.  
**Worktree:** `/home/pc/Workspace/tuttibom-ops-mcp-qa` (branch `exp/mcp-ops-qa`).  
**Fontes contratuais imutáveis:** `docs/rascunho-mcp-operacao.md` (§2, §4, §5, §6, §8, §10) e `docs/comando-inicial-agente-ops.md`.  
**Princípio central:** O agente é o motor; o MCP é o contrato. O servidor impõe o escopo e as regras no backend, independentemente do agente, modelo ou provedor conectado.

---

## 1. Objetivo e Escopo do Laboratório

Este documento formaliza a **Matriz de Aceitação em Laboratório** para o servidor de operação `tuttibom-ops-mcp`. A matriz foi desenhada para viabilizar testes determinísticos, portáveis e autônomos para a transferência da Ana e a operação multiagente do TuttiBom OPS, **sem conexão com serviços reais, sem tocar em banco de produção, sem emissão de mensagens a clientes reais e sem dependência de APIs em estado não implementado**.

### 1.1 Isolação e Limites
1. **Ambiente 100% sintético:** Todos os testes e fixtures utilizam identificadores, referências, números e mídias puramente fictícios.
2. **Separação estrita dos MCPs:**
   - `tuttibom-core-mcp` (antigo `tuttibom-mcp` v0.1.1): MCP de desenvolvimento/manutenção que só indica estado, voltado ao agente que constrói ou monitora o ambiente.
   - `tuttibom-ops-mcp`: MCP novo, exclusivo da operação (atendimento, CRM, catálogo, criativos, social, anúncios, pedidos). O agente operacional **não tem acesso a código, repositório, ambiente, comandos de sistema nem credenciais**.
3. **Portabilidade:** A matriz define interfaces de entrada, saídas esperadas, invariantes e códigos de erro formais para que a futura implementação (`src/tuttibom/mcp_ops/`) se combine de forma transparente com esta suíte de testes.

---

## 2. Invariantes Absolutos de Segurança e Governança

As 7 regras inegociáveis abaixo regem todos os cenários da matriz:

1. **Nada publica, envia ou combina preço sem aprovação da usuária ao texto exato (e à imagem exata):** A autorização de uma função crítica (como `01.02 - ops_atendimento_responder` ou `05.02 - ops_social_publicar`) apenas disponibiliza a ferramenta; cada disparo individual exige um token de aprovação assinado com o hash SHA-256 do texto exato.
2. **Catálogo apenas administrativo:** Agentes operacionais não possuem ferramenta para listar ou varrer o catálogo completo de funções. O cliente só descobre as ferramentas expressamente autorizadas no seu manifesto.
3. **Referência sem poder sozinha:** A referência gerada no comando administrativo (`AUTH-REF-...`) é pública/não-secreta; ela só é ativada quando acompanhada da identidade criptograficamente verificável do cliente configurada fora do chat.
4. **Uso único e lock atômico na ativação:** Cada autorização permite exatamente uma ativação. Tentativas de reuso ou ativações simultâneas em corrida (race conditions) são rejeitadas.
5. **Aperto de mão (Handshake) obrigatório:** O agente deve ler o manifesto, conferir seu hash SHA-256 e registrar `ops_confirmar_atribuicoes(hash, resumo)` antes de qualquer escrita ser liberada.
6. **Um escritor por área gravável (Lease sem prazo fixo):** Cada área gravável (ex.: Área 01 - Atendimento) possui um único titular de escrita por vez. O lease permanece ativo até que o agente seja trocado ou revogado pela usuária.
7. **Mídia é requisito obrigatório de atendimento:** Nenhum agente pode enviar ou propor resposta em atendimento sem antes ter baixado e visualizado imagens anexas e baixado e transcrito áudios recebidos.

---

## 3. Matriz de Aceitação — Os 10 Domínios de Verificação

### Domínio 1: Catálogo Apenas Administrativo
- **Fundamento:** `rascunho-mcp-operacao.md` §5 (item 0 e 1), §8.
- **Regra:** O catálogo global de funções é consultado apenas pela usuária via CLI administrativa autenticada (`tuttibom-ops-admin listar-atribuicoes`). Agentes no `tuttibom-ops-mcp` recebem apenas as ferramentas vinculadas ao seu token (teto de 27). O catálogo não expõe PII, dados operacionais ou preços dinâmicos.

| ID | Tipo | Caso de Teste | Entrada / Ação | Resultado Esperado | Invariante / Validação |
|---|---|---|---|---|---|
| `CAT-01-POS` | Positivo | Consulta administrativa do catálogo oficial | `tuttibom-ops-admin listar-atribuicoes` | Status 200; lista estruturada com 22 funções distribuídas nos setores 0 a 8, com número estável, nome, área e risco. | Dados operacionais e PII = 0; números são estáveis e únicos. |
| `CAT-02-NEG` | Negativo | Agente operacional tenta varrer o catálogo global via MCP | Chamada JSON-RPC `tools/list` com token operacional ou chamada a `ops_listar_catalogo_completo` | Erro `-32601` (`ERR_METHOD_OR_SCOPE_RESTRICTED`); apenas ferramentas autorizadas no manifesto são visíveis. | O agente operacional nunca descobre ferramentas fora da sua atribuição. |
| `CAT-03-NEG` | Negativo | Cliente sem token tenta listar ferramentas operacionais | Conexão MCP sem token executando `tools/list` | Erro `401` / `ERR_AUTHENTICATION_REQUIRED`. Nenhuma ferramenta operacional é exibida. | Proibida enumeração pré-autenticação. |

---

### Domínio 2: Autorização de Número Estável
- **Fundamento:** `rascunho-mcp-operacao.md` §5 (item 1 e 2), `comando-inicial-agente-ops.md` §1.
- **Regra:** As funções são referenciadas por números estáveis (ex.: `01.01`, `01.02`, `02.01`). Funções de risco `critico` exigem seleção individual explícita pelo seu número, nunca inclusão implícita por wildcard de área.

| ID | Tipo | Caso de Teste | Entrada / Ação | Resultado Esperado | Invariante / Validação |
|---|---|---|---|---|---|
| `AUT-01-POS` | Positivo | Autorização com números estáveis válidos | `tuttibom-ops-admin autorizar --agente ana-01 --funcoes 01.01,01.02,02.01,03.01` | Status 200; registro de autorização criado com status `pendente_ativacao` e referência `AUTH-REF-...`. | Lista de funções preservada exatamente como os números selecionados. |
| `AUT-02-NEG` | Negativo | Tentativa de autorizar área genérica com função crítica implícita | `tuttibom-ops-admin autorizar --agente ana-01 --area 01` (sem explicitar 01.02) | Erro `400` (`ERR_CRITICAL_FUNCTION_REQUIRES_EXPLICIT_NUMBER`). | Funções críticas nunca entram por pacote ou wildcard. |
| `AUT-03-NEG` | Negativo | Autorização com número inexistente ou adulterado | `tuttibom-ops-admin autorizar --agente ana-01 --funcoes 99.99` | Erro `400` (`ERR_UNKNOWN_FUNCTION_NUMBER`). | Rejeição imediata de números fora da tabela canônica. |

---

### Domínio 3: Referência Sem Poder Sozinha
- **Fundamento:** `rascunho-mcp-operacao.md` §5 (item 2 e 3), `comando-inicial-agente-ops.md` §1.
- **Regra:** A referência devolvida pelo comando administrativo é pública e trafega no prompt entregue ao agente. A referência sozinha não concede acesso, não é segredo e não funciona como bearer token.

| ID | Tipo | Caso de Teste | Entrada / Ação | Resultado Esperado | Invariante / Validação |
|---|---|---|---|---|---|
| `REF-01-POS` | Positivo | Ativação legítima combinando referência e chave de identidade | Requisição de ativação no endpoint de bootstrap contendo referência + assinatura da chave privada do cliente configurada fora do chat. | Status 200; token de sessão emitido por canal autenticado diretamente ao cliente (`ops_ana01_...`). | Token entregue exclusivamente ao cliente autenticado; nunca impresso no chat. |
| `REF-02-NEG` | Negativo | Uso da referência diretamente como credencial/token em ferramentas | Chamada a `ops_atendimento_ler_conversa` com header `Authorization: Bearer AUTH-REF-...` | Erro `401` (`ERR_AUTHENTICATION_REQUIRED`). | Referência não secreta rejeitada sumariamente como credencial de execução. |
| `REF-03-NEG` | Negativo | Ativação de referência sem comprovação de identidade fora do chat | Requisição de ativação fornecendo apenas a string `AUTH-REF-...` sem credencial de transporte | Erro `401` (`ERR_AUTHENTICATION_REQUIRED`). | Falha de autenticação mútua no canal de bootstrap. |

---

### Domínio 4: Identidade Errada
- **Fundamento:** `rascunho-mcp-operacao.md` §4, §5 (item 3).
- **Regra:** Uma autorização é vinculada à identidade estrita do agente designado. O servidor valida a correspondência exata entre a identidade apresentada e a identidade vinculada na autorização.

| ID | Tipo | Caso de Teste | Entrada / Ação | Resultado Esperado | Invariante / Validação |
|---|---|---|---|---|---|
| `IDE-01-POS` | Positivo | Identidade correspondente ativa autorização | Cliente autenticado como `agent:ana-01:...` ativa `AUTH-REF-20261123-ANA01-7F8A` | Status 200; emissão do token autorizada. | Identidade confere com o registro administrativo. |
| `IDE-02-NEG` | Negativo | Cliente com outra identidade tenta ativar a referência | Cliente autenticado como `agent:ana-02:...` tenta ativar `AUTH-REF-20261123-ANA01-7F8A` | Erro `403` (`ERR_IDENTITY_MISMATCH`). | Servidor bloqueia ativação cruzada e registra alerta na auditoria. |

---

### Domínio 5: Uso Único e Concorrente na Ativação
- **Fundamento:** `rascunho-mcp-operacao.md` §5 (item 2), `comando-inicial-agente-ops.md` §1.
- **Regra:** Cada referência permite exatamente uma única ativação. Uma vez consumida, torna-se permanentemente inválida. Disparos simultâneos concorrentes devem ser arbitrados por lock atômico no servidor.

| ID | Tipo | Caso de Teste | Entrada / Ação | Resultado Esperado | Invariante / Validação |
|---|---|---|---|---|---|
| `UNI-01-POS` | Positivo | Primeira ativação bem-sucedida consome referência | Cliente `ana-01` ativa `AUTH-REF-20261123-ANA01-7F8A` | Status 200; campo `ativada` transiciona para `true`. | Estado atômico persistido. |
| `UNI-02-NEG` | Negativo | Tentativa de reuso da referência consumida | Cliente `ana-01` tenta reativar a mesma referência já consumida | Erro `409` (`ERR_AUTHORIZATION_ALREADY_CONSUMED`). | Referências são de uso estritamente único. |
| `UNI-03-NEG` | Negativo | Disparos concorrentes simultâneos (Race Condition) | Dois processos tentam ativar `AUTH-REF-20261123-CONCORRENTE-RACE` no mesmo milissegundo | Processo A: 200 OK (token emitido); Processo B: 409 Conflict (`ERR_ACTIVATION_IN_PROGRESS_OR_CONSUMED`). | Exatamente 1 token gerado; zero duplicação por concorrência. |

---

### Domínio 6: Manifesto Inválido e Ciclo de Reconexão
- **Fundamento:** `rascunho-mcp-operacao.md` §5 (passos 1 a 5).
- **Regra:** Na conexão (initialize), o servidor envia o manifesto com o `hash_atribuicao` (SHA-256). O agente deve executar `ops_confirmar_atribuicoes(hash, resumo)` antes de qualquer escrita. Se o manifesto for alterado no servidor, o manifesto atual é invalidado e exige reconexão.

| ID | Tipo | Caso de Teste | Entrada / Ação | Resultado Esperado | Invariante / Validação |
|---|---|---|---|---|---|
| `MAN-01-POS` | Positivo | Handshake e confirmação íntegra do manifesto | Chamada a `ops_confirmar_atribuicoes(hash=sha256_correto, resumo="...")` | Status 200; `escrita_liberada: true`; auditoria registrada com o hash confirmado. | Liberação das ferramentas graváveis atribuídas. |
| `MAN-02-NEG` | Negativo | Escrita prévia ao handshake de confirmação | Agente tenta chamar `ops_crm_registrar_lead` antes de confirmar o manifesto | Erro `-32000` (`ERR_HANDSHAKE_PENDING_WRITES_BLOCKED`). | Apenas leituras são aceitas antes da confirmação formal do handshake. |
| `MAN-03-NEG` | Negativo | Confirmação com hash adulterado | Agente chama `ops_confirmar_atribuicoes` passando hash divergente do manifesto | Erro `-32000` (`ERR_MANIFEST_HASH_MISMATCH`). | Rejeição da confirmação; escritas continuam bloqueadas. |
| `MAN-04-POS` | Positivo | Invalidação de manifesto e reconexão por mudança de escopo | Usuária remove função `01.02` no admin durante a sessão; agente chama ferramenta em seguida | Erro `-32000` (`ERR_MANIFEST_INVALIDATED_RECONNECT_REQUIRED`); agente reconecta, recebe novo manifesto e refaz handshake. | Mudança administrativa surte efeito imediato no próximo ciclo de chamada. |

---

### Domínio 7: Dois Escritores e Revogação de Lease
- **Fundamento:** `rascunho-mcp-operacao.md` §2, §5 (lease sem prazo fixo), §8.
- **Regra:** Cada área gravável possui um único escritor ativo (lease sem prazo fixo). Um segundo agente que tente obter escrita na área ocupada recebe recusa ("área ocupada"). A revogação do token do primeiro agente pela usuária derruba o lease imediatamente, permitindo que o sucessor assuma.

| ID | Tipo | Caso de Teste | Entrada / Ação | Resultado Esperado | Invariante / Validação |
|---|---|---|---|---|---|
| `ESC-01-POS` | Positivo | Adquirição inicial do lease exclusivo pelo Agente 1 | `ana-01` realiza handshake com a Área 01 atribuída | Status 200; lease da Área 01 ativado para `ana-01` sem prazo de expiração. | Agente 1 é o titular exclusivo de escrita da Área 01. |
| `ESC-02-NEG` | Negativo | Segundo agente tenta obter escrita na mesma área | `ana-02` conecta e tenta confirmar escrita para a Área 01 com lease ativo de `ana-01` | Erro `-32000` (`ERR_AREA_OCCUPIED`). Escrita bloqueada; leitura permitida se autorizada. | Proibidos dois escritores simultâneos na mesma conversa/área. |
| `ESC-03-POS` | Positivo | Revogação administrativa do Agente 1 e sucessão limpa pelo Agente 2 | 1. `tuttibom-ops-admin revogar --agente ana-01`<br>2. `ana-01` tenta operar<br>3. `ana-02` faz handshake | 1. Lease de `ana-01` liberado imediatamente.<br>2. Chamada de `ana-01` retorna `ERR_TOKEN_REVOKED`.<br>3. `ana-02` assume lease exclusivo da Área 01. | Transição atômica e segura de escritor sem reinício de servidor. |

---

### Domínio 8: Aprovação da Resposta Exata
- **Fundamento:** `rascunho-mcp-operacao.md` §2, §6, `comando-inicial-agente-ops.md` §2.
- **Regra:** Nenhuma mensagem ou preço é enviado ao cliente sem aprovação prévia da usuária ao texto exato. O servidor verifica se o hash SHA-256 do texto submetido bate exatamente com o hash registrado na aprovação. Preços devem obrigatoriamente constar na tabela canônica `PRECOS_SKU`.

| ID | Tipo | Caso de Teste | Entrada / Ação | Resultado Esperado | Invariante / Validação |
|---|---|---|---|---|---|
| `APR-01-POS` | Positivo | Envio de resposta com texto exatamente idêntico ao aprovado | `ops_atendimento_responder(id_aprovacao="APROV-001", texto="Olá! O rolo...", ...)` | Status 200; mensagem despachada com status `enviado` e hash verificado. | Integridade absoluta do texto aprovado pela usuária. |
| `APR-02-NEG` | Negativo | Tentativa de envio sem token de aprovação | `ops_atendimento_responder(id_aprovacao=null, texto="Olá!...")` | Erro `-32000` (`ERR_EXACT_APPROVAL_REQUIRED`). | Nenhuma mensagem sai sem aprovação prévia explícita. |
| `APR-03-NEG` | Negativo | Texto alterado em 1 caractere em relação ao aprovado | Agente altera valor ou pontuação no texto submetido com o mesmo `id_aprovacao` | Erro `-32000` (`ERR_APPROVED_TEXT_HASH_MISMATCH`). | Divergência de hash SHA-256 detectada pelo servidor. |
| `APR-04-NEG` | Negativo | Proposta com preço inventado ou fora de tabela | Agente tenta submeter para aprovação valor não constante em `PRECOS_SKU` (ex.: R$ 65,00) | Erro `-32000` (`ERR_PRICE_NOT_IN_CATALOG`). | Preço é invariante de catálogo; nunca inventado ou negociado fora de tabela. |

---

### Domínio 9: Idempotência com TTL e Integridade de Payload
- **Fundamento:** `rascunho-mcp-operacao.md` §6.
- **Regra:** Operações com efeitos colaterais críticos (`ops_atendimento_responder`, `ops_operacao_registrar_pedido`) exigem `idempotency_key` (UUID v4). Retransmissões com a mesma chave e mesmo payload retornam o resultado original cacheado sem reexecutar. Mesma chave com payload diferente gera erro de conflito.

| ID | Tipo | Caso de Teste | Entrada / Ação | Resultado Esperado | Invariante / Validação |
|---|---|---|---|---|---|
| `IDEM-01-POS` | Positivo | Primeira execução com chave de idempotência válida | Chamada com `idempotency_key="e5b4b1a4-..."` e payload válido | Status 200; resposta gerada e registrada no cache com hash do payload e TTL de 24h. | Execução única registrada no backend. |
| `IDEM-02-POS` | Positivo | Retransmissão idêntica (mesma chave e mesmo payload) | Reenvio da mesma requisição dentro da janela de TTL | Status 200; resposta idêntica retornada com flag `idempotente: true`, sem novo disparo externo. | Prevenção absoluta de duplicidade de mensagens ao cliente. |
| `IDEM-03-NEG` | Negativo | Mesma chave de idempotência com payload divergente | Reenvio da mesma chave com texto ou destinatário alterado | Erro `-32000` (`ERR_IDEMPOTENCY_PAYLOAD_MISMATCH`). | Conflito de parâmetros para a mesma chave de idempotência. |
| `IDEM-04-NEG` | Negativo | Chamada crítica sem chave de idempotência | Chamada a `ops_atendimento_responder` com `idempotency_key=null` | Erro `-32000` (`ERR_IDEMPOTENCY_KEY_REQUIRED`). | Requisito obrigatório para qualquer ferramenta de envio ou pedido. |

---

### Domínio 10: Mídia Obrigatória e Continuidade de Fila na Troca de Agente
- **Fundamento:** `rascunho-mcp-operacao.md` §2, §4, `comando-inicial-agente-ops.md` §2.
- **Regra:** Todo agente que atende deve baixar e inspecionar imagens e baixar e transcrever áudios antes de responder. A fila de atendimento vive no servidor (CRM/Chatwoot); ao trocar de agente, o novo titular recebe a fila completa e íntegra, com mídias transcritas e estado de saudações já cumpridas, sem duplicar cumprimentos e sem perder mensagens.

| ID | Tipo | Caso de Teste | Entrada / Ação | Resultado Esperado | Invariante / Validação |
|---|---|---|---|---|---|
| `MID-01-POS` | Positivo | Processamento obrigatório prévio de imagem e áudio | Agente lê conversa com anexo de imagem e áudio, processa visão e transcrição localmente antes de propor resposta | Status 200; status das mídias atualizado para `processado` no backend; proposta liberada para aprovação. | Todas as modalidades de mídia consumidas antes da formulação de preço. |
| `MID-02-NEG` | Negativo | Tentativa de responder com mídia pendente na conversa | Agente tenta chamar `ops_atendimento_responder` enquanto há imagem ou áudio não analisados | Erro `-32000` (`ERR_MEDIA_PENDING_ANALYSIS`). | Bloqueio estrito no servidor até que todas as mídias da conversa sejam inspecionadas. |
| `MID-03-POS` | Positivo | Continuidade da fila de mensagens na troca de agente | `ana-01` analisa mídias e desconecta. `ana-02` assume o atendimento e lê a conversa via `ops_atendimento_ler_conversa` | Status 200; `ana-02` recebe histórico sanitizado com as transcrições das mídias, indicador de cumprimento de saudação (`saudacao_pendente: false`) e retoma diretamente o orçamento. | Zero perda de anexos, zero mensagens descartadas e sem reenvio de saudação duplicada. |

---

## 4. Tabela Canônica de Códigos de Erro do Servidor

| Código de Erro | Status HTTP / JSON-RPC | Descrição e Causa |
|---|---|---|
| `ERR_AUTHENTICATION_REQUIRED` | 401 / -32000 | Tentativa de acesso sem identidade verificável ou token válido. |
| `ERR_IDENTITY_MISMATCH` | 403 / -32000 | Identidade do cliente não confere com o titular vinculado na autorização. |
| `ERR_AUTHORIZATION_ALREADY_CONSUMED` | 409 / -32000 | Tentativa de reutilizar uma referência de autorização de uso único já consumida. |
| `ERR_ACTIVATION_IN_PROGRESS_OR_CONSUMED` | 409 / -32000 | Conflito em tentativa concorrente de ativação simultânea. |
| `ERR_CRITICAL_FUNCTION_REQUIRES_EXPLICIT_NUMBER` | 400 / -32602 | Tentativa de autorizar função crítica sem seleção individual explícita pelo seu número estável. |
| `ERR_UNKNOWN_FUNCTION_NUMBER` | 400 / -32602 | Número de função inexistente ou não catalogado. |
| `ERR_HANDSHAKE_PENDING_WRITES_BLOCKED` | 403 / -32000 | Tentativa de chamada gravável antes da confirmação formal do manifesto via `ops_confirmar_atribuicoes`. |
| `ERR_MANIFEST_HASH_MISMATCH` | 400 / -32000 | Hash fornecido pelo agente não coincide com o hash SHA-256 do manifesto emitido. |
| `ERR_MANIFEST_INVALIDATED_RECONNECT_REQUIRED` | 409 / -32000 | Atribuição alterada administrativamente durante a sessão; exige reconexão e novo handshake. |
| `ERR_AREA_OCCUPIED` | 409 / -32000 | Área gravável já possui escritor ativo; segundo escritor tem escrita recusada. |
| `ERR_TOKEN_REVOKED` | 401 / -32000 | Token revogado pela usuária via interface administrativa. |
| `ERR_EXACT_APPROVAL_REQUIRED` | 403 / -32000 | Tentativa de disparo de mensagem ou publicação sem id de aprovação prévia. |
| `ERR_APPROVED_TEXT_HASH_MISMATCH` | 400 / -32000 | Texto submetido difere em 1 ou mais caracteres do texto aprovado pela usuária. |
| `ERR_PRICE_NOT_IN_CATALOG` | 400 / -32000 | Preço proposto não consta na tabela canônica oficial (`PRECOS_SKU`). |
| `ERR_IDEMPOTENCY_KEY_REQUIRED` | 400 / -32602 | Operação crítica sem fornecimento obrigatório de chave de idempotência. |
| `ERR_IDEMPOTENCY_PAYLOAD_MISMATCH` | 409 / -32000 | Mesma chave de idempotência reutilizada com payload conflitante. |
| `ERR_MEDIA_PENDING_ANALYSIS` | 412 / -32000 | Tentativa de responder conversa com imagem ou áudio ainda pendente de processamento. |
| `ERR_METHOD_OR_SCOPE_RESTRICTED` | 404 / -32601 | Ferramenta fora do manifesto do agente ou tentativa de varredura global do catálogo. |

---

## 5. Mapeamento das Fixtures (`tests/fixtures/mcp_ops/`)

Os dados de teste estão organizados em 8 arquivos JSON autocontidos em `tests/fixtures/mcp_ops/`:

1. `catalogo_admin.json`:
   - 22 atribuições canônicas dos setores 0 a 8.
   - Números estáveis, riscos (`seguro`, `atencao`, `critico`), regras de isolamento e sondagens negativas.
2. `autorizacoes.json`:
   - Autorizações administrativas válidas para `ana-01`, `ana-02` e `hermes-plat`.
   - Cenários negativos de referência isolada, identidade divergente, reuso de código consumido e concorrência simultânea com lock atômico.
3. `manifestos.json`:
   - Estrutura completa de manifesto de atribuições com hash SHA-256 pré-calculado.
   - Handshake positivo via `ops_confirmar_atribuicoes` e cenários de bloqueio de escrita pré-handshake e hash adulterado.
4. `leases_concorrencia.json`:
   - Estado de lease gravável da Área 01 (Atendimento) sem prazo fixo.
   - Rejeição de segundo escritor (`ERR_AREA_OCCUPIED`) e ciclo de revogação imediata + sucessão de agente.
5. `aprovacao_resposta.json`:
   - Registro de aprovação com texto exato assinado pela usuária e hash SHA-256 correspondente.
   - Casos de sucesso, tentativa sem aprovação, adulteração de caractere e preço fora do `PRECOS_SKU`.
6. `idempotencia.json`:
   - Configuração de TTL (86400s), registro inicial, retransmissão idêntica transparente e detecção de payload conflitante.
7. `midia_fila_troca.json`:
   - Fila sintética com 3 mensagens (texto, anexo de imagem em base64 e anexo de áudio com metadados).
   - Bloqueio por mídia pendente e recuperação íntegra da fila na troca de `ana-01` por `ana-02`.
8. `scenarios_matrix.json`:
   - Consolidação estruturada de todos os 28 cenários dos 10 domínios, com referências diretas de fixture e critérios de aceitação.

---

## 6. Guia de Portabilidade e Combinação com a Implementação Futura

Quando a construção do servidor `tuttibom-ops-mcp` for autorizada na frente de implementação (em `src/tuttibom/mcp_ops/`):

1. **Validação contra as fixtures:** O servidor deve ser testado contra as fixtures desta matriz antes de qualquer exposição ou teste com clientes de IA.
2. **Sem criação de atalhos operacionais:** Todo acesso de agentes deve passar pelos endpoints do MCP (`auth/activate`, `initialize`, `ops_confirmar_atribuicoes`, `tools/call`).
3. **Persistência de estado fora do agente:** O servidor deve persistir leases, autorizações, auditoria e cache de idempotência no SQLite local da operação (`src/tuttibom/crm/` ou similar), garantindo que a queda ou substituição de um agente mantenha o atendimento íntegro.
4. **Zero alteração das regras de segurança:** As validações de aprovação exata de texto, hashing de manifesto e checagem de mídia devem ocorrer obrigatoriamente no lado do servidor, nunca dependendo da boa conduta do modelo do agente.
