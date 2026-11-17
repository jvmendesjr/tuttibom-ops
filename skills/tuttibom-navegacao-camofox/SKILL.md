# Navegação Camofox + Jev (TuttiBom)

Skill do fluxo de navegação do TuttiBom Ops: operar o Facebook e o painel
Deskcomm pelo motor Camofox, com o Jev escolhendo cada clique a partir do
print. Vale para qualquer agente que for navegar — ler antes de agir.

## Um perfil por superfície, isolado

- Um perfil persistente por superfície: `profile-fb/` (Facebook, conta
  TuttiBom Novidade) e `profile-panel/` (Deskcomm). Nunca reutilizar um perfil
  em outra superfície — o login de uma nunca vaza para a outra.
- Cada perfil tem sua impressão digital FIXA, gerada uma vez e salva em
  `fingerprint.json` dentro do perfil. É o ID próprio do navegador daquela
  superfície: o Facebook sempre vê a mesma identidade da loja.
- Perfis, cookies e telas separados (verificado 2026-11-17): `profile-fb` tem
  só facebook.com e google.com; `profile-panel`, só deskcomm.petemcasa.com.
  O Facebook abre no :0 real (visível no noVNC); o painel, num Xvfb virtual.
- Usar o motor Camofox, não o servidor camofox-browser — o servidor não clica
  por coordenada e o motor clica as coordenadas que o Jev devolve.
- Chromium headless (Playwright) é fallback quando o Camofox não está
  disponível, com o mesmo ciclo de print, locate, clique e reobservação.
- O usuário digita senhas e faz login na tela real quando a superfície precisa
  de login novo. Nunca digitar ou enviar credencial.

## O perfil só está em uso com o navegador aberto

- O loop do agente vivo, sozinho, NÃO ocupa o perfil. Só o navegador aberto
  ocupa.
- O Firefox deixa DOIS arquivos de trava no perfil: `.parentlock` e `lock`.
  Os dois precisam ser checados; uma trava órfã (link para pid morto, arquivo
  de 0 bytes) não prova uso.
- Status calculado ao vivo por `scripts/profile-fb-status.sh`
  (LIVRE/OCUPADO/ATENCAO) — nunca guardar "livre/ocupado" num arquivo
  marcador, que apodrece se o agente cair. O procedimento completo está em
  `docs/operacao-perfil-fb.md`.
- Para janela de uso direto do perfil (capa, foto, ação manual): parar o loop
  (`touch /tmp/fb-agent.stop` ou `/tmp/panel-camofox.stop`), status até LIVRE,
  backup do perfil, trabalho, relançar o loop.
- Nunca `kill -9` no Firefox, nem apagar trava com o navegador aberto — é
  assim que se perde o login. Nunca dois navegadores no mesmo perfil.
- O script da capa (`scripts/fb_trocar_capa.py`) aborta com o loop vivo — é a
  trava certa, não um bug.

## Guiar o navegador por fila de tarefas

- Uma ação por entrada (goto, locate, click, type, scroll, shot) num arquivo
  de tarefas; ler o resultado depois de cada uma antes da próxima.
- Facebook: tarefas em `/tmp/fb-agent-job.json`, resultado em
  `/tmp/fb-agent-result.json`, print em `/tmp/fb-agent-shot.png`.
- Parar com o arquivo `.stop` quando a tarefa termina ou precisa interromper,
  e deixar o navegador num estado limpo.
- Definir um teto de passos antes de começar e parar no teto, em vez de
  tentar em rajada.

## O Jev localiza cada alvo a partir do print

- Print novo antes de cada locate; mandar ao Jev pelo cliente Python de visão
  (operação `box`).
- Jev 0.24.0 ou mais recente para visão — versões anteriores rejeitam o tipo
  `box` e não veem pixels.
- Clicar só as coordenadas que o Jev devolveu para aquele alvo; nunca inventar
  coordenada nem clicar num alvo que o Jev não localizou.
- Localização com confiança baixa é erro: print novo e outra tentativa, em vez
  de clicar mesmo assim.
- Rolar o alvo para dentro da vista antes de localizar — formulário ou botão
  abaixo da dobra fica invisível para o Jev até a página rolar.
- Confirmar o login pelo conteúdo visível da página (tela ou itens esperados),
  nunca só pela URL.
- Parar e reportar em checkpoint, aviso de bot ou suspeita, em vez de insistir.

## Verificar cada passo e reobservar

- Print novo depois de cada ação e confirmar o efeito antes de escolher a
  próxima (foco, mudança de página, endereço esperado).
- Nada é enviado, publicado ou alterado na conta sem a aprovação do texto ou
  da imagem exatos pelo usuário.
- Ritmo lento, humano, entre ações; sem rajadas de tentativas.
