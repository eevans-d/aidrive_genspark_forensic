import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../contexts/AuthContext'
import { Producto, Proveedor } from '../types/database'
import { Plus, Minus, Search } from 'lucide-react'

export default function Deposito() {
  const { user } = useAuth()
  const [productos, setProductos] = useState<Producto[]>([])
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedProducto, setSelectedProducto] = useState<Producto | null>(null)
  const [tipo, setTipo] = useState<'entrada' | 'salida'>('entrada')
  const [cantidad, setCantidad] = useState('')
  const [destino, setDestino] = useState('')
  const [proveedorId, setProveedorId] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [loading, setLoading] = useState(false)
  const [mensaje, setMensaje] = useState<{ tipo: 'success' | 'error', texto: string } | null>(null)

  useEffect(() => {
    loadProductos()
    loadProveedores()
  }, [])

  async function loadProductos() {
    const { data } = await supabase
      .from('productos')
      .select('*')
      .eq('activo', true)
      .order('nombre')
    
    if (data) setProductos(data)
  }

  async function loadProveedores() {
    const { data } = await supabase
      .from('proveedores')
      .select('*')
      .eq('activo', true)
      .order('nombre')
    
    if (data) setProveedores(data)
  }

  const productosFiltrados = productos.filter(p =>
    p.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (p.codigo_barras && p.codigo_barras.includes(searchTerm))
  )

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    
    if (!selectedProducto || !cantidad) {
      setMensaje({ tipo: 'error', texto: 'Por favor complete todos los campos requeridos' })
      return
    }

    setLoading(true)
    setMensaje(null)

    try {
      // Registrar movimiento
      const { error: movError } = await supabase
        .from('movimientos_deposito')
        .insert({
          producto_id: selectedProducto.id,
          tipo: tipo,
          cantidad: parseInt(cantidad),
          destino: tipo === 'salida' ? destino : null,
          proveedor_id: tipo === 'entrada' ? proveedorId : null,
          observaciones: observaciones || null,
          usuario_id: user?.id || null,
          usuario_nombre: user?.user_metadata?.nombre || user?.email || 'Usuario',
          fecha: new Date().toISOString()
        })

      if (movError) throw movError

      // Actualizar stock
      const { data: stockActual } = await supabase
        .from('stock_deposito')
        .select('*')
        .eq('producto_id', selectedProducto.id)
        .maybeSingle()

      if (stockActual) {
        const nuevaCantidad = tipo === 'entrada'
          ? stockActual.cantidad_actual + parseInt(cantidad)
          : stockActual.cantidad_actual - parseInt(cantidad)

        await supabase
          .from('stock_deposito')
          .update({ 
            cantidad_actual: Math.max(0, nuevaCantidad),
            updated_at: new Date().toISOString()
          })
          .eq('id', stockActual.id)
      } else {
        // Crear registro de stock si no existe
        if (tipo === 'entrada') {
          await supabase
            .from('stock_deposito')
            .insert({
              producto_id: selectedProducto.id,
              cantidad_actual: parseInt(cantidad),
              cantidad_minima: 10
            })
        }
      }

      setMensaje({ tipo: 'success', texto: 'Movimiento registrado correctamente' })
      
      // Limpiar formulario
      setSelectedProducto(null)
      setCantidad('')
      setDestino('')
      setProveedorId('')
      setObservaciones('')
      setSearchTerm('')
      
    } catch (error: any) {
      console.error('Error:', error)
      setMensaje({ tipo: 'error', texto: 'Error al registrar el movimiento' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Gestión de Depósito</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-6">Registrar Movimiento</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Tipo de movimiento */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tipo de Movimiento
            </label>
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => setTipo('entrada')}
                className={`flex-1 py-4 px-6 rounded-lg border-2 font-medium transition-all ${
                  tipo === 'entrada'
                    ? 'border-green-500 bg-green-50 text-green-700'
                    : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                }`}
              >
                <Plus className="w-6 h-6 mx-auto mb-2" />
                ENTRADA
              </button>
              <button
                type="button"
                onClick={() => setTipo('salida')}
                className={`flex-1 py-4 px-6 rounded-lg border-2 font-medium transition-all ${
                  tipo === 'salida'
                    ? 'border-red-500 bg-red-50 text-red-700'
                    : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                }`}
              >
                <Minus className="w-6 h-6 mx-auto mb-2" />
                SALIDA
              </button>
            </div>
          </div>

          {/* Búsqueda de producto */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Buscar Producto
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Escriba el nombre o código del producto..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
              />
            </div>
          </div>

          {/* Lista de productos filtrados */}
          {searchTerm && (
            <div className="border border-gray-200 rounded-lg max-h-60 overflow-y-auto">
              {productosFiltrados.map((producto) => (
                <button
                  key={producto.id}
                  type="button"
                  onClick={() => {
                    setSelectedProducto(producto)
                    setSearchTerm('')
                  }}
                  className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b last:border-b-0"
                >
                  <div className="font-medium">{producto.nombre}</div>
                  {producto.codigo_barras && (
                    <div className="text-sm text-gray-500">{producto.codigo_barras}</div>
                  )}
                </button>
              ))}
              {productosFiltrados.length === 0 && (
                <div className="px-4 py-3 text-gray-500">No se encontraron productos</div>
              )}
            </div>
          )}

          {/* Producto seleccionado */}
          {selectedProducto && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="font-medium text-blue-900">Producto seleccionado:</div>
              <div className="text-lg font-bold text-blue-900">{selectedProducto.nombre}</div>
            </div>
          )}

          {/* Cantidad */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cantidad
            </label>
            <input
              type="number"
              value={cantidad}
              onChange={(e) => setCantidad(e.target.value)}
              min="1"
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
              placeholder="Ingrese la cantidad"
            />
          </div>

          {/* Proveedor (solo para entradas) */}
          {tipo === 'entrada' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Proveedor
              </label>
              <select
                value={proveedorId}
                onChange={(e) => setProveedorId(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
              >
                <option value="">Seleccione un proveedor</option>
                {proveedores.map((prov) => (
                  <option key={prov.id} value={prov.id}>
                    {prov.nombre}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Destino (solo para salidas) */}
          {tipo === 'salida' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Destino
              </label>
              <select
                value={destino}
                onChange={(e) => setDestino(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
              >
                <option value="">Seleccione destino</option>
                <option value="Mini Market">Mini Market</option>
                <option value="Otro">Otro</option>
              </select>
            </div>
          )}

          {/* Observaciones */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Observaciones (Opcional)
            </label>
            <textarea
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              rows={3}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
              placeholder="Notas adicionales..."
            />
          </div>

          {/* Mensaje */}
          {mensaje && (
            <div
              className={`p-4 rounded-lg ${
                mensaje.tipo === 'success'
                  ? 'bg-green-50 text-green-800 border border-green-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}
            >
              {mensaje.texto}
            </div>
          )}

          {/* Botón submit */}
          <button
            type="submit"
            disabled={loading || !selectedProducto}
            className="w-full py-4 px-6 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-lg"
          >
            {loading ? 'Registrando...' : 'REGISTRAR MOVIMIENTO'}
          </button>
        </form>
      </div>
    </div>
  )
}
