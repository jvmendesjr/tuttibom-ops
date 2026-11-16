# Frentes ativas — DeskcommCRM / TuttiBom

> Registro de reivindicação de módulos entre agentes. Antes de mexer num
> módulo, confira aqui; não toque em arquivo reivindicado por outro.
> Pontos de acoplamento (organizations.settings, supabase/baseline.sql e
> migrations, funções SQL compartilhadas, catálogo MCP) têm um dono por vez.

| Módulo | Dono | Arquivos | Branch/worktree | Início | Estado |
|---|---|---|---|---|---|
| P7 — vocabulário canônico de tags (ação adicionar, tela Tags, migration 9224) | autor do handover (intocável até liberar) | lib/schemas/tags.ts; app/api/v1/tags/vocabulario/route.ts; fn_vocabulario_de_tags_operar + migration ..._9224_adicionar_etiqueta_no_vocabulario.sql + apêndice no baseline.sql; app/app/settings/tags/_painel.tsx; lib/operacao/marcadores-e-time.ts; tests/unit/tags-vocabulario*.test.ts(x) | local/v1.20.0-petemcasa (HEAD fc4a4e0b6) | 2026-11-16 (registro) | em andamento |
| Varredura agendada do gestor + mcp-ultima-varredura.json | autor do handover | rotina 08/14/20h | — | — | fora do escopo do TuttiBom Ops |
| fb_agent.py / Camofox | autor do handover | — | — | — | fora do escopo do TuttiBom Ops |
| Criativo e fluxos sociais (Facebook → Instagram) — pesquisa Gamma + persona; F1 a refazer | TuttiBom Ops | docs/plano-social-facebook-instagram.md; docs/pesquisa-criativo-gamma-persona.md; criativos/f1-lote-01.md (registro; a refazer) | só docs por enquanto | 2026-11-16 | pesquisa Gamma + persona; F1 a refazer |
