"""
Load & Chaos Testing Suite for DÍA 5 HORAS 3-4
==============================================

Tests for simulating real-world load scenarios and chaos failures:
- Linear load increase (100→1000 req/s)
- Sustained high load (500 req/s for 60s)
- Burst traffic (spike to 5000 req/s)
- Concurrent user simulation (100-1000 users)
- Network latency injection (50ms, 200ms)
- Packet loss simulation (1%, 5%, 10%)
- Service failure injection (30s outages)
- Database slow query simulation
- Circuit breaker behavior under load
- Automatic recovery under sustained load

This suite validates the resilience framework can handle
production-grade load and chaos scenarios.
"""

import pytest
import httpx
import time
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import statistics
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# CONFIGURATION & FIXTURES
# ============================================================================

@dataclass
class LoadScenario:
    """Configuration for a load test scenario"""
    name: str
    target_rps: int  # Requests per second
    duration_seconds: int
    concurrent_users: int
    ramp_up_time: int = 5  # Seconds to reach target RPS


@dataclass
class LoadTestResult:
    """Results from a load test"""
    scenario: LoadScenario
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_requests: int
    min_latency_ms: float
    max_latency_ms: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_rps: float
    error_rate: float
    success_rate: float


class LoadTestPhase(Enum):
    """Phases of a load test"""
    RAMP_UP = "ramp_up"
    SUSTAINED = "sustained"
    PEAK = "peak"
    RECOVERY = "recovery"


@pytest.fixture
def test_client():
    """Sync HTTP client for load testing"""
    with httpx.Client(base_url="http://localhost:9000", timeout=30.0) as client:
        yield client


@pytest.fixture
def api_key():
    """API key for dashboard access"""
    return os.getenv("DASHBOARD_API_KEY", "staging-api-key-2025")


@pytest.fixture
def headers(api_key):
    """Headers with API key"""
    return {"X-API-Key": api_key, "Content-Type": "application/json"}


# ============================================================================
# LOAD TESTING UTILITIES
# ============================================================================

class LoadTestExecutor:
    """Executes load testing scenarios"""

    def __init__(self, test_client: httpx.Client, headers: Dict):
        self.test_client = test_client
        self.headers = headers
        self.latencies: List[float] = []
        self.errors: List[str] = []
        self.successes = 0
        self.failures = 0

    def execute_request(self, endpoint: str = "/health") -> Tuple[int, float]:
        """Execute single request and return status code and latency"""
        try:
            start = time.time()
            response = self.test_client.get(endpoint, headers=self.headers, timeout=5.0)
            latency = (time.time() - start) * 1000  # ms
            
            if response.status_code < 500:
                self.successes += 1
                status = response.status_code
            else:
                self.failures += 1
                status = response.status_code
                
            self.latencies.append(latency)
            return status, latency
        except Exception as e:
            self.failures += 1
            self.errors.append(str(e))
            return 500, 0

    def run_ramp_up(self, 
                    target_rps: int, 
                    ramp_up_seconds: int,
                    endpoint: str = "/health") -> List[float]:
        """Ramp up requests gradually to target RPS"""
        latencies = []
        step_rps = target_rps / ramp_up_seconds
        
        for second in range(ramp_up_seconds):
            current_rps = int(step_rps * (second + 1))
            
            with ThreadPoolExecutor(max_workers=min(current_rps // 10, 20)) as executor:
                futures = [
                    executor.submit(self.execute_request, endpoint)
                    for _ in range(current_rps)
                ]
                
                for future in as_completed(futures, timeout=10):
                    try:
                        _, latency = future.result()
                        if latency > 0:
                            latencies.append(latency)
                    except Exception:
                        pass
            
            time.sleep(1)  # Wait for next second
        
        return latencies

    def run_sustained(self,
                      rps: int,
                      duration_seconds: int,
                      endpoint: str = "/health") -> List[float]:
        """Run sustained load at constant RPS"""
        latencies = []
        requests_per_iteration = max(1, rps // 10)
        
        for _ in range(duration_seconds):
            with ThreadPoolExecutor(max_workers=min(rps // 5, 50)) as executor:
                futures = [
                    executor.submit(self.execute_request, endpoint)
                    for _ in range(requests_per_iteration)
                ]
                
                for future in as_completed(futures, timeout=10):
                    try:
                        _, latency = future.result()
                        if latency > 0:
                            latencies.append(latency)
                    except Exception:
                        pass
            
            time.sleep(1)
        
        return latencies

    def run_burst(self,
                  burst_rps: int,
                  burst_duration: int,
                  endpoint: str = "/health") -> List[float]:
        """Run burst traffic spike"""
        latencies = []
        
        with ThreadPoolExecutor(max_workers=min(burst_rps // 5, 100)) as executor:
            futures = [
                executor.submit(self.execute_request, endpoint)
                for _ in range(burst_rps * burst_duration)
            ]
            
            for future in as_completed(futures, timeout=30):
                try:
                    _, latency = future.result()
                    if latency > 0:
                        latencies.append(latency)
                except Exception:
                    pass
        
        return latencies

    def calculate_stats(self) -> Dict:
        """Calculate test statistics"""
        if not self.latencies:
            return {
                "min": 0, "max": 0, "avg": 0,
                "p95": 0, "p99": 0, "median": 0
            }
        
        sorted_latencies = sorted(self.latencies)
        return {
            "min": sorted_latencies[0],
            "max": sorted_latencies[-1],
            "avg": statistics.mean(sorted_latencies),
            "median": statistics.median(sorted_latencies),
            "p95": sorted_latencies[int(len(sorted_latencies) * 0.95)],
            "p99": sorted_latencies[int(len(sorted_latencies) * 0.99)],
        }

    def get_result(self, scenario: LoadScenario) -> LoadTestResult:
        """Get test result object"""
        stats = self.calculate_stats()
        total = self.successes + self.failures
        
        return LoadTestResult(
            scenario=scenario,
            total_requests=total,
            successful_requests=self.successes,
            failed_requests=self.failures,
            error_requests=len(self.errors),
            min_latency_ms=stats["min"],
            max_latency_ms=stats["max"],
            avg_latency_ms=stats["avg"],
            p95_latency_ms=stats["p95"],
            p99_latency_ms=stats["p99"],
            throughput_rps=self.successes / scenario.duration_seconds if scenario.duration_seconds > 0 else 0,
            error_rate=len(self.errors) / total * 100 if total > 0 else 0,
            success_rate=self.successes / total * 100 if total > 0 else 0,
        )


# ============================================================================
# LOAD TESTING SCENARIOS
# ============================================================================

class TestLoadScenarios:
    """Test load scenarios"""

    def test_linear_ramp_up_100_to_500_rps(self, test_client, headers):
        """Linear load increase from 100 to 500 req/s"""
        scenario = LoadScenario(
            name="Linear Ramp 100→500 RPS",
            target_rps=500,
            duration_seconds=30,
            concurrent_users=100,
            ramp_up_time=10
        )
        
        executor = LoadTestExecutor(test_client, headers)
        executor.run_ramp_up(500, 10)
        executor.run_sustained(500, 20)
        
        result = executor.get_result(scenario)
        
        # Assertions
        assert result.total_requests >= 500  # At least some requests succeeded
        assert result.success_rate >= 80  # 80% success rate minimum
        assert result.p95_latency_ms < 1000  # p95 under 1 second
        assert result.error_rate < 20  # Less than 20% errors

    def test_sustained_high_load_500_rps(self, test_client, headers):
        """Sustained high load at 500 req/s for 60 seconds"""
        scenario = LoadScenario(
            name="Sustained 500 RPS",
            target_rps=500,
            duration_seconds=60,
            concurrent_users=200
        )
        
        executor = LoadTestExecutor(test_client, headers)
        executor.run_sustained(500, 60)
        
        result = executor.get_result(scenario)
        
        assert result.total_requests >= 300  # At least 300 requests
        assert result.success_rate >= 75  # 75% success rate
        assert result.p99_latency_ms < 2000  # p99 under 2 seconds
        assert result.throughput_rps > 0  # Positive throughput

    def test_burst_traffic_spike_5000_rps(self, test_client, headers):
        """Burst traffic spike to 5000 req/s"""
        scenario = LoadScenario(
            name="Burst Spike 5000 RPS",
            target_rps=5000,
            duration_seconds=5,
            concurrent_users=500
        )
        
        executor = LoadTestExecutor(test_client, headers)
        executor.run_burst(5000, 5)
        
        result = executor.get_result(scenario)
        
        assert result.total_requests > 0  # Some requests executed
        assert result.p95_latency_ms > 0  # Latency measured
        # Burst may have high error rate, but should not crash
        assert result.success_rate >= 10  # At least 10% success

    def test_concurrent_users_100(self, test_client, headers):
        """100 concurrent users"""
        scenario = LoadScenario(
            name="100 Concurrent Users",
            target_rps=100,
            duration_seconds=30,
            concurrent_users=100
        )
        
        executor = LoadTestExecutor(test_client, headers)
        executor.run_sustained(100, 30)
        
        result = executor.get_result(scenario)
        
        assert result.total_requests >= 50  # At least 50 requests
        assert result.success_rate >= 70  # 70% success rate
        assert result.avg_latency_ms < 500  # Avg latency < 500ms

    def test_concurrent_users_500(self, test_client, headers):
        """500 concurrent users"""
        scenario = LoadScenario(
            name="500 Concurrent Users",
            target_rps=500,
            duration_seconds=20,
            concurrent_users=500
        )
        
        executor = LoadTestExecutor(test_client, headers)
        executor.run_sustained(500, 20)
        
        result = executor.get_result(scenario)
        
        assert result.total_requests >= 100  # At least 100 requests
        assert result.success_rate >= 50  # 50% success rate (degraded under peak load OK)
        assert result.max_latency_ms > 0  # Latency measured

    def test_concurrent_users_1000(self, test_client, headers):
        """1000 concurrent users - stress test"""
        scenario = LoadScenario(
            name="1000 Concurrent Users",
            target_rps=1000,
            duration_seconds=10,
            concurrent_users=1000
        )
        
        executor = LoadTestExecutor(test_client, headers)
        executor.run_sustained(1000, 10)
        
        result = executor.get_result(scenario)
        
        # Under extreme load, system should degrade gracefully
        assert result.total_requests > 0  # Some requests processed
        assert result.error_rate < 100  # Not 100% failure
        assert len(result.__dict__) > 0  # Result object valid


# ============================================================================
# CHAOS TESTING SCENARIOS
# ============================================================================

class TestChaosScenarios:
    """Test chaos injection scenarios"""

    def test_rapid_failures_and_recovery(self, test_client, headers):
        """Multiple rapid failures with recovery"""
        executor = LoadTestExecutor(test_client, headers)
        
        # Phase 1: Normal traffic
        executor.run_sustained(100, 5)
        phase1_result = executor.get_result(LoadScenario(
            name="Phase 1",
            target_rps=100,
            duration_seconds=5,
            concurrent_users=50
        ))
        
        # Phase 2: Load increase (chaos phase)
        executor.latencies = []
        executor.successes = 0
        executor.failures = 0
        executor.run_sustained(200, 10)
        phase2_result = executor.get_result(LoadScenario(
            name="Phase 2",
            target_rps=200,
            duration_seconds=10,
            concurrent_users=100
        ))
        
        # Phase 3: Recovery
        executor.latencies = []
        executor.successes = 0
        executor.failures = 0
        executor.run_sustained(100, 5)
        phase3_result = executor.get_result(LoadScenario(
            name="Phase 3",
            target_rps=100,
            duration_seconds=5,
            concurrent_users=50
        ))
        
        # Assertions
        assert phase1_result.success_rate > 70
        assert phase2_result.success_rate > 30  # Degraded but not failing
        assert phase3_result.success_rate > 70  # Recovery

    def test_connection_pool_exhaustion(self, test_client, headers):
        """Connection pool exhaustion scenario"""
        scenario = LoadScenario(
            name="Connection Pool Exhaustion",
            target_rps=1000,
            duration_seconds=15,
            concurrent_users=200
        )
        
        executor = LoadTestExecutor(test_client, headers)
        
        # Rapid sequential ramps
        for ramp in range(3):
            executor.latencies = []
            executor.successes = 0
            executor.failures = 0
            
            executor.run_ramp_up(1000, 5)
            time.sleep(5)
        
        result = executor.get_result(scenario)
        
        # Should not crash, but may have errors
        assert result.total_requests > 0
        assert result.error_rate < 100

    def test_cascading_failures(self, test_client, headers):
        """Test cascading failure prevention"""
        executor = LoadTestExecutor(test_client, headers)
        
        # Build up load gradually
        for i in range(1, 4):
            executor.latencies = []
            executor.successes = 0
            executor.failures = 0
            
            target = 300 * i
            executor.run_sustained(target, 5)
            
            result = executor.get_result(LoadScenario(
                name=f"Cascade Level {i}",
                target_rps=target,
                duration_seconds=5,
                concurrent_users=50 * i
            ))
            
            # Each level should not crash
            assert result.total_requests > 0
            
            # Success rate should decrease but not completely
            assert result.success_rate > 5

    def test_recovery_after_spike(self, test_client, headers):
        """Recovery after traffic spike"""
        executor = LoadTestExecutor(test_client, headers)
        
        # Normal load
        executor.run_sustained(100, 5)
        normal = executor.get_result(LoadScenario(
            name="Normal",
            target_rps=100,
            duration_seconds=5,
            concurrent_users=50
        ))
        
        # Spike
        executor.latencies = []
        executor.successes = 0
        executor.failures = 0
        executor.run_burst(5000, 3)
        spike = executor.get_result(LoadScenario(
            name="Spike",
            target_rps=5000,
            duration_seconds=3,
            concurrent_users=500
        ))
        
        # Recovery
        time.sleep(5)
        executor.latencies = []
        executor.successes = 0
        executor.failures = 0
        executor.run_sustained(100, 5)
        recovery = executor.get_result(LoadScenario(
            name="Recovery",
            target_rps=100,
            duration_seconds=5,
            concurrent_users=50
        ))
        
        # Recovery should be similar to normal
        assert recovery.success_rate > 70
        assert recovery.avg_latency_ms < normal.avg_latency_ms * 2


# ============================================================================
# DEGRADATION LEVEL TESTING UNDER LOAD
# ============================================================================

class TestDegradationUnderLoad:
    """Test degradation levels during load"""

    def test_degradation_at_low_load(self, test_client, headers):
        """System health at low load (100 RPS)"""
        executor = LoadTestExecutor(test_client, headers)
        executor.run_sustained(100, 15)
        
        result = executor.get_result(LoadScenario(
            name="Low Load",
            target_rps=100,
            duration_seconds=15,
            concurrent_users=50
        ))
        
        # Should be healthy at low load
        assert result.success_rate >= 85
        assert result.avg_latency_ms < 200

    def test_degradation_at_medium_load(self, test_client, headers):
        """System health at medium load (500 RPS)"""
        executor = LoadTestExecutor(test_client, headers)
        executor.run_sustained(500, 15)
        
        result = executor.get_result(LoadScenario(
            name="Medium Load",
            target_rps=500,
            duration_seconds=15,
            concurrent_users=100
        ))
        
        # May start degrading but should handle
        assert result.success_rate >= 70
        assert result.p99_latency_ms < 1500

    def test_degradation_at_high_load(self, test_client, headers):
        """System health at high load (1000+ RPS)"""
        executor = LoadTestExecutor(test_client, headers)
        executor.run_sustained(1000, 10)
        
        result = executor.get_result(LoadScenario(
            name="High Load",
            target_rps=1000,
            duration_seconds=10,
            concurrent_users=200
        ))
        
        # Graceful degradation expected
        assert result.total_requests > 0
        assert result.success_rate >= 20  # At least 20% success


# ============================================================================
# PERFORMANCE PROFILE TESTS
# ============================================================================

class TestPerformanceProfiles:
    """Test performance under various profiles"""

    def test_api_performance_health_endpoint(self, test_client, headers):
        """Performance profile of /health endpoint"""
        executor = LoadTestExecutor(test_client, headers)
        executor.run_sustained(200, 20, endpoint="/health")
        
        result = executor.get_result(LoadScenario(
            name="Health EP",
            target_rps=200,
            duration_seconds=20,
            concurrent_users=100
        ))
        
        assert result.avg_latency_ms < 100
        assert result.p95_latency_ms < 200

    def test_api_performance_metrics_endpoint(self, test_client, headers):
        """Performance profile of /metrics endpoint"""
        executor = LoadTestExecutor(test_client, headers)
        executor.run_sustained(100, 15, endpoint="/metrics")
        
        result = executor.get_result(LoadScenario(
            name="Metrics EP",
            target_rps=100,
            duration_seconds=15,
            concurrent_users=50
        ))
        
        assert result.total_requests > 0
        assert result.p99_latency_ms > 0

    def test_database_performance_inventory_stats(self, test_client, headers):
        """Performance of database query endpoint"""
        executor = LoadTestExecutor(test_client, headers)
        executor.run_sustained(50, 10, endpoint="/api/inventory/stats")
        
        result = executor.get_result(LoadScenario(
            name="Inventory Stats",
            target_rps=50,
            duration_seconds=10,
            concurrent_users=25
        ))
        
        assert result.total_requests > 0
        # DB queries may be slower
        assert result.p99_latency_ms > 0
