
"""
E-commerce Sync Scheduler - Sincronización Automática con MercadoLibre
Programador de tareas de sincronización con plataformas e-commerce.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import schedule
import time
from threading import Thread
import json

from integrations.ecommerce.mercadolibre_client import MercadoLibreClient
from models.database import get_db_session
from utils.retry_handler import retry_with_backoff
from utils.notifications import EmailNotifier, SlackNotifier

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TipoSyncEcommerce(Enum):
    """Tipos de sincronización e-commerce"""
    SYNC_STOCK = "sync_stock"
    SYNC_PRECIOS = "sync_precios"
    PROCESAR_ORDENES = "procesar_ordenes"
    ACTUALIZAR_PUBLICACIONES = "actualizar_publicaciones"
    SINCRONIZAR_PREGUNTAS = "sincronizar_preguntas"
    BACKUP_DATOS = "backup_datos"

@dataclass
class TareaSyncEcommerce:
    """Definición de tarea de sincronización e-commerce"""
    tipo: TipoSyncEcommerce
    descripcion: str
    intervalo_minutos: int
    activa: bool = True
    ultima_ejecucion: Optional[datetime] = None
    proxima_ejecucion: Optional[datetime] = None
    intentos_fallidos: int = 0
    max_intentos: int = 5

class EcommerceSyncScheduler:
    """
    Scheduler para sincronización automática con plataformas e-commerce.
    Maneja stock, precios, órdenes y publicaciones en MercadoLibre.
    """

    def __init__(self, 
                 ml_client: MercadoLibreClient,
                 email_notifier: Optional[EmailNotifier] = None,
                 slack_notifier: Optional[SlackNotifier] = None):
        self.ml_client = ml_client
        self.email_notifier = email_notifier
        self.slack_notifier = slack_notifier
        self.tareas: List[TareaSyncEcommerce] = []
        self.running = False
        self.scheduler_thread: Optional[Thread] = None

        # Configurar tareas por defecto
        self._configurar_tareas_default()

    def _configurar_tareas_default(self):
        """Configura las tareas de sync e-commerce por defecto"""
        tareas_default = [
            TareaSyncEcommerce(
                tipo=TipoSyncEcommerce.SYNC_STOCK,
                descripcion="Sincronizar stock con MercadoLibre",
                intervalo_minutos=10  # Cada 10 minutos
            ),
            TareaSyncEcommerce(
                tipo=TipoSyncEcommerce.SYNC_PRECIOS,
                descripcion="Sincronizar precios con MercadoLibre",
                intervalo_minutos=30  # Cada 30 minutos
            ),
            TareaSyncEcommerce(
                tipo=TipoSyncEcommerce.PROCESAR_ORDENES,
                descripcion="Procesar nuevas órdenes de MercadoLibre",
                intervalo_minutos=5  # Cada 5 minutos
            ),
            TareaSyncEcommerce(
                tipo=TipoSyncEcommerce.ACTUALIZAR_PUBLICACIONES,
                descripcion="Actualizar información de publicaciones",
                intervalo_minutos=60  # Cada hora
            ),
            TareaSyncEcommerce(
                tipo=TipoSyncEcommerce.SINCRONIZAR_PREGUNTAS,
                descripcion="Sincronizar preguntas de usuarios",
                intervalo_minutos=15  # Cada 15 minutos
            ),
            TareaSyncEcommerce(
                tipo=TipoSyncEcommerce.BACKUP_DATOS,
                descripcion="Backup de datos e-commerce",
                intervalo_minutos=120  # Cada 2 horas
            )
        ]

        self.tareas.extend(tareas_default)
        logger.info(f"Configuradas {len(tareas_default)} tareas de sync e-commerce por defecto")

    @retry_with_backoff(max_retries=3, backoff_in_seconds=2)
    async def sincronizar_stock(self) -> Dict:
        """Sincronizar stock con MercadoLibre"""
        try:
            logger.info("Iniciando sincronización de stock con MercadoLibre")

            # Obtener productos con stock modificado
            with get_db_session() as db:
                # Simular productos con stock actualizado
                productos_actualizar = [
                    {
                        "producto_id": "PROD001",
                        "ml_item_id": "MLA123456789",
                        "stock_actual": 50,
                        "stock_ml": 45,
                        "nombre": "Producto A"
                    },
                    {
                        "producto_id": "PROD002", 
                        "ml_item_id": "MLA987654321",
                        "stock_actual": 25,
                        "stock_ml": 30,
                        "nombre": "Producto B"
                    },
                    {
                        "producto_id": "PROD003",
                        "ml_item_id": "MLA555666777",
                        "stock_actual": 0,
                        "stock_ml": 10,
                        "nombre": "Producto C"
                    }
                ]

            # Preparar actualizaciones para envío bulk
            bulk_updates = []
            for producto in productos_actualizar:
                if producto["stock_actual"] != producto["stock_ml"]:
                    bulk_updates.append({
                        "item_id": producto["ml_item_id"],
                        "available_quantity": producto["stock_actual"],
                        "producto_id": producto["producto_id"]
                    })

            if not bulk_updates:
                logger.info("No hay stock para sincronizar")
                return {
                    "status": "success",
                    "productos_procesados": 0,
                    "productos_actualizados": 0,
                    "mensaje": "No hay cambios de stock para sincronizar"
                }

            # Ejecutar actualización bulk
            resultados_bulk = await self.ml_client.bulk_update_stock(bulk_updates)

            # Procesar resultados
            actualizaciones_exitosas = 0
            actualizaciones_error = 0
            errores_detalle = []

            for i, resultado in enumerate(resultados_bulk):
                producto_id = bulk_updates[i]["producto_id"]
                item_id = bulk_updates[i]["item_id"]

                if resultado.get("status") == "success":
                    actualizaciones_exitosas += 1
                    logger.info(f"Stock actualizado para {producto_id}: {bulk_updates[i]['available_quantity']}")

                    # Actualizar stock en BD local
                    # En implementación real usar SQLAlchemy

                else:
                    actualizaciones_error += 1
                    error_msg = resultado.get("error", "Error desconocido")
                    logger.error(f"Error actualizando stock {producto_id}: {error_msg}")

                    errores_detalle.append({
                        "producto_id": producto_id,
                        "item_id": item_id,
                        "error": error_msg
                    })

            # Notificar resultados
            if actualizaciones_error == 0:
                mensaje = f"Sync stock exitoso: {actualizaciones_exitosas} productos actualizados"
                await self._notificar_sync_exitoso("Stock MercadoLibre", mensaje)
            else:
                mensaje = f"Sync stock: {actualizaciones_exitosas} OK, {actualizaciones_error} errores"
                await self._notificar_sync_error("Stock MercadoLibre", mensaje)

            logger.info(f"Sincronización stock completada: {actualizaciones_exitosas} OK, {actualizaciones_error} errores")

            return {
                "status": "success" if actualizaciones_error == 0 else "partial_success",
                "productos_procesados": len(bulk_updates),
                "productos_actualizados": actualizaciones_exitosas,
                "productos_error": actualizaciones_error,
                "errores": errores_detalle
            }

        except Exception as e:
            logger.error(f"Error en sincronización de stock: {str(e)}")
            await self._notificar_sync_error("Stock MercadoLibre", str(e))
            raise

    @retry_with_backoff(max_retries=3, backoff_in_seconds=2)
    async def sincronizar_precios(self) -> Dict:
        """Sincronizar precios con MercadoLibre"""
        try:
            logger.info("Iniciando sincronización de precios con MercadoLibre")

            # Obtener productos con precios modificados
            productos_precio = [
                {
                    "producto_id": "PROD001",
                    "ml_item_id": "MLA123456789",
                    "precio_sistema": 1250.00,
                    "precio_ml": 1200.00,
                    "nombre": "Producto A"
                },
                {
                    "producto_id": "PROD002",
                    "ml_item_id": "MLA987654321", 
                    "precio_sistema": 850.50,
                    "precio_ml": 850.50,
                    "nombre": "Producto B"
                }
            ]

            # Preparar actualizaciones de precios
            bulk_price_updates = []
            for producto in productos_precio:
                if abs(producto["precio_sistema"] - producto["precio_ml"]) > 0.01:
                    bulk_price_updates.append({
                        "item_id": producto["ml_item_id"],
                        "price": producto["precio_sistema"],
                        "producto_id": producto["producto_id"]
                    })

            if not bulk_price_updates:
                logger.info("No hay precios para sincronizar")
                return {
                    "status": "success",
                    "productos_procesados": 0,
                    "productos_actualizados": 0,
                    "mensaje": "No hay cambios de precios para sincronizar"
                }

            # Ejecutar actualización bulk de precios
            resultados_precios = await self.ml_client.bulk_update_prices(bulk_price_updates)

            # Procesar resultados
            precios_actualizados = 0
            precios_error = 0
            errores_precio = []

            for i, resultado in enumerate(resultados_precios):
                producto_id = bulk_price_updates[i]["producto_id"]
                nuevo_precio = bulk_price_updates[i]["price"]

                if resultado.get("status") == "success":
                    precios_actualizados += 1
                    logger.info(f"Precio actualizado para {producto_id}: ${nuevo_precio:,.2f}")
                else:
                    precios_error += 1
                    error_msg = resultado.get("error", "Error desconocido")
                    logger.error(f"Error actualizando precio {producto_id}: {error_msg}")

                    errores_precio.append({
                        "producto_id": producto_id,
                        "precio": nuevo_precio,
                        "error": error_msg
                    })

            # Notificar resultados
            if precios_error == 0:
                mensaje = f"Sync precios exitoso: {precios_actualizados} productos actualizados"
                await self._notificar_sync_exitoso("Precios MercadoLibre", mensaje)
            else:
                mensaje = f"Sync precios: {precios_actualizados} OK, {precios_error} errores"
                await self._notificar_sync_error("Precios MercadoLibre", mensaje)

            logger.info(f"Sincronización precios completada: {precios_actualizados} OK, {precios_error} errores")

            return {
                "status": "success" if precios_error == 0 else "partial_success",
                "productos_procesados": len(bulk_price_updates),
                "productos_actualizados": precios_actualizados,
                "productos_error": precios_error,
                "errores": errores_precio
            }

        except Exception as e:
            logger.error(f"Error en sincronización de precios: {str(e)}")
            await self._notificar_sync_error("Precios MercadoLibre", str(e))
            raise

    @retry_with_backoff(max_retries=3, backoff_in_seconds=1)
    async def procesar_ordenes(self) -> Dict:
        """Procesar nuevas órdenes de MercadoLibre"""
        try:
            logger.info("Iniciando procesamiento de órdenes MercadoLibre")

            # Obtener órdenes recientes no procesadas
            ordenes_nuevas = await self.ml_client.obtener_ordenes_pendientes()

            if not ordenes_nuevas:
                # Simular órdenes para el ejemplo
                ordenes_nuevas = [
                    {
                        "id": "2000001234567",
                        "status": "paid",
                        "date_created": datetime.now().isoformat(),
                        "buyer": {
                            "id": 123456789,
                            "nickname": "COMPRADOR123"
                        },
                        "order_items": [
                            {
                                "item": {
                                    "id": "MLA123456789",
                                    "title": "Producto A"
                                },
                                "quantity": 2,
                                "unit_price": 1250.00
                            }
                        ],
                        "total_amount": 2500.00,
                        "shipping": {
                            "id": "40000001234",
                            "mode": "me2",
                            "status": "pending"
                        }
                    }
                ]

            ordenes_procesadas = 0
            ordenes_error = 0
            errores_orden = []

            for orden in ordenes_nuevas:
                try:
                    # Validar orden
                    if orden["status"] != "paid":
                        logger.warning(f"Orden {orden['id']} no está pagada, status: {orden['status']}")
                        continue

                    # Crear orden en sistema interno
                    orden_interna = {
                        "ml_order_id": orden["id"],
                        "fecha_orden": orden["date_created"],
                        "cliente_ml_id": orden["buyer"]["id"],
                        "cliente_nickname": orden["buyer"]["nickname"],
                        "total": orden["total_amount"],
                        "estado": "PAGADA",
                        "items": []
                    }

                    # Procesar items de la orden
                    for item in orden["order_items"]:
                        item_interno = {
                            "ml_item_id": item["item"]["id"],
                            "titulo": item["item"]["title"],
                            "cantidad": item["quantity"],
                            "precio_unitario": item["unit_price"],
                            "subtotal": item["quantity"] * item["unit_price"]
                        }
                        orden_interna["items"].append(item_interno)

                        # Descontar stock del producto
                        # En implementación real usar SQLAlchemy para actualizar stock
                        logger.info(f"Descontando stock: {item['item']['id']} - cantidad: {item['quantity']}")

                    # Guardar orden en BD
                    # En implementación real usar SQLAlchemy
                    logger.info(f"Orden procesada: {orden['id']} - Total: ${orden['total_amount']:,.2f}")
                    ordenes_procesadas += 1

                    # Notificar nueva orden si está configurado
                    if orden["total_amount"] > 5000:  # Órdenes importantes
                        mensaje_orden = f"Nueva orden importante: {orden['id']} - ${orden['total_amount']:,.2f}"
                        await self._notificar_sync_exitoso("Nueva Orden ML", mensaje_orden)

                except Exception as e:
                    ordenes_error += 1
                    error_msg = str(e)
                    logger.error(f"Error procesando orden {orden['id']}: {error_msg}")

                    errores_orden.append({
                        "orden_id": orden["id"],
                        "error": error_msg
                    })

            # Notificar resultados generales
            if ordenes_error == 0 and ordenes_procesadas > 0:
                mensaje = f"Órdenes procesadas exitosamente: {ordenes_procesadas}"
                await self._notificar_sync_exitoso("Órdenes MercadoLibre", mensaje)
            elif ordenes_error > 0:
                mensaje = f"Procesamiento órdenes: {ordenes_procesadas} OK, {ordenes_error} errores"
                await self._notificar_sync_error("Órdenes MercadoLibre", mensaje)

            logger.info(f"Procesamiento órdenes completado: {ordenes_procesadas} OK, {ordenes_error} errores")

            return {
                "status": "success" if ordenes_error == 0 else "partial_success",
                "ordenes_encontradas": len(ordenes_nuevas),
                "ordenes_procesadas": ordenes_procesadas,
                "ordenes_error": ordenes_error,
                "errores": errores_orden
            }

        except Exception as e:
            logger.error(f"Error en procesamiento de órdenes: {str(e)}")
            await self._notificar_sync_error("Órdenes MercadoLibre", str(e))
            raise

    @retry_with_backoff(max_retries=2, backoff_in_seconds=5)
    async def actualizar_publicaciones(self) -> Dict:
        """Actualizar información de publicaciones"""
        try:
            logger.info("Iniciando actualización de publicaciones MercadoLibre")

            # Obtener publicaciones activas
            publicaciones = await self.ml_client.obtener_publicaciones_activas()

            # Simular publicaciones si no hay respuesta
            if not publicaciones:
                publicaciones = [
                    {
                        "id": "MLA123456789",
                        "title": "Producto A - Excelente Calidad",
                        "price": 1250.00,
                        "available_quantity": 50,
                        "status": "active",
                        "health": 0.85
                    },
                    {
                        "id": "MLA987654321",
                        "title": "Producto B - Oferta Especial", 
                        "price": 850.50,
                        "available_quantity": 25,
                        "status": "paused",
                        "health": 0.60
                    }
                ]

            publicaciones_actualizadas = 0
            publicaciones_pausadas = 0
            publicaciones_reactivadas = 0

            for pub in publicaciones:
                try:
                    # Verificar salud de la publicación
                    if pub.get("health", 1.0) < 0.7:
                        logger.warning(f"Publicación {pub['id']} tiene baja salud: {pub.get('health', 'N/A')}")

                        # Optimizar publicación (en implementación real)
                        # - Actualizar título, descripción
                        # - Mejorar imágenes
                        # - Ajustar precio competitivo

                    # Verificar stock disponible
                    if pub["available_quantity"] == 0 and pub["status"] == "active":
                        # Pausar publicación sin stock
                        await self.ml_client.pausar_publicacion(pub["id"])
                        publicaciones_pausadas += 1
                        logger.info(f"Publicación pausada por falta de stock: {pub['id']}")

                    elif pub["available_quantity"] > 0 and pub["status"] == "paused":
                        # Reactivar publicación con stock
                        await self.ml_client.reactivar_publicacion(pub["id"])
                        publicaciones_reactivadas += 1
                        logger.info(f"Publicación reactivada: {pub['id']}")

                    publicaciones_actualizadas += 1

                except Exception as e:
                    logger.error(f"Error actualizando publicación {pub['id']}: {str(e)}")

            mensaje = f"Publicaciones actualizadas: {publicaciones_actualizadas}, pausadas: {publicaciones_pausadas}, reactivadas: {publicaciones_reactivadas}"
            await self._notificar_sync_exitoso("Publicaciones ML", mensaje)

            logger.info(f"Actualización publicaciones completada: {publicaciones_actualizadas} procesadas")

            return {
                "status": "success",
                "publicaciones_procesadas": len(publicaciones),
                "publicaciones_actualizadas": publicaciones_actualizadas,
                "publicaciones_pausadas": publicaciones_pausadas,
                "publicaciones_reactivadas": publicaciones_reactivadas
            }

        except Exception as e:
            logger.error(f"Error actualizando publicaciones: {str(e)}")
            await self._notificar_sync_error("Publicaciones ML", str(e))
            raise

    @retry_with_backoff(max_retries=2, backoff_in_seconds=3)
    async def sincronizar_preguntas(self) -> Dict:
        """Sincronizar preguntas de usuarios"""
        try:
            logger.info("Iniciando sincronización de preguntas MercadoLibre")

            # Obtener preguntas no respondidas
            preguntas_pendientes = await self.ml_client.obtener_preguntas_pendientes()

            # Simular preguntas si no hay respuesta
            if not preguntas_pendientes:
                preguntas_pendientes = [
                    {
                        "id": 12345678,
                        "text": "¿Cuándo llega el producto?",
                        "item_id": "MLA123456789",
                        "from": {
                            "id": 987654321,
                            "answered_questions": 5
                        },
                        "date_created": datetime.now().isoformat(),
                        "status": "UNANSWERED"
                    },
                    {
                        "id": 87654321,
                        "text": "¿Hacen factura A?",
                        "item_id": "MLA987654321",
                        "from": {
                            "id": 123456789,
                            "answered_questions": 15
                        },
                        "date_created": (datetime.now() - timedelta(hours=2)).isoformat(),
                        "status": "UNANSWERED"
                    }
                ]

            preguntas_respondidas = 0
            preguntas_pendientes_manual = 0

            for pregunta in preguntas_pendientes:
                try:
                    # Analizar pregunta para respuesta automática
                    texto_pregunta = pregunta["text"].lower()
                    respuesta_automatica = None

                    # Respuestas automáticas básicas
                    if "envío" in texto_pregunta or "envio" in texto_pregunta or "llega" in texto_pregunta:
                        respuesta_automatica = "¡Hola! Los envíos se realizan dentro de las 24hs hábiles. El tiempo de entrega depende de tu ubicación. ¡Gracias por tu consulta!"

                    elif "factura" in texto_pregunta:
                        respuesta_automatica = "¡Hola! Sí, emitimos factura A y B según corresponda. Indicanos tu situación fiscal al comprar. ¡Gracias!"

                    elif "stock" in texto_pregunta or "disponible" in texto_pregunta:
                        respuesta_automatica = "¡Hola! Tenemos stock disponible. Podés comprar con confianza. ¡Gracias por consultarnos!"

                    if respuesta_automatica:
                        # Enviar respuesta automática
                        resultado = await self.ml_client.responder_pregunta(
                            pregunta["id"], 
                            respuesta_automatica
                        )

                        if resultado.get("success"):
                            preguntas_respondidas += 1
                            logger.info(f"Pregunta respondida automáticamente: {pregunta['id']}")
                        else:
                            preguntas_pendientes_manual += 1
                            logger.warning(f"No se pudo responder pregunta: {pregunta['id']}")
                    else:
                        # Marcar para respuesta manual
                        preguntas_pendientes_manual += 1
                        logger.info(f"Pregunta marcada para respuesta manual: {pregunta['id']}")

                        # Guardar en BD para revisión manual
                        # En implementación real usar SQLAlchemy

                except Exception as e:
                    logger.error(f"Error procesando pregunta {pregunta['id']}: {str(e)}")

            if preguntas_respondidas > 0:
                mensaje = f"Preguntas procesadas: {preguntas_respondidas} respondidas, {preguntas_pendientes_manual} pendientes"
                await self._notificar_sync_exitoso("Preguntas ML", mensaje)

            logger.info(f"Sincronización preguntas completada: {preguntas_respondidas} respondidas, {preguntas_pendientes_manual} pendientes")

            return {
                "status": "success",
                "preguntas_encontradas": len(preguntas_pendientes),
                "preguntas_respondidas": preguntas_respondidas,
                "preguntas_pendientes_manual": preguntas_pendientes_manual
            }

        except Exception as e:
            logger.error(f"Error sincronizando preguntas: {str(e)}")
            await self._notificar_sync_error("Preguntas ML", str(e))
            raise

    @retry_with_backoff(max_retries=2, backoff_in_seconds=1)
    async def backup_datos_ecommerce(self) -> Dict:
        """Backup de datos e-commerce"""
        try:
            logger.info("Iniciando backup de datos e-commerce")

            # Recopilar datos para backup
            fecha_backup = datetime.now()

            # Simular datos de backup
            datos_backup = {
                "fecha_backup": fecha_backup.isoformat(),
                "ordenes_recientes": [
                    {
                        "id": "2000001234567",
                        "fecha": "2024-01-15T10:30:00",
                        "total": 2500.00,
                        "estado": "PROCESADA"
                    }
                ],
                "publicaciones_activas": [
                    {
                        "id": "MLA123456789",
                        "titulo": "Producto A",
                        "precio": 1250.00,
                        "stock": 50
                    }
                ],
                "preguntas_respondidas": [
                    {
                        "id": 12345678,
                        "pregunta": "¿Cuándo llega?",
                        "respuesta": "Envíos en 24hs",
                        "fecha": "2024-01-15T14:20:00"
                    }
                ],
                "metricas": {
                    "ventas_dia": 15750.00,
                    "ordenes_dia": 8,
                    "preguntas_respondidas": 12,
                    "publicaciones_activas": 45
                }
            }

            # Guardar backup
            backup_filename = f"backup_ecommerce_{fecha_backup.strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = f"backups/ecommerce/{backup_filename}"

            import os
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)

            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(datos_backup, f, indent=2, ensure_ascii=False)

            mensaje = f"Backup e-commerce creado: {len(datos_backup['ordenes_recientes'])} órdenes, {len(datos_backup['publicaciones_activas'])} publicaciones"
            await self._notificar_sync_exitoso("Backup E-commerce", mensaje)

            logger.info(f"Backup e-commerce completado: {backup_filename}")

            return {
                "status": "success",
                "archivo_backup": backup_filename,
                "ordenes_respaldadas": len(datos_backup["ordenes_recientes"]),
                "publicaciones_respaldadas": len(datos_backup["publicaciones_activas"]),
                "tamaño_mb": 0.2  # Simular tamaño
            }

        except Exception as e:
            logger.error(f"Error en backup e-commerce: {str(e)}")
            await self._notificar_sync_error("Backup E-commerce", str(e))
            raise

    async def ejecutar_sync(self, tipo_sync: TipoSyncEcommerce) -> Dict:
        """Ejecutar sincronización específica por tipo"""
        ejecutores = {
            TipoSyncEcommerce.SYNC_STOCK: self.sincronizar_stock,
            TipoSyncEcommerce.SYNC_PRECIOS: self.sincronizar_precios,
            TipoSyncEcommerce.PROCESAR_ORDENES: self.procesar_ordenes,
            TipoSyncEcommerce.ACTUALIZAR_PUBLICACIONES: self.actualizar_publicaciones,
            TipoSyncEcommerce.SINCRONIZAR_PREGUNTAS: self.sincronizar_preguntas,
            TipoSyncEcommerce.BACKUP_DATOS: self.backup_datos_ecommerce
        }

        if tipo_sync not in ejecutores:
            raise ValueError(f"Tipo de sync no soportado: {tipo_sync}")

        # Encontrar la tarea
        tarea = next((t for t in self.tareas if t.tipo == tipo_sync), None)
        if not tarea:
            raise ValueError(f"Tarea no encontrada: {tipo_sync}")

        try:
            logger.info(f"Ejecutando sync e-commerce: {tarea.descripcion}")

            # Ejecutar la sincronización
            resultado = await ejecutores[tipo_sync]()

            # Actualizar estado de la tarea
            tarea.ultima_ejecucion = datetime.now()
            tarea.proxima_ejecucion = datetime.now() + timedelta(minutes=tarea.intervalo_minutos)
            tarea.intentos_fallidos = 0

            logger.info(f"Sync e-commerce completado exitosamente: {tipo_sync.value}")
            return resultado

        except Exception as e:
            # Incrementar contador de fallos
            tarea.intentos_fallidos += 1

            logger.error(f"Error ejecutando sync e-commerce {tipo_sync.value}: {str(e)}")

            # Si superó el máximo de intentos, desactivar temporalmente
            if tarea.intentos_fallidos >= tarea.max_intentos:
                tarea.activa = False
                logger.warning(f"Sync e-commerce {tipo_sync.value} desactivado por múltiples fallos")
                await self._notificar_sync_error(
                    f"Sync E-commerce Desactivado: {tarea.descripcion}",
                    f"Desactivado tras {tarea.intentos_fallidos} intentos fallidos"
                )

            raise

    async def _notificar_sync_exitoso(self, titulo: str, mensaje: str):
        """Notificar sincronización exitosa"""
        try:
            if self.email_notifier:
                await self.email_notifier.enviar_notificacion(
                    asunto=f"✅ E-commerce Sync: {titulo}",
                    mensaje=mensaje,
                    tipo="success"
                )

            if self.slack_notifier:
                await self.slack_notifier.enviar_mensaje(
                    canal="#ecommerce-sync",
                    mensaje=f"✅ *{titulo}*\n{mensaje}",
                    color="good"
                )
        except Exception as e:
            logger.warning(f"Error enviando notificación de éxito: {str(e)}")

    async def _notificar_sync_error(self, titulo: str, error: str):
        """Notificar error en sincronización"""
        try:
            if self.email_notifier:
                await self.email_notifier.enviar_notificacion(
                    asunto=f"❌ E-commerce Sync Error: {titulo}",
                    mensaje=f"Error: {error}",
                    tipo="error"
                )

            if self.slack_notifier:
                await self.slack_notifier.enviar_mensaje(
                    canal="#ecommerce-sync",
                    mensaje=f"❌ *{titulo}*\nError: {error}",
                    color="danger"
                )
        except Exception as e:
            logger.warning(f"Error enviando notificación de error: {str(e)}")

    def programar_syncs(self):
        """Programar todas las sincronizaciones activas"""
        schedule.clear("ecommerce_sync")  # Limpiar tareas previas

        for tarea in self.tareas:
            if not tarea.activa:
                continue

            # Programar según intervalo
            schedule.every(tarea.intervalo_minutos).minutes.do(
                self._ejecutar_sync_sync, tarea.tipo
            ).tag("ecommerce_sync")

        logger.info(f"Programadas {len([t for t in self.tareas if t.activa])} sincronizaciones e-commerce")

    def _ejecutar_sync_sync(self, tipo_sync: TipoSyncEcommerce):
        """Wrapper sincrónico para ejecutar syncs async"""
        try:
            asyncio.run(self.ejecutar_sync(tipo_sync))
        except Exception as e:
            logger.error(f"Error en ejecución sincrónica de {tipo_sync.value}: {str(e)}")

    def iniciar_scheduler(self):
        """Iniciar el scheduler de sync e-commerce"""
        if self.running:
            logger.warning("E-commerce Sync Scheduler ya está ejecutándose")
            return

        self.running = True
        self.programar_syncs()

        def run_scheduler():
            logger.info("Iniciando E-commerce Sync Scheduler")
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(30)  # Verificar cada 30 segundos
                except Exception as e:
                    logger.error(f"Error en e-commerce scheduler loop: {str(e)}")
                    time.sleep(30)

        self.scheduler_thread = Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("E-commerce Sync Scheduler iniciado exitosamente")

    def detener_scheduler(self):
        """Detener el scheduler"""
        if not self.running:
            return

        self.running = False
        schedule.clear("ecommerce_sync")

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        logger.info("E-commerce Sync Scheduler detenido")

    def obtener_estado_syncs(self) -> List[Dict]:
        """Obtener estado actual de todas las sincronizaciones"""
        estado_syncs = []

        for tarea in self.tareas:
            estado_syncs.append({
                "tipo": tarea.tipo.value,
                "descripcion": tarea.descripcion,
                "activa": tarea.activa,
                "intervalo_minutos": tarea.intervalo_minutos,
                "ultima_ejecucion": tarea.ultima_ejecucion.isoformat() if tarea.ultima_ejecucion else None,
                "proxima_ejecucion": tarea.proxima_ejecucion.isoformat() if tarea.proxima_ejecucion else None,
                "intentos_fallidos": tarea.intentos_fallidos,
                "max_intentos": tarea.max_intentos
            })

        return estado_syncs

    async def ejecutar_sync_manual(self, tipo_sync: TipoSyncEcommerce) -> Dict:
        """Ejecutar sincronización manualmente"""
        logger.info(f"Sincronización e-commerce manual solicitada para: {tipo_sync.value}")

        try:
            resultado = await self.ejecutar_sync(tipo_sync)
            logger.info(f"Sincronización e-commerce manual completada: {tipo_sync.value}")
            return {
                "status": "success",
                "tipo_sync": tipo_sync.value,
                "resultado": resultado,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en sincronización e-commerce manual {tipo_sync.value}: {str(e)}")
            return {
                "status": "error",
                "tipo_sync": tipo_sync.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Factory function
def crear_ecommerce_sync_scheduler(
    ml_client: MercadoLibreClient,
    config_notificaciones: Optional[Dict] = None
) -> EcommerceSyncScheduler:
    """
    Factory para crear un EcommerceSyncScheduler configurado.
    """

    email_notifier = None
    slack_notifier = None

    if config_notificaciones:
        if config_notificaciones.get("email_enabled"):
            from utils.notifications import EmailNotifier
            email_notifier = EmailNotifier(
                smtp_server=config_notificaciones["email_smtp_server"],
                smtp_port=config_notificaciones["email_smtp_port"],
                username=config_notificaciones["email_username"],
                password=config_notificaciones["email_password"],
                from_email=config_notificaciones["email_from"]
            )

        if config_notificaciones.get("slack_enabled"):
            from utils.notifications import SlackNotifier
            slack_notifier = SlackNotifier(
                webhook_url=config_notificaciones["slack_webhook_url"],
                canal_default=config_notificaciones.get("slack_canal", "#ecommerce-sync")
            )

    return EcommerceSyncScheduler(
        ml_client=ml_client,
        email_notifier=email_notifier,
        slack_notifier=slack_notifier
    )

if __name__ == "__main__":
    # Ejemplo de uso
    import asyncio
    from integrations.ecommerce.mercadolibre_client import MLCredentials

    async def ejemplo_uso():
        # Crear cliente MercadoLibre
        credentials = MLCredentials(
            app_id="1234567890123456",
            client_secret="AbCdEfGhIjKlMnOpQrStUvWxYz",
            access_token="APP_USR-1234567890123456-abcdef-ghijklmnopqrstuvwxyz123456-987654321",
            refresh_token="TG-abcdef1234567890abcdef1234567890abcdef12"
        )

        from integrations.ecommerce.mercadolibre_client import MercadoLibreClient
        ml_client = MercadoLibreClient(credentials)

        # Crear scheduler
        scheduler = crear_ecommerce_sync_scheduler(ml_client)

        # Iniciar scheduler
        scheduler.iniciar_scheduler()

        # Ejecutar sync manual para testing
        resultado = await scheduler.ejecutar_sync_manual(
            TipoSyncEcommerce.SYNC_STOCK
        )
        print("Resultado sync manual:", resultado)

        # Obtener estado
        estado = scheduler.obtener_estado_syncs()
        print("Estado syncs:", estado)

        # Esperar y detener
        await asyncio.sleep(5)
        scheduler.detener_scheduler()

    # Ejecutar ejemplo
    asyncio.run(ejemplo_uso())
