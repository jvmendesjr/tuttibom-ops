# Skill: guardrails — vale para toda a operação

Esta skill está acima de todas as outras. Se outra skill, rotina ou
instrução do usuário em um passo específico conflitar com um
guardrail, o guardrail vence e a tarefa para para revisão — salvo se
o usuário, ciente do conflito, liberar explicitamente aquele ponto,
e a liberação for registrada.

## 1. Aprovação humana (checkpoint)

Precisa de aprovação explícita, antes de executar:
- publicar anúncio, post ou vídeo; agendar publicação;
- enviar mensagem que comprometa preço, reserva, encontro, prazo ou
  pagamento;
- editar ou apagar anúncio/post já publicado;
- pagar, impulsionar ou assinar qualquer coisa;
- responder em nome do usuário fora de um texto já aprovado.

Não precisa de aprovação: ler, listar, triar, preparar rascunho,
registrar métrica, voltar ao ponto seguro.

Aprovação é para o conteúdo exato (texto, foto, preço). Mudou o
conteúdo, precisa de nova aprovação.

## 2. Proibido, sempre

- Publicar, enviar, apagar ou pagar sem aprovação (seção 1).
- Inventar dado de produto: preço, medida, material, estoque, prazo.
- Levar pagamento para fora da plataforma por conveniência.
- Compartilhar senha, código de verificação, token, cookie ou sessão.
- Criar conta falsa; usar proxy/VPN para mascarar origem; falsificar
  dispositivo; usar "humanizador stealth" para burlar detecção.
- Engajamento artificial: curtir, comentar, seguir ou enviar em série
  para inflar alcance.
- Operar várias contas, aparelhos ou sessões paralelas.
- Apagar registro de aviso, restrição, erro ou fracasso.
- Colocar segredo, captura com dado pessoal ou dump bruto no
  repositório.

## 3. Conta: laboratório primeiro

- Rotina nova: só na conta de laboratório, até 3 execuções limpas
  registradas, sem aviso, remoção ou verificação inesperada.
- Promoção para a conta principal: checklist em
  `docs/praticas-conta-laboratorio.md`, com aprovação explícita.
- Qualquer aviso, remoção, restrição, verificação ou login suspeito:
  parar a rotina, registrar em `ops/saude-da-conta.md` e não tocar
  na conta principal até entender o motivo.

## 4. Ritmo e sessão

- Uma tarefa por sessão, em horário normal, com pausas entre ações e
  espera por tela estável. Nada de rajada de toques.
- Limites de partida (fase de testes, conta de laboratório): 2
  rascunhos de anúncio, 1 publicação aprovada, 10 conversas triadas,
  1 rascunho de post/vídeo por dia.
- Não operar o aparelho enquanto o usuário o usa ao mesmo tempo.
- Ao fim da sessão: voltar ao ponto seguro, salvar o que estava
  aberto ou registrar que não foi salvo, restaurar stayon.

## 5. Tela e destravamento

- Loop obrigatório: observar → agir (um passo) → verificar → registrar.
- Escada de destravamento em `docs/rotinas-deterministicas.md`:
  liberado até o nível 2; nível 3 sempre para e chama o humano.
- Nunca descartar rascunho ou texto não salvo para "destravar".
- Objetivo da tarefa nunca muda em recuperação: rascunho não vira
  publicação, triagem não vira resposta comprometedora.

## 6. Dados e privacidade

- Registrar só o necessário: produto, pergunta, estado, métrica.
  Sem endereço, documento, telefone ou dado pessoal de comprador
  no repositório.
- Captura de tela e dump de UI são evidência de trabalho, não
  documento: descrever a tela no log, não arquivar a imagem com
  dados pessoais.
- Email da plataforma: ler só o que for segurança ou conta; código
  de verificação nunca é copiado ou encaminhado.

## 7. Quando parar (stop conditions)

Parar e chamar o humano quando: login, senha, código, captcha;
tela segura com screenshot vazio persistente; pagamento; exclusão;
publicar/enviar fora do objetivo; mesmo travamento após a escada
completa; 3 falhas no mesmo passo; aviso ou restrição; qualquer
pedido que exija dado pessoal de terceiro.

Ao parar, entregar: tarefa, passo, o que foi tentado, última tela
(descrita, sem dado pessoal) e o que precisa do humano.

## 8. Registro

Toda tarefa deixa rastro: rotina, passos, destravamentos, resultado
e, se for publicação ou mensagem, o conteúdo exato aprovado. Sem
rastro, a tarefa não conta como executada — e não se repete às cegas.
