/**
 * Load Test: Inventory Write Endpoint (POST)
 * 
 * Escenario: Escritura de inventario bajo carga
 * Objetivo: Verificar performance de operaciones POST /api/inventory
 * 
 * Umbrales:
 * - P95 latency < 500ms (write operations son más lentas)
 * - Error rate < 1%
 * - Throughput > 50 req/s
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Métricas custom
const errorRate = new Rate('errors');
const writeDuration = new Trend('inventory_write_duration');
const requestCounter = new Counter('total_requests');
const successfulWrites = new Counter('successful_writes');
const failedWrites = new Counter('failed_writes');

// Configuración del test
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp-up conservador
    { duration: '1m', target: 10 },    // Carga baja sostenida
    { duration: '30s', target: 25 },   // Incremento medio
    { duration: '1m', target: 25 },    // Mantener carga media
    { duration: '30s', target: 50 },   // Carga alta
    { duration: '1m', target: 50 },    // Mantener carga alta
    { duration: '30s', target: 0 },    // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],     // 95% < 500ms
    http_req_failed: ['rate<0.01'],       // Error rate < 1%
    http_reqs: ['rate>50'],               // > 50 req/s
    errors: ['rate<0.01'],
    successful_writes: ['count>1000'],    // Al menos 1000 writes exitosos
  },
  summaryTrendStats: ['min', 'med', 'avg', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

// Configuración
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const API_KEY = __ENV.API_KEY || 'test-api-key-dev';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json',
};

// Datos de prueba para generar productos
const categories = ['lacteos', 'bebidas', 'panaderia', 'carnes', 'verduras', 'limpieza'];
const suppliers = ['SUPPLIER-A', 'SUPPLIER-B', 'SUPPLIER-C', 'SUPPLIER-D'];

function generateRandomProduct() {
  const timestamp = Date.now();
  const randomId = Math.floor(Math.random() * 100000);
  
  return {
    sku: `TEST-SKU-${timestamp}-${randomId}`,
    nombre: `Producto Test ${randomId}`,
    descripcion: `Descripción del producto de prueba generado automáticamente`,
    categoria: categories[Math.floor(Math.random() * categories.length)],
    precio_venta: parseFloat((Math.random() * 1000 + 50).toFixed(2)),
    costo_adquisicion: parseFloat((Math.random() * 500 + 20).toFixed(2)),
    stock_actual: Math.floor(Math.random() * 200),
    stock_minimo: Math.floor(Math.random() * 20 + 5),
    proveedor: suppliers[Math.floor(Math.random() * suppliers.length)],
    ubicacion: `Pasillo-${Math.floor(Math.random() * 10 + 1)}`,
    codigo_barras: `${timestamp}${randomId}`,
    unidad_medida: 'unidad',
  };
}

export default function () {
  group('Inventory Write Operations', () => {
    
    // Test 1: Create new product
    group('POST /api/inventory - Create Product', () => {
      const productData = generateRandomProduct();
      
      const response = http.post(
        `${BASE_URL}/api/inventory`,
        JSON.stringify(productData),
        { headers }
      );
      
      const checkResult = check(response, {
        'status is 201': (r) => r.status === 201,
        'response time < 500ms': (r) => r.timings.duration < 500,
        'has product id': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.id !== undefined || body.sku !== undefined;
          } catch (e) {
            return false;
          }
        },
        'returns created product': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.sku === productData.sku;
          } catch (e) {
            return false;
          }
        },
      });

      // Registrar métricas
      errorRate.add(!checkResult);
      writeDuration.add(response.timings.duration);
      requestCounter.add(1);
      
      if (response.status === 201) {
        successfulWrites.add(1);
      } else {
        failedWrites.add(1);
      }
    });

    sleep(1);

    // Test 2: Update stock (simulación de venta)
    group('POST /api/inventory/update-stock', () => {
      const updateData = {
        sku: `SKU${Math.floor(Math.random() * 100).toString().padStart(3, '0')}`,
        quantity: -Math.floor(Math.random() * 5 + 1), // Reducir stock (venta)
        reason: 'venta',
      };
      
      const response = http.post(
        `${BASE_URL}/api/inventory/update-stock`,
        JSON.stringify(updateData),
        { headers }
      );
      
      const checkResult = check(response, {
        'status is 200 or 404': (r) => r.status === 200 || r.status === 404,
        'response time < 400ms': (r) => r.timings.duration < 400,
        'has success field': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.success !== undefined;
          } catch (e) {
            return false;
          }
        },
      });

      errorRate.add(!checkResult);
      writeDuration.add(response.timings.duration);
      requestCounter.add(1);
      
      if (response.status === 200) {
        successfulWrites.add(1);
      }
    });

    sleep(1);

    // Test 3: Bulk update (multiple products)
    group('POST /api/inventory/bulk-update', () => {
      const bulkData = {
        updates: [
          { sku: 'SKU001', field: 'precio_venta', value: 125.50 },
          { sku: 'SKU002', field: 'precio_venta', value: 89.90 },
          { sku: 'SKU003', field: 'stock_minimo', value: 10 },
        ],
      };
      
      const response = http.post(
        `${BASE_URL}/api/inventory/bulk-update`,
        JSON.stringify(bulkData),
        { headers }
      );
      
      const checkResult = check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 600ms': (r) => r.timings.duration < 600,
        'has results': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.updated !== undefined || body.results !== undefined;
          } catch (e) {
            return false;
          }
        },
      });

      errorRate.add(!checkResult);
      writeDuration.add(response.timings.duration);
      requestCounter.add(1);
      
      if (response.status === 200) {
        successfulWrites.add(1);
      }
    });
  });

  sleep(2);
}

export function setup() {
  console.log('🚀 Iniciando load test: Inventory Write Operations');
  console.log(`📍 Target URL: ${BASE_URL}/api/inventory`);
  console.log(`🔑 Using API Key: ${API_KEY.substring(0, 10)}...`);
  console.log('⚠️  ADVERTENCIA: Este test creará datos de prueba en el sistema');
  
  // Verificar autenticación
  const testProduct = generateRandomProduct();
  const response = http.post(
    `${BASE_URL}/api/inventory`,
    JSON.stringify(testProduct),
    { headers }
  );
  
  if (response.status === 401) {
    throw new Error('Authentication failed. Check API_KEY.');
  }
  
  if (response.status !== 201 && response.status !== 200) {
    console.warn(`⚠️  Warning: Unexpected status ${response.status}`);
    console.warn(`Response: ${response.body}`);
  }
  
  return { startTime: new Date() };
}

export function teardown(data) {
  const endTime = new Date();
  const duration = (endTime - data.startTime) / 1000;
  console.log(`✅ Test completado en ${duration.toFixed(2)} segundos`);
  console.log('🧹 Considere limpiar datos de prueba creados durante el test');
}

export function handleSummary(data) {
  const summary = generateTextSummary(data);
  
  return {
    'stdout': summary,
    'results/inventory-write-summary.json': JSON.stringify(data, null, 2),
    'results/inventory-write-summary.txt': summary,
  };
}

function generateTextSummary(data) {
  let summary = '\n';
  summary += '📊 Load Test Summary - Inventory Write Operations\n';
  summary += '='.repeat(60) + '\n\n';
  
  // Requests
  summary += `Total Requests: ${data.metrics.http_reqs.values.count}\n`;
  summary += `Failed Requests: ${data.metrics.http_req_failed.values.passes || 0}\n`;
  summary += `Request Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s\n`;
  summary += `Successful Writes: ${data.metrics.successful_writes ? data.metrics.successful_writes.values.count : 0}\n`;
  summary += `Failed Writes: ${data.metrics.failed_writes ? data.metrics.failed_writes.values.count : 0}\n\n`;
  
  // Latency
  summary += 'Response Time:\n';
  summary += `  Min: ${data.metrics.http_req_duration.values.min.toFixed(2)}ms\n`;
  summary += `  Med: ${data.metrics.http_req_duration.values.med.toFixed(2)}ms\n`;
  summary += `  Avg: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
  summary += `  P90: ${data.metrics.http_req_duration.values['p(90)'].toFixed(2)}ms\n`;
  summary += `  P95: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `  P99: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  summary += `  Max: ${data.metrics.http_req_duration.values.max.toFixed(2)}ms\n\n`;
  
  // Success Rate
  const totalReqs = data.metrics.http_reqs.values.count;
  const successWrites = data.metrics.successful_writes ? data.metrics.successful_writes.values.count : 0;
  const successRate = totalReqs > 0 ? (successWrites / totalReqs * 100).toFixed(2) : 0;
  summary += `Write Success Rate: ${successRate}%\n\n`;
  
  return summary;
}
