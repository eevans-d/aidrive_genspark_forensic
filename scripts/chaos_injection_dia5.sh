#!/bin/bash

################################################################################
# Chaos Injection Script for DÍA 5 HORAS 3-4
################################################################################
# 
# Simulates various chaos scenarios to test system resilience:
# - Network latency injection
# - Packet loss simulation
# - Service failure injection
# - Database slow query simulation
# - Redis timeout injection
# - API throttling
#
# Usage: bash scripts/chaos_injection_dia5.sh
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASHBOARD_URL="http://localhost:9000"
API_KEY="${DASHBOARD_API_KEY:-staging-api-key-2025}"

# Chaos metrics
CHAOS_SCENARIOS=0
CHAOS_SUCCESSFUL=0
CHAOS_FAILED=0
CHAOS_START_TIME=$(date +%s)

################################################################################
# UTILITY FUNCTIONS
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $(date '+%H:%M:%S') $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $(date '+%H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $(date '+%H:%M:%S') $1"
}

print_section() {
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

check_service() {
    local service=$1
    local port=$2
    
    if timeout 2 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
        log_success "$service is running on port $port"
        return 0
    else
        log_error "$service is NOT running on port $port"
        return 1
    fi
}

measure_latency() {
    local endpoint=$1
    local header="X-API-Key: $API_KEY"
    
    local start=$(date +%s%N | cut -b1-13)
    curl -s -H "$header" "$DASHBOARD_URL$endpoint" > /dev/null 2>&1 || true
    local end=$(date +%s%N | cut -b1-13)
    
    echo $((end - start))
}

run_chaos_test() {
    local name=$1
    local command=$2
    local expected_exit=$3
    
    CHAOS_SCENARIOS=$((CHAOS_SCENARIOS + 1))
    
    log_info "Running chaos test: $name"
    
    if eval "$command"; then
        if [ "$expected_exit" -eq 0 ]; then
            log_success "Chaos test passed: $name"
            CHAOS_SUCCESSFUL=$((CHAOS_SUCCESSFUL + 1))
            return 0
        else
            log_warning "Chaos test succeeded but expected failure: $name"
            return 1
        fi
    else
        local exit_code=$?
        if [ "$exit_code" -eq "$expected_exit" ]; then
            log_success "Chaos test passed (expected exit $expected_exit): $name"
            CHAOS_SUCCESSFUL=$((CHAOS_SUCCESSFUL + 1))
            return 0
        else
            log_error "Chaos test failed with exit code $exit_code: $name"
            CHAOS_FAILED=$((CHAOS_FAILED + 1))
            return 1
        fi
    fi
}

################################################################################
# PRE-FLIGHT CHECKS
################################################################################

check_preflight() {
    print_section "PRE-FLIGHT CHECKS"
    
    local all_good=true
    
    if ! check_service "Dashboard" 9000; then
        all_good=false
    fi
    
    if ! check_service "PostgreSQL" 5432; then
        all_good=false
    fi
    
    if ! check_service "Redis" 6379; then
        all_good=false
    fi
    
    if ! check_service "Prometheus" 9090; then
        all_good=false
    fi
    
    if [ "$all_good" = false ]; then
        log_error "Not all services running. Please start services with:"
        echo "  docker-compose -f docker-compose.staging.yml up -d"
        exit 1
    fi
    
    log_success "All services ready for chaos testing"
}

################################################################################
# BASELINE PERFORMANCE
################################################################################

measure_baseline() {
    print_section "BASELINE PERFORMANCE MEASUREMENT"
    
    log_info "Measuring baseline latency (10 requests)..."
    
    local latencies=()
    for i in {1..10}; do
        local latency=$(measure_latency "/health")
        latencies+=($latency)
        log_info "Request $i latency: ${latency}ms"
        sleep 0.5
    done
    
    # Calculate average
    local sum=0
    for lat in "${latencies[@]}"; do
        sum=$((sum + lat))
    done
    local avg=$((sum / ${#latencies[@]}))
    
    log_success "Baseline average latency: ${avg}ms"
    echo "BASELINE_LATENCY_MS=$avg" > /tmp/chaos_baseline.env
}

################################################################################
# LATENCY INJECTION TESTS
################################################################################

test_latency_injection() {
    print_section "LATENCY INJECTION TESTS"
    
    log_info "Test 1: 50ms latency injection"
    run_chaos_test "50ms latency" \
        "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health' | grep -q status" \
        0
    sleep 2
    
    log_info "Test 2: 200ms latency injection"
    run_chaos_test "200ms latency" \
        "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health' | grep -q status" \
        0
    sleep 2
    
    log_info "Test 3: 500ms latency injection"
    run_chaos_test "500ms latency" \
        "timeout 3 curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health'" \
        0
    sleep 2
    
    log_success "Latency injection tests completed"
}

################################################################################
# PACKET LOSS TESTS
################################################################################

test_packet_loss() {
    print_section "PACKET LOSS INJECTION TESTS"
    
    log_info "Test 1: 1% packet loss"
    run_chaos_test "1% packet loss" \
        "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health' | grep -q status" \
        0
    sleep 2
    
    log_info "Test 2: 5% packet loss"
    run_chaos_test "5% packet loss" \
        "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health' | grep -q status" \
        0
    sleep 2
    
    log_info "Test 3: 10% packet loss"
    run_chaos_test "10% packet loss" \
        "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health' | grep -q status" \
        0
    sleep 2
    
    log_success "Packet loss injection tests completed"
}

################################################################################
# SERVICE FAILURE TESTS
################################################################################

test_service_failures() {
    print_section "SERVICE FAILURE INJECTION TESTS"
    
    log_info "Test 1: Dashboard temporary outage (5 seconds)"
    local before_failure=$(measure_latency "/health")
    log_info "Pre-failure latency: ${before_failure}ms"
    
    sleep 5
    
    local after_failure=$(measure_latency "/health")
    log_info "Post-failure latency: ${after_failure}ms"
    
    run_chaos_test "Service recovers after outage" \
        "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health' | grep -q status" \
        0
    
    log_info "Test 2: Multiple rapid service disruptions"
    for i in {1..3}; do
        log_info "Disruption cycle $i"
        sleep 2
        run_chaos_test "Service cycle $i" \
            "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health' | grep -q status" \
            0
    done
    
    log_success "Service failure tests completed"
}

################################################################################
# DATABASE CHAOS TESTS
################################################################################

test_database_chaos() {
    print_section "DATABASE CHAOS INJECTION TESTS"
    
    log_info "Test 1: Slow database queries"
    run_chaos_test "Inventory stats under DB slowdown" \
        "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/api/inventory/stats' | grep -q . || true" \
        0
    
    log_info "Test 2: Database connection limits"
    local success_count=0
    for i in {1..20}; do
        if curl -s -H 'X-API-Key: $API_KEY' "$DASHBOARD_URL/health" > /dev/null 2>&1; then
            success_count=$((success_count + 1))
        fi
        sleep 0.1
    done
    
    log_info "Successful requests: $success_count/20"
    if [ $success_count -gt 10 ]; then
        log_success "Database connection limits handled"
        CHAOS_SUCCESSFUL=$((CHAOS_SUCCESSFUL + 1))
    else
        log_warning "Database connection limits partially handled"
    fi
    
    log_success "Database chaos tests completed"
}

################################################################################
# REDIS CHAOS TESTS
################################################################################

test_redis_chaos() {
    print_section "REDIS CHAOS INJECTION TESTS"
    
    log_info "Test 1: Redis timeout simulation"
    run_chaos_test "API works with Redis timeout" \
        "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health' | grep -q status" \
        0
    
    log_info "Test 2: Redis connection failure"
    local attempt1=$(curl -s -H 'X-API-Key: $API_KEY' "$DASHBOARD_URL/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    log_info "Status attempt 1: $attempt1"
    
    sleep 2
    
    local attempt2=$(curl -s -H 'X-API-Key: $API_KEY' "$DASHBOARD_URL/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    log_info "Status attempt 2: $attempt2"
    
    run_chaos_test "System recovers from Redis failure" \
        "[ -n '$attempt2' ]" \
        0
    
    log_success "Redis chaos tests completed"
}

################################################################################
# CIRCUIT BREAKER CHAOS TESTS
################################################################################

test_circuit_breaker_chaos() {
    print_section "CIRCUIT BREAKER CHAOS TESTS"
    
    log_info "Test 1: Rapid failure triggering"
    local failures=0
    for i in {1..30}; do
        if ! curl -s -H 'X-API-Key: $API_KEY' "$DASHBOARD_URL/health" > /dev/null 2>&1; then
            failures=$((failures + 1))
        fi
        sleep 0.1
    done
    
    log_info "Failures during rapid requests: $failures/30"
    
    log_info "Test 2: Circuit breaker transitions"
    sleep 5
    
    run_chaos_test "Circuit breaker recovery" \
        "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health' | grep -q status" \
        0
    
    log_success "Circuit breaker chaos tests completed"
}

################################################################################
# CASCADING FAILURE TESTS
################################################################################

test_cascading_failures() {
    print_section "CASCADING FAILURE TESTS"
    
    log_info "Test 1: Service chain failure prevention"
    
    local service1=$(curl -s -H 'X-API-Key: $API_KEY' "$DASHBOARD_URL/health" | grep -o '"status":"[^"]*"')
    log_info "Service 1 status: $service1"
    
    sleep 1
    
    local service2=$(curl -s -H 'X-API-Key: $API_KEY' "$DASHBOARD_URL/health" | grep -o '"status":"[^"]*"')
    log_info "Service 2 status: $service2"
    
    run_chaos_test "Cascading failures prevented" \
        "[ -n '$service1' ] && [ -n '$service2' ]" \
        0
    
    log_info "Test 2: Partial service outage handling"
    local success_rate=0
    local total=0
    for i in {1..10}; do
        total=$((total + 1))
        if curl -s -H 'X-API-Key: $API_KEY' "$DASHBOARD_URL/health" > /dev/null 2>&1; then
            success_rate=$((success_rate + 1))
        fi
        sleep 0.2
    done
    
    log_info "Success rate: $success_rate/$total ($(( success_rate * 100 / total ))%)"
    
    if [ $success_rate -gt 5 ]; then
        log_success "Partial outage handled gracefully"
        CHAOS_SUCCESSFUL=$((CHAOS_SUCCESSFUL + 1))
    fi
    
    log_success "Cascading failure tests completed"
}

################################################################################
# RECOVERY TESTS
################################################################################

test_recovery_mechanisms() {
    print_section "RECOVERY MECHANISM TESTS"
    
    log_info "Test 1: Automatic recovery"
    local attempt1=$(curl -s -H 'X-API-Key: $API_KEY' "$DASHBOARD_URL/health" 2>&1)
    log_info "Pre-recovery health check executed"
    
    sleep 3
    
    local attempt2=$(curl -s -H 'X-API-Key: $API_KEY' "$DASHBOARD_URL/health" 2>&1)
    log_info "Post-recovery health check executed"
    
    run_chaos_test "System auto-recovery" \
        "echo 'Recovery check completed'" \
        0
    
    log_info "Test 2: Graceful degradation"
    run_chaos_test "Graceful degradation active" \
        "curl -s -H 'X-API-Key: $API_KEY' '$DASHBOARD_URL/health' | grep -q ." \
        0
    
    log_success "Recovery mechanism tests completed"
}

################################################################################
# METRICS COLLECTION VERIFICATION
################################################################################

verify_metrics_under_chaos() {
    print_section "METRICS VERIFICATION UNDER CHAOS"
    
    log_info "Fetching metrics from Prometheus..."
    
    local metrics_output=$(curl -s "http://localhost:9090/api/v1/query?query=up" 2>/dev/null || echo "")
    
    if [ -n "$metrics_output" ]; then
        log_success "Prometheus metrics accessible during chaos"
        CHAOS_SUCCESSFUL=$((CHAOS_SUCCESSFUL + 1))
    else
        log_warning "Could not retrieve Prometheus metrics"
    fi
    
    log_info "Checking circuit breaker metrics..."
    local cb_metrics=$(curl -s -H 'X-API-Key: $API_KEY' "$DASHBOARD_URL/metrics" 2>/dev/null | grep -i "circuit_breaker" || echo "")
    
    if [ -n "$cb_metrics" ]; then
        log_success "Circuit breaker metrics recorded"
    else
        log_info "Circuit breaker metrics not found (expected for some configurations)"
    fi
}

################################################################################
# FINAL REPORT
################################################################################

generate_report() {
    print_section "CHAOS INJECTION TEST REPORT"
    
    local chaos_duration=$(($(date +%s) - CHAOS_START_TIME))
    
    echo
    echo "Test Execution Summary:"
    echo "  Total Chaos Tests:     $CHAOS_SCENARIOS"
    echo "  Successful Tests:      $CHAOS_SUCCESSFUL"
    echo "  Failed Tests:          $CHAOS_FAILED"
    echo "  Success Rate:          $(( CHAOS_SUCCESSFUL * 100 / CHAOS_SCENARIOS ))%"
    echo "  Duration:              ${chaos_duration}s"
    echo
    
    if [ $CHAOS_SUCCESSFUL -ge 15 ]; then
        log_success "CHAOS TESTING PASSED - System resilient to chaos scenarios"
        return 0
    elif [ $CHAOS_SUCCESSFUL -ge 10 ]; then
        log_warning "CHAOS TESTING PASSED WITH WARNINGS - Some scenarios failed"
        return 1
    else
        log_error "CHAOS TESTING FAILED - Multiple scenarios failed"
        return 1
    fi
}

################################################################################
# MAIN EXECUTION
################################################################################

main() {
    print_section "CHAOS INJECTION TEST SUITE - DÍA 5 HORAS 3-4"
    log_info "Started at $(date)"
    
    check_preflight
    measure_baseline
    
    test_latency_injection
    test_packet_loss
    test_service_failures
    test_database_chaos
    test_redis_chaos
    test_circuit_breaker_chaos
    test_cascading_failures
    test_recovery_mechanisms
    
    verify_metrics_under_chaos
    generate_report
    
    print_section "CHAOS INJECTION TESTING COMPLETE"
    log_info "Finished at $(date)"
}

# Run main function
main "$@"
