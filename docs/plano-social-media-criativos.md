# Plano de Social Media e Criativos — tuttibom-ops

> Adaptação, 2026-11-01, dos dois documentos enviados pelo usuário
> nesta data: "Plano Diretor de Social Media, Criativos e Contratos
> de Skills" e "Arquitetura de Motion Graphics por Código
> (tuttibom-estudio-criativo)". Onde divergir de `docs/arquitetura.md`
> v2 e `docs/roadmap.md` v2, valem os guardrails e as versões v2,
> salvo o adendo registrado em `docs/arquitetura.md` nesta mesma data.
>
> Status honesto nesta adaptação:
> - Links de skills da comunidade: **não recebidos nesta conversa**.
>   O bloco "[COLE SEUS LINKS AQUI]" do documento original ficou
>   vazio. Nenhum link foi inventado e nenhuma fonte nova foi
>   registrada em `docs/referencias.md` por causa dele. A ingestão
>   (seção 1) só roda quando os links chegarem.
> - Caderno efêmero do NotebookLM: o documento pede para "abrir o
>   primeiro caderno efêmero" e apresentar o storyboard da
>   Publicação 1. NotebookLM é semi-manual, sem API oficial estável
>   (ver `skills/tuttibom-notebooklm/`). O storyboard e o texto
>   exato da Publicação 1 estão, por isso, apresentados nesta
>   conversa e em `templates/storyboard-publicacao-1.md` como
>   checkpoint humano — não como caderno já aberto. O caderno
>   efêmero, sua exportação e sua deleção continuam pendentes e
>   manuais.
> - Brand sheet: a identidade já existe para esta conta e será
>   reavaliada, não criada do zero. Até a brand sheet estar validada,
>   o template de vídeo não fecha (regra já existente em
>   `skills/tuttibom-facebook-conteudo/`). Isso bloqueia o render
>   final, não o storyboard nem a aprovação do texto da Publicação 1.

## 1. Protocolo de ingestão de skills da comunidade (pendente de links)

Quando o usuário entregar links de skills externas (ex.: ClawHub,
Skills.sh, GitHub), o Muse NÃO copia código cegamente nem substitui
o executor ADB. Aplica o contrato `skills/_contrato/SKILL.md` em
4 passos:

1. **Extração agnóstica do padrão:** ler a skill e extrair só a
   inteligência estrutural (ganchos de copywriting, estrutura de
   retenção de Reels/Stories, cadência de carrossel, gatilhos
   visuais, regras de triagem).
2. **Descarte de premissas incompatíveis:** descartar comando de API
   não oficial, automação web via desktop/Chrome, "humanizadores
   stealth" para burlar detecção e disparos em massa que violem
   `skills/guardrails/SKILL.md`.
3. **Mapeamento nos 9 campos do contrato:** traduzir o padrão para
   as instâncias da TuttiBom (Propósito, Gatilho, Entradas, Passos
   determinísticos, Pontos de decisão, Condições de parada, Saídas,
   Adaptação e Nunca).
4. **Observação transversal:** o usuário define o setor principal
   daquela skill (ex.: Publicações), e o Muse avalia tecnicamente
   como o mesmo padrão pode beneficiar os outros módulos (ex.: usar
   um padrão de carrossel educativo para a imagem de tabela do
   Marketplace) e registra a fonte em `docs/referencias.md`.

## 2. Fábrica criativa desacoplada

A geração criativa (Remotion / HyperFrames / FFmpeg / edição de
imagem) sai de dentro de `tuttibom-facebook-conteudo` e vira a
instância agnóstica de rede `skills/tuttibom-estudio-criativo/`
(ver o contrato completo lá, e o detalhe técnico de motion em
`docs/motion-graphics-codigo.md`).

- **Estúdio:** produz o ativo, nunca publica, nunca inventa
  especificação ou preço.
- **Facebook-conteúdo:** recebe o ativo pronto, entra na fila e só
  executa no S10 via ADB (rotina R-06) após aprovação do texto e
  da mídia exatos.
- **NotebookLM:** roteiro e texto-base vêm do caderno efêmero;
  saída do NotebookLM é proposta, nunca aprovação.

Fluxo: catálogo + caderno efêmero → storyboard (checkpoint humano)
→ render determinístico → arquivo versionado no Drive
(`TuttiBom/02_Criativos/`, nome
`AAAAMMDD_produto_formato_rede_v01.ext`) → fila em
`ops/fila-publicacao.md` → aprovação → R-06 no S10 → prova por
screencap → reação (R-09: baseline, 1 intervenção por vez, leitura
em 24h e 72h).

## 3. Pilares editoriais (fita de cetim + impressão 3D, Cariri)

Contexto já registrado no projeto: fita de cetim personalizada é
oceano azul local (concorrentes só a 400–490 km, em Fortaleza ou
João Pessoa); impressão 3D tem concorrência local ativa (chaveiros
a R$ 6–R$ 8, temática religiosa forte). Ritmo em testes: **máximo
3 posts por semana, dias alternados, nunca 3 posts de venda
seguidos**.

1. **Hipnose de processo e bastidor** (Reels / vídeo curto 15–30s,
   Stories): vídeo real da fita saindo da impressora em hotstamp
   (brilho dourado/prateado) ou close-up do bico da impressora 3D.
   Gancho nos primeiros 3 segundos.
2. **Transformação "antes, durante e depois"** (carrossel de 3 a 4
   imagens): embalagem simples / rolo fechado → personalização
   (exemplo genérico "Sua logo aqui") → uso real + CTA (laço na
   caixa, combo 3D + fita).
3. **Interação e escolha rápida** (Stories / foto única no Feed):
   perguntas binárias, não abertas. Exemplos: Dourado Metalizado
   na fita preta ou Prata Metalizado na fita rosa? Qual cor para o
   suporte/chaveiro 3D — só cores com estoque real confirmado.
   Carrossel educativo quebra-objeções: fita pode lavar? Não —
   100% poliéster, para embalagem/decoração, sensível a atrito.
   Pedido mínimo? A partir de 1 rolo de 10 m. Produção? 3 a 5 dias
   úteis após aprovar a prévia, feita no Cariri.
4. **Prova local e sazonalidade regional** (B2B e B2C): lojistas e
   confeiteiras do Cariri que hoje pagam frete caro e esperam
   ~15 dias de fora; argumento central é rolo de lojista (50 m)
   ou de entrada (10 m), com prévia antes de imprimir. Calendário:
   romarias de Juazeiro, festas juninas, Santo Antônio de
   Barbalha, Expocrato, casamentos e aniversários.

## 4. Etapa 1 — primeiras publicações (sem preço fechado)

São os 3 conteúdos que **não dependem de preço fechado** — por
isso podem andar mesmo com o preço para o Facebook ainda
indefinido. Nenhum deles está aprovado até o usuário aprovar o
texto e a mídia exatos, um por vez (guardrail: 1 rascunho de
post/vídeo por dia em testes).

| Ordem | Canal / Formato | Produto / Tema | Mídia | Copy (base, a aprovar uma a uma) |
|-------|-----------------|----------------|-------|----------------------------------|
| Dia 1 | Stories + Feed (foto/arte) | Impressão 3D + fita — escolha de cor | Composição dividida Dourado vs. Prata sobre fitas reais, sem nome de cliente | Ver texto exato em `templates/storyboard-publicacao-1.md` |
| Dia 3 | Reels 15–20s + Stories | Fita de cetim — processo real | Vídeo bruto real de ~20s da fita saindo em hotstamp, editado em FFmpeg/Remotion, com tarja/badge de privacidade se houver nome de terceiros | "Bastidores da produção aqui no Cariri. Cada rolo passa pela gravação em hotstamp depois que a prévia da arte é aprovada. Você usa fita personalizada para festa ou para a embalagem da sua loja?" |
| Dia 5 | Carrossel de 3 fotos (Feed) | Combo 3D + fita — diferencial local | Foto 1: rolos no carretel. Foto 2: detalhe de peça/chaveiro 3D. Foto 3: caixa/lembrancinha fechada com laço genérico | "Por que entregar uma lembrancinha comum se você pode personalizar a peça em 3D e o laço de cetim no mesmo lugar? Produção local para Juazeiro, Crato e Barbalha. Me conta: qual é a próxima data especial aí na sua agenda?" |

Pendência aberta para o Dia 3 (pergunta final do documento de
motion): qual vídeo bruto usar como fundo — o da fita rosa ou o
da fita branca saindo da máquina? Os editados de 12s/19s ficam
como alternativa, a revisar antes (contato exibido precisa ser o
atual). A escolha não muda a Publicação 1 e pode ser decidida
junto com a aprovação dela, sem tocar no S10 ainda.

## 5. Checklist de execução segura via ADB no S10 (R-06, resumo)

Aplicar só depois da aprovação, na janela viva de ADB, seguindo
`skills/s10-navegacao/` e `skills/guardrails/`:

1. **Transferência limpa:** VM → S10 via SSH/SCP para pasta
   dedicada (ex.: `/sdcard/Download/tuttibom_fila/`) e media
   scanner (`am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE`)
   para a mídia aparecer no topo da galeria do Facebook.
2. **Gate de tela (R-01):** `adb devices`, acordar a tela
   (`keyevent 224`), confirmar Awake, operar 100% via
   `screencap -p` — `uiautomator dump` retorna nulo no app do
   Facebook.
3. **Texto sem erros:** preferir colar via clipboard (acentos e
   quebras de linha); nunca `input text` com `%20`; conferir na
   captura se o texto colado está idêntico ao aprovado.
4. **Trava de rascunho (R-06):** no Feed da Página, salvar como
   rascunho. Nos Stories, onde muitas vezes não há rascunho
   nativo na nuvem, o checkpoint humano acontece na tela de
   pré-visualização final no S10: montar, screencap, aguardar o
   "Aprovado, pode publicar" no chat e só então tocar em
   compartilhar, seguido de screencap de prova. **0 publicações
   sem prova.**
