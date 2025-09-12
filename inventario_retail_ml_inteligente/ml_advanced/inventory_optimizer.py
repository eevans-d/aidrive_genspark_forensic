"""
Optimizador de Inventario Inteligente con ML
Sistema que dice QUÉ comprar, CUÁNDO comprar y CUÁNTO comprar
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from demand_forecasting import DemandForecaster
from ml_engine_advanced import MLEngineAdvanced
import math

class InventoryOptimizer:
    """Optimizador inteligente de inventario con ML para retail argentino"""

    def __init__(self, ml_engine=None, demand_forecaster=None):
        self.ml_engine = ml_engine or MLEngineAdvanced()
        self.demand_forecaster = demand_forecaster or DemandForecaster(self.ml_engine)

        # Parámetros económicos argentinos
        self.inflation_rate_monthly = 0.045  # 4.5% mensual
        self.cost_of_capital = 0.05  # 5% anual
        self.holding_cost_rate = 0.02  # 2% mensual del valor stock

        # Configuración stock de seguridad por categoría
        self.safety_stock_config = {
            'Bebidas': {
                'factor': 1.5,  # 50% extra por volatilidad alta
                'lead_time_days': 3  # Tiempo reposición bebidas
            },
            'Almacen': {
                'factor': 1.2,  # 20% extra, productos estables
                'lead_time_days': 5  # Tiempo reposición almacén
            },
            'Lacteos': {
                'factor': 1.8,  # 80% extra por perecibilidad
                'lead_time_days': 1  # Reposición diaria lácteos
            },
            'Panaderia': {
                'factor': 2.0,  # 100% extra por alta volatilidad
                'lead_time_days': 1  # Reposición diaria panadería
            }
        }

    def calculate_optimal_order_quantity(self, producto_codigo, categoria, current_stock, 
                                       unit_cost, holding_cost=None, ordering_cost=500):
        """Calcular cantidad óptima de pedido usando EOQ modificado con ML"""

        # Obtener predicción demanda
        demand_forecast = self.demand_forecaster.predict_demand_multi_period(
            producto_codigo, categoria, [30]
        )

        if '30_dias' not in demand_forecast:
            return None

        monthly_demand = demand_forecast['30_dias']['demanda_total_periodo']
        annual_demand = monthly_demand * 12

        # Calcular holding cost si no se provee
        if holding_cost is None:
            holding_cost = unit_cost * self.holding_cost_rate * 12  # Anual

        # EOQ clásico
        if annual_demand > 0 and holding_cost > 0:
            eoq_classic = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        else:
            eoq_classic = monthly_demand  # Fallback

        # Ajuste por inflación argentina
        inflation_adjustment = 1 + (self.inflation_rate_monthly * 2)  # Comprar más por inflación

        # Ajuste por estacionalidad
        seasonality_factor = self._calculate_seasonality_factor(producto_codigo, categoria)

        # Cantidad óptima ajustada
        optimal_quantity = eoq_classic * inflation_adjustment * seasonality_factor

        return {
            'eoq_clasico': round(eoq_classic, 1),
            'cantidad_optima': round(optimal_quantity, 1),
            'demanda_mensual_predicha': monthly_demand,
            'factor_inflacion': round(inflation_adjustment, 2),
            'factor_estacionalidad': round(seasonality_factor, 2),
            'costo_total_estimado': round(optimal_quantity * unit_cost, 2)
        }

    def calculate_reorder_point(self, producto_codigo, categoria, current_stock):
        """Calcular punto de reorden inteligente"""

        # Configuración por categoría
        config = self.safety_stock_config.get(categoria, {
            'factor': 1.3, 'lead_time_days': 3
        })

        lead_time_days = config['lead_time_days']
        safety_factor = config['factor']

        # Predicción demanda durante lead time
        lead_time_forecast = self.demand_forecaster.predict_demand_multi_period(
            producto_codigo, categoria, [lead_time_days]
        )

        if f'{lead_time_days}_dias' not in lead_time_forecast:
            # Fallback: usar stock actual como referencia
            lead_time_demand = current_stock * 0.3
        else:
            lead_time_demand = lead_time_forecast[f'{lead_time_days}_dias']['demanda_total_periodo']

        # Stock de seguridad
        safety_stock = lead_time_demand * (safety_factor - 1)

        # Punto de reorden
        reorder_point = lead_time_demand + safety_stock

        # Análisis situación actual
        days_remaining = self._calculate_days_remaining(current_stock, producto_codigo, categoria)

        status = self._determine_stock_status(current_stock, reorder_point, days_remaining)

        return {
            'punto_reorden': round(reorder_point, 1),
            'stock_seguridad': round(safety_stock, 1),
            'demanda_lead_time': round(lead_time_demand, 1),
            'stock_actual': current_stock,
            'dias_restantes': days_remaining,
            'status': status,
            'accion_requerida': self._get_action_required(status, days_remaining),
            'urgencia': self._get_urgency_level(days_remaining, lead_time_days)
        }

    def _calculate_seasonality_factor(self, producto_codigo, categoria):
        """Calcular factor estacionalidad"""

        try:
            # Obtener predicción próximas 4 semanas
            monthly_forecast = self.demand_forecaster.predict_demand_multi_period(
                producto_codigo, categoria, [30]
            )

            if '30_dias' not in monthly_forecast:
                return 1.0

            # Comparar con promedio histórico
            current_month_avg = monthly_forecast['30_dias']['promedio_diario']

            # Análisis tendencia
            trend_analysis = self.demand_forecaster.detect_demand_trends(producto_codigo, categoria)

            if trend_analysis['direccion'] == 'creciente':
                return 1.2  # Aumentar 20% si tendencia creciente
            elif trend_analysis['direccion'] == 'decreciente':
                return 0.8  # Reducir 20% si tendencia decreciente
            else:
                return 1.0  # Estable

        except Exception as e:
            return 1.0  # Fallback neutral

    def _calculate_days_remaining(self, current_stock, producto_codigo, categoria):
        """Calcular días que dura el stock actual"""

        try:
            # Predicción demanda próximos 15 días
            forecast = self.demand_forecaster.predict_demand_multi_period(
                producto_codigo, categoria, [15]
            )

            if '15_dias' not in forecast:
                return 0

            daily_predictions = forecast['15_dias']['predicciones_diarias']

            # Simular consumo día a día
            remaining_stock = current_stock

            for i, day_pred in enumerate(daily_predictions):
                daily_demand = day_pred['prediccion_final']
                remaining_stock -= daily_demand

                if remaining_stock <= 0:
                    return i + 1  # Días hasta agotarse

            return 15  # Dura más de 15 días

        except Exception as e:
            # Fallback simple
            avg_daily = 2  # Consumo promedio fallback
            return max(0, current_stock / avg_daily) if avg_daily > 0 else 0

    def _determine_stock_status(self, current_stock, reorder_point, days_remaining):
        """Determinar status del stock"""

        if current_stock <= 0:
            return 'AGOTADO'
        elif current_stock < reorder_point * 0.5:
            return 'CRITICO'
        elif current_stock < reorder_point:
            return 'BAJO'
        elif current_stock < reorder_point * 1.5:
            return 'NORMAL'
        elif current_stock > reorder_point * 3:
            return 'SOBRESTOCKEADO'
        else:
            return 'OPTIMO'

    def _get_action_required(self, status, days_remaining):
        """Obtener acción requerida según status"""

        actions = {
            'AGOTADO': 'COMPRAR URGENTE - Stock agotado',
            'CRITICO': f'COMPRAR HOY - Solo {days_remaining} días restantes',
            'BAJO': f'Programar compra - {days_remaining} días restantes',
            'NORMAL': 'Monitorear - Stock adecuado',
            'OPTIMO': 'Sin acción - Stock óptimo',
            'SOBRESTOCKEADO': 'Liquidar exceso - Demasiado stock'
        }

        return actions.get(status, 'Revisar manualmente')

    def _get_urgency_level(self, days_remaining, lead_time_days):
        """Obtener nivel de urgencia"""

        if days_remaining <= 0:
            return 'URGENTE'
        elif days_remaining <= lead_time_days:
            return 'ALTA'
        elif days_remaining <= lead_time_days * 2:
            return 'MEDIA'
        else:
            return 'BAJA'

    def generate_inventory_analysis(self, productos_df):
        """Generar análisis completo de inventario"""

        analysis_results = []

        for _, producto in productos_df.iterrows():
            codigo = producto.get('codigo_producto', '')
            nombre = producto.get('nombre_producto', '')
            categoria = producto.get('categoria', 'General')
            stock_actual = producto.get('stock_actual', 0)
            costo_unitario = producto.get('costo_unitario', 100)

            # Análisis punto de reorden
            reorder_analysis = self.calculate_reorder_point(
                codigo, categoria, stock_actual
            )

            # Análisis cantidad óptima
            eoq_analysis = self.calculate_optimal_order_quantity(
                codigo, categoria, stock_actual, costo_unitario
            )

            # Predicción demanda
            demand_forecast = self.demand_forecaster.predict_demand_multi_period(
                codigo, categoria, [7, 15, 30]
            )

            result = {
                'producto': {
                    'codigo': codigo,
                    'nombre': nombre,
                    'categoria': categoria,
                    'stock_actual': stock_actual,
                    'costo_unitario': costo_unitario
                },
                'analisis_reorden': reorder_analysis,
                'cantidad_optima': eoq_analysis,
                'prediccion_demanda': demand_forecast,
                'fecha_analisis': datetime.now().isoformat()
            }

            analysis_results.append(result)

        return analysis_results

    def generate_daily_purchase_recommendations(self, productos_df, budget_limit=None):
        """Generar recomendaciones diarias de compra - EL CORAZÓN DEL SISTEMA"""

        # Análisis completo inventario
        inventory_analysis = self.generate_inventory_analysis(productos_df)

        # Filtrar productos que necesitan compra
        productos_comprar = []

        for analysis in inventory_analysis:
            reorder = analysis['analisis_reorden']
            eoq = analysis['cantidad_optima']
            producto = analysis['producto']

            # Determinar si necesita compra
            if reorder['status'] in ['AGOTADO', 'CRITICO', 'BAJO']:

                # Calcular cantidad recomendada
                if eoq:
                    cantidad_sugerida = eoq['cantidad_optima']
                else:
                    cantidad_sugerida = reorder['punto_reorden'] * 1.5

                # Ajustar por stock actual
                cantidad_neta = max(0, cantidad_sugerida - producto['stock_actual'])

                if cantidad_neta > 0:
                    costo_total = cantidad_neta * producto['costo_unitario']

                    productos_comprar.append({
                        'codigo_producto': producto['codigo'],
                        'nombre_producto': producto['nombre'],
                        'categoria': producto['categoria'],
                        'stock_actual': producto['stock_actual'],
                        'dias_restantes': reorder['dias_restantes'],
                        'urgencia': reorder['urgencia'],
                        'status': reorder['status'],
                        'cantidad_sugerida': round(cantidad_neta, 1),
                        'costo_unitario': producto['costo_unitario'],
                        'costo_total': round(costo_total, 2),
                        'razon_compra': reorder['accion_requerida'],
                        'prioridad': self._calculate_priority(reorder, eoq)
                    })

        # Ordenar por prioridad
        productos_comprar.sort(key=lambda x: (
            ['URGENTE', 'ALTA', 'MEDIA', 'BAJA'].index(x['urgencia']),
            -x['prioridad']
        ))

        # Aplicar límite presupuesto si existe
        if budget_limit:
            productos_comprar = self._apply_budget_constraint(productos_comprar, budget_limit)

        # Generar resumen de compras
        total_productos = len(productos_comprar)
        total_costo = sum([p['costo_total'] for p in productos_comprar])

        urgentes = len([p for p in productos_comprar if p['urgencia'] == 'URGENTE'])
        criticos = len([p for p in productos_comprar if p['urgencia'] in ['URGENTE', 'ALTA']])

        recomendaciones = {
            'fecha_recomendacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'resumen': {
                'total_productos_comprar': total_productos,
                'costo_total_estimado': round(total_costo, 2),
                'productos_urgentes': urgentes,
                'productos_criticos': criticos,
                'budget_limit': budget_limit,
                'presupuesto_utilizado': round((total_costo / budget_limit * 100), 1) if budget_limit else None
            },
            'lista_compras': productos_comprar,
            'recomendaciones_adicionales': self._generate_additional_recommendations(productos_comprar)
        }

        return recomendaciones

    def _calculate_priority(self, reorder_analysis, eoq_analysis):
        """Calcular prioridad de compra (0-100)"""

        priority = 50  # Base

        # Ajuste por urgencia
        urgency_scores = {'URGENTE': 40, 'ALTA': 30, 'MEDIA': 10, 'BAJA': 0}
        priority += urgency_scores.get(reorder_analysis['urgencia'], 0)

        # Ajuste por días restantes
        days_remaining = reorder_analysis['dias_restantes']
        if days_remaining <= 1:
            priority += 20
        elif days_remaining <= 3:
            priority += 10
        elif days_remaining <= 7:
            priority += 5

        # Ajuste por demanda predicha
        if eoq_analysis and eoq_analysis['demanda_mensual_predicha'] > 0:
            if eoq_analysis['demanda_mensual_predicha'] > 50:  # Producto de alta rotación
                priority += 10

        return min(100, max(0, priority))

    def _apply_budget_constraint(self, productos_comprar, budget_limit):
        """Aplicar restricción presupuestaria"""

        productos_filtrados = []
        budget_usado = 0

        for producto in productos_comprar:
            if budget_usado + producto['costo_total'] <= budget_limit:
                productos_filtrados.append(producto)
                budget_usado += producto['costo_total']
            elif producto['urgencia'] == 'URGENTE':
                # Incluir productos urgentes aunque excedan presupuesto
                producto['excede_presupuesto'] = True
                productos_filtrados.append(producto)

        return productos_filtrados

    def _generate_additional_recommendations(self, productos_comprar):
        """Generar recomendaciones adicionales"""

        recommendations = []

        # Análisis por categoría
        categorias = {}
        for producto in productos_comprar:
            cat = producto['categoria']
            if cat not in categorias:
                categorias[cat] = {'count': 0, 'cost': 0}
            categorias[cat]['count'] += 1
            categorias[cat]['cost'] += producto['costo_total']

        # Recomendaciones por categoría dominante
        if categorias:
            categoria_dominante = max(categorias.keys(), key=lambda x: categorias[x]['count'])
            recommendations.append(
                f"📊 Categoría con más necesidades: {categoria_dominante} "
                f"({categorias[categoria_dominante]['count']} productos)"
            )

        # Recomendaciones de timing
        urgentes = [p for p in productos_comprar if p['urgencia'] == 'URGENTE']
        if urgentes:
            recommendations.append(
                f"🚨 {len(urgentes)} productos URGENTES - comprar hoy mismo"
            )

        # Recomendaciones de presupuesto
        total_cost = sum([p['costo_total'] for p in productos_comprar])
        if total_cost > 10000:  # Umbral alto
            recommendations.append(
                f"💰 Compra alta: ${total_cost:,.2f} - considerar financiamiento"
            )

        return recommendations

# Función para testing
def test_inventory_optimizer():
    """Test del optimizador de inventario"""

    print("📦 Testing Optimizador de Inventario...")

    # Crear datos ejemplo
    productos_ejemplo = pd.DataFrame([
        {
            'codigo_producto': 'ACEIT001',
            'nombre_producto': 'Aceite Girasol 900ml', 
            'categoria': 'Almacen',
            'stock_actual': 5,  # Stock bajo
            'costo_unitario': 150.50
        },
        {
            'codigo_producto': 'LECHE001',
            'nombre_producto': 'Leche Larga Vida 1L',
            'categoria': 'Lacteos', 
            'stock_actual': 0,  # Agotado
            'costo_unitario': 120.00
        },
        {
            'codigo_producto': 'CERV001',
            'nombre_producto': 'Cerveza Quilmes 970ml',
            'categoria': 'Bebidas',
            'stock_actual': 50,  # Stock normal
            'costo_unitario': 200.00
        }
    ])

    # Inicializar optimizador
    optimizer = InventoryOptimizer()

    # Generar recomendaciones de compra
    recomendaciones = optimizer.generate_daily_purchase_recommendations(
        productos_ejemplo, budget_limit=5000
    )

    print(f"\n📋 RECOMENDACIONES DE COMPRA - {recomendaciones['fecha_recomendacion']}")
    print("=" * 60)

    resumen = recomendaciones['resumen']
    print(f"Total productos a comprar: {resumen['total_productos_comprar']}")
    print(f"Costo total estimado: ${resumen['costo_total_estimado']:,.2f}")
    print(f"Productos urgentes: {resumen['productos_urgentes']}")
    print(f"Productos críticos: {resumen['productos_criticos']}")

    print("\n🛒 LISTA DE COMPRAS:")
    print("-" * 60)

    for i, producto in enumerate(recomendaciones['lista_compras'], 1):
        print(f"{i}. {producto['nombre_producto']}")
        print(f"   📦 Stock actual: {producto['stock_actual']}")
        print(f"   ⏰ Días restantes: {producto['dias_restantes']}")
        print(f"   🚨 Urgencia: {producto['urgencia']}")
        print(f"   💰 Comprar: {producto['cantidad_sugerida']} unidades (${producto['costo_total']:,.2f})")
        print(f"   📝 Razón: {producto['razon_compra']}")
        print()

    print("💡 RECOMENDACIONES ADICIONALES:")
    for rec in recomendaciones['recomendaciones_adicionales']:
        print(f"   {rec}")

    return recomendaciones

if __name__ == "__main__":
    test_recomendaciones = test_inventory_optimizer()
    print("\n✅ Optimizador de Inventario listo!")
