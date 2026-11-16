# Experimento 0001 — Pesquisa no Marketplace do Cariri via ADB

- Data: 2026-10-30, 02:37–02:42 (-03:00)
- Aparelho: S10 Lite, via SSH pelo túnel Tailscale + ADB, bateria 91%,
  sem carregamento (por isso sem `stayon`).
- Ritmo: um passo por vez, com espera e nova captura de tela a cada
  passo; sem curtir, comentar, seguir, mandar mensagem ou abrir
  anúncio individual. Só leitura de resultados de busca.
- Ponto de partida: tela em Dozing → acordada com `keyevent 224`,
  vigília confirmada como Awake antes de tocar.

## Verificação prévia (remota, via SSH)

- Impressão digital do host lida no próprio aparelho, no Termux,
  bateu exatamente com a registrada na conexão:
  `SHA256:A3Mj9uWEV6SjUr52GivW2hQRbrBn2yIlOX3mZLlQ4Hg`.
  Limite honesto: essa checagem foi pelo mesmo canal SSH, não
  fora da banda — confirma consistência, não substitui uma
  confirmação presencial futura, se o usuário quiser.
- Facebook já estava logado; ao abrir, apareceu um aviso para
  confirmar email, fechado com o X (sem confirmar, sem adicionar
  email, sem mudar conta).
- `uiautomator dump` falhou com "null root node" no Facebook —
  observação foi só por captura de tela e app em foco, não por
  árvore de UI. Limite registrado para as próximas rotinas.
- Armadilha de digitação confirmada: `input text` com `%20` digita
  os caracteres literais. Espaço foi feito com `keyevent 62` entre
  palavras. Acentos foram evitados nas buscas.

## Busca 1 — "fita de cetim" (Marketplace, filtro Juazeiro do Norte)

- Resultado: a primeira tela foi direto para "Outros resultados",
  com aviso de que alguns classificados podem estar fora do raio.
- Exemplos visíveis na primeira tela: rolo de fita de cetim a R$8
  (Fortaleza, 400 km) e kit de lembrancinhas a R$120 (João Pessoa,
  490 km), além de kit escova + xuxinha de cetim a R$9 (Fortaleza,
  390 km).
- Leitura: dentro do raio do filtro, não apareceu oferta local de
  fita de cetim na primeira tela — o que apareceu era de fora do
  Cariri. Hipótese a testar, não conclusão: há espaço para oferta
  local de fita personalizada, porque quem busca no Cariri hoje
  encontra fornecedor a 400 km.

## Busca 2 — "impressao 3d" (mesmo filtro, Juazeiro do Norte)

- Resultado: oferta local abundante, a 1–2 km, no centro de
  Juazeiro do Norte.
- Exemplos visíveis na primeira tela:
  - "Impressão 3d" — marcado como Gratuito — Juazeiro, 1 km.
  - "IMPRESSÕES 3D" — R$6 — chaveiros de Nossa Senhora Aparecida
    em promoção, com estoque anunciado — Juazeiro, 2 km.
  - "Chaveiros 3D" — marcado como Gratuito — Juazeiro, 1 km.
  - "Chaveiro personalizado" — R$8 — com nome — Juazeiro, 1 km.
- Sugestões de busca que o próprio Facebook ofereceu: "impressão 3d
  personalizada", "impressão 3d encomenda" e "impressão 3d resina".
- Leitura: chaveiro personalizado já é o produto de entrada no
  Cariri, com preço de referência R$6–R$8 e tema religioso forte
  (Nossa Senhora Aparecida, coerente com o turismo religioso de
  Juazeiro). "Gratuito" aqui provavelmente significa preço a
  combinar, não produto grátis — não assumir gratuidade.
  Diferenciar vai precisar de mais que preço: tema, acabamento,
  foto em uso e kit com fita personalizada.

## O que NÃO foi feito

- Nenhum anúncio aberto individualmente, nenhuma mensagem, nenhum
  like, comentário, follow ou salvamento.
- Nenhuma publicação, rascunho ou alteração de conta.
- Ao final, a sessão ficou na tela de resultados da busca de fita,
  por voltar da busca de 3D — ponto seguro, sem trabalho não salvo.
  A tela apaga sozinha em 5 minutos (timeout atual).

## Próximos testes sugeridos (não executados)

- Busca "laco personalizado" e "lembrancinha personalizada" no
  mesmo filtro, para completar o mapa da fita.
- Abrir um anúncio local de chaveiro 3D (só leitura) para anotar
  foto, descrição e tempo de resposta — só com aprovação, porque
  abrir anúncio pode contar como visualização/engajamento.
- Comparar Crato e Barbalha mudando o filtro de localidade, em
  sessões separadas.
