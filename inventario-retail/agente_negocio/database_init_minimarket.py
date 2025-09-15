#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Inicialización de Base de Datos - Sistema Mini Market
==============================================================

Este script inicializa las tablas necesarias para el sistema de proveedores
Mini Market con los 12 proveedores configurados y sus categorías.

Autor: Sistema Multiagente
Fecha: 2025-01-18
Versión: 1.0
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Importar la configuración de proveedores
from provider_logic import MiniMarketProviderLogic

class MiniMarketDatabaseInitializer:
    """Inicializador de base de datos para el sistema Mini Market"""
    
    def __init__(self, db_path: str = "minimarket_inventory.db"):
        """
        Inicializa el inicializador de base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.provider_logic = MiniMarketProviderLogic()
        
    def create_database_schema(self) -> bool:
        """
        Crea el esquema completo de la base de datos
        
        Returns:
            bool: True si fue exitoso, False si hubo errores
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 1. Tabla de Proveedores
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS proveedores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT UNIQUE NOT NULL,
                        nombre TEXT NOT NULL,
                        contacto TEXT,
                        telefono TEXT,
                        email TEXT,
                        direccion TEXT,
                        activo BOOLEAN DEFAULT 1,
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        configuracion_json TEXT,
                        UNIQUE(codigo)
                    )
                """)
                
                # 2. Tabla de Categorías de Productos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categorias (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT UNIQUE NOT NULL,
                        descripcion TEXT,
                        activo BOOLEAN DEFAULT 1
                    )
                """)
                
                # 3. Tabla de Productos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS productos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        descripcion TEXT,
                        categoria_id INTEGER,
                        proveedor_id INTEGER,
                        codigo_barras TEXT,
                        precio_compra DECIMAL(10,2),
                        precio_venta DECIMAL(10,2),
                        stock_actual INTEGER DEFAULT 0,
                        stock_minimo INTEGER DEFAULT 5,
                        activo BOOLEAN DEFAULT 1,
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                        FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
                    )
                """)
                
                # 4. Tabla de Pedidos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pedidos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        proveedor_id INTEGER NOT NULL,
                        numero_pedido TEXT,
                        fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        estado TEXT DEFAULT 'pendiente',
                        total DECIMAL(10,2) DEFAULT 0.00,
                        observaciones TEXT,
                        fecha_entrega_esperada DATE,
                        fecha_entrega_real DATE,
                        FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
                    )
                """)
                
                # 5. Tabla de Detalles de Pedido
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detalle_pedidos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pedido_id INTEGER NOT NULL,
                        producto_nombre TEXT NOT NULL,
                        cantidad INTEGER NOT NULL,
                        precio_unitario DECIMAL(10,2),
                        subtotal DECIMAL(10,2),
                        observaciones TEXT,
                        FOREIGN KEY (pedido_id) REFERENCES pedidos (id)
                    )
                """)
                
                # 6. Tabla de Movimientos de Stock
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS movimientos_stock (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        producto_id INTEGER,
                        producto_nombre TEXT NOT NULL,
                        tipo_movimiento TEXT NOT NULL,
                        cantidad INTEGER NOT NULL,
                        precio_unitario DECIMAL(10,2),
                        proveedor_id INTEGER,
                        origen TEXT,
                        destino TEXT,
                        observaciones TEXT,
                        fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        usuario TEXT,
                        FOREIGN KEY (producto_id) REFERENCES productos (id),
                        FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
                    )
                """)
                
                # 7. Tabla de Facturas OCR
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS facturas_ocr (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        numero_factura TEXT NOT NULL,
                        proveedor_original TEXT,
                        proveedor_asignado_id INTEGER,
                        fecha_factura DATE,
                        total DECIMAL(10,2),
                        contenido_ocr TEXT,
                        productos_json TEXT,
                        procesado BOOLEAN DEFAULT 0,
                        fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (proveedor_asignado_id) REFERENCES proveedores (id)
                    )
                """)
                
                # 8. Tabla de Configuración del Sistema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS configuracion_sistema (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        clave TEXT UNIQUE NOT NULL,
                        valor TEXT NOT NULL,
                        descripcion TEXT,
                        fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Crear índices para optimizar consultas
                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria_id)",
                    "CREATE INDEX IF NOT EXISTS idx_productos_proveedor ON productos(proveedor_id)",
                    "CREATE INDEX IF NOT EXISTS idx_pedidos_proveedor ON pedidos(proveedor_id)",
                    "CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON pedidos(fecha_pedido)",
                    "CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_stock(fecha_movimiento)",
                    "CREATE INDEX IF NOT EXISTS idx_movimientos_producto ON movimientos_stock(producto_id)",
                    "CREATE INDEX IF NOT EXISTS idx_facturas_proveedor ON facturas_ocr(proveedor_asignado_id)"
                ]
                
                for indice in indices:
                    cursor.execute(indice)
                
                conn.commit()
                print("✅ Esquema de base de datos creado exitosamente")
                return True
                
        except Exception as e:
            print(f"❌ Error creando esquema: {e}")
            return False
    
    def insert_initial_providers(self) -> bool:
        """
        Inserta los 12 proveedores iniciales del Mini Market
        
        Returns:
            bool: True si fue exitoso, False si hubo errores
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener configuración de proveedores
                providers_config = self.provider_logic.PROVIDERS
                
                # Información adicional de contacto (simulada)
                contact_info = {
                    'BC': {
                        'contacto': 'Juan Carlos Viticultor',
                        'telefono': '011-4567-8900',
                        'email': 'ventas@bodegacedeira.com.ar',
                        'direccion': 'Ruta Nacional 40 Km 1050, Mendoza'
                    },
                    'CO': {
                        'contacto': 'María González',
                        'telefono': '011-4555-7890',
                        'email': 'distribuidores@cocacola.com.ar',
                        'direccion': 'Av. del Libertador 7635, CABA'
                    },
                    'Q': {
                        'contacto': 'Roberto Maldonado',
                        'telefono': '011-4333-5678',
                        'email': 'ventas@quilmes.com.ar',
                        'direccion': 'Ruta 2 Km 35, Quilmes'
                    },
                    'FA': {
                        'contacto': 'Ana Pérez',
                        'telefono': '011-4777-1234',
                        'email': 'comercial@fargo.com.ar',
                        'direccion': 'Parque Industrial Sur, Lote 15, Córdoba'
                    },
                    'LS': {
                        'contacto': 'Carlos Lechero',
                        'telefono': '011-4888-9999',
                        'email': 'distribuciones@laserenisima.com.ar',
                        'direccion': 'Ruta 5 Km 60, General Rodríguez'
                    },
                    'ACE': {
                        'contacto': 'Miguel Olivares',
                        'telefono': '0223-456-7890',
                        'email': 'ventas@aceitumar.com.ar',
                        'direccion': 'Zona Industrial, Mar del Plata'
                    },
                    'TER': {
                        'contacto': 'Laura Galletitas',
                        'telefono': '011-4222-3333',
                        'email': 'pedidos@terrabusi.com.ar',
                        'direccion': 'Av. Juan B. Justo 1234, CABA'
                    },
                    'LV': {
                        'contacto': 'Pedro Virginia',
                        'telefono': '011-4999-8888',
                        'email': 'comercial@lavirginia.com.ar',
                        'direccion': 'Zona Norte Industrial, San Isidro'
                    },
                    'FR': {
                        'contacto': 'Diego Bicho',
                        'telefono': '011-4111-2222',
                        'email': 'pedidos@frutasyverdurasbicho.com.ar',
                        'direccion': 'Mercado Central, Nave 15-16'
                    },
                    'MU': {
                        'contacto': 'Sandra Envases',  
                        'telefono': '011-4666-7777',
                        'email': 'ventas@multienvase.com.ar',
                        'direccion': 'Zona Industrial Oeste, Morón'
                    },
                    'GA': {
                        'contacto': 'Ricardo Galletas',
                        'telefono': '011-4444-5555',
                        'email': 'distribuciones@galletitera.com.ar',
                        'direccion': 'Parque Industrial Norte, Tigre'
                    },
                    'MAX': {
                        'contacto': 'Sofía Maxiconsumo',
                        'telefono': '011-4123-4567',
                        'email': 'mayorista@maxiconsumo.com.ar',
                        'direccion': 'Centro de Distribución Sur, Lanús'
                    }
                }
                
                providers_inserted = 0
                
                for codigo, config in providers_config.items():
                    contact = contact_info.get(codigo, {})
                    
                    # Convertir configuración a JSON
                    config_json = json.dumps(config, ensure_ascii=False)
                    
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO proveedores 
                            (codigo, nombre, contacto, telefono, email, direccion, configuracion_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            codigo,
                            config['name'],  # Corregido: 'name' en lugar de 'nombre'
                            contact.get('contacto', ''),
                            contact.get('telefono', ''),
                            contact.get('email', ''),
                            contact.get('direccion', ''),
                            config_json
                        ))
                        providers_inserted += 1
                        
                    except Exception as e:
                        print(f"⚠️  Error insertando proveedor {codigo}: {e}")
                
                conn.commit()
                print(f"✅ {providers_inserted} proveedores insertados exitosamente")
                return True
                
        except Exception as e:
            print(f"❌ Error insertando proveedores: {e}")
            return False
    
    def insert_initial_categories(self) -> bool:
        """
        Inserta las categorías iniciales de productos
        
        Returns:
            bool: True si fue exitoso, False si hubo errores
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Categorías basadas en la configuración de proveedores
                categorias = [
                    ('bebida', 'Bebidas sin alcohol (gaseosas, aguas, jugos)'),
                    ('bebida alcoholica', 'Bebidas alcohólicas (vinos, cervezas, licores)'),
                    ('lacteo', 'Productos lácteos (leche, yogurt, quesos)'),
                    ('conserva', 'Conservas y enlatados'),
                    ('galletita', 'Galletitas y productos de panadería'),
                    ('fruta', 'Frutas frescas y verduras'),
                    ('verdura', 'Verduras y hortalizas frescas'),
                    ('fiambre', 'Fiambres y embutidos'),
                    ('carne', 'Carnes frescas y congeladas'),
                    ('congelado', 'Productos congelados'),
                    ('limpieza', 'Productos de limpieza e higiene'),
                    ('higiene', 'Productos de higiene personal'),
                    ('kiosco', 'Productos de kiosco (golosinas, snacks)'),
                    ('panaderia', 'Productos de panadería'),
                    ('otros', 'Otros productos no clasificados')
                ]
                
                categories_inserted = 0
                
                for nombre, descripcion in categorias:
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO categorias (nombre, descripcion)
                            VALUES (?, ?)
                        """, (nombre, descripcion))
                        categories_inserted += 1
                    except Exception as e:
                        print(f"⚠️  Error insertando categoría {nombre}: {e}")
                
                conn.commit()
                print(f"✅ {categories_inserted} categorías insertadas exitosamente")
                return True
                
        except Exception as e:
            print(f"❌ Error insertando categorías: {e}")
            return False
    
    def insert_system_configuration(self) -> bool:
        """
        Inserta configuración inicial del sistema
        
        Returns:
            bool: True si fue exitoso, False si hubo errores
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                configs = [
                    ('sistema_version', '1.0.0', 'Versión del sistema Mini Market'),
                    ('stock_minimo_default', '5', 'Stock mínimo por defecto para nuevos productos'),
                    ('proveedor_default', 'MAX', 'Proveedor por defecto cuando no se puede determinar'),
                    ('auto_pedido_habilitado', 'true', 'Habilitar pedidos automáticos cuando stock < mínimo'),
                    ('ocr_habilitado', 'true', 'Habilitar procesamiento automático OCR'),
                    ('notificaciones_stock_bajo', 'true', 'Notificar cuando productos tengan stock bajo'),
                    ('formato_fecha', 'DD/MM/YYYY', 'Formato de fecha preferido para el sistema'),
                    ('moneda_default', 'ARS', 'Moneda por defecto para precios'),
                    ('iva_incluido', 'true', 'Los precios incluyen IVA por defecto'),
                    ('backup_automatico', 'true', 'Realizar backup automático de la base de datos')
                ]
                
                for clave, valor, descripcion in configs:
                    cursor.execute("""
                        INSERT OR REPLACE INTO configuracion_sistema (clave, valor, descripcion)
                        VALUES (?, ?, ?)
                    """, (clave, valor, descripcion))
                
                conn.commit()
                print(f"✅ {len(configs)} configuraciones del sistema insertadas")
                return True
                
        except Exception as e:
            print(f"❌ Error insertando configuración del sistema: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """
        Inicializa completamente la base de datos del Mini Market
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        print("🏪 === INICIALIZANDO BASE DE DATOS MINI MARKET ===")
        print()
        
        success = True
        
        # 1. Crear esquema
        print("1️⃣  Creando esquema de base de datos...")
        if not self.create_database_schema():
            success = False
        
        # 2. Insertar proveedores
        print("\n2️⃣  Insertando proveedores iniciales...")
        if not self.insert_initial_providers():
            success = False
        
        # 3. Insertar categorías
        print("\n3️⃣  Insertando categorías de productos...")
        if not self.insert_initial_categories():
            success = False
        
        # 4. Insertar configuración
        print("\n4️⃣  Insertando configuración del sistema...")
        if not self.insert_system_configuration():
            success = False
        
        print("\n" + "="*60)
        if success:
            print("✅ INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
            print(f"📊 Base de datos creada en: {self.db_path}")
            self.show_database_summary()
        else:
            print("❌ INICIALIZACIÓN COMPLETADA CON ERRORES")
        
        return success
    
    def show_database_summary(self):
        """Muestra un resumen de la base de datos inicializada"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Contar registros en cada tabla
                tables = [
                    ('proveedores', 'Proveedores registrados'),
                    ('categorias', 'Categorías de productos'),
                    ('configuracion_sistema', 'Configuraciones del sistema')
                ]
                
                print("\n📈 RESUMEN DE LA BASE DE DATOS:")
                print("-" * 40)
                
                for table, description in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"• {description}: {count}")
                
                # Mostrar proveedores
                print("\n🏢 PROVEEDORES CONFIGURADOS:")
                cursor.execute("SELECT codigo, nombre FROM proveedores ORDER BY codigo")
                providers = cursor.fetchall()
                
                for codigo, nombre in providers:
                    print(f"  • {codigo} - {nombre}")
                
        except Exception as e:
            print(f"⚠️  Error mostrando resumen: {e}")


def main():
    """Función principal para ejecutar la inicialización"""
    import sys
    
    # Verificar si se especificó una ruta de base de datos
    db_path = "minimarket_inventory.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # Crear inicializador
    initializer = MiniMarketDatabaseInitializer(db_path)
    
    # Verificar si la base de datos ya existe
    if Path(db_path).exists():
        print(f"⚠️  La base de datos {db_path} ya existe.")
        response = input("¿Deseas reinicializarla? (s/N): ").lower().strip()
        if response not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Inicialización cancelada por el usuario")
            return False
        else:
            # Hacer backup de la BD existente
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            Path(db_path).rename(backup_path)
            print(f"💾 Backup creado en: {backup_path}")
    
    # Ejecutar inicialización
    success = initializer.initialize_database()
    
    if success:
        print("\n🎯 La base de datos está lista para usar con el sistema Mini Market")
        print("🔗 Puedes conectar ahora el sistema de proveedores con persistencia")
    
    return success


if __name__ == "__main__":
    main()