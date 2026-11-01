# Painel v1 — esboço (só leitura)

> Esboço da primeira versão, 2026-10-31. Arquivo visual:
> [`painel-v1/index.html`](../painel-v1/index.html) — abrir no navegador.
> Todos os números no esboço são **mockados e marcados como mock**,
> para validar layout, abas e leitura. Nenhum dado real de comprador,
> nenhuma conversa, nenhum segredo e nenhum endpoint vivo aparecem no
> painel, nem na v1 nem nas próximas versões.

## Governança (decidida pelo usuário)

- Painel **só leitura para o usuário; só o Muse edita e atualiza**.
- Mudança sugerida pelo usuário passa por discussão honesta, com
  avaliação técnica do Muse, e só depois o Muse altera, com versão
  registrada.
- O painel se move porque o Muse atualiza a partir dos fluxos — o
  usuário visualiza e discute o que vê, não edita.
- Sem botão de publicar, responder, apagar, pagar ou impulsionar.
  Aprovação continua acontecendo na conversa, com texto e mídia exatos,
  nunca no painel e nunca em lote ("aprovar tudo" não existe).

## Decisão: Mobbin ou Magic Patterns? Os dois, em sequência

O usuário perguntou qual seria o mais ideal. Resposta técnica, após
pesquisa em 2026-10-31:

- **Mobbin primeiro — referência.** É uma biblioteca de telas reais
  de produtos já lançados, pesquisável por padrão, fluxo e plataforma,
  com integração com Figma e MCP para agentes. Serve para escolher
  padrões provados: dashboard de saúde, fila de aprovações, lista de
  incidentes/falhas, tabelas de métricas. Mobbin não gera a interface
  sozinha; ela mostra o que já funcionou em produção.
- **Magic Patterns depois — protótipo.** É uma ferramenta de IA que
  gera interface a partir de prompt, com editor, fluxos clicáveis e
  exportação para React ou Figma, e pode usar tokens de design
  (cores, tipografia, espaçamento) para não sair genérica. Serve para
  transformar os padrões escolhidos no Mobbin + a brand sheet da
  TuttiBom num protótipo rápido da v1.
- **Se fosse só um:** para um painel interno de operação, Mobbin
  pesaria mais, porque padrão provado de dashboard e incidente vale
  mais que novidade gerada. Para velocidade do esboço, Magic Patterns
  pesaria mais. Como os dois são Pro e secundários, a ordem certa é
  Mobbin → Magic Patterns → rebuild pelo Muse como HTML só leitura
  com contrato de dados real. Nenhum dos dois trava a produção se
  estiver ausente, e ambos podem ser descontinuados depois.
- **Como usar sem copiar:** referência é padrão (ex.: "lista de
  incidentes com severidade, contador e próxima ação"), nunca cópia
  de tela, marca ou texto de outro produto. A identidade visual do
  painel segue a identidade da TuttiBom, a reavaliar, não a de um
  app de referência.
- **Credenciais:** só pelo fluxo seguro, nunca no chat, e só quando
  forem realmente usadas. O esboço v1 foi feito sem acessar Mobbin
  nem Magic Patterns, então nenhuma credencial é necessária para
  validar esta versão. Quando o usuário decidir enviar, será um
  login por vez, pelo cartão seguro, para o site exato (mobbin.com
  ou magicpatterns.com) — não agora, em lote, e não no chat.

## Abas da v1

### 1. Mapa
Hierarquia completa, com o que entra, o que sai e onde há checkpoint
humano: Guardrails → check de acesso Android → skills de setor →
decisão Jev (System 1) + geração Muse/NotebookLM (System 2) → execução
(conector da Página ou ADB da conta pessoal) → auditoria → painel.
Cada nó mostra status do último check (mock na v1).

### 2. Setores (módulos)
Três módulos, cada um com sua máquina de estados e sua fila, sem
misturar: **Marketplace**, **Publicações**, **Interações**.
Cada módulo mostra: rascunhos, aprovados, publicados, atrasados e
próxima ação. Publicação em feed + stories, e Página + Marketplace
quando fizer sentido — cada frente com fila própria.

### 3. Aprovações
O que está parado esperando o usuário, com título, produto, rede,
formato, texto resumido e mídia indicada — nunca o texto completo de
uma conversa, nunca dado de comprador. Na v1, as aprovações são mock
e não aprovam nada de verdade; na versão com dados reais, a aprovação
continua na conversa, e o painel só reflete o estado depois.

### 4. Falhas
Taxonomia em dois eixos, com contadores por dia, semana e mês:

- **Crítica, interrompe o processo:** ADB fora, prompt de rede sem
  resposta, verificação do Facebook, sessão expirada, publicação sem
  prova. Exige humano, e o fluxo para.
- **Não crítica, não interrompe:** métrica atrasada, Jev abaixo do
  limiar (vai para humano), render que falhou e pode ser refeito,
  leitura que se resolve no próximo ciclo.

Cada falha: tipo, severidade, módulo, conta/rede, horário, causa
(conhecida ou desconhecida — nunca inventada), impacto e próxima ação.
Contadores por período servem para montar estratégia de correção:
exemplo de regra a calibrar — 3 falhas críticas do mesmo tipo em 7
dias disparam revisão da rotina, não retry em rajada.

### 5. Provedores, tokens e disponibilidade
Status com último check e horário, nunca "online" genérico: Muse,
SSH, ADB, Facebook (app no S10), NotebookLM, Jev, Supabase, Drive,
Mobbin, Magic Patterns, Figma Pro. E custo na mesma tela: tokens por
provedor e por tarefa, custo estimado por lote, tempo de render local.
Limiar de aviso a calibrar: se custo por lote subir ou confiança do
Jev cair, degrada para revisão humana.

### 6. Saúde do dispositivo
S10: bateria, disco, memória, uptime, reinícios, último watchdog,
último ADB FOUND, rede atual (sem nome de rede sensível no painel,
só "rede nova" / "rede conhecida" quando relevante para o prompt).
Se o telefone reiniciou ou trocou de rede, isso aparece aqui antes
de qualquer ação no app.

### 7. Skills e módulos (adicionada em 2026-10-31)
Contrato genérico + instâncias com nome, função, escopo e produto:
`tuttibom-facebook-marketplace`, `tuttibom-facebook-conteudo`,
`tuttibom-notebooklm`, `tuttibom-observabilidade`. Futuro, só como
padrão de nome: `tuttibom-tiktok-conteudo` — não criado. Ver
[`docs/skills-modulares.md`](skills-modulares.md).

## Contrato de dados (v1 → real)

| Aba | Fonte na v1 | Fonte real (futuro) | Atraso aceitável |
|---|---|---|---|
| Mapa | Mock fixo | Snapshot gerado pelo Muse | A cada atualização do Muse |
| Setores | Mock fixo | `ops/` + banco Supabase | Até o fim da sessão |
| Aprovações | Mock fixo | Fila aprovada na conversa | Imediato após aprovação |
| Falhas | Mock fixo | Logs + banco (tabela falhas) | Até o fim da sessão |
| Provedores | Mock fixo | Checks do Muse + APIs | Último check registrado |
| Saúde S10 | Mock fixo | SSH + logs do watchdog | Último check registrado |
| Skills | Mock fixo | `skills/` no repo | A cada skill criada/alterada |

**Nunca vai para o painel:** senha, token, chave, cookie, endpoint
vivo com porta, nome/telefone/email/endereço de comprador, conteúdo
de conversa, foto de cliente sem autorização, dado de outra conta.

## O que a v1 NÃO é (para não confundir)

- Não é o painel final, não é um app, não é um executor.
- Não publica, não responde, não agenda sozinha, não edita o Drive.
- Não substitui a conversa: a decisão continua sendo discutida aqui,
  com o painel como mapa do que está acontecendo.
- Não usa Mobbin nem Magic Patterns ao vivo: o esboço foi desenhado
  a partir dos padrões descritos acima, sem credencial.

## Próximos passos do painel (após aprovação da v1)

1. Usuário valida abas, ordem e o que falta/sobra no esboço.
2. Escolher padrões no Mobbin (dashboard, fila, incidentes) e gerar
   protótipo no Magic Patterns com a brand sheet — só então, se o
   usuário quiser, enviar credenciais pelo fluxo seguro.
3. Muse rebuilda o painel como HTML só leitura com o contrato de
   dados acima, ainda sem dado real.
4. Conectar o painel ao Supabase (quando o projeto for criado) e ao
   Drive (só metadados, nunca arquivo grande no painel).
5. Calibrar limiares: falhas por período, custo por lote, confiança
   do Jev, e regras de degradação para revisão humana.
