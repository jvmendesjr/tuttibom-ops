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
2. O trabalho vive na worktree /home/pc/Workspace/tuttibom-ops-crm, branch exp/crm-proprio. SSH ao PC sempre com `ssh -F ~/.ssh/config pc`; rsync com `-e "ssh -F /home/hatch/.ssh/config"` + `--no-owner --no-group`. A main (/home/pc/Workspace/tuttibom-ops) está congelada para a vertente.
3. Estado onde paramos:
   - Listener 0.6.1 em produção, verificado por /health e MD5. Imagem ou áudio sem legenda não cai no cumprimento genérico se a leitura do histórico falhar. O cumprimento também é suprimido se já houve resposta pública durante o timer. A pausa de 2h continua.
   - Prova viva da imagem pendente: primeiro preparar a transferência da Ana pelo MCP e, quando autorizada, fazer a prova com o novo agente e a imagem de teste da usuária.
   - MCPs separados na worktree de integração /home/pc/Workspace/tuttibom-ops-mcp-nucleo (exp/mcp-ops-nucleo), ainda fora da branch da vertente. Core só leitura. Ops local funciona com fila e Chatwoot simulados, autorização por função, mídia, aprovação exata, escrita exclusiva e revogação. Veja docs/operacao/mcp-ops-laboratorio.md. Ainda faltam identidade real, backends reais e validação em ambiente isolado; não houve transferência da Ana.
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
