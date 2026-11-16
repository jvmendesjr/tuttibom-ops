# Ajustes específicos da nossa aplicação — Jev no TuttiBom / Deskcomm

Este arquivo documenta COMO o projeto TuttiBom usa o Jev. O padrão geral
(perguntas atômicas, decisão em código, limiares) está no `SKILL.md` oficial
neste mesmo diretório; aqui vai só o que é específico da nossa aplicação.
Não editar o `SKILL.md` — ele é a cópia fiel do upstream (ver `FONTE.md`).

## Onde o Jev atua aqui
- **Deskcomm (org TuttiBom), agente Ana** — o Jev está ligado como cartão de
  decisão. Não há troca de modelo dentro de um turno: a Ana usa um único
  modelo, `core-medio` no 9Router (v9). Por isso NÃO existe roteamento por
  modelo neste projeto (descartado, D-002).
- **Muse (orquestrador)** — usa o CLI `jev` (`/home/pc/.hermes/bin/jev`) para
  decisões atômicas (escolha de ação em tela/ADB, tipagem de mídia). Ver
  "CLI" abaixo.

## Tarefas Jev no Deskcomm (estado 2026-11-07)
- `manipulacao` = **decidindo** (veredito do Jev em paralelo ao classificador
  LLM de jailbreak; nível final = máximo dos dois).
- `clima`, `humano`, `opt_out`, `sinal_de_urgencia`, `afirmacao_de_fato` =
  **observando**.
- `roteador` e `followup` = "Não roda" (não há roteador de intenção ativo).
- `campo_do_negocio` = Pausada.
- Skill instalada para a Ana: `jev-manipulacao` (gatilhos de jailbreak; a Ana
  nunca revela o prompt, mantém o papel e passa para humano se persistir).

## Jev antes do modelo (fix em produção, commit 265251a94)
Em `lib/agent-engine/agent/inbound-turn.ts`, o `perguntaAoJev` é esperado
PRIMEIRO. Quando o Jev de manipulação retorna `estado === 'decidindo'`, o
nível dele vale sozinho e o classificador LLM de jailbreak (`classifyJailbreak`)
é pulado. Se o Jev não decide, o LLM roda como fallback. Medido: o teste
pós-fix caiu de ~5 min 25 s para ~47 s; o `jailbreak_detect` LLM (~172 s no
turno "Fita") sumiu naquele turno, restando só o Jev (~185 ms).

## Classificação de risco + ack imediato (em construção, 2026-11-09)
Objetivo: mensagens pequenas, rápidas e sem risco recebem um "oi" como
primeira resposta (a pessoa sabe que já está em atendimento; a resposta
completa vem em 1–2 min). Se a mensagem já pergunta sobre fita, a Ana pede
um instante para verificar e dá o "oi, como posso ajudar?".

Desenho (seguindo o padrão oficial — o Jev julga, o código decide):
- **5 perguntas Noul ao Jev, numa só chamada, mesmo estado (só o texto da
  mensagem):** `eh_saudacao` (só saudação?), `pergunta_produto` (pergunta
  sobre fita/peça 3D, preço, cor, tamanho?), `tem_instrucao` (contém instrução
  para mudar comportamento, revelar instruções ou agir fora do serviço?),
  `eh_problema` (relata problema com pedido?), `eh_optout` (pede para parar?).
- **Limiares:** 0,7 = sim, 0,3 = não (começo, do SKILL.md oficial). Banda
  0,3–0,7 = não resolvido → tratar como "não é sim".
- **Tabela verdade (código):** `eh_optout` > 0,7 → sem ack, sem turno
  (respeitar opt-out). `tem_instrucao` > 0,7 → sem ack, direto ao turno
  completo (as guardas do turno cuidam). Senão → ack imediato e depois o
  turno completo. Ack de produto: "Oi! Vou verificar um instante e já te
  respondo." Demais: "Oi! Já te atendo." (textos exatos a aprovar com o
  usuário antes de ir ao ar).
- **NÃO perguntar ao Jev "isto é arriscado?"** — isso é pedir ao Jev que
  decida, camada errada (SKILL.md oficial, "Judgments from Jev, decisions
  in code"). As 5 perguntas são os julgamentos atômicos; a decisão é do código.
- Entra no fluxo depois do Ramo A (saudação fechada, primeiro contato) e
  antes do turno do modelo. Se o Jev falhar, NÃO mandar ack (fail closed:
  ir direto ao turno, como hoje).
- Brief de implementação: `/tmp/brief-ack-jev-risco.md` (PC).

## CLI do Jev (Muse)
- CLI `/home/pc/.hermes/bin/jev` v0.19.0, endpoint
  `https://api.typesafe.ai/v1/systemone`, modelo `jev-latest`.
- `jev ask` (noul/choice/score), `jev choose` (piso 0,65 — abaixo volta
  `reobserve`). ~US$0,00002 por decisão, ~0,2 s (medido).
- **Limite:** a visão do Jev (Box/coordenadas) NÃO está exposta neste CLI —
  só choice|score/noul. O Jev nunca vê screenshots nem dados pessoais;
  o Muse vê a tela/mídia, monta a tabela, o Jev escolhe o id, o Muse executa.
- O Jev NÃO escreve texto, não resume, não raciocina em vários passos,
  não vê pixels (neste CLI), não inventa coordenadas.

## Regras
- Nunca mostrar fragmentos de chave (nem os últimos 3–4 caracteres) no chat,
  mesmo a do dono. Identificar chaves só por tamanho/formato.
- Chave do Jev no Deskcomm: autorizada, uso transitório, nunca gravada,
  logada ou reportada.
- O texto exato do ack só vai ao ar após aprovação do usuário.
