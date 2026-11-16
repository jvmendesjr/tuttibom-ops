# Aprendizados de ADB da comunidade — análise 2026-11-05

> ANÁLISE, 2026-11-05 ~22:07. Não é decisão: cada aprendizado traz
> um veredito proposto (ADOTAR / ADAPTAR / DESCARTAR) pela análise,
> e a adoção é decisão do usuário. Nada foi instalado ou alterado.
> A lente pedida pelo usuário: abstrair o aprendizado, desconsiderar
> o foco de ferramenta de cada fonte (OpenClaw, Appium, httprunner,
> forense).
>
> **Nota 2026-11-16 (D-004):** o caminho ADB/S10 foi pausado; o Camofox
> é o navegador único do TuttiBom OPS. Estes aprendizados ficam como
> referência, não como prática ativa.

## Fontes lidas

1. **S1 — AndroidForensics** (GitHub, DouglasFreshHabian, MIT,
   546 stars). Toolkit forense + guia de ADB com 2 scripts bash
   (`extract.sh`, `dumpsys.sh`).
2. **S2 — appium-android-adb** (ClawHub, openlittlebear). Skill-base:
   loop de OCR primário (uiautomator2 + RapidOCR), Appium só como
   fallback. A fonte mais rica.
3. **S3 — staticai/android-adb** (ClawHub). Referência curta
   (60 linhas) de conexão e comandos básicos.
4. **S4 — httprunner/android-adb** (skills.sh). Referência de ADB
   cru. Conteúdo conferido também pelo espelho da skill e por dois
   forks que citam os mesmos comandos.

## Por fonte — o que serve e o que não serve

**S1 — útil:** o padrão de diagnóstico — gate antes de agir
(`adb devices`, `getprop`, `dumpsys battery/connectivity/wifi/power`,
`logcat -d`, `settings list global` com `boot_count`); o helper
`run_adb_command` (um comando → um arquivo, sucesso/falha
registrados); esperar com retries pela autorização do dispositivo
(até 30 s, 10×3 s); diretório de relatório com timestamp; resumo
final de sucesso/falha por comando. **Não serve:** a metade de
extração (contatos, SMS, call logs via `content query`) — no
Android 11+ é bloqueada via ADB sem root, e extrair dados de
pessoas viola nossa regra de nunca guardar dado de comprador. Só
a metade de diagnóstico interessa.

**S2 — útil:** screencap por streaming, re-verificação após cada
ação, espera por polling, clipboard+colar para texto não-ASCII,
árvore de acessibilidade quando a tela é preta (FLAG_SECURE),
`d.click` onde o tap cru é filtrado, higiene de sessão e de
screenshots. **Não serve:** o Appium em si (precisa de
`io.appium.settings` + troca de IME; bloqueado em aparelhos
comuns — a própria skill documenta a falha num Realme); os
detalhes de 12306/PDD e de chinês.

**S3 — útil:** o fluxo de pareamento wireless (código + porta —
igual ao nosso); `monkey` para abrir apps; tabela de keyevents;
swipe com duração; "sleep entre comandos". **Não serve:** é fina
demais — nada sobre espera, retry, recuperação ou diagnóstico;
o `screencap -p /sdcard + pull` é o caminho pior (S2/S4 fazem por
streaming); o `uiautomator dump` que ela recomenda é justamente
o que falha no nosso S10.

**S4 — útil:** `adb -s SERIAL` em todo comando; `wm size` antes
de ações por coordenada; `dumpsys window | grep
mCurrentFocus|mFocusedApp`; `am force-stop`; duplo tap com
`sleep 0.1`; ADB Keyboard por broadcast `ADB_INPUT_B64`
(base64, CJK/especiais); `exec-out screencap -p`; classificar o
stderr da falha (autorização/rede/estado tcpip). **Não serve:**
o framework httprunner/`hrp` e o CLI TypeScript dos forks; o
modo `tcpip 5555` (outro caminho, ver contradições).

## Aprendizados consolidados (27)

### Conexão e recuperação

1. **Esperar com retries limitados pela autorização do dispositivo**
   (até 30 s, 10×3 s) em vez de um único check — S1. **ADOTAR**:
   formalizar nosso gate de reconexão com retries limitados.
2. **`adb -s <serial>` em todo comando** — S4 (S1 aceita serial
   como argumento). **ADOTAR**: é a execução da nossa regra de
   identidade do aparelho; barato.
3. **`wm size` antes de ações por coordenada** — S4. **ADOTAR**:
   gate de uma linha, confirma 1080×2400 antes dos taps.
4. **Modo clássico `tcpip 5555`** — S4/S3. **DESCARTAR**: é outro
   caminho (sem código de pareamento, porta fixa); o nosso
   (pareamento + porta efêmera + mDNS) é o certo para o Android
   13. Não misturar.
5. **Sessões one-shot: criar, executar, encerrar; matar processos
   velhos** — S2. **ADAPTAR**: nosso equivalente é `adb
   disconnect` ao fim da janela e nada de servidor parado no PC;
   Appium não entra.

### Espera e sincronização

6. **Polling até o estado esperado com timeout (`wait-text`,
   `wait` 30 s) em vez de sleeps fixos** — S2. **ADAPTAR**: nosso
   fluxo usa sleeps fixos; evoluir para "poll por marcador"
   (screencap + procurar o texto/estado esperado) com timeout,
   mantendo sleep só como piso.
7. **Sleep de 2–3 s após ações antes de reler (a tela pode ainda
   estar animando)** — S2. **ADOTAR**: tornar explícito na rotina.

### Localização e interação sem UI dump

8. **Screencap por streaming (`adb exec-out screencap -p`), nada
   escrito no `/sdcard`** — S2, S4. **ADOTAR**: substitui nosso
   `screencap -p /sdcard + pull`; mais rápido e sem arquivo
   sobrando no telefone.
9. **Re-verificar após CADA ação que a tela realmente mudou** —
   S2. **ADOTAR**: já fazemos re-screencap após cada tap;
   formalizar como "verificar a mudança, não só uma imagem nova".
10. **Árvore de acessibilidade como olho quando o screencap é
    preto ou o dump falha** — S2. **ADAPTAR**: o dump do
    uiautomator2 passa pelo serviço de acessibilidade, mecanismo
    diferente do `uiautomator dump` de shell (que retorna nó nulo
    no nosso S10). Vale um teste controlado; instalar o atx-agent
    no telefone precisa de aprovação do usuário.
11. **Tap no centro do bounds** — S3, S4. **ADOTAR**: já é nossa
    prática; manter.
12. **Listas virtuais mentem (bounds colapsados, h=6 px, não
    respondem); usar OCR/marcadores e padrões de swipe** — S2.
    **ADAPTAR**: o Feed do Facebook é uma lista virtual — antes
    de cada tap num item, reler a tela e se reancorar com
    marcadores visíveis; o padrão `jump` (3 swipes grandes rápidos
    + micro-swipes de volta) entra como saída quando a lista
    "pula" a seção.
13. **`d.click` (uiautomator2) entrega toques onde o `adb input
    tap` cru é filtrado** — S2. **ADAPTAR**: manter o tap cru como
    primário (provado no Feed/Stories); documentar o clique via
    u2 como fallback se um tap algum dia não produzir efeito.
    Exige o mesmo teste/aprovação do item 10.
14. **`monkey` para abrir apps** — S3. **ADAPTAR**: só como
    fallback de abertura; preferir `am start` determinístico com
    componente explícito.

### Digitação

15. **Clipboard + long-press + Colar para texto não-ASCII onde a
    troca de IME é bloqueada** — S2. **ADAPTAR**: o candidato
    mais promissor para o nosso problema de digitação:
    `d.set_clipboard(texto)` + long-press no campo + tocar em
    Colar. Testar em sessão controlada no teclado Samsung; limpar
    o campo antes (colar sobre texto existente concatena — a
    skill bateu nisso).
16. **ADB Keyboard por broadcast `ADB_INPUT_B64`** — S4.
    **ADAPTAR** como segunda alternativa: exige instalar APK +
    trocar o IME (`ime set`) — mudança mais pesada, precisa de
    aprovação; e a troca de IME é justamente o que falha em
    aparelhos travados (S2), e no nosso S10 as chamadas de
    settings já falharam com `INTERACT_ACROSS_USERS`. Tentar o
    item 15 primeiro.
17. **`input text` com `%s` para espaços** — S3. **DESCARTAR**:
    já resolvemos espaços com `keyevent 62`; `%s` não resolve
    não-ASCII.

### Higiene, retries e diagnóstico

18. **Um comando → um arquivo, log de sucesso/falha por comando,
    resumo final** — S1. **ADOTAR**: formalizar o resultado por
    passo (ok/falha) no log da sessão.
19. **`logcat -d` (~1000 linhas) + `dumpsys` na falha;
    `bugreport` em segundo plano** — S1. **ADAPTAR**: numa janela
    com falha, capturar `logcat -d` + `dumpsys battery/wifi/power`
    como diagnóstico; não rodar `bugreport` de rotina (pesado).
20. **`dumpsys window | grep mCurrentFocus|mFocusedApp` para
    confirmar o app em foco** — S4. **ADOTAR**: implementar o
    gate "app em foco" com esse comando, em vez de inferir só
    pelo screencap.
21. **`dumpsys battery/connectivity/wifi/power`, `usagestats`,
    `boot_count`** para saúde — S1. **ADOTAR**: bateria/rede já
    fazem parte dos nossos checks; acrescentar `boot_count` como
    sinal barato de "o telefone reiniciou?".
22. **Classificar o stderr da falha (autorização / rede / estado
    tcpip)** — S4. **ADOTAR**: nossa taxonomia de falha deve
    incluir a causa do lado ADB (não autorizado vs offline vs sem
    rota), não só o sintoma.
23. **Sem tempestade de retries: após 2 falhas do mesmo passo,
    trocar de estratégia ou parar a janela** — S2. **ADAPTAR**:
    nossa regra "sem rajadas" já cobre; explicitar o limite de 2
    tentativas idênticas.

### Segurança da conta / anti-detecção

24. **Ritmo humanizado, um passo por vez, confirmar antes de
    ações irreversíveis** — S2. **ADOTAR**: já é nossa regra; as
    fontes confirmam como melhor prática da comunidade, não só
    cautela nossa.
25. **Higiene de screenshots: diretório privado 0700, expurgo
    automático >1 h, nada no `/sdcard`, nunca ecoar o texto
    digitado (só o tamanho)** — S2. **ADOTAR**: nossas capturas
    já vivem na VM/PC; formalizar o expurgo do lado do telefone
    (já apagamos após checar) e nunca registrar texto digitado.
26. **Servidores de automação só em loopback; parar ao
    terminar** — S2. **ADAPTAR**: vale para qualquer daemon futuro
    no PC; o equivalente nosso é nunca expor a porta ADB ou um
    servidor de controle além de localhost/Tailscale, e
    desconectar ao fim da janela.
27. **Dependências com versão fixada** — S2. **ADOTAR**:
    qualquer ferramental Python que adicionarmos (u2, OCR)
    precisa de versões fixadas.

## Contradições com nossa prática atual (resolvidas pela análise)

- **S3/S4 mandam usar `uiautomator dump` para achar
  coordenadas.** Contradiz nossa realidade observada (dump
  retorna nó raiz nulo no S10/Facebook). Julgamento: as fontes
  descrevem o caminho padrão; nosso aparelho/app é a exceção.
  Nosso screencap-only está certo para este caso; o que vale
  testar é o dump via serviço de acessibilidade (item 10), não o
  dump de shell.
- **S3/S4 dizem "sleep entre comandos" e a S2 diz "poll até o
  estado esperado".** Julgamento: a S2 está certa para robustez;
  sleep fixo é piso, não mecanismo de sincronização. Evoluir para
  poll por marcador (item 6).
- **S4 usa `tcpip 5555`; nós usamos pareamento do Android 11+.**
  Julgamento: o modo da S4 é o caminho antigo e menos seguro; o
  nosso está correto. Não rebaixar.
- **S1 extrai contatos/SMS/call logs.** Contradiz nossa regra de
  nunca guardar dado de comprador — e é bloqueado no Android 11+
  via ADB sem root. Adotar só a metade de diagnóstico, nunca a
  de extração.
- **S2 diz que o `adb input tap` cru é filtrado (UC WebView) e não
  confiável.** Nossa experiência prova o contrário no Facebook
  (Feed/Stories publicados). Julgamento: a falha é específica de
  apps com UC WebView; o app do Facebook é nativo. Manter o tap
  cru como primário, u2 como fallback.
- **S2 manda "tentar o loop de OCR primeiro, Appium só como
  fallback".** Não temos loop de OCR; nosso equivalente funcional
  é o Muse lendo o screencap com visão. O aprendizado se
  transfere sem a dependência de OCR.

## O que não foi verificado

- **S3 como publicada tem só 60 linhas** — não há SKILL.md com
  scripts acessível a partir da página; tratada como referência
  curta.
- **SKILL.md completa da S4**: a página do skills.sh mostra só o
  resumo; conferido o conteúdo pelo espelho em
  claudemarketplaces.com e por dois forks que citam os mesmos
  comandos. O repositório httprunner/skills em si não foi aberto.
- **Se o atx-agent do uiautomator2 instala e funciona no S10
  (Android 13, Samsung)** — não testado; precisa de teste
  controlado com aprovação do usuário.
- **Se clipboard + long-press + Colar funciona no teclado Samsung
  dentro do compositor do Facebook** — não testado; precisa de
  teste controlado.
- **Precisão do RapidOCR em texto PT-BR** — não verificada;
  irrelevante no curto prazo, porque nosso fluxo usa a visão do
  Muse sobre o screencap.
