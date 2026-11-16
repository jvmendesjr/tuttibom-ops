# Planilha no Drive — CRM TuttiBom (estrutura pronta)

> Título proposto: `CRM TuttiBom — Interessados`.
> Criação via conector de Sheets (`spreadsheets create` + `addSheet`
> + `values append`), só após o usuário conectar Drive e Sheets.
> Nunca subir `.xlsx` por cima: isso apaga as outras abas.
> A planilha é privada do usuário; compartilhar só com aprovação
> dele, no cartão de compartilhamento.

## Aba 1 — Leads

Cabeçalho:
ID conversa | Data 1º contato | Origem / anúncio | Produto |
Personalização | Valor est. (catálogo) | Cidade / retirada |
Estágio | Próxima ação | Data follow-up | Status

Estágios: Novo, Contatado, Qualificado, Proposta enviada,
Produção / Retirada, Fechado, Perdido, Adormecido.

## Aba 2 — Interações

Cabeçalho:
ID conversa | Data | Quem falou | Resumo (3 linhas no máximo) |
Onde parou | Promessa feita | Pendência | Próximo passo

Regra: uma linha por interação relevante, não por mensagem.
Antes de responder, ler a última linha desta aba para o lead.

## Aba 3 — Problemas e Contornos

Cabeçalho:
Problema | Sinal | O que NÃO fazer | Contorno aprovado |
Prevenção | Quantas vezes | Última vez

Linhas iniciais (ver `docs/persona-interacao.md`): sumiço,
pechincha, "Gratuito" confuso, nome/cor errado, cor diferente da
foto, prazo apertado, retirada não comparecida, pagamento fora
da plataforma / golpe, criativo de outro cliente.

## Aba 4 — Criativos

Cabeçalho:
ID conversa | Tipo (prova / foto final / vídeo / post) |
Descrição | Data de entrega | Aprovado por | Autorização p/ feed?

Regra: prova antes de produzir; foto final conferida contra a
ficha; nunca misturar clientes; pedido individual no feed só com
autorização.

## Aba 5 — Resumo

Contagem por estágio, follow-ups vencidos, motivos de perda e
problemas mais frequentes — atualizada na revisão semanal, não a
cada mensagem. Fórmulas simples (CONT.SE / CONT.SES) sobre as
abas 1 e 3, quando a planilha for criada no Sheets.

## Divisão com o repositório local

- Repositório (`ops/triagem-interessados.md`): estrutura, estágios,
  regras e padrões de problema — sem dado pessoal de comprador.
- Drive: notas de trabalho por lead, com o mínimo necessário para
  a entrega, sob controle do usuário.
- Quando o Drive estiver conectado, a planilha vira a fonte
  operacional e o arquivo local passa a ser só espelho de regras,
  não de leads.
