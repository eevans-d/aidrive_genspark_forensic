import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { TareaPendiente, StockDeposito, Producto } from '../types/database'
import { AlertTriangle, TrendingUp, Package, CheckCircle } from 'lucide-react'

export default function Dashboard() {
  const [tareasPendientes, setTareasPendientes] = useState<TareaPendiente[]>([])
  const [stockBajo, setStockBajo] = useState<number>(0)
  const [totalProductos, setTotalProductos] = useState<number>(0)
  const [tareasUrgentes, setTareasUrgentes] = useState<number>(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  async function loadDashboardData() {
    try {
      // Cargar tareas pendientes
      const { data: tareas } = await supabase
        .from('tareas_pendientes')
        .select('*')
        .eq('estado', 'pendiente')
        .order('prioridad', { ascending: false })
        .limit(5)

      if (tareas) {
        setTareasPendientes(tareas)
        setTareasUrgentes(tareas.filter(t => t.prioridad === 'urgente').length)
      }

      // Cargar stock
      const { data: stock } = await supabase
        .from('stock_deposito')
        .select('*')

      if (stock) {
        const stockBajoCount = stock.filter(
          (s: StockDeposito) => s.cantidad_actual <= s.cantidad_minima
        ).length
        setStockBajo(stockBajoCount)
      }

      // Cargar total de productos
      const { data: productos } = await supabase
        .from('productos')
        .select('*', { count: 'exact', head: true })

      if (productos) {
        setTotalProductos(productos.length || 0)
      }

    } catch (error) {
      console.error('Error cargando dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>

      {/* Métricas principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Tareas Urgentes</p>
              <p className="text-3xl font-bold text-red-600">{tareasUrgentes}</p>
            </div>
            <AlertTriangle className="w-12 h-12 text-red-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Stock Bajo</p>
              <p className="text-3xl font-bold text-orange-600">{stockBajo}</p>
            </div>
            <Package className="w-12 h-12 text-orange-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Productos</p>
              <p className="text-3xl font-bold text-blue-600">{totalProductos}</p>
            </div>
            <TrendingUp className="w-12 h-12 text-blue-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Tareas Pendientes</p>
              <p className="text-3xl font-bold text-green-600">{tareasPendientes.length}</p>
            </div>
            <CheckCircle className="w-12 h-12 text-green-600" />
          </div>
        </div>
      </div>

      {/* Tareas recientes */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">Tareas Pendientes Prioritarias</h2>
        </div>
        <div className="p-6">
          {tareasPendientes.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No hay tareas pendientes</p>
          ) : (
            <div className="space-y-3">
              {tareasPendientes.map((tarea) => (
                <div
                  key={tarea.id}
                  className={`p-4 rounded-lg border-l-4 ${
                    tarea.prioridad === 'urgente'
                      ? 'border-red-500 bg-red-50'
                      : tarea.prioridad === 'normal'
                      ? 'border-yellow-500 bg-yellow-50'
                      : 'border-blue-500 bg-blue-50'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{tarea.titulo}</h3>
                      <p className="text-sm text-gray-600 mt-1">{tarea.descripcion}</p>
                      <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                        <span>Asignado a: {tarea.asignada_a_nombre || 'Sin asignar'}</span>
                        {tarea.fecha_vencimiento && (
                          <span>Vence: {new Date(tarea.fecha_vencimiento).toLocaleDateString('es-AR')}</span>
                        )}
                      </div>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        tarea.prioridad === 'urgente'
                          ? 'bg-red-100 text-red-800'
                          : tarea.prioridad === 'normal'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {tarea.prioridad.toUpperCase()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
