# Operação do perfil do Facebook (`profile-fb`)

## O que é cada coisa

- `prototype-vision/profile-fb/` — sessão do Firefox logada no Facebook como
  TuttiBom Novidade. É por ela que o `fb_agent` opera.
- `prototype-vision/profile-panel/` — sessão separada, só Deskcomm. Nada a ver
  com o Facebook.
- `fb_agent.py` e `panel_camofox_drive.py` são LOOPS: ficam vivos esperando
  tarefa. Vivo ≠ usando.
- **O perfil só está EM USO quando o NAVEGADOR está aberto com ele.**

## Como saber se está livre (sem depender de ninguém lembrar de avisar)

`scripts/profile-fb-status.sh` — calcula na hora, não guarda marcador:

- **LIVRE** (exit 0): nenhum navegador aberto, nenhuma trava viva. Os loops
  podem estar vivos e parados — isso não ocupa o perfil.
- **OCUPADO** (exit 1): navegador aberto ou trava viva.
- **ATENCAO** (exit 2): trava órfã — resto de sessão fechada (arquivo
  `.parentlock` ou `lock` órfão, sem navegador). Limpar com `--limpar-orfaos` e
  conferir de novo. O Firefox deixa os dois arquivos no perfil; os dois
  precisam estar ausentes (ou vivos) para o perfil estar livre.

Por que não um arquivo "status: livre/ocupado"? Um marcador apodrece: se o
agente cair, o marcador fica "ocupado" para sempre e ninguém sabe. A checagem
viva (processo + trava) não apodrece — ninguém precisa lembrar de mudar nada.

## Janela de uso direto do perfil (capa, foto, qualquer ação manual)

1. `scripts/profile-fb-status.sh` — se OCUPADO, parar o loop:
   `touch /tmp/fb-agent.stop` (Facebook) e/ou `touch /tmp/panel-camofox.stop`
   (painel). O loop fecha o navegador de forma limpa e sai sozinho.
2. Rodar o status de novo até dar LIVRE (ou ATENCAO → `--limpar-orfaos` →
   LIVRE).
3. Backup antes da janela (navegador fechado = cópia consistente):
   `cp -a prototype-vision/profile-fb "prototype-vision/profile-fb-backup-$(date +%Y%m%d-%H%M)"`.
   Manter os 2 últimos.
4. Fazer o trabalho da janela. O script da capa (`scripts/fb_trocar_capa.py`)
   continua conservador: qualquer trava = aborta. Por isso a limpeza de
   órfãos vem antes.
5. Se o loop foi parado, relançar e remover o arquivo `.stop` se ainda existir:
   `cd prototype-vision && rm -f /tmp/fb-agent.stop && nohup ./.venv/bin/python -u fb_agent.py > /tmp/fb-agent.log 2>&1 & disown`
   (painel: o mesmo com `panel_camofox_drive.py` e `/tmp/panel-camofox.stop`.)
   Sem relançar, o Facebook fica sem operador até alguém notar.

## Nunca

- `kill -9` no Firefox, nem apagar `.parentlock` com o navegador aberto — é
  assim que se perde o login.
- Dois navegadores no mesmo perfil ao mesmo tempo.
- Apagar o diretório do perfil (o backup é a única volta).

## Isolamento confirmado (2026-11-17)

- **Perfis separados:** `profile-fb` (Facebook) e `profile-panel` (Deskcomm),
  cada um com `user_data_dir` próprio no código.
- **Impressão digital FIXA por perfil**, gerada uma vez e salva em
  `fingerprint.json` dentro do perfil (`profile-fb`: 15/11 21:48;
  `profile-panel`: 16/11 09:19). O Facebook sempre vê a mesma identidade de
  navegador da loja; o painel, outra identidade, só dele.
- **Cookies separados** (só contagem, sem valores): `profile-fb` tem
  facebook.com (`c_user`, `xs`, …) e google.com; `profile-panel` tem SÓ
  `deskcomm.petemcasa.com`. Nenhum dos dois tem a sessão do outro.
- **Telas separadas:** o Facebook abre no :0 real (visível no noVNC); o painel
  roda num Xvfb virtual, sem tocar a tela :0.

## Estado verificado

- 2026-11-17 ~17:50: nenhum navegador aberto; loops `fb_agent` (1672919) e
  `panel_camofox_drive` (1926714) vivos e parados; as travas eram órfãs nos
  DOIS arquivos (`.parentlock` de 0 bytes e o link `lock` para pid morto —
  fb 1673523, painel 1927316) e foram limpas com `--limpar-orfaos` (17:52);
  backups atualizados (fb 267M, painel 95M). Status: **LIVRE**. O dry-run da
  capa, depois da limpeza, aborta só pelo loop vivo — a trava certa para a
  janela.
