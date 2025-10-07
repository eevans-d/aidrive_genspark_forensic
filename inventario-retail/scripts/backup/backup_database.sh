#!/bin/bash
# backup_database.sh - Script para hacer backup de la base de datos PostgreSQL
# Uso: ./backup_database.sh [entorno]
# Ejemplo: ./backup_database.sh production

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/home/eevan/ProyectosIA/aidrive_genspark/inventario-retail/backups/database"
ENVIRONMENT=${1:-"development"}
CONFIG_FILE="../config/backup_config.${ENVIRONMENT}.env"
RETENTION_DAYS=30
COMPRESS=true
INCLUDE_SCHEMA=true

# Banner
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   🗃️  MINI MARKET DATABASE BACKUP 🗃️   ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "${YELLOW}Fecha: $(date)${NC}"
echo -e "${YELLOW}Entorno: ${ENVIRONMENT}${NC}"
echo

# Validación
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}ERROR: Archivo de configuración no encontrado: $CONFIG_FILE${NC}"
    echo -e "${YELLOW}Intentando usar variables de entorno predeterminadas...${NC}"
    
    # Valores default para desarrollo
    DB_HOST="localhost"
    DB_PORT="5432"
    DB_NAME="minimarket"
    DB_USER="postgres"
    
    # Pedir password si no está configurada
    if [ -z "$POSTGRES_PASSWORD" ]; then
        echo -e "${YELLOW}Ingrese password para PostgreSQL:${NC}"
        read -s PGPASSWORD
        export PGPASSWORD
    else
        export PGPASSWORD="$POSTGRES_PASSWORD"
    fi
else
    # Cargar config desde archivo
    echo -e "${GREEN}Cargando configuración desde $CONFIG_FILE${NC}"
    source "$CONFIG_FILE"
    export PGPASSWORD="$DB_PASSWORD"
fi

# Crear directorio si no existe
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Directorio de backup: $BACKUP_DIR${NC}"

# Nombre de archivo
BACKUP_FILENAME="${DB_NAME}_${ENVIRONMENT}_${TIMESTAMP}"
if [ "$INCLUDE_SCHEMA" = true ]; then
    SCHEMA_FILENAME="${BACKUP_DIR}/${BACKUP_FILENAME}_schema.sql"
    echo -e "${BLUE}Generando backup de schema...${NC}"
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --schema-only > "$SCHEMA_FILENAME"
    echo -e "${GREEN}✅ Schema guardado en: $SCHEMA_FILENAME${NC}"
fi

# Backup de datos
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILENAME}_data.sql"
echo -e "${BLUE}Generando backup de datos...${NC}"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --data-only > "$BACKUP_FILE"

# Comprimir si está configurado
if [ "$COMPRESS" = true ]; then
    echo -e "${BLUE}Comprimiendo backup...${NC}"
    gzip -f "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    if [ "$INCLUDE_SCHEMA" = true ]; then
        gzip -f "$SCHEMA_FILENAME"
        SCHEMA_FILENAME="${SCHEMA_FILENAME}.gz"
    fi
fi

# Verificar tamaño
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo -e "${GREEN}✅ Backup completo: $BACKUP_FILE (${BACKUP_SIZE})${NC}"

# Crear archivo de metadata
META_FILE="${BACKUP_DIR}/${BACKUP_FILENAME}_metadata.json"
cat > "$META_FILE" << EOF
{
  "database": "${DB_NAME}",
  "environment": "${ENVIRONMENT}",
  "timestamp": "$(date -Iseconds)",
  "hostname": "$(hostname)",
  "user": "$(whoami)",
  "postgres_version": "$(psql --version | head -n 1)",
  "files": [
    {
      "type": "data",
      "path": "${BACKUP_FILE}",
      "size": "${BACKUP_SIZE}",
      "compressed": ${COMPRESS}
    }
EOF

if [ "$INCLUDE_SCHEMA" = true ]; then
    SCHEMA_SIZE=$(du -h "$SCHEMA_FILENAME" | cut -f1)
    cat >> "$META_FILE" << EOF
    ,
    {
      "type": "schema",
      "path": "${SCHEMA_FILENAME}",
      "size": "${SCHEMA_SIZE}",
      "compressed": ${COMPRESS}
    }
EOF
fi

cat >> "$META_FILE" << EOF
  ]
}
EOF

echo -e "${GREEN}✅ Metadata guardada en: $META_FILE${NC}"

# Limpiar backups antiguos
echo -e "${BLUE}Eliminando backups más antiguos que $RETENTION_DAYS días...${NC}"
find "$BACKUP_DIR" -name "${DB_NAME}_${ENVIRONMENT}_*" -type f -mtime +$RETENTION_DAYS -delete
echo -e "${GREEN}✅ Limpieza completada${NC}"

# Resumen
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✅ BACKUP COMPLETADO EXITOSAMENTE${NC}"
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${YELLOW}Base de Datos:${NC} $DB_NAME"
echo -e "${YELLOW}Ambiente:${NC} $ENVIRONMENT"
echo -e "${YELLOW}Timestamp:${NC} $TIMESTAMP"
echo -e "${YELLOW}Archivos:${NC}"
echo -e "  📄 $(basename "$BACKUP_FILE") (${BACKUP_SIZE})"
if [ "$INCLUDE_SCHEMA" = true ]; then
    echo -e "  📄 $(basename "$SCHEMA_FILENAME") (${SCHEMA_SIZE})"
fi
echo -e "  📄 $(basename "$META_FILE")"
echo -e "${BLUE}=========================================${NC}"

# Limpiar variables sensibles
unset PGPASSWORD
unset DB_PASSWORD

exit 0