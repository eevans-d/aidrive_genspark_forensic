"""
Feature engineering para predicción de demanda
Incluye ventas históricas, inflación, estacionalidad y feriados argentinos

R4 Mitigation: Inflación externalizada a INFLATION_RATE_MONTHLY env var.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
import holidays
import logging

logger = logging.getLogger(__name__)

class ArgentinaHolidays:
    """Feriados argentinos fijos y variables"""

    FIXED_HOLIDAYS = {
        (1, 1): "Año Nuevo",
        (2, 20): "Día de la Soberanía Nacional", 
        (3, 24): "Día Nacional de la Memoria por la Verdad y la Justicia",
        (4, 2): "Día del Veterano y de los Caídos en la Guerra de Malvinas",
        (5, 1): "Día del Trabajador",
        (5, 25): "Día de la Revolución de Mayo",
        (6, 17): "Paso a la Inmortalidad del General Martín Miguel de Güemes",
        (6, 20): "Paso a la Inmortalidad del General Manuel Belgrano",
        (7, 9): "Día de la Independencia",
        (8, 17): "Paso a la Inmortalidad del General José de San Martín",
        (10, 12): "Día del Respeto a la Diversidad Cultural",
        (11, 20): "Día de la Soberanía Nacional",
        (12, 8): "Inmaculada Concepción de María",
        (12, 25): "Navidad"
    }

    @classmethod
    def is_holiday(cls, date: datetime) -> bool:
        """Verificar si una fecha es feriado"""
        month_day = (date.month, date.day)
        return month_day in cls.FIXED_HOLIDAYS

    @classmethod
    def get_holiday_name(cls, date: datetime) -> str:
        """Obtener nombre del feriado"""
        month_day = (date.month, date.day)
        return cls.FIXED_HOLIDAYS.get(month_day, "")

class SeasonalFactors:
    """Factores estacionales para Argentina"""

    SEASONAL_FACTORS = {
        # Verano (Dic-Feb): Alta demanda
        12: 1.3, 1: 1.2, 2: 1.1,
        # Otoño (Mar-May): Demanda normal
        3: 1.0, 4: 1.0, 5: 1.0,
        # Invierno (Jun-Ago): Baja demanda
        6: 0.8, 7: 0.7, 8: 0.8,
        # Primavera (Sep-Nov): Demanda media-alta
        9: 1.1, 10: 1.2, 11: 1.25
    }

    @classmethod
    def get_factor(cls, month: int) -> float:
        """Obtener factor estacional para un mes"""
        return cls.SEASONAL_FACTORS.get(month, 1.0)

class DemandFeatures:
    """Extractor de features para predicción de demanda (R4 Mitigation)"""

    def __init__(self, db_session: Session, inflacion_mensual: Optional[float] = None):
        """
        Inicializa extractor de features.
        
        Args:
            db_session: Sesión de base de datos
            inflacion_mensual: Tasa mensual de inflación (%). Si None, lee de INFLATION_RATE_MONTHLY env var.
        
        R4 Mitigation: Inflación externalizada a variable de entorno.
        """
        import os
        self.db = db_session
        # Si no se provee inflacion_mensual, leer de env var (como porcentaje, ej: 4.5)
        # Si env var está como decimal (0.045), multiplicar por 100
        if inflacion_mensual is None:
            env_rate = float(os.getenv("INFLATION_RATE_MONTHLY", "0.045"))
            # Detectar si es decimal o porcentaje
            self.inflacion_mensual = env_rate * 100 if env_rate < 1 else env_rate
        else:
            self.inflacion_mensual = inflacion_mensual

    def extract_sales_features(self, producto_id: int, days_back: int = 90) -> Dict[str, float]:
        """Extraer features de ventas históricas"""
        from shared.models import MovimientoStock, Producto

        # Fecha límite para histórico
        fecha_limite = datetime.now() - timedelta(days=days_back)

        # Consultar movimientos de salida (ventas)
        ventas = self.db.query(MovimientoStock).filter(
            MovimientoStock.producto_id == producto_id,
            MovimientoStock.tipo == 'salida',
            MovimientoStock.created_at >= fecha_limite
        ).all()

        if not ventas:
            return self._get_default_sales_features()

        # Agrupar por día
        ventas_diarias = {}
        for venta in ventas:
            fecha = venta.created_at.date()
            if fecha not in ventas_diarias:
                ventas_diarias[fecha] = 0
            ventas_diarias[fecha] += abs(venta.cantidad)

        # Calcular estadísticas
        cantidades = list(ventas_diarias.values())

        return {
            'venta_promedio_diaria': np.mean(cantidades),
            'venta_mediana_diaria': np.median(cantidades),
            'venta_std_diaria': np.std(cantidades),
            'venta_max_diaria': np.max(cantidades),
            'venta_min_diaria': np.min(cantidades),
            'venta_total_periodo': sum(cantidades),
            'dias_con_ventas': len(ventas_diarias),
            'dias_sin_ventas': days_back - len(ventas_diarias),
            'tendencia_7d': self._calculate_trend(ventas_diarias, 7),
            'tendencia_30d': self._calculate_trend(ventas_diarias, 30),
            'velocidad_rotacion': len(cantidades) / days_back if days_back > 0 else 0
        }

    def extract_temporal_features(self, target_date: datetime) -> Dict[str, float]:
        """Extraer features temporales"""
        return {
            'dia_semana': target_date.weekday(),  # 0=Lunes, 6=Domingo
            'dia_mes': target_date.day,
            'semana_año': target_date.isocalendar()[1],
            'mes': target_date.month,
            'trimestre': (target_date.month - 1) // 3 + 1,
            'es_fin_semana': 1.0 if target_date.weekday() >= 5 else 0.0,
            'es_inicio_mes': 1.0 if target_date.day <= 5 else 0.0,
            'es_fin_mes': 1.0 if target_date.day >= 25 else 0.0,
            'es_feriado': 1.0 if ArgentinaHolidays.is_holiday(target_date) else 0.0,
            'factor_estacional': SeasonalFactors.get_factor(target_date.month)
        }

    def extract_economic_features(self, target_date: datetime) -> Dict[str, float]:
        """Extraer features económicas"""
        # Días desde referencia (para calcular inflación acumulada)
        referencia = datetime(2024, 1, 1)
        dias_desde_ref = (target_date - referencia).days

        # Inflación acumulada
        inflacion_acumulada = (1 + self.inflacion_mensual/100) ** (dias_desde_ref / 30.44) - 1

        return {
            'inflacion_mensual': self.inflacion_mensual,
            'inflacion_acumulada': inflacion_acumulada * 100,
            'dias_desde_referencia': dias_desde_ref,
            'factor_inflacionario': 1 + inflacion_acumulada,
            'poder_adquisitivo': 1 / (1 + inflacion_acumulada),  # Inverso de inflación
            'mes_pago_aguinaldo': 1.0 if target_date.month in [6, 12] else 0.0,
            'temporada_alta': 1.0 if target_date.month in [11, 12, 1] else 0.0
        }

    def extract_product_features(self, producto_id: int) -> Dict[str, float]:
        """Extraer features del producto"""
        from shared.models import Producto

        producto = self.db.query(Producto).filter(Producto.id == producto_id).first()

        if not producto:
            return self._get_default_product_features()

        # Calcular métricas del producto
        stock_ratio = producto.stock_actual / max(producto.stock_minimo, 1)
        precio_categoria = self._get_avg_price_by_category(producto.categoria)

        return {
            'precio_compra': producto.precio_compra,
            'precio_venta': producto.precio_venta or producto.precio_compra * 1.5,
            'stock_actual': producto.stock_actual,
            'stock_minimo': producto.stock_minimo,
            'stock_ratio': stock_ratio,
            'es_stock_critico': 1.0 if stock_ratio <= 1.0 else 0.0,
            'margen_bruto': producto.margen_bruto or 0.0,
            'precio_relativo_categoria': (producto.precio_compra / precio_categoria) if precio_categoria > 0 else 1.0,
            'categoria_encoded': self._encode_category(producto.categoria),
            'dias_desde_creacion': (datetime.now() - producto.created_at).days
        }

    def create_feature_vector(self, producto_id: int, target_date: datetime) -> Dict[str, float]:
        """Crear vector completo de features"""
        features = {}

        # Combinar todos los features
        features.update(self.extract_sales_features(producto_id))
        features.update(self.extract_temporal_features(target_date))
        features.update(self.extract_economic_features(target_date))
        features.update(self.extract_product_features(producto_id))

        # Features adicionales calculados
        features['interaction_precio_estacional'] = features['precio_compra'] * features['factor_estacional']
        features['interaction_stock_tendencia'] = features['stock_actual'] * features.get('tendencia_7d', 0)

        return features

    def _calculate_trend(self, ventas_diarias: Dict, days: int) -> float:
        """Calcular tendencia de ventas"""
        if len(ventas_diarias) < 2:
            return 0.0

        # Obtener últimos N días con datos
        fechas_ordenadas = sorted(ventas_diarias.keys())[-days:]
        if len(fechas_ordenadas) < 2:
            return 0.0

        # Regresión lineal simple para tendencia
        x = np.arange(len(fechas_ordenadas))
        y = [ventas_diarias[fecha] for fecha in fechas_ordenadas]

        if np.var(x) == 0:
            return 0.0

        slope = np.cov(x, y)[0, 1] / np.var(x)
        return slope

    def _get_avg_price_by_category(self, categoria: str) -> float:
        """Obtener precio promedio por categoría"""
        from shared.models import Producto

        result = self.db.query(Producto).filter(
            Producto.categoria == categoria,
            Producto.activo == True
        ).all()

        if not result:
            return 1000.0  # Precio default

        precios = [p.precio_compra for p in result if p.precio_compra > 0]
        return np.mean(precios) if precios else 1000.0

    def _encode_category(self, categoria: str) -> float:
        """Encoding simple de categorías"""
        category_mapping = {
            'bebidas': 1.0,
            'lacteos': 2.0, 
            'panaderia': 3.0,
            'almacen': 4.0,
            'limpieza': 5.0,
            'carnes': 6.0,
            'verduras': 7.0,
            'otros': 8.0
        }
        return category_mapping.get(categoria.lower() if categoria else '', 8.0)

    def _get_default_sales_features(self) -> Dict[str, float]:
        """Features default cuando no hay datos de ventas"""
        return {
            'venta_promedio_diaria': 0.0,
            'venta_mediana_diaria': 0.0,
            'venta_std_diaria': 0.0,
            'venta_max_diaria': 0.0,
            'venta_min_diaria': 0.0,
            'venta_total_periodo': 0.0,
            'dias_con_ventas': 0.0,
            'dias_sin_ventas': 90.0,
            'tendencia_7d': 0.0,
            'tendencia_30d': 0.0,
            'velocidad_rotacion': 0.0
        }

    def _get_default_product_features(self) -> Dict[str, float]:
        """Features default cuando no se encuentra producto"""
        return {
            'precio_compra': 0.0,
            'precio_venta': 0.0,
            'stock_actual': 0.0,
            'stock_minimo': 0.0,
            'stock_ratio': 0.0,
            'es_stock_critico': 1.0,
            'margen_bruto': 0.0,
            'precio_relativo_categoria': 1.0,
            'categoria_encoded': 8.0,
            'dias_desde_creacion': 0.0
        }

if __name__ == "__main__":
    # Test de features
    print("🧪 Testing feature extraction...")

    # Test feriados
    test_dates = [
        datetime(2024, 1, 1),   # Año Nuevo
        datetime(2024, 5, 1),   # Día del Trabajador
        datetime(2024, 7, 9),   # Independencia
        datetime(2024, 6, 15)   # Día normal
    ]

    for date in test_dates:
        is_holiday = ArgentinaHolidays.is_holiday(date)
        name = ArgentinaHolidays.get_holiday_name(date)
        print(f"  {date.strftime('%d/%m/%Y')}: {'🎉' if is_holiday else '📅'} {name}")

    # Test factores estacionales
    print("\n📈 Factores estacionales:")
    for month in range(1, 13):
        factor = SeasonalFactors.get_factor(month)
        print(f"  Mes {month:2d}: {factor:.2f}")

    print("✅ Tests de features completados")
