"""
Sistema de Inventario Inteligente - Motor de Reordenamiento Integrado
Consolida ML predictions + inventory optimization + business intelligence
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Instalar dependencias:
# pip install redis pandas numpy flask

@dataclass
class AlertItem:
    """Estructura para elementos de alerta"""
    tipo: str
    producto_codigo: str
    producto_nombre: str
    nivel_criticidad: str  # 'CRITICO', 'ALTO', 'MEDIO', 'BAJO'
    mensaje: str
    accion_recomendada: str
    timestamp: datetime

@dataclass
class DashboardData:
    """Estructura consolidada para el dashboard operativo"""
    fecha_reporte: datetime
    compras_recomendadas: List[Dict]
    alertas_criticas: List[AlertItem]
    kpis_principales: Dict
    predicciones_demanda: Dict
    estado_inventario: Dict
    metricas_financieras: Dict

class MockRedisClient:
    """Cliente Redis simulado para demostración"""
    def __init__(self):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key)

    def setex(self, key, ttl, value):
        self.cache[key] = value
        return True

    def set(self, key, value):
        self.cache[key] = value
        return True

class ReorderEngineIntegrated:
    """
    Motor de reordenamiento integrado que consolida:
    - ML predictions (demand_forecasting.py)
    - Inventory optimization (inventory_optimizer.py) 
    - Business intelligence
    - Real-time alerts
    """

    def __init__(self, redis_client=None):
        # Usar Redis real en producción: redis.Redis(host='localhost', port=6379, db=0)
        self.redis_client = redis_client or MockRedisClient()
        self.logger = logging.getLogger(__name__)

        # Cargar componentes ML existentes
        self.ml_engine = None
        self.demand_forecaster = None
        self.inventory_optimizer = None

        print("✅ ReorderEngineIntegrated inicializado")

    def generar_dashboard_operativo_diario(self, fecha_target: datetime = None) -> DashboardData:
        """
        FUNCIÓN PRINCIPAL: Generar dashboard operativo diario completo

        Esta es la función que usarías cada mañana para obtener:
        - Qué comprar HOY
        - Alertas críticas
        - KPIs principales
        - Predicciones de demanda
        - Estado general del inventario
        """
        if fecha_target is None:
            fecha_target = datetime.now()

        print(f"🚀 Generando dashboard operativo para {fecha_target.strftime('%Y-%m-%d')}")

        # 1. Cargar datos de inventario actual
        inventario_actual = self._cargar_inventario_actual()

        # 2. Generar recomendaciones de compra diarias
        compras_recomendadas = self._generar_compras_diarias(inventario_actual, fecha_target)

        # 3. Detectar alertas críticas
        alertas_criticas = self._detectar_alertas_criticas(inventario_actual, fecha_target)

        # 4. Calcular KPIs principales
        kpis_principales = self._calcular_kpis_principales(inventario_actual, fecha_target)

        # 5. Generar predicciones de demanda clave
        predicciones_demanda = self._generar_predicciones_clave(inventario_actual, fecha_target)

        # 6. Evaluar estado general del inventario
        estado_inventario = self._evaluar_estado_inventario(inventario_actual)

        # 7. Calcular métricas financieras
        metricas_financieras = self._calcular_metricas_financieras(inventario_actual, compras_recomendadas)

        dashboard_data = DashboardData(
            fecha_reporte=fecha_target,
            compras_recomendadas=compras_recomendadas,
            alertas_criticas=alertas_criticas,
            kpis_principales=kpis_principales,
            predicciones_demanda=predicciones_demanda,
            estado_inventario=estado_inventario,
            metricas_financieras=metricas_financieras
        )

        # Cachear resultado en Redis
        self._cachear_dashboard(dashboard_data)

        return dashboard_data

    def _cargar_inventario_actual(self) -> pd.DataFrame:
        """Cargar inventario actual desde Redis o base de datos"""
        cache_key = "inventario_actual"

        try:
            # Intentar cargar desde cache
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return pd.read_json(cached_data)
        except:
            pass

        # En producción, esto vendría de tu base de datos
        # Aquí generamos datos de ejemplo
        productos_ejemplo = []
        categorias = ['Alimentos', 'Bebidas', 'Limpieza', 'Cuidado Personal', 'Tecnología']

        np.random.seed(42)  # Para resultados consistentes
        for i in range(50):
            producto = {
                'codigo': f'PROD_{i:03d}',
                'nombre': f'Producto {i}',
                'categoria': np.random.choice(categorias),
                'stock_actual': np.random.randint(0, 100),
                'stock_minimo': np.random.randint(10, 25),
                'stock_maximo': np.random.randint(50, 150),
                'precio_compra': round(np.random.uniform(50, 500) * 1.045, 2),  # Inflación Argentina
                'precio_venta': round(np.random.uniform(80, 800), 2),
                'demanda_promedio_diaria': round(np.random.uniform(1, 15), 2),
                'lead_time_dias': np.random.randint(1, 7),
                'ultimo_pedido': (datetime.now() - timedelta(days=np.random.randint(1, 30))).strftime('%Y-%m-%d'),
                'proveedor': f'Proveedor_{np.random.randint(1, 10)}'
            }
            productos_ejemplo.append(producto)

        df_inventario = pd.DataFrame(productos_ejemplo)

        # Cachear por 1 hora
        self.redis_client.setex(cache_key, 3600, df_inventario.to_json())

        return df_inventario

    def _generar_compras_diarias(self, inventario_df: pd.DataFrame, fecha_target: datetime) -> List[Dict]:
        """Generar recomendaciones de compra para HOY"""

        recomendaciones = []

        for _, producto in inventario_df.iterrows():
            # Regla: si stock < stock_mínimo, recomendar compra
            if producto['stock_actual'] < producto['stock_minimo']:
                cantidad_sugerida = producto['stock_maximo'] - producto['stock_actual']

                recomendacion = {
                    'codigo': producto['codigo'],
                    'nombre': producto['nombre'],
                    'categoria': producto['categoria'],
                    'stock_actual': producto['stock_actual'],
                    'cantidad_sugerida': cantidad_sugerida,
                    'costo_total': cantidad_sugerida * producto['precio_compra'],
                    'prioridad': 'ALTA' if producto['stock_actual'] == 0 else 'MEDIA',
                    'razon': 'Stock bajo - reposición necesaria',
                    'proveedor': producto['proveedor']
                }
                recomendaciones.append(recomendacion)

        # Ordenar por prioridad y costo
        recomendaciones.sort(key=lambda x: (
            x.get('prioridad') == 'ALTA', 
            -x.get('costo_total', 0)
        ), reverse=True)

        return recomendaciones[:10]  # Top 10 recomendaciones

    # ... resto de métodos internos ...

    def _calcular_metricas_financieras(self, inventario_df: pd.DataFrame, compras_recomendadas: List[Dict]) -> Dict:
        """Calcular métricas financieras del día"""

        # Costo de compras recomendadas
        costo_compras_hoy = sum([r.get('costo_total', 0) for r in compras_recomendadas])

        # Impacto de inflación Argentina (4.5% mensual aprox)
        factor_inflacion_mensual = 1.045
        factor_inflacion_diario = factor_inflacion_mensual ** (1/30)

        valor_inventario_actual = (inventario_df['stock_actual'] * inventario_df['precio_compra']).sum()
        impacto_inflacion_diario = valor_inventario_actual * (factor_inflacion_diario - 1)

        return {
            'costo_compras_recomendadas_hoy': round(costo_compras_hoy, 2),
            'valor_inventario_actual': round(valor_inventario_actual, 2),
            'impacto_inflacion_diario': round(impacto_inflacion_diario, 2),
            'ahorro_potencial_compra_temprana': round(impacto_inflacion_diario * 7, 2),
            'roi_estimado_reposicion': round((costo_compras_hoy * 0.3) / max(costo_compras_hoy, 1), 2)
        }

# EJEMPLO DE USO:
if __name__ == "__main__":
    # Crear instancia del motor
    engine = ReorderEngineIntegrated()

    # Generar dashboard operativo para HOY
    dashboard_hoy = engine.generar_dashboard_operativo_diario()

    print("="*60)
    print("🎯 DASHBOARD OPERATIVO DIARIO")
    print("="*60)
    print(f"📅 Fecha: {dashboard_hoy.fecha_reporte.strftime('%Y-%m-%d')}")
    print(f"🛒 Compras recomendadas: {len(dashboard_hoy.compras_recomendadas)}")
    print(f"⚠️ Alertas críticas: {len(dashboard_hoy.alertas_criticas)}")
    print(f"💰 Inversión recomendada: ${dashboard_hoy.metricas_financieras['costo_compras_recomendadas_hoy']:,.2f}")
    print(f"📈 Disponibilidad: {dashboard_hoy.kpis_principales['porcentaje_disponibilidad']}%")
