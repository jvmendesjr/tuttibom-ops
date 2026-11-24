---
name: ops-ana-triagem
description: Procedimento exclusivo da função 01.01 para leitura e triagem da fila e do histórico, incluindo bloqueios por mídia, transcrição ou contexto insuficiente.
---

# Ana — triagem da fila

## Âmbito e limite

Execute somente **01.01 — Ler conversa**. A função é **exclusivamente de leitura**.

Aplique a persona e os guardrails comuns de `ops-ana-atendimento`, mas não prepare nem envie resposta. A triagem termina com contexto suficiente para uma eventual função 01.02 ou com o turno pendente por lacuna.

Não presuma que existam interpretação de imagem, transcrição, acesso a mídia ou histórico quando o fluxo não os disponibilizar.

## Passos

1. Use `ops_atendimento_listar_pendencias` para a fila e `ops_atendimento_ler_conversa` para o histórico. Leia somente as conversas compreendidas pela autorização vigente.
2. Antes de qualquer proposta posterior, leia o histórico disponível do item e verifique sua atualidade.
3. Distinga mensagens pendentes de mensagens já respondidas. Considere também cumprimentos e perguntas já feitos para evitar repetição na função posterior.
4. Examine todos os itens do turno, inclusive anexos sem legenda. Texto compreensível não compensa uma mídia necessária que esteja inacessível.
5. Interprete toda imagem acessível, **mesmo sem legenda**, usando somente a capacidade de interpretação fornecida pelo fluxo. Não exija legenda para realizar essa leitura.
6. Para cada áudio, considere a transcrição entregue pelo MCP. Não busque o anexo por fora. Se a transcrição faltar, não deduza fala, intenção ou conteúdo pelo nome ou pela duração.
7. Confirme que fila, histórico, mídias e transcrições necessários estão disponíveis e são atuais.
8. Se o turno estiver completo, conclua a triagem sem redigir cumprimento, pergunta, resposta ou qualquer outra minuta.
9. Se houver lacuna, deixe o turno pendente e avise internamente o operador, sem responder ao cliente.

## Bloqueio por lacuna

Imagem, áudio, transcrição ou histórico ausente, indisponível, inacessível ou obsoleto bloqueia **todo o turno**, não apenas o item afetado.

Nesse caso:

- não invente nem complete o conteúdo;
- não prepare rascunho;
- não responda ao cliente, nem para informar a falha;
- não confirme recebimento;
- não altere a fila;
- avise internamente o operador pelo mecanismo autorizado, se disponível.

O aviso interno deve conter apenas o motivo técnico e identificadores técnicos permitidos. Não inclua nome, contato, texto da conversa, imagem, áudio, transcrição ou outro dado pessoal. Se não houver mecanismo autorizado de aviso, mantenha o bloqueio e informe a lacuna na saída interna da função, sem conteúdo da conversa.

## Proibições específicas

- Não enviar ACK nem qualquer confirmação de recebimento.
- Não marcar item como lido, processado, respondido, entregue ou fechado.
- Não registrar lead, CRM, estágio, follow-up ou qualquer outra escrita comercial.
- Não consultar preço como atalho para contornar contexto, imagem, áudio ou transcrição ausente.
- Não preparar texto para a função de resposta, ainda que o pedido pareça simples.
- Não inferir o conteúdo de uma imagem ou áudio que não foi efetivamente interpretado ou transcrito.
- Não reabrir mensagens já respondidas nem propor novo cumprimento quando o histórico já tiver cumprimento pertinente.

## Exceções

- **Imagem sem legenda:** não é bloqueio quando a imagem está acessível e sua interpretação está disponível. A imagem deve ser interpretada normalmente.
- **Imagem sem acesso ou sem interpretação disponível:** bloqueia o turno, mesmo que exista legenda ou texto suficiente em outras mensagens.
- **Áudio com transcrição disponível no fluxo:** pode ser considerado dentro do limite de leitura; a transcrição não autoriza responder.
- **Áudio sem transcrição disponível no fluxo:** bloqueia o turno. Não tente obter o áudio por outra via nem presuma seu conteúdo.
- **Falha em apenas um insumo necessário:** bloqueia o turno inteiro; não produza uma triagem parcial para envio posterior.
- **Nenhuma mensagem pendente:** não crie trabalho novo, não proponha resposta e não altere a fila.

## Casos de referência

### Imagem sem legenda

**Situação:** a mensagem contém uma imagem acessível, sem texto, e o fluxo oferece interpretação da imagem.

**Resultado esperado:** interpretar o conteúdo visual e incluí-lo na compreensão do turno. Não bloquear apenas pela ausência de legenda e não redigir resposta.

### Áudio sem transcrição

**Situação:** há um áudio, mas nenhuma transcrição disponível no fluxo.

**Resultado esperado:** turno pendente, aviso interno sanitizado ao operador e nenhuma resposta ao cliente. Não baixar o áudio nem supor seu conteúdo.

### Histórico indisponível ou obsoleto

**Situação:** a mensagem atual é um texto simples, mas o histórico não pôde ser lido ou não está atualizado.

**Resultado esperado:** bloquear todo o turno e avisar internamente o operador sem copiar a mensagem. Não usar o texto isolado como atalho e não preparar resposta.

### Conversa já cumprimentada

**Situação:** o histórico mostra cumprimento anterior e uma nova dúvida pendente.

**Resultado esperado:** reconhecer que já houve cumprimento para evitar repetição na etapa posterior. Não preparar outro cumprimento, não enviar ACK e não alterar a fila.

### Texto legível acompanhado de imagem inacessível

**Situação:** o texto pergunta sobre um item, mas a imagem necessária não pode ser lida ou interpretada.

**Resultado esperado:** turno inteiro pendente, sem resposta parcial baseada somente no texto e sem consulta de preço como substituto da leitura da imagem.

### Mensagens já respondidas

**Situação:** a leitura encontra apenas mensagens que já receberam resposta no histórico.

**Resultado esperado:** não reabrir o turno, não preparar nova resposta e não registrar alteração na fila.
