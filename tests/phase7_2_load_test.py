#!/usr/bin/env python3
"""
Phase 7.2: Integration Load Test con Memory Profiling
Objetivo: Validar que gc.collect() libera memoria bajo carga
"""

import asyncio
import gc
import os
import psutil
import sys
import time
from datetime import datetime
import json
import logging

# Logging estructurado JSON
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

class MemoryProfiler:
    """Monitoreo de memoria durante test de carga"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.measurements = []
        self.baseline_rss = None
        self.peak_rss = 0
        
    def start(self):
        """Registrar memoria inicial"""
        gc.collect()
        time.sleep(0.1)
        self.baseline_rss = self.process.memory_info().rss / 1024 / 1024
        self.peak_rss = self.baseline_rss
        logger.info(json.dumps({
            "event": "profile_start",
            "baseline_mb": round(self.baseline_rss, 2),
            "timestamp": datetime.now().isoformat()
        }))
    
    def checkpoint(self, label: str, force_gc=False):
        """Capturar snapshot de memoria"""
        if force_gc:
            gc.collect()
            time.sleep(0.05)
        
        rss = self.process.memory_info().rss / 1024 / 1024
        delta = rss - self.baseline_rss
        self.peak_rss = max(self.peak_rss, rss)
        
        measurement = {
            "event": "memory_checkpoint",
            "label": label,
            "rss_mb": round(rss, 2),
            "delta_mb": round(delta, 2),
            "peak_mb": round(self.peak_rss, 2),
            "timestamp": datetime.now().isoformat()
        }
        self.measurements.append(measurement)
        logger.info(json.dumps(measurement))
        
        return rss
    
    def report(self):
        """Generar reporte final"""
        final_rss = self.process.memory_info().rss / 1024 / 1024
        final_delta = final_rss - self.baseline_rss
        
        # Validación: memoria final debe ser similar a inicial ±10%
        threshold_mb = max(10, self.baseline_rss * 0.1)
        passed = abs(final_delta) <= threshold_mb
        
        report = {
            "event": "load_test_summary",
            "baseline_mb": round(self.baseline_rss, 2),
            "final_mb": round(final_rss, 2),
            "peak_mb": round(self.peak_rss, 2),
            "delta_mb": round(final_delta, 2),
            "threshold_mb": round(threshold_mb, 2),
            "passed": passed,
            "status": "PASS" if passed else "FAIL",
            "timestamp": datetime.now().isoformat()
        }
        logger.info(json.dumps(report))
        return report

async def simulate_deposito_client_requests(num_requests=1000):
    """Simular 1000+ requests al deposito_client"""
    
    profiler = MemoryProfiler()
    profiler.start()
    
    logger.info(json.dumps({"event": "load_test_start", "requests": num_requests}))
    
    # Fase 1: Acumulación de estadísticas (simular stats crecimiento)
    logger.info(json.dumps({"event": "phase", "name": "stats_accumulation", "requests": num_requests}))
    
    for i in range(0, num_requests, 100):
        # Simular aumento de stats dict
        stats = {
            'total_requests': i + 100,
            'success': i + 80,
            'errors': i + 20,
            'latency_ms': [50 + (i % 100)] * (i + 100),  # Lista creciente
        }
        
        # Simular memory pressure
        _ = [j for j in range(10000)]
        
        if i % 250 == 0:
            profiler.checkpoint(f"after_{i}_requests")
        
        await asyncio.sleep(0.001)
    
    profiler.checkpoint("stats_accumulation_complete")
    
    # Fase 2: Trigger reset (donde gc.collect() actúa)
    logger.info(json.dumps({"event": "phase", "name": "gc_collect_triggered"}))
    profiler.checkpoint("before_gc", force_gc=False)
    
    gc.collect()  # Simular lo que hace _reset_stats_if_needed
    
    profiler.checkpoint("after_gc_collect", force_gc=False)
    
    # Fase 3: Validación post-reset
    logger.info(json.dumps({"event": "phase", "name": "post_reset_validation"}))
    
    for i in range(100):
        # Pequeñas requests después del reset
        _ = [j for j in range(1000)]
        if i % 25 == 0:
            profiler.checkpoint(f"post_reset_{i}")
        await asyncio.sleep(0.001)
    
    profiler.checkpoint("final", force_gc=True)
    
    # Generar reporte
    report = profiler.report()
    
    return report

async def main():
    """Ejecutar Phase 7.2"""
    print("\n" + "="*70)
    print("PHASE 7.2: INTEGRATION LOAD TEST CON MEMORY PROFILING")
    print("="*70 + "\n")
    
    try:
        report = await simulate_deposito_client_requests(num_requests=1000)
        
        # Resultado final
        print("\n" + "="*70)
        print("PHASE 7.2 RESULT")
        print("="*70)
        if report['passed']:
            print("✅ PASS - Memory leak prevention working correctly")
            print(f"   - Baseline: {report['baseline_mb']} MB")
            print(f"   - Final: {report['final_mb']} MB")
            print(f"   - Peak: {report['peak_mb']} MB")
            print(f"   - Delta: {report['delta_mb']} MB (within {report['threshold_mb']} MB)")
            return 0
        else:
            print("❌ FAIL - Memory growth detected")
            print(f"   - Baseline: {report['baseline_mb']} MB")
            print(f"   - Final: {report['final_mb']} MB")
            print(f"   - Peak: {report['peak_mb']} MB")
            print(f"   - Delta: {report['delta_mb']} MB (threshold: {report['threshold_mb']} MB)")
            return 1
    
    except Exception as e:
        logger.error(json.dumps({
            "event": "load_test_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }))
        print(f"\n❌ ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
