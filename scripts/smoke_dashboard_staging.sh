#!/usr/bin/env bash
set -euo pipefail

# Smoke test para Dashboard en Staging.
# Uso:
#   ./scripts/smoke_dashboard_staging.sh -h <host> -k <api_key> [-p 8080]
# O usando variables de entorno:
#   DASHBOARD_HOST=staging.example.com DASHBOARD_API_KEY=xxxxx ./scripts/smoke_dashboard_staging.sh
#
# Códigos aceptados:
# - /api/summary puede devolver 200 o 500 (500 aceptable si hay fallo DB) pero nunca 401 ni 403.
# - /health debe devolver 200 o 503 (503 sólo si depende de DB y falla) con JSON.
#
# Salida: resumen final + exit code !=0 si fallo crítico.

HOST="${DASHBOARD_HOST:-}"      # host o host:puerto
API_KEY="${DASHBOARD_API_KEY:-}"   # api key
PORT="${DASHBOARD_PORT:-8080}"

while getopts "h:k:p:" opt; do
  case $opt in
    h) HOST="$OPTARG" ;;
    k) API_KEY="$OPTARG" ;;
    p) PORT="$OPTARG" ;;
    *) echo "Uso: $0 -h <host> -k <api_key> [-p puerto]" >&2; exit 1 ;;
  esac
done

if [ -z "$HOST" ] || [ -z "$API_KEY" ]; then
  echo "[ERROR] Debes especificar host y API Key (flags o variables)." >&2
  exit 1
fi

BASE="http://$HOST:$PORT"
FAILS=()

function status() {
  local url="$1"; shift
  curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" "$url" || echo 000
}

function status_noauth() {
  local url="$1"; shift
  curl -s -o /dev/null -w "%{http_code}" "$url" || echo 000
}

echo "[INFO] Smoke Dashboard → $BASE"

# 1. Health
S_HEALTH=$(status "$BASE/health")
if [[ "$S_HEALTH" != "200" && "$S_HEALTH" != "503" ]]; then
  FAILS+=("/health => $S_HEALTH")
fi

# 2. Summary sin API Key (debe 401)
S_SUMMARY_NOAUTH=$(status_noauth "$BASE/api/summary")
if [[ "$S_SUMMARY_NOAUTH" != "401" ]]; then
  FAILS+=("/api/summary sin API Key => $S_SUMMARY_NOAUTH (esperado 401)")
fi

# 3. Summary con API Key (200 o 500 aceptable)
S_SUMMARY=$(status "$BASE/api/summary")
if [[ "$S_SUMMARY" != "200" && "$S_SUMMARY" != "500" ]]; then
  FAILS+=("/api/summary con API Key => $S_SUMMARY (esperado 200/500)")
fi

# 4. Metrics
S_METRICS=$(status "$BASE/metrics")
if [[ "$S_METRICS" != "200" ]]; then
  FAILS+=("/metrics => $S_METRICS (esperado 200)")
fi

# 5. Export CSV
S_EXPORT=$(status "$BASE/api/export/summary.csv")
if [[ "$S_EXPORT" != "200" ]]; then
  FAILS+=("/api/export/summary.csv => $S_EXPORT (esperado 200)")
fi

# 6. Petición extra para generar algo de métricas
for i in {1..5}; do
  curl -s -H "X-API-Key: $API_KEY" "$BASE/api/providers" > /dev/null || true
done

# 7. Validar contenido mínimo /metrics
if ! curl -s -H "X-API-Key: $API_KEY" "$BASE/metrics" | grep -q "dashboard_requests_total"; then
  FAILS+=("/metrics sin dashboard_requests_total")
fi

echo "---" 
if [ ${#FAILS[@]} -eq 0 ]; then
  echo "[OK] Smoke test exitoso"
  exit 0
else
  echo "[FALLOS]" >&2
  for f in "${FAILS[@]}"; do echo " - $f" >&2; done
  exit 1
fi
