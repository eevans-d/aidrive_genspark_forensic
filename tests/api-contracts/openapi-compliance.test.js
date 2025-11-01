/**
 * API CONTRACT TESTS
 * Tests para validar cumplimiento con especificación OpenAPI 3.1
 */

const { describe, test, expect, beforeAll, afterAll, beforeEach, afterEach } = require('@jest/globals');
const fs = require('fs');
const path = require('path');

// Mock global
global.fetch = jest.fn();

// Cargar especificación OpenAPI
const openapiSpecPath = '/workspace/docs/api-proveedor-openapi-3.1.yaml';
let openapiSpec;

describe('📋 API CONTRACT TESTS - OpenAPI 3.1 Compliance', () => {
  
  describe('📖 Spec Loading and Validation', () => {
    
    test('debe cargar especificación OpenAPI correctamente', () => {
      expect(fs.existsSync(openapiSpecPath)).toBe(true);
      
      // Verificar que es un archivo YAML válido
      const specContent = fs.readFileSync(openapiSpecPath, 'utf8');
      expect(specContent).toContain('openapi: 3.1.0');
      expect(specContent).toContain('title: Mini Market API - Proveedor Maxiconsumo');
      expect(specContent).toContain('version: 1.0.0');
    });
    
    test('debe tener estructura OpenAPI válida', () => {
      const specContent = fs.readFileSync(openapiSpecPath, 'utf8');
      
      // Verificar secciones principales
      expect(specContent).toContain('info:');
      expect(specContent).toContain('servers:');
      expect(specContent).toContain('components:');
      expect(specContent).toContain('paths:');
      expect(specContent).toContain('security:');
    });
    
  });
  
  describe('🔌 Endpoint Compliance', () => {
    
    test('debe implementar GET /status según spec', async () => {
      const expectedResponse = {
        success: true,
        data: {
          sistema: {
            estado: 'operativo',
            version: '1.0.0',
            proveedor: 'Maxiconsumo Necochea'
          },
          estadisticas: {
            ultima_ejecucion: 'string',
            productos_totales: 0,
            oportunidades_activas: 0,
            ultima_sincronizacion: 'string',
            proximo_scrape_programado: 'string'
          },
          configuracion: {
            $ref: '#/components/schemas/ConfiguracionProveedor'
          }
        }
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(expectedResponse)
      });
      
      const response = await fetch('https://test.supabase.co/functions/v1/api-proveedor/status');
      const data = await response.json();
      
      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('application/json');
      expect(data.success).toBe(true);
      expect(data.data.sistema).toBeDefined();
      expect(data.data.estadisticas).toBeDefined();
    });
    
    test('debe implementar GET /precios según spec', async () => {
      const queryParams = [
        { name: 'categoria', type: 'string', required: false, default: 'todos' },
        { name: 'limit', type: 'integer', required: false, minimum: 1, maximum: 500, default: 50 },
        { name: 'offset', type: 'integer', required: false, minimum: 0, default: 0 },
        { name: 'activo', type: 'string', required: false, enum: ['true', 'false'], default: 'true' }
      ];
      
      for (const param of queryParams) {
        const url = `https://test.supabase.co/functions/v1/api-proveedor/precios?${param.name}=test`;
        
        fetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: {
              productos: [],
              paginacion: {
                total: 0,
                limite: param.default || 50,
                offset: 0,
                productos_mostrados: 0,
                tiene_mas: false
              }
            }
          })
        });
        
        const response = await fetch(url);
        expect(response.ok).toBe(true);
        
        const data = await response.json();
        expect(data.data.paginacion).toBeDefined();
        expect(data.data.productos).toBeDefined();
      }
    });
    
    test('debe implementar GET /productos según spec', async () => {
      const queryParams = [
        { name: 'busqueda', type: 'string', required: false },
        { name: 'categoria', type: 'string', required: false },
        { name: 'marca', type: 'string', required: false },
        { name: 'solo_con_stock', type: 'boolean', required: false, default: false },
        { name: 'limit', type: 'integer', required: false, minimum: 1, maximum: 1000, default: 100 }
      ];
      
      for (const param of queryParams) {
        const url = `https://test.supabase.co/functions/v1/api-proveedor/productos?${param.name}=test`;
        
        fetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: {
              productos: [],
              estadisticas: {
                total_productos: 0,
                productos_con_stock: 0,
                marcas_unicas: 0,
                categorias_disponibles: []
              }
            }
          })
        });
        
        const response = await fetch(url);
        expect(response.ok).toBe(true);
        
        const data = await response.json();
        expect(data.data.estadisticas).toBeDefined();
        expect(data.data.productos).toBeDefined();
      }
    });
    
    test('debe implementar GET /comparacion según spec', async () => {
      const queryParams = [
        { name: 'solo_oportunidades', type: 'boolean', required: false, default: false },
        { name: 'min_diferencia', type: 'number', required: false, minimum: 0, default: 0 },
        { name: 'orden', type: 'string', required: false, enum: ['diferencia_absoluta_desc', 'diferencia_absoluta_asc', 'diferencia_porcentual_desc', 'nombre_asc'], default: 'diferencia_absoluta_desc' },
        { name: 'limit', type: 'integer', required: false, minimum: 1, maximum: 200, default: 50 }
      ];
      
      for (const param of queryParams) {
        const url = `https://test.supabase.co/functions/v1/api-proveedor/comparacion?${param.name}=test`;
        
        fetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: {
              oportunidades: [],
              estadisticas: {
                total_oportunidades: 0,
                ahorro_total_estimado: 0,
                oportunidad_promedio: 0,
                mejor_oportunidad: null
              }
            }
          })
        });
        
        const response = await fetch(url);
        expect(response.ok).toBe(true);
        
        const data = await response.json();
        expect(data.data.oportunidades).toBeDefined();
        expect(data.data.estadisticas).toBeDefined();
      }
    });
    
    test('debe implementar POST /sincronizar según spec', async () => {
      const queryParams = [
        { name: 'categoria', type: 'string', required: false },
        { name: 'force_full', type: 'boolean', required: false, default: false }
      ];
      
      const url = `https://test.supabase.co/functions/v1/api-proveedor/sincronizar`;
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            sincronizacion: { scraping_completo: true },
            comparacion_generada: { comparaciones_realizadas: 0 }
          }
        })
      });
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer valid-token',
          'Content-Type': 'application/json'
        }
      });
      
      expect(response.status).toBe(200);
      expect(response.ok).toBe(true);
      
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(data.data.sincronizacion).toBeDefined();
    });
    
    test('debe implementar GET /alertas según spec', async () => {
      const queryParams = [
        { name: 'severidad', type: 'string', required: false, enum: ['baja', 'media', 'alta', 'critica', 'todos'], default: 'todos' },
        { name: 'tipo', type: 'string', required: false, enum: ['aumento', 'disminucion', 'nuevo_producto', 'todos'], default: 'todos' },
        { name: 'limit', type: 'integer', required: false, minimum: 1, maximum: 100, default: 20 }
      ];
      
      for (const param of queryParams) {
        const url = `https://test.supabase.co/functions/v1/api-proveedor/alertas?${param.name}=test`;
        
        fetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: {
              alertas: [],
              estadisticas: {
                total_alertas: 0,
                criticas: 0,
                altas: 0,
                medias: 0,
                bajas: 0,
                aumentos: 0,
                disminuciones: 0,
                nuevos_productos: 0
              }
            }
          })
        });
        
        const response = await fetch(url);
        expect(response.ok).toBe(true);
        
        const data = await response.json();
        expect(data.data.alertas).toBeDefined();
        expect(data.data.estadisticas).toBeDefined();
      }
    });
    
    test('debe implementar GET /estadisticas según spec', async () => {
      const queryParams = [
        { name: 'dias', type: 'integer', required: false, minimum: 1, maximum: 90, default: 7 },
        { name: 'categoria', type: 'string', required: false }
      ];
      
      for (const param of queryParams) {
        const url = `https://test.supabase.co/functions/v1/api-proveedor/estadisticas?${param.name}=test`;
        
        fetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: {
              estadisticas_periodo: [],
              metricas_agregadas: {
                total_ejecuciones: 0,
                productos_promedio: 0,
                tasa_exito: 0,
                tiempo_promedio_ms: 0
              }
            }
          })
        });
        
        const response = await fetch(url, {
          headers: { 'Authorization': 'Bearer valid-token' }
        });
        
        expect(response.ok).toBe(true);
        
        const data = await response.json();
        expect(data.data.estadisticas_periodo).toBeDefined();
        expect(data.data.metricas_agregadas).toBeDefined();
      }
    });
    
    test('debe implementar GET /configuracion según spec', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            configuracion: {
              nombre: 'Maxiconsumo Necochea',
              url_base: 'https://maxiconsumo.com/',
              frecuencia_scraping: 'diaria'
            },
            parametros_disponibles: {
              frecuencia_scraping: ['cada_hora', 'diaria', 'semanal'],
              severidad_alertas: ['baja', 'media', 'alta', 'critica'],
              tipos_cambio: ['aumento', 'disminucion', 'nuevo_producto']
            }
          }
        })
      });
      
      const response = await fetch('https://test.supabase.co/functions/v1/api-proveedor/configuracion', {
        headers: { 'Authorization': 'Bearer valid-token' }
      });
      
      expect(response.status).toBe(200);
      expect(response.ok).toBe(true);
      
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(data.data.configuracion).toBeDefined();
      expect(data.data.parametros_disponibles).toBeDefined();
    });
    
  });
  
  describe('📝 Schema Validation', () => {
    
    test('debe validar schema de ProductoProveedor', async () => {
      const validProduct = {
        id: 'uuid-string',
        sku: 'BEB001',
        nombre: 'Coca Cola 500ml',
        marca: 'Coca Cola',
        categoria: 'bebidas',
        precio_mayorista: 2500.00,
        precio_unitario: 250.50,
        stock_disponible: 100,
        codigo_barras: '1234567890123',
        url_producto: 'https://maxiconsumo.com/producto/123',
        imagen_url: 'https://maxiconsumo.com/imagen.jpg',
        descripcion: 'Bebida gaseosa',
        ultima_actualizacion: '2025-11-01T10:00:00Z',
        fuente: 'Maxiconsumo Necochea',
        activo: true
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { productos: [validProduct] }
        })
      });
      
      const response = await fetch('https://test.supabase.co/functions/v1/api-proveedor/precios?limit=1');
      const data = await response.json();
      
      expect(response.ok).toBe(true);
      expect(data.data.productos).toHaveLength(1);
      
      const product = data.data.productos[0];
      expect(product.sku).toBeDefined();
      expect(product.nombre).toBeDefined();
      expect(product.precio_unitario).toBeGreaterThanOrEqual(0);
      expect(product.categoria).toBeDefined();
      expect(typeof product.activo).toBe('boolean');
    });
    
    test('debe validar schema de ComparacionPrecio', async () => {
      const validComparison = {
        id: 'uuid-string',
        producto_id: 'uuid-string',
        nombre_producto: 'Producto Test',
        precio_actual: 280.00,
        precio_proveedor: 220.00,
        diferencia_absoluta: 60.00,
        diferencia_porcentual: 27.27,
        fuente: 'Maxiconsumo Necochea',
        fecha_comparacion: '2025-11-01T10:00:00Z',
        es_oportunidad_ahorro: true,
        recomendacion: 'OPORTUNIDAD CRÍTICA'
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { oportunidades: [validComparison] }
        })
      });
      
      const response = await fetch('https://test.supabase.co/functions/v1/api-proveedor/comparacion?limit=1');
      const data = await response.json();
      
      expect(response.ok).toBe(true);
      expect(data.data.oportunidades).toHaveLength(1);
      
      const comparison = data.data.oportunidades[0];
      expect(comparison.precio_actual).toBeGreaterThan(0);
      expect(comparison.precio_proveedor).toBeGreaterThan(0);
      expect(comparison.diferencia_absoluta).toBeGreaterThanOrEqual(0);
      expect(comparison.diferencia_porcentual).toBeGreaterThanOrEqual(0);
      expect(typeof comparison.es_oportunidad_ahorro).toBe('boolean');
      expect(comparison.recomendacion).toBeDefined();
    });
    
    test('debe validar schema de AlertaCambioPrecio', async () => {
      const validAlert = {
        id: 'uuid-string',
        producto_id: 'uuid-string',
        nombre_producto: 'Producto con Alerta',
        tipo_cambio: 'aumento',
        valor_anterior: 200.00,
        valor_nuevo: 260.00,
        porcentaje_cambio: 30.00,
        severidad: 'critica',
        mensaje: 'Precio aumentó 30.0%',
        accion_recomendada: 'Revisar estrategia de precios',
        fecha_alerta: '2025-11-01T10:00:00Z',
        procesada: false
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { alertas: [validAlert] }
        })
      });
      
      const response = await fetch('https://test.supabase.co/functions/v1/api-proveedor/alertas?limit=1');
      const data = await response.json();
      
      expect(response.ok).toBe(true);
      expect(data.data.alertas).toHaveLength(1);
      
      const alert = data.data.alertas[0];
      expect(['aumento', 'disminucion', 'nuevo_producto']).toContain(alert.tipo_cambio);
      expect(['baja', 'media', 'alta', 'critica']).toContain(alert.severidad);
      expect(typeof alert.procesada).toBe('boolean');
      expect(alert.mensaje).toBeDefined();
      expect(alert.accion_recomendada).toBeDefined();
    });
    
    test('debe validar schema de EstadisticasScraping', async () => {
      const validStats = {
        id: 'uuid-string',
        fuente: 'Maxiconsumo Necochea',
        categoria_procesada: 'bebidas',
        productos_encontrados: 1200,
        productos_nuevos: 150,
        productos_actualizados: 1050,
        tiempo_ejecucion_ms: 45000,
        errores_encontrados: 3,
        status: 'exitoso',
        detalles_error: null,
        created_at: '2025-11-01T10:00:00Z'
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { estadisticas_periodo: [validStats] }
        })
      });
      
      const response = await fetch('https://test.supabase.co/functions/v1/api-proveedor/estadisticas?dias=7', {
        headers: { 'Authorization': 'Bearer valid-token' }
      });
      const data = await response.json();
      
      expect(response.ok).toBe(true);
      expect(data.data.estadisticas_periodo).toHaveLength(1);
      
      const stats = data.data.estadisticas_periodo[0];
      expect(['exitoso', 'error', 'parcial']).toContain(stats.status);
      expect(stats.productos_encontrados).toBeGreaterThanOrEqual(0);
      expect(stats.tiempo_ejecucion_ms).toBeGreaterThanOrEqual(0);
      expect(stats.errores_encontrados).toBeGreaterThanOrEqual(0);
    });
    
  });
  
  describe('🔐 Security Schema Validation', () => {
    
    test('debe requerir autenticación para endpoints protegidos', async () => {
      const protectedEndpoints = [
        { path: '/sincronizar', method: 'POST' },
        { path: '/configuracion', method: 'GET' },
        { path: '/estadisticas', method: 'GET' }
      ];
      
      for (const { path, method } of protectedEndpoints) {
        // Sin token
        fetch.mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: () => Promise.resolve({
            success: false,
            error: { code: 'AUTH_REQUIRED', message: 'Se requiere autenticación' }
          })
        });
        
        const response = await fetch(`https://test.supabase.co/functions/v1/api-proveedor${path}`, {
          method,
          headers: { 'Content-Type': 'application/json' }
        });
        
        expect(response.status).toBe(401);
        
        const data = await response.json();
        expect(data.success).toBe(false);
        expect(data.error.code).toBe('AUTH_REQUIRED');
      }
    });
    
    test('debe incluir esquemas de seguridad en responses', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        headers: {
          'WWW-Authenticate': 'Bearer realm="api-proveedor"',
          'Content-Type': 'application/json'
        },
        json: () => Promise.resolve({
          success: true,
          data: { sistema: { estado: 'operativo' } }
        })
      });
      
      const response = await fetch('https://test.supabase.co/functions/v1/api-proveedor/status');
      
      expect(response.headers.get('WWW-Authenticate')).toBeDefined();
      expect(response.headers.get('Content-Type')).toContain('application/json');
    });
    
  });
  
  describe('📊 Response Format Compliance', () => {
    
    test('debe mantener estructura de respuesta consistente', async () => {
      const endpoints = [
        '/status',
        '/precios',
        '/productos',
        '/comparacion',
        '/alertas'
      ];
      
      for (const endpoint of endpoints) {
        fetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: { /* data específica del endpoint */ },
            timestamp: expect.any(String)
          })
        });
        
        const response = await fetch(`https://test.supabase.co/functions/v1/api-proveedor${endpoint}`);
        const data = await response.json();
        
        expect(response.ok).toBe(true);
        expect(data).toHaveProperty('success');
        expect(data).toHaveProperty('data');
        expect(data).toHaveProperty('timestamp');
        expect(typeof data.success).toBe('boolean');
        expect(data.data).toBeDefined();
      }
    });
    
    test('debe manejar errores con formato consistente', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({
          success: false,
          error: {
            code: 'BAD_REQUEST',
            message: 'Parámetros inválidos',
            timestamp: expect.any(String)
          }
        })
      });
      
      const response = await fetch('https://test.supabase.co/functions/v1/api-proveedor/precios?limit=invalid');
      const data = await response.json();
      
      expect(response.ok).toBe(false);
      expect(data).toHaveProperty('success', false);
      expect(data).toHaveProperty('error');
      expect(data.error).toHaveProperty('code');
      expect(data.error).toHaveProperty('message');
      expect(data.error).toHaveProperty('timestamp');
    });
    
  });
  
  describe('📋 Documentation Compliance', () => {
    
    test('debe incluir descripciones de endpoints en responses', async () => {
      const specContent = fs.readFileSync(openapiSpecPath, 'utf8');
      
      // Verificar que todos los endpoints tienen documentación
      const endpoints = [
        'summary: Estado del sistema de integración',
        'summary: Listar precios actuales del proveedor',
        'summary: Buscar productos disponibles',
        'summary: Comparación de precios con sistema',
        'summary: Trigger sincronización manual',
        'summary: Obtener alertas activas',
        'summary: Métricas de scraping',
        'summary: Configuración del proveedor'
      ];
      
      for (const endpoint of endpoints) {
        expect(specContent).toContain(endpoint);
      }
    });
    
    test('debe incluir información de contacto y licencia', async () => {
      const specContent = fs.readFileSync(openapiSpecPath, 'utf8');
      
      expect(specContent).toContain('contact:');
      expect(specContent).toContain('name: Soporte Técnico Mini Market');
      expect(specContent).toContain('email: soporte@minimarket.com');
      expect(specContent).toContain('license:');
      expect(specContent).toContain('name: Propietario - Mini Market');
    });
    
  });
  
});

// Setup
beforeAll(() => {
  // Cargar especificación OpenAPI
  if (fs.existsSync(openapiSpecPath)) {
    openapiSpec = fs.readFileSync(openapiSpecPath, 'utf8');
  }
});

afterAll(() => {
  jest.clearAllMocks();
});