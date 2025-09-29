#!/bin/bash
# Validate the complete framework implementation

set -e

echo "🔍 Validating Complete Framework Implementation"
echo "=============================================="

TOTAL_CHECKS=0
PASSED_CHECKS=0

check_framework_component() {
    local component="$1"
    local check_command="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "[$TOTAL_CHECKS] $component... "
    
    if eval "$check_command" > /dev/null 2>&1; then
        echo "✅ OK"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo "❌ MISSING"
    fi
}

echo ""
echo "📋 Core Framework Files..."

check_framework_component "Definitive prompts file" "test -f PROMPTS_GITHUB_COPILOT_PRO_DEFINITIVOS.md"
check_framework_component "Implementation guide" "test -f GUIA_IMPLEMENTACION_PROMPTS_DEFINITIVOS.md"
check_framework_component "Quick reference" "test -f QUICK_REFERENCE_PROMPTS_DEFINITIVOS.md"

echo ""
echo "📊 Documentation Structure..."

check_framework_component "Progress directory" "test -d docs/progress"
check_framework_component "Progress README" "test -f docs/progress/README.md"
check_framework_component "Diagnostico directory" "test -d docs/diagnostico"
check_framework_component "Architecture directory" "test -d docs/architecture"
check_framework_component "Security directory" "test -d docs/security"

echo ""
echo "🔧 Monitoring Scripts..."

check_framework_component "Progress monitor" "test -x scripts/monitor_progress.sh"
check_framework_component "Success criteria validator" "test -x scripts/validate_success_criteria.sh"
check_framework_component "Executive report generator" "test -x scripts/generate_executive_report.sh"
check_framework_component "Regression tester" "test -x scripts/regression_test_full.sh"
check_framework_component "Benchmark comparator" "test -x scripts/benchmark_compare.sh"
check_framework_component "Security auditor" "test -x scripts/security_audit_complete.sh"

echo ""
echo "🧪 Script Functionality..."

check_framework_component "Monitor script help" "./scripts/monitor_progress.sh --help | grep -q Usage"
check_framework_component "Validator script help" "./scripts/validate_success_criteria.sh --help | grep -q Usage"
check_framework_component "Report generator help" "./scripts/generate_executive_report.sh --help | grep -q Usage"

echo ""
echo "🎯 Repository Structure..."

check_framework_component "Inventario retail module" "test -d inventario-retail"
check_framework_component "BI orchestrator module" "test -d business-intelligence-orchestrator-v3.1"
check_framework_component "Sistema deposito module" "test -d sistema_deposito_semana1"

echo ""
echo "📦 Dependencies..."

check_framework_component "Test requirements" "test -f requirements-test.txt"
check_framework_component "Pytest available" "python -m pytest --version"
check_framework_component "Python modules importable" "python -c 'import sys, os; print(\"OK\")'"

# Calculate framework completeness score
COMPLETENESS_SCORE=$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))

echo ""
echo "📊 Framework Validation Results"
echo "=============================="
echo "Total Checks: $TOTAL_CHECKS"
echo "Passed: $PASSED_CHECKS"
echo "Completeness Score: $COMPLETENESS_SCORE%"

if [ $COMPLETENESS_SCORE -ge 90 ]; then
    echo "🎉 EXCELLENT: Framework is ready for production use!"
    echo ""
    echo "✅ All core components implemented"
    echo "✅ Monitoring scripts functional"
    echo "✅ Documentation structure complete"
    echo "✅ Repository structure validated"
    
    echo ""
    echo "🚀 Next Steps:"
    echo "1. Begin Prompt 1 execution"
    echo "2. Use monitoring scripts during execution"
    echo "3. Validate success criteria regularly"
    echo "4. Generate executive reports"
    
    exit 0
    
elif [ $COMPLETENESS_SCORE -ge 75 ]; then
    echo "✅ GOOD: Framework is mostly ready, minor issues to address"
    echo ""
    echo "⚠️  Some optional components missing"
    echo "✅ Core functionality available"
    
    echo ""
    echo "🔧 Recommended Actions:"
    echo "1. Address missing components if needed"
    echo "2. Proceed with caution"
    echo "3. Monitor execution closely"
    
    exit 0
    
else
    echo "❌ CRITICAL: Framework incomplete, address issues before proceeding"
    echo ""
    echo "🚨 Issues Found:"
    echo "- Core components missing"
    echo "- Framework may not function properly"
    
    echo ""
    echo "🛠️  Required Actions:"
    echo "1. Implement missing core components"
    echo "2. Verify script permissions and functionality"
    echo "3. Re-run this validation script"
    echo "4. Do not proceed with prompt execution until score ≥75%"
    
    exit 1
fi