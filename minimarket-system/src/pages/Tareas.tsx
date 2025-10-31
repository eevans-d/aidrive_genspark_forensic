import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { TareaPendiente } from '../types/database'
import { CheckCircle, X, Plus } from 'lucide-react'

export default function Tareas() {
  const [tareas, setTareas] = useState<TareaPendiente[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    titulo: '',
    descripcion: '',
    asignada_a_nombre: '',
    prioridad: 'normal' as 'baja' | 'normal' | 'urgente',
    fecha_vencimiento: ''
  })

  useEffect(() => {
    loadTareas()
  }, [])

  async function loadTareas() {
    try {
      const { data } = await supabase
        .from('tareas_pendientes')
        .select('*')
        .order('prioridad', { ascending: false })
        .order('fecha_creacion', { ascending: false })

      if (data) setTareas(data)
    } catch (error) {
      console.error('Error cargando tareas:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateTarea(e: React.FormEvent) {
    e.preventDefault()

    try {
      const { error } = await supabase
        .from('tareas_pendientes')
        .insert({
          ...formData,
          estado: 'pendiente',
          creada_por_nombre: 'Usuario Sistema',
          fecha_vencimiento: formData.fecha_vencimiento || null
        })

      if (error) throw error

      setShowForm(false)
      setFormData({
        titulo: '',
        descripcion: '',
        asignada_a_nombre: '',
        prioridad: 'normal',
        fecha_vencimiento: ''
      })
      loadTareas()
    } catch (error) {
      console.error('Error creando tarea:', error)
    }
  }

  async function handleCompletarTarea(id: string) {
    try {
      const { error } = await supabase
        .from('tareas_pendientes')
        .update({
          estado: 'completada',
          fecha_completada: new Date().toISOString(),
          completada_por_nombre: 'Usuario Sistema'
        })
        .eq('id', id)

      if (error) throw error
      loadTareas()
    } catch (error) {
      console.error('Error completando tarea:', error)
    }
  }

  async function handleCancelarTarea(id: string) {
    const razon = prompt('Ingrese la razón de cancelación:')
    if (!razon) return

    try {
      const { error } = await supabase
        .from('tareas_pendientes')
        .update({
          estado: 'cancelada',
          fecha_cancelada: new Date().toISOString(),
          cancelada_por_nombre: 'Usuario Sistema',
          razon_cancelacion: razon
        })
        .eq('id', id)

      if (error) throw error
      loadTareas()
    } catch (error) {
      console.error('Error cancelando tarea:', error)
    }
  }

  const tareasPendientes = tareas.filter(t => t.estado === 'pendiente')
  const tareasCompletadas = tareas.filter(t => t.estado === 'completada')

  if (loading) {
    return <div className="text-center py-8">Cargando...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Gestión de Tareas</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-5 h-5" />
          Nueva Tarea
        </button>
      </div>

      {/* Formulario de nueva tarea */}
      {showForm && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Crear Nueva Tarea</h2>
          <form onSubmit={handleCreateTarea} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Título
              </label>
              <input
                type="text"
                value={formData.titulo}
                onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descripción
              </label>
              <textarea
                value={formData.descripcion}
                onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Asignada a
                </label>
                <input
                  type="text"
                  value={formData.asignada_a_nombre}
                  onChange={(e) => setFormData({ ...formData, asignada_a_nombre: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prioridad
                </label>
                <select
                  value={formData.prioridad}
                  onChange={(e) => setFormData({ ...formData, prioridad: e.target.value as any })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="baja">Baja</option>
                  <option value="normal">Normal</option>
                  <option value="urgente">Urgente</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fecha de Vencimiento
              </label>
              <input
                type="datetime-local"
                value={formData.fecha_vencimiento}
                onChange={(e) => setFormData({ ...formData, fecha_vencimiento: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex gap-2">
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Crear Tarea
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tareas Pendientes */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">
            Tareas Pendientes ({tareasPendientes.length})
          </h2>
        </div>
        <div className="p-6 space-y-4">
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
                  {tarea.descripcion && (
                    <p className="text-sm text-gray-600 mt-1">{tarea.descripcion}</p>
                  )}
                  <div className="mt-2 flex items-center flex-wrap gap-4 text-sm text-gray-500">
                    {tarea.asignada_a_nombre && (
                      <span>Asignado: {tarea.asignada_a_nombre}</span>
                    )}
                    {tarea.fecha_vencimiento && (
                      <span>Vence: {new Date(tarea.fecha_vencimiento).toLocaleString('es-AR')}</span>
                    )}
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      tarea.prioridad === 'urgente'
                        ? 'bg-red-100 text-red-800'
                        : tarea.prioridad === 'normal'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {tarea.prioridad.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => handleCompletarTarea(tarea.id)}
                    className="p-2 text-green-600 hover:bg-green-100 rounded-lg"
                    title="Completar"
                  >
                    <CheckCircle className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => handleCancelarTarea(tarea.id)}
                    className="p-2 text-red-600 hover:bg-red-100 rounded-lg"
                    title="Cancelar"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
          {tareasPendientes.length === 0 && (
            <p className="text-gray-500 text-center py-4">No hay tareas pendientes</p>
          )}
        </div>
      </div>

      {/* Tareas Completadas */}
      {tareasCompletadas.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold">
              Tareas Completadas ({tareasCompletadas.length})
            </h2>
          </div>
          <div className="p-6 space-y-3">
            {tareasCompletadas.slice(0, 5).map((tarea) => (
              <div key={tarea.id} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-700">{tarea.titulo}</h3>
                    <div className="text-sm text-gray-500 mt-1">
                      Completada por {tarea.completada_por_nombre} el{' '}
                      {tarea.fecha_completada && new Date(tarea.fecha_completada).toLocaleString('es-AR')}
                    </div>
                  </div>
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
