# Entrega — Frente contratos + fila

**Workspace:** `/home/pc/Workspace/tuttibom-ops-contratos`  
**Branch:** `frente/contratos-fila` (base informada: `main` `b8a034a`)  
**Data:** 2026-11-17 (America/Fortaleza)

Contratos Pydantic v2 da F4, validador, testes, fila normalizada
e conferência do catálogo contra os 18 produtos citados nos docs.
O Deskcomm não foi consultado. Preços do documento não foram
alterados. Nada foi commitado.

## Contratos

Pacote `src/tuttibom/contratos/`, versão `1.0.0`.

| Contrato | Travas |
|---|---|
| `Publicacao` | `texto_aprovado: true`, arte, formato `9:16` ou `4:5`, rede `facebook` ou `instagram`, data ISO, `rotulo_ia: true`, `foto_de_cliente: false`. Qualquer preço no texto ou na arte falha, inclusive o do catálogo. A legenda social não leva valor. |
| `Criativo` | Formato, overlays curtos (`legivel: true`, até 120 caracteres — a legenda longa é da Publicacao), zonas seguras, botões A e B com rótulos diferentes. No `9:16`, piso topo 220 px, base 380 px, direita 140 px (storyboard do piloto e mapa 1080×1920). |
| `Lead` | Estágios do CRM local em `ops/triagem-interessados.md`: Novo, Contatado, Qualificado, Proposta enviada, Produção / Retirada, Fechado, Perdido, Adormecido. Próxima ação e `data_followup` obrigatórias. Perdido exige motivo. Sem e-mail, telefone, CPF ou endereço. Sem campo de nome. Preço só se for um dos 18 da captura. |

O texto do piloto (2026-11-01) está em `TEXTO_PILOTO`, copiado de
`templates/storyboard-publicacao-1.md`. O contrato não trava a fila
nesse único texto: outro texto aprovado, sem preço, também passa.

Marketplace ficou de fora de `Publicacao`. Anúncio de marketplace
pode levar preço de catálogo; a peça pública desta F4 não.

## Como rodar

Um CLI com três subcomandos (em vez de três scripts iguais):

```bash
python3 scripts/validate_contratos.py publicacao peca.json
python3 scripts/validate_contratos.py criativo criativo.json
python3 scripts/validate_contratos.py lead ficha.json
```

Sem caminho, lê JSON pelo stdin. Exit 0 válido (modelo em stdout),
1 inválido (erro em stderr), 2 uso.

```bash
make check
```

`make check` continua compilando o MCP e passa a compilar os
contratos e a rodar `PYTHONPATH=src python3 -m pytest -q tests`.
Dependências: `pydantic>=2.14` e `pytest` (`requirements.txt`).

O pytest cobre, para cada trava, um caso que passa e um que falha.
O texto do piloto passa. `R$ 99,90` falha na `Publicacao` e no CLI.
`R$ 71,90` (preço que está no catálogo) também falha na peça
pública e passa no `Lead`, no campo `valor_catalogo` ou na
observação.

**Esta sessão não executou `make check`.** Toda chamada de shell
voltou recusada, inclusive `python3 --version`. A suíte está
escrita; o verde precisa ser confirmado pelo coordenador.

## Catálogo — 18 produtos

Fonte dos valores: `catalogo/produto-fita-cetim.md` (captura Shopee
2026-10-30). Fonte dos códigos: docs do projeto (`catalogo/cores-fita-cetim.md`,
`docs/pacote-tuttibom.md`, `docs/relatorio-tuttibom-ops-estado.md`),
não o banco. `catalogo/produto-fita-cetim.md` não foi editado.

Os 18 preços estão no documento, em 4 anúncios. Nenhum combinação
largura × metragem × cor de impressão ficou sem valor.

| Código | Preço | No documento |
|---|---|---|
| FITA-22-50-PRETO | 71,90 | 22 mm, 50 m, Preto |
| FITA-22-50-DOURADO | 88,90 | Dourado Metalizado |
| FITA-22-50-PRATA | 88,90 | Prata Metalizado |
| FITA-22-25-PRETO | 38,90 | 22 mm, 25 m, Preto |
| FITA-22-25-DOURADO | 47,90 | Dourado Metalizado |
| FITA-22-25-PRATA | 47,90 | Prata Metalizado |
| FITA-22-10-PRETO | 18,90 | 22 mm, 10 m, Preto |
| FITA-22-10-DOURADO | 21,90 | "Dourado/Gold Metalizado" |
| FITA-22-10-PRATA | 21,90 | Prata Metalizado |
| FITA-15-10-PRETO | 15,00 | 15 mm, 10 m, Preto |
| FITA-15-10-DOURADO | 19,00 | Dourado Metalizado |
| FITA-15-10-PRATA | 19,00 | Prata Metalizado |
| FITA-15-25-PRETO | 29,00 | 15 mm, 25 m, Preto |
| FITA-15-25-DOURADO | 43,00 | "Dourada Metálica" |
| FITA-15-25-PRATA | 43,00 | "Prateada Metálica" |
| FITA-15-50-PRETO | 59,00 | 15 mm, 50 m, Preto |
| FITA-15-50-DOURADO | 79,00 | "Dourada Metálica" |
| FITA-15-50-PRATA | 79,00 | "Prateada Metálica" |

São 12 valores distintos: dourado e prata do mesmo tamanho
compartilham o preço. A mesma tabela está em
`src/tuttibom/contratos/precos.py` e é conferida por
`tests/test_precos_catalogo.py`.

### Divergências

1. **Códigos ausentes no documento do produto.** Os 18 códigos
   `FITA-<mm>-<m>-<COR>` não aparecem em `produto-fita-cetim.md`.
   O arquivo reconstruído da Shopee agrupa 4 anúncios. Os códigos
   são do cadastro Deskcomm de 2026-11-06, citados nos docs.
   Não foram escritos no documento do produto: isso misturaria o
   esquema posterior com a captura. Preço não mudou.
2. **Nome da cor de impressão não é único.** "Dourado Metalizado",
   "Dourado/Gold Metalizado" e "Dourada Metálica" são o mesmo eixo
   DOURADO; "Prata Metalizado" e "Prateada Metálica" são PRATA.
3. **22 mm / 10 m incompleto no próprio documento.** A página
   detalhada não veio. Descrição e prazo são herdados dos outros
   anúncios. Os três preços estão presentes.
4. **Estoque é por anúncio, não por SKU** (249, 149, 119 e 98).
   Os docs dizem que o Deskcomm não controla estoque por variação.
5. **Peso inconsistente** (não é furo dos 18): 0,22 kg no 22 mm;
   0,15 kg no 15 mm, com uma variação de 50 m a 0,187 kg.
6. **Outro eixo, não outra lista de 18.** As 69 cores de fita
   (`catalogo/cores-fita-cetim.md`, 18 marcadas disponíveis) são
   cor do cetim. Os 18 produtos são medida × cor da impressão.
   O documento do produto já separa as duas coisas.

As faixas do documento ("R$ 38,90 a R$ 88,90" e as outras) batem
com o menor e o maior preço de cada anúncio.

## Fila

`ops/fila-publicacao.md` ganhou uma tabela operacional:

- Dia 1 Feed e Dia 1 Stories: `publicado` em 2026-11-01, com o
  aprovador já escrito no histórico ("Aprovado, pode publicar o
  Feed" e o mesmo texto do piloto no Stories). Sem URL inventada.
- Dia 3 e Dia 5: `proposto`, coluna "Aprovado por" vazia.
- Nenhuma linha nova. Estado `rascunho` fica reservado a linha
  nova, sem aprovador.
- O relato longo de 2026-11-01 foi mantido na seção Histórico,
  inclusive o fecho antigo que dizia que nada estava publicado.
  Uma nota explica que esse fecho é anterior às atualizações do
  Dia 1 coladas na mesma célula.

`criativos/` não foi tocado. Posts F1-02 não entraram na fila.

## O que ficou pendente

- Rodar `make check` (shell desta sessão bloqueado).
- Piso em px do formato `4:5`. O storyboard só fixa os números
  do `9:16`. O contrato exige margem declarada (maior que zero)
  e texto fora da zona morta, sem inventar o piso.
- Os 56 px da esquerda, do mapa de motion, não são trava.
- Marketplace fora do enum `Rede`.
- Nomes do funil Vendas no Deskcomm (Novo contato, Já respondi,
  Pedido pago, Não comprou, …) não são aceitos como estágio.
  `Adormecido` existe no CRM local e, segundo o pacote, não
  existe no Deskcomm. O mapa entre os dois vocabulários não foi
  decidido aqui.
- A régua de follow-up (1 dia, 2–3 dias, 7 dias → Adormecido)
  não é calculada pelo contrato. A data é obrigatória; o prazo
  continua regra operacional.
- Nome de pessoa em texto livre não é detectado (falso positivo
  em cidade e em marca fictícia). A referência tem de ser código
  (`lead-001`), e não há campo de nome, telefone ou e-mail.
- Dia 3 no histórico ainda fala em "vídeo bruto real". A diretriz
  de mídia 100% fictícia é posterior. A linha não foi reescrita:
  isso seria mudança de proposta, não normalização.
- Critérios de promoção da seção 4 do roadmap (empresa, CEO,
  merge) não são desta frente. O critério de saída da F4 é o
  piloto passar e o preço inventado falhar.
- `docs/ESTADO.md`, `docs/roadmap.md` e `docs/decisoes/` não foram
  atualizados, por limite desta frente. Retain no Hindsight também
  não: a ordem foi não tocar em nada ao vivo. Fica para o
  coordenador, no commit.
