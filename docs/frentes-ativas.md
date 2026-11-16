# Frentes ativas — DeskcommCRM / TuttiBom

> Registro de reivindicação de módulos entre agentes. Antes de mexer num
> módulo, confira aqui; não toque em arquivo reivindicado por outro.
> Pontos de acoplamento (organizations.settings, supabase/baseline.sql e
> migrations, funções SQL compartilhadas, catálogo MCP) têm um dono por vez.

| Módulo | Dono | Arquivos | Branch/worktree | Início | Estado |
|---|---|---|---|---|---|
| P7 — vocabulário canônico de tags (ação adicionar, tela Tags, migration 9224) | autor do handover (intocável até liberar) | lib/schemas/tags.ts; app/api/v1/tags/vocabulario/route.ts; fn_vocabulario_de_tags_operar + migration ..._9224_adicionar_etiqueta_no_vocabulario.sql + apêndice no baseline.sql; app/app/settings/tags/_painel.tsx; lib/operacao/marcadores-e-time.ts; tests/unit/tags-vocabulario*.test.ts(x) | local/v1.20.0-petemcasa (HEAD fc4a4e0b6) | 2026-11-16 (registro) | concluída 2026-11-16 ~09:07 (arquivos seguem intocáveis) |
| Varredura agendada do gestor + mcp-ultima-varredura.json | autor do handover | rotina 08/14/20h | — | — | fora do escopo do TuttiBom Ops |
| fb_agent.py / Camofox | autor do handover | — | — | — | fora do escopo do TuttiBom Ops |
| Criativo e fluxos sociais (Facebook → Instagram) | TuttiBom Ops | docs/plano-social-facebook-instagram.md; docs/pesquisa-criativo-gamma-persona.md; docs/pesquisa-video-referencias.md; criativos/ | worktree /home/pc/Workspace/tuttibom-ops-social (social/fb-ig) | 2026-11-16 | próxima: nova capa da Página; config. via Camofox em janela combinada com o dono do profile-fb |

## Divisão de automações sociais (2026-11-16)

- Zernio (outro agente): só Messenger.
- Camofox/TuttiBom Ops: configurações da Página (capa, bio, categoria, rótulo IA).
- Uma única automação responde por conversa (Zernio ou Ana, nunca os dois).
- Troca da capa A3b: aguardando janela com o profile-fb livre. Script pronto, não executado: `scripts/fb_trocar_capa.py` (`--dry-run` só faz a pré-checagem).
