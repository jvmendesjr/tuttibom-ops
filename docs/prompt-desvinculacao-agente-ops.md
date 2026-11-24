# Prompt de desvinculação — agente TuttiBom OPS

**Vale usar:** o prompt deixa a fila e os envios em ordem. Ele **não revoga**
o acesso. A pessoa operadora revoga a atribuição, encerra as rotinas antigas
e confirma que o agente não consegue mais escrever. Se não houver resposta
do agente, prossiga com a revogação e reconcilie a fila pelo servidor.

Copie somente o bloco abaixo:

```text
Encerre seu papel no TuttiBom OPS e devolva a operação.

Ambiente: <laboratório ou produção>
Agente/cliente a desvincular: <identidade cadastrada>
Funções a encerrar: <IDs ou todas>

1. Pare de aceitar trabalho e não inicie novos envios, publicações, rascunhos,
   alterações de preço nem confirmações da fila. Não envie despedidas aos
   clientes; não troque de canal nem tente reconectar.
2. Não apague, reordene, reatribua ou confirme itens apenas para esvaziar a fila.
   Não reenvie nada. Separe “pendente”, “envio aceito e processamento
   confirmado” e “envio incerto ou aceito sem confirmação de processamento”.
   Se estiver sem acesso, declare isso em vez de presumir o estado.
3. No canal interno aprovado, informe contagens, bloqueios e o que precisa
   de reconciliação. Não inclua nomes, telefones, conteúdo de mensagens,
   imagens, tokens ou credenciais. As referências de trabalho ficam no
   sistema e só são consultadas por quem tiver atribuição.
4. Encerre sua conexão com o tuttibom-ops-mcp e as rotinas sob seu controle
   voltadas a esse papel. Não use acessos anteriores ou alternativos. Diga
   “Operação interrompida; <pendências ou incertezas>”. Não diga “acesso
   revogado” sem confirmação administrativa.
```

No laboratório, `tuttibom-ops-admin --laboratorio <diretório> revogar --agente
<id>` revoga **o agente inteiro**. Para manter algumas funções, revogue primeiro
a atribuição anterior e emita uma nova seleção menor. Não entregue ao sucessor
token, rascunho aprovado ou referência de autorização do titular antigo.
