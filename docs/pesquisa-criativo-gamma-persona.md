# Pesquisa — criativo gerado (Gamma) e persona do canal

> Rascunho, 2026-11-16 ~09:35 (America/Fortaleza). Só pesquisa e
> proposta. Nada publicado, nenhum segredo, nenhum dado de comprador.
> Não gasta crédito da conta Gamma neste passo (o conector MCP não
> foi acionado para gerar).
>
> Motivo: o José confirmou que **não há fotos reais suficientes**;
> a maior parte dos criativos será **gerada**. Ele tem conta e API
> do Gamma, usa pouco, quer dar mais finalidade, e diz que está na
> **versão 5**. A aplicação deve usar o Gamma para posts e
> carrosséis. Também pediu para pensar num canal profissional e
> comparar abordagens de persona (casal, mulher empreendedora,
> só marca/produto).

## 0. O que já vale e o que este doc muda

- **D-mídia (09:10):** misturar real autorizado e fictícia,
  sinalizando qual é qual. Este adendo **inclina o lote para
  gerada**, porque a biblioteca fotográfica não cobre o ritmo
  de um canal. Foto real autorizada continua bem-vinda quando
  houver; não é mais a base do lote.
- **D-preço:** legenda sem preço e sem frete; CTA no
  direct/Messenger. Ana não cita frete.
- **D8:** Instagram ainda não é profissional; F4 só o José
  executa. O canal começa no Facebook.
- Nada publica ou envia sem a aprovação do José ao texto e à
  mídia exatos.
- O lote `criativos/f1-lote-01.md` **não foi reescrito aqui**.
  Fica como registro; **precisa ser refeito** com mídia gerada
  depois que o José decidir tema, fluxo Gamma e persona (§6).

## 1. Gamma em 2026 — estado da versão 5 e da API

Pesquisa nas docs oficiais de desenvolvedor, lida em 2026-11-16.
O José está certo: **Gamma 5** é o caminho recomendado hoje.

Fontes âncora: [Explore the API](https://developers.gamma.app/get-started/understanding-the-api-options),
[Migrar Classic → Gamma 5](https://developers.gamma.app/get-started/migrate-from-classic-to-gamma-5),
[POST /agent/generations](https://developers.gamma.app/agent-gamma-5/create-agent-generation),
[Parâmetros da geração Classic](https://developers.gamma.app/guides/generate-api-parameters-explained),
[Acesso e preços](https://developers.gamma.app/get-started/access-and-pricing),
[Modelos de imagem](https://developers.gamma.app/reference/image-model-accepted-values).

### 1.1 Duas APIs no mesmo produto

| | **Gamma 5 (agente)** — recomendado | **Classic** — ainda existe |
|---|---|---|
| Criar | `POST https://public-api.gamma.app/v1.0/agent/generations` | `POST https://public-api.gamma.app/v1.0/generations` |
| Entrada | `prompt` (o brief); tom/público/idioma viram frase em `additionalInstructions` | `inputText` + `textMode` (`generate` / `condense` / `preserve`) |
| Formatos | `presentation`, `document`, `social` | Os três **e** `webpage`; também `pages[]` (até 50 páginas, site multi-página) |
| O que o agente **não** faz | `format: "webpage"` e gammas multi-página (`pages`) — recusa. Sem `imageOptions` / `cardOptions.dimensions` no request: o agente escolhe imagem e layout; proporção social se obtém com **template** já no tamanho certo, ou pela Classic | Dimensões explícitas: social `1x1`, `4x5` (padrão, feed/carrossel), `9x16` (Stories). Imagem: modelo e fonte pináveis |
| Tema | **Sem tema padrão.** Sem `themeId` ou `templateId`, o agente inventa o visual. Os dois juntos dão `400` | Sem `themeId`, usa o tema padrão do workspace |
| `numCards` | Alvo **frouxo** (pode errar por 1–2); teto do plano | Mais literal |
| Preço | Pelo **trabalho que o agente fez** (`quality`: `lite` / `standard` / `max`); a mesma prompt pode custar diferente a cada run | 1–3 créditos/card + créditos por imagem (2–125, conforme o modelo) |
| Poll | `GET /v1.0/agent/generations/{generationId}` (`gen_…`); job pode levar **até ~20 min** | `GET /v1.0/generations/{id}` |

A chave é a mesma (`X-API-KEY`). Exportação, temas, pastas e
créditos são compartilhados com o app. Auth também via OAuth
(consome os créditos de quem autorizou).

### 1.2 O que a API **faz** hoje (útil para a TuttiBom)

- Gerar **apresentação**, **documento**, **post social** e, na
  Classic, **webpage** / site multi-página.
- Gerar a partir de **template** aprovado no workspace
  (`templateId` no agente; `POST /generations/from-template` na
  Classic).
- Editar um Gamma existente com instrução em linguagem natural
  (`POST /agent/gammas/{id}/edits`).
- Listar temas (`GET /themes`), inclusive temas customizados do
  workspace — é aqui que entra a identidade TuttiBom.
- Gerar **imagem avulsa** on-brand (`POST /v1.0/images`), com
  presets de tamanho social (`social-square` 1:1, `social-portrait`
  4:5, `story` 9:16). O MCP expõe o mesmo em `generate_image`.
- Exportar `pdf`, `pptx` ou `png`. **PNG devolve um ZIP com um
  PNG por card**, não uma imagem só. Dá para pedir o export na
  própria geração (`exportAs`) ou depois
  (`POST /gammas/{id}/export`). Export **não cobra crédito**; o
  link de download expira em ~1 semana e **não está amarrado à
  chave** — tratar como segredo e baixar na hora para o Drive.
- Ler, buscar, comentar, mover, duplicar, e (plano Pro+)
  analytics de visualização.
- Idioma `pt-br` existe nos `textOptions` da Classic e no MCP
  `generate`. No agente Gamma 5, pede-se “escreva em português
  do Brasil” nas instruções.
- Qualidade do agente: `lite` / `standard` em todos os planos;
  `max` só Pro para cima.

### 1.3 O que a API **não faz** (não prometer)

- **Não publica** no Facebook nem no Instagram. Não agenda post.
- **Não é o caminho de Reel/vídeo.** Mesmo com nomes como
  `veo-3.1` no enum, a doc de modelos diz que
  `imageOptions.model` **gera só still**; esses valores não
  entregam vídeo. Vídeo da loja continua sendo gravação real,
  Higgsfield, ou outro gerador — não o Gamma.
- Gamma 5 **não gera webpage** nem site multi-página; isso
  fica na Classic. O fluxo “página estilo site para printar”
  usa Classic (`format: "webpage"` ou `document`) ou o MCP
  `generate` / `generate_multi_page_gamma` (o MCP ainda expõe
  webpage).
- No agente, **não se pina** modelo de imagem, proporção
  (`4x5` / `9x16`) nem rodapé/logo por campo de API. Para
  carrossel 4:5 repetível, o caminho seguro é um **template
  TuttiBom já no formato social**, ou a Classic com
  `cardOptions.dimensions`.
- `numCards` no agente não é contrato. Texto “preserve”
  no agente é só pedido no prompt, **sem validação** — se a
  legenda aprovada tiver que sair intacta, conferir o PNG
  ou ficar na Classic / MCP com `textMode: "preserve"`.
- Não controla pixel exato (1080×1350). A proporção sim; o
  recorte fino, se precisar, é no `media` (FFmpeg) depois do
  export.
- Esgotar crédito: `403 insufficient_credits`. Concorrência:
  2 jobs de agente no Free, 10 no pago (`429`). Free: até
  **10 cards** por gamma; pago: até **100**.

### 1.4 Créditos (ordem de grandeza, não orçamento)

A conta do app e a API **dividem o mesmo saldo**.
`GET /me` lê o saldo sem gastar. Auto-recarga é o que a
própria Gamma recomenda para não falhar no meio do lote.

Na Classic, um carrossel curto (5 cards, imagens num modelo
barato) fica na casa de dezenas de créditos; modelos premium
sobem rápido (a doc ilustra “socials com 30 cards + 30 imagens
ultra” na casa de 930–3900). No Gamma 5, o custo é o trabalho
do agente: medir com 2–3 prompts reais e ler
`credits.deducted` — não chutar.

Não registrar aqui o plano, o saldo nem a chave do José.

### 1.5 Conector Gamma MCP (já instalado neste bot)

O namespace `user-Gamma` está **ready**. É uma opção real para
gerar rascunhos da TuttiBom **já agora**, na conversa, com o
login do José — sem esperar o adapter na Ponte. As tools
cobrem o recorte que nos interessa: `generate` (com
`format: "social" | "presentation" | "document" | "webpage"`,
`cardOptions.dimensions` incluindo `4x5` e `9x16`,
`exportAs: "png" | "pdf" | "pptx"`, `textOptions.language: "pt-br"`,
tema e pasta), `generate_from_template`,
`generate_multi_page_gamma`, `generate_image`, `edit_gamma`,
`export_gamma`, `get_themes`, `get_folders`, leitura e busca.

Toda geração ou edição via MCP **gasta crédito** do mesmo
jeito que a API. Leitura, busca e export, segundo a doc,
não gastam. Este levantamento **não chamou** tool de geração.

Uso proposto no curto prazo: o bot gera o rascunho, exporta
PNG, põe no Drive `Pendentes/`; o José aprova. A aplicação
(Ponte), no médio prazo, fala com a API REST — o MCP não
substitui um adapter no servidor, mas serve para validar
tema, template e qualidade antes de gravar código.

## 2. Como a comunidade usa o Gamma para post e carrossel

Dois fluxos pedidas pelo José aparecem, com nomes diferentes,
na doc e na comunidade. Nenhum deles publica sozinho — o
passo final é exportar PNG (ou PDF→PNG) e subir na rede.

### Fluxo A — “apresentação → slides viram carrossel”

É o mais documentado.

1. Gerar um Gamma no formato `social` (4:5 para feed/carrossel;
   9:16 para Stories) **ou** uma apresentação e depois exportar
   cada card.
2. Exportar **PNG** (ZIP com um arquivo por slide) ou PDF e
   rasterizar.
3. Subir os PNGs **na ordem** no Facebook/Instagram como
   carrossel. A primeira lâmina é o gancho.

A própria Gamma ensina a exportar slides como PNG para social
e e-mail: [Export Slides as PNG](https://gamma.app/cs/explore/content/guides/export-slides-as-png-images-social-email).
O produto “social posts” está em
[gamma.app/products/social-media/social-posts](https://gamma.app/products/social-media/social-posts)
(a página oficial existia na busca; o fetch direto desta
rodada estourou tempo — reler na hora de implementar).

Comunidade:

- r/GammaApp, *How do I make social media posts… dimensions
  for Instagram vs LinkedIn*: criar em Social, 4:5 para
  carrossel IG, exportar cada card em PNG —
  https://www.reddit.com/r/GammaApp/comments/1s1oj79/how_do_i_make_social_media_posts_in_gamma_any/
- r/AIAssisted, *Create engaging social media carousels with
  Gamma* —
  https://www.reddit.com/r/AIAssisted/comments/1kigmcp/create_engaging_social_media_carousels_with_gamma/
- r/GammaApp, alguém perguntando se o formato social “parece
  nativo ou só um deck redimensionado” (dúvida útil: sempre
  revisar o PNG no tamanho do feed antes de aprovar) —
  https://www.reddit.com/r/GammaApp/comments/1v49vu3/has_anyone_actually_used_gammas_social_post/
- Automação n8n/Make (dez/2025): planilha → Gamma a partir de
  **template** → PDF→PNG (CloudConvert) → postar. A autora
  recomenda **aprovação humana** para negócio pequeno. No
  TuttiBom o post automático **não entra** (regra já fechada).
  Artigo + vídeo: https://www.sabrina.dev/p/gamma-ai-automation-carousels-social-media

### Fluxo B — “página estilo site para printar”

Menos comum na comunidade de carrossel, mas é capacidade
oficial: `format: "webpage"` (Classic / MCP) ou documento
tipo one-pager, às vezes publicado no subdomínio da Gamma.
O uso prático para a loja não é “ter um site no ar”, é
**uma página visual rica** (vitrine de cores, ocasiões, como
pedir) que se exporta em **PDF** ou se captura em PNGs para
o feed, para mandar no direct, ou para imprimir uma folha
de mostrário.

Como o agente Gamma 5 **recusa** webpage, este fluxo fica
na Classic ou no MCP. Não precisa estar no ar (`publish: true`
só se o José pedir um link; não é necessário para printar).

### O que a comunidade acerta e o que não copiar

- Acerta: **template de marca** + export PNG + conferir a
  primeira lâmina como gancho.
- Não copiar: postar no automático (Blotato etc.). No TuttiBom
  o clique de publicar é do José.
- Limite honesto (comparativos 2026): o Gamma é forte em
  deck/carrossel a partir de um brief; não substitui um
  estúdio de vídeo nem tem o recorte fino do Canva. Fonte:
  [Gamma vs Canva, 2026](https://www.yuzoki.com/compare/gamma-vs-canva).

## 3. Como a aplicação usaria o Gamma (Ponte + aprovação)

A Ponte hoje tem `media` (só `FFmpegStamper`) e a pasta
`ideation/` **vazia**. Não há adapter de Messenger/Instagram.
O lugar certo de um cliente Gamma é um adapter **novo** em
`ponte/ponte/adapters/ideation/` (ou um módulo `gamma` ao
lado de `media`), **fora do Deskcomm**, sem fork. A chave
fica no cofre, nunca no repo, no chat ou neste doc.

### Cinco passos do lote (sempre rascunho até o José aprovar)

1. **Preparar a casa no Gamma (uma vez, o José no app):** tema
   TuttiBom (cores, fonte, logo) e 2–3 **templates** no
   workspace: carrossel 4:5 (5–7 cards), post único 4:5,
   Story 9:16. Sem isso o agente Gamma 5 inventa o visual.
2. **Brief fechado** (texto já no tom da persona, **sem preço
   e sem frete**, CTA no direct; cores só as 18 disponíveis;
   tipo de mídia = gerada, com rótulo de IA). A aplicação
   (ou o bot via MCP, no começo) chama a API: de preferência
   `POST /agent/generations` com `templateId` + `format:
   "social"` + `exportAs: "png"`; webpage/mostrário pela
   Classic se for o Fluxo B.
3. **Poll** até `completed`, baixar o ZIP de PNGs **na hora**
   (o `exportUrl` é secreto e expira). Opcional: carimbo ou
   ajuste fino no `media` (FFmpeg). Gravar na pasta
   `Pendentes/` da Biblioteca e numa linha da fila, com o
   `gammaId` (não o token, não o exportUrl).
4. **O José aprova a peça exata** (ou pede `edit` / nova
   geração). Nada sobe na Página antes desse clique.
5. **Publicar** é passo separado (Business Suite ou ADB, F2).
   A aplicação não posta. Métricas voltam no ciclo seguinte.

Lote em série: respeitar o teto de jobs simultâneos; ler
`credits.remaining`; parar se faltar crédito, em vez de
falhar no escuro.

Enquanto o adapter não existe, o **MCP já instalado** faz
os passos 2–3 na conversa. Não misturar isso com Camofox
nem com a frente P7.

## 4. Referências de lojas parecidas

Referência de **formato e gancho**, não de texto, preço ou
arte para copiar. Perfis e sites checados por busca em
2026-11-16; o conteúdo do feed muda — olhar o perfil na
hora de montar o lote novo.

### Brasil

- **JN Fitas Personalizadas** — operação grande, muitas cores,
  uso em laço, convite, lembrancinha e embalagem de lojista.
  Site: https://jnfitaspersonalizadas.com.br/ —
  Instagram: https://www.instagram.com/jnfitas/
  O que observar: volume de produto no grid, variedade de
  ocasião, prova social de quantidade (“anos no mercado”),
  pouco “personagem”; o produto carrega o canal.
- **Mimos Delicatto** — fita de cetim personalizada (22 e
  38 mm, dourado/prata) + gráfica de festa. Instagram:
  https://www.instagram.com/mimosdelicatto/ —
  Facebook: https://www.facebook.com/mimosdelicatto —
  loja: https://mimosdelicatto.com.br/fitas-cetim-personalizadas/
  O que observar: catálogo visual direto (largura, metragem,
  cor de impressão) e presença simultânea IG + Facebook.
- **Fenix Design Studio** (RJ) — fita, laço, etiqueta, alça;
  discurso “crie a sua”.
  https://www.fenixdesignstudio.com.br/fitas
- **Easy Art** — hotstamp, prazo de produção explícito, fala
  com lojista e festa.
  https://www.easyart.com.br/fita-de-cetim-personalizada-30mm-50-metros-preto
- **@sdx_boutiquedelacos** (Cuiabá, envio BR) — loja menor,
  tom de pessoa (“Paula”), especialidade em hotstamp no bio.
  https://www.instagram.com/sdx_boutiquedelacos/
  O que observar: escala parecida com a TuttiBom; o rosto
  ou o nome da artesã aparece, mas o grid ainda é produto.

### Fora do Brasil

- **Anything Ribbons** — Reels de impressão de fita para
  *wedding favors* e embalagem; processo na frente.
  Ex.: https://www.instagram.com/anythingribbons/reel/Cgu37RkjiZ5/
  Perfil: https://www.instagram.com/anythingribbons/
- **For Ribbons’ Sake** (UK) — fita de cetim com foil,
  monograma, nome e data de casamento.
  https://forribbonssake.co.uk/
- **Printed Wedding Ribbons** — recorte estreito em favor de
  casamento.
  https://printedweddingribbons.com/

### Ganchos e formatos que se repetem (e servem à TuttiBom)

- Close da **textura + impressão** (hotstamp dourado/prata
  sobre cetim) — o diferencial visível.
- **Processo** (fita saindo impressa, laço na caixa) em vídeo
  curto; no nosso caso isso ainda é gravação ou Higgsfield,
  não Gamma.
- **Carrossel de ocasião:** casamento, aniversário, confeitaria,
  marca da loja — uma lâmina, uma ideia; a última é CTA
  (“me chama no direct”). Sem preço, no nosso caso.
- **Cartela de cores** só com o que está disponível.
- Dois públicos no mesmo canal, em peças separadas: festa /
  presente **e** lojista que quer fita com a marca.
- Gancho na primeira lâmina (pergunta ou antes/depois). Evitar
  isca de engajamento e depoimento com dado de criança.

## 5. Persona do canal — comparação e recomendação

O José pediu para pensar num canal profissional e comparou
três caminhos, inclusive influencer virtual. Abaixo, com as
travas que já existem: a Ana **nunca se apresenta como virtual
por conta própria**; não enganar o comprador; conteúdo de IA
com rótulo; Higgsfield e ElevenLabs já estão conectados no
bot (úteis para vídeo/voz **se** essa decisão existir — não
foram usados aqui).

### Regras da Meta que pesam nesta escolha (2026)

- No Facebook, Instagram e Threads o rótulo visível passou de
  “Feito com IA” / “Made with AI” para **“Informações de IA”**
  / “AI info” (e, em algumas telas do IG, “AI content”).
  Fontes: [Newsroom, fev/2024](https://about.fb.com/news/2024/02/labeling-ai-generated-images-on-facebook-instagram-and-threads/),
  [abordagem da Meta, abr/2024](https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/).
- **Obrigação de declarar** no post: vídeo **fotorrealista** e
  áudio **realista** criados ou alterados com IA. **Imagem
  ainda não tem obrigação** de auto-declaração, mas a Meta
  pode rotular sozinha se detectar C2PA/IPTC, e pode penalizar
  quem omite quando a declaração é exigida. No TuttiBom:
  declarar no vídeo/áudio gerado; nas imagens geradas, rotular
  na arte e na legenda (já é D-mídia) e aceitar o selo da
  plataforma se ele aparecer.
- Desde **31/08/2026**, perfil do Instagram que **apresenta uma
  pessoa gerada por IA** (influencer virtual) precisa do rótulo
  de perfil **“AI-generated profile”**. Sem o rótulo, a Meta
  pode tirar o perfil da recomendação (Reels/Explore). Quem
  rotula por conta própria não perde alcance por isso. Usar IA
  só para arte, legenda ou edição **não** exige esse rótulo de
  perfil. Fontes: [blog dos Creators](https://creators.instagram.com/blog/ai-generated-profile-label),
  [Help Center](https://help.instagram.com/1555776438852001).

### Comparação

| | (a) Casal | (b) Mulher empreendedora criativa | (c) Só marca / produto |
|---|---|---|---|
| Encaixe no nicho | “Casamento e festa” combina com casal, mas é ficção cara de manter | Muito comum em loja de laço/festa no BR; cativa, porém **não é o José** | O que as lojas maiores do recorte já fazem (produto no grid) |
| Custo e esforço | Dois rostos, dois corpos, consistência em foto e vídeo | Um personagem; Higgsfield ajuda na imagem, ElevenLabs na voz; ainda assim cada Reel pede direção | Gamma + tema dá conta do lote estático; vídeo de processo quando houver |
| Consistência | Frágil (dois personagens envelhecem/mudam) | Média-alta se houver bible de personagem; quebra se o atendimento “for ela” | Alta: logo, cor, cetim, tipo |
| Meta / rótulo | Se os dois forem IA, rótulo de perfil no IG + rótulo no conteúdo | Idem, se for persona virtual | Só rótulo de **conteúdo** nas peças geradas; perfil da loja continua sendo a loja |
| Risco de reputação | Alto, se o casal “conversa” no direct | **O mais alto** neste conjunto: o comprador manda nome de criança, logo e data de festa a alguém que não existe | Baixo, se a peça diz que é gerada e o atendimento é honesto |
| Relação com a Ana | Conflito: quem fala no Messenger? O casal ou a Ana? | Idem, pior: uma mulher inventada não pode ser a voz do WhatsApp | A voz já existe (`persona-interacao.md`); a Ana atende; o José é o produtor |

### Recomendação

**Começar pelo (c): canal da marca TuttiBom, com o produto no
centro.** Carrosséis e posts gerados no Gamma (tema + template),
sinalizados como mídia gerada; vídeo de processo **real** quando
o José gravar, ou gerado à parte (Higgsfield) com rótulo, sem
inventar um rosto que “é da loja”. A voz do canal é a persona
já escrita — acolhedora, direta, sem pressa — não um personagem
de ficção.

Por quê: a loja vende confiança (prova antes de produzir, nome
certo na fita). Uma influencer virtual, casal ou mulher, vira
o assunto e exige transparência pesada (rótulo de perfil no
IG, e mesmo assim o direct não pode fingir que é ela). O custo
de consistência em imagem e vídeo come o ganho de “canal
profissional”. As referências que mais vendem fita personalizada
sustentam o grid com **produto e processo**, não com novela.

**Face humana, se quiser calor no Reels/Stories:** o próprio
José (ou alguém real que aceite aparecer), em pedaços curtos de
bastidor — “produtor”, não personagem. Isso não pede rótulo de
perfil de IA.

**Influencer virtual (a ou b):** só num segundo momento, se o
José quiser testar com rótulo de perfil ligado, peças claramente
ficcionais, e **nunca** no atendimento (Ana/WhatsApp/Messenger
não “viram” essa pessoa). Não é o passo do lote F1.

## 6. Decisões para o José

- **G1. Tema e templates no Gamma.** Autoriza criar (no app, com
  ele) um tema TuttiBom e 2–3 templates (carrossel 4:5, post
  4:5, Story 9:16)? Sem isso o lote refeito não fica consistente.
- **G2. Motor padrão.** Gamma 5 + template para post/carrossel;
  Classic/MCP só quando for webpage/mostrário (Fluxo B). Concorda?
- **G3. Primeiro lote refeito.** Quantas peças, e quais fluxos
  no começo (só A = carrossel/post, ou A + um mostrário estilo
  site para printar)? O `f1-lote-01.md` espera essa resposta
  para ser reescrito com mídia gerada.
- **G4. Persona.** Confirma a recomendação (c) marca/produto,
  com ele em vídeo de processo se quiser? Ou quer testar
  influencer virtual já com rótulo de perfil?
- **G5. Onde gerar os primeiros rascunhos.** Pelo **MCP já
  ligado** (rápido, gasta crédito da conta dele, aprovação
  peça a peça) e só depois o adapter na Ponte? A chave da API
  não entra no chat.
- **G6. Vídeo.** Continua “existente + a criar” (gravação),
  com Higgsfield só se ele pedir, e Gamma fora do Reel?

## 7. Fontes (URLs)

- Gamma API / v5: https://developers.gamma.app/get-started/understanding-the-api-options — https://developers.gamma.app/get-started/migrate-from-classic-to-gamma-5 — https://developers.gamma.app/agent-gamma-5/create-agent-generation — https://developers.gamma.app/generations-classic/create-generation — https://developers.gamma.app/guides/generate-api-parameters-explained — https://developers.gamma.app/get-started/access-and-pricing — https://developers.gamma.app/reference/image-model-accepted-values — https://developers.gamma.app/workspace/list-themes
- Gamma produto (social / export PNG): https://gamma.app/products/social-media/social-posts — https://gamma.app/cs/explore/content/guides/export-slides-as-png-images-social-email
- Comunidade: https://www.reddit.com/r/GammaApp/comments/1s1oj79/how_do_i_make_social_media_posts_in_gamma_any/ — https://www.reddit.com/r/AIAssisted/comments/1kigmcp/create_engaging_social_media_carousels_with_gamma/ — https://www.reddit.com/r/GammaApp/comments/1v49vu3/has_anyone_actually_used_gammas_social_post/ — https://www.sabrina.dev/p/gamma-ai-automation-carousels-social-media
- Meta / Instagram (rótulos): https://about.fb.com/news/2024/02/labeling-ai-generated-images-on-facebook-instagram-and-threads/ — https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/ — https://creators.instagram.com/blog/ai-generated-profile-label — https://help.instagram.com/1555776438852001
- Lojas: URLs no §4.
