#!/bin/bash
# Validate success criteria for definitive prompts

set -e

PROMPT=""
HELP=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prompt=*)
            PROMPT="${1#*=}"
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            HELP=true
            shift
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
done

if [ "$HELP" = true ]; then
    echo "Usage: $0 --prompt=<1|2|3> [--verbose]"
    echo ""
    echo "Options:"
    echo "  --prompt=N    Validate prompt N (1=consolidacion, 2=security, 3=testing)"
    echo "  -v, --verbose Show detailed validation results"
    echo "  -h, --help    Show this help"
    exit 0
fi

if [ -z "$PROMPT" ]; then
    echo "Error: --prompt parameter is required"
    exit 1
fi

echo "🎯 Validating Success Criteria for Prompt $PROMPT"
echo "=================================================="

validate_prompt1() {
    echo "🏗️  Validating Prompt 1: Consolidación Arquitectónica y Performance"
    local score=0
    local total=5
    
    # 1. Check for baseline documentation
    if [ -f "docs/diagnostico/baseline_consolidado.md" ]; then
        echo "✅ Baseline consolidado documentation exists"
        score=$((score + 1))
    else
        echo "❌ Missing baseline_consolidado.md"
    fi
    
    # 2. Check for SQLite configuration
    if find . -name "sqlite_config.py" | grep -q .; then
        echo "✅ SQLite configuration found"
        score=$((score + 1))
    else
        echo "❌ Missing SQLite configuration"
    fi
    
    # 3. Check for shared core directory
    if find . -path "*/app/shared/core/*" | grep -q .; then
        echo "✅ Shared core structure found"
        score=$((score + 1))
    else
        echo "❌ Missing shared core structure"
    fi
    
    # 4. Check for metrics endpoint
    if grep -r "/metrics" . --include="*.py" | grep -q .; then
        echo "✅ Metrics endpoint implemented"
        score=$((score + 1))
    else
        echo "❌ Missing metrics endpoint"
    fi
    
    # 5. Check for architecture documentation
    if [ -f "docs/architecture/sistema_consolidado.md" ]; then
        echo "✅ Architecture documentation exists"
        score=$((score + 1))
    else
        echo "❌ Missing architecture documentation"
    fi
    
    echo ""
    echo "📊 Prompt 1 Score: $score/$total ($(( score * 100 / total ))%)"
    
    if [ $score -ge 4 ]; then
        echo "🎉 SUCCESS: Criteria mostly met"
        return 0
    else
        echo "⚠️  WARNING: Some criteria not met"
        return 1
    fi
}

validate_prompt2() {
    echo "🔒 Validating Prompt 2: Security Hardening y Supply Chain"
    local score=0
    local total=5
    
    # 1. Check for dependency audit
    if [ -f "security/supply_chain/dependency_audit.md" ]; then
        echo "✅ Dependency audit documentation exists"
        score=$((score + 1))
    else
        echo "❌ Missing dependency audit"
    fi
    
    # 2. Check for security module
    if find . -path "*/app/security/*" | grep -q .; then
        echo "✅ Security module found"
        score=$((score + 1))
    else
        echo "❌ Missing security module"
    fi
    
    # 3. Check for audit module
    if find . -path "*/app/audit/*" | grep -q .; then
        echo "✅ Audit module found"
        score=$((score + 1))
    else
        echo "❌ Missing audit module"
    fi
    
    # 4. Check for security pipeline
    if [ -f ".github/workflows/security_pipeline.yml" ]; then
        echo "✅ Security pipeline found"
        score=$((score + 1))
    else
        echo "❌ Missing security pipeline"
    fi
    
    # 5. Check for security documentation
    if [ -d "docs/security" ] && [ "$(ls -A docs/security 2>/dev/null)" ]; then
        echo "✅ Security documentation exists"
        score=$((score + 1))
    else
        echo "❌ Missing security documentation"
    fi
    
    echo ""
    echo "📊 Prompt 2 Score: $score/$total ($(( score * 100 / total ))%)"
    
    if [ $score -ge 4 ]; then
        echo "🎉 SUCCESS: Criteria mostly met"
        return 0
    else
        echo "⚠️  WARNING: Some criteria not met"
        return 1
    fi
}

validate_prompt3() {
    echo "📊 Validating Prompt 3: Testing Integral y Observabilidad Avanzada"
    local score=0
    local total=5
    
    # 1. Check test structure
    if [ -d "tests" ] && find tests -name "test_*.py" | grep -q .; then
        echo "✅ Test structure found"
        score=$((score + 1))
    else
        echo "❌ Missing test structure"
    fi
    
    # 2. Check testing framework
    if [ -d "testing_framework" ] || find . -name "conftest.py" | grep -q .; then
        echo "✅ Testing framework found"
        score=$((score + 1))
    else
        echo "❌ Missing testing framework"
    fi
    
    # 3. Check analytics module
    if find . -path "*/app/analytics/*" | grep -q .; then
        echo "✅ Analytics module found"
        score=$((score + 1))
    else
        echo "❌ Missing analytics module"
    fi
    
    # 4. Check monitoring dashboards
    if [ -d "monitoring/dashboards" ] && [ "$(ls -A monitoring/dashboards 2>/dev/null)" ]; then
        echo "✅ Monitoring dashboards found"
        score=$((score + 1))
    else
        echo "❌ Missing monitoring dashboards"
    fi
    
    # 5. Check CI/CD integration
    if grep -q "pytest" .github/workflows/ci.yml 2>/dev/null; then
        echo "✅ CI/CD integration found"
        score=$((score + 1))
    else
        echo "❌ Missing CI/CD integration"
    fi
    
    echo ""
    echo "📊 Prompt 3 Score: $score/$total ($(( score * 100 / total ))%)"
    
    if [ $score -ge 4 ]; then
        echo "🎉 SUCCESS: Criteria mostly met"
        return 0
    else
        echo "⚠️  WARNING: Some criteria not met"
        return 1
    fi
}

# Execute validation based on prompt
case $PROMPT in
    1)
        validate_prompt1
        ;;
    2)
        validate_prompt2
        ;;
    3)
        validate_prompt3
        ;;
    *)
        echo "Error: Invalid prompt number. Use 1, 2, or 3."
        exit 1
        ;;
esac