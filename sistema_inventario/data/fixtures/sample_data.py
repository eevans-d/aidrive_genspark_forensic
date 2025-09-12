#!/usr/bin/env python3
"""
Sistema de Gestión de Inventario - Generador de Datos de Test
Archivo: data/fixtures/sample_data.py

Descripción:
Generador inteligente de datos de prueba para el sistema de inventario.
Crea datos realistas con patrones de uso típicos, distribución estadística
correcta y relaciones consistentes entre entidades.

Características:
- Generación masiva de datos de test escalable
- Distribución estadística realista de productos por categoría
- Simulación de patrones de movimiento de stock reales
- Generación de transacciones históricas con fechas coherentes
- Validación automática de integridad referencial
- Soporte para diferentes escenarios de testing
- Métricas de generación y validación de datos
"""

import asyncio
import asyncpg
import logging
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
import os
import sys
from dataclasses import dataclass
from enum import Enum
import json
import argparse

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'inventario_system'), 
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres123')
}

class DataScale(Enum):
    """Escalas de datos para diferentes escenarios de testing."""
    SMALL = "small"      # 100 productos, 10 ubicaciones
    MEDIUM = "medium"    # 1,000 productos, 100 ubicaciones  
    LARGE = "large"      # 10,000 productos, 1,000 ubicaciones
    XLARGE = "xlarge"    # 100,000 productos, 10,000 ubicaciones

@dataclass
class GenerationConfig:
    """Configuración para generación de datos."""
    scale: DataScale
    num_warehouses: int
    num_products: int
    num_locations: int
    num_suppliers: int
    num_categories: int
    stock_movements_days: int = 365  # Días de historial

    @classmethod
    def get_config(cls, scale: DataScale) -> 'GenerationConfig':
        """Obtener configuración predefinida según escala."""
        configs = {
            DataScale.SMALL: cls(
                scale=scale,
                num_warehouses=2,
                num_products=100,
                num_locations=50,
                num_suppliers=10,
                num_categories=20,
                stock_movements_days=90
            ),
            DataScale.MEDIUM: cls(
                scale=scale,
                num_warehouses=5,
                num_products=1000,
                num_locations=500,
                num_suppliers=50,
                num_categories=50,
                stock_movements_days=180
            ),
            DataScale.LARGE: cls(
                scale=scale,
                num_warehouses=10,
                num_products=10000,
                num_locations=5000,
                num_suppliers=200,
                num_categories=100,
                stock_movements_days=365
            ),
            DataScale.XLARGE: cls(
                scale=scale,
                num_warehouses=25,
                num_products=100000,
                num_locations=50000,
                num_suppliers=1000,
                num_categories=200,
                stock_movements_days=730
            )
        }
        return configs[scale]

class SampleDataGenerator:
    """
    Generador avanzado de datos de prueba para el sistema de inventario.
    """

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

        # Caches para IDs generados
        self.category_ids: List[int] = []
        self.supplier_ids: List[int] = []
        self.warehouse_ids: List[int] = []
        self.location_ids: List[int] = []
        self.product_ids: List[int] = []

        # Datos base para generación
        self.brands = [
            'La Serenísima', 'Arcor', 'Coca Cola', 'Quilmes', 'Unilever',
            'Molinos', 'Sancor', 'Danone', 'Nestlé', 'Mastellone',
            'Bagley', 'Terrabusi', 'Bimbo', 'Frigorífico', 'Swift'
        ]

        self.categories_base = [
            ('Alimentos', ['Lácteos', 'Carnes', 'Panadería', 'Conservas']),
            ('Bebidas', ['Gaseosas', 'Jugos', 'Aguas', 'Cervezas']),
            ('Limpieza', ['Detergentes', 'Desinfectantes', 'Papel']),
            ('Cuidado Personal', ['Higiene', 'Cosmética', 'Perfumería']),
            ('Hogar', ['Decoración', 'Textil', 'Cocina']),
            ('Electrónicos', ['Audio', 'Video', 'Computación']),
            ('Ropa', ['Hombre', 'Mujer', 'Niños', 'Calzado']),
            ('Deportes', ['Fitness', 'Fútbol', 'Natación']),
            ('Juguetes', ['Educativos', 'Electrónicos', 'Tradicionales']),
            ('Librería', ['Escolares', 'Oficina', 'Arte'])
        ]

        self.provinces = [
            'Buenos Aires', 'Córdoba', 'Santa Fe', 'Mendoza', 'Tucumán',
            'Entre Ríos', 'Salta', 'Chaco', 'Corrientes', 'Misiones',
            'San Juan', 'Jujuy', 'Río Negro', 'Formosa', 'Neuquén',
            'Chubut', 'San Luis', 'Catamarca', 'La Rioja', 'La Pampa',
            'Santiago del Estero', 'Santa Cruz', 'Tierra del Fuego'
        ]

        self.cities = {
            'Buenos Aires': ['Buenos Aires', 'La Plata', 'Mar del Plata', 'Bahía Blanca'],
            'Córdoba': ['Córdoba', 'Villa Carlos Paz', 'Río Cuarto'],
            'Santa Fe': ['Santa Fe', 'Rosario', 'Rafaela'],
            'Mendoza': ['Mendoza', 'San Rafael', 'Godoy Cruz'],
            'Tucumán': ['San Miguel de Tucumán', 'Tafí Viejo']
        }

    async def connect(self):
        """Conectar a la base de datos."""
        try:
            self.pool = await asyncpg.create_pool(**DATABASE_CONFIG)
            logger.info("✅ Conectado a la base de datos")
        except Exception as e:
            logger.error(f"❌ Error conectando: {e}")
            raise

    async def disconnect(self):
        """Desconectar de la base de datos."""
        if self.pool:
            await self.pool.close()
            logger.info("🔒 Conexión cerrada")

    def generate_sku(self, category_prefix: str = None) -> str:
        """Generar SKU único."""
        if not category_prefix:
            category_prefix = random.choice(['ALM', 'BEB', 'LIM', 'HIG', 'HOG', 'ELE', 'ROP', 'DEP'])

        number = ''.join(random.choices(string.digits, k=4))
        return f"{category_prefix}{number}"

    def generate_barcode(self) -> str:
        """Generar código de barras EAN-13 válido."""
        # Prefijo para Argentina (779)
        country = "779"
        company = ''.join(random.choices(string.digits, k=4))
        product = ''.join(random.choices(string.digits, k=5))

        # Calcular dígito de control
        partial = country + company + product
        odd_sum = sum(int(partial[i]) for i in range(0, 12, 2))
        even_sum = sum(int(partial[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10

        return partial + str(check_digit)

    def generate_cuit(self) -> str:
        """Generar CUIT válido."""
        base = ''.join(random.choices(string.digits, k=8))
        # Simplificado: siempre empresa (30)
        return f"30-{base}-{random.randint(0, 9)}"

    async def clean_existing_data(self):
        """Limpiar datos existentes."""
        logger.info("🧹 Limpiando datos existentes...")

        clean_queries = [
            "TRUNCATE TABLE stock_movements RESTART IDENTITY CASCADE",
            "TRUNCATE TABLE product_locations RESTART IDENTITY CASCADE", 
            "TRUNCATE TABLE products RESTART IDENTITY CASCADE",
            "TRUNCATE TABLE locations RESTART IDENTITY CASCADE",
            "TRUNCATE TABLE warehouses RESTART IDENTITY CASCADE",
            "TRUNCATE TABLE suppliers RESTART IDENTITY CASCADE",
            "TRUNCATE TABLE categories RESTART IDENTITY CASCADE"
        ]

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for query in clean_queries:
                    await conn.execute(query)

        logger.info("✅ Datos limpiados")

    async def generate_categories(self):
        """Generar categorías jerárquicas."""
        logger.info(f"📁 Generando {self.config.num_categories} categorías...")

        categories_data = []
        category_id = 1

        # Generar categorías principales y subcategorías
        for main_cat, subcats in self.categories_base:
            if category_id > self.config.num_categories:
                break

            # Categoría principal
            categories_data.append((
                category_id,
                main_cat,
                f"Productos de {main_cat.lower()}",
                None
            ))
            main_id = category_id
            category_id += 1

            # Subcategorías
            for subcat in subcats:
                if category_id > self.config.num_categories:
                    break

                categories_data.append((
                    category_id,
                    subcat,
                    f"Productos de {subcat.lower()}",
                    main_id
                ))
                category_id += 1

        # Completar con categorías adicionales si es necesario
        while len(categories_data) < self.config.num_categories:
            categories_data.append((
                category_id,
                f"Categoría {category_id}",
                f"Categoría generada {category_id}",
                random.choice([None] + [c[0] for c in categories_data[:10]])
            ))
            category_id += 1

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany("""
                    INSERT INTO categories (id, name, description, parent_id)
                    VALUES ($1, $2, $3, $4)
                """, categories_data)

        self.category_ids = [c[0] for c in categories_data]
        logger.info(f"✅ {len(categories_data)} categorías generadas")

    async def generate_suppliers(self):
        """Generar proveedores."""
        logger.info(f"🏢 Generando {self.config.num_suppliers} proveedores...")

        suppliers_data = []

        for i in range(1, self.config.num_suppliers + 1):
            province = random.choice(self.provinces)
            city = random.choice(self.cities.get(province, [province]))

            suppliers_data.append((
                i,
                f"Proveedor {i} S.A.",
                f"Contacto {i}",
                f"contacto{i}@proveedor{i}.com.ar",
                f"0{random.randint(11, 388)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                f"Dirección {i} {random.randint(100, 9999)}",
                city,
                province,
                f"{random.randint(1000, 9999)}",
                "Argentina",
                self.generate_cuit(),
                True
            ))

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany("""
                    INSERT INTO suppliers (id, name, contact_person, email, phone, address, 
                                         city, province, postal_code, country, tax_id, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """, suppliers_data)

        self.supplier_ids = [s[0] for s in suppliers_data]
        logger.info(f"✅ {len(suppliers_data)} proveedores generados")

    async def generate_warehouses(self):
        """Generar depósitos."""
        logger.info(f"🏭 Generando {self.config.num_warehouses} depósitos...")

        warehouses_data = []

        for i in range(1, self.config.num_warehouses + 1):
            province = random.choice(self.provinces)
            city = random.choice(self.cities.get(province, [province]))

            warehouses_data.append((
                i,
                f"Depósito {city} {i}",
                f"DEP{i:02d}",
                f"Zona Industrial {i}",
                city,
                province,
                f"Manager {i}",
                f"manager{i}@empresa.com",
                f"0{random.randint(11, 388)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                True,
                round(random.uniform(1000, 10000), 2)
            ))

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany("""
                    INSERT INTO warehouses (id, name, code, address, city, province, 
                                          manager_name, manager_email, phone, is_active, capacity_cubic_meters)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, warehouses_data)

        self.warehouse_ids = [w[0] for w in warehouses_data]
        logger.info(f"✅ {len(warehouses_data)} depósitos generados")

    async def generate_locations(self):
        """Generar ubicaciones en depósitos."""
        logger.info(f"📍 Generando {self.config.num_locations} ubicaciones...")

        locations_data = []
        location_id = 1

        locations_per_warehouse = self.config.num_locations // self.config.num_warehouses

        zones = ['A', 'B', 'C', 'D', 'E']
        aisles = [f"{i:02d}" for i in range(1, 21)]
        racks = [f"R{i}" for i in range(1, 11)]
        shelves = [f"S{i}" for i in range(1, 6)]
        positions = [f"P{i}" for i in range(1, 4)]

        for warehouse_id in self.warehouse_ids:
            count = 0
            while count < locations_per_warehouse and location_id <= self.config.num_locations:
                zone = random.choice(zones)
                aisle = random.choice(aisles)
                rack = random.choice(racks)
                shelf = random.choice(shelves)
                position = random.choice(positions)

                location_code = f"{zone}-{aisle}-{rack}-{shelf}-{position}"

                locations_data.append((
                    location_id,
                    warehouse_id,
                    zone,
                    aisle,
                    rack,
                    shelf,
                    position,
                    location_code,
                    random.randint(50, 200),
                    True
                ))

                location_id += 1
                count += 1

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany("""
                    INSERT INTO locations (id, warehouse_id, zone, aisle, rack, shelf, position,
                                         location_code, capacity_units, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, locations_data)

        self.location_ids = [l[0] for l in locations_data]
        logger.info(f"✅ {len(locations_data)} ubicaciones generadas")

    async def generate_products(self):
        """Generar productos."""
        logger.info(f"📦 Generando {self.config.num_products} productos...")

        products_data = []

        for i in range(1, self.config.num_products + 1):
            category_id = random.choice(self.category_ids)
            supplier_id = random.choice(self.supplier_ids)
            brand = random.choice(self.brands)

            is_perishable = random.choice([True, False])
            expiration_days = random.randint(7, 365) if is_perishable else None

            cost_price = round(random.uniform(50, 2000), 2)
            sale_price = round(cost_price * random.uniform(1.3, 2.5), 2)

            products_data.append((
                i,
                self.generate_sku(),
                f"Producto {brand} {i}",
                f"Descripción del producto {i}",
                category_id,
                supplier_id,
                brand,
                f"Modelo {i}",
                self.generate_barcode(),
                random.choice(['unidad', 'kilogramo', 'litro', 'metro']),
                round(random.uniform(0.1, 5.0), 3),
                round(random.uniform(5, 50), 2),
                round(random.uniform(5, 50), 2),
                round(random.uniform(1, 30), 2),
                cost_price,
                sale_price,
                random.randint(5, 50),
                random.randint(100, 1000),
                random.randint(10, 100),
                True,
                random.choice([True, False]),
                is_perishable,
                expiration_days
            ))

        # Insertar en lotes para mejor performance
        batch_size = 1000
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for i in range(0, len(products_data), batch_size):
                    batch = products_data[i:i + batch_size]
                    await conn.executemany("""
                        INSERT INTO products (id, sku, name, description, category_id, supplier_id,
                                            brand, model, barcode, unit_of_measure, weight_kg,
                                            dimensions_length_cm, dimensions_width_cm, dimensions_height_cm,
                                            cost_price, sale_price, minimum_stock, maximum_stock, reorder_point,
                                            is_active, requires_serial_number, is_perishable, expiration_days)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23)
                    """, batch)

        self.product_ids = [p[0] for p in products_data]
        logger.info(f"✅ {len(products_data)} productos generados")

    async def generate_initial_stock(self):
        """Generar stock inicial."""
        logger.info("📊 Generando stock inicial...")

        stock_data = []

        # Distribución: 70% de productos con stock, 30% sin stock
        products_with_stock = random.sample(self.product_ids, int(len(self.product_ids) * 0.7))

        for product_id in products_with_stock:
            # Cada producto en 1-5 ubicaciones
            num_locations = random.randint(1, min(5, len(self.location_ids)))
            selected_locations = random.sample(self.location_ids, num_locations)

            for location_id in selected_locations:
                quantity = random.randint(10, 500)
                reserved = random.randint(0, min(20, quantity // 4))

                stock_data.append((
                    product_id,
                    location_id,
                    quantity,
                    reserved
                ))

        # Insertar en lotes
        batch_size = 1000
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for i in range(0, len(stock_data), batch_size):
                    batch = stock_data[i:i + batch_size]
                    await conn.executemany("""
                        INSERT INTO product_locations (product_id, location_id, quantity, reserved_quantity)
                        VALUES ($1, $2, $3, $4)
                    """, batch)

        logger.info(f"✅ {len(stock_data)} registros de stock inicial generados")

    async def generate_stock_movements(self):
        """Generar movimientos de stock históricos."""
        logger.info(f"📈 Generando movimientos de stock ({self.config.stock_movements_days} días)...")

        movements_data = []
        movement_id = 1

        # Obtener stock actual
        async with self.pool.acquire() as conn:
            stock_records = await conn.fetch("""
                SELECT product_id, location_id, quantity 
                FROM product_locations
            """)

        # Generar movimientos históricos
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.config.stock_movements_days)

        movement_types = ['IN', 'OUT', 'TRANSFER', 'ADJUSTMENT']

        for _ in range(len(stock_records) * 10):  # ~10 movimientos por registro de stock
            current_date = start_date + timedelta(
                seconds=random.randint(0, int((end_date - start_date).total_seconds()))
            )

            stock_record = random.choice(stock_records)
            movement_type = random.choice(movement_types)

            if movement_type == 'IN':
                quantity = random.randint(1, 100)
                previous_qty = random.randint(0, 200)
                new_qty = previous_qty + quantity
            elif movement_type == 'OUT':
                quantity = random.randint(-100, -1)
                previous_qty = random.randint(abs(quantity), 300)
                new_qty = previous_qty + quantity
            else:  # TRANSFER, ADJUSTMENT
                quantity = random.randint(-50, 50)
                previous_qty = random.randint(50, 200)
                new_qty = max(0, previous_qty + quantity)

            movements_data.append((
                movement_id,
                stock_record['product_id'],
                stock_record['location_id'],
                movement_type,
                quantity,
                previous_qty,
                new_qty,
                round(random.uniform(10, 500), 2),
                round(random.uniform(10, 500) * abs(quantity), 2),
                f"REF{movement_id:06d}",
                f"Movimiento {movement_type.lower()} generado",
                f"user{random.randint(1, 10)}",
                f"Usuario {random.randint(1, 10)}",
                current_date
            ))

            movement_id += 1

            if len(movements_data) >= 50000:  # Limitar para evitar exceso de datos
                break

        # Insertar en lotes
        batch_size = 1000
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for i in range(0, len(movements_data), batch_size):
                    batch = movements_data[i:i + batch_size]
                    await conn.executemany("""
                        INSERT INTO stock_movements (id, product_id, location_id, movement_type,
                                                   quantity, previous_quantity, new_quantity,
                                                   unit_cost, total_cost, reference_number, notes,
                                                   user_id, user_name, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    """, batch)

        logger.info(f"✅ {len(movements_data)} movimientos de stock generados")

    async def update_sequences(self):
        """Actualizar secuencias de la base de datos."""
        logger.info("🔄 Actualizando secuencias...")

        async with self.pool.acquire() as conn:
            await conn.execute("SELECT setval('categories_id_seq', (SELECT MAX(id) FROM categories))")
            await conn.execute("SELECT setval('suppliers_id_seq', (SELECT MAX(id) FROM suppliers))")
            await conn.execute("SELECT setval('warehouses_id_seq', (SELECT MAX(id) FROM warehouses))")
            await conn.execute("SELECT setval('locations_id_seq', (SELECT MAX(id) FROM locations))")
            await conn.execute("SELECT setval('products_id_seq', (SELECT MAX(id) FROM products))")
            await conn.execute("SELECT setval('product_locations_id_seq', (SELECT MAX(id) FROM product_locations))")
            await conn.execute("SELECT setval('stock_movements_id_seq', (SELECT MAX(id) FROM stock_movements))")

        logger.info("✅ Secuencias actualizadas")

    async def validate_data_integrity(self):
        """Validar integridad de los datos generados."""
        logger.info("🔍 Validando integridad de datos...")

        async with self.pool.acquire() as conn:
            # Verificar conteos
            categories_count = await conn.fetchval("SELECT COUNT(*) FROM categories")
            suppliers_count = await conn.fetchval("SELECT COUNT(*) FROM suppliers")
            warehouses_count = await conn.fetchval("SELECT COUNT(*) FROM warehouses")
            locations_count = await conn.fetchval("SELECT COUNT(*) FROM locations")
            products_count = await conn.fetchval("SELECT COUNT(*) FROM products")
            stock_count = await conn.fetchval("SELECT COUNT(*) FROM product_locations")
            movements_count = await conn.fetchval("SELECT COUNT(*) FROM stock_movements")

            # Verificar integridad referencial
            orphaned_products = await conn.fetchval("""
                SELECT COUNT(*) FROM products p 
                WHERE p.category_id NOT IN (SELECT id FROM categories)
                   OR p.supplier_id NOT IN (SELECT id FROM suppliers)
            """)

            orphaned_locations = await conn.fetchval("""
                SELECT COUNT(*) FROM locations l 
                WHERE l.warehouse_id NOT IN (SELECT id FROM warehouses)
            """)

            orphaned_stock = await conn.fetchval("""
                SELECT COUNT(*) FROM product_locations pl 
                WHERE pl.product_id NOT IN (SELECT id FROM products)
                   OR pl.location_id NOT IN (SELECT id FROM locations)
            """)

            # Reporte de validación
            validation_report = {
                "counts": {
                    "categories": categories_count,
                    "suppliers": suppliers_count,
                    "warehouses": warehouses_count,
                    "locations": locations_count,
                    "products": products_count,
                    "stock_records": stock_count,
                    "stock_movements": movements_count
                },
                "integrity": {
                    "orphaned_products": orphaned_products,
                    "orphaned_locations": orphaned_locations,
                    "orphaned_stock": orphaned_stock
                }
            }

            logger.info("📊 Reporte de validación:")
            logger.info(f"  • Categorías: {categories_count}")
            logger.info(f"  • Proveedores: {suppliers_count}")
            logger.info(f"  • Depósitos: {warehouses_count}")
            logger.info(f"  • Ubicaciones: {locations_count}")
            logger.info(f"  • Productos: {products_count}")
            logger.info(f"  • Registros de stock: {stock_count}")
            logger.info(f"  • Movimientos: {movements_count}")

            if orphaned_products == orphaned_locations == orphaned_stock == 0:
                logger.info("✅ Integridad referencial: OK")
            else:
                logger.warning(f"⚠️ Problemas de integridad detectados")
                logger.warning(f"  • Productos huérfanos: {orphaned_products}")
                logger.warning(f"  • Ubicaciones huérfanas: {orphaned_locations}")
                logger.warning(f"  • Stock huérfano: {orphaned_stock}")

            return validation_report

    async def generate_all_data(self, clean_first: bool = True):
        """Generar todos los datos de prueba."""
        start_time = datetime.now()
        logger.info(f"🚀 Iniciando generación de datos - Escala: {self.config.scale.value}")

        try:
            await self.connect()

            if clean_first:
                await self.clean_existing_data()

            # Generar datos en orden de dependencias
            await self.generate_categories()
            await self.generate_suppliers()
            await self.generate_warehouses()
            await self.generate_locations()
            await self.generate_products()
            await self.generate_initial_stock()
            await self.generate_stock_movements()

            # Finalizar
            await self.update_sequences()
            validation_report = await self.validate_data_integrity()

            end_time = datetime.now()
            duration = end_time - start_time

            logger.info(f"✅ Generación completada en {duration}")
            logger.info("🎉 ¡Datos de prueba listos para usar!")

            return validation_report

        except Exception as e:
            logger.error(f"❌ Error durante la generación: {e}")
            raise
        finally:
            await self.disconnect()

async def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Generar datos de prueba para el sistema de inventario')
    parser.add_argument('--scale', choices=['small', 'medium', 'large', 'xlarge'], 
                       default='medium', help='Escala de datos a generar')
    parser.add_argument('--no-clean', action='store_true', 
                       help='No limpiar datos existentes')
    parser.add_argument('--verbose', action='store_true', 
                       help='Mostrar información detallada')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        scale = DataScale(args.scale)
        config = GenerationConfig.get_config(scale)

        generator = SampleDataGenerator(config)
        report = await generator.generate_all_data(clean_first=not args.no_clean)

        print("\n📊 RESUMEN DE GENERACIÓN:")
        print(f"  • Escala: {scale.value.upper()}")
        print(f"  • Categorías: {report['counts']['categories']}")
        print(f"  • Proveedores: {report['counts']['suppliers']}")
        print(f"  • Depósitos: {report['counts']['warehouses']}")
        print(f"  • Ubicaciones: {report['counts']['locations']}")
        print(f"  • Productos: {report['counts']['products']}")
        print(f"  • Stock inicial: {report['counts']['stock_records']}")
        print(f"  • Movimientos: {report['counts']['stock_movements']}")

        if all(v == 0 for v in report['integrity'].values()):
            print("\n✅ DATOS GENERADOS CORRECTAMENTE")
        else:
            print("\n⚠️ ADVERTENCIAS DE INTEGRIDAD")
            for key, value in report['integrity'].items():
                if value > 0:
                    print(f"  • {key}: {value}")

        return 0

    except Exception as e:
        logger.error(f"Error fatal: {e}")
        print(f"\n💥 Error fatal: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
