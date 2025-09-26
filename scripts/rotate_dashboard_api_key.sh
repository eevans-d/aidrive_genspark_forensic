#!/usr/bin/env bash
set -euo pipefail

# Script de rotación de DASHBOARD_API_KEY y opcional DASHBOARD_UI_API_KEY.
# Requiere: gh (GitHub CLI) autenticado y permisos para setear secretos.
# Alineado a política: Staging rotación cada 30d, Producción cada 60d o incidente.

DEFAULT_LEN=48
FORMAT="base64" # base64 | hex

usage() {
  cat <<EOF
Uso: $0 -r <repo> [-k <nueva_api_key>] [-u <nueva_ui_api_key>] [--print-only] [--prod] [--len N] [--hex]

Opciones:
  -r           Repositorio (owner/name)
  -k           Nueva DASHBOARD_API_KEY (si se omite se genera aleatoria)
  -u           Nueva DASHBOARD_UI_API_KEY (opcional; si se omite no se cambia)
  --prod       Actualiza secretos de producción (usa PROD_* en lugar de STAGING_*)
  --len N      Longitud deseada de la clave aleatoria (default 48)
  --hex        Usar generación en hex (por defecto base64 filtrado)
  --print-only Muestra claves pero no ejecuta gh secret set

Ejemplo:
  $0 -r eevans-d/aidrive_genspark_forensic
  $0 -r eevans-d/aidrive_genspark_forensic -k "clave-fija" -u "clave-ui" --print-only
EOF
}

REPO=""
API_KEY=""
UI_KEY=""
PRINT_ONLY=false
PROD=false
LENGTH=$DEFAULT_LEN

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r) REPO="$2"; shift 2;;
    -k) API_KEY="$2"; shift 2;;
    -u) UI_KEY="$2"; shift 2;;
  --print-only) PRINT_ONLY=true; shift;;
  --prod) PROD=true; shift;;
  --len) LENGTH="$2"; shift 2;;
  --hex) FORMAT="hex"; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Arg desconocido: $1" >&2; usage; exit 1;;
  esac
done

if [[ -z "$REPO" ]]; then
  echo "Debe especificar -r <repo>" >&2
  exit 1
fi

rand_key() {
  if [[ "$FORMAT" == "hex" ]]; then
    BYTES=$(( (LENGTH + 1) / 2 ))
    openssl rand -hex "$BYTES" | cut -c1-"$LENGTH"
  else
    RAW_BYTES=$(( (LENGTH * 3 / 4) + 4 ))
    openssl rand -base64 "$RAW_BYTES" | tr -d '=+/\n' | cut -c1-"$LENGTH"
  fi
}

if [[ -z "$API_KEY" ]]; then
  API_KEY=$(rand_key)
fi

if [[ -z "$UI_KEY" ]]; then
  # Sólo generar si se desea rotar UI (puede omitirse sin impacto)
  :
fi

TARGET_PREFIX="STAGING"
if $PROD; then TARGET_PREFIX="PROD"; fi

echo "[INFO] Target: $TARGET_PREFIX"
echo "Nueva DASHBOARD_API_KEY ($FORMAT,$LENGTH): $API_KEY"
if [[ -n "$UI_KEY" ]]; then
  echo "Nueva DASHBOARD_UI_API_KEY: $UI_KEY"
fi

if $PRINT_ONLY; then
  echo "-- Modo print-only: no se actualizaron secretos --"
  exit 0
fi

command -v gh >/dev/null 2>&1 || { echo "gh CLI no encontrado" >&2; exit 1; }

SECRET_MAIN="${TARGET_PREFIX}_DASHBOARD_API_KEY"
SECRET_UI="${TARGET_PREFIX}_DASHBOARD_UI_API_KEY"

echo "$API_KEY" | gh secret set "$SECRET_MAIN" -R "$REPO" --app actions
if [[ -n "$UI_KEY" ]]; then
  echo "$UI_KEY" | gh secret set "$SECRET_UI" -R "$REPO" --app actions
fi
echo "Secretos actualizados en $REPO ($TARGET_PREFIX)" >&2
