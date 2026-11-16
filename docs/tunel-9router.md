# Túnel do 9Router — diagnóstico 2026-11-05

> DIAGNÓSTICO, 2026-11-05 ~23:35. Somente leitura: nada foi
> criado, alterado ou ativado. Nenhum segredo lido ou registrado.
> A senha padrão do painel NÃO foi lida nem alterada — trocar é
> ação do usuário em Profile settings.

## 1. O que é o túnel do painel

- O túnel embutido do 9Router é um **Cloudflare quick tunnel**
  (trycloudflare.com), gerenciado pelo próprio 9Router: ele lança
  o `cloudflared`, grava `~/.9router/tunnel/state.json` e registra
  `tunnelEnabled` + `tunnelUrl` no banco do 9Router (`settings`).
- O túnel aponta para `http://127.0.0.1:20128`, onde roda o
  encaminhador `9router-tunnel-forward.mjs`, que repassa para o
  9Router em `127.0.0.1:20130` (a porta padrão do 9Router é 20128;
  esta instância roda em 20130).
- URL registrada (29/10): `https://policies-bunch-infectious-person.trycloudflare.com`
  (shortId `p4lpjv`).

## 2. Causa do "Tunnel checking..." — túnel morto

Evidências, todas conferidas em 2026-11-05 ~23:35:

- **A URL está morta:** não resolve no DNS (`getent` sem resposta)
  e o curl falha (não resolve o host). Confirmado no host.
- **O processo existe mas está desconectado:** o `cloudflared`
  (PID 3261196, rodando há 7 dias) não tem nenhuma conexão de rede
  — zero TCP (`ss -tnp`) e zero UDP (`ss -unp`, o QUIC do túnel).
- **O diretório de configuração sumiu:**
  `/tmp/cloudflared-quick-0ODTbs/` não existe mais — se o processo
  morrer, ele não consegue recarregar a configuração.
- **O aplicativo ainda acredita que o túnel está ligado:**
  `settings` tem `tunnelEnabled: true` com a URL de 29/10, e o
  `state.json` tem a mesma URL. O painel fica sondando o status do
  túnel e ele nunca fica saudável — por isso o "Tunnel checking..."
  em loop (o outro estado do painel é "Tunnel reconnecting...").
- **Causa provável:** a conexão do túnel rápido caiu (ou as
  tentativas se esgotaram) e nada o recriou — túnel rápido é
  efêmero por desenho, e o 9Router não recria sozinho um túnel
  rápido morto.

## 3. Por que o restart manual NÃO foi tentado

- O ciclo de vida do túnel pertence ao 9Router (PID file,
  `state.json`, `settings`). Matar e relançar o `cloudflared` na
  mão **não atualizaria a URL registrada** — o painel continuaria
  mostrando a URL morta de 29/10 como "checking".
- O restart correto pelo caminho do aplicativo é o botão do túnel
  no painel (ação do usuário), que cria um NOVO túnel rápido com
  uma NOVA URL aleatória. Isso limparia o "checking", mas **não
  resolve o Deskcomm**: a URL nova também é efêmera e muda a cada
  reinício — o Deskcomm precisa de URL estável.
- Por isso nenhum restart foi executado nesta sessão.

## 4. O botão "Ativar" do Tailscale

- **O que faz:** liga a integração própria do 9Router com o
  Tailscale (o CLI gerencia por `tailscale.pid`). Hoje está
  DESLIGADA — não existe `tailscale.pid` em `~/.9router/tunnel/`.
- **O serve já existe por fora do 9Router:** `tailscale serve
  status` mostra o `:20130` servido na tailnet, apontando para
  `127.0.0.1:20130`. Verificado do host: o endpoint MagicDNS
  responde **HTTP 401** — alcançável, atrás da autenticação do
  9Router (401 sem chave é o comportamento esperado; com chave
  válida responde 200).
- **Precisa ativar para o Deskcomm? NÃO.** A régua de saída do
  Deskcomm bloqueia IPs da faixa do Tailscale (100.64/10) e o nome
  MagicDNS não resolve dentro dos containers — confirmado na
  validação (`docs/validacao-9router-deskcomm.md`).
- **Precisa ativar para acesso pela tailnet? NÃO.** O acesso pela
  tailnet já funciona pelo serve existente (com chave de API).
  Ativar o botão só duplicaria o serve que já existe.

## 5. Proposta de correção — URL pública estável (para aprovar, não executado)

1. **Trocar a senha padrão do painel primeiro** (usuário, em
   Profile settings). O aviso está no painel e o acesso ao painel
   via túnel está LIGADO — não expor o painel com senha padrão.
2. **Criar um túnel nomeado do Cloudflare** (nome fixo), separado
   do túnel da Ponte — **não tocar no `cloudflared-ponte.service`**.
   Criação pelo painel do Cloudflare ou `cloudflared tunnel
   create` (precisa das credenciais do Cloudflare — ação do
   usuário).
3. **Rodar o `cloudflared` do túnel nomeado apontando direto para
   `http://127.0.0.1:20130`** (dispensa o encaminhador da porta
   20128 — um salto a menos).
4. **Desligar o túnel rápido embutido no painel do 9Router** quando
   o nomeado estiver funcionando, para não haver duas URLs.
5. **Verificar:** a URL pública responde `GET /v1/models`
   (200 com chave, 401 sem chave — ambos provam alcance), sem
   redirecionamento, nome estável.
6. **Depois, no Deskcomm:** criar a credencial custom com
   `base_url=<URL pública>/v1` + chave de API do 9Router; "Salvar
   e validar" precisa devolver 200 com o `core-medio` na lista;
   vincular à organização TuttiBom (`provider=custom`,
   `model_id=core-medio`); testar um turno real do agente.
7. **Revalidar a régua de saída contra a nova versão do Deskcomm**
   depois que a atualização direta em andamento pousar (a validação
   atual é pré-atualização, contra a 1.44.0).

## 6. O que NÃO foi feito

- Nenhum restart do túnel (ver seção 3).
- Nenhuma alteração de configuração do 9Router, da Ponte ou do
  Deskcomm. A atualização direta do Deskcomm em andamento não foi
  tocada.
- Nenhuma senha ou chave lida, alterada ou registrada.

## 7. Conector Cloudflare — pronto (2026-11-06 ~00:05)

Conector `custom.cloudflare` criado (token via fluxo seguro,
Bearer, host `api.cloudflare.com`). Doc em
`~/workspace/custom-connectors/custom.cloudflare/CONNECTOR.md`,
helper `bin/client.py` (só leitura: `list-zones`,
`list-tunnels`, `verify`). Verificação 2026-11-06: credencial
OK (a primeira chamada estourou o timeout de 30 s aguardando
a aprovação; o retry passou em ~2 s). Zonas (3): essencpet.com.br,
orbut.top, petemcasa.com. Túneis listáveis (4): flip (down),
gpu-llm (down), ponte-kiwify (healthy), tudiobom (down).

**Pronto para criar o túnel nomeado:** conector verificado,
zona petemcasa.com disponível, origem `http://127.0.0.1:20130`
confirmada. **Ainda falta:** (1) o usuário trocar a senha
padrão do painel do 9Router (Profile settings); (2) escolher
o hostname (ex.: subdomínio de petemcasa.com) e o nome do
túnel — notar que já existe um túnel chamado `tudiobom`
(down); verificar antes de criar se ele é o túnel do
TuttiBom parado ou só um nome parecido, para não duplicar;
(3) confirmar que o token tem as permissões de escrita
(Cloudflare Tunnel Write + DNS Edit) — até aqui só leituras
foram testadas. Nenhum túnel, registro DNS ou arquivo de
configuração foi criado nesta preparação.

## 8. Túnel nomeado CRIADO (2026-11-06 ~00:07)

Senha do painel trocada pelo usuário (confirmado ~00:03) —
pré-requisito cumprido. Conector `custom.cloudflare` verificado
antes (ver seção 7).

- **Túnel:** `9router`, id
  d534f40e-ae65-490e-a8c4-1dac696043dc, criado via API
  (`config_src: cloudflare`, gerenciado remotamente).
- **Hostname:** 9router.petemcasa.com → origem
  `http://127.0.0.1:20130` (ingress remoto + catch-all 404).
- **DNS:** CNAME 9router.petemcasa.com →
  d534f40e-ae65-490e-a8c4-1dac696043dc.cfargotunnel.com
  (proxied), criado via API.
- **Serviço no PC:** `cloudflared-9router.service`
  (systemd, system, enabled, `Restart=always`), separado do
  `cloudflared-ponte.service` (intacto, sem alteração). Token
  do túnel em `/root/.cloudflared/9router-token.env` (modo
  600, root); a cópia de trânsito na VM foi destruída
  (`shred -u`). O token nunca foi impresso nem registrado.
- **Verificação:** `GET /v1/models` na URL pública responde
  **401** sem chave (`{"error":"API key required for remote
  API access"}` — erro do próprio 9Router, prova o caminho
  completo: edge → túnel → cloudflared → 9Router), sem
  redirecionamento, medido da VM (1,1 s) e do PC (0,2 s);
  hostname resolve no DNS público; túnel `healthy` na API,
  4 conexões QUIC registradas no journal. O 200 com chave
  fica para o "Salvar e validar" da credencial no Deskcomm
  (a chave do 9Router nunca foi lida aqui).
- **Túnel `tudiobom` (down):** verificado antes de criar —
  NÃO é do TuttiBom: criado em 2026-05-20, ingress
  `tbssh.orbut.top -> ssh://localhost:22`. Não tocado.
- **Túnel da Ponte:** verificado intacto (`ponte-kiwify`,
  healthy, hostnames deskcomm/crm/webhooks.petemcasa.com).
  Nenhuma alteração no Deskcomm, na Ponte ou no 9Router
  além do túnel novo.

**Ainda falta:** (1) criar a credencial custom no Deskcomm
(`base_url=https://9router.petemcasa.com/v1` + chave de API
do 9Router) e vincular à organização TuttiBom
(`provider=custom`, `model_id=core-medio`), com teste de
turno real — após a atualização direta do Deskcomm em
andamento; (2) revalidar a régua de saída contra a nova
versão do Deskcomm; (3) confirmação visual do usuário no
painel do 9Router de que o túnel rápido aparece como
desligado (ver §9).

## 9. Túnel rápido embutido DESLIGADO via código (2026-11-06 ~00:21)

O toggle do painel não funcionava (tentativa do usuário).
O usuário autorizou desligar direto no código ("Você pode
entrar e fazer isso. Você mesmo. No código."). Desligado
pela própria API do aplicativo — o mesmo caminho que o
painel usaria: `POST /api/tunnel/disable` no loopback
(`http://127.0.0.1:20130`), autenticado com o token CLI do
app (`x-9r-cli-token`, derivado de `machine-id` +
`auth/cli-secret`, calculado no PC e nunca impresso nem
registrado). Resposta: `{"success":true}`.

**Onde o estado vive (confirmado antes de mudar):**
`settings` (tabela de linha única, id=1) no SQLite
`~/.9router/db/data.sqlite`, campo JSON `data`, chaves
`tunnelEnabled` e `tunnelUrl`; mais
`~/.9router/tunnel/state.json` e
`~/.9router/tunnel/cloudflared.pid`.

**Backup antes da mudança** (em
`~/.9router/backups/tunnel-disable-20261106-0021/`):
backup online do SQLite (`data.sqlite`) + cópias de
`state.json` e `cloudflared.pid`.

**Mudanças (antes → depois):**
- `settings.tunnelEnabled`: `true` → `false`.
- `settings.tunnelUrl`:
  `https://policies-bunch-infectious-person.trycloudflare.com`
  → `""` (vazio).
- `state.json`: `"tunnelUrl"` (a URL morta) → `null`
  (`shortId` mantido, `"p4lpjv"`).
- Processo órfão do túnel rápido (`cloudflared`, PID
  3261196, `--url http://127.0.0.1:20128 --config
  /tmp/cloudflared-quick-0ODTbs/config.yml`): encerrado
  pelo próprio app no disable. O diretório de config
  `/tmp/cloudflared-quick-*` já não existia.
- O status `/api/tunnel/status` refletiu a mudança sozinho
  em ~1 min (o monitor do app atualizou): `enabled: false`,
  `settingsEnabled: false`, `tunnelUrl: ""`,
  `running: false`. (Imediatamente após o disable o status
  ainda mostrava os valores antigos, em cache; sem restart
  do 9Router — não foi necessário.)
- `publicUrl` residual (`https://rp4lpjv.abc-tunnel.us`)
  continua no status como dado antigo; `enabled` e
  `running` em `false` é o que vale.

**Não tocado:** `cloudflared-9router.service` e
`cloudflared-ponte.service` (ambos ativos);
`cloudflared` do túnel nomeado (PID 1538842); processo
principal do 9Router (PID 3252479, sem restart);
forwarder `9router-tunnel-forward.mjs` (PID 3252890,
loopback :20128, sem uso pelo túnel nomeado — mantido,
inofensivo); senha do painel (nunca lida nem alterada);
dados de modelos/chaves do 9Router; Deskcomm (atualização
direta em andamento em outro agente, não tocada).

**Verificação (2026-11-06 ~00:21–00:22):**
- Loopback `GET http://127.0.0.1:20130/v1/models` → 200.
- Pública `GET https://9router.petemcasa.com/v1/models` →
  401 sem chave (prova que o túnel nomeado segue
  funcionando).
- `systemctl is-active cloudflared-9router.service
  cloudflared-ponte.service` → active, active.
- Restam só 2 processos `cloudflared`: Ponte (4552) e
  túnel nomeado (1538842).
