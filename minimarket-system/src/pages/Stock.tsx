import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { StockDeposito, Producto } from '../types/database'
import { Package, AlertTriangle } from 'lucide-react'

interface StockConProducto extends StockDeposito {
  producto?: Producto
}

export default function Stock() {
  const [stock, setStock] = useState<StockConProducto[]>([])
  const [loading, setLoading] = useState(true)
  const [filtro, setFiltro] = useState<'todos' | 'bajo' | 'critico'>('todos')

  useEffect(() => {
    loadStock()
  }, [])

  async function loadStock() {
    try {
      const { data: stockData } = await supabase
        .from('stock_deposito')
        .select('*')
        .order('cantidad_actual', { ascending: true })

      if (stockData) {
        // Obtener información de productos
        const productosIds = stockData.map(s => s.producto_id)
        const { data: productos } = await supabase
          .from('productos')
          .select('*')
          .in('id', productosIds)

        const stockConProducto = stockData.map(s => ({
          ...s,
          producto: productos?.find(p => p.id === s.producto_id)
        }))

        setStock(stockConProducto)
      }
    } catch (error) {
      console.error('Error cargando stock:', error)
    } finally {
      setLoading(false)
    }
  }

  const stockFiltrado = stock.filter(s => {
    if (filtro === 'critico') return s.cantidad_actual === 0
    if (filtro === 'bajo') return s.cantidad_actual > 0 && s.cantidad_actual <= s.cantidad_minima
    return true
  })

  const getNivelStock = (item: StockConProducto) => {
    if (item.cantidad_actual === 0) return 'critico'
    if (item.cantidad_actual <= item.cantidad_minima / 2) return 'urgente'
    if (item.cantidad_actual <= item.cantidad_minima) return 'bajo'
    return 'normal'
  }

  if (loading) {
    return <div className="text-center py-8">Cargando...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Control de Stock</h1>
        
        <div className="flex gap-2">
          <button
            onClick={() => setFiltro('todos')}
            className={`px-4 py-2 rounded-lg ${
              filtro === 'todos' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Todos ({stock.length})
          </button>
          <button
            onClick={() => setFiltro('bajo')}
            className={`px-4 py-2 rounded-lg ${
              filtro === 'bajo' ? 'bg-orange-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Stock Bajo ({stock.filter(s => s.cantidad_actual > 0 && s.cantidad_actual <= s.cantidad_minima).length})
          </button>
          <button
            onClick={() => setFiltro('critico')}
            className={`px-4 py-2 rounded-lg ${
              filtro === 'critico' ? 'bg-red-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Crítico ({stock.filter(s => s.cantidad_actual === 0).length})
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Producto
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ubicación
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cantidad Actual
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Mínimo
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Estado
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {stockFiltrado.map((item) => {
              const nivel = getNivelStock(item)
              
              return (
                <tr key={item.id} className={
                  nivel === 'critico' ? 'bg-red-50' :
                  nivel === 'urgente' ? 'bg-orange-50' :
                  nivel === 'bajo' ? 'bg-yellow-50' :
                  ''
                }>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Package className="w-5 h-5 text-gray-400 mr-3" />
                      <div>
                        <div className="font-medium text-gray-900">
                          {item.producto?.nombre || 'Producto desconocido'}
                        </div>
                        {item.lote && (
                          <div className="text-sm text-gray-500">Lote: {item.lote}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.ubicacion || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-bold text-gray-900">{item.cantidad_actual}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.cantidad_minima}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {nivel === 'critico' && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <AlertTriangle className="w-4 h-4 mr-1" />
                        AGOTADO
                      </span>
                    )}
                    {nivel === 'urgente' && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                        <AlertTriangle className="w-4 h-4 mr-1" />
                        MUY BAJO
                      </span>
                    )}
                    {nivel === 'bajo' && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        STOCK BAJO
                      </span>
                    )}
                    {nivel === 'normal' && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        NORMAL
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        
        {stockFiltrado.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No hay productos en esta categoría
          </div>
        )}
      </div>
    </div>
  )
}
