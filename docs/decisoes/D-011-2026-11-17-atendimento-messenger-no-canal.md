# D-011 — Atendimento no Messenger, no canal onde a pessoa escreveu

Data: 2026-11-17. Decisão do usuário; arquitetura fixa.

## Contexto

Hoje o Messenger (via Zernio) está com a IA pausada e as mensagens vão para
atendimento humano. A Ana atende o WhatsApp 24/7. O risco: empurrar quem
escreve no Messenger para o WhatsApp e perder a pessoa no caminho.

## Decisão

O atendimento acontece **no canal onde a pessoa escreveu** — a Ana (ou outro
agente) atende por mensagem no Messenger. O WhatsApp pode ser informado no
início como opção, mas nunca como obrigação: se a pessoa quiser continuar no
Messenger, continua. Não obrigar a pessoa a ir para o WhatsApp.

## Plano (não executado — só planejamento)

1. Conferir o prompt da Ana v10 para o Messenger: a saudação oferece o
   WhatsApp como opção, nunca como exigência.
2. Ligar a IA no canal Zernio no painel (ação que muda comportamento ao vivo;
   execução com aprovação do usuário).
3. Testar com mensagem real e conferir o roteamento e a resposta.
4. A mesma regra vale para o Instagram quando conectar (DMs no canal).

O fallback humano continua existindo (handoff). Em aberto: ajuste de prompt
específico para Messenger? Quem atende se a Ana cair?
