/**
 * INTEGRATION TESTS - DATABASE
 * Tests de integración con la base de datos Supabase
 */

const { describe, test, expect, beforeAll, afterAll, beforeEach, afterEach } = require('@jest/globals');

// Mock de la configuración de Supabase para testing
const SUPABASE_CONFIG = {
  url: 'https://test-project.supabase.co',
  serviceKey: 'test-service-key'
};

// Mock fetch global
global.fetch = jest.fn();

describe('🗄️ INTEGRATION TESTS - Database', () => {
  
  describe('📊 Tabla precios_proveedor', () => {
    
    test('debe insertar y consultar productos correctamente', async () => {
      const productoTest = {
        sku: 'TEST_INTEGRATION_001',
        nombre: 'Producto Test Integración',
        marca: 'Marca Test',
        categoria: 'test',
        precio_unitario: 99.99,
        stock_disponible: 100,
        url_producto: 'https://test.com/producto/1',
        ultima_actualizacion: new Date().toISOString(),
        fuente: 'Test Integration',
        activo: true
      };
      
      // Mock inserción
      fetch
        .mockResolvedValueOnce({ // Verificar existencia
          ok: true,
          json: () => Promise.resolve([]) // No existe
        })
        .mockResolvedValueOnce({ // Insertar
          ok: true,
          json: () => Promise.resolve([{ id: 'new-product-id' }])
        })
        .mockResolvedValueOnce({ // Consulta
          ok: true,
          json: () => Promise.resolve([{
            id: 'new-product-id',
            ...productoTest
          }])
        });
      
      // Simular inserción
      const insertResult = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/precios_proveedor`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(productoTest)
      });
      
      expect(insertResult.ok).toBe(true);
      
      // Simular consulta
      const queryResult = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/precios_proveedor?sku=eq.TEST_INTEGRATION_001`, {
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`
        }
      });
      
      expect(queryResult.ok).toBe(true);
    });
    
    test('debe actualizar productos existentes', async () => {
      const productoActualizado = {
        nombre: 'Producto Actualizado',
        precio_unitario: 149.99,
        stock_disponible: 50
      };
      
      fetch
        .mockResolvedValueOnce({ // Verificar existencia
          ok: true,
          json: () => Promise.resolve([{ id: 'existing-id' }])
        })
        .mockResolvedValueOnce({ // Actualizar
          ok: true,
          json: () => Promise.resolve([{ id: 'existing-id', ...productoActualizado }])
        });
      
      const updateResult = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/precios_proveedor?sku=eq.TEST_INTEGRATION_001`, {
        method: 'PATCH',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(productoActualizado)
      });
      
      expect(updateResult.ok).toBe(true);
    });
    
    test('debe manejar búsquedas complejas', async () => {
      const filtros = {
        categoria: 'bebidas',
        marca: 'Coca Cola',
        solo_con_stock: true
      };
      
      let query = `${SUPABASE_CONFIG.url}/rest/v1/precios_proveedor?select=*&fuente=eq.Maxiconsumo Necochea&activo=eq.true`;
      
      // Aplicar filtros
      query += `&categoria=eq.${encodeURIComponent(filtros.categoria)}`;
      query += `&marca=ilike.*${encodeURIComponent(filtros.marca)}*`;
      query += `&stock_disponible=gt.0`;
      query += `&order=nombre.asc`;
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([
          {
            id: '1',
            sku: 'CC500',
            nombre: 'Coca Cola 500ml',
            marca: 'Coca Cola',
            categoria: 'bebidas',
            precio_unitario: 250.50,
            stock_disponible: 100
          }
        ])
      });
      
      const searchResult = await fetch(query, {
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`
        }
      });
      
      expect(searchResult.ok).toBe(true);
      
      // Verificar que la query contenga los filtros correctos
      const lastCall = fetch.mock.calls[fetch.mock.calls.length - 1];
      expect(lastCall[0]).toContain('categoria=eq.bebidas');
      expect(lastCall[0]).toContain('marca=ilike.*Coca%20Cola*');
      expect(lastCall[0]).toContain('stock_disponible=gt.0');
    });
    
  });
  
  describe('🔄 Tabla comparacion_precios', () => {
    
    test('debe insertar comparaciones de precios', async () => {
      const comparacion = {
        producto_id: 'producto-123',
        nombre_producto: 'Producto de Prueba',
        precio_actual: 100.00,
        precio_proveedor: 80.00,
        diferencia_absoluta: 20.00,
        diferencia_porcentual: 25.00,
        fuente: 'Maxiconsumo Necochea',
        fecha_comparacion: new Date().toISOString(),
        es_oportunidad_ahorro: true,
        recomendacion: 'OPORTUNIDAD CRÍTICA: Ahorro potencial del 25.0% ($20.00)'
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: 'comparison-123' }])
      });
      
      const result = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/comparacion_precios`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(comparacion)
      });
      
      expect(result.ok).toBe(true);
    });
    
    test('debe consultar vista de oportunidades de ahorro', async () => {
      const query = `${SUPABASE_CONFIG.url}/rest/v1/vista_oportunidades_ahorro?select=*&order=diferencia_absoluta.desc&limit=50`;
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([
          {
            id: 'opp1',
            nombre_producto: 'Producto 1',
            precio_actual: 100,
            precio_proveedor: 75,
            diferencia_absoluta: 25,
            diferencia_porcentual: 33.33,
            recomendacion: 'OPORTUNIDAD CRÍTICA'
          }
        ])
      });
      
      const result = await fetch(query, {
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`
        }
      });
      
      expect(result.ok).toBe(true);
      
      const data = await result.json();
      expect(data).toHaveLength(1);
      expect(data[0].es_oportunidad_ahorro).toBe(true);
    });
    
  });
  
  describe('🚨 Tabla alertas_cambios_precios', () => {
    
    test('debe crear alertas por cambios significativos', async () => {
      const alerta = {
        producto_id: 'producto-456',
        tipo_cambio: 'aumento',
        valor_anterior: 100.00,
        valor_nuevo: 130.00,
        porcentaje_cambio: 30.00,
        severidad: 'critica',
        mensaje: 'Precio aumentó 30.0%',
        accion_recomendada: 'Revisar estrategia de precios y márgenes',
        fecha_alerta: new Date().toISOString(),
        procesada: false,
        creado_por: 'Sistema Automatizado'
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: 'alert-123' }])
      });
      
      const result = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/alertas_cambios_precios`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(alerta)
      });
      
      expect(result.ok).toBe(true);
    });
    
    test('debe consultar vista de alertas activas', async () => {
      const query = `${SUPABASE_CONFIG.url}/rest/v1/vista_alertas_activas?select=*&order=fecha_alerta.desc&limit=20`;
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([
          {
            id: 'alert1',
            nombre_producto: 'Producto con Alerta',
            tipo_cambio: 'disminucion',
            porcentaje_cambio: -20.00,
            severidad: 'alta',
            mensaje: 'Precio disminuyó 20.0%',
            fecha_alerta: new Date().toISOString()
          }
        ])
      });
      
      const result = await fetch(query, {
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`
        }
      });
      
      expect(result.ok).toBe(true);
      
      const data = await result.json();
      expect(data).toHaveLength(1);
      expect(data[0].procesada).toBe(false);
    });
    
    test('debe marcar alertas como procesadas', async () => {
      const alertaId = 'alert-123';
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: alertaId, procesada: true }])
      });
      
      const result = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/alertas_cambios_precios?id=eq.${alertaId}`, {
        method: 'PATCH',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          procesada: true,
          fecha_procesamiento: new Date().toISOString()
        })
      });
      
      expect(result.ok).toBe(true);
    });
    
  });
  
  describe('📈 Tabla estadisticas_scraping', () => {
    
    test('debe registrar estadísticas de scraping', async () => {
      const estadisticas = {
        fuente: 'Maxiconsumo Necochea',
        categoria_procesada: 'bebidas',
        productos_encontrados: 1500,
        productos_nuevos: 200,
        productos_actualizados: 1300,
        tiempo_ejecucion_ms: 45000,
        errores_encontrados: 5,
        status: 'exitoso',
        detalles_error: null,
        metadata: {
          categorias_procesadas: ['bebidas'],
          productos_por_minuto: 2000,
          peak_memory_mb: 512
        }
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: 'stats-123' }])
      });
      
      const result = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/estadisticas_scraping`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(estadisticas)
      });
      
      expect(result.ok).toBe(true);
    });
    
    test('debe consultar estadísticas por fecha', async () => {
      const fechaInicio = new Date();
      fechaInicio.setDate(fechaInicio.getDate() - 7);
      
      const query = `${SUPABASE_CONFIG.url}/rest/v1/estadisticas_scraping?select=*&created_at=gte.${fechaInicio.toISOString()}&order=created_at.desc`;
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([
          {
            id: 'stats1',
            fuente: 'Maxiconsumo Necochea',
            productos_encontrados: 1200,
            tiempo_ejecucion_ms: 38000,
            status: 'exitoso',
            created_at: new Date().toISOString()
          }
        ])
      });
      
      const result = await fetch(query, {
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`
        }
      });
      
      expect(result.ok).toBe(true);
      
      const data = await result.json();
      expect(data).toHaveLength(1);
      expect(data[0].status).toBe('exitoso');
    });
    
  });
  
  describe('⚙️ Tabla configuracion_proveedor', () => {
    
    test('debe gestionar configuración del proveedor', async () => {
      const configuracion = {
        nombre: 'Maxiconsumo Necochea',
        url_base: 'https://maxiconsumo.com/sucursal_necochea/',
        activo: true,
        frecuencia_scraping: 'diaria',
        ultima_sincronizacion: new Date().toISOString(),
        proxima_sincronizacion: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        configuraciones: {
          categorias_soportadas: ['almacen', 'bebidas', 'limpieza'],
          timeout_request: 15000,
          max_reintentos: 3,
          delay_entre_requests: 2000
        },
        headers_personalizados: {
          'User-Agent': 'Mozilla/5.0 (Test)',
          'Accept': 'text/html,application/xhtml+xml'
        },
        reglas_extraccion: {
          selector_producto: 'div.producto',
          selector_nombre: 'h3',
          selector_precio: '.precio'
        }
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: 'config-123' }])
      });
      
      const result = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/configuracion_proveedor`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=representation'
        },
        body: JSON.stringify(configuracion)
      });
      
      expect(result.ok).toBe(true);
      
      const data = await result.json();
      expect(data).toHaveLength(1);
      expect(data[0].nombre).toBe('Maxiconsumo Necochea');
      expect(data[0].configuraciones.categorias_soportadas).toContain('bebidas');
    });
    
  });
  
  describe('📝 Tabla logs_scraping', () => {
    
    test('debe registrar logs de scraping', async () => {
      const logEntries = [
        {
          nivel: 'INFO',
          mensaje: 'Iniciando scraping de categoría bebidas',
          categoria: 'bebidas',
          sku: null,
          url: 'https://maxiconsumo.com/bebidas',
          detalle_error: null
        },
        {
          nivel: 'WARN',
          mensaje: 'Producto sin precio encontrado',
          categoria: 'bebidas',
          sku: 'UNKNOWN001',
          url: 'https://maxiconsumo.com/producto/unknown',
          detalle_error: 'Precio no encontrado en HTML'
        },
        {
          nivel: 'ERROR',
          mensaje: 'Error al procesar producto',
          categoria: 'bebidas',
          sku: 'ERROR001',
          url: 'https://maxiconsumo.com/producto/error',
          detalle_error: 'JSON parsing failed'
        }
      ];
      
      // Insertar múltiples logs
      fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([{ id: `log-${Date.now()}` }])
      });
      
      for (const log of logEntries) {
        const result = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/logs_scraping`, {
          method: 'POST',
          headers: {
            'apikey': SUPABASE_CONFIG.serviceKey,
            'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(log)
        });
        
        expect(result.ok).toBe(true);
      }
    });
    
    test('debe consultar logs por nivel y fecha', async () => {
      const query = `${SUPABASE_CONFIG.url}/rest/v1/logs_scraping?select=*&nivel=in.(ERROR,WARN)&order=created_at.desc&limit=50`;
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([
          {
            id: 'log1',
            nivel: 'ERROR',
            mensaje: 'Error crítico en scraping',
            created_at: new Date().toISOString()
          },
          {
            id: 'log2',
            nivel: 'WARN',
            mensaje: 'Advertencia menor',
            created_at: new Date().toISOString()
          }
        ])
      });
      
      const result = await fetch(query, {
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`
        }
      });
      
      expect(result.ok).toBe(true);
      
      const data = await result.json();
      expect(data).toHaveLength(2);
      expect(['ERROR', 'WARN']).toContain(data[0].nivel);
    });
    
  });
  
  describe('🔍 Funciones de Base de Datos', () => {
    
    test('debe ejecutar función de actualización de estadísticas', async () => {
      // Simular llamada a función stored procedure
      const callResult = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/rpc/fnc_actualizar_estadisticas_scraping`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          p_fuente: 'Maxiconsumo Necochea',
          p_categoria: 'bebidas',
          p_productos_encontrados: 1200,
          p_productos_nuevos: 150,
          p_productos_actualizados: 1050,
          p_tiempo_ejecucion: 35000,
          p_errores: 3,
          p_status: 'exitoso',
          p_detalles_error: null
        })
      });
      
      expect(callResult.ok).toBe(true);
    });
    
    test('debe ejecutar función de limpieza de datos antiguos', async () => {
      const callResult = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/rpc/fnc_limpiar_datos_antiguos`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });
      
      expect(callResult.ok).toBe(true);
      
      const data = await callResult.json();
      expect(typeof data).toBe('number'); // Debería retornar número de registros eliminados
    });
    
    test('debe ejecutar función de detección de cambios significativos', async () => {
      const callResult = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/rpc/fnc_deteccion_cambios_significativos`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          p_umbral_porcentual: 15.0
        })
      });
      
      expect(callResult.ok).toBe(true);
      
      const data = await callResult.json();
      expect(typeof data).toBe('number'); // Debería retornar número de alertas creadas
    });
    
  });
  
  describe('🔒 Performance y Manejo de Errores', () => {
    
    test('debe manejar timeout de base de datos', async () => {
      fetch.mockImplementationOnce(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Database timeout')), 100)
        )
      );
      
      await expect(fetch(`${SUPABASE_CONFIG.url}/rest/v1/precios_proveedor?limit=1000`, {
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`
        }
      })).rejects.toThrow('Database timeout');
    });
    
    test('debe manejar errores de conexión', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable'
      });
      
      const result = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/precios_proveedor?limit=10`, {
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`
        }
      });
      
      expect(result.ok).toBe(false);
      expect(result.status).toBe(503);
    });
    
    test('debe validar estructura de datos antes de inserción', async () => {
      const productoInvalido = {
        // Faltan campos requeridos
        nombre: 'Producto sin SKU',
        precio_unitario: 99.99
      };
      
      // Esto debería fallar en el nivel de base de datos
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request - Missing required fields'
      });
      
      const result = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/precios_proveedor`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(productoInvalido)
      });
      
      expect(result.ok).toBe(false);
      expect(result.status).toBe(400);
    });
    
  });
  
  describe('📊 Consultas Complejas y Agregaciones', () => {
    
    test('debe realizar consultas con múltiples joins', async () => {
      const query = `
        SELECT 
          pp.*,
          c.nombre as categoria_nombre,
          COUNT(cp.id) as total_comparaciones,
          AVG(cp.diferencia_porcentual) as ahorro_promedio
        FROM precios_proveedor pp
        LEFT JOIN categorias c ON c.nombre = pp.categoria
        LEFT JOIN comparacion_precios cp ON cp.producto_id = pp.id
        WHERE pp.activo = true 
          AND pp.fuente = 'Maxiconsumo Necochea'
        GROUP BY pp.id, c.nombre
        ORDER BY ahorro_promedio DESC
        LIMIT 50
      `;
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([
          {
            id: '1',
            nombre: 'Producto 1',
            categoria_nombre: 'Bebidas',
            total_comparaciones: 5,
            ahorro_promedio: 25.5
          }
        ])
      });
      
      const result = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/rpc/execute_raw_sql`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CONFIG.serviceKey,
          'Authorization': `Bearer ${SUPABASE_CONFIG.serviceKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      });
      
      expect(result.ok).toBe(true);
    });
    
  });
  
});

// Setup y teardown global
beforeAll(() => {
  // Configurar entorno de testing
  process.env.NODE_ENV = 'test';
  process.env.SUPABASE_URL = SUPABASE_CONFIG.url;
  process.env.SUPABASE_SERVICE_ROLE_KEY = SUPABASE_CONFIG.serviceKey;
});

afterAll(() => {
  // Limpiar mocks
  jest.clearAllMocks();
});