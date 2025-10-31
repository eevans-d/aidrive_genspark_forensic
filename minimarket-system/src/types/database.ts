export interface Proveedor {
  id: string
  nombre: string
  contacto: string | null
  email: string | null
  telefono: string | null
  productos_ofrecidos: string[] | null
  activo: boolean
  created_at: string
  updated_at: string
}

export interface Producto {
  id: string
  nombre: string
  categoria: string | null
  codigo_barras: string | null
  precio_actual: number | null
  precio_costo: number | null
  proveedor_principal_id: string | null
  margen_ganancia: number | null
  activo: boolean
  created_at: string
  updated_at: string
}

export interface PrecioHistorico {
  id: string
  producto_id: string
  precio: number
  fuente: string | null
  fecha: string
  cambio_porcentaje: number | null
  created_at: string
}

export interface StockDeposito {
  id: string
  producto_id: string
  cantidad_actual: number
  cantidad_minima: number
  ubicacion: string | null
  lote: string | null
  fecha_vencimiento: string | null
  created_at: string
  updated_at: string
}

export interface MovimientoDeposito {
  id: string
  producto_id: string
  tipo: 'entrada' | 'salida'
  cantidad: number
  fecha: string
  usuario_id: string | null
  usuario_nombre: string | null
  destino: string | null
  proveedor_id: string | null
  observaciones: string | null
  created_at: string
}

export interface ProductoFaltante {
  id: string
  producto_id: string | null
  producto_nombre: string | null
  fecha_reporte: string
  reportado_por_id: string | null
  reportado_por_nombre: string | null
  proveedor_asignado_id: string | null
  resuelto: boolean
  fecha_resolucion: string | null
  observaciones: string | null
  created_at: string
}

export interface TareaPendiente {
  id: string
  titulo: string
  descripcion: string | null
  asignada_a_id: string | null
  asignada_a_nombre: string | null
  prioridad: 'baja' | 'normal' | 'urgente'
  estado: 'pendiente' | 'completada' | 'cancelada'
  fecha_creacion: string
  fecha_vencimiento: string | null
  fecha_completada: string | null
  completada_por_id: string | null
  completada_por_nombre: string | null
  fecha_cancelada: string | null
  cancelada_por_id: string | null
  cancelada_por_nombre: string | null
  razon_cancelacion: string | null
  creada_por_id: string | null
  creada_por_nombre: string | null
  created_at: string
  updated_at: string
}

export interface NotificacionTarea {
  id: string
  tarea_id: string
  tipo: string | null
  mensaje: string | null
  usuario_destino_id: string | null
  usuario_destino_nombre: string | null
  fecha_envio: string
  leido: boolean
  created_at: string
}

export interface Personal {
  id: string
  nombre: string
  email: string | null
  telefono: string | null
  rol: string | null
  departamento: string | null
  activo: boolean
  fecha_ingreso: string | null
  user_auth_id: string | null
  created_at: string
  updated_at: string
}
