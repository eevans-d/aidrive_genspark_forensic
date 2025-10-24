#!/bin/bash
# validate_monitoring.sh
# Comprehensive validation script for monitoring stack
# Verifies Prometheus, Grafana, AlertManager and integration with Dashboard

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
DASHBOARD_URL="${DASHBOARD_URL:-http://localhost:8080}"
DASHBOARD_API_KEY="${DASHBOARD_API_KEY:-dev}"

# Counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# Helper Functions
# ============================================================================

test_result() {
    local test_name="$1"
    local result="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

check_url() {
    local url="$1"
    local method="${2:-GET}"
    local timeout="5"
    
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" --connect-timeout "$timeout" "$url" 2>/dev/null || echo "000")
    
    if [[ "$http_code" =~ ^[23][0-9][0-9]$ ]]; then
        return 0
    else
        return 1
    fi
}

check_metric_exists() {
    local metric_name="$1"
    local query="$2"
    local expected_result="${3:-1}"
    
    response=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=$query" 2>/dev/null || echo "{}")
    
    result=$(echo "$response" | grep -q '"result":\[' && echo "1" || echo "0")
    
    if [ "$result" -eq "$expected_result" ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Prometheus Validation
# ============================================================================

echo -e "\n${BLUE}========== PROMETHEUS VALIDATION ==========${NC}\n"

# Test 1: Prometheus connectivity
check_url "$PROMETHEUS_URL/-/healthy"
test_result "Prometheus health check" $?

# Test 2: Prometheus config loaded
check_url "$PROMETHEUS_URL/api/v1/status/config"
test_result "Prometheus config endpoint" $?

# Test 3: Check scrape targets
echo "Checking Prometheus scrape targets..."
targets=$(curl -s "${PROMETHEUS_URL}/api/v1/targets" 2>/dev/null | grep -c '"scrapePool"' || echo "0")
if [ "$targets" -gt "0" ]; then
    echo -e "${GREEN}✓${NC} Found $targets scrape targets"
    test_result "Scrape targets configured" 0
else
    echo -e "${RED}✗${NC} No scrape targets found"
    test_result "Scrape targets configured" 1
fi

# Test 4: Dashboard metrics available
check_metric_exists "dashboard_requests_total" "dashboard_requests_total" 1
test_result "Dashboard metrics endpoint active" $?

# Test 5: Forensic metrics available
check_metric_exists "forensic_analyses_total" "forensic_analyses_total" 1
test_result "Forensic metrics endpoint active" $?

# Test 6: Alert rules loaded
rules=$(curl -s "${PROMETHEUS_URL}/api/v1/rules" 2>/dev/null | grep -c '"name"' || echo "0")
if [ "$rules" -gt "0" ]; then
    test_result "Alert rules loaded" 0
else
    test_result "Alert rules loaded" 1
fi

# Test 7: Retention policy configured
check_url "$PROMETHEUS_URL/api/v1/query" "POST"
test_result "Prometheus query API" $?

# ============================================================================
# Grafana Validation
# ============================================================================

echo -e "\n${BLUE}========== GRAFANA VALIDATION ==========${NC}\n"

# Test 8: Grafana connectivity
check_url "$GRAFANA_URL/api/health"
test_result "Grafana health check" $?

# Test 9: Grafana data sources
echo "Checking Grafana data sources..."
datasources=$(curl -s "$GRAFANA_URL/api/datasources" 2>/dev/null | grep -c '"name"' || echo "0")
if [ "$datasources" -gt "0" ]; then
    echo -e "${GREEN}✓${NC} Found $datasources data sources"
    test_result "Data sources configured" 0
else
    test_result "Data sources configured" 1
fi

# Test 10: Prometheus data source working
curl -s "$GRAFANA_URL/api/datasources" 2>/dev/null | grep -q "prometheus" && test_result "Prometheus data source configured" 0 || test_result "Prometheus data source configured" 1

# ============================================================================
# AlertManager Validation
# ============================================================================

echo -e "\n${BLUE}========== ALERTMANAGER VALIDATION ==========${NC}\n"

# Test 11: AlertManager connectivity
check_url "$ALERTMANAGER_URL/-/healthy"
test_result "AlertManager health check" $?

# Test 12: AlertManager alerts API
check_url "$ALERTMANAGER_URL/api/v2/alerts"
test_result "AlertManager alerts endpoint" $?

# Test 13: AlertManager status
check_url "$ALERTMANAGER_URL/api/v2/status"
test_result "AlertManager status endpoint" $?

# ============================================================================
# Dashboard Integration
# ============================================================================

echo -e "\n${BLUE}========== DASHBOARD INTEGRATION ==========${NC}\n"

# Test 14: Dashboard metrics endpoint with auth
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
    -H "X-API-Key: $DASHBOARD_API_KEY" \
    "$DASHBOARD_URL/metrics" 2>/dev/null)

if [[ "$http_code" == "200" ]]; then
    test_result "Dashboard metrics endpoint accessible" 0
else
    test_result "Dashboard metrics endpoint accessible" 1
fi

# Test 15: Check metrics format
metrics_format=$(curl -s -H "X-API-Key: $DASHBOARD_API_KEY" \
    "$DASHBOARD_URL/metrics" 2>/dev/null | head -5)

if [[ "$metrics_format" =~ "HELP" ]] || [[ "$metrics_format" =~ "TYPE" ]]; then
    test_result "Dashboard metrics in Prometheus format" 0
else
    test_result "Dashboard metrics in Prometheus format" 1
fi

# Test 16: Check forensic endpoint metrics
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
    "$DASHBOARD_URL/api/forensic/metrics" 2>/dev/null)

if [[ "$http_code" == "200" ]]; then
    test_result "Forensic metrics endpoint accessible" 0
else
    test_result "Forensic metrics endpoint accessible" 1
fi

# ============================================================================
# Monitoring Stack Integration
# ============================================================================

echo -e "\n${BLUE}========== STACK INTEGRATION CHECKS ==========${NC}\n"

# Test 17: Prometheus scrapes dashboard successfully
echo "Checking Prometheus dashboard scrape status..."
dashboard_scrape=$(curl -s "${PROMETHEUS_URL}/api/v1/targets" 2>/dev/null | \
    grep -c '"health":"up".*dashboard' || echo "0")

if [ "$dashboard_scrape" -gt "0" ]; then
    test_result "Prometheus scraping dashboard metrics" 0
else
    test_result "Prometheus scraping dashboard metrics" 1
fi

# Test 18: Prometheus scrapes forensic endpoint successfully
echo "Checking Prometheus forensic scrape status..."
forensic_scrape=$(curl -s "${PROMETHEUS_URL}/api/v1/targets" 2>/dev/null | \
    grep -c '"health":"up".*forensic' || echo "0")

if [ "$forensic_scrape" -gt "0" ]; then
    test_result "Prometheus scraping forensic metrics" 0
else
    test_result "Prometheus scraping forensic metrics" 1
fi

# Test 19: Alert rules configured in Prometheus
echo "Checking alert rules in Prometheus..."
alert_groups=$(curl -s "${PROMETHEUS_URL}/api/v1/rules" 2>/dev/null | grep -c '"name"' || echo "0")

if [ "$alert_groups" -gt "0" ]; then
    test_result "Alert rules configured" 0
else
    test_result "Alert rules configured" 1
fi

# Test 20: AlertManager reachable from Prometheus
echo "Checking AlertManager integration..."
am_config=$(curl -s "${PROMETHEUS_URL}/api/v1/status/config" 2>/dev/null | \
    grep -c "alertmanagers" || echo "0")

if [ "$am_config" -gt "0" ]; then
    test_result "Prometheus AlertManager configuration" 0
else
    test_result "Prometheus AlertManager configuration" 1
fi

# ============================================================================
# Performance Baseline
# ============================================================================

echo -e "\n${BLUE}========== PERFORMANCE BASELINE ==========${NC}\n"

# Test 21: Query performance
echo "Testing Prometheus query performance..."
start_time=$(date +%s%N)
curl -s "${PROMETHEUS_URL}/api/v1/query" \
    --data-urlencode "query=dashboard_requests_total" >/dev/null 2>&1
end_time=$(date +%s%N)

query_time=$((($end_time - $start_time) / 1000000))
echo "Query time: ${query_time}ms"

if [ "$query_time" -lt 1000 ]; then
    test_result "Prometheus query performance (<1s)" 0
else
    test_result "Prometheus query performance (<1s)" 1
fi

# Test 22: Scrape performance
echo "Checking average scrape duration..."
avg_scrape=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
    --data-urlencode "query=scrape_duration_seconds" 2>/dev/null | \
    grep -o '"value":\[[0-9.]*' | head -1 | cut -d: -f2)

if [ -n "$avg_scrape" ]; then
    echo "Average scrape duration: ${avg_scrape}s"
    test_result "Scrape performance baseline" 0
else
    test_result "Scrape performance baseline" 1
fi

# ============================================================================
# Security Validation
# ============================================================================

echo -e "\n${BLUE}========== SECURITY VALIDATION ==========${NC}\n"

# Test 23: Prometheus has authentication headers
prom_headers=$(curl -s -i "$PROMETHEUS_URL/-/healthy" 2>/dev/null | grep -c "Content-Security-Policy\|X-Frame-Options\|X-Content-Type-Options")

if [ "$prom_headers" -gt "0" ]; then
    test_result "Prometheus security headers configured" 0
else
    test_result "Prometheus security headers configured" 1
fi

# Test 24: Dashboard metrics require auth
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$DASHBOARD_URL/metrics" 2>/dev/null)

if [[ "$http_code" != "200" ]]; then
    test_result "Dashboard metrics endpoint protected" 0
else
    test_result "Dashboard metrics endpoint protected" 1
fi

# ============================================================================
# Summary Report
# ============================================================================

echo -e "\n${BLUE}========== VALIDATION SUMMARY ==========${NC}\n"

TESTS_FAILED_COUNT=$((TESTS_TOTAL - TESTS_PASSED))

if [ "$TESTS_FAILED_COUNT" -eq "0" ]; then
    echo -e "${GREEN}All $TESTS_TOTAL tests PASSED ✓${NC}"
    SUMMARY_COLOR=$GREEN
    EXIT_CODE=0
else
    SUMMARY_COLOR=$RED
    EXIT_CODE=1
    echo -e "${SUMMARY_COLOR}$TESTS_PASSED/$TESTS_TOTAL tests passed, $TESTS_FAILED_COUNT failed${NC}"
fi

echo -e "├─ Prometheus: $(curl -s "$PROMETHEUS_URL/-/healthy" >/dev/null 2>&1 && echo -e "${GREEN}UP${NC}" || echo -e "${RED}DOWN${NC}")"
echo -e "├─ Grafana: $(curl -s "$GRAFANA_URL/api/health" >/dev/null 2>&1 && echo -e "${GREEN}UP${NC}" || echo -e "${RED}DOWN${NC}")"
echo -e "├─ AlertManager: $(curl -s "$ALERTMANAGER_URL/-/healthy" >/dev/null 2>&1 && echo -e "${GREEN}UP${NC}" || echo -e "${RED}DOWN${NC}")"
echo -e "└─ Dashboard: $(curl -s "$DASHBOARD_URL/health" >/dev/null 2>&1 && echo -e "${GREEN}UP${NC}" || echo -e "${RED}DOWN${NC}")"

echo -e "\n${SUMMARY_COLOR}Summary: $TESTS_PASSED/$TESTS_TOTAL PASS${NC}\n"

exit $EXIT_CODE
