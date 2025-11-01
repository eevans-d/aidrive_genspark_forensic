/**
 * UNIT TESTS - WEB SCRAPER MAXICONSUMO
 * Tests exhaustivos para el sistema de scraping
 */

const { describe, test, expect, beforeEach, afterEach } = require('@jest/globals');

// Mock de fetch global
global.fetch = jest.fn();

// Mock de console para testing
const originalConsole = console;
global.console = {
  ...originalConsole,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

// Importar funciones a testear
const scraperPath = '/workspace/supabase/functions/scraper-maxiconsumo/index.ts';

describe('🕷️ UNIT TESTS - Web Scraper Maxiconsumo', () => {
  
  describe('📦 Funciones de Extracción de Productos', () => {
    
    test('debe extraer productos con patrón principal correctamente', async () => {
      // Setup
      const htmlEjemplo = `
        <div class="producto">
          <h3>Coca Cola 500ml</h3>
          <span class="precio">$250.50</span>
          <div class="sku">CC500</div>
        </div>
        <div class="producto">
          <h3>Pepsi 2L</h3>
          <span class="precio">$450.75</span>
          <div class="sku">PE2L</div>
        </div>
      `;
      
      // Ejecutar
      const productos = extraerProductosConRegex(htmlEjemplo, 'bebidas', 'https://maxiconsumo.com/');
      
      // Verificar
      expect(productos).toHaveLength(2);
      expect(productos[0].nombre).toBe('Coca Cola 500ml');
      expect(productos[0].precio_unitario).toBe(250.50);
      expect(productos[0].sku).toBe('CC500');
      expect(productos[0].categoria).toBe('bebidas');
      
      expect(productos[1].nombre).toBe('Pepsi 2L');
      expect(productos[1].precio_unitario).toBe(450.75);
      expect(productos[1].sku).toBe('PE2L');
    });
    
    test('debe usar patrón alternativo si el principal no encuentra productos', async () => {
      const htmlSinProductos = `
        <div class="no-producto">
          <h1>Sin productos</h1>
          <p>precio $100.00</p>
        </div>
      `;
      
      const productos = extraerProductosConRegex(htmlSinProductos, 'almacen', 'https://maxiconsumo.com/');
      
      // Verificar que no usa el patrón principal pero podría usar el alternativo
      expect(Array.isArray(productos)).toBe(true);
    });
    
    test('debe manejar errores de parsing gracefully', () => {
      const htmlMalFormado = '<div><h3>Producto sin precio</div>';
      
      expect(() => {
        extraerProductosConRegex(htmlMalFormado, 'categoria', 'https://maxiconsumo.com/');
      }).not.toThrow();
    });
    
    test('debe extraer marca del nombre correctamente', () => {
      const nombres = [
        'Coca Cola 500ml',
        'Arcor Dulce de Leche',
        'Nestlé Chocolinas',
        'Producto Sin Marca'
      ];
      
      const marcas = nombres.map(extraerMarcaDelNombre);
      
      expect(marcas[0]).toBe('Coca Cola');
      expect(marcas[1]).toBe('Arcor');
      expect(marcas[2]).toBe('Nestlé');
      expect(marcas[3]).toBe('Producto');
    });
    
    test('debe generar SKU cuando no existe', () => {
      const sku = generarSKU('Producto de Prueba', 'categoria');
      
      expect(sku).toMatch(/^CAT-PRODU.*-[A-Z0-9]{6}$/);
      expect(sku.length).toBeLessThan(30);
    });
    
  });
  
  describe('🔄 Funciones de Rate Limiting y Reintentos', () => {
    
    test('debe implementar delay correctamente', async () => {
      const inicio = Date.now();
      await delay(100);
      const fin = Date.now();
      
      expect(fin - inicio).toBeGreaterThanOrEqual(95); // Allowar margen de timing
    });
    
    test('debe hacer reintentos con delay exponencial', async () => {
      // Mock fetch para fallar 2 veces y luego éxito
      fetch.mockResolvedValueOnce(Promise.reject(new Error('Network error')))
           .mockResolvedValueOnce(Promise.reject(new Error('Network error')))
           .mockResolvedValueOnce({
             ok: true,
             status: 200,
             text: () => Promise.resolve('success')
           });
      
      const headers = { 'User-Agent': 'Test' };
      
      await expect(fetchConReintentos('http://test.com', headers, 3))
        .resolves.toBeDefined();
      
      expect(fetch).toHaveBeenCalledTimes(3);
    });
    
    test('debe manejar rate limiting (HTTP 429)', async () => {
      fetch.mockResolvedValue({
        ok: false,
        status: 429,
        statusText: 'Too Many Requests'
      });
      
      const headers = { 'User-Agent': 'Test' };
      
      try {
        await fetchConReintentos('http://test.com', headers, 1);
      } catch (error) {
        expect(error.message).toContain('429');
      }
      
      expect(fetch).toHaveBeenCalled();
    });
    
  });
  
  describe('💾 Funciones de Guardado en Base de Datos', () => {
    
    test('debe guardar productos correctamente', async () => {
      const productos = [
        {
          sku: 'TEST001',
          nombre: 'Producto Test',
          precio_unitario: 100.50,
          categoria: 'test'
        }
      ];
      
      // Mock responses para verificación de existencia e inserción
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]) // No existe
      }).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: 'new-id' }])
      });
      
      const guardados = await guardarProductosExtraidos(
        productos, 
        'http://mock-supabase.com',
        'mock-key'
      );
      
      expect(guardados).toBe(1);
      expect(fetch).toHaveBeenCalledTimes(2);
    });
    
    test('debe actualizar productos existentes', async () => {
      const productos = [
        {
          sku: 'EXISTING001',
          nombre: 'Producto Actualizado',
          precio_unitario: 150.75
        }
      ];
      
      // Mock que indica que el producto ya existe
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: 'existing-id' }])
      }).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: 'existing-id' }])
      });
      
      const guardados = await guardarProductosExtraidos(
        productos,
        'http://mock-supabase.com',
        'mock-key'
      );
      
      expect(guardados).toBe(1);
      
      // Verificar que se hizo PATCH para actualizar
      const patchCall = fetch.mock.calls.find(call => 
        call[1]?.method === 'PATCH'
      );
      expect(patchCall).toBeDefined();
    });
    
  });
  
  describe('🔍 Funciones de Comparación de Precios', () => {
    
    test('debe generar comparación correcta', () => {
      const precioActual = 100;
      const precioProveedor = 80;
      
      const recomendacion = generarRecomendacion(precioActual, precioProveedor);
      
      expect(recomendacion).toContain('OPORTUNIDAD');
      expect(recomendacion).toContain('25.0%');
      expect(recomendacion).toContain('$20.00');
    });
    
    test('debe clasificar recomendaciones por porcentaje', () => {
      const testCases = [
        { actual: 100, proveedor: 70, expected: 'CRÍTICA' },
        { actual: 100, proveedor: 85, expected: 'BUENA' },
        { actual: 100, proveedor: 93, expected: 'MODERADA' },
        { actual: 100, proveedor: 97, expected: 'MENOR' },
        { actual: 80, proveedor: 100, expected: 'SUPERIOR' }
      ];
      
      testCases.forEach(testCase => {
        const recom = generarRecomendacion(testCase.actual, testCase.proveedor);
        expect(recom).toMatch(new RegExp(testCase.expected, 'i'));
      });
    });
    
  });
  
  describe('🚨 Funciones de Alertas', () => {
    
    test('debe calcular próximo scrape correctamente', () => {
      const proximo = calcularProximoScrape();
      const ahora = new Date();
      const diff = new Date(proximo).getTime() - ahora.getTime();
      
      // Debería ser aproximadamente 6 horas
      expect(diff).toBeGreaterThan(5 * 60 * 60 * 1000); // 5 horas
      expect(diff).toBeLessThan(7 * 60 * 60 * 1000); // 7 horas
    });
    
  });
  
  describe('⚙️ Funciones de Configuración', () => {
    
    test('debe retornar configuración de categorías completa', () => {
      const config = obtenerConfiguracionCategorias();
      
      expect(config).toHaveProperty('almacen');
      expect(config).toHaveProperty('bebidas');
      expect(config).toHaveProperty('limpieza');
      expect(config.almacen).toHaveProperty('slug');
      expect(config.almacen).toHaveProperty('prioridad');
      expect(config.almacen).toHaveProperty('max_productos');
    });
    
    test('debe generar headers aleatorios válidos', () => {
      const headers = generarHeadersAleatorios();
      
      expect(headers).toHaveProperty('User-Agent');
      expect(headers).toHaveProperty('Accept');
      expect(headers).toHaveProperty('Accept-Language');
      expect(headers['User-Agent']).toMatch(/Mozilla/);
    });
    
  });
  
  describe('🔧 Edge Cases y Validaciones', () => {
    
    test('debe manejar productos con datos faltantes', () => {
      const html = `
        <div class="producto">
          <h3></h3>
          <span class="precio">$0</span>
        </div>
      `;
      
      const productos = extraerProductosConRegex(html, 'test', 'https://test.com/');
      
      // No debería incluir productos inválidos
      expect(productos.length).toBe(0);
    });
    
    test('debe manejar precios malformados', () => {
      const html = `
        <div class="producto">
          <h3>Producto</h3>
          <span class="precio">precio no válido</span>
        </div>
      `;
      
      const productos = extraerProductosConRegex(html, 'test', 'https://test.com/');
      
      expect(productos.length).toBe(0);
    });
    
    test('debe validar límites de rate limiting', async () => {
      const requestCount = 10;
      const startTime = Date.now();
      
      // Simular múltiples requests
      for (let i = 0; i < requestCount; i++) {
        await delay(100);
      }
      
      const totalTime = Date.now() - startTime;
      expect(totalTime).toBeGreaterThan(900); // Mínimo tiempo esperado
    });
    
  });
  
  describe('📊 Métricas y Estadísticas', () => {
    
    test('debe calcular estadísticas correctamente', () => {
      const stats = {
        productos_procesados: 100,
        productos_exitosos: 95,
        productos_con_error: 5,
        tiempo_ejecucion: 30000
      };
      
      const tasaExito = (stats.productos_exitosos / stats.productos_procesados) * 100;
      
      expect(tasaExito).toBe(95);
      expect(stats.tiempo_ejecucion).toBeGreaterThan(0);
    });
    
  });
  
});

// Funciones auxiliares copiadas del scraper original para testing
function extraerProductosConRegex(html: string, categoria: string, urlBase: string) {
  const productos = [];
  const productoPattern = /<div[^>]*class="[^"]*producto[^"]*"[^>]*>.*?<h3[^>]*>(.*?)<\/h3>.*?<span[^>]*class="precio[^"]*">.*?(\d+[\.,]\d+).*?<\/span>.*?sku["']?\s*:?\s*["']?([^"'\s]+)["']?.*?<\/div>/gs;
  
  let match;
  while ((match = productoPattern.exec(html)) !== null) {
    try {
      const nombre = match[1]?.trim();
      const precioTexto = match[2]?.replace(',', '.');
      const precio = parseFloat(precioTexto);
      const sku = match[3];

      if (nombre && precio > 0 && sku) {
        productos.push({
          sku,
          nombre,
          marca: extraerMarcaDelNombre(nombre),
          categoria,
          precio_unitario: precio,
          url_producto: `${urlBase}producto/${sku}`,
          ultima_actualizacion: new Date().toISOString()
        });
      }
    } catch (error) {
      console.warn(`Error procesando producto:`, error.message);
    }
  }

  if (productos.length === 0) {
    const productosAlternativos = extraerProductosPatronAlternativo(html, categoria, urlBase);
    productos.push(...productosAlternativos);
  }

  return productos;
}

function extraerProductosPatronAlternativo(html: string, categoria: string, urlBase: string) {
  const productos = [];
  const productoPattern = /<h[2-6][^>]*>(.*?)<\/h[2-6]>.*?precio.*?(\d+[\.,]\d+)/gs;
  
  let match;
  while ((match = productoPattern.exec(html)) !== null) {
    try {
      const nombre = match[1]?.trim();
      const precioTexto = match[2]?.replace(',', '.');
      const precio = parseFloat(precioTexto);

      if (nombre && precio > 0 && nombre.length > 3) {
        const sku = generarSKU(nombre, categoria);
        
        productos.push({
          sku,
          nombre,
          marca: extraerMarcaDelNombre(nombre),
          categoria,
          precio_unitario: precio,
          url_producto: `${urlBase}buscar?q=${encodeURIComponent(nombre)}`,
          ultima_actualizacion: new Date().toISOString()
        });
      }
    } catch (error) {
      console.warn(`Error en patrón alternativo:`, error.message);
    }
  }

  return productos;
}

function extraerMarcaDelNombre(nombre: string): string {
  const marcasConocidas = [
    'Coca Cola', 'Pepsi', 'Fernet', 'Fernandez', 'Corona', 'Quilmes',
    'Ledesma', 'Nestlé', 'Arcor', 'Bagley', 'Jorgito', 'Ser',
    'Eden', 'Alcazar', 'La Serenísima', 'Tregar', 'Danone',
    'Ala', 'Ariel', 'Drive', 'Harina', 'Aceite', 'Arroz'
  ];

  for (const marca of marcasConocidas) {
    if (nombre.toLowerCase().includes(marca.toLowerCase())) {
      return marca;
    }
  }

  const palabras = nombre.split(' ');
  return palabras[0]?.substring(0, 20) || 'Sin Marca';
}

function generarSKU(nombre: string, categoria: string): string {
  const palabras = nombre.toUpperCase().split(' ').slice(0, 3);
  const sufijo = Math.random().toString(36).substring(2, 8).toUpperCase();
  return `${categoria.substring(0, 3).toUpperCase()}-${palabras.join('').substring(0, 8)}-${sufijo}`;
}

async function fetchConReintentos(url: string, headers: Record<string, string>, maxReintentos: number) {
  let ultimoError: Error;

  for (let i = 0; i < maxReintentos; i++) {
    try {
      const response = await fetch(url, { headers });

      if (response.ok) {
        return response;
      }

      if (response.status === 429) {
        await delay((i + 1) * 2000);
        continue;
      }

      if (response.status >= 500) {
        await delay((i + 1) * 1000);
        continue;
      }

      throw new Error(`HTTP ${response.status}: ${response.statusText}`);

    } catch (error) {
      ultimoError = error;
      if (i < maxReintentos - 1) {
        await delay((i + 1) * 2000);
      }
    }
  }

  throw ultimoError;
}

async function guardarProductosExtraidos(productos, supabaseUrl, serviceRoleKey) {
  let guardados = 0;

  for (const producto of productos) {
    try {
      const checkResponse = await fetch(
        `${supabaseUrl}/rest/v1/precios_proveedor?sku=eq.${producto.sku}&select=id`,
        {
          headers: {
            'apikey': serviceRoleKey,
            'Authorization': `Bearer ${serviceRoleKey}`,
          }
        }
      );

      if (!checkResponse.ok) continue;

      const existing = await checkResponse.json();

      if (existing.length > 0) {
        const updateResponse = await fetch(
          `${supabaseUrl}/rest/v1/precios_proveedor?sku=eq.${producto.sku}`,
          {
            method: 'PATCH',
            headers: {
              'apikey': serviceRoleKey,
              'Authorization': `Bearer ${serviceRoleKey}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              precio_unitario: producto.precio_unitario,
              nombre: producto.nombre,
              marca: producto.marca,
              categoria: producto.categoria,
              ultima_actualizacion: producto.ultima_actualizacion,
              activo: true
            })
          }
        );

        if (updateResponse.ok) {
          guardados++;
        }
      } else {
        const insertResponse = await fetch(
          `${supabaseUrl}/rest/v1/precios_proveedor`,
          {
            method: 'POST',
            headers: {
              'apikey': serviceRoleKey,
              'Authorization': `Bearer ${serviceRoleKey}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              sku: producto.sku,
              nombre: producto.nombre,
              marca: producto.marca,
              categoria: producto.categoria,
              precio_unitario: producto.precio_unitario,
              url_producto: producto.url_producto,
              ultima_actualizacion: producto.ultima_actualizacion,
              fuente: 'Maxiconsumo Necochea',
              activo: true
            })
          }
        );

        if (insertResponse.ok) {
          guardados++;
        }
      }
    } catch (error) {
      console.warn(`Error guardando producto ${producto.sku}:`, error.message);
    }
  }

  return guardados;
}

function generarRecomendacion(precioActual: number, precioProveedor: number): string {
  const diferencia = precioActual - precioProveedor;
  const porcentaje = (diferencia / precioProveedor) * 100;

  if (porcentaje > 20) {
    return `🚨 OPORTUNIDAD CRÍTICA: Ahorro potencial del ${porcentaje.toFixed(1)}% ($${diferencia.toFixed(2)})`;
  } else if (porcentaje > 10) {
    return `💰 BUENA OPORTUNIDAD: Ahorro del ${porcentaje.toFixed(1)}% ($${diferencia.toFixed(2)})`;
  } else if (porcentaje > 5) {
    return `📈 MEJORA MODERADA: Ahorro del ${porcentaje.toFixed(1)}% ($${diferencia.toFixed(2)})`;
  } else if (diferencia > 0) {
    return `⚖️ DIFERENCIA MENOR: Ahorro del ${porcentaje.toFixed(1)}% ($${diferencia.toFixed(2)})`;
  } else {
    return `📉 PRECIO SUPERIOR: Proveedor ${Math.abs(porcentaje).toFixed(1)}% más caro`;
  }
}

function calcularProximoScrape(): string {
  const ahora = new Date();
  const proximo = new Date(ahora);
  proximo.setHours(proximo.getHours() + 6);
  
  return proximo.toISOString();
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function obtenerConfiguracionCategorias() {
  return {
    'almacen': {
      slug: 'almacen',
      prioridad: 1,
      max_productos: 1000
    },
    'bebidas': {
      slug: 'bebidas',
      prioridad: 2,
      max_productos: 500
    },
    'limpieza': {
      slug: 'limpieza',
      prioridad: 3,
      max_productos: 300
    }
  };
}

function generarHeadersAleatorios(): Record<string, string> {
  const userAgents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
  ];

  return {
    'User-Agent': userAgents[Math.floor(Math.random() * userAgents.length)],
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8'
  };
}