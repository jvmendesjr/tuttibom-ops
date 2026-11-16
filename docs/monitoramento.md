# Monitoramento: email, perfil e métricas

> Sim, dá para monitorar os três. Mas cada canal tem um pré-requisito
> diferente — e nenhum deles publica nada. Monitoramento é só leitura.

## Canal 1 — Email da conta (mensagens da plataforma)

**Regra decidida em 2026-10-30: o email segue a mesma máxima das
redes sociais neste projeto.** Ou seja: monitoramento no celular,
via ADB, só leitura — não por um conector de email separado na VM.
Isso mantém o caminho único do experimento e dispensa a conexão do
Gmail neste ambiente (verificada como não conectada em 2026-10-30).

**O que monitorar:** emails da Meta/Facebook sobre a conta e os
anúncios: anúncio removido ou em revisão, aviso, restrição, login
novo ou suspeito, alteração de senha, confirmação de publicação,
mensagem sobre a Página.

**Como, via ADB (rotina R-07b, só leitura):**
1. Ponto seguro, rotina R-02.
2. Abrir o app de email do S10, na caixa da conta do Facebook
   (conta de laboratório, na fase de testes).
3. Buscar por remetente Meta/Facebook, período recente, e listar
   assunto e data — sem abrir em cadeia, sem marcar como lido em
   massa, sem mover ou apagar nada.
4. Ler o corpo só do que for plataforma ou segurança. Newsletter e
   promoção não entram no log.
5. Voltar ao ponto seguro e fechar a sessão de monitoramento.

**Regras:**
- Código de verificação que aparecer em email nunca é copiado,
  encaminhado ou usado fora do fluxo de login que o pediu.
- Cada achado relevante vai para `ops/monitoramento.md` e, se for
  aviso/restrição, também para `ops/saude-da-conta.md`.
- Email no celular tem a mesma proteção da conta que o Facebook:
  uma sessão por vez, horário normal, sem rajada, e parar diante de
  qualquer pedido de senha, código ou documento.

**Se o app de email do S10 ainda não estiver configurado com a caixa
da conta:** isso é pré-requisito manual do usuário, como o login no
Facebook/Messenger — e o canal 2 (notificações no app) cobre o
essencial enquanto isso, com atraso menor inclusive.

## Canal 2 — Perfil e notificações no app (via ADB, só leitura)

**O que monitorar, rotina R-07:**
1. Ponto seguro (Feed), rotina R-02.
2. Abrir notificações e listar as da plataforma (não as de amigos):
   remoção, revisão, aviso, restrição, login, Página.
3. Abrir o perfil / a Página e verificar: foto, nome, estado visível,
   e se há banner de restrição ou de revisão pendente.
4. Abrir o Marketplace e listar os anúncios ativos, com estado
   (ativo / em revisão / removido / vendido).
5. Não tocar em publicar, responder ou confirmar nada nesta rotina.
   Monitoramento que publica não é monitoramento.

**Frequência de partida (fase de testes):** 1 vez por dia, em horário
normal, junto com a triagem de inbox — nunca em rajada, nunca de
madrugada só porque o agente está livre. Se houver aviso, a
frequência não aumenta: o que aumenta é a atenção humana.

## Canal 3 — Métricas e alcance (via ADB, só leitura)

**O que monitorar, rotina R-08, na Página:**
- Alcance e visualizações da Página e por post (o que a tela de
  Insights do app de fato mostrar — nomes exatos variam por versão
  do app e tipo de Página; registrar o que a tela mostra, não o que
  a gente esperava que mostrasse).
- Interações por post: curtidas, comentários, compartilhamentos.
- Seguidores: total e variação desde a última leitura.
- Por anúncio no Marketplace: visualizações e mensagens recebidas,
  quando a tela mostrar — não confundir com alcance da Página.

**Como interpretar (para não se enganar com número bonito):**
- Comparar sempre com a leitura anterior, no mesmo horário
  aproximado: alcance de hoje vs. alcance da última leitura, post a
  post.
- Registrar em `ops/monitoramento.md` uma linha por post/anúncio,
  com data, alcance, interações e variação — nunca um número solto
  sem data.
- Alcance sem interação é só exposição; interação sem pergunta ou
  venda é só atenção. O que importa para este projeto, em ordem:
  1. perguntas de interessados, 2. interações, 3. alcance.
- Um post com alcance alto e zero perguntas ensina algo sobre o
  conteúdo (chamada fraca, preço ausente, foto confusa) — registrar
  a hipótese no experimento, não comemorar o alcance.
- Queda brusca após aviso/restrição: registrar como evento de saúde
  da conta, não como "o algoritmo mudou".

**O que o monitoramento NÃO faz:**
- Não compra alcance, não impulsiona post, não paga anúncio sem
  aprovação explícita e separada.
- Não gera engajamento artificial para inflar métrica.
- Não altera nada na conta: é leitura, registro e alerta ao usuário.

## Alerta ao usuário

Monitoramento bom é o que avisa na hora certa, não o que gera
relatório todo dia. Avisar imediatamente quando:
- anúncio removido, em revisão longa ou com aviso;
- restrição, verificação ou login suspeito;
- mensagem da plataforma pedindo ação;
- queda brusca de alcance após um evento de conta.

O resto vai para o log semanal, resumido em `RELATORIO.md`.
