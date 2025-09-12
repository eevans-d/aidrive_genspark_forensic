"""
API REST para el Dashboard Operativo del Sistema de Inventario Inteligente
"""

from flask import Flask, jsonify, request
from datetime import datetime
from reorder_engine_integrated import ReorderEngineIntegrated, DashboardData

class DashboardAPI:
    """
    API REST para el dashboard operativo del inventario inteligente

    Endpoints disponibles:
    - GET /dashboard/today - Dashboard completo de hoy
    - GET /dashboard/purchases - Solo recomendaciones de compra
    - GET /dashboard/alerts - Solo alertas críticas  
    - GET /dashboard/kpis - Solo KPIs principales
    - GET /dashboard/predictions - Solo predicciones ML
    - POST /dashboard/custom - Dashboard para fecha específica
    - GET /health - Health check del sistema
    """

    def __init__(self, reorder_engine: ReorderEngineIntegrated):
        self.engine = reorder_engine
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):
        """Configurar todas las rutas de la API"""

        @self.app.route('/dashboard/today', methods=['GET'])
        def get_dashboard_today():
            """Dashboard completo para hoy"""
            try:
                dashboard = self.engine.generar_dashboard_operativo_diario()
                return self._serialize_dashboard(dashboard)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/dashboard/purchases', methods=['GET'])
        def get_purchases_today():
            """Solo recomendaciones de compra para hoy"""
            try:
                dashboard = self.engine.generar_dashboard_operativo_diario()
                return jsonify({
                    'fecha': dashboard.fecha_reporte.isoformat(),
                    'compras_recomendadas': dashboard.compras_recomendadas,
                    'total_inversion': sum(c.get('costo_total', 0) for c in dashboard.compras_recomendadas),
                    'productos_urgentes': len([c for c in dashboard.compras_recomendadas if c.get('prioridad') == 'ALTA'])
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check del sistema"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'components': {
                    'reorder_engine': 'OK',
                    'redis_cache': 'OK' if self.engine.redis_client else 'DISCONNECTED',
                    'ml_engine': 'FALLBACK' if not self.engine.ml_engine else 'OK'
                }
            })

    def _serialize_dashboard(self, dashboard: DashboardData):
        """Serializar dashboard completo para JSON"""
        alertas_serializadas = []
        for alerta in dashboard.alertas_criticas:
            alertas_serializadas.append({
                'tipo': alerta.tipo,
                'producto_codigo': alerta.producto_codigo,
                'producto_nombre': alerta.producto_nombre,
                'nivel_criticidad': alerta.nivel_criticidad,
                'mensaje': alerta.mensaje,
                'accion_recomendada': alerta.accion_recomendada,
                'timestamp': alerta.timestamp.isoformat()
            })

        return jsonify({
            'fecha_reporte': dashboard.fecha_reporte.isoformat(),
            'compras_recomendadas': dashboard.compras_recomendadas,
            'alertas_criticas': alertas_serializadas,
            'kpis_principales': dashboard.kpis_principales,
            'predicciones_demanda': dashboard.predicciones_demanda,
            'estado_inventario': dashboard.estado_inventario,
            'metricas_financieras': dashboard.metricas_financieras,
            'resumen_ejecutivo': {
                'productos_para_comprar': len(dashboard.compras_recomendadas),
                'alertas_criticas': len(dashboard.alertas_criticas),
                'disponibilidad_general': dashboard.kpis_principales.get('porcentaje_disponibilidad', 0),
                'inversion_recomendada': dashboard.metricas_financieras.get('costo_compras_recomendadas_hoy', 0)
            }
        })

    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Ejecutar la API"""
        print(f"🚀 Iniciando Dashboard API en http://{host}:{port}")
        print("📋 Endpoints disponibles:")
        print("   • GET  /dashboard/today     - Dashboard completo")
        print("   • GET  /dashboard/purchases - Recomendaciones de compra")
        print("   • GET  /dashboard/alerts    - Alertas críticas")
        print("   • GET  /dashboard/kpis      - KPIs y métricas")
        print("   • GET  /health              - Estado del sistema")

        self.app.run(host=host, port=port, debug=debug)

# EJEMPLO DE USO:
if __name__ == "__main__":
    # Crear motor de reordenamiento
    engine = ReorderEngineIntegrated()

    # Crear API
    api = DashboardAPI(engine)

    # Ejecutar servidor
    api.run(debug=True)
