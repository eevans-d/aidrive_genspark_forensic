# Staging del Dashboard en Fly.io (guía paso a paso)

Esta guía te lleva a desplegar el Dashboard como entorno de “staging” en Fly.io, obtener la URL y correr los preflights antes del Go‑Live.

## 1) Requisitos
- Tener la imagen del Dashboard publicada en GHCR (o construirla en Fly). Ejemplo: `ghcr.io/eevans-d/aidrive_genspark_forensic:latest`.
- Fly CLI instalada y autenticada (`flyctl`).
- Una API Key para el Dashboard (protege `/api/*` y `/metrics`).

Sugerencia rápida para generar una API key sin tocar secretos de CI:
```bash
./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic --print-only
```
Copia el valor impreso como TU_API_KEY.

## 2) Crear la app en Fly (sin desplegar aún)
```bash
flyctl launch --no-deploy --name minimarket-dashboard-staging --region scl
# Si pregunta por builder, elige "no" para usar imagen existente
```

## 3) Desplegar usando tu imagen
Opción 1: especificar la imagen por flag en el deploy
```bash
docker login ghcr.io
flyctl deploy --image ghcr.io/eevans-d/aidrive_genspark_forensic:latest
```
Opción 2: fijar `image` en `fly.toml` (ver sección 6) y luego:
```bash
flyctl deploy
```

## 4) Configurar secretos (runtime)
```bash
flyctl secrets set DASHBOARD_API_KEY="<TU_API_KEY>"
flyctl secrets set DASHBOARD_ALLOWED_HOSTS="minimarket-dashboard-staging.fly.dev"
# Opcional (si quieres validar headers de prod)
flyctl secrets set DASHBOARD_FORCE_HTTPS="true" DASHBOARD_ENABLE_HSTS="true"
```

## 5) URL de Staging
- STAGING_URL = `https://minimarket-dashboard-staging.fly.dev`
- STAGING_DASHBOARD_API_KEY = `<TU_API_KEY>` (el de arriba)

## 6) fly.toml mínimo (opcional)
Si prefieres tenerlo versionado, crea `fly.toml` en el repo con este contenido:
```toml
app = "minimarket-dashboard-staging"
primary_region = "scl"

[build]
# Usa deploy con --image o define aquí la imagen pública/privada
# image = "ghcr.io/eevans-d/aidrive_genspark_forensic:latest"

[deploy]

[http_service]
internal_port = 8080
force_https = true
auto_stop_machines = true
auto_start_machines = true
min_machines_running = 1

[[services]]
internal_port = 8080
processes = ["app"]
protocol = "tcp"
[[services.ports]]
handlers = ["http"]
port = 80
[[services.ports]]
handlers = ["tls", "http"]
port = 443
```

## 7) Preflight de Staging (Dashboard)
Con Makefile:
```bash
make preflight STAGING_URL="https://minimarket-dashboard-staging.fly.dev" STAGING_DASHBOARD_API_KEY="<TU_API_KEY>"
```
Directo con script (usa `--prod` si activaste HSTS/HTTPS):
```bash
./scripts/preflight_rc.sh -u https://minimarket-dashboard-staging.fly.dev -k "<TU_API_KEY>" --prod
```
Smoke test rápido (opcional):
```bash
DASHBOARD_HOST="minimarket-dashboard-staging.fly.dev" DASHBOARD_API_KEY="<TU_API_KEY>" DASHBOARD_PORT=443 ./scripts/smoke_dashboard_staging.sh
```

## 8) ¿Qué valores pongo dónde?
- STAGING_URL → `https://minimarket-dashboard-staging.fly.dev`
- STAGING_DASHBOARD_API_KEY → la clave definida con `flyctl secrets set`.

## 9) Troubleshooting breve
- `flyctl auth status` debe mostrar sesión activa. Si no:
```bash
flyctl auth login
```
- Si expones HTTP (sin TLS), quita `--prod` en el preflight y usa `http://...`.
- Si la imagen es privada, asegúrate de `docker login ghcr.io` y permisos `read:packages`.
- Si el preflight falla en headers con HSTS, valida que `DASHBOARD_ENABLE_HSTS=true` y `DASHBOARD_FORCE_HTTPS=true` estén en secrets.

## 10) Go‑Live
Si el preflight pasa (error% <2%, métricas OK, headers OK):
1) Fusiona el PR de release.
2) Crea tag `v1.0.0`.
3) Sigue `FASE8_GO_LIVE_PROCEDURES.md`.
