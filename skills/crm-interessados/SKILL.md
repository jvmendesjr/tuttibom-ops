# Skill — CRM dos interessados (Marketplace / Page)

> Skill própria do projeto, criada a partir de `messaging`,
> `customer-outreach`, `meeting-follow-up`, das skills de referência
> de Marketplace e da pesquisa em
> `docs/pesquisa-interacao-crm.md`. Obedece a
> `skills/guardrails/SKILL.md` em qualquer conflito.

## Propósito

Transformar cada conversa de interessado em um negócio acompanhado
até o fim — sem perder follow-up, sem inventar dado e sem enviar
nada que comprometa preço, reserva, encontro ou pagamento sem
aprovação do usuário.

## Onde fica o CRM

`ops/triagem-interessados.md`, no repositório local. Uma linha por
negociação, não por pessoa. Sem telefone, email ou endereço no
repositório: só ID da conversa, anúncio, produto, personalização,
cidade/retirada, estágio, próxima ação e data. O dado pessoal fica
na thread do Messenger/Marketplace.

## Estágios

Novo → Contatado → Qualificado → Proposta enviada →
Produção / Retirada → Fechado / Perdido / Adormecido.

Qualificado significa: produto, personalização (nome/cor),
quantidade, prazo e cidade/retirada conhecidos. Proposta enviada
só com preço e prazo do catálogo, com aprovação.

## Rotina

1. **Triar (só leitura, rotina R-05):** abrir inbox via ADB, com
   cautela e ritmo humanizado, anotar conversas novas, classificar
   (interessado / dúvida / golpe / spam). Golpe: direto ao usuário,
   sem resposta.
2. **Encaminhar:** resumir o interessado ao usuário, com rascunho
   de resposta exato, usando `templates/resposta-interessado.md` e
   dado só do catálogo.
3. **Enviar só após aprovação:** texto exato aprovado, envio único
   via ADB, registro no CRM. Sem aprovação, fica em rascunho.
4. **Follow-up:** 1 dia após primeira resposta sem retorno; 2–3
   dias após proposta; 7 dias depois, Adormecido. Máximo de 2
   follow-ups por negócio sem resposta nova.
5. **Revisão semanal:** vencidos, quentes e motivos de perda
   (preço, prazo, sem resposta, concorrente, festa futura).

## Regras de interação (da comunidade, adaptadas)

- Primeira resposta em até 1 hora, em horário comercial, quando
  possível — confirmando disponibilidade e puxando o próximo passo
  com 2–3 opções, sem texto longo.
- Preço, retirada e pagamento confirmados antes do encontro;
  endereço só depois de pagamento e horário confirmados.
- Templates para "ainda está disponível?", preço, foto extra e
  retirada — personalizar só com dado real da conversa e do
  catálogo.
- Nunca: resposta automática em massa, disparo de marketing para
  quem não optou, promessa fora do catálogo, pressa artificial,
  código de verificação, pagamento fora da plataforma.
- Timeout ou interrupção não prova falha de envio: reler a
  conversa antes de qualquer nova tentativa, e nunca retentar em
  segundo plano.

## Quando migrar

Migrar para CRM pago (HubSpot Free, Pipedrive ou similar) só
quando houver mais de ~20 negócios abertos por semana ou mais
gente na operação — com os mesmos estágios e campos, sem
recomeçar. Até lá, a planilha do repositório basta, se for
atualizada toda semana.
