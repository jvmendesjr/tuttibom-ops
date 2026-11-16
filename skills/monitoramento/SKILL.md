# Skill: monitoramento

Monitorar, sem publicar: email da conta, perfil/notificações da
plataforma e métricas de alcance. Leitura e registro apenas.

## Canais

1. **Email (Meta/Facebook), mesma regra das redes:** monitoramento
   no celular via ADB, só leitura (rotina R-07b) — abrir o app de
   email do S10, buscar por remetente Meta/Facebook, listar assunto
   e data, ler só o corpo relevante. Sem conector de email separado
   na VM. Pré-requisito: app de email do S10 configurado com a caixa
   da conta (laboratório, na fase de testes); enquanto não estiver,
   o canal 2 cobre o essencial.
2. **Perfil/notificações no app (ADB, rotina R-07):** notificações da
   plataforma, estado do perfil/Página, estado dos anúncios no
   Marketplace. Só leitura, via `skills/s10-navegacao/`.
3. **Métricas (ADB, rotina R-08):** Insights da Página (alcance,
   visualizações, interações por post, seguidores) e, quando a tela
   mostrar, visualizações e mensagens por anúncio. Registrar o que a
   tela de fato mostra, com data — nunca número solto.

## Rotinas

- **R-07 — Checar plataforma:** Feed → notificações da plataforma →
  perfil/Página → anúncios. Nada publicado, nada respondido.
- **R-08 — Ler métricas:** Página → Insights → por post. Uma linha
  por post/anúncio em `ops/monitoramento.md`, com variação desde a
  última leitura.

## Reação da plataforma (incluída nesta skill, não numa skill solta)

Descobrir a reação é parte do monitoramento — por isso vive aqui,
em `docs/reacao-plataforma.md`, e não numa skill separada que
duplicaria o mesmo trabalho.

- Método: linha de base → uma intervenção por vez → leitura em 24 h
  e 72 h, no mesmo horário aproximado, comparando com post/anúncio
  do mesmo tipo.
- Rotina R-09 — Medir reação: registrar base, intervenção, 24 h e
  72 h em `ops/reacao-plataforma.md`.
- Antes de culpar a plataforma, checar confundidores: dia/horário,
  formato, primeira foto/frase, preço visível, frequência, evento de
  conta, sazonalidade.
- Reação só vira regra após 3 intervenções comparáveis, sem
  confundidor dominante. Antes disso, é hipótese.
- Nunca provocar a plataforma para testar reação: nada de conteúdo
  arriscado "para ver se cai", volume forçado ou teste de limite.

## Registro e alerta

- Tudo em `ops/monitoramento.md`; aviso/restrição também em
  `ops/saude-da-conta.md`.
- Alertar o usuário na hora quando: remoção, aviso, restrição,
  verificação, login suspeito, mensagem da plataforma pedindo ação,
  queda brusca de alcance após evento de conta.
- Frequência de partida: 1 vez por dia, em horário normal, junto com
  a triagem — nunca em rajada.
- Nunca: impulsionar, pagar anúncio, gerar engajamento artificial ou
  alterar a conta a partir do monitoramento.
