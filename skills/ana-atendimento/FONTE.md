# FONTE.md — skill `ana-atendimento`

## Origem

Skill nova, criada para a vertente da D-012 (2026-11-21). Não é cópia
de uma skill externa — é a consolidação do comportamento da Ana que já
existia no Deskcomm, adaptada para o atendimento feito aqui, pelo Muse.

## Fontes usadas (todas internas, lidas na íntegra)

| Fonte | O que trouxe |
|---|---|
| `docs/ana-prompt-v10.md` (62 linhas, no repo) | Base do prompt: identidade, horário, quem já conhece a loja, situações, amostra, limites, estilo, prazos, pagamento, entrega. |
| D-011 (2026-11-17) — atendimento no Messenger | Regra do canal (atender onde a pessoa escreveu), prompt único para os dois canais, regras da v11: nunca se apresentar como virtual de cara, nunca dizer que resolve 24h. |
| Prompt v12-B (publicada 2026-11-17 ~23:35) | Direção: prompt enxuto, 7.250 caracteres, + documento RAG "Prazos, pagamento e entrega" (23 trechos). |
| Skills Deskcomm `amostra-fita`, `frete-entrega`, `preco-catalogo`, `pos-venda` (zips em `skills/`) | Os 4 corpos de função, transcritos: amostra, frete, preço + desconto, pós-venda. |
| Skill monolito `atendimento-tuttibom` (zip em `skills/`) | A consolidação anterior das 4 funções + identidade — conferida contra as 4 skills. |
| `docs/setores/01-atendimento.md` (D-012) | A fronteira do setor 1: faz / não faz, aprovações, handoffs. |

## Ressalva honesta

**O texto exato da v12-B não está no repo** — ele vive só no painel do
Deskcomm (versão publicada). Esta skill é uma reconstrução fiel a
partir da v10 (arquivo no repo), das regras da v11 (D-011) e do resumo
da v12-B registrado na memória (enxuta, 7.250 caracteres). Se a v12-B
tiver uma linha que não está na v10 nem na D-011, ela não está aqui —
e a atualização é: ler a versão publicada no painel e trazer a linha
para cá, com decisão registrada.

## Adaptações para a nova vertente (o que mudou e por quê)

- "Consulte os produtos do Deskcomm" virou "cite o preço do catálogo
  (`catalogo/`)": na nova vertente não há Deskcomm; o catálogo vive no
  repo e no CRM próprio.
- "A amostra é feita pelo Muse. Você não gera a imagem — você pede ao
  Muse" virou "a prévia é gerada como rascunho": quem lê esta skill É
  o Muse, então a divisão é por etapa (gerar rascunho → aprovar →
  enviar), não por agente.
- "Equipe técnica ou o gerente" virou "o produtor / a equipe": com
  clientes, usa-se "produtor", nunca "gestor" (regra de 2026-11-06).
- Os blocos de prazos/pagamento/entrega, que na v10 estavam em inglês
  e em detalhe, foram condensados em PT-BR aqui; o detalhe vive nos
  setores 3 e 7, não na skill.
- As "regras de contato do aplicativo" (janela 7h–22h de disparo,
  resposta 0–24h) foram explicitadas onde importam (ack, follow-up,
  handoff no horário comercial).

## Como atualizar

1. Ler a versão publicada no painel do Deskcomm antes de afirmar que
   a skill está alinhada com a v12-B.
2. Qualquer mudança de comportamento passa pelo usuário e vira uma
   linha nova aqui — nunca uma exceção guardada só na memória.
3. Esta skill é o comportamento canônico da Ana na nova vertente
   (D-010: todo fluxo tem sua skill; o brief a nomeia).
