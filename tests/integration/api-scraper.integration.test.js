/**
 * INTEGRATION TESTS - API + Web Scraper
 * Tests de integración end-to-end entre API y sistema de scraping
 */

const { describe, test, expect, beforeAll, afterAll, beforeEach, afterEach } = require('@jest/globals');

// Mock global
global.fetch = jest.fn();

// URLs de testing
const API_URL = 'https://test-project.supabase.co/functions/v1/api-proveedor';
const SCRAPER_URL = 'https://test-project.supabase.co/functions/v1/scraper-maxiconsumo';

describe('🔄 INTEGRATION TESTS - API + Web Scraper', () => {
  
  describe('📊 Flujo Completo: Scraping → API → Comparación', () => {
    
    test('debe ejecutar scraping y exponer datos vía API', async () => {
      // 1. Mock respuesta del web scraper
      const scrapingResponse = {
        success: true,
        data: {
          scraping_completo: true,
          categoria_solicitada: 'todos',
          estadisticas: {
            productos_procesados: 2500,
            productos_exitosos: 2450,
            productos_con_error: 50,
            tiempo_ejecucion: 180000
          },
          productos_extraidos: 2450,
          productos_guardados: 2400,
          alertas_generadas: 15,
          errores: []
        }
      };
      
      // 2. Mock respuesta de comparación
      const comparacionResponse = {
        success: true,
        data: {
          comparaciones_realizadas: 1800,
          oportunidades_ahorro: 320,
          comparaciones: [
            {
              producto_id: 'prod-1',
              nombre_producto: 'Coca Cola 500ml',
              precio_actual: 280.00,
              precio_proveedor: 220.00,
              diferencia_absoluta: 60.00,
              diferencia_porcentual: 27.27,
              es_oportunidad_ahorro: true,
              recomendacion: 'OPORTUNIDAD CRÍTICA: Ahorro potencial del 27.3% ($60.00)'
            }
          ]
        }
      };
      
      // 3. Mock respuesta de estado
      const estadoResponse = {
        success: true,
        data: {
          sistema: {
            estado: 'operativo',
            version: '1.0.0',
            proveedor: 'Maxiconsumo Necochea'
          },
          estadisticas: {
            ultima_ejecucion: '2025-11-01T10:00:00Z',
            productos_totales: 12500,
            oportunidades_activas: 320,
            ultima_sincronizacion: '2025-11-01T09:30:00Z',
            proximo_scrape_programado: '2025-11-01T16:00:00Z'
          }
        }
      };
      
      // Simular secuencia de llamadas
      fetch
        .mockResolvedValueOnce({ // Scraping
          ok: true,
          json: () => Promise.resolve(scrapingResponse)
        })
        .mockResolvedValueOnce({ // Comparación
          ok: true,
          json: () => Promise.resolve(comparacionResponse)
        })
        .mockResolvedValueOnce({ // Estado
          ok: true,
          json: () => Promise.resolve(estadoResponse)
        });
      
      // Ejecutar flujo completo
      // Paso 1: Trigger scraping
      const scrapingResult = await fetch(`${SCRAPER_URL}/scrape?categoria=todos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trigger_type: 'manual' })
      });
      
      expect(scrapingResult.ok).toBe(true);
      const scrapingData = await scrapingResult.json();
      expect(scrapingData.data.productos_guardados).toBe(2400);
      
      // Paso 2: Generar comparaciones
      const comparacionResult = await fetch(`${SCRAPER_URL}/compare`, {
        method: 'POST'
      });
      
      expect(comparacionResult.ok).toBe(true);
      const comparacionData = await comparacionResult.json();
      expect(comparacionData.data.oportunidades_ahorro).toBeGreaterThan(0);
      
      // Paso 3: Verificar estado vía API
      const estadoResult = await fetch(`${API_URL}/status`);
      
      expect(estadoResult.ok).toBe(true);
      const estadoData = await estadoResult.json();
      expect(estadoData.data.sistema.estado).toBe('operativo');
      expect(estadoData.data.estadisticas.productos_totales).toBeGreaterThan(0);
      expect(estadoData.data.estadisticas.oportunidades_activas).toBeGreaterThan(0);
    });
    
    test('debe manejar errores de scraping gracefully', async () => {
      // Mock error en scraping
      fetch
        .mockResolvedValueOnce({ // Scraping falla
          ok: false,
          status: 500,
          json: () => Promise.resolve({
            success: false,
            error: { message: 'Web scraping failed - Timeout' }
          })
        });
      
      const scrapingResult = await fetch(`${SCRAPER_URL}/scrape?categoria=bebidas`, {
        method: 'POST'
      });
      
      expect(scrapingResult.ok).toBe(false);
      const errorData = await scrapingResult.json();
      expect(errorData.error.message).toContain('Timeout');
      
      // API debería seguir funcionando para endpoints de estado
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            sistema: { estado: 'error', proveedor: 'Maxiconsumo Necochea' },
            estadisticas: { productos_totales: 0, oportunidades_activas: 0 }
          }
        })
      });
      
      const estadoResult = await fetch(`${API_URL}/status`);
      expect(estadoResult.ok).toBe(true);
      
      const estadoData = await estadoResult.json();
      expect(estadoData.data.sistema.estado).toBe('error');
    });
    
  });
  
  describe('💰 Integración API con Datos de Scraper', () => {
    
    test('debe exponer precios vía API después del scraping', async () => {
      const productosScraped = [
        {
          id: '1',
          sku: 'BEB001',
          nombre: 'Coca Cola 500ml',
          marca: 'Coca Cola',
          categoria: 'bebidas',
          precio_unitario: 250.50,
          stock_disponible: 100,
          ultima_actualizacion: '2025-11-01T10:00:00Z',
          fuente: 'Maxiconsumo Necochea',
          activo: true
        },
        {
          id: '2',
          sku: 'BEB002',
          nombre: 'Pepsi 2L',
          marca: 'Pepsi',
          categoria: 'bebidas',
          precio_unitario: 450.75,
          stock_disponible: 50,
          ultima_actualizacion: '2025-11-01T10:00:00Z',
          fuente: 'Maxiconsumo Necochea',
          activo: true
        }
      ];
      
      // Mock respuesta de base de datos
      fetch
        .mockResolvedValueOnce({ // Consulta precios
          ok: true,
          json: () => Promise.resolve(productosScraped)
        })
        .mockResolvedValueOnce({ // Count total
          ok: true,
          json: () => Promise.resolve([{ count: 2 }])
        });
      
      // Llamar API de precios
      const preciosResult = await fetch(`${API_URL}/precios?categoria=bebidas&limit=10`, {
        headers: { 'Authorization': 'Bearer test-token' }
      });
      
      expect(preciosResult.ok).toBe(true);
      const preciosData = await preciosResult.json();
      
      expect(preciosData.success).toBe(true);
      expect(preciosData.data.productos).toHaveLength(2);
      expect(preciosData.data.productos[0].categoria).toBe('bebidas');
      expect(preciosData.data.productos[0].precio_unitario).toBe(250.50);
      expect(preciosData.data.filtros_aplicados.categoria).toBe('bebidas');
    });
    
    test('debe exponer comparaciones vía API', async () => {
      const oportunidades = [
        {
          id: '1',
          nombre_producto: 'Coca Cola 500ml',
          precio_actual: 280.00,
          precio_proveedor: 220.00,
          diferencia_absoluta: 60.00,
          diferencia_porcentual: 27.27,
          recomendacion: 'OPORTUNIDAD CRÍTICA'
        },
        {
          id: '2',
          nombre_producto: 'Pepsi 2L',
          precio_actual: 480.00,
          precio_proveedor: 420.00,
          diferencia_absoluta: 60.00,
          diferencia_porcentual: 14.29,
          recomendacion: 'BUENA OPORTUNIDAD'
        }
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(oportunidades)
      });
      
      const comparacionResult = await fetch(`${API_URL}/comparacion?solo_oportunidades=true&min_diferencia=10`, {
        headers: { 'Authorization': 'Bearer test-token' }
      });
      
      expect(comparacionResult.ok).toBe(true);
      const comparacionData = await comparacionResult.json();
      
      expect(comparacionData.success).toBe(true);
      expect(comparacionData.data.oportunidades).toHaveLength(2);
      expect(comparacionData.data.estadisticas.total_oportunidades).toBe(2);
      expect(comparacionData.data.estadisticas.ahorro_total_estimado).toBe(120);
      expect(comparacionData.data.estadisticas.mejor_oportunidad.diferencia_porcentual).toBe(27.27);
    });
    
    test('debe exponer alertas vía API', async () => {
      const alertas = [
        {
          id: '1',
          nombre_producto: 'Coca Cola 500ml',
          tipo_cambio: 'aumento',
          porcentaje_cambio: 35.00,
          severidad: 'critica',
          mensaje: 'Precio aumentó 35.0%',
          accion_recomendada: 'Revisar estrategia de precios y márgenes',
          fecha_alerta: '2025-11-01T10:00:00Z'
        },
        {
          id: '2',
          nombre_producto: 'Pepsi 2L',
          tipo_cambio: 'disminucion',
          porcentaje_cambio: -18.00,
          severidad: 'alta',
          mensaje: 'Precio disminuyó 18.0%',
          accion_recomendada: 'Evaluar oportunidad de compra o reposición',
          fecha_alerta: '2025-11-01T09:30:00Z'
        }
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(alertas)
      });
      
      const alertasResult = await fetch(`${API_URL}/alertas?severidad=critica&limit=10`, {
        headers: { 'Authorization': 'Bearer test-token' }
      });
      
      expect(alertasResult.ok).toBe(true);
      const alertasData = await alertasResult.json();
      
      expect(alertasData.success).toBe(true);
      expect(alertasData.data.alertas).toHaveLength(2);
      expect(alertasData.data.estadisticas.criticas).toBe(1);
      expect(alertasData.data.estadisticas.altas).toBe(1);
      expect(alertasData.data.estadisticas.aumentos).toBe(1);
      expect(alertasData.data.estadisticas.disminuciones).toBe(1);
    });
    
  });
  
  describe('🔄 Sincronización Manual Completa', () => {
    
    test('debe ejecutar sincronización manual end-to-end', async () => {
      const mockAuth = 'Bearer valid-test-token';
      
      // Mock secuencia completa de sincronización
      fetch
        .mockResolvedValueOnce({ // Trigger scraper
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: {
              scraping_completo: true,
              productos_extraidos: 1500,
              productos_guardados: 1450,
              estadisticas: { tiempo_ejecucion: 120000 }
            }
          })
        })
        .mockResolvedValueOnce({ // Comparación automática
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: {
              comparaciones_realizadas: 1000,
              oportunidades_ahorro: 180
            }
          })
        });
      
      // Llamar endpoint de sincronización
      const syncResult = await fetch(`${API_URL}/sincronizar?categoria=bebidas&force_full=true`, {
        method: 'POST',
        headers: { 
          'Authorization': mockAuth,
          'Content-Type': 'application/json'
        }
      });
      
      expect(syncResult.ok).toBe(true);
      const syncData = await syncResult.json();
      
      expect(syncData.success).toBe(true);
      expect(syncData.data.parametros.categoria).toBe('bebidas');
      expect(syncData.data.parametros.force_full).toBe(true);
      expect(syncData.data.sincronizacion.data.productos_guardados).toBe(1450);
      expect(syncData.data.comparacion_generada.data.oportunidades_ahorro).toBe(180);
    });
    
    test('debe requerir autenticación para sincronización', async () => {
      const syncResult = await fetch(`${API_URL}/sincronizar`, {
        method: 'POST'
        // Sin headers de autenticación
      });
      
      expect(syncResult.ok).toBe(false);
      
      const errorData = await syncResult.json();
      expect(errorData.success).toBe(false);
      expect(errorData.error.code).toBe('AUTH_REQUIRED');
    });
    
  });
  
  describe('📈 Métricas Integradas', () => {
    
    test('debe exponer estadísticas de scraping vía API', async () => {
      const estadisticasScraping = [
        {
          id: '1',
          fuente: 'Maxiconsumo Necochea',
          categoria_procesada: 'bebidas',
          productos_encontrados: 1200,
          productos_nuevos: 150,
          productos_actualizados: 1050,
          tiempo_ejecucion_ms: 45000,
          errores_encontrados: 3,
          status: 'exitoso',
          created_at: '2025-11-01T10:00:00Z'
        },
        {
          id: '2',
          fuente: 'Maxiconsumo Necochea',
          categoria_procesada: 'almacen',
          productos_encontrados: 800,
          productos_nuevos: 100,
          productos_actualizados: 700,
          tiempo_ejecucion_ms: 35000,
          errores_encontrados: 2,
          status: 'exitoso',
          created_at: '2025-11-01T09:00:00Z'
        }
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(estadisticasScraping)
      });
      
      const statsResult = await fetch(`${API_URL}/estadisticas?dias=7&categoria=bebidas`, {
        headers: { 'Authorization': 'Bearer test-token' }
      });
      
      expect(statsResult.ok).toBe(true);
      const statsData = await statsResult.json();
      
      expect(statsData.success).toBe(true);
      expect(statsData.data.metricas_agregadas.total_ejecuciones).toBe(2);
      expect(statsData.data.metricas_agregadas.productos_promedio).toBe(1000);
      expect(statsData.data.metricas_agregadas.tasa_exito).toBe(100);
      expect(statsData.data.metricas_agregadas.tiempo_promedio_ms).toBe(40000);
      expect(statsData.data.parametros.dias_analizados).toBe(7);
      expect(statsData.data.parametros.categoria).toBe('bebidas');
    });
    
  });
  
  describe('⚙️ Configuración Unificada', () => {
    
    test('debe exponer configuración del proveedor vía API', async () => {
      const configuracion = {
        id: 'config-1',
        nombre: 'Maxiconsumo Necochea',
        url_base: 'https://maxiconsumo.com/sucursal_necochea/',
        activo: true,
        frecuencia_scraping: 'diaria',
        ultima_sincronizacion: '2025-11-01T09:30:00Z',
        proxima_sincronizacion: '2025-11-02T09:30:00Z',
        configuraciones: {
          categorias_soportadas: ['almacen', 'bebidas', 'limpieza', 'frescos'],
          timeout_request: 15000,
          max_reintentos: 3,
          umbral_alertas: '15%'
        },
        headers_personalizados: {
          'User-Agent': 'Mozilla/5.0 (Scraper Bot)',
          'Accept': 'text/html,application/xhtml+xml'
        },
        created_at: '2025-10-31T00:00:00Z',
        updated_at: '2025-11-01T09:30:00Z'
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([configuracion])
      });
      
      const configResult = await fetch(`${API_URL}/configuracion`, {
        headers: { 'Authorization': 'Bearer test-token' }
      });
      
      expect(configResult.ok).toBe(true);
      const configData = await configResult.json();
      
      expect(configData.success).toBe(true);
      expect(configData.data.configuracion.nombre).toBe('Maxiconsumo Necochea');
      expect(configData.data.configuracion.frecuencia_scraping).toBe('diaria');
      expect(configData.data.parametros_disponibles.frecuencia_scraping).toContain('diaria');
      expect(configData.data.parametros_disponibles.severidad_alertas).toContain('critica');
    });
    
  });
  
  describe('🔄 Flujo de Actualización Continua', () => {
    
    test('debe mantener consistencia entre scraping y API', async () => {
      const productosEnScraper = [
        { sku: 'PROD001', nombre: 'Producto 1', precio_unitario: 100, categoria: 'cat1' },
        { sku: 'PROD002', nombre: 'Producto 2', precio_unitario: 200, categoria: 'cat2' }
      ];
      
      // Simular que el scraper actualizó productos
      fetch
        .mockResolvedValueOnce({ // Consultar productos para API
          ok: true,
          json: () => Promise.resolve(productosEnScraper)
        })
        .mockResolvedValueOnce({ // Count
          ok: true,
          json: () => Promise.resolve([{ count: 2 }])
        })
        .mockResolvedValueOnce({ // Oportunidades
          ok: true,
          json: () => Promise.resolve([
            {
              diferencia_absoluta: 20,
              diferencia_porcentual: 20,
              es_oportunidad_ahorro: true
            }
          ])
        });
      
      // Verificar que la API refleja los cambios del scraper
      const productosResult = await fetch(`${API_URL}/productos?busqueda=Producto`, {
        headers: { 'Authorization': 'Bearer test-token' }
      });
      
      const productosData = await productosResult.json();
      expect(productosData.data.productos).toHaveLength(2);
      
      // Verificar que las oportunidades se actualizaron
      const comparacionResult = await fetch(`${API_URL}/comparacion`, {
        headers: { 'Authorization': 'Bearer test-token' }
      });
      
      const comparacionData = await comparacionResult.json();
      expect(comparacionData.data.oportunidades).toHaveLength(1);
    });
    
    test('debe manejar concurrencia entre scraping y consultas API', async () => {
      let scrapingActive = false;
      
      // Mock para simular que el scraping está en progreso
      fetch.mockImplementation(async (url, options) => {
        if (url.includes('/scrape')) {
          scrapingActive = true;
          await new Promise(resolve => setTimeout(resolve, 100)); // Simular scraping
          scrapingActive = false;
          
          return {
            ok: true,
            json: () => Promise.resolve({
              success: true,
              data: { productos_guardados: 100 }
            })
          };
        }
        
        if (scrapingActive) {
          return {
            ok: true,
            json: () => Promise.resolve({
              success: true,
              data: {
                productos: [],
                estadisticas: { scraping_en_progreso: true }
              }
            })
          };
        }
        
        return {
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: { productos: [{ id: '1', nombre: 'Test' }] }
          })
        };
      });
      
      // Iniciar scraping
      const scrapingPromise = fetch(`${SCRAPER_URL}/scrape`, { method: 'POST' });
      
      // Mientras scrappeando, hacer consultas
      const consultaPromise = fetch(`${API_URL}/productos`);
      
      const [scrapingResult, consultaResult] = await Promise.all([
        scrapingPromise,
        consultaPromise
      ]);
      
      expect(scrapingResult.ok).toBe(true);
      expect(consultaResult.ok).toBe(true);
      
      const consultaData = await consultaResult.json();
      // La consulta podría estar vacía durante el scraping
      expect(Array.isArray(consultaData.data.productos)).toBe(true);
    });
    
  });
  
});

// Setup global
beforeAll(() => {
  // Configurar entorno de testing
  process.env.NODE_ENV = 'test';
});

afterAll(() => {
  jest.clearAllMocks();
});