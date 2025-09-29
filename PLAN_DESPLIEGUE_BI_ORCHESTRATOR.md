# PLAN DE DESPLIEGUE - BUSINESS INTELLIGENCE ORCHESTRATOR
## Resultado de aplicar PROMPT 2 con GitHub Copilot Pro

---

## 1. PREPARACIÓN PRE-DESPLIEGUE

### Checklist de Verificación de Código
```bash
# Verificación de ambiente
- [ ] Python 3.11+ disponible
- [ ] Chrome/Chromium instalado y funcionando
- [ ] Selenium WebDriver configurado
- [ ] Proxy pools configurados (si aplica)
- [ ] PostgreSQL/MongoDB accesible
- [ ] OpenAI API key válida y con crédito
- [ ] Variables de entorno configuradas

# Tests y validación  
- [ ] Tests de scraping básico pasando
- [ ] Tests de análisis con IA funcionando
- [ ] Verificación de respeto a robots.txt
- [ ] Rate limiting implementado correctamente
- [ ] Proxy rotation funcionando (si aplica)

# Compliance y legal
- [ ] Configuración de rate limiting ético
- [ ] Respeto a robots.txt habilitado
- [ ] User agent rotation configurado
- [ ] Logs de compliance habilitados
```

### Configuraciones Específicas para Producción
```bash
# Environment setup
ENVIRONMENT=production
DEBUG=false
PYTHONPATH=/app/src

# Scraping configuration
MAX_CONCURRENT_REQUESTS=20
DOWNLOAD_DELAY=1
RESPECT_ROBOTS_TXT=true
HEADLESS_BROWSER=true

# AI Analysis
OPENAI_API_KEY=sk-tu-clave-produccion
AI_ANALYSIS_ENABLED=true
OPENAI_RATE_LIMIT_PER_MINUTE=60

# Database
DATABASE_URL=postgresql://user:pass@host:5432/bi_production
REDIS_URL=redis://:password@host:6379/1
```

---

## 2. ESTRATEGIA DE HOSTING PARA ARGENTINA

### Recomendación: Fly.io
**Plataforma elegida**: Fly.io

### Justificación Técnica
```
✅ Ideal para BI Orchestrator:
- Soporte excelente para aplicaciones Python
- Deploy cerca de Argentina (São Paulo)
- Scaling automático basado en demanda
- Soporte nativo para cron jobs
- Network privada entre servicios

✅ Para web scraping intensivo:
- CPU y memoria configurables
- Storage persistente para datos
- Logs centralizados y detallados
- IP rotation posible con múltiples regiones
```

### Configuración Paso a Paso

#### Paso 1: Preparar Aplicación
```bash
# Crear fly.toml
cat > fly.toml << 'EOF'
app = "bi-orchestrator-argentina"
primary_region = "gru"  # São Paulo (cerca de Argentina)

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PYTHONPATH = "/app/src"
  ENVIRONMENT = "production"
  
[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[[services]]
  http_checks = []
  internal_port = 8080
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

[[vm]]
  cpu_kind = "performance"
  cpus = 2
  memory_mb = 4096
EOF
```

#### Paso 2: Deploy en Fly.io
```bash
# Instalar flyctl
curl -L https://fly.io/install.sh | sh

# Login y configurar
flyctl auth login
flyctl launch

# Configurar secrets
flyctl secrets set OPENAI_API_KEY=sk-tu-clave-real
flyctl secrets set DATABASE_URL=tu-database-url
flyctl secrets set REDIS_URL=tu-redis-url

# Deploy
flyctl deploy
```

### Costos Estimados (USD/mes)
```
💰 Configuración Recomendada:
- 2 CPU Performance, 4GB RAM: ~$60/mes
- PostgreSQL (512MB): ~$15/mes  
- Redis (256MB): ~$10/mes
- Storage (10GB): ~$5/mes
- Bandwidth (100GB): Incluido

Total estimado: ~$90/mes

💡 Optimización costos:
- Usar auto-stop durante inactividad: -30%
- Configurar horarios de scraping específicos
- Implementar caching inteligente
```

---

## 3. PROCESO DE DESPLIEGUE DETALLADO

### Comandos Git Exactos
```bash
# 1. Preparar release
git checkout main
git pull origin main
git checkout -b release/bi-orchestrator-$(date +%Y%m%d)

# 2. Configurar producción
cp config/production.template.json config/production.json
# Editar config/production.json con valores reales

# 3. Validar configuración
python src/main.py --validate-config --env production

# 4. Tests completos
python -m pytest tests/ -v --env production

# 5. Build y deploy
flyctl deploy --remote-only
```

### Verificación Post-Despliegue
```bash
# URLs para testear
BASE_URL="https://bi-orchestrator-argentina.fly.dev"

# Health check
curl -f "$BASE_URL/health"

# API status
curl -f "$BASE_URL/api/status"

# Test scraping básico
curl -X POST "$BASE_URL/api/scrape/test" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

---

Este plan proporciona una estrategia completa de deployment para el sistema BI Orchestrator, optimizada para Argentina con Fly.io como plataforma de hosting recomendada.