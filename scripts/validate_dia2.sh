#!/bin/bash
################################################################################
# validate_dia2.sh - DÍA 2 (HORAS 6-8) Validation Script
#
# Performs 20+ automated checks to validate all DÍA 2 deliverables
# Components tested:
#   - degradation_manager.py (enhanced)
#   - degradation_config.py (new)
#   - integration_degradation_breakers.py (new)
#   - recovery_loop.py (new)
#   - health_aggregator.py (new)
#
# Author: Operations Team
# Date: October 18, 2025
################################################################################

set -e  # Exit on first error

WORKSPACE="/home/eevan/ProyectosIA/aidrive_genspark"
SHARED_PATH="$WORKSPACE/inventario-retail/shared"
TEST_PATH="$WORKSPACE/tests/resilience"
VENV_PATH="$WORKSPACE/resilience_env"

# Debug: Print actual paths
echo "WORKSPACE: $WORKSPACE"
echo "SHARED_PATH: $SHARED_PATH"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
TOTAL_CHECKS=0

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

check_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((CHECKS_PASSED++))
    ((TOTAL_CHECKS++))
}

check_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((CHECKS_FAILED++))
    ((TOTAL_CHECKS++))
}

print_header() {
    echo ""
    echo -e "${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================================================================${NC}"
}

print_summary() {
    echo ""
    echo -e "${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}VALIDATION SUMMARY${NC}"
    echo -e "${BLUE}=================================================================================${NC}"
    echo -e "Total Checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
    if [ $CHECKS_FAILED -gt 0 ]; then
        echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
    fi
    echo ""
    
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ ALL CHECKS PASSED!${NC}"
        return 0
    else
        echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
        return 1
    fi
}

# ============================================================================
# SECTION 1: FILE EXISTENCE CHECKS
# ============================================================================

print_header "Section 1: File Existence Checks"

# Check 1: degradation_manager.py exists
if [ -f "$SHARED_PATH/degradation_manager.py" ]; then
    check_pass "degradation_manager.py exists"
else
    check_fail "degradation_manager.py exists"
    exit 1
fi

# Check 2: degradation_config.py exists
if [ -f "$SHARED_PATH/degradation_config.py" ]; then
    check_pass "degradation_config.py exists"
else
    check_fail "degradation_config.py exists"
    exit 1
fi

# Check 3: integration_degradation_breakers.py exists
if [ -f "$SHARED_PATH/integration_degradation_breakers.py" ]; then
    check_pass "integration_degradation_breakers.py exists"
else
    check_fail "integration_degradation_breakers.py exists"
    exit 1
fi

# Check 4: recovery_loop.py exists
if [ -f "$SHARED_PATH/recovery_loop.py" ]; then
    check_pass "recovery_loop.py exists"
else
    check_fail "recovery_loop.py exists"
    exit 1
fi

# Check 5: health_aggregator.py exists
if [ -f "$SHARED_PATH/health_aggregator.py" ]; then
    check_pass "health_aggregator.py exists"
else
    check_fail "health_aggregator.py exists"
    exit 1
fi

# Check 6: Test file exists
if [ -f "$TEST_PATH/test_degradation_dia2.py" ]; then
    check_pass "test_degradation_dia2.py exists"
else
    check_fail "test_degradation_dia2.py exists"
fi

# ============================================================================
# SECTION 2: SYNTAX VERIFICATION
# ============================================================================

print_header "Section 2: Python Syntax Verification"

python_compile() {
    if python3 -m py_compile "$1" 2>/dev/null; then
        check_pass "Syntax OK: $(basename $1)"
        return 0
    else
        check_fail "Syntax OK: $(basename $1)"
        return 1
    fi
}

python_compile "$SHARED_PATH/degradation_manager.py" || exit 1
python_compile "$SHARED_PATH/degradation_config.py" || exit 1
python_compile "$SHARED_PATH/integration_degradation_breakers.py" || exit 1
python_compile "$SHARED_PATH/recovery_loop.py" || exit 1
python_compile "$SHARED_PATH/health_aggregator.py" || exit 1

# ============================================================================
# SECTION 3: LINE COUNT VERIFICATION
# ============================================================================

print_header "Section 3: Line Count Verification"

check_line_count() {
    local file="$1"
    local expected_min="$2"
    local expected_max="$3"
    local count=$(wc -l < "$file")
    
    if [ "$count" -ge "$expected_min" ] && [ "$count" -le "$expected_max" ]; then
        check_pass "Line count for $(basename $file): $count lines (expected: $expected_min-$expected_max)"
    else
        check_fail "Line count for $(basename $file): $count lines (expected: $expected_min-$expected_max)"
    fi
}

check_line_count "$SHARED_PATH/degradation_manager.py" 450 500
check_line_count "$SHARED_PATH/degradation_config.py" 420 480
check_line_count "$SHARED_PATH/integration_degradation_breakers.py" 420 480
check_line_count "$SHARED_PATH/recovery_loop.py" 400 450
check_line_count "$SHARED_PATH/health_aggregator.py" 400 450

# ============================================================================
# SECTION 4: KEY CLASS VERIFICATION
# ============================================================================

print_header "Section 4: Key Class Verification"

check_class_exists() {
    local file="$1"
    local class_name="$2"
    
    if grep -q "^class $class_name" "$file"; then
        check_pass "Class $class_name exists in $(basename $file)"
    else
        check_fail "Class $class_name exists in $(basename $file)"
    fi
}

# degradation_manager.py classes
check_class_exists "$SHARED_PATH/degradation_manager.py" "ComponentHealth"
check_class_exists "$SHARED_PATH/degradation_manager.py" "AutoScalingConfig"
check_class_exists "$SHARED_PATH/degradation_manager.py" "DegradationManager"

# degradation_config.py classes
check_class_exists "$SHARED_PATH/degradation_config.py" "FeatureAvailability"
check_class_exists "$SHARED_PATH/degradation_config.py" "DegradationThresholds"
check_class_exists "$SHARED_PATH/degradation_config.py" "ComponentWeights"

# integration_degradation_breakers.py classes
check_class_exists "$SHARED_PATH/integration_degradation_breakers.py" "CircuitBreakerSnapshot"
check_class_exists "$SHARED_PATH/integration_degradation_breakers.py" "DegradationBreakerIntegration"

# recovery_loop.py classes
check_class_exists "$SHARED_PATH/recovery_loop.py" "RecoveryCheckpoint"
check_class_exists "$SHARED_PATH/recovery_loop.py" "AutoRecoveryLoop"

# health_aggregator.py classes
check_class_exists "$SHARED_PATH/health_aggregator.py" "HealthScoreCalculator"
check_class_exists "$SHARED_PATH/health_aggregator.py" "HealthStateMachine"

# ============================================================================
# SECTION 5: KEY METHOD VERIFICATION
# ============================================================================

print_header "Section 5: Key Method Verification"

check_method_exists() {
    local file="$1"
    local method_name="$2"
    
    if grep -q "def $method_name" "$file"; then
        check_pass "Method $method_name exists in $(basename $file)"
    else
        check_fail "Method $method_name exists in $(basename $file)"
    fi
}

# Critical methods in degradation_manager.py
check_method_exists "$SHARED_PATH/degradation_manager.py" "calculate_overall_health_score"
check_method_exists "$SHARED_PATH/degradation_manager.py" "predict_recovery_time"
check_method_exists "$SHARED_PATH/degradation_manager.py" "get_resource_scaling_config"

# Critical methods in recovery_loop.py
check_method_exists "$SHARED_PATH/recovery_loop.py" "predict_recovery_success"
check_method_exists "$SHARED_PATH/recovery_loop.py" "record_failure"

# Critical methods in health_aggregator.py
check_method_exists "$SHARED_PATH/health_aggregator.py" "calculate_component_score"
check_method_exists "$SHARED_PATH/health_aggregator.py" "get_next_state"

# ============================================================================
# SECTION 6: CONFIGURATION VALIDATION
# ============================================================================

print_header "Section 6: Configuration Validation"

# Check 6.1: Component weights sum to 1.0
if python3 << 'PYTHON_CHECK' 2>/dev/null; then
    import sys
    sys.path.insert(0, "$SHARED_PATH")
    from degradation_config import ComponentWeights
    assert ComponentWeights.validate(), "Weights don't sum to 1.0"
PYTHON_CHECK
    check_pass "Component weights sum to 1.0"
else
    check_fail "Component weights sum to 1.0"
fi

# Check 6.2: DegradationThresholds are logical (decreasing)
if python3 << 'PYTHON_CHECK' 2>/dev/null; then
    import sys
    sys.path.insert(0, "$SHARED_PATH")
    from degradation_config import DegradationThresholds
    th = DegradationThresholds.get_thresholds()
    assert th['optimal_min'] > th['degraded_min'] > th['limited_min'] > th['minimal_min']
PYTHON_CHECK
    check_pass "Degradation thresholds are logically ordered"
else
    check_fail "Degradation thresholds are logically ordered"
fi

# ============================================================================
# SECTION 7: IMPORT VERIFICATION
# ============================================================================

print_header "Section 7: Import Verification"

# Test that all modules can be imported
if python3 << 'PYTHON_IMPORT' 2>/dev/null; then
    import sys
    sys.path.insert(0, "$SHARED_PATH")
    from degradation_manager import DegradationManager
    from degradation_config import degradation_config
    from integration_degradation_breakers import DegradationBreakerIntegration
    from recovery_loop import AutoRecoveryLoop
    from health_aggregator import HealthAggregator
PYTHON_IMPORT
    check_pass "All modules import successfully"
else
    check_fail "All modules import successfully"
fi

# ============================================================================
# SECTION 8: FEATURE MATRIX VALIDATION
# ============================================================================

print_header "Section 8: Feature Matrix Validation"

# Check that feature availability levels exist
if python3 << 'PYTHON_FEATURES' 2>/dev/null; then
    import sys
    sys.path.insert(0, "$SHARED_PATH")
    from degradation_config import FeatureAvailability
    levels = ['OPTIMAL', 'DEGRADED', 'LIMITED', 'MINIMAL', 'EMERGENCY']
    for level in levels:
        features = FeatureAvailability.get_available_features(level)
        assert isinstance(features, set), f"Features for {level} not a set"
        assert len(features) > 0, f"No features for {level}"
PYTHON_FEATURES
    check_pass "Feature matrix has all 5 degradation levels"
else
    check_fail "Feature matrix has all 5 degradation levels"
fi

# ============================================================================
# SECTION 9: PROMETHEUS METRICS
# ============================================================================

print_header "Section 9: Prometheus Metrics Verification"

# Check that health score metric is defined
if grep -q "health_score" "$SHARED_PATH/degradation_manager.py"; then
    check_pass "Prometheus health_score metric defined"
else
    check_fail "Prometheus health_score metric defined"
fi

# Check that component health metric is defined
if grep -q "component_health" "$SHARED_PATH/degradation_manager.py"; then
    check_pass "Prometheus component_health metric defined"
else
    check_fail "Prometheus component_health metric defined"
fi

# ============================================================================
# SECTION 10: CODE QUALITY CHECKS
# ============================================================================

print_header "Section 10: Code Quality Checks"

# Check for proper docstrings
if grep -q '"""' "$SHARED_PATH/degradation_config.py"; then
    check_pass "degradation_config.py has docstrings"
else
    check_fail "degradation_config.py has docstrings"
fi

if grep -q '"""' "$SHARED_PATH/recovery_loop.py"; then
    check_pass "recovery_loop.py has docstrings"
else
    check_fail "recovery_loop.py has docstrings"
fi

# Check for proper error handling (try/except)
if grep -q "except" "$SHARED_PATH/degradation_manager.py"; then
    check_pass "degradation_manager.py has error handling"
else
    check_fail "degradation_manager.py has error handling"
fi

if grep -q "except" "$SHARED_PATH/health_aggregator.py"; then
    check_pass "health_aggregator.py has error handling"
else
    check_fail "health_aggregator.py has error handling"
fi

# ============================================================================
# SECTION 11: CONFIGURATION CONSISTENCY
# ============================================================================

print_header "Section 11: Configuration Consistency"

# Check that component names are consistent
if python3 << 'PYTHON_CONSISTENCY' 2>/dev/null; then
    import sys
    sys.path.insert(0, "$SHARED_PATH")
    from degradation_config import ComponentCircuitBreakerThresholds
    components = ['OPENAI', 'DATABASE', 'REDIS', 'S3']
    for comp in components:
        assert hasattr(ComponentCircuitBreakerThresholds, comp), f"Missing {comp}"
PYTHON_CONSISTENCY
    check_pass "All expected components in thresholds"
else
    check_fail "All expected components in thresholds"
fi

# ============================================================================
# SECTION 12: RECOVERY MECHANISM VALIDATION
# ============================================================================

print_header "Section 12: Recovery Mechanism Validation"

# Check exponential backoff logic
if grep -q "backoff" "$SHARED_PATH/recovery_loop.py"; then
    check_pass "Exponential backoff logic present"
else
    check_fail "Exponential backoff logic present"
fi

# Check pattern detection
if grep -q "detect_sequential_pattern" "$SHARED_PATH/recovery_loop.py"; then
    check_pass "Pattern detection implemented"
else
    check_fail "Pattern detection implemented"
fi

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print_summary
exit_code=$?

# Print timestamp
echo -e "${BLUE}Validation completed at: $(date)${NC}"
echo ""

exit $exit_code
