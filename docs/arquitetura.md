# Arquitetura v2 — tuttibom-ops

> Versão 2, 2026-10-31. Onde divergir das notas de 2026-10-30, vale esta
> versão, com as correções de 2026-10-31: nome tuttibom-ops; Railway
> fora do escopo; avaliação de "80–90%" retirada pelo usuário.

## Princípio de desenho

Separar o que é preparação (funciona sem o telefone) do que é execução
(só existe numa janela viva de ADB), e separar o que é agnóstico
(core) do que é configuração por conta/rede. Nada no painel executa;
nada na VM publica pela conta pessoal da loja; nada no repo guarda
segredo ou dado de comprador.

## Camadas, de cima para baixo

1. **Humano no checkpoint (usuário).** Aprova texto e mídia exatos,
   decide preço, identidade e exceções. Não há "aprovar tudo".
2. **Orquestração (Muse na VM).** Skills como contratos, fila,
   templates, catálogo, memória do projeto, painel (só leitura para o
   usuário, escrita só pelo Muse).
3. **Decisão System 1 (Jev, TypeSafe).** Classificação tipada:
   Choice / Noul / Score, com probabilidade e confiança. Exemplos:
   tipo de mensagem, estágio do CRM, urgência, risco, adequação de
   formato. Abaixo do limiar → humano. Jev não gera texto, não aprova,
   não publica.
4. **Geração System 2 (Muse + NotebookLM).** NotebookLM canônico como
   norteador (conceito, persona versionada, método de pesquisa e
   modelagem) + cadernos efêmeros por criativo (exportar, depois
   deletar caderno e chat). Muse gera imagem, vídeo e edição, com
   motion graphics via Remotion / HyperFrames / FFmpeg, storyboard
   antes de renderizar, arquivo versionado no Drive.
5. **Transporte (Tailscale + SSH).** Estável até aqui: IP do Tailscale
   se manteve, SSH responde, watchdog do sshd roda. "Visível na
   tailnet" não prova nada; só SSH e ADB respondendo provam.
6. **Execução no S10 (Termux + ADB + MacroDroid).** Frágil e efêmero:
   porta muda a cada reativação; rede nova pode pedir allow de novo.
   Watchdog + mDNS descobrem a porta; MacroDroid recoloca
   `adb_wifi_enabled=1`. Gate antes de qualquer ação: rede → SSH →
   ADB → tela acordada → app em foco → screencap atual.
7. **App (Facebook / Messenger, conta da loja, já logada no S10).**
   Único executor da conta pessoal da loja, por enquanto.
8. **Arquivo e índice (Drive + Supabase).** Drive (5 TB) = arquivo dos
   criativos. Supabase Postgres = índice e observabilidade (contas,
   redes, produtos, criativos, publicações, usos, falhas, métricas,
   tarefas). Banco guarda ponteiro, ficha e histórico — nunca o arquivo
   grande, nunca segredo, e, na v1, nunca dado pessoal de comprador.
9. **Auditoria e painel.** Logs, contadores e snapshots geram o painel.
   O painel lê; não escreve na conta, não publica, não responde.

## Executor: regra de ouro

- **Conta pessoal da loja (Marketplace, Messenger, perfil): só ADB.**
  Conector com outra conta seria autor errado. Conector neste ambiente
  não está ligado a conta nenhuma (checagem 2026-10-30).
- **Página TuttiBom: conector no futuro, só se a conta ligada for
  administradora da Página.** Complemento, não substituição.
- **Leitura/pesquisa:** conector pode ser referência, nunca substitui
  a triagem da conta da loja.

## Módulos (setores = módulos, não cópias)

Cada módulo tem a mesma forma, e só a configuração muda por rede/conta:

- **Marketplace:** catálogo → template → rascunho → aprovação →
  publicação via ADB → prova por screencap → triagem → CRM.
- **Publicações:** ideia → caderno efêmero → roteiro/texto →
  storyboard → render → arquivo versionado → fila (feed + stories) →
  aprovação → publicação → reação (baseline / intervenção / janela).
- **Interações:** monitoramento só leitura → Jev classifica → triagem
  → nota privada no Drive → rascunho de resposta → aprovação do texto
  exato → envio via ADB → registro + próxima ação com data.

Máquina de estados por módulo, com fila própria. Um anúncio não vira
post; um lead não vira métrica; um criativo não é republicado sem
registro de uso.

## Contrato de skill (modelo)

Toda skill nova segue este contrato, em `SKILL.md`:

- Propósito e onde se aplica (rede, conta, nicho, setor).
- Entradas (o que precisa estar pronto e aprovado antes).
- Passos determinísticos, em ordem, com checkpoint por screencap ou
  leitura quando houver tela.
- Pontos de decisão (onde entra Jev, com limiar; onde entra humano).
- Condições de parada e rota de fuga (voltar, home, parar, registrar).
- Saídas (rascunho, log, ficha no banco, arquivo no Drive).
- Adaptação para outra rede/nicho: o que muda, o que não muda.
- O que NUNCA faz (lista explícita, herdada dos guardrails).

Modelos externos (skills, plugins, ferramentas) entram de forma
agnóstica: extrai-se o padrão, descarta-se a premissa específica da
ferramenta de origem, registra-se a fonte do padrão (sem copiar texto,
foto, logo ou cliente de terceiros), e o usuário define o setor de
aplicação — o Muse observa tecnicamente outros setores onde o padrão
também serve.

## NotebookLM — skill a criar

- **Canônico:** um caderno, versionado via documento no repo, com
  conceito, objetivo, loja, redes, método de pesquisa/concorrência/
  modelagem, persona e conectores/processos conhecidos. Atualizado só
  por aprovação.
- **Efêmero:** um caderno por criativo/publicação, com só o trecho
  relevante do canônico + fontes daquele asset. Gera roteiro, texto e
  prompts de imagem. Exporta para Drive e repo. Depois, deleta caderno
  e chat, e registra a deleção (não o conteúdo apagado).
- **Limite honesto:** sem API oficial estável; entra como fonte
  semi-manual, com exportação como contrato. Não é dependência ao vivo
  de cada post. Não aprova, não publica, não substitui guardrail.
- **Consulta:** do início à produção, inclusive em decisões de
  criativos — como conselheiro norteador, não como decisor final.

## Dados: o que vai onde

| Dado | Onde fica | O que NÃO fica |
|---|---|---|
| Regras, templates, padrões, experimentos | Repo tuttibom-ops | Segredo, endpoint vivo, dado de comprador |
| Criativos (arquivo) | Drive, pastas 00–03 | — |
| Ficha, contagem e histórico de uso | Supabase (futuro) / ops/ (hoje) | Conteúdo de conversa, telefone, email |
| Notas por lead | Drive privado (CRM TuttiBom) | Repo, painel |
| Status vivo do telefone | Arquivos no Termux (`adb-endpoint.txt`, logs) | Repo |
| Decisões e o que foi verificado | Memória do Muse + RELATORIO.md | Senha, token, código |

## Falhas e observabilidade (contrato)

Toda falha vira registro: tipo, severidade, módulo, conta/rede,
horário, causa conhecida ou desconhecida, impacto (interrompe ou não),
próxima ação, e contador por dia/semana/mês.

- **Crítica, interrompe:** ADB fora, prompt de rede sem resposta,
  verificação do Facebook, sessão expirada, publicação sem prova.
- **Não crítica, não interrompe:** métrica atrasada, Jev abaixo do
  limiar (vai para humano), render que falhou e pode ser refeito,
  falha de leitura que se resolve no próximo ciclo.

Observabilidade constante: tokens por provedor/tarefa, disponibilidade
com último check (Muse, SSH, ADB, Facebook, NotebookLM, Jev, Supabase,
Drive), saúde do S10 (bateria, disco, memória, uptime, reinícios),
fila (rascunho, aprovado, publicado, atrasado). Se custo subir ou
confiança do Jev cair, degrada para revisão humana — nunca acelera
publicação para compensar.

## Provedores — papéis e limites

- **Muse:** orquestração, geração, edição, painel. Custo por tarefa,
  a acompanhar no painel.
- **Jev (TypeSafe):** decisão/classificação, barato e rápido por
  chamada, com limiar e rota humana. Não é oráculo.
- **NotebookLM:** roteiro e texto-base, semi-manual, via caderno
  canônico + efêmeros. Não é API estável.
- **Pangram:** só QA de naturalidade do texto. Não gera texto
  humanizado; a empresa é de detecção e afirma não vender humanizador.
  Naturalidade = qualidade editorial, não evasão.
- **Remotion / HyperFrames / FFmpeg:** vídeo determinístico por código
  e encode final. Storyboard antes de renderizar.
- **Mobbin / Magic Patterns:** secundários, opcionais, para referência
  e protótipo de interface (ver `docs/painel-v1.md`). Nunca travam a
  produção se ausentes; podem ser descontinuados depois.
- **Supabase:** banco recomendado para produção (ver `db/schema.sql`).
- **Fora do escopo:** Railway, por decisão do usuário (2026-10-31).
  Não entra em arquitetura, painel ou lista de provedores.

## Riscos assumidos, sem eufemismo

- ADB é o elo frágil: janela curta, porta efêmera, prompt por rede
  nova. Mitigação: gate de acesso, watchdog, log, allow manual quando
  preciso — não promessa de auto-recuperação total.
- Facebook UI dump falha (root nulo): observação só por screencap.
- `input text` com espaço quebra: usar `keyevent 62` para espaços.
- NotebookLM sem API oficial: quebra de automação é esperada; o
  contrato é a exportação, não a integração ao vivo.
- Jev com confiança imperfeita: limiar + humano, sempre.
- Publicação e resposta pelo ADB ainda não estão provadas (só leitura
  e rascunho em laboratório): não prometer a via até os testes 2–4
  passarem com aprovação.
