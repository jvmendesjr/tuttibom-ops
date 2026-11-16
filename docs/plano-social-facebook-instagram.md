# Plano — criativo e fluxos nas redes (Facebook → Instagram)

> Rascunho, 2026-11-16 (America/Fortaleza). Não aprovado, não executado.
> Sem segredo, sem token, sem dado pessoal de comprador.
> Este documento só descreve o que fazer; não publica, não envia e
> não altera código, containers, banco ou configs.
>
> Ordem pedida: Facebook (página da loja + Messenger) primeiro;
> Instagram (feed/reels/stories + DM) depois.
> Frente vizinha P7 (tags) e `fb_agent.py`/Camofox são intocáveis —
> ver §6.

## 0. Como ler

Duas frentes andam juntas, mas não se misturam:

- **Criativo** — produzir e guardar conteúdo (biblioteca no Drive,
  roteiro, arte, fila). Publicar só depois da aprovação do José ao
  texto e à mídia exatos.
- **Fluxos** — atendimento de DM e de comentário caindo no Deskcomm
  (org `deskcomm-local`, Ana no WhatsApp `tutibom`), com rascunho e
  aprovação, como já vale no WhatsApp.

Caminhos possíveis de publicação e de inbox estão em §2. A
recomendação deste rascunho respeita a decisão já tomada em
2026-11-05: **não criar aplicativo próprio no Facebook Developers**;
inbox inicial via Zernio; publicação da página pelo caminho já
provado (S10/ADB) ou pelo agendamento nativo do Meta Business Suite.
A pesquisa da Graph API entra como mapa e como alternativa, não como
ordem de implementação.

### Decisões fechadas em 2026-11-16 ~09:10 (America/Fortaleza)

O José fechou três pontos deste plano (nomes curtos dele, e o id
do §8 quando havia). Skills e `docs/pacote-tuttibom.md` **não foram
editados**; a decisão vigente é esta, mesmo quando aqueles textos
divergem (ver §1.3).

- **D-mídia (D3):** misturar foto/vídeo **real autorizado** e mídia
  **fictícia**, **sinalizando qual é qual**. Foto/vídeo real só com
  autorização para demonstrar; IA com rótulo na arte e na legenda
  (“Prévia simulada — imagem gerada por IA”). Vale para o lote F1
  e para o que vier depois. Adendo do mesmo horário: o José vai
  **usar vídeos existentes e também criar vídeos novos**.
- **D-preço (D2):** legenda social **sem preço**. CTA chamando no
  **direct/Messenger**. A Ana **não cita frete** (e a peça social
  também não). Preço, quando for o caso, fica na conversa — a Ana
  cita o catálogo do Deskcomm, nunca estima. O pacote §9 continua
  dizendo que o preço do catálogo está resolvido para o atendimento;
  isso **não autoriza** colocar valor na legenda.
- **D8:** o Instagram da loja **ainda não é profissional nem está
  ligado à Página**. Vira tarefa da **Fase 4**, que **só o José
  executa**.

### Adendo 2026-11-16 ~09:35 (America/Fortaleza)

O José confirmou que **não há fotos reais suficientes**; a maior
parte dos criativos será **GERADA**. Ele quer usar mais o Gamma
(conta + API, versão 5) para post e carrossel, inclusive na
aplicação. Pesquisa e proposta (persona, API, fluxos da
comunidade, Ponte/MCP):
`docs/pesquisa-criativo-gamma-persona.md`.

O lote `criativos/f1-lote-01.md` **fica como registro e precisa
ser refeito** com mídia gerada — **não foi reescrito neste
passo**. A F1 só fecha o lote novo depois das decisões G1–G6
dessa pesquisa (tema/templates no Gamma, motor, tamanho do lote,
persona, MCP vs adapter, vídeo).


### Adendo 2026-11-16 ~10:10 (America/Fortaleza)

Incorpora a D-004, a pesquisa de vídeo/referências
(`docs/pesquisa-video-referencias.md`) e as decisões posteriores
do José no mesmo dia. Não republica nem gasta crédito.

- **Navegação e publicação (D-004):** o Camofox (motor + Jev) é o
  navegador único desta frente — painel, redes da loja e criativos.
  O S10/ADB está **pausado**. O que já foi provado via ADB em
  2026-11-01 (Feed e Stories, com rótulo de IA) permanece como
  histórico. O caminho ativo de publicação é o **Meta Business
  Suite** (o José cola ou sobe a peça aprovada e confirma) e,
  quando houver sessão combinada, o **Camofox** com os guardrails
  permanentes da D-004 (navegação simulada, ritmo humanizado, sem
  ações em massa, sem modificar o Camofox; qualquer alerta de bot
  → pausar e reavaliar). Esta frente **não edita** `fb_agent.py`
  e **não opera** o Camofox sem o José. O adapter Messenger via
  ADB na Ponte (passo 5) fica **posto de lado**; o Zernio segue
  como ponte inicial do Messenger (F3).
- **Gamma é auxiliar:** plataforma já paga, para aproveitar
  créditos em post e carrossel (still). Não publica, não agenda
  e não gera Reel. Detalhe em
  `docs/pesquisa-criativo-gamma-persona.md`.
- **Canal:** marca e produto agora; persona virtual depois,
  sempre rotulada, nunca no atendimento.
- **Aviso de IA:** texto na bio/Sobre da Página (e do Instagram,
  quando existir) + rótulo nativo em cada post/Reel/Story. Ver
  `docs/pesquisa-video-referencias.md` §3. Rascunho de bio,
  ainda sem publicar, está lá.
- **Mídia — regra conciliadora:** a maior parte será gerada.
  **Produto fiel ao catálogo** (nunca inventar especificação);
  cenário e pessoas podem ser gerados; bruto real autorizado
  tem preferência quando existir. Reconcilia o “produto 100%
  real no fundo” de `docs/motion-graphics-codigo.md` com a falta
  de fotos. Texto da regra: `docs/pesquisa-video-referencias.md`
  §5.
- **Vídeo de primeira linha:** cena (real ou gerada via
  Higgsfield/Kling/Gemini Omni; o Veo 3.1 Preview na Gemini API
  foi encerrado em 22/10/2026) + motion graphics em Remotion
  (estilos A–D) + voz/música ElevenLabs + legendas. Pipeline de
  6 passos no mesmo doc, §1. O lote `criativos/f1-lote-01.md`
  continua como registro, a refazer sob essa regra.
- A loja trabalha com **fitas personalizadas e impressão 3D**.
  A Página hoje só mostra fita; cinco melhorias priorizadas no
  mesmo doc, §4.
- Correções de estado, só para não arrastar erro antigo deste
  plano: `ops/fila-publicacao.md` **existe** (o levantamento das
  09:10 dizia o contrário); `docs/arquitetura.md` voltou no
  merge `91af93d`. Caminho desta frente:
  `/home/pc/Workspace/tuttibom-ops-social`, branch `social/fb-ig`.
  Sem commit até o José validar.

## 1. Estado atual honesto

### 1.1 O que já é real (código, conta ou prova)

| Peça | O que existe de verdade | O que não existe |
|---|---|---|
| Publicação no Facebook via ADB no S10 | **Provado** em 2026-11-01: Feed (com rótulo de IA) e Stories 9:16 do piloto. Ponto de execução do ADB é o PC. Skill `s10-navegacao`. | Resposta a interessado via ADB **não provada**. Upload de Reel/vídeo no app do Facebook no S10 é o ponto mais frágil e **não está provado**. |
| Biblioteca de assets | Pasta `Biblioteca TuttiBom` no Drive da loja; planilha de classificação; **25 assets aprovados** em 2026-11-12 (23 reais de trabalho autorizado + 2 IA), por ocasião. Espelho em `catalogo/biblioteca-assets.md` e `catalogo/assets-lote-2026-11-12.md`. Paleta em `catalogo/cores-fita-cetim.md` (69 cores, 18 disponíveis). | Teste de a Ana **enviar imagem** pelo WAHA ainda não provado. Planilha/espelho não são fila de publicação. |
| Skills de criativo (tuttibom-ops) | Existem e estão vendored: `tuttibom-facebook-conteudo` (roteiro/post/fila, só Facebook), `tuttibom-estudio-criativo` (produz, não publica), `tuttibom-facebook-motion` (regras de reel 9:16; não renderiza), `facebook-conteudo` (versão curta, mais antiga), `s10-navegacao`. Skill 4 (estrutura de post) e skill 2 (motion, parcial) já adaptadas. | Skill 5 (`coreyhaines31/social`: pilares, calendário, reaproveitamento) **pendente de aval do José**. `ops/fila-publicacao.md` é citado nas skills e no plano do painel, **arquivo não encontrado**. Brand sheet da conta: existe, **a reavaliar**. |
| Deskcomm — canal social | Código real em `lib/channels/social/` e `lib/channels/zernio/`. Catálogo declara Facebook e Instagram com `inbox: true` e duas portas: `direta` e `intermediada`. Porta **intermediada** (`provider=zernio_social`) **implementada**: ingestão, envio de texto/imagem/vídeo/áudio na thread já aberta, health. Adapter em `lib/channels/adapters/zernio.ts` + `social/adapter.ts`. | Porta **direta** (`implementada: false`, `providerNoBanco: null`) — não há valor no CHECK de `channel_sessions` para Graph direta de Instagram/Facebook. **Nenhuma sessão social configurada** (handover e roadmap §10, verificação 2026-11-05: 0 conversas FB/IG, 0 integração Zernio). Este plano não recontou o banco. |
| Deskcomm — `lib/channels/meta/` | Cliente da **WhatsApp Cloud API** (Graph `v22.0` neste checkout; v26.0 já existia em 29/07/2026 e não foi subida de propósito). Não publica post de Página nem Instagram. | Não é caminho de criativo nem de Messenger da Página. |
| `contact_channels` (migration 9032) | Tabela no schema: canais `whatsapp`, `email`, `instagram`, `messenger`, `tiktok`, `x` por contato. Apêndice na `baseline.sql`. Migration 9222 ajustou RLS. | **Nenhum código em `lib/` ou `app/` usa a tabela** (Ponte `AGENTS.md` e busca neste levantamento). É ponto de apoio futuro, não fluxo vivo. Há também o arquivo órfão `..._0159_contact_channels.sql` (número original; renumerada para 9032). Não mexer em nenhum dos dois. |
| Ponte (`/home/pc/ponte`) | Arquitetura hexagonal. Adapters **com código**: `browser` (Camofox/ElevenLabs), `crm` (`DeskcommClient`, isolamento por `organization_id`), `media` (`FFmpegStamper`). Túnel `cloudflared-ponte` (ex.: `deskcomm.petemcasa.com`) já existe. | Pastas `ideation/` e `checkout/` **existem vazias** (só o diretório). **Não há adapter de Messenger nem de Instagram.** TuttiBom **não está** em `config/projects.json` (só petemcasa, porquebr, byterain). Scripts `gerar_post_unico_tutibom.py` / `tutibom_pipeline_pydantic.py` na raiz da Ponte são experimentos de geração via Camofox — **não são adapter da loja** e não devem ser ligados à conta da TuttiBom (Camofox não toca essa conta; ver §6). |
| Atendimento já no ar | Ana v9 no WhatsApp `tutibom`, Inbox/kanban/fluxos/rascunhos no Deskcomm. Persona, base de conhecimento e pacote documentados. | Messenger e Instagram não entram nesse inbox hoje. Encaminhar lead do Messenger para o WhatsApp está desenhado no painel v2, não construído. |

### 1.2 O que é só documento (planejado, não construído)

- **Painel reduzido, aba Conteúdo** (`docs/plano-painel-v2.md` §4): lista o Drive, fila, métricas 24h/72h, observabilidade. Decidido que o Deskcomm não publica post e não agenda conteúdo; o painel cobriria isso. **Plano não aprovado, aba não construída.** É o passo 6 da ordem do roadmap §10 — depois de Zernio e do adapter ADB. Não bloqueia produzir rascunhos agora.
- **Adapter Messenger via ADB na Ponte** (passo 5): desenhado no roadmap §10 (entrada por screencap, saída por digitação no S10 após aprovação). Sem código. Alvo e fallback se o Zernio falhar.
- **Virada “sem API do Facebook Developers”** (2026-11-05 ~21:43, emenda ~22:00): o telefone é a API no desenho da Ponte; Zernio entra como ponte inicial de inbox (“infração leve do princípio, aceitável por comodidade e para testar”). Segue valendo até o José rever.
- Roadmap §12 (estado 2026-11-14) ainda põe Zernio **depois** do gestor via MCP e de dois cliques do José (publicar Fluxo A; testar ack de áudio). Esta frente de criativo/fluxos pode **preparar** em paralelo (pesquisa, biblioteca, rascunhos, decisões de conta) sem ligar webhook nem publicar.

### 1.3 Divergências código × documento encontradas

1. Caminho do projeto no PC é `/home/pc/Workspace/tuttibom-ops` (W maiúsculo). Vários docs ainda citam `~/workspace/...`, que **não existe**.
2. O handover aponta `docs/arquitetura.md`, `docs/rascunho-rotina-diaria-gestor.md` e `docs/mcp-ultima-varredura.json` — **não estão** em `docs/` neste levantamento.
3. `ponte/AGENTS.md` (2026-10-29) ainda descreve produção Deskcomm em imagens 1.44.0 “não virada”. A virada ocorreu em 2026-11-06 (ver `docs/atualizacao-deskcomm.md`); o handover atual já fala da instalação local no branch `local/v1.20.0-petemcasa`.
4. Handover lista adapters da Ponte como `browser`, `checkout`, `crm`, `ideation`, `media`. **Checkout e ideation são pastas vazias**; só browser, crm e media têm código.
5. **Regra de mídia divergente entre épocas:** blueprint (2026-11-01) e skills `tuttibom-facebook-conteudo` / `tuttibom-estudio-criativo` / `tuttibom-facebook-motion` ainda mandam “mídia 100% fictícia, zero foto real de cliente”. A biblioteca de 2026-11-12 **aprovou fotos reais de trabalho autorizado** (com regras: autorização, sem vazar pedido alheio, IA rotulada). A skill curta `facebook-conteudo` já falava em “foto real” do catálogo. As skills longas **não foram atualizadas e não serão editadas neste passo**. **Decisão vigente (D-mídia, 2026-11-16 ~09:10):** misturar real autorizado e fictícia, sinalizando qual é qual; vídeos existentes e vídeos novos entram no criativo (F1/F2).
6. Preço em dois textos que **não foram editados aqui:** `docs/pacote-tuttibom.md` §9 diz preço **resolvido** em 2026-11-06 (18 produtos no Deskcomm, captura Shopee 2026-10-30 como ponto de partida; Ana cita o catálogo; sem desconto). O mesmo pacote, no texto da memória da org, e a skill `tuttibom-facebook-conteudo`, ainda dizem “preço do Facebook/WhatsApp não está decidido”. **Decisão vigente (D-preço, 2026-11-16 ~09:10):** legenda social **sem preço**, CTA no direct/Messenger; Ana não cita frete. O catálogo resolvido vale para o atendimento, não para a peça pública.
7. `contact_channels` nasceu como 0159 e foi renumerada para 9032; os dois arquivos de migration convivem no repo. Não tocar — não é desta frente, e o 0159 é o “solto” já registrado no handover informal.

## 2. Pesquisa 2026 — APIs da Meta e alternativas

Pesquisa de documentação oficial e páginas de produto, lida em 2026-11-16. Números de cota e tags mudam; antes de implementar, reler a página citada e, no Instagram, consultar `content_publishing_limit` da conta (não hard-codar 50 nem 100).

### 2.1 Facebook Pages — publicar e agendar (Graph API)

- Publicar no feed: `POST /{page-id}/feed` com token de **Página**, permissão `pages_manage_posts` (depende de `pages_read_engagement` e `pages_show_list`). Quem autoriza precisa da tarefa `CREATE_CONTENT` (e, conforme o endpoint, `MANAGE` / `MODERATE`). Foto vai em `/{page-id}/photos`; vídeo/Reels têm API própria.
- Agendar post de feed: `published=false` + `scheduled_publish_time` (Unix em segundos, ISO 8601 ou string relativa). Janela documentada no guia de Posts: **entre 10 minutos e 30 dias**. A referência do Page Feed, em algumas leituras de 2026, cita 75 dias — construir pela janela **mais curta** (10 min–30 dias) ou manter a fila do nosso lado e só entregar à Meta dentro dela.
- Reels da Página: `POST /{page-id}/video_reels` em três fases (`upload_phase=START`, upload, `FINISH` com `video_state=PUBLISHED` ou `SCHEDULED`). Agendamento de Reel: cerca de 10 minutos a 29 dias. Teto: **30 Reels publicados via API por período móvel de 24 h**. Flag `is_ai_generated` existe.
- Fontes: [Posts (Pages API)](https://developers.facebook.com/documentation/pages-api/posts), [Reels Publishing API](https://developers.facebook.com/docs/video-api/guides/reels-publishing/), [Page Video Reels](https://developers.facebook.com/docs/graph-api/reference/page/video_reels/), [Facebook Pages API](https://developers.facebook.com/documentation/pages-api).

### 2.2 Instagram — Content Publishing API

- Exige conta **Business ou Creator**. No modo Facebook Login, a conta precisa estar **ligada a uma Página** e usa-se token de Página; há também Instagram Login / Unified Login com conjuntos de permissão diferentes.
- Fluxo: criar container `POST /{ig-user-id}/media` (mídia em URL **pública**, a Meta faz o fetch) → opcionalmente esperar `status_code=FINISHED` → `POST /{ig-user-id}/media_publish`. Tipos: imagem (JPEG), `REELS`, `STORIES`, `CAROUSEL` (até 20 itens na doc atual; trechos mais antigos ainda dizem 10). Container expira em 24 h se não publicar.
- **Não há `scheduled_publish_time` nativo** nesta API: agendar é fila própria (ou Business Suite). Parâmetro `is_ai_generated` existe no container.
- Cota: o guia de Content Publishing fala em **100** posts via API / 24 h móveis (carrossel conta 1), cobrada em `media_publish`. O mesmo guia, na parte de carrossel, e o endpoint `GET /{ig-user-id}/content_publishing_limit` ainda citam `quota_total` **50**. Tratar como divergência da própria Meta: **ler `quota_usage` e `config.quota_total` da conta** antes de publicar em lote. Para a TuttiBom (poucos posts/semana) qualquer um dos tetos sobra.
- Fontes: [Content Publishing](https://developers.facebook.com/documentation/instagram-platform/content-publishing/), [content_publishing_limit](https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-user/content_publishing_limit).

### 2.3 Messenger Platform e Instagram Messaging API

- Janela padrão: **24 h** após a ação da pessoa (em anúncio click-to-Messenger / click-to-Direct, a primeira mensagem pode abrir até **7 dias**). Dentro da janela, conteúdo promocional é permitido (`messaging_type=RESPONSE` ou `UPDATE`).
- Fora da janela, só tag aprovada e **não promocional**, ou mensagem patrocinada / notificação única (esta última **não existe no Instagram**). Em 27/04/2026 foram descontinuadas as tags `CONFIRMED_EVENT_UPDATE`, `ACCOUNT_UPDATE` e `POST_PURCHASE_UPDATE` (erro 100). Seguem relevantes: **`HUMAN_AGENT`** (resposta manual de humano em até 7 dias; exige App Review e, em geral, verificação do negócio) e o template de feedback do cliente. Não usar tag para oferta, desconto ou CTA comercial.
- Instagram DM: permissões típicas `instagram_manage_messages` (+ `instagram_basic`, e metadados de Página no fluxo com Facebook Login). Conta profissional com “permitir acesso às mensagens” ligado. Deskcomm já modela isso em `zernio_social`: `freeformOutsideWindow: false`; só responde quem já escreveu (`providerConversationId`).
- Comentário → DM (private reply): **uma** mensagem por comentário, em até **7 dias**; follow-up só se a pessoa responder, e aí vale a janela de 24 h. Live: só durante a transmissão.
- Fontes: [Send a message (Messenger)](https://developers.facebook.com/documentation/business-messaging/messenger-platform/send-messages), [Policy](https://developers.facebook.com/documentation/business-messaging/messenger-platform/policy), [Instagram Messaging overview](https://developers.facebook.com/documentation/business-messaging/instagram-messaging/overview), [Private replies](https://developers.facebook.com/documentation/instagram-platform/private-replies).

### 2.4 App Review e permissões (se um dia houver app próprio)

Cada permissão pede descrição de uso e **screencast**. No recorte desta loja:

- Publicar Página: `pages_manage_posts` (+ dependências).
- Publicar Instagram: `instagram_content_publish` (ou `instagram_business_content_publish` no login nativo) + `instagram_basic` / equivalentes.
- Messenger: `pages_messaging`.
- Instagram DM / private reply: `instagram_manage_messages` e, para comentários, `instagram_manage_comments`.

Isso é pesado para uma loja só. É o motivo prático — além da decisão de 2026-11-05 — para **não** abrir app próprio agora. Fonte: [Permissions Reference](https://developers.facebook.com/docs/permissions/), [App Review for Instagram API](https://developers.facebook.com/documentation/instagram-platform/app-review).

### 2.5 Alternativas (o que serve à TuttiBom)

| Caminho | Serve para | Prós | Contras neste projeto |
|---|---|---|---|
| **Meta Business Suite** (nativo, grátis) | Agendar posts/Reels/Stories da Página e do Instagram ligado | Sem app, sem App Review, janela típica ~20 min a 29 dias; o José já opera a Página | Não entrega DM no Deskcomm; não é fila nossa; tetos do app nativo (ex.: ordem de grandeza de dezenas de agendados/dia no Instagram) irrelevantes para o volume da loja. Fontes: [agendar post da Página](https://www.facebook.com/business/help/1252240869631062), [agendar no Instagram](https://help.instagram.com/439971288310029) |
| **Zernio** (já decidido como ponte inicial de inbox) | DM Facebook/Instagram → API que o Deskcomm **já fala** | Código `zernio_social` pronto; 2 primeiras contas grátis; **10.000 enviadas/mês grátis**, depois US$ 1 / 10 mil; leitura e resposta a comentário **não** entram no medidor; sem cartão, o envio para ao estourar (403). Volume da loja cabe com folga | Terceiro sobre as APIs da Meta (a “infração leve” já assumida); webhook HTTPS (túnel já existe); conta e OAuth da Página são do José; não resolve publicação de feed/reel | Fontes: [Inbox pricing](https://docs.zernio.com/pricing/inbox), [Zernio Pricing](https://zernio.com/pricing.md), [Inbox API](https://docs.zernio.com/products/inbox) |
| **S10 / ADB** | Publicar na Página (já provado) e, no futuro, fallback de Messenger | Alinha com a doutrina “o telefone é a API”; não depende de App Review | Frágil em vídeo; Messenger saída **não provada**; Instagram app **não provado**; não colidir com Camofox/`fb_agent.py` |
| **ManyChat** | Comentário→DM, words-triggers, fluxos prontos de captura | Rápido para “comente X e receba o catálogo no DM” ([auto-DM de comentário](https://help.manychat.com/en/articles/17742037-quick-automation-auto-dm-links-from-comments), [trigger de comentário no Facebook](https://help.manychat.com/en/articles/17742196-facebook-comments-trigger)) | Inbox dividido (fora do Deskcomm, a menos de integração extra); mais um terceiro e mais um contrato; **adiar** até o Messenger estar no Deskcomm e o José pedir explicitamente |
| **App próprio Graph API** | Publicação e inbox oficiais, sem Zernio | Controle total, agendamento de Página nativo na API | App Review, tokens de longa duração, verificação, manutenção. **Fora do escopo** enquanto a decisão de 2026-11-05 valer |

### 2.6 Boas práticas de criativo — loja pequena de fita / 3D

Adequado ao Cariri e ao que a biblioteca já tem (ocasiões: aniversário, casamento, formatura, confeitaria, marca/empresa, etc.):

- **Ritmo realista:** 2–3 posts ou Reels por semana no Facebook, no começo (D4 ainda aberto). Stories quando houver processo ou recado curto, sem inventar movimento. Instagram, só depois da F4 (D8: conta ainda não é profissional). Aí Reels como formato principal, carrossel 4:5, Stories para bastidores.
- **Foto e vídeo (D-mídia):** misturar real autorizado e fictícia, sinalizando qual é qual. Luz de janela, fundo limpo, close da textura e da impressão, mãos trabalhando, laço. Foto/vídeo real **só de trabalho autorizado**; nunca pedido de outro cliente na peça pública se o nome estiver legível (borrar, recortar ou trocar). Prévia de IA com rótulo visível na arte e na legenda. Vídeo faz parte da F1 (rascunho/roteiro) e da F2 (publicar): reusar existentes e criar novos. O Reel **ainda não foi provado via ADB**.
- **Texto (D-preço):** gancho → benefício em “você” → uma CTA só, para o **direct/Messenger**. **Sem preço e sem frete** na legenda. 3–5 hashtags locais, sem enchimento — já está na skill `tuttibom-facebook-conteudo`.
- **O que não fazer:** valor, frete ou desconto na peça; depoimento com nome de criança; isca de engajamento; copiar concorrente; publicar lote no automático.
- Referências gerais (não são doutrina da loja): guias de makers/handmade e fotografia de embalagem, ex. [Craftybase / Instagram para loja](https://craftybase.com/blog/promoting-etsy-shop-on-instagram), [fotografia de wrapping](https://www.viewbug.com/knowledge/gift-wrapping-photography). A voz e as travas da TuttiBom prevalecem.

## 3. Princípios que já valem (não reabrir, só aplicar)

- Nada é publicado, enviado ou fechado em preço sem a aprovação do José ao **texto e à mídia exatos**. Trabalho chega como rascunho.
- Com o comprador, José é “produtor”, nunca “gestor”. A Ana não se apresenta como virtual por conta própria.
- Sem dado pessoal de comprador no repo, neste plano ou no painel.
- **D-004 (2026-11-16):** Camofox (motor + Jev) é o navegador único da loja; S10/ADB está pausado. Esta frente não edita `fb_agent.py` e não opera o Camofox sem o José. O histórico de 2026-11-01 (Feed e Stories via ADB, com rótulo de IA) permanece como prova passada, não como caminho ativo.
- Conteúdo de IA segue a regra da plataforma (rótulo quando exigido); nunca insinuar que não é IA. **D-mídia (2026-11-16):** real autorizado e fictícia podem conviver, desde que a peça diga qual é qual.
- **D-preço (2026-11-16):** peça social sem preço e sem frete; CTA no direct/Messenger. Ana não cita frete. Aprovar preço na conversa continua sendo clique do José, quando houver valor.
- Vídeo entra na F1 (roteiro e rascunho) e na F2 (publicação). Existentes, gerados e novos, com a regra conciliadora. O Reel ainda não foi provado; o primeiro Reel aprovado prefere o Meta Business Suite (Camofox só em sessão combinada, D-004). Pipeline: `docs/pesquisa-video-referencias.md` §1.
- Esta frente **não altera** o repo Deskcomm, migrations, baseline, `organizations.settings`, catálogo MCP, containers ou configs. Também **não edita** as skills vendored nem o `pacote-tuttibom.md` para “alinhar” o texto antigo — a divergência fica anotada aqui.

## 4. Criativo × fluxos

```
[ideia] → [roteiro/legenda] → [arte no Drive, pasta Pendentes/]
        → [José aprova a peça exata] → [pasta da ocasião + planilha]
        → [fila de publicação] → [José aprova data/rede/texto]
        → [publicar: Business Suite ou Camofox (D-004); ADB pausado]
        → [medir 24h/72h, sem dado de comprador]

[comentário ou DM no Facebook] → [Zernio webhook] → [Deskcomm inbox]
        → [Ana rascunha / caso humano] → [José aprova se for envio ou preço]
        → [resposta no Messenger, dentro da janela de 24h]
        → [lead qualificado pode ir ao WhatsApp, pelas regras já existentes]
```

O Instagram copia o mesmo desenho, só depois do Facebook estável.
O painel (aba Conteúdo) **observa** essa fila no futuro; não é o
lugar onde se aprova ou se publica.

## 5. Fases ordenadas

Nenhuma fase abaixo mexe em código do Deskcomm. Ligar Zernio e
publicar exigem ações de conta do José. Critério de pronto e prova
vêm no fim de cada fase.

### Fase 0 — Alinhamento (antes de postar ou ligar inbox)

**Entregáveis:** este plano lido; decisões do §8 respondidas ou
marcadas como fechadas; inventário de contas.

**Já fechado em 2026-11-16 ~09:10:** D-mídia (D3), D-preço (D2) e
D8 (Instagram ainda não é profissional nem está ligado à Página —
tarefa da F4, só o José executa). Também ficou registrado que
vídeo existente e vídeo novo entram no criativo.

**Ainda aberto:** D1, D4 (ritmo; o 1º lote já inclui Reel e Stories
em vídeo), D5, D6, D7. Acesso do José ao Business Suite como admin
da Página, a confirmar na hora de publicar (F2).

**Dependências:** o que resta é resposta do José (D1, D4–D7) e,
na F4, o trabalho de conta dele no Instagram. Nenhum token é
gerado por agente.

**Pronto quando:** D1 e D4–D7 tiverem resposta explícita (D2, D3 e
D8 já não bloqueiam). A F1 de rascunhos **já pode andar** com o
que foi fechado.
**Prova:** as respostas registradas neste doc (decisões fechadas
acima e §8) ou em `docs/decisoes/`, sem credencial.

### Fase 1 — Criativo Facebook (produção, zero publicação)

**Entregáveis:**

- Regra de mídia **fechada (D-mídia):** misturar real autorizado e
  fictícia, sinalizando qual é qual. As skills longas ainda dizem
  “100% fictícia” — divergência anotada no §1.3; **não editar** as
  skills neste passo (ajuste vendored, se o José pedir depois, vai
  em arquivo separado, nunca no `SKILL.md` original, e nunca no
  Deskcomm).
- Legendas **sem preço e sem frete**, CTA no direct/Messenger
  (D-preço). Cores só as 18 disponíveis do catálogo.
- **Vídeo faz parte da F1:** roteiro e rascunho de Reel e de Story
  em vídeo, com duração, cenas (gancho nos 3 s iniciais), texto na
  tela, áudio, e a marcação “vídeo existente (a escolher na
  Biblioteca)” ou “vídeo a criar”. O José usa os que já tem e
  também cria novos. Isto é rascunho — **não publica**.
- Usar a fila de publicação já existente em `ops/fila-publicacao.md`
  (o levantamento das 09:10 dizia que o arquivo não existia; ele
  voltou no merge `91af93d`). Colunas: peça, formato (4:5 feed /
  9:16 stories ou reels), rede, texto, status (rascunho / aprovado /
  agendado / publicado), data proposta. Sem nome de comprador.
  Não apagar o histórico do piloto de 2026-11-01.
- Primeiro lote de rascunhos Facebook: `criativos/f1-lote-01.md`
  (2026-11-16) — 8 peças da Página, misturando feed, Stories e
  um Reel, com 3 itens em vídeo. **Adendo 09:35: este lote
  precisa ser refeito com mídia gerada** (fotos reais insuficientes);
  o arquivo atual fica só como registro, sem reescrita neste
  passo. Ver `docs/pesquisa-criativo-gamma-persona.md`. Até o
  lote novo, nada disso se publica.
- Reavaliar o brand sheet (cores, logo, margens) o bastante para
  fechar a assinatura do Reel (P6); sem isso, a cena final do
  Reel fica só com o nome da loja, em rascunho.

**Dependências:** Drive da biblioteca (já existe). Escolha, pelo
José, do vídeo existente (P5) e a produção dos vídeos a criar
(P6, P7), agora também pelo pipeline de
`docs/pesquisa-video-referencias.md` (geração + Remotion), com a
regra conciliadora. Nenhuma permissão Meta. A F1 é só produção:
não publica e não opera o Camofox.

**Pronto quando:** o José aprovar o lote (ou as peças que forem
seguir); vídeos existentes escolhidos e revisados (sem nome
legível); vídeos a criar gravados; nenhum item com status
“publicado”.
**Prova:** o José vê `criativos/f1-lote-01.md` e as mídias; marca
aprovado peça a peça.

### Fase 2 — Publicar no Facebook (página: feed, depois stories, depois reels)

**Caminho recomendado (enquanto valer “sem app próprio”, e
segundo a D-004):**

1. **Meta Business Suite** para agendar feed/Reels/Stories da Página
   (o José cola ou sobe a peça já aprovada e confirma data/texto).
   É o caminho preferido, sobretudo para o **primeiro Reel**, que
   ainda não foi provado.
2. **Camofox (motor + Jev)**, só em sessão combinada com o José,
   com os guardrails permanentes da D-004: navegação simulada,
   ritmo humanizado, sem ações em massa, sem modificar o Camofox;
   qualquer alerta de bot → pausar e reavaliar. Uma publicação por
   sessão, ritual de prova por captura (Jev). Esta frente não edita
   `fb_agent.py`.
3. **Vídeo na F2.** Stories em vídeo e o primeiro Reel aprovado
   preferem o Suite até existir um teste controlado de upload via
   Camofox. O histórico de 2026-11-01 (Feed e Stories estáticos via
   ADB, com rótulo de IA) não se reabre no S10 enquanto a D-004
   valer. Não misturar o teste com horário de atendimento da Ana.

**Não fazer nesta fase:** app Graph, token de Página em agente,
voltar ao ADB/S10, impulsionar, Marketplace (skill existe; é
outra frente).

**Dependências:** aprovação peça a peça (D0 contínua); acesso do José
ao Business Suite e, se for o caso, sessão Camofox combinada.
Agente não publica sozinho.

**Pronto quando:** 1 post no Feed e 1 Story no ar, com o texto e a
mídia que o José aprovou; captura de confirmação no Feed (“Seu
story” / post visível na Página), sem conteúdo de terceiros no
arquivo guardado. Reel: só entra no critério desta fase depois
de publicado com aprovação; até um teste Camofox existir, o
Suite conta como prova de publicação do Reel.
**Prova:** captura + linha na fila (“publicado”, data, formato).
Métricas 24h/72h, se o José puder ler no Suite, entram como
anexo num ciclo seguinte — nunca inventadas.

### Fase 3 — Fluxos Facebook Messenger → Deskcomm

Esta é a ponte de **atendimento**, não de criativo. Coincide com o
passo 4 do roadmap §10, mas pode ser **preparada** em paralelo às
Fases 1–2; **ligar** o webhook só com o José na conta, e de
preferência depois das pendências que ele já tem no §12 (Fluxo A e
ack de áudio não bloqueiam tecnicamente o Zernio, mas competem pela
atenção dele).

**Entregáveis (configuração, sem código novo no Deskcomm):**

- José cria a conta Zernio no plano gratuito e conecta a **Página**
  da loja (OAuth no fluxo do Zernio — token fica com ele / no
  Deskcomm pela tela “Redes sociais”, nunca no chat nem neste repo).
- Registrar o webhook na URL pública HTTPS já existente do app
  (túnel Cloudflare). Quem configura é o José na tela, com roteiro
  ao lado; agente não cola segredo.
- Teste com **uma** mensagem real, enviada por um perfil de teste
  do José (não de cliente): deve aparecer no inbox do Deskcomm,
  canal Facebook; rascunho de resposta; José aprova o texto; a
  resposta chega no Messenger dentro da janela de 24 h.
- Regra de fluxo v1 (rascunho, para o José aprovar depois):
  saudação curta → entender ocasião/produto → oferecer prévia só
  no Modo A (perguntar antes) → preço só do catálogo, se D2
  autorizar na rede → qualificou, encaminhar ao WhatsApp pelas
  regras já existentes. Fora da janela de 24 h: não mandar oferta;
  esperar a pessoa falar de novo (Zernio/Deskcomm já recusam
  freeform fora da janela). Comentário na Página, no v1: **não**
  auto-DM; avisar o José / rascunhar. ManyChat fica de fora até D6.

**Dependências do José:** conta Zernio, conectar Página, conferir
URL do webhook, mandar a DM de teste, aprovar o texto da resposta.
**Dependências de sistema já existentes:** código `zernio_social`,
túnel HTTPS, org `deskcomm-local`. **Não** registrar `tutibom` na
Ponte nesta fase (isso é o passo 5, adapter ADB, outro dono de
desenho e ponto serializado de config da Ponte).

**Pronto quando:** ida e volta da DM de teste visíveis no Deskcomm e
no Messenger, com horário e captura (sem dado de terceiro).
**Prova:** as duas capturas + nota de que a sessão `zernio_social`
está `WORKING` na tela de Conexões. Se falhar, registrar o erro e
parar — não improvisar Messenger via Camofox nem reabrir ADB
nesta fase (saída ADB nunca foi provada; adapter ADB está posto
de lado pela D-004; Camofox/`fb_agent.py` não se edita aqui).

### Fase 4 — Instagram, contas (depois do Facebook estável)

**Estado em 2026-11-16 ~09:10 (D8, fechada):** o Instagram da loja
**ainda não é profissional nem está ligado à Página.** Esta fase
só começa quando o José quiser; **só ele executa** os passos de
conta. Ninguém da frente social cria, converte ou liga a conta
no lugar dele.

**Entregáveis (a executar pelo José):** converter (ou criar) a
conta Instagram da loja em modo Business ou Creator; **ligar à
mesma Página** usada no Facebook; ligar o acesso às mensagens;
confirmar que ele é admin nos dois lados. Depois disso, a mesma
conta Zernio pode conectar o Instagram (ainda cabe no “2 contas
grátis”, se a Página já ocupou uma vaga).

**Dependências:** só o José no app/Business Suite. Sem isso, a
Content Publishing API e o inbox oficial nem existem. Fases 5–7
esperam esta.

**Pronto quando:** o José confirma, por escrito, “IG profissional
ligado à Página X, mensagens liberadas”.
**Prova:** print das telas de ligação (sem token).

### Fase 5 — Criativo Instagram

**Entregáveis:** reaproveitar as peças já aprovadas no Facebook,
adaptando formato (Reels 9:16 como principal; carrossel 4:5; Stories
curtos). Mesma biblioteca, mesmas travas. Não criar identidade nova.
Calendário Instagram só depois da skill 5 (se D7 autorizar) ou de um
mínimo manual na mesma fila.

**Pronto quando:** pelo menos 3 rascunhos IG aprovados na fila,
reusando asset já autorizado.
**Prova:** a fila e as peças no Drive.

### Fase 6 — Publicar no Instagram

**Caminho recomendado:** o mesmo Meta Business Suite (planner único
Página + IG). Upload pelo app do Instagram via ADB **não está
provado** e o ADB está pausado (D-004). Camofox só em sessão
combinada, depois do Suite. API de publicação: só se o José
reabrir D1.

**Pronto quando:** 1 Reel ou 1 carrossel e 1 Story no ar, texto/mídia
aprovados, linha na fila.
**Prova:** captura no perfil da loja, sem conteúdo de terceiro
arquivado.

### Fase 7 — Fluxos Instagram (DM e comentário → Deskcomm)

**Entregáveis:** conectar a conta IG no Zernio (segunda conta);
teste de DM idêntico ao da Fase 3; regra de **comentário→DM** no
v1 ainda manual/rascunho (private reply é irreversível: 1 mensagem
/ 7 dias). Só automatizar se o José pedir, com texto fixo aprovado
(“obrigada, te chamei no privado” + convite para falar no WhatsApp
ou seguir no DM), sem preço e sem dado.

**Pronto quando:** DM de teste ida e volta no Deskcomm. Comentário→DM
só entra no critério se D6 for “sim” e o teste controlado passar.
**Prova:** iguais à Fase 3, no canal Instagram.

### Depois (fora desta etapa, só para não perder o fio)

- Adapter Messenger ADB na Ponte (passo 5 do roadmap) + registrar
  `tutibom` em `projects.json` — desenho já escrito; código zero;
  não começa enquanto esta etapa de pesquisa/plano estiver só em
  docs, e não colide com P7, mas **é serializado** com a config da
  Ponte e com quem opera o S10.
- Painel reduzido (aba Conteúdo + Planos).
- ManyChat, app Graph próprio, Marketplace, anúncios pagos.

## 6. Colisão com outros agentes

Como trabalhar **sem colidir** com o outro agente em paralelo:

| Superfície | Dono | O que esta frente faz |
|---|---|---|
| **P7 — vocabulário canônico de tags** | Autor do handover; **intocável** até ele liberar. HEAD citado: `fc4a4e0b6`. Arquivos: `lib/schemas/tags.ts`, `app/api/v1/tags/vocabulario/route.ts`, `fn_vocabulario_de_tags_operar` + migration `..._9224_adicionar_etiqueta_no_vocabulario.sql` + apêndice no `baseline.sql`, `app/app/settings/tags/_painel.tsx`, `lib/operacao/marcadores-e-time.ts`, testes `tags-vocabulario*`. | **Nada.** Nem leitura de alteração, nem “só um teste”. Fluxos sociais não precisam de tag nova para o plano. |
| **`fb_agent.py` / Camofox** | Autor do handover é dono do **código** (`fb_agent.py`); a D-004 tornou o Camofox o navegador único das redes da loja. | **Não editar, não refatorar, não apontar script novo.** Publicação e navegação da conta, quando o José aprovar, seguem a D-004 (Camofox + Jev, guardrails permanentes). Produção de arte desta frente: Drive + Remotion/FFmpeg/Higgsfield/Gamma no PC ou no box, sem operar a sessão Camofox sozinho. |
| **Varredura do gestor** (08:00 / 14:00 / 20:00) e `mcp-ultima-varredura.json` | Autor do handover. | Não rodar, não reescrever, não competir pelo token MCP. |
| **`organizations.settings`**, baseline / migrations, funções SQL compartilhadas, **catálogo MCP** | Um dono por vez (ver `docs/frentes-ativas.md`). | Esta frente **não escreve** nesses pontos. Ligar Zernio, se for pela tela do Deskcomm, é configuração da org — **só com o José na tela**, e avisando o outro agente antes se houver risco de mexer em settings. |
| **Repo Deskcomm** (`local/v1.20.0-petemcasa`) | Produção viva; nunca `git pull`; P7 em andamento. | Só leitura, como neste levantamento. Nenhum commit, migration ou compose. |
| **S10 / ADB** | Pausado pela D-004. Aprendizados em `docs/aprendizados-adb-comunidade.md` ficam como referência, não como prática ativa. | **Não usar** enquanto a D-004 valer. Não reabrir janela de ADB para publicar nem para Messenger. |

Trabalho paralelo **seguro agora:** rascunhos no Drive, este doc,
skills de criativo (só no repo tuttibom-ops, arquivos de ajuste),
fila de publicação, pesquisa. Trabalho que **espera o José e um
aviso explícito:** conectar Zernio, webhook, qualquer clique no
painel Deskcomm, qualquer sessão Camofox na conta da loja.

## 7. O que exige aprovação do José (publicar, enviar, preço)

Sempre, com o texto ou a imagem exatos na frente:

- Publicar ou agendar qualquer post, Reel ou Story (Facebook ou Instagram).
- Enviar qualquer DM, private reply ou resposta a comentário (mesmo a de teste).
- Citar preço, prazo de entrega, desconto (desconto já é “não”) ou condição de pagamento numa peça ou numa resposta.
- Impulsionar, anunciar, ou ligar CTA paga.
- Conectar Página/Instagram a Zernio, ManyChat ou qualquer app Meta; gerar ou colar token.
- Mudar a decisão “sem app no Facebook Developers”.
- Publicar versão de agente, fluxo ou memória no Deskcomm (já era regra; esta frente não pede isso).
- Qualquer uso de foto real que ainda não esteja autorizada na biblioteca.

Rascunhar, classificar no Drive, escrever este plano e pesquisar API
**não** exigem esse clique — mas também não saem do rascunho sozinhos.

## 8. Decisões do José

### Fechadas em 2026-11-16 ~09:10 (America/Fortaleza)

- **D2 / D-preço — FECHADA.** Legenda **sem preço**. CTA para o
  direct/Messenger. Ana não cita frete (a peça social também não).
  O catálogo do Deskcomm (pacote §9) continua valendo no
  atendimento; **não** se copia o valor para a legenda. Skills e
  pacote não foram editados — ver §1.3 item 6.
- **D3 / D-mídia — FECHADA**, com a **regra conciliadora** do
  adendo 10:10 (`docs/pesquisa-video-referencias.md` §5): produto
  fiel ao catálogo; cenário e pessoas podem ser gerados; bruto
  real autorizado tem preferência. Adendo das 09:10: usar vídeos
  existentes e criar vídeos novos. Skills longas que ainda pedem
  “100% fictício” ou “fundo 100% real” ficam como estão até um
  ajuste separado, se o José pedir — ver §1.3 item 5.
- **D8 — FECHADA.** O Instagram da loja ainda **não** é profissional
  e **não** está ligado à Página. Tarefa da F4, **só o José executa**.

### Ainda abertas

Resposta curta basta. A F1 de rascunhos já anda com o que foi
fechado; publicar (F2) e ligar inbox (F3) ainda dependem do que
falta.

- **D1. Caminho de publicação.** A D-004 já substitui o ADB pelo
  Camofox como navegador. A pergunta que resta: manter a decisão
  de 2026-11-05 (sem app próprio no Developers) — Business Suite
  para agendar + Camofox só em sessão combinada — ou reabrir
  Graph API / App Review? (Sugestão vigente: Suite, sobretudo
  para o **primeiro Reel**, ainda não provado; Camofox com os
  guardrails da D-004; ADB pausado.)
- **D4. Ritmo.** Quantos posts por semana no Facebook no começo
  (sugestão: 2–3)? O 1º lote (`criativos/f1-lote-01.md`) **já inclui**
  um Reel e dois Stories em vídeo, como rascunho — não precisa
  reperguntar se o Reel entra; falta só o ritmo e os horários.
- **D5. Quando ligar o Messenger (Zernio).** Pode ser em paralelo
  aos rascunhos de criativo, ou só depois de publicar o Fluxo A e
  testar o ack de áudio (§12 do roadmap)?
- **D6. Comentário→DM.** No v1, só rascunho/manual? Ou já quer um
  texto fixo aprovado? ManyChat agora, depois, ou não?
- **D7. Skill 5** (`coreyhaines31/social`: pilares e calendário) —
  autoriza adaptar agora, ou fica para depois do primeiro lote?

### O que só o José consegue gerar ou autorizar (conta / token)

- Login e papel de admin na Página.
- **F4 / D8:** converter o Instagram da loja para profissional,
  ligar à Página e liberar mensagens — só ele executa.
- Escolher na Biblioteca o vídeo existente (P5, e cortes do P6) e
  **gravar os vídeos novos** (P6, P7); aprovar cada peça do lote F1.
- Conta Zernio e o OAuth “conectar Página / Instagram” (Instagram
  só depois da F4).
- Confirmação do webhook (URL HTTPS já existe; o clique e o segredo
  são dele).
- Acesso ao Meta Business Suite para agendar (e para o primeiro Reel,
  enquanto o upload via Camofox não estiver provado).
- DM e comentário de **teste** a partir de um perfil que não seja de
  cliente.
- Se D1 reabrir app próprio: criar o app Meta, App Review, tokens de
  Página de longa duração — tudo no fluxo seguro, nunca no chat.
- Qualquer cartão, plano pago (Zernio além do grátis, ManyChat, etc.).

## 9. Fontes (URLs)

- Meta Pages / posts e Reels: https://developers.facebook.com/documentation/pages-api/posts — https://developers.facebook.com/docs/video-api/guides/reels-publishing/ — https://developers.facebook.com/docs/graph-api/reference/page/video_reels/ — https://developers.facebook.com/documentation/pages-api
- Instagram Content Publishing e cota: https://developers.facebook.com/documentation/instagram-platform/content-publishing/ — https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-user/content_publishing_limit
- Messenger / IG messaging / private replies / policy: https://developers.facebook.com/documentation/business-messaging/messenger-platform/send-messages — https://developers.facebook.com/documentation/business-messaging/messenger-platform/policy — https://developers.facebook.com/documentation/business-messaging/instagram-messaging/overview — https://developers.facebook.com/documentation/instagram-platform/private-replies
- Permissões e App Review: https://developers.facebook.com/docs/permissions/ — https://developers.facebook.com/documentation/instagram-platform/app-review
- Business Suite / agendamento nativo: https://www.facebook.com/business/help/1252240869631062 — https://help.instagram.com/439971288310029
- Zernio: https://docs.zernio.com/pricing/inbox — https://zernio.com/pricing.md — https://docs.zernio.com/products/inbox
- ManyChat: https://help.manychat.com/en/articles/17742037-quick-automation-auto-dm-links-from-comments — https://help.manychat.com/en/articles/17742196-facebook-comments-trigger
- Docs internos de autoridade (lidos; este plano e `docs/frentes-ativas.md` foram atualizados neste passo, os demais não): `docs/decisoes/D-004-2026-11-16-camofox-navegador-unico-adb-pausado.md`, `docs/pesquisa-video-referencias.md`, `docs/motion-graphics-codigo.md`, `docs/plano-social-media-criativos.md`, `docs/pesquisa-criativo-gamma-persona.md`, `docs/handover-deskcomm-outro-agente.md`, `docs/roadmap.md` §10–§12, `docs/plano-painel-v2.md`, `docs/pacote-tuttibom.md`, `docs/persona-interacao.md`, `docs/base-conhecimento-tuttibom.md`, `docs/aprendizados-adb-comunidade.md`, `docs/blueprint-inicial.md`, `docs/frentes-ativas.md`, `catalogo/*`; Ponte `AGENTS.md`; Deskcomm `lib/channels/{social,zernio,adapters,meta}/` e migrations 9032 / 0159 / 9222 / 9224 (esta última só para não tocá-la).
- Rótulo de IA (Meta): https://www.facebook.com/help/7434563519957988 — https://transparency.meta.com/en-us/governance/tracking-impact/labeling-ai-content — https://creators.instagram.com/blog/ai-generated-profile-label

## Registro 2026-11-16 ~10:16 (America/Fortaleza) — decisões e gestão das plataformas

- **Gestão das plataformas pelo Camofox (usuário, 10:16; ver D-004):** configurações das redes da loja são feitas pelo agente via Camofox (trinômio agente+camofox+jev, perfil `profile-fb`): ligar o **"Adicionar rótulo de IA"** em cada post/Reel/Story, ajustar categoria, Sobre/bio, capa e demais campos da Página. Guardrails da D-004 valem: navegação humana, sem ação em massa, tempo humanizado, todo print pelo Jev, pausar a qualquer alerta de bot. Toda mudança visível ao público (capa, Sobre, categoria, nome, publicação) só depois da aprovação do usuário ao texto/imagem exato.
- **Coordenação:** `fb_agent.py`/sessão `profile-fb` têm dono no outro agente; a frente social usa a sessão em janela combinada, sem login nem renovação própria (uma identidade por sessão).
- **Aviso de IA:** na bio/Sobre e no rótulo nativo de cada peça. "AI-generated profile" do IG fica desligado até haver persona virtual.
- **Decisões fechadas hoje:** canal da marca/produto agora, persona virtual depois; mídia mista (maioria gerada); legenda sem preço com CTA no direct; IG ainda não profissional nem ligado à Página; Gamma só auxiliar; fita + impressão 3D na identidade; ADB pausado (D-004).
- **Proposta (aguarda aprovação):** regra conciliadora — produto fiel ao catálogo, sem inventar especificação; bruto real autorizado tem preferência; cenário e pessoas podem ser gerados; sem fidelidade garantida, a peça se declara prévia/simulação.
- **Ordem definida pelo usuário (10:16):** 1) registros; 2) nova capa da Página (fita + 3D, recorte seguro), discutindo antes as ferramentas do usuário para a capa.

## Registro 2026-11-16 ~10:25 — ferramentas pagas do usuário no pipeline

- **Pangram (detector de IA):** etapa fixa antes da aprovação de todo texto público; auditoria de tom da Ana por amostra anonimizada (relatório, sem mexer em produção). Ver `docs/decisoes/D-005-...pangram...md`.
- **Mobbin:** referência de composição (conectado).
- **Magic Patterns:** protótipo do site/catálogo da loja e do painel reduzido; telas "site para printar" para post/carrossel (conectado).
- **Framer:** publicação do site/catálogo (a conectar quando chegar a hora).
- **Gamma:** auxiliar de still/carrossel (créditos do plano).
