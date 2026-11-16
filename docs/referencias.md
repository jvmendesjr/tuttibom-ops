# Referências

Fontes consultadas em 2026-10-30. O que entra no projeto é o padrão
abstraído, não código copiado sem auditoria.

## Skills de Marketplace (referência para as nossas skills)

- ClawHub, ivangdavila/facebook-marketplace:
  https://clawhub.ai/ivangdavila/skills/facebook-marketplace
  Aproveitado: memória estruturada, preço mínimo, triagem, saúde da
  conta. Descartado como executor: é playbook, não executa.
- Printing Press, mvanhorn/pp-facebook-marketplace:
  https://www.skills.sh/mvanhorn/printing-press-library/pp-facebook-marketplace
  Aproveitado: trava de escrita, checkpoints, vigia local.
  Descartado como executor neste projeto: CLI de desktop via sessão
  Chrome, não ADB no S10; superfície não oficial, exige auditoria.

## Pesquisa de comunidade (método agent-reach)

- agent-reach (Panniantong/Agent-Reach): camada de pesquisa
  multi-plataforma com roteamento e fallback entre backends.
  Papel aqui: método de pesquisa, não executor no S10. Não instalada
  localmente no Muse até 2026-10-30.

## Navegação simulada em Android (padrões abstraídos)

- AppAgent: visão + LLM via ADB, sem script manual.
- Mobile-Agent-v3 / GUI-Owl / UI-TARS, Minitap: decomposição em
  planejador/operador/verificador; benchmark AndroidWorld como
  referência de teto, não de Facebook real.
- Midscene.js, Maestro, Appium + UiAutomator2: fluxos determinísticos,
  espera por tela estável, seletores.
- Google Artemis: agente via ADB com MCP, modos Flash e Pro com
  verificação — referência de arquitetura, com controvérsia de
  autoria a verificar antes de copiar código.
- Relato prático de ADB ("Giving an AI Agent a Real Phone"): ler, agir,
  ler de novo; árvore de UI que mente em Compose/Flutter; colar via
  clipboard para texto com acento; screenshot vazio em tela segura.

## Anti-padrões descartados

- "Humanizador stealth" para burlar detecção de bot.
- Engajamento artificial (curtir/comentar/seguir em série).
- Conta falsa, proxy para mascarar origem, falsificação de dispositivo.
