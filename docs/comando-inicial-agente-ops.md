# Comando inicial padrão — agente da operação TuttiBom OPS

**Fluxo:** o operador escolhe as funções e vincula a atribuição ao
perfil HTTP. O agente recebe o [diretório de entrada](../agent-entry/tuttibom-ops/)
com o cliente já configurado e confere seu
manifesto. Ele não lista o catálogo, ativa uma referência ou pede novo
OK pelas mesmas funções.

**Status:** o catálogo, a autorização e o atendimento estão disponíveis
no [laboratório](operacao/mcp-ops-laboratorio.md), com o host sintético
iniciado e `--laboratorio <diretório>` antes do subcomando. Ainda não
conecte a uma operação real.

## 1. Comandos da usuária

No cliente administrativo autenticado, listar todas as funções, com
número estável, área, nome e risco de cada uma:

```sh
tuttibom-ops-admin --laboratorio /tmp/tuttibom-ops-lab listar-atribuicoes
```

Registrar a autorização só para os números escolhidos. `01.01` e
`01.02` são, respectivamente, ler conversa e responder no atendimento.
Uma função crítica, como responder, precisa ser selecionada pelo seu
número, nunca incluída automaticamente por selecionar uma área.

```sh
tuttibom-ops-admin --laboratorio /tmp/tuttibom-ops-lab autorizar --agente ana-teste --funcoes 01.01
```

Para um perfil HTTP cadastrado no host, o comando retorna o escopo
vinculado, sem referência de ativação. Configure endereço e credencial
individual no cliente, não no prompt. Para testes de desenvolvimento
por stdio, siga o fluxo separado no guia do laboratório.

## 2. Comando que a usuária entrega ao agente

Se precisar, use o [prompt de entrada](prompt-entrada-agente-ops.md)
sem preencher área, IDs ou referência. Ao retirar ou trocar
um agente, use o [prompt de desvinculação](prompt-desvinculacao-agente-ops.md)
e confirme a revogação administrativa antes de liberar o sucessor.
