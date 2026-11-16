# Pesquisa — vídeo de primeira linha e referências (fitas + 3D)

> Rascunho, 2026-11-16 ~10:10 (America/Fortaleza). Só pesquisa e
> proposta. Nada publicado, nenhum segredo, nenhum dado de comprador.
> Worktree: `/home/pc/Workspace/tuttibom-ops-social`, branch
> `social/fb-ig`. Sem commit até o José validar.

Motivo: fechar o pipeline de Reels 15–30 s com motion graphics
acima do padrão de mercado; ampliar referências de **fitas
personalizadas/laços** e de **impressão 3D**; registrar onde marcar
IA no Facebook e no Instagram; auditar a Página TuttiBom Novidade
pelo print de 2026-11-16; e conciliar o “produto 100% real no
fundo” de `docs/motion-graphics-codigo.md` com a mídia gerada
(fotos reais insuficientes).

O que este doc **não** faz: não publica, não gasta crédito de
Higgsfield/Gamma/ElevenLabs, não opera o Camofox, não instala
canal novo no Agent-Reach.

## 0. Decisões já tomadas (2026-11-16)

- Canal da **marca e do produto** agora; persona virtual depois,
  sempre rotulada, nunca no atendimento.
- Aviso de IA na **bio/Sobre** e no **rótulo nativo** de cada
  plataforma.
- Mídia mista: a maior parte será **gerada**; foto/vídeo real
  autorizado entra quando houver. Legenda **sem preço** nem frete;
  CTA no direct/Messenger.
- Instagram ainda **não** é profissional nem está ligado à Página
  (F4, só o José executa).
- Gamma é **ferramenta auxiliar** já paga (créditos de post e
  carrossel). Não publica, não agenda e **não gera Reel**.
- Navegação e publicação seguem a **D-004**: Camofox (motor + Jev)
  é o navegador único; S10/ADB **pausado**. Esta frente não edita
  `fb_agent.py`.
- A loja trabalha com **fitas personalizadas e impressão 3D**.

## 1. Pipeline de Reel 15–30 s (até 6 passos)

Contrato visual que já vale: `docs/motion-graphics-codigo.md`
(estilos A–D, safe zones 9:16, stills 1 s / 6 s / 12 s antes do
`.mp4`, encode H.264 yuv420p + AAC, 1080×1920 ou 1080×1350, 30
fps). O estúdio produz e nunca publica. A menção ao upload no S10
nesse doc está **superada** pela D-004; os parâmetros de encode
continuam.

Onde roda: roteiro, Remotion e FFmpeg no **PC ou no box**. Geração
de cena, voz e música são **APIs na nuvem** (Higgsfield,
ElevenLabs; Gemini Omni se o José autorizar a conta Google).
Nada disso publica na Página.

| Passo | O que acontece | Ferramenta | Critério de parada |
|---|---|---|---|
| 1. Brief e storyboard | Tema do catálogo, gancho nos 3 s, duração 15–30 s, estilo A–D, texto na tela, CTA sem preço. Usa `templates/roteiro-video.md`. | Texto no repo / Drive | José aprova o roteiro **antes** de gastar crédito de geração |
| 2. Placa (fundo) | **Preferir bruto real autorizado** (fita em hotstamp, bico 3D). Se não houver: gerar cena 9:16 com produto fiel (passo 5). Motion Control (Kling no Higgsfield) só para transferir movimento de um bruto real — não para inventar o produto. | Real: acervo. Gerada: [Higgsfield Video API](https://docs.higgsfield.ai/docs/models/video-generation) (Kling 2.6/3.0 e Motion Control, Seedance, Wan, MiniMax/Hailuo, etc.). Alternativa: [Gemini Omni Flash](https://aistudio.google.com/docs/omni) (`gemini-omni-1.2-flash`, 3–15 s com áudio nativo). [Runway Models](https://dev.runway.com/models/catalog) (Gen-4.5 t2v/i2v; Aleph é v2v). **Veo 3.1 Preview na Gemini API foi encerrado em 22/10/2026** ([deprecations](https://aistudio.google.com/docs/deprecations)); não usar esse endpoint. | Recusar placa que invente cor, largura, gravação ou peça 3D fora do catálogo |
| 3. Motion graphics | Tipografia cinética, callouts, máscara de privacidade (se o bruto tiver nome), CTA no card inferior. Nunca postar só texto piscando. | Remotion, estilos A–D de `docs/motion-graphics-codigo.md`. Stills com `npx remotion still` nos frames 1 s, 6 s e 12 s | José aprova os 3 stills **antes** do render completo |
| 4. Voz, música e legendas | Locução curta (PT-BR), trilha instrumental, legendas estilo Reels **dentro da safe zone** (não nos 220 px de topo nem nos 380 px de base). | Voz: [ElevenLabs TTS](https://elevenlabs.io/docs/capabilities/text-to-speech). Música: [Eleven Music](https://elevenlabs.io/docs/overview/capabilities/music). Legendas: [`@remotion/elevenlabs`](https://www.remotion.dev/docs/elevenlabs/elevenlabs-transcript-to-captions) + [`createTikTokStyleCaptions`](https://www.remotion.dev/docs/captions/displaying) | Áudio AAC sempre presente (mesmo instrumental baixo). Voz realista de IA **exige** rótulo nativo (ver §3) |
| 5. Encode e ficha | FFmpeg pós-render (yuv420p + AAC). Nome `AAAAMMDD_produto_formato_rede_v01.mp4` no Drive (`TuttiBom/02_Criativos/`). Linha em `ops/fila-publicacao.md` como **rascunho**. | FFmpeg no PC/box | Arquivo versionado; rótulo de IA anotado na ficha; **status ≠ publicado** |
| 6. Publicação (outra fase) | Só depois da aprovação do texto e da mídia exatos. Caminho ativo: Meta Business Suite; Camofox com os guardrails da D-004 quando houver sessão combinada. ADB pausado. Primeiro Reel ainda **não** foi provado. | Suite / Camofox | Um item por sessão; prova por captura; nunca o estúdio publica sozinho |

Gamma entra **antes** deste pipeline, só para still/carrossel, ou
como referência de layout — não no passo 2 de vídeo.

## 2. Referências de canais (fitas e 3D)

Agent-Reach no PC **não** tem backend de Instagram, Facebook,
TikTok nem YouTube ativo (ver §6). Por isso **não há contagem de
seguidores ou views auditada nesta pesquisa**. O que segue é
canal oficial ou loja identificada por site/link-in-bio, mais o
padrão do que postam. Números de agregadores (Socialcounts,
PicMany, Viralist) **não foram adotados**.

### 2.1 Fitas personalizadas e laços

| Canal | Onde | O que postam / gancho | O que aproveitar (padrão, não cópia) |
|---|---|---|---|
| [Fitas Progresso](https://link.fitasprogresso.com.br/) — fabricante BR | [IG](https://www.instagram.com/FitasProgresso/), [Facebook](https://www.facebook.com/FitasProgresso/), [TikTok](https://www.tiktok.com/@fitasprogresso), [YouTube](https://www.youtube.com/fitasprogresso), [site](https://fitasprogresso.com.br/), [Crie sua fita](https://criesuafita.com.br/) | Lançamento de cor/coleção, tutorial de laço e flor, “um detalhe muda tudo”, catálogo e “onde encontrar”. É indústria de fita lisa/estampada, não gráfica de logo. | Ritmo de inspiração + produto; tutoriais curtos de laço; o processo da TuttiBom (hotstamp com a marca do cliente) é o diferencial que eles **não** mostram |
| [Sinimbu Fitas](https://www.instagram.com/sinimbufitas/) | IG e [Facebook](https://www.facebook.com/sinimbufitas); [site](https://sinimbu.com.br/) | Guia de compra, lançamentos, conteúdo para distribuidor e artesão | Clareza B2B; a TuttiBom fala com lojista e festa no Cariri, não com distribuidor nacional |
| [JN Fitas](https://jnfitaspersonalizadas.com.br/) | [IG @jnfitas](https://www.instagram.com/jnfitas/), site próprio | Fita de cetim **com logomarca**, layout grátis, prazo de produção, entrega Brasil. Concorrente direto de oferta (SP, há 15 anos no site). | Mesmo produto-núcleo. Gancho de “sua marca no rolo” e prévia antes de produzir. Não copiar prazo/preço deles — só o que está no catálogo TuttiBom |
| [Mimos Delicatto](https://mimosdelicatto.com.br/) | [IG @mimosdelicatto](https://www.instagram.com/mimosdelicatto/), loja com [fita 15/22/38 mm](https://mimosdelicatto.com.br/fitas-cetim-personalizadas/) | Fita personalizada + laços e kits de festa | Foto do laço **em uso** (caixa, lembrancinha), não só o rolo |
| [Anything Ribbons](https://www.instagram.com/anythingribbons/) | IG (EUA); [Reel de processo](https://www.instagram.com/anythingribbons/reel/Cgu37RkjiZ5/) já citado em `docs/pesquisa-criativo-gamma-persona.md` | Impressão da fita no vídeo, favores de casamento, embalagem | Hipnose de processo nos 3 s: a fita saindo com o texto. É o estilo A do motion |
| [Offray Ribbon](https://www.instagram.com/offrayribbon/) | IG (marca US) | Tutorial de laço, tendência (ex.: coquette), “shop the look” | Tutorial curto funciona para alcance; na TuttiBom o CTA é o Messenger, não o shop genérico |
| [Renaissance Ribbons](https://www.instagram.com/renaissanceribbons/) | IG (marca US) | Colaboração com designer, close do desenho, “measure twice, craft once” | Close da textura e da gravação; um tema por peça |

Padrão que se repete e já estava em
`docs/pesquisa-publicacao-engajamento.md` e
`docs/plano-social-media-criativos.md`: vídeo de processo > foto
do produto parado; antes/durante/depois; pergunta binária;
personalização visível (nome ou logo aparecendo); prova local.

### 2.2 Impressão 3D

| Canal | Onde | O que postam / gancho | O que aproveitar |
|---|---|---|---|
| [Bambu Lab oficial](https://www.instagram.com/bambulab_official/) e [Bambu Lab Brasil](https://www.instagram.com/bambulab_br/) | IG, TikTok, [YouTube @BambuLab](https://www.youtube.com/@BambuLab) | Timelapse, qualidade/velocidade, AMS, comunidade de peças | Timelapse e close do bico (estilo A). Não fingir escala de fábrica |
| [Prusa 3D](https://www.youtube.com/@Prusa3D) / [IG Josef Průša](https://www.instagram.com/josefprusa/) | YouTube, IG | Hardware, Printables, transparência do processo | Bastidor honesto; “feito aqui” em vez de laboratório genérico |
| [CNC Kitchen](https://www.youtube.com/@CNCKitchen) | YouTube (também Shorts) | Teste, material, mito vs. medição | Um fato técnico por peça (material, camada, uso) — só o que o catálogo TuttiBom sustentar |
| [Slant 3D](https://www.youtube.com/@Slant3D) | YouTube / Shorts / TikTok | Gancho de “fábrica de impressão 3D”, operação, encomenda | Gancho forte nos 3 s e clareza de oferta. A TuttiBom é ateliê no Cariri: **não** imitar volume industrial |
| [3D Lab](https://www.instagram.com/3dlab_brasil/) | IG BR (filamento / loja) | Produto, dica, comunidade | Tom local BR; a TuttiBom soma o combo **peça 3D + fita** |
| [Sethi3D](https://www.instagram.com/sethi3d/) | IG BR (fabricante) | Máquina, aplicação, bastidor | Bastidor de produção nacional, sem copiar catálogo de máquina |

O diferencial da loja, já em
`docs/pesquisa-produtos-chamativos.md` e no plano diretor, é o
**combo**: chaveiro/peça 3D + laço de cetim no mesmo lugar, para
festa e comércio do Cariri. Os canais acima quase nunca cruzam
os dois produtos — é o espaço que a TuttiBom pode ocupar.

## 3. Onde marcar “Feito com IA”

Decisão do José: aviso na bio **e** rótulo nativo. Os dois se
complementam; um não substitui o outro.

### 3.1 Em cada post, Reel ou Story (obrigatório quando couber)

Facebook, ajuda oficial
[Label AI content on Facebook](https://www.facebook.com/help/7434563519957988)
(lida em 2026-11-16):

- **Obrigatório** rotular vídeo fotorrealista ou áudio de som
  realista que tenham sido gerados ou alterados digitalmente
  (inclui locução de IA). Há previsão de penalidade se não
  rotular o que é exigido.
- Imagem still **não** é de rotulagem obrigatória, mas a Meta
  pode aplicar o rótulo sozinha se detectar sinal (C2PA etc.).
  A TuttiBom **rotula mesmo assim**, por transparência e porque
  o piloto de 2026-11-01 já saiu com “Conteúdo de IA”
  (`ops/fila-publicacao.md`).
- Como ligar (Central de Ajuda, versão computador): no
  compositor do post, clicar em “AI label off” e ativar **Add
  AI label**; em Reels e Stories, o mesmo controle no menu.
  No app (já usado no piloto): ligar o rótulo na prévia, antes
  de compartilhar. Na interface em PT-BR o selo aparece como
  “Conteúdo de IA” / “AI Info”
  ([Transparency Center](https://transparency.meta.com/en-us/governance/tracking-impact/labeling-ai-content)).

Instagram: a página de ajuda
`help.instagram.com` bloqueou a leitura anônima nesta pesquisa
(HTTP 403). O mecanismo documentado de forma consistente
(mesmo requisito de vídeo/áudio da Meta) é: no post ou Reel,
ativar **Add AI label** antes de publicar; no Story, Opções →
Label AI → o mesmo interruptor. Quando o Instagram da loja
existir (F4), repetir o ritual do piloto do Facebook e
conferir o texto na própria tela.

### 3.2 No perfil / bio (aviso permanente)

- **Texto no Sobre da Página** (e na bio do Instagram, na F4):
  é o lugar que o José pediu. Rascunho, **não publicar ainda**:
  “Fitas personalizadas e impressão 3D no Cariri (Crato,
  Juazeiro e Barbalha). Parte das imagens e dos vídeos é feita
  com IA; o produto segue o catálogo. Chama no Messenger.”
- Facebook também oferece o rótulo de perfil **AI creator**,
  só no **app** (Editar perfil → AI creator → “Yes” se você
  publica conteúdo de IA com frequência). Conferir se a
  **Página** TuttiBom Novidade exibe esse controle — a ajuda
  fala em “profile”. Ligar só se o controle existir e o José
  aprovar; o Sobre em texto vale de qualquer forma.
- Instagram tem o rótulo de perfil
  [AI-generated profile](https://creators.instagram.com/blog/ai-generated-profile-label)
  (renomeado em 31/08/2026; antes “AI creator”). Serve para
  conta que **apresenta uma pessoa gerada**, não para quem só
  usa IA no processo. A própria Meta diz que quem apenas usa
  ferramentas de IA **não precisa** desse rótulo. Contas
  com pessoa fictícia **sem** o rótulo podem perder
  recomendação. **Agora não ligar** (canal da marca). Ligar
  somente se a persona virtual entrar, na fase 2.

## 4. Auditoria da Página “TuttiBom Novidade”

Fonte: print da própria Página, 2026-11-16, com o José logado
como admin (botão “Editar foto da capa” visível). Números
lidos no print, não recontados no app: **517 seguidores**,
seguindo 43; categoria **Criador de conteúdo digital**;
local **Crato, CE**. Capa rosa com rolos “Just for you”,
caixas com laço e o texto do topo **“PERSONALIZE SUAS IDEIAS”
cortado**. Logo circular com monograma T. Abas visíveis:
Tudo, Sobre, Reels, Fotos, Amigos, Mais. **Impressão 3D não
aparece** na identidade (capa e avatar são só fita).

Cinco melhorias, nesta ordem (nenhuma executada aqui):

1. **Refazer a capa com recorte seguro.** O título do topo
   está cortado no desktop do print; no celular a Meta come
   ainda mais as bordas. Uma frase só, central, legível, e
   **um recorte da impressão 3D** ao lado da fita — hoje a
   Página não conta que a loja faz os dois. Conferir a medida
   vigente em
   [foto de capa da Página](https://www.facebook.com/help/125379114252045)
   (a ajuda pediu login nesta leitura). Prova: print desktop +
   print do app, texto inteiro visível nos dois.
2. **Trocar a categoria** “Criador de conteúdo digital” por
   uma de loja/ofício (artesanato, fabricante, presente ou
   embalagem — o José escolhe a que a Meta oferecer e que
   descreva a atividade). A categoria atual comunica canal de
   conteúdo, não ateliê que vende.
3. **Completar o Sobre** com os dois produtos, a praça (Cariri:
   Crato, Juazeiro e Barbalha), o CTA para o Messenger e o
   aviso de IA do §3.2. Conferir o botão de ação (Mensagem)
   visível no cabeçalho.
4. **Rever o nome público “TuttiBom Novidade”.** “Novidade”
   parece página de recorte ou nome provisório e enfraquece a
   marca. Troca de nome é decisão e clique do José; o agente
   só recomenda.
5. **Limpar a composição e o tipo de presença.** A capa atual
   empilha muitas fotos e uma faixa diagonal pouco legível.
   Alinhar capa + logo à brand sheet (ainda a reavaliar). A
   aba “Amigos” e o “Seguindo 43” combinam com o modelo de
   criador — na F0 o José confirma se a Página está no
   formato de negócio que ele quer.

Nada disso se publica ou se edita na conta sem aprovação do
texto e da arte exatos.

## 5. Regra conciliadora — produto fiel, encenação livre

O princípio de `docs/motion-graphics-codigo.md` (“o produto no
fundo é 100% real”) existe para **impedir prova falsa**: não
inventar especificação, cor, metragem, gravação ou peça 3D.
Esse guardrail **continua no produto**. O que muda, porque não
há brutos suficientes, é o **cenário e as pessoas**.

1. **Especificação só do catálogo.** Largura (15/22 mm e as
   que estiverem listadas), material (100% poliéster, no que
   já está documentado), tipo de gravação, cores **somente**
   as disponíveis, prazos e o que a peça 3D é. Nunca inventar
   medida, cor fora de estoque ou um efeito que a loja não faz.
2. **Preferência de placa.** Havendo vídeo ou foto real
   autorizado do processo, ele é o fundo; o Remotion entra por
   cima (estilos A–D). Nome de cliente real: badge/máscara ou
   corte — não vai ao criativo sem autorização.
3. **Quando faltar bruto.** Cenário, bancada, festa, mãos e
   pessoas podem ser gerados (Higgsfield/Kling/Gemini Omni/
   Runway, ou still do Gamma). O produto na cena deve ser
   **fiel** (cor, largura, gravação, geometria 3D) ou composto
   a partir de still real. Se a fidelidade não der para
   garantir, a peça se declara **prévia/simulação**, nunca
   “pedido entregue” nem “foto real da produção”.
4. **Sinalização.** Aviso na bio (§3.2) + rótulo nativo em
   cada peça com geração, voz ou áudio de IA (§3.1) +, na arte
   ou na legenda, “prévia simulada” quando o fundo não for
   bruto real.
5. **Motion graphics por código**, nunca como único conteúdo.
6. **Persona virtual** só numa fase 2, com rótulo de perfil
   adequado, e fora do atendimento.

Esta regra prevalece sobre o “100% fictício” das skills longas
antigas e sobre a leitura literal do “fundo 100% real” quando
não houver bruto. Skills vendored **não são editadas** neste
passo (divergência já anotada no plano social, §1.3).

## 6. Agent-Reach

Instalado no PC: `/home/pc/.local/bin/agent-reach` (pipx),
**v1.5.0**. `doctor --json` em 2026-11-16, só leitura:

- **Disponíveis:** Jina Reader (página pública), RSS/Atom,
  V2EX, busca anônima de Bilibili.
- **Indisponíveis** (não instalei nem configurei): Instagram,
  Facebook, TikTok (não há canal TikTok no doctor), YouTube
  (`yt-dlp` ausente), Reddit, Exa, OpenCLI.
- Não usei cookies, tokens nem `configure`. Não li valores de
  `~/.agent-reach/config.yaml`.

Uso nesta pesquisa: o canal **web (Jina Reader)** para as
páginas oficiais da Meta, Higgsfield, Remotion e o link-in-bio
da Progresso. Canais de IG/FB/TikTok/YT **não** foram lidos
pelo Agent-Reach — daí a ausência de números de alcance.

Há atualização **v1.6.1**. Não atualizei. Se o José quiser:
“Ajude a atualizar o Agent-Reach:
https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/update.md”.

## 7. Fontes (URLs)

- D-004: `docs/decisoes/D-004-2026-11-16-camofox-navegador-unico-adb-pausado.md`
- Motion, plano diretor, engajamento, produtos, Gamma, lote F1:
  `docs/motion-graphics-codigo.md`,
  `docs/plano-social-media-criativos.md`,
  `docs/pesquisa-publicacao-engajamento.md`,
  `docs/pesquisa-produtos-chamativos.md`,
  `docs/pesquisa-criativo-gamma-persona.md`,
  `docs/plano-social-facebook-instagram.md`,
  `criativos/f1-lote-01.md`, `ops/fila-publicacao.md`,
  `templates/roteiro-video.md`
- Higgsfield: https://docs.higgsfield.ai/docs/models/video-generation — https://higgsfield.ai/higgsfield-api
- Gemini Omni / encerramento do Veo 3.1 Preview: https://aistudio.google.com/docs/omni — https://aistudio.google.com/docs/deprecations — https://ai.google.dev/gemini-api/docs/video
- Runway: https://dev.runway.com/models/catalog — https://docs.dev.runwayml.com/guides/models/
- Remotion + ElevenLabs: https://www.remotion.dev/docs/elevenlabs/elevenlabs-transcript-to-captions — https://www.remotion.dev/docs/captions/displaying — https://elevenlabs.io/docs/capabilities/text-to-speech — https://elevenlabs.io/docs/overview/capabilities/music
- Meta IA: https://www.facebook.com/help/7434563519957988 — https://transparency.meta.com/en-us/governance/tracking-impact/labeling-ai-content — https://creators.instagram.com/blog/ai-generated-profile-label
- Capa da Página (ajuda): https://www.facebook.com/help/125379114252045

## 8. Pendências do José

Além das D1 e D4–D7 já abertas no plano social:

- Aprovar a **regra conciliadora** do §5 (e o rascunho de bio
  do §3.2), antes de refazer o lote F1.
- Decidir se liga o rótulo de perfil **AI creator** no app do
  Facebook, caso a Página ofereça o controle.
- Prioridade das 5 melhorias da Página (§4), em especial a
  troca de categoria, a capa com 3D e o nome “Novidade”.
- Autorizar (ou não) gasto de crédito no Higgsfield e no
  ElevenLabs para um **Reel piloto** depois do roteiro
  aprovado; o Gamma segue só como auxiliar de still.
- Se quiser números de alcance auditados nos canais do §2:
  liberar (ou não) a instalação só leitura do OpenCLI /
  `yt-dlp` no Agent-Reach — sem isso não dá para contar
  seguidores daqui.
