# Skill: tuttibom-estudio-criativo

- **Marca:** TuttiBom
- **Conta:** conta da loja, agnóstica de rede — o ativo produzido
  aqui serve primeiro ao Facebook e, depois da primeira aprovação
  no Facebook, a outras redes como módulo novo (exemplo futuro:
  `tuttibom-tiktok-conteudo`). Por ser módulo agnóstico, como
  `tuttibom-notebooklm` e `tuttibom-observabilidade`, o nome omite
  a rede — precedente já existente no projeto, não exceção solta.
- **Função:** produzir o ativo visual finalizado (Reels/vídeo
  curto, Stories, carrossel, post estático). Produz, nunca publica.
- **Executor:** Muse na VM (Remotion / HyperFrames / FFmpeg /
  Canvas). Execução no S10 via ADB fica com
  `skills/tuttibom-facebook-conteudo/` (R-06), nunca com esta skill.
- **Produtos:** impressão 3D e fita de cetim personalizada, só com
  dados do catálogo (`catalogo/`). Nada de banco de imagem passado
  por produto próprio.
- **Região:** Cariri — Juazeiro do Norte / Crato / Barbalha.
- **Problemas específicos:** upload de vídeo é o ponto mais frágil
  no app do Facebook no S10; brand sheet existente a reavaliar
  (sem ela validada, o template de vídeo não fecha); vídeos
  brutos de ~20s podem conter nome de cliente real legível;
  `uiautomator dump` nulo no Facebook (por isso o checkpoint aqui
  é em imagem/texto no chat, não em tela do app).

## 1. Propósito

Transformar insumos brutos (`01_Brutos/` no Drive / mídia real da
loja), dados do catálogo e roteiros do caderno efêmero do
NotebookLM em ativos visuais finalizados em `02_Criativos/` —
nunca publica e nunca inventa especificações ou preços.

## 1b. Diretriz 2026-11-01 — fábrica visual 100% fictícia e realista

Decisão do usuário, aprovada em 2026-11-01, que prevalece sobre
o uso de mídia antiga nesta fábrica:

- **Zero uso das fotos e vídeos enviados anteriormente** que
  contenham impressão, nome, marca ou dado de cliente real.
  A checagem de 2026-11-01 (8 JPGs amostrados, todos com
  impressão de cliente) é o motivo prático, não só a regra.
- **Toda mídia visual do piloto e da Etapa 1 é gerada de forma
  fictícia e realista, por IA e código** (Remotion / FFmpeg /
  geração de imagem): rolos de cetim em preto, rosa, branco e
  marrom, hotstamp dourado e prateado, com inscrições fictícias
  e comerciais — ex.: "Sua Logo Aqui", "Sua Marca",
  "Lembrança Especial", "Ateliê Celebra" — e, para 3D, renders
  de peças utilitárias/decorativas (suportes, chaveiros
  geométricos, luminárias) em luz natural, destacando as camadas.
- **Honestidade do ativo gerado:** o render fictício é um
  exemplo ilustrativo do que a personalização pode ser, não uma
  foto da produção real da loja e não prova de um pedido real.
  A legenda não pode afirmar que a imagem é foto real de um
  trabalho entregue. Especificações (largura, metragem,
  material, prazo de 3 a 5 dias úteis) continuam só as do
  catálogo, nunca inventadas.
- **Copy:** foco em benefício e transformação, produção local
  no Cariri, prazos transparentes, facilidade de personalizar
  sob medida. Sem jargão robótico e sem falsa urgência ("corre
  que vai acabar").
- **Plano semanal completo só depois do piloto:** a primeira
  postagem (piloto) é desenhada e aprovada antes de qualquer
  calendário semanal/mensal. A matriz de públicos e ocasiões
  (B2B/lojistas/confeiteiras, festas, eventos esportivos e
  regionais, datas nacionais) e a cadência (máximo 3 posts por
  semana, dias alternados, nunca 3 vendas seguidas) ficam como
  desenho futuro, não como execução agora.

## 2. Gatilho

**Começa** quando há roteiro/copy gerado por caderno efêmero do
NotebookLM (ou, nesta fase de arranque, roteiro/copy aprovado em
conversa como checkpoint equivalente, registrado no repo) e mídia
bruta real ou asset genérico aprovado.

**NÃO começa** (fica no storyboard) se a brand sheet
(`00_Identidade/`) não estiver validada para render final, ou se
o ativo exigir dado de cliente real sem anonimização, ou se o
produto, preço ou prazo não estiver no catálogo.

## 3. Entradas

1. Trecho do catálogo (`produto-fita-cetim.md` ou
   `produto-impressao-3d.md`).
2. Roteiro e prompts exportados do caderno efêmero do NotebookLM
   (ou texto aprovado na conversa, até o caderno existir).
3. Mídia bruta real da loja (ex.: vídeos de ~20s da fita saindo
   em hotstamp, fotos de peças 3D) ou assets genéricos aprovados.

## 4. Passos determinísticos

1. **Sanitização de privacidade (crítico):** verificar se a
   foto/vídeo bruto contém nome, telefone ou marca de cliente
   real (como nos 21 arquivos de 30/10). Se houver, aplicar
   badge/máscara elegante via código (ver
   `docs/motion-graphics-codigo.md`) ou usar exclusivamente arte
   genérica ("Sua logo aqui" / "Personalize suas ideias").
2. **Storyboard visual:** antes de renderizar, montar storyboard
   em imagem/texto (cenas 1, 2, 3, texto na tela, cortes, paleta
   da brand sheet) e submeter ao checkpoint humano na conversa.
3. **Stills de prova:** para vídeo, extrair 3 frames estáticos
   (1s, 6s, 12s) com `npx remotion still` e mostrar ao usuário.
   Só renderizar o .mp4 completo após aprovação visual.
4. **Renderização determinística:** compilar com Remotion /
   HyperFrames / FFmpeg (vídeo) ou composição gráfica (carrossel/
   post), em 9:16 (1080x1920) para Stories/Reels e 4:5 (1080x1350)
   para Feed/Carrossel. Estilos A–D e parâmetros de encode em
   `docs/motion-graphics-codigo.md`: spring (não linear),
   safe zones (topo 220 px, base 380 px, direita 140 px livres),
   H.264 libx264, yuv420p, 30 fps, stream AAC presente.
5. **Controle de qualidade editorial (Pangram QA):** passar a
   legenda proposta pelo medidor de naturalidade editorial.
   Pangram é QA, nunca reescritor de evasão; naturalidade é
   qualidade para pessoas, não truque para detector.
6. **Versionamento e indexação:** salvar no Drive
   (`TuttiBom/02_Criativos/`) com
   `AAAAMMDD_produto_formato_rede_v01.ext` e registrar na fila
   (`ops/fila-publicacao.md`) como rascunho, nunca como publicado.

## 5. Pontos de decisão

- **Humano (sempre):** texto exato, mídia exata, storyboard,
  stills, preço (quando houver) e exceção. Mudou o conteúdo,
  nova aprovação.
- **Jev (quando entrar):** classificação de formato/adequação,
  com limiar e rota humana abaixo do limiar. Jev não gera texto,
  não aprova, não publica.

## 6. Condições de parada e rota de fuga

Parar e chamar o humano quando: dado de cliente real sem forma
segura de anonimizar, brand sheet ausente para render final,
render que falha 3 vezes no mesmo passo, mídia bruta que não
corresponde ao catálogo, ou qualquer pedido de preço/prazo não
confirmado. Rascunho nunca vira publicação em recuperação;
storyboard reprovado volta ao passo 2, não avança para render.

## 7. Saídas

- Storyboard aprovado (texto + descrição visual) no repo.
- Ativo final versionado no Drive + ficha em `ops/`.
- Linha na fila (`ops/fila-publicacao.md`) como rascunho, pronta
  para R-06 após aprovação.
- Log do que foi verificado (fonte do catálogo, anonimização
  aplicada, parâmetros de encode).

## 8. Adaptação

- **Outra rede:** mudam formato, safe zones, duração e CTA da
  rede; não mudam guardrails, aprovação, ritmo, registro,
  privacidade, nem a regra de storyboard antes de render.
- **Outro nicho/produto:** mudam catálogo, roteiro e props JSON;
  não muda a composição mestre nem o contrato de encode.
- **Outro projeto:** clonar e bifurcar o repo, trocar as
  variáveis da instância (marca, conta, produto, problemas
  específicos). Não copiar texto, foto, logo ou cliente.

## 9. Nunca (além dos guardrails)

- Publicar, agendar ou impulsionar; isso é R-06, com aprovação.
- Inventar preço, medida, material, estoque ou prazo.
- Usar foto/vídeo com nome de cliente real sem autorização, nem
  com borrão improvisado que ainda deixe o nome legível.
- Copiar texto, foto ou criativo de concorrente; modelar só
  estrutura e formato, com identidade própria.
- Usar "humanizador stealth" para burlar detecção.
- Renderizar o .mp4 completo antes do storyboard e dos stills
  aprovados.
- Posicionar texto fora das safe zones ou entregar .mp4 sem
  stream de áudio ou em yuv444p.
