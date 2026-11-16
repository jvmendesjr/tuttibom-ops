# Plano — Painel v2: as funções do Muse, passo a passo

> PLANO, 2026-11-05. Não aprovado, não construído. Para discutir
> antes de virar painel.
>
> **DECISÃO 2026-11-05 ~21:11 — PAINEL REDUZIDO A 2 ABAS: Conteúdo
> (social media) e Planos.** O Deskcomm passa a ser o atendente
> (inbox, kanban, handoff, follow-ups) e o Muse, o gestor. O que
> este plano descrevia com 10 abas está superado nesta parte: a
> aba Leads é cancelada (o kanban do Deskcomm é a visão de
> leads) e as abas Hoje, Funções, Agendamentos, Aprovações,
> Falhas, Saúde e provedores e Autorizações saem do painel — a
> visualização de operação passa para as superfícies do Deskcomm
> (inbox, radar, central de avisos, desempenho) e a autorização
> vira documento de escopo do Muse gestor. Ficam no painel só
> as seções 4 (Conteúdo) e 8 (Planos) deste plano, que o
> Deskcomm não cobre: ele não publica post, não agenda conteúdo
> e não tem visão de planos. O resto do documento fica como
> registro do que foi pensado e descartado. Detalhe da decisão:
> roadmap seção 10.
>
> Origem: o usuário pediu um painel simples para visualizar cada
> etapa das funções do Muse, com os agendamentos e os planos.
> Base: o painel v1 (`docs/painel-v1.md` + `painel-v1/index.html`,
> 7 abas, mockado) e os dois rascunhos de 2026-11-05
> (`rascunho-autorizacao-permanente-muse.md` e
> `rascunho-regras-whatsapp-handoff.md`), que alimentam a aba
> Autorizações.

## Governança (a mesma da v1, sem mudar)

- Painel **só leitura para o usuário; só o Muse edita e atualiza**.
- Sem botão de publicar, responder, apagar, pagar ou impulsionar.
  Aprovação continua na conversa, com texto e mídia exatos, nunca
  no painel e nunca em lote.
- Sem dado pessoal de comprador, sem conteúdo de conversa, sem
  segredo, sem endpoint vivo com porta, sem foto de cliente.
- Cada número mostra a fonte e a hora do último check; mock é
  marcado como mock até virar dado real.

## Abas da v2 — 10 abas

A v1 tinha 7 abas (Mapa, Setores, Aprovações, Falhas, Provedores,
Saúde do S10, Skills). A v2 reorganiza: o Mapa vira a visão de
pipeline dentro de Funções, Skills vai para Planos, e Saúde do S10
e Provedores se juntam numa aba só. Entram 6 abas novas: Hoje,
Funções, Agendamentos, Conteúdo, Autorizações e Leads (esta última
em 2026-11-05, inspirada no painel do Deskcomm — ver seção 10).

### 1. Hoje (Visão geral) — NOVA
O que está acontecendo agora, numa tela só.
- Próximo agendamento e o que ele vai fazer.
- Posts de hoje: o que foi publicado, o que está agendado, o que falhou.
- Aprovações paradas esperando o usuário (contagem + as 3 mais urgentes).
- Falhas das últimas 24h (contagem por severidade).
- Saúde do S10 em uma linha: bateria, rede, último ADB FOUND.
- Fonte: resumo das outras abas. Atualiza a cada ciclo do Muse.

### 2. Funções (pipeline) — NOVA, o coração do painel
Cada função do Muse como um pipeline, com as etapas e onde cada
item está. Nada de texto corrido: etapa, contagem, próximo passo.
- **Criar conteúdo:** ideia → roteiro/texto → storyboard/motion board → render → prova (stills) → na fila.
- **Publicar:** rascunho → aprovado → agendado → publicado → medido (24h/72h).
- **Responder (Messenger — é onde as interações começam):** as
  mensagens do Marketplace caem no Messenger, então é lá que a
  triagem e as respostas nascem: nova conversa no Messenger →
  triada → rascunho de resposta → aprovada → enviada → follow-up.
  Enquanto a resposta por ADB não for provada, a etapa "enviada"
  mostra "não provado — só rascunho". O Deskcomm trata Facebook/
  Messenger como segundo-cidadão (inbox compartilhado com o
  WhatsApp, sem aviso de janela próprio nem atribuição de anúncio);
  aqui o Messenger é o canal principal das interações, não um
  apêndice.
- **Encaminhar para o WhatsApp:** lead qualificado → condição do handoff → modelo enviado → conversa continua no WhatsApp.
- **Atender no WhatsApp (WAHA):** mensagem recebida → resposta pelas regras → registrada → gatilho de handoff → humano.
- **Follow-up:** lead com próxima ação → data vencida/hoje → lembrete → contato ou adormecido.
- Cada função mostra também sua regra de parada (o que trava e chama o humano).
- Fonte: `ops/`, fila de publicação, CRM (Drive), banco de memória.

### 3. Agendamentos — NOVA
Todos os trabalhos agendados, numa tabela: o que faz, quando roda,
última execução (hora + resultado), próxima execução, status.
- Postagem programada (ritmo a confirmar: diário ou 3/semana).
- Checagem de follow-up (quem venceu).
- Watchdog do S10 / ADB (180s) e boot.
- Checks de saúde (provedores, tokens, dispositivo).
- Fonte: crons e jobs do Muse + logs. Atraso aceitável: até o fim da sessão.

### 4. Conteúdo (Drive) — NOVA
Visualização do conteúdo criado e guardado no Drive, com link para
abrir cada item. O painel não hospeda o conteúdo: lista, descreve
e aponta para o Drive, onde a reprodução acontece.
- **O que lista:** roteiros (Docs), textos de post, áudios (narração,
  trilha), imagens e vídeos gerados, com título, tipo, data, status
  (rascunho / aprovado / agendado / publicado) e onde foi usado.
- **Conteúdo agendado:** os itens com data marcada, vindos da fila
  de publicação (`ops/fila-publicacao.md`) — o que vai sair, quando,
  em qual formato e rede.
- **Como visualiza:** o painel é hospedado no PC (rede privada via
  Tailscale) e, na atualização do painel, o Muse copia os arquivos
  de mídia do Drive (via o conector, já conectado) para a pasta do
  painel no PC — áudio, vídeo e imagem passam a ser servidos da
  mesma origem que a página, então tocam direto no painel, sem
  login na hora de ver. Roteiros e textos entram como texto no
  painel ou como link para o Doc. Correção importante: hospedar no
  PC **não** transfere o login do PC para quem abre a página — o
  login mora no navegador de quem abre, não no servidor. Por isso
  a cópia na atualização é o caminho: o painel serve o que já é do
  projeto, sem depender do login do Drive na hora. Alternativa
  futura (não nesta versão): um proxy no PC com token do Google,
  servindo o Drive ao vivo — exige um token guardado no PC e um
  serviço rodando, e só vale se a cópia na atualização ficar
  pesada ou desatualizada demais.
- **Métricas por conteúdo:** alcance, visualizações e engajamento
  agregados por post (sem dado de comprador), com a leitura de 24h
  e 72h da rotina R-09. Fonte: insights da Página (via conector do
  Facebook) + registro local. Métrica sem fonte é marcada como
  ausente, nunca inventada.
- **Observabilidade do conteúdo:** o que está atrasado, o que falhou
  no render, o que está sem prova (stills) e o que está sem medição.
- Fonte: conector do Google Drive (já conectado) + `ops/` + fila.
  Atualiza quando o Muse atualiza o painel, não ao vivo.

### 5. Aprovações — mantida da v1
O que está parado esperando o usuário, com título, produto, rede,
formato, texto resumido e mídia indicada. Na versão com dados reais,
a aprovação continua na conversa; o painel só reflete o estado depois.

### 6. Falhas — mantida da v1
Taxonomia em dois eixos (crítica / não crítica), contadores por dia,
semana e mês. Cada falha: tipo, severidade, módulo, horário, causa
(conhecida ou desconhecida — nunca inventada), impacto e próxima ação.
Regra a calibrar: 3 falhas críticas do mesmo tipo em 7 dias disparam
revisão da rotina, não retry em rajada.

### 7. Saúde e provedores — fusão da v1 (Saúde do S10 + Provedores e tokens)
- S10: bateria, disco, memória, uptime, reinícios, último watchdog, último ADB FOUND, rede ("rede nova" / "rede conhecida", sem nome sensível).
- Provedores: Muse, SSH, ADB, Facebook (app no S10), WAHA, Jev, Supabase, Drive, NotebookLM — status com último check e horário, nunca "online" genérico. Custo na mesma tela: tokens por provedor e por tarefa, custo estimado por lote.

### 8. Planos — NOVA (reúne Mapa + Skills da v1 + roadmap)
- Fases do roadmap (F0–F8) com checklist: o que está feito, o que falta, o que está bloqueado.
- Skills: as 5 externas analisadas (1 e 4 e 2 prontas; 5 pendente; 3 descartada) + skills locais, com nome, função e agente.
- Decisões: Paperclip x Muse autônomo, Deskcomm, WAHA — estado de cada uma (decidida / em discussão / descartada).
- Fonte: roadmap, `docs/ESTADO.md`, `skills/`.

### 9. Autorizações — NOVA
O estado das permissões de pé, para o usuário ver o que já autorizou
e o que ainda falta — sem aprovar nada no painel.
- Autorização permanente do Muse: estado (rascunho / aprovada / revogada), escopo coberto, regras fixas, gatilhos de handoff, decisões pendentes.
- Regras do handoff para o WhatsApp: condições, modelo exato, o que sempre precisa de humano.
- Decisões pendentes numeradas (número do WhatsApp, ritmo da postagem, teste do ADB, confirmação do caminho).
- Fonte: os dois rascunhos de 2026-11-05. Atualiza quando o usuário aprova ou muda algo na conversa.

### 10. Leads (visualização) — CANCELADA 2026-11-05 ~21:11 (ver decisão no topo deste plano e roadmap seção 10): o kanban do Deskcomm é a visão de leads; a aba não será construída. O texto abaixo fica como registro do que foi pensado.
O que o Deskcomm mostra de leads, adaptado para um painel só
leitura — sem o inbox, sem o agente atendente e sem automação.
Levantamento do painel do Deskcomm feito no código dele, em
2026-11-05 (não na tela logada): o que foi aproveitado está
abaixo; o que não foi, está na seção "Por que não estamos
recriando o Deskcomm".

- **Quadro por estado (kanban só leitura).** Um cartão por lead,
  com o que pediu, valor, etapa do CRM (Novo → Qualificado →
  Proposta → Fechado/Perdido/Adormecido), dono (Muse ou humano) e
  tempo na etapa. Padrão emprestado do Deskcomm: o cartão carrega
  um *slot* de estado calculado — "aguardando" (próxima ação
  pendente, ex. "sem resposta há 6 dias"), "esfriando" (tempo na
  etapa sem movimento) ou "tranquilo" — e o número não se repete
  duas vezes no mesmo cartão.
- **Dossiê do lead (ao abrir o cartão).** Estado, interesses
  (produto, cor, quantidade, ocasião), valor, próxima ação com
  data, e **histórico (linha do tempo)**: entrou por onde, mudou
  de etapa quando, rascunho aprovado ou descartado, passou para
  humano, retorno agendado, demanda encerrada. Regra emprestada
  do Deskcomm: só entra na linha do tempo o que muda o que alguém
  faria a seguir — recálculo de score e telemetria não geram
  linha ("silêncio para telemetria, pulso para mudança de
  estado").
- **Radar de risco (alertas que pedem o usuário).** A lista do
  que esfriou e precisa de atenção: Crítico / Em risco / Em voo
  (retorno já agendado). Cada item: há quanto tempo está aberto,
  há quanto tempo está parado, dono, e o que falta (sem próxima
  ação = risco de perder o cliente). É a mesma ideia do sino de
  avisos do Deskcomm, mas aqui o sino é só o contador no painel:
  o alerta chega ao usuário na conversa, não por outro canal.
- **Onde os dados vivem (honesto):** a fonte de verdade continua
  o CRM — planilha no Drive ("CRM TuttiBom — Interessados") e
  `ops/triagem-interessados.md`. O **Hindsight** (banco
  `tuttibom`) guarda por lead os fatos, os interesses e o
  estado, para o Muse lembrar sem reler tudo — é a camada de
  memória, não um banco relacional: ele não substitui a planilha
  nem vira tabela. O painel lê o CRM e mostra o que o Hindsight
  reteve; nenhum dado novo nasce no painel.
- **O que NÃO entra nesta aba:** conteúdo de conversa, telefone,
  e-mail ou endereço de comprador; botão de responder, mover de
  etapa ou assumir — tudo isso continua na conversa com o Muse,
  com aprovação do texto exato. Filtros: por etapa, por dono, por
  estado (aguardando / esfriando / tranquilo) e busca por produto.

## Por que não estamos recriando o Deskcomm

Pergunta do usuário em 2026-11-05, respondida com o levantamento
do código do Deskcomm: **não — estamos recriando a vitrine dele,
não o sistema.** A visão de leads (quadro, dossiê, linha do tempo,
radar, sino) é algo como 15–25% do produto, e a parte mais barata:
consulta a poucas tabelas e um pouco de apresentação.

O que o Deskcomm é de verdade — e o painel não recria — é o que
acontece atrás da vitrine: receber e enviar mensagens (inbox com
composer, WAHA, janela de 24h, templates), o agente de IA como
atendente com RAG, guardrails e handoff G1–G4, automação viva
(follow-ups automáticos, regras drenadas por cron), e
multi-operador com governança (atribuição, papéis, auditoria).
**Limite:** se um dia o painel precisar responder, atribuir ou
automatizar dentro dele, paramos e usamos o Deskcomm — reescrever
isso seria mais caro que usá-lo. Enquanto o objetivo for só
enxergar estado, interesses, histórico e alertas, a visão própria
é o caminho certo.

## Ferramentas de visual — Framer, Mobbin e Magic Patterns

Decisão já tomada na v1 e mantida aqui: **Mobbin primeiro, Magic
Patterns depois, rebuild pelo Muse como HTML só leitura.** Avaliação
das três para este painel:

- **Mobbin — usar primeiro (referência).** Biblioteca de telas reais
  de produtos lançados, pesquisável por padrão e fluxo. Serve para
  escolher padrões provados para este painel: dashboard de saúde,
  fila de aprovações, lista de incidentes, tabela de agendamentos,
  pipeline por etapas. Não gera a interface; mostra o que já
  funcionou. Para um painel interno de operação, é a que mais pesa.
- **Magic Patterns — usar depois (protótipo).** IA que gera interface
  a partir de prompt, com editor e exportação para React ou Figma.
  Serve para transformar os padrões do Mobbin + a identidade
  TuttiBom num protótipo rápido das abas novas (Hoje, Funções,
  Agendamentos, Conteúdo, Autorizações). Não trava a produção se
  estiver ausente.
- **Framer — não usar agora (só se quiser publicar).** Framer é
  construtor e hospedagem de site: bom para publicar um site
  interativo e compartilhável, ruim para este painel, que é um
  arquivo HTML local, só leitura, editado só pelo Muse, sem backend
  e sem login. Usar o Framer acrescentaria hospedagem, conta e
  dependência externa sem ganhar nada na leitura. Só reconsiderar
  se um dia o painel precisar ser um site publicado com link para
  abrir de qualquer lugar — e mesmo assim, com os mesmos limites
  (só leitura, sem dado de comprador).
- **Como usar sem copiar:** referência é padrão (ex.: "tabela de
  agendamentos com última/próxima execução e status"), nunca cópia
  de tela, marca ou texto de outro produto. A identidade visual
  segue a da TuttiBom, a reavaliar.
- **Credenciais:** só pelo fluxo seguro, nunca no chat, e só quando
  forem realmente usadas — um login por vez, para o site exato.
  O plano e o esboço não precisam de nenhuma credencial.

## MCP — as três têm servidor oficial; o Muse não tem conector para nenhuma

Verificado em 2026-11-05 (pesquisa + busca de conectores). O usuário
estava certo: o Muse **não tem conector** para Mobbin, Magic Patterns
nem Framer. Mas as três **têm MCP oficial** — ou seja, dá para ligar,
só não está ligado.

| Ferramenta | MCP oficial | Endereço | Autenticação | Plano | O que o Muse ganharia |
|---|---|---|---|---|---|
| Mobbin | Sim (mai/2026) | `https://api.mobbin.com/mcp` | OAuth | Pago (Pro/Team/Enterprise) | Buscar telas, fluxos e seções reais — só leitura (3 tools) |
| Magic Patterns | Sim | `https://mcp.magicpatterns.com/mcp` (só leitura: `.../mcp/readonly`) | OAuth ou API key | Pago | Ler designs e design system, levar design para o código e trazer layout do código de volta |
| Framer | Sim (22/out/2026) | `https://mcp.framer.com/mcp` | OAuth | Conta Framer | Criar/editar páginas, CMS e SEO; mudança fica em branch até publicar |

**Como ligar (quando o usuário quiser):** pelo fluxo de conector
personalizado do Muse — apontar para o MCP remoto, com OAuth ou API
key pelo fluxo seguro, nunca no chat. O MCP do Mobbin é só leitura;
o do Magic Patterns tem endpoint só leitura separado; o do Framer
edita o site (fica em branch até publicar). Todos os três exigem
plano pago. Nada disso é necessário para o painel v2 em HTML: o MCP
só muda como o Muse consulta as ferramentas durante o desenho, não
o painel em si. O Drive, por outro lado, **já tem conector e já
está conectado** — é ele que alimenta a aba Conteúdo.

## Ordem de construção (depois da aprovação do plano)

1. Usuário valida abas, ordem e o que falta/sobra.
2. Escolher padrões no Mobbin (pipeline, agendamentos, autorizações) e gerar protótipo no Magic Patterns com a identidade TuttiBom — só se o usuário quiser, com credencial pelo fluxo seguro.
3. Muse rebuilda como HTML só leitura (`painel-v2/index.html`), ainda mockado, com o contrato de dados acima.
4. Ligar os dados reais por aba, uma por vez, começando por Agendamentos e Funções (fontes que já existem: `ops/`, crons, logs).
5. Calibrar limiares (falhas por período, custo por lote, confiança do Jev).

## O que este plano NÃO inclui

- Nenhum botão de ação no painel (publicar, responder, aprovar em lote).
- Nenhum dado real de comprador ou conteúdo de conversa.
- Nenhuma credencial agora; nenhuma conta nova; nenhuma publicação do painel como site (Framer) nesta versão.
- Nenhuma mudança na operação: o painel só mostra; quem executa continua sendo o Muse, com as regras e autorizações da conversa.
