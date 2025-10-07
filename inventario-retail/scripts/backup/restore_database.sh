#!/bin/bash
# restore_database.sh - Script para restaurar base de datos PostgreSQL
# Uso: ./restore_database.sh [archivo_backup] [entorno]
# Ejemplo: ./restore_database.sh /ruta/al/backup/database_production_20251007_120000.tar.gz production

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Banner
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   🔄 MINI MARKET DATABASE RESTORE 🔄   ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "${YELLOW}Fecha: $(date)${NC}"
echo

# Verificar argumentos
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: Debe proporcionar un archivo de backup${NC}"
    echo -e "${YELLOW}Uso: $0 [archivo_backup] [entorno]${NC}"
    echo -e "${YELLOW}Ejemplo: $0 /ruta/al/backup/database_production_20251007_120000.tar.gz production${NC}"
    exit 1
fi

# Configuración
BACKUP_FILE="$1"
ENVIRONMENT=${2:-"development"}
CONFIG_FILE="../config/backup_config.${ENVIRONMENT}.env"
TEMP_DIR=$(mktemp -d)

# Cargar configuración según ambiente
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${GREEN}Cargando configuración desde: $CONFIG_FILE${NC}"
    source "$CONFIG_FILE"
else
    echo -e "${YELLOW}Archivo de configuración no encontrado: $CONFIG_FILE${NC}"
    echo -e "${YELLOW}Usando configuración por defecto...${NC}"
    
    # Configuración por defecto para desarrollo
    DB_HOST="localhost"
    DB_PORT="5432"
    DB_USER="postgres"
    DB_PASSWORD="postgres"
    DB_NAME="minimarket"
fi

# Verificar que el archivo de backup existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}ERROR: Archivo de backup no encontrado: $BACKUP_FILE${NC}"
    exit 1
fi

# Verificar si es un archivo .tar.gz
if [[ "$BACKUP_FILE" == *.tar.gz ]]; then
    echo -e "${BLUE}Descomprimiendo archivo tar.gz...${NC}"
    tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Fallo al descomprimir archivo${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Buscar archivos de esquema y datos
    SCHEMA_FILE=$(find "$TEMP_DIR" -name "*_schema.sql" | head -1)
    DATA_FILE=$(find "$TEMP_DIR" -name "*_data.sql" | head -1)
    
    if [ -z "$SCHEMA_FILE" ] || [ -z "$DATA_FILE" ]; then
        echo -e "${RED}ERROR: No se encontraron archivos de esquema y datos en el backup${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    echo -e "${GREEN}Archivos descomprimidos:${NC}"
    echo -e "  Schema: $(basename "$SCHEMA_FILE")"
    echo -e "  Data: $(basename "$DATA_FILE")"
    
    METADATA_FILE=$(find "$TEMP_DIR" -name "*_metadata.json" | head -1)
    if [ -n "$METADATA_FILE" ]; then
        echo -e "${BLUE}Metadata encontrada: $(basename "$METADATA_FILE")${NC}"
        echo -e "${YELLOW}Información del backup:${NC}"
        cat "$METADATA_FILE" | grep -E '"timestamp"|"environment"|"database"|"version"' | sed 's/^/  /'
        echo
    fi
else
    # Es un solo archivo SQL
    if [[ "$BACKUP_FILE" == *.sql ]]; then
        echo -e "${YELLOW}Archivo SQL detectado. Asumiendo que es un backup completo.${NC}"
        SCHEMA_FILE="$BACKUP_FILE"
        DATA_FILE="$BACKUP_FILE"
    else
        echo -e "${RED}ERROR: Formato de backup desconocido. Se esperaba .tar.gz o .sql${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

# Prompt de confirmación
echo -e "${RED}ADVERTENCIA: Esta operación eliminará TODOS los datos en la base de datos '$DB_NAME'${NC}"
echo -e "${RED}Esta acción NO SE PUEDE DESHACER.${NC}"
echo -e "${YELLOW}Por favor confirme la información:${NC}"
echo -e "  Host: $DB_HOST"
echo -e "  Puerto: $DB_PORT"
echo -e "  Usuario: $DB_USER"
echo -e "  Base de datos: $DB_NAME"
echo -e "  Ambiente: $ENVIRONMENT"
echo -e "${YELLOW}¿Está seguro de continuar? (s/N)${NC}"

read -r CONFIRM
if [[ ! "$CONFIRM" =~ ^[Ss]$ ]]; then
    echo -e "${BLUE}Restauración cancelada por el usuario.${NC}"
    rm -rf "$TEMP_DIR"
    exit 0
fi

# Verificar conexión a la base de datos
echo -e "${BLUE}Verificando conexión a la base de datos...${NC}"
if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "\q" >/dev/null 2>&1; then
    echo -e "${RED}ERROR: No se pudo conectar a PostgreSQL${NC}"
    echo -e "${RED}Verifique que PostgreSQL esté ejecutándose y las credenciales sean correctas${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Verificar si la base de datos existe
DB_EXISTS=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';")

if [ -n "$DB_EXISTS" ]; then
    echo -e "${YELLOW}La base de datos '$DB_NAME' ya existe y será eliminada.${NC}"
    # Terminar conexiones existentes
    echo -e "${BLUE}Terminando conexiones existentes...${NC}"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" >/dev/null 2>&1
    
    # Eliminar la base de datos
    echo -e "${BLUE}Eliminando base de datos existente...${NC}"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE \"$DB_NAME\";"
fi

# Crear base de datos nueva
echo -e "${BLUE}Creando base de datos nueva...${NC}"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE \"$DB_NAME\";"
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Fallo al crear base de datos${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Restaurar esquema
echo -e "${BLUE}Restaurando esquema...${NC}"
if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SCHEMA_FILE"; then
    echo -e "${RED}ERROR: Fallo al restaurar esquema${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Restaurar datos (solo si son archivos separados)
if [ "$SCHEMA_FILE" != "$DATA_FILE" ]; then
    echo -e "${BLUE}Restaurando datos...${NC}"
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$DATA_FILE"; then
        echo -e "${RED}ADVERTENCIA: Ocurrieron errores al restaurar datos${NC}"
    fi
fi

# Verificar restauración
echo -e "${BLUE}Verificando restauración...${NC}"
TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
ROW_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT sum(n_live_tup) 
    FROM pg_stat_user_tables;" 2>/dev/null)

echo -e "${GREEN}Restauración completada${NC}"
echo -e "${GREEN}Tablas encontradas: $TABLE_COUNT${NC}"
echo -e "${GREEN}Filas aproximadas: $ROW_COUNT${NC}"

# Limpiar archivos temporales
rm -rf "$TEMP_DIR"

# Resumen
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✅ RESTAURACIÓN DE BASE DE DATOS COMPLETADA${NC}"
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${YELLOW}Ambiente:${NC} $ENVIRONMENT"
echo -e "${YELLOW}Base de datos:${NC} $DB_NAME@$DB_HOST:$DB_PORT"
echo -e "${YELLOW}Archivo restaurado:${NC} $(basename "$BACKUP_FILE")"
echo -e "${YELLOW}Tablas:${NC} $TABLE_COUNT"
echo -e "${YELLOW}Filas aproximadas:${NC} $ROW_COUNT"
echo -e "${BLUE}=========================================${NC}"

exit 0