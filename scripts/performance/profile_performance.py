#!/usr/bin/env python3
"""
Performance Profiling & Optimization Tool

Profiles:
- Database query performance
- Memory usage
- CPU utilization
- Response times
- Bottleneck identification
"""

import time
import psutil
import json
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict

@dataclass
class PerformanceMetric:
    metric_name: str
    value: float
    unit: str
    timestamp: str
    threshold: float
    status: str  # ok, warning, critical

class PerformanceProfiler:
    """Comprehensive performance profiling"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.start_time = time.time()
    
    def log(self, message: str):
        """Print message"""
        print(f"[{datetime.now():%H:%M:%S}] {message}")
    
    def profile_memory_usage(self) -> PerformanceMetric:
        """Profile memory usage"""
        self.log("📊 Profiling memory usage...")
        
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        status = "ok" if memory_mb < 512 else "warning" if memory_mb < 1024 else "critical"
        
        return PerformanceMetric(
            metric_name="Memory Usage",
            value=memory_mb,
            unit="MB",
            timestamp=datetime.now().isoformat(),
            threshold=512.0,
            status=status
        )
    
    def profile_cpu_usage(self) -> PerformanceMetric:
        """Profile CPU usage"""
        self.log("📊 Profiling CPU usage...")
        
        cpu_percent = psutil.cpu_percent(interval=1)
        
        status = "ok" if cpu_percent < 70 else "warning" if cpu_percent < 90 else "critical"
        
        return PerformanceMetric(
            metric_name="CPU Usage",
            value=cpu_percent,
            unit="%",
            timestamp=datetime.now().isoformat(),
            threshold=70.0,
            status=status
        )
    
    def profile_response_time(self, endpoint: str = "/health") -> PerformanceMetric:
        """Profile API response time"""
        self.log(f"📊 Profiling response time for {endpoint}...")
        
        import requests
        
        try:
            start = time.time()
            response = requests.get(f"http://localhost:8080{endpoint}", timeout=5)
            duration_ms = (time.time() - start) * 1000
            
            status = "ok" if duration_ms < 100 else "warning" if duration_ms < 500 else "critical"
            
            return PerformanceMetric(
                metric_name=f"Response Time ({endpoint})",
                value=duration_ms,
                unit="ms",
                timestamp=datetime.now().isoformat(),
                threshold=100.0,
                status=status
            )
        except Exception as e:
            return PerformanceMetric(
                metric_name=f"Response Time ({endpoint})",
                value=-1,
                unit="ms",
                timestamp=datetime.now().isoformat(),
                threshold=100.0,
                status="critical"
            )
    
    def run_profiling(self):
        """Run all profiling"""
        self.log("╔" + "=" * 50 + "╗")
        self.log("║  PERFORMANCE PROFILING STARTED                ║")
        self.log("╚" + "=" * 50 + "╝")
        
        self.metrics.append(self.profile_memory_usage())
        self.metrics.append(self.profile_cpu_usage())
        self.metrics.append(self.profile_response_time("/health"))
        
        self.generate_report()
    
    def generate_report(self):
        """Generate performance report"""
        print("\n" + "=" * 70)
        print("PERFORMANCE PROFILING REPORT")
        print("=" * 70)
        
        for metric in self.metrics:
            icon = "✅" if metric.status == "ok" else "⚠️" if metric.status == "warning" else "❌"
            print(f"{icon} {metric.metric_name}: {metric.value:.1f}{metric.unit}")
        
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": [asdict(m) for m in self.metrics]
        }
        
        with open("/tmp/performance_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("\nReport saved: /tmp/performance_report.json")

if __name__ == "__main__":
    profiler = PerformanceProfiler()
    profiler.run_profiling()
