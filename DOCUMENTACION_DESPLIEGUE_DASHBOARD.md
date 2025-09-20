# Despliegue del Dashboard Mini Market

Guía para ejecutar el dashboard en desarrollo y producción.

## Requisitos
- Python 3.12
- Dependencias del proyecto instaladas (FastAPI, Uvicorn, Jinja2, etc.)
- Base de datos SQLite accesible por la app

## Variables de entorno clave
- `DASHBOARD_API_KEY` (requerida para /api y /metrics)
- `DASHBOARD_UI_API_KEY` (opcional; el frontend la inyecta y envía como `X-API-Key` en fetch a `/api/*`)
- `DASHBOARD_ALLOWED_HOSTS` (e.g., `example.com,localhost`)
- `DASHBOARD_FORCE_HTTPS` (`true|false`) → añade HTTPSRedirectMiddleware
- `DASHBOARD_ENABLE_HSTS` (`true|false`) → Strict-Transport-Security
- `DASHBOARD_CORS_ORIGINS` (lista separada por comas)
- `DASHBOARD_RATELIMIT_ENABLED` (`true|false`)
- `DASHBOARD_RATELIMIT_WINDOW` (segundos, por defecto 60)
- `DASHBOARD_RATELIMIT_MAX` (máx peticiones por ventana, por defecto 120)
- `DASHBOARD_LOG_LEVEL` (`INFO|DEBUG|WARNING|ERROR`)
- `DASHBOARD_LOG_DIR` (por defecto `web_dashboard/logs`)
- `DASHBOARD_LOG_ROTATE_WHEN` (por defecto `midnight`)
- `DASHBOARD_LOG_BACKUP_COUNT` (por defecto `7`)

## Desarrollo
- Ejecutar directamente el módulo:
  - Entrada: `inventario-retail/web_dashboard/dashboard_app.py`
  - El archivo incluye un bloque `if __name__ == "__main__":` con `uvicorn.run(..., reload=True)` en el puerto 8080.
- Acceso: http://localhost:8080/

## Producción (Uvicorn/Gunicorn)
- Ejecutar con Uvicorn:
  - Módulo: `inventario-retail.web_dashboard.dashboard_app:app`
  - Workers: acorde a CPU (e.g., 2-4)
  - Desactivar `reload` y habilitar logs a archivo
- Recomendado detrás de Nginx/Traefik con TLS y cabeceras de seguridad.

## Despliegue con Docker Compose

Ubicación: `deploy/compose/`

1) Copia el ejemplo de entorno y edita valores sensibles:
```bash
cp deploy/compose/.env.dashboard.example deploy/compose/.env.dashboard
# Edita DASHBOARD_API_KEY, ALLOWED_HOSTS, etc.
```

2) Levanta el servicio:
```bash
cd deploy/compose
docker compose -f docker-compose.dashboard.yml up -d
```

3) Verifica salud y métricas:
```bash
curl -H 'X-API-Key: $DASHBOARD_API_KEY' http://localhost:8080/health
curl -H 'X-API-Key: $DASHBOARD_API_KEY' http://localhost:8080/metrics | head
```

Notas:
- El volumen `dashboard_db` persiste la base SQLite en `/app/inventario-retail/agente_negocio` (ruta donde el dashboard espera `minimarket_inventory.db`).
- Ajusta puertos y variables según tu entorno; puedes mapear volumes a rutas del host si prefieres administrar backups allí.

### Frontend y API Key (DASHBOARD_UI_API_KEY)
Si defines `DASHBOARD_UI_API_KEY`, el dashboard insertará una meta en el HTML y los `fetch` de la UI enviarán `X-API-Key` automáticamente.

Ejemplo en Docker Compose (`deploy/compose/.env.dashboard`):

```bash
DASHBOARD_API_KEY=backend-secret
DASHBOARD_UI_API_KEY=frontend-secret
```

Pruebas rápidas:
- Abrir http://localhost:8080/ y verificar en Network que las solicitudes a `/api/summary` incluyen `X-API-Key`.
- Si no defines `DASHBOARD_UI_API_KEY`, las llamadas desde UI a `/api/*` fallarán con 401.

## Seguridad
- Definir obligatoriamente `DASHBOARD_API_KEY` antes de exponer `/api/*` y `/metrics`.
- Configurar `DASHBOARD_ALLOWED_HOSTS` para evitar Host header attacks.
- Activar `DASHBOARD_FORCE_HTTPS` y `DASHBOARD_ENABLE_HSTS` en producción.
- Habilitar CORS solo si se requieren orígenes externos.

## Logs
- Logs JSON estructurados en `${DASHBOARD_LOG_DIR}/dashboard.log` (rotación por tiempo).
- Incluyen: timestamp UTC, nivel, ruta, método, status, duración ms, ip cliente y `request_id`.

## Reverse Proxy (ejemplo Nginx)
- Proxy de `/` al app (localhost:8080)
- Pasar/forzar headers `X-Forwarded-Proto` para HTTPS si corresponde
- Opcional: reenviar `X-Request-ID`

## Health y Métricas
- `/health` sin autenticación para liveness probes.
- `/metrics` protegido por API Key para Prometheus (scrape vía sidecar/exporter si hace falta incluir header).

## Optimizaciones de Base de Datos
El dashboard incluye optimizaciones automáticas para SQLite:
- **PRAGMAs de rendimiento**: journal_mode=WAL, synchronous=NORMAL, temp_store=MEMORY, cache_size=10000, busy_timeout=30000
- **Índices automáticos**: sobre columnas críticas (pedidos.fecha_pedido, proveedores.activo, movimientos_stock.tipo_movimiento, etc.)
- **Estadísticas actualizadas**: ANALYZE ejecutado tras crear índices

Estas optimizaciones mejoran significativamente el rendimiento de consultas del dashboard sin configuración adicional.
