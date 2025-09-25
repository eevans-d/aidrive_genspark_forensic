# CI/CD del Dashboard y Módulos

Este documento describe el pipeline de Integración Continua (CI) y cómo extenderlo a Entrega/Despliegue Continuo (CD) con buenas prácticas de seguridad y rollback.

## CI: Pruebas automáticas en cada push/PR

Archivo: `.github/workflows/ci.yml`

- Dispara en pushes y PRs contra `master`.
- Job `test-dashboard`:
  - Python 3.12, cache de pip.
  - Instala dependencias del dashboard: `inventario-retail/web_dashboard/requirements.txt` y `pytest`.
  - Variables de entorno mínimas para pasar seguridad y evitar rate limit en test:
    - `DASHBOARD_API_KEY=test-key`
    - `DASHBOARD_RATELIMIT_ENABLED=false`
  - Ejecuta: `python -m pytest -q tests/web_dashboard`
  - Incluye test de cabecera CSP (`tests/test_csp_headers.py`) que verifica:
    - Ausencia de `'unsafe-inline'`.
    - Directivas `script-src` y `media-src` estrictas.
    - No reaparición de scripts inline no permitidos.

### Filtro temporal de tests legacy

Se añadió `pytest.ini` con `addopts = -k "not learning_system"` para excluir pruebas de un subsistema aún incompleto. Retirar este filtro cuando el módulo `learning_system` esté operativo.

### Recomendación de invocación

Usar siempre `python -m pytest` en CI garantiza el intérprete correcto del venv y evita falsos negativos de import.
- Job `lint-security` (no bloqueante):
  - Ejecuta `ruff check .` y `bandit -r .` como análisis asesor.

## Extender a cobertura y matriz de Python
- Añadir `pip install pytest-cov` y ejecutar `pytest --cov=inventario-retail/web_dashboard -q tests/web_dashboard`.
- Agregar matriz: `python-version: ["3.10", "3.11", "3.12"]` en `setup-python`.

## Cobertura de pruebas
- Instalación: `pytest-cov`
- Ejecución: `pytest --cov=inventario-retail/web_dashboard --cov-report=xml --cov-report=term-missing`
- Artefacto: `coverage.xml` (subido por el workflow). Puede añadirse un badge de cobertura al README.

## CD: Opciones de despliegue

1) Docker + GHCR
- Crear `Dockerfile` para `web_dashboard` (uvicorn + app).
- Workflow `docker.yml`:
  - Build con etiqueta `ghcr.io/<owner>/<repo>:sha` y `:latest` para branch `master`.
  - Push a GHCR usando `GITHUB_TOKEN` (permisos `packages: write`).
- Despliegue:
  - En staging/producción, `docker pull` + `docker compose up -d`.
  - Variables sensibles como `DASHBOARD_API_KEY`, `ALLOWED_HOSTS`, etc. inyectadas por secreto del entorno.

2) Deploy a VM vía SSH
- Usar `appleboy/ssh-action` o `rsync` para sincronizar sólo `inventario-retail/web_dashboard`.
- Ejecutar remoto: crear/activar venv, `pip install -r requirements.txt`, reiniciar servicio systemd de uvicorn.

3) PaaS (Railway/Render/Fly.io/Heroku)
- Definir variables de entorno en el proveedor.
- Lanzar con `uvicorn inventario-retail.web_dashboard.dashboard_app:app --host 0.0.0.0 --port $PORT`.

## Docker Build & Push (GHCR)

- Dockerfile: `inventario-retail/web_dashboard/Dockerfile`
- Job `docker-build-push` (solo en push a `master`):
  - Login a GHCR con `GITHUB_TOKEN` (permisos: packages:write)
  - Etiquetas: `latest` y `sha`
  - Imagen: `ghcr.io/<owner>/<repo>:latest` y `:sha-<commit>`

## Smoke Test de la Imagen

- Job `smoke-test-image`:
  - `docker pull ghcr.io/<owner>/<repo>:latest`
  - Ejecuta contenedor con `DASHBOARD_API_KEY=test-key`
  - Sonda `GET /health` (espera hasta 30s)
  - Intenta `GET /metrics` con `X-API-Key` (no bloqueante)

## Rollback seguro
- Mantener releases versionadas (tags) y artefactos Docker.
- Estrategia: `blue/green` o `canary` en staging, promoción manual a producción tras validación de smoke tests.
- Automatizar `restore_minimarket.sh` para revertir DB si fuera necesario (con backups válidos).

## Secretos y seguridad en CI/CD
- Nunca commitear claves. Usar `Actions secrets` y `Environments` con protección.
- Rotar `DASHBOARD_API_KEY` periódicamente. Limitar `ALLOWED_HOSTS`.
- Revisar outputs de `bandit` y `ruff` y corregir findings críticos.

## Observabilidad post-deploy
- Activar logs JSON y `/metrics` en producción.
- Añadir job opcional de smoke test post-deploy que consulte `/health` y `/metrics` con `X-API-Key`.
- Verificar periódicamente mediante el test CSP que la política se mantiene endurecida.

## Próximos pasos
- Añadir pipeline de Docker build & push.
- Implementar despliegue a staging con aprobación manual.
- Agregar badge de cobertura si se activa `pytest-cov`.
- Añadir test snapshot de la cabecera CSP si se desea mayor rigidez ante cambios.
- Eliminar el filtro `not learning_system` cuando las dependencias estén disponibles.

## Deploy manual a Staging (placeholder)
- Disparador: `workflow_dispatch` en GitHub Actions.
- Job `deploy-staging` imprime instrucciones y la referencia de imagen `ghcr.io/<owner>/<repo>:latest`.
- Cómo implementar:
  - Opción SSH: usar `appleboy/ssh-action` para conectarse a VM y correr `docker pull` + `docker compose up -d`.
  - Opción K8s: `azure/k8s-deploy` o `kubectl` para aplicar manifiestos.

## Despliegue SSH

El workflow incluye dos despliegues por SSH condicionados a que existan secretos en el repositorio:

- Staging (push a master): usa la imagen `:latest`.
- Producción (tags `v*`): usa la imagen etiquetada con el tag.

Secretos requeridos:
- Staging:
  - `STAGING_HOST`, `STAGING_USER`, `STAGING_KEY` (clave privada PEM)
  - `STAGING_GHCR_TOKEN` (token con permiso de lectura en GHCR)
  - `STAGING_DASHBOARD_API_KEY`
  - `STAGING_DASHBOARD_UI_API_KEY` (opcional; si quieres que la UI consuma `/api/*` desde el navegador)
- Producción:
  - `PROD_HOST`, `PROD_USER`, `PROD_KEY`
  - `PROD_GHCR_TOKEN`
  - `PROD_DASHBOARD_API_KEY`
  - `PROD_DASHBOARD_UI_API_KEY` (opcional)

Notas:
- El contenedor se corre como `minimarket-dashboard` exponiendo `:8080`. Ajusta puertos/variables según tu entorno.
- Para rollback, ejecuta el deploy con un tag previo (`vX.Y.Z`) o vuelve a `latest` estable.

Checklist host Staging (SSH):
- Docker Engine y Docker Compose instalados.
- Directorio de proyecto para compose, por ejemplo `/opt/minimarket-dashboard`.
- Archivo `.env.dashboard` basado en `deploy/compose/.env.dashboard.example` con valores reales.
- Abrir puerto 8080 o configurar proxy TLS (Nginx/Traefik) hacia el contenedor.

### Script para crear secretos de Staging (rápido y seguro)

Para agilizar la carga de secretos en GitHub Actions, puedes usar:

- Archivo de ejemplo: `scripts/.env.staging.secrets.example`
- Script: `scripts/set_staging_secrets.sh`

Pasos:
1) Instala y autentica GitHub CLI:
  - https://cli.github.com/
  - `gh auth login`
2) Copia y edita el archivo de ejemplo:
  - `cp scripts/.env.staging.secrets.example scripts/.env.staging.secrets`
  - Completa los valores (host, user, token GHCR, API keys, y ruta a tu clave SSH)
3) Ejecuta el script:
  - `bash scripts/set_staging_secrets.sh -f scripts/.env.staging.secrets`

El script configurará: `STAGING_HOST`, `STAGING_USER`, `STAGING_KEY` (desde archivo o inline), `STAGING_GHCR_TOKEN`, `STAGING_DASHBOARD_API_KEY` y, si lo indicas, `STAGING_DASHBOARD_UI_API_KEY`.
