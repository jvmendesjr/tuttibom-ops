# Notas de discussão — arquitetura e painel (rascunho, NÃO final)

Data da discussão: 2026-10-30 (noite, horário de Brasília; mensagens até ~21:12 -03).
Status: **RASCUNHO DE ANOTAÇÃO**. A discussão continua. O painel visual e a
arquitetura final NÃO devem ser construídos a partir daqui até o usuário dizer
que a discussão foi fechada. Este arquivo existe só para que nada do que foi
discutido se perca antes desse fechamento.

## Decisões confirmadas pelo usuário nesta noite

- **ADB como único acesso e gestão da conta pessoal da loja no Facebook, por
  enquanto.** O conector nativo do Muse, neste ambiente, não está ligado a
  conta nenhuma (checagem de 2026-10-30: `me` vazio). Ligar outra conta não
  resolveria Marketplace nem Messenger da loja, porque o autor seria outra
  pessoa. No futuro, o conector pode ser auxiliar só para a Página, se a conta
  ligada for administradora dela — complemento, não substituição, e não é o
  passo de agora.
- **MacroDroid / allow de rede nova: considerado superado por enquanto.**
  Usuário acompanha a tela, sem pedidos no momento, e avisará se houver
  contratempo. Nenhuma ação no telefone foi pedida ou feita a partir daqui.
- **Bootloader: NÃO fazer por enquanto.** Fica marcado apenas como solução de
  último caso, como tratado na discussão.
- **Humanização de texto — correção de entendimento:** não é para enganar
  detector de plataforma e não é para esconder uso de IA. É naturalidade para
  quem lê, para agradar e gerar engajamento, com esforço real por trás
  (processo verdadeiro, foto verdadeira, texto aprovado). Regra: nem esconder,
  nem escancarar; nunca usar ferramenta de evasão.
- **Painel: só leitura para o usuário; só o Muse mexe.** Qualquer mudança
  sugerida pelo usuário passa por discussão honesta, com avaliação técnica do
  Muse, e só depois o Muse altera, com versão registrada. Sem dado de
  comprador no painel, com certeza.
- **Projeto modular e multi-rede por desenho.** Depois da aprovação no
  Facebook, reaproveitar conteúdos, processos e fluxos dentro da Meta e em
  outras redes, para outras contas e outros nichos. Setores do painel são
  módulos (Marketplace, Publicações, Interações), não recursos só do Facebook.
- **Identidade visual: já existe para esta conta.** Será reavaliada se precisa
  de modificação, não criada do zero.

## Papéis de provedores e ferramentas, como discutido

- **Pangram:** só como medidor/QA de naturalidade do texto, não como gerador
  de texto humanizado (a Pangram Labs é empresa de detecção de texto por IA e
  afirma não vender humanizador).
- **Jev (TypeSafe, corrigido de "TapeSafe"):** modelo System 1 — decisão e
  classificação (ex.: tipo de lead, estágio do CRM), com limiar de confiança e
  rota para humano abaixo do limiar. Não gera texto.
- **NotebookLM (conta Google do usuário):** muito além de roteiro — centro
  nervoso e norteador, consultado do início à produção e nas decisões de
  criativos.
  - **Caderno canônico:** conceito do projeto, objetivo, loja, redes, como é
    feito, onde pesquisa concorrência e como modela sem copiar, e a persona
    que evolui à medida que aprende e que novos conectores/processos entram.
  - **Persona:** documento versionado no repo, que alimenta o canônico;
    atualizada por aprovação, não em silêncio.
  - **Cadernos efêmeros:** um por criativo/publicação, com só o trecho
    relevante do canônico mais as fontes daquele asset; geram roteiro, texto e
    prompts de imagem, exportam para Drive e repo, e depois são deletados
    junto com o chat do NotebookLM.
  - **Limite:** sem API oficial estável; entra como fonte semi-manual, com o
    texto exportado como contrato, não como dependência ao vivo de cada post.
  - **Governança:** aconselha e propõe; não aprova nem publica.
- **Criativo (Muse):** imagens, vídeos e edição, com motion graphics via
  Remotion / HyperFrames / FFmpeg. Fluxo discutido: roteiro do NotebookLM →
  composição com a brand sheet → storyboard para o usuário ver antes de
  renderizar → render → arquivo versionado → aprovação → publicação.
- **Runway:** geração complementar de vídeo, não prova falsa de produto. O
  processo real continua sendo o protagonista.
- **Magic Patterns e Mobbin (Pro disponível, segundo o usuário):**
  secundários e opcionais, como referência visual para painel e criativos.
  Podem complementar o NotebookLM na parte visual; nunca travam a produção se
  estiverem ausentes, e podem ser descontinuados depois.
- **Skills como contratos determinísticos, com agente de IA em primeiro
  plano.** Cada fase, ferramenta, etapa e interrelação mapeada para a skill
  correspondente, com entradas, passos, pontos de decisão, condições de
  parada e saídas — ajustável, desde que a mudança fique registrada e não
  quebre a guardrail. Modelos externos (skills, plugins, ferramentas) entram
  de forma agnóstica, mesmo quando focados numa ação específica; o usuário
  define em que pode ser aplicado e o setor de foco, e o Muse observa
  tecnicamente outros setores onde o padrão também serve.

## Drive como arquivo criativo (5 TB, segundo o usuário)

- Todo criativo (imagem e vídeo) catalogado, descrito, relacionado, contado e
  com histórico de uso, guardado no Google Drive, orientado a reutilização e
  a prazos/períodos das plataformas.
- Estrutura proposta na discussão (a confirmar no fechamento):
  `TuttiBom/00_Identidade/`, `01_Brutos/`, `02_Criativos/`,
  `03_Publicacoes/` por rede, conta e data.
- Nome padrão proposto, ex.: `20261030_fita-cetim_video-processo_facebook_v01.mp4`.
- O arquivo fica no Drive; a ficha e a contagem ficam no banco (abaixo).
- Pasta "CRM TuttiBom" e planilha "CRM TuttiBom — Interessados" já existem no
  Drive; as 5 abas ainda não foram preenchidas porque o Sheets não estava
  conectado na última checagem (2026-10-30).

## Banco de dados — recomendação técnica discutida (não decidida)

- **Recomendado para produção: Supabase Postgres como sistema de registro**
  (contas, redes, produtos, criativos, publicações, usos, falhas, métricas,
  tarefas). É o que permite contar falhas por dia/período, contar usos de
  cada criativo e alimentar o painel sem depender do telefone.
- Não há conector nativo de Supabase no catálogo do Muse; a conexão seria por
  API REST do Supabase ou cliente Postgres, com a chave no fluxo seguro,
  nunca no chat. O usuário tem conta Supabase paga (versão inicial Pro) e
  servidor online; criar o projeto e passar o acesso pelo fluxo seguro fica
  para quando for decidido — não agora.
- **Drive = arquivo; banco = índice** (o banco guarda só ponteiro, ficha e
  histórico).
- **SQLite só como protótipo ou fila local** — bom para desenhar o esquema e
  testar offline, ruim como produção multi-rede (preso a um aparelho, com
  backup e sincronização frágeis). Não usar SQLite no celular como banco
  principal.
- **Leads fora do primeiro passo:** o banco inicial cobre criativos, logs e
  métricas. Dados pessoais de comprador só entram depois, com decisão
  separada de privacidade e acesso restrito; por enquanto vale a regra atual
  de notas privadas no Drive.

## Painel — abas e observabilidade, como discutido

- **Mapa:** hierarquia Guardrails → check de acesso Android → skills de
  setor → decisão System 1 (Jev) e geração System 2 (Muse/NotebookLM) →
  execução (conector da Página ou ADB da conta pessoal) → auditoria e painel.
- **Setores separados como módulos:** Marketplace, Publicações, Interações,
  cada um com sua máquina de estados e sua fila. Publicação em ambas as
  frentes (feed e histórico/stories), e Página + Marketplace quando fizer
  sentido.
- **Aprovações:** o que está parado esperando o usuário, com texto e mídia
  exatos, nunca um "aprovar tudo".
- **Falhas:** taxonomia em dois eixos — crítica e que interrompe (ADB fora,
  prompt de rede sem resposta, verificação do Facebook, sessão expirada) vs.
  não-crítica e que não interrompe (métrica atrasada, Jev com baixa confiança
  e rota para humano, render que falhou e pode ser refeito). Toda falha vira
  registro com causa, impacto e próxima ação.
- **Contadores de falhas por dia e período**, para montar estratégias de
  correção e atenção.
- **Observabilidade constante em todos os eixos:** contagem de tokens por
  provedor e por tarefa, disponibilidade de cada agente e conector com último
  check, saúde do S10 (bateria, disco, memória, uptime, reinícios e estado
  físico), publicações pendentes, atrasadas e aprovadas. Se custo por lote
  subir ou confiança do Jev cair, o sistema degrada para revisão humana,
  nunca acelera publicação para compensar.

## Repositório — existe, mas o nome não serve mais

- Existe um repositório local do projeto em `~/workspace/facebook-s10-adb`
  (skills, catálogo, templates, ops, docs). Ainda não foi para o GitHub, por
  decisão do usuário e por um bloqueio na instalação do app do Muse no
  GitHub. Existe outro repositório separado, só de acesso ao aparelho:
  `jvmendesjr/acesso-dispositivo-smartphon`. São duas coisas diferentes e
  devem continuar separadas.
- O nome atual é específico demais para o novo escopo modular. Proposta do
  Muse na discussão (NÃO decidida): **tuttibom-ops** — a marca viaja por
  todas as redes sem prender a Facebook, S10, fita ou impressão 3D; dentro
  dele, `core/` agnóstico e `contas/<marca>/<rede>/` só como configuração.
  Se um dia o motor virar multi-marca de verdade, extrair `core/` para um
  nome totalmente agnóstico (ex.: `ops-agente`). **O nome adequado final
  ainda está em aberto e cabe ao usuário escolher.**

## Correção registrada nesta noite (não repetir o erro)

- A avaliação de que a discussão "cobre 80% a 90%" do que o usuário precisa
  foi **retirada pelo próprio usuário** como otimista demais: há muito mais a
  tratar e mais será descoberto durante o desenvolvimento. Não usar mais
  esse percentual.

## Em aberto (não inventar, não fechar sem o usuário)

1. Preço ajustado da fita de cetim para o Facebook (bloqueia o rascunho do
   anúncio no Marketplace) — valor ainda não definido pelo usuário.
2. Custo por rolo (não fornecido) e termos de entrega/retirada no Cariri.
3. Nomes das cores da fita, regra de aprovação da prévia e tamanho/repetição
   da arte.
4. Processo específico de texto para publicações (ainda a ser discutido).
5. Reavaliação da identidade visual existente.
6. Nome agnóstico final do repositório/projeto.
7. Criação do projeto Supabase e passagem de acesso pelo fluxo seguro
   (quando decidido).
8. Ligação da conta da loja no conector (futuro, só como auxiliar de Página).
9. Fechamento da discussão → só então criar o painel visual e a arquitetura
   final no repositório.
