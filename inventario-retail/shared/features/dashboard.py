"""
Dashboard con métricas en tiempo real
"""
from fastapi import APIRouter
from shared.database import db_manager, health_check_db
from shared.models import Producto, MovimientoStock
from shared.config import get_settings
import time
from datetime import datetime, timedelta

settings = get_settings()
router = APIRouter()

@router.get("/dashboard/metrics")
async def get_metrics():
    """Obtener métricas dashboard"""
    try:
        # Estadísticas BD
        stats = db_manager.get_statistics()

        # Métricas adicionales
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "sistema": {
                "uptime_hours": (time.time() - getattr(get_metrics, 'start_time', time.time())) / 3600,
                "version": "1.0.0",
                "temporada": settings.TEMPORADA,
                "inflacion_mensual": settings.INFLACION_MENSUAL
            },
            "productos": {
                "total": stats.get("productos_total", 0),
                "stock_critico": stats.get("productos_stock_critico", 0),
            },
            "movimientos": {
                "total": stats.get("movimientos_total", 0),
                "hoy": stats.get("movimientos_hoy", 0)
            },
            "database": stats
        }

        return metrics
    except Exception as e:
        return {"error": str(e)}

# Inicializar tiempo de inicio
get_metrics.start_time = time.time()
