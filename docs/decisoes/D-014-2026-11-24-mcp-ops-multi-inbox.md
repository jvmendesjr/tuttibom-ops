# D-014: MCP Ops por inbox, implementação separada do rollout

Data: 2026-11-24. Escopo autorizado pelo usuário: implementar Messenger
permanentemente no worktree, testar e deixar para revisão/merge posterior.
O usuário pediu delegação aos agentes conectados.

## Decisão técnica

Compor pilhas isoladas por inbox sob um único `ServidorOps`, em vez de
relaxar a validação single-inbox do backend Chatwoot ou compartilhar o
diário de entregas. WhatsApp e Messenger atendem no canal de origem.

O roteamento usa inbox configurado pelo operador. Leituras e rascunhos
são vinculados ao canal. IDs e chaves de idempotência não atravessam
pilhas. A aprovação exata de texto/imagem, a exclusividade de escrita,
o bloqueio de replay incerto e o ACK após aceitação continuam obrigatórios.

O listener precisa de pending filtrado antes do limite, paginação e ACK
escopado com confirmação granular. Sua alteração fica versionada no
repositório, não aplicada apenas ao arquivo em serviço.

## Limite da autorização inicial

Escopo histórico da implementação, antes da ordem posterior desta data.
Não fazer commit, merge, rollout ou envio real nesta implementação.
Não alterar Deskcomm production, túnel, S10/ADB ou PQBR2. Não reativar
cumprimento automático concorrente. A conversa `"8"` permanece bloqueada.
As restrições de laboratório não limitam o desenho do código permanente,
mas os testes continuam exclusivamente sintéticos.

## Emenda 2026-11-24 — snapshot saneado

A ordem posterior do usuário, nesta mesma data, autoriza publicar na
`main` um commit novo com o snapshot saneado. O único pai desse commit
é a `main` anterior. Os 44 commits entre essa base e
`exp/mcp-ops-nucleo` não entram como ancestrais. O push, se houver, é
somente da `main` e somente pela Factory.

A emenda não autoriza apagar nem reescrever refs já publicadas. Não
autoriza rollout, mensagem real nem ACK real. Deskcomm, túnel, S10/ADB,
PQBR2 e a conversa `"8"` continuam fora desta janela. O listener novo
permanece versionado no repositório; o serviço em execução não é
substituído por esta promoção.

Contrato e janela futura: [guia multi-inbox](../operacao/mcp-ops-multi-inbox.md).
O estado de validação fica em `docs/ESTADO.md`, sem transformar testes
locais em evidência de entrega real no Messenger.
