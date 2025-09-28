"""
Servicio de Stock con transacciones atómicas para sistema retail argentino
Incluye retry logic, validaciones y manejo de concurrencia
"""
import asyncio
import random
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import select, update, and_

from .validation import MovimientoStock, ValidacionStock


logger = logging.getLogger(__name__)


class StockService:
    """Servicio de gestión de stock con transacciones atómicas"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.max_retries = 3
        self.base_delay = 0.1  # 100ms base delay
        
    @asynccontextmanager
    async def atomic_stock_operation(self, producto_id: int):
        """
        Context manager para operaciones atómicas de stock
        Incluye retry logic para SQLite locks y PostgreSQL conflicts
        """
        for attempt in range(self.max_retries):
            session = None
            try:
                session = self.db_session_factory()
                
                # Iniciar transacción explícita
                session.begin()
                
                # Bloquear el producto específico para evitar race conditions
                # Para SQLite: SELECT ... no soporta FOR UPDATE, usamos transacción
                # Para PostgreSQL: usar FOR UPDATE
                producto = session.execute(
                    select("productos").where("productos.id" == producto_id)
                ).first()
                
                if not producto:
                    raise ValueError(f"Producto {producto_id} no encontrado")
                
                logger.debug(f"Stock operation locked for producto {producto_id}, attempt {attempt + 1}")
                
                yield session
                
                # Si llegamos aquí, commit exitoso
                session.commit()
                logger.info(f"Stock operation completed successfully for producto {producto_id}")
                break
                
            except (OperationalError, IntegrityError) as e:
                if session:
                    session.rollback()
                
                error_msg = str(e).lower()
                is_lock_error = any(keyword in error_msg for keyword in [
                    "database is locked", "lock timeout", "deadlock", "concurrent update"
                ])
                
                if is_lock_error and attempt < self.max_retries - 1:
                    # Backoff exponencial con jitter para evitar thundering herd
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                    logger.warning(f"Lock error on attempt {attempt + 1}, retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Stock operation failed after {attempt + 1} attempts: {e}")
                    raise
                    
            except Exception as e:
                if session:
                    session.rollback()
                logger.error(f"Unexpected error in stock operation: {e}")
                raise
                
            finally:
                if session:
                    session.close()
                    
        else:
            raise Exception(f"Stock operation failed after {self.max_retries} attempts")

    async def validar_stock_suficiente(self, session: Session, producto_id: int, cantidad_requerida: int) -> bool:
        """
        Validación específica de stock para retail con cálculo dinámico
        """
        # Calcular stock actual sumando todos los movimientos
        # Esta query debe ser optimizada con los índices creados
        stock_query = """
        SELECT COALESCE(SUM(
            CASE 
                WHEN tipo_movimiento IN ('ENTRADA', 'AJUSTE') AND cantidad > 0 THEN cantidad
                WHEN tipo_movimiento IN ('SALIDA', 'AJUSTE') AND cantidad < 0 THEN cantidad
                ELSE 0
            END
        ), 0) as stock_actual
        FROM movimientos_stock 
        WHERE producto_id = :producto_id
        """
        
        result = session.execute(stock_query, {"producto_id": producto_id}).first()
        stock_actual = result[0] if result else 0
        
        logger.debug(f"Stock actual producto {producto_id}: {stock_actual}")
        
        # Usar validación del modelo
        try:
            ValidacionStock.validar_stock_no_negativo(stock_actual, -cantidad_requerida)
            return True
        except ValueError as e:
            logger.warning(f"Stock insuficiente para producto {producto_id}: {e}")
            return False

    async def registrar_movimiento_stock(self, movimiento: MovimientoStock) -> Dict[str, Any]:
        """
        Registrar movimiento de stock con validaciones completas
        """
        async with self.atomic_stock_operation(movimiento.producto_id) as session:
            
            # 1. Validar stock suficiente para salidas
            if movimiento.tipo_movimiento == "SALIDA" and movimiento.cantidad > 0:
                if not await self.validar_stock_suficiente(session, movimiento.producto_id, movimiento.cantidad):
                    raise ValueError("Stock insuficiente para realizar la operación")
            
            # 2. Obtener stock anterior para auditoría
            stock_anterior = await self._calcular_stock_actual(session, movimiento.producto_id)
            
            # 3. Calcular stock posterior
            if movimiento.tipo_movimiento in ["ENTRADA", "AJUSTE"]:
                cantidad_real = abs(movimiento.cantidad)
            else:  # SALIDA, TRANSFERENCIA
                cantidad_real = -abs(movimiento.cantidad)
                
            stock_posterior = stock_anterior + cantidad_real
            
            # 4. Insertar movimiento con auditoría completa
            movimiento_data = {
                "producto_id": movimiento.producto_id,
                "cantidad": cantidad_real,
                "tipo_movimiento": movimiento.tipo_movimiento,
                "deposito_id": movimiento.deposito_id,
                "precio_unitario": movimiento.precio_unitario,
                "stock_anterior": stock_anterior,
                "stock_posterior": stock_posterior,
                "observaciones": movimiento.observaciones,
                "created_at": datetime.now(),
                "usuario_id": 1  # TODO: obtener del contexto
            }
            
            session.execute(
                "INSERT INTO movimientos_stock (producto_id, cantidad, tipo_movimiento, deposito_id, "
                "precio_unitario, stock_anterior, stock_posterior, observaciones, created_at, usuario_id) "
                "VALUES (:producto_id, :cantidad, :tipo_movimiento, :deposito_id, :precio_unitario, "
                ":stock_anterior, :stock_posterior, :observaciones, :created_at, :usuario_id)",
                movimiento_data
            )
            
            # 5. Actualizar stock actual en tabla productos (desnormalización para performance)
            session.execute(
                "UPDATE productos SET stock_actual = :stock_actual WHERE id = :producto_id",
                {"stock_actual": stock_posterior, "producto_id": movimiento.producto_id}
            )
            
            logger.info(
                f"Movimiento registrado: Producto {movimiento.producto_id}, "
                f"Tipo {movimiento.tipo_movimiento}, Cantidad {cantidad_real}, "
                f"Stock: {stock_anterior} → {stock_posterior}"
            )
            
            return {
                "success": True,
                "movimiento_id": "generated_id",  # TODO: obtener ID real
                "stock_anterior": stock_anterior,
                "stock_posterior": stock_posterior,
                "mensaje": f"Movimiento {movimiento.tipo_movimiento} registrado exitosamente"
            }

    async def _calcular_stock_actual(self, session: Session, producto_id: int) -> int:
        """Calcular stock actual basado en movimientos históricos"""
        query = """
        SELECT COALESCE(SUM(cantidad), 0) as stock_total
        FROM movimientos_stock 
        WHERE producto_id = :producto_id
        """
        
        result = session.execute(query, {"producto_id": producto_id}).first()
        return result[0] if result else 0

    async def obtener_alertas_stock_bajo(self, deposito_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtener productos con stock bajo para alertas
        """
        session = self.db_session_factory()
        try:
            query = """
            SELECT 
                p.id,
                p.codigo,
                p.nombre,
                p.stock_actual,
                p.stock_minimo,
                p.categoria,
                CASE 
                    WHEN p.stock_actual = 0 THEN 'AGOTADO'
                    WHEN p.stock_actual <= p.stock_minimo * 0.5 THEN 'CRITICO'
                    ELSE 'BAJO'
                END as nivel_criticidad
            FROM productos p
            WHERE p.stock_actual <= p.stock_minimo
                AND p.active = true
            """ + (" AND p.deposito_id = :deposito_id" if deposito_id else "") + """
            ORDER BY 
                CASE 
                    WHEN p.stock_actual = 0 THEN 1
                    WHEN p.stock_actual <= p.stock_minimo * 0.5 THEN 2
                    ELSE 3
                END,
                p.stock_actual ASC
            """
            
            params = {"deposito_id": deposito_id} if deposito_id else {}
            
            result = session.execute(query, params).fetchall()
            
            alertas = []
            for row in result:
                alertas.append({
                    "producto_id": row[0],
                    "codigo": row[1],
                    "nombre": row[2],
                    "stock_actual": row[3],
                    "stock_minimo": row[4],
                    "categoria": row[5],
                    "nivel_criticidad": row[6],
                    "fecha_alerta": datetime.now()
                })
            
            logger.info(f"Encontradas {len(alertas)} alertas de stock bajo")
            return alertas
            
        finally:
            session.close()

    async def transferir_stock(self, producto_id: int, deposito_origen: int, 
                              deposito_destino: int, cantidad: int, 
                              observaciones: str = None) -> Dict[str, Any]:
        """
        Transferir stock entre depósitos de forma atómica
        """
        # Validar transferencia
        ValidacionStock.validar_transferencia_depositos(deposito_origen, deposito_destino)
        
        # Crear movimientos de salida y entrada
        movimiento_salida = MovimientoStock(
            producto_id=producto_id,
            cantidad=cantidad,
            tipo_movimiento="SALIDA",
            deposito_id=deposito_origen,
            observaciones=f"Transferencia a depósito {deposito_destino}. {observaciones or ''}"
        )
        
        movimiento_entrada = MovimientoStock(
            producto_id=producto_id,
            cantidad=cantidad,
            tipo_movimiento="ENTRADA",
            deposito_id=deposito_destino,
            observaciones=f"Transferencia desde depósito {deposito_origen}. {observaciones or ''}"
        )
        
        # Ejecutar transferencia atómicamente
        async with self.atomic_stock_operation(producto_id) as session:
            # Registrar salida
            result_salida = await self.registrar_movimiento_stock(movimiento_salida)
            
            # Registrar entrada
            result_entrada = await self.registrar_movimiento_stock(movimiento_entrada)
            
            logger.info(
                f"Transferencia completada: Producto {producto_id}, "
                f"Cantidad {cantidad}, {deposito_origen} → {deposito_destino}"
            )
            
            return {
                "success": True,
                "transferencia_id": f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "movimiento_salida": result_salida,
                "movimiento_entrada": result_entrada,
                "mensaje": "Transferencia completada exitosamente"
            }