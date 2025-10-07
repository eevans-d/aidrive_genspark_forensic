#!/bin/bash
# backup_volumes.sh - Script para hacer backup de volúmenes Docker
# Uso: ./backup_volumes.sh [entorno]
# Ejemplo: ./backup_volumes.sh production

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/backups/volumes"
ENVIRONMENT=${1:-"development"}
CONFIG_FILE="../config/backup_config.${ENVIRONMENT}.env"
RETENTION_DAYS=30
VOLUMES_TO_BACKUP=(
    "inventario-retail_postgres-data"
    "inventario-retail_grafana-data"
    "inventario-retail_prometheus-data"
    "inventario-retail_loki-data"
    "inventario-retail_redis-data"
)

# Banner
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   📦 MINI MARKET VOLUMES BACKUP 📦   ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "${YELLOW}Fecha: $(date)${NC}"
echo -e "${YELLOW}Entorno: ${ENVIRONMENT}${NC}"
echo

# Validación
if [ ! -f "$CONFIG_FILE" ] && [ "$ENVIRONMENT" != "development" ]; then
    echo -e "${RED}ERROR: Archivo de configuración no encontrado: $CONFIG_FILE${NC}"
    echo -e "${YELLOW}Continuando con configuración por defecto...${NC}"
fi

# Crear directorio si no existe
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Directorio de backup: $BACKUP_DIR${NC}"

# Nombre de archivo
BACKUP_FILENAME="volumes_${ENVIRONMENT}_${TIMESTAMP}.tar.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

# Verificar que Docker está disponible
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker no está instalado o no está disponible en PATH${NC}"
    exit 1
fi

# Verificar volúmenes existentes
echo -e "${BLUE}Verificando volúmenes disponibles...${NC}"
AVAILABLE_VOLUMES=$(docker volume ls --format "{{.Name}}")

# Crear directorio temporal
TEMP_DIR=$(mktemp -d)
echo -e "${YELLOW}Directorio temporal: $TEMP_DIR${NC}"

# Array para almacenar volúmenes respaldados con éxito
BACKED_UP_VOLUMES=()
FAILED_VOLUMES=()
BACKUP_METADATA=()

# Hacer backup de cada volumen
for VOLUME in "${VOLUMES_TO_BACKUP[@]}"; do
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${YELLOW}Procesando volumen: $VOLUME${NC}"
    
    # Verificar si el volumen existe
    if ! echo "$AVAILABLE_VOLUMES" | grep -q "$VOLUME"; then
        echo -e "${RED}⚠️ Volumen no encontrado: $VOLUME${NC}"
        FAILED_VOLUMES+=("$VOLUME (no encontrado)")
        continue
    fi
    
    VOLUME_TEMP_DIR="${TEMP_DIR}/${VOLUME}"
    mkdir -p "$VOLUME_TEMP_DIR"
    
    # Crear contenedor temporal para acceder al volumen
    echo -e "${BLUE}Creando contenedor temporal para acceder al volumen...${NC}"
    CONTAINER_ID=$(docker run -d --rm -v "${VOLUME}:/data" -v "${VOLUME_TEMP_DIR}:/backup" alpine:latest tail -f /dev/null)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}⚠️ Error al crear contenedor para volumen: $VOLUME${NC}"
        FAILED_VOLUMES+=("$VOLUME (error de contenedor)")
        continue
    fi
    
    # Copiar datos del volumen al directorio temporal
    echo -e "${BLUE}Copiando datos del volumen...${NC}"
    docker exec "$CONTAINER_ID" sh -c "tar -cf /backup/${VOLUME}.tar -C /data ."
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}⚠️ Error al respaldar volumen: $VOLUME${NC}"
        FAILED_VOLUMES+=("$VOLUME (error de copia)")
    else
        VOLUME_SIZE=$(docker exec "$CONTAINER_ID" sh -c "du -sh /data | cut -f1")
        echo -e "${GREEN}✅ Volumen respaldado: $VOLUME (${VOLUME_SIZE})${NC}"
        BACKED_UP_VOLUMES+=("$VOLUME")
        BACKUP_METADATA+=("\"$VOLUME\": {\"size\": \"$VOLUME_SIZE\", \"timestamp\": \"$(date -Iseconds)\"}")
    fi
    
    # Detener y eliminar contenedor temporal
    docker stop "$CONTAINER_ID" >/dev/null
done

# Comprimir todos los backups en un solo archivo
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${BLUE}Comprimiendo todos los backups...${NC}"
tar -czf "$BACKUP_PATH" -C "$TEMP_DIR" .

# Verificar si la compresión fue exitosa
if [ $? -ne 0 ]; then
    echo -e "${RED}⚠️ Error al comprimir backups${NC}"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
echo -e "${GREEN}✅ Backup comprimido: $BACKUP_PATH (${BACKUP_SIZE})${NC}"

# Crear archivo de metadata
META_FILE="${BACKUP_DIR}/volumes_${ENVIRONMENT}_${TIMESTAMP}_metadata.json"

# Inicio del JSON
echo "{" > "$META_FILE"
echo "  \"backup_type\": \"docker_volumes\"," >> "$META_FILE"
echo "  \"environment\": \"${ENVIRONMENT}\"," >> "$META_FILE"
echo "  \"timestamp\": \"$(date -Iseconds)\"," >> "$META_FILE"
echo "  \"hostname\": \"$(hostname)\"," >> "$META_FILE"
echo "  \"user\": \"$(whoami)\"," >> "$META_FILE"
echo "  \"docker_version\": \"$(docker --version)\"," >> "$META_FILE"
echo "  \"backup_file\": \"${BACKUP_FILENAME}\"," >> "$META_FILE"
echo "  \"backup_size\": \"${BACKUP_SIZE}\"," >> "$META_FILE"

# Volumes respaldados
echo "  \"volumes\": {" >> "$META_FILE"

# Agregar cada volumen como un objeto JSON
COUNT=${#BACKUP_METADATA[@]}
for ((i=0; i<$COUNT; i++)); do
    echo "    ${BACKUP_METADATA[i]}" >> "$META_FILE"
    if [ $i -lt $((COUNT-1)) ]; then
        echo "," >> "$META_FILE"
    else
        echo "" >> "$META_FILE"
    fi
done

echo "  }," >> "$META_FILE"

# Volumes fallidos
echo "  \"failed_volumes\": [" >> "$META_FILE"
COUNT=${#FAILED_VOLUMES[@]}
for ((i=0; i<$COUNT; i++)); do
    echo "    \"${FAILED_VOLUMES[i]}\"" >> "$META_FILE"
    if [ $i -lt $((COUNT-1)) ]; then
        echo "," >> "$META_FILE"
    else
        echo "" >> "$META_FILE"
    fi
done

echo "  ]" >> "$META_FILE"
echo "}" >> "$META_FILE"

echo -e "${GREEN}✅ Metadata guardada en: $META_FILE${NC}"

# Limpiar directorio temporal
echo -e "${BLUE}Limpiando directorio temporal...${NC}"
rm -rf "$TEMP_DIR"

# Limpiar backups antiguos
echo -e "${BLUE}Eliminando backups más antiguos que $RETENTION_DAYS días...${NC}"
find "$BACKUP_DIR" -name "volumes_${ENVIRONMENT}_*" -type f -mtime +$RETENTION_DAYS -delete
echo -e "${GREEN}✅ Limpieza completada${NC}"

# Resumen
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✅ BACKUP DE VOLÚMENES COMPLETADO${NC}"
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${YELLOW}Ambiente:${NC} $ENVIRONMENT"
echo -e "${YELLOW}Timestamp:${NC} $TIMESTAMP"
echo -e "${YELLOW}Archivo:${NC} $(basename "$BACKUP_PATH") (${BACKUP_SIZE})"
echo -e "${YELLOW}Volúmenes respaldados:${NC} ${#BACKED_UP_VOLUMES[@]}"
for VOLUME in "${BACKED_UP_VOLUMES[@]}"; do
    echo -e "  ✅ $VOLUME"
done
if [ ${#FAILED_VOLUMES[@]} -gt 0 ]; then
    echo -e "${YELLOW}Volúmenes fallidos:${NC} ${#FAILED_VOLUMES[@]}"
    for FAILED in "${FAILED_VOLUMES[@]}"; do
        echo -e "  ⚠️ $FAILED"
    done
fi
echo -e "${BLUE}=========================================${NC}"

exit 0