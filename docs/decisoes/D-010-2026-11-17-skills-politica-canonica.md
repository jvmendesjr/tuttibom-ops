# D-010 — Skills como prática canônica do TuttiBom Ops

Data: 2026-11-17. Proposta pelo usuário; aceita na hora.

## Contexto

A construção do site no Framer (2026-11-17) terminou com as seções da Home
sobrepostas — o usuário viu no editor e mandou o print. O aprendizado daquele
incidente vivia espalhado: um aviso de linter ("siblings too close") na
entrega, lições no AGENTS.md, detalhes na memória. O agente que construiu não
tinha uma skill do fluxo para consultar antes de agir.

## Decisão

1. **Todo fluxo ou processo do TuttiBom Ops tem sua skill** em `skills/`:
   criada quando o fluxo nasce, atualizada quando um incidente ensina algo.
2. **O brief de qualquer tarefa delegada nomeia a(s) skill(s) do fluxo**, e o
   agente lê o `SKILL.md` antes de agir. A skill usada vai registrada na
   entrega.
3. **Roteamento:** não existe padrão de roteamento de skills por Jev na skill
   `typesafe-ai` vendada (verificado 2026-11-17 — o grep não achou nada sobre
   rotear para skills). Então o roteamento é determinístico pelo brief; quando
   mais de uma skill couber, o Jev `choose` decide entre as candidatas
   nomeadas (julgamento atômico, o código decide).
4. **Todo incidente gera a atualização ou criação da skill como parte do
   conserto**, antes de voltar à trilha principal. É a "ressalva e ajuste
   pontual" — depois, volta-se ao trabalho.
5. As skills seguem o padrão do projeto: cópia em `skills/` com `FONTE.md`
   quando houver origem externa; o original nunca é editado.

## Primeiras skills da política

- `skills/tuttibom-navegacao-camofox/` — a partir da skill aprendida
  `jev_camofox_navigation` (custom skills da VM) + a operação do profile-fb
  (duas travas, status vivo, backups, isolamento verificado).
- `skills/tuttibom-framer-site/` — lições da construção do site 2026-11-17,
  incluindo a sobreposição da Home.

## Aplicação à entrega de cargos via MCP

- Cada área mantém uma skill ou um conjunto enxuto em `skills/`. A skill
  é a fonte canônica da persona, dos prompts de trabalho, dos processos,
  das decisões, dos limites e do encaminhamento. Documentos de setor
  inventariam tarefas; não substituem as instruções na skill.
- O prompt de entrada só identifica a seleção já autorizada e a referência,
  sem endereço ou credencial. O manifesto mapeia IDs de função para o
  conhecimento necessário. O Ops entrega apenas as versões dessas skills,
  sem acesso a caminhos, a outras áreas ou a conteúdo técnico. Ter a skill
  não concede função, escrita ou aprovação de uma ação.
- Para liberar uma nova função, documente e revise sua skill, isole o
  conteúdo específico da função e teste a leitura pelo manifesto e a
  recusa de acesso em uma atribuição menor. Após incidentes, atualize a
  própria skill e repita os casos afetados. A área `08` tem skill técnica
  própria e não entra no manifesto do Ops.
