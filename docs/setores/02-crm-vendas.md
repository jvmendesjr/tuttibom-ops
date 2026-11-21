# Setor 2 — CRM e Vendas

**Objetivo:** nenhum lead se perde — todo contato tem etapa, próximo
passo e dono, do primeiro "oi" até pago ou perdido.

## Entra / Sai

- **Entra:** novo contato (setor 1), mudança de interesse, pagamento
  confirmado (setor 7), silêncio, pedido de pós-venda.
- **Sai:** etapa atual do lead, o que já foi perguntado e combinado,
  próxima ação com data, e o histórico que o atendimento e a memória
  por contato precisam.

## Faz

- Manter o funil Vendas com as 7 etapas herdadas do Deskcomm: Novo
  contato, Já respondi, Escolhendo o produto, Vai levar, Aguardando
  pagamento, Pedido pago (ganhou), Não comprou (perdeu) — com os
  motivos de perda preço / desistiu / sem resposta / produto
  indisponível / prazo não atende.
- Registrar cada conversa: canal (WhatsApp ou Messenger), produto de
  interesse (fita, 3D, preço), ocasião, e o que foi combinado. Sem
  dado pessoal de comprador no repo — o CRM próprio guarda o mínimo
  para operar, e o detalhe sensível fica fora do versionamento.
- Follow-ups: silêncio enquanto escolhe (1º toque em 24h, 2º em 3
  dias, máx. 3 toques em 2 dias para quem perguntou preço e sumiu) e
  aguardando pagamento (2h e ~24h). Fora de 7h–22h, o disparo aguarda
  a janela; a resposta, não (Ana responde 0–24h).
- Memória por contato: guardar o interesse demonstrado (fita / 3D /
  preço) para, no próximo "olá", ir direto ao produto certo sem
  perguntar de novo. O Jev só recebe o rótulo, nunca PII — o roteador
  decide por código (interesse único + saudação fechada), senão o Jev
  recebe só o rótulo.
- Fechar o lead como pago ou perdido, com motivo, e encerrar a
  conversa à parte quando for o caso (aprendizado do Deskcomm: fechar
  o lead não resolve a conversa sozinho).

## Não faz

- Não escreve a mensagem ao cliente — isso é do setor 1.
- Não decide preço, desconto, frete ou prazo — isso é dos setores 3 e 7.
- Não cria produto nem muda catálogo.
- Não dispara mensagem fora da janela de disparo (7h–22h) nem acima
  do teto de toques.
- Não guarda foto, vídeo ou dado pessoal de comprador no repo.

## Skill e diretório

- `src/tuttibom/crm/` (a criar na worktree `exp/crm-proprio`) +
  `db/schema.sql` — modelo mínimo: lead, conversa, etapa, produto,
  follow-up, memória por contato. Começa com SQLite local; Supabase
  só se o local deixar de bastar.
- Herda o desenho do Deskcomm (funil, follow-ups, memória), não o
  código nem a dependência dele.

## Aprovações

- Mudar etapa de ganho/perda em um caso real, e qualquer follow-up
  fora do roteiro aprovado, passam pelo usuário.
- A estrutura do funil só muda por decisão registrada (D-nova).

## Como se mede que deu certo

- Um lead simulado vai de Novo contato a Pedido pago, e outro a Não
  comprou com motivo, sem pular etapa e sem perder registro.
- Um contato que volta e diz "olá" é reconhecido pelo interesse
  anterior, sem repetir as perguntas iniciais.
- Follow-ups disparam na janela certa e param quando a pessoa responde.

## Handoffs

- Responder o cliente → setor 1 (Atendimento).
- Preço, cor, disponibilidade → setor 3 (Produto e Catálogo).
- Pagamento confirmado, produção, entrega → setor 7 (Operação).
- Erro, lentidão ou perda de dado → setor 8 (Plataforma).
