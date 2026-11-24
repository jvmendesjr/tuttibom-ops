# Skills canônicas por área

O `SKILL.md` é a fonte de instruções do cargo: persona, prompt de trabalho,
procedimentos, decisões, exceções e encaminhamentos. O catálogo lista ações
que o servidor pode autorizar. O prompt de entrada só inicia a ativação;
não substitui a skill nem amplia a atribuição.

| Área | Skills | O que o MCP entrega hoje |
|---|---|---|
| `01` Atendimento | [Ana: persona](../../skills/ops-ana-atendimento/SKILL.md), [triagem](../../skills/ops-ana-triagem/SKILL.md), [resposta](../../skills/ops-ana-resposta/SKILL.md) | `01.01` recebe persona e triagem. `01.02` acrescenta a skill de resposta e requer `01.01` selecionada. |
| `02` CRM e Vendas | [Analista de CRM e Vendas](../../skills/ops-crm-vendas/SKILL.md) | `02.01`–`02.05`: inventariadas, não concedidas. |
| `03` Produto e Catálogo | [Consulta de SKU](../../skills/ops-produto-consulta/SKILL.md) | `03.01`: SKU e preço versionado, sem confirmação de estoque. |
| `04` Criativos e Mídia | [Estúdio](../../skills/ops-criativos-midia/SKILL.md) | `04.01`–`04.02`: inventariadas, não concedidas. |
| `05` Social e Conteúdo | [Editor](../../skills/ops-social-conteudo/SKILL.md) | `05.01`–`05.02`: inventariadas, não concedidas. |
| `06` Anúncios e Aquisição | [Analista de Aquisição](../../skills/ops-anuncios-aquisicao/SKILL.md) | `06.01`: inventariada, não concedida. |
| `07` Pedidos, Produção e Pagamento | [Coordenador de Pedidos](../../skills/ops-pedidos-producao/SKILL.md) | `07.01`–`07.02`: inventariadas, não concedidas. |
| `08` Plataforma e Manutenção | [Manutenção Técnica](../../skills/core-plataforma-manutencao/SKILL.md) | Não aparece no manifesto do Ops. O Core permite consultar essa skill em `ler_doc`, não executar manutenção. |

`01.01`, `01.02` e `03.01` estão liberadas somente no laboratório.
Material das demais áreas documenta o fluxo, mas não autoriza improviso
por fora do MCP nem representa uma função pronta.

## Publicação e revisão de skills

1. Crie ou atualize a skill junto ao fluxo. Inclua a persona, o procedimento
   passo a passo, limites, aprovações, encaminhamento e casos de referência.
   Use exemplos fictícios; não inclua segredos, dados de comprador, endereços
   de conexão nem instruções para contornar o Ops.
2. Antes de conceder uma função, associe as skills ao **ID exato**.
   Conteúdo comum pode ser compartilhado; se uma skill ensinar ações de
   funções diferentes, separe esses procedimentos antes de expô-la.
   Um mesmo cliente pode receber mais de um papel sem ganhar o restante
   das áreas.
3. Teste no cliente MCP real quais skills chegam, quais são recusadas e
   se a confirmação exige a leitura de todas as versões do manifesto.
   O host carrega os arquivos no início. A versão é o SHA-256 dos bytes
   do arquivo e integra o hash do manifesto. Não há carga dinâmica de
   um arquivo indicado pelo agente.
4. Teste o comportamento do agente nos casos de referência. A leitura
   registrada pelo MCP não prova compreensão, e confirmar o manifesto
   não aprova a execução de uma ação.

Veja a [D-010](../decisoes/D-010-2026-11-17-skills-politica-canonica.md),
os [prompts de entrada](prompts-ops-por-area.md) e o
[inventário Core e Ops](mcp-core-e-ops.md).
