# Integração ana-listener — Protocolo Escopado Multi-Inbox (v0.7.0)

Este diretório versiona o código e o patch do `ana-listener` com suporte ao **protocolo escopado por inbox**, necessário para operação simultânea de múltiplos canais (WhatsApp inbox 1 + Messenger inbox 2) sob o mesmo host MCP Ops.

> **IMPORTANTE — AMBIENTE DE DESENVOLVIMENTO:**
> A fonte viva do listener no host é **estritamente somente leitura**.
> Este pacote é apenas versionamento no repositório; **não** ativa serviços em produção, **não** altera o serviço em execução e **não** envia mensagens reais. A implantação no serviço real depende de janela autorizada de rollout.

---

## 1. Origem e Checksums

| Arquivo | Versão | Origem | SHA-256 Checksum |
|---|---|---|---|
| `listener.py` (live) | 0.6.1 | `ana-listener/listener.py` (host) | `2a226826a94075cf04a8a537de595987e6199061228b6e4b44857a6a1c0d9084` |
| `listener.py` (versionado) | 0.7.0 | `integracoes/ana_listener/listener.py` | `71668a370461360fa3e2b9bcfa2b4d20e47596d8647408cdf829276681351c4e` |
| `patch-scoped-protocol.patch` | - | `diff -u` entre live e versionado | `5b022a377d24a1e6ceb0296a0461cc39f858e5fdfc905c030761dcbab8b70c85` |

---

## 2. Contrato do Protocolo Escopado

### 2.1. `GET /pending` (Consulta com Paginação Keyset)

- **Requisição escopada:**
  ```http
  GET /pending?inbox_id=2&after_message_id=0&limit=50 HTTP/1.1
  ```
  - `inbox_id` (obrigatório para modo escopado): ID numérico da caixa de entrada.
  - `after_message_id` (opcional, padrão 0): ID numérico do cursor. O filtro SQL aplica `WHERE estado='pendente' AND inbox_id=? AND message_id > ? ORDER BY message_id ASC LIMIT ?`.
  - `limit` (opcional, padrão 50, clamp 1..200): Limite de itens por página.
  - **Filtro ANTES do LIMIT:** Garante que canais com grande volume (ex.: >20 mensagens no WhatsApp) não ocultem mensagens do Messenger.

- **Resposta esperada:**
  ```json
  {
    "ok": true,
    "scoped": true,
    "inbox_id": 2,
    "after_message_id": 0,
    "limit": 50,
    "count": 1,
    "pending": [
      {
        "message_id": 105,
        "conversation_id": 42,
        "inbox_id": 2,
        "contato_ref": "ref-opaca",
        "handoff": null,
        "recebido_em": "2026-11-24T10:00:00+00:00",
        "cumprimento": null
      }
    ]
  }
  ```

- **Compatibilidade legada:**
  - Requisição sem query param `inbox_id` continua respondendo com `{"pending": [...]}` (sem a chave `"scoped": true`), preservando compatibilidade com clientes legados v0.6.x.
  - Clientes configurados com `protocolo_escopado=True` recusam respostas sem `"scoped": true` com o código `listener_legado_incompativel` (falha fechada).

---

### 2.2. `POST /ack` (Confirmação Granular por Inbox)

- **Requisição escopada:**
  ```http
  POST /ack HTTP/1.1
  Content-Type: application/json

  {
    "inbox_id": 2,
    "message_ids": [105, 106]
  }
  ```

- **Resposta esperada:**
  ```json
  {
    "ok": true,
    "scoped": true,
    "inbox_id": 2,
    "marcados": 1,
    "accepted": [105],
    "rejected": [106]
  }
  ```
  - `accepted`: IDs que pertencem a `inbox_id` e estão pendentes ou já entregues. Um ACK repetido após resposta perdida é idempotente: o ID já entregue volta em `accepted` sem incrementar `marcados`. Apenas os aceites são removidos da fila local `acks_listener_pendentes_v1`.
  - `marcados`: quantidade de novas transições de `pendente` para `entregue`; não conta repetições idempotentes.
  - `rejected`: IDs inexistentes ou pertencentes a outro inbox. Permanecem na fila local para reattempt.

- **Compatibilidade legada:**
  - Requisições sem `inbox_id` respondem com `{"ok": true, "marcados": n}` (sem `"scoped": true`). O ACK só pode alterar um `message_id` que exista em exatamente uma linha. Se o mesmo ID existir em dois inboxes, a operação falha fechada com `marcados: 0` e não altera nenhuma das linhas; o cliente deve usar o ACK escopado.

### 2.3. Migração Transacional do Banco

Na primeira abertura de uma base anterior, o listener executa a migração em uma única transação `BEGIN IMMEDIATE`:

- `events` passa a impor unicidade por `(inbox_id, message_id)`, preservando todos os eventos e seus estados;
- `cumprimentos` recebe `inbox_id` e unicidade composta, preservando IDs, textos fixos, variantes e timestamps;
- o inbox de cada cumprimento antigo é derivado somente quando existe exatamente um evento correspondente;
- cumprimento órfão, evento sem inbox ou atribuição ambígua aborta a migração com `cumprimento_inbox_indeterminado`. O rollback preserva integralmente o esquema e os registros originais; nenhum inbox é presumido.

O backup anterior ao rollout continua obrigatório. Uma migração que falha fecha a inicialização para correção manual da base, sem apagar nem reescrever os registros originais.

---

## 3. Guia de Implantação em Rollout Autorizado

Quando houver janela formal de manutenção autorizada pelo operador:

1. **Backup prévio:**
   ```bash
   cp <DIR_SERVICO_ANA_LISTENER>/listener.py <DIR_SERVICO_ANA_LISTENER>/listener.py.bak.$(date +%Y%m%d%H%M%S)
   cp <DIR_SERVICO_ANA_LISTENER>/listener.db <DIR_SERVICO_ANA_LISTENER>/listener.db.bak.$(date +%Y%m%d%H%M%S)
   ```

2. **Aplicação via Patch:**
   ```bash
   cd <DIR_SERVICO_ANA_LISTENER>
   patch -p1 < /CAMINHO_REPO/integracoes/ana_listener/patch-scoped-protocol.patch
   ```
   *Ou substituição direta pelo arquivo versionado validando o checksum.*

3. **Verificação de Integridade:**
   ```bash
   sha256sum <DIR_SERVICO_ANA_LISTENER>/listener.py
   # Deve bater: 71668a370461360fa3e2b9bcfa2b4d20e47596d8647408cdf829276681351c4e
   ```

4. **Reinício do Serviço:**
   Conforme procedimento operacional padrão do host.

5. **Rollback (se necessário):**
   ```bash
   cp <DIR_SERVICO_ANA_LISTENER>/listener.py.bak.* <DIR_SERVICO_ANA_LISTENER>/listener.py
   ```

---

## 4. Dependências Locais e Supressão de Cumprimento

### 4.1. Módulos Auxiliares Locais
O `listener.py` opera no host importando módulos auxiliares locais localizados no mesmo diretório de execução:
- `chatwoot_client.py`: Comunicação com a API do Chatwoot (envio de mensagens de cumprimento e inspeção de conversas).
- `handoff.py`: Detecção e aplicação de regras de transição para atendimento humano.
- `ignorados.py`: Regras e listas de contatos/empresas ignoradas (descarte antes da fila).

### 4.2. Trava de Supressão de Cumprimentos no Rollout Multi-Inbox
O listener possui rotina de cumprimento automático ("Olá! Sou a Ana..."), controlada via `MODO_OPERACAO_FILE` (padrão `modo_operacao.json`):
- A supressão existente configurada apenas para o inbox 1 (`"inboxes_sem_cumprimento": ["1"]`) **NÃO** é suficiente para o suporte ao inbox 2 (Messenger).
- Para evitar disparos paralelos de saudações pelo timer do listener enquanto o MCP Ops atende a fila, o arquivo `modo_operacao.json` DEVE ser atualizado antes da transição do escritor:
  ```json
  {
    "cumprimento_automatico": false,
    "inboxes_sem_cumprimento": ["1", "2"]
  }
  ```
- **Atenção:** A supressão deve estar comprovada em ambos os inboxes antes de liberar o escritor de atendimento no novo host.

---

## 5. Regras de Segurança e Privacidade

- **Sem Segredos:** Nenhuma chave de API, PAT ou token embutido no código.
- **Sem PII:** O listener e o banco `listener.db` registram apenas referências opacas (`contato_ref`), IDs numéricos e tamanhos de payload. Nenhum número de telefone, texto ou identificador sensível é exposto em logs ou retornos HTTP.
- **Serviço Live Intocado:** A fonte em `/home/pc/chatwoot/ana-listener/listener.py` é estritamente somente leitura neste laboratório. Não iniciar, reiniciar nem editar o serviço live em produção.
