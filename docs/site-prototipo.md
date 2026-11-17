# Site/catálogo TuttiBom — protótipo (Magic Patterns)

Data: 2026-11-16 · Branch: `social/fb-ig` · Status: protótipo, **não publicado**. Framer ainda não conectado.

## Links
- Editor Magic Patterns (precisa de login na conta do José): https://www.magicpatterns.com/c/7fm8x7puzjvafafgwpjwm2
- Preview do MP (também pede login, não serve para público): https://project-fortunate-dune-581.magicpatterns.app
- Artifact ativo: `88dac4bb-7a43-4eaf-82bb-b07ac00d2093` (CTAs no WhatsApp). O artifact anterior, `889da5ce-4ffb-4126-b5a1-056ccee5ee8d`, apontava para o Messenger.
- Prints (box do agente): `/workspace/tuttibom/site/prototipo-mobile-hero-whatsapp.png`, `prototipo-mobile-full-whatsapp.png`, `prototipo-mobile-sticky-whatsapp.png`, `prototipo-desktop-full-whatsapp.png` (renderizados localmente a partir do código do artifact, porque o preview do MP exige login). Os prints anteriores, sem o sufixo `-whatsapp`, são da versão com Messenger.

## Decisão de canal (16/11/2026, José)

O José aprovou encaminhar o site para o WhatsApp, não para o Messenger: o objetivo é chegar no WhatsApp, onde a Ana já atende pela sessão WAHA `tutibom` (org `deskcomm-local`).

- **Site e bio** → WhatsApp da TuttiBom (número comercial da sessão `tutibom`).
- **Página do Facebook e legendas** → Messenger, por enquanto (é onde quem está no Facebook responde mais fácil).
- **Um sistema por canal:** Zernio no Messenger, Ana no WhatsApp. Os dois nunca respondem a mesma conversa.

Quando o Instagram estiver ligado à Página, o botão de WhatsApp pode entrar lá também.

## Direção visual
- Conversa com a capa aprovada A3b: fundo pérola → rosa bebê, régua dourada fina sob o título, título em Fraunces com 2ª linha itálica, texto Inter.
- Paleta exata no `tailwind.config.js`: Pérola #F6EDE3, Rosa Bebê #F4C4CF, Rosa #E8A0B0, Pink #E03E8C, Azul Bebê #8EC8F0, Azul #4A90D9, Piscina #5BD0C8, Dourado #C9A227, Preto #1A1A1A, Marrom #5C3A2A.
- Mobile-first (390px), cards arredondados 18–24px, sombra suave; rodapé em Marrom.

## Seções (em ordem)
1. Header: wordmark TUTTIBOM + pílula "Chama no WhatsApp" (âncoras Fitas / Impressão 3D / Como pedir no desktop).
2. Hero: "TUTTIBOM · CRATO-CE" / "Fitas personalizadas & impressão 3D" / "Detalhes feitos para a sua ocasião, no Cariri." / botão "Chama no WhatsApp" + link "Ver o que fazemos".
3. O que fazemos: cards Fitas personalizadas (chips Nome, Logo, Datas, Frases) e Impressão 3D (chips Vasos, Decoração, Brindes), cada um com "Chama no WhatsApp" e mensagem pronta da linha.
4. Para cada ocasião: Aniversário, Chá de bebê, Casamento, Empresas (grade 2×2, tons da paleta, cada card abre o WhatsApp com a ocasião).
5. Como pedir em 3 passos: Chama no WhatsApp → A gente monta a ideia com você → Produção e entrega combinadas (pelo WhatsApp).
6. Galeria: 6 imagens em masonry + "Algumas imagens são criadas com IA."
7. CTA final (Rosa Bebê): "Vamos criar o seu?" + "Chama no WhatsApp".
8. Rodapé: "TuttiBom · Crato-CE, Cariri", link "Chama no WhatsApp", links Facebook/Instagram (placeholder), "Algumas imagens são criadas com IA.", © TuttiBom.
- Barra fixa inferior no celular "Chama no WhatsApp", aparece após rolar 360px.

## Regras de conteúdo (verificadas no código)
- Sem preços, sem medidas, prazos, materiais, números de clientes, avaliações ou depoimentos.
- Todos os CTAs do site (hero, pílula do header, barra fixa, cards de produto, cards de ocasião, "Como pedir", CTA final e rodapé) apontam para `https://wa.me/<número da sessão tutibom>?text=<mensagem url-encoded>` (função `whatsappUrl` e constante `WHATSAPP_NUMBER` em `data/site.ts`). Mensagens prontas, sem preço, por seção — por exemplo "Oi! Vi no site da TuttiBom." no hero e "Oi! Vi no site: fitas personalizadas" no card de fitas. Texto do botão: "Chama no WhatsApp".
- Redes sociais → `#PLACEHOLDER`.
- O número no `wa.me` é o comercial público da loja (sessão WAHA `tutibom`, org `deskcomm-local`, conferido em 16/11/2026 por GET em `/api/sessions/tutibom/me` e na tabela `channel_sessions`). Não é dado pessoal de cliente.
- Aviso de IA em dois pontos (galeria e rodapé).

## Imagens
- Todas geradas pelo próprio Magic Patterns (CDN `cdn.magicpatterns.com/patterns/generated-images/...`): hero, 2 cards de produto, 6 da galeria.
- Atenção: a escrita dourada nas fitas geradas é ilegível/inventada (não diz "TuttiBom"); a fita do hero saiu lisa. Servem como placeholder de layout, não como prova de produto.

## Referências Mobbin (só referência)
- Replit — landing "ASCoffee" (hero artesanal split, serif + CTA escuro): https://mobbin.com/screens/95903548-c8f9-4eb0-90bc-0efb85f38ebe
- Variant — "ASMOB" (padaria em tons rosa, cards arredondados): https://mobbin.com/screens/f64c026e-cadf-4f4d-a6c1-5bf4286c462c
- Canva Print Shop — "How it works" em 3 passos para produto impresso: https://mobbin.com/screens/86ec3ab9-7b80-423d-ba57-1525c07b63db

## Pendências
- José revisar o protótipo no editor e aprovar copy/seções.
- Trocar o hero e os cards pela capa A3b / fotos reais autorizadas (fita com "TuttiBom" legível) antes de publicar.
- Links reais de Facebook/Instagram (o WhatsApp do site já usa o número da sessão `tutibom`).
- Botão da Página do Facebook e legendas continuam no Messenger até outra decisão.
- Passar os textos públicos no Pangram quando `PANGRAM_API_KEY` existir.
- Recriar no Framer e publicar (José aprova); só então o link entra na bio e no botão da Página.
- Decidir domínio (subdomínio Framer ou próprio).
