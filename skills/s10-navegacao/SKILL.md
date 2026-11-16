# Skill: s10-navegacao

Navegação determinística no Galaxy S10 Lite via ADB. Esta skill é o
executor do experimento: nenhuma outra skill toca na tela sem passar
por este loop.

## Dispositivo e acesso

- Aparelho: Samsung Galaxy S10 Lite (SM-G770F, Android 13, Wi-Fi,
  sem chip), via Termux + Tailscale + SSH.
- **Ponto de execução do ADB: o PC** (`~/platform-tools/adb`),
  não a VM e não o próprio aparelho. Correção 2026-11-01: a
  versão anterior desta skill dizia que o ADB rodava no aparelho;
  o ponto mudou para o PC (ver `docs/08-pc-adb-ponto-execucao.md`
  no repo acesso-dispositivo-smartphon).
- A porta do ADB é efêmera e muda a cada reativação: reler o
  endpoint (`~/adb-endpoint.txt` / `~/adb-status.txt` no telefone,
  via SSH, ou a tela do S10) antes de cada conexão. Nunca fixar
  IP/porta em documento como valor permanente.
- **Portão de conexão** (`scripts/adb-gate.sh`, no PC): antes de
  qualquer janela, `adb-gate.sh connect <endpoint>` — reconexão
  com retries limitados (10 tentativas × 3 s, 30 s máx) e falha
  classificada (não autorizado / offline / sem rota). Depois,
  `adb-gate.sh check <endpoint>` verifica identidade (modelo
  SM-G770F), tamanho (`wm size`, esperado 1080×2400), app em foco
  (`dumpsys window`) e `boot_count` (sinal de reinício).
- **Todo comando ADB usa `adb -s <endpoint>`** (o serial é o
  endpoint). Verificar a identidade do aparelho antes de agir
  sobre qualquer telemetria ou tela.
- Ações por SSH não mudam a tela; toques, teclas e aberturas de app via
  ADB são toques reais e visíveis.

## Regra da tela (antes de qualquer passo de UI)

1. Checar vigília. Desbloqueado não significa acordado.
2. Se estiver em Dozing ou a captura voltar preta: `keyevent 224`,
   verificar acordado, recapturar.
3. Timeout de tela: 5 minutos. Após idle, a regra continua valendo.
4. Durante sessão com carregador, `stayon true` pode ser usado
   temporariamente e deve voltar a `false` no fim.

## Loop obrigatório por passo

Observar → agir (um passo) → verificar (reler tela/árvore) → registrar.
Nunca agir sobre tela em cache. Nunca repetir o mesmo toque às cegas.

- **Captura por streaming:** `adb exec-out screencap -p`, nada
  escrito no `/sdcard` do telefone. Mais rápido e sem arquivo
  sobrando no aparelho.
- **Esperar por marcador, não por sleep fixo:** após agir, esperar
  até o estado esperado aparecer (poll por marcador na captura,
  com timeout); o sleep é só piso — **2–3 s após cada ação** antes
  de reler, porque a tela pode ainda estar animando.
- **Re-verificar após CADA ação que a tela realmente mudou:**
  verificar a mudança, não só que veio uma imagem nova.
- **Listas virtuais mentem:** o Feed é uma lista virtual
  (bounds colapsados, itens que não respondem). Antes de cada tap
  num item, reler a tela e se reancorar com marcadores visíveis.
  Saída quando a lista "pula" a seção: padrão `jump` (3 swipes
  grandes rápidos + micro-swipes de volta).
- **Tap no centro do bounds.** Se um tap cru algum dia não
  produzir efeito, o fallback é o clique via uiautomator2
  (teste controlado, ver abaixo) — nunca repetir o tap às cegas.
- **Abrir app:** preferir `am start` determinístico com
  componente explícito; `monkey` só como fallback de abertura.
- **Registro por passo:** um comando → uma linha de log, com
  resultado ok/falha por passo e resumo final da sessão. A falha
  é classificada pela causa do lado ADB (não autorizado vs offline
  vs sem rota), não só pelo sintoma.
- **Limite de tentativas idênticas: 2.** Após 2 falhas idênticas
  no mesmo passo, trocar de estratégia ou parar a janela (ver
  escada). O limite antigo de "no máximo 3 tentativas
  alternativas por passo" continua valendo para tentativas
  *diferentes*; 2 idênticas é o teto para repetir o mesmo.

## Rotinas e destravamento

Toda tarefa usa uma rotina nomeada em
`docs/rotinas-deterministicas.md` (R-01 a R-06 e as que forem criadas).
Quando travar, o agente sobe a escada de destravamento:

- Nível 0: esperar 5 s e reler.
- Nível 1: fechar teclado, rolar, voltar 1 passo, mover foco pelo
  teclado, colar via clipboard em vez de digitar.
- Nível 2: voltar ao ponto seguro (Feed) ou reabrir o app — mas nunca
  descartar rascunho ou texto não salvo; se não der para salvar, parar.
- Nível 3: parar e chamar o humano. Login, verificação, captcha,
  pagamento, exclusão, publicar/enviar fora do objetivo, fechar app
  com trabalho não salvo, reiniciar o aparelho.

Limites: no máximo 3 tentativas alternativas por passo; no máximo 1
retorno ao ponto seguro por tarefa, salvo registro explícito de
recomeço. Objetivo da tarefa nunca muda em recuperação.

## Texto em português

Preferir colar via clipboard a digitar, para não perder acentos.
Confirmar o texto na tela depois de colar, antes de avançar.

- Método atual (provado): digitação tecla por tecla no teclado
  Samsung (`adb shell input text` falha em não-ASCII; `%s` para
  espaços NÃO resolve — descartado).
- **Teste controlado pendente:** clipboard + long-press + Colar
  (via uiautomator2) para texto não-ASCII — primeiro em campo
  neutro, depois como rascunho descartado no compositor. Limpar o
  campo antes de colar (colar sobre texto existente concatena).
  Segunda alternativa, só se o clipboard falhar: ADB Keyboard por
  broadcast (`ADB_INPUT_B64`) — exige APK + troca de IME.
- **Fallback de interação pendente de teste:** árvore de
  acessibilidade via uiautomator2 quando o screencap é preto ou o
  dump falha (o `uiautomator dump` de shell retorna nó nulo neste
  aparelho; o dump via serviço de acessibilidade é outro mecanismo).
  Instalação do atx-agent no telefone aprovada pelo usuário em
  2026-11-05 ~22:14, se preciso para o teste.

## Fim de janela (sempre)

1. `adb-gate.sh disconnect <endpoint>` — sessão one-shot: criar,
   executar, encerrar. Nada de servidor parado no PC ao fim.
2. `stayon false` se foi usado `stayon true` durante a sessão.
3. Expurgar capturas do lado do telefone (nada fica no `/sdcard`) e
   do lado do PC/VM o que não for evidência da sessão.
4. Resumo final da sessão (passos ok/falha, `boot_count` se mudou).

## Higiene (regras fixas)

- Capturas vivem em diretório privado, com expurgo automático;
  nunca ecoar ou registrar o texto digitado (só o tamanho).
- Servidores de automação só em loopback; parar ao terminar.
  Nunca expor a porta ADB ou um servidor de controle além de
  localhost/Tailscale.
- Qualquer ferramental Python adicionado (uiautomator2, OCR)
  precisa de versão fixada (pin), nunca `latest` do dia.
- Sem varredura de portas, sem `tcpip 5555`, sem mudar
  configuração de sistema para "destravar".

## Registro

Cada sessão registra: rotina, passo, tela esperada, tela obtida,
ação de destravamento (se houve) e resultado — em `experimentos/`
e, em resumo, em `RELATORIO.md`. Capturas brutas e dumps com dados
pessoais não vão para o repositório (ver `.gitignore`).
