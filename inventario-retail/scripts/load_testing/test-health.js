/**
 * Load Test: Health Check Endpoint
 * 
 * Escenario: Baseline performance test
 * Objetivo: Verificar que el endpoint /health responde correctamente bajo carga
 * 
 * Umbrales:
 * - P95 latency < 100ms
 * - Error rate < 0.1%
 * - Throughput > 200 req/s
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Métricas custom
const errorRate = new Rate('errors');
const healthCheckDuration = new Trend('health_check_duration');
const requestCounter = new Counter('total_requests');

// Configuración del test
export const options = {
  stages: [
    { duration: '30s', target: 50 },   // Ramp-up a 50 usuarios
    { duration: '1m', target: 50 },    // Mantener 50 usuarios
    { duration: '30s', target: 100 },  // Ramp-up a 100 usuarios
    { duration: '1m', target: 100 },   // Mantener 100 usuarios
    { duration: '30s', target: 0 },    // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<100'],     // 95% de requests < 100ms
    http_req_failed: ['rate<0.001'],      // Error rate < 0.1%
    http_reqs: ['rate>200'],              // Throughput > 200 req/s
    errors: ['rate<0.001'],
  },
  summaryTrendStats: ['min', 'med', 'avg', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

// URL base (puede ser sobrescrita desde CLI)
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  // Request al endpoint /health
  const response = http.get(`${BASE_URL}/health`);
  
  // Verificaciones
  const checkResult = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 100ms': (r) => r.timings.duration < 100,
    'has status field': (r) => r.json('status') !== undefined,
    'status is healthy': (r) => r.json('status') === 'healthy',
  });

  // Registrar métricas
  errorRate.add(!checkResult);
  healthCheckDuration.add(response.timings.duration);
  requestCounter.add(1);

  // Pequeña pausa entre requests (simular comportamiento real)
  sleep(0.1);
}

/**
 * Setup function - Se ejecuta una vez antes del test
 */
export function setup() {
  console.log('🚀 Iniciando load test: Health Check Endpoint');
  console.log(`📍 Target URL: ${BASE_URL}/health`);
  
  // Verificar que el servicio esté disponible
  const response = http.get(`${BASE_URL}/health`);
  if (response.status !== 200) {
    throw new Error(`Service not available. Status: ${response.status}`);
  }
  
  return { startTime: new Date() };
}

/**
 * Teardown function - Se ejecuta una vez después del test
 */
export function teardown(data) {
  const endTime = new Date();
  const duration = (endTime - data.startTime) / 1000;
  console.log(`✅ Test completado en ${duration.toFixed(2)} segundos`);
}

/**
 * Handle summary - Custom summary output
 */
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'results/health-check-summary.json': JSON.stringify(data, null, 2),
  };
}

// Utility function para summary
function textSummary(data, options) {
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;
  
  let summary = '\n';
  summary += `${indent}📊 Load Test Summary - Health Check\n`;
  summary += `${indent}${'='.repeat(50)}\n\n`;
  
  // Requests
  summary += `${indent}Total Requests: ${data.metrics.http_reqs.values.count}\n`;
  summary += `${indent}Failed Requests: ${data.metrics.http_req_failed.values.passes || 0}\n`;
  summary += `${indent}Request Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s\n\n`;
  
  // Latency
  summary += `${indent}Response Time:\n`;
  summary += `${indent}  Min: ${data.metrics.http_req_duration.values.min.toFixed(2)}ms\n`;
  summary += `${indent}  Med: ${data.metrics.http_req_duration.values.med.toFixed(2)}ms\n`;
  summary += `${indent}  Avg: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
  summary += `${indent}  P95: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `${indent}  Max: ${data.metrics.http_req_duration.values.max.toFixed(2)}ms\n\n`;
  
  return summary;
}
