#!/usr/bin/env bash
# adb-gate.sh — portão de conexão ADB para o S10 Lite (TuttiBom)
#
# Aprendizados ADB da comunidade, itens 1, 2, 3, 5, 18, 20, 21, 22
# (ver docs/aprendizados-adb-comunidade.md e roadmap §11).
#
# Uso (no PC, ponto de execução do ADB):
#   adb-gate.sh connect <endpoint>   # endpoint relido antes, nunca fixo
#   adb-gate.sh check   <endpoint>   # identidade, tamanho, foco, boot
#   adb-gate.sh disconnect <endpoint>
#
# Regras:
# - O endpoint é sempre passado como argumento, relido antes de cada
#   conexão (~/adb-endpoint.txt no telefone, via SSH, ou a tela do S10).
#   Nunca há IP/porta fixos neste script.
# - Todo comando usa `adb -s <endpoint>` (identidade do aparelho).
# - Reconexão com retries limitados: 10 tentativas x 3 s (30 s máx).
# - Falha é classificada (não autorizado / offline / sem rota), não
#   só relatada como sintoma.
# - Nenhum endpoint, IP ou porta é impresso no log: só a causa.
# - Sem varredura de portas, sem tcpip 5555, sem mudar configuração.

set -u

ADB="${ADB:-$HOME/platform-tools/adb}"
[ -x "$ADB" ] || ADB="adb"
if ! command -v "$ADB" >/dev/null 2>&1; then
  printf 'STEP: adb FAIL no-adb-binary (%s nao encontrado)\n' "$ADB"
  printf 'SUMMARY: GATE FAIL causa=no-adb-binary\n'
  exit 1
fi

MODEL_ESPERADO="SM-G770F"
TAMANHO_ESPERADO="1080x2400"
TENTATIVAS=10
ESPERA_S=3

passo() { # passo <nome> <ok|FAIL> [detalhe]
  printf 'STEP: %s %s %s\n' "$1" "$2" "${3:-}"
}

uso() {
  echo "uso: $0 connect|check|disconnect <endpoint>" >&2
  exit 2
}

[ $# -eq 2 ] || uso
ACAO="$1"
ENDPOINT="$2"

case "$ACAO" in
  connect)
    tentativa=1
    while [ "$tentativa" -le "$TENTATIVAS" ]; do
      saida="$("$ADB" connect "$ENDPOINT" 2>&1)"
      modelo="$("$ADB" -s "$ENDPOINT" shell getprop ro.product.model 2>/dev/null | tr -d '\r' | tr -d ' ')"
      if [ "$modelo" = "$MODEL_ESPERADO" ]; then
        passo "connect" "OK" "tentativa $tentativa/$TENTATIVAS, modelo $modelo"
        passo "identity" "OK" "modelo $MODEL_ESPERADO"
        printf 'SUMMARY: GATE OK\n'
        exit 0
      fi
      case "$saida" in
        *refused*)  causa="connection-refused (depuração caiu ou endereço mudou)" ;;
        *timed\ out*|*No\ route*|*unreachable*) causa="network (sem rota ou fora do ar)" ;;
        *unauthorized*) causa="not-authorized (aparelho não autorizou)" ;;
        *) causa="unknown ($saida)" ;;
      esac
      passo "connect" "FAIL" "tentativa $tentativa/$TENTATIVAS, causa: $causa"
      tentativa=$((tentativa + 1))
      [ "$tentativa" -le "$TENTATIVAS" ] && sleep "$ESPERA_S"
    done
    printf 'SUMMARY: GATE FAIL causa=%s apos %s tentativas\n' "$causa" "$TENTATIVAS"
    exit 1
    ;;
  check)
    modelo="$("$ADB" -s "$ENDPOINT" shell getprop ro.product.model 2>/dev/null | tr -d '\r' | tr -d ' ')"
    if [ "$modelo" = "$MODEL_ESPERADO" ]; then
      passo "identity" "OK" "modelo $modelo"
    else
      passo "identity" "FAIL" "modelo obtido: ${modelo:-<vazio>}, esperado: $MODEL_ESPERADO"
      printf 'SUMMARY: CHECK FAIL identity\n'
      exit 1
    fi
    tamanho="$("$ADB" -s "$ENDPOINT" shell wm size 2>/dev/null | tr -d '\r')"
    case "$tamanho" in
      *"$TAMANHO_ESPERADO"*) passo "wm-size" "OK" "$tamanho" ;;
      *) passo "wm-size" "FAIL" "${tamanho:-<vazio>}, esperado: $TAMANHO_ESPERADO"; printf 'SUMMARY: CHECK FAIL wm-size\n'; exit 1 ;;
    esac
    foco="$("$ADB" -s "$ENDPOINT" shell dumpsys window 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' | head -2 | tr -d '\r')"
    passo "focus" "OK" "$(printf '%s' "$foco" | tr '\n' ' ')"
    boot="$("$ADB" -s "$ENDPOINT" shell settings get global boot_count 2>/dev/null | tr -d '\r')"
    passo "boot_count" "OK" "${boot:-<indisponivel>}"
    printf 'SUMMARY: CHECK OK\n'
    exit 0
    ;;
  disconnect)
    "$ADB" disconnect "$ENDPOINT" >/dev/null 2>&1
    estado="$("$ADB" devices 2>/dev/null | grep -c "$ENDPOINT" || true)"
    if [ "$estado" = "0" ]; then
      passo "disconnect" "OK" "sessao encerrada"
      printf 'SUMMARY: DISCONNECT OK\n'
      exit 0
    fi
    passo "disconnect" "FAIL" "endpoint ainda listado"
    printf 'SUMMARY: DISCONNECT FAIL\n'
    exit 1
    ;;
  *)
    uso
    ;;
esac
