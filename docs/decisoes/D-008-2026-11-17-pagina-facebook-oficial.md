# D-008 — 2026-11-17 — Página oficial do Facebook da loja

**Data:** 2026-11-17 ~10:21 (America/Fortaleza)
**Decisor:** usuário
**Status:** decidido; conferência com o Zernio pendente

## Decisão

1. A Página de trabalho da loja é `https://www.facebook.com/profile.php?id=100089750066330`, da mesma conta do usuário, renomeada pelo usuário para **TuttiBom** (com dois "t").
2. Capa (A3b), bio, categoria, botão, posts, Marketplace e o layout do site miram nessa Página.
3. Uma Página só para a loja inteira: fitas e 3D juntos, separados por álbuns, destaques e coleções. Sem páginas separadas por linha de produto.
4. O perfil pessoal "TuttiBom Novidade" segue como vitrine e divulga a Página; o Messenger de perfil pessoal não conecta no Zernio.
5. Começar com poucos seguidores é aceito: a publicação começa agora.

## Pendente

- Confirmar que o id `100089750066330` é a Página conectada ao Zernio (a que recebeu o "ola" de teste); se não for, reconectar no Zernio, decisão do usuário.
- Aplicar capa e bio na janela do `profile-fb` combinada com o dono do fb_agent.

## Nota de integração (2026-11-17, merge com main)

- Renumerada de D-006 para D-008: na main, D-005 é a renomeação da Página e D-006 é a Ana 24/7.
- A D-005 da main registra a Página ligada ao Zernio/Deskcomm como **id 143473822920252**. Aqui o usuário passou `profile.php?id=100089750066330`. Na Página no formato novo do Facebook, o id do perfil da Página (`profile.php?id=`) pode ser diferente do page id da Graph/Zernio; **conferir se é a mesma Página** antes de aplicar capa/foto. O script `scripts/fb_trocar_capa.py` ainda aponta para `tuttibom10` (perfil pessoal) e precisa mirar a Página antes de rodar.
