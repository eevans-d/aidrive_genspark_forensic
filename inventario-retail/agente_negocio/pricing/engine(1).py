"""
AgenteNegocio - Pricing Engine
Motor de precios con inflación 4.5% mensual y estacionalidad argentina
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import json
import math
from pathlib import Path

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductCategory(Enum):
    """Categorías de productos con comportamientos de precio específicos"""
    ALIMENTOS = "alimentos"
    BEBIDAS = "bebidas"
    LIMPIEZA = "limpieza"
    HIGIENE = "higiene"
    ELECTRODOMESTICOS = "electrodomesticos"
    ROPA = "ropa"
    MEDICAMENTOS = "medicamentos"
    COMBUSTIBLES = "combustibles"
    CONSTRUCCION = "construccion"
    OTROS = "otros"

class SeasonalityType(Enum):
    """Tipos de estacionalidad"""
    ALTA_DEMANDA = "alta_demanda"
    BAJA_DEMANDA = "baja_demanda"
    NAVIDAD = "navidad"
    VACACIONES_INVIERNO = "vacaciones_invierno"
    VACACIONES_VERANO = "vacaciones_verano"
    BACK_TO_SCHOOL = "back_to_school"
    NORMAL = "normal"

@dataclass
class PriceConfig:
    """Configuración del motor de precios"""
    # Inflación base
    monthly_inflation_rate: Decimal = Decimal("0.045")  # 4.5% mensual
    annual_inflation_rate: Decimal = Decimal("0.68")    # ~68% anual

    # Factores de ajuste
    supplier_markup: Decimal = Decimal("0.25")          # 25% markup proveedor
    retail_markup: Decimal = Decimal("0.35")            # 35% markup retail
    transport_factor: Decimal = Decimal("0.08")         # 8% factor transporte

    # Límites de variación
    max_daily_variation: Decimal = Decimal("0.15")      # 15% máximo diario
    min_profit_margin: Decimal = Decimal("0.12")        # 12% margen mínimo

    # Ajustes regionales
    caba_factor: Decimal = Decimal("1.15")              # CABA +15%
    gba_factor: Decimal = Decimal("1.08")               # GBA +8%
    interior_factor: Decimal = Decimal("0.95")          # Interior -5%

@dataclass
class SeasonalityFactor:
    """Factor de estacionalidad para productos"""
    category: ProductCategory
    month: int
    seasonality_type: SeasonalityType
    factor: Decimal
    description: str

@dataclass
class PriceCalculation:
    """Resultado del cálculo de precio"""
    product_id: str
    base_price: Decimal
    inflation_adjusted_price: Decimal
    seasonal_adjusted_price: Decimal
    final_price: Decimal

    # Factores aplicados
    inflation_factor: Decimal
    seasonal_factor: Decimal
    regional_factor: Decimal
    markup_factor: Decimal

    # Metadata
    calculation_date: datetime
    reference_date: datetime
    category: ProductCategory
    region: str
    confidence_score: float

    # Desglose de costos
    cost_breakdown: Dict[str, Decimal] = field(default_factory=dict)

class PricingEngine:
    """
    Motor de precios inteligente para Argentina
    Maneja inflación, estacionalidad y factores regionales
    """

    def __init__(self, config: Optional[PriceConfig] = None):
        """
        Inicializa el motor de precios

        Args:
            config: Configuración personalizada del motor
        """
        self.config = config or PriceConfig()
        self.seasonality_factors = self._initialize_seasonality_factors()
        self.category_adjustments = self._initialize_category_adjustments()

        logger.info(f"PricingEngine inicializado - Inflación mensual: {self.config.monthly_inflation_rate:.1%}")

    def _initialize_seasonality_factors(self) -> List[SeasonalityFactor]:
        """Inicializa factores de estacionalidad por categoría y mes"""
        factors = []

        # Factores por categoría y mes (Argentina)
        seasonality_data = {
            # Alimentos - picos en fiestas y vacaciones
            ProductCategory.ALIMENTOS: {
                1: (SeasonalityType.VACACIONES_VERANO, Decimal("1.15"), "Vacaciones verano - mayor consumo"),
                2: (SeasonalityType.VACACIONES_VERANO, Decimal("1.12"), "Fin vacaciones - normalización"),
                3: (SeasonalityType.BACK_TO_SCHOOL, Decimal("1.08"), "Vuelta al cole - incremento moderado"),
                4: (SeasonalityType.NORMAL, Decimal("1.00"), "Otoño - demanda normal"),
                5: (SeasonalityType.NORMAL, Decimal("0.98"), "Pre-invierno - leve baja"),
                6: (SeasonalityType.BAJA_DEMANDA, Decimal("0.95"), "Invierno - menor consumo fresco"),
                7: (SeasonalityType.VACACIONES_INVIERNO, Decimal("1.05"), "Vacaciones invierno"),
                8: (SeasonalityType.NORMAL, Decimal("1.02"), "Fin invierno - recuperación"),
                9: (SeasonalityType.NORMAL, Decimal("1.00"), "Primavera - demanda estable"),
                10: (SeasonalityType.ALTA_DEMANDA, Decimal("1.10"), "Pre-fiestas - aumento demanda"),
                11: (SeasonalityType.ALTA_DEMANDA, Decimal("1.18"), "Fiestas - pico de demanda"),
                12: (SeasonalityType.NAVIDAD, Decimal("1.25"), "Navidad/Año Nuevo - máximo consumo")
            },

            # Bebidas - similar a alimentos pero más marcado en verano
            ProductCategory.BEBIDAS: {
                1: (SeasonalityType.VACACIONES_VERANO, Decimal("1.30"), "Verano - máximo consumo bebidas"),
                2: (SeasonalityType.VACACIONES_VERANO, Decimal("1.25"), "Verano - alta demanda continúa"),
                3: (SeasonalityType.NORMAL, Decimal("1.10"), "Otoño - normalización gradual"),
                4: (SeasonalityType.NORMAL, Decimal("1.00"), "Otoño - demanda normal"),
                5: (SeasonalityType.BAJA_DEMANDA, Decimal("0.90"), "Pre-invierno - baja demanda"),
                6: (SeasonalityType.BAJA_DEMANDA, Decimal("0.85"), "Invierno - mínimo consumo frías"),
                7: (SeasonalityType.BAJA_DEMANDA, Decimal("0.88"), "Invierno - leve recuperación"),
                8: (SeasonalityType.NORMAL, Decimal("0.95"), "Fin invierno - preparación primavera"),
                9: (SeasonalityType.NORMAL, Decimal("1.05"), "Primavera - incremento demanda"),
                10: (SeasonalityType.ALTA_DEMANDA, Decimal("1.15"), "Pre-verano - aumento"),
                11: (SeasonalityType.ALTA_DEMANDA, Decimal("1.20"), "Fiestas + pre-verano"),
                12: (SeasonalityType.NAVIDAD, Decimal("1.35"), "Navidad + verano")
            },

            # Ropa - estacional marcada
            ProductCategory.ROPA: {
                1: (SeasonalityType.BAJA_DEMANDA, Decimal("0.80"), "Post-fiestas - liquidación verano"),
                2: (SeasonalityType.BAJA_DEMANDA, Decimal("0.75"), "Fin verano - rebajas"),
                3: (SeasonalityType.BACK_TO_SCHOOL, Decimal("1.20"), "Vuelta al cole - ropa otoño"),
                4: (SeasonalityType.ALTA_DEMANDA, Decimal("1.15"), "Otoño - cambio de temporada"),
                5: (SeasonalityType.ALTA_DEMANDA, Decimal("1.25"), "Pre-invierno - ropa abrigada"),
                6: (SeasonalityType.NORMAL, Decimal("1.10"), "Invierno - demanda sostenida"),
                7: (SeasonalityType.NORMAL, Decimal("1.05"), "Invierno - estabilización"),
                8: (SeasonalityType.BAJA_DEMANDA, Decimal("0.85"), "Fin invierno - liquidación"),
                9: (SeasonalityType.ALTA_DEMANDA, Decimal("1.20"), "Primavera - nueva temporada"),
                10: (SeasonalityType.ALTA_DEMANDA, Decimal("1.25"), "Pre-verano - ropa liviana"),
                11: (SeasonalityType.ALTA_DEMANDA, Decimal("1.30"), "Verano + fiestas"),
                12: (SeasonalityType.NAVIDAD, Decimal("1.40"), "Navidad - pico de ventas")
            },

            # Electrodomésticos - picos fiestas y promociones
            ProductCategory.ELECTRODOMESTICOS: {
                1: (SeasonalityType.BAJA_DEMANDA, Decimal("0.90"), "Post-fiestas - baja demanda"),
                2: (SeasonalityType.BAJA_DEMANDA, Decimal("0.88"), "Febrero - mes más bajo"),
                3: (SeasonalityType.BACK_TO_SCHOOL, Decimal("1.05"), "Vuelta al cole - equipamiento"),
                4: (SeasonalityType.NORMAL, Decimal("1.00"), "Otoño - demanda normal"),
                5: (SeasonalityType.ALTA_DEMANDA, Decimal("1.15"), "Día de la Madre - promociones"),
                6: (SeasonalityType.ALTA_DEMANDA, Decimal("1.12"), "Día del Padre + invierno"),
                7: (SeasonalityType.NORMAL, Decimal("1.00"), "Invierno - estabilidad"),
                8: (SeasonalityType.NORMAL, Decimal("1.02"), "Fin invierno - preparación"),
                9: (SeasonalityType.NORMAL, Decimal("1.05"), "Primavera - renovación"),
                10: (SeasonalityType.ALTA_DEMANDA, Decimal("1.10"), "Pre-fiestas - anticipación"),
                11: (SeasonalityType.ALTA_DEMANDA, Decimal("1.25"), "Black Friday - Hot Sale"),
                12: (SeasonalityType.NAVIDAD, Decimal("1.35"), "Navidad - máximo del año")
            }
        }

        # Generar factores para todas las categorías
        for category, monthly_data in seasonality_data.items():
            for month, (seasonality_type, factor, description) in monthly_data.items():
                factors.append(SeasonalityFactor(
                    category=category,
                    month=month,
                    seasonality_type=seasonality_type,
                    factor=factor,
                    description=description
                ))

        # Para categorías sin datos específicos, usar factores neutros
        remaining_categories = set(ProductCategory) - set(seasonality_data.keys())
        for category in remaining_categories:
            for month in range(1, 13):
                if month in [11, 12]:  # Fiestas
                    factor = Decimal("1.10")
                    seasonality_type = SeasonalityType.NAVIDAD
                elif month in [1, 2]:  # Post-fiestas
                    factor = Decimal("0.95")
                    seasonality_type = SeasonalityType.BAJA_DEMANDA
                else:
                    factor = Decimal("1.00")
                    seasonality_type = SeasonalityType.NORMAL

                factors.append(SeasonalityFactor(
                    category=category,
                    month=month,
                    seasonality_type=seasonality_type,
                    factor=factor,
                    description=f"{category.value} - factor genérico"
                ))

        logger.info(f"Factores de estacionalidad inicializados: {len(factors)} factores")
        return factors

    def _initialize_category_adjustments(self) -> Dict[ProductCategory, Dict[str, Decimal]]:
        """Inicializa ajustes específicos por categoría"""
        return {
            ProductCategory.ALIMENTOS: {
                "volatility": Decimal("0.12"),      # 12% volatilidad extra
                "perishable_factor": Decimal("1.08"), # 8% factor perecederos
                "transport_sensitivity": Decimal("1.15") # 15% más sensible a transporte
            },
            ProductCategory.COMBUSTIBLES: {
                "volatility": Decimal("0.25"),      # 25% volatilidad alta
                "international_factor": Decimal("1.30"), # 30% factor internacional
                "transport_sensitivity": Decimal("0.95")  # Menos sensible (es el transporte)
            },
            ProductCategory.MEDICAMENTOS: {
                "volatility": Decimal("0.05"),      # 5% baja volatilidad
                "regulation_factor": Decimal("0.90"), # 10% descuento regulación
                "transport_sensitivity": Decimal("1.05") # Leve sensibilidad
            },
            ProductCategory.ELECTRODOMESTICOS: {
                "volatility": Decimal("0.18"),      # 18% volatilidad media-alta
                "import_factor": Decimal("1.25"),   # 25% factor importación
                "transport_sensitivity": Decimal("1.10") # Moderada sensibilidad
            }
        }

    def calculate_price(self, 
                       product_id: str,
                       base_price: Decimal,
                       category: ProductCategory,
                       reference_date: Optional[datetime] = None,
                       target_date: Optional[datetime] = None,
                       region: str = "CABA") -> PriceCalculation:
        """
        Calcula el precio ajustado para un producto

        Args:
            product_id: ID del producto
            base_price: Precio base de referencia
            category: Categoría del producto
            reference_date: Fecha de referencia del precio base
            target_date: Fecha objetivo para el cálculo
            region: Región donde se aplicará el precio

        Returns:
            PriceCalculation: Cálculo completo del precio
        """
        if reference_date is None:
            reference_date = datetime.now() - timedelta(days=30)  # Default: hace 1 mes

        if target_date is None:
            target_date = datetime.now()

        logger.info(f"Calculando precio para {product_id} - {category.value} en {region}")

        # Paso 1: Ajuste por inflación
        inflation_factor = self._calculate_inflation_factor(reference_date, target_date)
        inflation_adjusted_price = base_price * inflation_factor

        # Paso 2: Ajuste por estacionalidad
        seasonal_factor = self._get_seasonal_factor(category, target_date.month)
        seasonal_adjusted_price = inflation_adjusted_price * seasonal_factor

        # Paso 3: Ajuste regional
        regional_factor = self._get_regional_factor(region)
        regional_adjusted_price = seasonal_adjusted_price * regional_factor

        # Paso 4: Aplicar markup y factores de categoría
        markup_factor = self._calculate_markup_factor(category)
        final_price = regional_adjusted_price * markup_factor

        # Paso 5: Aplicar límites y validaciones
        final_price = self._apply_price_limits(base_price, final_price, category)

        # Paso 6: Calcular confianza del cálculo
        confidence_score = self._calculate_confidence_score(
            reference_date, target_date, category, seasonal_factor
        )

        # Crear desglose de costos
        cost_breakdown = {
            "base_price": base_price,
            "inflation_adjustment": inflation_adjusted_price - base_price,
            "seasonal_adjustment": seasonal_adjusted_price - inflation_adjusted_price,
            "regional_adjustment": regional_adjusted_price - seasonal_adjusted_price,
            "markup_and_factors": final_price - regional_adjusted_price
        }

        # Crear resultado
        calculation = PriceCalculation(
            product_id=product_id,
            base_price=base_price,
            inflation_adjusted_price=inflation_adjusted_price,
            seasonal_adjusted_price=seasonal_adjusted_price,
            final_price=final_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            inflation_factor=inflation_factor,
            seasonal_factor=seasonal_factor,
            regional_factor=regional_factor,
            markup_factor=markup_factor,
            calculation_date=datetime.now(),
            reference_date=reference_date,
            category=category,
            region=region,
            confidence_score=confidence_score,
            cost_breakdown=cost_breakdown
        )

        logger.info(f"Precio calculado: ${base_price} -> ${calculation.final_price} "
                   f"(inf: {inflation_factor:.3f}, est: {seasonal_factor:.3f}, "
                   f"reg: {regional_factor:.3f})")

        return calculation

    def _calculate_inflation_factor(self, reference_date: datetime, target_date: datetime) -> Decimal:
        """Calcula el factor de inflación entre dos fechas"""
        # Calcular diferencia en meses
        months_diff = (target_date.year - reference_date.year) * 12 + (target_date.month - reference_date.month)

        # Ajuste por días dentro del mes
        days_in_current_month = (target_date - target_date.replace(day=1)).days
        days_in_month = (target_date.replace(month=target_date.month % 12 + 1, day=1) - 
                        target_date.replace(day=1)).days
        partial_month = Decimal(days_in_current_month) / Decimal(days_in_month)

        total_months = Decimal(months_diff) + partial_month

        # Aplicar inflación compuesta
        if total_months > 0:
            inflation_factor = (Decimal("1") + self.config.monthly_inflation_rate) ** total_months
        else:
            # Si es fecha pasada, aplicar deflación
            inflation_factor = (Decimal("1") + self.config.monthly_inflation_rate) ** total_months

        return inflation_factor

    def _get_seasonal_factor(self, category: ProductCategory, month: int) -> Decimal:
        """Obtiene el factor de estacionalidad para una categoría y mes"""
        for factor in self.seasonality_factors:
            if factor.category == category and factor.month == month:
                return factor.factor

        # Factor por defecto si no se encuentra
        return Decimal("1.00")

    def _get_regional_factor(self, region: str) -> Decimal:
        """Obtiene el factor de ajuste regional"""
        region_upper = region.upper()

        if "CABA" in region_upper or "CAPITAL" in region_upper:
            return self.config.caba_factor
        elif "GBA" in region_upper or "BUENOS AIRES" in region_upper:
            return self.config.gba_factor
        else:
            return self.config.interior_factor

    def _calculate_markup_factor(self, category: ProductCategory) -> Decimal:
        """Calcula el factor de markup según la categoría"""
        base_markup = self.config.supplier_markup + self.config.retail_markup

        # Ajustes específicos por categoría
        category_adjustments = self.category_adjustments.get(category, {})

        # Factor de volatilidad
        volatility = category_adjustments.get("volatility", Decimal("0.10"))
        volatility_adjustment = Decimal("1.00") + volatility

        # Factor de transporte
        transport_sensitivity = category_adjustments.get("transport_sensitivity", Decimal("1.00"))
        transport_adjustment = self.config.transport_factor * transport_sensitivity

        # Factor total
        total_markup = base_markup + transport_adjustment
        final_factor = (Decimal("1.00") + total_markup) * volatility_adjustment

        return final_factor

    def _apply_price_limits(self, base_price: Decimal, calculated_price: Decimal, 
                          category: ProductCategory) -> Decimal:
        """Aplica límites y validaciones al precio calculado"""

        # Límite de variación máxima diaria
        max_variation = base_price * self.config.max_daily_variation
        max_price = base_price + max_variation
        min_price = base_price - max_variation

        # Para períodos largos, permitir mayor variación
        # (esto se podría mejorar basándose en las fechas)

        # Validar margen mínimo
        min_price_with_margin = base_price * (Decimal("1.00") + self.config.min_profit_margin)

        # Aplicar límites
        final_price = max(min_price_with_margin, min(calculated_price, max_price * Decimal("3.0")))

        if final_price != calculated_price:
            logger.warning(f"Precio ajustado por límites: {calculated_price} -> {final_price}")

        return final_price

    def _calculate_confidence_score(self, reference_date: datetime, target_date: datetime,
                                  category: ProductCategory, seasonal_factor: Decimal) -> float:
        """Calcula la confianza del cálculo de precio"""

        # Base de confianza
        base_confidence = 0.8

        # Penalizar por antigüedad de la fecha de referencia
        days_old = (datetime.now() - reference_date).days
        if days_old > 90:
            age_penalty = 0.3
        elif days_old > 30:
            age_penalty = 0.1
        else:
            age_penalty = 0.0

        # Bonus por estacionalidad conocida
        if seasonal_factor != Decimal("1.00"):
            seasonality_bonus = 0.1
        else:
            seasonality_bonus = 0.0

        # Ajuste por categoría
        category_adjustments = self.category_adjustments.get(category, {})
        volatility = float(category_adjustments.get("volatility", Decimal("0.10")))
        volatility_penalty = volatility / 2  # Mayor volatilidad = menor confianza

        # Calcular confianza final
        confidence = base_confidence - age_penalty + seasonality_bonus - volatility_penalty

        return max(0.1, min(1.0, confidence))  # Entre 0.1 y 1.0

    def batch_calculate_prices(self, products: List[Dict[str, Any]], 
                             target_date: Optional[datetime] = None,
                             region: str = "CABA") -> List[PriceCalculation]:
        """
        Calcula precios para múltiples productos

        Args:
            products: Lista de productos con keys: id, base_price, category, reference_date
            target_date: Fecha objetivo
            region: Región

        Returns:
            List[PriceCalculation]: Lista de cálculos
        """
        results = []

        for product in products:
            try:
                calculation = self.calculate_price(
                    product_id=product["id"],
                    base_price=Decimal(str(product["base_price"])),
                    category=ProductCategory(product["category"]),
                    reference_date=product.get("reference_date"),
                    target_date=target_date,
                    region=region
                )
                results.append(calculation)

            except Exception as e:
                logger.error(f"Error calculando precio para {product.get('id', 'unknown')}: {e}")

        logger.info(f"Cálculo en lote completado: {len(results)}/{len(products)} productos")
        return results

    def get_price_trend(self, product_id: str, base_price: Decimal, 
                       category: ProductCategory, days: int = 30) -> Dict[str, Any]:
        """
        Calcula tendencia de precios para los próximos días

        Args:
            product_id: ID del producto
            base_price: Precio base
            category: Categoría del producto
            days: Número de días a proyectar

        Returns:
            Dict: Tendencia de precios
        """
        reference_date = datetime.now()
        trend_data = []

        for i in range(days + 1):
            target_date = reference_date + timedelta(days=i)
            calculation = self.calculate_price(
                product_id=product_id,
                base_price=base_price,
                category=category,
                reference_date=reference_date,
                target_date=target_date
            )

            trend_data.append({
                "date": target_date.isoformat(),
                "price": float(calculation.final_price),
                "inflation_factor": float(calculation.inflation_factor),
                "seasonal_factor": float(calculation.seasonal_factor)
            })

        # Calcular estadísticas
        prices = [item["price"] for item in trend_data]
        trend_stats = {
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": sum(prices) / len(prices),
            "total_increase": ((prices[-1] - prices[0]) / prices[0]) * 100,
            "daily_avg_increase": (((prices[-1] / prices[0]) ** (1/days)) - 1) * 100
        }

        return {
            "product_id": product_id,
            "base_price": float(base_price),
            "category": category.value,
            "days_projected": days,
            "trend_data": trend_data,
            "statistics": trend_stats
        }

    def export_seasonality_calendar(self, output_path: Union[str, Path]) -> bool:
        """Exporta calendario de estacionalidad a JSON"""
        try:
            calendar_data = {}

            for factor in self.seasonality_factors:
                category_key = factor.category.value
                if category_key not in calendar_data:
                    calendar_data[category_key] = {}

                calendar_data[category_key][factor.month] = {
                    "factor": float(factor.factor),
                    "seasonality_type": factor.seasonality_type.value,
                    "description": factor.description
                }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(calendar_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Calendario de estacionalidad exportado: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exportando calendario: {e}")
            return False

# Funciones de utilidad
def calculate_simple_price(base_price: float, category: str, 
                          months_forward: int = 1, region: str = "CABA") -> float:
    """
    Función simple para cálculo rápido de precios

    Args:
        base_price: Precio base
        category: Categoría del producto
        months_forward: Meses hacia adelante
        region: Región

    Returns:
        float: Precio calculado
    """
    engine = PricingEngine()

    reference_date = datetime.now()
    target_date = reference_date + timedelta(days=30 * months_forward)

    try:
        category_enum = ProductCategory(category.lower())
    except ValueError:
        category_enum = ProductCategory.OTROS

    calculation = engine.calculate_price(
        product_id="temp",
        base_price=Decimal(str(base_price)),
        category=category_enum,
        reference_date=reference_date,
        target_date=target_date,
        region=region
    )

    return float(calculation.final_price)

def get_category_seasonal_factors(category: str) -> Dict[int, float]:
    """
    Obtiene factores estacionales para una categoría

    Args:
        category: Nombre de la categoría

    Returns:
        Dict: Factores por mes (1-12)
    """
    engine = PricingEngine()

    try:
        category_enum = ProductCategory(category.lower())
    except ValueError:
        category_enum = ProductCategory.OTROS

    factors = {}
    for month in range(1, 13):
        factor = engine._get_seasonal_factor(category_enum, month)
        factors[month] = float(factor)

    return factors
