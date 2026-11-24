# Blueprint inicial — tuttibom-ops com Paperclip no servidor PC

> Status: RASCUNHO INICIAL, 2026-11-01.
> Para discussão e atualização. Nada aqui está aprovado para a main,
> nada foi implementado, e nenhum agente, organização ou MCP foi criado
> ainda a partir deste documento.
>
> Atualização 2026-11-16: várias seções foram superadas por decisões
> posteriores — ver `docs/decisoes/` (D-002, D-003, D-004) e o roadmap §12
> (estado atual).

## 1. O que é

O tuttibom-ops é o sistema de operação da loja TuttiBom, no Cariri
(Juazeiro do Norte / Crato / Barbalha), para vender principalmente
fitas de cetim personalizadas e itens impressos em 3D, com o Facebook
como primeira rede aprovada e arquitetura modular para outras redes
depois.

Este blueprint descreve um novo caminho, em branch, sem substituir o
que já funciona: o Paperclip passa a organizar o trabalho em uma
empresa no servidor PC, os agentes próprios passam a executar tarefas
com modelos via 9Router, o Muse passa a ser o provedor de mídia quando
o fluxo pedir, e o Galaxy S10 Lite continua sendo a superfície de
execução no Facebook via ADB.

## 2. Decisões já tomadas

- Marca e projeto: TuttiBom, repositório tuttibom-ops.
- Primeira rede: Facebook, via aplicativo no S10, por ADB.
- Mídia: 100% fictícia, gerada por IA/código, sem uso de foto ou vídeo
  real de cliente. O rótulo de IA é ligado quando o Facebook o exige
  para conteúdo realista criado por IA.
- Nada é publicado, enviado, respondido com compromisso ou fechado em
  preço sem aprovação do usuário ao texto exato.
- Nenhum dado pessoal de comprador vai para o repositório, para o
  painel ou para este blueprint. Notas por lead ficam só no Drive
  privado do usuário.
- O painel é somente leitura para o usuário; só o Muse o edita, após
  discussão honesta quando o usuário sugere mudança.
- Navegação no S10: cautelosa, humanizada, um passo por vez, com a
  tela verificada e acordada antes de qualquer toque, sem rajadas
  de tentativas.
- Railway está fora do escopo deste projeto e não entra na
  arquitetura, no painel ou na lista de provedores.

## 3. Decisões propostas, ainda não aprovadas

- Usar o Paperclip já instalado no servidor PC, com uma organização
  nova só para este projeto.
- Usar agentes próprios no Paperclip, com modelos via 9Router, em
  vez de conectar Claude Code ou Codex como padrão inicial.
- Criar uma branch nova no tuttibom-ops para este caminho e promover
  para a main só se os critérios da seção 10 passarem.
- Ter um agente mantenedor, com acesso a um MCP do projeto, para
  propor melhorias no sistema.
- Ter o Muse como provedor de mídia, e não como runtime de todos os
  agentes. (Ver seção 6: isso é uma mudança em relação à ideia
  anterior de o Muse conduzir todas as cadeiras.)

## 4. Arquitetura em camadas

```
PC servidor
  Paperclip (organização nova: TuttiBom)
  9Router (roteador local de modelos, endpoint OpenAI-compatível)
  PostgreSQL do Paperclip (ou Postgres externo, se o embutido falhar)
        |
        | issues, metas, orçamentos, aprovações, auditoria
        v
Agentes próprios (via 9Router)
        |
        | tarefa de mídia com brief fechado
        v
Muse, provedor de mídia (nesta conversa / VM)
  devolve arquivo + descrição + histórico de uso, como rascunho
        |
        | só após aprovação do texto exato pelo usuário
        v
Galaxy S10 Lite, via ADB
  Facebook (Feed, e futuramente Stories e Marketplace)
        |
        v
Drive privado do usuário
  arquivo de criativos e CRM por lead (sem dados no repo)
```

O S10 não roda o servidor Paperclip neste desenho. O S10 continua
sendo a estação de execução no Facebook. O servidor PC é o plano de
controle. A VM do Muse é o operador e o provedor de mídia.

## 5. Papéis propostos no Paperclip

Nenhum destes agentes foi criado ainda. A ordem importa: o primeiro
agente de uma empresa no Paperclip é sempre o CEO.

- CEO: lê a meta da empresa, propõe estratégia, cria tarefas e
  delega. Não publica nada sozinho.
- Conteúdo: prepara textos e roteiros, sempre como rascunho.
- Mídia (provedor externo, Muse): recebe brief, entrega mídia
  fictícia, descreve e registra uso. Não publica.
- Triagem: organiza interessados, prepara respostas como rascunho,
  sem enviar antes da aprovação do texto exato.
- Publicação S10: monta a publicação no S10 via ADB, só após
  aprovação, e confirma no Feed com captura e texto conferido.
- Mantenedor: propõe melhorias em docs, skills e estrutura, em
  branch, sem se autoaprovar e sem publicar.

Por trás de papéis diferentes, um mesmo runtime não vira modelos
independentes. Se um papel for operado pelo Muse e outro por um
modelo via 9Router, isso deve ficar registrado na tarefa, para a
auditoria não fingir separação que não existe.

## 6. Como o Muse entra como provedor de mídia

Quando o fluxo pedir mídia, o Paperclip abre uma tarefa com um brief
fechado:

- Formato: 9:16 (Stories/Reels) ou 4:5 (Feed), ou outro, explícito.
- Texto na arte, se houver, exato e revisado.
- Cores, marca e referência visual, sem foto de cliente.
- Uso pretendido e data/período.
- Status esperado: rascunho.

O Muse devolve:

- O arquivo da mídia, com nome e versão.
- Descrição do que a mídia mostra, para catálogo e reuso.
- Registro de uso: onde foi usada, quando, e se foi aprovada.
- Status: rascunho, aguardando aprovação.

Publicação é um passo separado, com aprovação própria, e só acontece
no S10 via ADB, após o texto exato ser aprovado.

## 7. 9Router: o que ele resolve e o que não resolve

O 9Router é um proxy local que expõe um endpoint OpenAI-compatível
e encaminha pedidos para vários provedores e modelos, com fallback
em camadas (assinatura, depois barato, depois gratuito) e tradução
de formato entre provedores.

O que ele resolve:

- Um só endpoint para os agentes, em vez de uma conta direta por
  agente e por fornecedor.
- Troca de modelo por agente e por tarefa, sem reconfigurar o agente.
- Continuidade quando um provedor atinge limite, caindo para o
  próximo da fila.

O que ele não resolve, e precisa de regra:

- Fallback troca de modelo, e modelo diferente não é equivalente.
  Para texto final, arte final e qualquer saída que vá ao público,
  travar um modelo fixo por tarefa, sem fallback silencioso.
- Compressão de tokens (RTK) pode alterar fidelidade de saída de
  ferramenta. Não usar compressão agressiva para logs, leituras
  completas de arquivo e qualquer dado cuja fidelidade seja crítica,
  sem teste antes.
- O painel do 9Router, se exposto fora do localhost, precisa de
  autenticação própria. Por padrão, tratar como serviço local.

## 8. Mantenedor e MCP: escopo, não chave-mestra

O mantenedor é útil para o sistema evoluir sem depender de uma
sessão só, mas ele não pode receber todas as chaves e segredos em
texto, nem aprovar o próprio trabalho.

Regras do MCP do projeto, a definir antes de criar:

- Leitura: repositório, docs, issues e metas da empresa TuttiBom.
- Escrita: só em branch, abrindo proposta de mudança para revisão.
- Segredos: por referência, pelo nome, nunca devolvendo o valor.
  O Paperclip já trabalha com segredos criptografados que os
  agentes referenciam sem copiar os valores; o MCP segue a mesma
  lógica.
- Proibido para o mantenedor: publicar no Facebook, enviar mensagem
  a comprador, fechar preço, aprovar a própria mudança, ler ou
  escrever dado pessoal de comprador.
- Chave do mantenedor: escopada só para esta empresa do Paperclip,
  nunca um token de board com acesso a tudo.
- Toda mudança do mantenedor só vai para a main após aprovação do
  usuário, com a mudança descrita em linguagem simples.

## 9. Dados e onde cada coisa mora

- Paperclip no PC: empresa, agentes, tarefas, metas, orçamentos,
  aprovações e auditoria.
- 9Router no PC: configuração de provedores, modelos e combos.
  Chaves de provedor ficam no cofre do 9Router / do Paperclip,
  nunca neste documento e nunca no repositório.
- Repositório tuttibom-ops: regras, docs, skills, templates e
  painel, sem dado de comprador e sem segredo.
- Drive do usuário: arquivo de criativos e CRM por lead, privado.
- S10: execução no Facebook via ADB, com janelas curtas e
  verificação de tela antes de cada toque.

## 10. Branch e critério para promover para a main

Branch proposta: `paperclip-9router`, a partir do estado atual do
trabalho, não só da main remota.

Atenção prévia, já verificada: a pasta local do tuttibom-ops nesta
VM não é um repositório git (o push de 2026-10-31 foi um snapshot),
e há documentos locais de 2026-11-01 fora daquele snapshot. Antes de
abrir a branch, é preciso reconciliar o trabalho local com a main
remota, senão a branch perde trabalho.

"Deu certo" significa passar nestes quatro testes, nesta ordem:

1. Organização nova criada no Paperclip do PC e um agente via
   9Router respondendo uma issue de teste.
2. Um pedido de mídia voltando como rascunho aprovado, sem
   publicação automática.
3. O mantenedor abrindo uma mudança em branch, sem vazar segredo
   e sem se autoaprovar.
4. Uma publicação no S10 continuando só após aprovação do texto
   exato pelo usuário.

Se um teste falhar, o trabalho fica na branch. Promoção para a main
é decisão do usuário, após ver o resultado dos testes.

## 11. O que já está provado e o que ainda não está

Provado:

- Publicação no Feed via ADB, com texto exato e rótulo de IA, em
  2026-11-01.
- Ponto de execução do ADB no PC, com platform-tools isolado e
  pareamento próprio da chave do PC, provado em 2026-11-01.
- Publicação do Stories 9:16 do piloto via ADB do PC, com
  rótulo de IA ligado, em 2026-11-01 ~12:43-12:44.
- Publicação do tuttibom-ops no GitHub, em 2026-10-31.
- SSH para o S10 via Tailscale e SSH para o PC via Tailscale, com
  aprovação do usuário.
- Criação do diretório vazio `Workspace/tuttibom-ops` no PC, em
  2026-11-01. (Atenção: no PC a pasta é `Workspace`, com W
  maiúsculo; `workspace` minúsculo não existe lá.)

Não provado:

- Organização nova no Paperclip do PC.
- Agente via 9Router executando uma issue de ponta a ponta.
- MCP do projeto e mantenedor operando com segredos por referência.
- Resposta a interessado via ADB.
- Preço para o Facebook. Segue indeciso e bloqueia o rascunho do
  anúncio no Marketplace; nenhum preço deve ser inventado.
- Teste de ponta a ponta da recuperação do ADB (queda real,
  reinício, troca de rede). Segue adiado pelo usuário.

## 12. Perguntas abertas para a próxima conversa

1. Qual modelo fixo usar para texto final e qual para rascunho e
   pesquisa, no 9Router?
2. O mantenedor pode escrever em quais pastas, e quais pastas são
   só leitura para ele?
3. A organização nova no Paperclip se chama TuttiBom, ou outro nome?
4. A branch `paperclip-9router` nasce do trabalho local atual, com
   reconciliação prévia, ou o usuário prefere primeiro sincronizar
   o trabalho local na main e só depois ramificar?
5. O diretório novo no PC recebe uma cópia dos docs e skills atuais,
   ou começa só com este blueprint e cresce a partir dele?
6. Qual é o primeiro teste de ponta a ponta que vale a pena: uma
   issue de conteúdo, uma de mídia, ou uma de triagem?

---

## 13. Atualização 2026-11-01 — decisões após o rascunho inicial

Avaliação: sim, era necessário atualizar. Este rascunho foi criado
às 10:37, antes das decisões abaixo, tomadas entre 10:48 e 10:55 do
mesmo dia. Nada nesta seção cria agente, organização ou MCP, e
nada aqui autoriza publicação.

### 13.1 S10 principal, Camofox secundário — DECIDIDO (SUPERSEDEDO por D-004, 2026-11-16)

> **SUPERSEDEDO por D-004 (2026-11-16):** o S10/ADB foi pausado e o
> Camofox é o navegador único do TuttiBom OPS (painel, redes sociais,
> criativos). O que segue nesta seção é o registro da decisão original
> de 2026-11-01, não a prática atual.

- O S10 via ADB continua sendo o caminho principal para tudo que
  toca a conta da loja. Não há migração total para o Camofox e o
  S10 não é abandonado.
- O Camofox no PC fica só como secundário, em teste, sem tocar na
  conta por enquanto. Uso inicial previsto: leitura e pesquisa,
  perfil fixo, sem rotação de fingerprint, sem rodar em paralelo
  com o S10 na mesma ação.
- Motivo registrado: o S10 é o ambiente real já aquecido e com
  publicação provada; um navegador novo no servidor traz risco
  de checkpoint, e o S10 continua sendo o dispositivo familiar
  de recuperação se um checkpoint aparecer.
- Teste do S10 continua, com o Camofox como reserva.

### 13.2 Divulgação de conteúdo de IA — ESCLARECIMENTO

Regra vigente, corrigindo qualquer leitura mais solta de "não
esconder IA":

- Seguir a regra da plataforma para conteúdo de IA, incluindo
  ligar o rótulo de IA quando a plataforma o exigir, como foi
  feito na publicação do piloto no Feed em 2026-11-01.
- Nunca dizer, nem insinuar, que o conteúdo não é de IA.
- Não colocar anúncio gratuito na legenda, como "feito por IA",
  só porque sim. O rótulo exigido pela plataforma e um anúncio
  na legenda são coisas diferentes.
- O texto da legenda só leva menção a IA se a plataforma exigir
  ou se o texto exato aprovado pelo usuário incluir essa menção.

### 13.3 Automação — filosofia confirmada

- A automação é agente em primeiro plano por desenho, com o
  usuário humano apenas nas aprovações críticas. O usuário não
  vê conflito nisso e entende essa automação como uma realidade
  legítima e crescente, que as plataformas deveriam levar a sério.
- O ponto anterior sobre "conflito" fica reenquadrado como aviso
  prático apenas: as plataformas hoje ainda dão checkpoint em
  sessão automatizada, mesmo com intenção legítima. Por isso a
  escolha de canal (S10 principal) e as travas de aprovação
  humana continuam como controles de risco, sem mudar o desenho
  agente em primeiro plano.

### 13.4 Infra confirmada no PC

- SSH para o PC via Tailscale confirmado em 2026-11-01, com
  aprovação do usuário no pedido da rede. Usuário `pc`, home
  `/home/pc`, pasta de projetos `Workspace` (com W maiúsculo).
- Diretório `Workspace/tuttibom-ops` criado e verificado vazio
  em 2026-11-01, antes deste blueprint. Este arquivo é o único
  conteúdo dele até esta atualização.
- Paperclip e 9Router já existem no PC, verificados só por
  listagem, sem leitura de credencial. Nenhuma organização nova,
  agente ou MCP foi criado a partir deste blueprint até aqui.

### 13.5 Teste do Stories 9:16 do piloto — EM PREPARAÇÃO

- Arte local confirmada em 2026-11-01: Stories 9:16, arquivo
  `20261101_fita-cetim_piloto-dia1-stories_facebook_v01.jpg`,
  1152x2048, 272K, já presente no telefone em
  `/sdcard/Download/tuttibom_fila/` desde 2026-11-01 00:51.
- Texto vigente do piloto é o mesmo do Feed, aprovado em
  2026-11-01, sem preço. Publicação nos Stories NÃO está
  aprovada: o checkpoint final é na pré-visualização no S10,
  antes de qualquer compartilhamento.
- Checagem do S10 em 2026-11-01 ~10:55: SSH ok, watchdog de ADB
  vivo, arquivo de endpoint atualizado às 10:53 com porta
  descoberta por mDNS. Ponto honesto: nesta VM o binário `adb`
  não foi encontrado nesta checagem, então o teste de conexão
  ADB a partir daqui fica pendente até localizar ou instalar o
  `adb`, ou definir outro ponto de execução. Isso não bloqueia
  o preparo do teste, mas bloqueia a execução dele.
- Próximo passo do teste, sem publicar: confirmar o ponto de
  execução do ADB, montar só até a pré-visualização nos Stories
  e parar para aprovação do usuário.

### 13.6 Perguntas abertas que mudaram

- A pergunta sobre migrar para o Camofox está respondida:
  não migrar, S10 principal, Camofox secundário.
- Seguem abertas as perguntas 1 a 6 da seção 12, mais estas:
  7. O teste do Stories usa o ponto de execução ADB a partir
     desta VM, do PC, ou de outro lugar?
  8. O Camofox secundário começa com leitura de quê, e com
     qual perfil fixo, quando o usuário aprovar esse teste?

---

## 14. Atualização 2026-11-01 — PC como ponto de execução do ADB e Stories publicado

Decidido e provado em 2026-11-01, entre 11:07 e 12:44. Esta seção
substitui o estado da seção 13.5, que dizia que o teste do Stories
estava em preparação, sem ponto de execução e sem aprovação de
publicação. Nada aqui é push para o GitHub; é atualização local
do blueprint no PC.

### 14.1 Ponto de execução do ADB: o PC — DECIDIDO e PROVADO

- Decidido pelo usuário em 2026-11-01 ~11:07: o PC, não a VM, é
  o ponto de execução do ADB, porque um agente do Paperclip no
  PC vai assumir essa tarefa no futuro, e o ADB deve morar onde
  o agente vai morar. O S10 continua sendo o aparelho principal;
  o PC é só onde o `adb` roda.
- O binário `adb` não foi encontrado nem nesta VM nem no PC na
  checagem de 11:07-11:08. Escolher o PC resolveu a arquitetura,
  não a ferramenta.
- Com aprovação do usuário, o platform-tools oficial foi
  instalado isolado em `~/platform-tools` no PC, sem apt e sem
  mexer no sistema: adb 1.0.41 / 37.0.1, verificado.
- A primeira conexão do PC falhou, com lista de dispositivos
  vazia, mesmo com o endpoint fresco do telefone.

### 14.2 Pareamento: é por chave de cada máquina

- A chave nova do `adb` do PC precisou de pareamento próprio.
  A lista de pareados na tela do S10 mostrava só o Termux local
  e outro computador; nenhum `pc`.
- Fluxo usado, com o usuário na tela: no S10, "Parear o
  dispositivo com um código de pareamento"; o telefone mostra
  um código de seis dígitos e uma porta de pareamento, que
  expiram rápido. A porta de pareamento também foi descoberta
  por mDNS no telefone, serviço `_adb-tls-pairing._tcp`, e o
  valor achado bateu com o da tela. No PC, `adb pair` com a
  porta de pareamento e o código, e depois `adb connect` na
  porta principal mostrada na tela do S10.
- Resultado: pareamento com sucesso, conexão como `device`,
  modelo SM-G770F confirmado, tela Awake, bateria 87%
  descarregando, arte do Stories presente no telefone.
- Código de pareamento, IP vivo e porta viva nunca são
  registrados neste blueprint: são efêmeros.

### 14.3 Porta efêmera, com churn real

- A porta principal mudou de novo logo após o pareamento. O
  arquivo de endpoint no telefone foi atualizado por mDNS e o
  PC reconectou na porta nova. O `adb` do PC também passou a
  listar o aparelho por descoberta mDNS.
- Observação honesta, sem causa estabelecida: às 12:02, a porta
  principal mostrada na tela do S10 não batia com a porta do
  serviço `_adb-tls-connect` no mDNS naquele momento, e a
  conexão na porta da tela funcionou enquanto a anterior, na
  porta do mDNS, tinha falhado. Não fixar nenhuma das duas:
  reler o endpoint / mDNS antes de cada conexão.
- Para o agente futuro do Paperclip: reutilizar o mesmo ponto
  de execução (`~/platform-tools/adb`, chave já pareada no PC,
  descoberta de endpoint por mDNS no telefone). A chave pareada
  mora no PC; se for regenerada ou o PC for reconstruído, o
  pareamento precisa ser refeito na tela do telefone.

### 14.4 Stories 9:16 do piloto — PUBLICADO

- Publicação aprovada pelo usuário em 2026-11-01 às 12:37
  ("já pode publicar"), substituindo o checkpoint só-de-prévia
  da seção 13.5.
- Facebook aberto como TuttiBom, Criar story, primeira miniatura
  da galeria era a arte do piloto, prévia conferida em 9:16
  cheio, rótulo de IA estava desligado e foi ligado antes de
  compartilhar, Público, compartilhamento no WhatsApp
  desativado, Compartilhar tocado, pedido de atalho na tela
  inicial recusado com "Agora não" (nenhum atalho adicionado).
- Confirmação no Feed: fileira de stories com "Seu story" e a
  miniatura da arte do piloto. Telefone deixado no Feed,
  bateria 85% às 12:46.
- Nota de observação: tocar em "Seu story" abriu o
  visualizador, mas a foto de 5 s avançou sozinha para o story
  seguinte antes da captura, então a prova é o cartão "Seu
  story" no Feed, não a captura do visualizador. Capturas com
  conteúdo de terceiros no Feed foram apagadas após a checagem.
- Segue não provado: resposta a interessado via ADB; preço
  para o Facebook, segue indeciso; teste de ponta a ponta da
  recuperação do ADB, segue adiado pelo usuário.

### 14.5 Perguntas abertas que mudaram

- A pergunta 7 da seção 13.6 está respondida: o ponto de
  execução do ADB é o PC.
- O teste 4 da seção 10 continua valendo: uma publicação no
  S10 continua só após aprovação do texto exato pelo usuário.
  O que mudou é o ponto de execução, não a trava.
- Seguem abertas as perguntas 1 a 6 da seção 12, e seguem não
  criados: organização nova no Paperclip, agente via 9Router,
  MCP e mantenedor. Atualização em 2026-11-05: as perguntas
  foram respondidas e registradas na seção 15 e no documento
  `docs/roadmap.md`; a criação continua pendente.

---

## 15. Atualização 2026-11-05 — Paperclip: stack do PQBR2 mapeada, decisões tomadas, roadmap criado

> Integração MCP Ops em desenvolvimento: WhatsApp e Messenger serão
> compostos por pilhas isoladas por inbox no mesmo host/escritor.
> [Contrato e rollout](operacao/mcp-ops-multi-inbox.md). Isso não modifica
> o Deskcomm nem ativa serviços reais. O desenho específico atual usa o
> canal Chatwoot existente, sem construir outro conector da Ponte.

> Nova vertente, 2026-11-23: a arquitetura atual dos MCPs está no
> [desenho de operação](rascunho-mcp-operacao.md). O Core é independente e
> somente leitura. O [inventário atual](operacao/mcp-core-e-ops.md) define
> as funções do Ops e a entrega de skills no manifesto por atribuição
> explícita. A integração atual é de laboratório. No HTTP, a credencial
> individual abre o escopo pré-vinculado, sem referência no prompt.
> O histórico abaixo não define o acesso
> dos agentes de operação.

Em 2026-11-05 o usuário pediu para conferir o PQBR2 no mesmo
servidor (`~/Workspace/PQBR2`) e usar arquitetura similar. Tudo
abaixo foi verificado por leitura de arquivos e checagem de
serviços no pc, antes de escrever. Nada foi criado ainda:
empresa, agentes, namespace, bank e MCP continuam pendentes.

### 15.1 O que foi enxergado no PQBR2

- Paperclip em instância separada `~/paperclip-pqbr2`, porta
  3110, empresa PQBR2 criada em 2026-11-05, agentes
  Pauta/Roteiro/Revisão/SEO via API com adapter
  `opencode_local`, heartbeats desligados, US$20/mês por agente.
- 9Router do PQBR2 na porta 20130, segredo de empresa
  referenciado por nome, combos `core-baixo`/`core-alto`/
  `core-revisao` em `config/modelos_9router.json`.
- Temporal Server do host (`localhost:7233`), namespace próprio
  `pqbr2`, workflow `produzir_short`, worker próprio.
- Contratos Pydantic v2 (`PautaEpisodio`, `RoteiroShort`,
  `Cena`), 23 testes passando.
- codebase-memory, projeto `PQBR2`, modo full, daemon na 9749.
- Hindsight, bank `pqbr2`, API na 8890 saudável; retain
  obrigatório ao fim de cada operação.
- MCP `pqbr2-mcp`, stdio, só leitura, 10 tools, entre elas
  `onde_esta_tudo` e `checklist_fim_operacao`; o MCP só indica,
  o agente age e grava via git.
- Postgres app próprio na porta 55435, com migrations e
  orçamento.
- NotebookLM: cadernos efêmeros por episódio via Camofox 9387,
  activities Temporal próprias (F4, em revisão).
- Flow: geração de vídeo por prompts manuais / Camofox, 720p,
  sem agente Flow no Temporal.
- Jev (TypeSafe, modelo de decisão, não LLM de texto): Gate 1
  de QA visual primeiro, depois Gates 2 e 3; tarefas tipadas
  Noul/Score/Choice/Box; integração real ainda pendente no
  PQBR2 (cliente stub).

### 15.2 Decisões do usuário (2026-11-05)

1. **Empresa no 3110**, na instância do PQBR2. Custo de memória
   quase zero (só linhas no mesmo banco); empresas isoladas
   entre si, com exportação por empresa para mover uma sozinha
   depois — segredos, caminhos locais e histórico não viajam.
2. **9Router na porta 20128**, o original do pc, não o 20130
   do PQBR2.
3. **Banco local por enquanto**: Postgres app no pc, mesmo
   padrão do PQBR2; Supabase fica para depois.
4. **Temporal implementado logo**, com planejamento, seguranças,
   testes e pesquisa de soluções da comunidade para a
   instabilidade do ADB (UiAutomator2, localizadores estáveis,
   esperas explícitas, animações desligadas, retries, nova
   checagem por screencap, fallback `adb shell input tap`).
5. **Agentes a planejar, começando só com o CEO.**
6. **Primeira issue de teste: criação e postagem simples de
   um reel.**
7. **Criativo é com o Muse; o Paperclip solicita e o Muse
   entrega.** O Paperclip não gera criativo.
8. **O Muse substitui o NotebookLM e o Flow do PQBR2** no
   caminho Paperclip: pesquisa/síntese e geração de vídeo são
   feitas pelo Muse, por uma única activity de polling,
   `solicitar_criativo_muse`. Os desenhos de NotebookLM e Flow
   continuam existindo no caminho manual, mas não são chamados
   por este fluxo.
9. **Jev como auditor e decisor tipado**: lista de 8 situações
   do TuttiBom a pontuar, e o Jev só é chamado onde fizer
   sentido, entregando sempre Noul/Score/Choice/Box. Gate 1
   primeiro; Jev não aprova publicação; áudio é medição em
   código, Jev fora.

### 15.3 Adaptação e fases

Detalhe completo em `docs/roadmap.md` (328 linhas em
2026-11-05): empresa TuttiBom, namespace Temporal `tuttibom`
com workflow `publicar_conteudo`, contratos
`Publicacao`/`Criativo`/`Lead` em Pydantic v2, bank Hindsight
`tuttibom`, projeto codebase-memory `TUTTIBOM`, MCP
`tuttibom-mcp` com 12 tools, fases F0–F8 (reconciliação do git,
empresa, memórias, MCP, contratos, Temporal, primeiro teste,
publicação piloto, promoção), com promoção para a main só se
os 5 critérios passarem.

Ainda em aberto: prefixo de issue da empresa (sugestão `TUT`),
porta do Postgres app local e organograma completo dos agentes.

### 15.4 Base implementada em 2026-11-05 (fora de ordem)

A pedido do usuário, sem reinventar a roda e com liberdade para
melhorar e descartar o que não faz sentido para o TuttiBom, a
estrutura, o MCP e as memórias foram feitos antes da F0 e da F1,
para que o MCP já tenha todas as funções acessíveis caso outro
agente precise atuar. Verificado pelo Muse após a implementação.

- Estrutura em `~/Workspace/tuttibom-ops`: 26 arquivos,
  `company/`, `config/`, `src/tuttibom/`, `scripts/`,
  `tests/`, `work/`, `docs/ESTADO.md`, `docs/operacao/`,
  `docs/decisoes/`, `AGENTS.md`, `README.md`, `Makefile`.
  Contratos e workflows só com README do que virá (F4/F5).
- MCP `tuttibom-mcp`: stdio, só leitura, 12 tools, testado
  via `tools/list`. `fila_publicacao` e `catalogo` avisam que
  os arquivos ainda não existem no PC, sem inventar conteúdo.
- Hindsight: bank `tuttibom` criado, com retain inicial
  verificado. codebase-memory: projeto `TUTTIBOM`, modo full,
  182 nós e 378 arestas.
- Melhorias sobre o PQBR2: `estado` e `git_status` explicam a
  F0 pendente em vez de erro cru; `ler_doc` aceita `ops/`,
  `catalogo/` e `templates/`; travas do TuttiBom nas
  instructions do MCP. Descartado: Folha stickman, Remotion,
  templates Flow, activities NotebookLM, workflow de Shorts,
  Postgres do PQBR2.
- Seguem pendentes: F0 (reconciliação git), F1 (empresa na
  3110 + CEO), F4 (contratos), F5 (Temporal), F6 (reel de
  teste), F7 e F8.

---

Documento inicial, para conversar e atualizar. Cada resposta às
perguntas das seções 12 e 13 vira uma edição deste blueprint, com
data, antes de virar implementação.

### 15.5 — Skills externas: decisões 2026-11-05

O usuário enviou 5 skills para os agentes do Facebook; analisadas
em 2026-11-05 sem instalar nada. **Aprovado o começo em ~18:05:**
skills 1 e 4, sanitizadas e adaptadas para PT-BR e Cariri, entram
primeiro na estrutura do Paperclip dos agentes responsáveis.

- **1 — ivangdavila/facebook-marketplace: adaptar (híbrido).**
  Fronteira de automação, memória, triângulo de preço e anúncio
  parado. Triagem, Publicação e Revisão.
- **2 — formula100k/motion-reels-f100k: parcial.** Regras sim
  (zonas seguras, densidade 1/5 s, motion board, QA), ferramenta
  não. Para o reel de teste. Conteúdo via Muse e Revisão/Jev.
- **3 — mvanhorn/pp-facebook-marketplace: descartar o uso.**
  CLI com cookies do Chrome replayando GraphQL, fora do S10 —
  maior risco de conta. Só referência de desenho.
- **4 — anthropics/content-creation: adaptar.** Estrutura de
  post social, ganchos e CTAs. Conteúdo via Muse e Revisão/Jev.
- **5 — coreyhaines31/social: adaptar (híbrido).** Pilares,
  ganchos + No AI Tells, reaproveitamento, calendário. Para depois
  do começo. Conteúdo, Triagem e CEO.

Detalhe completo no roadmap, seção 8; estado curto em
`docs/ESTADO.md`.

### 15.6 — Decisão 2026-11-05: Deskcomm como atendente, Muse como gestor

Decidido pelo usuário em 2026-11-05 ~21:11, após verificação no
mesmo dia. Nada foi mudado em nenhum sistema — só documentos.

- **O Deskcomm atende; o 9Router é o provedor dos modelos do
  agente dele; o Muse é o gestor junto com o usuário; o painel
  próprio fica só com conteúdo de social media e planos.**
- **A camada de agentes do Paperclip é substituída pelo agente
  do Deskcomm.** F1 (empresa na 3110) e F5 (Temporal) canceladas;
  o teste do reel continua como teste de conteúdo, fora do
  Paperclip. Fica a base: skills adaptadas, MCP `tuttibom-mcp`,
  Hindsight `tuttibom`, TUTTIBOM indexado, regras e guardrails.
- **A Ponte (`/home/pc/ponte`) é a ponte do Messenger** (e do
  Instagram): camada externa de conectores sobre o Deskcomm, sem
  fork, decidida em 2026-10-29. Conectores vivem na Ponte, nunca
  dentro do código do DeskComm. Estado honesto: ainda não existe
  código de adapter de Messenger ou Instagram — existe a
  arquitetura e o ponto de apoio no banco (`contact_channels`,
  migração 9032). A ponte é um projeto a construir, não uma
  conexão viva.
- **Painel reduzido a 2 abas: Conteúdo e Planos.** A aba Leads é
  cancelada (o kanban do Deskcomm é a visão de leads); as demais
  abas de operação saem do painel para as superfícies do
  Deskcomm.
- **Regras de virada do Deskcomm** (de `/home/pc/ponte/AGENTS.md`):
  nunca pull direto na branch local, nunca migration direto em
  produção, nunca `down -v`; sequência cópia de teste → staging
  → produção com backup/rollback; **sempre os dois composes
  juntos** (`docker-compose.prod.yml` + `docker-compose.ponte.yml`),
  ou o túnel Cloudflare perde a porta 3000 e a Ponte bloqueia.
  Não tocar no `cloudflared-ponte.service` sem aprovação.
- **WAHA:** externo, :3005, sessões `tutibom` e `petemcasa`
  WORKING; divergência não confirmada sobre onde vive a
  instância ativa (README da Ponte diz outro servidor; sondagem
  anterior viu container no PC). Decisão interno vs externo
  pendente antes de qualquer virada.
- **Ordem:** (1) validar 9Router como provider custom;
  (2) configurar o agente Deskcomm para o TuttiBom;
  (3) Muse gestor via MCP; (4) conector Messenger na Ponte;
  (5) ativar o Messenger e testar; (6) painel reduzido.

Detalhe completo no roadmap, seção 10; estado curto em
`docs/ESTADO.md`.

## 16. Atualização 2026-11-09 — Ana v9 volta ao 9Router (core-medio), funcionando

Em 2026-11-08 21:48 -03 o usuário publicou a v9 da Ana com o 9Router de
volta como provedor (custom/core-medio, credencial 9Router). A v8
(OpenRouter direto, z-ai/glm-5.3-flash) ficou superseded. Verificado
funcionando pelo Muse (só leitura, 2026-11-09 ~21:50 -03): 3 turnos
core-medio com status ok após a publicação, com respostas reais no
WhatsApp (conversa do Junior e uma conversa nova de cliente sobre MDF).

- Restaura a decisão de 2026-11-06 (modelos e agentes no 9Router) e o
  padrão da org (custom/core-medio).
- Ressalva inalterada: o teto de custo do Deskcomm não enxerga o gasto
  do core-medio (fora de ai_pricing); o controle real é do lado do
  9Router.
- Detalhe em `docs/ESTADO.md` (seção 2026-11-09) e
  `docs/decisoes/D-001-2026-11-09-ana-v9-volta-9router.md`.

## 17. Atualização 2026-11-17 — 3 frentes delegadas, revisadas e juntadas + MCP v0.1.1

Muse como coordenador; Cursor agent (`--print --trust`, `grok-4.7-high`)
no PC, um por worktree/branch a partir da `main` `cdd9497`. Merges
`57d2af8` (identidade), `c8e96b1` (contratos F4), `12a19f4` (skill 5);
estado em `0c9f1d9`.

- **F1 identidade (D-009):** `fb_trocar_capa.py` corrigido para a página
  oficial `100089750066330`; `--dry-run` exit 2 (`profile-fb` ocupado
  pelo `fb_agent`). Bio e posts F1-02 em rascunho. Ações ao vivo
  pendentes (janela do `profile-fb`, Pangram, Framer, Instagram).
- **F2 contratos F4:** `Publicacao`/`Criativo`/`Lead` (Pydantic v2),
  CLI `scripts/validate_contratos.py`, 68 testes, `make check` verde.
- **F3 skill 5:** `skills/tuttibom-facebook-social/` — fonte
  `coreyhaines31/marketingskills` skill `social` v2.5.2, commit
  `1f83744…`, MIT; `SKILL.md` byte-idêntico ao upstream.
- **MCP v0.1.1 (`cdd9497`):** `onde_esta_tudo` calculado no disco a
  cada chamada (o texto fixo desatualizado fazia todo agente novo
  sinalizar uma falha que não existia); autenticação única por
  ferramenta, já feita no PC.
- **Lição:** as sessões do Cursor tiveram o shell recusado — nenhuma
  verificação rodou nelas; o coordenador rodou tudo (testes, dry-run,
  Pangram, Framer, Zernio). Lançar por script (`/tmp/launch-frentes.sh`,
  `nohup` + `disown`); o comando inline por ssh travou e lançou
  agentes duplicados (um par por frente foi morto).
- **Bloqueios ao vivo:** Pangram sem créditos na conta de API;
  Framer sem projeto da TuttiBom (o único projeto é "Heartwarming
  Company"); renomeação da página ainda não aprovada (Zernio mostra
  "TutiBom" em 2026-11-17 17:26); Instagram sem @ no repo.

Detalhe em `docs/ESTADO.md` (seções "Frente social" e "Próximo passo")
e `docs/roadmap.md` §6/§14; entregas em `docs/frentes/`.
