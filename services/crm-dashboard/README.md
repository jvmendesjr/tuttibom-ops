# CRM TuttiBom — dashboard só leitura no Chatwoot

Página do CRM próprio para embutir no Chatwoot (dashboard app, iframe).
Mostra os leads do CRM vivo agrupados pelas 7 etapas do funil, com
produto/SKU (+ preço), interesse, **estágio da prévia** (`pendente` /
`entregue em <data> · <ref>` / `—` sem pedido, desde 0.2.0), próxima
ação, data de follow-up, resumos de mensagens e memória do contato —
mais o resumo do catálogo (18 produtos) e os follow-ups pendentes.

## O que faz / o que não faz

| Faz | Não faz |
|---|---|
| `GET /` — página HTML estática por request (recarregar = refresh) | Nenhuma escrita: sem botão, sem endpoint de escrita |
| `GET /health` — JSON `{"ok": true, ...}` (aberto, sem token) | Não responde, não envia, não altera lead nenhum |
| Lê o SQLite em modo read-only (`mode=ro`, timeout 10 s) | Não abre o DB vivo em modo escrita, nunca |
| Escapa todo valor vindo do banco (`html.escape`) | Sem JavaScript que faça requisições; sem CDN/dependência externa |

Qualquer outro método (POST/PUT/DELETE) → 405. Qualquer outro path → 404.
Se o DB falhar ao ler → 503 com mensagem simples (nunca stack trace).

## Arquivos

| Arquivo | O que é |
|---|---|
| `dashboard.py` | Servidor HTTP próprio, só stdlib, porta 3022 |
| `test_dashboard.py` | Testes (unittest, stdlib) — sobe o servidor com DB de teste |
| `crm-dashboard.service` | Unit systemd |
| `.env.example` | Modelo do `.env` (o `.env` real nunca entra no git) |

## Token (autenticação)

A página NÃO é pública: o CRM tem dado de comprador. `GET /` exige
`?token=<TOKEN>`; sem token ou token errado → 401, sem revelar nada.

- O token vive SÓ em `/home/pc/chatwoot/crm-dashboard/.env`
  (`CRM_DASHBOARD_TOKEN=<valor>`, chmod 600, fora do git — o
  `.gitignore` do repo já cobre `.env`).
- O serviço lê o `.env` na inicialização e SE RECUSA a subir sem ele
  (nunca há token padrão).
- Gerar no PC, sem nunca imprimir o valor (o comando escreve direto
  no arquivo):

```sh
mkdir -p /home/pc/chatwoot/crm-dashboard
python3 -c "import os, secrets; d='/home/pc/chatwoot/crm-dashboard'; open(os.path.join(d,'.env'),'w').write('CRM_DASHBOARD_TOKEN='+secrets.token_urlsafe(32)+'\n')"
chmod 600 /home/pc/chatwoot/crm-dashboard/.env
```

- Trocar o token: gere um novo no `.env`, atualize a URL no registro
  do dashboard app do Chatwoot e reinicie o serviço
  (`sudo systemctl restart crm-dashboard`). O token antigo morre no restart.

### Tradeoff: token na URL

Quem tiver a URL completa (com o token) vê o CRM — é o preço da
autenticação por query param, que é o que o iframe do Chatwoot
permite (não há como mandar header). Por isso o token é longo e
aleatório (`secrets.token_urlsafe(32)`), a URL só vive em dois
lugares (o `.env` e o registro do dashboard app no Chatwoot) e
nunca vai para chat, log, arquivo versionado ou print. O acesso
também passa pelo túnel do Chatwoot, não é uma porta pública
direta. Se a URL vazar, troque o token (acima) — é um comando só.

## Porta e deploy

- **Porta:** 3022 (livre — verificado antes do deploy; 3020 é a ponte
  Zernio, 3021 é o ana-listener).
- **Deploy:** `/home/pc/chatwoot/crm-dashboard/` (código espelhado do
  repo; o `.env` vive lá, fora do git). Unit em
  `/etc/systemd/system/crm-dashboard.service`:

```sh
rsync -av --no-owner --no-group -e "ssh -F /home/hatch/.ssh/config" \
  services/crm-dashboard/ pc:/home/pc/chatwoot/crm-dashboard/
# no PC:
sudo systemctl daemon-reload && sudo systemctl enable --now crm-dashboard
```

- **Verificar:** `systemctl status crm-dashboard` (`active`),
  `curl http://127.0.0.1:3022/health` (200, sem token),
  página `/` com o token lido do `.env` dentro do comando no PC
  (conferir só o status 200 e que o HTML contém "CRM TuttiBom").

## Testes

```sh
python3 -m unittest discover -s services/crm-dashboard -p 'test_*.py' -v
```

Cobre: GET / com token (200, com os dados), sem token e com token
errado (401), /health aberto (200), POST / (405), path desconhecido
(404) e escape de HTML nos valores do banco.
