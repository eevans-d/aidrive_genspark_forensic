# Generación de Certificados TLS para Prometheus

Este directorio contiene los certificados TLS autofirmados para comunicaciones seguras entre componentes de observabilidad.

## Estructura

```
tls/
├── README.md                 # Este archivo
├── generate_certs.sh         # Script de generación de certificados
├── ca.crt                    # Certificado de CA (Certificate Authority)
├── ca.key                    # Clave privada de CA
├── prometheus.crt            # Certificado de Prometheus
├── prometheus.key            # Clave privada de Prometheus
├── alertmanager.crt          # Certificado de Alertmanager
└── alertmanager.key          # Clave privada de Alertmanager
```

## Uso

### Generar Certificados

```bash
./generate_certs.sh
```

Este script genera:
1. Certificado y clave de Certificate Authority (CA)
2. Certificados y claves para Prometheus y Alertmanager
3. Todos los certificados son válidos por 365 días

### Renovar Certificados

Para renovar certificados antes de que expiren:

```bash
# Eliminar certificados existentes
rm -f *.crt *.key *.csr

# Regenerar
./generate_certs.sh
```

### Verificar Certificados

```bash
# Ver información del certificado de Prometheus
openssl x509 -in prometheus.crt -text -noout

# Verificar que el certificado fue firmado por la CA
openssl verify -CAfile ca.crt prometheus.crt
```

## Seguridad

⚠️ **IMPORTANTE:**

- Estos certificados son autofirmados y solo apropiados para entornos de desarrollo/staging
- Para producción, usar certificados firmados por una CA confiable (Let's Encrypt, DigiCert, etc.)
- Las claves privadas (`*.key`) NO deben ser commiteadas al repositorio
- Mantener permisos restrictivos en archivos de claves: `chmod 600 *.key`

## Uso en Docker Compose

Los certificados se montan como volumes en los servicios:

```yaml
prometheus:
  volumes:
    - ./prometheus/tls:/etc/prometheus/tls:ro
    
alertmanager:
  volumes:
    - ./alertmanager/tls:/etc/alertmanager/tls:ro
```

## Referencias

- [Prometheus TLS Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#tls_config)
- [Alertmanager TLS Configuration](https://prometheus.io/docs/alerting/latest/configuration/#tls_config)