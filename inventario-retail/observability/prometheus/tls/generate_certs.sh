#!/bin/bash
# generate_certs.sh - Script para generar certificados TLS autofirmados
# Para uso en entornos de desarrollo/staging de Prometheus y Alertmanager

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   Generador de Certificados TLS        ${NC}"
echo -e "${BLUE}   Prometheus & Alertmanager            ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo

# Configuración
DAYS_VALID=365
CA_SUBJECT="/C=AR/ST=Buenos Aires/L=CABA/O=MiniMarket/OU=DevOps/CN=MiniMarket CA"
PROMETHEUS_SUBJECT="/C=AR/ST=Buenos Aires/L=CABA/O=MiniMarket/OU=Monitoring/CN=prometheus"
ALERTMANAGER_SUBJECT="/C=AR/ST=Buenos Aires/L=CABA/O=MiniMarket/OU=Monitoring/CN=alertmanager"

# Verificar si ya existen certificados
if [ -f "ca.crt" ] || [ -f "prometheus.crt" ] || [ -f "alertmanager.crt" ]; then
    echo -e "${YELLOW}⚠️  Se encontraron certificados existentes.${NC}"
    echo -e "${YELLOW}¿Desea sobrescribirlos? (s/N)${NC}"
    read -r CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Ss]$ ]]; then
        echo -e "${BLUE}Operación cancelada.${NC}"
        exit 0
    fi
    echo -e "${YELLOW}Eliminando certificados existentes...${NC}"
    rm -f *.crt *.key *.csr *.srl
fi

# 1. Generar CA (Certificate Authority)
echo -e "${BLUE}1. Generando Certificate Authority (CA)...${NC}"
openssl req -x509 -newkey rsa:4096 -days $DAYS_VALID -nodes \
    -keyout ca.key -out ca.crt \
    -subj "$CA_SUBJECT" \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ CA generada exitosamente${NC}"
    chmod 600 ca.key
    echo -e "${YELLOW}   Archivo: ca.crt, ca.key${NC}"
else
    echo -e "${RED}❌ Error al generar CA${NC}"
    exit 1
fi

# 2. Generar certificado para Prometheus
echo -e "${BLUE}2. Generando certificado para Prometheus...${NC}"

# Crear CSR (Certificate Signing Request)
openssl req -newkey rsa:4096 -nodes \
    -keyout prometheus.key -out prometheus.csr \
    -subj "$PROMETHEUS_SUBJECT" \
    2>/dev/null

# Firmar CSR con CA
openssl x509 -req -in prometheus.csr -days $DAYS_VALID \
    -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out prometheus.crt \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Certificado de Prometheus generado${NC}"
    chmod 600 prometheus.key
    rm prometheus.csr
    echo -e "${YELLOW}   Archivo: prometheus.crt, prometheus.key${NC}"
else
    echo -e "${RED}❌ Error al generar certificado de Prometheus${NC}"
    exit 1
fi

# 3. Generar certificado para Alertmanager
echo -e "${BLUE}3. Generando certificado para Alertmanager...${NC}"

# Crear CSR
openssl req -newkey rsa:4096 -nodes \
    -keyout alertmanager.key -out alertmanager.csr \
    -subj "$ALERTMANAGER_SUBJECT" \
    2>/dev/null

# Firmar CSR con CA
openssl x509 -req -in alertmanager.csr -days $DAYS_VALID \
    -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out alertmanager.crt \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Certificado de Alertmanager generado${NC}"
    chmod 600 alertmanager.key
    rm alertmanager.csr
    echo -e "${YELLOW}   Archivo: alertmanager.crt, alertmanager.key${NC}"
else
    echo -e "${RED}❌ Error al generar certificado de Alertmanager${NC}"
    exit 1
fi

# Limpieza de archivos temporales
rm -f *.srl

# Resumen
echo
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✅ Certificados generados exitosamente${NC}"
echo -e "${BLUE}=========================================${NC}"
echo
echo -e "${YELLOW}Archivos generados:${NC}"
ls -lh *.crt *.key | awk '{print "  "$9" ("$5")"}'
echo
echo -e "${YELLOW}Válidos por: ${DAYS_VALID} días${NC}"
echo -e "${YELLOW}Expiración:${NC} $(date -d "+${DAYS_VALID} days" '+%Y-%m-%d')"
echo

# Verificar certificados
echo -e "${BLUE}Verificando certificados...${NC}"
if openssl verify -CAfile ca.crt prometheus.crt >/dev/null 2>&1; then
    echo -e "${GREEN}✅ prometheus.crt verificado${NC}"
else
    echo -e "${RED}❌ prometheus.crt falló verificación${NC}"
fi

if openssl verify -CAfile ca.crt alertmanager.crt >/dev/null 2>&1; then
    echo -e "${GREEN}✅ alertmanager.crt verificado${NC}"
else
    echo -e "${RED}❌ alertmanager.crt falló verificación${NC}"
fi

echo
echo -e "${BLUE}=========================================${NC}"
echo -e "${YELLOW}📝 Próximos pasos:${NC}"
echo -e "  1. Actualizar prometheus.yml con configuración TLS"
echo -e "  2. Actualizar alertmanager.yml con configuración TLS"
echo -e "  3. Reiniciar servicios de observabilidad"
echo -e "  4. Verificar conectividad con TLS habilitado"
echo -e "${BLUE}=========================================${NC}"