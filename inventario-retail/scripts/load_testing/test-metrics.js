/**
 * Load Test: Metrics Endpoint
 * 
 * Escenario: Monitoreo de métricas bajo carga
 * Objetivo: Verificar que Prometheus pueda scrape métricas sin impacto
 * 
 * Umbrales:
 * - P95 latency < 200ms
 * - Error rate < 0.1%
 * - Throughput > 50 req/s
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Métricas custom
const errorRate = new Rate('errors');
const metricsDuration = new Trend('metrics_duration');
const requestCounter = new Counter('total_requests');
const authErrors = new Counter('auth_errors');

// Configuración del test
export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Ramp-up
    { duration: '2m', target: 20 },    // Carga constante (simular Prometheus scrape)
    { duration: '30s', target: 50 },   // Carga alta momentánea
    { duration: '1m', target: 50 },    // Mantener
    { duration: '30s', target: 0 },    // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],     // 95% < 200ms
    http_req_failed: ['rate<0.001'],      // Error rate < 0.1%
    http_reqs: ['rate>50'],               // > 50 req/s
    errors: ['rate<0.001'],
  },
  summaryTrendStats: ['min', 'med', 'avg', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

// Configuración
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const API_KEY = __ENV.API_KEY || 'test-api-key-dev';

const headers = {
  'X-API-Key': API_KEY,
};

export default function () {
  // Request al endpoint /metrics
  const response = http.get(
    `${BASE_URL}/metrics`,
    { headers }
  );
  
  const checkResult = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
    'is prometheus format': (r) => {
      return r.body.includes('# HELP') && r.body.includes('# TYPE');
    },
    'has dashboard metrics': (r) => {
      return r.body.includes('dashboard_requests_total') ||
             r.body.includes('dashboard_errors_total') ||
             r.body.includes('dashboard_request_duration');
    },
    'response not empty': (r) => r.body.length > 100,
  });

  // Registrar métricas
  errorRate.add(!checkResult);
  metricsDuration.add(response.timings.duration);
  requestCounter.add(1);
  
  if (response.status === 401 || response.status === 403) {
    authErrors.add(1);
  }

  // Simular intervalo de scrape de Prometheus (15s)
  sleep(0.5);
}

export function setup() {
  console.log('🚀 Iniciando load test: Metrics Endpoint');
  console.log(`📍 Target URL: ${BASE_URL}/metrics`);
  console.log(`🔑 Using API Key: ${API_KEY.substring(0, 10)}...`);
  console.log('📊 Simulating Prometheus scrape pattern');
  
  // Verificar autenticación y formato
  const response = http.get(
    `${BASE_URL}/metrics`,
    { headers }
  );
  
  if (response.status === 401) {
    throw new Error('Authentication failed. Check API_KEY.');
  }
  
  if (response.status !== 200) {
    throw new Error(`Metrics endpoint not available. Status: ${response.status}`);
  }
  
  if (!response.body.includes('# HELP')) {
    console.warn('⚠️  Warning: Response may not be in Prometheus format');
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
    'results/metrics-summary.json': JSON.stringify(data, null, 2),
    'results/metrics-summary.txt': summary,
  };
}

function generateTextSummary(data) {
  let summary = '\n';
  summary += '📊 Load Test Summary - Metrics Endpoint\n';
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
  
  // Prometheus compatibility
  summary += '📈 Prometheus Compatibility:\n';
  summary += `  All responses in Prometheus format: ${checkPrometheusFormat(data)}\n`;
  summary += `  Avg response size: ${calculateAvgResponseSize(data)} bytes\n\n`;
  
  return summary;
}

function checkPrometheusFormat(data) {
  // Verificar si todos los checks de formato pasaron
  if (data.root_group && data.root_group.checks) {
    const formatCheck = data.root_group.checks.find(c => c.name === 'is prometheus format');
    if (formatCheck) {
      return formatCheck.passes === formatCheck.fails + formatCheck.passes ? '✅ Yes' : '❌ No';
    }
  }
  return 'Unknown';
}

function calculateAvgResponseSize(data) {
  if (data.metrics.http_req_receiving && data.metrics.http_req_receiving.values) {
    return Math.round(data.metrics.http_req_receiving.values.avg);
  }
  return 'N/A';
}
