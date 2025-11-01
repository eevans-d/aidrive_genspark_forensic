/**
 * TESTING SUITE SETUP
 * Configuración global y utilities para el sistema de testing
 */

// Jest setup global
const { jest } = require('@jest/globals');

// Configuración global de testing
global.TEST_CONFIG = {
  // URLs de testing
  API_BASE_URL: 'https://test-project.supabase.co/functions/v1/api-proveedor',
  SCRAPER_BASE_URL: 'https://test-project.supabase.co/functions/v1/scraper-maxiconsumo',
  
  // Configuración de performance
  PERFORMANCE_THRESHOLDS: {
    MAX_RESPONSE_TIME: 2000, // 2 segundos
    MIN_THROUGHPUT: 100, // requests por segundo
    MAX_CONCURRENT_REQUESTS: 50,
    TARGET_PRODUCTS: 40000,
    MEMORY_LIMIT_MB: 512
  },
  
  // Configuración de seguridad
  SECURITY_CONFIG: {
    RATE_LIMIT: 100, // requests por minuto
    MAX_PAYLOAD_SIZE: 10 * 1024 * 1024, // 10MB
    AUTH_TIMEOUT: 300000, // 5 minutos
    ALLOWED_ORIGINS: [
      'https://minimarket.com',
      'https://app.minimarket.com',
      'http://localhost:3000'
    ]
  }
};

// Utils globales para testing
global.TestUtils = {
  // Mock data generators
  generateMockProduct: (id = 0) => ({
    id: `mock-product-${id}`,
    sku: `SKU-${String(id).padStart(6, '0')}`,
    nombre: `Producto Mock ${id}`,
    marca: `Marca Mock ${Math.floor(id / 100) + 1}`,
    categoria: ['almacen', 'bebidas', 'limpieza', 'frescos', 'congelados'][id % 5],
    precio_unitario: Math.random() * 1000 + 10,
    precio_mayorista: Math.random() * 10000 + 100,
    stock_disponible: Math.floor(Math.random() * 500),
    codigo_barras: String(1234567890123 + id).slice(0, 13),
    url_producto: `https://maxiconsumo.com/producto/${id}`,
    imagen_url: `https://maxiconsumo.com/imagenes/${id}.jpg`,
    descripcion: `Descripción del producto mock ${id}`,
    ultima_actualizacion: new Date().toISOString(),
    fecha_creacion: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    fuente: 'Maxiconsumo Necochea',
    activo: true,
    metadata: {
      categoria_detallada: `Subcategoria ${id % 10}`,
      proveedor_original: 'Maxiconsumo Necochea',
      fecha_scraping: new Date().toISOString()
    }
  }),

  generateMockComparison: (id = 0) => ({
    id: `mock-comparison-${id}`,
    producto_id: `product-${id}`,
    nombre_producto: `Producto ${id}`,
    precio_actual: Math.random() * 1000 + 100,
    precio_proveedor: Math.random() * 800 + 50,
    diferencia_absoluta: Math.random() * 200,
    diferencia_porcentual: Math.random() * 50,
    fuente: 'Maxiconsumo Necochea',
    fecha_comparacion: new Date().toISOString(),
    es_oportunidad_ahorro: Math.random() > 0.5,
    recomendacion: `Recomendación para producto ${id}`
  }),

  generateMockAlert: (id = 0) => ({
    id: `mock-alert-${id}`,
    producto_id: `product-${id}`,
    nombre_producto: `Producto con Alerta ${id}`,
    tipo_cambio: ['aumento', 'disminucion', 'nuevo_producto'][id % 3],
    valor_anterior: Math.random() * 500 + 100,
    valor_nuevo: Math.random() * 600 + 120,
    porcentaje_cambio: (Math.random() - 0.5) * 100,
    severidad: ['baja', 'media', 'alta', 'critica'][id % 4],
    mensaje: `Cambio significativo detectado en producto ${id}`,
    accion_recomendada: 'Revisar y evaluar impacto',
    fecha_alerta: new Date().toISOString(),
    procesada: Math.random() > 0.7,
    fecha_procesamiento: Math.random() > 0.7 ? new Date().toISOString() : null,
    creado_por: 'Sistema Automatizado'
  }),

  generateMockStats: (id = 0) => ({
    id: `mock-stats-${id}`,
    fuente: 'Maxiconsumo Necochea',
    categoria_procesada: ['almacen', 'bebidas', 'limpieza', 'frescos', 'congelados'][id % 5],
    productos_encontrados: Math.floor(Math.random() * 2000) + 500,
    productos_nuevos: Math.floor(Math.random() * 200) + 50,
    productos_actualizados: Math.floor(Math.random() * 1500) + 300,
    tiempo_ejecucion_ms: Math.floor(Math.random() * 120000) + 30000,
    errores_encontrados: Math.floor(Math.random() * 10),
    status: ['exitoso', 'error', 'parcial'][id % 3],
    detalles_error: Math.random() > 0.8 ? 'Error simulado en testing' : null,
    metadata: {
      productos_por_segundo: Math.random() * 100 + 50,
      peak_memory_mb: Math.random() * 256 + 128,
      network_requests: Math.floor(Math.random() * 100) + 20
    },
    created_at: new Date(Date.now() - id * 3600000).toISOString()
  }),

  // Performance utilities
  measureExecutionTime: async (fn) => {
    const start = Date.now();
    const result = await fn();
    const end = Date.now();
    return {
      result,
      executionTime: end - start
    };
  },

  measureMemoryUsage: () => {
    return process.memoryUsage();
  },

  generateLoad: async (fn, iterations = 1000, concurrent = 10) => {
    const results = [];
    const batches = Math.ceil(iterations / concurrent);
    
    for (let i = 0; i < batches; i++) {
      const batch = Array(Math.min(concurrent, iterations - i * concurrent))
        .fill()
        .map(() => fn());
      
      const batchResults = await Promise.allSettled(batch);
      results.push(...batchResults);
    }
    
    return results;
  },

  // Security utilities
  generateSqlInjectionPayloads: () => [
    "'; DROP TABLE precios_proveedor; --",
    "1' OR '1'='1",
    "' UNION SELECT * FROM usuarios --",
    "admin'; DELETE FROM comparacion_precios; --",
    "' OR 1=1 LIMIT 1 --",
    "1; INSERT INTO logs_scraping VALUES ('hacked')",
    "' AND (SELECT COUNT(*) FROM precios_proveedor) > 0 --",
    "'; WAITFOR DELAY '00:00:05' --"
  ],

  generateXssPayloads: () => [
    '<script>alert("XSS")</script>',
    '<img src=x onerror=alert(1)>',
    'javascript:alert("XSS")',
    '<iframe src="javascript:alert(1)"></iframe>',
    '${7*7}',
    '{{7*7}}',
    '<svg onload=alert(1)>',
    '"><script>alert(1)</script>'
  ],

  validateResponseSchema: (response, expectedSchema) => {
    const data = typeof response === 'string' ? JSON.parse(response) : response;
    
    // Validar estructura básica
    expect(data).toHaveProperty('success');
    expect(typeof data.success).toBe('boolean');
    
    if (data.success) {
      expect(data).toHaveProperty('data');
      expect(data).toHaveProperty('timestamp');
    } else {
      expect(data).toHaveProperty('error');
      expect(data.error).toHaveProperty('code');
      expect(data.error).toHaveProperty('message');
    }
    
    // Validaciones específicas del schema
    if (expectedSchema) {
      Object.keys(expectedSchema).forEach(key => {
        if (expectedSchema[key].required && !data.data[key]) {
          throw new Error(`Missing required field: ${key}`);
        }
      });
    }
    
    return true;
  },

  // Database utilities
  createTestConnection: () => ({
    query: jest.fn(),
    close: jest.fn()
  }),

  mockSupabaseResponse: (data, status = 200) => {
    return {
      ok: status >= 200 && status < 300,
      status,
      headers: {
        get: jest.fn((name) => {
          const headers = {
            'content-type': 'application/json',
            'access-control-allow-origin': '*',
            'x-rate-limit-remaining': '99'
          };
          return headers[name.toLowerCase()];
        })
      },
      json: () => Promise.resolve(data)
    };
  },

  // Time utilities
  sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

  waitFor: async (condition, timeout = 5000, interval = 100) => {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      if (await condition()) {
        return true;
      }
      await global.TestUtils.sleep(interval);
    }
    
    throw new Error(`Timeout waiting for condition after ${timeout}ms`);
  },

  // Validation utilities
  isValidUUID: (str) => {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(str);
  },

  isValidISODate: (str) => {
    const date = new Date(str);
    return date instanceof Date && !isNaN(date) && date.toISOString() === str;
  },

  isValidEmail: (str) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(str);
  },

  isValidURL: (str) => {
    try {
      new URL(str);
      return true;
    } catch {
      return false;
    }
  },

  // Constants
  TEST_PRODUCTS_COUNT: 10000,
  TEST_CATEGORIES: ['almacen', 'bebidas', 'limpieza', 'frescos', 'congelados', 'perfumeria', 'mascotas', 'hogar', 'electro'],
  TEST_MARCAS: ['Coca Cola', 'Pepsi', 'Arcor', 'Nestlé', 'Bagley', 'Ser', 'La Serenísima', 'Tregar', 'Danone', 'Ala'],
  
  // Mock HTTP responses
  MOCK_RESPONSES: {
    success: (data = {}) => ({
      success: true,
      data,
      timestamp: new Date().toISOString()
    }),
    
    error: (code = 'TEST_ERROR', message = 'Test error') => ({
      success: false,
      error: {
        code,
        message,
        timestamp: new Date().toISOString()
      }
    }),
    
    rateLimited: () => ({
      success: false,
      error: {
        code: 'RATE_LIMITED',
        message: 'Too many requests',
        retryAfter: 60,
        timestamp: new Date().toISOString()
      }
    }),
    
    unauthorized: () => ({
      success: false,
      error: {
        code: 'AUTH_REQUIRED',
        message: 'Se requiere autenticación',
        timestamp: new Date().toISOString()
      }
    })
  }
};

// Setup global antes de cada test
beforeEach(() => {
  // Limpiar todos los mocks antes de cada test
  jest.clearAllMocks();
  
  // Configurar fetch mock por defecto
  global.fetch = global.fetch || jest.fn();
  
  // Resetear contadores de performance
  global.performanceMetrics = {
    requests: 0,
    errors: 0,
    totalTime: 0,
    memorySnapshots: []
  };
});

// Cleanup global después de cada test
afterEach(() => {
  // Verificar que no quedaron mocks sin verificar si estamos en modo estricto
  if (global.expect) {
    // Los tests pueden verificar explícitamente los mocks si es necesario
  }
});

// Setup global antes de todos los tests
beforeAll(() => {
  // Configurar variables de entorno para testing
  process.env.NODE_ENV = 'test';
  process.env.SUPABASE_URL = global.TEST_CONFIG.API_BASE_URL.replace('/functions/v1/api-proveedor', '');
  process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
  
  // Configurar timezone para tests consistentes
  process.env.TZ = 'UTC';
  
  console.log('🚀 Testing Suite Setup Complete');
  console.log(`📊 Performance Config:`, global.TEST_CONFIG.PERFORMANCE_THRESHOLDS);
  console.log(`🔒 Security Config:`, global.TEST_CONFIG.SECURITY_CONFIG);
});

// Cleanup global después de todos los tests
afterAll(() => {
  // Limpiar mocks
  jest.clearAllMocks();
  
  // Forzar garbage collection si está disponible
  if (global.gc) {
    global.gc();
  }
  
  console.log('✅ Testing Suite Cleanup Complete');
});

// Exportar para uso en tests
module.exports = global.TestUtils;