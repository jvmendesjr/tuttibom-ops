#!/usr/bin/env bash
# Roda um comando com as variáveis de /home/pc/Workspace/tuttibom-ops/.env.ferramentas carregadas.
# Uso: scripts/com-ferramentas.sh claude | cursor-agent | gemini | mcporter list
set -euo pipefail
F="${TUTTIBOM_ENV_FERRAMENTAS:-/home/pc/Workspace/tuttibom-ops/.env.ferramentas}"
[ -r "$F" ] || { echo "faltando $F" >&2; exit 1; }
set -a; . "$F"; set +a
exec "$@"
