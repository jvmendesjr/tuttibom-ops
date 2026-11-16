# Site/catálogo TuttiBom — protótipo (Magic Patterns)

Data: 2026-11-16 · Branch: `social/fb-ig` · Status: protótipo, **não publicado**. Framer ainda não conectado.

## Links
- Editor Magic Patterns (precisa de login na conta do José): https://www.magicpatterns.com/c/7fm8x7puzjvafafgwpjwm2
- Preview do MP (também pede login, não serve para público): https://project-fortunate-dune-581.magicpatterns.app
- Artifact ativo: `889da5ce-4ffb-4126-b5a1-056ccee5ee8d`
- Prints (box do agente): `/workspace/tuttibom/site/prototipo-mobile-hero.png`, `prototipo-mobile-full.png`, `prototipo-mobile-sticky.png`, `prototipo-desktop-full.png` (renderizados localmente a partir do código do artifact, porque o preview do MP exige login).

## Direção visual
- Conversa com a capa aprovada A3b: fundo pérola → rosa bebê, régua dourada fina sob o título, título em Fraunces com 2ª linha itálica, texto Inter.
- Paleta exata no `tailwind.config.js`: Pérola #F6EDE3, Rosa Bebê #F4C4CF, Rosa #E8A0B0, Pink #E03E8C, Azul Bebê #8EC8F0, Azul #4A90D9, Piscina #5BD0C8, Dourado #C9A227, Preto #1A1A1A, Marrom #5C3A2A.
- Mobile-first (390px), cards arredondados 18–24px, sombra suave; rodapé em Marrom.

## Seções (em ordem)
1. Header: wordmark TUTTIBOM + pílula "Messenger" (âncoras Fitas / Impressão 3D / Como pedir no desktop).
2. Hero: "TUTTIBOM · CRATO-CE" / "Fitas personalizadas & impressão 3D" / "Detalhes feitos para a sua ocasião, no Cariri." / botão "Chama no Messenger" + link "Ver o que fazemos".
3. O que fazemos: cards Fitas personalizadas (chips Nome, Logo, Datas, Frases) e Impressão 3D (chips Vasos, Decoração, Brindes), cada um com "Peça pelo Messenger".
4. Para cada ocasião: Aniversário, Chá de bebê, Casamento, Empresas (grade 2×2, tons da paleta, cada card abre o Messenger).
5. Como pedir em 3 passos: Chama no Messenger → A gente monta a ideia com você → Produção e entrega combinadas.
6. Galeria: 6 imagens em masonry + "Algumas imagens são criadas com IA."
7. CTA final (Rosa Bebê): "Vamos criar o seu?" + "Chama no Messenger".
8. Rodapé: "TuttiBom · Crato-CE, Cariri", links Facebook/Instagram (placeholder), "Algumas imagens são criadas com IA.", © TuttiBom.
- Barra fixa inferior no celular "Chama no Messenger", aparece após rolar 360px.

## Regras de conteúdo (verificadas no código)
- Sem preços, sem medidas, prazos, materiais, números de clientes, avaliações ou depoimentos.
- Todos os CTAs → `https://m.me/PLACEHOLDER-PAGINA-TUTTIBOM` (constante `MESSENGER_URL` em `data/site.ts`, marcada `// PLACEHOLDER` e `data-placeholder="messenger-link"`). Redes sociais → `#PLACEHOLDER`.
- Nenhum telefone, e-mail ou dado pessoal.
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
- Link real do Messenger (m.me/<usuário da Página>) e links reais de Facebook/Instagram.
- Passar os textos públicos no Pangram quando `PANGRAM_API_KEY` existir.
- Recriar no Framer e publicar (José aprova); só então o link entra na bio e no botão da Página.
- Decidir domínio (subdomínio Framer ou próprio).
