# Rotinas determinísticas e destravamento

> Status: especificação inicial, 2026-10-30. Os tempos e contagens abaixo
> são valores de partida para calibrar nos primeiros testes — não são
> resultados validados ainda. Cada calibragem vai para `experimentos/`
> e para o histórico no fim deste arquivo.

## Ideia central

Tarefa repetida não se resolve com "o agente improvisa a cada vez".
Ela se resolve com uma rotina nomeada, com passos fixos, tela esperada
depois de cada passo e condição de parada. O improviso só entra onde
ele é liberado: dentro da escada de destravamento, e nunca mudando o
objetivo da tarefa.

Exemplo do que NÃO pode acontecer por improviso: a tarefa era "salvar
rascunho", e o agente, travado, publica. Ou a tarefa era "triar inbox",
e o agente responde comprometendo preço. Objetivo não se negocia em
recuperação.

## O loop de todo passo (obrigatório)

1. **Observar:** checar vigília, capturar tela e, quando disponível,
   despejar a árvore de UI.
2. **Agir:** executar UM passo da rotina.
3. **Verificar:** reler tela/árvore e confirmar o efeito esperado.
4. **Registrar:** passo, tela esperada, tela obtida, resultado.
5. Se o efeito não veio, entrar na escada de destravamento — não repetir
   o mesmo toque às cegas.

## Navegar com cautela, sem pressa, em ritmo humanizado

Instrução do usuário, 2026-10-30, que vale para toda navegação no S10
e já segue as skills aprendidas: sem pressa, sem rajada, sem retry
apressado. Na prática: esperar a tela estabilizar antes de cada
passo; um toque por vez; pausa entre ações; se travar, esperar, reler
e só então subir a escada de destravamento; se o aparelho estiver
offline, não forçar conexão — registrar o bloqueio e aguardar o
usuário trazer o aparelho online. Cautela não é lentidão por lentidão:
é o que mantém a conta, a sessão e o experimento íntegros.

## Sinais de travamento

- Mesma tela / mesma árvore de UI após 2 ações diferentes.
- Indicador de carregamento por mais de 30 segundos (valor inicial).
- Teclado cobrindo o botão que a rotina precisa.
- Popup, diálogo ou permissão bloqueando a tela.
- Diálogo "o app não está respondendo" (ANR).
- Tela preta (Dozing) ou screenshot vazio (tela segura).
- Botão esperado não aparece após rolar até o fim da área rolável.
- Mesmo erro pela 3ª vez, ainda que em telas diferentes.

## Escada de destravamento (liberação do agente)

O agente está liberado para subir esta escada sozinho até o nível 2.
O nível 3 sempre para e chama o humano. Cada tentativa é registrada,
com no máximo 3 tentativas alternativas por passo.

### Nível 0 — Esperar e reler (sempre liberado)

- Esperar 5 s, recapturar, reler a árvore.
- Se era só lentidão de rede/renderização, o fluxo retoma aqui.
- Não conta como "tentativa alternativa" se a tela mudar sozinha.

### Nível 1 — Ajuste de navegação (liberado)

- Fechar o teclado (`back` ou toque fora do campo, conforme a tela).
- Rolar para cima / para baixo dentro da área atual, procurando o
  elemento esperado por texto, depois por descrição de conteúdo.
- Voltar 1 passo (`back`) e reentrar pelo caminho da rotina.
- Mover foco pelo teclado quando a árvore expõe um único nó para a
  tela inteira (caso Compose/Flutter).
- Colar via clipboard em vez de digitar, quando o campo rejeita texto
  ou perde acentos.

### Nível 2 — Voltar a um ponto seguro (liberado, com registro)

- Voltar à tela inicial do app (Feed) pelo botão de início ou por
  `back` repetido, no máximo 3 vezes, verificando cada volta.
- Reabrir o app pelo ícone, se ele fechou ou ficou em segundo plano.
- **Antes de reabrir ou fechar o app:** se há rascunho ou texto não
  salvo em andamento, tentar salvar primeiro. Se salvar não for
  possível, parar no nível 3 — nunca descartar trabalho do usuário
  para "destravar".
- Depois de voltar ao ponto seguro, retomar a rotina do passo
  marcado como checkpoint, nunca do zero sem verificar o estado
  (rascunho já existe? mensagem já foi enviada? anúncio já existe?).

### Nível 3 — Parar e chamar o humano (nunca improvisar aqui)

- Login, senha, código de verificação, captcha ou qualquer
  autenticação.
- Tela segura com screenshot vazio que persiste após acordar o aparelho.
- Pagamento, confirmação de compra, aceite de termos, exclusão.
- Publicar ou enviar algo que a tarefa não pedia.
- Fechar o app à força com trabalho não salvo.
- Reiniciar o aparelho, mudar configuração de sistema, conceder
  permissão sensível.
- Mesmo travamento após a escada completa, ou 3 falhas no mesmo passo.

Ao parar no nível 3, o agente entrega: o que estava fazendo, em que
passo travou, o que tentou em cada nível, a última tela (descrição,
sem dados pessoais) e o que precisa do humano.

## Rotinas determinísticas (catálogo inicial)

Cada rotina tem: objetivo, pré-condições, passos, tela esperada por
passo, checkpoint e condição de parada. As rotinas de Facebook abaixo
só entram em teste após login manual no S10.

### R-01 — Acordar e abrir o Facebook

1. Checar vigília; se Dozing/preta, `keyevent 224` e verificar acordado.
2. Abrir o Facebook (`com.facebook.katana`).
3. Esperar tela estabilizar; confirmar que é o Feed ou a tela de login.
4. Se for tela de login: nível 3 (humano faz login).
5. Checkpoint: app aberto, usuário logado, Feed visível.

### R-02 — Voltar ao ponto seguro

1. Fechar teclado, se aberto.
2. `back` até o Feed, no máximo 3 vezes, verificando cada volta.
3. Se não chegar ao Feed, reabrir o app (nível 2) e verificar.
4. Checkpoint: Feed visível, nenhuma edição em andamento perdida.

### R-03 — Abrir um anúncio / conversa / post pelo identificador

1. Partir do ponto seguro (R-02).
2. Navegar pelo caminho mapeado da rotina chamadora (Marketplace,
   Messenger, Página), nunca por busca genérica improvisada.
3. Confirmar título/identificador na tela antes de qualquer ação.
4. Parada: identificador diferente do esperado = parar, não agir.

### R-04 — Salvar rascunho e sair sem publicar

1. Preencher campos a partir do catálogo (nunca inventar dado).
2. Verificar cada campo na tela antes de avançar.
3. Salvar como rascunho; confirmar o estado "rascunho" na tela.
4. Sair sem tocar em publicar.
5. Checkpoint: rascunho listado, com título conferido.

### R-05 — Triar inbox sem responder

1. Abrir o Messenger a partir do ponto seguro.
2. Listar conversas novas, sem abrir conversa que exija resposta imediata
   fora da fila.
3. Classificar cada uma (interessado / dúvida / golpe suspeito / spam)
   em `ops/triagem-interessados.md`.
4. Não enviar mensagem, não comprometer preço, não marcar encontro.
5. Checkpoint: fila atualizada, nada enviado.

### R-06 — Preparar post/vídeo como rascunho

1. Partir do catálogo e do roteiro aprovado.
2. Montar texto e mídia, conferir ordem e legenda.
3. Salvar como rascunho da Página; confirmar estado "rascunho".
4. Não publicar, não agendar sem aprovação explícita.

## Orçamento de desvio

- Máximo 3 tentativas alternativas por passo travado.
- Máximo 1 retorno ao ponto seguro por tarefa, salvo se a tarefa
  explicitamente permitir recomeçar (e registrar o recomeço).
- Tempo máximo por tarefa a calibrar no teste 1; estourado o tempo,
  parar no nível 3 com relatório parcial, não acelerar toques.

## O que o agente NÃO pode fazer "para destravar"

Publicar, enviar, apagar, pagar, logar, aceitar termos, conceder
permissão, reiniciar o aparelho, fechar app com trabalho não salvo ou
mudar o objetivo da tarefa. Se a única saída parecer ser uma dessas,
a saída certa é parar.

## Histórico de calibragem

- 2026-10-30 — Especificação inicial: escada 0–3, orçamento de 3
  tentativas por passo, tempos de partida (espera 5 s, carregamento
  30 s). Ainda sem validação no S10.
