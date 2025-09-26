# 📘 Guía Extendida Staging → Producción (Dashboard)

Este documento complementa `README_DEPLOY_STAGING.md` sin modificarlo. Aquí se concentran los elementos operativos ampliados: matriz de variables, checklist integral, política DO/DON'T, rollback rápido, smoke test dedicado, métricas iniciales y roadmap post Go-Live.

> Nota: Mientras esté vigente el plan de hardening, no renombrar directorios ni introducir cambios estructurales; cualquier refactor se pospone post Go-Live.

---
## 1. Resumen rápido (Contexto actual)
- Cobertura dashboard: 86% (objetivo ≥85% cumplido)
- Tests legacy aislados / filtrados
- CSP bloqueada (cambios requieren actualización test + doc)
- Próxima fase inmediata: provisión de secretos Staging + smoke automation

---
## 2. Matriz extendida de variables (Staging vs Producción)
| Variable | Staging (ejemplo) | Producción (política) | Rotación | Notas |
|----------|-------------------|------------------------|----------|-------|
| DASHBOARD_API_KEY | aleatoria 32+ chars | aleatoria 40+ chars | 30 días | Protege `/api/*` y `/metrics` |
| DASHBOARD_UI_API_KEY | (opcional) igual o distinta | Distinta a API_KEY | 30 días | Sólo si el frontend llama API |
| DASHBOARD_RATELIMIT_ENABLED | true | true | N/A | Nunca desactivar en Prod salvo P1 |
| DASHBOARD_RATELIMIT_MAX | 600 | 600 (ajustable) | Trimestral | Ajustar tras métricas reales |
| DASHBOARD_ALLOWED_HOSTS | * (inicio) | dominio final | Pre-Go-Live | Restringir antes de exponer |
| DASHBOARD_ENABLE_HSTS | false | true | N/A | Activar tras TLS estable |
| DASHBOARD_FORCE_HTTPS | false | true | N/A | Requiere proxy TLS delante |
| DASHBOARD_LOG_LEVEL | INFO | INFO / WARNING | Mensual | Reducir ruido si es alto |
| DASHBOARD_LOG_DIR | /app/logs | /var/log/dashboard | N/A | Volumen persistente en Prod |
| DASHBOARD_LOG_BACKUP_COUNT | 7 | 14 | Semestral | Política retención |
| DASHBOARD_CORS_ORIGINS | (vacío) | Lista explícita | Antes de UI pública | No usar `*` |

---
## 3. Checklist Operativo Staging → Producción
### A. Preparación
1. [ ] Secretos Staging cargados y verificados en CI
2. [ ] `pytest tests/web_dashboard -q` verde
3. [ ] Cobertura ≥85% (actual 86%)
4. [ ] Imagen `latest` en GHCR disponible
5. [ ] Revisión CSP sin cambios accidentales
6. [ ] Dominio final y certificado listos (si aplica)

### B. Validación en Staging
1. [ ] `/health` → healthy
2. [ ] `/metrics` counters incrementan
3. [ ] `/api/summary` 401 sin API Key
4. [ ] `/api/summary` 200/500 con API Key válida
5. [ ] Logs JSON incluyen `request_id`
6. [ ] 50 llamadas rápidas no gatillan rate limit
7. [ ] Export CSV `/api/export/summary.csv` → 200

### C. Pre-Go-Live
1. [ ] Ajustar `DASHBOARD_ALLOWED_HOSTS` → dominio real
2. [ ] Activar `DASHBOARD_FORCE_HTTPS` + `DASHBOARD_ENABLE_HSTS`
3. [ ] Generar API Key Producción distinta a Staging
4. [ ] Etiquetar `v1.0.0-rc1` y desplegar
5. [ ] Ensayar rollback (ver sección Rollback) OK
6. [ ] Etiquetar y desplegar `v1.0.0`

---
## 4. Política DO / DON'T
**DO:**
- Añadir test antes de cambiar rutas críticas
- Documentar cambios en headers de seguridad
- Rotar API Keys según matriz
- Revisar ratio errores tras cada deploy

**DON'T:**
- Renombrar directorios con guiones antes Go-Live
- Introducir dependencias sin justificación y ticket
- Desactivar rate limiting en Prod (salvo incidente P1)
- Ampliar caching sin datos de latencia previos

**“DONES” (criterios de corte):**
- Cobertura >85% suficiente (no perseguir >88% ahora)
- Warnings coverage por path (import) diferidos
- Ramas de error DB improbables no se fuerzan con mocks destructivos

---
## 5. Rollback Rápido (≤5 min)
Escenario: Tag `v1.0.0` genera aumento anómalo de 5xx.

1. Identificar tag estable previo (ej: `v1.0.0-rc1`)
2. Redeploy remoto:
```bash
ssh $STAGING_USER@$STAGING_HOST \
  "cd ~/minimarket-deploy && export IMAGE_TAG=v1.0.0-rc1 && \
   docker compose -f docker-compose.dashboard.yml pull && \
   docker compose -f docker-compose.dashboard.yml up -d"
```
3. Validar `docker ps` (imagen/tag correcto)
4. Consultar `/metrics` y confirmar descenso de errores
5. Registrar incidente en `RUNBOOK_OPERACIONES_DASHBOARD.md`

**Plan B:**
```bash
docker run --rm -p 8080:8080 ghcr.io/<org>/dashboard:v1.0.0-rc1
```

---
## 6. Smoke Test Dashboard (mínimo)
Script sugerido (`scripts/smoke_dashboard_staging.sh`):
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/health -H "X-API-Key:$DASHBOARD_API_KEY"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/api/summary               # 401
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/api/summary -H "X-API-Key:$DASHBOARD_API_KEY"  # 200/500
curl -s http://localhost:8080/metrics -H "X-API-Key:$DASHBOARD_API_KEY" | grep dashboard_requests_total
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/api/export/summary.csv -H "X-API-Key:$DASHBOARD_API_KEY"
```
**Extendido opcional:** medir latencia media (curl repetido + `time`), añadir chequeo de `X-Request-ID`.

---
## 7. Métricas a Observar (primeros 15 min post deploy)
| Métrica | Fuente | Umbral inicial |
|---------|--------|----------------|
| errores_total / requests_total | /metrics | >2% sostenido |
| p95 duration_ms | logs JSON | >800ms |
| Conteo por path | /metrics | Picos anómalos (ataque / abuso) |
| Uptime segundos | /metrics | Creciendo (no resets inesperados) |

---
## 8. Roadmap Post-Go-Live (Parking Lot)
- Empaquetar módulo (eliminar carga dinámica y warning coverage)
- Cliente Prometheus oficial (histogram latencias)
- Rotación automática de API Key (Action programada)
- Prueba de carga ligera (hey / k6) + baseline
- Pydantic Settings + validación estructurada `.env`
- Alertas simples (GitHub Actions + curl /metrics + grep > threshold)

---
## 9. Referencias Cruzadas
| Tema | Documento principal |
|------|----------------------|
| Despliegue base | `README_DEPLOY_STAGING.md` |
| CI/CD detalles | `DOCUMENTACION_CI_CD.md` |
| Runbook / Incidentes | `RUNBOOK_OPERACIONES_DASHBOARD.md` |
| Seguridad / CSP | Tests + `DOCUMENTACION_DASHBOARD_WEB_COMPLETO.md` |

## 10. Notas Finales
Esta guía se mantiene “extendida” para no sobrecargar el README base. Cualquier cambio operativo aprobado debe reflejarse aquí y luego condensarse en el runbook.

## 11. Plantilla comandos carga de secretos (Staging / Producción)

### Staging
```bash
gh secret set STAGING_HOST -R eevans-d/aidrive_genspark_forensic --body "staging.example.com"
gh secret set STAGING_USER -R eevans-d/aidrive_genspark_forensic --body "deploy"
gh secret set STAGING_KEY -R eevans-d/aidrive_genspark_forensic < /ruta/clave_staging.pem
gh secret set STAGING_GHCR_TOKEN -R eevans-d/aidrive_genspark_forensic --body "<ghcr_pat_read_packages>"
# API Key (generar y subir)
./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic --print-only
./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic
# UI opcional
./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic -u "$(openssl rand -hex 32)"
```

### Producción (NO ejecutar hasta aprobado)
```bash
gh secret set PROD_HOST -R eevans-d/aidrive_genspark_forensic --body "prod.example.com"
gh secret set PROD_USER -R eevans-d/aidrive_genspark_forensic --body "deploy"
gh secret set PROD_KEY -R eevans-d/aidrive_genspark_forensic < /ruta/clave_prod.pem
gh secret set PROD_GHCR_TOKEN -R eevans-d/aidrive_genspark_forensic --body "<ghcr_pat_read_packages>"
# API Key prod (simular primero)
./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic --prod --print-only
./scripts/rotate_dashboard_api_key.sh -r eevans-d/aidrive_genspark_forensic --prod
```

Verificación:
```bash
gh secret list -R eevans-d/aidrive_genspark_forensic | grep -E 'STAGING_|PROD_'
```

## 12. Verificación rápida post-deploy (script)
Para evaluar rápidamente errores y p95 tras el despliegue usa:
```bash
scripts/check_metrics_dashboard.sh -u https://staging.example.com -k "$STAGING_DASHBOARD_API_KEY"
```
Retornos:
- Código 0: dentro de umbrales
- Código 5: error % supera umbral (default 2%)

Parámetros opcionales:
```bash
scripts/check_metrics_dashboard.sh -u <URL> -k <API_KEY> -t 3
```

## 13. Procedimiento Tagging RC y Release Final
1. Cargar y verificar secretos Staging (ver sección 11).
2. Push a `master` y esperar deploy automático + smoke ✅.
3. Verificar métricas: error% <2, p95 <800ms.
3.1 Verificar headers seguridad:
```bash
scripts/check_security_headers.sh -u https://staging.example.com
```
Si staging ya está detrás de HTTPS y HSTS activado:
```bash
scripts/check_security_headers.sh -u https://staging.example.com --expect-hsts
```
4. Crear tag RC:
```bash
scripts/preflight_rc.sh -u https://staging.example.com -k $STAGING_DASHBOARD_API_KEY
git tag v1.0.0-rc1
git push origin v1.0.0-rc1
```
5. Esperar deploy production (si pipeline configurado para tags RC) o validar manual si sólo aplica a final.
6. Ventana de observación mínima sugerida: 30-60 min tráfico real.
7. Si estable, crear tag final:
```bash
git tag v1.0.0
git push origin v1.0.0
```
8. Registrar en `RUNBOOK_OPERACIONES_DASHBOARD.md` fecha/hora y métricas iniciales.

Nota: No introducir cambios de código entre `-rc1` y `v1.0.0` salvo fix crítico + nuevo `-rc2`.

---
Última actualización: 2025-09-26
