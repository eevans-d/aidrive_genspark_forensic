#!/bin/bash
# Migración de SQLite a PostgreSQL para escalabilidad
# Uso: ./migrate_postgres.sh [force] [backup]

set -e

FORCE_MIGRATION="${1:-false}"
CREATE_BACKUP="${2:-true}"
SQLITE_DB="${SQLITE_DB:-data/inventario.db}"
PG_HOST="${PG_HOST:-localhost}"
PG_PORT="${PG_PORT:-5432}"
PG_USER="${PG_USER:-inventario}"
PG_DB="${PG_DB:-inventario_retail}"

echo "🔄 Iniciando migración SQLite → PostgreSQL"
echo "   SQLite: $SQLITE_DB"
echo "   PostgreSQL: $PG_USER@$PG_HOST:$PG_PORT/$PG_DB"

# Verificar que existe base SQLite
if [ ! -f "$SQLITE_DB" ]; then
    echo "❌ Base SQLite no encontrada: $SQLITE_DB"
    exit 1
fi

# Verificar conexión PostgreSQL
if ! psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c "SELECT 1;" &>/dev/null; then
    echo "❌ No se puede conectar a PostgreSQL"
    echo "Verificar: psql -h $PG_HOST -p $PG_PORT -U $PG_USER -d $PG_DB"
    exit 1
fi

# Verificar si ya hay datos en PostgreSQL
ROW_COUNT=$(psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

if [ "$ROW_COUNT" -gt 0 ] && [ "$FORCE_MIGRATION" != "true" ]; then
    echo "⚠️ PostgreSQL ya contiene tablas ($ROW_COUNT)"
    echo "Usar: ./migrate_postgres.sh force para forzar migración"
    exit 1
fi

# Crear backup si se solicita
if [ "$CREATE_BACKUP" = "true" ]; then
    BACKUP_FILE="data/backup_pre_migration_$(date +%Y%m%d_%H%M%S).db"
    echo "📦 Creando backup: $BACKUP_FILE"
    cp "$SQLITE_DB" "$BACKUP_FILE"
fi

# Script Python para migración
cat > /tmp/migrate_to_postgres.py << 'EOF'
import sqlite3
import psycopg2
import os
import sys
from datetime import datetime

def migrate_database():
    """Migrar datos de SQLite a PostgreSQL"""

    # Configuración desde environment
    sqlite_db = os.getenv('SQLITE_DB', 'data/inventario.db')
    pg_config = {
        'host': os.getenv('PG_HOST', 'localhost'),
        'port': int(os.getenv('PG_PORT', 5432)),
        'user': os.getenv('PG_USER', 'inventario'),  
        'password': os.getenv('PG_PASSWORD', 'inventario123'),
        'database': os.getenv('PG_DB', 'inventario_retail')
    }

    print(f"🔗 Conectando a SQLite: {sqlite_db}")
    sqlite_conn = sqlite3.connect(sqlite_db)
    sqlite_conn.row_factory = sqlite3.Row

    print(f"🔗 Conectando a PostgreSQL: {pg_config['user']}@{pg_config['host']}")
    pg_conn = psycopg2.connect(**pg_config)
    pg_cursor = pg_conn.cursor()

    # Mapeo de tipos SQLite → PostgreSQL
    type_mapping = {
        'INTEGER': 'INTEGER',
        'TEXT': 'TEXT', 
        'REAL': 'DOUBLE PRECISION',
        'BLOB': 'BYTEA',
        'DATETIME': 'TIMESTAMP',
        'BOOLEAN': 'BOOLEAN',
        'FLOAT': 'DOUBLE PRECISION'
    }

    try:
        # 1. Recrear esquema en PostgreSQL
        print("📋 Recreando esquema...")

        # Obtener esquema de SQLite
        tables_info = sqlite_conn.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()

        for table in tables_info:
            table_name = table['name']
            create_sql = table['sql']

            print(f"   Creando tabla: {table_name}")

            # Convertir SQL de SQLite a PostgreSQL
            pg_sql = create_sql

            # Reemplazar tipos
            for sqlite_type, pg_type in type_mapping.items():
                pg_sql = pg_sql.replace(sqlite_type, pg_type)

            # Ajustes específicos PostgreSQL
            pg_sql = pg_sql.replace('AUTOINCREMENT', '')
            pg_sql = pg_sql.replace('INTEGER PRIMARY KEY', 'SERIAL PRIMARY KEY')

            # Ejecutar en PostgreSQL
            pg_cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            pg_cursor.execute(pg_sql)

        pg_conn.commit()

        # 2. Migrar datos tabla por tabla
        print("📊 Migrando datos...")

        tables_to_migrate = ['productos', 'movimientos_stock', 'facturas', 'factura_items']

        for table_name in tables_to_migrate:
            print(f"   Migrando tabla: {table_name}")

            # Verificar si existe en SQLite
            try:
                count = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                print(f"     Registros a migrar: {count}")

                if count == 0:
                    continue

                # Obtener estructura de columnas
                columns_info = sqlite_conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                columns = [col['name'] for col in columns_info]

                # Obtener datos
                cursor = sqlite_conn.execute(f"SELECT * FROM {table_name}")

                migrated_count = 0
                batch_size = 1000

                while True:
                    rows = cursor.fetchmany(batch_size)
                    if not rows:
                        break

                    # Preparar INSERT para PostgreSQL
                    placeholders = ','.join(['%s'] * len(columns))
                    insert_sql = f"""
                        INSERT INTO {table_name} ({','.join(columns)}) 
                        VALUES ({placeholders})
                    """

                    # Convertir datos
                    batch_data = []
                    for row in rows:
                        row_data = list(row)
                        # Conversiones específicas si es necesario
                        batch_data.append(tuple(row_data))

                    # Insertar batch
                    pg_cursor.executemany(insert_sql, batch_data)
                    migrated_count += len(batch_data)

                    if migrated_count % batch_size == 0:
                        print(f"     Migrados: {migrated_count}")

                pg_conn.commit()
                print(f"   ✅ {table_name}: {migrated_count} registros migrados")

            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    print(f"     Tabla {table_name} no existe en SQLite, omitiendo")
                else:
                    raise

        # 3. Actualizar secuencias PostgreSQL
        print("🔢 Actualizando secuencias...")

        sequence_tables = {
            'productos': 'productos_id_seq',
            'movimientos_stock': 'movimientos_stock_id_seq',
            'facturas': 'facturas_id_seq',
            'factura_items': 'factura_items_id_seq'
        }

        for table, sequence in sequence_tables.items():
            try:
                max_id = sqlite_conn.execute(f"SELECT MAX(id) FROM {table}").fetchone()[0]
                if max_id:
                    pg_cursor.execute(f"SELECT setval('{sequence}', {max_id})")
                    print(f"   {sequence}: actualizado a {max_id}")
            except:
                pass  # Tabla puede no existir

        pg_conn.commit()

        # 4. Verificación de integridad
        print("✅ Verificando integridad...")

        for table_name in tables_to_migrate:
            try:
                sqlite_count = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                pg_count = pg_cursor.fetchone()[0]

                if sqlite_count == pg_count:
                    print(f"   ✅ {table_name}: {pg_count} registros OK")
                else:
                    print(f"   ❌ {table_name}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
                    return False
            except:
                pass

        print("🎉 Migración completada exitosamente")
        return True

    except Exception as e:
        print(f"❌ Error en migración: {e}")
        pg_conn.rollback()
        return False

    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
EOF

# Ejecutar migración Python
echo "🐍 Ejecutando migración..."
export SQLITE_DB PG_HOST PG_PORT PG_USER PG_DB
if python3 /tmp/migrate_to_postgres.py; then
    echo "✅ Migración exitosa"

    # Actualizar configuración para usar PostgreSQL
    echo "⚙️ Actualizando configuración..."
    if [ -f ".env" ]; then
        # Backup configuración actual
        cp .env .env.backup

        # Actualizar DATABASE_URL
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$PG_USER:inventario123@$PG_HOST:$PG_PORT/$PG_DB|" .env

        echo "✅ Configuración actualizada en .env"
        echo "   Backup anterior: .env.backup"
    fi

    echo ""
    echo "🎉 Migración PostgreSQL completada"
    echo "📋 Próximos pasos:"
    echo "1. Verificar que servicios usen nueva configuración"
    echo "2. Ejecutar tests: pytest tests/"
    echo "3. Crear backup regular PostgreSQL"

else
    echo "❌ Migración falló"
    exit 1
fi
