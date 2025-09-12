#!/usr/bin/env python3
"""
Cache Performance Testing Script
===============================

Script para realizar tests comparativos de performance antes y después
de implementar cache inteligente.

Features:
- Benchmark endpoints con y sin cache
- Medición latencia, throughput y hit rates
- Comparación automática de resultados
- Generación de reportes de mejora
- Tests de carga simulados
- Análisis estadístico de resultados

Usage:
    python performance_test.py --mode benchmark --concurrent 10
    python performance_test.py --mode comparison --baseline baseline.json
    python performance_test.py --mode load --duration 60
    python performance_test.py --mode report --output perf_report.json
"""

import asyncio
import aiohttp
import argparse
import json
import time
import statistics
import sys
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging
import random

# Add project root to path
sys.path.append('/home/user/inventario-retail')

from cache import get_cache_status, reset_all_cache_stats

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """Suite completa de tests de performance para cache"""

    def __init__(self, base_urls: Dict[str, str] = None):
        self.base_urls = base_urls or {
            'deposito': 'http://localhost:8001',
            'negocio': 'http://localhost:8002',
            'ml': 'http://localhost:8003'
        }
        self.session = None
        self.test_results = []

    async def __aenter__(self):
        """Context manager entrada"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager salida"""
        if self.session:
            await self.session.close()

    async def single_request_benchmark(self, 
                                     service: str, 
                                     endpoint: str, 
                                     method: str = 'GET',
                                     data: Dict = None) -> Dict[str, Any]:
        """
        Benchmark de una sola request

        Returns:
            Dict con métricas de la request
        """
        url = f"{self.base_urls[service]}{endpoint}"

        start_time = time.time()

        try:
            if method.upper() == 'GET':
                async with self.session.get(url) as response:
                    response_data = await response.json()
                    status_code = response.status
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data) as response:
                    response_data = await response.json()
                    status_code = response.status
            else:
                raise ValueError(f"Método {method} no soportado")

            end_time = time.time()
            latency = (end_time - start_time) * 1000  # ms

            return {
                'service': service,
                'endpoint': endpoint,
                'method': method,
                'latency_ms': latency,
                'status_code': status_code,
                'success': 200 <= status_code < 300,
                'timestamp': datetime.now().isoformat(),
                'response_size': len(str(response_data))
            }

        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000

            return {
                'service': service,
                'endpoint': endpoint,
                'method': method,
                'latency_ms': latency,
                'status_code': 0,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def concurrent_benchmark(self, 
                                 service: str,
                                 endpoint: str,
                                 concurrent_requests: int = 10,
                                 total_requests: int = 100,
                                 method: str = 'GET',
                                 data: Dict = None) -> Dict[str, Any]:
        """
        Benchmark con requests concurrentes

        Returns:
            Estadísticas agregadas del benchmark
        """
        logger.info(f"🚀 Benchmark {service}{endpoint}: {total_requests} requests, {concurrent_requests} concurrentes")

        # Semáforo para controlar concurrencia
        semaphore = asyncio.Semaphore(concurrent_requests)

        async def limited_request():
            async with semaphore:
                return await self.single_request_benchmark(service, endpoint, method, data)

        # Ejecutar todas las requests
        start_test_time = time.time()
        tasks = [limited_request() for _ in range(total_requests)]
        results = await asyncio.gather(*tasks)
        end_test_time = time.time()

        # Analizar resultados
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]

        if successful_results:
            latencies = [r['latency_ms'] for r in successful_results]

            stats = {
                'service': service,
                'endpoint': endpoint,
                'method': method,
                'test_duration_seconds': end_test_time - start_test_time,
                'total_requests': total_requests,
                'concurrent_requests': concurrent_requests,
                'successful_requests': len(successful_results),
                'failed_requests': len(failed_results),
                'success_rate_percent': (len(successful_results) / total_requests) * 100,
                'latency_stats': {
                    'min_ms': min(latencies),
                    'max_ms': max(latencies),
                    'mean_ms': statistics.mean(latencies),
                    'median_ms': statistics.median(latencies),
                    'p95_ms': self._percentile(latencies, 95),
                    'p99_ms': self._percentile(latencies, 99),
                    'std_dev_ms': statistics.stdev(latencies) if len(latencies) > 1 else 0
                },
                'throughput': {
                    'requests_per_second': total_requests / (end_test_time - start_test_time),
                    'avg_response_time_ms': statistics.mean(latencies)
                },
                'errors': [{'error': r.get('error', 'Unknown'), 'count': 1} for r in failed_results],
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Todos los requests fallaron
            stats = {
                'service': service,
                'endpoint': endpoint,
                'error': 'All requests failed',
                'total_requests': total_requests,
                'failed_requests': len(failed_results),
                'timestamp': datetime.now().isoformat()
            }

        return stats

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcula percentil de una lista de valores"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    async def cache_effectiveness_test(self) -> Dict[str, Any]:
        """
        Test específico para medir efectividad del cache

        Hace múltiples requests al mismo endpoint para medir hit rate
        """
        logger.info("📊 Test de efectividad del cache")

        # Reset stats para measurement limpio
        try:
            reset_all_cache_stats()
            logger.info("🔄 Cache stats reseteadas")
        except Exception as e:
            logger.warning(f"No se pudieron resetear stats: {e}")

        # Endpoints para test (productos específicos)
        test_endpoints = [
            ('deposito', '/productos/1'),
            ('deposito', '/productos/2'), 
            ('deposito', '/productos/3'),
            ('deposito', '/stock/resumen'),
            ('negocio', '/ocr/estadisticas'),
        ]

        cache_results = []

        for service, endpoint in test_endpoints:
            logger.info(f"🎯 Testing cache effectiveness: {service}{endpoint}")

            # Primera request (cache miss esperado)
            first_request = await self.single_request_benchmark(service, endpoint)

            # Esperar un poco para que se procese el cache
            await asyncio.sleep(0.1)

            # Múltiples requests para test hit rate
            hit_test_results = []
            for _ in range(20):
                result = await self.single_request_benchmark(service, endpoint)
                hit_test_results.append(result)
                await asyncio.sleep(0.05)  # Pequeña pausa entre requests

            # Analizar mejora de latencia
            successful_hits = [r for r in hit_test_results if r['success']]
            if successful_hits:
                hit_latencies = [r['latency_ms'] for r in successful_hits]
                avg_hit_latency = statistics.mean(hit_latencies)

                improvement = ((first_request['latency_ms'] - avg_hit_latency) / first_request['latency_ms']) * 100

                cache_results.append({
                    'service': service,
                    'endpoint': endpoint,
                    'first_request_latency_ms': first_request['latency_ms'],
                    'avg_cached_latency_ms': avg_hit_latency,
                    'latency_improvement_percent': improvement,
                    'cache_hit_tests': len(successful_hits),
                    'consistency': statistics.stdev(hit_latencies) if len(hit_latencies) > 1 else 0
                })

        return {
            'test_type': 'cache_effectiveness',
            'timestamp': datetime.now().isoformat(),
            'results': cache_results,
            'summary': {
                'avg_improvement_percent': statistics.mean([r['latency_improvement_percent'] for r in cache_results if r['latency_improvement_percent'] > 0]),
                'endpoints_tested': len(cache_results)
            }
        }

    async def load_test(self, duration_seconds: int = 60, rps_target: int = 50) -> Dict[str, Any]:
        """
        Test de carga sostenida

        Args:
            duration_seconds: Duración del test
            rps_target: Requests por segundo objetivo
        """
        logger.info(f"⚡ Load test: {duration_seconds}s @ {rps_target} RPS")

        # Endpoints para load test
        endpoints = [
            ('deposito', '/productos'),
            ('deposito', '/productos/1'),
            ('deposito', '/stock/resumen'),
            ('negocio', '/ocr/estadisticas'),
        ]

        start_time = time.time()
        results = []
        request_count = 0

        # Calcular intervalo entre requests
        interval = 1.0 / rps_target

        while (time.time() - start_time) < duration_seconds:
            # Seleccionar endpoint random
            service, endpoint = random.choice(endpoints)

            # Ejecutar request
            result = await self.single_request_benchmark(service, endpoint)
            results.append(result)
            request_count += 1

            # Control de rate
            elapsed = time.time() - start_time
            expected_requests = elapsed * rps_target
            if request_count >= expected_requests:
                sleep_time = interval - (time.time() - start_time - (request_count - 1) * interval)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        # Analizar resultados
        total_duration = time.time() - start_time
        successful_results = [r for r in results if r['success']]

        if successful_results:
            latencies = [r['latency_ms'] for r in successful_results]

            return {
                'test_type': 'load_test',
                'duration_seconds': total_duration,
                'target_rps': rps_target,
                'actual_rps': len(results) / total_duration,
                'total_requests': len(results),
                'successful_requests': len(successful_results),
                'failed_requests': len(results) - len(successful_results),
                'success_rate_percent': (len(successful_results) / len(results)) * 100,
                'latency_stats': {
                    'min_ms': min(latencies),
                    'max_ms': max(latencies),
                    'mean_ms': statistics.mean(latencies),
                    'median_ms': statistics.median(latencies),
                    'p95_ms': self._percentile(latencies, 95),
                    'p99_ms': self._percentile(latencies, 99)
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'test_type': 'load_test',
                'error': 'All requests failed during load test',
                'duration_seconds': total_duration,
                'total_requests': len(results),
                'timestamp': datetime.now().isoformat()
            }

    async def comprehensive_benchmark(self, concurrent: int = 10) -> Dict[str, Any]:
        """Benchmark completo de todos los endpoints críticos"""
        logger.info("🎯 Ejecutando benchmark completo del sistema")

        # Definir endpoints para test
        endpoints_to_test = [
            # AgenteDepósito
            ('deposito', '/productos', 'GET'),
            ('deposito', '/productos/1', 'GET'),
            ('deposito', '/productos/2', 'GET'),
            ('deposito', '/stock/resumen', 'GET'),
            ('deposito', '/health', 'GET'),

            # AgenteNegocio
            ('negocio', '/health', 'GET'),
            ('negocio', '/ocr/estadisticas', 'GET'),
            ('negocio', '/pricing/analisis-mercado', 'GET'),

            # Tests de cache stats
            ('deposito', '/cache/stats', 'GET'),
            ('negocio', '/cache/stats', 'GET'),
        ]

        benchmark_results = []

        for service, endpoint, method in endpoints_to_test:
            try:
                result = await self.concurrent_benchmark(
                    service=service,
                    endpoint=endpoint,
                    concurrent_requests=concurrent,
                    total_requests=50,  # 50 requests por endpoint
                    method=method
                )
                benchmark_results.append(result)

                # Pausa entre tests
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Error testing {service}{endpoint}: {e}")
                benchmark_results.append({
                    'service': service,
                    'endpoint': endpoint,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })

        # Obtener stats del cache después del test
        try:
            cache_stats = get_cache_status()
        except Exception as e:
            cache_stats = {'error': str(e)}

        return {
            'test_type': 'comprehensive_benchmark',
            'concurrent_requests': concurrent,
            'endpoints_tested': len(endpoints_to_test),
            'results': benchmark_results,
            'cache_stats_post_test': cache_stats,
            'timestamp': datetime.now().isoformat()
        }

    def generate_performance_report(self, 
                                  test_results: List[Dict], 
                                  baseline: Dict = None) -> Dict[str, Any]:
        """Genera reporte completo de performance"""

        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'test_count': len(test_results),
                'report_version': '1.0'
            },
            'test_results': test_results,
            'performance_analysis': {},
            'recommendations': []
        }

        # Análisis agregado
        all_latencies = []
        all_success_rates = []

        for test_result in test_results:
            if 'latency_stats' in test_result:
                all_latencies.append(test_result['latency_stats']['mean_ms'])
                all_success_rates.append(test_result.get('success_rate_percent', 0))

        if all_latencies:
            analysis = {
                'overall_avg_latency_ms': statistics.mean(all_latencies),
                'overall_median_latency_ms': statistics.median(all_latencies),
                'overall_success_rate': statistics.mean(all_success_rates),
                'fastest_endpoint': min(test_results, key=lambda x: x.get('latency_stats', {}).get('mean_ms', float('inf'))),
                'slowest_endpoint': max(test_results, key=lambda x: x.get('latency_stats', {}).get('mean_ms', 0))
            }

            # Comparación con baseline si existe
            if baseline:
                baseline_latency = baseline.get('overall_avg_latency_ms', 0)
                if baseline_latency > 0:
                    improvement = ((baseline_latency - analysis['overall_avg_latency_ms']) / baseline_latency) * 100
                    analysis['improvement_vs_baseline_percent'] = improvement

            report['performance_analysis'] = analysis

        # Recomendaciones
        recommendations = []

        if all_latencies:
            avg_latency = statistics.mean(all_latencies)
            if avg_latency > 1000:  # > 1 segundo
                recommendations.append({
                    'priority': 'high',
                    'category': 'performance',
                    'issue': f'Latencia promedio alta: {avg_latency:.0f}ms',
                    'recommendation': 'Revisar configuración cache y TTL'
                })

            avg_success_rate = statistics.mean(all_success_rates)
            if avg_success_rate < 95:
                recommendations.append({
                    'priority': 'high',
                    'category': 'reliability',
                    'issue': f'Tasa de éxito baja: {avg_success_rate:.1f}%',
                    'recommendation': 'Revisar logs de errores y configuración servicios'
                })

        report['recommendations'] = recommendations

        return report


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Performance Testing Suite")
    parser.add_argument(
        "--mode",
        choices=["benchmark", "cache", "load", "comparison", "report"],
        default="benchmark",
        help="Modo de test"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Requests concurrentes para benchmark"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duración en segundos para load test"
    )
    parser.add_argument(
        "--rps",
        type=int,
        default=50,
        help="Requests por segundo para load test"
    )
    parser.add_argument(
        "--output",
        help="Archivo output para resultados"
    )
    parser.add_argument(
        "--baseline",
        help="Archivo baseline para comparación"
    )

    args = parser.parse_args()

    async with PerformanceTestSuite() as test_suite:
        results = None

        if args.mode == "benchmark":
            logger.info("🚀 Ejecutando benchmark completo...")
            results = await test_suite.comprehensive_benchmark(args.concurrent)

        elif args.mode == "cache":
            logger.info("📊 Ejecutando test de efectividad cache...")
            results = await test_suite.cache_effectiveness_test()

        elif args.mode == "load":
            logger.info(f"⚡ Ejecutando load test: {args.duration}s @ {args.rps} RPS...")
            results = await test_suite.load_test(args.duration, args.rps)

        elif args.mode == "report":
            # Ejecutar suite completa
            logger.info("📋 Ejecutando suite completa de tests...")

            benchmark_results = await test_suite.comprehensive_benchmark(args.concurrent)
            cache_results = await test_suite.cache_effectiveness_test()

            # Cargar baseline si existe
            baseline = None
            if args.baseline:
                try:
                    with open(args.baseline, 'r') as f:
                        baseline = json.load(f)
                except Exception as e:
                    logger.warning(f"No se pudo cargar baseline: {e}")

            # Generar reporte completo
            all_results = [benchmark_results, cache_results]
            results = test_suite.generate_performance_report(all_results, baseline)

        # Guardar resultados
        if results:
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                logger.info(f"✅ Resultados guardados en: {args.output}")
            else:
                print(json.dumps(results, indent=2))

        # Mostrar resumen
        if args.mode == "benchmark" and 'results' in results:
            successful_tests = [r for r in results['results'] if 'latency_stats' in r]
            if successful_tests:
                avg_latency = statistics.mean([r['latency_stats']['mean_ms'] for r in successful_tests])
                avg_success_rate = statistics.mean([r['success_rate_percent'] for r in successful_tests])

                logger.info(f"📊 RESUMEN BENCHMARK:")
                logger.info(f"   Endpoints testeados: {len(successful_tests)}")
                logger.info(f"   Latencia promedio: {avg_latency:.1f}ms")
                logger.info(f"   Tasa de éxito: {avg_success_rate:.1f}%")

        elif args.mode == "cache" and 'summary' in results:
            summary = results['summary']
            logger.info(f"📊 RESUMEN CACHE EFFECTIVENESS:")
            logger.info(f"   Endpoints testeados: {summary['endpoints_tested']}")
            logger.info(f"   Mejora promedio: {summary['avg_improvement_percent']:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
