# Skill: tuttibom-facebook-conteudo

- **Marca:** TuttiBom
- **Conta:** Página TuttiBom no Facebook + Marketplace, via S10
- **Rede:** Facebook — feed e stories
- **Função:** roteiro, vídeo, foto, post e fila de publicação. Não
  publica sem aprovação.
- **Executor hoje:** ADB no S10, via `skills/s10-navegacao/`. Conector
  da Página só no futuro, se a conta ligada for administradora dela.
- **Produtos:** impressão 3D e fita de cetim personalizada, com foto e
  processo reais. Nada de banco de imagem passado por produto próprio.
- **Identidade:** já existe para esta conta; será reavaliada, não criada
  do zero. Brand sheet (cores, tipografia, logo, margens) é pré-requisito
  para fechar template de vídeo — sem ela aprovada, o vídeo fica em
  rascunho.

## Fluxo (rotina R-06)

1. Partir do catálogo + caderno efêmero do NotebookLM (ver
   `skills/tuttibom-notebooklm/`): roteiro, texto e prompts de imagem.
2. Escrever roteiro em `templates/roteiro-video.md` ou texto em
   `templates/post-pagina.md`: o que mostrar, em que ordem, legenda,
   chamada (pergunta, preço, disponibilidade — só se estiver no catálogo).
3. Montar como rascunho e conferir na tela: ordem da mídia, legenda,
   corte do vídeo. Storyboard para o usuário ver antes de renderizar.
4. Renderizar com Muse: Remotion / HyperFrames / FFmpeg, arquivo
   versionado no Drive (`02_Criativos/`), ficha no banco/ops.
5. Entrar na fila em `ops/fila-publicacao.md` como rascunho.
6. Publicar ou agendar só com aprovação explícita, após revisão do
   rascunho na tela. Depois, medir reação (R-09): baseline, 1
   intervenção por vez, leitura em 24h e 72h.

## Ritmo e formatos (fase de testes)

- No máximo 3 posts/semana, dias alternados: 1 processo + 1 produto em
  uso + 1 pergunta/personalização. Nada de 3 posts de venda seguidos.
- Ordem de teste: vídeo curto do processo (15–45 s) → antes/durante/
  depois em 3 fotos → pergunta concreta → personalização como
  protagonista → prova local do Cariri → história curta → preço com
  próximo passo claro (quando o catálogo permitir).
- Uma tarefa por sessão, 1 rascunho de post/vídeo por dia em testes.
- Datas do Cariri com antecedência: festas juninas, Santo Antônio de
  Barbalha, JuáForró, Expocrato, romarias de Juazeiro, Feirart Cariri.

## Problemas específicos desta conta

- Dump de UI nulo e espaço no `input text`: mesmas regras da skill de
  Marketplace (screencap; `keyevent 62`).
- Upload de vídeo é o ponto mais frágil no app: testar com rascunho
  primeiro (tamanho, formato, tempo de espera).
- Processo específico de texto para publicações: ainda a discutir com
  o usuário. Até lá, texto exato aprovado, sem exceção.

## Nunca (além dos guardrails)

- Publicar, agendar ou impulsionar sem aprovação; post em série.
- Engajamento artificial: curtir/comentar/seguir em série.
- Usar foto de cliente sem autorização; copiar criativo de concorrente.
- Texto "humanizado" para burlar detector: naturalidade é qualidade
  editorial para pessoas, com processo e foto reais — nem esconder,
  nem escancarar uso de IA.
