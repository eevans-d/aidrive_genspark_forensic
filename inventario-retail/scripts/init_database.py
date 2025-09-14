#!/usr/bin/env python3
"""
Script de Inicialización de Base de Datos
Sistema de Gestión de Depósito

Este script:
1. Crea todas las tablas con índices y constraints
2. Pobla datos iniciales realistas argentinos
3. Verifica la integridad de los datos
4. Optimiza performance con índices
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Añadir path del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agente_deposito.database import db_manager, init_database
from agente_deposito.models import Producto, MovimientoStock, Proveedor, Cliente
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
    logging.FileHandler(os.getenv('LOG_PATH', 'logs/init_database.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """
    Inicializador completo de base de datos con datos realistas argentinos
    """

    def __init__(self):
        self.logger = logger

    def run_initialization(self):
        """
        Ejecuta la inicialización completa de la base de datos
        """
        try:
            self.logger.info("=== INICIANDO INICIALIZACIÓN DE BASE DE DATOS ===")

            # 1. Verificar conexión
            if not self._test_connection():
                return False

            # 2. Crear tablas
            if not self._create_tables():
                return False

            # 3. Poblar datos iniciales
            if not self._populate_initial_data():
                return False

            # 4. Crear índices adicionales
            if not self._create_additional_indexes():
                return False

            # 5. Verificar integridad
            if not self._verify_data_integrity():
                return False

            # 6. Mostrar estadísticas
            self._show_statistics()

            self.logger.info("=== INICIALIZACIÓN COMPLETADA EXITOSAMENTE ===")
            return True

        except Exception as e:
            self.logger.error(f"Error en inicialización: {e}")
            return False

    def _test_connection(self) -> bool:
        """Prueba la conexión a la base de datos"""
        self.logger.info("Probando conexión a base de datos...")

        if db_manager.test_connection():
            info = db_manager.get_connection_info()
            self.logger.info(f"✓ Conexión exitosa a {info.get('database', 'N/A')}")
            return True
        else:
            self.logger.error("✗ Error de conexión a base de datos")
            return False

    def _create_tables(self) -> bool:
        """Crea todas las tablas con sus constraints"""
        self.logger.info("Creando estructura de tablas...")

        try:
            # Eliminar tablas existentes (solo para desarrollo)
            db_manager.drop_tables()

            # Crear todas las tablas
            if init_database():
                self.logger.info("✓ Tablas creadas exitosamente")
                return True
            else:
                self.logger.error("✗ Error creando tablas")
                return False

        except Exception as e:
            self.logger.error(f"Error en creación de tablas: {e}")
            return False

    def _populate_initial_data(self) -> bool:
        """Pobla datos iniciales realistas argentinos"""
        self.logger.info("Poblando datos iniciales...")

        try:
            with db_manager.get_session() as session:
                # 1. Crear proveedores argentinos realistas
                self._create_proveedores(session)

                # 2. Crear clientes argentinos realistas
                self._create_clientes(session)

                # 3. Crear productos argentinos realistas
                self._create_productos(session)

                # 4. Crear movimientos de stock iniciales
                self._create_movimientos_iniciales(session)

                session.commit()
                self.logger.info("✓ Datos iniciales poblados exitosamente")
                return True

        except Exception as e:
            self.logger.error(f"Error poblando datos: {e}")
            return False

    def _create_proveedores(self, session):
        """Crea proveedores argentinos realistas"""
        proveedores_data = [
            {
                'codigo': 'PROV001',
                'razon_social': 'Distribuidora San Martín S.A.',
                'nombre_fantasia': 'Distribuidora San Martín',
                'cuit': '30-12345678-9',
                'telefono': '011-4123-4567',
                'email': 'ventas@sanmartin.com.ar',
                'direccion': 'Av. Corrientes 1234',
                'ciudad': 'Ciudad Autónoma de Buenos Aires',
                'provincia': 'Ciudad Autónoma de Buenos Aires',
                'codigo_postal': '1043',
                'condicion_iva': 'Responsable Inscripto',
                'condicion_pago': '30 días fecha factura'
            },
            {
                'codigo': 'PROV002',
                'razon_social': 'Mayorista del Norte S.R.L.',
                'nombre_fantasia': 'Mayorista Norte',
                'cuit': '30-23456789-1',
                'telefono': '0341-456-7890',
                'email': 'compras@mayoristandelnorte.com',
                'direccion': 'Belgrano 567',
                'ciudad': 'Rosario',
                'provincia': 'Santa Fe',
                'codigo_postal': '2000',
                'condicion_iva': 'Responsable Inscripto',
                'condicion_pago': '60 días fecha factura'
            },
            {
                'codigo': 'PROV003',
                'razon_social': 'Electrodomésticos Córdoba S.A.',
                'nombre_fantasia': 'ElectroCordoba',
                'cuit': '30-34567891-2',
                'telefono': '0351-123-4567',
                'email': 'ventas@electrocordoba.com.ar',
                'direccion': 'San Martín 890',
                'ciudad': 'Córdoba',
                'provincia': 'Córdoba',
                'codigo_postal': '5000',
                'condicion_iva': 'Responsable Inscripto',
                'condicion_pago': '45 días fecha factura'
            }
        ]

        for data in proveedores_data:
            proveedor = Proveedor(**data)
            session.add(proveedor)

        self.logger.info(f"✓ {len(proveedores_data)} proveedores creados")

    def _create_clientes(self, session):
        """Crea clientes argentinos realistas"""
        clientes_data = [
            {
                'codigo': 'CLI001',
                'tipo_cliente': 'EMPRESA',
                'razon_social': 'Supermercado La Plaza S.A.',
                'nombre_fantasia': 'Super La Plaza',
                'documento_tipo': 'CUIT',
                'documento_numero': '30-45678912-3',
                'telefono': '011-5123-4567',
                'email': 'compras@laplaza.com.ar',
                'direccion': 'Av. Rivadavia 2345',
                'ciudad': 'Ciudad Autónoma de Buenos Aires',
                'provincia': 'Ciudad Autónoma de Buenos Aires',
                'codigo_postal': '1034',
                'condicion_iva': 'Responsable Inscripto',
                'lista_precio': 'MAYORISTA'
            },
            {
                'codigo': 'CLI002',
                'tipo_cliente': 'PERSONA',
                'nombre': 'Juan Carlos',
                'apellido': 'Pérez',
                'documento_tipo': 'DNI',
                'documento_numero': '12345678',
                'telefone': '011-6789-1234',
                'celular': '011-15-6789-1234',
                'email': 'jcperez@gmail.com',
                'direccion': 'Mitre 456',
                'ciudad': 'San Isidro',
                'provincia': 'Buenos Aires',
                'codigo_postal': '1642',
                'condicion_iva': 'Consumidor Final',
                'lista_precio': 'GENERAL'
            },
            {
                'codigo': 'CLI003',
                'tipo_cliente': 'EMPRESA',
                'razon_social': 'Kiosco Central S.R.L.',
                'nombre_fantasia': 'Kiosco Central',
                'documento_tipo': 'CUIT',
                'documento_numero': '30-56789123-4',
                'telefono': '0223-345-6789',
                'email': 'central@kioscocentral.com',
                'direccion': 'San Martín 123',
                'ciudad': 'Mar del Plata',
                'provincia': 'Buenos Aires',
                'codigo_postal': '7600',
                'condicion_iva': 'Responsable Inscripto',
                'lista_precio': 'GENERAL'
            }
        ]

        for data in clientes_data:
            cliente = Cliente(**data)
            session.add(cliente)

        self.logger.info(f"✓ {len(clientes_data)} clientes creados")

    def _create_productos(self, session):
        """Crea productos argentinos realistas"""
        productos_data = [
            # Electrodomésticos
            {
                'codigo': 'ELEC001',
                'nombre': 'Heladera NoFrost Gafa 364L',
                'descripcion': 'Heladera con freezer, tecnología NoFrost, 364 litros',
                'categoria': 'ELECTRODOMESTICOS',
                'marca': 'Gafa',
                'modelo': 'HGF-364NF',
                'precio_costo': Decimal('89000.00'),
                'precio_venta': Decimal('129000.00'),
                'precio_mayorista': Decimal('119000.00'),
                'stock_actual': 15,
                'stock_minimo': 5,
                'stock_maximo': 50,
                'ubicacion_deposito': 'A-01-001',
                'peso_kg': Decimal('65.5'),
                'dimensiones': '60x60x185'
            },
            {
                'codigo': 'ELEC002',
                'nombre': 'Lavarropas Automático Drean 7kg',
                'descripcion': 'Lavarropas automático carga frontal 7kg, 1200 RPM',
                'categoria': 'ELECTRODOMESTICOS',
                'marca': 'Drean',
                'modelo': 'NEXT-7.12-ECO',
                'precio_costo': Decimal('75000.00'),
                'precio_venta': Decimal('109000.00'),
                'precio_mayorista': Decimal('99000.00'),
                'stock_actual': 8,
                'stock_minimo': 3,
                'stock_maximo': 25,
                'ubicacion_deposito': 'A-01-002',
                'peso_kg': Decimal('58.0'),
                'dimensiones': '60x54x85'
            },
            {
                'codigo': 'ELEC003',
                'nombre': 'Microondas BGH 23L Digital',
                'descripcion': 'Microondas digital 23 litros con grill',
                'categoria': 'ELECTRODOMESTICOS',
                'marca': 'BGH',
                'modelo': 'B123D20',
                'precio_costo': Decimal('25000.00'),
                'precio_venta': Decimal('35000.00'),
                'precio_mayorista': Decimal('32000.00'),
                'stock_actual': 25,
                'stock_minimo': 10,
                'stock_maximo': 60,
                'ubicacion_deposito': 'B-02-001',
                'peso_kg': Decimal('12.5'),
                'dimensiones': '48x38x28'
            },

            # Tecnología
            {
                'codigo': 'TECH001',
                'nombre': 'Smart TV 55" 4K Samsung',
                'descripcion': 'Smart TV LED 55 pulgadas 4K UHD con WiFi',
                'categoria': 'TECNOLOGIA',
                'marca': 'Samsung',
                'modelo': 'UN55AU7000',
                'precio_costo': Decimal('95000.00'),
                'precio_venta': Decimal('139000.00'),
                'precio_mayorista': Decimal('125000.00'),
                'stock_actual': 12,
                'stock_minimo': 5,
                'stock_maximo': 30,
                'ubicacion_deposito': 'C-01-001',
                'peso_kg': Decimal('15.8'),
                'dimensiones': '123x71x6'
            },
            {
                'codigo': 'TECH002',
                'nombre': 'Notebook Lenovo IdeaPad 3',
                'descripcion': 'Notebook 15.6" Intel Core i5 8GB RAM 256GB SSD',
                'categoria': 'TECNOLOGIA',
                'marca': 'Lenovo',
                'modelo': 'IdeaPad-3-15ITL6',
                'precio_costo': Decimal('125000.00'),
                'precio_venta': Decimal('179000.00'),
                'precio_mayorista': Decimal('165000.00'),
                'stock_actual': 6,
                'stock_minimo': 3,
                'stock_maximo': 20,
                'ubicacion_deposito': 'C-02-001',
                'peso_kg': Decimal('1.85'),
                'dimensiones': '36x25x2'
            },

            # Hogar
            {
                'codigo': 'HOG001',
                'nombre': 'Juego de Sábanas King Size',
                'descripcion': 'Juego de sábanas 100% algodón king size',
                'categoria': 'HOGAR',
                'marca': 'Cannon',
                'modelo': 'Premium-King',
                'precio_costo': Decimal('8500.00'),
                'precio_venta': Decimal('12900.00'),
                'precio_mayorista': Decimal('11500.00'),
                'stock_actual': 45,
                'stock_minimo': 20,
                'stock_maximo': 100,
                'ubicacion_deposito': 'D-01-001',
                'peso_kg': Decimal('2.1'),
                'dimensiones': '30x25x15'
            },
            {
                'codigo': 'HOG002',
                'nombre': 'Almohada Memory Foam',
                'descripcion': 'Almohada viscoelástica memory foam',
                'categoria': 'HOGAR',
                'marca': 'Piero',
                'modelo': 'Memory-Comfort',
                'precio_costo': Decimal('4500.00'),
                'precio_venta': Decimal('6900.00'),
                'precio_mayorista': Decimal('6200.00'),
                'stock_actual': 2, # Stock crítico para testing
                'stock_minimo': 15,
                'stock_maximo': 80,
                'ubicacion_deposito': 'D-01-002',
                'peso_kg': Decimal('1.2'),
                'dimensiones': '50x30x12'
            },

            # Herramientas
            {
                'codigo': 'HERR001',
                'nombre': 'Taladro Percutor Bosch 650W',
                'descripcion': 'Taladro percutor profesional 13mm 650W',
                'categoria': 'HERRAMIENTAS',
                'marca': 'Bosch',
                'modelo': 'GSB-13-RE',
                'precio_costo': Decimal('35000.00'),
                'precio_venta': Decimal('49000.00'),
                'precio_mayorista': Decimal('45000.00'),
                'stock_actual': 18,
                'stock_minimo': 10,
                'stock_maximo': 40,
                'ubicacion_deposito': 'E-01-001',
                'peso_kg': Decimal('1.8'),
                'dimensiones': '25x20x8'
            }
        ]

        for data in productos_data:
            producto = Producto(**data)
            session.add(producto)

        self.logger.info(f"✓ {len(productos_data)} productos creados")

    def _create_movimientos_iniciales(self, session):
        """Crea movimientos iniciales de stock"""
        # Obtener productos para crear movimientos
        productos = session.query(Producto).all()

        movimientos_count = 0
        for producto in productos:
            # Crear movimiento de entrada inicial (stock inicial)
            movimiento = MovimientoStock(
                producto_id=producto.id,
                tipo_movimiento='ENTRADA',
                subtipo='STOCK_INICIAL',
                cantidad=producto.stock_actual,
                stock_anterior=0,
                stock_posterior=producto.stock_actual,
                precio_unitario=producto.precio_costo,
                valor_total=producto.precio_costo * producto.stock_actual,
                documento_referencia=f'INIT-{producto.codigo}',
                fecha_movimiento=datetime.now() - timedelta(days=30),
                usuario='SISTEMA',
                observaciones=f'Stock inicial para producto {producto.nombre}',
                ubicacion_destino=producto.ubicacion_deposito
            )
            session.add(movimiento)
            movimientos_count += 1

            # Agregar algunos movimientos adicionales para productos específicos
            if producto.codigo in ['ELEC001', 'TECH001', 'HOG001']:
                # Movimiento de salida
                cantidad_salida = random.randint(1, 5)
                nuevo_stock = producto.stock_actual - cantidad_salida

                movimiento_salida = MovimientoStock(
                    producto_id=producto.id,
                    tipo_movimiento='SALIDA',
                    subtipo='VENTA',
                    cantidad=-cantidad_salida,
                    stock_anterior=producto.stock_actual,
                    stock_posterior=nuevo_stock,
                    precio_unitario=producto.precio_venta,
                    valor_total=producto.precio_venta * cantidad_salida,
                    documento_referencia=f'FC-{random.randint(1000, 9999)}',
                    fecha_movimiento=datetime.now() - timedelta(days=random.randint(1, 15)),
                    usuario='VENDEDOR',
                    observaciones=f'Venta de {cantidad_salida} unidades'
                )
                session.add(movimiento_salida)
                movimientos_count += 1

                # Actualizar stock del producto
                producto.stock_actual = nuevo_stock

        self.logger.info(f"✓ {movimientos_count} movimientos de stock creados")

    def _create_additional_indexes(self) -> bool:
        """Crea índices adicionales para optimizar performance"""
        self.logger.info("Creando índices adicionales...")

        try:
            indexes_sql = [
                # Índices para búsquedas frecuentes
                "CREATE INDEX IF NOT EXISTS idx_productos_nombre_trgm ON productos USING gin(nombre gin_trgm_ops);",
                "CREATE INDEX IF NOT EXISTS idx_productos_codigo_upper ON productos (upper(codigo));",
                "CREATE INDEX IF NOT EXISTS idx_movimientos_fecha_desc ON movimientos_stock (fecha_movimiento DESC);",
                "CREATE INDEX IF NOT EXISTS idx_productos_precio_categoria ON productos (categoria, precio_venta);",

                # Índices compuestos para reportes
                "CREATE INDEX IF NOT EXISTS idx_productos_activo_stock ON productos (activo, stock_actual) WHERE activo = true;",
                "CREATE INDEX IF NOT EXISTS idx_movimientos_tipo_usuario ON movimientos_stock (tipo_movimiento, usuario);",
            ]

            for sql in indexes_sql:
                try:
                    db_manager.execute_raw_sql(sql)
                except Exception as e:
                    # Algunos índices pueden fallar si la extensión no está disponible
                    self.logger.warning(f"Índice no creado (puede requerir extensiones): {e}")

            self.logger.info("✓ Índices adicionales procesados")
            return True

        except Exception as e:
            self.logger.error(f"Error creando índices: {e}")
            return False

    def _verify_data_integrity(self) -> bool:
        """Verifica la integridad de los datos"""
        self.logger.info("Verificando integridad de datos...")

        try:
            with db_manager.get_session() as session:
                # Verificar que todos los productos tienen precios positivos
                productos_precio_invalido = session.query(Producto).filter(
                    (Producto.precio_costo <= 0) | (Producto.precio_venta <= 0)
                ).count()

                if productos_precio_invalido > 0:
                    self.logger.error(f"✗ {productos_precio_invalido} productos con precios inválidos")
                    return False

                # Verificar que todos los movimientos tienen referencias válidas
                movimientos_huerfanos = session.query(MovimientoStock).filter(
                    ~MovimientoStock.producto_id.in_(
                        session.query(Producto.id)
                    )
                ).count()

                if movimientos_huerfanos > 0:
                    self.logger.error(f"✗ {movimientos_huerfanos} movimientos sin producto válido")
                    return False

                # Verificar consistencia de stock
                inconsistencias_stock = 0
                productos = session.query(Producto).all()

                for producto in productos:
                    ultimo_movimiento = session.query(MovimientoStock).filter(
                        MovimientoStock.producto_id == producto.id
                    ).order_by(MovimientoStock.fecha_movimiento.desc()).first()

                    if ultimo_movimiento and ultimo_movimiento.stock_posterior != producto.stock_actual:
                        inconsistencias_stock += 1
                        self.logger.warning(
                            f"Inconsistencia stock producto {producto.codigo}: "
                            f"BD={producto.stock_actual}, Último mov={ultimo_movimiento.stock_posterior}"
                        )

                if inconsistencias_stock > 0:
                    self.logger.warning(f"⚠ {inconsistencias_stock} inconsistencias de stock encontradas")

                self.logger.info("✓ Verificación de integridad completada")
                return True

        except Exception as e:
            self.logger.error(f"Error verificando integridad: {e}")
            return False

    def _show_statistics(self):
        """Muestra estadísticas finales"""
        self.logger.info("=== ESTADÍSTICAS FINALES ===")

        stats = db_manager.get_table_stats()

        for table, count in stats.items():
            self.logger.info(f"{table.replace('_', ' ').title()}: {count}")

        # Mostrar algunos datos específicos
        with db_manager.get_session() as session:
            # Productos más caros
            producto_caro = session.query(Producto).order_by(
                Producto.precio_venta.desc()
            ).first()

            if producto_caro:
                self.logger.info(f"Producto más caro: {producto_caro.nombre} (${producto_caro.precio_venta})")

            # Productos con stock crítico
            productos_criticos = session.query(Producto).filter(
                Producto.stock_actual <= Producto.stock_minimo
            ).all()

            if productos_criticos:
                self.logger.info("Productos en stock crítico:")
                for p in productos_criticos:
                    self.logger.info(f"  - {p.nombre}: {p.stock_actual}/{p.stock_minimo}")

def main():
    """Función principal del script"""
    print("\n" + "="*60)
    print("  INICIALIZADOR DE BASE DE DATOS - SISTEMA DEPÓSITO")
    print("="*60)

    initializer = DatabaseInitializer()

    try:
        success = initializer.run_initialization()

        if success:
            print("\n✅ INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
            print("\nLa base de datos está lista para usar.")
            return 0
        else:
            print("\n❌ ERROR EN LA INICIALIZACIÓN")
            print("\nRevise los logs para más detalles.")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Inicialización interrumpida por el usuario")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        logger.exception("Error crítico en inicialización")
        return 1

if __name__ == "__main__":
    exit(main())
