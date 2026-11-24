# Setor 8 — Plataforma e Manutenção

**Objetivo:** o sistema se manter de pé, seguro e observável — e
ninguém prometer o que a plataforma não entrega.

## Entra / Sai

- **Entra:** erro, lentidão, alerta de plataforma, bloqueio de conta,
  pedido de mudança técnica, nova ferramenta.
- **Sai:** diagnóstico honesto (o que foi checado, o que foi provado,
  o que segue desconhecido), sistema de volta ao ar ou o bloqueio
  registrado com o próximo passo.

## Faz

- Manter o CRM próprio (código em `src/tuttibom/`, schema em
  `db/schema.sql`, na worktree `exp/crm-proprio`): sem segredo no git,
  sem dado de comprador no repo, sem expor o MCP em porta de rede
  (stdio local, só leitura, só indica).
- Manter as ferramentas que não mudam: 9Router (túnel
  `9router.petemcasa.com` → `127.0.0.1:20130`), Jev (CLI no PC,
  decisor tipado — nunca escreve texto livre nem aprova publicação),
  Camofox como navegador único (D-004; perfis `profile-fb` e
  `profile-panel` separados; display virtual Xvfb, nunca o :0 real),
  Drive como arquivo de criativos, WAHA standalone (:3005) e Zernio
  (Messenger, IA pausada no canal até decisão em contrário).
- Observabilidade: painel só leitura, só o Muse edita; contadores de
  falha e saúde do sistema visíveis; sem dado de comprador no painel.
- Segurança da Ana na nova vertente: a lição do Deskcomm vale aqui —
  fora de tópico, injeção de prompt e drenagem de tokens precisam de
  trava determinística, não só de linha no prompt. Teto de turnos por
  conversa e custo visível do modelo entram no desenho do CRM próprio,
  não ficam para depois.
- Git e worktrees: cada frente numa worktree e num branch separados,
  a partir da `main`; ninguém commita por outro; o Muse revisa, junta
  e dá push. `ESTADO.md`, `roadmap.md` e `decisoes/` só mudam com a
  decisão registrada.

## Não faz

- Não atende cliente, não cria conteúdo, não decide preço ou prazo.
- Não toca na produção (Deskcomm, WAHA, Zernio, número, página) sem
  decisão separada do usuário.
- Não mexe no S10/ADB sem decisão nova (pausado, D-004), não toca no
  PQBR2, não cria empresa ou agente no Paperclip sem ordem explícita.
- Não faz `git pull` no branch local do Deskcomm, migration direto no
  banco de produção, nem `docker compose down -v`; nunca desliga o
  `cloudflared-ponte` sem aprovação.

## Skill e diretório

- `AGENTS.md` (raiz do repo), `skills/tuttibom-observabilidade/`,
  `skills/tuttibom-navegacao-camofox/`, `skills/typesafe-ai/`,
  `docs/operacao/` — o mapa de onde está tudo vive no `tuttibom-mcp`
  (tools `estado` / `onde_esta_tudo` / `decisoes`).
- Hindsight bank `tuttibom` para memória de decisões e lições,
  sanitizada, sem segredo e sem dado de comprador. Bank separado para
  o teste, se o teste poluir a memória viva — a decidir quando o
  primeiro retain do teste for feito.

## Aprovações

- Qualquer mudança de infra, de ferramenta ou de acesso passa pelo
  usuário. Deploy em produção, só com aprovação separada.
- Nova ferramenta só entra após verificar que não quebra as que
  já funcionam.

## Como se mede que deu certo

- Sistema no ar após cada mudança, com `make check` passando no que
  a mudança tocou; falha registrada com causa, não com palpite.
- Nenhum segredo e nenhum dado de comprador no repo, no painel ou no
  Hindsight — verificado, não afirmado.

## Handoffs

- Falha que trava atendimento ou venda → avisa o usuário com o que
  foi checado e o que falta, e pausa o setor afetado até resolver.
- Mudança que afeta outro setor → registra na decisão e atualiza o
  documento do setor afetado, não só na memória.
