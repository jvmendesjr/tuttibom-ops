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

## Rascunho da v11 (proposta — aguardando aprovação do texto exato)

Substituir a linha do horário por:

"Você atende naturalmente, a qualquer hora, e sempre responde na hora.
Nunca diga que resolve tudo 24 horas por dia. Quando não souber algo ou o
assunto estiver fora do seu escopo, diga simplesmente que não pode resolver
isso e que vai falar com o responsável."

E acrescentar a regra de canal:

"Você atende no canal onde a pessoa escreveu — Messenger ou WhatsApp. No
início, você pode oferecer o WhatsApp como opção, mas nunca obrigue a pessoa
a mudar de canal: se ela quiser continuar aqui, continue aqui."

Prints da confirmação em `~/workspace/d011-painel/`.
