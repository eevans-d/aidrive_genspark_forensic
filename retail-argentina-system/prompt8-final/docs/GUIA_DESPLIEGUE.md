# Guía de Despliegue - Sistema Retail Argentina

## Prerrequisitos

### Sistema Base
- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.25+ (para producción)
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Credenciales Requeridas
- Certificados AFIP (homologación/producción)
- CUIT de la empresa
- Claves AWS S3 (para backups)
- API Keys MercadoLibre (opcional)

## Instalación Rápida (Desarrollo)

### 1. Clonar y Configurar
```bash
git clone <repo-url> retail-argentina
cd retail-argentina

# Copiar plantilla de configuración
cp docker/.env.template .env

# Editar variables de entorno
vim .env
```

### 2. Variables de Entorno Críticas
```bash
# Base de datos
POSTGRES_PASSWORD=tu_password_seguro
REDIS_PASSWORD=tu_redis_password

# AFIP
AFIP_CUIT=20123456789
AFIP_ENVIRONMENT=testing  # o production

# Seguridad
JWT_SECRET_KEY=tu_clave_jwt_secreta_muy_larga
```

### 3. Levantar Servicios
```bash
# Desarrollo
docker-compose up -d

# Verificar servicios
docker-compose ps
curl http://localhost:8000/health
```

### 4. Inicializar Base de Datos
```bash
# Ejecutar migraciones
docker-compose exec agente-deposito alembic upgrade head

# Datos de prueba (opcional)
docker-compose exec agente-deposito python scripts/seed_data.py
```

## Despliegue en Producción

### 1. Preparar Certificados AFIP
```bash
# Crear directorio para certificados
mkdir -p certs/

# Copiar certificados AFIP
cp afip_prod.crt certs/afip.crt
cp afip_prod.key certs/afip.key

# Permisos restrictivos
chmod 600 certs/*
```

### 2. Configurar Kubernetes
```bash
# Crear namespace
kubectl apply -f k8s/00-namespace.yaml

# Configurar secrets
kubectl create secret generic retail-secrets \
  --from-literal=POSTGRES_PASSWORD=tu_password \
  --from-literal=REDIS_PASSWORD=tu_redis_password \
  --from-literal=JWT_SECRET_KEY=tu_jwt_key \
  --namespace=retail-argentina

# Certificados AFIP
kubectl create secret generic afip-certificates \
  --from-file=afip.crt=certs/afip.crt \
  --from-file=afip.key=certs/afip.key \
  --namespace=retail-argentina
```

### 3. Desplegar Infraestructura
```bash
# Base de datos y cache
kubectl apply -f k8s/02-postgres.yaml
kubectl apply -f k8s/03-redis.yaml

# Esperar a que estén listos
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s -n retail-argentina
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s -n retail-argentina
```

### 4. Desplegar Aplicaciones
```bash
# Microservicios
kubectl apply -f k8s/04-microservices.yaml

# API Gateway y UI
kubectl apply -f k8s/05-gateway.yaml

# Verificar despliegue
kubectl get pods -n retail-argentina
```

### 5. Configurar Ingress/Load Balancer
```bash
# NGINX Ingress
kubectl apply -f k8s/06-ingress.yaml

# Verificar acceso externo
curl https://retail.tu-dominio.com/health
```

## Configuración de Certificados SSL

### Let's Encrypt con cert-manager
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: retail-tls
  namespace: retail-argentina
spec:
  secretName: retail-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - retail.tu-dominio.com
```

## Monitoreo y Observabilidad

### 1. Desplegar Prometheus
```bash
# Agregar Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Instalar stack de monitoreo
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values monitoring/prometheus-values.yaml
```

### 2. Configurar Dashboards Grafana
```bash
# Importar dashboards personalizados
kubectl apply -f monitoring/grafana/dashboards/
```

### 3. Alertas
```bash
# Configurar alertas críticas
kubectl apply -f monitoring/alerts/
```

## Backup y Recuperación

### 1. Configurar Backup Automático
```bash
# Desplegar servicio de backup
kubectl apply -f backup_automation/k8s-backup.yaml

# Verificar cronjobs
kubectl get cronjobs -n retail-argentina
```

### 2. Restauración Manual
```bash
# Restaurar base de datos
kubectl exec -it postgres-pod -- \
  psql -U retail_user -d retail_argentina < backup.sql

# Verificar integridad
kubectl exec -it agente-deposito-pod -- \
  python scripts/verify_data.py
```

## Procedimientos de Actualización

### Rolling Update
```bash
# Actualizar imagen
kubectl set image deployment/agente-deposito \
  agente-deposito=retail-argentina/agente-deposito:v2.0 \
  -n retail-argentina

# Verificar rollout
kubectl rollout status deployment/agente-deposito -n retail-argentina
```

### Rollback
```bash
# Rollback en caso de problemas
kubectl rollout undo deployment/agente-deposito -n retail-argentina
```

## Verificación Post-Despliegue

### 1. Health Checks
```bash
# Verificar todos los servicios
curl https://retail.tu-dominio.com/health

# Específicos por servicio
curl https://retail.tu-dominio.com/deposito/health
curl https://retail.tu-dominio.com/negocio/health
curl https://retail.tu-dominio.com/ml/health
```

### 2. Tests de Integración
```bash
# Ejecutar suite de tests
kubectl exec -it agente-deposito-pod -- \
  python -m pytest tests/integration/

# Test AFIP
curl -X POST https://retail.tu-dominio.com/afip/test \
  -H "Content-Type: application/json" \
  -d '{"cuit":"20123456789"}'
```

### 3. Verificar Métricas
```bash
# Acceder a Grafana
kubectl port-forward service/prometheus-grafana 3000:80 -n monitoring

# Verificar dashboards en http://localhost:3000
```

## Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión a Base de Datos
```bash
# Verificar pod PostgreSQL
kubectl logs postgres-pod -n retail-argentina

# Verificar conectividad
kubectl exec -it agente-deposito-pod -- \
  pg_isready -h postgres-service -p 5432
```

#### 2. Error de Certificados AFIP
```bash
# Verificar montaje de certificados
kubectl exec -it agente-negocio-pod -- \
  ls -la /app/certs/

# Verificar permisos
kubectl exec -it agente-negocio-pod -- \
  openssl x509 -text -noout -in /app/certs/afip.crt
```

#### 3. Performance Issues
```bash
# Verificar recursos
kubectl top pods -n retail-argentina

# Escalar horizontalmente
kubectl scale deployment/agente-deposito --replicas=3 -n retail-argentina
```

### Logs Centralizados
```bash
# Ver logs agregados
kubectl logs -f deployment/agente-deposito -n retail-argentina

# Filtrar por nivel
kubectl logs deployment/agente-deposito -n retail-argentina | grep ERROR
```

## Seguridad en Producción

### 1. Network Policies
```bash
# Aplicar políticas de red
kubectl apply -f security/network-policies/
```

### 2. Pod Security Standards
```bash
# Configurar PSS
kubectl label namespace retail-argentina \
  pod-security.kubernetes.io/enforce=restricted
```

### 3. RBAC
```bash
# Aplicar roles y permisos
kubectl apply -f security/rbac/
```

## Procedimientos de Mantenimiento

### 1. Actualizaciones de Seguridad
```bash
# Escanear vulnerabilidades
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image retail-argentina/agente-deposito:latest

# Actualizar imágenes base
docker build --no-cache -t retail-argentina/agente-deposito:latest .
```

### 2. Limpieza de Recursos
```bash
# Limpiar imágenes antiguas
docker image prune -a

# Limpiar backups antiguos
python backup_automation/backup_manager.py cleanup
```

### 3. Optimización de Performance
```bash
# Analizar métricas
kubectl exec -it prometheus-pod -- \
  promtool query instant 'rate(http_requests_total[5m])'

# Optimizar consultas DB
kubectl exec -it postgres-pod -- \
  psql -c "EXPLAIN ANALYZE SELECT * FROM stock WHERE quantity < reorder_point;"
```

## Contacto y Soporte

Para soporte técnico y consultas sobre el despliegue:
- Email: soporte@retail-argentina.com
- Documentación: https://docs.retail-argentina.com
- Issues: https://github.com/retail-argentina/issues

---

**Nota**: Esta guía asume familiaridad con Docker, Kubernetes y conceptos de DevOps. Para instalaciones en entornos específicos, consultar la documentación adicional en `/docs/`.
