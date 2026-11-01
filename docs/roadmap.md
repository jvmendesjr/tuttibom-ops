# Roadmap v2 — tuttibom-ops

> Versão 2, 2026-10-31. Ordem é prioridade, não pressa: cada fase só avança
> quando a anterior estiver provada, com aprovação onde a guardrail exige.
> Legenda: **P0** = bloqueia o resto · **P1** = próximo passo real ·
> **P2** = só depois de P0/P1 provados · **Último caso** = só com decisão
> explícita do usuário, nunca como atalho.

## Visão em uma linha

Uma operação agent-first e modular para vender impressão 3D e fitas de
cetim personalizadas a partir do Cariri, começando pelo Facebook no S10
via ADB, e reaproveitando conteúdos, processos e fluxos em outras redes,
contas e nichos — com rascunho antes de publicar, humano no checkpoint,
painel só leitura e observabilidade constante.

## Fase 0 — Fundação e conexão estável [P0 · em grande parte feita]

- [x] S10 no Tailscale, SSH com chave dedicada, proxy de túnel (porta
  3130), config com caminhos absolutos (`ssh -F ~/.ssh/config s10`).
- [x] sshd com watchdog e Termux:Boot; Facebook já logado, Messenger
  instalado (só instalado, sem login feito pelo Muse).
- [x] Recuperação de ADB instalada: macro MacroDroid (15 min + boot,
  `adb_wifi_enabled=1`), descoberta de porta por mDNS, watchdog no
  Termux — validada por componente, ainda NÃO provada de ponta a ponta
  em todos os cenários.
- [x] Regra de tela: verificar vigília, acordar com `keyevent 224`,
  confirmar Awake antes de qualquer toque.
- [x] Teste de retorno após horas parado (2026-10-30, ~10:00): SSH
  sobreviveu a queda e retorno de energia/internet; ADB não.
- [x] Incidente rede nova (2026-10-30, 15:40–20:05): ADB ausente por
  prompt "Permitir depuração por Wi-Fi nesta rede?"; após novo allow,
  ADB voltou (watchdog FOUND 20:09). Considerado superado por enquanto;
  usuário acompanha a tela e avisará qualquer contratempo.
- [ ] Observar os próximos ciclos do MacroDroid na rede nova: o prompt
  repete a cada ciclo mesmo com "sempre permitir"? Registrar, não assumir.

**Porta de saída:** SSH volta sozinho; ADB volta após allow manual em
rede nova, com log do watchdog. **Não fazer:** escanear portas, rajada
de tentativas, forçar conexão ignorando chave, reinstalar Termux.

## Fase 1 — Catálogo real e identidade [P0 · bloqueia anúncios]

- [ ] Definir 3–5 produtos de partida; para cada um: material, medidas,
  cores, tempo real de produção, preço para o Facebook, prazo e retirada
  em Juazeiro/Crato/Barbalha, foto em luz natural.
- [ ] Pendências conhecidas da fita de cetim: nomes das cores, preço
  para o Facebook, entrega no Cariri, regra de aprovação da prévia,
  tamanho/repetição da arte, custo por rolo.
- [ ] Reavaliar a identidade visual existente da conta (já existe; não
  criar do zero) e registrar a brand sheet: cores, tipografia, logo,
  margens, formato de legenda. Sem brand sheet aprovada, template de
  vídeo não fecha.
- [ ] Preencher `catalogo/produto-impressao-3d.md` e
  `catalogo/produto-fita-cetim.md` só com dados confirmados.

**Porta de saída:** catálogo aprovado, com foto. **Não fazer:** anunciar
com preço estimado, prometer prazo não medido, usar foto de cliente ou
de anúncio alheio, copiar texto/foto/logo de concorrente (modelar só
estrutura e formato).

## Fase 2 — Testes de laboratório, em rascunho [P1]

Um teste por sessão, com calma:

1. [x] Teste 1 — ciclo de leitura: abrir Facebook, pesquisar, voltar.
   Provado em 2026-10-30 (pesquisa no Cariri, só leitura).
2. [ ] Teste 2 — rascunho de anúncio no Marketplace, sem publicar.
3. [ ] Teste 3 — triagem de inbox sem responder o que compromete.
4. [ ] Teste 4 — rascunho de post/vídeo sem publicar, com texto e mídia
   exatos para aprovação.

**Regra de promoção:** um teste só sai do laboratório após 3 execuções
limpas (sem aviso, remoção ou verificação inesperada) + aprovação
explícita do usuário. **Não fazer:** publicar, responder preço,
impulsionar, curtir/seguir em série, tentar contornar verificação.

## Fase 3 — Painel v1, só leitura [P1 · este documento + esboço]

- [x] Esboço v1 criado: `painel-v1/index.html` + `docs/painel-v1.md`,
  com dados mockados e marcados como mock, sem dado de comprador.
- [ ] Definir padrões de referência com Mobbin (primeiro) e gerar o
  protótipo com Magic Patterns (depois) — ver decisão em
  `docs/painel-v1.md`. Credenciais só pelo fluxo seguro, nunca no chat,
  e só quando forem realmente usadas; o esboço v1 não precisa delas.
- [ ] Contrato de dados do painel: o que cada aba mostra, de onde vem,
  com que atraso, e o que NUNCA vai para o painel (segredo, endpoint
  vivo, dado de comprador, conteúdo de conversa).
- [ ] Contadores de falhas por dia/semana/mês, por tipo e severidade,
  e observabilidade: tokens por provedor/tarefa, disponibilidade com
  último check, saúde do S10 (bateria, disco, memória, uptime, reinícios).

**Porta de saída:** painel v1 abre, mostra as 6 abas com dados mock
coerentes, e o usuário só visualiza. **Não fazer:** botão de publicar,
responder ou apagar no painel; edição pelo usuário; dado real sem
contrato de dados aprovado.

## Fase 4 — Criação de conteúdo, com NotebookLM [P1, após catálogo]

- [ ] Criar a skill do NotebookLM: caderno canônico (conceito, objetivo,
  loja, redes, método de pesquisa/concorrência/modelagem, persona
  versionada) + cadernos efêmeros por criativo/publicação, exportar
  antes de deletar, deletar caderno e chat ao fim.
- [ ] Rotina de preparação de criativo: NotebookLM (roteiro, texto,
  prompts de imagem) → Muse (imagem, vídeo, edição, motion graphics
  via Remotion/HyperFrames/FFmpeg) → storyboard para o usuário ver
  antes de renderizar → arquivo versionado → aprovação → fila.
- [ ] Calendário de partida (teste): no máximo 3 posts/semana, dias
  alternados, 1 processo + 1 produto em uso + 1 pergunta/personalização.
  Nada de 3 posts de venda seguidos. Formatos em ordem de teste:
  vídeo curto do processo → antes/durante/depois em 3 fotos → pergunta
  concreta → personalização como protagonista → prova local do Cariri
  → história curta → preço com próximo passo claro (quando o catálogo
  permitir).
- [ ] Processo específico de texto para publicações: ainda a discutir
  com o usuário; até lá, nenhum texto vai para publicação sem o texto
  exato aprovado.
- [ ] Datas do Cariri com antecedência: festas juninas, Santo Antônio
  de Barbalha, JuáForró, Expocrato, romarias de Juazeiro, Feirart Cariri.

**Porta de saída:** 3 formatos com reação repetida, documentados.
**Não fazer:** postar todo dia para "ganhar alcance", repostar o mesmo
anúncio em série, usar foto de cliente sem autorização.

## Fase 5 — Marketplace, interação e CRM [P1, após triagem provada]

- [ ] Manutenção do Marketplace: rotinas R-07 (perfil/notificações e
  estado dos anúncios, só leitura), R-08 (Page Insights), R-07b (email
  no celular via ADB, só leitura — não via conector Gmail na VM).
- [ ] Reação da plataforma (R-09): baseline → 1 intervenção por vez →
  leitura em 24h e 72h, mesmo horário, comparando com post/anúncio
  parecido; regra nova só após 3 repetições sem confusor dominante.
  Nunca provocar a plataforma para testar.
- [ ] CRM: preencher as 5 abas da planilha "CRM TuttiBom — Interessados"
  no Drive quando o Sheets estiver conectado, sem subir arquivo por
  cima da planilha. Triagem real só leitura (1–3 linhas) antes de
  qualquer resposta. Depois, 1 resposta aprovada por vez, com registro
  e próxima ação com data. Follow-up: 1 dia sem retorno, 2–3 dias após
  proposta, 7 dias → Adormecido, no máximo 2 follow-ups sem resposta.
- [ ] Classificação com Jev (TypeSafe, System 1): tipo de lead, estágio,
  urgência, risco — com limiar de confiança e rota para humano abaixo
  do limiar. Jev não gera texto e não aprova nada sozinho.
- [ ] Drive criativo: pastas `00_Identidade/`, `01_Brutos/`,
  `02_Criativos/`, `03_Publicacoes/` por rede/conta/data; cada criativo
  catalogado, descrito, relacionado, contado e com histórico de uso;
  nome padrão `AAAAMMDD_produto_formato_rede_v01.ext`.

**Porta de saída:** 10 conversas triadas, 3 respostas aprovadas enviadas
e registradas, 0 follow-up vencido sem decisão. **Não fazer:** disparo
de marketing, resposta automática, dado pessoal no repositório, dar
preço sem aprovação.

## Fase 6 — Banco de dados e módulos multi-rede [P1/P2]

- [ ] Esquema Supabase Postgres (rascunho em `db/schema.sql`): contas,
  redes, produtos, criativos, publicações, usos, falhas, métricas,
  tarefas. Drive = arquivo; banco = índice (só ponteiro, ficha e
  histórico). Leads fora do primeiro passo, por decisão de privacidade.
- [ ] Criar o projeto Supabase (conta Pro do usuário) e passar acesso
  pelo fluxo seguro, quando decidido — não agora, e nunca no chat.
- [ ] Migrar skills atuais para `core/` agnóstico + `contas/<marca>/
  <rede>/` como configuração; cada skill com contrato: propósito, onde
  se aplica, entradas, passos, decisões, paradas, saídas, adaptação
  para outra rede/nicho. Modelos externos entram de forma agnóstica.
- [ ] Segunda rede só após a primeira aprovada no Facebook, com a
  mesma guardrail, fila e painel — módulo novo, não cópia solta.
- [ ] Revisão semanal curta: anúncios ativos, perguntas sem resposta,
  follow-ups vencidos, motivos de perda, saúde da conta, falhas da
  semana e custo por provedor.

**Porta de saída:** painel lendo do banco (não de mock), com 4 semanas
de monitoramento registrado, sem surpresa não explicada.

## Fase 7 — Escala e decisões [P2, só depois de P0/P1 provados]

- [ ] Pontos e ofertas (adiado pelo usuário).
- [ ] Publicar no GitHub o repositório tuttibom-ops (hoje local; antes,
  resolver a instalação do app do Muse no GitHub).
- [ ] Migrar o CRM para ferramenta paga só se passar de ~20 negócios
  abertos por semana ou entrar mais gente na operação, com os mesmos
  estágios.
- [ ] Revisar limites de laboratório (2 rascunhos/dia, 1 publicação/dia,
  10 triagens/dia) só com histórico limpo e aprovação.

## Último caso (não é fase, é exceção)

- **Desbloqueio de bootloader do S10:** NÃO fazer por enquanto. Fica
  marcado apenas como solução de último caso, com decisão explícita,
  backup completo, re-login, re-pareamento e plano de volta — sabendo
  que há wipe, Knox tripado e risco de apps detectarem root, e que o
  desbloqueio sozinho não resolve o prompt de rede nova.
- **Conector nativo do Facebook:** só como auxiliar de Página no
  futuro, se a conta ligada for administradora dela. Nunca como
  executor da conta pessoal da loja por outra conta.
- **Railway:** fora desta aplicação, por decisão do usuário. Não entra
  em arquitetura, painel ou lista de provedores.

## O que vale para todas as fases (guardrails, sem exceção)

- Uma tarefa por sessão, ritmo humanizado, tela verificada antes de
  cada toque, sem rajada e sem retry apressado.
- Nada publica, responde preço/reserva/encontro/pagamento, edita ou
  apaga conteúdo publicado, paga ou impulsiona sem aprovação do texto
  e da mídia exatos.
- Uma conta, um aparelho, uma sessão por vez, em horário normal; nada
  de conta falsa, proxy para mascarar origem, spoofing, "stealth
  humanizer" ou engajamento artificial.
- Sem dado pessoal de comprador no repositório e no painel; notas de
  trabalho por lead ficam no Drive privado do usuário.
- Todo teste vira registro em `experimentos/` e entrada no RELATORIO.md
  — o que não foi registrado, não conta como provado.
- Falhar fechado: na dúvida, parar e chamar o humano, nunca acelerar
  publicação para compensar custo, atraso ou falha.
