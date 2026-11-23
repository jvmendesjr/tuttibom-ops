# Relatório — TuttiBom Ops: descrição e estado atual

**Data:** 2026-11-15

**Atualização 2026-11-16:** este relatório é um instantâneo de 2026-11-14/15, anterior à pausa do ADB e à adoção do Camofox como navegador único (D-004). Para o estado corrente, ver o roadmap §12 e o ESTADO.md.
**Base:** `docs/roadmap.md` §12 ("Estado atual — 2026-11-14"), `docs/ESTADO.md`
(2026-11-07), `docs/rascunho-memoria-roteador.md`,
`docs/rascunho-investigacao-b-retorno.md`,
`docs/rascunho-mcp-gestor-funcoes.md`,
`docs/rascunho-rotina-diaria-gestor.md` (rascunho, não aprovado) e
`MEMORY.md`. Números de produção conferidos em 2026-11-14.

**Aviso sobre as fontes:** o `ESTADO.md` é de 2026-11-07 e várias
partes dele já foram superadas (a Ana está na v9, não na v3; o
caminho Paperclip foi cancelado; o 9Router já foi validado e o
travamento do teste, corrigido). O estado corrente é o do roadmap
§12 (2026-11-14). Onde o `ESTADO.md` diverge, vale o roadmap e
este relatório diz isso.

---

## 1. O que é o TuttiBom Ops

O TuttiBom é uma loja do Cariri, Ceará — triângulo Juazeiro do
Norte / Crato / Barbalha — que vende **fitas de cetim
personalizadas** e **itens impressos em 3D**. O projeto
`tuttibom-ops` (nome decidido 2026-10-31) é a operação completa
da loja: atendimento, catálogo, produção, entrega e, depois,
redes sociais. É modular e multirrede por desenho — o que
funciona no WhatsApp deve ser reutilizável no Facebook e no
Instagram depois de aprovado — mas hoje a operação viva é uma
só: **o atendimento no WhatsApp, feito pela Ana, no Deskcomm**.

A regra de trabalho, fechada em 2026-11-13: o **Muse é o agente
de gestão e manutenção do usuário, sempre com ele** — implementa
tudo ele mesmo; nada vai para o Cursor ou o Agy até o usuário
pedir explicitamente para delegar. Nada é publicado, enviado ou
combinado em preço, reserva ou encontro sem a aprovação do
usuário ao texto exato. Publicar uma nova versão da Ana no
Deskcomm é um clique do usuário.

## 2. O produto: fita de cetim personalizada

- **Variações:** 15 mm (nº 3) e 22 mm (nº 5); 10, 25 e 50 m;
  impressão hotstamp em Preto, Dourado Metalizado ou Prata
  Metalizado; 100% poliéster.
- **Produção:** 3–5 dias úteis após a prévia aprovada e o
  pagamento confirmado. Não lavável, sensível a atrito.
- **Catálogo no Deskcomm:** 18 produtos em `catalog_products`
  (org tutibom), um por combinação largura/metragem/cor de
  impressão — códigos `FITA-22-50-PRETO` etc. — com os preços
  da captura Shopee de 2026-10-30 como **ponto de partida**, a
  ajustar. Estoque não é controlado por variação (tratado como
  disponível). Imagens vazias por enquanto: o usuário vai
  disponibilizar as imagens reais autorizadas.
- **Cores:** paleta do fornecedor com 69 cores
  (`catalogo/cores-fita-cetim.md`); **18 marcadas como
  disponíveis** nas duas larguras. A Ana nunca diz "não temos
  essa cor" — diz que vai consultar a disponibilidade — e mantém
  sempre a ressalva de que depende da confirmação. Cor da fita
  não é cor da impressão. "Amarelo" = Canário (09), a confirmar.
- **Imagens — regra corrigida 2026-11-06:** as duas opções
  existem. (1) **Imagens reais são permitidas**, só as de
  trabalhos já produzidos **com autorização** para demonstrar.
  (2) **Imagens fictícias são para a amostra personalizada** —
  um render (IA) da personalização da própria pessoa, com
  nome/data fictícios se ela não quiser informar os dados.
  Armazenamento: bucket `catalog-photos` (privado) + tabela
  `catalog_products` (`imagem_url` e `fotos`).
- **Amostra (Modo A):** a Ana oferece a prévia como pergunta,
  monta quando a pessoa aceita e só envia depois que o humano
  aprova a imagem exata. Amostra física não é oferecida nem
  decidida pela Ana — quando a situação surgir, passa para o
  humano e o caso vira aprendizado registrado.
- **Biblioteca de assets:** no Drive da conta `tutibom10`,
  pasta `Biblioteca TuttiBom` (13 subpastas por ocasião) +
  planilha de classificação. Primeiro lote, 2026-11-12: **25
  assets catalogados e aprovados** (23 reais + 2 de IA), 6
  duplicatas descartadas. Fluxo: Muse gera a prévia →
  `Pendentes/` → humano aprova a imagem exata → pasta da
  ocasião + `Aprovado` na planilha + bucket → Ana envia.
- **Preços e pagamento:** Pix é o padrão; cartão via link
  Mercado Pago do usuário, taxas para o comprador, sem
  adiantamento. No cartão, a produção começa na **aprovação**,
  não quando o dinheiro cai. **Sem desconto** — a Ana diz que
  o valor já é bom e justo e não passa para o produtor.
- **Frete e entrega:** a Ana **não cita valor de frete** — o
  produtor confirma a taxa no app. A tabela de frete está em
  construção incremental (a cada pedido, o valor exato é
  confirmado no app e a tabela é atualizada); revisão marcada
  para ~2026-12-06, para decidir se ela passa a dizer o valor
  aproximado. Entrega local em Crato/Juazeiro/Barbalha
  (motofrete Uber/99, taxa no app); retirada sem taxa na
  Av. Pedro Gonçalves Norões 280, Grangeiro, Crato; Correios
  só como exceção humana.
- **Produção:** o produtor é o **José** — com os clientes, usa-se
  sempre "produtor", nunca "gestor".

## 3. O atendimento: a Ana

- **Versão viva: v9**, publicada 2026-11-08, verificada
  2026-11-09. Modelo `core-medio` via **9Router** (provedor
  `custom`, túnel `9router.petemcasa.com` → 127.0.0.1:20130).
  Transcrição de áudio: ElevenLabs Scribe (`scribe_v1`),
  provada em produção. OpenAI só para embedding.
- **Canal:** WhatsApp via WAHA (sessão `tutibom`,
  558881022939, WORKING). Organização tutibom
  (`92bfe3dd-1117-4b12-8413-95a2e8e143e0`, slug
  `deskcomm-local`); agente Ana
  (`c9008471-d098-4e9f-88e9-da77dde393ea`, v9
  `75d8ba2d-9b49-4847-92fd-cde5c598c14a`).
- **Como ela atende:** prompt enxuto (identidade + regras
  duras) + **4 skills por função** — `amostra-fita`,
  `frete-entrega`, `preco-catalogo`, `pos-venda` — carregadas
  por matching determinístico de palavra-chave. Saudação
  simples, que pode variar; **nunca começa dizendo que é
  atendente virtual** — só diz se perguntarem. Sempre em
  português brasileiro. Uma pergunta por vez. O roteiro de
  atendimento é um GPS, não um trilho: continuar de onde
  parou, tratar quem já está no funil como conhecido, não
  repetir perguntas.
- **Ramo A (saudação instantânea), em produção desde
  2026-11-07:** saudação fechada no primeiro contato vira
  resposta na hora — "Oi! Me conta o que você está buscando
  que eu te ajudo."
- **Reconhecimento imediato (ack):** mensagens pequenas recebem
  um "oi" primeiro; a resposta completa vem em 1–2 min. Depois
  da primeira interação, o ack gira entre "Só um instante",
  "Vou verificar" e "Ok, só um instante", sem repetir em
  sequência. Tempo medido: 27–33 s, aceito; o refinamento do
  tempo ficou adiado. A Ana devolve o cumprimento no início
  da **resposta completa**, uma vez por abertura de conversa.
- **Conhecimento:** FAQ TuttiBom (13 pares, 16 trechos) e Base
  de conhecimento TuttiBom (22 chunks), ambos prontos;
  "Conversas anteriores" vinculada, com 0 chunks. Funil
  **Vendas** com 7 etapas (Novo contato → Já respondi →
  Escolhendo o produto → Vai levar → Aguardando pagamento →
  Pedido pago → Não comprou).
- **Follow-ups:** Fluxo A, "Silêncio — escolhendo o produto"
  (silêncio 24h → msg1 → espera 3 dias → msg2); Fluxo B,
  "Aguardando pagamento" (ao entrar na etapa → 2h → msg1 →
  ~24h → msg2). Os dois ativos e vinculados à Ana.
- **Janela de resposta:** o padrão do Deskcomm é 7h–22h; fora
  dela, o turno era adiado para as 07:00. **Ponto aberto
  (2026-11-15):** o usuário decidiu que a Ana atende 24/7 —
  falta confirmar/mudar a janela da tutibom para isso valer
  de fato.
- **Segurança:** 17 gates de saída (cadeia v13); a mensagem só
  chega ao canal se todos passarem. O Jev (TypeSafe) julga
  manipulação em paralelo com o classificador de jailbreak do
  LLM; vale o maior dos dois níveis. O teto de custo **não
  enxerga** o `core-medio` (fora de `ai_models` e de
  `ai_pricing`) — o controle real do gasto está do lado do
  9Router. Não há teto de turnos por conversa; a correção
  proposta (teto de turnos + precificar o modelo) aguarda
  decisão do usuário.

## 4. A operação no Deskcomm — o que está ligado e o que está feito

### 4.1 Memória por contato + roteador Jev (deploy 2026-11-13)

- **Memória por contato:** tabela `contact_interests`
  (migration 9223) + ingestão noturna às **03:35** das
  conversas resolvidas. A Ana recupera os trechos do contato
  no turno; o roteador decide por código quando há um único
  interesse + saudação fechada; senão, o Jev recebe só o
  rótulo (nunca PII). Commit `305e8e124`, deploy 2026-11-13
  ~00:33. Detalhe em `docs/rascunho-memoria-roteador.md`.
- **Roteador "Roteador TuttiBom" LIGADO** no número do TuttiBom
  desde 2026-11-13 ~13:00: 3 membros, todos a Ana — `fita` (1),
  `impressao_3d` (2), `preco` (3) — fallback Ana; tarefa Jev
  `roteador` em **decidindo**, modo comparação.
- **Estado real (conferido 2026-11-14):** 16 conversas, **0
  resolvidas**, 0 registros em `contact_interests`, 0 trechos
  de memória. A memória ainda não tem o que aprender — a
  primeira prova real vem quando uma conversa resolver, o lote
  da madrugada rodar e um contato voltar com "olá". O caminho
  agendado está íntegro (crontab 03:30 + 03:35; disparo manual
  sem falhas).

### 4.2 Correções de áudio e do "decidindo" (deploy 2026-11-13 ~20:56)

- **Ack de áudio:** o reconhecimento ganhou chamada própria ao
  Jev com a transcrição (`[áudio] <transcrição>`); a
  manipulação continua só-texto. Áudio com transcrição vazia
  não gera ack; imagem/vídeo/documento/figurinha não geram ack.
- **"Decidindo":** o classificador da IA volta a rodar em todo
  turno que classifica, com teto de 30 s — a causa era um
  atalho de performance de 2026-11-07 que pulava o
  classificador quando o Jev decidia (e os testes estavam
  certos, o código estava errado).
- **Etiqueta de família (Investigação B, parte A):** quando um
  produto é apresentado, o lead ganha também a etiqueta da
  família (`fita`/`3d`), além do código da variação.
- Commits `de96f0520` e `c1d7efbc2`. Testes: unitários 73/73,
  invariante 14/14, typecheck OK. O `gov:verify` segue vermelho
  por falhas pré-existentes (100, todas reproduzidas na árvore
  limpa ou flakes de carga) — o verde se julga por feature,
  nunca se promete suíte verde.

### 4.3 Investigação B, parte B — aguardando um clique do usuário

O retorno automático (Fluxo A) não lia o histórico antes de
enviar — chegou a mandar 3 vezes a mensagem da fita para quem
perguntava de letras em MDF. O desenho aprovado: condição
"Tem etiqueta fita?" antes da msg1 — quem tem a etiqueta
recebe a msg1 da fita ("Oi! Ficou alguma dúvida sobre a
fita? Se quiser, me conta o que você está buscando que eu te
ajudo."), quem não tem recebe a genérica. O rascunho já está
trocado no painel (o rascunho antigo do usuário foi salvo
antes); a versão viva continua `1df069fe`. **Falta o usuário
publicar o rascunho no painel (um clique)** — re-conferido
2026-11-14, segue sem publicar. Detalhe em
`docs/rascunho-investigacao-b-retorno.md`.

### 4.4 Infraestrutura e deploys

- **Stack:** DeskcommCRM no PC (`/home/pc/DeskcommCRM`,
  branch `local/v1.20.0-petemcasa`, HEAD `c1d7efbc2`), Next.js
  16, Supabase **cloud** como banco de produção, WAHA
  standalone :3005, scheduler com crontab embutido na imagem.
- **Deploy é build local, não PR para a main** — o branch nunca
  foi para a origin/main. Sobe-se com os 3 composes juntos
  (prod + ponte + build). Nunca: `git pull` nesse branch,
  migrations direto no banco de produção, `docker compose
  down -v`, desligar o `cloudflared-ponte` sem aprovação.
- **Supabase direto é só-IPv6** — as operações do kit com o
  banco precisam de `PSQL_DOCKER_NETWORK=host`.
- **Painel:** só Conteúdo + Planos (a aba Leads foi cancelada);
  read-only para o usuário, só o Muse edita; sem dados de
  comprador.

## 5. O gestor via MCP — o que é, o que já se sabe, o que falta

O Deskcomm expõe um **servidor MCP** (`/api/mcp`) com as
operações do CRM como ferramentas. O gestor é o agente que usa
esse servidor para cuidar da operação depois da conversa:
finalizar contato e venda, verificar o que vai para a memória,
mover leads sem retorno para o funil, organizar etapas e
etiquetas, acompanhar o que foi prometido e o histórico.

**O que já foi verificado (2026-11-14/15):**

- **É previsto na documentação do Deskcomm** — spec 11
  (servidor MCP interno; prevê agentes internos e, futuramente,
  Cursor/Claude Desktop), spec 14 (contrato de governança para
  agentes externos; o agente externo previsto chama-se
  **Vendaval**, runtime 1:N fora do repo) e spec 13. O papel
  **gerente** é um nível documentado
  (viewer < agent < manager < admin).
- **O gestor pode ser qualquer agente** — o servidor não
  distingue quem está do outro lado, só o token e o papel.
  Entregar um token a outro agente continua sendo delegar e
  precisa de pedido explícito do usuário. O Muse é o primeiro
  gestor.
- **Inventário, levantado do código: 75 ferramentas em 6
  pacotes** por jornada (atender, vender, reter, escalar,
  organizar, evoluir). **Teto de 27 ferramentas por agente**
  — corrigido neste relatório: o inventário de 2026-11-14
  dizia 25, mas o código (`lib/mcp/tools/selecao-por-pacote.ts:83`)
  diz 27. Riscos: 40 seguras (só leitura), 25 de atenção
  (mudam dados, reversíveis pela tela) e **10 críticas**
  (irreversíveis ou que saem do sistema) — as críticas nunca
  entram por pacote; cada uma exige marcação explícita, uma a
  uma. Detalhe em `docs/rascunho-mcp-gestor-funcoes.md`.
- **O catálogo é da Ana também** — o mesmo catálogo serve o
  agente interno (o motor monta as ferramentas do turno da Ana
  dele, menos o harness — enviar WhatsApp e handoff nunca são
  ferramentas dela — e menos o que a nativa já cobre) e o
  gestor externo via MCP. A Ana também é cliente de MCP
  (consome servidores externos no turno).
- **O que o MCP não tem:** publicar versão de agente ou de
  fluxo, gerenciar roteadores, gerenciar os próprios tokens,
  criar produtos no catálogo, configurar a organização, ler
  ou escrever a memória por contato (`contact_interests`).
  Isso continua sendo clique humano no painel, mudança de
  código com deploy, ou leitura direta no banco.
- **O modo de despacho continua `native`.** Virar para
  `external` faria a Ana parar de atender — fora de questão
  nesta rotina.

**O que falta decidir/fazer (nada disto está feito):**

- O usuário **aprovar o desenho da rotina diária do gestor**
  (rascunho 2026-11-15, ver §6) — escopo enxuto de 25 de 27
  ferramentas, zero críticas, 3 varreduras por dia.
- Emitir o primeiro token (Muse, papel gerente, org tutibom)
  e rodar a primeira varredura supervisionada, antes de virar
  rotina.

## 6. A rotina diária do gestor — rascunho, não aprovado

Desenhada em 2026-11-15 a pedido do usuário
(`docs/rascunho-rotina-diaria-gestor.md`). **Status: rascunho,
nada executado, nada agendado.**

- **O loop tem 3 partes:** (1) o motor determinístico do
  Deskcomm, que já roda 24h (follow-ups, varredura de silêncio,
  crons); (2) a **varredura do gestor via MCP, 3 vezes por dia
  — 08:00, 14:00 e 20:00, todos os dias da semana** — em 8
  passos (casos humanos, radar de risco, follow-ups, funil e
  promessas, rascunhos, etiquetas/etapas, memória da org,
  relatório); (3) o **checkpoint humano** — o usuário aprova
  ou recusa as propostas críticas. Nada crítico sai sem essa
  aprovação.
- **Escopo do primeiro token (v1): 25 de 27 ferramentas, zero
  críticas.** O gestor aplica só o reversível; o crítico vira
  proposta. Cada varredura relata só o que mudou desde a
  anterior.
- **Fora da rotina, a discutir depois:** a **saúde do sistema**
  — disponibilidade dos modelos (9Router), do roteador, do
  Deskcomm, do WAHA e dos túneis; alertas de risco; disco, RAM
  e CPU do PC; tokens TypeSafe/Jev. O MCP não tem ferramenta
  de saúde; a verificação é por SSH ao PC, com outro
  agendamento. Fica registrado no roadmap para não perder a
  linha no Deskcomm.
- **Pontos a confirmar pelo usuário antes de ligar:** os
  horários e a entrega no chat principal; os limiares (3 dias
  sem resposta após a msg2 → propor reativação; 7 dias →
  propor encerrar como perdido); se mover etapa pode ser
  automático quando o histórico prova; se salvar memória da
  org só após aprovação do texto; e a autorização para emitir
  o token e criar o agendamento.

## 7. O telefone e as redes sociais — o outro módulo

- **S10 Lite (principal):** Samsung S10 Lite, via Tailscale e
  ADB a partir do PC. O PC é só o ponto de execução. A
  navegação é cautelosa e humanizada, um passo por vez, com a
  tela acordada antes de cada toque. **Publicação provada**
  (Feed piloto, Stories 9:16, em 2026-11-01); **responder pelo
  ADB ainda não provado**. Recuperação automática instalada
  (MacroDroid + Termux), mas o teste fim-a-fim está adiado.
  O telefone não tem SIM — só Wi-Fi.
- **Redes sociais — outro módulo, depois do Deskcomm:** a
  gestão de Facebook, Marketplace e Instagram é o **TuttiBom
  OPS**, que só volta depois que o Deskcomm estiver
  configurado. Não é parte da operação do Deskcomm.
- **Ponte (`/home/pc/ponte`):** a ponte do Messenger (e do
  Instagram) sobre o Deskcomm. **Ainda não há adapter** de
  Messenger nem de Instagram, e o `tutibom` ainda não está
  registrado nela. Decidido: sem API do Facebook — o adaptador
  será transporte **S10/ADB** (o telefone é a API); o
  **Zernio** é a ponte inicial (para testar e pela comodidade),
  e o ADB fica como alvo e fallback.
- **Ordem combinada:** validar 9Router → configurar o agente
  → gestor via MCP → conector Messenger na Ponte → ativar o
  Messenger e testar → painel reduzido. Os dois primeiros
  passos estão feitos; o terceiro é o que está em discussão
  agora.

## 8. Números do estado (conferidos 2026-11-14)

| Item | Valor |
|---|---|
| Conversas na org tutibom | 16 |
| Conversas resolvidas | 0 |
| Registros em `contact_interests` | 0 |
| Trechos `memoria_contato` em `ai_chunks` | 0 |
| Sessão WAHA tutibom | WORKING (558881022939) |
| Roteador "Roteador TuttiBom" | ativo, 3 membros, Jev `roteador` decidindo |
| Fluxo A — versão viva | `1df069fe` (rascunho com ramo presente, sem publicar) |
| Ana — versão viva | v9 |
| Deskcomm — HEAD | `c1d7efbc2` (`local/v1.20.0-petemcasa`) |
| Scheduler — crontab | 03:30 + 03:35, intacto; disparo manual sem falhas |
| Produtos no catálogo | 18 (FITA-22/15-10/25/50-PRETO/DOURADO/PRATA) |
| Assets aprovados na biblioteca | 25 (23 reais + 2 de IA) |
| Cores da fita disponíveis | 18 de 69 |
| Ferramentas MCP no catálogo | 75 (teto 27 por agente) |

## 9. Pendências, na ordem mais técnica

1. **Publicar o rascunho do Fluxo A no painel** (um clique do
   usuário; só então vale para novas inscrições).
2. **Teste de confirmação do ack de áudio em produção** — o
   usuário manda um áudio e vê o ack chegar em segundos antes
   da resposta completa.
3. **Gestor via MCP** — rotina desenhada 2026-11-15 (rascunho);
   falta o usuário aprovar o desenho → primeiro token →
   primeira varredura supervisionada → agendamento 3×/dia.
   Inclui confirmar a janela 24/7 da Ana.
4. **Provar a memória em produção** — depende de uma conversa
   resolver primeiro.
5. **Zernio** (ponte inicial do Messenger) → **adapter
   Messenger via ADB** → **painel reduzido**.
6. **Revisão da tabela de frete ~2026-12-06.**
7. **Saúde do sistema** — desenhar depois (escopo, cadência,
   limiares, para quem alertar).
8. **Menores, para observar no próximo teste:** refinamento do
   tempo do ack (27–33 s, aceito); `reason` tentado 1× no turno
   de áudio; Ana não ofereceu a prévia como pergunta nesse
   áudio; intervalo silencioso de ~5 min sem log no turno do
   contato de teste da V4; teste de imagem; testes de ADB
   desbloqueados pelo u2; teste fim-a-fim da recuperação do S10.

## 10. Regras que governam tudo isto

- O Muse implementa tudo ele mesmo; nada vai para o Cursor ou
  o Agy até o usuário pedir explicitamente para delegar.
- O Muse é o agente de gestão e manutenção do usuário, sempre
  com ele — Deskcomm, Ponte e loja.
- Nada publica, envia ou combina sem aprovação do usuário ao
  texto exato; o trabalho chega sempre como rascunho primeiro.
- Sem dado de comprador no repositório local nem no painel; as
  notas de trabalho por lead ficam só no Drive privado do
  usuário.
- O painel é somente leitura para o usuário: só o Muse o edita,
  após discussão honesta.
- Paperclip **deferido** (não cancelado). Vocero Lab **deixado
  de lado** — não reviver a menos que o usuário levante o tema.
  Railway fora de escopo.
- O S10 é o principal para tudo que toca a conta da loja; o
  Camofox fica só como secundário de teste, sem escrita na
  conta.

## Fontes

- `docs/roadmap.md` §12 (Estado atual — 2026-11-14)
- `docs/ESTADO.md` (2026-11-07 — partes superadas, ver aviso)
- `docs/rascunho-memoria-roteador.md`
- `docs/rascunho-investigacao-b-retorno.md`
- `docs/rascunho-mcp-gestor-funcoes.md` (inventário das 75
  ferramentas; teto corrigido para 27 neste relatório)
- `docs/rascunho-rotina-diaria-gestor.md` (rascunho 2026-11-15)
- `MEMORY.md` e `memory/2026-11-14.md`
- Código do DeskcommCRM no PC (conferido 2026-11-14/15)
