"""
Sincronizador de stock entre sistema local y MercadoLibre
Maneja actualizaciones bidireccionales con detección de conflictos
"""
import asyncio
import aiohttp
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncDirection(Enum):
    LOCAL_TO_ML = "local_to_ml"
    ML_TO_LOCAL = "ml_to_local"
    BIDIRECTIONAL = "bidirectional"

class ConflictResolution(Enum):
    LOCAL_WINS = "local_wins"
    ML_WINS = "ml_wins" 
    LATEST_TIMESTAMP = "latest_timestamp"
    MANUAL_REVIEW = "manual_review"

@dataclass
class StockRecord:
    """Registro de stock unificado"""
    sku: str
    available_quantity: int
    reserved_quantity: int = 0
    total_quantity: int = 0
    last_updated: datetime = None
    source: str = ""  # 'local' o 'mercadolibre'
    ml_item_id: str = ""
    price: float = 0.0

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
        if self.total_quantity == 0:
            self.total_quantity = self.available_quantity + self.reserved_quantity

@dataclass
class SyncConflict:
    """Conflicto de sincronización detectado"""
    sku: str
    local_record: StockRecord
    ml_record: StockRecord
    conflict_type: str
    detected_at: datetime
    resolution_status: str = "pending"

class MLStockSynchronizer:
    """Sincronizador de stock con MercadoLibre"""

    def __init__(
        self,
        ml_client,  # Instancia de MercadoLibreClient
        local_db_client,  # Cliente de base de datos local
        sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        conflict_resolution: ConflictResolution = ConflictResolution.LATEST_TIMESTAMP,
        batch_size: int = 50,
        sync_interval_minutes: int = 30
    ):
        self.ml_client = ml_client
        self.local_db = local_db_client
        self.sync_direction = sync_direction
        self.conflict_resolution = conflict_resolution
        self.batch_size = batch_size
        self.sync_interval = sync_interval_minutes

        # Control de estado
        self.is_syncing = False
        self.last_sync = None
        self.sync_stats = {
            'total_synced': 0,
            'conflicts_detected': 0,
            'errors': 0,
            'last_run': None
        }

        # Cache de mapeo SKU -> ML Item ID
        self.sku_mapping_cache = {}
        self.conflicts_queue = []

    async def start_continuous_sync(self):
        """Inicia sincronización continua en background"""
        logger.info(f"Iniciando sincronización continua cada {self.sync_interval} minutos")

        while True:
            try:
                await self.sync_stock()
                await asyncio.sleep(self.sync_interval * 60)
            except Exception as e:
                logger.error(f"Error en sincronización continua: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto antes de reintentar

    async def sync_stock(self) -> Dict[str, Any]:
        """Ejecuta sincronización completa de stock con timeout protection"""
        if self.is_syncing:
            logger.warning("Sincronización ya en progreso, saltando")
            return {"status": "skipped", "reason": "sync_in_progress"}

        self.is_syncing = True
        start_time = datetime.now()

        try:
            logger.info("Iniciando sincronización de stock")

            # Timeout protection para toda la sincronización
            sync_timeout = int(os.getenv('STOCK_SYNC_TIMEOUT_SECONDS', '300'))  # 5 minutes default
            
            result = await asyncio.wait_for(
                self._sync_stock_internal(),
                timeout=sync_timeout
            )
            
            logger.info(f"Sincronización completada en {datetime.now() - start_time}")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Stock sync timeout after {sync_timeout} seconds", exc_info=True, extra={
                "sync_timeout": sync_timeout,
                "sync_direction": self.sync_direction.value,
                "batch_size": self.batch_size,
                "context": "stock_sync_timeout"
            })
            return {
                "status": "timeout",
                "error": f"Sync timeout after {sync_timeout} seconds",
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
        except Exception as e:
            logger.error(f"Error en sincronización: {e}", exc_info=True, extra={
                "sync_direction": self.sync_direction.value,
                "batch_size": self.batch_size,
                "context": "stock_sync_error"
            })
            return {
                "status": "error",
                "error": str(e),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
        finally:
            self.is_syncing = False
    
    async def _sync_stock_internal(self) -> Dict[str, Any]:
        """Internal sync implementation"""
        start_time = datetime.now()
        
        # 1. Cargar registros locales y de ML
        local_records = await self._load_local_stock()
        ml_records = await self._load_ml_stock()

        # 2. Detectar conflictos
        conflicts = await self._detect_conflicts(local_records, ml_records)

        # 3. Resolver conflictos
        resolved_records = await self._resolve_conflicts(conflicts, local_records, ml_records)

        # 4. Ejecutar sincronización según dirección
        sync_results = await self._execute_sync(resolved_records)

        # 5. Actualizar estadísticas
        self._update_sync_stats(sync_results, conflicts, start_time)

        return {
            "status": "success",
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "records_processed": len(resolved_records),
            "conflicts_detected": len(conflicts),
            "sync_results": sync_results
        }

    async def _load_local_stock(self) -> Dict[str, StockRecord]:
        """Carga registros de stock del sistema local"""
        try:
            # Mock implementation - reemplazar con query real
            query = """
            SELECT sku, available_quantity, reserved_quantity, 
                   last_updated, price, ml_item_id
            FROM inventory 
            WHERE active = 1
            """

            # Simular datos locales
            local_data = [
                {
                    'sku': 'PROD001',
                    'available_quantity': 50,
                    'reserved_quantity': 5,
                    'last_updated': datetime.now() - timedelta(hours=1),
                    'price': 1500.0,
                    'ml_item_id': 'MLA123456789'
                },
                {
                    'sku': 'PROD002', 
                    'available_quantity': 25,
                    'reserved_quantity': 0,
                    'last_updated': datetime.now() - timedelta(hours=2),
                    'price': 2500.0,
                    'ml_item_id': 'MLA987654321'
                }
            ]

            records = {}
            for item in local_data:
                record = StockRecord(
                    sku=item['sku'],
                    available_quantity=item['available_quantity'],
                    reserved_quantity=item['reserved_quantity'],
                    last_updated=item['last_updated'],
                    price=item['price'],
                    ml_item_id=item['ml_item_id'],
                    source='local'
                )
                records[item['sku']] = record

            logger.info(f"Cargados {len(records)} registros del stock local")
            return records

        except Exception as e:
            logger.error(f"Error cargando stock local: {e}", exc_info=True, extra={
                "context": "load_local_stock_error"
            })
            return {}

    async def _load_ml_stock(self) -> Dict[str, StockRecord]:
        """Carga registros de stock de MercadoLibre"""
        try:
            # Obtener items del usuario
            items_response = await self.ml_client.get_my_items()

            if not items_response.get('success'):
                logger.error("Error obteniendo items de ML")
                return {}

            records = {}

            # Procesar items en lotes
            items = items_response.get('items', [])
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]

                for item in batch:
                    try:
                        # Obtener detalles completos del item
                        item_details = await self.ml_client.get_item_details(item['id'])

                        if item_details.get('success') and item_details.get('item'):
                            item_data = item_details['item']

                            # Extraer información de stock
                            sku = item_data.get('seller_custom_field') or item['id']
                            available_qty = item_data.get('available_quantity', 0)

                            record = StockRecord(
                                sku=sku,
                                available_quantity=available_qty,
                                reserved_quantity=0,  # ML no expone reservados
                                last_updated=self._parse_ml_timestamp(item_data.get('last_updated')),
                                price=item_data.get('price', 0.0),
                                ml_item_id=item['id'],
                                source='mercadolibre'
                            )

                            records[sku] = record

                    except Exception as e:
                        logger.error(f"Error procesando item {item.get('id')}: {e}")
                        continue

                # Respetar rate limits
                await asyncio.sleep(0.1)

            logger.info(f"Cargados {len(records)} registros de MercadoLibre")
            return records

        except Exception as e:
            logger.error(f"Error cargando stock de ML: {e}")
            return {}

    async def _detect_conflicts(
        self, 
        local_records: Dict[str, StockRecord],
        ml_records: Dict[str, StockRecord]
    ) -> List[SyncConflict]:
        """Detecta conflictos entre registros locales y ML"""
        conflicts = []

        # Verificar SKUs que existen en ambos sistemas
        common_skus = set(local_records.keys()) & set(ml_records.keys())

        for sku in common_skus:
            local_record = local_records[sku]
            ml_record = ml_records[sku]

            # Detectar diferentes tipos de conflictos
            conflict_types = []

            # Conflicto de cantidad
            if local_record.available_quantity != ml_record.available_quantity:
                conflict_types.append("quantity_mismatch")

            # Conflicto de precio
            if abs(local_record.price - ml_record.price) > 0.01:
                conflict_types.append("price_mismatch")

            # Conflicto de timestamp (modificación simultánea)
            time_diff = abs((local_record.last_updated - ml_record.last_updated).total_seconds())
            if time_diff < 300:  # Menos de 5 minutos de diferencia
                conflict_types.append("concurrent_modification")

            if conflict_types:
                conflict = SyncConflict(
                    sku=sku,
                    local_record=local_record,
                    ml_record=ml_record,
                    conflict_type=", ".join(conflict_types),
                    detected_at=datetime.now()
                )
                conflicts.append(conflict)

        logger.info(f"Detectados {len(conflicts)} conflictos")
        return conflicts

    async def _resolve_conflicts(
        self,
        conflicts: List[SyncConflict],
        local_records: Dict[str, StockRecord],
        ml_records: Dict[str, StockRecord]
    ) -> Dict[str, StockRecord]:
        """Resuelve conflictos según la estrategia configurada"""
        resolved_records = {}

        # Copiar registros sin conflictos
        all_skus = set(local_records.keys()) | set(ml_records.keys())
        conflict_skus = {c.sku for c in conflicts}

        for sku in all_skus - conflict_skus:
            if sku in local_records:
                resolved_records[sku] = local_records[sku]
            else:
                resolved_records[sku] = ml_records[sku]

        # Resolver conflictos
        for conflict in conflicts:
            resolved_record = await self._resolve_single_conflict(conflict)
            resolved_records[conflict.sku] = resolved_record

            # Agregar a cola para revisión manual si es necesario
            if self.conflict_resolution == ConflictResolution.MANUAL_REVIEW:
                self.conflicts_queue.append(conflict)

        return resolved_records

    async def _resolve_single_conflict(self, conflict: SyncConflict) -> StockRecord:
        """Resuelve un conflicto individual"""
        if self.conflict_resolution == ConflictResolution.LOCAL_WINS:
            return conflict.local_record

        elif self.conflict_resolution == ConflictResolution.ML_WINS:
            return conflict.ml_record

        elif self.conflict_resolution == ConflictResolution.LATEST_TIMESTAMP:
            if conflict.local_record.last_updated > conflict.ml_record.last_updated:
                return conflict.local_record
            else:
                return conflict.ml_record

        else:  # MANUAL_REVIEW
            # Por defecto usar el más reciente mientras se resuelve manualmente
            if conflict.local_record.last_updated > conflict.ml_record.last_updated:
                return conflict.local_record
            else:
                return conflict.ml_record

    async def _execute_sync(self, resolved_records: Dict[str, StockRecord]) -> Dict[str, Any]:
        """Ejecuta la sincronización según la dirección configurada"""
        results = {
            'local_updates': 0,
            'ml_updates': 0,
            'errors': 0,
            'error_details': []
        }

        if self.sync_direction in [SyncDirection.LOCAL_TO_ML, SyncDirection.BIDIRECTIONAL]:
            # Actualizar MercadoLibre con datos locales/resueltos
            ml_results = await self._sync_to_ml(resolved_records)
            results['ml_updates'] = ml_results['updates']
            results['errors'] += ml_results['errors']
            results['error_details'].extend(ml_results['error_details'])

        if self.sync_direction in [SyncDirection.ML_TO_LOCAL, SyncDirection.BIDIRECTIONAL]:
            # Actualizar sistema local con datos de ML/resueltos
            local_results = await self._sync_to_local(resolved_records)
            results['local_updates'] = local_results['updates']
            results['errors'] += local_results['errors']
            results['error_details'].extend(local_results['error_details'])

        return results

    async def _sync_to_ml(self, records: Dict[str, StockRecord]) -> Dict[str, Any]:
        """Sincroniza registros hacia MercadoLibre"""
        results = {'updates': 0, 'errors': 0, 'error_details': []}

        # Filtrar registros que necesitan actualización en ML
        ml_updates = []
        for sku, record in records.items():
            if record.ml_item_id and (record.source == 'local' or record.source == ''):
                ml_updates.append(record)

        # Procesar en lotes
        for i in range(0, len(ml_updates), self.batch_size):
            batch = ml_updates[i:i + self.batch_size]

            for record in batch:
                try:
                    # Actualizar stock en ML
                    update_data = {
                        'available_quantity': record.available_quantity,
                        'price': record.price
                    }

                    response = await self.ml_client.update_item(record.ml_item_id, update_data)

                    if response.get('success'):
                        results['updates'] += 1
                        logger.debug(f"Actualizado ML item {record.ml_item_id} (SKU: {record.sku})")
                    else:
                        results['errors'] += 1
                        error_msg = f"Error actualizando {record.sku}: {response.get('error')}"
                        results['error_details'].append(error_msg)
                        logger.error(error_msg)

                except Exception as e:
                    results['errors'] += 1
                    error_msg = f"Excepción actualizando {record.sku}: {str(e)}"
                    results['error_details'].append(error_msg)
                    logger.error(error_msg)

            # Rate limiting
            await asyncio.sleep(0.2)

        return results

    async def _sync_to_local(self, records: Dict[str, StockRecord]) -> Dict[str, Any]:
        """Sincroniza registros hacia el sistema local"""
        results = {'updates': 0, 'errors': 0, 'error_details': []}

        # Filtrar registros que necesitan actualización local
        local_updates = []
        for sku, record in records.items():
            if record.source == 'mercadolibre':
                local_updates.append(record)

        for record in local_updates:
            try:
                # Mock update - reemplazar con query real
                update_query = """
                UPDATE inventory 
                SET available_quantity = ?, price = ?, last_updated = ?
                WHERE sku = ?
                """

                # Simular actualización exitosa
                results['updates'] += 1
                logger.debug(f"Actualizado registro local SKU: {record.sku}")

            except Exception as e:
                results['errors'] += 1
                error_msg = f"Error actualizando registro local {record.sku}: {str(e)}"
                results['error_details'].append(error_msg)
                logger.error(error_msg)

        return results

    def _parse_ml_timestamp(self, timestamp_str: str) -> datetime:
        """Parsea timestamp de MercadoLibre"""
        try:
            if timestamp_str:
                # ML usa formato ISO 8601
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                return datetime.now()
        except:
            return datetime.now()

    def _update_sync_stats(self, sync_results: Dict, conflicts: List, start_time: datetime):
        """Actualiza estadísticas de sincronización"""
        self.sync_stats.update({
            'total_synced': sync_results.get('ml_updates', 0) + sync_results.get('local_updates', 0),
            'conflicts_detected': len(conflicts),
            'errors': sync_results.get('errors', 0),
            'last_run': start_time,
            'last_duration': (datetime.now() - start_time).total_seconds()
        })
        self.last_sync = datetime.now()

    def get_sync_status(self) -> Dict[str, Any]:
        """Obtiene estado actual de sincronización"""
        return {
            'is_syncing': self.is_syncing,
            'last_sync': self.last_sync,
            'sync_direction': self.sync_direction.value,
            'conflict_resolution': self.conflict_resolution.value,
            'stats': self.sync_stats,
            'pending_conflicts': len(self.conflicts_queue)
        }

    def get_pending_conflicts(self) -> List[Dict[str, Any]]:
        """Obtiene conflictos pendientes de revisión manual"""
        return [
            {
                'sku': c.sku,
                'conflict_type': c.conflict_type,
                'detected_at': c.detected_at.isoformat(),
                'local_qty': c.local_record.available_quantity,
                'ml_qty': c.ml_record.available_quantity,
                'local_price': c.local_record.price,
                'ml_price': c.ml_record.price
            }
            for c in self.conflicts_queue
            if c.resolution_status == 'pending'
        ]

    async def resolve_manual_conflict(self, sku: str, resolution: str) -> bool:
        """Resuelve conflicto manual específico"""
        try:
            # Buscar conflicto en cola
            conflict = next((c for c in self.conflicts_queue if c.sku == sku), None)

            if not conflict:
                return False

            # Aplicar resolución
            if resolution == 'use_local':
                await self._sync_to_ml({sku: conflict.local_record})
            elif resolution == 'use_ml':
                await self._sync_to_local({sku: conflict.ml_record})

            # Marcar como resuelto
            conflict.resolution_status = 'resolved'

            return True

        except Exception as e:
            logger.error(f"Error resolviendo conflicto manual {sku}: {e}")
            return False


# Utilidades adicionales
class StockSyncUtils:
    """Utilidades para sincronización de stock"""

    @staticmethod
    def calculate_sync_hash(record: StockRecord) -> str:
        """Calcula hash para detectar cambios"""
        sync_data = f"{record.sku}:{record.available_quantity}:{record.price}"
        return hashlib.md5(sync_data.encode()).hexdigest()

    @staticmethod
    def format_sync_report(sync_results: Dict[str, Any]) -> str:
        """Formatea reporte de sincronización"""
        report_lines = [
            "=== REPORTE DE SINCRONIZACIÓN ===",
            f"Estado: {sync_results.get('status', 'unknown')}",
            f"Duración: {sync_results.get('duration_seconds', 0):.2f} segundos",
            f"Registros procesados: {sync_results.get('records_processed', 0)}",
            f"Conflictos detectados: {sync_results.get('conflicts_detected', 0)}",
            ""
        ]

        if 'sync_results' in sync_results:
            sr = sync_results['sync_results']
            report_lines.extend([
                "Actualizaciones:",
                f"  - MercadoLibre: {sr.get('ml_updates', 0)}",
                f"  - Sistema local: {sr.get('local_updates', 0)}",
                f"  - Errores: {sr.get('errors', 0)}",
                ""
            ])

            if sr.get('error_details'):
                report_lines.append("Errores detallados:")
                for error in sr['error_details'][:5]:  # Mostrar max 5 errores
                    report_lines.append(f"  - {error}")

        return "\n".join(report_lines)


# Ejemplo de uso
if __name__ == "__main__":
    # Configuración de ejemplo
    async def ejemplo_sincronizacion():
        # Mock clients
        class MockMLClient:
            async def get_my_items(self):
                return {'success': True, 'items': []}

            async def update_item(self, item_id, data):
                return {'success': True}

        class MockDBClient:
            pass

        # Crear sincronizador
        synchronizer = MLStockSynchronizer(
            ml_client=MockMLClient(),
            local_db_client=MockDBClient(),
            sync_direction=SyncDirection.BIDIRECTIONAL,
            conflict_resolution=ConflictResolution.LATEST_TIMESTAMP
        )

        # Ejecutar sincronización
        resultado = await synchronizer.sync_stock()
        print(StockSyncUtils.format_sync_report(resultado))

    # Ejecutar ejemplo
    # asyncio.run(ejemplo_sincronizacion())
