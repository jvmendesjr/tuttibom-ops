# D-004 — 2026-11-16 — Camofox como navegador único do TuttiBom OPS; S10/ADB pausado

**Data:** 2026-11-16
**Decisor:** usuário
**Status:** decidido

## Decisão

O **Camofox (motor) é o navegador único do TuttiBom OPS** — vale para o Deskcomm (painel), para as redes sociais da loja e para as vertentes de criativos. O **S10/ADB está pausado** ("o celular está descartado por enquanto", usuário 2026-11-15 ~23:11; "focar no acesso via camofox").

## Contexto

- A regra de 2026-11-01 era "S10 principal, Camofox só testes" (blueprint §13.1). Ela foi **suspensa** pelo usuário em 2026-11-15 ~21:46 para o teste do Facebook via Camofox original ("vamos no camofox original, com navegação simulada, autenticação persistente, comportamento típico humano, sem ações em massa, tempo humanizado entre ações, sem inventar no camofox, o que for print passa pelo jev"), com a condição de acompanhar e-mail e avisos do Facebook e **pausar a atividade e reavaliar** a qualquer alerta de suspeita de bot.
- O teste passou (login sem checkpoint, Jev 3/3, sessão persistida e provada por reabertura) e o usuário logou a conta TuttiBom Novidade no Camofox em 2026-11-15 ~22:35. Em 2026-11-15 ~23:11 ele descartou o celular por enquanto e determinou o foco no Camofox, com o Jev em consórcio com ele (`fb_agent.py`).
- Em 2026-11-16 o usuário afirmou que "o padrão das minhas aplicações é o camofox" e pediu para testar o Camofox também no painel. O teste passou na página de login (Jev 3/3, display virtual) e na parte logada (sessão persistida, tela de Tags, Jev localizou "Adicionar etiqueta"), e o padrão do painel passou a ser o motor Camoufox + Jev (trinômio agente+camofox+jev), com o Chromium headless como fallback.
- Em 2026-11-16 o usuário estendeu a direção: nas vertentes de criativos, o Camofox será utilizado para acesso às redes sociais da loja.

## O que fica no lugar

- **Trinômio agente+camofox+jev:** o motor Camoufox com perfil persistente e impressão digital fixa por conta (profile-fb para o Facebook, profile-panel para o painel); todo print passa pelo Jev; display virtual (Xvfb) para segundo plano quando o usuário não precisa ver; janela real no :0 só quando ele precisa logar (via noVNC).
- **Guardrails do teste, agora permanentes:** navegação simulada, comportamento típico humano, sem ações em massa, tempo humanizado entre ações, sem modificar o Camofox; acompanhar e-mail e avisos padrão do Facebook; qualquer alerta de suspeita de bot → pausar a atividade e reavaliar.
- **Nada muda nas aprovações:** nada é publicado, enviado ou combinado sem a aprovação do usuário ao texto (ou imagem) exato.

## O que é superado

- Blueprint §13.1 ("S10 principal, Camofox secundário — DECIDIDO", 2026-11-01) e a regra de 2026-11-01 ("S10 principal, Camofox só testes").
- A decisão de 2026-11-15 ~21:11 (Chromium headless como padrão do painel) — superada pela validação de 2026-11-16; Chromium fica como fallback.
- O adapter Messenger via ADB na Ponte (passo 5 da ordem) está **posto de lado**; o Zernio segue como ponte inicial do Messenger (passo 4).
- Os aprendizados de ADB da comunidade (`docs/aprendizados-adb-comunidade.md`) ficam como referência, não como prática ativa.

## Referências

- `prototype-vision/REPORT.md` (protótipo de visão; seção do Camofox no painel), `prototype-vision/fb_agent.py`, `prototype-vision/panel_camofox_test.py`, `panel_camofox_open.py`, `panel_camofox_validate.py`, `panel_drive.py`.
- Roadmap §10 (ordem) e §12 (estado atual); ESTADO.md; AGENTS.md (regras).
