# Runbook de Operaciones - Dashboard Mini Market

Procedimientos para operar, monitorear y solucionar problemas del Dashboard.

## Checklist de arranque
- Variables de entorno definidas (API Key, Allowed Hosts, HTTPS/HSTS, Rate Limit, Logging)
- Base de datos accesible
- Logs rotando a `${DASHBOARD_LOG_DIR}`
- Probes: `/health` responde 200

## Diagnóstico rápido
- Ver health: GET `/health`
- Ver métricas: GET `/metrics` con `X-API-Key`
- Revisar logs: `${DASHBOARD_LOG_DIR}/dashboard.log`
- Correlación: usar/propagar `X-Request-ID`
 - Script rápido métricas (requests, errores, p95): `scripts/check_metrics_dashboard.sh -u <url> -k <API_KEY>`
 - Script headers seguridad: `scripts/check_security_headers.sh -u <url>` (usar `--expect-hsts` en producción HTTPS)

## Respuesta a incidentes comunes
- 401 en APIs: validar `X-API-Key` y valor en `DASHBOARD_API_KEY`
- 429 Too Many Requests: ajustar `DASHBOARD_RATELIMIT_*` o esperar la ventana
- 5xx frecuentes: inspeccionar logs con `request_id`, revisar consultas/BD
- CORS bloquea front externo: configurar `DASHBOARD_CORS_ORIGINS`
- Error de Host: setear `DASHBOARD_ALLOWED_HOSTS`

## Mantenimiento
- Rotación de logs vía `TimedRotatingFileHandler` (configurable)
- Respaldo de logs antes de depuración profunda
- Revisión de métricas de latencia y errores por ruta

### Rotación de API Keys
- Política: Staging cada 30 días, Producción cada 60 días o ante incidente.
- Tooling: `scripts/rotate_dashboard_api_key.sh`
- Staging ejemplo:
	```bash
	./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic --print-only
	./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic
	```
- Producción (planificar ventana baja):
	```bash
	./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic --prod --print-only
	./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic --prod
	```
- Validación post-rotación:
	1. Confirmar `/api/summary` 401 con clave anterior
	2. Confirmar 200/500 con nueva clave
	3. Revisar `/metrics` (requests_total sigue aumentando)

## Prometheus/Grafana
- Scrape `/metrics` con API Key (via sidecar/exporter o auth en proxy)
- Paneles: solicitudes totales, errores 5xx, latencia por ruta, uptime

## Seguridad operativa
- Mantener la API Key fuera de repos y logs
- Forzar HTTPS en entornos públicos
- Limitar orígenes CORS
 - Validar headers tras cambios: `scripts/check_security_headers.sh -u <url>`

## Restauración de servicio
- Escalar workers Uvicorn/Gunicorn
- Reiniciar servicio tras cambios de env vars
- Verificar accesos en `/`, `/analytics`, `/providers`

### Rollback rápido (Staging / Producción)
Condición: incremento súbito de errores 5xx post despliegue.

1. Identificar tag estable previo (ej: `v1.0.0-rc1`)
2. Redeploy:
	```bash
	ssh $STAGING_USER@$STAGING_HOST \
	  "cd ~/minimarket-deploy && export IMAGE_TAG=v1.0.0-rc1 && \
		docker compose -f docker-compose.dashboard.yml pull && \
		docker compose -f docker-compose.dashboard.yml up -d"
	```
3. Verificar `/health` y reducción de errores en `/metrics`
4. Registrar incidente (timestamp, causa tentativa, acciones) en este runbook
5. Para producción, mismo procedimiento cambiando variables y host

### Criterios de corte ("DONES")
- Cobertura ya ≥85%: no perseguir mejoras marginales previas a Go-Live.
- No refactors de estructura o nombres de directorios hasta fase post-Go-Live.
- No expansión de caching sin métricas de latencia concretas.
- Ramas de error DB extremas no se fuerzan en tests ahora.

### Tagging (RC → Release)
1. Validar staging (preflight): `scripts/preflight_rc.sh -u <url> -k <API_KEY>`
2. Tag RC: `git tag v1.0.0-rc1 && git push origin v1.0.0-rc1`
3. Observar 30–60 min métricas y logs
4. Si estable: `git tag v1.0.0 && git push origin v1.0.0`
5. Registrar métricas iniciales (requests_total, error%, p95) aquí
