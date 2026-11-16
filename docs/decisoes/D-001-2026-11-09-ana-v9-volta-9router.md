# D-001 — 2026-11-09 — Ana volta ao 9Router (core-medio) na v9, funcionando

**Data:** 2026-11-09 (publicada 2026-11-08 21:48 -03 pelo usuário; verificada 2026-11-09 ~21:50 -03)
**Decisor:** usuário (publicação por clique dele no Deskcomm)
**Status:** aplicada e verificada funcionando

## Decisão

A Ana volta a usar o **9Router** como provedor de modelos. A versão publicada
atual é a **v9** (id `75d8ba2d-9b49-4847-92fd-cde5c598c14a`, version_number 9),
provedor `custom`, modelo `core-medio`, credencial `9Router` (label 9Router,
base `https://9router.petemcasa.com/v1`, validada 2026-11-06, ativa).
Publicada pelo usuário em 2026-11-09 00:48:27 UTC (2026-11-08 21:48:27 -03).

## Contexto

- A v8 (`6118c86d`, publicada 2026-11-07 18:17 UTC) usava OpenRouter direto
  com `z-ai/glm-5.3-flash` (credencial `openrouter`), como tentativa de
  reduzir a latência dos turnos — a cauda do combo `core-medio` chegava a
  ~30 s no primeiro texto.
- A v7 (`f947c16d`) usava `9-noGemini` (9Router).
- O usuário decidiu voltar ao 9Router e publicou a v9 com `core-medio`.
  A v8 ficou superseded.
- Isso restaura a regra de 2026-11-06 ("Modelos e agentes usam o 9Router —
  nunca a chave da instalação nem o OpenRouter padrão") e o padrão da org
  (custom/core-medio).

## Verificação (Muse, só leitura, 2026-11-09 ~21:50 -03)

- Versão publicada: v9, provider `custom`, model `core-medio`, credential
  `f0e0f64f-504e-40cd-864d-90f8bf36a8b9` (9Router). Confirmado no banco
  (`ai_agent_versions` + `ai_provider_credentials`).
- Credencial 9Router: label "9Router", base_url
  `https://9router.petemcasa.com/v1`, `is_active` true, `validated_at`
  2026-11-06, `models_available` inclui `core-medio`.
- **Funcionando:** após a publicação da v9, 3 chamadas `agent_turn` com
  `core-medio`, todas status `ok` (2026-11-09 14:51:07 UTC; 2026-11-10
  00:45:01 UTC; 2026-11-10 00:46:54 UTC). Respostas reais enviadas no
  WhatsApp: conversa do Junior (00:44 e 00:46 UTC de 10/11) e uma conversa
  nova de cliente (pergunta sobre MDF, respondida 14:50 UTC de 09/11).
- Nota: o usuário disse "v8" ao pedir a atualização, mas a versão
  publicada é a **v9** (version_number 9). A v8 era a do OpenRouter/glm,
  agora superseded.

## Ressalvas (inalteradas)

- O teto de custo do Deskcomm segue sem enxergar o gasto do `core-medio`
  (`core-medio` fora de `ai_models` e `ai_pricing`; custo NULL). O controle
  real continua do lado do 9Router.
- A lentidão dos turnos de produto (inflação de contexto, 89–118 mil tokens
  de entrada por turno) segue como investigação separada (brief em
  `/tmp/brief-investigacao-contexto.md` no PC).

## Referências

- `docs/ESTADO.md` — seção "Ana v9 — volta ao 9Router (core-medio),
  funcionando (2026-11-09)".
- `docs/blueprint-inicial.md` §16.
- `docs/roadmap.md` — item "Ligar o 9Router no Deskcomm" fechado ([x]).
