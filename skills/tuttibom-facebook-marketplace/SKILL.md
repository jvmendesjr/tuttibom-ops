# Skill: tuttibom-facebook-marketplace

- **Marca:** TuttiBom
- **Conta:** conta pessoal da loja no Facebook, logada no Galaxy S10 Lite
- **Rede:** Facebook — Marketplace
- **Função:** criar anúncio em rascunho, triar interessados, encaminhar
  ao usuário. Não publica, não responde com preço, não fecha venda.
- **Agentes Paperclip que usam esta skill:** Triagem (triagem de
  compradores, padrões de mensagem, registro de incidentes),
  Publicação (rascunho de anúncio, preço, anúncio parado) e Revisão
  (saúde da conta). Fase: F4 (contratos) / F6 e F7 (reel de teste e
  publicação piloto).
- **Executor:** ADB no S10, via `skills/s10-navegacao/`. O conector
  nativo do Muse NÃO é executor desta conta (não está ligado a conta
  nenhuma neste ambiente; outra conta seria autor errado).
- **Produtos:** fita de cetim personalizada (15/22 mm, 10/25/50 m,
  hotstamp Preto/Dourado/Prata) e impressão 3D, só com os dados de
  `catalogo/`. Preço para o Facebook ainda pendente — nunca inventar,
  nunca usar preço da Shopee como preço do Facebook sem aprovação do
  usuário.
- **Região:** Cariri — Juazeiro do Norte / Crato / Barbalha. Filtro de
  Marketplace: Juazeiro do Norte.
- **Modo de operação:** vendedora. O lado comprador (buscar ofertas,
  retirada como compradora) está quase todo fora desta skill; dele só
  se aproveita a lógica de triagem de compradores.

## 1. Princípios e travas

Estas travas valem acima de qualquer regra herdada da skill original.

1. **Nada publica, envia, responde com compromisso ou acerta preço
   sem a aprovação do usuário ao texto exato.** O trabalho sempre
   chega como rascunho primeiro.
2. **O S10 via ADB é o único caminho de escrita que toca a conta da
   loja.** Nada de atalho de desktop, nada de sessão de Chrome com
   cookies repetindo chamadas GraphQL, nada de conector separado.
   Ações logadas são manuais ou assistidas, uma de cada vez.
3. **Nada irreversível sem confirmação explícita.** Publicar, excluir,
   responder, segurar, marcar como vendido: cada passo pede
   confirmação antes.
4. **Sem dado pessoal de comprador no repo.** Padrões de mensagem sim;
   nome, telefone e endereço, não. As notas de trabalho por lead
   ficam só no Drive privado do usuário.
5. **Mídia 100% fictícia, gerada por IA ou código.** Nenhuma foto ou
   vídeo real de cliente entra em criativo ou anúncio.
6. **Regra de IA:** seguir a regra da plataforma e ligar o rótulo
   quando exigido; nunca dizer ou insinuar que o conteúdo NÃO é IA;
   não colocar anúncio gratuito de IA no texto da legenda.
7. **"Humanizar" é qualidade editorial:** texto natural e agradável
   para pessoas, não disfarce de automação nem truque para enganar
   detector. Anúncio com cara de IA perde confiança.
8. **Navegação no S10 é cautelosa e humanizada,** um passo por vez,
   sem rajadas de toques nem retries apressados. **Modo segurança
   vence velocidade:** sinal de golpe, pressa artificial, pedido de
   pagamento fora da plataforma ou urgência falsa — parar de otimizar
   conversão, resumir o risco e propor o passo mais seguro.

## 2. Superfícies — o que cada uma pode fazer

Três superfícies diferentes; nunca presumir que um recurso existe
em todas.

- **Web pública (só leitura):** pesquisar anúncios públicos, comparar
  preços de concorrentes no Cariri, ler páginas de item. É a
  superfície segura para pesquisa assistida. Nada de login aqui.
- **Web logada (referência, não escrita):** serve para entender
  fluxos e conferir como o Marketplace se comporta no desktop.
  Não é caminho de escrita da TuttiBom: nenhuma ação que toque a
  conta sai daqui.
- **App no S10 (único caminho de escrita):** publicar rascunho,
  responder, gerenciar anúncios — sempre por ADB, com a tela
  verificada e acordada antes de cada toque.

### Particularidades do S10 e do app

1. **Dump de UI do Facebook falha (root nulo).** Observação só por
   screencap e checagem de app em foco. Nunca agir sobre tela em cache.
2. **`input text` com espaço quebra.** Espaço vai por `keyevent 62`;
   `%20` digita os caracteres literais.
3. **Banner de confirmação de email.** Dispensar com o X, sem
   confirmar e sem adicionar email, salvo instrução explícita do usuário.
4. **Tela do S10 dorme e volta preta.** Regra de vigília: verificar,
   acordar com `keyevent 224`, confirmar Awake, recapturar se preto,
   antes de qualquer toque.
5. **Oferta local desigual (pesquisa 2026-10-30, só leitura).**
   "Fita de cetim" sem oferta local na primeira tela (resultados a
   400–490 km); "impressao 3d" com oferta forte local, chaveiros
   personalizados a R$6–R$8, tema Nossa Senhora Aparecida em destaque.
   Isso é contexto de mercado, não preço a copiar.

## 3. Memória — onde cada coisa mora

A estrutura de memória da skill original foi mapeada para os
caminhos do projeto. Nada de `~/facebook-marketplace/` solto.

| Original | TuttiBom | O que vai dentro |
|---|---|---|
| `memory.md` | Drive privado (CRM) + `ops/` | Perfil da operação, região, regras duráveis |
| `inventory.md` | `catalogo/` + `ops/fila-publicacao.md` | Produto, preço pedido, piso, preço de venda rápida, estado do anúncio |
| `message-lab.md` | `templates/resposta-interessado.md` + `ops/triagem-interessados.md` | Padrões de resposta, faixas de oferta, regras de não comparecimento |
| `incident-log.md` | `ops/saude-da-conta.md` | Golpes, disputas, cancelamentos, padrões bloqueados |
| `account-health.md` | `ops/saude-da-conta.md` | Avisos, remoções, recursos, condições de parada |
| `saved-searches.md` | `docs/pesquisa-concorrencia-preco.md` | Só o recorte de pesquisa de concorrência; lista de compras não existe aqui |

Regras: guardar contexto durável, não transcrição de conversa.
Estado do anúncio: `rascunho | ativo | parado | pendente | vendido`.
Padrões de mensagem guardam o texto-tipo, nunca nome, telefone ou
endereço de comprador. Se o usuário recusar persistência, operar
sem memória.

## 4. Preço — o triângulo, só depois da decisão

**O preço do Facebook ainda está indeciso. O triângulo de preço só
vale depois que o usuário decidir o preço — nunca inventar preço.**

Quando o preço existir, definir os três números antes de publicar:
**preço pedido** (deixa margem para a negociação esperada), **piso**
(menor valor aceitável para fechar) e **venda rápida** (só quando o
tempo importa mais que a margem).

Base para os três números: comparáveis locais no Cariri, não
anúncios aspiracionais nem preço nacional de item que só vende
localmente; condição, completude (largura, metragem, cor do
hotstamp), prazo de produção (3–5 dias úteis) e esforço de retirada
ou embalagem. Preços da Shopee e da pesquisa de concorrência são
contexto de mercado, não preço a copiar — e nunca viram preço do
Facebook sem aprovação. Para item de baixo valor ou retirada local,
distância e esforço podem pesar mais que o preço de tabela.

## 5. Anúncio — rascunho primeiro, diagnóstico antes de editar

O anúncio responde às primeiras dúvidas do comprador sem parecer
forçado: nome exato do item e palavras úteis (fita de cetim
personalizada, 15 ou 22 mm, metragem; peça impressa em 3D, material
e uso); condição declarada com clareza (produto novo, feito sob
encomenda); o que está incluído e o que não está; por que o preço
faz sentido; cidade de retirada (Juazeiro do Norte) e qualquer
limite real de envio. A primeira foto ganha o clique. O título não
carrega o anúncio sozinho. Mídia do anúncio é fictícia (IA/código),
conforme a diretriz do projeto.

**Categoria e condição:** categoria errada ou condição enganosa gera
lead ruim e disputa depois. Escolher a categoria mais precisa, mesmo
que outra pareça mais movimentada. Se houver limite ou defeito, dizer
antes de o comprador perguntar. Nunca inventar medida, material,
estoque, prazo, cor ou preço.

**Antes de baixar o preço, melhorar a conversão,** nesta ordem:
clareza da foto de capa, especificidade do título, partes incluídas
e medidas, honestidade da condição, termos de retirada ou envio. Se
isso estiver fraco, um desconto só atrai comprador de qualidade pior.

**Anúncio parado — diagnosticar antes de editar.** Não reeditar no
impulso nem republicar em repetição. Checar, nesta ordem: preço
errado, fotos fracas, texto vago, categoria errada, atrito de
retirada, disponibilidade irreal. Só depois decidir: revisar, pausar
ou manter — e registrar o diagnóstico em `ops/fila-publicacao.md`.

### R-04 — Anúncio em rascunho (não publica)

1. Partir de `catalogo/` + `templates/anuncio-marketplace.md`.
2. Conferir cada campo na tela antes de avançar.
3. Salvar como rascunho e confirmar o estado "rascunho" por screencap.
4. Registrar em `ops/fila-publicacao.md` e em `experimentos/`.
5. Publicar só com aprovação explícita, após revisão do rascunho na tela.

## 6. Mensagens — baseadas em evidência, com texto aprovado

Antes de avançar um negócio, confirmar o que muda a decisão: o
produto exato (largura, metragem, cor do hotstamp, modelo 3D);
quantidade e prazo de produção; disponibilidade e janela de retirada;
forma de pagamento e quem paga o envio, se houver. Resposta vaga de
comprador não é prova. Cada mensagem faz um trabalho por vez:
confirmar disponibilidade, confirmar os fatos que mudam a decisão,
testar flexibilidade de preço, fechar o encontro. Primeira resposta
curta e crível; nada de muralha de perguntas antes de confirmar que
o interesse é real.

**Faixa de oferta:** três zonas, definidas antes de responder —
aceite imediato, contraproposta e recusa. Contrapropor só quando o
comprador parece real. Comprador de baixo esforço e comunicação
fraca costuma virar não comparecimento.

**Política de reserva (definir antes de precisar):** sem reserva;
reserva curta com horário confirmado; reserva só após pagamento
protegido, se o fluxo da plataforma permitir. Nunca inventar regra
de reserva no meio da pressão.

**Não comparecimento:** para padrões que se repetem, apertar o
sistema — confirmação no mesmo dia, janelas exatas de retirada, um
único lembrete, liberação automática após a janela perdida. Não
gastar energia perseguindo lead fraco.

### R-05 — Triagem e encaminhamento (não responde o que compromete)

1. Listar conversas novas, sem responder fora da fila.
2. Classificar em `ops/triagem-interessados.md`: interessado, dúvida,
   golpe suspeito, spam. Sinais de golpe: pressa artificial, pedido
   para sair da plataforma, pagamento por outro canal, código de
   verificação, link estranho, valor acima do pedido — parar e
   encaminhar ao usuário.
3. Encaminhar resumo: produto, pergunta, valor mencionado, urgência,
   próximo passo sugerido — sem comprometer preço, reserva ou encontro.
4. Resposta só com texto aprovado ou a partir de
   `templates/resposta-interessado.md`, sempre registrada.
5. Jev pode classificar tipo, urgência e risco, com limiar e rota
   humana; Jev não gera a resposta e não aprova nada.

**Atenção:** responder pelo ADB ainda não está provado. Até a prova,
toda resposta é rascunho para aprovação do usuário, nunca envio direto.

## 7. Entrega, envio e proteção

- **Retirada local é o padrão** no Cariri: menos ambiguidade na
  conferência do produto, sem custo de embalagem e sem disputa de
  entrega. Encontro só com o que foi combinado e aprovado.
- **Envio é troca, não padrão:** amplia o alcance, mas soma taxas,
  esforço de embalagem, risco de dano, disputas e fraude. Só vale
  quando margem, risco e proteção da plataforma continuarem fazendo
  sentido depois de todos os custos. A fita não é lavável e é
  sensível a atrito — embalar protegendo o hotstamp.
- **Cadeia de prova da vendedora:** foto do item antes de embalar,
  foto da embalagem, comprovante de postagem ou entrega, notas de
  linha do tempo se algo der errado. Prova boa transforma disputa
  vaga em caso documentável. (Prova de transação é evidência
  operacional, não material de publicação.)
- **Pagamento fica na plataforma.** Nada de depósito avulso, atalho
  de pagamento paralelo ou prova fora da plataforma por conveniência.
  Antes de pagar ou receber, confirmar que proteção o fluxo da
  plataforma de fato oferece para aquela transação.
- **Se a transação ficar confusa, documentar primeiro e aconselhar
  depois.** Não improvisar sobre prova faltando, endereço vago ou
  termo mudado.

## 8. Saúde da conta

**Condições de parada:** parar o conselho normal de venda e entrar
em modo de recuperação quando remoções começam a se repetir; o
usuário menciona restrição ou perda de recurso; aparecem pedidos de
identidade ou verificação; categorias de risco ou contatos de golpe
se acumulam. Modo de recuperação é ação mais lenta, mais limpa e
baseada em evidência.

**Anúncio removido ou aviso:** capturar a mensagem exata e o
horário; guardar prints, texto do anúncio e fotos; identificar o
provável desencontro de política; revisar fatos, categoria ou item
antes de republicar. Registrar tudo em `ops/saude-da-conta.md` com
data, motivo aparente e evidência descrita (sem dado pessoal).
Repetir publicação após aviso, duplicar anúncio ou editar às
pressas é proibido sem revisão humana.

**Recursos:** recurso funciona melhor com história simples — qual
item foi anunciado, por que ele é permitido ou está descrito com
precisão, e que evidência prova isso. Nada de explicação emocional
ou especulativa.

## O que esta skill NÃO faz

- Não publica, não envia mensagem e não fecha venda sem aprovação
  do usuário ao texto exato.
- Não inventa API, CLI ou endpoint Graph do Marketplace; não promete
  postagem ou mensagem automatizada.
- Não recomenda bot, scraping atrás de login, mensagem em massa,
  republicação em série, fazenda de contas ou tática de
  anti-detecção.
- Não ajuda a contornar restrição, burlar aviso ou falsificar
  identidade.
- Não garante venda, prazo de entrega, elegibilidade de envio ou
  resultado de política.
- Não compra por conta da loja nem gerencia lista de compras — o
  lado comprador está fora, exceto a triagem de compradores.
- Não pede senha, código, dado de cartão ou documento em texto
  aberto; não move pagamento para fora da plataforma.

## Origem

Adaptada de `ivangdavila/facebook-marketplace` (OpenClaw/ClawHub,
espelho `dvcrn/openclaw-skills-marketplace`), reescrita em PT-BR
para a TuttiBom, com as guardrails do projeto embutidas. Licença da
skill original não confirmada — nenhuma licença é afirmada aqui.
