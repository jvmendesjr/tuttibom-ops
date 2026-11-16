# Relatório — roteador v0

Medido em 2026-11-07, 13:22 (−03), uma amostra por tarefa, depois de um
aquecimento descartado em `core-medio` (TTFT 23,329 s). Base
`https://9router.petemcasa.com/v1`, catálogo ao vivo com 282 modelos.
Nenhuma chave foi lida para este texto.

## Candidatos

O Jev escolhe entre estes ids. O fallback, fora da tabela, é
`core-medio`.

| Id no 9Router | Quando a descrição pede |
|---|---|
| `cu/grok-4.7-low` | tarefa leve / primeira resposta cedo |
| `cu/grok-4.7-medium` | dificuldade média |
| `cu/grok-4.7-high` | tarefa difícil (prioritário) |
| `cu/cursor-grok-4.5-high` | alternativa de tier alto |

O esquema do `jev choose` não aceita `/` no id. A tabela enviada ao
Jev usa `:` (`cu:grok-4.7-low`); a chamada ao 9Router usa o id da
coluna acima. `reobserve` e `abstain` existem porque o esquema exige;
se o Jev os devolver, ou se a confiança ficar abaixo de 0,65, o
script cai em `core-medio`. Nesta rodada isso não aconteceu.

## O que não entrou

No catálogo de 282 modelos não há `cu/grok-4.6` e não há nenhum id
com "composer". O Grok 4.6 do Cursor pedido na conversa não está no
9Router. O que existe de Grok 4.6 é `factory/grok-4.6` e
`warp/grok-4-6-high`, `warp/grok-4-6-low`, `warp/grok-4-6-medium`,
`warp/grok-4-6-xhigh` — nenhum deles é o modelo do Cursor, e nenhum
entrou na tabela. O Composer 2.5 também não entrou.

## Tempos

`primeira` é o que se espera até o primeiro texto: tempo do Jev mais
o tempo até o primeiro texto do modelo. Na referência não há Jev.
Números em segundos. As seis chamadas devolveram texto.

| Nível | Escolha | Conf. | Jev | Até o 1º texto do modelo | Primeira (roteador) | Total roteador | `core-medio` até o 1º texto | Total referência |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| fácil | `cu/grok-4.7-low` | 1,00 | 0,479 | 4,394 | **4,873** | 4,874 | 28,457 (`gemini-3.8-flash-n`) | 28,458 |
| médio | `cu/grok-4.7-medium` | 0,99 | 0,514 | 20,710 | **21,224** | 22,329 | 1,362 (`claude-sonnet-4-6`) | 3,930 |
| difícil | `cu/grok-4.7-high` | 0,99 | 0,453 | 87,598 | **88,051** | 92,572 | 31,862 (`gemini-3.8-flash-n`) | 34,999 |

Comparação da primeira resposta (referência menos roteador; positivo
quer dizer que o roteador chegou antes):

| Nível | Diferença |
|---|---:|
| fácil | +23,584 s |
| médio | −19,862 s |
| difícil | −56,189 s |

O Jev acertou o tier nas três e gastou cerca de meio segundo. O que
muda o início é o modelo chamado, não o custo da escolha. Nesta
amostra o roteador antecipou a primeira resposta só na tarefa fácil.
No médio e no difícil, o Grok 4.7 segurou o primeiro byte (o tempo
até o primeiro byte coincidiu com o tempo até o primeiro texto) e o
`core-medio` chegou antes.

O `core-medio` é um combo: a referência fácil e a difícil resolveram
para `gemini-3.8-flash-n` (28 s e 32 s) e a média para
`claude-sonnet-4-6` (1,4 s). Uma amostra só não separa fila de
modelo.

Respostas conferidas: fácil devolveu `4` nos dois caminhos; médio e
difícil devolveram texto sobre o pedido. JSON completo em
`medicoes-v0.json`.

## Pendente

- O caminho de fallback (confiança abaixo de 0,65, Jev fora, ou
  `reobserve`/`abstain`) não rodou: as três escolhas ficaram em
  0,99–1,00.
- Amostra única. Repetir a mesma tarefa muda o número, sobretudo no
  `core-medio`, porque o combo troca o modelo por baixo.
- O protótipo não está ligado a canal nenhum.
