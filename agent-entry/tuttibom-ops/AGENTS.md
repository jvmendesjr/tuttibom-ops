# TuttiBom Ops

Este é o ponto de entrada para a operação. Use o servidor `tuttibom-ops-mcp`
já configurado para sua sessão. Você não precisa saber qual perfil ou
quais funções o operador selecionou.

1. Chame `ops_minhas_atribuicoes` para descobrir suas funções, papéis e skills.
2. Leia todas as skills do manifesto com `ops_ler_skill`. Confirme o
   manifesto com `ops_confirmar_atribuicoes`, usando o hash e um resumo do
   escopo. Repita em cada nova conexão.
3. Execute a tarefa pedida somente com as ferramentas do seu escopo e de
   acordo com as skills. Se nenhuma tarefa foi pedida, informe o escopo e
   aguarde. A atribuição não aprova envios ou outros compromissos.

Se o MCP não estiver disponível ou o escopo não permitir a tarefa, informe o
bloqueio. Não use o acesso a arquivos, outros perfis ou canais para contornar
o MCP. Não peça nem informe credenciais no chat.
