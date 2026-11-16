# config/ — configs versionadas (sem segredos)

- `modelos_9router.json`: combos de modelos por agente, no 9Router
  original do pc (`http://127.0.0.1:20128/v1`). O PQBR2 usa o `:20130`,
  separado; não trocar.
- A chave do 9Router é segredo de empresa no Paperclip, referenciada
  por nome nos agentes — nunca em texto aqui, nunca no git.
