# TLS Setup para Prometheus y Alertmanager

## Índice
- [Introducción](#introducción)
- [Arquitectura de Seguridad](#arquitectura-de-seguridad)
- [Generación de Certificados](#generación-de-certificados)
- [Configuración de Prometheus](#configuración-de-prometheus)
- [Configuración de Alertmanager](#configuración-de-alertmanager)
- [Despliegue con Docker Compose](#despliegue-con-docker-compose)
- [Verificación](#verificación)
- [Troubleshooting](#troubleshooting)
- [Renovación de Certificados](#renovación-de-certificados)
- [Mejores Prácticas](#mejores-prácticas)

---

## Introducción

Este documento describe la configuración de TLS (Transport Layer Security) para asegurar las comunicaciones entre Prometheus y Alertmanager en el sistema Mini Market.

### ¿Por Qué TLS?

- **Confidencialidad**: Encripta los datos en tránsito
- **Integridad**: Previene modificación de datos
- **Autenticación**: Verifica la identidad de los servicios
- **Compliance**: Cumple con mejores prácticas de seguridad

### Alcance

Esta configuración cubre:
- ✅ Comunicación Prometheus → Alertmanager (HTTPS)
- ✅ Autenticación mutua con certificados cliente/servidor
- ✅ Validación de certificados con CA propia

**NO cubre** (por ahora):
- ❌ TLS para scraping de métricas de servicios
- ❌ TLS para Grafana → Prometheus
- ❌ Certificados firmados por CA pública

---

## Arquitectura de Seguridad

```
┌─────────────────┐                    ┌──────────────────┐
│   Prometheus    │◄──── TLS/HTTPS ───►│  Alertmanager    │
│                 │     (port 9093)    │                  │
│  - Client cert  │                    │  - Server cert   │
│  - Client key   │                    │  - Server key    │
│  - CA cert      │                    │  - CA cert       │
└─────────────────┘                    └──────────────────┘
         │                                      │
         └──────────── Ambos confían ──────────┘
                       en la misma CA
```

### Flujo de Autenticación

1. **Prometheus** inicia conexión HTTPS a **Alertmanager**
2. **Alertmanager** presenta su certificado servidor
3. **Prometheus** verifica certificado usando CA
4. **Alertmanager** solicita certificado cliente
5. **Prometheus** presenta su certificado cliente
6. **Alertmanager** verifica certificado cliente usando CA
7. Conexión TLS establecida ✅

---

## Generación de Certificados

### Ubicación de Archivos

```
inventario-retail/observability/prometheus/tls/
├── generate_certs.sh       # Script de generación
├── ca.crt                  # Certificado de CA
├── ca.key                  # Clave privada de CA (NO committear)
├── prometheus.crt          # Certificado de Prometheus
├── prometheus.key          # Clave privada de Prometheus (NO committear)
├── alertmanager.crt        # Certificado de Alertmanager
└── alertmanager.key        # Clave privada de Alertmanager (NO committear)
```

### Generar Certificados

```bash
cd inventario-retail/observability/prometheus/tls
./generate_certs.sh
```

**Output esperado:**
```
=========================================
   Generador de Certificados TLS        
=========================================
1. Generando Certificate Authority (CA)...
✅ CA generada exitosamente
2. Generando certificado para Prometheus...
✅ Certificado de Prometheus generado
3. Generando certificado para Alertmanager...
✅ Certificado de Alertmanager generado
=========================================
Válidos por: 365 días
Expiración: 2026-10-16
```

### Verificar Certificados

```bash
# Verificar certificado de Prometheus
openssl x509 -in prometheus.crt -text -noout

# Verificar certificado de Alertmanager
openssl x509 -in alertmanager.crt -text -noout

# Verificar firma con CA
openssl verify -CAfile ca.crt prometheus.crt
openssl verify -CAfile ca.crt alertmanager.crt
```

---

## Configuración de Prometheus

### Archivo: `prometheus_tls.yml`

Cambios clave respecto a `prometheus.yml`:

```yaml
# Antes (sin TLS):
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Después (con TLS):
alerting:
  alertmanagers:
    - scheme: https              # ← HTTPS en lugar de HTTP
      tls_config:
        ca_file: /etc/prometheus/tls/ca.crt
        cert_file: /etc/prometheus/tls/prometheus.crt
        key_file: /etc/prometheus/tls/prometheus.key
        insecure_skip_verify: false  # ← Verifica certificado
      static_configs:
        - targets:
            - alertmanager:9093
```

### Parámetros TLS

| Parámetro | Descripción | Valor |
|-----------|-------------|-------|
| `scheme` | Protocolo de comunicación | `https` |
| `ca_file` | Certificado de CA para verificar servidor | `/etc/prometheus/tls/ca.crt` |
| `cert_file` | Certificado cliente de Prometheus | `/etc/prometheus/tls/prometheus.crt` |
| `key_file` | Clave privada cliente de Prometheus | `/etc/prometheus/tls/prometheus.key` |
| `insecure_skip_verify` | ¿Omitir verificación de certificado? | `false` (siempre verificar) |

---

## Configuración de Alertmanager

### Archivo: `alertmanager_tls.yml`

Cambios clave respecto a `alertmanager.yml`:

```yaml
# Configuración TLS en Alertmanager
tls_config:
  cert_file: /etc/alertmanager/tls/alertmanager.crt
  key_file: /etc/alertmanager/tls/alertmanager.key
  client_ca_file: /etc/alertmanager/tls/ca.crt
  client_auth_type: "RequireAndVerifyClientCert"  # ← Autenticación mutua
```

### Parámetros TLS

| Parámetro | Descripción | Valor |
|-----------|-------------|-------|
| `cert_file` | Certificado servidor de Alertmanager | `/etc/alertmanager/tls/alertmanager.crt` |
| `key_file` | Clave privada servidor de Alertmanager | `/etc/alertmanager/tls/alertmanager.key` |
| `client_ca_file` | CA para verificar certificados cliente | `/etc/alertmanager/tls/ca.crt` |
| `client_auth_type` | Tipo de autenticación cliente | `RequireAndVerifyClientCert` |

---

## Despliegue con Docker Compose

### Actualización de `docker-compose.observability.yml`

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus_tls.yml'  # ← Usar config TLS
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    volumes:
      - ./prometheus/prometheus_tls.yml:/etc/prometheus/prometheus_tls.yml:ro
      - ./prometheus/alerts.yml:/etc/prometheus/alerts.yml:ro
      - ./prometheus/tls:/etc/prometheus/tls:ro  # ← Montar certificados
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - observability

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager_tls.yml'  # ← Usar config TLS
      - '--web.listen-address=:9093'
      - '--cluster.listen-address='
    volumes:
      - ./alertmanager/alertmanager_tls.yml:/etc/alertmanager/alertmanager_tls.yml:ro
      - ./alertmanager/templates:/etc/alertmanager/templates:ro
      - ./prometheus/tls:/etc/alertmanager/tls:ro  # ← Montar certificados
      - alertmanager-data:/alertmanager
    ports:
      - "9093:9093"
    networks:
      - observability
```

### Levantar Servicios

```bash
cd inventario-retail/observability
docker-compose -f docker-compose.observability.yml up -d prometheus alertmanager
```

---

## Verificación

### 1. Verificar Logs de Prometheus

```bash
docker logs prometheus | grep -i tls
```

**Output esperado:**
```
level=info msg="Successfully loaded TLS configuration"
level=info msg="Server is ready to receive web requests."
```

### 2. Verificar Conexión a Alertmanager

Desde dentro del contenedor de Prometheus:

```bash
docker exec -it prometheus /bin/sh
wget --no-check-certificate https://alertmanager:9093/-/healthy
```

**Output esperado:**
```
HTTP request sent, awaiting response... 200 OK
```

### 3. Verificar Status de Alertmanager en Prometheus UI

1. Abrir: http://localhost:9090/alerts
2. Verificar que aparezca **Alertmanager** en estado `UP`
3. No debe haber errores de conexión

### 4. Probar Envío de Alerta

```bash
# Simular alerta firing
docker exec -it prometheus \
  curl -X POST \
    -H "Content-Type: application/json" \
    -d '[{"labels":{"alertname":"TestAlert","severity":"high"}}]' \
    http://localhost:9090/api/v1/alerts
```

Verificar recepción en Alertmanager:
```bash
curl -k https://localhost:9093/api/v1/alerts
```

---

## Troubleshooting

### Error: "certificate signed by unknown authority"

**Causa:** CA no es reconocida

**Solución:**
```bash
# Verificar que ca.crt esté montado correctamente
docker exec prometheus ls -la /etc/prometheus/tls/

# Verificar permisos
docker exec prometheus cat /etc/prometheus/tls/ca.crt
```

### Error: "x509: certificate has expired"

**Causa:** Certificados vencidos

**Solución:**
```bash
# Regenerar certificados
cd inventario-retail/observability/prometheus/tls
./generate_certs.sh

# Reiniciar servicios
docker-compose restart prometheus alertmanager
```

### Error: "remote error: tls: bad certificate"

**Causa:** Certificado cliente inválido o no presente

**Solución:**
1. Verificar que `prometheus.crt` y `prometheus.key` existan
2. Verificar que estén montados en `/etc/prometheus/tls/`
3. Verificar permisos (deben ser legibles por usuario prometheus)

### Error: "connection refused"

**Causa:** Alertmanager no está escuchando en puerto HTTPS

**Solución:**
```bash
# Verificar que Alertmanager usa config TLS
docker exec alertmanager cat /etc/alertmanager/alertmanager_tls.yml | grep tls_config

# Verificar logs
docker logs alertmanager
```

---

## Renovación de Certificados

### Cuándo Renovar

- **Recomendado:** 30 días antes del vencimiento
- **Urgente:** 7 días antes del vencimiento
- **Crítico:** Certificado vencido

### Procedimiento de Renovación

```bash
# 1. Generar nuevos certificados
cd inventario-retail/observability/prometheus/tls
./generate_certs.sh

# 2. Verificar nuevos certificados
openssl x509 -in prometheus.crt -noout -dates

# 3. Reiniciar servicios con rolling update
docker-compose restart prometheus
sleep 10
docker-compose restart alertmanager

# 4. Verificar conectividad
curl -k https://localhost:9093/-/healthy
```

### Automatización con Cron

```bash
# /etc/cron.monthly/renew-observability-certs.sh
#!/bin/bash
cd /path/to/inventario-retail/observability/prometheus/tls
./generate_certs.sh
docker-compose -f ../../docker-compose.observability.yml restart prometheus alertmanager
```

---

## Mejores Prácticas

### Seguridad

1. ✅ **Nunca committear claves privadas** (`.key` files)
   ```bash
   # En .gitignore:
   *.key
   ca.key
   ```

2. ✅ **Usar permisos restrictivos**
   ```bash
   chmod 600 *.key
   chmod 644 *.crt
   ```

3. ✅ **Rotar certificados regularmente** (cada 90 días recomendado)

4. ✅ **Usar certificados de CA confiable en producción** (Let's Encrypt, DigiCert)

5. ✅ **Monitorear expiración de certificados**
   ```yaml
   # Alerta de Prometheus
   - alert: CertificateExpiring
     expr: (prometheus_sd_file_mtime_seconds - time()) < 604800
     labels:
       severity: warning
   ```

### Desarrollo vs Producción

| Aspecto | Desarrollo/Staging | Producción |
|---------|-------------------|------------|
| **Tipo de certificados** | Autofirmados | CA confiable (Let's Encrypt) |
| **Validez** | 365 días | 90 días (renovación automática) |
| **Verificación** | Puede deshabilitarse | Siempre habilitada |
| **Almacenamiento claves** | Filesystem | Secrets manager (Vault, AWS SM) |

### Performance

- TLS añade ~5-10ms de latencia por conexión
- Impacto en throughput: < 5%
- CPU overhead: ~2-3% adicional

---

## Referencias

- [Prometheus TLS Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#tls_config)
- [Alertmanager TLS Configuration](https://prometheus.io/docs/alerting/latest/configuration/#tls_config)
- [OpenSSL Certificate Management](https://www.openssl.org/docs/man1.1.1/man1/openssl-x509.html)
- [Let's Encrypt for Production](https://letsencrypt.org/)