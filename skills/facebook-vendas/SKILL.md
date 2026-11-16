# Skill: facebook-vendas

Vender no Facebook via S10 + ADB: catálogo, anúncio, triagem e
encaminhamento de interessados. Execução de tela só via
`skills/s10-navegacao/`.

## Catálogo primeiro

Nenhum anúncio nasce de memória solta. Todo produto vive em
`catalogo/` com: nome, tipo (impressão 3D ou fita de cetim), material,
medidas, variações (cor/tamanho/metragem), condição, preço, preço
mínimo, estoque/tempo de produção, fotos e observações. Dado que não
está no catálogo não entra no anúncio — o agente pergunta, não inventa.

## Criar anúncio (rotina R-04)

1. Partir do catálogo e do template em `templates/anuncio-marketplace.md`.
2. Preço a partir da realidade local e do preço mínimo; nunca abaixo
   do mínimo sem aprovação.
3. Conferir cada campo na tela antes de avançar.
4. Salvar como rascunho e confirmar o estado "rascunho".
5. Publicar só com aprovação explícita do usuário, depois de revisar o
   rascunho na tela.

## Triar e encaminhar (rotina R-05)

1. Listar conversas novas sem responder fora da fila.
2. Classificar em `ops/triagem-interessados.md`: interessado, dúvida,
   golpe suspeito, spam.
3. Sinais de golpe: pressa artificial, pedido para sair da plataforma,
   pagamento por outro canal, código de verificação, link estranho,
   valor acima do pedido. Nesses casos, parar e encaminhar ao usuário.
4. Encaminhar interessados com resumo: produto, pergunta, valor
   mencionado, urgência e próximo passo sugerido — sem comprometer
   preço, reserva ou encontro.
5. Resposta só sai com texto aprovado ou a partir de
   `templates/resposta-interessado.md`, e sempre registrada.

## Saúde da conta

Anúncio removido, aviso, restrição ou conversa suspeita vai para
`ops/saude-da-conta.md` com data, motivo aparente e evidência (texto
da tela, sem dados pessoais). Repetir publicação após aviso, duplicar
anúncio ou editar às pressas é proibido sem revisão humana.

## Nunca

- Publicar sem aprovação; enviar mensagem comprometendo preço, reserva,
  encontro ou pagamento sem aprovação.
- Levar pagamento para fora da plataforma por conveniência.
- Compartilhar código de verificação, senha ou dado pessoal.
- Inventar característica, medida, defeito ou história do produto.
