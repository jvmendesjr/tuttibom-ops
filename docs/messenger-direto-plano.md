# Messenger direto — plano de migração (V5)

**Decisão:** usuária, 2026-11-22 ~22:38 — adaptador próprio do Messenger
(V5, independência do Deskcomm). **Status:** PARKED 2026-11-22 ~22:55 —
usuária sem empresa formalizada (sem CNPJ); a revisão da Meta (Business
Verification) é inviável, então o caminho direto ficaria restrito a
testers; o Zernio segue como canal do Messenger do público. Fase B
cancelada; fase A (plano + token) fica como registro.

**Objetivo:** tirar o Zernio do caminho do Messenger e ligar a Página
"TuttiBom" direto ao Chatwoot, sem passar pelo Deskcomm.

## 0. Estado atual (verificado 2026-11-23 ~01:50)

| Peça | Estado |
|---|---|
| Messenger hoje | Ponte `zernio-bridge` (systemd, porta 3020) traduz webhooks do Zernio → API do Chatwoot, inbox 2 "Messenger" (`Channel::Api`) |
| Página | "TuttiBom", id canônico `100089750066330` (id no Zernio `143473822920252`, mesma página). Perfil pessoal "TuttiBom Novidade" NÃO é Página e não conecta — não tocar |
| Conta Meta for Developers | `tutibom10@gmail.com`, **sem app criado** |
| Chatwoot | `v4.20.1-ce`, `https://chatwoot.petemcasa.com`; `.env` já tem `FB_APP_ID`, `FB_APP_SECRET` e `FB_VERIFY_TOKEN` — os três **vazios** (o `FB_VERIFY_TOKEN` foi gerado nesta fase A, ver §4) |
| Rota do webhook nativo | `mount Integrations::Facebook::WebhookServer, at: 'bot'` (`routes.rb:748`) — `GET /bot` existe (200) e `/webhooks/facebook` dá 404. **Callback URL é `https://chatwoot.petemcasa.com/bot`** |
| Atendimento | Ouvinte (3021) + hook de 60 s + cumprimento + follow-up + handoff + ignorados — lê `message_created` da conta, **não filtra por inbox**. O inbox novo entra no fluxo sem mudar nada nele. Inbox 1 (WhatsApp/WAHA) não é tocado |
| Deskcomm | Continua recebendo webhooks do Zernio (endpoint de reserva, main congelada) — **não apagar** |

## 1. Desenho escolhido: canal nativo do Chatwoot + app Meta próprio

**Por quê (verificado no código 4.20.1-ce em execução):**

- O Chatwoot já gerencia tudo do canal: token da página (troca por
  token longo em `callbacks_controller.rb`), inscrição da página no
  webhook, envio pelo Graph API, `message_echoes` (não duplica a
  resposta do agente), entregas/leituras e reautorização do token.
- O envio (`send_on_facebook_service.rb`) usa `merge_human_agent_tag`
  — dentro da janela de 24 h manda `RESPONSE` sem tag; fora dela, só
  põe `HUMAN_AGENT` se quem envia é um usuário humano. **Não há mais o
  `ACCOUNT_UPDATE` que a Meta passou a rejeitar com erro 100 em
  2026-04-27** (issue Chatwoot #14674, corrigido antes da 4.20.1).
- A gem `facebook-messenger 2.0.1` chama o Graph com versão `v3.2`
  fixa. A Meta **não rejeita** chamadas a versões antigas: pelo guia
  de versionamento, chamadas a uma versão fora de uso são servidas na
  versão mais antiga ainda suportada. O teste vivo (§5) é a prova —
  se o envio falhar com erro de versão, o conserto é um patch pequeno
  (um initializer reabrindo a gem com a versão atual), não um serviço
  novo.

**Por que NÃO um serviço próprio (webhook → Graph API → API do
Chatwoot):** ele reimplementaria token, inscrição, envio, echoes,
entregas, contatos e anexos — e precisaria do **mesmo** app Meta, das
**mesmas** permissões e da **mesma** revisão do app. Não evita nenhum
portão da Meta. Só se justificaria se o canal nativo estivesse quebrado
— e ele não está (verificado acima; o teste vivo confirma).

## 2. O portão da Meta — ler antes de começar

Isto é o que decide o cronograma, não o código:

- **O app nasce em modo Development.** Nesse modo, só pessoas com um
  papel no app (admin, desenvolvedor, tester) conseguem mandar
  mensagem para a Página e ter a mensagem entregue no webhook.
- **Para o público em geral:** é preciso **App Review** com
  **Advanced Access** a `pages_messaging` (+ `pages_manage_metadata`,
  `pages_show_list`, `pages_read_engagement`) e depois mudar o app
  para **Live**. A revisão exige: verificação da empresa (Business
  Verification, com documentos da empresa), URL de política de
  privacidade, categoria, instruções de exclusão de dados e um
  **screencast de 2–5 min** mostrando o fluxo completo (cliente manda
  mensagem → aparece no Chatwoot → agente responde → resposta chega
  no Messenger), além de credenciais de teste para o revisor.
- **Ponto de atenção — verificar com a usuária:** a Business
  Verification pede documentos de empresa (CNPJ/registro e
  comprovante). Se o TuttiBom não tem empresa formalizada, a revisão
  pode travar — nesse caso, o caminho direto fica limitado a testers
  até isso se resolver, e o Zernio segue como canal do público.
- **O teste vivo com a Gleiciane NÃO precisa da revisão:** basta
  adicioná-la como **Tester** do app (ela aceita o convite nas
  notificações do Facebook). Isso prova a tubulação ponta a ponta.
  Mas prova só isso: **o público só passa a funcionar depois da
  revisão + Live**. Não prometer o contrário.
- A Página precisa estar **publicada** e com mensagens ativadas
  (a TuttiBom já está — recebe mensagens pelo Zernio hoje).

## 3. Passo a passo — console da Meta (cliques da usuária)

Fazer em `https://developers.facebook.com` logada como
`tutibom10@gmail.com`. Nada aqui precisa do Muse; não tente logar
como ela.

**3.1. Criar o app**

1. "Create App" (ou "Criar aplicativo").
2. Caso de uso: **Business** (se aparecer "Other" antes, escolha
   "Other" e depois "Business", como no guia do Chatwoot).
3. Nome do app: `TuttiBom Chatwoot` (sugestão — o nome aparece só
   no console, não para os clientes). E-mail de contato: o da loja.
4. Criar. Anotar o **App ID** (fica em App Settings → Basic).

**3.2. Configurações básicas do app (App Settings → Basic)**

1. **App Domains:** `chatwoot.petemcasa.com`.
2. **Privacy Policy URL** e **Terms of Service URL**: preencher com
   as URLs públicas da loja (se não existirem, criar uma página
   simples — a revisão exige; para o teste com a Gleiciane não é
   preciso, mas sem isso o app não vai para Live depois).
3. **Category:** Business and Pages (ou a mais próxima).
4. **Data Deletion Instructions URL:** preencher (ou callback).
5. **App Secret:** em App Settings → Basic, clicar "Show" e copiar.
   **Não colar no chat.** Guardar para a fase B (§4).

**3.3. Adicionar o produto Facebook Login**

1. No painel do app: "Add Product" → **Facebook Login** → "Set Up".
2. Em Facebook Login → Settings:
   - **Web OAuth Login:** ON.
   - **Login with JavaScript SDK:** ON.
   - **Allowed Domains for the JavaScript SDK:**
     `chatwoot.petemcasa.com`.
   - Salvar. (Não é preciso preencher "Valid OAuth Redirect URIs":
     o Chatwoot usa o SDK de JS para conectar a Página.)

**3.4. Adicionar o produto Messenger e o webhook**

1. "Add Product" → **Messenger** → "Set Up".
2. Em Messenger → Settings, seção de webhooks:
   - **Callback URL:** `https://chatwoot.petemcasa.com/bot`
   - **Verify Token:** o valor de `FB_VERIFY_TOKEN` — ele já foi
     gerado e está no `.env` do Chatwoot no PC. Ver no terminal do
     PC com:
     `grep FB_VERIFY_TOKEN /home/pc/chatwoot/.env`
     (não colar o valor no chat nem em documento).
   - Clicar "Verify and Save". Se der erro de verificação, parar e
     avisar o Muse — o Chatwoot ainda não foi reiniciado com o token
     (isso é da fase B, §4), então a verificação **só passa depois**
     da fase B. A ordem certa é: criar o app e os produtos agora;
     a verificação do webhook acontece na fase B, com o Chatwoot já
     reiniciado.
3. **Versão da inscrição do webhook:** 17.0, se oferecida; senão, a
   mais antiga disponível (guia do Chatwoot).

**3.5. Conectar a Página e assinar os eventos (teste)**

1. Em Messenger → Settings, "Add or remove pages": conectar a
   Página **TuttiBom** (a Página, não o perfil Novidade).
2. Na Página conectada, "Add subscriptions" e assinar:
   `messages`, `messaging_postbacks`, `message_deliveries`,
   `message_reads`, `message_echoes`. Salvar.
3. **Adicionar a Gleiciane como Tester:** App Settings → Roles →
   Testers → "Add Testers" → buscar a Gleiciane pelo nome/perfil do
   Facebook → enviar. Ela precisa **aceitar o convite** nas
   notificações do Facebook dela. Sem isso, a mensagem de teste dela
   não chega no webhook em modo Development.

**3.6. O que passar para o Muse quando terminar**

- App ID e App Secret — **nunca no chat**: digitar no terminal do
  PC com `read -s` (o Muse passa os comandos na hora) ou pelo cofre.
- Confirmação de que: app criado (tipo Business), produtos Facebook
  Login + Messenger adicionados, Página TuttiBom conectada, campos
  assinados, Gleiciane adicionada como Tester e convite aceito.

## 4. Fase B — conexão (Muse, depois do §3)

1. Preencher `/home/pc/chatwoot/.env`: `FB_APP_ID` e
   `FB_APP_SECRET` com os valores do app (via `read -s` no PC,
   nunca no chat). `FB_VERIFY_TOKEN` já está preenchido (fase A).
2. Reiniciar o Chatwoot recriando os contêineres (`docker compose
   up -d` — `restart` **não** recarrega o `.env`).
3. Verificar o webhook: `GET /bot?hub.mode=subscribe&hub.challenge=TESTE&hub.verify_token=<valor>`
   tem que devolver `TESTE` no corpo; com token errado, não pode
   devolver o challenge. Checar local (`127.0.0.1:3001`) e público
   (`https://chatwoot.petemcasa.com/bot`).
4. Criar o inbox no Chatwoot (UI): Settings → Inboxes → Add Inbox →
   Facebook → login com o Facebook → escolher a Página **TuttiBom**
   → nome `Messenger (direto)` (o inbox 2 já se chama "Messenger";
   renomear depois do corte).
5. Confirmar a inscrição da Página no app: a criação do inbox pede
   a inscrição via API; conferir em Messenger → Settings que a
   Página segue conectada e os 5 campos assinados.
6. **Parar a ponte temporariamente** (`systemctl stop
   zernio-bridge`) durante o teste, para a mesma mensagem não
   chegar duplicada (ponte + nativo). Se o teste falhar, religar a
   ponte na hora — nada se perde.
7. Teste vivo com a Gleiciane (§5).

## 5. Teste vivo (prova do corte)

1. Gleiciane manda "Olá" no Messenger para a Página TuttiBom.
2. A mensagem tem que chegar no Chatwoot **no inbox novo**
   ("Messenger (direto)"), **sem passar pelo Zernio** (conferir no
   log da ponte parada e no `/stats` do ouvinte).
3. O ouvinte enfileira, o hook acorda em ~60 s, a Ana responde pelo
   Chatwoot e a resposta chega no Messenger da Gleiciane.
4. Medir: hora do "Olá" → hora da chegada no Chatwoot → hora da
   resposta da Ana → confirmação da entrega no Messenger.
5. Critério de passa: ida e volta completas pelo caminho direto, com
   a resposta entregue. Latência alvo: cumprimento ~10 s, resposta
   completa 1–2 min (o gargalo hoje é o acordar, não o canal).

## 6. Corte (só depois do §5 passar)

1. **Desligar a ponte:** `systemctl disable --now zernio-bridge`
   (arquivos e `bridge.db` ficam no PC; o endpoint
   Zernio→Deskcomm continua existindo como reserva e **não** é
   apagado).
2. Renomear o inbox novo para "Messenger" e **apagar o inbox 2**
   (o antigo, `Channel::Api`) depois de alguns dias de uso — ou
   apagar na hora se a usuária preferir. Enquanto o inbox 2 existir
   sem a ponte, ele só fica vazio.
3. Atualizar `skills/chatwoot-operacao/SKILL.md` e
   `docs/ana-chatwoot-configuracao.md` com o novo caminho
   (inbox novo, webhook `/bot`, app Meta) e a reversão (§7).
4. Commit + push no branch desta migração.

## 7. Reversão (voltar para a ponte)

1. `systemctl enable --now zernio-bridge`.
2. No console da Meta, manter ou remover a inscrição da Página no
   app novo (se remover, o nativo para de receber; se mantiver e a
   ponte também estiver ligada, a mensagem chega duplicada — não
   deixar os dois ligados).
3. As conversas do inbox novo ficam no Chatwoot (histórico
   preservado); as novas voltam a cair no inbox 2.
4. Se o inbox 2 foi apagado, recriá-lo não é preciso: a ponte cria
   a conversa via API no inbox que existir — verificar na hora.

## 8. Riscos e pendências

- **Business Verification / CNPJ:** a revisão do app pode pedir
  documentos de empresa. Verificar com a usuária se o TuttiBom tem
  empresa formalizada; se não tiver, o caminho direto fica restrito
  a testers até lá.
- **Screencast da revisão:** gravar o fluxo completo quando for
  pedir a revisão (a prova do §5 serve de base).
- **Versão do webhook:** se 17.0 não for oferecida na criação da
  inscrição, usar a mais antiga disponível.
- **Janela de 24 h:** respostas fora da janela de 24 h da última
  mensagem do cliente seguem a regra do `HUMAN_AGENT` (só para
  envio por humano); o atendimento já opera dentro da janela nos
  testes.
- **Duplicata durante a transição:** nunca deixar ponte e nativo
  ligados ao mesmo tempo para a mesma Página.

## 9. O que NÃO muda

- Atendimento: ouvinte (3021), hook de 60 s, cumprimento,
  follow-up, handoff, ignorados — nenhum deles filtra por inbox.
- Inbox 1 WhatsApp (WAHA), Deskcomm, Ana v12-B pausada, CRM vivo
  (só leitura neste trabalho), `cloudflared-ponte` (não reiniciar).
- Nenhum segredo em git, log ou chat: App Secret e tokens só no
  `.env` do PC (chmod 600) e no console da Meta.
