# Motion Graphics por Código — tuttibom-estudio-criativo

> Adaptação, 2026-11-01, do documento "Arquitetura de Motion
> Graphics por Código (tuttibom-estudio-criativo)". A arquitetura
> v2 já previa Remotion / HyperFrames / FFmpeg na Camada 4
> (Geração System 2); este documento formaliza o contrato de
> engenharia visual. Não muda guardrails: o estúdio produz, nunca
> publica, nunca inventa especificação ou preço, nunca expõe nome
> de cliente real.

## Princípio: motion híbrido

Nunca postar só uma tela com texto piscando (template genérico).
O código (React/Remotion/Canvas) cria camadas cinemáticas,
tipografia cinética, máscaras de privacidade elegantes e UI
animada **por cima dos vídeos e fotos reais** da fita saindo em
hotstamp e da impressora 3D trabalhando.

Vantagens que justificam o caminho por código, e não IA
generativa pura:

1. **Parametrização total (JSON → vídeo):** uma composição mestre,
   e só as props mudam — fita 15 mm, fita 22 mm, chaveiro 3D de
   romaria, kit confeiteira — mantendo 100% da brand sheet
   (fontes, cores, margens) quando ela estiver validada.
2. **Anonimização elegante via código (privacy masking):** em vez
   de borrão feio, um badge flutuante animado (glassmorphism)
   posicionado exatamente sobre a área sensível, ou corte nos
   frames limpos, exibindo especificação técnica (ex.: "Hotstamp
   Dourado Metalizado · 22 mm"). Nome de cliente real nunca vai
   para o criativo final sem autorização.
3. **Zero alucinação de produto:** o produto no fundo é 100% real
   (brutos), respeitando o guardrail de nunca usar prova falsa de
   produto; só o design ao redor é gerado.

## Os 4 estilos (templates/motion/)

### Estilo A — Híbrido Cinético B-Roll (Reels e Stories de processo, 15–20s)

- Fundo (`<OffthreadVideo>`): vídeo real da fita rosa/branca
  saindo da impressora ou bico da impressora 3D depositando camada.
- 0,0–2,5s (hook): tipografia cinética palavra por palavra com
  física de mola (`spring({ damping: 14, stiffness: 180 })`) e card
  translúcido com blur (`backdrop-filter: blur(12px)`), ex.:
  "Sua marca gravada em ouro no Cariri".
- 2,5–12,0s (callouts técnicos): linhas guia animadas (SVG
  `stroke-dashoffset`) apontando para o brilho metálico, com
  pílulas em stagger (5 frames de atraso em cascata): "100%
  Poliéster" → "Hotstamp Metálico" → "A partir de 10 metros".
- 12,0–18,0s (CTA local): card inferior animado simulando barra
  de busca ou mensagem do Messenger: "Juazeiro · Crato ·
  Barbalha | Peça sua prévia".

### Estilo B — UI Launch Reel / Simulador de Pedido (quebra de objeção)

Mostra como é fácil encomendar, já que no Facebook o cliente
manda logo/texto pelo chat antes de produzir:

- Cena 1 (0–4s): interface estilo chat — entra "sua-logo.png" +
  escolha de cor (Dourado Metalizado).
- Cena 2 (4–9s): carimbo animado "PRÉVIA APROVADA" com escala
  elástica, cortando para o vídeo real da fita sendo impressa.
- Cena 3 (9–15s): contador "Produção: 3 a 5 dias úteis no Cariri"
  + foto final do laço pronto na caixa.

### Estilo C — Split-Screen Comparativo Dinâmico (Stories de escolha)

Para Dourado vs. Prata ou 15 mm vs. 22 mm:

- Divisão diagonal ou vertical animada por código (clip-path
  interpolado).
- Topo: fita preta com gravação Prata Metalizado; embaixo: fita
  rosa/marrom com gravação Dourado Metalizado (exemplos genéricos,
  sem nome de cliente).
- Dois botões pulsantes desenhados via código no centro —
  "A: Dourado Real" vs. "B: Prata Elegante" — induzindo o toque na
  enquete dos Stories ou o comentário no Feed.

### Estilo D — Editorial Collage & Spec-Sheet Animada (anúncio, 15–25s)

Vídeo-catálogo vivo para Marketplace/Feed:

- Fotos reais de rolos empilhados e laços em caixas entrando com
  câmera virtual 2.5D (zoom lento + sombra projetada).
- Tabela animada mostrando a diferença visual de tamanho entre
  15 mm (festa/lembrancinha) e 22 mm (lojista/confeitaria) e as
  metragens 10 m, 25 m, 50 m — só dados que estão no catálogo.

## Regras técnicas de renderização (contrato, para não falhar no S10)

O upload no app do Facebook no Galaxy S10 Lite é o ponto mais
sensível da rotina R-06. Parâmetros determinísticos:

1. **Física e ritmo (proibido linear):** toda animação usa
   ease-out ou spring, nunca interpolação linear seca. Transições
   rápidas (0,3–0,5s) e tempo de leitura confortável.
2. **Safe zones do Facebook, 9:16 (1080x1920):** nunca posicionar
   texto ou preço nos 220 px superiores (cabeçalho de
   Stories/Reels), nem nos 380 px inferiores e 140 px da lateral
   direita (botões de curtir, comentar, compartilhar e legenda).
3. **Pré-renderização de prova (stills antes do render):** antes
   de renderizar ~450 frames, extrair com `npx remotion still`
   (ou equivalente) **3 imagens estáticas — frames de 1s, 6s e
   12s** — e mostrar ao usuário no chat. Só renderizar o .mp4
   completo após aprovação visual.
4. **Encode compatível com Android/Facebook (FFmpeg pós-render):**
   - Resolução: 1080x1920 (9:16, Stories/Reels) ou 1080x1350
     (4:5, Feed/Marketplace), 30 fps.
   - Vídeo: H.264 (libx264), perfil high, pixel format yuv420p
     — yuv444p pode dar tela preta ou falha no upload no app
     Android do Facebook.
   - Áudio: sempre incluir stream de áudio AAC, mesmo sem
     locução — trilha instrumental leve livre de direitos ou
     faixa silenciosa (`-f lavfi -i anullsrc`) — porque o player
     de Reels/Stories no Android às vezes rejeita ou engasga com
     .mp4 sem áudio.

## Entradas e saídas do estúdio

- **Entradas obrigatórias:** trecho do catálogo, roteiro e
  prompts exportados do caderno efêmero do NotebookLM, mídia
  bruta real ou asset genérico aprovado. Sem brand sheet validada
  ou com dado de cliente real sem anonimização, o estúdio não
  inicia o render — fica no storyboard.
- **Saídas:** ativo final versionado no Drive
  (`TuttiBom/02_Criativos/`, `AAAAMMDD_produto_formato_rede_v01.ext`),
  ficha em `ops/`, linha em `ops/fila-publicacao.md` como
  rascunho. Publicação continua sendo R-06, com aprovação e
  prova por screencap.
