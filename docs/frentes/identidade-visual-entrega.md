# Frente 1 — identidade visual — entrega

Data da sessão: 2026-11-17, início 16:22 (America/Fortaleza).
Workspace: `/home/pc/Workspace/tuttibom-ops-identidade`
Branch: `frente/identidade-visual`
Commit apontado pelo ref da branch: `cdd94975bf8f9048e4ec50bec0800615aa77ba6b`
Base informada no brief: `main` `b8a034a` (a relação não foi refeita com `git log`; o shell não rodou).

Nada foi publicado, enviado, agendado ou colado na Página. Nenhum commit.

## Bloqueio do ambiente

O shell desta sessão foi recusado em toda tentativa (`Rejected`, sem saída). Por isso não rodou:

- `scripts/fb_trocar_capa.py --dry-run`
- `mcporter` (Pangram e Framer)
- lista de processos `fb_agent`
- consulta ao vivo do nome da Página (Zernio, Deskcomm ou Facebook)

Não abri login novo em ferramenta nenhuma. A autenticação que vale continua a do mcporter, já feita no PC.

## 1. Capa

`scripts/fb_trocar_capa.py` deixou de mirar `facebook.com/tuttibom10` (perfil pessoal “TuttiBom Novidade”).

Agora:

- URL: `https://www.facebook.com/profile.php?id=100089750066330`
- Mesma Página do id Zernio `143473822920252`
- Nome aceito: `TuttiBom` (depois da aprovação) ou `TutiBom` (enquanto o Facebook analisa)
- Se aparecer “TuttiBom Novidade”, aborta
- Imagem: `criativos/capa-2026-11-16/capa-A3b.png` (não regenerada)

O script só abre o navegador sem `--dry-run`. Nesta sessão ele não foi executado.

### Lock

- `/home/pc/Workspace/tuttibom-ops/prototype-vision/profile-fb/.parentlock` existe. O arquivo está vazio; o travamento do Firefox é por `flock`, e isso não deu para consultar.
- O symlink `profile-fb/lock` não apareceu na leitura.
- Processos `fb_agent`: não listados.

O brief e o `docs/ESTADO.md` dizem que o `fb_agent.py` está no perfil. Tratei o perfil como ocupado e parei. Não matei processo e não apaguei lock.

### Comando na janela livre

```bash
cd /home/pc/Workspace/tuttibom-ops-identidade
python3 scripts/fb_trocar_capa.py --dry-run
```

Saída esperada: `0` se o perfil estiver livre (só imprime o plano). `2` se o lock, o `fb_agent` ou a imagem bloquearem. Nos dois casos o navegador não abre.

Aplicar, só depois desse dry-run em `0` e com o `fb_agent` parado:

```bash
python3 scripts/fb_trocar_capa.py
```

A arte A3b já está aprovada. Mesmo assim a aplicação é ação ao vivo: fica para a janela combinada com o dono do `profile-fb`.

## 2. Foto de perfil

A arte não está no git. Está no Magic Patterns:

- https://www.magicpatterns.com/c/oa6jym3ubfzkmwqd4lrydc
- artefato com prefixo `b4f96dc8`
- monograma TB, “vamos deixar assim” — não regenerar

O conector do Cursor para o Magic Patterns pediu autenticação. Não criei outro token. O PNG não foi baixado.

Pronto no disco:

- `scripts/fb_trocar_foto.py` (mesma Página, mesmas travas, não rodado)
- `criativos/perfil-2026-11-17/PASSOS.md`

Quando o PNG estiver em `criativos/perfil-2026-11-17/monograma-tb.png` e o perfil estiver livre:

```bash
python3 scripts/fb_trocar_foto.py --dry-run
```

Sem o PNG, o dry-run sai `2` e não abre o navegador. Não aplicar nesta frente.

## 3. Bio

Rascunho em `criativos/bio-2026-11-17.md`.

Intro (99/100), sem preço:

> Fita personalizada e impressão 3D no Cariri. Chama no WhatsApp. Algumas imagens são criadas com IA.

Sobre com o WhatsApp comercial já público no repo (`https://wa.me/<NUMERO_LOJA>`) e o site só como campo, sem URL inventada. Sem rua, sem horário, sem preço.

Pangram: pendente. Não é falta de chave (`PANGRAM_API_KEY` não faz parte do acesso; o OAuth do mcporter é o caminho). O `mcporter` não foi chamado porque o shell não rodou.

Quando o shell voltar, o primeiro comando é só listar, sem publicar:

```bash
scripts/com-ferramentas.sh mcporter list pangram
```

Aí sim chamar a tool de detecção que essa lista mostrar, com o texto do rascunho. Se responder sem acesso, o bloqueio fica registrado e o texto continua valendo como rascunho.

Não colei a bio na Página.

## 4. Site no Framer

Não há `FRAMER_PROJECT_URL` no repo (`.env.example` deixa a variável comentada; `docs/acesso-ferramentas.md` marca “A DEFINIR”). Nenhuma URL `framer.com` de projeto da TuttiBom.

Fonte do site: Magic Patterns https://www.magicpatterns.com/c/7fm8x7puzjvafafgwpjwm2 , artefato atual `43a5f6f4` (home, `/3d`, `/fitas`, WhatsApp, sem preço). O `docs/site-prototipo.md` ainda cita o artefato anterior `f6c5bf01`.

O Framer não apareceu entre os conectores desta sessão do Cursor. Não listei os projetos e não publiquei.

Comando exato para achar o projeto (não publica):

```bash
cd /home/pc/Workspace/tuttibom-ops-identidade
scripts/com-ferramentas.sh mcporter list framer
```

O comando de publicar fica sem nome de tool até essa lista sair. Publicar continua sendo decisão do usuário, com a URL do projeto preenchida fora do git. Não gravar o valor no repositório.

## 5. Renomeação

Verificação ao vivo: não feita (shell e leitura da Página recusados).

Último resultado que o repo já tinha, e que esta frente não conseguiu atualizar:

- Solicitação enviada 2026-11-17 ~10:16 (TutiBom → TuttiBom).
- Na mesma hora o nome ainda era “TutiBom” no Facebook, no Zernio (página `143473822920252`) e no Deskcomm (`facebook · TutiBom`).
- O Facebook tem até 3 dias. Nesta sessão, no fim da tarde de 2026-11-17, não há leitura nova.

Dono da próxima leitura: quem puder consultar o Zernio ou o Deskcomm em só leitura, ou a Página, sem usar o `profile-fb` enquanto o `fb_agent` estiver nele.

## 6. Posts F1-02

A definição não está em `docs/plano-social-facebook-instagram.md`. Está em `criativos/f1-lote-02.md` (8 posts, P1–P8, só prompt).

Refeito em `criativos/f1-02-natal.md`: 8 legendas em rascunho, cada uma apontando para um JPEG que já existe em `criativos/anuncios/2026-11-natal/`. Nada publicado. CTA no Messenger. Sem preço. Aviso de IA em todas. Pangram pendente.

## 7. Instagram — o que falta

Não tentei login nem senha.

O que o repo registra (D8, `docs/plano-social-facebook-instagram.md`, fechada em 2026-11-16 ~09:10):

- A conta da loja no Instagram não é profissional e não está ligada à Página.
- O @ não está escrito em nenhum doc desta worktree. Não há e-mail de recuperação, nem mensagem de erro de login, nem sessão Instagram no Zernio.
- O Zernio tem a Página do Facebook (`TutiBom`, id `143473822920252`). O Instagram seria a segunda vaga do plano grátis, e não está conectado.
- O Deskcomm, no estado escrito em 2026-11-17, tem o canal Facebook/Zernio. Não há canal Instagram WORKING descrito.

Não existe, no material lido, um erro do tipo “senha incorreta” ou “conta desativada” para diagnosticar. O buraco é anterior: a conta não está identificada nem ligada.

O que só o usuário faz:

1. Dizer qual @ é o da loja (ou criar um, se ainda não houver).
2. Se não entrar, recuperar pelo fluxo do próprio Instagram, com o e-mail ou o telefone daquela conta. A senha fica com ele.
3. Converter para profissional (Business ou Creator).
4. Ligar à Página `100089750066330`.
5. Liberar o acesso às mensagens.
6. Confirmar por escrito. Só então o Zernio pode receber o Instagram. Esta frente não conecta.

## 8. O que ficou para aprovação

| Peça | Arquivo | Pode ir ao ar? |
|---|---|---|
| Capa A3b, script apontado | `scripts/fb_trocar_capa.py` | Não. Falta o dry-run executar e a janela do `profile-fb`. |
| Monograma TB | `scripts/fb_trocar_foto.py`, `criativos/perfil-2026-11-17/PASSOS.md` | Não. Falta o PNG e a janela. |
| Bio | `criativos/bio-2026-11-17.md` | Não. Falta Pangram e o ok ao texto. |
| Posts | `criativos/f1-02-natal.md` | Não. Falta Pangram e o ok de cada legenda. |
| Site | artefato `43a5f6f4` | Não. Sem projeto Framer e sem publicar. |

## Dono de cada bloqueio

| Bloqueio | Dono |
|---|---|
| Rodar o `--dry-run` (shell recusado aqui) | agente na próxima janela, com shell |
| Parar o `fb_agent` e liberar o `profile-fb` | dono do `fb_agent` |
| Exportar o monograma sem regenerar | agente com o mcporter do Magic Patterns |
| Pangram nos textos | agente com `scripts/com-ferramentas.sh mcporter` |
| URL do projeto Framer e o publicar | usuário, depois que a lista do Framer existir |
| Nome da Página ao vivo | agente em só leitura, fora do `profile-fb` ocupado |
| Instagram (@, senha, conta profissional) | usuário |
