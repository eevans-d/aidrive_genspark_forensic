#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integración Base de Datos - Sistema Mini Market
==============================================

Este módulo conecta el sistema de lógica de proveedores con la base de datos SQLite
para persistir pedidos, movimientos de stock y datos de OCR.

Autor: Sistema Multiagente
Fecha: 2025-01-18
Versión: 1.0
"""

import sqlite3
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import asdict

from provider_logic import MiniMarketProviderLogic, ProviderMatch, StockCommands


class MiniMarketDatabaseManager:
    """Gestor de base de datos para el sistema Mini Market"""
    
    def __init__(self, db_path: str = "minimarket_inventory.db"):
        """
        Inicializa el gestor de base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.provider_logic = MiniMarketProviderLogic()
    
    def get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
        return conn
    
    def registrar_pedido_natural(self, comando: str, usuario: str = "sistema") -> Dict[str, Any]:
        """
        Registra un pedido procesado desde comando natural
        
        Args:
            comando: Comando natural ("Pedir Coca Cola x 6")
            usuario: Usuario que realizó el pedido
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Procesar comando natural
            resultado_comando = self.provider_logic.procesar_comando_natural(comando)
            
            if not resultado_comando['success']:
                return {
                    'success': False,
                    'error': f"Error procesando comando: {resultado_comando['error']}"
                }
            
            # Extraer información
            proveedor_info = resultado_comando['proveedor']
            producto = resultado_comando['producto']
            cantidad = resultado_comando['cantidad_extraida']
            
            # Registrar en base de datos
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener ID del proveedor
                cursor.execute("SELECT id FROM proveedores WHERE codigo = ?", (proveedor_info['codigo'],))
                proveedor_row = cursor.fetchone()
                
                if not proveedor_row:
                    return {
                        'success': False,
                        'error': f"Proveedor {proveedor_info['codigo']} no encontrado en BD"
                    }
                
                proveedor_id = proveedor_row['id']
                
                # Crear pedido
                cursor.execute("""
                    INSERT INTO pedidos 
                    (proveedor_id, numero_pedido, estado, observaciones)
                    VALUES (?, ?, ?, ?)
                """, (
                    proveedor_id,
                    f"PED-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    'pendiente',
                    f"Pedido desde comando natural: {comando}"
                ))
                
                pedido_id = cursor.lastrowid
                
                # Agregar detalle del pedido
                cursor.execute("""
                    INSERT INTO detalle_pedidos
                    (pedido_id, producto_nombre, cantidad, observaciones)
                    VALUES (?, ?, ?, ?)
                """, (
                    pedido_id,
                    producto,
                    cantidad,
                    f"Comando original: {comando}"
                ))
                
                conn.commit()
                
                return {
                    'success': True,
                    'pedido_id': pedido_id,
                    'proveedor': proveedor_info,
                    'producto': producto,
                    'cantidad': cantidad,
                    'comando_original': comando
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error registrando pedido: {str(e)}"
            }
    
    def registrar_movimiento_stock(self, comando: str, usuario: str = "sistema") -> Dict[str, Any]:
        """
        Registra un movimiento de stock desde comando natural
        
        Args:
            comando: Comando de stock ("Dejé 4 bananas del ecuador")
            usuario: Usuario que realizó el movimiento
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Procesar comando de stock
            resultado_comando = StockCommands.procesar_comando_stock(comando, self.provider_logic)
            
            if not resultado_comando['success']:
                return {
                    'success': False,
                    'error': f"Error procesando comando: {resultado_comando['error']}"
                }
            
            # Extraer información
            operacion = resultado_comando['operacion']
            producto = resultado_comando['producto']
            cantidad = resultado_comando['cantidad']
            origen = resultado_comando.get('origen', '')
            destino = resultado_comando.get('destino', '')
            
            proveedor_id = None
            if 'proveedor_sugerido' in resultado_comando:
                proveedor_info = resultado_comando['proveedor_sugerido']
                
                # Obtener ID del proveedor
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM proveedores WHERE codigo = ?", (proveedor_info['codigo'],))
                    proveedor_row = cursor.fetchone()
                    if proveedor_row:
                        proveedor_id = proveedor_row['id']
            
            # Registrar en base de datos
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO movimientos_stock
                    (producto_nombre, tipo_movimiento, cantidad, proveedor_id, 
                     origen, destino, observaciones, usuario)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    producto,
                    operacion,
                    cantidad,
                    proveedor_id,
                    origen,
                    destino,
                    f"Comando original: {comando}",
                    usuario
                ))
                
                movimiento_id = cursor.lastrowid
                conn.commit()
                
                return {
                    'success': True,
                    'movimiento_id': movimiento_id,
                    'operacion': operacion,
                    'producto': producto,
                    'cantidad': cantidad,
                    'proveedor_sugerido': resultado_comando.get('proveedor_sugerido'),
                    'comando_original': comando
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error registrando movimiento: {str(e)}"
            }
    
    def procesar_factura_ocr(self, ocr_result: Dict[str, Any], usuario: str = "sistema") -> Dict[str, Any]:
        """
        Procesa una factura OCR y registra en base de datos
        
        Args:
            ocr_result: Resultado del OCR con estructura estándar
            usuario: Usuario que procesó la factura
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            # Usar función de integración OCR
            from provider_logic import enhance_ocr_with_provider_logic
            enhanced_result = enhance_ocr_with_provider_logic(ocr_result, self.provider_logic)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Determinar proveedor principal de la factura
                proveedor_principal_id = None
                if enhanced_result.get('productos'):
                    # Tomar el proveedor del primer producto que tenga asignación
                    for producto in enhanced_result['productos']:
                        if 'proveedor_sugerido' in producto:
                            proveedor_codigo = producto['proveedor_sugerido']['codigo']
                            cursor.execute("SELECT id FROM proveedores WHERE codigo = ?", (proveedor_codigo,))
                            proveedor_row = cursor.fetchone()
                            if proveedor_row:
                                proveedor_principal_id = proveedor_row['id']
                                break
                
                # Registrar factura OCR
                cursor.execute("""
                    INSERT INTO facturas_ocr
                    (numero_factura, proveedor_original, proveedor_asignado_id, 
                     fecha_factura, total, contenido_ocr, productos_json, procesado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    enhanced_result.get('factura_numero', ''),
                    enhanced_result.get('proveedor_original', ''),
                    proveedor_principal_id,
                    enhanced_result.get('fecha_factura'),
                    enhanced_result.get('total', 0),
                    json.dumps(ocr_result, ensure_ascii=False),
                    json.dumps(enhanced_result['productos'], ensure_ascii=False),
                    True
                ))
                
                factura_id = cursor.lastrowid
                
                # Registrar movimientos de entrada para cada producto
                for producto in enhanced_result['productos']:
                    if 'proveedor_sugerido' in producto:
                        proveedor_codigo = producto['proveedor_sugerido']['codigo']
                        cursor.execute("SELECT id FROM proveedores WHERE codigo = ?", (proveedor_codigo,))
                        proveedor_row = cursor.fetchone()
                        proveedor_id = proveedor_row['id'] if proveedor_row else None
                        
                        cursor.execute("""
                            INSERT INTO movimientos_stock
                            (producto_nombre, tipo_movimiento, cantidad, precio_unitario,
                             proveedor_id, origen, observaciones, usuario)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            producto['descripcion'],
                            'entrada',
                            producto.get('cantidad', 1),
                            producto.get('precio', 0),
                            proveedor_id,
                            f"Factura {enhanced_result.get('factura_numero', '')}",
                            f"Procesado desde OCR - Factura ID: {factura_id}",
                            usuario
                        ))
                
                conn.commit()
                
                return {
                    'success': True,
                    'factura_id': factura_id,
                    'productos_procesados': len(enhanced_result['productos']),
                    'enhanced_result': enhanced_result
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error procesando factura OCR: {str(e)}"
            }
    
    def obtener_resumen_pedidos(self, dias: int = 7) -> Dict[str, Any]:
        """
        Obtiene resumen de pedidos por proveedor en los últimos días
        
        Args:
            dias: Número de días a considerar
            
        Returns:
            Dict con resumen de pedidos
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Pedidos por proveedor
                cursor.execute("""
                    SELECT 
                        p.codigo,
                        p.nombre,
                        COUNT(ped.id) as total_pedidos,
                        SUM(dp.cantidad) as total_productos,
                        GROUP_CONCAT(dp.producto_nombre || ' (x' || dp.cantidad || ')') as productos
                    FROM proveedores p
                    LEFT JOIN pedidos ped ON p.id = ped.proveedor_id
                    LEFT JOIN detalle_pedidos dp ON ped.id = dp.pedido_id
                    WHERE ped.fecha_pedido >= datetime('now', '-{} days')
                    GROUP BY p.id, p.codigo, p.nombre
                    HAVING total_pedidos > 0
                    ORDER BY total_pedidos DESC
                """.format(dias))
                
                pedidos_por_proveedor = []
                for row in cursor.fetchall():
                    pedidos_por_proveedor.append({
                        'codigo': row['codigo'],
                        'nombre': row['nombre'],
                        'total_pedidos': row['total_pedidos'],
                        'total_productos': row['total_productos'] or 0,
                        'productos': row['productos'].split(',') if row['productos'] else []
                    })
                
                # Movimientos de stock recientes
                cursor.execute("""
                    SELECT 
                        tipo_movimiento,
                        COUNT(*) as cantidad_movimientos,
                        SUM(cantidad) as total_productos
                    FROM movimientos_stock
                    WHERE fecha_movimiento >= datetime('now', '-{} days')
                    GROUP BY tipo_movimiento
                """.format(dias))
                
                movimientos_stock = []
                for row in cursor.fetchall():
                    movimientos_stock.append({
                        'tipo': row['tipo_movimiento'],
                        'cantidad_movimientos': row['cantidad_movimientos'],
                        'total_productos': row['total_productos']
                    })
                
                return {
                    'success': True,
                    'periodo_dias': dias,
                    'pedidos_por_proveedor': pedidos_por_proveedor,
                    'movimientos_stock': movimientos_stock,
                    'total_proveedores_activos': len(pedidos_por_proveedor)
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error obteniendo resumen: {str(e)}"
            }
    
    def obtener_stock_bajo(self, limite_minimo: int = 5) -> Dict[str, Any]:
        """
        Obtiene productos con stock bajo basado en movimientos
        
        Args:
            limite_minimo: Cantidad mínima considerada como stock bajo
            
        Returns:
            Dict con productos de stock bajo
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Calcular stock actual por producto
                cursor.execute("""
                    SELECT 
                        producto_nombre,
                        SUM(CASE WHEN tipo_movimiento = 'entrada' THEN cantidad ELSE -cantidad END) as stock_actual,
                        MAX(fecha_movimiento) as ultima_modificacion
                    FROM movimientos_stock
                    GROUP BY producto_nombre
                    HAVING stock_actual <= ?
                    ORDER BY stock_actual ASC, ultima_modificacion DESC
                """, (limite_minimo,))
                
                productos_stock_bajo = []
                for row in cursor.fetchall():
                    # Sugerir proveedor para el producto
                    provider_match = self.provider_logic.asignar_proveedor(row['producto_nombre'])
                    
                    productos_stock_bajo.append({
                        'producto': row['producto_nombre'],
                        'stock_actual': row['stock_actual'],
                        'ultima_modificacion': row['ultima_modificacion'],
                        'proveedor_sugerido': {
                            'codigo': provider_match.provider_code,
                            'nombre': provider_match.provider_name,
                            'confianza': provider_match.confidence
                        }
                    })
                
                return {
                    'success': True,
                    'productos_stock_bajo': productos_stock_bajo,
                    'total_productos': len(productos_stock_bajo),
                    'limite_aplicado': limite_minimo
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error calculando stock bajo: {str(e)}"
            }


# Funciones de utilidad para testing
def test_database_integration():
    """Función de prueba para la integración con base de datos"""
    
    print("🏪 === TESTING INTEGRACIÓN BASE DE DATOS MINI MARKET ===")
    print()
    
    db_manager = MiniMarketDatabaseManager()
    
    # 1. Test registro de pedidos naturales
    print("1️⃣  Testing registro de pedidos naturales")
    print("-" * 50)
    
    comandos_pedido = [
        "Pedir Coca Cola x 6",
        "Falta Sprite lima limón",
        "Anotar Salchichas Paladini x 3",
        "Necesito bananas x 5"
    ]
    
    for comando in comandos_pedido:
        resultado = db_manager.registrar_pedido_natural(comando, "test_user")
        if resultado['success']:
            print(f"✅ {comando} → Pedido #{resultado['pedido_id']} - {resultado['proveedor']['codigo']}")
        else:
            print(f"❌ {comando} → Error: {resultado['error']}")
    
    print()
    
    # 2. Test movimientos de stock
    print("2️⃣  Testing movimientos de stock")
    print("-" * 50)
    
    comandos_stock = [
        "Dejé 4 bananas del ecuador",
        "Ingreso 12 Coca Cola del distribuidor",
        "Saqué 6 productos para el kiosco"
    ]
    
    for comando in comandos_stock:
        resultado = db_manager.registrar_movimiento_stock(comando, "test_user")
        if resultado['success']:
            print(f"✅ {comando} → Movimiento #{resultado['movimiento_id']} ({resultado['operacion']})")
        else:
            print(f"❌ {comando} → Error: {resultado['error']}")
    
    print()
    
    # 3. Test procesamiento OCR
    print("3️⃣  Testing procesamiento facturas OCR")
    print("-" * 50)
    
    # Simular resultado OCR
    ocr_test = {
        'factura_numero': 'F001-TEST-12345',
        'proveedor_original': 'DISTRIBUIDOR TEST',
        'productos': [
            {'descripcion': 'Coca Cola 2.5L', 'precio': 450.00, 'cantidad': 2},
            {'descripcion': 'Galletitas Oreo', 'precio': 380.00, 'cantidad': 1},
            {'descripcion': 'Banana ecuador kg', 'precio': 280.00, 'cantidad': 3}
        ],
        'total': 1390.00
    }
    
    resultado = db_manager.procesar_factura_ocr(ocr_test, "test_user")
    if resultado['success']:
        print(f"✅ Factura procesada → ID #{resultado['factura_id']}, {resultado['productos_procesados']} productos")
    else:
        print(f"❌ Error procesando factura: {resultado['error']}")
    
    print()
    
    # 4. Test resumen de pedidos
    print("4️⃣  Testing resumen de pedidos")
    print("-" * 50)
    
    resumen = db_manager.obtener_resumen_pedidos(7)
    if resumen['success']:
        print(f"📊 Proveedores activos: {resumen['total_proveedores_activos']}")
        for proveedor in resumen['pedidos_por_proveedor']:
            print(f"  • {proveedor['codigo']} - {proveedor['nombre']}: {proveedor['total_pedidos']} pedidos")
        
        print(f"\n📦 Movimientos de stock:")
        for mov in resumen['movimientos_stock']:
            print(f"  • {mov['tipo']}: {mov['cantidad_movimientos']} movimientos ({mov['total_productos']} productos)")
    else:
        print(f"❌ Error obteniendo resumen: {resumen['error']}")
    
    print()
    
    # 5. Test stock bajo
    print("5️⃣  Testing productos con stock bajo")
    print("-" * 50)
    
    stock_bajo = db_manager.obtener_stock_bajo(10)  # Stock bajo = menos de 10
    if stock_bajo['success']:
        print(f"⚠️  Productos con stock bajo: {stock_bajo['total_productos']}")
        for producto in stock_bajo['productos_stock_bajo']:
            print(f"  • {producto['producto']}: {producto['stock_actual']} unidades")
            print(f"    → Proveedor sugerido: {producto['proveedor_sugerido']['codigo']}")
    else:
        print(f"❌ Error calculando stock bajo: {stock_bajo['error']}")
    
    print()
    print("✅ === TESTING INTEGRACIÓN COMPLETADO ===")


if __name__ == "__main__":
    test_database_integration()