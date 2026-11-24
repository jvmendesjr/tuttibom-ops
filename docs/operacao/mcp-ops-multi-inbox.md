# MCP Ops: WhatsApp e Messenger no mesmo host

Implementação permanente no repositório, sem ativação automática de canais.
O merge não instala o listener nem transfere a Ana. O rollout exige uma
janela autorizada, backup e exclusão do escritor anterior.

## Composição e contrato

Um `ServidorOps` mantém a exclusividade de escrita da área de atendimento
para todos os inboxes. Cada inbox tem fila, backend Chatwoot, cache de
mídia, adaptador de atendimento e diário de entregas próprios. Os IDs de
mensagem e as chaves de idempotência podem coincidir entre canais sem
compartilhar reservas ou ACKs.

Em configuração multi-inbox, informar `inbox_id` nas chamadas
`ops_atendimento_ler_conversa` e `ops_atendimento_preparar_resposta`.
A listagem agrega os canais e identifica o inbox de cada pendência;
aceita filtro `inbox_id`. O rascunho mantém seu inbox original, inclusive
durante inspeção, aprovação, envio e reconciliação.

A aprovação administrativa deve incluir o `inbox_id`, a `conversa_ref`,
o `rascunho_ref` e o texto/imagem exatos. Aprovação de outro canal não
autoriza envio. Ler e preparar não confirmam mensagens. O ACK só ocorre
na fila do canal cujo destino aceitou a entrega. Entregas incertas não
são reenviadas automaticamente.

A configuração legada de um inbox continua válida. Não reutilizar os
arquivos SQLite legados para outro inbox nem copiar um diário entre canais.

## Configuração privada

O mesmo `--config-canal` aceita a configuração single-inbox anterior ou:

```json
{
  "canais": [
    {
      "conta_id": "2",
      "inbox_id": "1",
      "pat_arquivo": "/CAMINHO/PRIVADO/pat",
      "chatwoot_porta": 3001,
      "listener_porta": 3021,
      "conversas_ignoradas": ["8"]
    },
    {
      "conta_id": "2",
      "inbox_id": "2",
      "pat_arquivo": "/CAMINHO/PRIVADO/pat",
      "chatwoot_porta": 3001,
      "listener_porta": 3021,
      "conversas_ignoradas": ["8"]
    }
  ]
}
```

Os caminhos são exemplos, não credenciais reais. Não guardar a
configuração preenchida no Git. Arquivos privados pertencem ao operador,
com modo `0600`; diretórios, `0700`. As pilhas ficam em
`ESTADO/inbox-1/` e `ESTADO/inbox-2/`. O lock do host continua em
`ESTADO/host.lock`. Só uma conta pode ser configurada no mesmo host,
pois a chave pública de roteamento é o inbox.

O modo multi-inbox exige o protocolo escopado do listener versionado em
`integracoes/ana_listener/`. A consulta deve filtrar inbox antes do limite,
paginar por ID e anunciar suporte ao protocolo. O ACK precisa informar
inbox e confirmar IDs individualmente. Um listener antigo não constitui
fallback seguro nesse modo.

Contrato escopado:

- `GET /pending?inbox_id=2&after_message_id=0&limit=100`, com resposta
  `{"scoped": true, "pending": [...]}`. O cursor avança pelo ID da última
  mensagem recebida, inclusive quando a fila local recusa esse item.
- `POST /ack`, com `{"inbox_id": 2, "message_ids": [123]}`. A resposta
  contém `ok`, `scoped`, `inbox_id`, `accepted` e `rejected`.
  Só os IDs aceitos saem da fila local de ACKs.
- Sem confirmação escopada válida, o cliente não usa ACK global como
  fallback nem considera o lote confirmado.

No modo multi-inbox, a ação administrativa `reconciliar-acks` exige
`--inbox-id 1` ou `--inbox-id 2`. Ela atua somente na pilha selecionada.

## Pré-checagem, não executada nesta promoção

`scripts/preflight-multi-inbox` é só leitura. Nenhum comando abaixo é
executado contra o host nesta fase. Os caminhos são placeholders.

```sh
scripts/preflight-multi-inbox \
  --listener-live /CAMINHO/PRIVADO/listener.py \
  --modo-operacao /CAMINHO/PRIVADO/modo_operacao.json \
  --listener-db /CAMINHO/PRIVADO/listener.db \
  --estado-host /CAMINHO/PRIVADO/estado \
  --backup-dir /CAMINHO/PRIVADO/backups
```

Obrigatórios: `--listener-live`, `--modo-operacao`, `--listener-db`,
`--estado-host` e `--backup-dir` (este pode repetir). Opcional:
`--listener-repo`, com default em `integracoes/ana_listener/listener.py`.
Opcional: `--json`, que troca o texto por JSON e mantém o mesmo critério
de saída.

A saída é `0` somente quando todas as checagens estão OK. Qualquer item
PENDENTE termina com `1`. Banco com cabeçalho WAL, ou com arquivo `-wal`
ao lado, fica PENDENTE e não é aberto: a consulta não cria nem altera
sidecar. Backup detectado conta arquivo não vazio de extensão reconhecida;
não prova integridade nem atualidade.

A migração do listener versionado corre numa transação. Se um cumprimento
antigo não puder ser atribuído a um único inbox, a migração aborta com
rollback e os registros anteriores permanecem.

## Rollout posterior, não executado pela implementação

1. Revisar os testes e a origem da fonte versionada do listener.
2. Fazer backup dos bancos e da configuração do listener e do host.
3. Autorizar a janela de implantação. Não alterar Deskcomm production,
   `cloudflared-ponte`, S10/ADB ou PQBR2.
4. Implantar o protocolo do listener e comprovar a supressão do
   cumprimento automático em **ambos** os inboxes antes de transferir o
   escritor. A configuração MCP não desliga outros escritores.
5. Parar o escritor anterior antes de iniciar o novo host com o mesmo
   diretório de estado protegido por lock. Não executar dois hosts sobre
   estados distintos para contornar exclusividade. Antes de parar o host
   single-inbox, rodar `reconciliar-acks` e confirmar zero entregas
   pendentes ou incertas. Depois, mover `fila.sqlite` e `entregas.sqlite`
   (com os arquivos `-wal`/`-shm`) da raiz do estado para `inbox-1/`.
   Sem essa mudança, o host novo começa o inbox 1 com diário vazio e
   perde a proteção contra reenvio de entregas já aceitas.
6. Validar leitura por canal. Qualquer envio real exige nova aprovação do
   destino e do texto/imagem exatos. Conversa `"8"` e grupos permanecem
   bloqueados. Nenhuma mensagem real faz parte dos testes deste patch.
7. Para rollback, parar o novo host, restaurar o listener/configuração
   anterior sob a janela autorizada e reconciliar entregas antes de
   liberar o escritor anterior. Não apagar os novos diários e não repetir
   envios de estado incerto.

## Verificação local

```sh
make check
git diff --check
```

Os testes usam filas fictícias e servidores loopback sintéticos. Aprovar
esses testes não comprova entrega Messenger real nem autoriza rollout.
