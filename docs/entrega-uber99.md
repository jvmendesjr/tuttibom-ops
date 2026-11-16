# Entrega Uber/99 — como calcular o valor (RASCUNHO)

> **RASCUNHO — pesquisa + proposta, 2026-11-06.** Nada aqui foi aplicado:
> não entrou no pacote, na FAQ, no prompt do agente, na persona nem no
> Deskcomm. O usuário decide o método primeiro.
>
> Contexto: venda local — Crato (origem) e vizinhas, Juazeiro do Norte
> (maior volume de interessados) e Barbalha. Entrega por Uber ou 99,
> com motoqueiro contratado; o valor depende do endereço (variável,
> nunca fixo) e é confirmado no app antes de combinar a entrega.
> Pagamento: Pix. Ver docs/prazos.md (§3 regras 9–10, §4).

## 0. Origem (decidida pelo usuário, 2026-11-06)

**Avenida Pedro Gonçalves Norões, 280, Grangeiro, Crato — CE.**

- É a origem de todas as estimativas e o ponto de retirada.
- Observação de mapa: o OpenStreetMap registra a via como **Rua**
  Pedro Gonçalves Norões, Grangeiro, CEP 63109-086, nas coordenadas
  lat -7,2656683, lon -39,4347378. É a mesma via — "Avenida" (como o
  usuário informou) vs "Rua" (como está no mapa) é diferença de nome
  no cadastro, não outro endereço. Confirmar o pin digitando o
  endereço no app da Uber/99 na primeira vez (ver §4).

## 1. O que a pesquisa encontrou (com fontes)

### 1.1 Uber e 99 — como o preço é formado

- **O preço aparece no app antes de confirmar.** Na 99, o valor de
  99Pop, 99Moto e 99Compartilha é fixo antes de solicitar: é estimado
  por rota, tempo de viagem, distância e demais custos; se a viagem
  exceder muito a estimativa, o valor é recalculado e o passageiro é
  avisado durante a corrida. No 99Táxi a estimativa não é preço
  fechado. Na Uber, o app mostra o preço fechado (upfront) antes de
  confirmar; o valor leva em conta distância, tempo estimado, demanda
  do momento, pedágios e taxas.
  - Fonte: 99 — "Como é calculada a estimativa de valor da corrida?",
    https://www.reclameaqui.com.br/empresa/99taxis/conteudos/como-e-calculada-a-estimativa-de-valor-da-corrida_pN4Y6cT7twd1EED4/
  - Fonte: "Como funciona o aplicativo do Uber 99?",
    https://vocepergunta.com/library/artigo/read/420436-como-funciona-o-aplicativo-do-uber-99

- **Uber tem um estimador na web, mas não é uma ferramenta de
  cotação.** O Uber oferece um estimador de preço no site
  (uber.com/us/en/price-estimate), que dá uma faixa, não um valor
  travado — e a disponibilidade dele varia; há relatos de que, para
  alguns trajetos, ele responde que a estimativa não está disponível
  e manda baixar o app. Calculadoras de terceiros usam médias dos
  EUA e não servem para o Cariri.
  - Fonte: "3 Ways to Get an Uber Fare Estimate in Advance",
    https://www.thetechedvocate.org/3-ways-to-get-an-uber-fare-estimate-in-advance/

- **API da Uber existe, mas não é viável para a TuttiBom agora.**
  A Rides API v1.2 tem `GET /v1.2/estimates/price` (estimativa de
  preço) e `POST /v1.2/requests/estimate` (estimativa para reserva).
  Para usar, é preciso conta de desenvolvedor na Uber, cadastro de
  um app e token OAuth (client credentials grant) — os antigos
  server tokens estão sendo descontinuados. Além disso, a Rides API
  cobre corridas (UberX etc.), não entrega de encomenda; entrega é
  outro produto (Uber Direct), com onboarding comercial próprio.
  Conclusão: burocracia e manutenção para obter um número que o app
  já mostra de graça em segundos.
  - Fonte: Uber Developers — documentação de migração da Ride
    Request API (server tokens descontinuados; OAuth Bearer token
    com escopo; `GET /v1.2/estimates/price`); resumo em
    https://copyprogramming.com/howto/uber-ride-request-using-api

- **99 não tem API pública nem estimador na web.** Nada foi
  encontrado: nem API de estimativa, nem página pública de cotação.
  A estimativa vive só dentro do app (digitar o destino → o preço
  aparece antes de confirmar). A categoria de entrega é a **99Entrega**;
  a **99Moto** transporta passageiro e faz entregas. Conclusão: para
  a 99, o app é a única fonte do valor exato.

- **Conclusão do §1.1:** não existe caminho oficial, gratuito e sem
  login para obter o valor EXATO da Uber/99 a partir de um endereço
  de forma automática. O valor exato vem do app, na hora de contratar.
  O que DÁ para calcular automaticamente é a **distância por rua** —
  e a distância vira valor pela **média local (R$/km)**. É por isso que
  o método recomendado (§2) tem duas peças: tabela de médias (para
  cotar) + conferência no app na hora (para fechar).

### 1.2 Distância sem chave paga (verificado ao vivo, 2026-11-06)

Tudo abaixo foi testado com chamadas reais nesta pesquisa, a partir
da origem do §0 (lat -7,2656683, lon -39,4347378).

- **Nominatim (geocodificador do OpenStreetMap):** gratuito, sem
  chave. Converte endereço em coordenadas. Política de uso: no máximo
  1 requisição por segundo e um User-Agent identificando quem chama.
  - Fonte: https://github.com/dvcrn/openclaw-skills-marketplace/blob/HEAD/plugins/adhishthite--maps-osrm/skills/maps/SKILL.md

- **OSRM (Open Source Routing Machine), servidor público de
  demonstração:** gratuito, sem chave. Calcula a rota por rua entre
  dois pontos e devolve distância e duração. Endpoint usado:
  `https://router.project-osrm.org/route/v1/driving/{lon},{lat};{lon},{lat}?overview=false`
  O servidor de demonstração é uma cortesia, sem SLA e sem trânsito
  ao vivo; uso razoável (poucas consultas por venda) é o uso previsto.
  Para uso pesado, o caminho é auto-hospedar o OSRM. Não há trânsito
  em tempo real — a duração é estimada pelo tipo de via.
  - Fonte: https://bytetools.bytevancer.com/public-apis/geolocation/osrm-routing-api

- **OpenRouteService (ORS):** alternativa com chave gratuita —
  plano Standard gratuito: 2.000 direções/dia, 40/minuto (cadastro em
  openrouteservice.org). Só vale a pena se o servidor de demonstração
  do OSRM ficar indisponível ou lento; para o volume da TuttiBom,
  o OSRM basta.
  - Fonte: https://staging.openrouteservice.org/plans/
  - Fonte: https://github.com/avinashlng1080/travel-planner/blob/HEAD/OPENROUTESERVICE_SETUP.md

- **Google Maps (Distance Matrix):** pago (cerca de US$ 5 por 1.000
  requisições), exige chave e cartão — não é necessário; o OSM cobre
  o uso.

- **Distâncias medidas ao vivo, da origem (§0):**

  | Destino | Distância por rua | Duração |
  |---|---|---|
  | Centro do Crato | 4,9 km | 8 min |
  | Juazeiro do Norte (centro) | 17,0 km | 21 min |
  | Barbalha (centro) | 25,5 km | 31 min |

  Os destinos acima são os centros das cidades. O endereço exato do
  comprador dá a distância exata — é a mesma conta, trocando o ponto
  final. As distâncias foram medidas com Nominatim (geocodificação)
  + OSRM (rota) em 2026-11-06.

- **Como reproduzir a medição** (para preencher a tabela do §2):

  ```
  # 1. Geocodificar o endereço (1 req/seg, com User-Agent próprio):
  curl -A "TuttiBom/1.0" "https://nominatim.openstreetmap.org/search?q=<endereço>&format=json&limit=1"
  # 2. Rota da origem (lon -39,4347378, lat -7,2656683) ao destino:
  curl "https://router.project-osrm.org/route/v1/driving/-39.4347378,-7.2656683;<lon>,<lat>?overview=false"
  # A resposta traz routes[0].distance (metros) e routes[0].duration (segundos).
  ```

### 1.3 Como pequenos negócios locais lidam com frete variável

- **Tabela por bairro ou por faixa de distância** é o padrão. Exemplo
  publicado (Menuzia, hamburgueria): até 3 km R$ 5; 3 a 6 km R$ 8;
  6 a 10 km R$ 12; acima de 10 km, não entrega. A lógica: perto da
  loja a taxa fica abaixo do custo (atrai pedido), longe cobre a
  diferença — na média, a conta fecha. Por bairro é mais fácil para o
  cliente entender; por km é mais justo quando os bairros são grandes
  ou irregulares. Muitas centrais misturam: faixas por bairro, com
  adicional por km fora da área.
  - Fonte: https://www.menuzia.com.br/blog/tutoriais/como-configurar-taxa-de-entrega-por-bairro.html

- **Média de mercado do motoboy terceirizado em 2026:** R$ 1,50 a
  R$ 2,30 por km rodado, com taxa mínima de saída de R$ 8 a R$ 10
  para raios curtos (até 3–5 km). Valores variam por região (interior
  mais barato que capital), combustível e chuva/demanda.
  - Fonte: https://controlenamao.com.br/blog/quanto-custa-um-motoboy-terceirizado-para-delivery/
  - Fonte: https://www.impulsiodigital.com/blog/quanto-cobrar-por-entrega-de-motoboy
    (mesma lógica: custo por km + taxa mínima; arredondar para cima.)

- **Regra comum:** o valor da tabela é média/estimativa; o valor
  exato é confirmado na contratação. É exatamente o desenho do §2.

## 2. Método recomendado (proposta)

Duas peças, como o usuário confirmou: **a conferência ao vivo, na
hora, é a confirmação; a tabela de médias é a base da cotação.**

### 2.1 Peça A — tabela de médias (base da cotação)

Origem: Avenida Pedro Gonçalves Norões, 280, Grangeiro, Crato (§0).
Distâncias já medidas (§1.2). Valores em R$ — **a preencher** com os
valores reais do app; nenhum preço foi inventado aqui.

| Destino | Distância (medida) | Média Uber/99 (a preencher) | Como foi medido |
|---|---|---|---|
| Crato — Grangeiro (mesmo bairro) | a medir | R$ [ ] | OSRM, origem → endereço do bairro |
| Crato — Centro | 4,9 km | R$ [ ] | OSRM, origem → Centro |
| Crato — [outros bairros com mais pedidos] | a medir | R$ [ ] | OSRM, origem → bairro |
| Juazeiro do Norte — Centro | 17,0 km | R$ [ ] | OSRM, origem → centro |
| Juazeiro do Norte — [bairro] | a medir | R$ [ ] | OSRM, origem → bairro |
| Barbalha — Centro | 25,5 km | R$ [ ] | OSRM, origem → centro |
| Barbalha — [bairro] | a medir | R$ [ ] | OSRM, origem → bairro |
| Qualquer outro endereço | OSRM na hora | R$/km × distância (§2.3) | OSRM, origem → endereço |

- **Como preencher (medição única, ~15 minutos):** para cada
  destino, abrir o app da Uber ou da 99, colocar origem (§0) e
  destino, anotar o valor mostrado — **sem confirmar a corrida**.
  Repetir em 2–3 dias/horários diferentes se quiser uma média estável.
  O usuário diz que, na região, os preços quase não variam ("quase o
  mesmo preço há toda a vida") — por isso a média serve para cotar.
- **Revisão:** re-checar a tabela quando o combustível ou as tarifas
  dos apps subirem de forma relevante. Um valor parado há anos vai
  comendo o ganho aos poucos (regra do mercado, §1.3).

### 2.2 Peça B — conferência ao vivo, na hora (confirmação)

Quando o comprador informa o endereço, quem contrata (o usuário)
abre o app da Uber ou da 99 com origem (§0) e destino (endereço do
comprador) e lê o valor **antes de confirmar**. Esse valor é o que
vale para fechar. Se for diferente da média da tabela, o comprador
sabe o valor confirmado antes de fechar — nunca depois.

- A média da tabela serve para **cotar** ("fica em torno de R$ X").
- O valor do app serve para **fechar** ("confirmado: R$ Y").
- Preço dinâmico: os dois apps variam o preço com demanda e horário
  (pico/chuva). A média vale para horários normais; em pico, o valor
  do app pode ser maior — é por isso que a conferência existe.

### 2.3 Fórmula por km (fallback, só se o usuário aprovar)

Para endereço fora da tabela: **valor ≈ maior entre (taxa mínima)
e (distância × R$/km)**.

- Taxa mínima e R$/km: **a decidir pelo usuário**, de preferência
  derivados das médias medidas — por exemplo, R$/km = média ÷
  distância das rotas já medidas (§2.1). Referência de mercado para
  motoboy: R$ 1,50–2,30/km, mínima de R$ 8–10 (§1.3) — referência,
  não número da TuttiBom.
- Sem decisão do usuário sobre a fórmula, endereço fora da tabela
  não tem cotação automática: o agente diz que o valor depende do
  endereço e será confirmado na contratação (§3, item 5).

## 3. Regra do agente para cotar a entrega (proposta para o prompt)

1. **Pedir o endereço completo:** rua, número, bairro e cidade.
   Sem o endereço, não há valor — só a explicação de que depende
   dele.
2. **Consultar a tabela (§2.1)** e cotar a média como **estimativa**:
   "a entrega fica em torno de R$ X". Nunca como preço fechado.
3. **Nunca dar valor fixo de entrega.** Nunca dizer que a entrega
   está incluída sem conferir.
4. **Antes de fechar, o valor exato é confirmado no app** (Peça B,
   §2.2). Se for diferente da média, o comprador sabe o valor
   confirmado antes de fechar.
5. **Deixar claro que é estimativa.** O comprador tem que estar
   ciente: o valor cotado é a média do que já enviamos e pode
   ter algumas variações de preço, para mais ou para menos. O
   valor exato só existe na confirmação no app, antes de fechar.
6. **Endereço fora da tabela:** dizer que o valor depende do
   endereço e será confirmado na contratação — ou calcular pela
   fórmula por km, se o usuário a tiver aprovado (§2.3).
7. **Retirada no Crato:** sem taxa de entrega (o comprador busca no
   endereço do §0, em dia e horário combinados).
8. **Fora da área (Correios):** é outro caminho, com intervenção
   humana (ver docs/prazos.md §3 regra 9) — não é cotação de
   Uber/99.
9. **Quem paga o entregador — DECIDIDO 2026-11-06.** O comprador
   paga a taxa de envio. Duas formas, a combinar com o
   comprador antes de fechar: (a) ele chama o aplicativo ele
   mesmo, informando o endereço, e paga a corrida direto no
   app; (b) a TuttiBom chama o motoqueiro, mas só com a taxa
   paga **antecipadamente** pelo comprador — o vendedor não
   adianta o valor da corrida. Sem o pagamento da taxa, não há
   chamada do motorista.

### Frases-modelo (não texto fixo)

- "Qual é o seu endereço completo? Assim eu confirmo quanto fica
  a entrega."
- "Para [bairro/cidade], a entrega fica em torno de R$ X — é uma
  média. Antes de fechar eu confirmo o valor exato no aplicativo."
- "Esse endereço fica fora da minha tabela — o valor depende dele e
  eu confirmo na hora de contratar. Quer me passar o endereço
  completo?"
- "Se preferir retirar no Crato, não tem taxa de entrega."

## 4. O que só o usuário decide / fornece (não inventar)

- [ ] **Médias por destino** — a tabela do §2.1 é preenchida
  AOS POUCOS, conforme os interessados chegam (ver §5): a
  cada novo endereço, o usuário verifica o valor no app e
  o Muse atualiza a tabela. Não é preciso medir tudo de
  uma vez.
- [ ] **Fórmula por km** — usar ou não; se sim, qual R$/km e qual
  taxa mínima (§2.3).
- [ ] **Confirmar o pin da origem no app** — digitar o endereço do
  §0 na Uber/99 na primeira vez ("Avenida" vs "Rua" no mapa).
- [ ] **Bairros do Crato na tabela** — quais bairros entram (os que
  têm mais pedidos).
- [ ] **Conferência ao vivo pelo agente?** — hoje: NÃO. A
  conferência no app é feita pelo usuário na hora de contratar; o
  agente só cota a média e escala a confirmação. Se um dia o agente
  passar a fazer a conferência, é outra decisão.
- [ ] **Ritmo de revisão da tabela** — quando re-checar (ex.: quando
  o combustível ou as tarifas subirem).
- [ ] **Quem paga a entrega** — DECIDIDO 2026-11-06: o comprador
  paga a taxa do motoqueiro, separada do produto. Se a TuttiBom
  chama o motoqueiro, a taxa é paga antecipadamente pelo
  comprador (o vendedor não adianta); o comprador pode chamar
  o aplicativo ele mesmo e pagar direto no app. Aberto: a
  entrega vai no mesmo link do Mercado Pago ou é paga à parte;
  se há pedido mínimo para entrega ou para frete reduzido.

## 5. Rotina de preenchimento — DECIDIDA pelo usuário, 2026-11-06

A tabela não é preenchida de uma vez. Ela cresce com os pedidos:

1. Chega um interessado com endereço (bairro e localização).
2. O Muse chama o usuário.
3. O usuário faz o cálculo no app (origem §0 → endereço do
   comprador) e informa o valor.
4. O Muse atualiza a tabela (§2.1) com o valor medido.
5. **Realimentação após a contratação:** quando a entrega for
   contratada de verdade, o usuário atualiza a tabela com o
   valor exato que foi cobrado — ou pede ao Muse para
   atualizar, informando o valor exato. Assim a média melhora
   a cada entrega: estimativa → valor exato cobrado → tabela
   atualizada.

**Aproximação:** quando houver bastante informação, a cotação
passa a poder ser feita por aproximação, verificando o
comportamento dos preços — bairros próximos ou similares
herdam a média de bairros já medidos (mesma faixa de distância
e mesmo perfil), sem precisar medir cada endereço novo. A
aproximação só vale para cotar; o valor exato continua sendo
confirmado no app na hora de contratar.

**Liberdade da Ana para citar o aproximado — EM ABERTO (user, 2026-11-06 ~17:35):** a tabela será completada à medida que o projeto estiver em produção. A Ana NÃO cita valor de frete agora (verifica com o gestor). A liberdade de a Ana dizer o valor aproximado só será dada quando o usuário achar adequado — **revisar daqui a ~1 mês (~2026-12-06)** se a tabela já tem dados suficientes para essa implementação.

## Fontes

- 99 — "Como é calculada a estimativa de valor da corrida?":
  https://www.reclameaqui.com.br/empresa/99taxis/conteudos/como-e-calculada-a-estimativa-de-valor-da-corrida_pN4Y6cT7twd1EED4/
- "Como funciona o aplicativo do Uber 99?":
  https://vocepergunta.com/library/artigo/read/420436-como-funciona-o-aplicativo-do-uber-99
- "3 Ways to Get an Uber Fare Estimate in Advance":
  https://www.thetechedvocate.org/3-ways-to-get-an-uber-fare-estimate-in-advance/
- Uber Developers — migração da Ride Request API (resumo):
  https://copyprogramming.com/howto/uber-ride-request-using-api
- OSRM — API pública de rotas (sem chave):
  https://bytetools.bytevancer.com/public-apis/geolocation/osrm-routing-api
- Nominatim/OSRM — limites de uso (1 req/seg, User-Agent):
  https://github.com/dvcrn/openclaw-skills-marketplace/blob/HEAD/plugins/adhishthite--maps-osrm/skills/maps/SKILL.md
- OpenRouteService — planos (Standard gratuito: 2.000 direções/dia):
  https://staging.openrouteservice.org/plans/
- OpenRouteService — guia de configuração:
  https://github.com/avinashlng1080/travel-planner/blob/HEAD/OPENROUTESERVICE_SETUP.md
- Menuzia — "Como Calcular e Configurar Taxa de Entrega por Bairro":
  https://www.menuzia.com.br/blog/tutoriais/como-configurar-taxa-de-entrega-por-bairro.html
- ControleNaMão — "Motoboy terceirizado: custos para o delivery":
  https://controlenamao.com.br/blog/quanto-custa-um-motoboy-terceirizado-para-delivery/
- Impulsio Digital — "Quanto cobrar por entrega de motoboy":
  https://www.impulsiodigital.com/blog/quanto-cobrar-por-entrega-de-motoboy
- Medições ao vivo (2026-11-06): Nominatim + OSRM — origem Rua Pedro
  Gonçalves Norões, Grangeiro, Crato (lat -7,2656683, lon
  -39,4347378); destinos: Centro do Crato 4,9 km / 8 min; Juazeiro do
  Norte (centro) 17,0 km / 21 min; Barbalha (centro) 25,5 km / 31 min.
