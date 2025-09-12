#!/usr/bin/env python3
"""
Sistema de Gestión de Inventario - Inicialización de Base de Datos
Archivo: scripts/init_database.py

SCRIPT COMPLETO DE INICIALIZACIÓN CON DATOS ARGENTINOS REALES
"""

import asyncio
import asyncpg
import logging
import sys
import argparse
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
import os
import random

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('database_init.log')
    ]
)
logger = logging.getLogger(__name__)

DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'inventario_system'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres123')
}

class DatabaseInitializer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool = None

    async def create_connection_pool(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("✅ Pool de conexiones creado")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise

    async def close_pool(self):
        if self.pool:
            await self.pool.close()
            logger.info("🔒 Pool cerrado")

    async def drop_all_tables(self):
        drop_sql = """
        DROP TABLE IF EXISTS stock_movements CASCADE;
        DROP TABLE IF EXISTS product_locations CASCADE;
        DROP TABLE IF EXISTS products CASCADE;
        DROP TABLE IF EXISTS locations CASCADE;
        DROP TABLE IF EXISTS warehouses CASCADE;
        DROP TABLE IF EXISTS suppliers CASCADE;
        DROP TABLE IF EXISTS categories CASCADE;
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(drop_sql)
                logger.info("🗑️ Tablas eliminadas")

    async def create_schema(self):
        schema_sql = """
        CREATE TABLE categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            parent_id INTEGER REFERENCES categories(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE suppliers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            contact_person VARCHAR(100),
            email VARCHAR(100),
            phone VARCHAR(20),
            address TEXT,
            city VARCHAR(100),
            province VARCHAR(100),
            postal_code VARCHAR(10),
            country VARCHAR(50) DEFAULT 'Argentina',
            tax_id VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE warehouses (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(10) NOT NULL UNIQUE,
            address TEXT,
            city VARCHAR(100),
            province VARCHAR(100),
            manager_name VARCHAR(100),
            manager_email VARCHAR(100),
            phone VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            capacity_cubic_meters DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE locations (
            id SERIAL PRIMARY KEY,
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
            zone VARCHAR(20) NOT NULL,
            aisle VARCHAR(10) NOT NULL,
            rack VARCHAR(10) NOT NULL,
            shelf VARCHAR(10) NOT NULL,
            position VARCHAR(10),
            location_code VARCHAR(50) NOT NULL,
            capacity_units INTEGER DEFAULT 100,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(warehouse_id, location_code)
        );

        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            sku VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            category_id INTEGER REFERENCES categories(id),
            supplier_id INTEGER REFERENCES suppliers(id),
            brand VARCHAR(100),
            model VARCHAR(100),
            barcode VARCHAR(50) UNIQUE,
            unit_of_measure VARCHAR(20) DEFAULT 'unidad',
            weight_kg DECIMAL(8,3),
            dimensions_length_cm DECIMAL(8,2),
            dimensions_width_cm DECIMAL(8,2),
            dimensions_height_cm DECIMAL(8,2),
            cost_price DECIMAL(12,2),
            sale_price DECIMAL(12,2),
            minimum_stock INTEGER DEFAULT 0,
            maximum_stock INTEGER DEFAULT 1000,
            reorder_point INTEGER DEFAULT 10,
            is_active BOOLEAN DEFAULT TRUE,
            requires_serial_number BOOLEAN DEFAULT FALSE,
            is_perishable BOOLEAN DEFAULT FALSE,
            expiration_days INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE product_locations (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
            quantity INTEGER NOT NULL DEFAULT 0,
            reserved_quantity INTEGER NOT NULL DEFAULT 0,
            available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_counted_at TIMESTAMP,
            UNIQUE(product_id, location_id),
            CONSTRAINT check_quantities CHECK (
                quantity >= 0 AND 
                reserved_quantity >= 0 AND 
                reserved_quantity <= quantity
            )
        );

        CREATE TABLE stock_movements (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id),
            location_id INTEGER NOT NULL REFERENCES locations(id),
            movement_type VARCHAR(20) NOT NULL,
            quantity INTEGER NOT NULL,
            previous_quantity INTEGER NOT NULL,
            new_quantity INTEGER NOT NULL,
            unit_cost DECIMAL(12,2),
            total_cost DECIMAL(12,2),
            reference_number VARCHAR(100),
            notes TEXT,
            user_id VARCHAR(100),
            user_name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT check_movement_quantity CHECK (quantity <> 0)
        );

        -- Índices optimizados
        CREATE INDEX idx_products_sku ON products(sku);
        CREATE INDEX idx_products_category ON products(category_id);
        CREATE INDEX idx_products_supplier ON products(supplier_id);
        CREATE INDEX idx_stock_movements_product ON stock_movements(product_id);
        CREATE INDEX idx_stock_movements_date ON stock_movements(created_at);
        CREATE INDEX idx_product_locations_composite ON product_locations(product_id, location_id);
        CREATE INDEX idx_locations_warehouse ON locations(warehouse_id);
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(schema_sql)
                logger.info("🏗️ Esquema creado")

    async def populate_data(self):
        # Categorías
        categories_data = [
            ('Alimentos y Bebidas', 'Productos alimenticios', None),
            ('Lácteos', 'Productos lácteos', 1),
            ('Carnes', 'Carnes frescas', 1),
            ('Bebidas', 'Bebidas varias', 1),
            ('Limpieza', 'Productos de limpieza', None),
            ('Electrónicos', 'Productos electrónicos', None),
            ('Indumentaria', 'Ropa y calzado', None),
            ('Herramientas', 'Herramientas varias', None)
        ]

        # Proveedores argentinos
        suppliers_data = [
            ('Distribuidora San Miguel S.A.', 'Carlos Rodriguez', 'carlos@sanmiguel.com.ar', 
             '011-4567-8900', 'Av. San Martín 1234', 'Buenos Aires', 'Buenos Aires', '1425', 'Argentina', '30-12345678-9'),
            ('Alimentos del Sur Ltda.', 'María González', 'maria@alimentosdelsur.com', 
             '0261-456-7890', 'Ruta 40 Km 15', 'Mendoza', 'Mendoza', '5500', 'Argentina', '30-87654321-0'),
            ('Electrónica Rosario S.R.L.', 'Juan Pérez', 'juan@electronicarosario.com', 
             '0341-234-5678', 'Córdoba 567', 'Rosario', 'Santa Fe', '2000', 'Argentina', '30-11111111-1')
        ]

        # Depósitos
        warehouses_data = [
            ('Depósito Central Buenos Aires', 'DCBA', 'Av. General Paz 5678', 'Buenos Aires', 
             'Buenos Aires', 'Carlos Mendoza', 'carlos@empresa.com', '011-1234-5678', True, 5000.00),
            ('Centro Distribución Rosario', 'CDR', 'Ruta A012 Km 45', 'Rosario', 
             'Santa Fe', 'María Sánchez', 'maria@empresa.com', '0341-987-6543', True, 3500.00)
        ]

        # Productos argentinos típicos
        products_data = [
            ('LAC001', 'Leche La Serenísima 1L', 'Leche entera pasteurizada', 2, 1, 'La Serenísima', 'Entera 1L', '7790070000001', 'litro', 1.03, 6.5, 6.5, 19.5, 180.50, 220.00, 10, 500, 20, True, False, True, 7),
            ('CAR001', 'Asado de Tira Kg', 'Asado de tira fresco', 3, 1, 'Frigorífico', 'Premium', '2000000000001', 'kilogramo', 1.00, 0.0, 0.0, 0.0, 1250.00, 1580.00, 5, 100, 10, True, False, True, 3),
            ('BEB001', 'Coca Cola 2.25L', 'Gaseosa cola', 4, 1, 'Coca Cola', '2.25L', '7790895000001', 'unidad', 2.30, 10.5, 10.5, 32.0, 285.75, 380.00, 20, 400, 40, True, False, False, 0),
            ('LIM001', 'Detergente Ala 750ml', 'Detergente limón', 5, 2, 'Ala', 'Limón 750ml', '7791293000001', 'unidad', 0.78, 8.5, 5.5, 21.0, 165.80, 220.00, 25, 200, 40, True, False, False, 0)
        ]

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Insertar categorías
                await conn.executemany(
                    "INSERT INTO categories (name, description, parent_id) VALUES ($1, $2, $3)",
                    categories_data
                )
                logger.info(f"📁 {len(categories_data)} categorías insertadas")

                # Insertar proveedores
                await conn.executemany("""
                    INSERT INTO suppliers (name, contact_person, email, phone, address, city, 
                                         province, postal_code, country, tax_id) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, suppliers_data)
                logger.info(f"🏢 {len(suppliers_data)} proveedores insertados")

                # Insertar depósitos
                await conn.executemany("""
                    INSERT INTO warehouses (name, code, address, city, province, manager_name, 
                                          manager_email, phone, is_active, capacity_cubic_meters) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, warehouses_data)
                logger.info(f"🏭 {len(warehouses_data)} depósitos insertados")

                # Crear ubicaciones
                locations_data = []
                for warehouse_id in [1, 2]:
                    for zone in ['A', 'B']:
                        for aisle in ['01', '02', '03']:
                            for rack in ['R1', 'R2']:
                                for shelf in ['S1', 'S2']:
                                    location_code = f"{zone}-{aisle}-{rack}-{shelf}"
                                    locations_data.append((
                                        warehouse_id, zone, aisle, rack, shelf, None,
                                        location_code, 100, True
                                    ))

                await conn.executemany("""
                    INSERT INTO locations (warehouse_id, zone, aisle, rack, shelf, position, 
                                         location_code, capacity_units, is_active) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, locations_data)
                logger.info(f"📍 {len(locations_data)} ubicaciones insertadas")

                # Insertar productos
                await conn.executemany("""
                    INSERT INTO products (sku, name, description, category_id, supplier_id, brand, model, 
                                        barcode, unit_of_measure, weight_kg, dimensions_length_cm, 
                                        dimensions_width_cm, dimensions_height_cm, cost_price, sale_price, 
                                        minimum_stock, maximum_stock, reorder_point, is_active, 
                                        requires_serial_number, is_perishable, expiration_days) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)
                """, products_data)
                logger.info(f"📦 {len(products_data)} productos insertados")

                # Stock inicial
                stock_data = []
                for product_id in range(1, 5):
                    for location_id in range(1, 11):
                        quantity = random.randint(50, 300)
                        reserved = random.randint(0, 20)
                        stock_data.append((product_id, location_id, quantity, reserved))

                await conn.executemany("""
                    INSERT INTO product_locations (product_id, location_id, quantity, reserved_quantity) 
                    VALUES ($1, $2, $3, $4)
                """, stock_data)
                logger.info(f"📊 {len(stock_data)} registros de stock inicial")

    async def initialize_database(self, reset: bool = False, verbose: bool = False):
        start_time = datetime.now()
        logger.info(f"🚀 Iniciando inicialización - {start_time}")

        try:
            await self.create_connection_pool()

            if reset:
                logger.info("🔄 Modo reset - eliminando datos existentes")
                await self.drop_all_tables()

            logger.info("📋 Creando esquema...")
            await self.create_schema()

            logger.info("📋 Poblando datos...")
            await self.populate_data()

            end_time = datetime.now()
            duration = end_time - start_time

            logger.info(f"✅ Inicialización completada en {duration}")
            return True

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise
        finally:
            await self.close_pool()

async def main():
    parser = argparse.ArgumentParser(description='Inicializar BD del sistema de inventario')
    parser.add_argument('--reset', action='store_true', help='Eliminar y recrear tablas')
    parser.add_argument('--verbose', action='store_true', help='Información detallada')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        initializer = DatabaseInitializer(DATABASE_CONFIG)
        success = await initializer.initialize_database(reset=args.reset, verbose=args.verbose)

        if success:
            print("\n🎉 ¡Base de datos inicializada exitosamente!")
            print("\n📋 Resumen:")
            print("  • Esquema completo creado con índices optimizados")
            print("  • Datos de ejemplo argentinos insertados")
            print("  • Stock inicial distribuido")
            print("\n🚀 El sistema está listo para usar!")
            return 0
        else:
            print("\n❌ La inicialización falló.")
            return 1

    except Exception as e:
        logger.error(f"Error fatal: {e}")
        print(f"\n💥 Error fatal: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
