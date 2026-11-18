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
- **Nuances:** C2 "confirme os dados acima" aponta para lista duas seções
  acima da Amostra; v11 usa "transferência" enquanto # Limites diz "Nunca
  diga que vai transferir a pessoa para um humano" (compatíveis — momento
  interno vs. o que ela diz à lead; observar no teste).
