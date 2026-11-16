# D-002 — 2026-11-09 — Roteador por modelo DESCARTADO; fica a decisão de roteamento da resposta

**Data:** 2026-11-09 ~22:07 -03
**Decisor:** usuário
**Status:** decidido

## Decisão

O **roteador por modelo** (escolher o modelo por dificuldade da tarefa, com o
Jev escolhendo entre Grok 4.7/4.6 e Composer 2.5) está **DESCARTADO**. A Ana
usa um único modelo — `core-medio` no 9Router — então não há o que rotear
entre modelos.

## Contexto

- O roteador v0 nasceu para melhorar o tempo de resposta da Ana, com o Jev
  escolhendo diretamente o modelo entre os prioritários do Cursor pela
  dificuldade da tarefa (brief em `/tmp/brief-roteador-v0.md`, prompt da nova
  sessão entregue ao usuário em 2026-11-07).
- Em 2026-11-08 o usuário voltou a Ana ao 9Router (v9, `core-medio`) e
  decidiu que a operação usa um único modelo. Com um só modelo, o roteador
  por dificuldade não tem função.
- O que **permanece necessário** é a decisão de **roteamento da resposta**:
  para cada mensagem que chega, decidir se ela recebe um reconhecimento
  imediato ("oi", ack) ou se vai direto para o turno completo do modelo.
  Isso NÃO é roteamento de modelo — é a classificação de risco da mensagem,
  que é o trabalho seguinte (ver abaixo).

## O que fica no lugar

- **Classificação de risco com Jev + ack imediato.** Para mensagens pequenas,
  rápidas e sem risco, a Ana dá um "oi" como primeira resposta, para a
  pessoa saber que já está em atendimento, e a resposta completa vem em
  1–2 minutos. Se a mensagem já pergunta diretamente sobre fita, ela pede
  um instante para verificar e dá o "oi, como posso ajudar?".
- A classificação segue o padrão oficial do Jev (`typesafe-ai/skills`):
  o Jev responde julgamentos atômicos (Noul) e o CÓDIGO decide na tabela
  verdade — não se pergunta ao Jev "isto é arriscado?" (isso é pedir ao Jev
  que decida, camada errada). Ver `docs/decisoes/D-003-...` (a criar) e o
  brief do ack imediato.
- O roteador v0 por modelo não será construído. O brief
  `/tmp/brief-roteador-v0.md` fica como registro do que foi descartado.

## Referências

- Repositório oficial das skills do Jev: `typesafe-ai/skills`
  (https://github.com/typesafe-ai/skills, MIT) — SKILL.md lida em
  2026-11-09: "Judgments from Jev, decisions in code", perguntas atômicas,
  limiares 0,7/0,3 para Noul, perguntas em paralelo no mesmo estado.
- ESTADO.md (seção 2026-11-09), AGENTS.md (seção de orquestração atualizada).
