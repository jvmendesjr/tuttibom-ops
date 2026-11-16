# Regras da amostra de fita — transferência térmica (Zebra) e geração da imagem (APROVADO — 2026-11-06)

> **APROVADO — contrato e regras aprovados pelo usuário em 2026-11-06.** A aplicação no pacote, na FAQ e no prompt do agente está **preparada** no §7 deste documento — a Fase A foi concluída e as regras foram aplicadas ao prompt do agente (5 ajustes, ~18:34) e depois movidas para a skill `amostra-fita` na divisão prompt/skills (o prompt guarda só as regras duras). Nenhuma imagem foi gerada; nenhum cliente foi contatado.

> **ADENDO 2026-11-06 ~17:41 — regra de imagens CORRIGIDA (supersede o "só fictício" como regra geral):** as DUAS opções existem. (1) **Imagens REAIS são permitidas** — fotos/vídeos de trabalhos reais já produzidos, SOMENTE os que têm autorização para demonstrar (o usuário vai disponibilizar). A Ana informa ao interessado, de forma informal, que pode mostrar uma imagem real de um trabalho realizado com autorização. (2) **Imagens FICTÍCIAS são para a amostra personalizada** — quando a personalização é real (a pessoa dá as diretrizes, logotipo, data, nome), a amostra é um render fictício (IA) da personalização DELA, para ela ver como ficaria, com nome/data fictícios se ela não quiser informar os dados. O "só fictício" vale para a amostra da personalização do lead, NÃO para mostrar exemplos de trabalhos reais autorizados. Armazenamento: bucket `catalog-photos` no Deskcomm + `imagem_url`/`fotos` no produto.

## Contexto

A TuttiBom vende fita de cetim personalizada em hotstamp (15 mm e
22 mm; 10/25/50 m; impressão Preto, Dourado Metalizado e Prata
Metalizado; 100% poliéster; produção 3 a 5 dias úteis; não lavável).
A experiência do usuário, que fazia isso à mão: a impressora não
imprime linhas muito finas — muitas vezes o comprador enviava um
logotipo e um texto e era preciso engrossar as linhas; detalhes
finos não aparecem; algumas cores destacam o conteúdo impresso e
outras fazem o contrário; na fita de 22 mm a imagem pode ser maior,
então linhas um pouco mais finas são toleráveis; na fita mais
estreita, o espaço aperta.

A estratégia **aprovada** pelo usuário em 2026-11-06: oferecer uma amostra gerada
pelo Muse — uma imagem simulada da fita com o texto/logo da lead —
só para leads viáveis, que já enviaram o texto ou o logotipo e
mostraram interesse real. A amostra é uma prévia, não a prova de
produção e não é foto do produto final. A impressora é uma Zebra de
transferência térmica (ver §1.6), adaptada para foil dourado e
metalizado — sempre monocromática.

Regras do projeto que continuam valendo: mídia 100% fictícia
(a amostra é um render/simulação realista, nunca apresentada como
foto do produto real); prova antes de produzir; nada chega ao
comprador sem aprovação do usuário.

## 1. Limites da impressora (hotstamp) — regras com números e fontes

### 1.1 Espessura mínima de linha

O hotstamp preenche ("empasta") traços finos e complicados: arte
detalhada pode não imprimir como mostrada, e linhas próximas se
preenchem. As fontes divergem no número exato conforme o processo
(papel/cartão vs tecido), mas convergem na ordem de grandeza:

| Regra | Número | Fonte |
|---|---|---|
| Linha positiva em foil, piso absoluto | 0,1 mm (0,28 pt) | Print Peppermint |
| Linha positiva em foil, alvo de projeto | ≥ 0,15 mm (0,43 pt) | Print Peppermint |
| Linha mínima prática em foil | 0,5 pt (0,18 mm) | UniqueLinks; Smilesprint; Aquaholic (tecido) |
| Linha mínima, foil convencional | 1 pt (0,35 mm) | FlyerAlarm (datasheet) |
| Linha mínima, foil digital | 2 pt (0,7 mm) | FlyerAlarm (datasheet digital) |
| Traço fino em tecido não segura | abaixo de 0,5 pt some na trama | Aquaholic |

**Regra de trabalho (confirmada pelo cruzamento com a Zebra, ver §1.6):** desenhar com linhas de **≥ 1 pt (0,35 mm)** e nunca
abaixo do piso da resolução da impressora: a 300 dpi o piso é
0,5 pt (0,18 mm, ≈ 2 pontos); a 203 dpi o piso sobe para
**0,25 mm (≈ 0,7 pt, 2 pontos)** — 0,5 pt a 203 dpi é só 1,4
ponto e não segura. Em fita, preferir ≥ 1 pt: uma linha
de 0,5 mm, nítida na prova em papel, cai sobre as saliências da
trama e sai quebrada em vez de fina (xxr-webbing). O cetim tem a
face mais lisa e é o tecido mais tolerante a detalhe fino e a foil
(Beiheng) — mesmo assim, o guia do próprio fabricante de foil
(Foilmakers, série 140 para fitas de cetim, 100–130 °C) classifica
o trabalho em fita de cetim como "detalhe médio a grande", não
fino.

### 1.2 Espaço mínimo entre elementos

| Regra | Número | Fonte |
|---|---|---|
| Intervalo entre elementos, alvo / piso | 0,25 mm / 0,15 mm | Print Peppermint |
| Distância entre objetos | ≥ 1 pt (0,35 mm) | FlyerAlarm |
| Linhas separadas por menos de 2 pt se preenchem | ≥ 2 pt entre linhas | Hot Stamping (guia) |
| Intervalo linha/ponto | ≥ 1 pt | Smilesprint |
| Distância entre elementos, foil digital | ≥ 2 pt (0,7 mm) | FlyerAlarm (digital) |

**Regra de trabalho:** manter **≥ 0,35 mm (1 pt)** entre
elementos e **≥ 0,7 mm (2 pt)** entre linhas paralelas próximas.

### 1.3 Tamanho mínimo de texto

| Regra | Número | Fonte |
|---|---|---|
| Texto positivo em foil, mínimo / recomendado | 7 pt / 8 pt | Print Peppermint |
| Texto em foil, mínimo | 8 pt | UniqueLinks; SilkCards; Hot Stamping (guia) |
| Texto em foil, mínimo | 7 pt | Smilesprint |
| Altura mínima de letra minúscula | 4 mm | FlyerAlarm (convencional) |
| Altura mínima de letra minúscula, foil digital | 2,5 mm (≈ 14 pt Arial) | FlyerAlarm (digital) |
| Texto em fita, altura mínima | 4 mm de altura | Smith Ribbon |
| Texto em tecido estreito, mínimo | 8 pt (sans-serif limpa) | Aquaholic |
| Texto vazado (letras recortadas de foil sólido) | ≥ 10 pt, médio/negrito | Print Peppermint; Smilesprint |
| Serifadas de alto contraste (Didone) | ≥ 12 pt | Print Peppermint |
| Fontes pesadas/negrito, mínimo | 11 pt | Hot Stamping (guia) |

**Regra de trabalho:** texto positivo com **≥ 8 pt e altura de
letra ≥ 3 mm** (4 mm na fita de 15 mm, ver §2); texto vazado
só com **≥ 10 pt em negrito**; serifadas de traço fino e
cursivas de traço fino, só se os traços mais finos medidos no
tamanho final passarem no piso de linha (§1.1) — medir o traço,
não só o corpo da fonte. **Nunca** texto menor que isso na
amostra: a amostra não pode mostrar legível o que a produção
não imprime.

### 1.4 O que o foil não faz

- **Sem gradientes, meios-tons ou fotos:** o foil é uma cor
  chapada a 100% — ou tem foil ou não tem (FlyerAlarm;
  DiplomaCovers).
- **Sem QR code ou código de barras em foil:** os módulos se
  ligam e o código para de ler (Print Peppermint).
- **Texto sobre fundo sólido de foil se preenche** (Hot
  Stamping, guia); os contadores (espaços internos das letras)
  se preenchem no texto vazado (SilkCards).
- **Registro (alinhamento):** ± 0,5 mm foil–impressão e ± 0,25 mm
  foil–foil (Print Peppermint); outras fontes citam ± 0,1 mm
  (Huamei, embalagem de luxo) e ± 1,5 mm (Smilesprint). Na
  prática: não desenhar nada que dependa de alinhamento mais
  fino que 0,5 mm. Confirmado para transferência térmica: ± 0,5 mm
  de precisão de posicionamento (Honeywell PD45S — ver §1.6).
- **Arte:** vetor (AI/PDF/EPS) de preferência; raster com no
  mínimo 300 DPI no tamanho real; fontes convertidas em curva
  (Beiheng; Smith Ribbon; Litex). Foil em camada separada, cor
  chapada a 100% (FlyerAlarm; Printi).

### 1.5 Contraste: cor do foil × cor da fita

O foil é opaco: o dourado continua brilhante sobre base escura,
onde a tinta ficaria fraca (DiplomaCovers). O dourado destaca em
bases escuras (preto, azul-marinho, verde, vinho); o prata vai
bem em azul-marinho e preto; o dourado "estoura" no preto e no
cinza-carvão; o prata é uma opção segura e brilhante no escuro;
o preto garante legibilidade nas bases claras (pc/nametag).
Superfícies muito brilhantes podem reduzir o contraste de tintas
metálicas claras; um cetim mais fosco melhora a legibilidade
(rcgeotech).

Cores de fita já produzidas (fotos de 30/10/2026, histórico de
produção — **não** é lista de estoque atual): rosa pink, branco,
verde-oliva, preto, amarelo, cinza, verde-limão, marrom escuro.

**Tabela de contraste (orientação — confirmar com as tonalidades
reais do foil usado):**

| Foil \ Base da fita | Preto | Marrom escuro | Verde-oliva | Cinza | Rosa pink | Branco | Amarelo | Verde-limão |
|---|---|---|---|---|---|---|---|---|
| **Dourado Metalizado** | forte | forte | forte | bom | bom | moderado | moderado | moderado |
| **Prata Metalizado** | forte | forte | forte | bom | bom | fraco | fraco | fraco |
| **Preto** | não usar | não usar | fraco | bom | forte | forte | forte | forte |

Leitura: metálicos (dourado/prata) precisam de base escura ou
média para destacar; o prata some sobre base clara (branco,
amarelo, verde-limão); o preto precisa de base clara e some
sobre base escura. É exatamente o que o usuário observou: há
cores que destacam o conteúdo impresso e outras que fazem o
contrário — a tabela acima é a forma prática dessa observação.

## 1.6 A impressora real: Zebra de transferência térmica (não prensa de hotstamp)

Correção de processo: os limites do §1 foram pesquisados para
hotstamp (foil aplicado por prensa quente). A impressora da loja
é uma **Zebra de transferência térmica**, adaptada — e o
cruzamento abaixo confirma as regras de trabalho, com uma
correção no piso de linha (§1.1).

- **Máquina:** impressora térmica Zebra (modelo exato e dpi a
  confirmar — ver §5), normalmente usada para etiquetas com
  **fita de cera preta** (etiquetas e cupons) — esse é o padrão
  dela.
- **Adaptação:** foi adaptada para imprimir em **dourado e
  metalizado (prata)**, com fitas de cera/resina metalizadas
  próprias para cetim. No futuro, outras cores podem entrar
  (por exemplo, vermelho) — mas **sempre monocromático**: uma
  só cor por impressão, sem gradiente e sem cores variadas na
  mesma impressão. É o mesmo princípio do foil: cor chapada a
  100%, ou tem cor ou não tem (§1.4).
- **Gabarito:** o usuário construiu um gabarito para a fita
  entrar reta, com a impressão saindo com precisão no centro,
  a partir do centro de cada fita. Alinhamento central é o
  requisito documentado do processo: a fita e a mídia têm de
  ficar no meio do eixo e alinhadas, e a fita de impressão tem
  de ser igual ou mais larga que a mídia (Zebra, guia de
  carga; fornecedor de fita metalizada). Guias de mídia mal
  ajustadas são causa documentada de enrugamento da fita e
  desvio da impressão (Zebra ZT411).
- **Prática comum:** imprimir em fita de cetim com impressora
  térmica Zebra é prática estabelecida — é o processo padrão
  de etiquetas de cuidado de lavagem (wash care) em cetim, com
  fitas metalizadas de cera/resina próprias para Zebra, TSC,
  Godex, Sato e outras. Não foi encontrado um artigo
  específico sobre gabarito caseiro para centralizar fita — o
  gabarito é adaptação própria do usuário, registrada aqui
  como tal.
- **Resolução → piso de linha:** Zebra de mesa opera a 203 dpi
  (8 pontos/mm, 1 ponto = 0,125 mm) ou 300 dpi (12 pontos/mm,
  1 ponto ≈ 0,083 mm). Uma linha confiável em transferência
  térmica precisa de 2 a 3 pontos: a 203 dpi, 2 pontos =
  0,25 mm; a 300 dpi, 2 pontos ≈ 0,17 mm. Por isso a regra de
  **≥ 1 pt (0,35 mm ≈ 2,8 pontos a 203 dpi)** está confirmada,
  e o piso "nunca abaixo de 0,5 pt" só vale a 300 dpi — a
  203 dpi o piso é 0,25 mm (≈ 0,7 pt). Confirmar o modelo e o
  dpi da Zebra da loja no primeiro uso real (ver §5).
- **Largura da mídia:** modelos de mesa Zebra aceitam mídia a
  partir de 15 mm (ZD421: 15–108 mm), então a fita de 15 mm
  alimenta; modelos industriais partem de 25,4 mm (ZT411) —
  o modelo importa, e o da loja já imprime 15 mm na prática.
- **Registro:** ± 0,5 mm de precisão de posicionamento é o
  número documentado para transferência térmica (Honeywell
  PD45S) — confirma o ± 0,5 mm já adotado no §1.4.

## 2. Ajustes por largura — 15 mm vs 22 mm

A largura é uma restrição de impressão, não só de design: uma
fita de 3 mm não carrega a mesma arte que uma de 50 mm, e o
comprimento da repetição do logo tem de ser especificado junto
com a largura (Beiheng). Em fita estreita, a tipografia é o
elemento com maior chance de falhar (Aquaholic; Smith Ribbon).

### 2.1 Margem de segurança (zona segura)

As fontes **discordam** (ver §5): 2 mm de cada lado (Aquaholic,
para fitas de 15–25 mm) vs 5 mm de cada lado, com mínimo de
3 mm da borda (Smith Ribbon, exemplo de 25 mm). Na fita de
15 mm, 5 mm de cada lado deixariam só 5 mm de área útil — por
isso este rascunho adota **2 mm de cada lado** como regra de
trabalho, a confirmar com a impressora.

Área útil resultante (regra de trabalho, 2 mm de cada lado):
**15 mm → ~11 mm de altura útil; 22 mm → ~18 mm.**

### 2.2 O que cabe em cada largura

Referência análoga (fitas estreitas de 15–25 mm, Aquaholic):
15 mm → só logotipo, nenhum texto abaixo de 8 pt; 20 mm →
logotipo + URL curta ou slogan; 25 mm → logotipo + slogan +
URL, maior liberdade.

| | 15 mm | 22 mm |
|---|---|---|
| Altura útil (≈) | ~11 mm | ~18 mm |
| Conteúdo máximo | 1 linha de texto **ou** logotipo pequeno com símbolo | logotipo + 1 linha curta **ou** 2 linhas de texto |
| Texto | ≥ 8 pt, altura de letra ≥ 4 mm; 1 linha | ≥ 8 pt, altura de letra ≥ 3 mm; até 2 linhas |
| Linhas | alvo ≥ 1 pt, nunca < 0,5 pt | alvo ≥ 1 pt; linhas um pouco mais finas são toleráveis porque a arte fica ~1,5× maior que na de 15 mm |
| Logotipo | simplificar: tirar detalhe fino, engrossar traços, manter símbolo sólido | mesmo tratamento, com mais folga para símbolo + texto |

A fita de 22 mm é ~47% mais larga que a de 15 mm: a mesma arte
renderiza cerca de 1,5× maior, por isso linhas um pouco mais
finas são toleráveis nela — é a observação do usuário, e a
matemática confirma. Se o logotipo tem detalhe fino, uma fita
um pouco mais larga às vezes produz um resultado bem melhor
(PersonalisedPrintedRibbons).

### 2.3 Repetição ao longo da fita

A impressão se repete ao longo da fita (documento do produto).
O tamanho de cada impressão e o espaço entre repetições
importam, principalmente se a fita for cortada em pedaços ou
amarrada em caixas (PersonalisedPrintedRibbons). **Aberto:**
a distância exata da repetição nesta impressora (ver §5) — a
amostra deve mostrar pelo menos 2 repetições, retas e
alinhadas, para o comprador ver o ritmo da estampa.

## 3. Prompt da amostra — o que o Muse deve exigir e proibir ao gerar a imagem

A amostra é gerada pelo Muse com a arte da lead (texto ou
logotipo que ela mesma enviou). O prompt da geração deve
embutir as regras acima, para a amostra nunca prometer o que
a produção não entrega.

### 3.1 O prompt deve EXIGIR

- Render realista de fita de cetim (rolo e trecho desenrolado),
  com a largura correta em proporção (15 mm estreita, 22 mm
  mais larga), brilho do cetim e relevo do foil com brilho
  metálico que pega a luz.
- A arte impressa com os traços **engrossados** conforme §1.1:
  traços grossos e sólidos, sem filete, sem serifada de traço
  fino, sem cursiva de traço fino, sem texto miúdo.
- Texto **exato** como aprovado (grafia exata), no máximo 1
  linha na fita de 15 mm e 2 linhas na de 22 mm, com altura de
  letra legível na escala da fita (§1.3, §2.2).
- Cor do foil combinada com a cor da fita conforme a tabela
  de contraste (§1.5) — nunca prata sobre fita clara, nunca
  preto sobre fita escura.
- Repetição da estampa ao longo da fita (pelo menos 2
  repetições visíveis), reta e alinhada.
- Fundo neutro, luz natural, sem outros produtos, sem mãos,
  sem texto adicional na imagem além da arte da fita e do
  rótulo de simulação (abaixo).
- Rótulo visível **na imagem e** na mensagem que a acompanha:
  **"Prévia simulada — imagem gerada por IA, não é foto do produto
  final."** (a imagem circula sem a mensagem — o rótulo tem de
  estar nela; a mensagem repete o aviso completo, ver §6).

### 3.2 O prompt deve PROIBIR

- Linhas finas, filetes, serifadas Didone, cursivas de traço
  fino, texto menor que o legível na escala, texto vazado
  miúdo, gradientes ou sombras dentro da impressão em foil,
  QR code ou código de barras em foil.
- Detalhe maior do que a largura suporta (ex.: logotipo
  complexo com 3 linhas de texto numa fita de 15 mm).
- Cor de foil que não contrasta com a base (prata em fita
  branca/amarela; preto em fita preta).
- Apresentar a amostra como se fosse a fita pronta ou foto
  real do produto.
- Prometer correspondência exata de cor (tela vs foil) ou
  prazo/preço na imagem.
- Usar arte de outro cliente, nome de outra pessoa ou marca
  que não seja a da lead.

### 3.3 Bloco de prompt (rascunho, colar e preencher)

```text
Gere uma prévia simulada de uma fita de cetim personalizada
da TuttiBom, realista, como render de produto — NÃO é foto
do produto real.
- Fita: cetim 100% poliéster, largura [15 mm | 22 mm],
  cor da fita [COR], com rolo e um trecho desenrolado sobre
  fundo neutro, luz natural.
- Impressão em hotstamp, cor [Preto | Dourado Metalizado |
  Prata Metalizado], repetida ao longo da fita (pelo menos
  2 repetições visíveis), reta e alinhada, com brilho
  metálico que pega a luz.
- Arte: [TEXTO EXATO ou descrição do logotipo]. Traços
  grossos e sólidos, sem filetes, sem letras miúdas, sem
  gradiente na impressão, sem QR code. No máximo [1 linha |
  2 linhas] de texto, com letras grandes e legíveis na
  escala da fita.
- Não inventar outros textos, marcas ou preços. Não mostrar
  a fita como produto finalizado nem como foto real.
- Incluir o rótulo "Prévia simulada — imagem gerada por IA" de forma legível na própria imagem.
```

## 4. Fluxo da amostra — em duas etapas (aprovado)

1. **Quando oferecer:** só para lead viável — ela já enviou o
   texto ou o logotipo **e** mostrou interesse real (perguntou
   largura, metragem, cor do foil, quantidade ou prazo, ou
   confirmou que o produto serve para a festa/negócio dela).
   Não oferecer no primeiro contato nem por curiosidade.
2. **O que pedir antes de gerar:** largura (15/22 mm),
   metragem, cor do foil, cor da fita, texto exato ou arquivo
   do logo (PNG preto e branco, de preferência), ocasião/uso,
   quantidade e prazo.
3. **Gerar:** o Muse gera a amostra com as regras do §3, a
   partir da arte que a lead enviou.
4. **Aprovação do usuário:** o usuário aprova a imagem exata
   e o texto exato **antes** de qualquer envio à lead — nada
   chega ao comprador sem aprovação (regra do projeto).
5. **Enviar à lead:** a imagem vai com o rótulo "prévia
   simulada — imagem gerada por IA" e a mensagem do §6 (expressão
   artística, imagem feita por IA, não é o produto real, sem
   compromisso e sem custo, nada exposto ou publicado, descarte
   após a confirmação).
6. **A amostra não substitui a prova:** a prova escrita/foto
   do modelo antes de produzir continua obrigatória (regra da
   persona). A amostra ajuda a decidir; a prova fecha a
   produção.
7. **Preço fora do fluxo:** preço continua escalado para uma
   pessoa — a amostra não traz preço.
8. **Registro:** anotar na ficha da lead (CRM) que a amostra
   foi enviada, quando e qual versão — sem dado pessoal no
   repositório.
9. **Descarte:** depois que o pedido for confirmado, a arte da
   lead e a imagem da amostra são descartadas — não ficam
   guardadas nem são usadas para nada. (Gatilho exato a
   confirmar no primeiro uso real: confirmação do pedido.)
10. **Etapa 2 — amostra física (só na iminência de fechar):** se,
    na iminência de fechar o contrato, ainda restar alguma
    dúvida mesmo depois da amostra em imagem, o agente **NÃO oferece nem decide a amostra física** (decisão do usuário 2026-11-06 ~14:30) — ele **passa a conversa para o humano** e o que for discutido é guardado como aprendizado/registro; automação só depois de catalogar repetições. A amostra física, quando feita, é um pedaço real de fita impressa, feito por José. O usuário aprova antes de fazer (custa
    material e tempo real: fita + foil + tempo de máquina). A
    amostra física segue os mesmos limites da impressora
    (§1, §1.6: uma só cor, centrada a partir do centro, linhas,
    texto e espaçamentos) e não substitui a prova antes de
    produzir: é uma amostra, não a tiragem; a prova escrita
    continua obrigatória antes de produzir o pedido completo.

## 5. Pontos em aberto (fontes discordam ou calam)

1. **Mínimos exatos desta impressora:** parcialmente resolvido —
   a impressora é uma Zebra de transferência térmica (§1.6) e o
   piso de linha agora tem base em dpi (2 pontos: 0,25 mm a
   203 dpi, 0,17 mm a 300 dpi). Falta confirmar: o modelo exato
   e o dpi da Zebra da loja, e a distância de repetição.
2. **Margem de segurança:** 2 mm de cada lado (Aquaholic)
   vs 5 mm de cada lado, mínimo 3 mm da borda (Smith Ribbon).
   Na fita de 15 mm, 5 mm de cada lado deixam só 5 mm úteis —
   a regra de trabalho adotada aqui (2 mm) precisa de
   confirmação.
3. **Cores da fita em estoque hoje (com nome):** não
   confirmado. As cores listadas no §1.5 vêm de fotos de
   produção passada.
4. **Tonalidades reais do foil:** Dourado/Prata/Preto
   metalizado usados pela loja podem deslocar a tabela de
   contraste do §1.5.
5. **Cursivas:** o catálogo mostra nomes em cursiva já
   produzidos — falta registrar quanto de engrossamento foi
   preciso neles na prática.
6. **Repetição:** distância exata entre repetições nesta
   impressora; e se a amostra deve mostrar 1 ou 2 repetições.
7. **Rótulo "prévia simulada":** RESOLVIDO — nos dois: na imagem
   ("Prévia simulada — imagem gerada por IA") e na mensagem (§6).
8. **Fora do escopo deste documento:** peças 3D (a amostra
   aqui é só de fita).
9. **Gatilho do descarte:** a regra é descartar arte e imagem
   depois que o pedido for confirmado — confirmar no primeiro
   uso real se o gatilho é a confirmação do pedido, a entrega,
   ou a desistência da lead.
10. **Amostra física (Etapa 2):** tamanho do pedaço, como é
    entregue (junto com o pedido, retirada, envio) e se há
    custo para a lead — a definir no primeiro uso real; o
    agente NÃO oferece (handoff humano, decisão 2026-11-06
    ~14:30), José aprova e faz.

## 6. Mensagem de entrega da amostra (template aprovado)

Quando a amostra em imagem for enviada à lead, ela vai com esta
mensagem (tom da persona: acolhedor, direto, frases curtas, uma
pergunta por vez). É o texto exato a aprovar com o usuário antes
de enviar — nada chega à lead sem aprovação.

> Oi! Preparei uma prévia da sua fita, para você ter uma ideia de como ela vai ficar.
>
> Essa imagem é uma expressão artística, feita por inteligência artificial. Ela não é uma foto do produto real, e pode haver algumas diferenças na cor e nos detalhes. O objetivo é só você visualizar como fica.
>
> Não tem compromisso nenhum e não tem custo nenhum para você. A sua arte não vai ser exposta, publicada nem usada para nada. Depois que o pedido for confirmado, tudo é descartado.
>
> Quer ajustar alguma coisa na prévia?

Regras do template (melhores práticas do mercado, confirmadas na pesquisa):
- **Divulgação da IA no texto e na imagem:** a imagem carrega o rótulo "Prévia simulada — imagem gerada por IA" e a mensagem diz que foi feita por inteligência artificial. A imagem circula sem a mensagem — o rótulo tem de estar nela. (Postoria; lav1: divulgar quando a IA muda o que o cliente acredita estar recebendo; lovino.ai: rotular imagens que podem ser confundidas com a realidade é melhor prática; UE AI Act art. 50(3): imagens realistas geradas por IA devem ser rotuladas como geradas artificialmente — referência de mercado, não assessoria jurídica.)
- **Sem falsa impressão:** a mensagem diz que é expressão artística e que pode haver diferenças — a divulgação não substitui mostrar com precisão o que está sendo vendido (Postoria; FTC: imagens de IA devem representar o produto com precisão e não criar impressões materialmente falsas).
- **Sem compromisso e sem custo:** dito explicitamente — a prévia não obriga a nada nem custa nada.
- **Privacidade e descarte:** a arte da lead não é exposta, publicada nem usada para nada; depois que o pedido for confirmado, arte e imagem são descartadas. Gatilho exato a confirmar no primeiro uso real (ver §5).
- **Uma pergunta por vez:** a mensagem termina com uma só pergunta ("Quer ajustar alguma coisa na prévia?") — a conversa continua a partir da resposta.

## 7. Aplicação — o que muda no pacote, na FAQ e no prompt do agente (PREPARADO, NÃO APLICADO)

> **Preparado, não aplicado.** Nada desta seção foi colado no
> pacote, na FAQ, na persona ou no prompt do agente. A aplicação
> aguarda a conclusão da Fase A. Quando for aplicar, colar
> exatamente como está aqui e marcar este §7 como aplicado, com
> data.

**Liberdade com discernimento (decisão do usuário, 2026-11-06):**
o roteiro da amostra entra no prompt como **roteiro orientado**,
não como passo a passo rígido. O agente segue o roteiro com
discernimento e decide na conversa quando o portão foi atingido
(lead viável, iminência de fechar, dúvida restante). A ressalva
final do §7.2 é condição — e as travas duras continuam duras:
nunca prometer o que a produção não entrega, nunca citar preço,
e o usuário aprova a imagem exata e a mensagem exata antes de
qualquer coisa chegar à lead.

### 7.1 Novas duplas de FAQ (acrescentar ao §5 do pacote)

14. **Posso ver uma prévia da minha fita antes de fechar?** — Sim, quando você já enviou o texto ou o logotipo e a gente confirmou os detalhes, a gente prepara uma prévia simulada da fita, feita por inteligência artificial, para você ter uma ideia de como vai ficar. A prévia não é foto do produto real e pode ter pequenas diferenças de cor e detalhe. Não tem custo nem compromisso, e não substitui a prova antes de produzir.
15. **A prévia é a foto do produto final?** — Não: é uma imagem gerada por inteligência artificial, uma expressão artística para você visualizar como fica. A produção só começa depois da prova aprovada.
16. **O que acontece com a minha arte depois?** — A sua arte não é exposta, publicada nem usada para nada além do seu pedido. Depois que o pedido for confirmado, tudo é descartado.
17. **Dá para ver uma amostra de verdade antes de fechar?** — **NÃO ENTRA (decidido pelo usuário 2026-11-06 ~14:30).** A amostra física virou handoff humano: o agente não a oferece; quando a situação surgir, passa a conversa para o humano e registra o caso como aprendizado. (Texto original da proposta, guardado: 'Se na iminência de fechar o pedido ainda restar alguma dúvida, a gente pode fazer uma amostra física, um pedaço real da fita impressa, para você ver antes. É só pedir, e a gente combina.')

### 7.2 Acréscimo ao prompt v2 do agente (pacote §4)

Colar no prompt, depois da seção de situações, antes dos Limites.
É um **roteiro orientado**: o agente segue com discernimento e
decide na conversa quando cada portão foi atingido — não é um
passo a passo rígido a executar do mesmo jeito sempre.

**Atualização 2026-11-06 noite (divisão prompt/skills):** o procedimento da amostra saiu do prompt e vive na skill `amostra-fita`; o prompt guarda só as regras duras (não pedir nome/data da criança, não oferecer amostra física, nada vai para a lead sem aprovação). O texto abaixo fica como registro do procedimento original.

```markdown
# Amostra da fita
- Ofereça a amostra em imagem só para lead viável: ela já enviou o texto ou o logotipo e mostrou interesse real (perguntou largura, metragem, cor do foil, quantidade ou prazo, ou confirmou que o produto serve). Nunca ofereça no primeiro contato. Você decide na conversa quando a lead mostrou esse interesse — não é uma lista de verificação rígida.
- Antes de pedir a amostra, confirme com a lead: largura (15 ou 22 mm), metragem, cor do foil, cor da fita, texto exato ou arquivo do logo, ocasião, quantidade e prazo.
- A amostra é feita pelo Muse, com as regras de impressão (traços grossos, sem detalhe fino, uma só cor, centrada). Você não gera a imagem — você pede ao Muse e aguarda.
- Nada vai para a lead sem aprovação do usuário: a imagem exata e a mensagem exata são aprovadas antes de enviar.
- Envie com o rótulo "Prévia simulada — imagem gerada por IA" e a mensagem do template (expressão artística, feita por IA, não é o produto real, sem compromisso e sem custo, nada exposto ou publicado, descarte após a confirmação). A amostra não substitui a prova antes de produzir e não traz preço.
- Etapa 2 — amostra física: **o agente NÃO oferece nem decide a amostra física** (decisão do usuário 2026-11-06 ~14:30). Se, na iminência de fechar o contrato, ainda restar alguma dúvida mesmo depois da amostra em imagem, passe a conversa para um humano e registre o caso como aprendizado. A amostra física, quando feita, é um pedaço real de fita impressa, feito por José; o usuário aprova antes de fazer. A amostra física segue os mesmos limites da impressora e não substitui a prova antes de produzir.
- Depois que o pedido for confirmado, a arte da lead e a imagem da amostra são descartadas.

# Ressalva final da amostra (condição)
- A amostra, em imagem ou física, é uma prévia para a lead ter uma ideia de como vai ficar — nunca prometa o que a produção não entrega, nunca cite preço, e nunca envie nada à lead sem a aprovação do usuário da imagem exata e da mensagem exata.
```

### 7.3 Adendo à persona (preparado, não aplicado)

Acrescentar a `docs/persona-interacao.md`, como adendo de papéis (a persona existente não é reescrita):

- **Amostra (imagem e física):** a entrega da amostra segue o tom da persona e o template do §6. O agente nunca apresenta a amostra como o produto real nem como foto do produto. A amostra em imagem é uma prévia simulada feita por IA; a amostra física é um pedaço real, feito por José, e o agente **NÃO a oferece** — quando a situação surgir (iminência de fechar, dúvida restante), passa a conversa para o humano (decisão 2026-11-06 ~14:30). As duas passam por aprovação do usuário antes de chegar à lead, e nenhuma das duas substitui a prova antes de produzir. O agente decide com discernimento quando oferecer a amostra em imagem — o roteiro é orientado, não rígido.

## Fontes

- Print Peppermint — Minimum Line Weight & Type Size: Every
  Process. https://www.printpeppermint.com/guides/file-setup/minimum-line-weight-and-type-size
- FlyerAlarm — Hot foil datasheet (fontes e linhas).
  https://www.flyeralarm.com/sheets/en/etikett_71x96_fp.pdf
- FlyerAlarm — Hot foil (digital) datasheet.
  https://www.flyeralarm.com/sheets/en/pv_rechteck_gkl_fp2.pdf
- UniqueLinks — Foil Stamping for Packaging Box Printing.
  https://uniquelinksb.com/why-do-foil-stamping-on-packaging/
- SilkCards — Gold Foil Business Cards.
  https://silkcards.com/blog/business-cards/premium-business-cards/gold-foil-business-cards/
- Smilesprint — Preparing Hot Stamping Design and Spot UV.
  https://smilesprint.s3.ap-southeast-1.amazonaws.com/guides&Specs/General/general-preparing-hot-stamping-and-spot-uv-only.pdf
- Hot Stamping — Art guidelines (PDF).
  https://d207zvy2rsg5b5.cloudfront.net/DCF1CAEE-D995-4642-AC3C-7601048040A0/StaticImages/HotStamping.pdf?timestamp=11/02/2023%2014
- Huamei — Hot-foil stamping for luxury packaging.
  https://www.huamei.io/blogs/hot-foil-stamping-for-luxury-packaging
- DiplomaCovers — What Is Foil Stamping.
  https://www.diplomacovers.net/blog/what-is-foil-stamping/
- Foilmakers — Guide to Hot Stamping and Foil Selection (PDF).
  https://store-s73upa7phh.mybigcommerce.com/content/products/Foilmakers%20Hot%20Foil%20Stamping%20Information%20Guide.pdf
- Beiheng Ribbon — Satin vs Grosgrain vs Taffeta vs Herringbone.
  https://blog.bei-heng.com/blog/Satin-vs.-Grosgrain-vs.-Taffeta-vs.-Herringbone-Ribbon:-A-Buyer-s-Comparison.html
- xxr-webbing — Custom Printed Polyester Ribbon: Which Route.
  https://www.xxr-webbing.com/dlp/custom-printed-polyester-ribbon.html
- LuLu Packaging — Custom Foil Stamped Tags.
  https://www.lulupackaging.com/custom-foil-tags
- rcgeotech — Custom Printed Satin Ribbon: Print, Width & Finish.
  https://www.rcgeotech.com/news/textiles/fabrics/Custom-Printed-Satin-Ribbon-How-to-Choose-Print-Quality-Width-and-Finish.html
- Aquaholic — Lanyard Design Guide (fitas estreitas 15–25 mm).
  https://www.aquaholic.com.sg/corporate-gifts/lanyard-design-guide-singapore-artwork-specs-custom-printing/
- Smith Ribbon — Ribbon Artwork Pre-Press Setup (2026).
  https://smithribbon.com/blog-ribbon-artwork-pre-press-workflow-guide-2026.html
- PersonalisedPrintedRibbons — How to Print on Ribbon.
  https://www.personalisedprintedribbons.co.uk/how-to-print-logos-on-ribbon/
- pc/nametag — guias de cor de foil em fitas (Facebook Reels).
  https://www.facebook.com/reel/4244871152508074/
  https://www.facebook.com/reel/853389177316681/
- Litex Embalagens — Como enviar arte para embalagem
  personalizada. https://blog.litexembalagens.com.br/2026/10/30/como-enviar-arte-para-embalagem-personalizada-guia-rapido/
- Etiquetas Brasil — Manual de fitas personalizadas (PDF).
  https://www.etiquetasbrasil.com.br/uploads/manual-fitas-personalizadas.pdf

- Zebra — Ribbon Overview and Use (cera/resina, fita igual ou mais
  larga que a mídia).
  https://docs.zebra.com/us/en/printers/desktop/gk420t-desktop-thermal-printer-user-guide/t-gk420d-ug-print-operations/c-gk420t-ug-ribbon-overview.html
- Zebra — XiIIIPlus User Guide, Load Ribbon (guia de carga, fita
  mais larga que a mídia protege o cabeçote).
  https://www.zebra.com/content/dam/external-dam/knowledge-base/cpws/docs/xi3plus/XiIIIPlus_LoadRibbon.pdf
- Zebra ZD421 — especificações (mídia a partir de 15 mm, 203/300 dpi).
  https://matrixwarehouse.co.za/products/zebra-zd421-desktop-printer
- Zebra ZT411 — especificações e guia de fita (203/300 dpi, guia de
  mídia, enrugamento).
  https://epicriseelectronics.com/products/zebra-zt411-thermal-transfer-industrial-printer-300-dpi-print-width-4-inches-features-serial-usb-ethernet-and-bluetooth-connectivity-zt41143-t010000z
- Fornecedor de fita metalizada para Zebra (cera/resina, cetim,
  monocromático, centragem no eixo).
  https://dgkbtm.en.made-in-china.com/product/cFVJZguxYzkE/China-Fabric-Satin-Clothing-Label-Printing-Metallic-Silver-Wash-Resin-Ink-Color-Ribbon-for-Zebra-Printer.html
- Honeywell PD45S — precisão de posicionamento ± 0,5 mm.
  https://www.pos99.com.au/barcode-label-printers/shipping-label-printers/honeywell-thermal-transfer-label-printer-pd45s-203dpi-eth1.html
- Postoria — AI Content on Social Media: What to Label and Not to Fake.
  https://postoria.io/blog/ai-generated-content-social-media-labeling
- lav1 — Should Businesses Disclose That Content Was Created With AI?
  https://lav1.com/should-businesses-disclose-ai-created-content/
- lovino.ai — AI Content Ethics: When and How to Disclose AI-Generated Images.
  http://lovino.ai/blog/ai-content-ethics-disclosure-guide
- sota.io — EU AI Act Art. 50 Transparency 2026.
  https://www.sota.io/blog/eu-ai-act-art50-transparency-saas-developer-guide-2026

Documento interno do projeto (não é fonte externa): 
`catalogo/produto-fita-cetim.md` (produto, cores de fita vistas
em fotos, fluxo de encomenda) e `docs/persona-interacao.md`
(prova antes de produzir, nada sem aprovação).
