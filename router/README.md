# Roteador v0

Protótipo no PC. Recebe um texto, pede ao Jev para escolher um modelo
pela dificuldade (entre os prioritários do Cursor que existem no
9Router) e chama esse modelo. Mede o tempo até a primeira resposta.

Não publica, não liga a canal e não grava chave.

## Como rodar

A chave do 9Router precisa estar no ambiente, com o nome
`NINEROUTER_API_KEY`. A chave do Jev fica no keystore do CLI; este
script não lê nenhuma das duas.

```bash
python3 /home/pc/Workspace/tuttibom-ops/router/route.py \
  "Quanto é 2+2? Responda só o número."
```

JSON:

```bash
python3 /home/pc/Workspace/tuttibom-ops/router/route.py --json \
  "Quanto é 2+2? Responda só o número."
```

Referência sem roteador (`core-medio` direto):

```bash
python3 /home/pc/Workspace/tuttibom-ops/router/route.py --baseline \
  "Quanto é 2+2? Responda só o número."
```

Os três exemplos (fácil, médio, difícil) mais a referência:

```bash
python3 /home/pc/Workspace/tuttibom-ops/router/route.py --bench \
  > /home/pc/Workspace/tuttibom-ops/router/medicoes-v0.json
```

## O que entra na conta

- **jev_s** — tempo do `jev choose`.
- **ttft_s** — do início da chamada ao 9Router até o primeiro texto.
- **primeira_resposta_s** — `jev_s + ttft_s` (o que se espera até
  começar a ver a resposta). Na referência, é só o `ttft_s`.
- **total_s** — parede até a resposta fechar.

Piso de confiança: 0,65. Abaixo disso, ou se o Jev falhar, o modelo
é `core-medio`.

O id enviado ao Jev troca `/` por `:` (`cu:grok-4.7-low`), porque o
esquema do `jev choose` não aceita barra. A chamada ao 9Router usa o
id original (`cu/grok-4.7-low`).

Base: `https://9router.petemcasa.com/v1`.
