# Skills modulares — genérico na estrutura, específico na instância

> Decisão do usuário, 2026-10-31: a estrutura é modular para todo o
> desenvolvimento. As skills podem ser genéricas no que for possível,
> mas são focadas no produto atual, com nome, função, escopo e produto
> explícitos, e com os problemas específicos desta marca, desta conta e
> destas plataformas.

## A ideia em uma frase

O esqueleto é o mesmo para todo mundo; o corpo é da TuttiBom, hoje.
Quando entrar outra rede, outra conta ou outro nicho, troca-se o corpo
— nome, rede, produto, problemas específicos — e o esqueleto continua.

## Nome, função, escopo, produto — sempre juntos

Toda instância declara, no topo:

- **Nome:** `tuttibom-facebook-marketplace`, `tuttibom-facebook-conteudo`,
  `tuttibom-notebooklm`, `tuttibom-observabilidade`.
- **Função:** vender / publicar / nortear e gerar roteiro / observar.
- **Escopo:** conta, rede, região, executor, limites da fase.
- **Produto:** impressão 3D e fita de cetim personalizada, com os dados
  que estão no catálogo — nunca com dado inventado.

Sem esses quatro, a skill não está pronta para rodar, mesmo que a
estrutura esteja correta.

## Instâncias atuais (neste repo)

| Instância | Função | Executor hoje | Problemas específicos que ela carrega |
|---|---|---|---|
| tuttibom-facebook-marketplace | Anúncio, triagem, encaminhamento | ADB no S10, conta pessoal da loja | Dump de UI nulo no Facebook (só screencap); espaço no `input text` (usar `keyevent 62`); banner de confirmação de email (dispensar com X, sem confirmar); filtro Juazeiro do Norte; preço para o Facebook ainda pendente — nunca inventar |
| tuttibom-facebook-conteudo | Post, vídeo, fila, reação | ADB no S10, Página + Marketplace | Ritmo máximo 3 posts/semana em testes; nada de 3 vendas seguidas; vídeo de processo antes de catálogo; brand sheet existente a reavaliar |
| tuttibom-notebooklm | Norteador + roteiro/texto/prompts | Conta Google do usuário, semi-manual | Sem API oficial estável; caderno canônico nunca usado para um asset só; caderno efêmero por criativo, com deleção ao fim |
| tuttibom-estudio-criativo (2026-11-01) | Produzir ativo visual finalizado; nunca publica | Muse na VM (Remotion/HyperFrames/FFmpeg) | Brand sheet a validar antes do render final; vídeo bruto pode ter nome de cliente — sanitizar com badge/máscara ou usar arte genérica; encode yuv420p + AAC, stills 1s/6s/12s antes do .mp4 |
| tuttibom-observabilidade | Painel, falhas, tokens, saúde | Muse na VM, lendo logs/banco | Painel só leitura; só o Muse edita; sem dado de comprador; sem endpoint vivo |

## Instância futura, só como exemplo de nome

`tuttibom-tiktok-conteudo` seguiria o mesmo contrato, com outras
especificidades (formato vertical, som, duração, regras da rede) e
outros problemas específicos daquela rede. Ela NÃO existe ainda e NÃO
deve ser criada por antecipação: rede nova só entra após a primeira
aprovada no Facebook, como módulo novo, não como cópia solta.

## Clonar, bifurcar, extrair — quando cada um vale

- **Clonar e bifurcar (hoje, para outro projeto):** copiar o repo
  tuttibom-ops, renomear a marca, trocar as variáveis da instância,
  adaptar arquitetura e/ou infraestrutura onde o novo projeto exigir.
  O que é da TuttiBom fica na TuttiBom; o que é estrutura viaja.
- **Reaproveitar a arquitetura (só ao ampliar ou adicionar algo novo):**
  quando um novo módulo, rede ou conta entra, ele herda guardrails,
  contrato de skill, fila, aprovação, painel e observabilidade — e
  registra o que adaptou.
- **Extrair o core (só se virar multi-marca de verdade):** tirar o
  esqueleto agnóstico para um repo próprio (ex.: `ops-agente`) e deixar
  as instâncias por marca/rede como configuração. Não fazer isso antes
  da hora: extrair cedo cria dois lugares para manter a mesma regra.

## Figma Pro — onde entra

Conta Figma Pro do usuário (informada em 2026-10-31, sem credencial
recebida ou usada até aqui). Papel, secundário e nunca bloqueador:

- **Brand sheet:** fonte visual da identidade existente, a reavaliar.
- **Painel:** Mobbin (referência de padrão) → Figma (layout com a
  identidade) → Magic Patterns (protótipo, exporta para Figma/React)
  → Muse rebuilda como HTML só leitura. Figma é o hub de design, não
  o executor.
- **Criativos:** layouts e variações, sempre com foto e processo
  reais da loja; nunca como substituto do material próprio.
- **Credencial:** só pelo fluxo seguro, para o site exato, quando for
  realmente usada — nunca no chat, nunca em lote, nunca agora por
  antecipação.

## Cadernos NotebookLM — isolamento como prática

O cuidado com os cadernos efêmeros não é burocracia: é isolamento de
produção. Um caderno por criativo evita que o roteiro de um produto
contamine o de outro, que uma decisão de uma publicação vaze para a
próxima, e que um chat longo acumule contexto errado. O usuário já
sentiu isso na prática, e é também o que a comunidade tem praticado:
ambiente isolado, focado só naquele criativo, exportar, deletar, e
só o canônico permanece como memória do projeto.
