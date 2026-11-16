# Pesquisa: interação com consumidores e CRM dos interessados

> Pesquisa de 2026-10-30, guardada no repositório local. Ideia para
> testar, não sistema contratado. Nada aqui envia mensagem sozinho:
> toda resposta que compromete preço, reserva, encontro ou pagamento
> passa por aprovação do usuário (skills/guardrails/SKILL.md).

## Skills que alimentam isto

### Do Muse (lidas na íntegra)

- `messaging`: resolver o destinatário pela conversa atual, nunca
  pela memória; ler a conversa antes de responder, para não repetir
  pergunta já respondida; mostrar o texto exato e o destinatário
  antes de enviar; enviar uma vez só — timeout não prova falha, por
  isso reler a conversa antes de qualquer nova tentativa; nunca
  falar pelo usuário além do aprovado, nem acrescentar compromisso,
  promessa ou dado pessoal que ele não deu; conversa delegada tem
  um dono, um objetivo e um ponto de parada.
- `customer-outreach`: escolher público e canal pelo consentimento;
  marketing só para quem optou por receber — responder a quem
  perguntou no Marketplace não é disparo de marketing, mas segue a
  mesma regra de não inventar dado de personalização; prévia com
  público, conteúdo, remetente e horário antes de qualquer envio;
  nunca retentar envio automaticamente; medir resposta qualificada
  e conversão, não só abertura; guardar detalhe de cliente na
  ferramenta do negócio, não em instrução reutilizável.
- `meeting-follow-up` (estrutura aproveitada): transformar conversa
  em decisão, dono e próximo passo com data — é o que o CRM faz com
  cada thread do Marketplace.
- `marketplaces` e as duas skills de referência do projeto
  (ClawHub e Printing Press): padrões de mensagem de comprador e
  vendedor, log de incidentes e de saúde da conta, e trava de
  escrita (rascunho antes de enviar).

### Da comunidade, para situações próximas (venda por Marketplace e
### artesanato, pequeno negócio)

Fontes:
- https://vagasdeempregonordeste.com.br/como-ganhar-dinheiro-com-o-facebook-marketplace/
- https://sacredspacesllc.com/how-to-respond-on-facebook-marketplace/
- https://improveworkspace.com/facebook-marketplace-selling-etiquette/
- https://www.infinitepay.io/materiais/planilha-de-controle-de-clientes-gratis
- https://saleoid.com/blog/sales-crm-features-for-small-businesses/
- https://bolde.fi/blog/simple-crm-spreadsheet-for-freelancers.html

O que se repete, em ordem:

1. **Velocidade na primeira resposta.** Responder em até 1 hora,
   em horário comercial, porque o comprador está falando com vários
   vendedores ao mesmo tempo. Resposta rápida não é pressa: é
   confirmar disponibilidade e já puxar o próximo passo ("quando
   você quer retirar?"), com 2–3 opções, não um texto longo.
2. **Clareza antes de preço baixo.** Preço, local de retirada e
   forma de pagamento confirmados antes do encontro; endereço só
   depois de forma de pagamento e horário confirmados; defeito ou
   limite do produto descrito, não escondido.
3. **Tipos de comprador, mesmo tratamento.** Curioso, interessado
   que precisa de convencimento, apreensivo e pronto para comprar —
   e até suspeito de golpe recebe tom cordial, sem dado, sem
   resposta que comprometa nada, e vai direto para o usuário.
4. **Templates, não improviso.** Resposta salva para "ainda está
   disponível?", para preço, para foto extra e para retirada. O
   template acelera sem virar robô: nome, produto e dado do
   catálogo entram na hora, o resto já está pronto.
5. **Follow-up com limite.** Depois de proposta: 2–3 dias, depois
   1 semana; depois disso, vira "adormecido", não insistência.
   Sem resposta não é "não" definitivo para festa futura — é
   motivo de perda a registrar ("sem resposta"), para aprender o
   padrão, não para apagar a conversa.
6. **CRM de planilha basta no começo.** Uma linha por negociação
   (não por pessoa — a mesma pessoa com novo pedido ganha nova
   linha), no máximo 6–7 estágios, cada um com condição de saída
   clara. A regra que mais se repete: **todo negócio aberto tem
   próxima ação e data; sem data, ele será esquecido.** Revisão
   semanal curta (15 min): atualizar estágio, agendar follow-up,
   priorizar os quentes. Só vale migrar para CRM pago (HubSpot
   Free, Pipedrive e afins, citados na comunidade) quando o volume
   passar de ~20 negócios abertos por semana ou quando entrar mais
   gente na operação.

## Ideia de CRM para este projeto (proposta)

### Onde fica

No repositório local, em `ops/triagem-interessados.md`, ampliado
abaixo — não em plataforma externa, não em planilha solta no
celular. É o CRM operacional do experimento, enquanto o volume
for pequeno. Quando crescer, migra-se com os mesmos estágios e
campos, sem recomeçar do zero.

### Privacidade (regra dura)

No repositório, só o mínimo operacional: ID da conversa, anúncio,
produto, personalização, cidade/retirada, estágio, próxima ação e
data. **Nenhum telefone, email ou endereço no repositório.** O
dado pessoal fica na thread do Messenger/Marketplace, que é onde
ele nasceu, e só é usado para a conversa que o usuário aprovou.
Isso segue a regra do `customer-outreach` (detalhe de cliente não
vai para instrução reutilizável) e a do projeto (sem dado pessoal
no repo, `.gitignore` já bloqueia screencap e dump).

### Estágios (6, adaptados ao Marketplace + encomenda)

| Estágio | Significa | Sai quando |
|---------|-----------|------------|
| Novo | Chegou pergunta, ainda não triada | Triagem feita, sem responder o que compromete |
| Contatado | Primeira resposta aprovada enviada | Comprador respondeu com o que quer |
| Qualificado | Sabemos produto, personalização (nome/cor), quantidade, prazo e cidade/retirada | Orçamento/confirmado para enviar |
| Proposta enviada | Preço e prazo do catálogo enviados, com aprovação | Aceitou, recusou ou 7 dias sem resposta |
| Produção / Retirada | Aceitou; produzir, confirmar retirada/entrega | Entregue e pago |
| Fechado / Perdido / Adormecido | Fim do ciclo | Motivo registrado (preço, prazo, sem resposta, concorrente, festa futura) |

### Campos por linha

Data do primeiro contato · Origem (anúncio, Page, grupo) ·
Produto · Personalização · Valor estimado (só do catálogo) ·
Cidade/retirada · Estágio · Última interação · Próxima ação ·
Data do follow-up · Encaminhado ao usuário? · Resposta
aprovada/enviada? · Motivo de perda, se houver.

### Rotina (ligada às rotinas determinísticas)

1. **Triagem (R-05, só leitura):** abrir inbox no S10 via ADB,
   com cautela, anotar cada conversa nova no CRM, classificar
   (interessado / dúvida / golpe / spam). Golpe vai direto ao
   usuário, sem resposta.
2. **Encaminhamento:** Muse resume o interessado para o usuário
   neste chat, com rascunho de resposta exato (template em
   `templates/resposta-interessado.md`, dado só do catálogo).
3. **Envio só após aprovação:** usuário aprova o texto exato; aí
   sim envia via ADB, uma vez, e registra no CRM. Sem aprovação,
   fica em rascunho.
4. **Follow-up:** 1 dia após primeira resposta sem retorno; 2–3
   dias após proposta; 7 dias depois, vira Adormecido. Nunca mais
   de 2 follow-ups por negócio sem resposta nova do comprador.
5. **Revisão semanal:** listar vencidos (follow-up atrasado),
   quentes (Qualificado/Proposta) e motivos de perda. É daqui que
   sai a próxima decisão de produto e preço, não de achismo.

### O que NÃO é CRM aqui

- Não é disparo de marketing, não é lista de contatos para
  campanha, não é automação de resposta (nem a Meta AI automática
  do Marketplace, que a comunidade cita como novidade — ativar
  isso seria entregar a resposta a um sistema fora do nosso
  controle, contra as guardrails).
- Não é escore de lead por dado sensível. Classificação é só por
  comportamento na conversa: respondeu? qualificou? aceitou?

## Próximo passo (para aprovar, não executado)

1. Aprovar os 6 estágios e a cadência acima (ou ajustar).
2. Testar a triagem (R-05) em 1 sessão real, só leitura, e
   preencher 1–3 linhas de exemplo com conversas reais — sem
   enviar nada.
3. Só depois, testar 1 resposta aprovada, medir tempo de resposta
   e registrar o resultado no CRM e no log de reação.
