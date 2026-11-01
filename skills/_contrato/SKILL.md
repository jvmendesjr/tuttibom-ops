# Contrato genérico de skill — NÃO usar direto, instanciar

Toda skill deste projeto nasce deste contrato. O contrato é genérico e
reaproveitável; a instância é específica. Nunca rode o contrato vazio:
sempre rode a instância com nome, função, escopo e produto preenchidos.

## Nome da instância

Formato obrigatório: `<marca>-<rede>-<funcao>`

Exemplos já definidos:
- `tuttibom-facebook-marketplace` — vender no Marketplace do Facebook.
- `tuttibom-facebook-conteudo` — posts e vídeos da Página no Facebook.
- `tuttibom-notebooklm` — caderno canônico + cadernos efêmeros.
- `tuttibom-observabilidade` — painel, falhas, tokens e saúde do S10.

Exemplo futuro, só como padrão de nome (não criado, não aprovado):
- `tuttibom-tiktok-conteudo` — mesma estrutura, outra rede, outras
  especificidades. Criar só quando a rede entrar de fato no projeto.

## Variáveis da instância (preencher todas, sem inventar)

- `marca:` ex.: TuttiBom
- `conta:` ex.: conta pessoal da loja no Facebook, no S10
- `rede:` ex.: Facebook
- `executor:` ex.: ADB no S10 (conta pessoal) / conector da Página (futuro)
- `produtos:` ex.: impressão 3D; fita de cetim personalizada
- `regiao:` ex.: Cariri — Juazeiro do Norte / Crato / Barbalha
- `problemas_especificos:` lista fechada, com evidência, ex.: dump de UI
  nulo no Facebook, espaço no `input text`, banner de confirmação de
  email, filtro de Marketplace por Juazeiro do Norte.
- `fontes_de_verdade:` catálogo, templates, Drive, banco, caderno canônico
- `limites:` os da guardrail + os da fase de testes

## Contrato (campos obrigatórios em toda instância)

1. **Propósito** — uma frase: o que esta skill faz, e o que ela NÃO faz.
2. **Gatilho** — quando ela começa, e quando ela NÃO começa.
3. **Entradas** — o que precisa estar pronto e aprovado antes do passo 1.
4. **Passos determinísticos** — em ordem, um passo por vez, com checkpoint
   (screencap, leitura, log ou arquivo) antes de avançar.
5. **Pontos de decisão** — onde entra Jev (com limiar e rota humana) e
   onde entra o humano (texto e mídia exatos, preço, exceção).
6. **Condições de parada e rota de fuga** — voltar, home, parar, registrar.
   Objetivo nunca muda na recuperação: rascunho não vira publicação,
   triagem não vira resposta comprometedora.
7. **Saídas** — rascunho, log em `experimentos/`, ficha no banco, arquivo
   no Drive, linha em `ops/`, atualização do painel (só pelo Muse).
8. **Adaptação** — o que muda para outra rede, conta ou nicho, e o que
   NÃO muda (guardrails, aprovação, ritmo, registro, privacidade).
9. **Nunca** — lista explícita, herdada de `skills/guardrails/`, mais as
   proibições específicas da instância.

## Regras de reuso

- **Clonar e bifurcar:** para outro projeto, clone o repositório
  tuttibom-ops, renomeie a marca, substitua só as variáveis da
  instância, e adapte arquitetura e/ou infraestrutura onde o novo
  projeto exigir. Não copie segredo, endpoint vivo, dado de comprador,
  texto, foto, logo ou cliente de outro projeto.
- **Extrair o core:** só quando o motor virar multi-marca de verdade.
  Até lá, o core vive dentro de tuttibom-ops, e as instâncias carregam
  o nome da marca, da rede e do produto — isso é intencional, não
  defeito. Genérico na estrutura, específico na instância.
- **Modelo externo:** skill, plugin ou ferramenta de fora entra como
  padrão, de forma agnóstica: extrai-se a estrutura, descarta-se a
  premissa específica da ferramenta de origem, registra-se a fonte do
  padrão, e o usuário define o setor de aplicação. O Muse observa
  tecnicamente outros setores onde o padrão também serve.
- **Versão:** mudança de contrato gera entrada em RELATORIO.md e, se
  mudar comportamento, nova rodada de testes em laboratório (3
  execuções limpas) antes de ir para a conta principal.
