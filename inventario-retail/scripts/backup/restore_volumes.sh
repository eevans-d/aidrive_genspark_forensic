#!/bin/bash
# restore_volumes.sh - Script para restaurar volúmenes Docker
# Uso: ./restore_volumes.sh [archivo_backup] [entorno]
# Ejemplo: ./restore_volumes.sh /ruta/al/backup/volumes_production_20251007_120000.tar.gz production

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Banner
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    🔄 MINI MARKET VOLUMES RESTORE 🔄    ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "${YELLOW}Fecha: $(date)${NC}"
echo

# Verificar argumentos
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: Debe proporcionar un archivo de backup${NC}"
    echo -e "${YELLOW}Uso: $0 [archivo_backup] [entorno]${NC}"
    echo -e "${YELLOW}Ejemplo: $0 /ruta/al/backup/volumes_production_20251007_120000.tar.gz production${NC}"
    exit 1
fi

# Configuración
BACKUP_FILE="$1"
ENVIRONMENT=${2:-"development"}
CONFIG_FILE="../config/backup_config.${ENVIRONMENT}.env"
TEMP_DIR=$(mktemp -d)
VOLUMES_PREFIX="inventario-retail_"

# Verificar que el archivo de backup existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}ERROR: Archivo de backup no encontrado: $BACKUP_FILE${NC}"
    exit 1
fi

# Verificar que Docker está disponible
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker no está instalado o no está disponible en PATH${NC}"
    exit 1
fi

# Descomprimir el archivo de backup
echo -e "${BLUE}Descomprimiendo archivo de backup...${NC}"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Fallo al descomprimir archivo de backup${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Buscar metadata del backup
METADATA_FILE=$(find "$TEMP_DIR" -name "*_metadata.json" 2>/dev/null | head -1)
VOLUMES_INFO=()

if [ -n "$METADATA_FILE" ]; then
    echo -e "${BLUE}Metadata encontrada: $(basename "$METADATA_FILE")${NC}"
    echo -e "${YELLOW}Información del backup:${NC}"
    cat "$METADATA_FILE" | grep -E '"timestamp"|"environment"|"backup_file"|"volumes"' | grep -v '{' | head -4 | sed 's/^/  /'
    
    # Extraer información de volúmenes
    VOLUMES_LIST=$(cat "$METADATA_FILE" | grep -A 50 '"volumes": {' | grep -B 50 '"failed_volumes":' | grep -v 'volumes' | grep -v '{' | grep -v '}')
    echo -e "${YELLOW}Volúmenes en el backup:${NC}"
    echo "$VOLUMES_LIST" | sed 's/^/  /'
    
    # Obtener nombres de volúmenes
    VOLUMES_INFO=($(echo "$VOLUMES_LIST" | grep -o '"[^"]*": {' | cut -d'"' -f2))
else
    # Buscar archivos tar directamente
    echo -e "${YELLOW}No se encontró metadata, buscando archivos de volumen...${NC}"
    VOLUME_FILES=($(find "$TEMP_DIR" -name "*.tar" 2>/dev/null))
    
    if [ ${#VOLUME_FILES[@]} -eq 0 ]; then
        echo -e "${RED}ERROR: No se encontraron archivos de volumen en el backup${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Extraer nombres de volúmenes de los archivos
    for FILE in "${VOLUME_FILES[@]}"; do
        VOLUME_NAME=$(basename "$FILE" .tar)
        VOLUMES_INFO+=("$VOLUME_NAME")
    done
    
    echo -e "${YELLOW}Volúmenes encontrados:${NC}"
    for VOLUME in "${VOLUMES_INFO[@]}"; do
        echo -e "  $VOLUME"
    done
fi

# Prompt de confirmación
echo
echo -e "${RED}ADVERTENCIA: Esta operación sobrescribirá los volúmenes Docker existentes.${NC}"
echo -e "${RED}Esta acción NO SE PUEDE DESHACER y puede causar pérdida de datos.${NC}"
echo -e "${RED}Asegúrese de que los servicios que usan estos volúmenes estén detenidos.${NC}"
echo -e "${YELLOW}¿Está seguro de continuar? (s/N)${NC}"

read -r CONFIRM
if [[ ! "$CONFIRM" =~ ^[Ss]$ ]]; then
    echo -e "${BLUE}Restauración cancelada por el usuario.${NC}"
    rm -rf "$TEMP_DIR"
    exit 0
fi

# Verificar volúmenes existentes
echo -e "${BLUE}Verificando volúmenes existentes...${NC}"
EXISTING_VOLUMES=$(docker volume ls --format "{{.Name}}")

# Arrays para seguimiento
RESTORED_VOLUMES=()
CREATED_VOLUMES=()
FAILED_VOLUMES=()

# Restaurar cada volumen
for VOLUME in "${VOLUMES_INFO[@]}"; do
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${YELLOW}Procesando volumen: $VOLUME${NC}"
    
    VOLUME_TAR="${TEMP_DIR}/${VOLUME}.tar"
    if [ ! -f "$VOLUME_TAR" ]; then
        echo -e "${RED}⚠️ Archivo tar no encontrado para volumen: $VOLUME${NC}"
        FAILED_VOLUMES+=("$VOLUME (archivo no encontrado)")
        continue
    fi
    
    # Verificar si el volumen existe
    if ! echo "$EXISTING_VOLUMES" | grep -q "$VOLUME"; then
        echo -e "${YELLOW}Volumen no existente, creando: $VOLUME${NC}"
        docker volume create "$VOLUME"
        if [ $? -ne 0 ]; then
            echo -e "${RED}⚠️ Error al crear volumen: $VOLUME${NC}"
            FAILED_VOLUMES+=("$VOLUME (error al crear)")
            continue
        fi
        CREATED_VOLUMES+=("$VOLUME")
    else
        echo -e "${YELLOW}Volumen encontrado: $VOLUME${NC}"
    fi
    
    # Crear contenedor temporal para restaurar el volumen
    echo -e "${BLUE}Restaurando datos al volumen...${NC}"
    
    # Paso 1: Crear contenedor con volumen montado
    CONTAINER_ID=$(docker run -d --rm -v "${VOLUME}:/data" alpine:latest tail -f /dev/null)
    if [ $? -ne 0 ]; then
        echo -e "${RED}⚠️ Error al crear contenedor para volumen: $VOLUME${NC}"
        FAILED_VOLUMES+=("$VOLUME (error de contenedor)")
        continue
    fi
    
    # Paso 2: Copiar archivo tar al contenedor
    docker cp "$VOLUME_TAR" "$CONTAINER_ID:/volume.tar"
    if [ $? -ne 0 ]; then
        echo -e "${RED}⚠️ Error al copiar archivo tar al contenedor: $VOLUME${NC}"
        docker stop "$CONTAINER_ID" >/dev/null
        FAILED_VOLUMES+=("$VOLUME (error de copia)")
        continue
    fi
    
    # Paso 3: Limpiar y restaurar datos
    docker exec "$CONTAINER_ID" sh -c "rm -rf /data/* /data/..?* /data/.[!.]* 2>/dev/null || true"
    docker exec "$CONTAINER_ID" sh -c "tar -xf /volume.tar -C /data"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}⚠️ Error al restaurar volumen: $VOLUME${NC}"
        docker stop "$CONTAINER_ID" >/dev/null
        FAILED_VOLUMES+=("$VOLUME (error de restauración)")
        continue
    fi
    
    # Paso 4: Verificar
    RESTORED_SIZE=$(docker exec "$CONTAINER_ID" sh -c "du -sh /data | cut -f1")
    echo -e "${GREEN}✅ Volumen restaurado: $VOLUME (${RESTORED_SIZE})${NC}"
    RESTORED_VOLUMES+=("$VOLUME")
    
    # Detener contenedor temporal
    docker stop "$CONTAINER_ID" >/dev/null
done

# Limpiar archivos temporales
echo -e "${BLUE}Limpiando archivos temporales...${NC}"
rm -rf "$TEMP_DIR"

# Resumen
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✅ RESTAURACIÓN DE VOLÚMENES COMPLETADA${NC}"
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${YELLOW}Ambiente:${NC} $ENVIRONMENT"
echo -e "${YELLOW}Archivo restaurado:${NC} $(basename "$BACKUP_FILE")"

if [ ${#RESTORED_VOLUMES[@]} -gt 0 ]; then
    echo -e "${YELLOW}Volúmenes restaurados:${NC} ${#RESTORED_VOLUMES[@]}"
    for VOLUME in "${RESTORED_VOLUMES[@]}"; do
        echo -e "  ✅ $VOLUME"
    done
fi

if [ ${#CREATED_VOLUMES[@]} -gt 0 ]; then
    echo -e "${YELLOW}Volúmenes creados:${NC} ${#CREATED_VOLUMES[@]}"
    for VOLUME in "${CREATED_VOLUMES[@]}"; do
        echo -e "  ➕ $VOLUME"
    done
fi

if [ ${#FAILED_VOLUMES[@]} -gt 0 ]; then
    echo -e "${RED}Volúmenes fallidos:${NC} ${#FAILED_VOLUMES[@]}"
    for FAILED in "${FAILED_VOLUMES[@]}"; do
        echo -e "  ⚠️ $FAILED"
    done
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${YELLOW}Nota: Reinicie los servicios que utilizan estos volúmenes${NC}"

exit 0