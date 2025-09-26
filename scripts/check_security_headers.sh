#!/usr/bin/env bash
set -euo pipefail
# check_security_headers.sh
# Verifica presencia y valores básicos de headers de seguridad en el Dashboard.
# Uso:
#   ./scripts/check_security_headers.sh -u https://staging.example.com [-k API_KEY] [--expect-hsts]
# Opciones:
#   -u URL_BASE          (obligatorio)
#   -k API_KEY           API Key si la home requiere proteger endpoints secundarios (opcional para /)
#   --expect-hsts        Falla si Strict-Transport-Security no está presente
#   --csp-prefix VAL     Prefijo esperado de la CSP (default: "default-src 'self'")
# Salidas:
#   0 éxito, >0 fallos.

BASE=""
API_KEY=""
EXPECT_HSTS=0
CSP_PREFIX="default-src 'self'"

usage(){
  echo "Uso: $0 -u URL_BASE [-k API_KEY] [--expect-hsts] [--csp-prefix VAL]" >&2
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -u) BASE="$2"; shift 2 ;;
    -k) API_KEY="$2"; shift 2 ;;
    --expect-hsts) EXPECT_HSTS=1; shift ;;
    --csp-prefix) CSP_PREFIX="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Argumento desconocido: $1" >&2; usage; exit 1 ;;
  esac
done

[ -z "$BASE" ] && { echo "Falta -u URL_BASE" >&2; exit 2; }

HDR_TMP=$(mktemp)

# Realiza petición a la raíz / (no falla por códigos HTTP si responde)
if [ -n "$API_KEY" ]; then
  curl -s -D "$HDR_TMP" -H "X-API-Key: $API_KEY" -o /dev/null "$BASE/" || true
else
  curl -s -D "$HDR_TMP" -o /dev/null "$BASE/" || true
fi

pass=1
report(){ echo "[INFO] $1"; }
fail(){ echo "[FAIL] $1"; pass=0; }

get_header(){ awk -v h="$1" 'BEGIN{IGNORECASE=1} tolower($0) ~ tolower(h":" ) {sub(/^[^:]+:[ ]*/, ""); print; exit}' "$HDR_TMP"; }

CSP=$(get_header "Content-Security-Policy" || true)
if [ -z "$CSP" ]; then fail "Missing Content-Security-Policy"; else
  if [[ "$CSP" == $CSP_PREFIX* ]]; then report "CSP OK (prefijo coincide)"; else fail "CSP no comienza con prefijo esperado"; fi
fi

XCTO=$(get_header "X-Content-Type-Options" || true)
[[ "$XCTO" == "nosniff" ]] && report "X-Content-Type-Options OK" || fail "X-Content-Type-Options inválido ($XCTO)"

XFO=$(get_header "X-Frame-Options" || true)
[[ "$XFO" == "DENY" || "$XFO" == "SAMEORIGIN" ]] && report "X-Frame-Options OK" || fail "X-Frame-Options ausente o inesperado ($XFO)"

RP=$(get_header "Referrer-Policy" || true)
[[ -n "$RP" ]] && report "Referrer-Policy presente ($RP)" || fail "Referrer-Policy ausente"

PP=$(get_header "Permissions-Policy" || true)
[[ -n "$PP" ]] && report "Permissions-Policy presente" || fail "Permissions-Policy ausente"

HSTS=$(get_header "Strict-Transport-Security" || true)
if [ $EXPECT_HSTS -eq 1 ]; then
  [[ -n "$HSTS" ]] && report "HSTS presente" || fail "Se esperaba HSTS y no está"
else
  if [ -n "$HSTS" ]; then report "HSTS presente (entorno probablemente HTTPS)"; else report "HSTS no esperado (OK en staging http)"; fi
fi

rm -f "$HDR_TMP"

if [ $pass -eq 1 ]; then
  echo "[OK] Headers de seguridad verificados"; exit 0
else
  echo "[ERROR] Fallas en headers"; exit 10
fi
