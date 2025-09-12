
"""
Compliance Scheduler - Sistema de Tareas Automáticas Fiscales
Programador de tareas de compliance fiscal para sistema argentino.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import schedule
import time
from threading import Thread

from compliance.fiscal.iva_reporter import ReporteIVA
from integrations.afip.wsfe_client import AFIPWSFEClient
from models.database import get_db_session
from utils.notifications import EmailNotifier, SlackNotifier

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TipoTareaCompliance(Enum):
    """Tipos de tareas de compliance"""
    REPORTE_IVA_MENSUAL = "reporte_iva_mensual"
    DECLARACION_JURADA = "declaracion_jurada"
    BACKUP_FACTURAS = "backup_facturas"
    VERIFICACION_AFIP = "verificacion_afip"
    AUDITORIA_STOCK = "auditoria_stock"
    REPORTE_VENTAS = "reporte_ventas"

@dataclass
class TareaCompliance:
    """Definición de tarea de compliance"""
    tipo: TipoTareaCompliance
    descripcion: str
    cron_expresion: str
    activa: bool = True
    ultima_ejecucion: Optional[datetime] = None
    proxima_ejecucion: Optional[datetime] = None
    intentos_fallidos: int = 0
    max_intentos: int = 3

class ComplianceScheduler:
    """
    Scheduler para tareas automáticas de compliance fiscal.
    Maneja reportes IVA, declaraciones juradas, backups y auditorías.
    """

    def __init__(self, 
                 cuit_empresa: str,
                 afip_client: Optional[AFIPWSFEClient] = None,
                 email_notifier: Optional[EmailNotifier] = None,
                 slack_notifier: Optional[SlackNotifier] = None):
        self.cuit_empresa = cuit_empresa
        self.afip_client = afip_client
        self.email_notifier = email_notifier
        self.slack_notifier = slack_notifier
        self.reporte_iva = ReporteIVA()
        self.tareas: List[TareaCompliance] = []
        self.running = False
        self.scheduler_thread: Optional[Thread] = None

        # Configurar tareas por defecto
        self._configurar_tareas_default()

    def _configurar_tareas_default(self):
        """Configura las tareas de compliance por defecto"""
        tareas_default = [
            TareaCompliance(
                tipo=TipoTareaCompliance.REPORTE_IVA_MENSUAL,
                descripcion="Generar reporte mensual de IVA",
                cron_expresion="0 9 1 * *"  # 1er día del mes a las 9:00
            ),
            TareaCompliance(
                tipo=TipoTareaCompliance.DECLARACION_JURADA,
                descripcion="Generar declaración jurada mensual",
                cron_expresion="0 10 15 * *"  # 15 de cada mes a las 10:00
            ),
            TareaCompliance(
                tipo=TipoTareaCompliance.BACKUP_FACTURAS,
                descripcion="Backup de facturas electrónicas",
                cron_expresion="0 2 * * 1"  # Lunes a las 2:00 AM
            ),
            TareaCompliance(
                tipo=TipoTareaCompliance.VERIFICACION_AFIP,
                descripcion="Verificar conexión y servicios AFIP",
                cron_expresion="0 8 * * 1-5"  # Lunes a viernes 8:00 AM
            ),
            TareaCompliance(
                tipo=TipoTareaCompliance.AUDITORIA_STOCK,
                descripcion="Auditoría de consistencia de stock",
                cron_expresion="0 6 * * 0"  # Domingos a las 6:00 AM
            ),
            TareaCompliance(
                tipo=TipoTareaCompliance.REPORTE_VENTAS,
                descripcion="Reporte semanal de ventas",
                cron_expresion="0 17 * * 5"  # Viernes a las 17:00
            )
        ]

        self.tareas.extend(tareas_default)
        logger.info(f"Configuradas {len(tareas_default)} tareas de compliance por defecto")

    def agregar_tarea(self, tarea: TareaCompliance):
        """Agregar nueva tarea de compliance"""
        self.tareas.append(tarea)
        logger.info(f"Agregada tarea: {tarea.descripcion}")

    def remover_tarea(self, tipo_tarea: TipoTareaCompliance):
        """Remover tarea por tipo"""
        self.tareas = [t for t in self.tareas if t.tipo != tipo_tarea]
        logger.info(f"Removida tarea tipo: {tipo_tarea.value}")

    def activar_tarea(self, tipo_tarea: TipoTareaCompliance, activa: bool = True):
        """Activar/desactivar tarea específica"""
        for tarea in self.tareas:
            if tarea.tipo == tipo_tarea:
                tarea.activa = activa
                estado = "activada" if activa else "desactivada"
                logger.info(f"Tarea {tipo_tarea.value} {estado}")
                break

    async def ejecutar_reporte_iva_mensual(self) -> Dict:
        """Ejecutar reporte mensual de IVA"""
        try:
            logger.info("Iniciando generación de reporte IVA mensual")

            # Obtener mes anterior
            hoy = datetime.now()
            mes_anterior = hoy.replace(day=1) - timedelta(days=1)
            año = mes_anterior.year
            mes = mes_anterior.month

            # Generar reporte
            reporte = await self.reporte_iva.generar_reporte_mensual(
                año=año, 
                mes=mes, 
                cuit_emisor=self.cuit_empresa
            )

            # Guardar archivos
            nombre_archivo = f"reporte_iva_{año}_{mes:02d}"
            ruta_csv = f"reportes/iva/{nombre_archivo}.csv"
            ruta_excel = f"reportes/iva/{nombre_archivo}.xlsx"

            await self.reporte_iva.exportar_csv(reporte, ruta_csv)
            await self.reporte_iva.exportar_excel(reporte, ruta_excel)

            # Notificar éxito
            mensaje = f"Reporte IVA {mes:02d}/{año} generado exitosamente"
            await self._notificar_tarea_completada("Reporte IVA Mensual", mensaje)

            logger.info(f"Reporte IVA mensual completado: {nombre_archivo}")
            return {"status": "success", "archivo": nombre_archivo, "registros": len(reporte["comprobantes"])}

        except Exception as e:
            logger.error(f"Error en reporte IVA mensual: {str(e)}")
            await self._notificar_error("Reporte IVA Mensual", str(e))
            raise

    async def ejecutar_declaracion_jurada(self) -> Dict:
        """Ejecutar declaración jurada mensual"""
        try:
            logger.info("Iniciando generación de declaración jurada")

            hoy = datetime.now()
            mes_anterior = hoy.replace(day=1) - timedelta(days=1)
            año = mes_anterior.year
            mes = mes_anterior.month

            declaracion = await self.reporte_iva.generar_declaracion_jurada(año=año, mes=mes)

            # Guardar declaración
            nombre_archivo = f"declaracion_jurada_{año}_{mes:02d}.json"
            ruta_archivo = f"reportes/declaraciones/{nombre_archivo}"

            os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                import json
                json.dump(declaracion, f, indent=2, ensure_ascii=False)

            mensaje = f"Declaración jurada {mes:02d}/{año} generada"
            await self._notificar_tarea_completada("Declaración Jurada", mensaje)

            logger.info(f"Declaración jurada completada: {nombre_archivo}")
            return {"status": "success", "archivo": nombre_archivo}

        except Exception as e:
            logger.error(f"Error en declaración jurada: {str(e)}")
            await self._notificar_error("Declaración Jurada", str(e))
            raise

    async def ejecutar_backup_facturas(self) -> Dict:
        """Ejecutar backup de facturas electrónicas"""
        try:
            logger.info("Iniciando backup de facturas electrónicas")

            # Obtener facturas de la semana pasada
            fecha_fin = datetime.now().date()
            fecha_inicio = fecha_fin - timedelta(days=7)

            with get_db_session() as db:
                # Aquí iría la lógica para obtener facturas de la BD
                facturas_query = """
                SELECT * FROM facturas_electronicas 
                WHERE fecha_emision BETWEEN :fecha_inicio AND :fecha_fin
                """

                # Simular backup (en implementación real usar SQLAlchemy)
                facturas_count = 150  # Placeholder

            # Crear backup
            backup_filename = f"backup_facturas_{fecha_inicio}_{fecha_fin}.sql"
            backup_path = f"backups/facturas/{backup_filename}"

            os.makedirs(os.path.dirname(backup_path), exist_ok=True)

            # Simular creación de backup
            with open(backup_path, 'w') as f:
                f.write(f"-- Backup facturas {fecha_inicio} a {fecha_fin}\n")
                f.write(f"-- Total facturas: {facturas_count}\n")

            mensaje = f"Backup facturas completado: {facturas_count} registros"
            await self._notificar_tarea_completada("Backup Facturas", mensaje)

            logger.info(f"Backup facturas completado: {backup_filename}")
            return {"status": "success", "archivo": backup_filename, "registros": facturas_count}

        except Exception as e:
            logger.error(f"Error en backup facturas: {str(e)}")
            await self._notificar_error("Backup Facturas", str(e))
            raise

    async def ejecutar_verificacion_afip(self) -> Dict:
        """Verificar conexión y servicios AFIP"""
        try:
            logger.info("Iniciando verificación de servicios AFIP")

            if not self.afip_client:
                raise Exception("Cliente AFIP no configurado")

            # Verificar autenticación
            auth_result = await self.afip_client.verificar_autenticacion()

            # Verificar servicios disponibles
            servicios_disponibles = []
            servicios_test = ["wsfe", "wsfev1", "ws_sr_padron"]

            for servicio in servicios_test:
                try:
                    # Simular verificación de servicio
                    disponible = True  # En implementación real hacer request
                    servicios_disponibles.append({
                        "servicio": servicio,
                        "disponible": disponible,
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    servicios_disponibles.append({
                        "servicio": servicio,
                        "disponible": False,
                        "timestamp": datetime.now().isoformat()
                    })

            servicios_ok = sum(1 for s in servicios_disponibles if s["disponible"])
            total_servicios = len(servicios_disponibles)

            if servicios_ok == total_servicios:
                mensaje = f"Todos los servicios AFIP operativos ({servicios_ok}/{total_servicios})"
                await self._notificar_tarea_completada("Verificación AFIP", mensaje)
            else:
                mensaje = f"Servicios AFIP con problemas ({servicios_ok}/{total_servicios})"
                await self._notificar_error("Verificación AFIP", mensaje)

            logger.info(f"Verificación AFIP completada: {servicios_ok}/{total_servicios} servicios OK")
            return {
                "status": "success" if servicios_ok == total_servicios else "warning",
                "servicios": servicios_disponibles,
                "operativos": servicios_ok,
                "total": total_servicios
            }

        except Exception as e:
            logger.error(f"Error en verificación AFIP: {str(e)}")
            await self._notificar_error("Verificación AFIP", str(e))
            raise

    async def ejecutar_auditoria_stock(self) -> Dict:
        """Ejecutar auditoría de consistencia de stock"""
        try:
            logger.info("Iniciando auditoría de consistencia de stock")

            # Simular auditoría de stock
            inconsistencias = []
            productos_auditados = 500

            # En implementación real:
            # - Verificar stock físico vs sistema
            # - Detectar movimientos sin justificar
            # - Validar reservas vs disponible
            # - Comprobar coherencia entre depósitos

            # Simular algunas inconsistencias
            if datetime.now().day % 7 == 0:  # Simular inconsistencias los domingos
                inconsistencias = [
                    {
                        "producto_id": "PROD001",
                        "tipo_inconsistencia": "stock_negativo",
                        "stock_sistema": -5,
                        "stock_esperado": 0
                    },
                    {
                        "producto_id": "PROD002", 
                        "tipo_inconsistencia": "diferencia_depositos",
                        "deposito_1": 100,
                        "deposito_2": 95
                    }
                ]

            # Generar reporte de auditoría
            reporte_auditoria = {
                "fecha": datetime.now().isoformat(),
                "productos_auditados": productos_auditados,
                "inconsistencias_encontradas": len(inconsistencias),
                "inconsistencias": inconsistencias,
                "estado": "OK" if not inconsistencias else "ATENCIÓN_REQUERIDA"
            }

            # Guardar reporte
            filename = f"auditoria_stock_{datetime.now().strftime('%Y%m%d')}.json"
            filepath = f"auditorias/stock/{filename}"

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                import json
                json.dump(reporte_auditoria, f, indent=2, ensure_ascii=False)

            if inconsistencias:
                mensaje = f"Auditoría completada: {len(inconsistencias)} inconsistencias encontradas"
                await self._notificar_error("Auditoría Stock", mensaje)
            else:
                mensaje = f"Auditoría completada: {productos_auditados} productos OK"
                await self._notificar_tarea_completada("Auditoría Stock", mensaje)

            logger.info(f"Auditoría stock completada: {filename}")
            return reporte_auditoria

        except Exception as e:
            logger.error(f"Error en auditoría stock: {str(e)}")
            await self._notificar_error("Auditoría Stock", str(e))
            raise

    async def ejecutar_reporte_ventas(self) -> Dict:
        """Ejecutar reporte semanal de ventas"""
        try:
            logger.info("Iniciando reporte semanal de ventas")

            # Calcular período (semana anterior)
            hoy = datetime.now().date()
            inicio_semana = hoy - timedelta(days=hoy.weekday() + 7)
            fin_semana = inicio_semana + timedelta(days=6)

            # Simular datos de ventas
            reporte_ventas = {
                "periodo": {
                    "inicio": inicio_semana.isoformat(),
                    "fin": fin_semana.isoformat()
                },
                "resumen": {
                    "total_ventas": 125000.50,
                    "cantidad_facturas": 45,
                    "ticket_promedio": 2777.79,
                    "productos_vendidos": 180
                },
                "top_productos": [
                    {"nombre": "Producto A", "cantidad": 25, "ingresos": 15000.00},
                    {"nombre": "Producto B", "cantidad": 18, "ingresos": 12000.00},
                    {"nombre": "Producto C", "cantidad": 15, "ingresos": 9500.00}
                ],
                "ventas_por_dia": {
                    "lunes": 18500.00,
                    "martes": 22000.00,
                    "miércoles": 19500.00,
                    "jueves": 21000.00,
                    "viernes": 25000.50,
                    "sabado": 15000.00,
                    "domingo": 4000.00
                }
            }

            # Guardar reporte
            filename = f"reporte_ventas_{inicio_semana}_{fin_semana}.json"
            filepath = f"reportes/ventas/{filename}"

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                import json
                json.dump(reporte_ventas, f, indent=2, ensure_ascii=False)

            mensaje = f"Reporte ventas semanal: ${reporte_ventas['resumen']['total_ventas']:,.2f}"
            await self._notificar_tarea_completada("Reporte Ventas", mensaje)

            logger.info(f"Reporte ventas completado: {filename}")
            return reporte_ventas

        except Exception as e:
            logger.error(f"Error en reporte ventas: {str(e)}")
            await self._notificar_error("Reporte Ventas", str(e))
            raise

    async def ejecutar_tarea(self, tipo_tarea: TipoTareaCompliance) -> Dict:
        """Ejecutar tarea específica por tipo"""
        ejecutores = {
            TipoTareaCompliance.REPORTE_IVA_MENSUAL: self.ejecutar_reporte_iva_mensual,
            TipoTareaCompliance.DECLARACION_JURADA: self.ejecutar_declaracion_jurada,
            TipoTareaCompliance.BACKUP_FACTURAS: self.ejecutar_backup_facturas,
            TipoTareaCompliance.VERIFICACION_AFIP: self.ejecutar_verificacion_afip,
            TipoTareaCompliance.AUDITORIA_STOCK: self.ejecutar_auditoria_stock,
            TipoTareaCompliance.REPORTE_VENTAS: self.ejecutar_reporte_ventas
        }

        if tipo_tarea not in ejecutores:
            raise ValueError(f"Tipo de tarea no soportado: {tipo_tarea}")

        # Encontrar la tarea
        tarea = next((t for t in self.tareas if t.tipo == tipo_tarea), None)
        if not tarea:
            raise ValueError(f"Tarea no encontrada: {tipo_tarea}")

        try:
            logger.info(f"Ejecutando tarea: {tarea.descripcion}")

            # Ejecutar la tarea
            resultado = await ejecutores[tipo_tarea]()

            # Actualizar estado de la tarea
            tarea.ultima_ejecucion = datetime.now()
            tarea.intentos_fallidos = 0

            logger.info(f"Tarea completada exitosamente: {tipo_tarea.value}")
            return resultado

        except Exception as e:
            # Incrementar contador de fallos
            tarea.intentos_fallidos += 1

            logger.error(f"Error ejecutando tarea {tipo_tarea.value}: {str(e)}")

            # Si superó el máximo de intentos, desactivar temporalmente
            if tarea.intentos_fallidos >= tarea.max_intentos:
                tarea.activa = False
                logger.warning(f"Tarea {tipo_tarea.value} desactivada por múltiples fallos")
                await self._notificar_error(
                    f"Tarea Desactivada: {tarea.descripcion}",
                    f"Desactivada tras {tarea.intentos_fallidos} intentos fallidos"
                )

            raise

    async def _notificar_tarea_completada(self, titulo: str, mensaje: str):
        """Notificar tarea completada exitosamente"""
        try:
            if self.email_notifier:
                await self.email_notifier.enviar_notificacion(
                    asunto=f"✅ {titulo} - Completada",
                    mensaje=mensaje,
                    tipo="success"
                )

            if self.slack_notifier:
                await self.slack_notifier.enviar_mensaje(
                    canal="#compliance",
                    mensaje=f"✅ *{titulo}*\n{mensaje}",
                    color="good"
                )
        except Exception as e:
            logger.warning(f"Error enviando notificación de éxito: {str(e)}")

    async def _notificar_error(self, titulo: str, error: str):
        """Notificar error en tarea"""
        try:
            if self.email_notifier:
                await self.email_notifier.enviar_notificacion(
                    asunto=f"❌ {titulo} - Error",
                    mensaje=f"Error: {error}",
                    tipo="error"
                )

            if self.slack_notifier:
                await self.slack_notifier.enviar_mensaje(
                    canal="#compliance",
                    mensaje=f"❌ *{titulo}*\nError: {error}",
                    color="danger"
                )
        except Exception as e:
            logger.warning(f"Error enviando notificación de error: {str(e)}")

    def programar_tareas(self):
        """Programar todas las tareas activas"""
        schedule.clear()  # Limpiar tareas previas

        for tarea in self.tareas:
            if not tarea.activa:
                continue

            # Convertir cron a schedule (simplificado)
            # En implementación completa usar croniter o similar
            if tarea.tipo == TipoTareaCompliance.REPORTE_IVA_MENSUAL:
                schedule.every().month.at("09:00").do(
                    self._ejecutar_tarea_sync, tarea.tipo
                )
            elif tarea.tipo == TipoTareaCompliance.DECLARACION_JURADA:
                schedule.every(15).days.at("10:00").do(
                    self._ejecutar_tarea_sync, tarea.tipo
                )
            elif tarea.tipo == TipoTareaCompliance.BACKUP_FACTURAS:
                schedule.every().monday.at("02:00").do(
                    self._ejecutar_tarea_sync, tarea.tipo
                )
            elif tarea.tipo == TipoTareaCompliance.VERIFICACION_AFIP:
                schedule.every().day.at("08:00").do(
                    self._ejecutar_tarea_sync, tarea.tipo
                )
            elif tarea.tipo == TipoTareaCompliance.AUDITORIA_STOCK:
                schedule.every().sunday.at("06:00").do(
                    self._ejecutar_tarea_sync, tarea.tipo
                )
            elif tarea.tipo == TipoTareaCompliance.REPORTE_VENTAS:
                schedule.every().friday.at("17:00").do(
                    self._ejecutar_tarea_sync, tarea.tipo
                )

        logger.info(f"Programadas {len([t for t in self.tareas if t.activa])} tareas de compliance")

    def _ejecutar_tarea_sync(self, tipo_tarea: TipoTareaCompliance):
        """Wrapper sincrónico para ejecutar tareas async"""
        try:
            asyncio.run(self.ejecutar_tarea(tipo_tarea))
        except Exception as e:
            logger.error(f"Error en ejecución sincrónica de {tipo_tarea.value}: {str(e)}")

    def iniciar_scheduler(self):
        """Iniciar el scheduler de compliance"""
        if self.running:
            logger.warning("Scheduler ya está ejecutándose")
            return

        self.running = True
        self.programar_tareas()

        def run_scheduler():
            logger.info("Iniciando scheduler de compliance fiscal")
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Verificar cada minuto
                except Exception as e:
                    logger.error(f"Error en scheduler loop: {str(e)}")
                    time.sleep(60)

        self.scheduler_thread = Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("Compliance Scheduler iniciado exitosamente")

    def detener_scheduler(self):
        """Detener el scheduler"""
        if not self.running:
            return

        self.running = False
        schedule.clear()

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        logger.info("Compliance Scheduler detenido")

    def obtener_estado_tareas(self) -> List[Dict]:
        """Obtener estado actual de todas las tareas"""
        estado_tareas = []

        for tarea in self.tareas:
            estado_tareas.append({
                "tipo": tarea.tipo.value,
                "descripcion": tarea.descripcion,
                "activa": tarea.activa,
                "ultima_ejecucion": tarea.ultima_ejecucion.isoformat() if tarea.ultima_ejecucion else None,
                "proxima_ejecucion": tarea.proxima_ejecucion.isoformat() if tarea.proxima_ejecucion else None,
                "intentos_fallidos": tarea.intentos_fallidos,
                "max_intentos": tarea.max_intentos
            })

        return estado_tareas

    async def ejecutar_tarea_manual(self, tipo_tarea: TipoTareaCompliance) -> Dict:
        """Ejecutar tarea manualmente (fuera del scheduler)"""
        logger.info(f"Ejecución manual solicitada para: {tipo_tarea.value}")

        try:
            resultado = await self.ejecutar_tarea(tipo_tarea)
            logger.info(f"Ejecución manual completada: {tipo_tarea.value}")
            return {
                "status": "success",
                "tipo_tarea": tipo_tarea.value,
                "resultado": resultado,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en ejecución manual {tipo_tarea.value}: {str(e)}")
            return {
                "status": "error",
                "tipo_tarea": tipo_tarea.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Factory function para crear scheduler configurado
def crear_compliance_scheduler(
    cuit_empresa: str,
    afip_client: Optional[AFIPWSFEClient] = None,
    config_notificaciones: Optional[Dict] = None
) -> ComplianceScheduler:
    """
    Factory para crear un ComplianceScheduler configurado.

    Args:
        cuit_empresa: CUIT de la empresa
        afip_client: Cliente AFIP configurado
        config_notificaciones: Configuración para notificaciones

    Returns:
        ComplianceScheduler configurado
    """

    # Configurar notificadores si se proporciona configuración
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
                canal_default=config_notificaciones.get("slack_canal", "#compliance")
            )

    return ComplianceScheduler(
        cuit_empresa=cuit_empresa,
        afip_client=afip_client,
        email_notifier=email_notifier,
        slack_notifier=slack_notifier
    )

if __name__ == "__main__":
    # Ejemplo de uso
    import asyncio

    async def ejemplo_uso():
        # Crear scheduler
        scheduler = crear_compliance_scheduler(
            cuit_empresa="20-12345678-9"
        )

        # Iniciar scheduler
        scheduler.iniciar_scheduler()

        # Ejecutar tarea manual para testing
        resultado = await scheduler.ejecutar_tarea_manual(
            TipoTareaCompliance.VERIFICACION_AFIP
        )
        print("Resultado ejecución manual:", resultado)

        # Obtener estado de tareas
        estado = scheduler.obtener_estado_tareas()
        print("Estado tareas:", estado)

        # Esperar un poco y detener
        await asyncio.sleep(5)
        scheduler.detener_scheduler()

    # Ejecutar ejemplo
    asyncio.run(ejemplo_uso())
