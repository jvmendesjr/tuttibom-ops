# Protótipo visão do Jev — relatório (2026-11-15)

Caminho padrão: print → Jev Box → clique. Modelo fixo `jev-1.14.0`.
Núcleo único `jev_navigate.py` (Noul + Choice + Box num só pedido; portão
noul ≥ 0,5, count == "one", confiança ≥ 0,6; zoom = recorte de metade do
tamanho centrado na caixa, re-pergunta, mapeia de volta).

## Upgrade do Jev (PC)

- `hermes-jev-skills` 0.19.0 → **0.25.3** (cópia cirúrgica do plugin:
  `hermes/plugin/hermes-jev` + `jevkit/` da tag v0.25.3; instalador completo
  não usado para não tocar perfis/skills/scripts).
- Backup da 0.19.0 em `/home/pc/.hermes/plugins/hermes-jev-0.19.0-backup-20261115`.
- Verificado: `jev --version` 0.25.3; `jev doctor` chave presente, Jev
  alcançável (292 ms); `jev ask` fumaça ok (noul 0,46, 285 tokens, 313 ms).
- Visão: `scripts/live_images_check.py` exit 0 — Box IoU 0,834, confiança
  0,96, 1.162 tokens, 202 ms, modelo `jev-1.14.0`.

## Painel Deskcomm — Playwright Chromium headless (1280×800)

Página testada: `https://deskcomm.petemcasa.com/login` (sem login; só localizar
e clicar em campos, sem digitar e sem enviar).

- **Baseline:** DOM completo 42.490 caracteres ≈ **10.623 tokens**; print PNG
  16.048 bytes; captura ~3,2–3,7 s.
- **Precisão (10 alvos, verdade do DOM): 9/10 = 90%** — limiar 0,6 mantém
  10/10 com 9 acertos; limiar 0,9 mantém 4/10, todos acertos.
  Média **3.076 tokens/localização**, **213 ms**.
- **Único erro:** rótulo "Email" (34×14 px) — centro (499, 284) fora dos
  limites (x 448–482, y 265–279). Zoom: (467, 280) — corrige x, fica 1 px
  abaixo da borda inferior. Alvos < 20 px de altura seguem no limite do Box.
- **Tarefa roteirizada 2/2 verificada:** localizar campo de e-mail → clicar
  → foco confirmado em `input#email`; localizar campo de senha → clicar →
  foco confirmado em `input#password`. Sem digitar, sem enviar.
- **Portões (§8):** precisão ≥ 85% ✓ (90%); tokens/passo < baseline do dump ✓
  (3.076 < 10.623). **Painel APROVA os portões.** Ressalva honesta: o Box
  ganha do dump completo do DOM, mas uma tabela DOM podada (150–300 tokens)
  continua mais barata — visão é o caminho para o que o DOM não resolve
  (fluxos só de UI, verificação visual), não o substituto universal do DOM.

## ADB (S10) — BLOQUEADO, aguardando o usuário

- `adb devices` vazio em 2026-11-15 ~21:30. O endereço de depuração sem fio
  muda a cada reativação; a skill proíbe varrer portas. **Falta o endereço
  novo mostrado na tela do telefone** (Configurações → Opções do
  desenvolvedor → Depuração sem fio) para conectar e rodar a metade ADB
  do protótipo (baseline do `uiautomator dump`, 10 alvos na tela inicial,
  zoom, tarefa roteirizada sem tocar na conta da loja).

## Facebook via Camofox original — teste sem login APROVADO (2026-11-15 ~22:06)

- **Decisão do usuário:** Camoufox original (motor), navegação simulada,
  autenticação persistente, mouse e tempo humanizados, sem ações em massa,
  sem modificar o Camofox; todo print passa pelo Jev. Regra S10-principal
  suspensa para este teste; acompanhar e-mail e avisos do Facebook e pausar
  a qualquer alerta de suspeita de bot.
- **Driver `camofox_driver.py`** (venv próprio): perfil persistente
  `profile-fb/`; impressão digital FIXA gerada uma vez e reutilizada
  (`profile-fb/fingerprint.json`); `humanize=True` do próprio Camoufox;
  pausas 1,2–4 s entre ações, 5–10 s de leitura; `headless=False` no
  **Xfce :0 real** (compositor/GPU/janelas reais — o mais próximo de humano;
  o Xvfb virtual fica como reserva); geoip alinhado ao IP; `i_know_what_im_doing=True`
  (a impressão fixa é intencional).
- **VNC para o usuário ver:** `x11vnc` no :0, só Tailscale (`<TAILSCALE_IP>:5900`)
  e LAN (`<LAN_IP>:5900`), sem senha, `-allow <TAILSCALE_CIDR>,<LAN_CIDR>`;
  teste de fora da rede não alcançou o servidor (roteador bloqueia a IPv6 pública).
- **Teste sem login (`fb_test.py`, 2026-11-15 22:06):** facebook.com abriu sem
  checkpoint nem bloqueio; Jev localizou **3/3** (e-mail HIT conf 0,91,
  2.811 tokens, 354 ms; senha HIT conf 0,86, 2.798 tokens, 300 ms; botão
  Entrar localizado em (960, 353) conf 0,85 — o "MISS" registrado foi falha
  do seletor DOM de verdade, não do Jev; confirmado no print); clique no
  campo de e-mail com foco verificado (`input[name=email]`). Nada digitado,
  nada enviado, nenhum login tentado. Print em `fb-login.png`.
- **Falta:** o primeiro login (passo separado; credenciais uma vez via cofre).

## Painel Deskcomm no motor Camoufox — teste APROVADO (2026-11-16)

- **Decisão:** o usuário afirmou que o padrão das aplicações dele é o Camofox; testado o motor Camoufox no painel (trinômio agente+camofox+jev), com perfil separado `profile-panel/` (não toca o `profile-fb` do Facebook).
- **Login (2026-11-16 ~09:20, display virtual):** Jev 3/3 — e-mail noul 0,99 conf 0,85; senha noul 0,99 conf 0,87; botão Entrar noul 0,98 conf 0,88; clique no e-mail com foco confirmado (`INPUT#email`). Nada digitado, nada enviado. Nenhuma janela do painel apareceu na tela :0 real (segundo plano de verdade).
- **Parte logada (2026-11-16 ~09:26, display virtual):** usuário logou ~09:25 no Camoufox; reabertura do perfil caiu direto na tela de Tags já logada (sessão persistida); 11 etiquetas visíveis (3d, fita, preco); Jev localizou "Adicionar etiqueta" (noul 0,87, conf 0,82).
- **Padrão atualizado:** navegação do painel = motor Camoufox + Jev; Chromium headless fica como fallback. Scripts: `panel_camofox_test.py` (login), `panel_camofox_open.py` (abrir para o usuário logar), `panel_camofox_validate.py` (reabertura + localizar botão). Driver interativo do painel no Camoufox (equivalente ao `panel_drive.py` do Chromium, usado para criar as 3 tags da P7) ainda não construído — próximo passo se a navegação interativa for necessária.

## Arquivos

- `jev_navigate.py` — núcleo (prep, locate, zoom, log em `/tmp/jev_navigate.jsonl`)
- `panel_driver.cjs` — Playwright (probe/links/click)
- `run_panel_task.py` — tarefa roteirizada do painel
- Logs: `/tmp/panel-accuracy.json`, `/tmp/jev_navigate.jsonl`
