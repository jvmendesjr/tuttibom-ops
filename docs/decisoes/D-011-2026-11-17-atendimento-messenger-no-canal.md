# D-011 — Atendimento no Messenger, no canal onde a pessoa escreveu

Data: 2026-11-17. Decisão do usuário; arquitetura fixa.

## Contexto

Hoje o Messenger (via Zernio) está com a IA pausada e as mensagens vão para
atendimento humano. A Ana atende o WhatsApp 24/7. O risco: empurrar quem
escreve no Messenger para o WhatsApp e perder a pessoa no caminho.

## Decisão

O atendimento acontece **no canal onde a pessoa escreveu** — a Ana (ou outro
agente) atende por mensagem no Messenger. O WhatsApp pode ser informado no
início como opção, mas nunca como obrigação: se a pessoa quiser continuar no
Messenger, continua. Não obrigar a pessoa a ir para o WhatsApp.

## Plano (não executado — só planejamento)

1. Conferir o prompt da Ana v10 para o Messenger: a saudação oferece o
   WhatsApp como opção, nunca como exigência.
2. Ligar a IA no canal Zernio no painel (ação que muda comportamento ao vivo;
   execução com aprovação do usuário).
3. Testar com mensagem real e conferir o roteamento e a resposta.
4. A mesma regra vale para o Instagram quando conectar (DMs no canal).

O fallback humano continua existindo (handoff). Em aberto: ajuste de prompt
específico para Messenger? Quem atende se a Ana cair?

## Passo 1 — confirmado no painel (2026-11-17 ~21:00, só leitura)

- **O prompt da Ana é ÚNICO — não existe um por canal.** Uma só agente
  (Ana, cartão único, selos `default` e `Publicado`, tipo `rag_bot`) em
  `/app/ai/agents`; um único campo de prompt, "As instruções dele"
  (12.448/20.000 caracteres, ~2.939 tokens). O controle de IA por canal é
  só liga/desliga (diálogo "Acesso da IA nesta rede": "Pausar respostas da
  IA" / "Liberar atendimento ao público", sem campo de prompt nem seletor
  de agente). **Consequência: a v11 mexe no prompt dos dois canais juntos**
  (WhatsApp e Messenger usam a mesma Ana e o mesmo prompt). Cartões em
  Conexões → Redes sociais: WhatsApp "IA aberta ao público", Facebook
  "IA pausada".
- **Versão viva: a v10 ESTÁ publicada** — selo "Publicado v10 (rascunho v5
  superado)", "Sem rascunho para publicar." O "rascunho" do espelho local
  estava desatualizado; o painel é a fonte da verdade. **Não existe espelho
  local do texto do prompt** (grep não achou nada em `tuttibom-ops` nem em
  `DeskcommCRM`). A data/hora exata da publicação da v10 não foi confirmada
  no painel (memória diz ~15:08 de 2026-11-17; aba Histórico não foi lida).
- **Frase do canal, exata no painel:** "Se perguntarem o horário de
  atendimento, explique: aqui no WhatsApp o atendimento é 24 horas, mas os
  assuntos de produção e os detalhes da produção são resolvidos só no
  horário comercial. Quando o assunto for de produção, diga que quem resolve
  é a equipe técnica ou o gerente, no horário comercial." **Nenhuma menção
  a "Messenger" e nenhuma regra de ficar no canal de origem** em todo o
  prompt lido.
- **Achado extra:** o cartão do Facebook no painel ainda exibe "TutiBom"
  (um T) — a renomeação não se propagou para o display do painel. Há um
  botão Renomear; decisão do usuário pendente.

## Regras da Ana para a v11 (usuário, 2026-11-17 ~21:04)

1. Nunca se apresentar como assistente virtual de cara — não esconder, não
   escancarar; só dizer se perguntado (reafirma a regra de 2026-11-07).
2. Nunca dizer que resolve 24h — ela atende naturalmente e sempre responde
   na hora; quando não souber ou estiver fora do escopo, diz que não pode
   resolver e vai falar com o responsável, simples assim.
3. Sem API da Meta — Zernio + Deskcomm + Camofox são as formas alternativas;
   regras de plataforma da Meta (janela 24h, tags) são operacionais, não
   entram no texto do prompt.
4. Sem frase negativa sobre 24h (correção do usuário, 2026-11-17 ~21:07) —
   não precisa constar; ela atende sem restrição de horário; só a
   transferência para responsável/especialista respeita o horário comercial.
   Enxugar o prompt ao máximo para garantir atendimento rápido, sem perder
   qualidade nem trazer risco ao atendimento.

## Base da v11 — pesquisa de melhores práticas (2026-11-17)

Pesquisa de mercado e comunidade (página "Boas práticas — Ana no
Messenger"): consenso é um só núcleo de prompt/persona com bloco curto por
canal injetado como variável; atender sempre no canal de origem; WhatsApp só
como opção, 1x por conversa; handoff na primeira vez que o cliente pedir,
quando a IA não souber, em reclamação/reembolso/cancelamento/desconto fora
de tabela/prazo não confirmável — sempre com histórico. Ajustes pelas regras
acima: fora a divulgação de IA na primeira mensagem (recomendação da
pesquisa) e fora qualquer menção a "resolve 24h". Ressalvas: páginas
oficiais da Meta não foram abertas diretamente (citations secundárias
convergentes); divergência não resolvida sobre divulgação de IA no WhatsApp.

## Rascunho da v11 — APROVADO 2026-11-17 ~21:09 (aguardando publicação — clique do usuário; em aberto publicar agora ou aguardar as propostas de enxugamento)

Substituir a linha do horário por (revisado 2026-11-17 ~21:07 — fora a frase
negativa sobre 24h):

"Você atende sempre que a pessoa escrever — não há restrição de horário
para atender. Quando não souber algo ou o assunto estiver fora do seu
escopo, diga que não pode resolver isso e que vai falar com o responsável;
a transferência para o responsável ou especialista acontece no horário
comercial."

E acrescentar a regra de canal:

"Você atende no canal onde a pessoa escreveu — Messenger ou WhatsApp. No
início, você pode oferecer o WhatsApp como opção, mas nunca obrigue a pessoa
a mudar de canal: se ela quiser continuar aqui, continue aqui."

Prints da confirmação em `~/workspace/d011-painel/`.

## Revisão de enxugamento (proposta, 2026-11-17 ~21:14 — nada aplicado)

Arquivo: `~/workspace/d011-trim-proposta.md` (transcrição + cortes + totais).

- **Cobertura: só ~46% do prompt** (5.729 de 12.448 caracteres). Entre as
  capturas há saltos de ~12 linhas em média — bem mais que as "1–2 linhas"
  relatadas na exploração. O corpo inteiro de "# Quem já conhece a loja" e
  ~2/3 do bloco em inglês não foram capturados. Nenhum corte pode ser
  proposto com segurança sobre os ~54% não vistos (lacunas L1–L11 no arquivo).
- **7 cortes propostos.** Seguros (C1 estilo duplicado, C2 lista única,
  C4a pechincha): 227 caracteres, ~1% — quase não movem o total. C3 (prova
  escrita fundida): ~50, risco baixo. C4b ("regras de contato do aplicativo"):
  49, risco médio — esclarecer o que são essas regras antes de cortar.
- **O corte real é o 8A** (bloco de referência em inglês → PT-BR condensado,
  texto já redigido): −25% na estimativa conservadora, até −51% no cenário
  otimista; risco médio (condensação/tradução pode perder nuance; ~2/3 do
  bloco não lidos). **8B** (tirar os números do prompt, deixar só nos
  materiais): risco alto, NÃO recomendado sem verificar número por número e
  testar — o prompt é o único lugar garantido em todo turno.
- **A v11 aprovada é mais longa que a v10** (+140 caracteres). Com os cortes
  seguros, volta a ~−1%.
- **Recomendação:** publicar a v11 agora (desbloqueia o Messenger) e fazer o
  enxugamento como v12 — o trim exige recaptura do texto completo (rolagem
  em passos de ~200 px ou copiar o conteúdo do campo) e teste com turnos
  reais, então seria uma versão separada de qualquer jeito. A esclarecer
  antes de cortar: "regras de contato do aplicativo" e item 5 de pagamento +
  "(fastest payout, 80)".

## Espelho do texto v10 (2026-11-17 ~21:17)

Texto completo colado pelo usuário no chat; salvo em
`docs/ana-prompt-v10.md` (cópia literal do texto vivo no painel; fonte da
verdade continua sendo o painel). Resolve as lacunas L1–L11 da revisão de
enxugamento: "(fastest payout, 80)" era "D0"; item 5 de pagamento é "Never
claim payment was received without confirmation."; "regras de contato do
aplicativo" segue sem definição no prompt. Finalização da revisão de
enxugamento encomendada com o texto completo.

## Proposta da v12 (2026-11-17 ~21:25 — nada aplicado, nada publicado)

Arquivos: `~/workspace/d011-v12-proposta.md` (texto completo + variantes +
riscos), `~/workspace/d011-v12-rag-entrega.md` (documento RAG),
`~/workspace/d011-v12-prompt.txt` (texto puro da v12-B, pronto para colar).

- **v12-B (recomendada): 7.250 caracteres, −42% vs v10** (v10: 12.448; v11
  aprovada: 12.553, +1%; v12-A só cortes seguros: 12.186, −2%). Prompt com
  comportamento + caminho rápido local; referência num só documento RAG
  (7.149 caracteres).
- **Vereditos finais:** C1 −90 (sem risco); C2 −62 (baixo); **C3 revisado:
  NÃO fazer** (economiza 1 caractere); C4 −17 (C4a −67; C4b resolvido —
  "siga as regras de contato do aplicativo" não tem definição em lugar
  nenhum; o roteiro documenta a cadência "no máximo 3 toques em 2 dias,
  sempre com algo útil, e pare quando a pessoa responder"; o Fluxo A ainda
  é rascunho, então nada impõe a regra fora do prompt — a v12 escreve a
  regra por extenso); C5 (novo, ressalva da amostra fundida) −198 (baixo);
  **8A-novo −4.936** (bloco inglês 6.467 → PT-BR enxuto 1.531 + RAG).
- **Correção:** "30–35 dias" de importação CONSTA em `docs/prazos.md` (a
  busca anterior usou "30 a 35"). Os únicos números que só existiam no
  prompt são os rótulos Tier A/B — passam a viver no RAG.
- **Notas fora do prompt e fora do RAG** (vivem nos docs do projeto):
  "Urgency fee NOT decided (25%)" → `docs/prazos.md`; "No real link can
  carry a value until the Facebook price is decided" → status do projeto.
- **Decisão pendente:** publicar a v11 agora ou aprovar a v12-B e publicar
  ela direto (inclui as mudanças da v11 — publicar a v11 fica sem sentido).
  Pré-requisitos da v12-B: carregar o RAG como material da Ana no Deskcomm
  + testar com turnos reais (preço, prazo com/sem estoque, PAC, SEDEX,
  Correios, cor a importar, Mercado Pago, amostra, pechincha). Publicar o
  Fluxo A é item separado (quando publicado, a cadência passa a ser imposta
  pelo sistema).

## v12-B aprovada (2026-11-17 ~21:43 — direto, sem publicar a v11)

Sequência: (1) carregar o RAG como material da Ana no Deskcomm; (2) testar
com turnos reais; (3) publicar a v12-B no painel (clique do usuário).
Verificação do mecanismo de carga de material delegada às 21:43 (só leitura
no painel, sem editar nada) — o procedimento exato volta para aprovação
antes de qualquer carga.

**Decisão do usuário (2026-11-17 ~21:52): publicar a v11 primeiro, depois
a v12, para o histórico do painel ficar v10 → v11 → v12.** Motivos: cada
versão é um checkpoint; se a v12 der problema, o retorno é para a v11 (e
não para a v10, que tem a frase errada sobre o WhatsApp); separa os dois
riscos (v11 testa horário + canal, v12 testa o RAG). Texto da v11 pronto
para colar em `~/workspace/d011-v11-prompt.txt` (12.553 caracteres, diff
confere exatamente as duas mudanças aprovadas). Messenger com IA pausada
até a v12 estar publicada e testada. Nova sequência: (1) publicar a v11
(clique do usuário); (2) carregar o RAG; (3) testar a v12-B; (4) publicar
a v12-B (clique do usuário).

## v11 publicada (2026-11-17 ~22:17, pelo usuário)

O usuário colou o texto da v11 (`d011-v11-prompt.txt`, 12.553 caracteres) no
campo "As instruções dele" e publicou. **Verificação 22:20 — v11 CONFIRMADA
publicada (só leitura):** selo "Publicado v11 (rascunho v5 superado)",
contador 12.553/20.000 (~2.959 tokens), seção "# Canal" presente no texto
e o trecho final da regra nova de horário visível; sem divergências. Prints
em `~/workspace/d011-painel/v11-publicada.png` e
`v11-publicada-canal.png`.
**Mudança de plano (22:17): o usuário vai colar as demais ele mesmo** —
v12-B e RAG passados no chat. Ordem: carregar o RAG (IA › Conhecimento →
"+ Adicionar material" → Documento → nome "Prazos, pagamento e entrega" →
colar o texto em "...ou cole o texto aqui" → "Adicionar ao acervo" →
preparar e confirmar "O agente já sabe", trechos > 0) e SÓ DEPOIS publicar
a v12-B (mesmo fluxo da v11). Sem o RAG preparado, a Ana não tem de onde
tirar os números de envio. **Mudança 22:19: o usuário delegou a carga do
RAG a mim** ("não sei mexer" nessa parte) — carga delegada ao painel
(upload do arquivo já no PC), sem tocar no prompt e sem publicar nada; a
publicação da v12-B continua sendo o clique do usuário.

## v12-B publicada (2026-11-17 ~23:35, pelo usuário)

O usuário colou o texto da v12-B (`d011-v12-prompt.txt`, 7.250 caracteres)
no campo "As instruções dele" e publicou — selo "Publicado v12". O RAG já
estava carregado e preparado desde ~22:53, então a publicação estava
desbloqueada. Verificação do selo e do contador (7.250/20.000) em curso
(só leitura, print em `~/workspace/d011-painel/v12-publicada.png`).
Próximo: testar com turnos reais não-locais (PAC, SEDEX, Correios, cor a
importar) e confirmar que a Ana responde com os números do RAG e que
"Consultado por" passa a mostrar Ana; depois ligar a IA no canal Zernio
(com aprovação, em horário acompanhável).

## RAG carregado e preparado (2026-11-17 ~22:53)

- **Material "Prazos, pagamento e entrega" (Documento), "O agente já
  sabe"** — preparado automaticamente logo após a criação; **23 trechos**
  (os prontos têm 22 e 16); acervo passou de 4 materiais · 2 prontos para
  **5 materiais · 3 prontos**. Conteúdo conferido: detalhe do material com
  o Markdown renderizado igual ao texto exato do RAG (início e fim
  conferidos antes de enviar). Print em
  `~/workspace/d011-painel/rag-carregado.png`.
- **Método:** upload tentado primeiro, como pedido — o drive do painel não
  tem ação de seletor de arquivos: ao clicar "Procurar...", abre o diálogo
  nativo GTK, que o drive não opera. `xdotool` instalado (sudo sem senha)
  para operar o diálogo: abriu a barra de local e digitou o caminho, mas o
  diálogo fechou sem criar o material — mecanismo exato não identificado,
  não insistido. **Cola (fallback autorizado):** reaberto o diálogo, tipo
  Documento, nome "Prazos, pagamento e entrega" (o formulário retém estado
  entre aberturas — na segunda tentativa o nome veio duplicado; corrigido
  com Ctrl+A + redigitação e conferido único), colado o texto exato do RAG
  (7.149 caracteres, início e fim conferidos no print — o placeholder
  "# Política de troca" foi substituído, não somado) e clicado "Adicionar
  ao acervo". Criou e preparou sozinho, sem "Preparar de novo".
- **Divergência — "Consultado por: nenhum assistente ainda":** na tela da
  Ana não existe seletor por material; a porta é a capacidade "Consultar o
  que a empresa já sabe" (`crm_search_knowledge`), já ligada. A evidência
  indica que "Consultado por" é por **uso**, não configuração: "Base de
  conhecimento" e "FAQ" (usados em conversas reais) mostram Ana; "Memória
  por contato" (nunca preparado) mostra nenhum; "Conversas anteriores"
  (nunca preparado, mas a Ana lê o histórico em todo turno) mostra Ana.
  Nada a ligar — o campo deve virar "Ana" na primeira consulta real, que
  é o teste da v12 (turno não-local: PAC, SEDEX, Correios ou cor a
  importar). Único item que depende da fase de teste para confirmar.
- **Nada mais tocado:** prompt da Ana intacto, nenhum clique em
  "Publicar", IA do Messenger não ligada, nenhum outro material editado.
  Loop do painel vivo e livre no fim (navegador na página de Conhecimento).
  Serialização respeitada com a verificação da v11 (~4,5 min de espera).

## Verificação do mecanismo de carga do RAG (2026-11-17 ~22:09 — só leitura,
nada editado, nada publicado, nenhum upload)

- **Materiais vivem em IA › Conhecimento** (`/app/ai/knowledge/sources`,
  página "O que o agente sabe") — não na página da Ana nem em Configurações.
  Acervo atual: 4 materiais, 2 prontos — "Base de conhecimento TuttiBom"
  (Documento, "O agente já sabe", 22 trechos, consultado por: Ana) e "FAQ
  TuttiBom" (Perguntas e respostas, 16 trechos, Ana); "Memória por contato"
  e "Conversas anteriores" estão "Ainda não preparado" (0 trechos).
- **Como se adiciona:** "+ Adicionar material" → diálogo "Ensinar algo novo
  ao agente", 4 tipos; **Documento**: "Envie o arquivo (PDF, Markdown, CSV
  ou texto) ou cole o conteúdo" — até 20 MB, sem limite visível no campo de
  colar. Botões "Cancelar" / "Adicionar ao acervo".
- **O RAG pode ser carregado:** arquivo `.md`, 7.149 caracteres / 7.410
  bytes, muito abaixo de 20 MB. Recomendado o upload (o painel guarda o
  original, igual à "Base de conhecimento TuttiBom"). **Arquivo já no PC:**
  `/tmp/d011-v12-rag-entrega.md`, sha256 `ffcddfca55f49c6abff1252c3e8fe92ab
  0ea7156eff34235abe2fef74b98d3ff`, idêntico ao da VM.
- **A Ana vai consultar o material novo:** capacidades "Consultar o que a
  empresa já sabe" (`crm_search_knowledge`) e "Ver os materiais
  cadastrados" (`crm_list_knowledge_sources`) já LIGADAS em Capacidades ›
  "Aprender e evoluir". Não há seletor por material — a capacidade é a
  porta, já ligada. O preparo é pela OpenAI (chave da instalação).
- **Procedimento exato:** A) publicar a v11 (Ana → Configuração →
  "Conversar com o cliente" → campo "As instruções dele" (12.448/20.000)
  → colar a v11 → "Salvar rascunho" → "Publicar"; o selo deve passar a
  "Publicado v11". B) carregar o RAG (IA › Conhecimento → "+ Adicionar
  material" → Documento → nome "Prazos, pagamento e entrega" → upload de
  `/tmp/d011-v12-rag-entrega.md` → "Adicionar ao acervo" → preparar
  ("Preparar de novo" se não disparar sozinho) → confirmar "O agente já
  sabe", trechos > 0 e "Consultado por: Ana"). C) publicar a v12-B (mesmo
  fluxo de A, texto em `d011-v12-prompt.txt`, 7.250 caracteres — cabe no
  limite de 20.000) e testar com turnos reais não-locais.
- **Observações (não são bloqueios):** "Procurar produto na loja" está com
  1 falha em Capacidades (1 de 4 tentativas, última 07/11) — pré-existente,
  vale olhar antes do teste da v12, porque o prompt enxuto depende do
  catálogo para preços. "Memória por contato" existe como material, mas
  nunca foi preparada (0 trechos, nenhum assistente) — pendência conhecida.
- Prints da verificação em `~/workspace/d011-painel/` (`v12-ana-top.png`,
  `v12-conhecimento.png`, `v12-add-doc4.png`, `v12-add-doc5.png`,
  `v12-ler-bc2.png`, `v12-ana-lista2.png`, `v12-ana-lista3.png`).
- **Nuances:** C2 "confirme os dados acima" aponta para lista duas seções
  acima da Amostra; v11 usa "transferência" enquanto # Limites diz "Nunca
  diga que vai transferir a pessoa para um humano" (compatíveis — momento
  interno vs. o que ela diz à lead; observar no teste).

## Ana não responde no WhatsApp (2026-11-18 ~00:25) — causa raiz: o modelo

Dois testes do usuário ("Oi teste" 00:25 e "Olá" 00:43, conversa
3577efc6, Junior +5588997111267) receberam só o ack ("Só um instante" /
"Vou verificar"). Investigação no log e no banco do 9Router:

- O combo `core-medio` no 9Router hoje é UM modelo só:
  `cu/cursor-grok-4.5-high` (Cursor AgentService; combo mexido na noite
  de 17/11, última edição 2026-11-18 00:21 -03). Chamadas sem ferramentas
  funcionam (Hermes, classificadores `jailbreak_detect` /
  `stage_classifier` passam) — por isso o usuário achou que o combo
  funcionava. Mas o turno da Ana anexa as ferramentas do Deskcomm e o
  modelo rejeita com 400: "Cursor AgentService requested an unsupported
  IDE tool" / "returned an empty turn" (`modelo_sem_ferramentas`).
- Prova do turno real: o job `inbound_turn`
  (d8ac5f8d-3ec8-425f-b47c-2b69168c821f) falhou e repetiu as tentativas
  às 03:44–03:48 UTC com o mesmo 400. Os testes no modo teste
  (`agent_preview`) falham igual. O RAG e a v12 não têm nada com isso.
- Falso rastro: o `ai-response-worker` pula os turnos com
  `agent_inactive_or_missing` (`workers/ai-response-worker.ts:776`) —
  esse worker só atende agentes LEGADOS (`precisaRecuperarLegado`); a Ana
  é `rag_bot` moderna, então ele declina corretamente. O turno real é do
  `inbound_turn`, que é o que falha no modelo. O nome do motivo induz ao
  erro; não é problema de atribuição.
- Painel conferido e OK: Ana é o agente ativo da conversa (modo
  Automático, acks assinados "IA · Ana"), roteador "Roteador TuttiBom"
  ativo, WhatsApp "IA aberta ao público", chave 9Router validada,
  "22 de 27 capacidades ligadas".
- Correção pendente: trocar o modelo (combo `core-medio` no 9Router ou
  modelo da Ana no painel) por um que aceite chamadas com ferramentas, e
  testar no modo teste antes de testar no WhatsApp. Atenção: os modelos
  com prefixo `cu/` (Cursor) podem ter o mesmo problema; os candidatos
  fora do Cursor são `ag/gemini-3.8-flash-high` (core-alto) e os GLM de
  `warp`/`factory` (core-baixo) — confirmar no modo teste, não assumir.
