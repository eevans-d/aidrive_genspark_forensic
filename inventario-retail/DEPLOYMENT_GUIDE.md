# 🚀 Sistema Inventario Multi-Agente - Guía de Deployment

## 📋 Componentes del Sistema

### Servicios Principales
- **AgenteDepósito** (Puerto 8001) - Gestión ACID de stock y productos
- **AgenteNegocio** (Puerto 8002) - OCR, pricing y reglas de negocio  
- **ML Service** (Puerto 8003) - Predicciones y machine learning
- **Dashboard Web** (Puerto 8080) - Interfaz de usuario principal
- **Nginx** (Puerto 80/443) - Reverse proxy y load balancer

### Infraestructura
- **PostgreSQL** (Puerto 5432) - Base de datos principal
- **Redis** (Puerto 6379) - Cache y sessions

---

## 🛠️ Instalación y Deployment

### Prerrequisitos
```bash
# Docker & Docker Compose
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER

# Verificar instalación
docker --version
docker-compose --version
```

### Deployment Rápido

1. **Clonar y configurar**:
```bash
git clone <repo-url>
cd inventario-retail

# Configurar environment
cp .env.production.template .env.production
nano .env.production  # Editar valores reales
```

2. **Desplegar sistema completo**:
```bash
./scripts/deploy.sh --up
```

3. **Verificar estado**:
```bash
./scripts/deploy.sh --status
```

### URLs del Sistema
- Dashboard Principal: http://localhost
- API Depósito: http://localhost/api/deposito/
- API Negocio: http://localhost/api/negocio/  
- API ML: http://localhost/api/ml/

---

## 🔧 Gestión del Sistema

### Comandos Principales
```bash
# Verificar prerrequisitos
./scripts/deploy.sh --check

# Construir imágenes
./scripts/deploy.sh --build

# Levantar servicios
./scripts/deploy.sh --up

# Ver logs en tiempo real
./scripts/deploy.sh --logs

# Ver estado de servicios
./scripts/deploy.sh --status

# Reiniciar servicios
./scripts/deploy.sh --restart

# Detener servicios
./scripts/deploy.sh --down

# Backup de base de datos
./scripts/deploy.sh --backup

# Restaurar backup
./scripts/deploy.sh --restore backup_file.sql
```

### Monitoreo
```bash
# Ver logs específicos
docker-compose -f docker-compose.production.yml logs -f agente-deposito
docker-compose -f docker-compose.production.yml logs -f dashboard

# Acceder a contenedores
docker exec -it agente_deposito bash
docker exec -it inventario_retail_db psql -U postgres inventario_retail

# Ver métricas de recursos
docker stats
```

---

## ⚙️ Configuración de Producción

### Variables de Entorno Críticas
```bash
# Seguridad
JWT_SECRET_KEY=<256-bit-random-key>
POSTGRES_PASSWORD=<secure-password>
DASHBOARD_API_KEY=<api-key>

# CORS (restrictivo en producción)
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Base de datos
DATABASE_URL=postgresql://user:pass@postgres:5432/inventario_retail
```

### SSL/HTTPS (Producción)
```bash
# Obtener certificados SSL
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# El nginx.conf ya incluye configuración HTTPS
```

---

## 🛡️ Seguridad

### Autenticación JWT
- Todos los endpoints API están protegidos con JWT
- Roles: `admin`, `deposito`, `negocio`, `ml_service`
- Tokens expiran en 8 horas (configurable)

### API Keys
- Dashboard API protegido con `DASHBOARD_API_KEY`
- Header requerido: `X-API-Key: <your-key>`

### CORS
- Configurado restrictivamente en producción
- Solo orígenes autorizados en `CORS_ORIGINS`

---

## 📊 Monitoreo y Observabilidad

### Health Checks
```bash
# Verificar salud de todos los servicios
curl http://localhost/health
curl http://localhost:8001/health  # Agente Depósito
curl http://localhost:8002/health  # Agente Negocio
curl http://localhost:8003/health  # ML Service
curl http://localhost:8080/health  # Dashboard
```

### Logs
- Logs centralizados en `./logs/`
- Rotación automática diaria
- Formato JSON para parsing automático

### Métricas
- Métricas Prometheus en endpoints `/metrics`
- Grafana dashboard configurado (opcional)

---

## 🔄 Backup y Restore

### Backup Automático
```bash
# Backup manual
./scripts/deploy.sh --backup

# Programar backup diario (cron)
0 2 * * * /path/to/inventario-retail/scripts/deploy.sh --backup
```

### Restore
```bash
# Restaurar desde backup
./scripts/deploy.sh --restore backups/backup_20250101_020000.sql
```

---

## 🚨 Troubleshooting

### Problemas Comunes

**Servicios no inician**:
```bash
# Ver logs de error
docker-compose -f docker-compose.production.yml logs

# Verificar puertos ocupados
sudo netstat -tulpn | grep :8001
```

**Base de datos no conecta**:
```bash
# Verificar PostgreSQL
docker exec -it inventario_retail_db pg_isready -U postgres

# Ver logs de DB
docker logs inventario_retail_db
```

**JWT tokens inválidos**:
```bash
# Verificar JWT_SECRET_KEY en .env.production
# Regenerar tokens con nuevo secret
```

### Logs de Debug
```bash
# Habilitar debug logs
echo "LOG_LEVEL=DEBUG" >> .env.production
./scripts/deploy.sh --restart
```

---

## 📈 Escalado

### Horizontal Scaling
```bash
# Escalar servicios específicos
docker-compose -f docker-compose.production.yml up -d --scale agente-deposito=3
docker-compose -f docker-compose.production.yml up -d --scale agente-negocio=2
```

### Load Balancer
- Nginx configurado untuk load balancing automático
- Health checks y failover incluidos

---

## 🆙 Actualizaciones

### Rolling Updates
```bash
# Actualizar imagen específica
docker-compose -f docker-compose.production.yml pull agente-deposito
docker-compose -f docker-compose.production.yml up -d --no-deps agente-deposito

# Actualización completa
git pull
./scripts/deploy.sh --build
./scripts/deploy.sh --restart
```

---

## 📞 Contacto y Soporte

- **Documentación técnica**: Ver archivos en `/docs/`
- **APIs**: Swagger UI disponible en `/docs` de cada servicio
- **Logs**: Revisar `./logs/` para troubleshooting

**Estado del sistema**: ✅ Listo para producción