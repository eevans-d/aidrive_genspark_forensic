-- SQLite Optimization Pragmas for inventario-retail module
-- Optimizado para operaciones de stock retail con alta concurrencia

-- WAL mode para mejor concurrencia
PRAGMA journal_mode=WAL;

-- Sincronización normal para balance performance/durabilidad
PRAGMA synchronous=NORMAL;

-- Habilitar foreign keys para integridad referencial
PRAGMA foreign_keys=ON;

-- Timeout para operaciones bloqueadas (10 segundos)
PRAGMA busy_timeout=10000;

-- Cache de 64MB para operaciones frecuentes
PRAGMA cache_size=-64000;

-- Almacenar temporales en memoria
PRAGMA temp_store=MEMORY;

-- Optimizar para lecturas secuenciales
PRAGMA mmap_size=268435456;

-- Habilitar estadísticas para el optimizador
PRAGMA optimize;

-- Índices específicos para stock (solo si no existen)
CREATE INDEX IF NOT EXISTS idx_producto_stock ON movimientos_stock(producto_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_stock_active ON productos(id) WHERE stock_actual > 0;
CREATE INDEX IF NOT EXISTS idx_movimientos_tipo ON movimientos_stock(tipo_movimiento, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria) WHERE categoria IS NOT NULL;

-- Índice compuesto para consultas frecuentes de stock
CREATE INDEX IF NOT EXISTS idx_stock_producto_fecha ON movimientos_stock(producto_id, tipo_movimiento, created_at DESC);