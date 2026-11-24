# Site TuttiBom no Framer

Skill do fluxo do site da loja no Framer: construir e ajustar as páginas a
partir do protótipo do Magic Patterns, sem publicar sem decisão do usuário.
Ler antes de qualquer tarefa no projeto Framer.

## O que nunca fazer

- **Nunca reexecutar os programas de construção** (`/tmp/framer-build-home.js`,
  `/tmp/framer-build-3d.js`, `/tmp/framer-build-fitas.js`) — eles duplicariam o
  conteúdo. Ajustes SÓ por patch ou programa cirúrgico via `framer.exec`.
- **Nunca publicar** sem a decisão explícita do usuário. O site existe só no
  editor até lá. Domínio pendente.
- **Nunca colocar preço** em lugar nenhum do site — o protótipo também não tem.
- Nunca inventar texto, prazo, endereço ou link que não esteja no protótipo.

## Layout — a lição da sobreposição (2026-11-17)

- As seções da Home foram construídas sobrepostas (print do usuário): textos
  por cima de cartões, respiro zerado.
- **Causa real (confirmada na árvore): o programa de construção criava os
  stacks sem declarar altura, e o Framer aplicava a altura padrão do FrameNode
  — 100 px fixos — em cada seção.** O conteúdo (500–1500 px por seção)
  transbordava com overflow visível para dentro da seção seguinte. O gap 0
  entre as seções NÃO era a causa (só fazia as seções se tocarem) e o aviso
  "siblings too close" era sintoma, não causa.
- **Regra: todo FrameNode de stack precisa de `height: "auto"` (fit content)
  ou de altura explícita intencional — nunca deixar a altura em branco**,
  porque o padrão de 100 px quebra a página inteira silenciosamente.
  Correção feita por patch (174 nós, `100px` → `auto`, sem reexecutar os
  programas de construção): 0 ocorrências de `100px` restantes, linter vazio.
- Depois de qualquer ajuste de layout, verificar lendo a árvore: alturas
  `auto` onde o conteúdo manda, gaps maiores que zero, nenhuma seção invadindo
  a outra, nenhum aviso restante.
- Só o breakpoint Desktop (1200 px) foi construído; mobile e tablet herdam o
  empilhamento — revisar no editor antes de publicar.

## Conteúdo

- Fonte: protótipo Magic Patterns, editor `7fm8x7puzjvafafgwpjwm2`, artefato
  `43a5f6f4-4d35-4cc0-990b-9da9329d3da0` (só leitura; nada alterado lá).
- Projeto Framer: "TuttiBom", id `BDhe0URLFRQFGavqPZy6`. Páginas: Home `/`,
  Impressão 3D `/3d`, Fitas `/fitas`.
- CTAs vão para o WhatsApp (`wa.me/<NUMERO_LOJA>`) com as mensagens exatas de
  `data/site.ts` do artefato. Imagens via CDN público do Magic Patterns.
- Créditos de modelo onde existirem (ex.: "Modelo: @kayocavalcantte, licença
  CC BY"). Metadados (título/descrição) em cada página.
- Cores: fundo `#F6EBD8`, texto `#3E241C`, ouro `#C9A15B`, fita `#C45C32`.
  Fontes: Cormorant Garamond (títulos) + Inter (texto). Tema de Natal até o
  Natal.

## Breakpoints — lições da versão de celular (2026-11-17)

- O site nasce só com o Desktop. A versão de celular não aparece sozinha:
  breakpoints são criados pela API com `tree.createVariant` — os ids pedidos
  são renomeados pelo Framer; usar os ids devolvidos (`renamedIds`).
- Overrides vão SÓ nas variantes novas (o Desktop não se toca): no celular,
  menu de navegação oculto (`visible: false`), paddings 32 → 20 px, linhas de
  cartões em empilhamento vertical, imagens menores, chips com quebra de linha
  (`stackWrapEnabled: true`), fontes reduzidas (H1 60 → 44 px).
- O parser de scripts do Framer rejeita `$` em acesso por ponto
  (`p.$breakpoints` dá SyntaxError) — usar colchetes (`p["$breakpoints"]`).
- `fontSize` pode ser patchado no descendente da variante e altera os runs do
  texto.
- Diagnósticos do linter que vêm junto com o resultado de uma mutação
  refletem o estado PRÉ-mutação — sempre reler só-leitura para validar.

## Verificação

- 3 páginas com paths `/`, `/3d`, `/fitas`, nenhuma em draft.
- Conferir links (internos, âncoras, wa.me com as mensagens exatas) e a
  ausência de preço antes de entregar.
- A revisão visual final é do usuário, no editor — o agente verifica pela
  árvore e registra o que ficou para o olho humano.
