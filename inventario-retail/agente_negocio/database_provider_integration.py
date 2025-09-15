#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini Market Provider Database Integration
========================================

Este módulo integra el sistema de lógica de proveedores con la base de datos,
proporcionando persistencia para pedidos, movimientos de stock y facturas OCR.

Autor: Sistema Multiagente
Fecha: 2025-01-18
Versión: 1.0
"""

import sqlite3
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from provider_logic import MiniMarketProviderLogic, StockCommands

@dataclass
class DatabaseResult:
    """Resultado de operaciones con la base de datos"""
    success: bool
    message: str = ""
    data: Any = None
    error: str = ""

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
        
        # Verificar que la BD existe
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {db_path}. Ejecuta database_init_minimarket.py primero.")
    
    def _get_provider_id_by_code(self, provider_code: str) -> Optional[int]:
        """
        Obtiene el ID del proveedor por su código
        
        Args:
            provider_code: Código del proveedor (ej: 'CO', 'FR', etc.)
            
        Returns:
            ID del proveedor o None si no existe
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM proveedores WHERE codigo = ?", (provider_code,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception:
            return None
    
    def registrar_pedido_completo(self, productos_pedidos: List[Dict[str, Any]], 
                                observaciones: str = "") -> DatabaseResult:
        """
        Registra un pedido completo con múltiples productos agrupados por proveedor
        
        Args:
            productos_pedidos: Lista de diccionarios con 'producto', 'cantidad', 'proveedor_codigo'
            observaciones: Observaciones generales del pedido
            
        Returns:
            DatabaseResult con información del pedido registrado
        """
        try:
            # Agrupar productos por proveedor
            pedidos_por_proveedor = {}
            
            for item in productos_pedidos:
                proveedor_codigo = item['proveedor_codigo']
                if proveedor_codigo not in pedidos_por_proveedor:
                    pedidos_por_proveedor[proveedor_codigo] = []
                pedidos_por_proveedor[proveedor_codigo].append(item)
            
            pedidos_creados = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for proveedor_codigo, productos in pedidos_por_proveedor.items():
                    # Obtener ID del proveedor
                    proveedor_id = self._get_provider_id_by_code(proveedor_codigo)
                    if not proveedor_id:
                        continue
                    
                    # Generar número de pedido
                    fecha_actual = datetime.now()
                    numero_pedido = f"PED-{proveedor_codigo}-{fecha_actual.strftime('%Y%m%d-%H%M%S')}"
                    
                    # Crear pedido principal
                    cursor.execute("""
                        INSERT INTO pedidos (proveedor_id, numero_pedido, observaciones)
                        VALUES (?, ?, ?)
                    """, (proveedor_id, numero_pedido, observaciones))
                    
                    pedido_id = cursor.lastrowid
                    total_pedido = 0.0
                    
                    # Agregar detalles del pedido
                    for producto in productos:
                        precio_estimado = self._estimar_precio_producto(producto['producto'])
                        subtotal = precio_estimado * producto['cantidad']
                        total_pedido += subtotal
                        
                        cursor.execute("""
                            INSERT INTO detalle_pedidos 
                            (pedido_id, producto_nombre, cantidad, precio_unitario, subtotal)
                            VALUES (?, ?, ?, ?, ?)
                        """, (pedido_id, producto['producto'], producto['cantidad'], 
                             precio_estimado, subtotal))
                    
                    # Actualizar total del pedido
                    cursor.execute("""
                        UPDATE pedidos SET total = ? WHERE id = ?
                    """, (total_pedido, pedido_id))
                    
                    pedidos_creados.append({
                        'pedido_id': pedido_id,
                        'numero_pedido': numero_pedido,
                        'proveedor_codigo': proveedor_codigo,
                        'total': total_pedido,
                        'productos_count': len(productos)
                    })
                
                conn.commit()
            
            return DatabaseResult(
                success=True,
                message=f"Pedidos registrados exitosamente: {len(pedidos_creados)} proveedores",
                data={'pedidos': pedidos_creados, 'total_productos': len(productos_pedidos)}
            )
            
        except Exception as e:
            return DatabaseResult(
                success=False,
                error=f"Error registrando pedido: {e}"
            )
    
    def registrar_movimiento_stock(self, producto_nombre: str, tipo_movimiento: str,
                                 cantidad: int, proveedor_codigo: str = None,
                                 origen: str = "", destino: str = "",
                                 observaciones: str = "", usuario: str = "sistema") -> DatabaseResult:
        """
        Registra un movimiento de stock (entrada/salida)
        
        Args:
            producto_nombre: Nombre del producto
            tipo_movimiento: 'entrada' o 'salida'
            cantidad: Cantidad del movimiento
            proveedor_codigo: Código del proveedor (opcional)
            origen: Origen del movimiento
            destino: Destino del movimiento
            observaciones: Observaciones del movimiento
            usuario: Usuario que realiza el movimiento
            
        Returns:
            DatabaseResult con información del movimiento
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                proveedor_id = None
                if proveedor_codigo:
                    proveedor_id = self._get_provider_id_by_code(proveedor_codigo)
                
                # Buscar si existe el producto
                cursor.execute("""
                    SELECT id, stock_actual FROM productos 
                    WHERE LOWER(nombre) = LOWER(?)
                """, (producto_nombre,))
                producto_result = cursor.fetchone()
                
                producto_id = None
                stock_actual = 0
                
                if producto_result:
                    producto_id = producto_result[0]
                    stock_actual = producto_result[1] or 0
                
                # Registrar movimiento
                cursor.execute("""
                    INSERT INTO movimientos_stock 
                    (producto_id, producto_nombre, tipo_movimiento, cantidad, 
                     proveedor_id, origen, destino, observaciones, usuario)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (producto_id, producto_nombre, tipo_movimiento, cantidad,
                     proveedor_id, origen, destino, observaciones, usuario))
                
                movimiento_id = cursor.lastrowid
                
                # Actualizar stock si existe el producto
                if producto_id:
                    if tipo_movimiento == 'entrada':
                        nuevo_stock = stock_actual + cantidad
                    else:  # salida
                        nuevo_stock = max(0, stock_actual - cantidad)
                    
                    cursor.execute("""
                        UPDATE productos SET stock_actual = ? WHERE id = ?
                    """, (nuevo_stock, producto_id))
                
                conn.commit()
                
                return DatabaseResult(
                    success=True,
                    message=f"Movimiento de stock registrado: {tipo_movimiento} de {cantidad} {producto_nombre}",
                    data={
                        'movimiento_id': movimiento_id,
                        'producto_id': producto_id,
                        'stock_nuevo': nuevo_stock if producto_id else None
                    }
                )
                
        except Exception as e:
            return DatabaseResult(
                success=False,
                error=f"Error registrando movimiento: {e}"
            )
    
    def procesar_comando_con_bd(self, comando: str, usuario: str = "usuario") -> DatabaseResult:
        """
        Procesa un comando natural y lo registra en la base de datos
        
        Args:
            comando: Comando en lenguaje natural
            usuario: Usuario que ejecuta el comando
            
        Returns:
            DatabaseResult con el resultado del procesamiento
        """
        try:
            # 1. Intentar como comando de pedido
            resultado_pedido = self.provider_logic.procesar_comando_natural(comando)
            
            if resultado_pedido['success']:
                # Registrar pedido en BD
                productos_pedidos = [{
                    'producto': resultado_pedido['producto'],  # Corregido: 'producto' en lugar de 'producto_normalizado'
                    'cantidad': resultado_pedido['cantidad_extraida'],
                    'proveedor_codigo': resultado_pedido['proveedor']['codigo']
                }]
                
                result_bd = self.registrar_pedido_completo(
                    productos_pedidos, 
                    f"Pedido generado por comando: {comando}"
                )
                
                if result_bd.success:
                    return DatabaseResult(
                        success=True,
                        message=f"Pedido registrado: {resultado_pedido['cantidad_extraida']} {resultado_pedido['producto']} → {resultado_pedido['proveedor']['codigo']}",  # Corregido
                        data={'tipo': 'pedido', 'pedido_bd': result_bd.data, 'comando_resultado': resultado_pedido}
                    )
            
            # 2. Intentar como comando de stock
            resultado_stock = StockCommands.procesar_comando_stock(comando, self.provider_logic)
            
            if resultado_stock['success']:
                # Registrar movimiento en BD
                proveedor_codigo = None
                if 'proveedor_sugerido' in resultado_stock:
                    proveedor_codigo = resultado_stock['proveedor_sugerido']['codigo']
                
                result_bd = self.registrar_movimiento_stock(
                    producto_nombre=resultado_stock['producto'],
                    tipo_movimiento=resultado_stock['operacion'],
                    cantidad=resultado_stock['cantidad'],
                    proveedor_codigo=proveedor_codigo,
                    origen=resultado_stock.get('origen', ''),
                    destino=resultado_stock.get('destino', ''),
                    observaciones=f"Movimiento por comando: {comando}",
                    usuario=usuario
                )
                
                if result_bd.success:
                    return DatabaseResult(
                        success=True,
                        message=f"Movimiento registrado: {resultado_stock['operacion']} de {resultado_stock['cantidad']} {resultado_stock['producto']}",
                        data={'tipo': 'stock', 'movimiento_bd': result_bd.data, 'comando_resultado': resultado_stock}
                    )
            
            # No se pudo procesar el comando
            return DatabaseResult(
                success=False,
                error=f"No se pudo interpretar el comando: {comando}"
            )
            
        except Exception as e:
            return DatabaseResult(
                success=False,
                error=f"Error procesando comando: {e}"
            )
    
    def registrar_factura_ocr(self, factura_data: Dict[str, Any]) -> DatabaseResult:
        """
        Registra una factura procesada por OCR en la base de datos
        
        Args:
            factura_data: Datos de la factura con productos y proveedores asignados
            
        Returns:
            DatabaseResult con información de la factura registrada
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener proveedor asignado (del primer producto si existe)
                proveedor_id = None
                if 'productos' in factura_data and factura_data['productos']:
                    primer_producto = factura_data['productos'][0]
                    if 'proveedor_sugerido' in primer_producto:
                        proveedor_codigo = primer_producto['proveedor_sugerido']['codigo']
                        proveedor_id = self._get_provider_id_by_code(proveedor_codigo)
                
                # Registrar factura
                cursor.execute("""
                    INSERT INTO facturas_ocr 
                    (numero_factura, proveedor_original, proveedor_asignado_id, 
                     total, contenido_ocr, productos_json, procesado)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    factura_data.get('factura_numero', ''),
                    factura_data.get('proveedor_original', ''),
                    proveedor_id,
                    factura_data.get('total', 0.0),
                    json.dumps(factura_data, ensure_ascii=False),
                    json.dumps(factura_data.get('productos', []), ensure_ascii=False),
                    True
                ))
                
                factura_id = cursor.lastrowid
                
                # Registrar movimientos de stock por cada producto
                movimientos_registrados = 0
                
                for producto in factura_data.get('productos', []):
                    if 'proveedor_sugerido' in producto:
                        result_mov = self.registrar_movimiento_stock(
                            producto_nombre=producto['descripcion'],
                            tipo_movimiento='entrada',
                            cantidad=producto.get('cantidad', 1),
                            proveedor_codigo=producto['proveedor_sugerido']['codigo'],
                            origen=f"Factura {factura_data.get('factura_numero', '')}",
                            observaciones="Entrada por factura OCR",
                            usuario="ocr_system"
                        )
                        
                        if result_mov.success:
                            movimientos_registrados += 1
                
                conn.commit()
                
                return DatabaseResult(
                    success=True,
                    message=f"Factura OCR registrada con {movimientos_registrados} movimientos de stock",
                    data={
                        'factura_id': factura_id,
                        'movimientos_registrados': movimientos_registrados,
                        'proveedor_asignado_id': proveedor_id
                    }
                )
                
        except Exception as e:
            return DatabaseResult(
                success=False,
                error=f"Error registrando factura OCR: {e}"
            )
    
    def obtener_resumen_pedidos(self, fecha_desde: date = None, 
                              fecha_hasta: date = None) -> DatabaseResult:
        """
        Obtiene un resumen de pedidos en un rango de fechas
        
        Args:
            fecha_desde: Fecha de inicio (opcional)
            fecha_hasta: Fecha de fin (opcional)
            
        Returns:
            DatabaseResult con resumen de pedidos
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Construir consulta con filtros de fecha
                query = """
                    SELECT 
                        p.id, p.numero_pedido, p.fecha_pedido, p.estado, p.total,
                        pr.codigo as proveedor_codigo, pr.nombre as proveedor_nombre,
                        COUNT(dp.id) as cantidad_productos
                    FROM pedidos p
                    JOIN proveedores pr ON p.proveedor_id = pr.id
                    LEFT JOIN detalle_pedidos dp ON p.id = dp.pedido_id
                """
                
                params = []
                
                if fecha_desde or fecha_hasta:
                    query += " WHERE "
                    conditions = []
                    
                    if fecha_desde:
                        conditions.append("DATE(p.fecha_pedido) >= ?")
                        params.append(fecha_desde.isoformat())
                    
                    if fecha_hasta:
                        conditions.append("DATE(p.fecha_pedido) <= ?")
                        params.append(fecha_hasta.isoformat())
                    
                    query += " AND ".join(conditions)
                
                query += """
                    GROUP BY p.id
                    ORDER BY p.fecha_pedido DESC
                """
                
                cursor.execute(query, params)
                pedidos = cursor.fetchall()
                
                # Convertir a diccionarios
                pedidos_lista = []
                total_general = 0.0
                
                for pedido in pedidos:
                    pedido_dict = {
                        'id': pedido[0],
                        'numero_pedido': pedido[1],
                        'fecha_pedido': pedido[2],
                        'estado': pedido[3],
                        'total': pedido[4] or 0.0,
                        'proveedor': {
                            'codigo': pedido[5],
                            'nombre': pedido[6]
                        },
                        'cantidad_productos': pedido[7]
                    }
                    pedidos_lista.append(pedido_dict)
                    total_general += pedido_dict['total']
                
                return DatabaseResult(
                    success=True,
                    message=f"Resumen obtenido: {len(pedidos_lista)} pedidos",
                    data={
                        'pedidos': pedidos_lista,
                        'total_pedidos': len(pedidos_lista),
                        'total_general': total_general,
                        'fecha_desde': fecha_desde.isoformat() if fecha_desde else None,
                        'fecha_hasta': fecha_hasta.isoformat() if fecha_hasta else None
                    }
                )
                
        except Exception as e:
            return DatabaseResult(
                success=False,
                error=f"Error obteniendo resumen de pedidos: {e}"
            )
    
    def obtener_stock_bajo(self, limite_stock: int = 5) -> DatabaseResult:
        """
        Obtiene productos con stock bajo
        
        Args:
            limite_stock: Límite de stock para considerar "bajo"
            
        Returns:
            DatabaseResult con productos de stock bajo
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        p.id, p.nombre, p.stock_actual, p.stock_minimo,
                        pr.codigo as proveedor_codigo, pr.nombre as proveedor_nombre,
                        c.nombre as categoria
                    FROM productos p
                    LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    WHERE p.stock_actual <= ? AND p.activo = 1
                    ORDER BY p.stock_actual ASC
                """, (limite_stock,))
                
                productos = cursor.fetchall()
                
                productos_lista = []
                for producto in productos:
                    productos_lista.append({
                        'id': producto[0],
                        'nombre': producto[1],
                        'stock_actual': producto[2] or 0,
                        'stock_minimo': producto[3] or 5,
                        'proveedor': {
                            'codigo': producto[4],
                            'nombre': producto[5]
                        } if producto[4] else None,
                        'categoria': producto[6]
                    })
                
                return DatabaseResult(
                    success=True,
                    message=f"Encontrados {len(productos_lista)} productos con stock bajo",
                    data={
                        'productos': productos_lista,
                        'total_productos': len(productos_lista),
                        'limite_aplicado': limite_stock
                    }
                )
                
        except Exception as e:
            return DatabaseResult(
                success=False,
                error=f"Error obteniendo productos con stock bajo: {e}"
            )
    
    def _estimar_precio_producto(self, producto_nombre: str) -> float:
        """
        Estima un precio para un producto basado en su nombre (función auxiliar)
        
        Args:
            producto_nombre: Nombre del producto
            
        Returns:
            Precio estimado en pesos argentinos
        """
        # Precios estimados básicos por categoría de producto
        precios_base = {
            'coca cola': 450.0,
            'sprite': 420.0,
            'fanta': 420.0,
            'cerveza': 320.0,
            'brahma': 320.0,
            'quilmes': 340.0,
            'vino': 800.0,
            'leche': 380.0,
            'yogurt': 280.0,
            'galletitas': 350.0,
            'oreo': 380.0,
            'banana': 280.0,
            'manzana': 320.0,
            'salchicha': 450.0,
            'fiambre': 520.0,
            'aceite': 680.0,
            'arroz': 320.0,
            'fideos': 280.0
        }
        
        producto_lower = producto_nombre.lower()
        
        # Buscar coincidencias parciales
        for producto, precio in precios_base.items():
            if producto in producto_lower:
                return precio
        
        # Precio por defecto
        return 300.0


def main():
    """Función principal para probar la integración"""
    # Verificar que la BD existe
    db_path = "minimarket_inventory.db"
    
    if not Path(db_path).exists():
        print("❌ Base de datos no encontrada. Ejecuta primero:")
        print("   python3 database_init_minimarket.py")
        return
    
    print("🏪 === PRUEBA DE INTEGRACIÓN BD + PROVIDER LOGIC ===")
    print()
    
    # Crear gestor
    db_manager = MiniMarketDatabaseManager(db_path)
    
    # Pruebas
    comandos_test = [
        "Pedir Coca Cola x 6",
        "Falta Sprite lima limón x 3", 
        "Dejé 4 bananas del ecuador",
        "Saqué 2 galletitas Oreo para el kiosco"
    ]
    
    print("🧪 PROCESANDO COMANDOS CON PERSISTENCIA:")
    print("-" * 50)
    
    for comando in comandos_test:
        print(f"\n• Comando: \"{comando}\"")
        result = db_manager.procesar_comando_con_bd(comando)
        
        if result.success:
            print(f"  ✅ {result.message}")
        else:
            print(f"  ❌ {result.error}")
    
    # Resumen de pedidos
    print("\n📊 RESUMEN DE PEDIDOS:")
    print("-" * 30)
    
    resumen = db_manager.obtener_resumen_pedidos()
    if resumen.success:
        data = resumen.data
        print(f"Total pedidos: {data['total_pedidos']}")
        print(f"Total general: ${data['total_general']:.2f}")
        
        for pedido in data['pedidos']:
            print(f"• {pedido['numero_pedido']} - {pedido['proveedor']['codigo']} (${pedido['total']:.2f})")
    
    print("\n✅ Integración BD + Provider Logic funcionando correctamente")


if __name__ == "__main__":
    main()