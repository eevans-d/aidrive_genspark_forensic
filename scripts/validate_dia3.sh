#!/bin/bash

################################################################################
# DÍA 3 VALIDATION SCRIPT
# 
# Comprehensive validation of DÍA 3 deliverables (HORAS 1-7):
# - Redis Circuit Breaker (HORAS 1-4)
# - S3 Circuit Breaker (HORAS 4-7)
# 
# Author: Resilience Team
# Date: October 19, 2025
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counter variables
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Helper functions
check_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSED_CHECKS++))
}

check_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILED_CHECKS++))
}

check_start() {
    echo -e "${BLUE}→${NC} $1"
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# ============================================================================
# SECTION 1: FILE EXISTENCE CHECKS
# ============================================================================

echo ""
echo "==============================================================================="
echo "SECTION 1: FILE EXISTENCE CHECKS"
echo "==============================================================================="

check_start "Checking Redis Circuit Breaker files"
((TOTAL_CHECKS++))
if [ -f "inventario-retail/shared/redis_service.py" ]; then
    check_pass "inventario-retail/shared/redis_service.py exists"
else
    check_fail "inventario-retail/shared/redis_service.py NOT FOUND"
fi

((TOTAL_CHECKS++))
if [ -f "tests/resilience/test_redis_circuit_breaker.py" ]; then
    check_pass "tests/resilience/test_redis_circuit_breaker.py exists"
else
    check_fail "tests/resilience/test_redis_circuit_breaker.py NOT FOUND"
fi

check_start "Checking S3 Circuit Breaker files"
((TOTAL_CHECKS++))
if [ -f "inventario-retail/shared/s3_service.py" ]; then
    check_pass "inventario-retail/shared/s3_service.py exists"
else
    check_fail "inventario-retail/shared/s3_service.py NOT FOUND"
fi

((TOTAL_CHECKS++))
if [ -f "tests/resilience/test_s3_circuit_breaker.py" ]; then
    check_pass "tests/resilience/test_s3_circuit_breaker.py exists"
else
    check_fail "tests/resilience/test_s3_circuit_breaker.py NOT FOUND"
fi

# ============================================================================
# SECTION 2: LINE COUNT VERIFICATION
# ============================================================================

echo ""
echo "==============================================================================="
echo "SECTION 2: LINE COUNT VERIFICATION"
echo "==============================================================================="

check_start "Verifying Redis service line count (expected: ~850-900 lines)"
((TOTAL_CHECKS++))
redis_lines=$(wc -l < "inventario-retail/shared/redis_service.py")
if [ "$redis_lines" -gt 800 ] && [ "$redis_lines" -lt 1000 ]; then
    check_pass "redis_service.py: $redis_lines lines (VALID)"
else
    check_fail "redis_service.py: $redis_lines lines (expected 800-1000)"
fi

check_start "Verifying Redis tests line count (expected: ~350-400 lines)"
((TOTAL_CHECKS++))
redis_test_lines=$(wc -l < "tests/resilience/test_redis_circuit_breaker.py")
if [ "$redis_test_lines" -gt 350 ] && [ "$redis_test_lines" -lt 450 ]; then
    check_pass "test_redis_circuit_breaker.py: $redis_test_lines lines (VALID)"
else
    check_fail "test_redis_circuit_breaker.py: $redis_test_lines lines (expected 350-450)"
fi

check_start "Verifying S3 service line count (expected: ~640-750 lines)"
((TOTAL_CHECKS++))
s3_lines=$(wc -l < "inventario-retail/shared/s3_service.py")
if [ "$s3_lines" -gt 620 ] && [ "$s3_lines" -lt 800 ]; then
    check_pass "s3_service.py: $s3_lines lines (VALID)"
else
    check_fail "s3_service.py: $s3_lines lines (expected 620-800)"
fi

check_start "Verifying S3 tests line count (expected: ~300-400 lines)"
((TOTAL_CHECKS++))
s3_test_lines=$(wc -l < "tests/resilience/test_s3_circuit_breaker.py")
if [ "$s3_test_lines" -gt 280 ] && [ "$s3_test_lines" -lt 450 ]; then
    check_pass "test_s3_circuit_breaker.py: $s3_test_lines lines (VALID)"
else
    check_fail "test_s3_circuit_breaker.py: $s3_test_lines lines (expected 280-450)"
fi

# ============================================================================
# SECTION 3: SYNTAX VERIFICATION
# ============================================================================

echo ""
echo "==============================================================================="
echo "SECTION 3: SYNTAX VERIFICATION"
echo "==============================================================================="

check_start "Verifying Python syntax for all files"

((TOTAL_CHECKS++))
if python3 -m py_compile "inventario-retail/shared/redis_service.py" 2>/dev/null; then
    check_pass "redis_service.py syntax is valid"
else
    check_fail "redis_service.py has syntax errors"
fi

((TOTAL_CHECKS++))
if python3 -m py_compile "tests/resilience/test_redis_circuit_breaker.py" 2>/dev/null; then
    check_pass "test_redis_circuit_breaker.py syntax is valid"
else
    check_fail "test_redis_circuit_breaker.py has syntax errors"
fi

((TOTAL_CHECKS++))
if python3 -m py_compile "inventario-retail/shared/s3_service.py" 2>/dev/null; then
    check_pass "s3_service.py syntax is valid"
else
    check_fail "s3_service.py has syntax errors"
fi

((TOTAL_CHECKS++))
if python3 -m py_compile "tests/resilience/test_s3_circuit_breaker.py" 2>/dev/null; then
    check_pass "test_s3_circuit_breaker.py syntax is valid"
else
    check_fail "test_s3_circuit_breaker.py has syntax errors"
fi

# ============================================================================
# SECTION 4: CLASS & KEY COMPONENTS VERIFICATION
# ============================================================================

echo ""
echo "==============================================================================="
echo "SECTION 4: CLASS & KEY COMPONENTS VERIFICATION"
echo "==============================================================================="

check_start "Verifying Redis Circuit Breaker classes and components"

((TOTAL_CHECKS++))
if grep -q "class RedisCircuitBreaker" "inventario-retail/shared/redis_service.py"; then
    check_pass "RedisCircuitBreaker class found"
else
    check_fail "RedisCircuitBreaker class NOT FOUND"
fi

((TOTAL_CHECKS++))
if grep -q "class RedisHealthMetrics" "inventario-retail/shared/redis_service.py"; then
    check_pass "RedisHealthMetrics class found"
else
    check_fail "RedisHealthMetrics class NOT FOUND"
fi

((TOTAL_CHECKS++))
if grep -q "class CircuitBreakerState" "inventario-retail/shared/redis_service.py"; then
    check_pass "CircuitBreakerState enum found in redis_service"
else
    check_fail "CircuitBreakerState enum NOT FOUND in redis_service"
fi

check_start "Verifying S3 Circuit Breaker classes and components"

((TOTAL_CHECKS++))
if grep -q "class S3CircuitBreaker" "inventario-retail/shared/s3_service.py"; then
    check_pass "S3CircuitBreaker class found"
else
    check_fail "S3CircuitBreaker class NOT FOUND"
fi

((TOTAL_CHECKS++))
if grep -q "class S3HealthMetrics" "inventario-retail/shared/s3_service.py"; then
    check_pass "S3HealthMetrics class found"
else
    check_fail "S3HealthMetrics class NOT FOUND"
fi

((TOTAL_CHECKS++))
if grep -q "class CircuitBreakerState" "inventario-retail/shared/s3_service.py"; then
    check_pass "CircuitBreakerState enum found in s3_service"
else
    check_fail "CircuitBreakerState enum NOT FOUND in s3_service"
fi

# ============================================================================
# SECTION 5: METHOD VERIFICATION
# ============================================================================

echo ""
echo "==============================================================================="
echo "SECTION 5: METHOD VERIFICATION"
echo "==============================================================================="

check_start "Verifying Redis Circuit Breaker critical methods"

# Redis critical operations - verificar al menos los principales
redis_critical_methods=("get" "set" "delete" "incr" "lpush" "llen" "hset" "hgetall" "ping")
for method in "${redis_critical_methods[@]}"; do
    ((TOTAL_CHECKS++))
    if grep -q "async def $method\|def $method" "inventario-retail/shared/redis_service.py"; then
        check_pass "Redis method '$method' found"
    else
        check_fail "Redis method '$method' NOT FOUND"
    fi
done

# Redis critical methods
((TOTAL_CHECKS++))
if grep -q "async def initialize\|def initialize" "inventario-retail/shared/redis_service.py"; then
    check_pass "Redis initialize method found"
else
    check_fail "Redis initialize method NOT FOUND"
fi

((TOTAL_CHECKS++))
if grep -q "def get_health" "inventario-retail/shared/redis_service.py"; then
    check_pass "Redis get_health method found"
else
    check_fail "Redis get_health method NOT FOUND"
fi

check_start "Verifying S3 Circuit Breaker critical methods"

# S3 critical operations
s3_critical_methods=("upload" "download" "delete" "list_objects" "head_object")
for method in "${s3_critical_methods[@]}"; do
    ((TOTAL_CHECKS++))
    if grep -q "async def $method\|def $method" "inventario-retail/shared/s3_service.py"; then
        check_pass "S3 method '$method' found"
    else
        check_fail "S3 method '$method' NOT FOUND"
    fi
done

# S3 critical methods
((TOTAL_CHECKS++))
if grep -q "async def initialize\|def initialize" "inventario-retail/shared/s3_service.py"; then
    check_pass "S3 initialize method found"
else
    check_fail "S3 initialize method NOT FOUND"
fi

((TOTAL_CHECKS++))
if grep -q "def get_health" "inventario-retail/shared/s3_service.py"; then
    check_pass "S3 get_health method found"
else
    check_fail "S3 get_health method NOT FOUND"
fi

# ============================================================================
# SECTION 6: PROMETHEUS METRICS VERIFICATION
# ============================================================================

echo ""
echo "==============================================================================="
echo "SECTION 6: PROMETHEUS METRICS VERIFICATION"
echo "==============================================================================="

check_start "Verifying Redis Prometheus metrics (expected: 5)"

redis_metrics=("redis_requests_total" "redis_errors_total" "redis_latency_seconds" "redis_circuit_breaker_state" "redis_health_score")
for metric in "${redis_metrics[@]}"; do
    ((TOTAL_CHECKS++))
    if grep -q "$metric" "inventario-retail/shared/redis_service.py"; then
        check_pass "Redis metric '$metric' found"
    else
        check_fail "Redis metric '$metric' NOT FOUND"
    fi
done

check_start "Verifying S3 Prometheus metrics (expected: 6)"

s3_metrics=("s3_requests_total" "s3_errors_total" "s3_latency_seconds" "s3_circuit_breaker_state" "s3_bytes_transferred" "s3_health_score")
for metric in "${s3_metrics[@]}"; do
    ((TOTAL_CHECKS++))
    if grep -q "$metric" "inventario-retail/shared/s3_service.py"; then
        check_pass "S3 metric '$metric' found"
    else
        check_fail "S3 metric '$metric' NOT FOUND"
    fi
done

# ============================================================================
# SECTION 7: TEST COVERAGE VERIFICATION
# ============================================================================

echo ""
echo "==============================================================================="
echo "SECTION 7: TEST COVERAGE VERIFICATION"
echo "==============================================================================="

check_start "Verifying Redis test classes"

redis_test_classes=("TestRedisHealthMetrics" "TestCircuitBreakerState" "TestRedisOperations" "TestCircuitBreakerProtection" "TestHealthAndStatus" "TestPerformance")
for test_class in "${redis_test_classes[@]}"; do
    ((TOTAL_CHECKS++))
    if grep -q "class $test_class" "tests/resilience/test_redis_circuit_breaker.py"; then
        check_pass "Redis test class '$test_class' found"
    else
        check_fail "Redis test class '$test_class' NOT FOUND"
    fi
done

check_start "Verifying S3 test classes"

s3_test_classes=("TestS3HealthMetrics" "TestCircuitBreakerState" "TestS3Operations" "TestCircuitBreakerProtection" "TestHealthAndStatus")
for test_class in "${s3_test_classes[@]}"; do
    ((TOTAL_CHECKS++))
    if grep -q "class $test_class" "tests/resilience/test_s3_circuit_breaker.py"; then
        check_pass "S3 test class '$test_class' found"
    else
        check_fail "S3 test class '$test_class' NOT FOUND"
    fi
done

# ============================================================================
# SECTION 8: GIT STATUS VERIFICATION
# ============================================================================

echo ""
echo "==============================================================================="
echo "SECTION 8: GIT STATUS VERIFICATION"
echo "==============================================================================="

check_start "Verifying recent git commits for DÍA 3"

((TOTAL_CHECKS++))
# Check for Redis commit
if git log --oneline | head -10 | grep -q "Redis Circuit Breaker"; then
    check_pass "Redis Circuit Breaker commit found"
else
    check_fail "Redis Circuit Breaker commit NOT FOUND"
fi

((TOTAL_CHECKS++))
# Check for S3 commit
if git log --oneline | head -10 | grep -q "S3 Circuit Breaker"; then
    check_pass "S3 Circuit Breaker commit found"
else
    check_fail "S3 Circuit Breaker commit NOT FOUND"
fi

# ============================================================================
# FINAL SUMMARY
# ============================================================================

echo ""
echo "==============================================================================="
echo "FINAL SUMMARY"
echo "==============================================================================="
echo ""
echo "Total Checks:    $TOTAL_CHECKS"
echo -e "Passed:          ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed:          ${RED}$FAILED_CHECKS${NC}"
echo ""

if [ "$FAILED_CHECKS" -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
    echo ""
    info "DÍA 3 HORAS 1-7 Deliverables Summary:"
    echo "  • Redis Circuit Breaker: $redis_lines lines"
    echo "  • Redis Tests: $redis_test_lines lines"
    echo "  • S3 Circuit Breaker: $s3_lines lines"
    echo "  • S3 Tests: $s3_test_lines lines"
    echo "  • Total lines delivered: $((redis_lines + redis_test_lines + s3_lines + s3_test_lines))"
    echo ""
    info "Ready for DÍA 3 HORAS 7-8: Integration and Deployment Preparation"
    exit 0
else
    echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
    echo ""
    info "Please review the failures above and correct them."
    exit 1
fi
