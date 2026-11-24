# Dois MCPs, dois papéis

**Worktree de integração:** `tuttibom-ops-mcp-nucleo`, branch `exp/mcp-ops-nucleo`.

| Servidor | Pode | Não pode |
|---|---|---|
| `tuttibom-core-mcp` | Consultar as 12 ferramentas de manutenção por stdio | Atender, publicar, conceder atribuições ou alterar dados |
| `tuttibom-ops-mcp` | Operar só o que consta no manifesto do cliente | Acessar ferramentas do Core, administrar atribuições, executar shell ou ler arquivos à escolha do agente |

`scripts/tuttibom-mcp` continua funcionando como caminho legado do Core.
`scripts/tuttibom-ops-admin` é a interface do operador, não uma ferramenta MCP.

## Rodar o laboratório

Na raiz da worktree, com as dependências de `requirements.txt` disponíveis
no Python usado pelos scripts (`. .venv/bin/activate` se instaladas na venv):

```sh
./scripts/tuttibom-ops-admin --laboratorio /tmp/tuttibom-ops-lab servir
```

Use um diretório absoluto ainda inexistente. O host usa sockets Unix
privados e estado em memória, incluindo sessão, fila e simulador. Não abre
porta TCP, não usa credenciais reais e não carrega dados de produção.
Ao parar o host, o estado sintético é perdido. O operador controla a conta
do sistema que executa o host; os perfis `ana-01` e `ana-02` simulam
identidades distintas. Os sockets **não** isolam processos do mesmo usuário
do sistema entre si. Não entregue acesso ao socket administrativo nem
trate a configuração como autenticação de produção.

Para testar sobrevivência ao reinício, acrescente ao comando `servir`
`--estado-lab <diretório-absoluto-privado>`, separado dos sockets. O modo
durável preserva a fila e o diário de entregas SQLite; não preserva
autorizações, sessões, rascunhos nem o histórico simulado. O diretório é
de uso exclusivo de uma instância por vez.

Para cadastrar outros clientes de laboratório, passe, por exemplo,
`servir --cliente-lab agente-teste --cliente-lab agente-reserva`.
O procedimento não exige um provedor ou nome específico.

Em outro terminal, o operador escolhe os IDs:

```sh
./scripts/tuttibom-ops-admin --laboratorio /tmp/tuttibom-ops-lab listar-atribuicoes
./scripts/tuttibom-ops-admin --laboratorio /tmp/tuttibom-ops-lab autorizar --agente ana-01 --funcoes 01.01,01.02
```

O catálogo tem 18 IDs estáveis. O lab executa `01.01` (fila e leitura),
`01.02` (rascunho e resposta simulada) e `03.01` (preço versionado, sem
estoque verificado). As demais funções aparecem como indisponíveis e não
podem ser concedidas pelo CLI. A resposta requer que a leitura também tenha
sido selecionada; o servidor não acrescenta atribuições sozinho.

Configure no cliente MCP o comando `scripts/tuttibom-ops-mcp` pelo
caminho absoluto desta worktree, com argumentos
`["--laboratorio", "/tmp/tuttibom-ops-lab", "--cliente", "ana-01"]`.
O Core usa `scripts/tuttibom-core-mcp`, sem argumentos e sem conexão com
o host do Ops.

## Operador autenticado no laboratório

Por padrão o socket administrativo aceita qualquer processo do mesmo
usuário do sistema, como antes. Para exigir credencial do operador,
suba o host com `--digests-operador-lab <arquivo-0600>` apontando para
um JSON `{"operador-lab": "<sha256 do segredo>"}` e passe a cada comando
administrativo `--credencial-operador <arquivo-0600>` com o segredo de
32 bytes em hexadecimal. Sem credencial, com credencial errada ou com
tipo inválido, a resposta é sempre `operador_nao_autenticado`, antes do
despacho da ação; a credencial não aparece na auditoria. O digest do
operador não pode repetir nenhum digest de perfil HTTP. A credencial
continua sintética: prova posse de um arquivo local, não identidade
humana, e não isola processos do mesmo usuário entre si.

## Cliente pré-configurado por HTTP

O mesmo host sintético aceita MCP Streamable HTTP opcionalmente. Em
`servir`, configure juntos `--digests-http`, `--host-tailnet` e
`--porta-loopback`. A config é um JSON privado (`0600`) de perfil autorizado
para SHA-256 do segredo. Cada cliente recebe na configuração, não no
prompt, um segredo aleatório de 32 bytes codificado em hexadecimal e
`Authorization: Bearer <segredo>`. Não coloque segredo na URL nem reutilize
o segredo entre perfis. `autorizar --agente <perfil> --funcoes <IDs>`
ativa a seleção no host para os perfis do JSON. Eles não recebem
socket stdio nem ferramentas de ativação. Antes dessa vinculação a
credencial não abre uma sessão; depois, o manifesto já está disponível
no primeiro contato, inclusive em novas conexões. O stdio local de
desenvolvimento mantém `ops_ativar` e `ops_reconectar`.

O servidor só escuta no loopback. Para acesso remoto, publique exclusivamente a rota
`/tuttibom-ops-lab/mcp` via Tailscale Serve HTTPS em uma porta dedicada,
sem Funnel, sem sobrescrever rotas existentes e sem repassar o socket
administrativo. O cliente usa Streamable HTTP, não precisa de SSH, shell
ou acesso à instalação. Confirme recusa sem credencial e que as
atribuições disponíveis correspondem à seleção do operador. Não use esse host para credenciais
ou canais de produção.

Para encerrar a prova, revogue a atribuição, remova só a rota dedicada
e pare o host. A revogação invalida funções e bloqueia a credencial HTTP
nesse host. Para nova concessão, use outro perfil e outra credencial;
ao recriar o host, não recarregue segredos revogados. Os vínculos do
laboratório não são persistidos.

## Turno e troca de agente

O operador entrega apenas o [diretório de entrada](../../agent-entry/tuttibom-ops/)
e a sessão com o MCP configurado. Não compartilhe a raiz do projeto, o
socket administrativo ou os arquivos de configuração do host. O `AGENTS.md`
orienta a primeira chamada; não instala um cliente nem concede acesso só por
ser lido. Qualquer cliente MCP com Streamable HTTP, cabeçalho Bearer e
alcance ao endpoint privado pode usar o mesmo fluxo.

Use os modelos de [entrada](../prompt-entrada-agente-ops.md) e
[desvinculação](../prompt-desvinculacao-agente-ops.md). O modelo de saída
não substitui a revogação nem autoriza apagar ou confirmar pendências.
O [índice de skills](skills-por-area.md) indica exatamente qual material
acompanha cada função.

1. Entregue o cliente HTTP configurado. Na conexão já vinculada o
   agente chama `ops_minhas_atribuicoes`. Se estiver testando pelo
   stdio legado, o cliente de teste chama `ops_ativar` com a
   `referencia` e as `funcoes` do CLI. O token interno não aparece em
   respostas.
2. O agente confere seu escopo no manifesto, lê as skills anunciadas
   pelo ID em `ops_ler_skill` e chama
   `ops_confirmar_atribuicoes` com o hash e um resumo. A confirmação
   adquire a escrita exclusiva; outro agente autorizado pode ler, mas
   não pode escrever enquanto a área estiver ocupada. Ao reabrir a
   conexão, releia e confirme o manifesto (no stdio legado, chame
   `ops_reconectar` primeiro).
   O manifesto inclui o SHA-256 do `SKILL.md` entregue ao cliente.
   O MCP exige a leitura de todas as skills do manifesto na sessão, mas
   não pode provar que o agente entendeu o procedimento. Não permite
   leitura de caminhos do repositório. No HTTP pré-configurado, a
   confirmação é exigida inclusive antes de operar em modo leitura.
3. Liste pendências e leia a conversa. A imagem vem em um bloco MCP
   `image` e o áudio vem com a saída do transcritor sintético. A
   preparação exige os hashes das imagens recebidas e os IDs da fila a
   responder. O hash verifica qual imagem foi entregue pelo MCP, não
   comprova que um modelo realmente a interpretou.
4. O operador aprova por `tuttibom-ops-admin --laboratorio <diretório>
   aprovar-resposta`, passando JSON via stdin, com `rascunho_ref`,
   `conversa_ref`, `texto` exato e, quando houver imagem de saída,
   `imagem_base64` com os bytes exatos. Entregue a `aprovacao_ref`
   resultante ao agente. O envio fica vinculado ao rascunho e à sessão.
5. O agente chama `ops_atendimento_responder` com a referência do
   rascunho e a da aprovação. A fila só recebe ACK (confirmação de
   processamento) após o destino simulado aceitar. Se o destino aceitou
   mas o ACK falhou, no modo durável o operador pode usar
   `reconciliar-acks` para confirmar a fila sem novo envio. Uma nova chave
   não libera outro envio para o item. Resultado incerto é bloqueado
   para investigação, não repetido automaticamente.
6. Para simular sucessão, revogue `ana-01` pelo CLI (`revogar --agente
   ana-01`), autorize `ana-02` e confirme o manifesto do novo agente.
   A fila e o histórico já processado permanecem no mesmo host. Rascunhos
   e aprovações do antigo titular não são transferidos.

Verificação: `make check` executa os testes dos componentes e
`tests/test_mcp_ops_stdio.py` verifica os dois MCPs com um cliente MCP
real e os comandos administrativos. A [matriz QA](../teste-lab-mcp-ops.md)
é material de referência, não a especificação da CLI.

## Prova ponta a ponta com Chatwoot isolado

Com o projeto `tuttibom-chatwoot-lab` isolado em execução, os testes
opt-in criam conversas **fictícias**. O teste ponta a ponta importa
os IDs das entradas da conversa de teste, sobe o host Ops com fila e
diário SQLite e usa o cliente MCP stdio real para verificar manifesto,
PNG sem legenda, aprovação exata de texto e imagem, entrega e ACK.
Reinicia o host, ativa a sucessora e confirma no histórico do Chatwoot
que a tentativa com outra chave não gerou segundo envio.

```sh
TUTTIBOM_TEST_CHATWOOT_LAB=1 PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_mcp_ops_chatwoot_isolado.py tests/test_mcp_ops_chatwoot_e2e.py
```

O transporte de teste executa no contêiner, sem publicar porta. Só o
processo de prova tem acesso ao Docker; o cliente MCP não o recebe.
O `servir` padrão continua sintético. A importação é explícita e se
limita a uma conversa fictícia; não é ingestão contínua. Sem a variável
opt-in, os testes que usam o contêiner não rodam em `make check`.

A prova integrada `tests/test_mcp_ops_integrado_lab.py` combina, sobre o
mesmo Chatwoot isolado, a cerca de conversa única do piloto
(`piloto_conversa.py`): só entram eventos incoming públicos da tupla
exata conta+inbox+conversa; leitura, mídia e envio fora do escopo são
recusados; desativar o escopo esvazia a fila e bloqueia até um envio já
aprovado (`conversa_fora_do_piloto`), que só sai após a reativação.
`permite_envio_legado` é a verificação final que um escritor legado
deve chamar imediatamente antes de enviar; ainda não foi ligada a
nenhum escritor. Na mesma prova, autorizar, aprovar e revogar exigem a
credencial do operador. Um segundo teste opt-in passa áudio real
(sintetizado localmente com espeak-ng) pelo pipeline de leitura com o
`TranscritorOffline` (`transcricao_offline.py`, faster-whisper local,
sem rede), e a transcrição aparece na leitura da conversa:

```sh
TUTTIBOM_TEST_CHATWOOT_LAB=1 PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_mcp_ops_integrado_lab.py::test_piloto_chatwoot_com_operador_autenticado
TUTTIBOM_TEST_WHISPER=1 PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_mcp_ops_integrado_lab.py::test_audio_offline_real_no_pipeline
```

## Antes da transferência real

O lab já prova aprovação exata com operador autenticado por credencial
local, cerca de conversa única com recusa de leitura e envio fora do
escopo e transcrição offline de voz sintética (modelo `small`; `tiny`
não é suficiente). Ainda faltam: identidade autenticada fora do
laboratório, ingestão contínua, ligar a cerca do piloto a todos os
escritores reais (inclusive agendados) antes de qualquer virada, áudio
real vindo do canal (não sintetizado) e a verificação, só com metadados,
do destino controlado. O transporte remoto, quando validado, fica
restrito à tailnet. Depois: transferência explícita para um único
titular e prova controlada com o novo agente, sem eventos falsos nem
mensagens de teste a clientes reais.
