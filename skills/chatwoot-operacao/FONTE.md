# FONTE — skill chatwoot-operacao

Skill própria do TuttiBom Ops (não é cópia de upstream).

- **Base:** Chatwoot v4.20.1-ce, instalado no PC em 2026-11-21
  (`/home/pc/chatwoot/`, conta "TuttiBom" id 2).
- **Referência da API:** https://developers.chatwoot.com/api-reference
  (endpoints de conversas, mensagens, contatos e inboxes; canal API).
- **Referência do app WAHA → Chatwoot:**
  https://waha.devlike.pro/docs/apps/chatwoot/
- **Referência dos webhooks do Zernio:** https://docs.zernio.com/webhooks
  (assinatura HMAC-SHA256, dedupe por id, até 50 endpoints).
- **Detalhe da implementação:** ponte `zernio-bridge` em
  `/home/pc/chatwoot/zernio-bridge/` (fora do repo); log da fase 2 em
  `/home/pc/chatwoot/BUILD_LOG.md`.

Atualizar quando a URL pública da ponte existir, quando a volta
(Chatwoot → Zernio) for ativada com a chave da API, ou quando a
versão do Chatwoot mudar.
