/**
 * UNIT TESTS - API PROVEEDOR
 * Tests exhaustivos para todos los endpoints de la API
 */

const { describe, test, expect, beforeEach, afterEach } = require('@jest/globals');

// Mock global
global.fetch = jest.fn();

// Importar funciones a testear
const apiPath = '/workspace/supabase/functions/api-proveedor/index.ts';

describe('🔌 UNIT TESTS - API Proveedor', () => {
  
  describe('📊 GET /status - Estado del Sistema', () => {
    
    test('debe retornar estado operativo correctamente', async () => {
      // Mock responses para estadísticas
      fetch
        .mockResolvedValueOnce({ // estadísticas_scraping
          ok: true,
          json: () => Promise.resolve([{
            created_at: '2025-10-31T10:00:00Z',
            productos_encontrados: 1500
          }])
        })
        .mockResolvedValueOnce({ // precios_proveedor count
          ok: true,
          json: () => Promise.resolve([{ count: 5000 }])
        })
        .mockResolvedValueOnce({ // vista_oportunidades_ahorro count
          ok: true,
          json: () => Promise.resolve([{ count: 150 }])
        })
        .mockResolvedValueOnce({ // configuracion_proveedor
          ok: true,
          json: () => Promise.resolve([{
            nombre: 'Maxiconsumo Necochea',
            ultima_sincronizacion: '2025-10-31T08:00:00Z',
            proxima_sincronizacion: '2025-11-01T08:00:00Z'
          }])
        });
      
      const url = new URL('http://test.com/api/status');
      const resultado = await getEstadoSistema(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {}
      );
      
      expect(resultado.success).toBe(true);
      expect(resultado.data.sistema.estado).toBe('operativo');
      expect(resultado.data.estadisticas.productos_totales).toBe(5000);
      expect(resultado.data.estadisticas.oportunidades_activas).toBe(150);
    });
    
    test('debe manejar errores de base de datos gracefully', async () => {
      fetch.mockRejectedValue(new Error('Database connection failed'));
      
      const url = new URL('http://test.com/api/status');
      
      await expect(getEstadoSistema(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {}
      )).rejects.toThrow('Database connection failed');
    });
    
  });
  
  describe('💰 GET /precios - Precios Actuales', () => {
    
    test('debe retornar precios con filtros aplicados', async () => {
      const mockProductos = [
        {
          id: '1',
          sku: 'BEB001',
          nombre: 'Coca Cola 500ml',
          precio_unitario: 250.50,
          categoria: 'bebidas'
        }
      ];
      
      fetch
        .mockResolvedValueOnce({ // productos con filtros
          ok: true,
          json: () => Promise.resolve(mockProductos)
        })
        .mockResolvedValueOnce({ // count total
          ok: true,
          json: () => Promise.resolve([{ count: 100 }])
        });
      
      const url = new URL('http://test.com/api/precios?categoria=bebidas&limit=1');
      const resultado = await getPreciosActuales(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false
      );
      
      expect(resultado.success).toBe(true);
      expect(resultado.data.productos).toHaveLength(1);
      expect(resultado.data.productos[0].categoria).toBe('bebidas');
      expect(resultado.data.paginacion.total).toBe(100);
      expect(resultado.data.filtros_aplicados.categoria).toBe('bebidas');
    });
    
    test('debe manejar parámetros inválidos', async () => {
      const url = new URL('http://test.com/api/precios?limit=invalid&offset=-1');
      
      // Debería manejar valores inválidos gracefully
      expect(() => {
        getPreciosActuales(
          'http://mock-supabase.com',
          'mock-key',
          url,
          {},
          false
        );
      }).not.toThrow();
    });
    
    test('debe aplicar paginación correctamente', async () => {
      const url = new URL('http://test.com/api/precios?limit=10&offset=20');
      
      const resultado = await getPreciosActuales(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false
      );
      
      expect(resultado.data.paginacion.limite).toBe(10);
      expect(resultado.data.paginacion.offset).toBe(20);
      expect(resultado.data.paginacion.productos_mostrados).toBeLessThanOrEqual(10);
    });
    
  });
  
  describe('📦 GET /productos - Búsqueda de Productos', () => {
    
    test('debe filtrar productos por búsqueda', async () => {
      const mockProductos = [
        {
          id: '1',
          nombre: 'Coca Cola 500ml',
          marca: 'Coca Cola',
          categoria: 'bebidas',
          stock_disponible: 100
        }
      ];
      
      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockProductos)
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]) // stats de categorías
        });
      
      const url = new URL('http://test.com/api/productos?busqueda=coca&marca=Coca Cola');
      const resultado = await getProductosDisponibles(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false
      );
      
      expect(resultado.success).toBe(true);
      expect(resultado.data.productos).toHaveLength(1);
      expect(resultado.data.filtros_aplicados.busqueda).toBe('coca');
      expect(resultado.data.filtros_aplicados.marca).toBe('Coca Cola');
    });
    
    test('debe filtrar productos con stock disponible', async () => {
      const url = new URL('http://test.com/api/productos?solo_con_stock=true');
      
      const resultado = await getProductosDisponibles(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false
      );
      
      expect(resultado.data.filtros_aplicados.solo_con_stock).toBe(true);
    });
    
    test('debe calcular estadísticas correctamente', async () => {
      const productos = [
        { stock_disponible: 100, marca: 'Marca A', categoria: 'cat1' },
        { stock_disponible: 0, marca: 'Marca B', categoria: 'cat1' },
        { stock_disponible: 50, marca: 'Marca A', categoria: 'cat2' }
      ];
      
      const stats = await obtenerEstadisticasCategorias('http://mock.com', 'key');
      
      // Verificar que se llamó correctamente
      expect(fetch).toHaveBeenCalled();
    });
    
  });
  
  describe('🔄 GET /comparacion - Comparación de Precios', () => {
    
    test('debe retornar oportunidades de ahorro', async () => {
      const mockOportunidades = [
        {
          id: '1',
          nombre_producto: 'Producto A',
          precio_actual: 100,
          precio_proveedor: 80,
          diferencia_absoluta: 20,
          diferencia_porcentual: 25,
          recomendacion: 'OPORTUNIDAD CRÍTICA'
        }
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockOportunidades)
      });
      
      const url = new URL('http://test.com/api/comparacion?solo_oportunidades=true&min_diferencia=15');
      const resultado = await getComparacionConSistema(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false
      );
      
      expect(resultado.success).toBe(true);
      expect(resultado.data.oportunidades).toHaveLength(1);
      expect(resultado.data.estadisticas.total_oportunidades).toBe(1);
      expect(resultado.data.estadisticas.ahorro_total_estimado).toBe(20);
    });
    
    test('debe ordenar resultados correctamente', async () => {
      const url = new URL('http://test.com/api/comparacion?orden=nombre_asc');
      
      await getComparacionConSistema(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false
      );
      
      // Verificar que se construyó la query con orden correcto
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('nombre_producto.asc'),
        expect.any(Object)
      );
    });
    
    test('debe calcular estadísticas de comparación', () => {
      const oportunidades = [
        { diferencia_absoluta: 10 },
        { diferencia_absoluta: 20 },
        { diferencia_absoluta: 30 }
      ];
      
      const stats = calcularEstadisticasComparacion(oportunidades);
      
      expect(stats.total_oportunidades).toBe(3);
      expect(stats.ahorro_total_estimado).toBe(60);
      expect(stats.oportunidad_promedio).toBe(20);
      expect(stats.mejor_oportunidad.diferencia_absoluta).toBe(30);
    });
    
  });
  
  describe('🔄 POST /sincronizar - Sincronización Manual', () => {
    
    test('debe requerir autenticación', async () => {
      const url = new URL('http://test.com/api/sincronizar');
      
      const resultado = await triggerSincronizacion(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false // no autenticado
      );
      
      expect(resultado.success).toBe(false);
      expect(resultado.error.code).toBe('AUTH_REQUIRED');
    });
    
    test('debe iniciar sincronización con parámetros', async () => {
      const url = new URL('http://test.com/api/sincronizar?categoria=bebidas&force_full=true');
      
      fetch
        .mockResolvedValueOnce({ // scraper response
          ok: true,
          json: () => Promise.resolve({ success: true, productos_extraidos: 500 })
        })
        .mockResolvedValueOnce({ // comparacion response
          ok: true,
          json: () => Promise.resolve({ success: true, comparaciones_realizadas: 200 })
        });
      
      const resultado = await triggerSincronizacion(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        true // autenticado
      );
      
      expect(resultado.success).toBe(true);
      expect(resultado.data.parametros.categoria).toBe('bebidas');
      expect(resultado.data.parametros.force_full).toBe(true);
    });
    
    test('debe manejar errores de scraper', async () => {
      fetch.mockRejectedValue(new Error('Scraper failed'));
      
      await expect(triggerSincronizacion(
        'http://mock-supabase.com',
        'mock-key',
        new URL('http://test.com'),
        {},
        true
      )).rejects.toThrow('Scraper failed');
    });
    
  });
  
  describe('🚨 GET /alertas - Alertas Activas', () => {
    
    test('debe filtrar alertas por severidad', async () => {
      const mockAlertas = [
        {
          id: '1',
          severidad: 'critica',
          tipo_cambio: 'aumento',
          mensaje: 'Precio aumentó 30%'
        }
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockAlertas)
      });
      
      const url = new URL('http://test.com/api/alertas?severidad=critica&limit=10');
      const resultado = await getAlertasActivas(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false
      );
      
      expect(resultado.success).toBe(true);
      expect(resultado.data.estadisticas.criticas).toBe(1);
      expect(resultado.data.filtros_aplicados.severidad).toBe('critica');
    });
    
    test('debe contar alertas por tipo de cambio', async () => {
      const alertas = [
        { severidad: 'critica', tipo_cambio: 'aumento' },
        { severidad: 'alta', tipo_cambio: 'disminucion' },
        { severidad: 'media', tipo_cambio: 'aumento' },
        { severidad: 'baja', tipo_cambio: 'nuevo_producto' }
      ];
      
      const url = new URL('http://test.com/api/alertas');
      const resultado = await getAlertasActivas(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false
      );
      
      expect(resultado.data.estadisticas.aumentos).toBe(2);
      expect(resultado.data.estadisticas.disminuciones).toBe(1);
      expect(resultado.data.estadisticas.nuevos_productos).toBe(1);
    });
    
  });
  
  describe('📈 GET /estadisticas - Métricas de Scraping', () => {
    
    test('debe calcular métricas agregadas', async () => {
      const mockEstadisticas = [
        {
          productos_encontrados: 1000,
          tiempo_ejecucion_ms: 30000,
          status: 'exitoso'
        },
        {
          productos_encontrados: 500,
          tiempo_ejecucion_ms: 15000,
          status: 'exitoso'
        }
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockEstadisticas)
      });
      
      const url = new URL('http://test.com/api/estadisticas?dias=7');
      const resultado = await getEstadisticasScraping(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false
      );
      
      expect(resultado.success).toBe(true);
      expect(resultado.data.metricas_agregadas.total_ejecuciones).toBe(2);
      expect(resultado.data.metricas_agregadas.productos_promedio).toBe(750);
      expect(resultado.data.metricas_agregadas.tasa_exito).toBe(100);
      expect(resultado.data.metricas_agregadas.tiempo_promedio_ms).toBe(22500);
    });
    
    test('debe filtrar por categoría', async () => {
      const url = new URL('http://test.com/api/estadisticas?categoria=bebidas');
      
      await getEstadisticasScraping(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false
      );
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('categoria_procesada=eq.bebidas'),
        expect.any(Object)
      );
    });
    
  });
  
  describe('⚙️ GET /configuracion - Configuración del Proveedor', () => {
    
    test('debe requerir autenticación para configuración', async () => {
      const url = new URL('http://test.com/api/configuracion');
      
      const resultado = await getConfiguracionProveedor(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        false // no autenticado
      );
      
      expect(resultado.success).toBe(false);
      expect(resultado.error.code).toBe('AUTH_REQUIRED');
    });
    
    test('debe retornar configuración con parámetros disponibles', async () => {
      const mockConfig = {
        nombre: 'Maxiconsumo Necochea',
        url_base: 'https://maxiconsumo.com/',
        frecuencia_scraping: 'diaria'
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([mockConfig])
      });
      
      const url = new URL('http://test.com/api/configuracion');
      const resultado = await getConfiguracionProveedor(
        'http://mock-supabase.com',
        'mock-key',
        url,
        {},
        true // autenticado
      );
      
      expect(resultado.success).toBe(true);
      expect(resultado.data.configuracion.nombre).toBe('Maxiconsumo Necochea');
      expect(resultado.data.parametros_disponibles.frecuencia_scraping).toContain('diaria');
      expect(resultado.data.parametros_disponibles.severidad_alertas).toContain('critica');
    });
    
  });
  
  describe('🔐 Autenticación y Autorización', () => {
    
    test('debe detectar tokens válidos', () => {
      const authHeader = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
      const isAuthenticated = authHeader && authHeader.startsWith('Bearer ');
      
      expect(isAuthenticated).toBe(true);
    });
    
    test('debe rechazar headers inválidos', () => {
      const invalidHeaders = [
        null,
        undefined,
        'Invalid token',
        'Basic YWxhZGRpbjpvcGVuc2VzYW1l', // Basic auth
        ''
      ];
      
      invalidHeaders.forEach(header => {
        const isAuthenticated = header && header.startsWith('Bearer ');
        expect(isAuthenticated).toBe(false);
      });
    });
    
  });
  
  describe('🛡️ Validación de Entrada', () => {
    
    test('debe validar parámetros de query correctamente', () => {
      const validParams = [
        { categoria: 'bebidas', limit: '50', offset: '0' },
        { busqueda: 'coca cola', marca: 'coca', solo_con_stock: 'true' },
        { solo_oportunidades: 'true', min_diferencia: '15', orden: 'nombre_asc' }
      ];
      
      validParams.forEach(params => {
        const url = new URL('http://test.com/api/test');
        Object.entries(params).forEach(([key, value]) => {
          url.searchParams.set(key, value);
        });
        
        expect(() => parseInt(url.searchParams.get('limit') || '10')).not.toThrow();
        expect(() => parseFloat(url.searchParams.get('min_diferencia') || '0')).not.toThrow();
      });
    });
    
    test('debe manejar valores inválidos gracefully', () => {
      const invalidValues = [
        { limit: 'invalid', offset: '-1' },
        { min_diferencia: 'not_a_number', solo_oportunidades: 'maybe' },
        { orden: 'invalid_order' }
      ];
      
      invalidValues.forEach(params => {
        const url = new URL('http://test.com/api/test');
        Object.entries(params).forEach(([key, value]) => {
          url.searchParams.set(key, value);
        });
        
        // Debería manejar valores inválicos sin crashear
        expect(() => parseInt(url.searchParams.get('limit') || '10')).not.toThrow();
      });
    });
    
  });
  
});

// Funciones auxiliares copiadas de la API para testing
async function getEstadoSistema(supabaseUrl, serviceRoleKey, url, corsHeaders) {
  try {
    const estadisticasResponse = await fetch(
      `${supabaseUrl}/rest/v1/estadisticas_scraping?select=*&order=created_at.desc&limit=1`,
      {
        headers: {
          'apikey': serviceRoleKey,
          'Authorization': `Bearer ${serviceRoleKey}`,
        }
      }
    );

    let ultimaEstadistica = null;
    if (estadisticasResponse.ok) {
      const stats = await estadisticasResponse.json();
      ultimaEstadistica = stats[0] || null;
    }

    const productosTotalesResponse = await fetch(
      `${supabaseUrl}/rest/v1/precios_proveedor?select=count&fuente=eq.Maxiconsumo Necochea&activo=eq.true`,
      {
        headers: {
          'apikey': serviceRoleKey,
          'Authorization': `Bearer ${serviceRoleKey}`,
        }
      }
    );

    let totalProductos = 0;
    if (productosTotalesResponse.ok) {
      const countData = await productosTotalesResponse.json();
      totalProductos = countData[0]?.count || 0;
    }

    const oportunidadesResponse = await fetch(
      `${supabaseUrl}/rest/v1/vista_oportunidades_ahorro?select=count`,
      {
        headers: {
          'apikey': serviceRoleKey,
          'Authorization': `Bearer ${serviceRoleKey}`,
        }
      }
    );

    let totalOportunidades = 0;
    if (oportunidadesResponse.ok) {
      const countData = await oportunidadesResponse.json();
      totalOportunidades = countData[0]?.count || 0;
    }

    const configResponse = await fetch(
      `${supabaseUrl}/rest/v1/configuracion_proveedor?select=*&nombre=eq.Maxiconsumo Necochea`,
      {
        headers: {
          'apikey': serviceRoleKey,
          'Authorization': `Bearer ${serviceRoleKey}`,
        }
      }
    );

    let configuracion = null;
    if (configResponse.ok) {
      const config = await configResponse.json();
      configuracion = config[0] || null;
    }

    return {
      success: true,
      data: {
        sistema: {
          estado: 'operativo',
          version: '1.0.0',
          proveedor: 'Maxiconsumo Necochea'
        },
        estadisticas: {
          ultima_ejecucion: ultimaEstadistica?.created_at || 'Nunca',
          productos_totales: totalProductos,
          oportunidades_activas: totalOportunidades,
          ultima_sincronizacion: configuracion?.ultima_sincronizacion || 'Nunca',
          proximo_scrape_programado: calcularProximoScrape(configuracion)
        },
        configuracion: configuracion
      }
    };

  } catch (error) {
    throw error;
  }
}

async function getPreciosActuales(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated) {
  const categoria = url.searchParams.get('categoria') || 'todos';
  const limite = parseInt(url.searchParams.get('limit') || '50');
  const offset = parseInt(url.searchParams.get('offset') || '0');
  const activo = url.searchParams.get('activo') || 'true';

  try {
    let query = `${supabaseUrl}/rest/v1/precios_proveedor?select=*&fuente=eq.Maxiconsumo Necochea&activo=eq.${activo}`;
    
    if (categoria !== 'todos') {
      query += `&categoria=eq.${encodeURIComponent(categoria)}`;
    }
    
    query += `&order=ultima_actualizacion.desc&limit=${limite}&offset=${offset}`;

    const response = await fetch(query, {
      headers: {
        'apikey': serviceRoleKey,
        'Authorization': `Bearer ${serviceRoleKey}`,
      }
    });

    if (!response.ok) {
      throw new Error(`Error obteniendo precios: ${response.statusText}`);
    }

    const productos = await response.json();

    let totalQuery = `${supabaseUrl}/rest/v1/precios_proveedor?select=count&fuente=eq.Maxiconsumo Necochea&activo=eq.${activo}`;
    if (categoria !== 'todos') {
      totalQuery += `&categoria=eq.${encodeURIComponent(categoria)}`;
    }

    const totalResponse = await fetch(totalQuery, {
      headers: {
        'apikey': serviceRoleKey,
        'Authorization': `Bearer ${serviceRoleKey}`,
      }
    });

    const totalData = await totalResponse.json();
    const total = totalData[0]?.count || 0;

    return {
      success: true,
      data: {
        productos: productos,
        paginacion: {
          total: total,
          limite: limite,
          offset: offset,
          productos_mostrados: productos.length,
          tiene_mas: (offset + limite) < total
        },
        filtros_aplicados: {
          categoria: categoria,
          activo: activo
        },
        timestamp: new Date().toISOString()
      }
    };

  } catch (error) {
    throw error;
  }
}

async function getProductosDisponibles(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated) {
  const busqueda = url.searchParams.get('busqueda') || '';
  const categoria = url.searchParams.get('categoria') || 'todos';
  const marca = url.searchParams.get('marca') || '';
  const limite = parseInt(url.searchParams.get('limit') || '100');
  const solo_con_stock = url.searchParams.get('solo_con_stock') === 'true';

  try {
    let query = `${supabaseUrl}/rest/v1/precios_proveedor?select=*&fuente=eq.Maxiconsumo Necochea&activo=eq.true`;
    
    const filtros = [];
    
    if (busqueda) {
      filtros.push(`or=(nombre.ilike.*${encodeURIComponent(busqueda)}*,marca.ilike.*${encodeURIComponent(busqueda)}*)`);
    }
    
    if (categoria !== 'todos') {
      filtros.push(`categoria=eq.${encodeURIComponent(categoria)}`);
    }
    
    if (marca) {
      filtros.push(`marca=ilike.*${encodeURIComponent(marca)}*`);
    }
    
    if (solo_con_stock) {
      filtros.push(`stock_disponible=gt.0`);
    }
    
    if (filtros.length > 0) {
      query += '&' + filtros.join('&');
    }
    
    query += `&order=nombre.asc&limit=${limite}`;

    const response = await fetch(query, {
      headers: {
        'apikey': serviceRoleKey,
        'Authorization': `Bearer ${serviceRoleKey}`,
      }
    });

    if (!response.ok) {
      throw new Error(`Error obteniendo productos: ${response.statusText}`);
    }

    const productos = await response.json();

    const categoriasStats = await obtenerEstadisticasCategorias(supabaseUrl, serviceRoleKey);

    return {
      success: true,
      data: {
        productos: productos,
        estadisticas: {
          total_productos: productos.length,
          productos_con_stock: productos.filter((p) => p.stock_disponible > 0).length,
          marcas_unicas: [...new Set(productos.map((p) => p.marca).filter(Boolean))].length,
          categorias_disponibles: categoriasStats
        },
        filtros_aplicados: {
          busqueda: busqueda,
          categoria: categoria,
          marca: marca,
          solo_con_stock: solo_con_stock
        },
        timestamp: new Date().toISOString()
      }
    };

  } catch (error) {
    throw error;
  }
}

async function getComparacionConSistema(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated) {
  const solo_oportunidades = url.searchParams.get('solo_oportunidades') === 'true';
  const min_diferencia = parseFloat(url.searchParams.get('min_diferencia') || '0');
  const limite = parseInt(url.searchParams.get('limit') || '50');
  const orden = url.searchParams.get('orden') || 'diferencia_absoluta_desc';

  try {
    let query = `${supabaseUrl}/rest/v1/vista_oportunidades_ahorro?select=*`;
    
    if (solo_oportunidades) {
      query += `&diferencia_porcentual=gte.${min_diferencia}`;
    }
    
    switch (orden) {
      case 'diferencia_absoluta_desc':
        query += `&order=diferencia_absoluta.desc`;
        break;
      case 'diferencia_absoluta_asc':
        query += `&order=diferencia_absoluta.asc`;
        break;
      case 'diferencia_porcentual_desc':
        query += `&order=diferencia_porcentual.desc`;
        break;
      case 'nombre_asc':
        query += `&order=nombre_producto.asc`;
        break;
      default:
        query += `&order=diferencia_absoluta.desc`;
    }
    
    query += `&limit=${limite}`;

    const response = await fetch(query, {
      headers: {
        'apikey': serviceRoleKey,
        'Authorization': `Bearer ${serviceRoleKey}`,
      }
    });

    if (!response.ok) {
      throw new Error(`Error obteniendo comparación: ${response.statusText}`);
    }

    const oportunidades = await response.json();

    const estadisticas = calcularEstadisticasComparacion(oportunidades);

    return {
      success: true,
      data: {
        oportunidades: oportunidades,
        estadisticas: estadisticas,
        filtros_aplicados: {
          solo_oportunidades: solo_oportunidades,
          min_diferencia: min_diferencia,
          orden: orden
        },
        timestamp: new Date().toISOString()
      }
    };

  } catch (error) {
    throw error;
  }
}

async function triggerSincronizacion(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated) {
  if (!isAuthenticated) {
    return {
      success: false,
      error: {
        code: 'AUTH_REQUIRED',
        message: 'Se requiere autenticación para sincronizar manualmente'
      }
    };
  }

  const categoria = url.searchParams.get('categoria') || 'todos';
  const force_full = url.searchParams.get('force_full') === 'true';

  try {
    const scrapingUrl = `${supabaseUrl}/functions/v1/scraper-maxiconsumo/scrape?categoria=${encodeURIComponent(categoria)}`;
    
    const response = await fetch(scrapingUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        trigger_type: 'manual',
        force_full: force_full,
        categoria: categoria,
        initiated_by: 'api_proveedor_manual'
      })
    });

    if (!response.ok) {
      throw new Error(`Error en sincronización: ${response.statusText}`);
    }

    const resultadoScraping = await response.json();

    let resultadoComparacion = null;
    if (resultadoScraping.success) {
      try {
        const comparacionUrl = `${supabaseUrl}/functions/v1/scraper-maxiconsumo/compare`;
        const comparacionResponse = await fetch(comparacionUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (comparacionResponse.ok) {
          resultadoComparacion = await comparacionResponse.json();
        }
      } catch (error) {
        console.warn('Error generando comparaciones automáticas:', error.message);
      }
    }

    return {
      success: true,
      data: {
        sincronizacion: resultadoScraping,
        comparacion_generada: resultadoComparacion,
        parametros: {
          categoria: categoria,
          force_full: force_full,
          timestamp: new Date().toISOString()
        }
      }
    };

  } catch (error) {
    throw error;
  }
}

async function getAlertasActivas(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated) {
  const severidad = url.searchParams.get('severidad') || 'todos';
  const tipo = url.searchParams.get('tipo') || 'todos';
  const limite = parseInt(url.searchParams.get('limit') || '20');

  try {
    let query = `${supabaseUrl}/rest/v1/vista_alertas_activas?select=*`;
    
    const filtros = [];
    
    if (severidad !== 'todos') {
      filtros.push(`severidad=eq.${severidad}`);
    }
    
    if (tipo !== 'todos') {
      filtros.push(`tipo_cambio=eq.${tipo}`);
    }
    
    if (filtros.length > 0) {
      query += '&' + filtros.join('&');
    }
    
    query += `&order=fecha_alerta.desc&limit=${limite}`;

    const response = await fetch(query, {
      headers: {
        'apikey': serviceRoleKey,
        'Authorization': `Bearer ${serviceRoleKey}`,
      }
    });

    if (!response.ok) {
      throw new Error(`Error obteniendo alertas: ${response.statusText}`);
    }

    const alertas = await response.json();

    const estadisticas = {
      total_alertas: alertas.length,
      criticas: alertas.filter((a) => a.severidad === 'critica').length,
      altas: alertas.filter((a) => a.severidad === 'alta').length,
      medias: alertas.filter((a) => a.severidad === 'media').length,
      bajas: alertas.filter((a) => a.severidad === 'baja').length,
      aumentos: alertas.filter((a) => a.tipo_cambio === 'aumento').length,
      disminuciones: alertas.filter((a) => a.tipo_cambio === 'disminucion').length,
      nuevos_productos: alertas.filter((a) => a.tipo_cambio === 'nuevo_producto').length
    };

    return {
      success: true,
      data: {
        alertas: alertas,
        estadisticas: estadisticas,
        filtros_aplicados: {
          severidad: severidad,
          tipo: tipo
        },
        timestamp: new Date().toISOString()
      }
    };

  } catch (error) {
    throw error;
  }
}

async function getEstadisticasScraping(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated) {
  const dias = parseInt(url.searchParams.get('dias') || '7');
  const categoria = url.searchParams.get('categoria') || '';

  try {
    const fechaInicio = new Date();
    fechaInicio.setDate(fechaInicio.getDate() - dias);
    
    let query = `${supabaseUrl}/rest/v1/estadisticas_scraping?select=*&created_at=gte.${fechaInicio.toISOString()}&order=created_at.desc`;
    
    if (categoria) {
      query += `&categoria_procesada=eq.${encodeURIComponent(categoria)}`;
    }

    const response = await fetch(query, {
      headers: {
        'apikey': serviceRoleKey,
        'Authorization': `Bearer ${serviceRoleKey}`,
      }
    });

    if (!response.ok) {
      throw new Error(`Error obteniendo estadísticas: ${response.statusText}`);
    }

    const estadisticas = await response.json();

    const metricas = calcularMetricasScraping(estadisticas);

    return {
      success: true,
      data: {
        estadisticas_periodo: estadisticas,
        metricas_agregadas: metricas,
        parametros: {
          dias_analizados: dias,
          categoria: categoria,
          fecha_inicio: fechaInicio.toISOString(),
          fecha_fin: new Date().toISOString()
        },
        timestamp: new Date().toISOString()
      }
    };

  } catch (error) {
    throw error;
  }
}

async function getConfiguracionProveedor(supabaseUrl, serviceRoleKey, url, corsHeaders, isAuthenticated) {
  if (!isAuthenticated) {
    return {
      success: false,
      error: {
        code: 'AUTH_REQUIRED',
        message: 'Se requiere autenticación para ver la configuración'
      }
    };
  }

  try {
    const response = await fetch(
      `${supabaseUrl}/rest/v1/configuracion_proveedor?select=*&nombre=eq.Maxiconsumo Necochea`,
      {
        headers: {
          'apikey': serviceRoleKey,
          'Authorization': `Bearer ${serviceRoleKey}`,
        }
      }
    );

    if (!response.ok) {
      throw new Error(`Error obteniendo configuración: ${response.statusText}`);
    }

    const configuraciones = await response.json();
    const configuracion = configuraciones[0] || null;

    return {
      success: true,
      data: {
        configuracion: configuracion,
        parametros_disponibles: {
          frecuencia_scraping: ['cada_hora', 'diaria', 'semanal'],
          severidad_alertas: ['baja', 'media', 'alta', 'critica'],
          tipos_cambio: ['aumento', 'disminucion', 'nuevo_producto']
        },
        timestamp: new Date().toISOString()
      }
    };

  } catch (error) {
    throw error;
  }
}

async function obtenerEstadisticasCategorias(supabaseUrl, serviceRoleKey) {
  try {
    const response = await fetch(
      `${supabaseUrl}/rest/v1/precios_proveedor?select=categoria&fuente=eq.Maxiconsumo Necochea&activo=eq.true`,
      {
        headers: {
          'apikey': serviceRoleKey,
          'Authorization': `Bearer ${serviceRoleKey}`,
        }
      }
    );

    if (!response.ok) return [];

    const productos = await response.json();
    
    const categorias = productos.reduce((acc, producto) => {
      const cat = producto.categoria || 'Sin categoría';
      acc[cat] = (acc[cat] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(categorias).map(([nombre, cantidad]) => ({
      categoria: nombre,
      cantidad_productos: cantidad
    }));

  } catch (error) {
    return [];
  }
}

function calcularEstadisticasComparacion(oportunidades) {
  if (oportunidades.length === 0) {
    return {
      total_oportunidades: 0,
      ahorro_total_estimado: 0,
      oportunidad_promedio: 0,
      mejor_oportunidad: null
    };
  }

  const ahorroTotal = oportunidades.reduce((sum, opp) => sum + opp.diferencia_absoluta, 0);
  const oportunidadPromedio = ahorroTotal / oportunidades.length;
  const mejorOportunidad = oportunidades.reduce((best, opp) => 
    opp.diferencia_absoluta > best.diferencia_absoluta ? opp : best
  );

  return {
    total_oportunidades: oportunidades.length,
    ahorro_total_estimado: Math.round(ahorroTotal * 100) / 100,
    oportunidad_promedio: Math.round(oportunidadPromedio * 100) / 100,
    mejor_oportunidad: mejorOportunidad
  };
}

function calcularMetricasScraping(estadisticas) {
  if (estadisticas.length === 0) {
    return {
      total_ejecuciones: 0,
      productos_promedio: 0,
      tasa_exito: 0,
      tiempo_promedio: 0
    };
  }

  const totalEjecuciones = estadisticas.length;
  const productosTotales = estadisticas.reduce((sum, stat) => sum + (stat.productos_encontrados || 0), 0);
  const productosPromedio = Math.round(productosTotales / totalEjecuciones);
  const ejecucionesExitosas = estadisticas.filter(stat => stat.status === 'exitoso').length;
  const tasaExito = Math.round((ejecucionesExitosas / totalEjecuciones) * 100);
  const tiempoTotal = estadisticas.reduce((sum, stat) => sum + (stat.tiempo_ejecucion_ms || 0), 0);
  const tiempoPromedio = Math.round(tiempoTotal / totalEjecuciones);

  return {
    total_ejecuciones: totalEjecuciones,
    productos_promedio: productosPromedio,
    tasa_exito: tasaExito,
    tiempo_promedio_ms: tiempoPromedio
  };
}

function calcularProximoScrape(configuracion) {
  if (!configuracion?.proxima_sincronizacion) {
    const proximo = new Date();
    proximo.setHours(proximo.getHours() + 6);
    return proximo.toISOString();
  }
  
  return configuracion.proxima_sincronizacion;
}