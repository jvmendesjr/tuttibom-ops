# Laboratório V3 — relatório

**Rodado em:** 2026-11-21T19:31:18+00:00 (UTC) — banco SQLite temporário, personas fictícias, nenhum canal real.
**Entradas:** skill da Ana `c918ea0` (`exp/atendimento-ana`), CRM `54f271c` (`exp/crm-proprio`).

**Resultado: 45/45 checagens passaram; 0 falharam.**

## Transcrição (fictícia)

**Cliente (fictício):** oi
**Ana:** Oi! Me conta o que você está buscando que eu te ajudo.
**Cliente (fictício):** quero uma fita para aniversário
**Ana:** Para qual ocasião é a fita, aniversário de criança ou de adulto?
**Cliente (fictício):** aniversário de criança, fita 22 mm 50 m preta
**Ana:** A fita de 22 mm com 50 m e impressão preta fica R$ 71,90. Qual cor de fita você quer?
**Cliente (fictício):** quanto fica o frete para Juazeiro?
**Ana:** Me passa o endereço completo que eu verifico com o produtor e te retorno, pode aguardar?
**Cliente (fictício):** quero ver como fica antes de fechar
**Ana:** Quer que eu monte uma prévia para você ver como fica na fita? É uma simulação que eu preparo para você visualizar antes de confirmar.
**Cliente (fictício):** oi
**Ana:** Oi! Me conta o que você está buscando que eu te ajudo.
**Cliente (fictício):** faz por metade do preço?
**Ana:** O valor já é bom e justo e, infelizmente, não podemos dar desconto. Você continua com interesse? Fico à disposição para tirar dúvidas sobre o produto.

## O que NÃO foi testado aqui

- O texto exato da v12-B (só no painel do Deskcomm).
- WAHA, Zernio, número e página: nenhum foi tocado.
- O LLM gerando a resposta: as respostas acima são o comportamento esperado segundo a skill, verificado por checagens determinísticas — não geração ao vivo.
- Frete com valor real e endereço pós-pagamento: fora do laboratório, com o produtor, no V4.
