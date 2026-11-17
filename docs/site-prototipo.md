# Site/catálogo TuttiBom — protótipo (Magic Patterns)

Data: 2026-11-16 (America/Sao_Paulo, UTC-3) · Branch: `social/fb-ig` · Status: protótipo, **não publicado**. Framer ainda não conectado.

## Links
- Editor Magic Patterns (precisa de login na conta do José): https://www.magicpatterns.com/c/7fm8x7puzjvafafgwpjwm2
- Preview do MP (também pede login, não serve para público): https://project-fortunate-dune-581.magicpatterns.app
- Artifact desta versão (catálogo `/3d` e identidade de Natal): `43a5f6f4-4d35-4cc0-990b-9da9329d3da0` (confirmado 2026-11-17 via API do Magic Patterns — é o artefato do editor `7fm8x7puzjvafafgwpjwm2`). O anterior, `f6c5bf01-36ad-43d7-b709-d9b30ba9bcfa`, também já tinha `/3d` e Natal. Antes dele, `88dac4bb-7a43-4eaf-82bb-b07ac00d2093`, ainda com CTAs no WhatsApp mas sem a página `/3d` nem a temporada de Natal. O ainda anterior, `889da5ce-4ffb-4126-b5a1-056ccee5ee8d`, apontava para o Messenger.
- Prints (box do agente, sufixo `-natal`): `/workspace/tuttibom/site/prototipo-mobile-home-natal.png`, `prototipo-mobile-3d-natal.png`, `prototipo-desktop-home-natal.png`, e as versões `*-full-natal.png` de home e `/3d` (mobile e desktop), mais `prototipo-mobile-sticky-natal.png`. Renderizados localmente a partir do código do artifact, porque o preview do MP exige login. Os prints com sufixo `-whatsapp` são da versão anterior, só com WhatsApp e sem `/3d`.
- Anúncios (imagens IA, 1080×1080 e 1080×1350): `criativos/anuncios/2026-11-natal/` no worktree, com `manifest.md`.

## Decisão de canal (16/11/2026, José)

O José aprovou encaminhar o site para o WhatsApp, não para o Messenger: o objetivo é chegar no WhatsApp, onde a Ana já atende pela sessão WAHA `tutibom` (org `deskcomm-local`).

- **Site e bio** → WhatsApp da TuttiBom (número comercial da sessão `tutibom`, conferido; nos relatos só os quatro últimos dígitos: 2939).
- **Página do Facebook e legendas** → Messenger, por enquanto (é onde quem está no Facebook responde mais fácil).
- **Um sistema por canal:** Zernio no Messenger, Ana no WhatsApp. Os dois nunca respondem a mesma conversa.

Quando o Instagram estiver ligado à Página, o botão de WhatsApp pode entrar lá também.

## Direção visual (temporada de Natal, até o Natal)

- Continua a conversa com a capa aprovada A3b: fundo pérola, régua dourada fina, título em Fraunces com 2ª linha itálica, texto Inter, wordmark TUTTIBOM.
- Paleta no `tailwind.config.js`: Pérola #F6EDE3, Rosa Bebê #F4C4CF, Rosa #E8A0B0, Pink #E03E8C, Azul Bebê #8EC8F0, Azul #4A90D9, Piscina #5BD0C8, Dourado #C9A227 (mantido), Preto #1A1A1A, Marrom #5C3A2A, e nesta temporada **Pinho #2C4A3E** e **Musgo #4A5D43**.
- Detalhes sazonais discretos (estrela dourada no header, faixa “TEMPORADA DE NATAL”), não visual de carnaval ou kit de Natal genérico.
- Mobile-first (390px), cards arredondados 18–24px, sombra suave; rodapé passou de Marrom para Pinho, com a linha “Temporada de Natal”.

## Arquitetura
- Home (`/`) com 4–6 destaques de impressão 3D e o botão **Ver catálogo 3D**.
- Página própria `/3d` (`Catalog3dPage`) e página `/fitas` (`CatalogFitasPage`), no mesmo protótipo (react-router-dom 6.30.2).
- O chaveiro NFC **não entra** no site: José confirmou em 16/11/2026 que não tem tags NFC. No doc do catálogo o item ficou marcado **fora: sem NFC**.

## Seções da home (em ordem)
1. Header: estrela dourada + wordmark TUTTIBOM + pílula "Chama no WhatsApp". Links: Fitas `/fitas`, Impressão 3D `/3d`, Como pedir `/#como-pedir`.
2. Hero: "TUTTIBOM · CRATO-CE · TEMPORADA DE NATAL" / "Fitas personalizadas & impressão 3D" / "Detalhes feitos para a sua ocasião — também no Natal, no Cariri." / botão "Chama no WhatsApp" + link "Ver o que fazemos" para `#destaques-3d`. Imagem nova de natureza-morta de Natal (IA).
3. O que fazemos: cards Fitas personalizadas e Impressão 3D; o card 3D leva a `/3d` ("Ver catálogo 3D"); o de fitas leva a `/fitas` ("Ver fitas") e tem um rodapé discreto do bloco padrão de larguras (texto só, sem a foto, para não poluir).
4. Destaques 3D (6 cards): bola de Natal com nome, porta-vela árvore, lanterna natalina, topo de bolo, capelo de formatura e caixinha, cada um com "Chama no WhatsApp" e mensagem pronta da peça; botão "Ver catálogo 3D" no fim do bloco.
5. Para cada ocasião (grade 2×3): Aniversário, Chá de bebê, Casamento, Empresas, Formatura, Natal. Cada card abre o WhatsApp com a ocasião.
6. Como pedir em 3 passos: Chama no WhatsApp → A gente monta a ideia com você → Produção e entrega combinadas (pelo WhatsApp).
7. Galeria: imagens IA novas + "Algumas imagens são criadas com IA."
8. CTA final (Rosa Bebê): "Vamos criar o seu?" + "Chama no WhatsApp".
9. Rodapé em Pinho: "TuttiBom · Crato-CE, Cariri", "Temporada de Natal", link "Catálogo 3D" (`/3d`), "Chama no WhatsApp", Facebook/Instagram (placeholder), aviso de IA, © TuttiBom.
- Barra fixa inferior no celular "Chama no WhatsApp", aparece após rolar.

## Página `/3d`
- Abre com "Catálogo de impressão 3D": peças sob demanda, personalizadas com o nome ou a ocasião; nesta temporada, Natal e formatura vão à frente; velas de LED tealight (o José tem) entram nas peças que as usam. Sem preços.
- Seções: Natal, Formatura, Vela de LED, Aniversário, Casamento, Decoração.
- 18 cards com imagem IA, título, linha e "Chama no WhatsApp" (mensagem pronta da peça, sem preço). Sem chaveiro NFC.
- Itens do levantamento ainda sem imagem exclusiva ficam só em `docs/pesquisa-catalogo-3d.md`, não como card.
- CTA final de WhatsApp no rodapé da página.

## Página `/fitas`

- Catálogo de fitas personalizadas, tema de Natal (árvore, presentes, peça 3D, embalagem). Sem preço, sem comprimento de rolo, sem outras larguras além das listadas.
- A **única referência de tamanho** é o bloco padrão `FitasLargurasPadrao` na parte inferior da página, antes do rodapé: a foto medida `fitas-escala-15-22` (commit `ff8a23b`) e o texto curto «Larguras disponíveis: 15 mm e 22 mm» e «moeda de R$ 1 = 27 mm».
- As larguras vivem em `FITAS_LARGURAS` em `data/site.ts`; tamanho futuro entra só adicionando um item. Não há faixas CSS de proporção nem outra imagem de escala no site.
- Prints do bloco: `/workspace/tuttibom/site/prototipo-mobile-fitas-padrao.png` e `prototipo-desktop-fitas-padrao.png`.

## Regras de conteúdo (verificadas no código)
- Sem preços, prazos, materiais, números de clientes, avaliações ou depoimentos. As únicas medidas no site são as larguras de fita (15 mm e 22 mm) e a referência da moeda de R$ 1 (27 mm), só no bloco padrão de `/fitas` (e no rodapé discreto do card de fitas da home).
- Todos os CTAs do site (hero, pílula do header, barra fixa, cards de produto, cards de ocasião, "Como pedir", CTA final e rodapé) apontam para `https://wa.me/<número da sessão tutibom>?text=<mensagem url-encoded>` (função `whatsappUrl` e constante `WHATSAPP_NUMBER` em `data/site.ts`). Mensagens prontas, sem preço, por seção ou por peça. Texto do botão: "Chama no WhatsApp".
- Redes sociais → `#PLACEHOLDER`.
- O número no `wa.me` é o comercial público da loja (sessão WAHA `tutibom`, org `deskcomm-local`, conferido em 16/11/2026 por GET em `/api/sessions/tutibom/me` e na tabela `channel_sessions`). Não é dado pessoal de cliente.
- Aviso de IA em dois pontos (galeria e rodapé).

## Imagens
- Quase todas geradas por IA no Magic Patterns (`generate_image`, OS `1bQLQVdU8LfJL1sqGFexPU`, conversa `tuttibom natal`), CDN `cdn.magicpatterns.com/patterns/generated-images/...`. A foto de escala `fitas-escala-15-22` foi recomposta de forma determinística (PIL) sobre a foto de origem e verificada por medição (commit `ff8a23b`); é a única referência de tamanho. Nenhuma foto real da loja. Fotos de MakerWorld serviram só como referência de forma, não foram copiadas; sem logos ou marcas d'água de terceiros.
- 20 imagens no total (hero, fitas, e 18 peças / cenas). Arquivo para anúncio em `criativos/anuncios/2026-11-natal/` (1080×1080 e 1080×1350) com `manifest.md`.
- Observações de geração (não impedem o uso): o potinho capelo saiu com suculenta; o topo de bolo lembra bolo de casamento de dois andares, com placa em branco; a caixinha ficou mais rendada do que uma caixa dobrável simples; a placa de Natal é um pouco mais gráfica. A ferramenta de imagem do Magic Patterns não recebe pedido de texto na cena, porque o texto sai ilegível.
- Pangram: pendente (textos e imagens), quando `PANGRAM_API_KEY` existir.

## Referências Mobbin (só referência)
- Replit — landing "ASCoffee" (hero artesanal split, serif + CTA escuro): https://mobbin.com/screens/95903548-c8f9-4eb0-90bc-0efb85f38ebe
- Variant — "ASMOB" (padaria em tons rosa, cards arredondados): https://mobbin.com/screens/f64c026e-cadf-4f4d-a6c1-5bf4286c462c
- Canva Print Shop — "How it works" em 3 passos para produto impresso: https://mobbin.com/screens/86ec3ab9-7b80-423d-ba57-1525c07b63db

## Pendências
- José revisar o protótipo no editor (home + `/3d` + `/fitas`, identidade de Natal, catálogo sem NFC, bloco padrão de larguras) e aprovar copy/seções.
- Trocar, no futuro, parte das imagens por fotos reais autorizadas da peça impressa pela TuttiBom (por enquanto, só IA).
- Links reais de Facebook/Instagram (o WhatsApp do site já usa o número da sessão `tutibom`).
- Botão da Página do Facebook e legendas continuam no Messenger até outra decisão.
- Passar os textos públicos e as imagens no Pangram quando `PANGRAM_API_KEY` existir.
- Recriar no Framer e publicar (José aprova); só então o link entra na bio e no botão da Página.
- Decidir domínio (subdomínio Framer ou próprio).
- Porta-canudo / porta-diploma de formatura: sem modelo comercial no MakerWorld; só entra se for desenho próprio.
- Base de luz da luminária lua (litofania) ainda não confirmada; Combo / 19 cores da Kobra X ainda não confirmado.
