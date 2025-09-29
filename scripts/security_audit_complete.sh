#!/bin/bash
# Complete security audit for the repository

set -e

echo "🔒 Complete Security Audit"
echo "=========================="

DATE=$(date +%Y%m%d_%H%M)
AUDIT_DIR="docs/security"
mkdir -p "$AUDIT_DIR"
AUDIT_REPORT="$AUDIT_DIR/security_audit_${DATE}.md"

# Initialize audit report
cat > "$AUDIT_REPORT" << EOF
# Security Audit Report
Date: $(date)
Repository: eevans-d/aidrive_genspark_forensic

## Executive Summary
EOF

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

run_security_check() {
    local check_name="$1"
    local check_command="$2"
    local severity="$3"  # CRITICAL, HIGH, MEDIUM, LOW
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "[$TOTAL_CHECKS] $check_name... "
    
    if eval "$check_command" > /tmp/security_check_$TOTAL_CHECKS.log 2>&1; then
        echo "✅ PASS"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        echo "### ✅ $check_name" >> "$AUDIT_REPORT"
        echo "**Status:** PASS" >> "$AUDIT_REPORT"
        echo "**Severity:** $severity" >> "$AUDIT_REPORT"
        echo "" >> "$AUDIT_REPORT"
    else
        echo "❌ FAIL ($severity)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        if [ "$severity" = "CRITICAL" ] || [ "$severity" = "HIGH" ]; then
            WARNINGS=$((WARNINGS + 1))
        fi
        echo "### ❌ $check_name" >> "$AUDIT_REPORT"
        echo "**Status:** FAIL" >> "$AUDIT_REPORT"
        echo "**Severity:** $severity" >> "$AUDIT_REPORT"
        echo "**Details:** See /tmp/security_check_$TOTAL_CHECKS.log" >> "$AUDIT_REPORT"
        echo "" >> "$AUDIT_REPORT"
    fi
}

echo ""
echo "🔍 File and Directory Security..."

# Check 1: Sensitive files exposure
run_security_check "No sensitive files in root" "! find . -maxdepth 1 -name '*.key' -o -name '*.pem' -o -name '*.p12' | grep -q ." "HIGH"

# Check 2: Environment files
run_security_check "Environment files properly named" "! find . -name '.env' | grep -q ." "MEDIUM"

# Check 3: Secrets in code
run_security_check "No hardcoded secrets" "! grep -r 'password\s*=\|secret\s*=\|api_key\s*=' . --include='*.py' --include='*.js' | grep -v 'example\|template\|test' | grep -q ." "CRITICAL"

# Check 4: File permissions (if applicable)
run_security_check "No overly permissive files" "! find . -type f -perm /o+w | grep -q ." "MEDIUM"

echo ""
echo "🐍 Python Security..."

# Check 5: Requirements security (basic)
run_security_check "Requirements files exist" "find . -name 'requirements*.txt' | grep -q ." "LOW"

# Check 6: No eval/exec usage
run_security_check "No dangerous functions" "! grep -r 'eval(\|exec(' . --include='*.py' | grep -v test | grep -q ." "HIGH"

# Check 7: SQL injection patterns
run_security_check "No SQL injection patterns" "! grep -r 'cursor.execute.*%\|cursor.execute.*format' . --include='*.py' | grep -q ." "HIGH"

# Check 8: No pickle usage (potential deserialization)
run_security_check "No unsafe pickle usage" "! grep -r 'pickle.loads\|cPickle.loads' . --include='*.py' | grep -q ." "MEDIUM"

echo ""
echo "🌐 Web Security..."

# Check 9: CORS configuration
if grep -r "CORS\|cors" . --include="*.py" > /dev/null 2>&1; then
    run_security_check "CORS properly configured" "grep -r 'CORS.*allow_origins' . --include='*.py' | grep -v '\*' | grep -q ." "MEDIUM"
fi

# Check 10: Security headers
run_security_check "Security headers implemented" "grep -r 'X-Frame-Options\|X-Content-Type-Options\|Strict-Transport-Security' . --include='*.py' | grep -q ." "MEDIUM"

# Check 11: No debug mode in production configs
run_security_check "No debug mode enabled" "! grep -r 'debug.*=.*true\|DEBUG.*=.*True' . --include='*.py' --include='*.json' | grep -v 'example\|template\|test' | grep -q ." "HIGH"

echo ""
echo "🔐 Authentication & Authorization..."

# Check 12: Authentication implementation
if grep -r "auth\|login\|token" . --include="*.py" > /dev/null 2>&1; then
    run_security_check "Authentication mechanisms present" "grep -r 'auth\|token\|login' . --include='*.py' | grep -q ." "LOW"
fi

# Check 13: No default credentials
run_security_check "No default credentials" "! grep -r 'admin:admin\|user:password\|root:root' . --include='*.py' --include='*.json' --include='*.yml' | grep -q ." "CRITICAL"

echo ""
echo "📦 Dependencies & Supply Chain..."

# Check 14: Package managers present
run_security_check "Package management files exist" "find . -name 'requirements.txt' -o -name 'package.json' -o -name 'Pipfile' | grep -q ." "LOW"

# Check 15: No suspicious packages (basic check)
if [ -f "requirements.txt" ] || find . -name "requirements*.txt" | grep -q .; then
    run_security_check "No obviously suspicious packages" "! find . -name 'requirements*.txt' -exec grep -l 'backdoor\|malware\|trojan' {} \;" "CRITICAL"
fi

echo ""
echo "🚀 Deployment Security..."

# Check 16: Docker security (if Dockerfile exists)
if [ -f "Dockerfile" ]; then
    run_security_check "Docker security basics" "! grep -q 'FROM.*:latest' Dockerfile && ! grep -q 'USER root' Dockerfile" "MEDIUM"
fi

# Check 17: CI/CD security
if [ -d ".github/workflows" ]; then
    run_security_check "CI/CD workflows exist" "find .github/workflows -name '*.yml' | grep -q ." "LOW"
    run_security_check "No secrets in CI/CD" "! grep -r '\${{.*secret\|password\|key.*}}' .github/workflows/ | grep -v 'secrets\.' | grep -q ." "HIGH"
fi

echo ""
echo "📊 Security Enhancements..."

# Check 18: Security documentation
run_security_check "Security documentation exists" "find . -name '*security*' -o -name '*SECURITY*' | grep -q ." "LOW"

# Check 19: Audit logging
run_security_check "Audit mechanisms present" "grep -r 'audit\|log.*security' . --include='*.py' | grep -q . || find . -path '*/audit/*' | grep -q ." "MEDIUM"

# Check 20: Input validation
run_security_check "Input validation present" "grep -r 'pydantic\|validator\|validate' . --include='*.py' | grep -q ." "MEDIUM"

# Calculate security score
SECURITY_SCORE=$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))

# Add summary to report
cat >> "$AUDIT_REPORT" << EOF

## Security Score: $SECURITY_SCORE%

### Results Summary
- **Total Checks:** $TOTAL_CHECKS
- **Passed:** $PASSED_CHECKS
- **Failed:** $FAILED_CHECKS
- **Critical/High Warnings:** $WARNINGS

### Risk Assessment
EOF

if [ $WARNINGS -eq 0 ]; then
    cat >> "$AUDIT_REPORT" << EOF
**🟢 LOW RISK** - No critical security issues detected
EOF
elif [ $WARNINGS -le 2 ]; then
    cat >> "$AUDIT_REPORT" << EOF
**🟡 MEDIUM RISK** - Few critical issues detected, address promptly
EOF
else
    cat >> "$AUDIT_REPORT" << EOF
**🔴 HIGH RISK** - Multiple critical issues detected, immediate action required
EOF
fi

cat >> "$AUDIT_REPORT" << EOF

### Recommendations

#### Immediate Actions (Priority 1)
1. Review all failed CRITICAL and HIGH severity checks
2. Implement missing security headers
3. Remove any hardcoded credentials or secrets
4. Enable input validation where missing

#### Short-term Improvements (Priority 2)
1. Implement comprehensive audit logging
2. Add security documentation
3. Set up automated security scanning
4. Review and harden CI/CD pipelines

#### Long-term Enhancements (Priority 3)
1. Regular security assessments
2. Security training for development team
3. Implement security testing in CI/CD
4. Establish security incident response procedures

---
*Generated by security_audit_complete.sh on $(date)*
EOF

echo ""
echo "📊 Security Audit Results"
echo "========================"
echo "Security Score: $SECURITY_SCORE%"
echo "Total Checks: $TOTAL_CHECKS"
echo "Passed: $PASSED_CHECKS" 
echo "Failed: $FAILED_CHECKS"
echo "Critical/High Warnings: $WARNINGS"

if [ $WARNINGS -eq 0 ]; then
    echo "🎉 Excellent! No critical security issues found."
elif [ $WARNINGS -le 2 ]; then
    echo "⚠️  Good security posture with minor issues to address."
else
    echo "🚨 Security concerns detected. Review critical issues immediately."
fi

echo ""
echo "📋 Full audit report: $AUDIT_REPORT"
echo ""
echo "🔍 Next Steps:"
echo "1. Review the full audit report"
echo "2. Address any CRITICAL or HIGH severity issues"
echo "3. Implement recommended security enhancements"
echo "4. Re-run this audit after fixes"

# Clean up temp files older than 1 hour
find /tmp -name "security_check_*.log" -mmin +60 -delete 2>/dev/null || true

exit $WARNINGS