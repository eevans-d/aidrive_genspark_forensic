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

Entendido. Te presento, sin desviarme del alcance, un plan integral y operativo para llevar el proyecto desde su estado actual hasta “Listo para Iniciar la Etapa de Despliegue” (pre‑deploy). Incluye: criterio de aprobación (qué confirmar y verificar), evidencias requeridas y un plan de ejecución paso a paso para conseguirlas. No aborda la ejecución del despliegue, sólo la preparación/validación previa.

1) Radiografía del estado actual (base real del repo)
Componentes principales
inventario-retail/:
agente_deposito, agente_negocio, ml (código, Dockerfiles y compose de producción).
web_dashboard/ (FastAPI, seguridad reforzada: CSP, HSTS opcional, API Key en /api/* y /metrics, métricas texto, logging con request_id).
nginx/nginx.conf para capa frontal.
docker-compose.production.yml para orquestación.
Toolkit optimización y validaciones: app/retail/ y shared/ con tests en tests/retail/.
CI/CD (en .github/workflows/ci.yml) centrado en Dashboard:
Tests+coverage (target ≥85% cumplido), build/push GHCR, smoke container, Trivy advisory, deploy staging con secretos, smoke post-deploy y verificación de métricas en staging (advisory).
Scripts y operaciones
Preflight RC del Dashboard (smoke+metrics+headers): preflight_rc.sh
Checks: check_metrics_dashboard.sh, check_security_headers.sh, smoke_dashboard_staging.sh
Makefile con atajos: make preflight / make rc-tag / make coverage, etc.
SQL y config de bases: config/database/*.sql, .env.production.template
Monitoreo básico: monitoring_basic/*.py y dashboards JSON.
Documentación operativa clave
README_DEPLOY_STAGING.md / README_DEPLOY_STAGING_EXT.md
DEPLOYMENT_GUIDE.md (multi-agente)
RUNBOOK_OPERACIONES_DASHBOARD.md
CHANGELOG.md
Conclusión: El Dashboard está casi listo con pipeline end‑to‑end hacia staging. El multi‑agente tiene artefactos de producción listos (Dockerfiles, compose, NGINX, guías), pero faltan gates de calidad unificados en CI y preflights similares a los del Dashboard.

2) Criterios de aprobación para pasar a “Listo para Despliegue”
Debemos poder afirmar, con evidencias, que:

A. Código y calidad

A1. Dashboard: tests verdes con cobertura ≥85% (actual 86%) y snapshot CSP ok.
A2. Núcleo retail (agente_deposito, agente_negocio, ml, shared/app): tests “unit/funcionales” verdes en tests/retail y sin dependencias externas en ejecución CI.
A3. Lint y seguridad (advisory) sin hallazgos críticos bloqueantes (Trivy: 0 Critical; Bandit/Ruff sin issues críticos).
B. Seguridad y cumplimiento

B1. Dashboard: headers de seguridad pasan check_security_headers.sh (CSP prefijo válido; HSTS sólo si forzado).
B2. Todos los endpoints sensibles detrás de auth (Dashboard: X‑API‑Key ya forzado; agentes: confirmar políticas o reverse proxy con NGINX).
B3. Secretos definidos y validados (Staging y Producción): host, user, key, GHCR token, API keys por componente (no en repo).
C. Configuración y datos

C1. Plantillas de entorno productivo completas: .env.production.template parametrizada y verificada por servicio.
C2. Esquemas/índices BD aplicables y validados (scripts SQL en config/database/*), con plan de ejecución y verificación (dry-run y post‑apply).
D. Observabilidad y performance (pre‑deploy)

D1. Métricas base expuestas (Dashboard: dashboard_requests_total/errors_total/p95; agentes: endpoints /metrics o equivalente).
D2. Preflight funcional por componente (salud + auth + rutas críticas) listo para correr contra staging.
D3. Umbrales iniciales: error% <2% y p95 <800ms en Dashboard en staging (mínimo 30–60 min de observación); para agentes: health OK y rutas críticas responden con tiempos razonables definidos.
E. Infra y orquestación

E1. docker-compose.production.yml resuelve servicios, redes y volúmenes sin conflictos; imágenes disponibles en GHCR.
E2. NGINX config valida rutas, headers y upstreams; sin directivas inseguras.
E3. Rollback plan comprobado (re-deploy con tag previo), documentado en runbook.
F. Gestión de versión y gobernanza

F1. Tagging definido (vX.Y.Z-rcN → vX.Y.Z), CHANGELOG actualizado y checklist RC completado.
F2. Aprobación formal Go/No‑Go para pasar a despliegue.
“Listo para Despliegue” = todos los puntos A–F en estado Done con evidencia documentada.

3) Evidencias a recolectar y cómo obtenerlas (operativas y medibles)
EVD‑A1 (Dashboard tests/cobertura): salida pytest y reporte coverage.xml ≥85%.
EVD‑A2 (Tests retail): salida pytest tests/retail, sin dependencias externas (usar fixtures).
EVD‑A3 (Lint/seguridad): salida de Ruff y Bandit (advisory), reporte Trivy con 0 Critical.
EVD‑B1 (Headers): salida check_security_headers.sh en staging (y prod si HTTPS), adjuntando log.
EVD‑B2 (Auth): curl 401 sin API Key y 200/500 con API Key en rutas clave, por servicio.
EVD‑B3 (Secretos): captura “secrets list” (nombres, no valores) y validación del job staging‑secrets‑check (Dashboard) + plan/registro para agentes.
EVD‑C1 (Env): dif de .env.production.template con valores esperados (sin secretos), verificación por servicio.
EVD‑C2 (BD): ejecución controlada de config/database/* en entorno de prueba o staging y verificación de índices/aplicación.
EVD‑D1/D2/D3 (Obs/perf): salidas de preflight_rc.sh (Dashboard) y preflights análogos para agentes (health+latencias); snapshots de /metrics donde aplique.
EVD‑E1 (Compose): docker compose config/convert sin errores; dry‑run pull/up en staging para validar arranque.
EVD‑E2 (NGINX): nginx -t y curl con headers, validando CSP y proxies hacia upstreams.
EVD‑E3 (Rollback): bitácora de un ensayo rollback en staging (cambiar tag → revertir, 5 min).
EVD‑F1 (Versionado): CHANGELOG con entrada RC; issue de checklist RC completado.
EVD‑F2 (Go/No‑Go): acta/nota de aprobación (comentario en issue) con responsables.
4) Plan de ejecución estratégico (preciso y eficiente)
Respetando los “DONES”: sin refactors, sin deps pesadas, sin cambios de estructura. Priorizamos validar y preparar. Duraciones estimadas, responsables “Dev/DevOps/SRE” según tu equipo.

Fase 0 — Alineación y preparación (0.5 d)

0.1 Sincronizar local (hecho) y activar venv (hecho).
0.2 Revisar variables y secretos necesarios (staging y prod) para Dashboard y servicios agentes; listar faltantes.
0.3 Abrir issue “RC Readiness Gate” usando plantilla release_rc_checklist.md.
Fase 1 — Calidad y seguridad (1 d)

1.1 Dashboard: make coverage (esperado ≥85%).
1.2 Retail toolkit y agentes: pytest tests/retail (registrar salida; si algún test depende de externo, aislar con fixture o marcar skip razonado).
1.3 Lint/seguridad: ruff check . y bandit -q -r . (advisory); trivy sobre imagen dashboard (ya en CI) y, si aplica, imágenes de agentes (advisory).
Evidencias: EVD‑A1/A2/A3 adjuntas al issue.
Fase 2 — Config y secretos (0.5 d)

2.1 Completar inventario de variables por servicio (basado en .env.production.template y guías).
2.2 Cargar/verificar secretos staging y prod en el repo (sólo nombres, no valores en issue); correr staging‑secrets‑check para Dashboard (ya en CI); plan análogo para agentes (si se añaden deploy jobs).
Evidencias: EVD‑B3/C1.
Fase 3 — BD y datos (0.5–1 d)

3.1 Revisar scripts SQL en config/database/* (índices, pragmas, optimizaciones); elaborar orden de aplicación por entorno.
3.2 Ensayo en entorno de prueba/staging: aplicar scripts y validar con consultas (tiempos, índices creados).
Evidencias: EVD‑C2.
Fase 4 — Observabilidad y preflights (1 d)

4.1 Dashboard staging: preflight_rc.sh -u <staging> -k <key>; capturar resultados (error% <2%, p95 <800ms si disponible).
4.2 Agentes staging: preflight por servicio (health, rutas clave, 401/200, latencias básicas). Si no existen scripts, crear curl one‑liners (no código en servicios).
4.3 Métricas: snapshots de /metrics para Dashboard; para agentes, confirmar exposición o, si no, validar health/logs y plan de métricas vía NGINX/exporter si corresponde (post‑deploy).
Evidencias: EVD‑D1/D2/D3.
Fase 5 — Infra y orquestación (0.5–1 d)

5.1 docker-compose.production.yml: docker compose config y validación de imágenes (pull) en staging (sin exponer públicamente aún).
5.2 NGINX: nginx -t y curl con headers; confirmar CSP, X‑Content-Type‑Options, etc., contra upstream de staging.
5.3 Rollback ensayo: alternar IMAGE_TAG a tag previo (o latest/rc) y revertir. Registrar tiempos (objetivo ≤5 min).
Evidencias: EVD‑E1/E2/E3.
Fase 6 — Gobernanza y cierre (0.5 d)

6.1 CHANGELOG: entrada [1.0.0‑rc1] con cambios relevantes (scripts, seguridad, CI, docs).
6.2 Checklist RC en issue: marcar todos los ítems con evidencias (enlaces a logs, outputs, capturas).
6.3 Go/No‑Go meeting/confirmación: firmar aprobación para pasar a etapa de despliegue (sin ejecutar aún).
Evidencias: EVD‑F1/F2.
Resultado de estas fases: “Aprobado para iniciar Etapa de Despliegue”.

5) Gaps potenciales y cómo resolverlos (si aparecen)
Tests retail fallan o dependen de externos: aislar con fixtures/datos embebidos o marcar skip con justificación en tests/retail (sin tocar lógica de producción).
Faltan métricas en agentes: como pre‑deploy, basta health y latencias; métricas se programan post‑Go‑Live o vía proxy (evitar introducir librerías ahora).
Vulnerabilidades críticas en imágenes: parche mínimo (update base image) o “ignore‑unfixed” con justificación si no explotables y plan post‑deploy para remediación.
CSP regresa distinta del snapshot: ajustar NGINX para no inyectar inline/externals no contemplados o actualizar snapshot si hay un motivo válido con doc anexa.
6) Entregables (todo tangible y verificable)
Issue “RC Readiness Gate” con:
EVD‑A…F (logs, capturas, outputs) adjuntos.
Checklist release_rc_checklist.md completado.
Acta breve Go/No‑Go (comentario).
CHANGELOG.md con sección [1.0.0‑rc1] final.
Parámetros de entorno (staging/prod) documentados por servicio (sin valores).
Bitácora de BD (scripts aplicados, timestamp, resultados).
Reporte de preflight(s) firmados (Dashboard y agentes).
7) Línea de tiempo sugerida (2–3 días hábiles)
Día 1: Fase 1 (calidad) + Fase 2 (secretos) + arranque de Fase 3 (BD).
Día 2: Cierre Fase 3 (BD) + Fase 4 (preflights) + Fase 5 (infra).
Día 3 (buffer/observación): Repetir preflight si hubo ajustes + Fase 6 (gobernanza) → “Listo para Despliegue”.
8) Responsables y handoffs
Dev: pruebas y evidencia A1/A2, soporte en headers/metrics si aplica.
DevOps/SRE: CI advisory, Trivy, secretos, preflights, compose/nginx, rollback.

Verificación automática previa:
- El job `staging-secrets-check` valida que los secretos críticos (`STAGING_HOST`, `STAGING_USER`, `STAGING_KEY`, `STAGING_GHCR_TOKEN`, `STAGING_DASHBOARD_API_KEY`) estén presentes. Si falta alguno, el job de `Deploy to Staging` se omite y en el summary del workflow verás la lista de faltantes.

### Estado actual de secretos (Go-Live Plan)
| Secreto | Uso | Estado | Notas |
|---------|-----|--------|-------|
| STAGING_HOST | Host SSH VM | PENDIENTE | Añadir con `gh secret set` |
| STAGING_USER | Usuario SSH | PENDIENTE | Debe tener permisos docker |
| STAGING_KEY | Clave privada SSH | PENDIENTE | Formato PEM sin passphrase |
| STAGING_GHCR_TOKEN | Pull GHCR | PENDIENTE | Token con scope read:packages |
| STAGING_DASHBOARD_API_KEY | API Key runtime | PENDIENTE | Generar y rotar cada 30d |
| STAGING_DASHBOARD_UI_API_KEY (opcional) | API Key UI | PENDIENTE | Solo si frontend llama /api/* |

Para cargarlos rápidamente:
```bash
./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic --print-only
# Después usar gh para setear HOST/USER/KEY/GHCR.
```

Una vez cargados, el job `staging-secrets-check` mostrará ✅ y habilitará el deploy.

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
