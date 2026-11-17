#!/usr/bin/env bash
# profile-fb-status.sh — o perfil do Facebook está LIVRE ou OCUPADO?
#
# Regra (docs/operacao-perfil-fb.md): só o NAVEGADOR ABERTO ocupa o perfil.
# O loop do agente vivo, sozinho, NÃO ocupa. A trava .parentlock, sozinha,
# também não prova nada: ela só vale se for um link para um pid vivo.
# Por isso o status é CALCULADO a cada chamada, não guardado num arquivo:
# um marcador "ocupado" apodrece se o agente cair; a checagem viva não.
#
# Uso:
#   scripts/profile-fb-status.sh                 # só informa
#   scripts/profile-fb-status.sh --limpar-orfaos # remove travas órfãs (só sem navegador)
#
# Saída: LIVRE (exit 0) | OCUPADO (exit 1) | ATENCAO (exit 2, trava órfã sem navegador)
set -u

BASE="$(cd "$(dirname "$0")/.." && pwd)/prototype-vision"
FB="$BASE/profile-fb"
PANEL="$BASE/profile-panel"

navegador_aberto() {
    # [f]irefox não casa com a própria linha de comando (truque do colchete).
    # keepalive.sh contém "camofox" no caminho e não é navegador — fora.
    pgrep -f '[f]irefox' >/dev/null 2>&1 && return 0
    pgrep -x Xvfb >/dev/null 2>&1 && return 0
    return 1
}

trava() { # $1 = perfil; imprime: ausente | viva:<pid> | orfa
    # O Firefox deixa DOIS arquivos de trava no perfil: .parentlock e lock.
    # Cada um só vale se for um link para um pid vivo.
    local perfil="$1" estado="ausente" nome lock alvo pid
    for nome in .parentlock lock; do
        lock="$perfil/$nome"
        [ -e "$lock" ] || [ -L "$lock" ] || continue
        if [ -L "$lock" ]; then
            alvo="$(readlink "$lock")"
            pid="${alvo##*+}"
            case "$pid" in
                ''|*[!0-9]*) estado="orfa" ;;
                *) if kill -0 "$pid" 2>/dev/null; then echo "viva:$pid"; return; else estado="orfa"; fi ;;
            esac
        else
            estado="orfa"   # arquivo regular (0 bytes nas travas vistas): resto de sessão fechada
        fi
    done
    echo "$estado"
}

limpar_orfaos() { # $1 = perfil; remove travas órfãs; recusa se houver trava viva
    local perfil="$1" nome lock alvo pid
    for nome in .parentlock lock; do
        lock="$perfil/$nome"
        [ -e "$lock" ] || [ -L "$lock" ] || continue
        if [ -L "$lock" ]; then
            alvo="$(readlink "$lock")"; pid="${alvo##*+}"
            case "$pid" in
                ''|*[!0-9]*) echo "NÃO removo (alvo sem pid legível): $lock -> $alvo"; return 1 ;;
                *) if kill -0 "$pid" 2>/dev/null; then echo "ERRO: trava viva em $lock (pid $pid) — não removo nada."; return 1; else rm -f "$lock" && echo "removida trava órfã: $lock -> $alvo"; fi ;;
            esac
        else
            rm -f "$lock" && echo "removida trava órfã: $lock"
        fi
    done
    return 0
}

pid_processo() { # $1 = padrão; pid do processo python (comm=python*), não do lançador bash
    local p comm
    for p in $(pgrep -f "$1" 2>/dev/null); do
        comm="$(ps -o comm= -p "$p" 2>/dev/null)"
        case "$comm" in python*) echo "$p"; return ;; esac
    done
}

LIMPAR=false
[ "${1:-}" = "--limpar-orfaos" ] && LIMPAR=true

NAV=0; navegador_aberto && NAV=1
TRAVA_FB="$(trava "$FB")"
TRAVA_PANEL="$(trava "$PANEL")"
AG_FB=$(pid_processo '[f]b_agent.py')
AG_PANEL=$(pid_processo '[p]anel_camofox_drive.py')

echo "profile-fb: trava=$TRAVA_FB | loop fb_agent=${AG_FB:-parado} | navegador=$([ "$NAV" = 1 ] && echo aberto || echo fechado)"
echo "profile-panel: trava=$TRAVA_PANEL | loop painel=${AG_PANEL:-parado}"

if [ "$LIMPAR" = true ]; then
    if [ "$NAV" = 1 ]; then
        echo "ERRO: navegador aberto — não removo trava nenhuma."; exit 1
    fi
    limpar_orfaos "$FB" || exit 1
    limpar_orfaos "$PANEL" || exit 1
    TRAVA_FB="$(trava "$FB")"; TRAVA_PANEL="$(trava "$PANEL")"
fi

case "$TRAVA_FB" in
    viva:*) echo "OCUPADO — navegador com o profile-fb aberto (trava viva)."; exit 1 ;;
esac
if [ "$NAV" = 1 ]; then echo "OCUPADO — há navegador aberto."; exit 1; fi
case "$TRAVA_FB:$TRAVA_PANEL" in
    *orfa*) echo "ATENCAO — trava órfã (resto de sessão fechada). Rode com --limpar-orfaos e confira de novo."; exit 2 ;;
esac
echo "LIVRE — nenhum navegador aberto e nenhuma trava viva. (Os loops dos agentes podem estar vivos e parados; isso não ocupa o perfil.)"
exit 0
