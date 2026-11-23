# Comando de retomada — nova vertente TuttiBom OPS

**O que é:** o comando para entregar a um agente (o Muse numa nova
sessão, ou outro agente) para recomeçar de onde paramos. Copiar e
colar o bloco abaixo.

## O comando (copiar e colar)

```text
Você está retomando o trabalho da nova vertente do TuttiBom OPS (CRM próprio + atendimento pelo Muse como Ana), de onde paramos na sessão anterior.

1. Leia primeiro, nesta ordem:
   - docs/rascunho-mcp-operacao.md (desenho do mcp ops, atualizado — é a fonte da verdade do MCP)
   - docs/comando-inicial-agente-ops.md (comando inicial padrão do agente da operação)
   - ~/MEMORY.md (memória do projeto — decisões, regras, estado)
   - docs/roadmap-nova-vertente.md e docs/setores/README.md (o contexto da vertente)
2. O trabalho vive na worktree /home/pc/Workspace/tuttibom-ops-crm, branch exp/crm-proprio (último commit 0740352). SSH ao PC sempre com `ssh -F ~/.ssh/config pc`; rsync com `-e "ssh -F /home/hatch/.ssh/config"` + `--no-owner --no-group`. A main (/home/pc/Workspace/tuttibom-ops) está congelada para a vertente.
3. Estado onde paramos:
   - Cumprimento corrigido e deployado (listener 0.6.0, commit 9034ad9): pool genérico com as 3 frases da usuária; áudio/imagem sem legenda cai no genérico, nunca no "vou verificar". Teste vivo pendente (conversa da Gleiciane, Messenger — a do Junior tem a pausa de 2h).
   - Prova viva da imagem pendente (aguardando a usuária enviar uma imagem de teste).
   - MCP ops: só desenho, construção não começou. Nomes canônicos: tuttibom-core-mcp (hoje ainda tuttibom-mcp v0.1.1, a renomear na próxima atualização) e tuttibom-ops-mcp (nasce em src/tuttibom/mcp_ops/ na worktree exp/crm-proprio, antes do merge). Decisões registradas: isolado do core; atribuições enumeradas por número com OK da usuária antes de qualquer acesso; comando inicial padrão; lease sem prazo fixo; acesso via Tailscale; hospedagem no PC; tudo da operação pelo MCP; entrega por área a outro agente para testar e monitorar; mídia é padrão para todo agente; atendimento autônomo via Chatwoot sem interferência do Muse. Em aberto: quem emite/revoga tokens (proposta: só a usuária).
   - Atendimento no Chatwoot segue operando pelo Muse como Ana (hook de 60 s; vigília desligada); Ana do Deskcomm pausada; main congelada.
4. Regras que não se negociam:
   - O Muse implementa tudo ele mesmo; nada vai para o Cursor/Agy sem pedido explícito da usuária.
   - Nada é publicado, enviado ou combinado em preço sem aprovação da usuária ao texto exato — e à imagem exata, quando houver.
   - Sem dado de comprador no repo, no painel ou no Hindsight; sem segredos no git/logs/chat.
   - Camofox é o navegador único (D-004); S10/ADB pausado.
   - Nunca reiniciar/desligar cloudflared-ponte sem aprovação da usuária.
   - MEMORY.md é root-owned: editar só com a ferramenta de edição, nunca por script.
   - Verificar de forma independente antes de reportar (testes + /health + md5 do deploy).
   - Nunca criar evento falso em conversa real nem enviar mensagem de teste para cliente real.
5. Comece confirmando o que entendeu do estado e pergunte por onde continuar.
```
