# Skill: tuttibom-facebook-marketplace

- **Marca:** TuttiBom
- **Conta:** conta pessoal da loja no Facebook, logada no Galaxy S10 Lite
- **Rede:** Facebook — Marketplace
- **Função:** criar anúncio em rascunho, triar interessados, encaminhar
  ao usuário. Não publica, não responde com preço, não fecha venda.
- **Executor hoje:** ADB no S10, via `skills/s10-navegacao/`. Conector
  nativo do Muse NÃO é executor desta conta (não está ligado a conta
  nenhuma neste ambiente; outra conta seria autor errado).
- **Produtos:** impressão 3D e fita de cetim personalizada, só com os
  dados de `catalogo/`. Preço para o Facebook ainda pendente — nunca
  inventar, nunca usar preço da Shopee como preço do Facebook sem
  aprovação do usuário.
- **Região:** Cariri — Juazeiro do Norte / Crato / Barbalha. Filtro de
  Marketplace: Juazeiro do Norte.

## Problemas específicos desta marca, conta e plataforma

1. **Dump de UI do Facebook falha (root nulo).** Observação só por
   screencap e checagem de app em foco. Nunca agir sobre tela em cache.
2. **`input text` com espaço quebra.** Espaço vai por `keyevent 62`;
   `%20` digita os caracteres literais.
3. **Banner de confirmação de email.** Dispensar com o X, sem confirmar
   e sem adicionar email, salvo instrução explícita do usuário.
4. **Oferta local desigual (pesquisa 2026-10-30, só leitura).** "Fita de
   cetim" sem oferta local na primeira tela (resultados a 400–490 km);
   "impressao 3d" com oferta forte local, chaveiros personalizados a
   R$6–R$8, tema Nossa Senhora Aparecida em destaque. Isso é contexto
   de mercado, não preço a copiar.
5. **Tela do S10 dorme e volta preta.** Seguir a regra de vigília:
   verificar, acordar com `keyevent 224`, confirmar Awake, recapturar
   se preto, antes de qualquer toque.

## Rotinas

### R-04 — Anúncio em rascunho (não publica)

1. Partir de `catalogo/` + `templates/anuncio-marketplace.md`.
2. Conferir cada campo na tela antes de avançar.
3. Salvar como rascunho e confirmar o estado "rascunho" por screencap.
4. Registrar em `ops/fila-publicacao.md` e em `experimentos/`.
5. Publicar só com aprovação explícita, após revisão do rascunho na tela.

### R-05 — Triagem e encaminhamento (não responde o que compromete)

1. Listar conversas novas, sem responder fora da fila.
2. Classificar em `ops/triagem-interessados.md`: interessado, dúvida,
   golpe suspeito, spam. Sinais de golpe: pressa artificial, pedido
   para sair da plataforma, pagamento por outro canal, código de
   verificação, link estranho, valor acima do pedido — parar e
   encaminhar ao usuário.
3. Encaminhar resumo: produto, pergunta, valor mencionado, urgência,
   próximo passo sugerido — sem comprometer preço, reserva ou encontro.
4. Resposta só com texto aprovado ou a partir de
   `templates/resposta-interessado.md`, sempre registrada.
5. Jev pode classificar tipo/urgência/risco, com limiar e rota humana;
   Jev não gera a resposta e não aprova nada.

## Saúde da conta

Anúncio removido, aviso, restrição ou conversa suspeita vai para
`ops/saude-da-conta.md` com data, motivo aparente e evidência descrita
(sem dado pessoal). Repetir publicação após aviso, duplicar anúncio ou
editar às pressas é proibido sem revisão humana.

## Nunca (além dos guardrails)

- Publicar sem aprovação; enviar preço, reserva, encontro ou pagamento
  sem aprovação; levar pagamento para fora da plataforma.
- Inventar medida, material, estoque, prazo, cor ou preço.
- Compartilhar código, senha, token ou dado pessoal de comprador.
- Copiar texto, foto, logo ou cliente de concorrente.
