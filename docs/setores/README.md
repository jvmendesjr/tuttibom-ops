# Setores da operação — TuttiBom OPS (nova vertente)

**Decisão-mãe:** D-012 (2026-11-21) — CRM próprio e atendimento pelo
Muse, em teste paralelo, produção Deskcomm/Ana v12-B intocada.
**Worktree dos documentos:** `tuttibom-ops-setores`, branch
`exp/setores-nova-vertente`.

## Por que dividir em setores

A operação misturava atendimento, CRM, produto, criativo, social,
anúncio, produção e plataforma no mesmo lugar — e era essa mistura que
confundia Deskcomm com TuttiBom Ops. Cada setor aqui tem um dono
(documento + skill/diretório), uma fronteira escrita e um handoff
definido. Um setor só age dentro da sua fronteira; o resto ele passa
ao setor dono, nunca improvisa por cima dele.

Os arquivos abaixo inventariam os setores. O
[índice de skills](../operacao/skills-por-area.md) contém os procedimentos
e o escopo em que o MCP os entrega. O setor 08 é técnico, fora do Ops.

## Os 8 setores

| # | Setor | Documento | Pergunta que ele responde |
|---|---|---|---|
| 1 | Atendimento — Ana | `01-atendimento.md` | O que eu digo ao cliente, e como? |
| 2 | CRM e Vendas | `02-crm-vendas.md` | Onde o lead está, e qual o próximo passo? |
| 3 | Produto e Catálogo | `03-produto-catalogo.md` | O que vendemos, por quanto, e o que temos? |
| 4 | Criativos e Mídia | `04-criativos-midia.md` | Como fica a imagem / o vídeo? |
| 5 | Social e Conteúdo | `05-social-conteudo.md` | O que a página publica, e quando? |
| 6 | Anúncios, Aquisição e Concorrência | `06-anuncios-concorrencia.md` | Como chega gente nova, e onde estamos no preço? |
| 7 | Operação, Produção e Pagamento | `07-operacao-producao.md` | Como o pedido sai, chega e é pago? |
| 8 | Plataforma e Manutenção | `08-plataforma-manutencao.md` | O sistema está de pé, seguro e sem vazar nada? |

## Molde de cada documento

Todo documento de setor segue o mesmo molde, nesta ordem:

1. **Objetivo** — uma frase, o que o setor entrega.
2. **Entra / Sai** — o que chega a ele e o que ele devolve, e para quem.
3. **Faz / Não faz** — a fronteira. O "não faz" é tão importante quanto
   o "faz": é ele que impede um setor de prometer o que é de outro.
4. **Skill e diretório** — onde vive o comportamento executável dele.
5. **Aprovações** — o que precisa do usuário antes de acontecer.
6. **Como se mede que deu certo** — o teste do setor, sem cliente real
   até a promoção.
7. **Handoffs** — para qual setor passa cada caso fora do seu escopo.

## Regras que valem para todos os setores

- Nada publica, envia ou combina preço sem aprovação do usuário ao
  texto exato — e à imagem exata, quando houver.
- Conversas sempre em português brasileiro. Com clientes, "produtor"
  (José), nunca "gestor".
- Sem segredo no git, nos logs ou no Hindsight. Sem dado de comprador
  no repo, no painel ou no Hindsight.
- Camofox é o navegador único (D-004). S10/ADB pausado.
- Fluxo baixo é uma vantagem do teste: cada setor é provado com poucas
  conversas, uma por vez, antes de qualquer escala.
- Dúvida de fronteira: parar e perguntar ao usuário, não adivinhar.
  A correção de fronteira vira uma linha nova no documento do setor,
  não uma exceção guardada na memória.

## Ordem de construção

1. Documentos (esta worktree) — primeiro a fronteira, depois o código.
2. Skill da Ana (setor 1) + CRM mínimo (setor 2) — o núcleo do teste.
3. Marketing e criativos (setores 4 e 5) — com as skills que já existem.
4. Demais setores — um por vez, só quando o núcleo estiver provado.
