# Brief: memória interna por contato + roteador Jev

## Contexto

- Repo: `/home/pc/DeskcommCRM`, branch `local/v1.20.0-petemcasa`.
  HEAD esperado: `80f354895`. **Confirmar HEAD + árvore limpa antes de
  começar; se divergir, parar e reportar.**
- Objetivo: a Ana (e o roteador) consultam automaticamente o histórico
  do contato antes de decidir. Um "olá" de quem já comprou ou perguntou
  vai para o produto certo, sem perguntar de novo o que já se sabe.
- Decisão do usuário (2026-11-12): implementar a memória interna e os
  ajustes do Jev. As decisões técnicas (o que guardar, como buscar, o
  que buscar) foram delegadas a Muse e estão neste brief.

## O que já existe (não reinventar, não quebrar)

- Embedding `text-embedding-3-small` (1536 dim), `lib/ai/embed.ts`;
  pgvector + `ai_chunks`; busca top-k; teto `RAG_MAX_TOKENS`.
- A ingestão de conversas EXISTENTE
  (`lib/ai/rag/ingest/conversations.ts`) é **ANONIMIZADA e por
  ORGANIZAÇÃO** (fonte "Conversas anteriores", `source_type`
  "conversas", cron `app/api/v1/cron/kb-conversations-batch/route.ts`,
  gate `usable_for_rag` + `status='resolved'`). Ela serve ao acervo
  compartilhado — **NÃO serve à memória por contato** (a identidade é
  removida e não há `contact_id`). **NÃO alterar esse pipeline; a
  memória por contato é um mecanismo SEPARADO.**
- O roteador Jev (`lib/ai/decisao/roteador.ts`) decide **QUAL AGENTE
  atende**, entre os membros do roteador de intenção do número. Só roda
  com roteador de intenção **ATIVO** (máx. 1 por `channel_session`).
  A pergunta ao Jev leva só a última mensagem (R4) + intenções —
  **NÃO leva histórico**. Respeitar a decisão DEC-012 (doc 89) sobre o
  Jev não rotear sozinho: o classificador de sempre continua como
  reserva.
- A seleção de skills da Ana é keyword matching (não Jev). **O
  roteador de skills via Jev está FORA deste escopo** (brief separado).

## Fase 1 — Memória interna por contato

### 1a. Registro de interesse (estruturado, para o roteador)

- Nova tabela (migration **em arquivo no repo**, nome seguindo as
  convenções do projeto; ex.: `contact_interests`): `contact_id`,
  `organization_id`, `produto` (`fita` | `3d` | `ambos` | null),
  `ocasiao`, `ultimo_produto` (texto curto), `ultimo_stage`,
  `updated_at`. Índice por (`organization_id`, `contact_id`).
- Atualização: quando uma conversa resolve (hook no caminho de
  resolução) ou por job. Derivar o interesse dos dados já capturados
  na conversa (produto/ocasião registrados pelas skills/tools). Na
  primeira versão, **não usar LLM pesado** para derivar — regras sobre
  os dados existentes; se não houver dado, deixar null.
- Leitura: função que devolve o registro do contato
  (`organization_id` + `contact_id`). Retorna null se não houver
  (contato novo).

### 1b. Trechos por contato (vetor, para a Ana)

- Nova ingestão por contato: indexar os turnos das conversas
  resolvidas do contato em `ai_chunks` com `contact_id` no metadata
  (novo `source_type`, ex.: `memoria_contato`). **NÃO anonimizar a
  identidade** — o filtro por `contact_id` é a proteção (o agente só
  vê o histórico do contato que está atendendo, como já vê no CRM).
  Manter o guard de PII sensível (CPF etc.) reutilizando o detector
  existente; se ele bloquear, revisar o caso, não anonimizar às cegas.
- Reutilizar embedder (`text-embedding-3-small`), chunker e pgvector.
  Job em lote seguindo o padrão do `kb-conversations-batch` (nova
  rota/cron) e/ou indexação na resolução. Não mexer no pipeline
  anonimizado existente.

### 1c. Busca por contato

- Retrieval top-k filtrado por `organization_id` + `contact_id`
  (estender `retrieve_top_k_chunks` ou criar função análoga; **não
  remover o filtro por organização**).
- Ana: no turno, recuperar os trechos relevantes do contato (top-k,
  com teto de tokens) e incluir no contexto, como o RAG atual faz —
  mas filtrado por contato. Se não houver nada, o turno segue igual.
- Roteador: ler o registro de interesse (1a) antes de decidir; se
  houver, usar para decidir o agente; se não houver, seguir só com a
  mensagem.

## Fase 2 — Roteador Jev

- Configurar/ativar um roteador de intenção para a sessão/número do
  TuttiBom (membros: Ana; intenções: fita, 3d, preço, etc., definidas
  a partir das skills/produtos existentes; o membro 3D entra quando o
  agente 3D for criado).
- Ligar a tarefa Jev "roteador" (estado decidindo, com
  `min_confidence`; a IA de sempre como reserva, como o desenho prevê).
- **MUDANÇA DE DESENHO (explicitar):** a entrada do roteador passa a
  incluir o registro de interesse do contato (produto/ocasião), além
  da última mensagem + intenções. **NÃO incluir PII cru** (nome,
  telefone, endereço) na pergunta ao Jev — só o rótulo de interesse.
  Se o registro não existir, a entrada é só mensagem + intenções
  (como hoje).
- **Decisão determinística primeiro:** se o registro aponta um único
  produto e a mensagem é ambígua ("olá", saudação), o código decide
  direto pelo registro, sem chamar o Jev. O Jev/classificador entra
  para mensagens novas/ambíguas sem registro ou com conflito.

## Testes

- Em container `node:22`, como nos commits anteriores. Suite verde
  antes de considerar pronto.
- Cenários de prova (contatos de teste, nunca reais):
  - Contato com interesse "3d" diz "olá" → roteador aponta 3D.
  - Contato com interesse "fita" diz "olá" → aponta fita.
  - Contato novo diz "olá" → sem memória, decide só pela mensagem.
  - Ana recupera trecho passado do contato e não pergunta de novo o
    que já sabe.
  - Isolamento: a busca do contato A nunca devolve trecho do contato B
    (mesma org); e nunca cruza organização.
- **Não commitar nem deployar sem aprovação separada do usuário.**

## Travas

- Só DeskcommCRM, branch `local/v1.20.0-petemcasa`. Confirmar HEAD +
  árvore limpa antes de começar; se divergir, parar e reportar.
- Nunca `git pull` no branch, nunca trocar de branch, nunca migrations
  direto no DB de produção (migrations só como arquivos no repo,
  aplicadas pelo fluxo normal de deploy), nunca `docker compose down
  -v`, nunca tocar no cloudflared.
- Não mexer no pipeline anonimizado de "Conversas anteriores" nem na
  seleção de skills por keyword (fora do escopo).
- Não commitar e não deployar sem aprovação separada.
- Testes em container `node:22`.
