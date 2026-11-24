# Core e Ops: fronteira, tarefas e papéis

## Dois MCPs, sem sobreposição

- **`tuttibom-core-mcp`** é a continuação do MCP que já era usado para
  desenvolvimento, manutenção e apoio à gestão. Continua **somente
  leitura**: estado, decisões, arquitetura, documentação e diagnóstico
  técnico. Não gerencia leads, aprova envios, responde clientes, executa
  mudanças de infraestrutura nem opera ferramentas da loja. O comando
  legado `tuttibom-mcp` aponta para o Core.
- **`tuttibom-ops-mcp`** é a interface das tarefas operacionais. Expõe só
  funções concedidas por ID e as skills necessárias a essas funções. Não
  expõe repositório, shell, ambiente, credenciais, logs técnicos nem o
  catálogo administrativo completo. Manutenção de plataforma (setor
  `08`) fica fora do Ops; os IDs antigos `08.xx` permanecem reservados
  e não são concedidos.

O Ops deve ser a entrada de **todas** as tarefas da loja, não um único
agente com acesso a tudo. A lista abaixo define o escopo planejado;
**não** significa que todas as ferramentas já estão disponíveis.

| Área / persona | Tarefas do Ops | Limite, encaminhamento e estado atual |
|---|---|---|
| `01` Atendimento / **Ana** | Ler fila, histórico e mídias; acolher e qualificar; preparar e responder; encaminhar exceções e pós-venda; preservar e confirmar pendências. | `01.01` e `01.02` testadas também pelo MCP no Chatwoot isolado com PNG e dados fictícios. Ingestão contínua e áudio real não validados. A Ana não confirma pagamento, frete ou prazo pelo produtor. |
| `02` CRM e Vendas / **Analista de CRM e Vendas** | Registrar lead, interesse, resumo e próximo passo; mover etapa; marcar motivo de perda; programar follow-up dentro da janela; consultar histórico e encaminhamentos. | `02.01`–`02.05` inventariadas, ainda não concedidas. Programar follow-up não autoriza enviá-lo; Atendimento envia. |
| `03` Produto e Catálogo / **Especialista de Produto e Catálogo** | Consultar SKU, preço, cor e disponibilidade; manter variações, catálogo 3D e fotos autorizadas mediante aprovação. | `03.01` consulta preço versionado no laboratório, sem confirmar estoque. Escritas, disponibilidade real e demais evoluções ainda não expostas. |
| `04` Criativos e Mídia / **Estúdio de Criativos e Mídia** | Consultar biblioteca; preparar prévia fictícia, imagem, vídeo e motion; versionar e apresentar conteúdo para aprovação. | `04.01`–`04.02` inventariadas, ainda não concedidas. Não envia a cliente nem publica. |
| `05` Social e Conteúdo / **Editor de Social e Conteúdo** | Planejar calendário; escrever e revisar rascunhos; agendar ou publicar material aprovado; manter a identidade da Página. | `05.01`–`05.02` inventariadas, ainda não concedidas. Sem preço em legenda ou atendimento improvisado em comentário. |
| `06` Anúncios, Aquisição e Concorrência / **Analista de Aquisição e Anúncios** | Pesquisar ofertas públicas, fonte e data; preparar listagens e campanhas, acompanhar aquisição e encaminhar interessados. | `06.01` inventariada, ainda não concedida. Gasto e publicação exigem função separada e aprovação de verba, destino, texto e mídia. |
| `07` Operação, Produção e Pagamento / **Coordenador de Pedidos, Produção e Pagamento** | Registrar pedido, prova, pagamento confirmado, produção, frete validado, retirada ou entrega; encaminhar pós-venda. | `07.01`–`07.02` inventariadas, ainda não concedidas. Não cobra, não cria link e não declara pagamento sem confirmação do responsável. |
| `08` Plataforma e Manutenção / **Manutenção técnica (Core)** | Diagnosticar serviço, dependência, bloqueio de plataforma e defeito de código. | Fora do Ops. Core só consulta; mudanças de infraestrutura são executadas fora dos MCPs, com autorização própria. |

## Como um cliente recebe seu papel

1. O operador configura a conexão no cliente, fora do prompt, e escolhe
   os IDs da atribuição. Pode conceder uma ou várias áreas a um cliente
   ou distribuir funções entre clientes. Não há concessão automática
   por nome de persona ou área inteira.
2. No HTTP de laboratório, o operador vincula a credencial individual
   à seleção antes de entregar o cliente. O [prompt de entrada](../prompt-entrada-agente-ops.md)
   é opcional. O agente não recebe IDs, referência, endereço ou chaves no
   prompt. Um modelo ou fornecedor não é requisito do papel.
3. O cliente encontra o manifesto em `ops_minhas_atribuicoes`.
   Cada papel indica `SKILL.md` versionados por SHA-256 e lidos por
   `ops_ler_skill`. Persona, instruções e procedimentos vêm dessas skills,
   não do nome do bot nem de um segundo guia. Não há leitura arbitrária
   de arquivos, nem acesso a skills de funções não autorizadas.
4. O cliente lê as skills e confirma o manifesto. Só o titular
   confirmado pode escrever na área. O servidor controla o que o agente
   pode fazer, mas não prova que o modelo entendeu a persona. Valide o
   comportamento de cada cliente em casos representativos antes de liberá-lo.
5. A autorização de função não aprova texto, mídia, pagamento ou verba.
   Na troca, use o [prompt de desvinculação](../prompt-desvinculacao-agente-ops.md)
   e revogue a atribuição no servidor; o prompt não revoga acesso.

O inventário de cada setor está no [índice de setores](../setores/README.md).
Veja as [skills por área e a política de entrega](skills-por-area.md).
A [D-010](../decisoes/D-010-2026-11-17-skills-politica-canonica.md) define
as skills como fonte canônica dos fluxos. Os playbooks ainda sem
ferramentas disponíveis orientam o desenvolvimento, mas não são
entregues como atribuições em operação.
Uma função nova só passa de inventariada para disponível quando tiver
permissão por ID, skill para esse escopo, teste do caminho real e das
recusas, aprovação exigida aplicada pelo servidor e teste de
transferência do titular.
