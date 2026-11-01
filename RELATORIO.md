# Relatório do experimento: gestão do Facebook via S10 + ADB

> Documento vivo. Criado em 2026-10-30 e atualizado à medida que testamos.
> Regra: cada teste novo entra em `experimentos/` e resume aqui em uma linha,
> com o que funcionou, o que quebrou e a lição abstraída. Nada de apagar
> fracasso: fracasso documentado é dado do experimento.

## 1. Pergunta do experimento

Até onde dá para ir gerindo o Facebook de um pequeno vendedor usando um
único caminho de execução: um Galaxy S10 Lite, operado por agente via ADB
(navegação simulada no app), sem depender de API/CLI oficial do Facebook
para publicar, responder ou postar?

## 2. Escopo decidido (2026-10-30)

- **Dispositivo:** Samsung Galaxy S10 Lite ("S10 Lite de Tutti"), Android,
  acesso via Termux + Tailscale + SSH, ADB local no próprio aparelho.
- **Apps:** Facebook (`com.facebook.katana`, já presente) e Messenger
  (`com.facebook.orca`, instalado em 2026-10-29, ainda sem abrir nem logar).
- **Produtos:** principalmente itens de impressão 3D e fitas de cetim.
- **Tarefas:** criar anúncios, tarefas relacionadas à venda, vigiar e
  responder perguntas, encaminhar interessados, navegar no Facebook para
  engajamento da Página, publicar conteúdo dos produtos, criar vídeos e
  postagens.
- **Skills externas:** as duas skills de Marketplace analisadas são
  referência para criar as nossas próprias skills, não executores
  plug-and-play deste projeto.
- **Caminho único:** execução via ADB no S10. Outras ferramentas só entram
  como pesquisa, referência ou leitura — não como atalho de publicação.

## 3. Decisões e princípios

1. **Agent first, humano no checkpoint.** O agente prepara, o humano
   aprova antes de publicar, responder comprometendo preço, reservar,
   marcar encontro ou mexer em pagamento.
2. **Rascunho antes de publicar.** Nada vai ao ar direto da primeira
   tentativa de um fluxo novo.
3. **Ler, agir, ler de novo.** Nunca agir sobre uma tela em cache.
   Depois de cada ação, reler a tela / árvore de UI e confirmar o efeito
   antes do próximo passo.
4. **Idempotência antes de velocidade.** Antes de publicar ou enviar,
   verificar se já existe rascunho, anúncio ou mensagem igual. Um toque
   repetido não pode duplicar anúncio nem mensagem.
5. **Parar é um resultado.** Tela travada, login pedido, verificação,
   screenshot vazio ou UI irreconhecível: parar, registrar e pedir ajuda
   humana. Insistir não é persistência, é risco.
6. **Sem engajamento artificial e sem evasão.** Nada de simular pessoas,
   inflar curtidas/comentários ou burlar detecção de bot. Engajamento aqui
   significa conteúdo real do produto, resposta rápida e útil, e post
   programado com revisão.
7. **Sem segredos no repositório.** Nada de senha, cookie, token, sessão
   ou captura com dados pessoais. O `.gitignore` bloqueia esses arquivos.
8. **Experimento documentado.** Cada sessão gera um arquivo em
   `experimentos/` e uma linha na seção 7 deste relatório.

## 4. O que já sabemos do dispositivo (base validada antes do experimento)

- Tela: "desbloqueado não significa acordado". Antes de cada passo de UI,
  checar vigília, acordar com `keyevent 224`, verificar, e recapturar se
  voltar preto. Timeout de tela em 5 minutos (alterado em 2026-10-29);
  a regra de acordar continua valendo após idle.
- Ações via SSH/Termux não mudam a tela; toques, teclas e aberturas de app
  via ADB são toques reais e visíveis no aparelho.
- Condições normais de acesso: aparelho ligado e carregado, internet e
  Tailscale conectados, Termux vivo com sshd rodando. Fora disso, pode
  falhar: bateria, rede, Tailscale revogado, Android matando o Termux ou
  reboot mudando a porta do ADB.
- Facebook já estava instalado; Messenger foi só instalado, sem login.
  **Pendente:** login manual no Facebook/Messenger pelo usuário antes de
  qualquer teste de publicação ou inbox.

## 5. Análise das skills de referência

### 5.1 ClawHub — ivangdavila/facebook-marketplace (o cérebro)

- Organiza o trabalho em comprador, vendedor, proteção contra golpe e
  saúde da conta, com memória para inventário, preços mínimos, modelos de
  mensagem e registro de incidentes.
- Bom para: preço pela realidade local, confirmar condição/medida/
  retirada/envio antes de fechar, não levar pagamento para fora da
  plataforma.
- Limite: é um playbook, não executa nada. E avisa explicitamente contra
  inventar API do Marketplace e contra bots, scraping após login,
  mensagens em massa, fazendas de republicação e táticas anti-detecção.
- O que abstraímos dela: estrutura de memória, faixa de preço e preço
  mínimo, triagem de comprador, diário de saúde da conta.

### 5.2 Printing Press — mvanhorn/pp-facebook-marketplace (a mão, fora do S10)

- Promete um CLI com trava de escrita para buscar, criar anúncio, subir
  foto, vigiar anúncios e responder.
- Limites para este projeto: usa sessão do navegador Chrome como
  credencial (desktop, não app Android via ADB), é superfície não oficial
  do Facebook e a página pública é só um resumo — exige auditoria do
  código antes de qualquer uso em conta principal.
- O que abstraímos dela: trava de escrita e checkpoints antes de
  publicar/responder, e a ideia de "vigia" local de anúncios.

### 5.3 agent-reach (pesquisa, não execução)

- Não foi encontrada no catálogo local do Muse. Na comunidade, é o
  projeto Panniantong/Agent-Reach: camada de pesquisa multi-plataforma,
  com roteamento entre backends e fallback quando um quebra.
- Papel neste projeto: método de pesquisa (várias fontes ao mesmo tempo:
  web, GitHub, dev.to, redes sociais), não executor no S10.
- Pendente, se o usuário quiser: instalar e auditar a agent-reach como
  skill de pesquisa do projeto.

## 6. O que a comunidade já aprendeu (síntese, 2026-10-30)

- **Loop universal:** observar (screenshot + `uiautomator dump`) →
  decidir → agir (`tap`/`swipe`/`text`/`keyevent`) → verificar (reler a
  tela) → registrar. Agir sobre tela em cache é a causa mais comum de
  toque no lugar errado.
- **Árvore de UI vs. visão:** preferir a árvore quando ela é boa;
  cair para visão quando o app (Compose/Flutter) expõe um único nó para
  a tela inteira. Nesse caso, mover foco pelo teclado e reler a árvore.
- **Texto com acento:** `input text` é armadilha para português. Caminho
  mais são: colar via clipboard e colar com keyevent.
- **Telas seguras:** `screencap` pode voltar vazio em telas com
  FLAG_SECURE. Tratar imagem vazia como "não sei", nunca como "tela
  igual".
- **Famílias de solução:** AppAgent (visão + LLM via ADB, sem script);
  Mobile-Agent-v3 / GUI-Owl / UI-TARS e Minitap (decomposição em
  planejador/operador/verificador, benchmarks AndroidWorld — referência
  de teto, não de Facebook real); Midscene.js e Maestro (fluxos
  determinísticos em YAML, espera por tela estável, via UIAutomator);
  Appium + UiAutomator2 (padrão pesado, seletores estáveis); Google
  Artemis (agente open source via ADB com MCP, modos Flash reativo e Pro
  multi-agente com verificação — referência de arquitetura, com
  controvérsia de autoria a verificar antes de copiar código).
- **Anti-padrão descartado:** "humanizador stealth" para burlar detecção
  de bot e gerar engajamento artificial. Fora do experimento.
- **Conclusão prática para nós:** tarefa repetida (criar anúncio) pede
  fluxo determinístico mapeado uma vez; tarefa exploratória (achar uma
  conversa, entender um erro) pede agente de visão com verificação.

## 7. Diário de testes (resumo — detalhe em `experimentos/`)

| # | Data | Teste | Resultado | Lição abstraída |
|---|------|-------|-----------|-----------------|
| 0 | 2026-10-30 | Criação do repositório e das skills | Repositório e relatório criados; testes no S10 ainda não executados | Documentar antes de automatizar: o relatório é o ponto de partida, não o epílogo |
| — | — | (próximo) Loop ADB só de leitura no Facebook | Pendente | — |
| — | — | (próximo) Rascunho de anúncio, sem publicar | Pendente | — |
| — | — | (próximo) Triagem de inbox / encaminhamento | Pendente | — |
| — | — | (próximo) Rascunho de post/vídeo da Página | Pendente | — |

## 8. Riscos em aberto

- Conta: automação por UI em app de terceiros pode gerar verificação,
  restrição ou remoção de anúncio. Mitigação: ritmo humano, checkpoints,
  nada de volume em massa, nada de evasão.
- Fragilidade: interface do Facebook muda, login expira, verificação em
  duas etapas aparece, porta do ADB muda após reboot.
- Duplicidade: sem verificação de estado antes de agir, anúncio e
  mensagem duplicam.
- Vídeo e foto: upload pelo app é o passo mais sensível a tamanho,
  formato e tempo de espera; testar com rascunho primeiro.
- Messenger sem login: inbox não pode ser testada até o login manual.

## 9. Próximos passos (ordem sugerida)

1. Usuário faz login no Facebook e no Messenger no S10.
2. Teste 1 — só leitura: abrir o Facebook, confirmar tela, voltar.
   Registrar em `experimentos/0001-loop-leitura.md`.
3. Teste 2 — rascunho de anúncio de um produto real (3D ou fita),
   sem publicar. Registrar o caminho de telas e os textos/campos.
4. Teste 3 — triagem de inbox: listar conversas, classificar, encaminhar
   sem responder comprometendo preço.
5. Teste 4 — rascunho de post/vídeo da Página, sem publicar.
6. A cada teste, atualizar a seção 7 e a skill correspondente.

## 10. Rotinas determinísticas e destravamento

Ver `docs/rotinas-deterministicas.md`. Resumo: toda tarefa usa uma
rotina nomeada (R-01 a R-06), com tela esperada por passo. Ao travar,
o agente sobe uma escada liberada até o nível 2 (esperar e reler;
ajuste de navegação; voltar ao ponto seguro ou reabrir o app, sem
descartar trabalho não salvo) e para no nível 3, chamando o humano
(login, verificação, pagamento, publicar/enviar fora do objetivo,
fechar app com rascunho aberto, reiniciar o aparelho). Limite: 3
tentativas alternativas por passo; objetivo da tarefa nunca muda em
recuperação.

## 11. Práticas para proteger a conta do laboratório

Ver `docs/praticas-conta-laboratorio.md`. Resumo: testar sempre na
conta de laboratório primeiro; promover rotina para a conta principal
só após 3 execuções limpas registradas. Uma conta, um aparelho, uma
sessão por vez, em horário normal, uma tarefa por sessão, com pausas
e sem rajada de toques. Limites de partida na fase de testes: 2
rascunhos de anúncio, 1 publicação aprovada, 10 conversas triadas e
1 rascunho de post/vídeo por dia. Nada de evasão: sem conta falsa,
sem proxy para mascarar origem, sem falsificação de dispositivo, sem
"humanizador stealth", sem engajamento artificial. A proteção vem de
agir como uso legítimo em escala humana, não de esconder o agente.
Qualquer aviso, remoção ou verificação para tudo e vai para
`ops/saude-da-conta.md`.

## 12. Monitoramento: email, perfil e métricas

Ver `docs/monitoramento.md` e `skills/monitoramento/SKILL.md`. Três
canais, todos só leitura: (1) email da conta, com mensagens da
Meta/Facebook — seguindo a mesma máxima das redes sociais: no celular
via ADB, só leitura (rotina R-07b), sem conector de email separado na
VM; pré-requisito é o app de email do S10 configurado com a caixa da
conta, e o Gmail na VM foi verificado como não conectado em
2026-10-30, por isso não é o caminho deste projeto; (2) perfil e notificações no app,
via ADB, rotina R-07 — notificações da plataforma, estado do perfil/
Página e dos anúncios; (3) métricas, via ADB, rotina R-08 — Insights
da Página (alcance, visualizações, interações por post, seguidores)
e, quando a tela mostrar, visualizações e mensagens por anúncio.
Frequência de partida: 1 vez por dia, em horário normal. Alerta
imediato para remoção, aviso, restrição, verificação, login suspeito
ou queda brusca de alcance após evento de conta.

## 13. Reação da plataforma via métricas

Ver `docs/reacao-plataforma.md`. Decisão: incluída na skill de
monitoramento, não criada como skill solta, para não duplicar o
mesmo trabalho. Método: linha de base → uma intervenção por vez →
leitura em 24 h e 72 h, comparando com post/anúncio do mesmo tipo
(rotina R-09, log em `ops/reacao-plataforma.md`). Antes de culpar a
plataforma, checar confundidores (dia/horário, formato, foto, preço,
frequência, evento de conta, sazonalidade). Reação só vira regra após
3 intervenções comparáveis, sem confundidor dominante. Nunca provocar
a plataforma para testar reação.

## 14. Guardrail para toda a operação

Ver `skills/guardrails/SKILL.md`. É a skill acima de todas as outras:
se outra skill, rotina ou passo conflitar com um guardrail, o
guardrail vence e a tarefa para para revisão. Cobre: aprovação humana
para publicar, enviar comprometendo preço, editar/apagar, pagar e
impulsionar; proibições absolutas (inventar dado, pagamento fora da
plataforma, senha/código, conta falsa, proxy, falsificação, stealth,
engajamento artificial, sessões paralelas, apagar registro); conta de
laboratório primeiro, com promoção só após 3 execuções limpas;
ritmo e limites de partida; loop de tela e escada de destravamento;
dados e privacidade; condições de parada; registro obrigatório.

## 15. Estrutura do repositório

- `skills/guardrails/` — vale para toda a operação, acima das demais.
- `skills/s10-navegacao/` — loop ADB, vigília, verificação, parada.
- `skills/facebook-vendas/` — catálogo, anúncio, triagem, encaminhamento.
- `skills/facebook-conteudo/` — roteiro, vídeo, post, fila de publicação.
- `skills/monitoramento/` — email, perfil, métricas e reação da
  plataforma (R-07, R-08, R-09).
- `skills/pesquisa-comunidade/` — método agent-reach adaptado.
- `catalogo/` — um arquivo por produto, sem preço inventado.
- `templates/` — anúncio, resposta, roteiro de vídeo, post.
- `ops/` — fila de publicação, triagem, saúde da conta, monitoramento,
  reação da plataforma.
- `experimentos/` — um arquivo por teste, com hipótese e resultado.
- `docs/` — decisões, rotinas determinísticas, práticas da conta,
  monitoramento, reação da plataforma, pesquisa de publicação e
  engajamento, pesquisa de produtos chamativos e referências.

## 16. Histórico de atualizações deste relatório

- 2026-10-30 — Criação: pergunta, escopo, decisões, base do dispositivo,
  análise das skills, síntese da comunidade, riscos e próximos passos.
  Testes no S10 ainda pendentes.
- 2026-10-30 — Adicionadas rotinas determinísticas com escada de
  destravamento (níveis 0–3) e práticas de proteção da conta do
  laboratório, com checklist de promoção laboratório → principal.
- 2026-10-30 — Adicionado monitoramento em três canais (email,
  perfil/notificações, métricas), com Gmail verificado como não
  conectado; reação da plataforma incluída na skill de monitoramento
  (método base → intervenção → 24 h/72 h); e skill de guardrail para
  toda a operação. Repositório local completo em esqueleto;
  publicação no GitHub pendente.
- 2026-10-30 — Monitoramento de email alinhado à mesma máxima das redes:
  no celular via ADB, só leitura (R-07b), sem conector Gmail na VM.
  Usuário confirmou a criação e publicação do repositório no GitHub.
- 2026-10-30 — GitHub adiado pelo usuário: repositório fica guardado
  só localmente por enquanto; a questão do GitHub será ajustada quando
  estiver disponível. Tentativa de criação no GitHub falhou antes com
  403 (app do Muse sem acesso para criar repositório).
- 2026-10-30 — Pesquisa guardada localmente: skills e melhores práticas
  de publicação no Facebook, criativos que geram engajamento, e itens
  chamativos para 3D e fitas de cetim personalizadas
  (docs/pesquisa-publicacao-engajamento.md e
  docs/pesquisa-produtos-chamativos.md). Loja vai funcionar no Cariri
  CE (Juazeiro do Norte / Crato / Barbalha).
- 2026-10-30 — Pesquisa no app do Facebook no S10, na região do Cariri,
  NÃO concluída na primeira tentativa: S10 offline via pareamento do
  Muse (visto por último em 2026-10-29 23:57 UTC) e SSH via Tailscale
  falhou no início (verificação de chave do host para o IP, timeout
  para o nome do host). Sem forçar: o aparelho precisa voltar online,
  com Termux e sshd ativos, e a chave do host precisa ser confirmada
  pelo usuário antes de nova tentativa. Instrução do usuário nesta
  data: navegar com cautela, sem pressa, em ritmo humanizado, seguindo
  as skills aprendidas.
- 2026-10-30 — Conexão estável restabelecida: o S10 estava visível na
  tailnet, mas "visível na lista" não prova sshd alcançável. Causas
  corrigidas: SSH direto não alcança a tailnet (só via proxy de túnel
  na porta 3130), host desconhecido com BatchMode falha sem perguntar,
  e encaminhador com buffer travava na troca de chaves. Solução:
  encaminhador Python sem buffer em ~/workspace/s10-tunnel-proxy.py,
  config SSH com caminhos absolutos em ~/.ssh/config, uso obrigatório
  de `ssh -F ~/.ssh/config s10`, e chave de host registrada em
  ~/.ssh/known_hosts_s10 (impressão digital ED25519 a confirmar pelo
  usuário no Termux). Ver docs/conexao-estavel.md. sshd com watchdog
  e Termux:Boot já estavam no aparelho.
- 2026-10-30 — Pesquisa no Cariri CONCLUÍDA via ADB, com o usuário
  longe do aparelho: impressão digital do host lida remotamente no
  Termux bateu com a registrada (checagem pelo mesmo canal, não fora
  da banda). Facebook aberto via ADB, aviso de email fechado sem
  confirmar, Marketplace pesquisado só em leitura, sem like,
  comentário ou mensagem. Achados: "fita de cetim" sem oferta local
  na primeira tela (resultados de Fortaleza e João Pessoa, 400–490
  km); "impressao 3d" com oferta local forte em Juazeiro do Norte
  (1–2 km), chaveiro personalizado a R$6–R$8, tema Nossa Senhora
  Aparecida em destaque. Ver
  experimentos/0001-pesquisa-cariri-marketplace.md. Armadilhas
  registradas: `uiautomator dump` falha no Facebook (só screencap)
  e `input text` com `%20` digita os caracteres literais.
- 2026-10-30 — Conclusão sobre navegação (usuário, 2026-10-30):
  a pergunta era só sobre o processo de navegação, não sobre
  pontos e ofertas — esses ficam para depois. Resposta registrada:
  navegação via ADB é viável para pesquisa, monitoramento, triagem
  e preparo de rascunho, provada pelo ciclo completo de leitura
  desta sessão; publicar/responder ainda não foi provado e depende
  dos testes de rascunho (Testes 2–4), com aprovação. Não é viável
  como automação rápida e invisível em massa, e nem deve ser, pela
  proteção da conta.
- 2026-10-30 — Teste pendente, proposto pelo usuário: deixar o S10
  parado por horas e, depois, testar se a conexão volta sem
  intervenção manual. Estado ao encerrar a sessão: app do Facebook
  parado na tela de resultados do Marketplace, tela para apagar
  sozinha em 5 minutos (timeout atual), bateria em 91% e sem
  carregamento, sem `stayon` ativado, sem trabalho não salvo. O
  que o teste vai verificar: se o sshd (com watchdog) e o Tailscale
  sobrevivem ao período parado e ao Dozing, ou se o Android mata o
  Termux e exige reabertura manual.
- 2026-10-30 — Pesquisa de interação com consumidores e ideia de
  CRM (usuário): skills do Muse lidas (`messaging`,
  `customer-outreach`, `meeting-follow-up`) e comunidade pesquisada
  (resposta em até 1h, templates, follow-up com limite, CRM de
  planilha com 1 linha por negociação e próxima ação com data).
  Proposta guardada em docs/pesquisa-interacao-crm.md, skill própria
  em skills/crm-interessados/SKILL.md e CRM ampliado em
  ops/triagem-interessados.md — 6 estágios, sem dado pessoal no
  repositório, envio só após aprovação do texto exato. Teste real
  de triagem ainda pendente de aprovação.
- 2026-10-30 — Persona de interação e planilha no Drive (usuário):
  Drive e Sheets verificados e NÃO conectados neste ambiente —
  criação da planilha só após o usuário conectar os dois (links
  entregues na conversa). Enquanto isso, tudo ficou pronto local:
  persona em docs/persona-interacao.md, skill em
  skills/persona-interacao/SKILL.md e estrutura da planilha em
  ops/planilha-crm-drive.md (5 abas: Leads, Interações, Problemas
  e Contornos, Criativos, Resumo). A persona retoma de onde parou
  por ficha por lead (onde parou, o que foi prometido, pendência,
  problema e contorno), registra problemas e contornos e trata a
  entrega de criativos como sensível (prova antes de produzir,
  foto conferida, nunca misturar clientes, feed só com
  autorização). Divisão: repositório guarda regras e padrões sem
  dado pessoal; Drive, privado do usuário, guarda as notas de
  trabalho por lead. Tudo sob as guardrails.
- 2026-10-30 — Drive conectado e planilha criada: pasta "CRM
  TuttiBom" e planilha "CRM TuttiBom — Interessados" criadas no
  Drive do usuário via conexão do Drive. As 5 abas e os cabeçalhos
  (Leads, Interações, Problemas e Contornos, Criativos, Resumo)
  ainda não foram preenchidos, porque o Sheets ainda não estava
  conectado neste ambiente — o preenchimento via API do Sheets
  fica para quando essa conexão estiver pronta, sem subir arquivo
  por cima da planilha. Estrutura pronta em
  ops/planilha-crm-drive.md.
- 2026-10-30 — Roadmap criado (usuário): docs/roadmap.md, do zero
  à loja funcionando, com prioridades marcadas. P0: fundação e
  conexão estável + catálogo real (bloqueia anúncios e respostas).
  P1: testes de laboratório em rascunho, manutenção do
  Marketplace, conteúdo e interação/CRM. P2: pontos e ofertas,
  GitHub e migração de CRM, só depois de P0/P1 provados. O roadmap
  já incorpora o resultado misto do teste de retorno após horas
  parado (SSH sobreviveu, ADB não) e a recuperação de ADB
  instalada por componente, ainda sem prova de ponta a ponta.
