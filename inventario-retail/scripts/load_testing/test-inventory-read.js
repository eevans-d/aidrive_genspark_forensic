/**
 * Load Test: Inventory Read Endpoint (GET)
 * 
 * Escenario: Lectura de inventario bajo carga
 * Objetivo: Verificar performance de consultas GET /api/inventory
 * 
 * Umbrales:
 * - P95 latency < 300ms
 * - Error rate < 0.5%
 * - Throughput > 100 req/s
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Métricas custom
const errorRate = new Rate('errors');
const readDuration = new Trend('inventory_read_duration');
const requestCounter = new Counter('total_requests');
const authErrors = new Counter('auth_errors');

// Configuración del test
export const options = {
  stages: [
    { duration: '1m', target: 30 },    // Ramp-up gradual
    { duration: '2m', target: 30 },    // Carga sostenida
    { duration: '1m', target: 60 },    // Incremento de carga
    { duration: '2m', target: 60 },    // Mantener carga alta
    { duration: '1m', target: 0 },     // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<300'],     // 95% < 300ms
    http_req_failed: ['rate<0.005'],      // Error rate < 0.5%
    http_reqs: ['rate>100'],              // > 100 req/s
    errors: ['rate<0.005'],
    auth_errors: ['count<10'],            // Máximo 10 errores auth
  },
  summaryTrendStats: ['min', 'med', 'avg', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

// Configuración
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const API_KEY = __ENV.API_KEY || 'test-api-key-dev';

// Headers para autenticación
const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json',
};

export default function () {
  group('Inventory Read Operations', () => {
    
    // Test 1: Get all products
    group('GET /api/inventory', () => {
      const response = http.get(
        `${BASE_URL}/api/inventory`,
        { headers }
      );
      
      const checkResult = check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 300ms': (r) => r.timings.duration < 300,
        'has products array': (r) => {
          try {
            const body = JSON.parse(r.body);
            return Array.isArray(body.products);
          } catch (e) {
            return false;
          }
        },
        'products not empty': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.products && body.products.length > 0;
          } catch (e) {
            return false;
          }
        },
      });

      // Registrar métricas
      errorRate.add(!checkResult);
      readDuration.add(response.timings.duration);
      requestCounter.add(1);
      
      if (response.status === 401 || response.status === 403) {
        authErrors.add(1);
      }
    });

    sleep(0.5);

    // Test 2: Get product by SKU (simular búsqueda específica)
    group('GET /api/inventory/:sku', () => {
      const testSKUs = ['SKU001', 'SKU002', 'SKU003', 'SKU004', 'SKU005'];
      const randomSKU = testSKUs[Math.floor(Math.random() * testSKUs.length)];
      
      const response = http.get(
        `${BASE_URL}/api/inventory/${randomSKU}`,
        { headers }
      );
      
      const checkResult = check(response, {
        'status is 200 or 404': (r) => r.status === 200 || r.status === 404,
        'response time < 200ms': (r) => r.timings.duration < 200,
        'has valid response': (r) => {
          if (r.status === 404) return true;
          try {
            const body = JSON.parse(r.body);
            return body.sku !== undefined;
          } catch (e) {
            return false;
          }
        },
      });

      errorRate.add(!checkResult);
      readDuration.add(response.timings.duration);
      requestCounter.add(1);
    });

    sleep(0.5);

    // Test 3: Query with filters
    group('GET /api/inventory?filters', () => {
      const filters = [
        'status=available',
        'category=lacteos',
        'low_stock=true',
        'status=available&category=bebidas',
      ];
      const randomFilter = filters[Math.floor(Math.random() * filters.length)];
      
      const response = http.get(
        `${BASE_URL}/api/inventory?${randomFilter}`,
        { headers }
      );
      
      const checkResult = check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 350ms': (r) => r.timings.duration < 350,
        'has products array': (r) => {
          try {
            const body = JSON.parse(r.body);
            return Array.isArray(body.products);
          } catch (e) {
            return false;
          }
        },
      });

      errorRate.add(!checkResult);
      readDuration.add(response.timings.duration);
      requestCounter.add(1);
    });
  });

  sleep(1);
}

export function setup() {
  console.log('🚀 Iniciando load test: Inventory Read Operations');
  console.log(`📍 Target URL: ${BASE_URL}/api/inventory`);
  console.log(`🔑 Using API Key: ${API_KEY.substring(0, 10)}...`);
  
  // Verificar autenticación
  const response = http.get(
    `${BASE_URL}/api/inventory`,
    { headers }
  );
  
  if (response.status === 401) {
    throw new Error('Authentication failed. Check API_KEY.');
  }
  
  if (response.status !== 200) {
    console.warn(`⚠️  Warning: Unexpected status ${response.status}`);
  }
  
  return { startTime: new Date() };
}

export function teardown(data) {
  const endTime = new Date();
  const duration = (endTime - data.startTime) / 1000;
  console.log(`✅ Test completado en ${duration.toFixed(2)} segundos`);
}

export function handleSummary(data) {
  const summary = generateTextSummary(data);
  
  return {
    'stdout': summary,
    'results/inventory-read-summary.json': JSON.stringify(data, null, 2),
    'results/inventory-read-summary.txt': summary,
  };
}

function generateTextSummary(data) {
  let summary = '\n';
  summary += '📊 Load Test Summary - Inventory Read Operations\n';
  summary += '='.repeat(60) + '\n\n';
  
  // Requests
  summary += `Total Requests: ${data.metrics.http_reqs.values.count}\n`;
  summary += `Failed Requests: ${data.metrics.http_req_failed.values.passes || 0}\n`;
  summary += `Request Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s\n`;
  summary += `Auth Errors: ${data.metrics.auth_errors ? data.metrics.auth_errors.values.count : 0}\n\n`;
  
  // Latency
  summary += 'Response Time:\n';
  summary += `  Min: ${data.metrics.http_req_duration.values.min.toFixed(2)}ms\n`;
  summary += `  Med: ${data.metrics.http_req_duration.values.med.toFixed(2)}ms\n`;
  summary += `  Avg: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
  summary += `  P90: ${data.metrics.http_req_duration.values['p(90)'].toFixed(2)}ms\n`;
  summary += `  P95: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `  P99: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  summary += `  Max: ${data.metrics.http_req_duration.values.max.toFixed(2)}ms\n\n`;
  
  // Thresholds
  summary += 'Thresholds:\n';
  const thresholds = data.root_group.checks || [];
  thresholds.forEach(check => {
    const passed = check.passes === check.fails ? '✅' : '❌';
    summary += `  ${passed} ${check.name}: ${check.passes}/${check.fails + check.passes}\n`;
  });
  
  return summary;
}
