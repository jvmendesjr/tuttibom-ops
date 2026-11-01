# Como descobrir a reação da plataforma via métricas

> A plataforma não explica o que fez. Ela reage em métricas, em estado
> de anúncio e em notificações. Este documento ensina a ler essa
> reação sem inventar causalidade: um post que caiu não prova
> punição, e um post que subiu não prova recompensa.

## Método: linha de base → intervenção → janela

Toda ação publicável é uma intervenção, e toda intervenção precisa
de uma linha de base antes dela.

1. **Linha de base (antes):** ler métricas da Página e do anúncio
   (rotina R-08) e registrar: alcance, interações, seguidores,
   perguntas, estado dos anúncios. Sem base, não há "reação".
2. **Intervenção (uma por vez):** publicar um post, criar um anúncio,
   responder uma leva de interessados, mudar um preço — nunca duas
   mudanças grandes no mesmo dia na fase de testes. Se duas coisas
   mudam juntas, não dá para saber qual reagiu.
3. **Janela de leitura:** 24 h e 72 h depois da intervenção, no mesmo
   horário aproximado. Alcance de 1 hora não é reação, é ruído.
4. **Comparar com o próprio histórico, não com a internet:** o post
   anterior do mesmo tipo (foto de produto, vídeo de processo) é o
   controle. Comparar vídeo de impressão 3D com foto de fita é
   comparar coisas diferentes.
5. **Registrar em `ops/reacao-plataforma.md`:** hipótese, intervenção,
   base, 24 h, 72 h, conclusão provisória.

## Sinais e o que cada um sugere (não prova)

| Sinal | Sugere investigar | Não concluir sozinho |
|-------|-------------------|----------------------|
| Alcance cai de repente, em vários posts, após aviso/restrição | Efeito de evento de conta | "Fui punido para sempre" — pode ser janela, conteúdo ou dia da semana |
| Anúncio fica muito tempo "em revisão" | Revisão manual ou sensibilidade do tema/foto | Bloqueio — esperar a janela e checar notificação/email |
| Anúncio removido com motivo | Regra violada no texto, foto ou categoria | Que todos os anúncios vão cair — corrigir o ponto, não apagar tudo |
| Alcance sobe num post, cai no seguinte | Conteúdo, horário, formato | Que a plataforma "gosta" do agente — é o conteúdo que variou |
| Perguntas sobem sem alcance subir | Chamada e preço claros, público certo | Que alcance não importa — ele importa para trazer gente nova |
| Mensagens sobem, vendas não | Preço, retirada, prazo ou resposta lenta | Que o anúncio está ruim — pode ser a oferta, não o alcance |
| Zero entrega após login novo / verificação | Verificação pendente ou restrição | Que a conta morreu — checar notificações e email primeiro |

## Confundidores: antes de culpar a plataforma, checar

- Dia da semana e horário (fim de semana vs. dia útil, noite vs. dia).
- Formato (vídeo vs. foto), primeira foto, primeira frase, preço
  visível ou não.
- Frequência: post em série no mesmo dia dilui cada post.
- Evento de conta no mesmo período (aviso, remoção, revisão).
- Sazonalidade do produto (fita para festa, item 3D para presente).
- Mudança no próprio catálogo (preço, foto, descrição).

Regra: se há confundidor óbvio, a conclusão fica como "inconclusiva"
e o teste se repete com o confundidor controlado.

## O que conta como descoberta

Uma reação só vira regra do projeto depois de se repetir em 3
intervenções comparáveis, sem confundidor dominante, registradas em
`ops/reacao-plataforma.md`. Antes disso, é hipótese — e hipótese se
escreve com ponto de interrogação.

Exemplos de regras que podem emergir (não assumir antes de testar):
- "Vídeo de processo tem mais pergunta por alcance que foto estática?"
- "Post com preço no texto gera mais pergunta que post sem preço?"
- "Anúncio com foto X fica mais tempo em revisão que com foto Y?"

## Limites

- Métricas do app são agregadas e atrasadas; não dão o motivo exato
  de uma decisão da plataforma.
- Nunca testar reação provocando a plataforma: não publicar conteúdo
  arriscado "para ver se cai", não forçar volume, não testar limite
  de restrição. Descobrir reação é observar o uso normal, não
  provocar punição.
- Se a reação vier junto com aviso/restrição, a rotina para e vai
  para `ops/saude-da-conta.md` — a descoberta não vale a conta.
