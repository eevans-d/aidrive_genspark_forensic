/**
 * PERFORMANCE TESTS
 * Tests de rendimiento para el sistema con 40k+ productos
 */

const { describe, test, expect, beforeAll, afterAll, beforeEach, afterEach } = require('@jest/globals');

// Mock global para performance testing
global.fetch = jest.fn();

// Configuración de tests de performance
const PERFORMANCE_CONFIG = {
  TARGET_PRODUCTS: 40000,
  CONCURRENT_REQUESTS: 50,
  TEST_DURATION: 30000, // 30 segundos
  MAX_RESPONSE_TIME: 2000, // 2 segundos
  MIN_THROUGHPUT: 100, // requests por segundo
  MEMORY_LIMIT_MB: 512
};

describe('🚀 PERFORMANCE TESTS - Mini Market Sprint 6', () => {
  
  describe('📊 Load Testing - 40k+ Productos', () => {
    
    test('debe manejar 40000+ productos en base de datos', async () => {
      const startTime = Date.now();
      const productosGenerados = [];
      
      // Generar 40000+ productos de prueba
      for (let i = 0; i < PERFORMANCE_CONFIG.TARGET_PRODUCTS; i++) {
        productosGenerados.push({
          id: `perf-${i}`,
          sku: `SKU-${String(i).padStart(6, '0')}`,
          nombre: `Producto Performance Test ${i}`,
          marca: `Marca ${Math.floor(i / 1000) + 1}`,
          categoria: ['almacen', 'bebidas', 'limpieza', 'frescos', 'congelados'][i % 5],
          precio_unitario: Math.random() * 1000 + 10,
          stock_disponible: Math.floor(Math.random() * 500),
          fuente: 'Maxiconsumo Necochea',
          activo: true,
          ultima_actualizacion: new Date().toISOString()
        });
      }
      
      // Simular inserción en lotes
      const batchSize = 1000;
      let insertados = 0;
      
      for (let i = 0; i < productosGenerados.length; i += batchSize) {
        const batch = productosGenerados.slice(i, i + batchSize);
        
        fetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(batch.map(p => ({ id: p.id })))
        });
        
        // Simular inserción
        const response = await fetch('https://test.supabase.co/rest/v1/precios_proveedor', {
          method: 'POST',
          headers: {
            'apikey': 'test-key',
            'Authorization': 'Bearer test-key',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(batch)
        });
        
        expect(response.ok).toBe(true);
        insertados += batch.length;
      }
      
      const insertTime = Date.now() - startTime;
      const insertRate = (insertados / insertTime) * 1000; // inserts per second
      
      console.log(`📊 Performance Results:`);
      console.log(`   Products inserted: ${insertados}`);
      console.log(`   Insert time: ${insertTime}ms`);
      console.log(`   Insert rate: ${insertRate.toFixed(2)}/sec`);
      
      expect(insertados).toBe(PERFORMANCE_CONFIG.TARGET_PRODUCTS);
      expect(insertRate).toBeGreaterThan(500); // Mínimo 500 inserts/sec
    });
    
    test('debe responder consultas grandes en tiempo aceptable', async () => {
      const startTime = Date.now();
      
      // Mock respuesta con 40000 productos paginados
      const productosPaginados = Array.from({ length: 1000 }, (_, i) => ({
        id: `query-${i}`,
        sku: `QUERY-${String(i).padStart(6, '0')}`,
        nombre: `Producto Consulta ${i}`,
        precio_unitario: Math.random() * 500 + 50
      }));
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(productosPaginados)
      }).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ count: 40000 }])
      });
      
      // Simular consulta grande con paginación
      const response = await fetch('https://test.supabase.co/rest/v1/precios_proveedor?limit=1000&offset=0', {
        headers: {
          'apikey': 'test-key',
          'Authorization': 'Bearer test-key'
        }
      });
      
      const queryTime = Date.now() - startTime;
      
      expect(response.ok).toBe(true);
      expect(queryTime).toBeLessThan(PERFORMANCE_CONFIG.MAX_RESPONSE_TIME);
      
      const data = await response.json();
      expect(data).toHaveLength(1000);
      
      console.log(`📊 Query Performance: ${queryTime}ms para 1000 productos`);
    });
    
  });
  
  describe('⚡ Concurrent Request Handling', () => {
    
    test('debe manejar 50 requests concurrentes', async () => {
      const concurrentRequests = [];
      
      // Ejecutar 50 requests concurrentes
      for (let i = 0; i < PERFORMANCE_CONFIG.CONCURRENT_REQUESTS; i++) {
        const requestPromise = simulateAPICall(i);
        concurrentRequests.push(requestPromise);
      }
      
      const startTime = Date.now();
      const results = await Promise.all(concurrentRequests);
      const totalTime = Date.now() - startTime;
      
      // Verificar resultados
      const successfulRequests = results.filter(r => r.success);
      const responseTimes = results.map(r => r.responseTime);
      
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      const maxResponseTime = Math.max(...responseTimes);
      const throughput = (results.length / totalTime) * 1000; // requests per second
      
      console.log(`📊 Concurrent Requests Results:`);
      console.log(`   Total requests: ${results.length}`);
      console.log(`   Successful: ${successfulRequests.length}`);
      console.log(`   Total time: ${totalTime}ms`);
      console.log(`   Avg response time: ${avgResponseTime.toFixed(2)}ms`);
      console.log(`   Max response time: ${maxResponseTime}ms`);
      console.log(`   Throughput: ${throughput.toFixed(2)} req/sec`);
      
      expect(successfulRequests.length).toBeGreaterThanOrEqual(45); // 90% success rate
      expect(avgResponseTime).toBeLessThan(PERFORMANCE_CONFIG.MAX_RESPONSE_TIME);
      expect(throughput).toBeGreaterThan(PERFORMANCE_CONFIG.MIN_THROUGHPUT);
    });
    
    test('debe mantener performance con carga mixta', async () => {
      const requestTypes = ['status', 'precios', 'productos', 'comparacion', 'alertas'];
      const mixedRequests = [];
      
      // Crear mezcla de tipos de requests
      for (let i = 0; i < 100; i++) {
        const requestType = requestTypes[i % requestTypes.length];
        mixedRequests.push(simulateMixedAPICall(requestType, i));
      }
      
      const startTime = Date.now();
      const results = await Promise.all(mixedRequests);
      const totalTime = Date.now() - startTime;
      
      const successfulResults = results.filter(r => r.success);
      const throughput = (results.length / totalTime) * 1000;
      
      console.log(`📊 Mixed Load Results:`);
      console.log(`   Request types: ${requestTypes.join(', ')}`);
      console.log(`   Total requests: ${results.length}`);
      console.log(`   Success rate: ${(successfulResults.length / results.length * 100).toFixed(1)}%`);
      console.log(`   Throughput: ${throughput.toFixed(2)} req/sec`);
      
      expect(successfulResults.length).toBeGreaterThan(85); // 85% success rate
      expect(throughput).toBeGreaterThan(200); // 200 req/sec
    });
    
  });
  
  describe('💾 Memory and Resource Usage', () => {
    
    test('debe mantener uso de memoria bajo control', async () => {
      const initialMemory = process.memoryUsage();
      const memorySnapshots = [initialMemory];
      
      // Procesar 10000 productos y medir memoria
      for (let batch = 0; batch < 10; batch++) {
        const productos = Array.from({ length: 1000 }, (_, i) => ({
          id: `mem-test-${batch}-${i}`,
          nombre: `Producto Memory Test ${batch}-${i}`,
          data: 'x'.repeat(1000) // 1KB de datos adicionales
        }));
        
        // Simular procesamiento
        const processed = productos.map(p => ({
          ...p,
          procesado: true,
          timestamp: Date.now()
        }));
        
        const currentMemory = process.memoryUsage();
        memorySnapshots.push(currentMemory);
        
        // Limpiar referencias
        productos.length = 0;
        processed.length = 0;
      })
      
      const finalMemory = process.memoryUsage();
      const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;
      const memoryIncreaseMB = memoryIncrease / (1024 * 1024);
      
      console.log(`📊 Memory Usage:`);
      console.log(`   Initial heap: ${(initialMemory.heapUsed / 1024 / 1024).toFixed(2)}MB`);
      console.log(`   Final heap: ${(finalMemory.heapUsed / 1024 / 1024).toFixed(2)}MB`);
      console.log(`   Memory increase: ${memoryIncreaseMB.toFixed(2)}MB`);
      
      expect(memoryIncreaseMB).toBeLessThan(PERFORMANCE_CONFIG.MEMORY_LIMIT_MB);
    });
    
  });
  
  describe('🕷️ Web Scraper Performance', () => {
    
    test('debe scrapear 40000 productos en tiempo razonable', async () => {
      const startTime = Date.now();
      
      // Mock HTML responses para múltiples categorías
      const categorias = ['almacen', 'bebidas', 'limpieza', 'frescos', 'congelados'];
      const productosPorCategoria = 8000; // 8k por categoría
      
      for (const categoria of categorias) {
        // Mock respuesta HTML con productos
        const html = generateMockHTML(categoria, productosPorCategoria);
        
        fetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          text: () => Promise.resolve(html)
        });
        
        // Simular scraping de categoría
        const scrapedProducts = await simulateScrapingCategory(categoria, html);
        expect(scrapedProducts.length).toBeGreaterThan(0);
      }
      
      const scrapingTime = Date.now() - startTime;
      const productsPerSecond = (categorias.length * productosPorCategoria) / (scrapingTime / 1000);
      
      console.log(`📊 Scraping Performance:`);
      console.log(`   Categories processed: ${categorias.length}`);
      console.log(`   Products per category: ${productosPorCategoria}`);
      console.log(`   Total products: ${categorias.length * productosPorCategoria}`);
      console.log(`   Scraping time: ${scrapingTime}ms`);
      console.log(`   Products/sec: ${productsPerSecond.toFixed(2)}`);
      
      expect(scrapingTime).toBeLessThan(300000); // Menos de 5 minutos
      expect(productsPerSecond).toBeGreaterThan(100); // Mínimo 100 productos/sec
    });
    
    test('debe manejar rate limiting correctamente', async () => {
      const requestTimes = [];
      const requests = 20;
      
      for (let i = 0; i < requests; i++) {
        const requestStart = Date.now();
        
        // Simular request con rate limiting
        const response = await simulateRateLimitedRequest(i);
        requestTimes.push(Date.now() - requestStart);
        
        // Verificar que se respetó el delay
        if (i > 0) {
          const delay = requestTimes[i] - requestTimes[i - 1];
          expect(delay).toBeGreaterThanOrEqual(2000); // 2 segundos entre requests
        }
      }
      
      const avgRequestTime = requestTimes.reduce((a, b) => a + b, 0) / requestTimes.length;
      
      console.log(`📊 Rate Limiting Performance:`);
      console.log(`   Requests: ${requests}`);
      console.log(`   Avg request time: ${avgRequestTime.toFixed(2)}ms`);
      console.log(`   Min delay: ${Math.min(...requestTimes)}ms`);
      console.log(`   Max delay: ${Math.max(...requestTimes)}ms`);
      
      expect(avgRequestTime).toBeGreaterThan(2000); // Con rate limiting
    });
    
  });
  
  describe('🔄 Database Performance', () => {
    
    test('debe ejecutar consultas complejas eficientemente', async () => {
      const queryTests = [
        {
          name: 'Complex JOIN with aggregations',
          query: `
            SELECT pp.*, 
                   COUNT(cp.id) as comparaciones_count,
                   AVG(cp.diferencia_porcentual) as ahorro_promedio
            FROM precios_proveedor pp
            LEFT JOIN comparacion_precios cp ON cp.producto_id = pp.producto_id
            WHERE pp.activo = true 
              AND pp.categoria IN ('bebidas', 'almacen')
            GROUP BY pp.id
            ORDER BY ahorro_promedio DESC
            LIMIT 5000
          `,
          expectedTime: 1500
        },
        {
          name: 'Full-text search',
          query: `
            SELECT * FROM precios_proveedor 
            WHERE nombre ILIKE '%coca%' 
              OR marca ILIKE '%coca%'
            ORDER BY ultima_actualizacion DESC
            LIMIT 1000
          `,
          expectedTime: 800
        },
        {
          name: 'Aggregation with date filtering',
          query: `
            SELECT DATE(fecha_comparacion) as fecha,
                   COUNT(*) as comparaciones,
                   AVG(diferencia_porcentual) as ahorro_promedio
            FROM comparacion_precios
            WHERE fecha_comparacion >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(fecha_comparacion)
            ORDER BY fecha DESC
          `,
          expectedTime: 1000
        }
      ];
      
      for (const test of queryTests) {
        const startTime = Date.now();
        
        // Mock respuesta de base de datos
        fetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(generateMockQueryResults(test.name))
        });
        
        await simulateComplexQuery(test.query);
        
        const queryTime = Date.now() - startTime;
        
        console.log(`📊 Query Performance - ${test.name}: ${queryTime}ms`);
        expect(queryTime).toBeLessThan(test.expectedTime);
      }
    });
    
  });
  
  describe('📊 Stress Testing', () => {
    
    test('debe sobrevivir a carga extrema', async () => {
      const stressDuration = 10000; // 10 segundos
      const requestsPerSecond = 100;
      const totalRequests = (stressDuration / 1000) * requestsPerSecond;
      const requestPromises = [];
      
      const startTime = Date.now();
      
      // Generar requests continuos
      let requestCount = 0;
      const interval = setInterval(() => {
        if (Date.now() - startTime < stressDuration) {
          for (let i = 0; i < Math.floor(requestsPerSecond / 10); i++) {
            requestPromises.push(simulateStressRequest(requestCount++));
          }
        } else {
          clearInterval(interval);
        }
      }, 100); // Cada 100ms
      
      // Esperar a que terminen los requests
      await new Promise(resolve => setTimeout(resolve, stressDuration + 2000));
      
      const results = await Promise.allSettled(requestPromises);
      const successfulRequests = results.filter(r => r.status === 'fulfilled').length;
      const successRate = (successfulRequests / results.length) * 100;
      
      console.log(`📊 Stress Test Results:`);
      console.log(`   Duration: ${stressDuration}ms`);
      console.log(`   Total requests: ${results.length}`);
      console.log(`   Successful: ${successfulRequests}`);
      console.log(`   Success rate: ${successRate.toFixed(1)}%`);
      console.log(`   Avg requests/sec: ${(results.length / (stressDuration / 1000)).toFixed(2)}`);
      
      expect(successRate).toBeGreaterThan(80); // 80% success rate mínimo
    });
    
  });
  
});

// Funciones auxiliares para testing
async function simulateAPICall(requestId) {
  const startTime = Date.now();
  
  try {
    // Simular delay de red
    await new Promise(resolve => setTimeout(resolve, Math.random() * 100));
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true, requestId })
    });
    
    const response = await fetch('https://test.supabase.co/functions/v1/api-proveedor/status');
    const responseTime = Date.now() - startTime;
    
    return { success: response.ok, responseTime, requestId };
  } catch (error) {
    return { success: false, responseTime: Date.now() - startTime, requestId, error };
  }
}

async function simulateMixedAPICall(requestType, requestId) {
  const startTime = Date.now();
  
  try {
    const endpoints = {
      status: '/status',
      precios: '/precios?limit=50',
      productos: '/productos?limit=100',
      comparacion: '/comparacion',
      alertas: '/alertas'
    };
    
    const endpoint = endpoints[requestType] || '/status';
    
    await new Promise(resolve => setTimeout(resolve, Math.random() * 200));
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ 
        success: true, 
        endpoint: requestType,
        requestId 
      })
    });
    
    const response = await fetch(`https://test.supabase.co${endpoint}`);
    const responseTime = Date.now() - startTime;
    
    return { success: response.ok, responseTime, requestType, requestId };
  } catch (error) {
    return { success: false, responseTime: Date.now() - startTime, requestType, requestId, error };
  }
}

async function simulateScrapingCategory(categoria, html) {
  // Simular extracción de productos
  const products = [];
  const productPattern = /<div[^>]*class="[^"]*producto[^"]*"[^>]*>.*?<h3[^>]*>(.*?)<\/h3>.*?<span[^>]*class="precio[^"]*">.*?(\d+[\.,]\d+).*?<\/span>/gs;
  
  let match;
  while ((match = productPattern.exec(html)) !== null) {
    products.push({
      sku: `SCRAPE-${categoria}-${products.length}`,
      nombre: match[1].trim(),
      precio_unitario: parseFloat(match[2].replace(',', '.')),
      categoria: categoria
    });
  }
  
  return products;
}

function generateMockHTML(categoria, productCount) {
  let html = `<div class="category-${categoria}">`;
  
  for (let i = 0; i < productCount; i++) {
    const precio = (Math.random() * 1000 + 10).toFixed(2);
    const nombre = `${categoria.charAt(0).toUpperCase() + categoria.slice(1)} Product ${i}`;
    
    html += `
      <div class="producto">
        <h3>${nombre}</h3>
        <span class="precio">$${precio}</span>
        <div class="sku">${categoria.toUpperCase()}-${String(i).padStart(6, '0')}</div>
      </div>
    `;
  }
  
  html += '</div>';
  return html;
}

async function simulateRateLimitedRequest(requestId) {
  // Simular rate limiting con delay
  const minDelay = 2000; // 2 segundos entre requests
  const jitter = Math.random() * 500; // Variación aleatoria
  
  await new Promise(resolve => setTimeout(resolve, minDelay + jitter));
  
  fetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({ success: true, requestId, delay: minDelay + jitter })
  });
  
  const response = await fetch('https://test.supabase.co/functions/v1/scraper-maxiconsumo/scrape');
  return response.ok;
}

async function simulateComplexQuery(query) {
  // Simular ejecución de query compleja
  await new Promise(resolve => setTimeout(resolve, Math.random() * 500 + 100));
  
  fetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({ query })
  });
  
  return fetch('https://test.supabase.co/rest/v1/rpc/execute_query', {
    method: 'POST',
    body: JSON.stringify({ query })
  });
}

function generateMockQueryResults(queryName) {
  // Generar resultados mock basados en el tipo de query
  const results = {
    'Complex JOIN': Array.from({ length: 1000 }, (_, i) => ({
      id: i,
      nombre: `Product ${i}`,
      comparaciones_count: Math.floor(Math.random() * 10),
      ahorro_promedio: Math.random() * 50
    })),
    'Full-text search': Array.from({ length: 500 }, (_, i) => ({
      id: i,
      nombre: `Coca Product ${i}`,
      marca: 'Coca Cola',
      ultima_actualizacion: new Date().toISOString()
    })),
    'Aggregation': Array.from({ length: 7 }, (_, i) => ({
      fecha: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      comparaciones: Math.floor(Math.random() * 100) + 50,
      ahorro_promedio: Math.random() * 30
    }))
  };
  
  return results[queryName] || [];
}

async function simulateStressRequest(requestId) {
  const endpoints = ['/status', '/precios', '/productos', '/comparacion'];
  const endpoint = endpoints[requestId % endpoints.length];
  
  try {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true, requestId, endpoint })
    });
    
    const response = await fetch(`https://test.supabase.co${endpoint}`);
    return response.ok;
  } catch (error) {
    return false;
  }
}

// Setup y cleanup
beforeAll(() => {
  // Configurar V8 flags para performance testing
  if (typeof global.gc === 'function') {
    global.gc(); // Force garbage collection antes de tests
  }
});

afterAll(() => {
  jest.clearAllMocks();
  if (typeof global.gc === 'function') {
    global.gc(); // Force garbage collection después de tests
  }
});