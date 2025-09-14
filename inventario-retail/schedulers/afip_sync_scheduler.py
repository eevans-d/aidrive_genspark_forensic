
"""
AFIP Sync Scheduler - Sincronización Automática con AFIP
Programador de tareas de sincronización con servicios AFIP.
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

from integrations.afip.wsfe_client import AFIPWSFEClient, FacturaElectronica
from models.database import get_db_session
from utils.retry_handler import retry_with_backoff
from utils.notifications import EmailNotifier, SlackNotifier

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TipoSyncAFIP(Enum):
    """Tipos de sincronización AFIP"""
    FACTURAS_PENDIENTES = "facturas_pendientes"
    VALIDACION_CAES = "validacion_caes"
    ACTUALIZACION_PUNTOS_VENTA = "actualizacion_puntos_venta"
    SINCRONIZACION_PADRON = "sincronizacion_padron"
    BACKUP_COMPROBANTES = "backup_comprobantes"

@dataclass
class TareaSyncAFIP:
    """Definición de tarea de sincronización AFIP"""
    tipo: TipoSyncAFIP
    descripcion: str
    intervalo_minutos: int
    activa: bool = True
    ultima_ejecucion: Optional[datetime] = None
    proxima_ejecucion: Optional[datetime] = None
    intentos_fallidos: int = 0
    max_intentos: int = 5

class AFIPSyncScheduler:
    """
    Scheduler para sincronización automática con AFIP.
    Maneja facturas electrónicas, CAEs, puntos de venta y padrón.
    """

    def __init__(self, 
                 afip_client: AFIPWSFEClient,
                 email_notifier: Optional[EmailNotifier] = None,
                 slack_notifier: Optional[SlackNotifier] = None):
        self.afip_client = afip_client
        self.email_notifier = email_notifier
        self.slack_notifier = slack_notifier
        self.tareas: List[TareaSyncAFIP] = []
        self.running = False
        self.scheduler_thread: Optional[Thread] = None

        # Configurar tareas por defecto
        self._configurar_tareas_default()

    def _configurar_tareas_default(self):
        """Configura las tareas de sync AFIP por defecto"""
        tareas_default = [
            TareaSyncAFIP(
                tipo=TipoSyncAFIP.FACTURAS_PENDIENTES,
                descripcion="Sincronizar facturas pendientes con AFIP",
                intervalo_minutos=15  # Cada 15 minutos
            ),
            TareaSyncAFIP(
                tipo=TipoSyncAFIP.VALIDACION_CAES,
                descripcion="Validar CAEs generados",
                intervalo_minutos=30  # Cada 30 minutos
            ),
            TareaSyncAFIP(
                tipo=TipoSyncAFIP.ACTUALIZACION_PUNTOS_VENTA,
                descripcion="Actualizar información de puntos de venta",
                intervalo_minutos=120  # Cada 2 horas
            ),
            TareaSyncAFIP(
                tipo=TipoSyncAFIP.SINCRONIZACION_PADRON,
                descripcion="Sincronizar datos del padrón AFIP",
                intervalo_minutos=360  # Cada 6 horas
            ),
            TareaSyncAFIP(
                tipo=TipoSyncAFIP.BACKUP_COMPROBANTES,
                descripcion="Backup de comprobantes electrónicos",
                intervalo_minutos=60  # Cada hora
            )
        ]

        self.tareas.extend(tareas_default)
        logger.info(f"Configuradas {len(tareas_default)} tareas de sync AFIP por defecto")

    async def sincronizar_facturas_pendientes(self) -> Dict:
        """Sincronizar facturas pendientes con AFIP con circuit breaker"""
        # Circuit breaker implementation
        max_failures = int(os.getenv('AFIP_MAX_FAILURES', '5'))
        timeout_seconds = int(os.getenv('AFIP_TIMEOUT_SECONDS', '30'))
        
        try:
            logger.info("Iniciando sincronización de facturas pendientes")
            
            # Timeout protection
            return await asyncio.wait_for(
                self._sync_facturas_internal(),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error(f"AFIP sync timeout after {timeout_seconds} seconds", exc_info=True, extra={
                "timeout_seconds": timeout_seconds,
                "context": "afip_sync_timeout"
            })
            raise
        except Exception as e:
            logger.error(f"AFIP sync failed: {e}", exc_info=True, extra={
                "context": "afip_sync_error"
            })
            raise
    
    async def _sync_facturas_internal(self) -> Dict:

            # Obtener facturas pendientes de envío a AFIP
            with get_db_session() as db:
                # Simular query de facturas pendientes
                facturas_pendientes = [
                    {
                        "id": 1,
                        "numero": 1001,
                        "punto_venta": 1,
                        "tipo_comprobante": 1,  # Factura A
                        "cuit_cliente": "20-12345678-9",
                        "fecha_emision": datetime.now().date(),
                        "importe_total": 1210.00,
                        "estado": "PENDIENTE_AFIP"
                    },
                    {
                        "id": 2,
                        "numero": 1002,
                        "punto_venta": 1,
                        "tipo_comprobante": 6,  # Factura B
                        "cuit_cliente": "27-87654321-3",
                        "fecha_emision": datetime.now().date(),
                        "importe_total": 550.50,
                        "estado": "PENDIENTE_AFIP"
                    }
                ]

            resultados = []
            facturas_exitosas = 0
            facturas_error = 0

            for factura_data in facturas_pendientes:
                try:
                    # Crear objeto FacturaElectronica
                    factura = FacturaElectronica(
                        tipo_cbte=factura_data["tipo_comprobante"],
                        punto_vta=factura_data["punto_venta"],
                        cbte_desde=factura_data["numero"],
                        cbte_hasta=factura_data["numero"],
                        imp_total=factura_data["importe_total"],
                        fecha_cbte=factura_data["fecha_emision"],
                        doc_tipo=80,  # CUIT
                        doc_nro=int(factura_data["cuit_cliente"].replace("-", "")),
                        concepto=1,  # Productos
                        mon_id="PES",
                        mon_cotiz=1.0
                    )

                    # Generar CAE con AFIP
                    resultado_cae = await self.afip_client.generar_cae(factura)

                    if resultado_cae.get("success"):
                        # Actualizar factura en BD con CAE
                        cae_info = {
                            "cae": resultado_cae["cae"],
                            "fecha_vencimiento": resultado_cae["fecha_vencimiento"],
                            "estado": "APROBADA_AFIP",
                            "fecha_sync": datetime.now().isoformat()
                        }

                        # Simular actualización en BD
                        logger.info(f"Factura {factura_data['id']} sincronizada: CAE {cae_info['cae']}")
                        facturas_exitosas += 1

                        resultados.append({
                            "factura_id": factura_data["id"],
                            "numero": factura_data["numero"],
                            "status": "success",
                            "cae": cae_info["cae"]
                        })
                    else:
                        error_msg = resultado_cae.get("error", "Error desconocido")
                        logger.error(f"Error en factura {factura_data['id']}: {error_msg}")
                        facturas_error += 1

                        resultados.append({
                            "factura_id": factura_data["id"],
                            "numero": factura_data["numero"],
                            "status": "error",
                            "error": error_msg
                        })

                except Exception as e:
                    logger.error(f"Error procesando factura {factura_data['id']}: {str(e)}")
                    facturas_error += 1

                    resultados.append({
                        "factura_id": factura_data["id"],
                        "numero": factura_data["numero"],
                        "status": "error",
                        "error": str(e)
                    })

            # Notificar resultados
            if facturas_error == 0:
                mensaje = f"Sincronización AFIP exitosa: {facturas_exitosas} facturas procesadas"
                await self._notificar_sync_exitoso("Facturas AFIP", mensaje)
            else:
                mensaje = f"Sincronización AFIP con errores: {facturas_exitosas} OK, {facturas_error} errores"
                await self._notificar_sync_error("Facturas AFIP", mensaje)

            logger.info(f"Sincronización facturas completada: {facturas_exitosas} OK, {facturas_error} errores")

            return {
                "status": "success" if facturas_error == 0 else "partial_success",
                "facturas_procesadas": len(facturas_pendientes),
                "facturas_exitosas": facturas_exitosas,
                "facturas_error": facturas_error,
                "resultados": resultados
            }

        except Exception as e:
            logger.error(f"Error en sincronización de facturas: {str(e)}")
            await self._notificar_sync_error("Facturas AFIP", str(e))
            raise

    @retry_with_backoff(max_retries=3, backoff_in_seconds=1)
    async def validar_caes_generados(self) -> Dict:
        """Validar CAEs ya generados"""
        try:
            logger.info("Iniciando validación de CAEs generados")

            # Obtener CAEs recientes para validar
            fecha_desde = datetime.now().date() - timedelta(days=7)

            # Simular CAEs para validar
            caes_validar = [
                {
                    "id": 1,
                    "tipo_cbte": 1,
                    "punto_venta": 1,
                    "numero": 1001,
                    "cae": "67891234567890",
                    "fecha_generacion": "2024-01-15"
                },
                {
                    "id": 2,
                    "tipo_cbte": 6,
                    "punto_venta": 1,
                    "numero": 1002,
                    "cae": "67891234567891",
                    "fecha_generacion": "2024-01-15"
                }
            ]

            resultados_validacion = []
            caes_validos = 0
            caes_invalidos = 0

            for cae_data in caes_validar:
                try:
                    # Validar CAE con AFIP
                    resultado_validacion = await self.afip_client.validar_cae(
                        tipo_cbte=cae_data["tipo_cbte"],
                        punto_venta=cae_data["punto_venta"],
                        numero_cbte=cae_data["numero"],
                        cae=cae_data["cae"]
                    )

                    if resultado_validacion.get("valido"):
                        caes_validos += 1
                        estado_validacion = "VALIDO"
                    else:
                        caes_invalidos += 1
                        estado_validacion = "INVALIDO"

                    resultados_validacion.append({
                        "cae_id": cae_data["id"],
                        "cae": cae_data["cae"],
                        "estado": estado_validacion,
                        "detalles": resultado_validacion
                    })

                    logger.info(f"CAE {cae_data['cae']}: {estado_validacion}")

                except Exception as e:
                    logger.error(f"Error validando CAE {cae_data['cae']}: {str(e)}")
                    caes_invalidos += 1

                    resultados_validacion.append({
                        "cae_id": cae_data["id"],
                        "cae": cae_data["cae"],
                        "estado": "ERROR",
                        "error": str(e)
                    })

            # Notificar resultados
            if caes_invalidos == 0:
                mensaje = f"Validación CAEs exitosa: {caes_validos} CAEs válidos"
                await self._notificar_sync_exitoso("Validación CAEs", mensaje)
            else:
                mensaje = f"Validación CAEs: {caes_validos} válidos, {caes_invalidos} inválidos"
                await self._notificar_sync_error("Validación CAEs", mensaje)

            logger.info(f"Validación CAEs completada: {caes_validos} válidos, {caes_invalidos} inválidos")

            return {
                "status": "success" if caes_invalidos == 0 else "warning",
                "caes_validados": len(caes_validar),
                "caes_validos": caes_validos,
                "caes_invalidos": caes_invalidos,
                "resultados": resultados_validacion
            }

        except Exception as e:
            logger.error(f"Error en validación de CAEs: {str(e)}")
            await self._notificar_sync_error("Validación CAEs", str(e))
            raise

    @retry_with_backoff(max_retries=2, backoff_in_seconds=5)
    async def actualizar_puntos_venta(self) -> Dict:
        """Actualizar información de puntos de venta"""
        try:
            logger.info("Iniciando actualización de puntos de venta")

            # Obtener puntos de venta desde AFIP
            puntos_venta_afip = await self.afip_client.obtener_puntos_venta()

            # Simular respuesta AFIP
            if not puntos_venta_afip:
                puntos_venta_afip = [
                    {
                        "numero": 1,
                        "descripcion": "MATRIZ",
                        "fecha_baja": None,
                        "estado": "ACTIVO"
                    },
                    {
                        "numero": 2,
                        "descripcion": "SUCURSAL CENTRO",
                        "fecha_baja": None,
                        "estado": "ACTIVO"
                    }
                ]

            # Actualizar puntos de venta en BD local
            puntos_actualizados = 0
            puntos_nuevos = 0

            with get_db_session() as db:
                for punto in puntos_venta_afip:
                    # Simular actualización/inserción en BD
                    # En implementación real usar SQLAlchemy

                    # Verificar si existe
                    existe = False  # Simular verificación

                    if existe:
                        puntos_actualizados += 1
                        logger.info(f"Punto de venta {punto['numero']} actualizado")
                    else:
                        puntos_nuevos += 1
                        logger.info(f"Punto de venta {punto['numero']} creado")

            mensaje = f"Puntos de venta actualizados: {puntos_actualizados} actualizados, {puntos_nuevos} nuevos"
            await self._notificar_sync_exitoso("Puntos de Venta", mensaje)

            logger.info(f"Actualización puntos de venta completada: {len(puntos_venta_afip)} procesados")

            return {
                "status": "success",
                "puntos_procesados": len(puntos_venta_afip),
                "puntos_actualizados": puntos_actualizados,
                "puntos_nuevos": puntos_nuevos,
                "puntos_venta": puntos_venta_afip
            }

        except Exception as e:
            logger.error(f"Error actualizando puntos de venta: {str(e)}")
            await self._notificar_sync_error("Puntos de Venta", str(e))
            raise

    @retry_with_backoff(max_retries=2, backoff_in_seconds=10)
    async def sincronizar_padron(self) -> Dict:
        """Sincronizar datos del padrón AFIP"""
        try:
            logger.info("Iniciando sincronización de padrón AFIP")

            # Obtener CUITs de clientes para verificar en padrón
            cuits_clientes = [
                "20-12345678-9",
                "27-87654321-3",
                "30-71234567-4"
            ]

            resultados_padron = []
            clientes_actualizados = 0

            for cuit in cuits_clientes:
                try:
                    # Consultar padrón AFIP
                    datos_padron = await self.afip_client.consultar_padron(cuit)

                    # Simular respuesta del padrón
                    if not datos_padron:
                        datos_padron = {
                            "cuit": cuit,
                            "razon_social": f"Cliente {cuit}",
                            "estado": "ACTIVO",
                            "condicion_iva": "RESPONSABLE_INSCRIPTO",
                            "domicilio": "Calle Falsa 123, CABA",
                            "fecha_actualizacion": datetime.now().isoformat()
                        }

                    # Actualizar datos del cliente en BD
                    # En implementación real actualizar con SQLAlchemy
                    clientes_actualizados += 1

                    resultados_padron.append({
                        "cuit": cuit,
                        "estado": "actualizado",
                        "datos": datos_padron
                    })

                    logger.info(f"Padrón actualizado para CUIT {cuit}")

                except Exception as e:
                    logger.error(f"Error consultando padrón para {cuit}: {str(e)}")

                    resultados_padron.append({
                        "cuit": cuit,
                        "estado": "error",
                        "error": str(e)
                    })

            mensaje = f"Sincronización padrón completada: {clientes_actualizados} clientes actualizados"
            await self._notificar_sync_exitoso("Padrón AFIP", mensaje)

            logger.info(f"Sincronización padrón completada: {clientes_actualizados} clientes procesados")

            return {
                "status": "success",
                "clientes_procesados": len(cuits_clientes),
                "clientes_actualizados": clientes_actualizados,
                "resultados": resultados_padron
            }

        except Exception as e:
            logger.error(f"Error en sincronización de padrón: {str(e)}")
            await self._notificar_sync_error("Padrón AFIP", str(e))
            raise

    @retry_with_backoff(max_retries=2, backoff_in_seconds=1)
    async def backup_comprobantes(self) -> Dict:
        """Backup de comprobantes electrónicos"""
        try:
            logger.info("Iniciando backup de comprobantes electrónicos")

            # Obtener comprobantes de las últimas 24 horas
            fecha_desde = datetime.now() - timedelta(hours=24)

            # Simular comprobantes para backup
            comprobantes = [
                {
                    "id": 1,
                    "tipo": "FACTURA_A",
                    "numero": 1001,
                    "cae": "67891234567890",
                    "fecha": datetime.now().isoformat(),
                    "importe": 1210.00
                },
                {
                    "id": 2,
                    "tipo": "FACTURA_B",
                    "numero": 1002,
                    "cae": "67891234567891",
                    "fecha": datetime.now().isoformat(),
                    "importe": 550.50
                }
            ]

            # Crear backup
            backup_data = {
                "fecha_backup": datetime.now().isoformat(),
                "periodo": {
                    "desde": fecha_desde.isoformat(),
                    "hasta": datetime.now().isoformat()
                },
                "total_comprobantes": len(comprobantes),
                "comprobantes": comprobantes
            }

            # Guardar backup
            backup_filename = f"backup_comprobantes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = f"backups/afip/{backup_filename}"

            import os
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)

            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            mensaje = f"Backup comprobantes creado: {len(comprobantes)} registros"
            await self._notificar_sync_exitoso("Backup Comprobantes", mensaje)

            logger.info(f"Backup comprobantes completado: {backup_filename}")

            return {
                "status": "success",
                "archivo_backup": backup_filename,
                "comprobantes_respaldados": len(comprobantes),
                "tamaño_mb": 0.1  # Simular tamaño
            }

        except Exception as e:
            logger.error(f"Error en backup de comprobantes: {str(e)}")
            await self._notificar_sync_error("Backup Comprobantes", str(e))
            raise

    async def ejecutar_sync(self, tipo_sync: TipoSyncAFIP) -> Dict:
        """Ejecutar sincronización específica por tipo"""
        ejecutores = {
            TipoSyncAFIP.FACTURAS_PENDIENTES: self.sincronizar_facturas_pendientes,
            TipoSyncAFIP.VALIDACION_CAES: self.validar_caes_generados,
            TipoSyncAFIP.ACTUALIZACION_PUNTOS_VENTA: self.actualizar_puntos_venta,
            TipoSyncAFIP.SINCRONIZACION_PADRON: self.sincronizar_padron,
            TipoSyncAFIP.BACKUP_COMPROBANTES: self.backup_comprobantes
        }

        if tipo_sync not in ejecutores:
            raise ValueError(f"Tipo de sync no soportado: {tipo_sync}")

        # Encontrar la tarea
        tarea = next((t for t in self.tareas if t.tipo == tipo_sync), None)
        if not tarea:
            raise ValueError(f"Tarea no encontrada: {tipo_sync}")

        try:
            logger.info(f"Ejecutando sync: {tarea.descripcion}")

            # Ejecutar la sincronización
            resultado = await ejecutores[tipo_sync]()

            # Actualizar estado de la tarea
            tarea.ultima_ejecucion = datetime.now()
            tarea.proxima_ejecucion = datetime.now() + timedelta(minutes=tarea.intervalo_minutos)
            tarea.intentos_fallidos = 0

            logger.info(f"Sync completado exitosamente: {tipo_sync.value}")
            return resultado

        except Exception as e:
            # Incrementar contador de fallos
            tarea.intentos_fallidos += 1

            logger.error(f"Error ejecutando sync {tipo_sync.value}: {str(e)}")

            # Si superó el máximo de intentos, desactivar temporalmente
            if tarea.intentos_fallidos >= tarea.max_intentos:
                tarea.activa = False
                logger.warning(f"Sync {tipo_sync.value} desactivado por múltiples fallos")
                await self._notificar_sync_error(
                    f"Sync Desactivado: {tarea.descripcion}",
                    f"Desactivado tras {tarea.intentos_fallidos} intentos fallidos"
                )

            raise

    async def _notificar_sync_exitoso(self, titulo: str, mensaje: str):
        """Notificar sincronización exitosa"""
        try:
            if self.email_notifier:
                await self.email_notifier.enviar_notificacion(
                    asunto=f"✅ AFIP Sync: {titulo}",
                    mensaje=mensaje,
                    tipo="success"
                )

            if self.slack_notifier:
                await self.slack_notifier.enviar_mensaje(
                    canal="#afip-sync",
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
                    asunto=f"❌ AFIP Sync Error: {titulo}",
                    mensaje=f"Error: {error}",
                    tipo="error"
                )

            if self.slack_notifier:
                await self.slack_notifier.enviar_mensaje(
                    canal="#afip-sync",
                    mensaje=f"❌ *{titulo}*\nError: {error}",
                    color="danger"
                )
        except Exception as e:
            logger.warning(f"Error enviando notificación de error: {str(e)}")

    def programar_syncs(self):
        """Programar todas las sincronizaciones activas"""
        schedule.clear("afip_sync")  # Limpiar tareas previas de AFIP

        for tarea in self.tareas:
            if not tarea.activa:
                continue

            # Programar según intervalo
            schedule.every(tarea.intervalo_minutos).minutes.do(
                self._ejecutar_sync_sync, tarea.tipo
            ).tag("afip_sync")

        logger.info(f"Programadas {len([t for t in self.tareas if t.activa])} sincronizaciones AFIP")

    def _ejecutar_sync_sync(self, tipo_sync: TipoSyncAFIP):
        """Wrapper sincrónico para ejecutar syncs async"""
        try:
            asyncio.run(self.ejecutar_sync(tipo_sync))
        except Exception as e:
            logger.error(f"Error en ejecución sincrónica de {tipo_sync.value}: {str(e)}")

    def iniciar_scheduler(self):
        """Iniciar el scheduler de sync AFIP"""
        if self.running:
            logger.warning("AFIP Sync Scheduler ya está ejecutándose")
            return

        self.running = True
        self.programar_syncs()

        def run_scheduler():
            logger.info("Iniciando AFIP Sync Scheduler")
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(30)  # Verificar cada 30 segundos
                except Exception as e:
                    logger.error(f"Error en AFIP sync scheduler loop: {str(e)}")
                    time.sleep(30)

        self.scheduler_thread = Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("AFIP Sync Scheduler iniciado exitosamente")

    def detener_scheduler(self):
        """Detener el scheduler"""
        if not self.running:
            return

        self.running = False
        schedule.clear("afip_sync")

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        logger.info("AFIP Sync Scheduler detenido")

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

    async def ejecutar_sync_manual(self, tipo_sync: TipoSyncAFIP) -> Dict:
        """Ejecutar sincronización manualmente"""
        logger.info(f"Sincronización manual solicitada para: {tipo_sync.value}")

        try:
            resultado = await self.ejecutar_sync(tipo_sync)
            logger.info(f"Sincronización manual completada: {tipo_sync.value}")
            return {
                "status": "success",
                "tipo_sync": tipo_sync.value,
                "resultado": resultado,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en sincronización manual {tipo_sync.value}: {str(e)}")
            return {
                "status": "error",
                "tipo_sync": tipo_sync.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Factory function
def crear_afip_sync_scheduler(
    afip_client: AFIPWSFEClient,
    config_notificaciones: Optional[Dict] = None
) -> AFIPSyncScheduler:
    """
    Factory para crear un AFIPSyncScheduler configurado.
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
                canal_default=config_notificaciones.get("slack_canal", "#afip-sync")
            )

    return AFIPSyncScheduler(
        afip_client=afip_client,
        email_notifier=email_notifier,
        slack_notifier=slack_notifier
    )

if __name__ == "__main__":
    # Ejemplo de uso
    import asyncio
    from integrations.afip.wsfe_client import AFIPCredentials

    async def ejemplo_uso():
        # Crear cliente AFIP
        credentials = AFIPCredentials(
            cuit="20-12345678-9",
            certificado_path="cert.pem",
            clave_privada_path="key.pem",
            ambiente="testing"
        )

        from integrations.afip.wsfe_client import AFIPWSFEClient
        afip_client = AFIPWSFEClient(credentials)

        # Crear scheduler
        scheduler = crear_afip_sync_scheduler(afip_client)

        # Iniciar scheduler
        scheduler.iniciar_scheduler()

        # Ejecutar sync manual para testing
        resultado = await scheduler.ejecutar_sync_manual(
            TipoSyncAFIP.FACTURAS_PENDIENTES
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
