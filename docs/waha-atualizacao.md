# WAHA — precisa atualizar? (checagem 2026-11-06)

> CHECK ONLY, 2026-11-06 ~09:10. Somente leitura: nada foi
> atualizado, reiniciado, recriado ou tocado. Nenhum segredo lido
> ou registrado. Proposta de atualização futura no fim, para
> aprovar quando houver versão nova.

## Veredito: NÃO precisa atualizar

A versão em produção **já é a última estável**: `2026.10.1`.
Não existe release mais nova. Os únicos pushes mais recentes no
Docker Hub são builds `dev` (29/10), pré-lançamento — não
recomendados para produção.

## Versão em execução vs última (com evidência)

**Em execução (verificado 2026-11-06 ~09:10):**

- `GET http://127.0.0.1:3005/api/version` → 200:
  `version 2026.10.1`, engine GOWS, tier CORE, linux/x64.
- Container `waha`, imagem `devlikeapro/waha:latest`, Up 7 dias
  (recriado 2026-10-29).
- Digest da imagem em execução:
  `sha256:2fc1787ddbd343ed2e7d59482846d1b22aa5ca134e29aa8d42d0e88c54e24779`
  (imagem construída 2026-10-28, revisão
  `c42f68ab25b93fd77f583e17477cbcc9d14471cc`).
- Sessões `tutibom` e `petemcasa`: status **WORKING** (API
  `/api/sessions`, sem autenticação), webhooks para o Deskcomm via
  gateway Docker (`http://172.17.0.1:3000/api/v1/webhooks/waha`),
  eventos `message`, `message.any`, `message.ack`. Atividade
  recente nas duas.

**Última estável (Docker Hub + GitHub, conferidos 2026-11-06):**

- Docker Hub `devlikeapro/waha`: tags `latest` e
  `latest-2026.10.1` apontam para o **mesmo digest** da imagem em
  execução (`sha256:2fc1787d…`). Último push estável: 2026-10-28.
- GitHub Releases (`devlikeapro/waha`): o release mais recente é
  `2026.10.1` (changelog `2026.9.2...2026.10.1`). Nada de
  `2026.11.x`.
- Tags `dev` / `dev-chrome` / `dev-arm` (push 2026-10-29) são
  builds de desenvolvimento, não release.

**O que a 2026.10.1 já traz (e por isso não há urgência):**

- Segurança: Node.js CVE-2026-111497 (Brotli RCE), `file-type`
  CVE-2026-31808, `shell-quote` CVE-2026-13311, `sharp` GHSA
  (decodificadores de imagem); `x-api-key` redactada dos logs de
  websocket; valores não-string de `x-api-key` rejeitados.
- GOWS: engine atualizado; `FAILED` em falhas de conexão (ban,
  cliente desatualizado etc.); link preview, status (about),
  prévia de vídeo, labels sync, correções de LID.
- O release anterior era `2026.9.2`; a produção já tinha pulado
  para `2026.10.1` em 2026-10-29.

## Preservação das sessões (avaliação)

As sessões vivem em DADOS, não no container:

- `waha_sessions_data` (external: true) → `/app/.sessions`
  (ESSENCIAL): contém o store GOWS, **315,7 MB** no disco.
- `waha_data` → `/app/.waha`: historicamente vazio (**4,0 KB**),
  mantido por compatibilidade.
- Um recreate com o mesmo compose preserva as sessões — provado
  em 2026-10-29, quando o WAHA foi de `2026.8.2` para `2026.10.1`
  sem perda de sessão.
- Regras de ouro (documentadas em `~/waha/README.md` no PC):
  nunca apagar `waha_sessions_data`; nunca rodar
  `docker compose down -v` nesse diretório; antes de qualquer
  parada ou recriação, conferir que o compose continua montando
  `waha_sessions_data` em `/app/.sessions`.

**Detalhe:** o arquivo `~/waha-override-sessions.yml` (citado no
label do container na criação) **não existe mais** — foi
aposentado e arquivado em 2026-10-29, conforme o README. O
`docker-compose.yml` atual é a única fonte. Um recreate pelo
compose atual funciona sem ele.

## Relação com o serviço `waha` interno do Deskcomm

- O compose do Deskcomm tem um serviço `waha` próprio, com
  imagem fixada em `latest-2026.7.2` (mais antiga que a produção)
  e webhook interno `http://app:3000/api/v1/webhooks/waha`.
- Ele **NÃO foi iniciado** (decisão ainda aberta) e **não** é o
  WAHA em uso: o que atende é o standalone (`waha`, `:3005`,
  `2026.10.1`, webhook via gateway Docker).
- São instâncias separadas: ligar o interno criaria um segundo
  WAHA, não compartilharia as sessões do standalone. Não iniciar
  sem decisão.

## Proposta de atualização futura (não executada)

Para quando sair uma versão nova (`2026.11.x` ou posterior).
Ordem, conforme `~/waha/README.md` no PC:

1. **Backup do volume de sessões, antes de parar qualquer
   coisa:** `docker run --rm -v waha_sessions_data:/data -v
   ~/backups-waha-20261029:/backup alpine tar czf
   /backup/waha-sessions-volume-AAAA-MM-DD.tar.gz -C /data .`
2. Baixar a imagem nova: `docker compose pull` (ou
   `docker pull devlikeapro/waha:latest`) — conferir o digest
   antes de subir.
3. Subir: `docker compose up -d` (no diretório `~/waha`).
4. Validar, tudo precisa estar verde:
   - `curl http://127.0.0.1:3005/api/version` → versão nova.
   - `curl http://127.0.0.1:3005/api/sessions` → `tutibom`
     WORKING e `petemcasa` WORKING, sem QR Code.
   - Logs com webhook para o DeskComm retornando HTTP 200.
5. Se alguma sessão voltar FAILED ou pedir QR Code: parar o
   container, restaurar o backup do volume, voltar a imagem
   anterior pelo digest e subir de novo.

**Rollback (valores conhecidos):**

- Imagem anterior a 2026-10-29: `2026.8.2`, digest
  `sha256:527ff3d634925adb26d596883d7b3ca502c080f737af3c2af2be0c973c511533`.
  (A imagem `2026.10.1` atual também fica local após o pull da
  nova, como volta imediata.)
- Backups de volume em `~/backups-waha-20261029/` no PC
  (`waha-sessions-final-20261029.tar.gz` e o compose original).

**Riscos da atualização futura:** recriação do container derruba
o WhatsApp por alguns minutos (sessões reconectam sozinhas se o
volume estiver montado); uma versão nova pode mudar o
comportamento do engine GOWS ou o formato do store (o changelog
do release deve ser lido antes); o digest precisa ser conferido
para não subir um `latest` diferente do esperado. Nada disso se
aplica agora — não há versão nova.
