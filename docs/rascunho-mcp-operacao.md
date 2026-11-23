# Rascunho — MCP da operação inteira (`tuttibom-ops-mcp`)

**Data:** 2026-11-21. **Status:** rascunho — desenho aprovado para
escrita pelo usuário em 2026-11-21; **não é decisão de construção**.
**Trabalho de plataforma (setor 08), para depois da V4** — não se
constrói no meio do teste ao vivo da V4.

**Decisão-mãe:** D-012 (2026-11-21) — CRM próprio + atendimento pelo
Muse, produção Deskcomm/Ana v12-B intocada até a promoção por setor.
**Princípio (user, 2026-11-15; confirmado 2026-11-21):** a operação é
agnóstica quanto ao agente — o gestor é um papel, não um agente; o
Muse é a primeira instância, não o agente único. Qualquer agente
designado entra e opera, de qualquer provedor ou modelo.

## 1. O problema que resolve

Hoje cada frente inventa o seu próprio acesso:

- O MCP do Deskcomm só cobre o gestor (token + papel, 27 ferramentas
  no escopo unificado, catálogo de 75 — ver
  `docs/rascunho-mcp-gestor-funcoes.md`).
- O `tuttibom-core-mcp` só indica (stdio, só leitura: estado, mapa,
  checklist, fila, catálogo, roadmap, decisões).
- O atendimento da nova vertente é vigília de 5 em 5 min + clique no
  painel (V4: 11 e 16 min por resposta).
- Nada conecta as 8 áreas (`docs/setores/`) num mesmo contrato.

O que falta é **um conector definido para a operação inteira**: o
agente se conecta, recebe as suas atribuições por área, confirma o
que foi liberado, e opera os fluxos como motor — o mesmo agente em
várias áreas, ou agentes distintos em áreas distintas, sem depender
de quem o agente é nem de onde veio.

## 2. Princípios (não negociar sem decisão do usuário)

- **O agente é o motor; o MCP é o contrato.** O servidor não decide
  nada sobre o cliente — ele expõe ferramentas, impõe o escopo e
  registra tudo. O comportamento vive nas skills (`skills/`), não no
  servidor.
- **O servidor impõe o escopo.** Lição do Deskcomm: lá o servidor
  NÃO impõe a lista de ferramentas nem o zero críticas — o escopo é
  disciplina do cliente + checkpoint humano. Neste MCP, não: uma
  ferramenta fora da atribuição do token é recusada pelo servidor,
  não pelo bom comportamento do agente.
- **Um agente ativo por área gravável.** Leitura pode ser
  compartilhada; escrita numa área tem um único dono por vez
  (lease sem prazo fixo — ver §5). Nunca dois agentes na mesma
  conversa ao mesmo tempo.
- **Nada publica, envia ou combina preço** sem aprovação do usuário
  ao texto exato — e à imagem exata, quando houver. Ferramentas que
  falam com o cliente de verdade são `critico` e nunca entram por
  pacote: exigem marcação explícita do usuário, uma a uma (mesma
  regra do MCP do Deskcomm).
- **Sem segredo** no git, nos logs, no MCP ou no Hindsight. **Sem
  dado de comprador** no repo, no painel ou no Hindsight. Memória
  por contato guarda só rótulo de interesse, nunca PII.
- **Conversas sempre em PT-BR.** Com clientes, "produtor" (José),
  nunca "gestor". Camofox é o navegador único (D-004); S10/ADB
  pausado.
- **O Muse implementa tudo ele mesmo** até o usuário pedir para
  delegar (regra de delegação, 2026-11-13) — inclusive este servidor,
  quando a construção for aprovada.
- **Isolado do MCP de desenvolvimento (decisão 2026-11-23 ~00:18).**
  Este é um servidor NOVO, só para a operação — não é o MCP de
  desenvolvimento, onde o agente lê o estado e tem acesso ao código
  e a tudo do ambiente. O MCP da operação expõe SÓ ferramentas da
  operação (atendimento, CRM, produto, criativos, social, anúncios,
  operação, plataforma); ele não dá acesso a código, repositório,
  estado do ambiente, credenciais nem a ferramentas de
  desenvolvimento. Um agente da operação nunca vê o código.
- **Atendimento autônomo via Chatwoot (decisão 2026-11-23 ~00:29).**
  O agente que recebe a Ana atende pelo Chatwoot normal — o mesmo
  caminho que o Muse usa hoje (fila do ouvinte, API do Chatwoot,
  skill da Ana) — e o MCP garante que isso aconteça com autonomia,
  sem interferência do Muse. O objetivo é que o outro agente faça
  as funções da Ana e a operação corra normalmente, sem interrupções
  e corretamente, como nos testes já feitos — só que com outro
  agente. O teste da Ana com outro agente aguarda a construção do
  MCP.
- **Tudo da operação passa pelo MCP (decisão 2026-11-23 ~00:31).**
  Inclusive o que o Muse faz enquanto desenvolve junto com a
  usuária: quando uma área existe no MCP, o trabalho daquela área
  vai pelo MCP, não por atalho direto (API, script, painel). Cada
  área pronta é entregue a outro agente para testar e monitorar — e
  o desenho tem que funcionar com qualquer agente, não só com um
  modelo ou provedor.
- **O Muse mantém acesso total pelo MCP de desenvolvimento (decisão
  2026-11-23 ~00:33).** A isolação é do lado da operação: o Muse
  desenvolve com acesso a tudo — código, estado, o próprio MCP ops
  — e pode se corrigir quanto ao MCP ops, que pode precisar de
  ajuste. No desenvolvimento valem correções, fixes, correção de
  bugs, atualização de pools e tudo do core da aplicação. O que
  passa pelo MCP ops é o trabalho da operação; o que mexe no código
  e no core é desenvolvimento.
- **Mídia é padrão para todo agente que atende (decisão 2026-11-22
  ~23:58).** Todo agente — o Muse ou outro — baixa e vê as imagens
  e baixa e transcreve os áudios que o lead envia, antes de
  responder. O ouvinte do Chatwoot hoje só entrega o texto; a mídia
  vem pela API (`data_url` do anexo; áudio transcrito com ElevenLabs
  Scribe). Quando este MCP for construído, a capacidade de mídia é
  requisito — não opcional.

## 3. Arquitetura

```
Agente (qualquer provedor/modelo, cliente MCP)
        │  MCP (JSON-RPC) — stdio local ou HTTP + token
        ▼
tuttibom-ops-mcp  (Python, src/tuttibom/mcp_ops/)
  ├─ auth: token → agente + áreas + limites
  ├─ manifesto: o que este agente pode fazer (por área)
  ├─ handshake: confirmação antes de qualquer escrita
  ├─ enforcement: recusa por ferramenta, no servidor
  └─ auditoria: toda chamada registrada
        │
        ▼
Backends (o MCP não guarda dado de cliente)
  ├─ CRM próprio (SQLite, src/tuttibom/crm/ — V2, já existe)
  ├─ Canais por API/webhook: WAHA, Zernio, Chatwoot (a decidir)
  ├─ Catálogo de produtos (18 SKUs, preços do PRECOS_SKU)
  └─ Drive (biblioteca de assets) e 9Router (modelo)
```

- **Transporte:** stdio para agentes no PC (mesmo padrão do
  `tuttibom-core-mcp`); HTTP com token para agentes remotos — só atrás
  de túnel, nunca porta aberta (decisão 2026-11-23 ~00:40:
  Tailscale, igual ao Muse).
- **Nomes (decisão 2026-11-23 ~00:34, renomeação 2026-11-23 ~00:51):**
  **tuttibom-core-mcp** (mcp core) e **tuttibom-ops-mcp** (mcp ops).
  O da manutenção hoje ainda se chama `tuttibom-mcp` (v0.1.1, só
  leitura via stdio: ele só indica o estado; quem grava é o agente)
  e leva o nome `tuttibom-core-mcp` na próxima atualização. O da
  operação nasce como `tuttibom-ops-mcp`. Quando o texto disser só
  "o MCP", é o mcp ops — o da operação. Os nomes são canônicos e
  devem ser usados na implementação (servidor, comandos, docs).
- **O servidor não toca no Deskcomm de produção.** O MCP do
  Deskcomm (gestor) continua como está; este é outro servidor, para
  a nova vertente.
- **O `tuttibom-core-mcp` (só indica) vira o núcleo de leitura** deste
  servidor — as ferramentas dele passam a ser a área de leitura do
  setor 08, não um servidor separado.

## 4. Identidade e áreas

- **Um token por agente, nunca compartilhado.** O token é a
  identidade: `ops_<prefixo>_<segredo>`, hash SHA256 guardado no
  servidor (mesmo padrão do Deskcomm). Só o usuário emite e revoga.
- **O token carrega a atribuição:** agente + áreas + limites por
  área. Exemplo: `ana-01` → áreas 01 + 02 (atendimento e CRM);
  `social-01` → áreas 04 + 05 (criativos e social); `gestor-01` →
  áreas 01–08 em leitura + 02 e 07 em escrita.
- **Áreas = os 8 setores** (`docs/setores/`):

| # | Área | Dono (documento) |
|---|---|---|
| 1 | Atendimento — Ana | `01-atendimento.md` |
| 2 | CRM e Vendas | `02-crm-vendas.md` |
| 3 | Produto e Catálogo | `03-produto-catalogo.md` |
| 4 | Criativos e Mídia | `04-criativos-midia.md` |
| 5 | Social e Conteúdo | `05-social-conteudo.md` |
| 6 | Anúncios, Aquisição e Concorrência | `06-anuncios-concorrencia.md` |
| 7 | Operação, Produção e Pagamento | `07-operacao-producao.md` |
| 8 | Plataforma e Manutenção | `08-plataforma-manutencao.md` |

- **Vários agentes ao mesmo tempo (decisão 2026-11-23 ~00:18).** A
  operação pode usar mais de um agente: cada um recebe só as suas
  atribuições (ex.: a Ana e todas as suas funções para um bot, a
  mídia social para outro, a gestão do CRM para outro). Um agente
  nunca vê as ferramentas das áreas que não lhe foram entregues —
  o teto de 27 vale por agente, sobre as SUAS áreas. Os agentes
  são de uso geral, parecidos com o Muse (ex.: Grokbot, Hermes,
  Cue da Manus) — o MCP serve a qualquer um deles.
- **Trocar de agente = trocar token + agendamento.** O novo agente
  recebe as mesmas áreas, repete o aperto de mão (§5) e continua de
  onde o anterior parou — o estado vive no CRM e nos documentos, não
  no agente.
- **Teto por agente:** seguir o padrão do Deskcomm — o agente nunca
  vê o catálogo inteiro de uma vez; vê só as ferramentas das suas
  áreas (teto de 27, mesmo número do MCP do Deskcomm).

## 5. O aperto de mão (handshake) — o coração do desenho

O agente, ao se conectar, já recebe as suas atribuições — e confirma
as atividades liberadas **antes de iniciar**. Sem a confirmação,
nenhuma escrita libera.

**0. Antes do token — solicitar as atribuições (decisão 2026-11-23
~00:18).** O agente novo chega sem token: recebe o comando inicial
padrão (Apêndice), conecta ao MCP e chama o método de catálogo
(`ops_listar_atribuicoes`), que devolve a lista ENUMERADA de
atribuições (áreas + funções). O agente apresenta a lista numerada
à usuária e AGUARDA o OK — sem executar nada antes. A usuária
indica os números que lhe cabem; só então o servidor emite o token
com acesso APENAS às ferramentas dessas atribuições, e o agente
reconecta e segue o handshake (passo 1).

```
1. connect (initialize) com o token
        → o servidor devolve o MANIFESTO:
          agente, áreas, ferramentas por área (com risco),
          limites (leitura / escrita reversível / com aprovação),
          hash da atribuição, validade do lease (sem prazo fixo)
2. o agente LÊ o manifesto e confirma:
        → ops_confirmar_atribuicoes(hash, resumo)
          (o resumo é o agente dizendo, nas próprias palavras,
           o que entendeu que pode e que não pode fazer)
3. o servidor registra a confirmação (auditoria) e LIBERA as escritas
        → antes disso, só leitura — e só nas áreas atribuídas
4. durante a operação, cada chamada é checada no servidor:
        ferramenta fora da atribuição → recusada (erro, não silêncio)
5. fim: token revogado, agente trocado ou agente desconectado
        → escritas bloqueiam; reconectar repete o handshake do zero
```

- **O lease é o dono da área gravável:** ao confirmar, o agente
  segura o lease da área (ex.: atendimento) **sem prazo fixo — o
  agente permanece atuando no seu escopo enquanto não for trocado**
  (decisão 2026-11-23 ~00:40; a proposta inicial de 8 h, renovável,
  foi descartada). Outro agente que pedir a mesma área em escrita
  recebe "área ocupada" e só lê. O lease termina quando o token é
  revogado ou o agente é trocado — o novo agente repete o handshake
  e assume.
- **A confirmação é uma chamada de ferramenta, não um "ok" no
  chat.** Ela fica na auditoria com o hash do manifesto — dá para
  provar depois o que o agente aceitou.
- **Mudança de atribuição no meio do turno** (o usuário libera ou
  tira uma área): o servidor invalida o manifesto, o agente recebe
  o novo na próxima chamada e confirma de novo antes de continuar
  escrevendo.

## 6. Ferramentas por área (inventário de partida)

Namespace por área (`ops_<area>_*`). Risco herdado do Deskcomm:
`seguro` (só consulta), `atencao` (altera, reversível),
`critico` (fala com o cliente de verdade ou não dá para desfazer —
nunca por pacote).

| Área | Ferramentas (partida) | Risco | Status |
|---|---|---|---|
| núcleo | `ops_listar_atribuicoes` (catálogo enumerado, sem token — só para pedir atribuição), `ops_minhas_atribuicoes`, `ops_confirmar_atribuicoes`, `ops_estado`, `ops_auditoria` (só as próprias chamadas) | seguro | a construir |
| 01 Atendimento | `ops_atendimento_ler_conversa`, `ops_atendimento_responder` | seguro / **critico** | a construir (canal por API/webhook primeiro) |
| 02 CRM e Vendas | `ops_crm_registrar_lead`, `ops_crm_mover_etapa`, `ops_crm_registrar_mensagem` (resumo, sem texto bruto), `ops_crm_followup`, `ops_crm_memoria_contato` (só rótulo) | seguro / atencao | **base existe** (`src/tuttibom/crm/` — V2) |
| 03 Produto | `ops_produto_consultar` (SKU, preço exato, disponibilidade) | seguro | a construir (dados existem: `PRECOS_SKU`, 18 SKUs) |
| 04 Criativos | `ops_criativo_listar_aprovados`, `ops_criativo_gerar_previa` (Modo A, só após aprovação da imagem exata) | seguro / atencao | a construir |
| 05 Social | `ops_social_rascunho_post`, `ops_social_publicar` | atencao / **critico** | a construir |
| 06 Anúncios | `ops_anuncio_consultar_concorrencia` | seguro | a construir |
| 07 Operação | `ops_operacao_registrar_pedido`, `ops_operacao_confirmar_pagamento` (só com confirmação do produtor) | atencao | a construir |
| 08 Plataforma | `ops_plataforma_saude`, `ops_plataforma_logs`, `ops_plataforma_reindex` | seguro / atencao | a construir (núcleo: `tuttibom-core-mcp`) |

- **Preço nunca é inventado:** a ferramenta de produto é a única
  fonte de preço; se o SKU não existir, a resposta é "vou
  consultar", nunca um valor.
- **Frete nunca é citado com valor:** a ferramenta de operação não
  tem preço de frete — o produtor confirma no app.
- **Enviar mensagem é `critico` em qualquer área.** O envio passa
  por `idempotency_key` com TTL (mesmo padrão do Deskcomm) para não
  duplicar.

## 7. Auditoria e observabilidade

- **Toda chamada registrada:** agente, área, ferramenta, argumentos
  sanitizados (sem segredo, sem PII de comprador), resultado,
  timestamp. O usuário vê quem fez o quê, quando, em qual área.
- **Contadores de falha** por área e por agente, visíveis — o mesmo
  padrão de observabilidade do setor 08.
- **O manifesto confirmado** fica guardado com o hash: dá para
  auditar depois o que cada agente aceitou operar.
- **Sem dado de comprador nos logs.** Resumo de mensagem, nunca
  texto bruto; contato por referência, nunca nome/telefone no log.

## 8. Segurança

- Token bearer + hash SHA256; revogação imediata pelo usuário.
- Enforcement no servidor, por ferramenta, em cada chamada
  (não só na conexão).
- Lease por área gravável, sem prazo fixo; área ocupada recusa
  escrita de outro agente.
- Rate limit por agente (a calibrar no v1).
- Jev como decisor tipado onde houver julgamento atômico (nunca
  escreve texto livre nem aprova publicação).
- Nada deste servidor é exposto em porta pública sem túnel e sem
  decisão do usuário.

## 9. O que este MCP NÃO é

- **Não é o agente.** O motor é o agente conectado — Muse hoje,
  outro amanhã. O MCP é o contrato entre o agente e a operação.
- **Não substitui a skill da Ana.** O comportamento (o que dizer,
  como dizer, as 26 regras "nunca") vive em
  `skills/ana-atendimento/SKILL.md`, não no servidor.
- **Não é o inbox.** WAHA, Zernio e Chatwoot são transporte; o MCP
  lê e escreve por cima deles via API/webhook. Trocar o inbox não
  troca o MCP.
- **Não toca na produção Deskcomm.** O agente do Deskcomm e a Ana
  v12-B continuam no MCP do Deskcomm até a promoção por setor (V5).

## 10. Sequência de construção (v1 mínimo, depois da V4)

1. **Núcleo:** auth por token + manifesto + handshake
   (`ops_confirmar_atribuicoes`) + enforcement + auditoria. Sem
   nenhuma área gravável ainda — só leitura do setor 08.
2. **Área 02 (CRM) primeiro:** o store já existe (V2) — é a
   primeira área gravável, com teste de laboratório (V3 por área).
3. **Área 01 (Atendimento):** quando o canal tiver API/webhook
   (Chatwoot ou ouvinte de webhook — decisão em aberto, §11).
4. **Demais áreas, uma por vez**, cada uma com o seu teste de
   laboratório antes de tocar em cliente real. Falha volta para o
   laboratório — não se "ajeita em produção".
5. **Promoção:** o MCP só vira o caminho principal quando os
   setores 1, 2, 3 e 7 estiverem promovidos (mesmo critério da V5).

## 11. Decisões em aberto (para o usuário, antes de construir)

- Hospedagem do servidor: **RESOLVIDO 2026-11-23 ~00:40 — o mesmo servidor que hospeda o tuttibom-ops (o PC).**
- Transporte: **RESOLVIDO 2026-11-23 ~00:40 — o agente acessa o PC via Tailscale, igual ao Muse (stdio no PC; HTTP com token só atrás da tailnet, nunca porta aberta).**
- O inbox vira Chatwoot? (Chatwoot é pesado: 4 contêineres, mínimo
  4 GB RAM / 2 CPU, ~US$ 15–25/mês hospedado — oversized para o
  volume atual; o peso se paga se o objetivo for trocar o inbox, não
  se for só responder mais rápido.)
- Duração do lease por área: **RESOLVIDO 2026-11-23 ~00:40 — sem prazo fixo; o agente permanece atuando no seu escopo enquanto não for trocado (a proposta de 8 h foi descartada).**
- Quem emite/revoga tokens (proposta: só o usuário).
- Nome do servidor: **RESOLVIDO 2026-11-23 ~00:51 — `tuttibom-ops-mcp` (mcp ops); o da manutenção, `tuttibom-core-mcp` (mcp core).**

## 12. Relação com o que existe

| Peça | Relação |
|---|---|
| MCP do Deskcomm (gestor) | Continua. É o modelo de token + papel + risco que este desenho generaliza. |
| `tuttibom-core-mcp` (só indica) | Vira o núcleo de leitura do setor 08 deste servidor. |
| CRM próprio (V2) | Primeiro backend gravável (§10, passo 2). |
| Skill da Ana | Comportamento; o MCP é só o contrato de acesso. |
| Setores (`docs/setores/`) | As áreas do manifesto — a fronteira já está escrita. |
| Chatwoot / WAHA / Zernio | Transporte, não parte do MCP (§9). |

## Apêndice — Comando inicial padrão (bootstrap)

A usuária entrega este comando a qualquer agente novo, antes de
qualquer atribuição. O agente não executa nada antes do OK dela.

> Você vai operar no TuttiBom OPS pelo MCP da operação
> (`tuttibom-ops-mcp`) — um servidor SÓ da operação, isolado do MCP
> de desenvolvimento: você não tem acesso a código, repositório,
> estado do ambiente nem credenciais.
>
> 1. Conecte ao MCP da operação e chame `ops_listar_atribuicoes` —
>    o catálogo ENUMERADO de atribuições (áreas + funções).
> 2. Apresente a lista numerada à usuária e AGUARDE o OK dela, sem
>    executar nada antes.
> 3. Quando ela indicar os números que lhe cabem, o servidor emite
>    o seu token — com acesso APENAS às ferramentas dessas
>    atribuições. Reconecte com o token, leia o manifesto e confirme
>    com `ops_confirmar_atribuicoes`, dizendo nas suas palavras o que
>    entendeu que pode e que não pode fazer.
> 4. Opere SÓ dentro das suas atribuições. Mídia é padrão: baixe e
>    veja as imagens e baixe e transcreva os áudios que o lead envia,
>    antes de responder.
> 5. Nada publica, envia ou combina preço sem a aprovação da usuária
>    ao texto exato — e à imagem exata, quando houver. Conversas
>    sempre em PT-BR; com clientes, "produtor" (José), nunca
>    "gestor". Sem segredo no git, nos logs ou no Hindsight; sem
>    dado de comprador no repo, no painel ou no Hindsight.
