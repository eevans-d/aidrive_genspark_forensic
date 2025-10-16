# 🤝 Handover Documentation - Mini Market Dashboard

**Fecha de Entrega:** 16 de octubre de 2025  
**Versión:** 1.0.0 (Production Ready)  
**Preparado por:** ETAPA 3 Development Team  
**Para:** Equipo de Operaciones y Mantenimiento

---

## 📋 Quick Start para Ops

### Acceso Inicial

```bash
# 1. Clonar repositorio
git clone https://github.com/eevans-d/aidrive_genspark_forensic.git
cd aidrive_genspark_forensic

# 2. Configurar environment
cp inventario-retail/.env.example inventario-retail/.env.production
# → Editar con valores de producción

# 3. Levantar servicios
cd inventario-retail
docker-compose -f docker-compose.production.yml up -d

# 4. Verificar salud
curl http://localhost:8080/health

# 5. Acceder a dashboard
# Abrir: http://minimarket.local:8080
```

### Credenciales y Secretos

| Item | Ubicación | Responsabilidad |
|------|-----------|-----------------|
| DASHBOARD_API_KEY | `.env.production` | Rotación anual |
| DATABASE_ENCRYPTION_KEY | `.env.production` | Nunca compartir vía chat |
| TLS Certificates | `observability/prometheus/tls/` | Renovar 30 días antes vencimiento |
| SSH Keys | Password manager corporativo | Never in Git |
| AWS/S3 Keys | `.env.production` | Rotación trimestral |

---

## 🏗️ Arquitectura en 5 Minutos

```
┌─────────────────────────────────────────────────────────┐
│                      NGINX (Puerto 80/443)              │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │        Dashboard Web (Python FastAPI)            │  │
│  │  • GraphQL/REST APIs                              │  │
│  │  • Rate limiting, CORS, Security headers         │  │
│  │  • Prometheus metrics exposition                 │  │
│  └──────────────────────────────────────────────────┘  │
│          ↓ RPC              ↓ RPC                       │
│  ┌──────────────┐    ┌──────────────┐                 │
│  │  Agente      │    │  Agente      │                 │
│  │  Depósito    │    │  Negocio     │                 │
│  │  (Puerto     │    │  (Puerto     │                 │
│  │   8001)      │    │   8002)      │                 │
│  └──────────────┘    └──────────────┘                 │
│          ↓ DBAPI             ↓ DBAPI                   │
│  ┌────────────────────────────────────┐              │
│  │      PostgreSQL (Puerto 5432)      │              │
│  │  • AES-256 encryption at rest      │              │
│  │  • Audit logging enabled           │              │
│  │  • Backup cron job                 │              │
│  └────────────────────────────────────┘              │
│                                                        │
│  ┌────────────────────────────────────┐              │
│  │      Redis Cache (Puerto 6379)     │              │
│  │  • Session storage                 │              │
│  │  • Query results cache             │              │
│  └────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘
       ↓                                    ↓
  ┌──────────────┐                  ┌──────────────┐
  │ Prometheus   │                  │  Alertmanager│
  │ (9090)       │                  │   (9093)     │
  │ [Métricas]   │                  │ [Alerts]     │
  └──────────────┘                  └──────────────┘
       ↓                                    ↓
  ┌──────────────┐                  ┌──────────────┐
  │  Grafana     │                  │   Loki       │
  │  (3000)      │                  │  (3100)      │
  │ [Dashboards] │                  │  [Logs]      │
  └──────────────┘                  └──────────────┘
```

**Componentes Críticos:**
- 🔴 **Dashboard:** Sin esto, usuarios no ven nada
- 🔴 **PostgreSQL:** Pérdida = pérdida total de datos
- 🟡 **Redis:** Sin cache, lentitud, pero funciona
- 🟡 **Observability:** Sin métricas, no sabemos si hay problema

---

## ✅ Pre-Entrega Checklist

### Acceso Configurado

- [ ] SSH key para deploy agregada a servidor production
- [ ] Credenciales de GitHub compartidas (deploy key)
- [ ] Variables de entorno `.env.production` generadas
- [ ] API Keys rotadas y documentadas
- [ ] Database user/password configurado
- [ ] TLS certificates en lugar correcto

### Servicios Validados

- [ ] `docker-compose ps` muestra todos servicios UP
- [ ] `curl http://localhost:8080/health` retorna 200 OK
- [ ] `curl http://localhost/api/inventory` retorna datos
- [ ] `curl http://localhost/metrics` retorna Prometheus metrics
- [ ] Dashboard accesible vía navegador

### Monitoreo Configurado

- [ ] Prometheus scrapeando todas las targets
- [ ] Alertas firing en Alertmanager
- [ ] Grafana dashboards mostrando datos
- [ ] Logs apareciendo en Loki
- [ ] Backup cron job ejecutándose diariamente

### Documentación Revisada

- [ ] DEPLOYMENT_GUIDE.md leído y entendido
- [ ] OPERATIONS_RUNBOOK.md accessible para equipo
- [ ] TLS_SETUP.md procedimientos conocidos
- [ ] DATA_ENCRYPTION.md y key rotation entendidos
- [ ] LOAD_TESTING.md y SLO targets compartidos

### Permisos Asignados

- [ ] On-call engineer tiene PagerDuty access
- [ ] Equipo ops tiene acceso a GitHub repo
- [ ] Access a servidor staging y production
- [ ] Slack channels creados (#minimarket-ops, #minimarket-emergencies)
- [ ] Contactos de escalamiento documentados

---

## 📚 Documentación Principal

### Para Comenzar

1. **DEPLOYMENT_GUIDE.md** (1,100+ líneas)
   - Arquitectura completa
   - Procedimientos deployment
   - Troubleshooting by symptom
   - TLS setup y renovación
   - Data encryption procedures
   - Load testing integration

2. **OPERATIONS_RUNBOOK.md** (650+ líneas)
   - Procedimientos de emergencia (< 5 min response)
   - Playbooks por tipo de incidente
   - Escalamiento y contactos
   - Daily health checks
   - Disaster recovery procedures

3. **GUIA_USUARIO_DASHBOARD.md** (Expanded)
   - Cómo usar el dashboard
   - Filtros y búsqueda
   - Exportación de datos
   - Métricas explicadas
   - FAQ completo

### Para Profundizar

| Documento | Propósito | Audiencia |
|-----------|-----------|-----------|
| TLS_SETUP.md | Configuración TLS/mTLS | DevOps, Security |
| DATA_ENCRYPTION.md | Implementación AES-256 | DBA, Security |
| LOAD_TESTING.md | Suite de performance | QA, DevOps |
| README_DEPLOY_STAGING.md | Staging deployment | DevOps |
| CHANGELOG.md | Historia de versiones | PMs, Leads |

### Ubicación en Repo

```
inventario-retail/
├── DEPLOYMENT_GUIDE.md           ← LÉEME PRIMERO
├── OPERATIONS_RUNBOOK.md         ← Para emergencias
├── HANDOVER.md                   ← Estás aquí
├── security/
│   ├── TLS_SETUP.md
│   └── DATA_ENCRYPTION.md
├── scripts/load_testing/
│   ├── LOAD_TESTING.md
│   ├── test-*.js
│   └── run-all.sh
├── observability/
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── tls/
│   ├── grafana/
│   │   └── dashboards/
│   └── loki/
├── database/
│   └── migrations/
│       ├── 004_add_encryption.sql
│       └── 004_add_encryption_rollback.sql
└── docker-compose.production.yml
```

---

## 🔐 Secretos y Configuración

### Variables de Entorno Requeridas

```bash
# .env.production template

# Dashboard
DASHBOARD_API_KEY=<64-char-hex-key>           # Cambiar en producción
DASHBOARD_ENABLE_HSTS=true
DASHBOARD_FORCE_HTTPS=true
DASHBOARD_RATELIMIT_ENABLED=true

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/inventario_retail
DATABASE_ENCRYPTION_KEY=<64-char-hex-key>      # Jamás compartir
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=10

# Observability
PROMETHEUS_RETENTION=30d
ALERTMANAGER_SLACK_WEBHOOK=<webhook-url>
GRAFANA_ADMIN_PASSWORD=<strong-password>

# AWS/Backups (si aplica)
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
S3_BACKUP_BUCKET=minimarket-backups
```

### Generación de API Key

```bash
# Generar nueva API Key (64 caracteres hex)
openssl rand -hex 32

# Guardar en:
# 1. .env.production como DASHBOARD_API_KEY
# 2. Password manager corporativo
# 3. Comunicar a usuarios que requieran acceso API
```

### Rotación de Secrets

| Secret | Frecuencia | Procedimiento |
|--------|-----------|---------------|
| API Key | Semestral | Generate new, update env, restart dashboard |
| Database Password | Anual | Change in postgres, update .env.production |
| TLS Certs | Anual (o 30d antes vencimiento) | `./generate_certs.sh`, restart observability |
| Database Encryption Key | Nunca (imposible rotation) | Plan antes de usar |

---

## 🚨 Incidentes Críticos - Respuesta Rápida

### Si no puedo acceder al dashboard

```bash
# 1. ¿Servicios están UP?
docker-compose -f docker-compose.production.yml ps

# 2. Reinicia
docker-compose -f docker-compose.production.yml restart dashboard

# 3. Si sigue no funcionando → Ver OPERATIONS_RUNBOOK.md § P1
```

### Si datos están cifrados pero clave falta

```bash
# ⚠️ NO HACERLO SIN ARQUITECTO PRESENTE

# La clave de encriptación NO tiene recovery
# Si perdida:
# - Option A: Restaurar backup pre-encriptado
# - Option B: Aceptar pérdida de esos datos encriptados
# - Option C: Cambiar clave (pero datos viejos inutilizable)
```

### Si hay alerta de memoria

```bash
# Seguir OPERATIONS_RUNBOOK.md § PB3: Uso de Memoria Alto
# Resumen:
# 1. Reiniciar servicios (libera memoria)
# 2. Aumentar Docker memory limits si es crónico
# 3. Revisar código si memory leak persistente
```

---

## 📊 Métricas Clave a Monitorear

### SLO Targets (Service Level Objectives)

```
Métrica                    Objetivo    Acción si falla
─────────────────────────────────────────────────────
P95 Latency                < 300ms     Paging ops
Error Rate                 < 0.5%      Paging ops
Database CPU               < 70%       Investigate queries
Memory Usage               < 80%       Alert on-call
Uptime                     > 99.5%     Postmortem
```

### Dashboards en Grafana

1. **Mini Market Overview**
   - Request rates, latencies, errors
   - Database connections, slow queries
   - Redis hit rate, evictions

2. **Infrastructure**
   - CPU, Memory, Disk I/O por contenedor
   - Network I/O
   - Docker stats

3. **Business Metrics**
   - Total inventory value
   - Rotation rates
   - Provider performance
   - Top products by revenue

---

## 👥 Team Roles y Responsabilidades

### DevOps/Infrastructure Engineer

**Responsabilidades:**
- Mantener servicios UP
- Monitorear recursos
- Deployments y rollbacks
- TLS certificate renewal (antes 30 días vencimiento)
- Backup integrity checks (semanal)

**Escalada:**
- P1 (servicios down) → Immediate
- P2 (degraded performance) → 15 min
- P3 (non-critical issues) → Next business day

### DBA / Database Specialist

**Responsabilidades:**
- Optimize slow queries
- Database backups y recovery drills
- Encryption key management (documentation)
- Performance tuning
- Migration scripts testing

**Contacto:** Para issues with `DATABASE_ENCRYPTION_KEY` o encrypted data access

### Application Developer

**Responsabilidades:**
- Monitor application logs
- Investigate 5XX errors
- API performance profiling
- Dependency updates (security patches)

**NO es responsable:** Infrastructure, certificates, database backups

---

## 🔄 Maintenance Windows

### Tipo 1: Patches de Seguridad (< 5 min downtime)

```
1. Verificar que release está en GHCR
2. `docker-compose pull`
3. `docker-compose -f docker-compose.production.yml up -d`
4. Verificar endpoints responden
5. Monitorear 5 minutos
```

### Tipo 2: Database Migration (5-30 min downtime)

```
1. Backup actual (full, no incremental)
2. Notificar usuarios: "maintenance window 2-2:30 PM"
3. Stop dashboard y agentes
4. Run migration: psql -f migration.sql
5. Verify: SELECT COUNT(*) FROM products;
6. Start servicios
7. Test endpoints
8. Post-incident: check backups worked
```

### Tipo 3: TLS Certificate Renewal (0 min downtime)

```
1. Generar nuevos certs: ./generate_certs.sh
2. Verificar: openssl verify
3. Copiar a docker mounts
4. Restart containers: docker-compose restart prometheus alertmanager
5. Verify: curl --cacert test TLS
```

---

## 📞 Contactos y Escalamiento

### Slack Channels

| Channel | Propósito |
|---------|-----------|
| #minimarket-ops | Planificación, cambios, mantenimiento |
| #minimarket-emergencies | Incidentes P1/P2 24/7 |
| #minimarket-dashboard | Uso del dashboard, reportes |

### Contactos Directos

```
Director de Operaciones: <nombre> - <email> - <cel>
On-Call Engineer (rotativo):
  - Lunes-Viernes: <persona semanal>
  - Fines de semana: <persona en turno>
DBA Especialista: <nombre> - <email>
Lead Técnico: <nombre> - <email>
```

---

## 🚀 Próximos Pasos (Post-Handover)

### Week 1: Estabilización

- [ ] Equipo ops familiarizado con OPERATIONS_RUNBOOK
- [ ] Health checks ejecutándose correctamente
- [ ] Backups validados (restore test)
- [ ] TLS certs alarmados para vencimiento

### Week 2: Optimización

- [ ] Load testing suite ejecutada
- [ ] SLO targets baseline estabelecidos
- [ ] Grafana dashboards finalizados
- [ ] Alertas calibradas (reducir false positives)

### Month 1: Automatización

- [ ] Backup cron job hardened
- [ ] Certificate renewal automatizado
- [ ] Health checks en Kubernetes (si migramos)
- [ ] Disaster recovery drill ejecutado

---

## 📋 Sign-Off

```
Preparado por:       [ETAPA 3 Dev Team]
Revisado por:        [Lead Técnico]
Aceptado por:        [Director de Operaciones]

Fecha de Handover:   16 de octubre de 2025
Versionado en Git:   commit <hash>
Ambiente:            Production
Status:              ✅ READY FOR PRODUCTION
```

---

**Documento confidencial - Solo para equipo de Operaciones**  
**Para soporte técnico, ver OPERATIONS_RUNBOOK.md**  
**Para uso del sistema, ver GUIA_USUARIO_DASHBOARD.md**
