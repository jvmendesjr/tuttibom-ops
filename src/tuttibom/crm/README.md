# CRM próprio mínimo — nota de desenho (D-012, V2)

## O que é

O núcleo do teste da nova vertente: um banco SQLite local com lead,
funil, mensagem (resumo), follow-up e memória por contato. Sem
Deskcomm, sem rede, sem dependência nova (só stdlib + os contratos
que já existem em `src/tuttibom/contratos/`).

- Esquema: `db/crm.sql`
- Código: `src/tuttibom/crm/store.py` (+ `funil.py`)
- Testes: `tests/test_crm_minimo.py` (stdlib `unittest` — não há
  pytest no Python do PC, e a V2 não vai criar dependência só para
  testar)
- Demonstração dos critérios de saída: `scripts/crm_demo.py`

## Como rodar

```bash
python3 -m unittest discover -s tests -v -k crm_minimo
python3 scripts/crm_demo.py   # critérios de saída da V2, banco temporário
```

O arquivo do banco (`.sqlite3`) NÃO vai para o git: é dado
operacional, e o `.gitignore` já cobre `work/` — bancos de teste
vivem em diretório temporário ou em `work/`, nunca commitados.

## Duas divergências honestas (não escondidas)

### 1. Por que `db/crm.sql` e não `db/schema.sql`

O `db/schema.sql` é o rascunho Supabase v1, e ele diz explicitamente
que "Leads ficam FORA desta v1, por decisão de privacidade". Reescrevê-lo
apagaria essa decisão. O esquema do CRM próprio vive então em
`db/crm.sql`, separado. O roadmap dizia `db/schema.sql` por engano —
corrigir a linha lá na promoção, não nesta branch.

### 2. Funil: Vendas (7 etapas) x contrato F4 (8 estágios)

O contrato F4 (`contratos/lead.py`) usa outro vocabulário — Novo,
Contatado, Qualificado, Proposta enviada, Produção / Retirada,
Fechado, Perdido, Adormecido — e diz que os nomes do funil Vendas
"não entram aqui". A V2 usa o funil Vendas do Deskcomm (7 etapas),
porque é ele que o setor 2 (aprovado pelo usuário) especifica, é ele
que está vivo em produção desde 2026-11-06, e é ele que a skill da
Ana e os follow-ups assumem. O que a V2 reaproveita do F4: a tabela
de preços (`contratos.precos.PRECOS_SKU`, 18 SKUs) e o guarda de PII
(`contratos.pii.afirmar_sem_pii`). Alinhar o contrato F4 com o funil
Vendas é uma decisão separada, para depois da V3 — não um ajuste
silencioso agora.

## Privacidade, por desenho

- Nenhuma coluna de nome, telefone, e-mail ou endereço. O endereço
  do cliente não é guardado: só o flag `endereco_coletado`.
- `contato_ref` é opaco (`contato-teste-01`), nunca telefone ou @.
- `mensagens.resumo` é um resumo escrito pelo atendimento, não o
  texto cru do cliente. Texto com PII é rejeitado; a conversa crua
  vive no canal (WAHA/Zernio), não neste repo.
- Preço só por SKU. SKU fora do catálogo falha — não existe preço
  inventado neste banco.
- "Não comprou" exige motivo de perda (código fechado). "Pedido pago"
  é terminal. Lead perdido pode reabrir (o Junior voltou, 2026-11-18).
- Mensagem inbound cancela os follow-ups de silêncio pendentes
  (cancelar-ao-responder, como o Fluxo A do Deskcomm).
