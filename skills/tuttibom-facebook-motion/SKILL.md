# Skill: tuttibom-facebook-motion

- **Marca:** TuttiBom — fita de cetim personalizada e itens
  impressos em 3D, no Cariri (Juazeiro do Norte / Crato /
  Barbalha).
- **Rede:** Facebook — Reels e Stories 9:16 (1080×1920). Só
  este formato nesta skill.
- **Função:** definir O QUE o motion de um reel precisa
  satisfazer — zonas seguras, densidade, classificação,
  motion board e QA. Esta skill não renderiza nada: quem gera
  a mídia é o Muse, com FFmpeg/código, conforme
  `docs/motion-graphics-codigo.md` e
  `skills/tuttibom-estudio-criativo/`.
- **Agentes que usam:** Conteúdo (criativo via Muse) e
  Revisão/Jev.
- **Fase:** F4 (campos de motion board no contrato `Criativo`)
  e F6 (reel de teste).
- **Produtos:** fita de cetim personalizada (15/22 mm; 10/25/50
  m; hotstamp Preto/Dourado/Prata) e impressão 3D. Só dados do
  catálogo — nunca inventar medida, preço, prazo ou material.

Adaptada de `formula100k/motion-reels-f100k` (ver nota de origem
no fim). Não é cópia: é reescrita em PT-BR, na voz TuttiBom,
mantendo só as regras — a ferramenta da fonte foi descartada
por inteiro.

## 1. Princípios e travas

Estas travas valem mais que qualquer regra desta skill.

1. **Nada publica sem a aprovação do usuário ao texto exato.**
   O trabalho chega sempre como rascunho primeiro — storyboard
   e motion board antes do render, stills de prova antes do
   .mp4 completo.
2. **O criativo é do Muse.** O Paperclip pede, o Muse entrega.
   Esta skill define as regras do motion; o render é Muse com
   FFmpeg/código.
3. **O S10 via ADB é o único caminho de escrita** que toca a
   conta da loja.
4. **Mídia 100% fictícia**, gerada por IA ou código. Zero uso
   de foto ou vídeo real de cliente. O produto no vídeo é um
   render fictício e realista — exemplo ilustrativo do que a
   personalização pode ser, nunca foto de produção real nem
   prova de pedido real.
5. **Regra de IA:** seguir a regra da plataforma e ligar o
   rótulo quando exigido; nunca dizer ou insinuar que o
   conteúdo NÃO é IA; não colocar anúncio gratuito de IA na
   legenda.
6. **"Humanizador" significa texto natural e agradável para
   pessoas** — qualidade editorial, não disfarce para burlar
   detector nem para esconder automação.
7. **Sem dado pessoal de comprador no repo.** Sem preço
   inventado: preço, prazo e especificação só entram se
   estiverem no catálogo.
8. **O produto é o sujeito.** Não há pessoa real em câmera,
   não há rosto para cobrir — mas também não há rosto para
   esconder erro atrás: nada de overlay cobrindo o produto,
   o hotstamp ou o detalhe que o reel está mostrando.

## 2. Zonas seguras 9:16

Mapa do frame 1080×1920. A fonte trazia margens mortas de
200 px no topo e 250 px na base; o contrato local do projeto
(`docs/motion-graphics-codigo.md`, verificado contra o app do
Facebook no S10) é mais estrito e **é ele que vale aqui**:

```
┌────────────────────────────────┐  y=0
│         (margem morta)          │  y=0–220px    ← NADA: cabeçalho
│  ██████ ZONA SUPERIOR ██████   │  y=220–420px  ← pills / kinetic
├────────────────────────────────┤                 (top: 220px)
│  PRODUTO (não cobrir)          │  y=420–1400px ← corpo do frame
│  laterais livres: 56 px        │
│  direita: 140 px livres        │  ← botões do app
├────────────────────────────────┤
│  ██████ ZONA INFERIOR ██████   │  y=1420–1540px ← cards curtos
│         (margem morta)          │  y=1540–1920  ← NADA: botões +
└────────────────────────────────┘                 legenda (bottom: 380px)
```

- **Pills e palavras cinéticas:** `top: 220px; left: 56px;`
  (ou `right: 56px` quando o produto está à esquerda).
- **Cards:** `bottom: 380px; left: 56px; right: 56px;` — ou
  lateral (`top: 50%; width: 460px`) quando o produto está
  deslocado para um lado.
- **Conflito registrado:** a zona inferior da fonte
  (`bottom: 250px`, cards em y=1420–1670) cai dentro da
  margem morta local de 380 px e **não é adotada** até ser
  verificada no player do Facebook no S10. Até lá, card
  grande demais para caber em 1420–1540 vai para a lateral
  ou vira dois overlays menores.
- **Posição do produto:** extrair um frame no meio do vídeo
  (50% da duração) e registrar `PRODUTO_X` (left/center/
  right) e `PRODUTO_Y` (upper/full/lower). Produto centrado
  é o padrão; se estiver deslocado, os cards vão para o lado
  livre, nunca por cima dele.

## 3. Densidade e ritmo — 1 overlay a cada 5 segundos

**Esta regra não é negociável.** Nenhum trecho de 5 segundos
pode ficar sem motion graphic ativo.

- **Mínimo:** `duração_em_segundos // 5` overlays. Um reel de
  30 s precisa de pelo menos 6; um de 60 s, pelo menos 12.
- **Preenchimento de gaps:** se o conteúdo natural gerar
  menos overlays que o mínimo, preencher o gap com variedade
  — rodar entre palavra cinética, pill de ambiente e citação,
  sem repetir o mesmo tipo duas vezes seguidas. Se o trecho
  disser um número do catálogo, usar pill de dado
  ("22 mm", "50 metros", "3 a 5 dias úteis").
- **Durações típicas de preenchimento:** palavra cinética
  3–4 s; pill de dado 4–5 s; pill de ambiente 4 s; citação
  5–6 s.
- **Variedade obrigatória:** nenhum reel se apoia em 1–2
  tipos. Objetivo: ≥3 tipos distintos (reel até 45 s) ou ≥4
  (acima de 45 s), e nenhum tipo acima de 45% do total. Se um
  tipo dominar, converter a enumeração mais clara em card de
  capítulo, a frase mais forte em citação e o maior contraste
  em card comparativo.
- **Animação:** toda animação usa ease-out ou spring, nunca
  interpolação linear seca. Entrada e saída em todo overlay
  (saída 0,5–0,6 s antes do fim do clip). Elementos múltiplos
  entram em stagger de 0,15–0,18 s. Não repetir o mesmo ease
  em todos os overlays do vídeo. A entrada começa no mínimo
  0,08 s depois do início do overlay, nunca exatamente nele.

## 4. Classificação intenção → template

Agrupar o roteiro em blocos de 5–10 segundos e classificar
cada bloco pela INTENÇÃO, não pela frase literal. A tabela é
generosa de propósito: repartir os 6 tipos, não cair sempre
em pill + card de interface.

| Intenção do trecho | Template | Exemplo TuttiBom |
|---|---|---|
| Contraste / mudança entre dois estados | Card comparativo ANTES/AGORA | Dourado vs. Prata; 15 mm vs. 22 mm; fita comum vs. personalizada |
| Enumeração de passos, razões, jeitos | Card de capítulo com lista | "3 jeitos de usar fita personalizada"; passos da encomenda |
| Tela / pedido / simulação mostrada | Card de interface flutuante | Simulação de pedido no chat: logo + cor + "PRÉVIA APROVADA" |
| Frase forte / ideia central do reel | Citação | "Sua marca gravada em ouro no Cariri" |
| Conceito / palavra-força solta | Palavra cinética | "DOURADO", "PRATA", "CARIRI" em grande |
| Atributo / identidade do produto | Pills | "100% Poliéster", "Hotstamp Metálico", "22 mm" |
| Dado / métrica do catálogo | Pill de dado ou card comparativo | "50 metros", "3 a 5 dias úteis" — só número do catálogo |

- **Anti-padrão:** pills e card de interface são os mais
  sobre-usados. Se um trecho cabe em pill MAS também tem
  enumeração, citação forte ou contraste, preferir o tipo
  menos usado até aquele momento. Citação e palavra cinética
  são escolhas de primeira classe, não relleno.
- **Card de interface aqui não é app de terceiro:** é a
  simulação do pedido (chat, escolha de cor, carimbo de
  prévia) — Estilo B do contrato local. Nada de mostrar
  ferramenta externa.

## 5. motion_board.json como contrato

O motion board é o contrato entre roteiro, render e QA. Um
overlay por item, com início, duração e tipo. Campos:

```json
[
  {
    "type": "pill_labels",
    "start": 2.8,
    "duration": 3.5,
    "labels": ["100% Poliéster", "Hotstamp Metálico"],
    "position": "top"
  },
  {
    "type": "comparison",
    "start": 8.0,
    "duration": 5.0,
    "title": "Dourado ou Prata?",
    "before": "Dourado Metalizado",
    "now": "Prata Elegante",
    "position": "bottom"
  },
  {
    "type": "kinetic_word",
    "start": 15.5,
    "duration": 3.5,
    "text": "CARIRI",
    "position": "top",
    "note": "preenchimento de densidade"
  }
]
```

- `type`: `pill_labels`, `stat_pill`, `ambient_pill`,
  `comparison`, `ui_card`, `chapter`, `kinetic_word`,
  `quote_pull`.
- `start` e `duration` em segundos; `position`: `top`,
  `bottom` ou `lateral`.
- Antes de renderizar: verificar densidade (nenhum gap
  > 5 s) e variedade (seção 3) sobre o board final, e
  mostrar o board ao usuário como rascunho. Mudou texto ou
  timing, novo board, nova aprovação.

## 6. Checklist de QA

Antes de entregar o reel, conferir — com o vídeo renderizado
e os stills de prova (frames de 1 s, 6 s e 12 s) na mão:

- [ ] **Densidade OK** — nenhum trecho de 5 s sem overlay
  ativo.
- [ ] **Produto nunca coberto** — nenhum overlay tapa o
  produto, o hotstamp ou o detalhe em foco.
- [ ] **Zonas seguras** — pills e cards dentro do mapa da
  seção 2; nada na margem morta do topo, da base ou da
  lateral direita.
- [ ] **Texto legível** — duração suficiente para ler cada
  overlay; nada cortado no player.
- [ ] **Animação de entrada E saída** — fluida, sem corte
  abrupto; sem interpolação linear seca.
- [ ] **Áudio intacto** — o áudio original do vídeo está
  presente (o player do Android rejeita .mp4 sem áudio;
  trilha leve ou faixa silenciosa, conforme o contrato
  local).

**Revisão/Jev:** onde fizer sentido, o Jev responde perguntas
tipadas sobre o reel — nunca texto livre, nunca aprova
publicação:

- `zona_segura?` → Box. A região do overlay está dentro do
  mapa da seção 2?
- `texto_cortado?` → Noul. Algum texto sai cortado no
  player?
- `produto_coberto?` → Noul. Algum overlay cobre o produto
  ou o hotstamp?
- `densidade_ok?` → Noul. Algum trecho de 5 s ficou sem
  overlay?
- `animacao_suave?` → Score. Entrada e saída fluidas, sem
  corte abrupto?

Confiança baixa vai para o agente de QC, nunca direto ao
usuário. Qualquer "sim" em `produto_coberto?` ou
`texto_cortado?` barra o rascunho até corrigir.

## 7. O que esta skill NÃO faz

- Não renderiza: não instala HyperFrames, não usa Supadata,
  não usa mlx-whisper, não entrega por Telegram, não usa
  Higgsfield (a própria fonte avisa que o texto da IA
  deforma). O render é do Muse, com FFmpeg/código.
- Não promete vídeo com apresentadora: não há pessoa real
  em câmera nos reels da TuttiBom.
- Não inventa dado, preço, prazo ou especificação para
  preencher densidade: gap sem conteúdo do catálogo vira
  palavra cinética ou pill de ambiente, nunca número
  inventado.
- Não publica, agenda ou impulsiona sem aprovação; isso é
  R-06, com aprovação do texto exato.
- Não usa foto ou vídeo real de cliente, nem com autorização
  nesta skill: a regra aqui é fictício sempre.
- Não posiciona texto fora das zonas seguras nem entrega
  .mp4 sem stream de áudio.

## Origem

Adaptada de `formula100k/motion-reels-f100k` (ClawHub), lida
integralmente em 2026-11-05 — linhas 0–2254, incluindo o meio
1600–1900 (templates 4 — Chapter Card — e 5 — Kinetic Word).
Licença não confirmada — nenhuma licença é afirmada aqui.
Aproveitados: mapa de zonas seguras 9:16, densidade de
1 overlay/5 s com preenchimento de gaps, tabela de
classificação intenção→template, motion_board.json como
contrato e checklist de QA. Descartados: HyperFrames, Supadata,
mlx-whisper, entrega por Telegram, Higgsfield, os 9 templates
HyperFrames como estão e a premissa de vídeo com apresentadora.
Alinhada a `docs/motion-graphics-codigo.md` e a
`skills/tuttibom-estudio-criativo/` — onde o contrato local é
mais estrito (zonas seguras), ele prevalece; ver seção 2.
