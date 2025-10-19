#!/bin/bash

# ============================================================================
# Failure Injection Test Validation Script
# DÍA 5 HORAS 1-2: Validate failure scenarios and recovery
# ============================================================================

set -e

WORKSPACE="${WORKSPACE:-.}"
LOG_DIR="${WORKSPACE}/logs/staging"
VALIDATION_LOG="${LOG_DIR}/failure_injection_validation_$(date +%Y%m%d_%H%M%S).log"
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

mkdir -p "$LOG_DIR"

# ============================================================================
# FUNCTIONS
# ============================================================================

log_section() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$VALIDATION_LOG"
    echo -e "${BLUE}$1${NC}" | tee -a "$VALIDATION_LOG"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$VALIDATION_LOG"
}

check_result() {
    local check_name=$1
    local status=$2
    local details=$3
    
    ((TOTAL_CHECKS++))
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $check_name" | tee -a "$VALIDATION_LOG"
        ((PASSED_CHECKS++))
    else
        echo -e "${RED}✗${NC} $check_name - $details" | tee -a "$VALIDATION_LOG"
    fi
}

check_service() {
    local service=$1
    local port=$2
    local health_endpoint=$3
    
    if curl -s -f -H "X-API-Key: staging-api-key-2025" "http://localhost:${port}${health_endpoint}" > /dev/null 2>&1; then
        check_result "$service health check" "PASS"
    else
        check_result "$service health check" "FAIL" "Service not responding on port $port"
    fi
}

# ============================================================================
# MAIN VALIDATION
# ============================================================================

log_section "FAILURE INJECTION TEST SUITE VALIDATION"

echo "[$(date)] Starting failure injection validation..." | tee -a "$VALIDATION_LOG"
echo ""

# ============================================================================
# SECTION 1: Service Availability
# ============================================================================

log_section "1. Service Availability Checks"

check_service "PostgreSQL" "5433" "/health"
check_service "Redis" "6380" "/health"
check_service "Dashboard" "9000" "/health"

# ============================================================================
# SECTION 2: Circuit Breaker Configuration
# ============================================================================

log_section "2. Circuit Breaker Configuration"

# Check OpenAI CB config
if [ -n "$OPENAI_CB_FAILURE_THRESHOLD" ]; then
    check_result "OpenAI CB threshold configured" "PASS"
else
    check_result "OpenAI CB threshold configured" "FAIL" "OPENAI_CB_FAILURE_THRESHOLD not set"
fi

# Check Database CB config
if [ -n "$DB_CB_FAILURE_THRESHOLD" ]; then
    check_result "Database CB threshold configured" "PASS"
else
    check_result "Database CB threshold configured" "FAIL" "DB_CB_FAILURE_THRESHOLD not set"
fi

# Check Redis CB config
if [ -n "$REDIS_CB_FAILURE_THRESHOLD" ]; then
    check_result "Redis CB threshold configured" "PASS"
else
    check_result "Redis CB threshold configured" "FAIL" "REDIS_CB_FAILURE_THRESHOLD not set"
fi

# Check S3 CB config
if [ -n "$S3_CB_FAILURE_THRESHOLD" ]; then
    check_result "S3 CB threshold configured" "PASS"
else
    check_result "S3 CB threshold configured" "FAIL" "S3_CB_FAILURE_THRESHOLD not set"
fi

# ============================================================================
# SECTION 3: Health Check Configuration
# ============================================================================

log_section "3. Health Check Configuration"

# Verify health check interval
if [ -n "$HEALTH_CHECK_INTERVAL" ]; then
    check_result "Health check interval configured" "PASS"
else
    check_result "Health check interval configured" "FAIL" "HEALTH_CHECK_INTERVAL not set"
fi

# Verify degradation levels
if [ -n "$OPTIMAL_THRESHOLD" ] && [ -n "$DEGRADED_THRESHOLD" ] && [ -n "$LIMITED_THRESHOLD" ]; then
    check_result "Degradation thresholds configured" "PASS"
else
    check_result "Degradation thresholds configured" "FAIL" "Missing degradation thresholds"
fi

# ============================================================================
# SECTION 4: API Endpoints
# ============================================================================

log_section "4. API Endpoint Availability"

# Check /health endpoint
STATUS=$(curl -s -H "X-API-Key: staging-api-key-2025" -o /dev/null -w "%{http_code}" http://localhost:9000/health)
if [ "$STATUS" = "200" ]; then
    check_result "/health endpoint responds" "PASS"
else
    check_result "/health endpoint responds" "FAIL" "Got HTTP $STATUS"
fi

# Check /metrics endpoint
STATUS=$(curl -s -H "X-API-Key: staging-api-key-2025" -o /dev/null -w "%{http_code}" http://localhost:9000/metrics)
if [ "$STATUS" = "200" ] || [ "$STATUS" = "401" ]; then
    check_result "/metrics endpoint available" "PASS"
else
    check_result "/metrics endpoint available" "FAIL" "Got HTTP $STATUS"
fi

# ============================================================================
# SECTION 5: Metrics Collection
# ============================================================================

log_section "5. Metrics Collection"

# Check Prometheus metrics
METRICS=$(curl -s http://localhost:9091/metrics 2>/dev/null | head -50)
if echo "$METRICS" | grep -q "circuit_breaker\|cb_\|degradation"; then
    check_result "Prometheus collecting metrics" "PASS"
else
    check_result "Prometheus collecting metrics" "FAIL" "Prometheus not collecting expected metrics"
fi

# Check Grafana availability
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3003/api/health)
if [ "$STATUS" = "200" ] || [ "$STATUS" = "302" ]; then
    check_result "Grafana dashboard accessible" "PASS"
else
    check_result "Grafana dashboard accessible" "FAIL" "Got HTTP $STATUS"
fi

# ============================================================================
# SECTION 6: Database Connectivity
# ============================================================================

log_section "6. Database Connectivity Verification"

# Check database via health endpoint
HEALTH=$(curl -s -H "X-API-Key: staging-api-key-2025" http://localhost:9000/health | jq '.database' 2>/dev/null)
if [ "$HEALTH" = '"connected"' ] || [ "$HEALTH" = '"degraded"' ]; then
    check_result "Database connectivity verified" "PASS"
else
    check_result "Database connectivity verified" "FAIL" "Database not connected: $HEALTH"
fi

# ============================================================================
# SECTION 7: Test Suite Files
# ============================================================================

log_section "7. Test Suite File Verification"

# Check failure injection tests exist
if [ -f "$WORKSPACE/tests/staging/test_failure_injection_dia5.py" ]; then
    check_result "Failure injection tests created" "PASS"
    
    # Count test classes and methods
    TEST_CLASSES=$(grep -c "^class Test" "$WORKSPACE/tests/staging/test_failure_injection_dia5.py")
    TEST_METHODS=$(grep -c "async def test_" "$WORKSPACE/tests/staging/test_failure_injection_dia5.py")
    
    echo "  Test Classes: $TEST_CLASSES" | tee -a "$VALIDATION_LOG"
    echo "  Test Methods: $TEST_METHODS" | tee -a "$VALIDATION_LOG"
else
    check_result "Failure injection tests created" "FAIL" "Tests file not found"
fi

# ============================================================================
# SECTION 8: Smoke Test Compatibility
# ============================================================================

log_section "8. Smoke Test Compatibility"

if [ -f "$WORKSPACE/tests/staging/smoke_test_staging.py" ]; then
    check_result "Smoke tests still in place" "PASS"
else
    check_result "Smoke tests still in place" "FAIL" "Smoke tests file not found"
fi

# ============================================================================
# SECTION 9: Configuration Files
# ============================================================================

log_section "9. Configuration Files Verification"

# Check docker-compose
if [ -f "$WORKSPACE/docker-compose.staging.yml" ]; then
    check_result "Docker Compose file present" "PASS"
else
    check_result "Docker Compose file present" "FAIL" "docker-compose.staging.yml not found"
fi

# Check .env.staging
if [ -f "$WORKSPACE/.env.staging" ]; then
    check_result ".env.staging file present" "PASS"
else
    check_result ".env.staging file present" "FAIL" ".env.staging not found"
fi

# ============================================================================
# SECTION 10: Docker Container Status
# ============================================================================

log_section "10. Docker Container Status"

# Check running containers
CONTAINERS=$(docker-compose -f "$WORKSPACE/docker-compose.staging.yml" ps 2>/dev/null | grep "staging" | wc -l)
if [ "$CONTAINERS" -ge 4 ]; then
    check_result "Staging containers running" "PASS"
    echo "  Active containers: $CONTAINERS" | tee -a "$VALIDATION_LOG"
else
    check_result "Staging containers running" "FAIL" "Expected 4+, found $CONTAINERS"
fi

# Check container health
HEALTHY=$(docker-compose -f "$WORKSPACE/docker-compose.staging.yml" ps 2>/dev/null | grep "healthy" | wc -l)
if [ "$HEALTHY" -ge 2 ]; then
    check_result "Services showing healthy status" "PASS"
    echo "  Healthy services: $HEALTHY" | tee -a "$VALIDATION_LOG"
else
    check_result "Services showing healthy status" "FAIL" "Expected 2+, found $HEALTHY"
fi

# ============================================================================
# SECTION 11: Recovery Configuration
# ============================================================================

log_section "11. Recovery Mechanism Configuration"

# Check recovery timeouts
if [ -n "$OPENAI_CB_RECOVERY_TIMEOUT" ]; then
    check_result "OpenAI recovery timeout configured" "PASS"
else
    check_result "OpenAI recovery timeout configured" "FAIL"
fi

if [ -n "$DB_CB_RECOVERY_TIMEOUT" ]; then
    check_result "Database recovery timeout configured" "PASS"
else
    check_result "Database recovery timeout configured" "FAIL"
fi

# Check half-open request limits
if [ -n "$OPENAI_CB_HALF_OPEN_REQUESTS" ]; then
    check_result "Half-open request limits configured" "PASS"
else
    check_result "Half-open request limits configured" "FAIL"
fi

# ============================================================================
# SECTION 12: Ready for Testing
# ============================================================================

log_section "12. Readiness for Failure Testing"

# All services up
if [ "$CONTAINERS" -ge 4 ]; then
    check_result "All services deployed" "PASS"
else
    check_result "All services deployed" "FAIL"
fi

# Tests created
if [ -f "$WORKSPACE/tests/staging/test_failure_injection_dia5.py" ]; then
    check_result "Failure tests ready" "PASS"
else
    check_result "Failure tests ready" "FAIL"
fi

# Configuration complete
if [ -n "$HEALTH_CHECK_INTERVAL" ] && [ -n "$OPTIMAL_THRESHOLD" ]; then
    check_result "Configuration complete" "PASS"
else
    check_result "Configuration complete" "FAIL"
fi

# ============================================================================
# SUMMARY
# ============================================================================

log_section "VALIDATION SUMMARY"

PERCENTAGE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo ""
echo "Total Checks: $TOTAL_CHECKS" | tee -a "$VALIDATION_LOG"
echo "Passed: $PASSED_CHECKS" | tee -a "$VALIDATION_LOG"
echo "Failed: $((TOTAL_CHECKS - PASSED_CHECKS))" | tee -a "$VALIDATION_LOG"
echo "Success Rate: $PERCENTAGE%" | tee -a "$VALIDATION_LOG"
echo ""

if [ $PERCENTAGE -ge 90 ]; then
    echo -e "${GREEN}✓ VALIDATION SUCCESSFUL - Ready for failure injection testing${NC}" | tee -a "$VALIDATION_LOG"
    exit 0
elif [ $PERCENTAGE -ge 80 ]; then
    echo -e "${YELLOW}⚠ VALIDATION PASSED WITH WARNINGS - Most checks successful${NC}" | tee -a "$VALIDATION_LOG"
    exit 0
else
    echo -e "${RED}✗ VALIDATION FAILED - Critical checks did not pass${NC}" | tee -a "$VALIDATION_LOG"
    exit 1
fi
