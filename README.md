# tuttibom-ops

Operação modular, agent-first, de uma loja no Cariri (Juazeiro do Norte /
Crato / Barbalha) — impressão 3D e fitas de cetim personalizadas, marca
TuttiBom — reaproveitável em várias redes, contas e nichos.

Nome decidido pelo usuário em 2026-10-31. Nome anterior, específico demais
para o novo escopo: `facebook-s10-adb`. Este repositório é o projeto. O
repositório de acesso ao aparelho (`acesso-dispositivo-smartphon`) é outro
projeto, separado, e continua separado.

## Princípios (não negociáveis sem discussão)

- Agent first, humano no checkpoint: nada publica, responde com preço,
  reserva, encontro ou pagamento, edita ou apaga conteúdo publicado, paga
  ou impulsiona sem aprovação do texto e da mídia exatos.
- Rascunho antes de publicar. Uma tarefa por sessão, ritmo humanizado,
  sem rajada e sem retry apressado.
- Parar é um resultado: login, verificação, tela irreconhecível,
  screenshot vazio, ADB fora ou prompt de rede sem resposta param o fluxo
  e viram registro, não tentativa repetida.
- Sem engajamento artificial e sem evasão de detecção. Naturalidade de
  texto é qualidade editorial para pessoas, não truque para enganar
  detector de plataforma. Não se esconde uso de IA, nem se escancara:
  o esforço real (processo, foto, revisão, aprovação) é o que sustenta
  o conteúdo.
- Sem segredos no repositório: nada de senha, cookie, token, sessão,
  endpoint vivo ou dado pessoal de comprador.
- Painel só leitura para o usuário; só o Muse edita e atualiza o painel,
  após discussão e avaliação técnica, com versão registrada.
- Railway NÃO entra nesta aplicação (correção do usuário, 2026-10-31:
  a conta mencionada era Railway, não Runway, e está fora do escopo).

## Estrutura

- `core/` (a criar na migração) — guardrails, contratos de skills,
  esquema do banco, painel, observabilidade. Agnóstico de rede e conta.
- `contas/<marca>/<rede>/` (a criar na migração) — só configuração por
  conta e rede. Nada de segredo aqui.
- `catalogo/` — um arquivo por produto, sem preço inventado.
- `templates/` — anúncio, resposta, roteiro de vídeo, post.
- `ops/` — fila de publicação, triagem, saúde da conta, monitoramento,
  reação da plataforma.
- `experimentos/` — um arquivo por teste, com hipótese e resultado.
- `docs/` — decisões, roadmap, arquitetura, painel, rotinas, práticas.
- `painel-v1/` — esboço HTML só leitura da primeira versão do painel.
- `db/` — esquema Supabase Postgres (rascunho, sem credencial).

## Skills — genérico na estrutura, específico na instância

Modelo completo em [`docs/skills-modulares.md`](docs/skills-modulares.md)
e contrato em `skills/_contrato/SKILL.md`. Nome obrigatório:
`<marca>-<rede>-<funcao>`.

Instâncias atuais (focadas no produto e na conta de hoje):

- `skills/tuttibom-facebook-marketplace/` — anúncio, triagem,
  encaminhamento; problemas específicos do Facebook no S10.
- `skills/tuttibom-facebook-conteudo/` — post, vídeo, fila, reação.
- `skills/tuttibom-notebooklm/` — canônico + efêmeros, roteiro e texto.
- `skills/tuttibom-observabilidade/` — painel, falhas, tokens, saúde.

Legado, a migrar para o modelo acima quando tocado:

- `skills/guardrails/` — vale para toda a operação, acima das demais.
- `skills/s10-navegacao/` — loop ADB, vigília da tela, verificação, parada.
- `skills/facebook-vendas/` e `skills/facebook-conteudo/` — base das
  instâncias tuttibom correspondentes.
- `skills/monitoramento/`, `skills/pesquisa-comunidade/`,
  `skills/crm-interessados/`, `skills/persona-interacao/`.

## Documentos de referência

- [`docs/roadmap.md`](docs/roadmap.md) — roadmap v2, por fases, com
  critérios de saída, riscos e o que NÃO fazer.
- [`docs/arquitetura.md`](docs/arquitetura.md) — arquitetura modular v2.
- [`docs/painel-v1.md`](docs/painel-v1.md) — esboço da primeira versão
  do painel, abas, métricas, contadores de falhas e contrato de dados.
- [`docs/arquitetura-discussao-2026-10-30.md`](docs/arquitetura-discussao-2026-10-30.md)
  — notas históricas da discussão de 2026-10-30. Não é o documento
  final: onde divergir, valem `roadmap.md` e `arquitetura.md` v2, e as
  correções de 2026-10-31 (nome tuttibom-ops; Railway fora do escopo).

## Começo rápido

1. Ler `docs/roadmap.md` e `docs/arquitetura.md` antes de rodar teste.
2. Teste só leitura no S10, seguindo `skills/s10-navegacao/SKILL.md`.
3. Registrar o teste em `experimentos/` e resumir em `RELATORIO.md`.

## Estado

- 2026-10-31: repositório renomeado localmente para tuttibom-ops;
  roadmap v2, arquitetura v2 e esboço do painel v1 criados. Publicação
  no GitHub continua pendente (bloqueio na instalação do app do Muse
  no GitHub, a resolver pelo usuário quando decidir publicar).
- Execução da conta pessoal da loja no Facebook: só via ADB no S10,
  por enquanto. Conector nativo do Muse não está ligado a conta nenhuma
  neste ambiente (checagem 2026-10-30); no futuro, só como auxiliar de
  Página, se a conta ligada for administradora dela.
