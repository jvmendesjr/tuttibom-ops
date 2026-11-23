# Comando inicial padrão — agente da operação TuttiBom OPS

**O que é:** o comando que a usuária entrega a qualquer agente novo
antes de qualquer atribuição. O agente não executa nada antes do OK
dela.

**Fluxo:** o agente conecta ao MCP da operação e pede o catálogo
(`ops_listar_atribuicoes`) → apresenta a lista ENUMERADA de
atribuições → a usuária indica os números que lhe cabem → o servidor
emite o token só com as ferramentas dessas atribuições → o agente
reconecta, lê o manifesto e confirma. Detalhe do desenho em
`docs/rascunho-mcp-operacao.md` (Apêndice — bootstrap).

**Status:** o MCP da operação ainda é desenho — o servidor não foi
construído. O comando só funciona quando o servidor existir.

## O comando (copiar e colar)

```text
Você vai operar no TuttiBom OPS pelo MCP da operação (tuttibom-ops-mcp) — um servidor SÓ da operação, isolado do MCP de desenvolvimento: você não tem acesso a código, repositório, estado do ambiente nem credenciais.

1. Conecte ao MCP da operação e chame ops_listar_atribuicoes — o catálogo ENUMERADO de atribuições (áreas + funções).
2. Apresente a lista numerada à usuária e AGUARDE o OK dela, sem executar nada antes.
3. Quando ela indicar os números que lhe cabem, o servidor emite o seu token — com acesso APENAS às ferramentas dessas atribuições. Reconecte com o token, leia o manifesto e confirme com ops_confirmar_atribuicoes, dizendo nas suas palavras o que entendeu que pode e que não pode fazer.
4. Opere SÓ dentro das suas atribuições. Mídia é padrão: baixe e veja as imagens e baixe e transcreva os áudios que o lead envia, antes de responder.
5. Nada publica, envia ou combina preço sem a aprovação da usuária ao texto exato — e à imagem exata, quando houver. Conversas sempre em PT-BR; com clientes, "produtor" (José), nunca "gestor". Sem segredo no git, nos logs ou no Hindsight; sem dado de comprador no repo, no painel ou no Hindsight.
```
