#!/usr/bin/env bash
set -euo pipefail
# preflight_rc.sh
# Ejecuta un chequeo integral previo a crear un tag Release Candidate:
# - Smoke endpoints clave (/health, /api/summary, export CSV)
# - Validación de auth (401 sin API Key)
# - Métricas (requests, errores %, p95)
# - Headers de seguridad
# Requisitos: curl, awk, scripts: check_metrics_dashboard.sh, check_security_headers.sh
# Uso:
#   ./scripts/preflight_rc.sh -u https://staging.example.com -k $STAGING_DASHBOARD_API_KEY [--prod]
# Flags:
#   -u URL_BASE (obligatorio)
#   -k API_KEY  (obligatorio)
#   --prod      Espera HSTS (usa --expect-hsts en headers)
#   -t PCT_ERR_MAX  Umbral error% (default 2)
#   -p95 P95_MAX_MS Umbral p95 ms (default 800, sólo informativo si métrica existe)
# Salida: código 0 si todo pasa, >0 si falla algún chequeo.

BASE=""
API_KEY=""
EXPECT_PROD=0
ERR_MAX=2
P95_MAX=800

usage(){
  grep '^# ' "$0" | sed 's/^# //'
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -u) BASE="$2"; shift 2 ;;
    -k) API_KEY="$2"; shift 2 ;;
    --prod) EXPECT_PROD=1; shift ;;
    -t) ERR_MAX="$2"; shift 2 ;;
    -p95) P95_MAX="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Argumento desconocido: $1" >&2; usage; exit 1 ;;
  esac
done

[ -z "$BASE" ] && { echo "[ERROR] Falta -u URL_BASE" >&2; exit 2; }
[ -z "$API_KEY" ] && { echo "[ERROR] Falta -k API_KEY" >&2; exit 2; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REQS=("check_metrics_dashboard.sh" "check_security_headers.sh")
for r in "${REQS[@]}"; do
  [ -x "$SCRIPT_DIR/$r" ] || { echo "[ERROR] Script requerido no encontrado: $r" >&2; exit 3; }
done

fail(){ echo "[FAIL] $1"; exit 10; }
ok(){ echo "[OK] $1"; }
warn(){ echo "[WARN] $1"; }

echo "[INFO] Preflight RC sobre $BASE"

status_code(){ curl -s -o /dev/null -w "%{http_code}" "$@"; }

HC=$(status_code -H "X-API-Key: $API_KEY" "$BASE/health" || true)
[[ "$HC" == "200" || "$HC" == "503" ]] || fail "/health status inesperado: $HC"
[[ "$HC" == "200" ]] && ok "/health 200" || warn "/health 503 (degradado, revisar antes de tag)"

NOAUTH=$(status_code "$BASE/api/summary" || true)
[[ "$NOAUTH" == "401" ]] || fail "/api/summary sin auth debe 401 (recibido $NOAUTH)"
ok "/api/summary 401 sin API Key"

WITHAUTH=$(status_code -H "X-API-Key: $API_KEY" "$BASE/api/summary" || true)
[[ "$WITHAUTH" == "200" || "$WITHAUTH" == "500" ]] || fail "/api/summary con auth => $WITHAUTH"
[[ "$WITHAUTH" == "200" ]] && ok "/api/summary 200" || warn "/api/summary 500 (aceptable si datos/bd parcial)"

CSV=$(status_code -H "X-API-Key: $API_KEY" "$BASE/api/export/summary.csv" || true)
[[ "$CSV" == "200" ]] || fail "Export CSV summary => $CSV"
ok "Export CSV 200"

# Métricas
METRICS_RAW=$(curl -s -H "X-API-Key: $API_KEY" "$BASE/metrics" || true)
if [ -z "$METRICS_RAW" ]; then
  fail "No se pudo obtener /metrics"
fi
REQ_TOTAL=$(echo "$METRICS_RAW" | awk '/^dashboard_requests_total /{print $2; exit}')
ERR_TOTAL=$(echo "$METRICS_RAW" | awk '/^dashboard_errors_total /{print $2; exit}')
ERR_TOTAL=${ERR_TOTAL:-0}
if [ -z "$REQ_TOTAL" ]; then fail "Métrica dashboard_requests_total ausente"; fi
if [ "$REQ_TOTAL" -gt 0 ] 2>/dev/null; then
  ERR_PCT=$(awk -v e="$ERR_TOTAL" -v r="$REQ_TOTAL" 'BEGIN{printf "%.2f", (e/r)*100}')
else
  ERR_PCT=0
fi
echo "[INFO] Métricas: requests=$REQ_TOTAL errores=$ERR_TOTAL error%=$ERR_PCT"
GT=$(awk -v a="$ERR_PCT" -v b="$ERR_MAX" 'BEGIN{ if (a>b) print 1; else print 0 }')
[ "$GT" -eq 1 ] && fail "Error% $ERR_PCT > umbral $ERR_MAX" || ok "Error% dentro de umbral"
P95=$(echo "$METRICS_RAW" | awk '/^dashboard_request_duration_ms_p95 /{print $2; exit}')
if [ -n "$P95" ]; then
  echo "[INFO] p95(ms)=$P95 (umbral $P95_MAX)"
  GT95=$(awk -v a="$P95" -v b="$P95_MAX" 'BEGIN{ if (a>b) print 1; else print 0 }')
  [ "$GT95" -eq 1 ] && warn "p95 supera umbral (no bloquea RC)" || ok "p95 dentro de umbral"
else
  warn "p95 no expuesta (métrica opcional)"
fi

# Headers
HEADER_CMD=("$SCRIPT_DIR/check_security_headers.sh" -u "$BASE")
[ $EXPECT_PROD -eq 1 ] && HEADER_CMD+=(--expect-hsts)
set +e
"${HEADER_CMD[@]}"
HDR_RC=$?
set -e
[ $HDR_RC -eq 0 ] || fail "Headers de seguridad fallan"

ok "Preflight RC completado con éxito"
