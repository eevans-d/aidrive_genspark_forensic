#!/usr/bin/env python3
"""
Ejemplo de integración del sistema de optimización retail
Demuestra cómo usar las validaciones, servicios y métricas implementadas
"""
import asyncio
import logging
from decimal import Decimal
from typing import Dict, Any

# Imports de nuestro sistema de optimización
from app.retail import (
    MovimientoStock, ProductoRetail, StockService,
    retail_metrics, setup_metrics_server,
    ocr_service, OCRStatus
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetailIntegrationDemo:
    """Demostración de integración del sistema retail optimizado"""
    
    def __init__(self):
        self.stock_service = None  # Se inicializaría con DB real
        
    async def demo_product_validation(self):
        """Demostrar validaciones de productos argentinos"""
        logger.info("🏷️ Testing Product Validations...")
        
        try:
            # Producto válido argentino
            producto_valido = ProductoRetail(
                codigo_barras="7790001234567",  # EAN-13 argentino típico
                nombre="Coca Cola 500ml",
                categoria="Bebidas",
                precio_venta=Decimal("450.00"),
                precio_costo=Decimal("320.00"),
                stock_minimo=10,
                stock_maximo=100,
                iva_categoria="21"  # IVA general Argentina
            )
            
            logger.info(f"✅ Producto válido: {producto_valido.nombre} - ${producto_valido.precio_venta}")
            
            # Intentar producto con código inválido
            try:
                producto_invalido = ProductoRetail(
                    codigo_barras="123456",  # Muy corto
                    nombre="Producto Test",
                    categoria="Test", 
                    precio_venta=Decimal("100.00")
                )
            except Exception as e:
                logger.info(f"❌ Validación correcta - código inválido rechazado: {e}")
                
        except Exception as e:
            logger.error(f"Error en validación de productos: {e}")

    async def demo_stock_operations(self):
        """Demostrar operaciones de stock atómicas"""
        logger.info("📦 Testing Stock Operations...")
        
        try:
            # Simular movimiento de entrada
            movimiento_entrada = MovimientoStock(
                producto_id=123,
                cantidad=50,
                tipo_movimiento="ENTRADA",
                deposito_id=1,
                precio_unitario=Decimal("320.00"),
                observaciones="Recepción mercadería proveedor ABC"
            )
            
            logger.info(f"✅ Movimiento válido creado: {movimiento_entrada.tipo_movimiento} x{movimiento_entrada.cantidad}")
            
            # Registrar métrica de operación
            retail_metrics.record_stock_operation(
                operation_type=movimiento_entrada.tipo_movimiento,
                deposito_id=movimiento_entrada.deposito_id,
                result="success",
                categoria="Bebidas"
            )
            
            # Simular operación inválida (cantidad cero)
            try:
                movimiento_invalido = MovimientoStock(
                    producto_id=123,
                    cantidad=0,  # Inválido
                    tipo_movimiento="ENTRADA", 
                    deposito_id=1
                )
            except Exception as e:
                logger.info(f"❌ Validación correcta - cantidad cero rechazada: {e}")
                
        except Exception as e:
            logger.error(f"Error en operaciones de stock: {e}")

    async def demo_ocr_processing(self):
        """Demostrar procesamiento OCR optimizado"""
        logger.info("🔍 Testing OCR Processing...")
        
        try:
            # Simular procesamiento de imagen de producto
            result = await ocr_service.process_image_with_fallbacks(
                image="fake_product_image.jpg",  # Simulado
                timeout=5.0,
                min_confidence=0.8
            )
            
            if result.status == OCRStatus.SUCCESS:
                logger.info(f"✅ OCR exitoso: '{result.text}' (confianza: {result.confidence:.2f})")
            elif result.status == OCRStatus.CACHED:
                logger.info(f"⚡ OCR desde cache: '{result.text}' (tiempo: {result.processing_time:.2f}s)")
            else:
                logger.info(f"⚠️ OCR falló: status={result.status.value}")
            
            # Registrar métrica de OCR
            retail_metrics.record_ocr_processing(
                processing_time=result.processing_time,
                ocr_type="product_recognition",
                success=result.status == OCRStatus.SUCCESS,
                product_category="Bebidas"
            )
            
            # Simular reconocimiento de código de barras
            barcode_result = await ocr_service.recognize_barcode("fake_barcode.jpg")
            logger.info(f"📊 Barcode recognition: {barcode_result.text or 'Failed'}")
            
        except Exception as e:
            logger.error(f"Error en procesamiento OCR: {e}")

    async def demo_metrics_collection(self):
        """Demostrar recolección de métricas de negocio"""
        logger.info("📈 Testing Metrics Collection...")
        
        try:
            # Obtener métricas actuales (simuladas)
            current_metrics = {
                'total_products': 1250,
                'total_inventory_value': 850000.50,
                'critical_stock_items': 15,
                'low_stock_items_total': 45
            }
            
            logger.info("📊 Métricas de negocio actuales:")
            logger.info(f"   • Total productos: {current_metrics['total_products']:,}")
            logger.info(f"   • Valor inventario: ${current_metrics['total_inventory_value']:,.2f}")
            logger.info(f"   • Items críticos: {current_metrics['critical_stock_items']}")
            logger.info(f"   • Stock bajo total: {current_metrics['low_stock_items_total']}")
            
            # Simular alerta de stock crítico
            if current_metrics['critical_stock_items'] > 10:
                logger.warning(f"🚨 ALERTA: {current_metrics['critical_stock_items']} productos con stock crítico!")
                
        except Exception as e:
            logger.error(f"Error en recolección de métricas: {e}")

    def demo_database_optimizations(self):
        """Mostrar información sobre optimizaciones de DB"""
        logger.info("🗄️ Database Optimizations Applied...")
        
        optimizations = {
            "SQLite (inventario-retail)": [
                "✅ WAL mode habilitado para concurrencia",
                "✅ Cache de 64MB configurado", 
                "✅ Índices específicos para stock operations",
                "✅ Foreign keys habilitado",
                "✅ Busy timeout optimizado (10s)"
            ],
            "PostgreSQL (BI orchestrator)": [
                "✅ Índices concurrentes para taxonomías",
                "✅ Optimizaciones para legal compliance",
                "✅ Índices para competitive monitoring", 
                "✅ Estadísticas automáticas actualizadas"
            ]
        }
        
        for db_type, opts in optimizations.items():
            logger.info(f"\n📂 {db_type}:")
            for opt in opts:
                logger.info(f"   {opt}")

    async def run_full_demo(self):
        """Ejecutar demostración completa"""
        logger.info("🚀 Starting Retail Optimization System Demo...")
        logger.info("=" * 60)
        
        # Configurar servidor de métricas (en puerto diferente para demo)
        try:
            setup_metrics_server(port=9091)
            logger.info("📊 Metrics server started on http://localhost:9091/metrics")
        except Exception as e:
            logger.warning(f"Metrics server setup failed: {e}")
        
        # Ejecutar demos
        await self.demo_product_validation()
        await self.demo_stock_operations()
        await self.demo_ocr_processing()
        await self.demo_metrics_collection()
        self.demo_database_optimizations()
        
        logger.info("=" * 60)
        logger.info("✅ Demo completado exitosamente!")
        logger.info("\n📚 Para más información, consulta:")
        logger.info("   • docs/RETAIL_OPTIMIZATION_GUIDE.md")
        logger.info("   • monitoring/dashboards/retail_dashboard.json")
        logger.info("   • tests/retail/test_retail_validations.py")


async def main():
    """Función principal del demo"""
    demo = RetailIntegrationDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    # Ejecutar demo
    print("🛒 AIDRIVE_GENSPARK_FORENSIC - Retail Optimization Demo")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()