# Validação — 9Router como provider custom do Deskcomm

> VALIDAÇÃO, 2026-11-05 ~23:30. Somente leitura: nada foi alterado
> no Deskcomm, no `.env`, nos containers ou no 9Router. Nenhum valor
> de segredo foi lido ou registrado (sem chaves, sem tokens, sem
> endereços fixos neste documento — os endereços aparecem só como
> descrição do mecanismo).
>
> **PRÉ-ATUALIZAÇÃO:** todos os resultados abaixo foram validados
> contra o Deskcomm **1.44.0 em produção**. O usuário autorizou
> uma atualização direta do Deskcomm em 2026-11-05 ~23:22 (a
> produção só tem dados de teste). **Revalidar contra a nova versão
> depois que a atualização pousar** — em especial a régua de saída
> (item 3) e a existência do provider custom (item 4).

## Veredito

**NÃO PASSOU POR COMPLETO — bloqueado na base URL.** O mecanismo
está provado (provider custom existe no 1.44.0 em produção, o
`core-medio` passa direto no binding, a régua de saída foi lida no
código em produção), mas **hoje não existe nenhuma base URL
alcançável a partir dos containers do Deskcomm que passe na régua**.
A proposta mínima está no fim deste documento. O item (1) do
roadmap fica **por marcar**, com a nota do bloqueio.

## 1. Listeners do 9Router e modelos — PASS (com correção)

- **20128:** só em loopback (`127.0.0.1`), processo do
  `9router-tunnel-forward`.
- **20130:** só em loopback para o 9Router (`127.0.0.1`, serviço
  `9router`). **Correção ao que se supunha:** o listener na porta
  20130 do IP do Tailscale **não é o 9Router — é o próprio
  `tailscaled`** (Tailscale Serve, que proxya para o 9Router em
  loopback pelo nome MagicDNS do PC). O 9Router em si só escuta em
  loopback.
- **Modelos:** as duas instâncias servem a **mesma lista de 282
  modelos** (`GET /v1/models` a partir do host, sem autenticação).
  O combo **`core-medio` está servido** e resolve (lido do banco
  SQLite do 9Router, somente leitura) para a cadeia de fallback:
  `ag/gemini-3.8-flash-medium` → `ag/claude-sonnet-4-6` →
  `ag/claude-sonnet-5-5-medium`. Os três estão na lista servida.
- O listener na porta 20130 do IP de gateway Docker é o relay de
  desenvolvimento `egress_dev.py` do PQBR (não um endpoint do
  9Router — ver item 2).

## 2. Alcançável de dentro do container do Deskcomm — FAIL

Testado de dentro de `deskcommcrm-app-1` (imagem 1.44.0 em
produção, `Up 9 days, healthy`):

| Candidato | Resultado |
|---|---|
| loopback `:20128` | Conexão recusada (loopback do container) |
| IP de gateway Docker `:20130` | HTTP 401 — é o relay `egress_dev.py`, que exige autenticação própria (`via-relay`) e injeta segredo por requisição; ferramenta de desenvolvimento do PQBR, não um caminho para o Deskcomm |
| IP do Tailscale `:20130` | HTTP 400 ("requisição HTTP para servidor HTTPS") e o handshake TLS é recusado (alerta interno) até pelo curl do host — é o `tailscaled`, não o 9Router |
| Nome MagicDNS do PC `:20130` (https) | DNS não resolve dentro do container (o DNS do container é o do Docker, sem MagicDNS) |
| gateway da rede do Deskcomm `:20130` | Conexão recusada |
| URL pública do túnel rápido (registrada no estado do 9Router, de 29/10) | DNS não resolve nem no host nem no container — a URL está **morta** (o processo do túnel ainda roda, mas o nome não existe mais) |

Controle positivo: o container resolve e alcança `https://openrouter.ai`
normalmente — a saída pública do container funciona; o problema é
só que **não existe hoje nenhuma URL pública viva para o 9Router**.

## 3. Fiação do provider no 1.44.0 em produção — PASS, com correção

Confirmado no código **em produção** (marcadores presentes nos
chunks do servidor da imagem 1.44.0: `100.64`, `redirect_not_followed`,
`ai_purpose_bindings`, `Provedor personalizado`,
`platform_settings.internal_destinations`); a semântica abaixo foi
lida no fonte do checkout (ramo 1.20), que coincide com os
marcadores em produção:

- O provider **`custom`** existe: "Provedor personalizado (compatível
  com OpenAI)" — o catálogo cita nominalmente o **9Router** e exige
  "num endereço público".
- A allowlist **`platform_settings.internal_destinations`** existe
  em produção (linha `id=1`, cache de 30 s), editável em
  `/admin/destinos-internos`; o piso do `.env`
  (`IA_DESTINOS_INTERNOS_PERMITIDOS`) está **ausente** do `.env` vivo
  (só a presença foi checada).
- **Correção à suposição inicial: a allowlist NÃO autoriza a base
  URL de um provider custom.** Pela decisão 22-d, regra 2, a lista
  só vale para destino configurado pela **instalação**; um endereço
  escolhido por uma **organização** passa sempre pela régua
  completa — e a base URL do provider custom é por organização
  (`fetchParaDestinoDaOrganizacao`, com origem `"organizacao"`).
  Nenhuma entrada na allowlist ajuda aqui.
- A régua, aplicada no cadastro **e em cada chamada** do agente:
  texto (sem `localhost`/`127.`/`10.`/`192.168.`/`169.254.`/
  `172.16/12`; `https` obrigatório em produção; sem literal IPv6)
  **e** IP resolvido — que bloqueia as faixas especiais **incluindo
  `100.64/10` (CGNAT, a faixa do Tailscale)**. Ou seja: mesmo que o
  nome MagicDNS resolvesse dentro do container, o IP resolvido
  seria recusado. Redirecionamento não é seguido.
- O documento do recurso (`docs/features/provedor-personalizado.md`,
  no checkout) diz com todas as letras: um gateway na mesma máquina
  que o CRM "não entra por aqui".

## 4. Binding com `core-medio` — PASS (mecanismo)

- O binding mora em **`ai_purpose_bindings`** (por organização e
  por propósito: `provider`, `credential_id`, `model_id`, `base_url`,
  `is_enabled`); a credencial mora em **`ai_provider_credentials`**
  (`provider`, `label`, `base_url`, chave cifrada).
- Para provider `custom`, o `model_id` **passa direto, sem tradução**
  — o 9Router resolve o combo do lado dele. O binding seria:
  `provider=custom`, `model_id=core-medio`, `base_url=<URL pública>/v1`.
- O teste antes de salvar é `GET {base}/models` com a chave
  (`Bearer`), timeout de 10 s, sem seguir redirect. O 9Router
  responde `/v1/models` (200 a partir do host; com chave, conforme
  o README do 9Router). A lista devolvida incluiria o `core-medio`.
- **Item aberto para a implementação:** qual chave de API do
  9Router usar como credencial do Deskcomm (criar uma dedicada no
  painel do 9Router, ou reutilizar a chave do CLI pelo fluxo seguro
  — o valor nunca passa por aqui). O 9Router espera
  `Authorization: Bearer <chave>`; existe um segredo de CLI no
  diretório de autenticação do 9Router (só o nome do arquivo foi
  visto, o valor nunca foi lido).

## 5. Estado atual — PASS (no que dá para ler sem segredo)

- No container da aplicação em produção estão presentes (só os
  **nomes**): `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`,
  `OPENAI_API_KEY`, `AI_CRED_AES_KEY`. `OPENROUTER_BASE_URL` também
  está presente no `.env` vivo (só a presença; o destino continua
  sem resposta do usuário).
- O 9Router entraria **ao lado** do OpenRouter, como binding
  custom por organização (no caso, a futura organização TuttiBom);
  o OpenRouter continua sendo o padrão/fallback da instalação — se
  o binding faltar ou a chave falhar, o agente cai no padrão com
  aviso.
- Bindings/credenciais por organização no banco: **BLOQUEADO** —
  exigiria acesso ao Supabase com credencial, que não foi lido.

## Proposta mínima para ligar o 9Router (para aprovar, não executado)

1. **Publicar o 9Router numa URL pública estável em HTTPS**
   (a URL do túnel rápido está morta; criar um túnel nomeado do
   Cloudflare com nome fixo, ou outro reverse proxy público com
   certificado válido). Sem redirect; a URL deve responder
   `GET /v1/models`.
2. **Nenhuma entrada na allowlist** — ela não vale para base URL
   de organização e nenhuma entrada é necessária.
3. No Deskcomm, em **IA › Credenciais**, criar a credencial
   `custom` com `base_url=<URL pública>/v1` e a chave de API do
   9Router; rodar "Salvar e validar" (precisa devolver 200 com o
   `core-medio` na lista).
4. Vincular à organização TuttiBom para o propósito do agente:
   `provider=custom`, `model_id=core-medio`
   (`ai_purpose_bindings`).
5. Verificar com a prova de crédito / um turno real do agente.

Ordem: (1) antes de (3) — sem URL viva, a validação falha no
cadastro. Alternativa **não recomendada** como mínima: apontar o
`OPENROUTER_BASE_URL` da instalação para o 9Router desviaria o
tráfego de **todas** as organizações (inclusive a petemcasa) e
passa por fora da régua de organização — blast radius global.

## Divergências checkout × produção anotadas

- O código lido em detalhe é o checkout (ramo 1.20); a produção
  roda a imagem 1.44.0. Todos os marcadores verificados em
  produção (`100.64`, `redirect_not_followed`,
  `ai_purpose_bindings`, `Provedor personalizado`,
  `internal_destinations`) coincidem com o checkout — nenhuma
  divergência encontrada nos pontos checados.

## Adendo — túnel do 9Router (2026-11-05 ~23:35)

Diagnóstico completo em `docs/tunel-9router.md`. Resumo: o túnel
embutido (Cloudflare quick tunnel, URL de 29/10) está MORTO — a URL
não resolve, o processo `cloudflared` não tem conexões e o
diretório de configuração em /tmp sumiu; o aplicativo ainda registra
`tunnelEnabled: true`, por isso o painel fica em "Tunnel checking..."
em loop. Restart manual não foi tentado: o ciclo de vida do túnel
pertence ao 9Router e só o botão do painel atualizaria a URL
registrada — e criaria outra URL efêmera, que não serve ao Deskcomm.
O botão "Ativar" do Tailscale não é necessário: o serve da tailnet
para :20130 já existe por fora do 9Router (endpoint responde 401 do
host) e, para o Deskcomm, a régua bloqueia a faixa do Tailscale de
qualquer forma. Proposta: túnel nomeado do Cloudflare com nome fixo,
apontando direto para 127.0.0.1:20130, após trocar a senha padrão do
painel.

## Revalidação — Deskcomm 1.102.0 (2026-11-06 ~09:07–09:30)

> REVALIDAÇÃO, 2026-11-06. Somente leitura, exceto os curls de
> alcance de dentro do container (previstos na tarefa). Nada foi
> alterado no Deskcomm, no `.env`, nos containers ou no 9Router.
> Nenhum valor de segredo foi lido ou registrado. A validação
> anterior (acima) era PRÉ-ATUALIZAÇÃO contra o 1.44.0 e está
> superada por esta seção.

### Veredito

**PASS — mecanismo revalidado contra a 1.102.0.** A régua de saída,
o provider custom, o alcance da URL pública e o caminho de
ligação foram todos confirmados na versão nova, em produção.
**A ligação em si segue bloqueada** por dois itens que não são
falha da validação: (a) falta a chave de API do 9Router (o
usuário precisa criar uma dedicada no painel do 9Router);
(b) a existência da organização TuttiBom no Deskcomm não pôde
ser verificada sem credencial (ver item 5) — a ligação depende
dela existir. O item do roadmap passa a marcado como
**revalidado**; a ligação (credencial + binding + teste de
turno real) fica como item próprio, por marcar.

### 1. Régua de saída na 1.102.0 — PASS (com um aperto novo)

Lida no checkout fundido (ramo `local/v1.20.0-petemcasa`,
commits `8e2d91ab2` + `dc68ffb73`) **e** confirmada na imagem
em produção (1.102.0, `deskcommcrm-app-1`, `Up 8 hours`,
healthy): os cinco marcadores da validação anterior estão
presentes nos chunks do servidor — `100.64`,
`redirect_not_followed`, `ai_purpose_bindings`,
`Provedor personalizado`, `platform_settings.internal_destinations`.

Regras confirmadas, iguais às de antes:

- Guarda textual (`lib/automation/outbound-url.ts`,
  `assertSafeOutboundUrl`): esquema http/https; `https`
  obrigatório em produção; literal IPv6 bloqueado por inteiro;
  host recusado por `localhost`, `127.`, `10.`, `192.168.`,
  `169.254.`, `172.16/12`, `0.`.
- Guarda de IP resolvido (`lib/automation/outbound-ip.ts`,
  `assertDestinoResolvidoSeguro`): recusa se QUALQUER endereço
  resolvido cair em faixa especial — inclui `100.64/10`
  (CGNAT, a faixa do Tailscale), `10/8`, `127/8`,
  `169.254/16`, `172.16/12`, `192.168/16`, `0/8`,
  `192.0/24`, `192.0.2/24`, `198.18/15`, `198.51.100/24`,
  `203.0.113/24`, `224/4`, `240/4`, e IPv6 especiais
  (`::`, `::1`, `fe80`, `fc00::/7`, `ff`, `2001:db8`,
  `64:ff9b` NAT64, `::ffff:` mapeado).
- Composição (`motivoDaRecusaDeDestino`, origem
  `"organizacao"`): guarda textual + guarda de IP resolvido,
  em **cada** chamada (`fetchParaDestinoDaOrganizacao`,
  `redirect: "manual"`, 3xx vira recusa). A allowlist
  `platform_settings.internal_destinations` (decisão 22-d,
  regra 2) **continua não valendo** para endereço escolhido
  por organização: com origem `"organizacao"` a lista é
  `[]` — nenhuma entrada ajuda a base URL do provider custom.
  Sem mudança nesse ponto.

**O que mudou vs 1.44.0 (verificado por `git log`
`v1.44.0..v1.102.0`):**

- `#1651` (commit `8414be763`, 2026-09-25) — "endereço do
  provedor personalizado passa pela régua de destino da
  organização" — **NÃO está no 1.44.0**. Ou seja: na 1.44.0
  em produção, o cadastro da base URL custom **não** passava
  pela régua (a validação anterior inferiu a régua no cadastro
  a partir do checkout 1.20, que já continha o commit, e dos
  marcadores da imagem — a régua por chamada já existia, a do
  cadastro não). **Na 1.102.0 a régua vale no cadastro E em
  cada chamada** (`validateCustomKey` chama
  `motivoDaRecusaDeDestino(base, "organizacao")`). É um aperto,
  não um afrouxamento — e a URL pública passa nele do mesmo
  jeito (ver item 3).
- `#9537` (commit `953724884`) — "a chave do provedor
  personalizado é validada pelo endereço da própria linha" —
  também **não está no 1.44.0**. Na 1.102.0, a validação em
  segundo plano (`validarEmSegundoPlano`) lê a `base_url` DA
  LINHA gravada, nunca do chamador: cadastro e revalidação
  testam exatamente o que o runtime vai usar.
- A validação da credencial **não bloqueia mais a resposta
  de salvar**: `guardarCredencial` grava a credencial cifrada
  (AES-GCM) e dispara a validação em segundo plano
  (fire-and-forget); a tela mostra "Credencial salva.
  Validando…" e consulta o status ~3 s depois. Uma chave
  inválida NÃO impede o cadastro — aparece como
  `validation_error` no card e `validated_at` nulo.

### 2. Provider custom no catálogo da 1.102.0 — PASS

- `lib/ai/pontos/provedores.ts`: entrada `id: "custom"`,
  rótulo "Provedor personalizado (compatível com OpenAI)",
  descrição cita nominalmente o **9Router** e exige "num
  endereço público". `aceitaEndpointProprio: true`,
  `catalogoSincronizavel: false` (não há portal de chave; a
  chave é emitida pelo gateway do próprio operador).
- `validateCustomKey` (10 s de timeout, `GET {base}/models`
  com `Bearer`, `redirect: "manual"`, 3xx vira
  `unsafe_url:redirect_not_followed`; 401/403 vira
  `auth_failed_401`): aceita o catálogo em `{ data: [{ id }] }`
  ou `{ models: [{ id }] }`; sem catálogo o endereço ainda
  foi provado. A chave nunca é logada.
- "Salvar e validar" na tela: salva primeiro (ver item 1) e
  a validação roda em segundo plano; o card reflete
  `validated_at` / `validation_error` / `models_available`.

### 3. Alcance de dentro do container (1.102.0) — PASS

Testado de dentro de `deskcommcrm-app-1` (imagem 1.102.0,
`Up 8 hours`, healthy). `curl` **não existe** no container —
o teste foi com `node -e` + `fetch` (o container roda Node):

| Candidato | Resultado |
|---|---|
| `https://9router.petemcasa.com/v1/models` | **401 em 0,2 s, sem redirect**, corpo `{"error":"API key required for remote API access"}` — erro do próprio 9Router; o caminho completo funciona e a régua deixou passar (URL pública, IP resolvido público) |
| Controle `https://openrouter.ai/api/v1/models` | 200 |
| Loopback `:20130` / MagicDNS | Não testado por curl (sem curl no container); pela validação anterior e pela régua, seguem falhando — loopback do container é o próprio container, o nome MagicDNS não resolve no DNS do Docker, e o IP do Tailscale é recusado pelo guarda de IP resolvido |

Detalhe: dentro do container, `9router.petemcasa.com`
resolve para um IPv6 público da Cloudflare
(`2606:4700:3034::ac43:983b`) — não é faixa especial para
`ipEhEspecial`. A URL pública segue viva e o serviço
`cloudflared-9router.service` segue ativo (reconfirmado
nesta sessão).

### 4. Caminho de ligação na 1.102.0 — PASS (mecanismo)

Nenhum caminho exige escrita crua no banco. Os dois caminhos
oficiais:

**A. Credencial — tela IA › Credenciais
(`app/app/ai/credentials`) ou API:**

- Tela: diálogo "Adicionar credencial" — provedor
  `custom`, campo base URL obrigatório começando com
  `http://` ou `https://`; salva e valida em segundo plano.
- API: `POST /api/v1/ai/credentials` (admin), corpo
  `{ provider: "custom", label, api_key, base_url }`.
  Trailing slash removida antes de gravar; `base_url`
  obrigatório para custom (422 sem ele); `base_url` em
  provedor nativo é recusado (422). Grava em
  `ai_provider_credentials` (chave cifrada AES-GCM,
  `api_key_last4`, `base_url`, `is_active: true`);
  `validated_at` / `validation_error` /
  `models_available` vêm da validação em segundo plano.
  Rótulo duplicado para o mesmo provedor dá 409
  (`label_em_uso`).

**B. Binding — tela IA › Provedores
(`app/app/ai/providers`) ou API:**

- Tela: painel por ponto; para o ponto `agent_turn`
  ("Responder o cliente"), escolher provedor `custom`,
  modelo e chave. O campo de modelo vira **texto livre**
  quando o provedor não tem modelos no catálogo — que é o
  caso do `custom` (`ai_models` não tem linhas de
  `custom`; `catalogoSincronizavel: false`) — então
  `core-medio` pode ser digitado. O campo "Endereço próprio
  (opcional)" existe por ponto, mas o canônico é o da
  credencial (a validação lê o endereço da linha).
- API: `PUT /api/v1/ai/providers`, corpo `{ purpose,
  provider, model_id, credential_id, base_url?, is_enabled? }`
  → upsert em `ai_purpose_bindings` por
  `(organization_id, purpose)`. A rota confere que a
  credencial é desta organização e do mesmo provedor.
- Catraca (`validarBinding`): `agent_turn` é ponto livre
  (exige tools + imagem), **não** é de menu fechado. Modelo
  fora do catálogo (`core-medio` não está em `ai_models`)
  **não é recusado** — passa com aviso ("Não conseguimos
  verificar o que o modelo sabe fazer…"). Consequência:
  a exigência de ferramentas **não é verificada** para
  modelo desconhecido — o binding salva, e só o teste de
  turno real prova se o modelo resolvido usa ferramentas
  (sem elas, o agente conversa mas não cria lead nem move
  o funil, sem erro na tela).

**Ordem de ligação (pronta para executar quando os
bloqueios caírem):**

1. Criar a chave dedicada do 9Router no painel do 9Router
   (bloqueio — ver item 7).
2. Garantir a organização TuttiBom no Deskcomm (bloqueio —
   ver item 5).
3. Na tela IA › Credenciais (como admin da org TuttiBom):
   provedor `custom`, rótulo (ex.: "9Router"),
   `base_url=https://9router.petemcasa.com/v1`, chave.
   Aguardar o card mostrar validado e `core-medio` em
   `models_available`.
4. Na tela IA › Provedores, ponto `agent_turn`: provedor
   `custom`, modelo `core-medio` (texto livre), chave da
   etapa 3. Salvar (passa com o aviso de modelo
   desconhecido — esperado).
5. Teste de turno real do agente: mensagem de teste e
   conferir que o agente responde **e** opera o CRM
   (cria/move lead) — é isso que prova o tool calling
   do modelo resolvido.

### 5. Organização TuttiBom — BLOQUEADO (não verificável sem credencial)

Verificar a existência da org exigiria sessão autenticada
no Deskcomm ou acesso ao Supabase com credencial — nenhum
dos dois está disponível sem ler segredo (o que a tarefa
proíbe). Pelos registros anteriores, a organização TuttiBom
**não existe ainda** (a criação dela é o passo seguinte da
implementação, guia `deskcomm-cliente-novo`); a org
existente é a petemcasa. A ligação depende da org existir:
sem ela não há onde gravar credencial nem binding.
**Não foi criada aqui.**

### 6. Teto de gasto — custo do provider custom na 1.85 — PASS (com nuance)

CHANGELOG 1.85.0 (2026-10-17): "O custo das chamadas do
provedor personalizado passa a ser calculado pelo preço do
catálogo. Se você usa o provedor personalizado e tem teto de
gasto de IA em modo de bloqueio, confira o teto antes de
atualizar: as chamadas desse provedor passam a ser contadas
pelo preço real, e o gasto do mês pode cruzar o limite e
pausar a IA nas conversas."

O que o código faz (`lib/ai/cost.ts`, `computeCost`): tenta
a tarifa promocional, depois `ai_pricing` (lista curta
escrita à mão), depois o catálogo `ai_models`
(`precoDoCatalogo`, que tenta o id como veio e sem o
prefixo). Se **nenhum** catálogo conhece o modelo, o custo
é `null` — nunca 0 — e o gasto fica registrado como
incompleto (o sinal de gasto incompleto acende; o teto
soma `coalesce(cost_cents, 0)`, ou seja, **não enxerga
esse gasto**).

Para o `core-medio`: ele é um combo do 9Router, não está
em `ai_pricing` nem em `ai_models` — então, pelo código
lido, o custo do turno sai `null` e o teto **não** o
conta (o sinal de gasto incompleto acende). Ou seja: a
mudança da 1.85 **não** faz o teto travar por causa do
core-medio — mas também não o mede. Qual id de modelo o
runtime grava no uso (o `core-medio` do binding ou o id
resolvido pela cadeia de fallback do 9Router) **não foi
verificado** — é um ponto aberto para o teste de turno
real. Se um dia o id gravado passar a existir no catálogo,
o custo passa a contar pelo preço dele.

### 7. Bloqueios para a ligação (o que falta)

1. **Chave de API do 9Router (dedicada).** O usuário cria
   no painel do 9Router uma chave dedicada para o Deskcomm
   (recomendado: dedicada, para revogar separado; a
   alternativa é reutilizar a chave do CLI pelo fluxo
   seguro). O valor nunca passa por aqui. Sem ela, a
   credencial não pode ser criada — o cadastro exige a
   chave.
2. **Organização TuttiBom no Deskcomm.** Criar pela
   sequência de cliente novo (`deskcomm-cliente-novo`):
   org + agente + orçamento. Sem ela, não há onde gravar
   credencial nem binding.
3. **Teste de turno real** (após 1 e 2): prova o tool
   calling do modelo resolvido e o id de modelo gravado
   no uso (ver item 6).

### O que mudou vs a validação anterior (1.44.0)

- A base URL pública **existe agora** (túnel nomeado
  `9router`, `9router.petemcasa.com`, verificado 401 de
  dentro do container) — o bloqueio central da validação
  anterior caiu.
- A régua no cadastro da base URL custom **é nova na
  1.102.0** (#1651) — na 1.44.0 em produção ela
  provavelmente não existia (a validação anterior a inferiu
  do checkout 1.20, que já continha o commit de 25/09, e
  dos marcadores da imagem). A régua por chamada já
  existia. Nada muda na prática para a URL pública.
- A validação da credencial passou a ser **em segundo
  plano** (não bloqueia o salvar) e a ler o endereço **da
  linha gravada** (#9537, também novo na 1.102.0).
- O custo do provider custom passou a contar pelo preço
  do catálogo (1.85) — para o `core-medio`, sem linha no
  catálogo, o custo sai `null` e o teto não o enxerga
  (ver item 6).
- O campo de modelo do ponto vira **texto livre** quando o
  provedor não tem catálogo — é o que permite digitar
  `core-medio` na tela.
