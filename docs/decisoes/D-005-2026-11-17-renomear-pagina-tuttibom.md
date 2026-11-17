# D-005 — 2026-11-17 — Renomear a Página do Facebook de "TutiBom" para "TuttiBom"

**Data:** 2026-11-17
**Decisor:** usuário
**Status:** decidido; solicitação enviada ao Facebook, aguardando análise

## Decisão

Renomear a **Página** do Facebook de **"TutiBom"** (um T) para **"TuttiBom"** (dois T's). A marca continua "TuttiBom" (dois T's). **Nada de reestruturar** documentos, código, infos da Ana, Deskcomm e agentes — a renomeação é uma configuração só no Facebook.

## Contexto

- A página ligada ao Zernio e ao Deskcomm é a "TutiBom" (id 143473822920252, logo vermelho/azul, 1 seguidor). O perfil público da loja é a "TuttiBom Novidade" (tuttibom10, 518 seguidores), que é um **perfil pessoal** — e perfil pessoal nunca pode ser conectado (nem Zernio, nem Messenger Platform).
- Em 2026-11-17 08:21 o usuário apontou que o perfil da loja é a Novidade (518 seguidores) e a página conectada tem só 1 seguidor. Discutimos os dois jeitos: renomear a **marca** para um T (reestruturação grande) × renomear a **página** para dois T's (uma configuração no Facebook; o Zernio liga pelo ID da página, não pelo nome).
- O usuário decidiu (2026-11-17 08:49): "Se dá para renomear, é melhor deixar com dois T's, porque fica diferente e dá menos trabalho, correto?" + "renomer tutibom para tuttibom".

## Correção feita na mesma manhã

- Eu havia apresentado a "conversão de perfil em Página" como se levasse os seguidores junto — **errado**: o botão antigo de migração foi aposentado. Hoje só dá para criar Página nova a partir da conta; seguidores não migram sozinhos (convite, cada um aceita ou não), posts/fotos não vão junto, e a Novidade continua perfil (vira a conta administradora). Modo Profissional não resolve. Corrigido antes de o usuário decidir.

## Execução

- **Solicitação enviada 2026-11-17 ~10:16:** o usuário digitou a senha via noVNC e clicou "Solicitar alteração" (diálogo mostrava TutiBom → TuttiBom). O Facebook vai analisar (até 3 dias) e o nome só muda após aprovar; depois de aprovado, não dá para mudar de novo por 60 dias.
- Verificado ~10:16: página ainda "TutiBom" no Facebook, no Zernio (conta `6aed2e33…` ativa, page 143473822920252, messagingSubscribed) e no Deskcomm (canal `zernio_social` `a7a7d71a-…` WORKING, display `facebook · TutiBom`) — esperado. O ID da página não mudou, então a conexão não se afeta.

## O que a renomeação NÃO resolve

- A renomeação resolve o **nome**, não o **público**: os 518 seguidores continuam no perfil pessoal TuttiBom Novidade, que não conecta, e a página ligada continua com 1 seguidor. O alcance do Messenger continua limitado até o público migrar ou a página crescer.
- Antes de criar uma terceira presença, checar o que é a outra página TutiBom (ícone "T" verde-água) — se for da loja, reaproveitar em vez de criar outra.

## Referências

- ESTADO.md (seção "Zernio — LIGADO e PROVADO + renomeação da página + Ana 24/7 + v10"); roadmap §10 (ordem).
