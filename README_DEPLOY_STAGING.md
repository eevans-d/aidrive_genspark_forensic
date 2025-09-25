# 🚀 Guía de Despliegue en Staging (Dashboard)

Esta guía cubre el despliegue del Dashboard Web usando Docker Compose en una VM de staging.

## 1) Requisitos en la VM
- Docker Engine y Docker Compose instalados
- Puerto 8080 abierto (o proxy inverso configurado)
- Usuario con acceso SSH y permisos para `docker`

Instalación rápida (Ubuntu):

```bash
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

## 2) Estructura de despliegue
Usaremos el compose ya incluido en el repo:
- `deploy/compose/docker-compose.dashboard.yml`
- `deploy/compose/.env.dashboard` (lo creas a partir del ejemplo)

```bash
mkdir -p ~/minimarket-deploy
# Copiaremos el contenido de deploy/compose aquí vía CI; o puedes copiarlo manualmente
```

## 3) Configurar `.env.dashboard`
Crea el archivo a partir del ejemplo y completa claves reales:

```bash
cp deploy/compose/.env.dashboard.example deploy/compose/.env.dashboard
```

Variables mínimas:
- `DASHBOARD_API_KEY` (obligatoria, protege /api/* y /metrics)
- `ALLOWED_HOSTS` (coma separada, e.g. `mi-dominio.com,localhost`)
- Opcional `DASHBOARD_UI_API_KEY` si la UI debe invocar `/api/*` desde el navegador

## 4) Levantar el dashboard (manual)
En la VM o en tu entorno local:

```bash
cd deploy/compose
export IMAGE_TAG=latest
docker compose -f docker-compose.dashboard.yml pull
docker compose -f docker-compose.dashboard.yml up -d
```

## 5) Pruebas de salud y métricas

```bash
curl -H "X-API-Key: $DASHBOARD_API_KEY" http://localhost:8080/health
curl -H "X-API-Key: $DASHBOARD_API_KEY" http://localhost:8080/metrics | head
```

Si definiste `DASHBOARD_UI_API_KEY`, abre http://localhost:8080 y verifica en la consola de red del navegador que las peticiones a `/api/summary` incluyen `X-API-Key`.

Seguridad (headers):
- La política CSP está fijada por test snapshot. Cambios requieren actualizar el test y justificar en `DOCUMENTACION_CI_CD.md`.
- Si exportas el dashboard detrás de HTTPS y quieres HSTS añade en tu `.env.dashboard`:
  ```bash
  DASHBOARD_ENABLE_HSTS=true
  DASHBOARD_FORCE_HTTPS=true
  ```
  Existe un test que verifica que el header `Strict-Transport-Security` aparece cuando `DASHBOARD_ENABLE_HSTS=true`.

## 6) Despliegue automático por CI (opcional)
El workflow `.github/workflows/ci.yml` copia `deploy/compose/*` a `~/minimarket-deploy` y ejecuta `docker compose up -d` por SSH cuando hay push a `master` y existen secretos de staging.

Secretos necesarios (staging):
- `STAGING_HOST`, `STAGING_USER`, `STAGING_KEY` (PEM)
- `STAGING_GHCR_TOKEN`
- `STAGING_DASHBOARD_API_KEY`
- (Opcional) `STAGING_DASHBOARD_UI_API_KEY`

Verificación automática previa:
- El job `staging-secrets-check` valida que los secretos críticos (`STAGING_HOST`, `STAGING_USER`, `STAGING_KEY`, `STAGING_GHCR_TOKEN`, `STAGING_DASHBOARD_API_KEY`) estén presentes. Si falta alguno, el job de `Deploy to Staging` se omite y en el summary del workflow verás la lista de faltantes.

## 7) Troubleshooting rápido
- Ver logs del contenedor:
  ```bash
  docker logs -f minimarket-dashboard
  ```
- Revisar healthcheck del Compose:
  ```bash
  docker inspect --format='{{json .State.Health}}' minimarket-dashboard | jq
  ```
- Verificar que el `.env.dashboard` tenga la API Key y que el `healthcheck` está usando ese valor.
- Si usas proxy TLS, asegúrate de pasar `X-Forwarded-Proto` y configurar `DASHBOARD_FORCE_HTTPS=true` y `DASHBOARD_ENABLE_HSTS=true` si corresponde.

---
Staging listo. Para producción, usa tags (`vX.Y.Z`) que activan el job `deploy-production` con imagen versionada.
