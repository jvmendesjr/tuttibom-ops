# Práticas para proteger a conta do laboratório

> Princípio: a proteção vem de agir como um uso legítimo, em escala
> humana, numa conta de teste — não de enganar a detecção. Nada aqui é
> técnica de evasão: sem falsificação de dispositivo, sem proxy para
> mascarar origem, sem "humanizador" para burlar bot, sem conta falsa,
> sem automação paralela. Se uma prática só faz sentido para esconder
> que há um agente, ela está fora.

## 1. Conta de laboratório primeiro

- Testar rotinas novas sempre na conta de laboratório, nunca direto na
  conta principal de vendas.
- Só promover uma rotina para a conta principal depois de: 3 execuções
  limpas na conta de laboratório, sem aviso, sem remoção e sem
  verificação inesperada, registradas em `experimentos/`.
- Uma conta, um aparelho, uma sessão por vez. Nada de sessões paralelas,
  nada de alternar contas no meio de uma tarefa, nada de operar a conta
  de laboratório e a principal ao mesmo tempo no mesmo aparelho.
- Se a conta de laboratório receber aviso, restrição ou verificação:
  parar tudo, registrar em `ops/saude-da-conta.md` e não tocar na conta
  principal até entender o motivo.

## 2. Ritmo humano — limites internos conservadores (a calibrar)

Os números abaixo são limites internos do experimento, não limites
oficiais do Facebook (que não são publicados). Começar baixo e só
subir se os testes ficarem limpos.

- **Uma tarefa por sessão, com começo, meio e fim.** Nada de encadear
  anúncio + inbox + post + engajamento numa rajada só.
- **Sessões curtas, em horário de uso normal do usuário.** Nada de
  atividade na madrugada só porque o agente está livre.
- **Pausas entre ações:** esperar a tela estabilizar antes do próximo
  passo; nunca disparar toques em rajada. A pressa é o sinal mais
  barato de automação.
- **Limites de partida por dia, na conta de laboratório:**
  - no máximo 2 rascunhos de anúncio criados;
  - no máximo 1 publicação (só após revisão e aprovação);
  - no máximo 10 conversas triadas, 0 mensagens enviadas sem aprovação;
  - no máximo 1 rascunho de post/vídeo.
- **Intervalo entre sessões:** no mínimo 1 hora entre tarefas
  diferentes no mesmo dia, na fase de testes.
- **Sem repetição mecânica:** não republicar o mesmo anúncio, não
  reenviar a mesma mensagem, não curtir/comentar em série. Cada ação
  tem um motivo registrado na tarefa.

## 3. Comportamento de sessão

- Começar sempre pelo ponto seguro (Feed), como um usuário faria, e
  terminar a sessão no ponto seguro, sem deixar rascunho aberto sem
  salvar.
- Ler antes de agir: abrir a conversa, o anúncio ou o post, confirmar
  o identificador e só então decidir.
- Não navegar em círculos: se a rotina precisa de mais de 3 voltas
  pela mesma tela, parar e revisar a rotina — navegação circular é
  outro sinal de automação.
- Não operar enquanto o usuário está usando o aparelho ao mesmo tempo.
  Sessão do agente e sessão humana não se misturam: risco de toque
  cruzado e de estado inconsistente.
- Ao fim da sessão, restaurar o estado do aparelho (tela, stayon) e
  registrar o que foi feito.

## 4. Conteúdo e mensagens: autenticidade verificável

- Só produto real, foto real, preço real, medida real. Nada de texto
  genérico em massa.
- Cada anúncio e post tem origem no catálogo e revisão humana antes de
  publicar. Conteúdo duplicado em vários anúncios é evitado: variar
  descrição de verdade, não por sinônimo automático.
- Respostas: tom de pessoa, informação concreta, sem template colado
  sem adaptação ao que o interessado de fato perguntou.
- Nada de engajamento artificial: não curtir, comentar ou seguir em
  série para inflar a Página. Engajamento é resposta e conteúdo, não
  volume.

## 5. Sinais de alerta — parar imediatamente

- Aviso, remoção de anúncio, pedido de verificação, captcha, bloqueio
  temporário, "atividade incomum", solicitação de documento.
- Mudança repentina de interface no meio da tarefa (pode ser teste
  A/B ou verificação).
- Qualquer pedido de senha, código ou documento dentro do fluxo.
- Ao parar: registrar a tela (descrição, sem dados pessoais), a rotina,
  o passo e o que foi tentado; não tentar "contornar" o alerta.

## 6. O que é proibido, mesmo que "proteja" a conta

- Criar conta falsa ou conta só para o experimento que não seja do
  próprio usuário.
- Usar proxy/VPN para mascarar localização ou origem.
- Falsificar modelo de aparelho, impressão digital ou sinais do
  dispositivo.
- Usar ferramenta "stealth"/"humanizer" para burlar detecção.
- Operar várias contas, vários aparelhos ou sessões paralelas para
  diluir volume.
- Apagar evidência de aviso ou restrição do diário para "limpar" a conta.

## 7. Promoção laboratório → principal (checklist)

- [ ] Rotina executada 3 vezes limpa no laboratório, registrada.
- [ ] Sem aviso, remoção ou verificação nas 3 execuções.
- [ ] Rascunhos revisados pelo usuário em todas as execuções.
- [ ] Limites de ritmo respeitados (seção 2).
- [ ] Diário de saúde da conta atualizado.
- [ ] Usuário aprovou explicitamente a promoção da rotina.

Sem todos os itens, a rotina fica no laboratório.

## Histórico de calibragem

- 2026-10-30 — Especificação inicial: limites de partida e checklist
  de promoção. Ainda sem validação no S10.
