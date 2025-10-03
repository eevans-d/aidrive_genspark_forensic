#!/usr/bin/env python3
"""
ETAPA 2 Security Mitigations Validation Script
===============================================

Validates R1, R2, R3, R4, R6 mitigations without requiring pytest.

Usage:
    python3 validate_etapa2_mitigations.py
    
Exit codes:
    0: All validations passed
    1: One or more validations failed
"""

import sys
from pathlib import Path
import yaml


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class ValidationResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def pass_test(self, test_name):
        self.passed += 1
        print(f"{Colors.GREEN}✓{Colors.RESET} {test_name}")
    
    def fail_test(self, test_name, reason=""):
        self.failed += 1
        print(f"{Colors.RED}✗{Colors.RESET} {test_name}")
        if reason:
            print(f"  {Colors.RED}Reason: {reason}{Colors.RESET}")
    
    def warn(self, message):
        self.warnings += 1
        print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
    
    def section(self, title):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
        print("=" * len(title))
    
    def summary(self):
        print(f"\n{Colors.BOLD}Summary:{Colors.RESET}")
        print(f"  Passed: {Colors.GREEN}{self.passed}{Colors.RESET}")
        print(f"  Failed: {Colors.RED}{self.failed}{Colors.RESET}")
        print(f"  Warnings: {Colors.YELLOW}{self.warnings}{Colors.RESET}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All validations passed!{Colors.RESET}")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ {self.failed} validation(s) failed{Colors.RESET}")
            return 1


def validate_r1_container_security(result: ValidationResult):
    """R1: Validate containers run as non-root users"""
    result.section("R1: Container Security")
    
    dockerfiles = {
        "inventario-retail/agente_deposito/Dockerfile": "agente",
        "inventario-retail/agente_negocio/Dockerfile": "negocio",
        "inventario-retail/ml/Dockerfile": "mluser",
        "inventario-retail/web_dashboard/Dockerfile": "dashboarduser",
    }
    
    for dockerfile_path, expected_user in dockerfiles.items():
        path = Path(dockerfile_path)
        
        if not path.exists():
            result.fail_test(f"Dockerfile exists: {dockerfile_path}", "File not found")
            continue
        
        content = path.read_text()
        
        if f"USER {expected_user}" in content:
            result.pass_test(f"{dockerfile_path} has USER {expected_user}")
        else:
            result.fail_test(f"{dockerfile_path} has USER {expected_user}", 
                           f"Expected 'USER {expected_user}' not found")


def validate_r6_dependency_scanning(result: ValidationResult):
    """R6: Validate Trivy dependency scanning is enforced"""
    result.section("R6: Dependency Scanning")
    
    ci_file = Path(".github/workflows/ci.yml")
    
    if not ci_file.exists():
        result.fail_test("CI workflow exists", "File not found")
        return
    
    content = ci_file.read_text()
    
    # Check job exists
    if "trivy-scan-dependencies" in content:
        result.pass_test("trivy-scan-dependencies job exists")
    else:
        result.fail_test("trivy-scan-dependencies job exists", "Job not found in CI")
        return
    
    # Check exit-code enforcement
    if "exit-code: '1'" in content or 'exit-code: "1"' in content:
        result.pass_test("Trivy enforced with exit-code: 1")
    else:
        result.fail_test("Trivy enforced with exit-code: 1", 
                       "exit-code not set to '1'")
    
    # Check severity configuration
    if "CRITICAL" in content and "HIGH" in content:
        result.pass_test("Trivy scans for CRITICAL,HIGH severity")
    else:
        result.fail_test("Trivy scans for CRITICAL,HIGH severity",
                       "Severity configuration incomplete")


def validate_r3_ocr_timeout(result: ValidationResult):
    """R3: Validate OCR timeout configuration"""
    result.section("R3: OCR Timeout Protection")
    
    # Check docker-compose
    compose_file = Path("inventario-retail/docker-compose.production.yml")
    if compose_file.exists():
        content = compose_file.read_text()
        if "OCR_TIMEOUT_SECONDS" in content:
            result.pass_test("OCR_TIMEOUT_SECONDS in docker-compose")
        else:
            result.fail_test("OCR_TIMEOUT_SECONDS in docker-compose", 
                           "Variable not found")
    else:
        result.fail_test("docker-compose.production.yml exists", "File not found")
    
    # Check .env template
    env_template = Path("inventario-retail/.env.production.template")
    if env_template.exists():
        content = env_template.read_text()
        if "OCR_TIMEOUT_SECONDS" in content:
            result.pass_test("OCR_TIMEOUT_SECONDS in .env template")
        else:
            result.fail_test("OCR_TIMEOUT_SECONDS in .env template",
                           "Variable not documented")
    else:
        result.fail_test(".env.production.template exists", "File not found")
    
    # Check main_complete.py
    main_file = Path("inventario-retail/agente_negocio/main_complete.py")
    if main_file.exists():
        content = main_file.read_text()
        if "OCR_TIMEOUT_SECONDS" in content and "asyncio.wait_for" in content:
            result.pass_test("OCR timeout implementation in main_complete.py")
        else:
            result.fail_test("OCR timeout implementation in main_complete.py",
                           "Missing OCR_TIMEOUT_SECONDS or asyncio.wait_for")
    else:
        result.fail_test("main_complete.py exists", "File not found")


def validate_r2_jwt_isolation(result: ValidationResult):
    """R2: Validate JWT secret isolation per agent"""
    result.section("R2: JWT Secret Isolation")
    
    # Check docker-compose
    compose_file = Path("inventario-retail/docker-compose.production.yml")
    if compose_file.exists():
        content = compose_file.read_text()
        
        required_secrets = [
            "JWT_SECRET_DEPOSITO",
            "JWT_SECRET_NEGOCIO",
            "JWT_SECRET_ML",
            "JWT_SECRET_DASHBOARD",
        ]
        
        for secret in required_secrets:
            if secret in content:
                result.pass_test(f"{secret} in docker-compose")
            else:
                result.fail_test(f"{secret} in docker-compose", "Variable not found")
    else:
        result.fail_test("docker-compose.production.yml exists", "File not found")
    
    # Check .env template
    env_template = Path("inventario-retail/.env.production.template")
    if env_template.exists():
        content = env_template.read_text()
        
        if all(secret in content for secret in required_secrets):
            result.pass_test("All JWT secrets documented in .env template")
        else:
            result.fail_test("All JWT secrets documented in .env template",
                           "One or more secrets missing")
    else:
        result.fail_test(".env.production.template exists", "File not found")
    
    # Check shared/auth.py
    auth_file = Path("shared/auth.py")
    if auth_file.exists():
        content = auth_file.read_text()
        
        if "issuer" in content.lower() and ('"iss"' in content or "'iss'" in content):
            result.pass_test("AuthManager supports issuer claim")
        else:
            result.fail_test("AuthManager supports issuer claim",
                           "Issuer support not found")
        
        managers = [
            "auth_manager_deposito",
            "auth_manager_negocio",
            "auth_manager_ml",
            "auth_manager_dashboard",
        ]
        
        if all(mgr in content for mgr in managers):
            result.pass_test("Per-agent AuthManager instances exist")
        else:
            result.fail_test("Per-agent AuthManager instances exist",
                           "One or more instances missing")
    else:
        result.fail_test("shared/auth.py exists", "File not found")


def validate_r4_ml_inflation(result: ValidationResult):
    """R4: Validate ML inflation rate externalization"""
    result.section("R4: ML Inflation Externalization")
    
    # Check docker-compose
    compose_file = Path("inventario-retail/docker-compose.production.yml")
    if compose_file.exists():
        content = compose_file.read_text()
        if "INFLATION_RATE_MONTHLY" in content:
            result.pass_test("INFLATION_RATE_MONTHLY in docker-compose")
        else:
            result.fail_test("INFLATION_RATE_MONTHLY in docker-compose",
                           "Variable not found")
    else:
        result.fail_test("docker-compose.production.yml exists", "File not found")
    
    # Check .env template
    env_template = Path("inventario-retail/.env.production.template")
    if env_template.exists():
        content = env_template.read_text()
        if "INFLATION_RATE_MONTHLY" in content:
            result.pass_test("INFLATION_RATE_MONTHLY in .env template")
        else:
            result.fail_test("INFLATION_RATE_MONTHLY in .env template",
                           "Variable not documented")
    else:
        result.fail_test(".env.production.template exists", "File not found")
    
    # Check ml/predictor.py
    predictor_file = Path("inventario-retail/ml/predictor.py")
    if predictor_file.exists():
        content = predictor_file.read_text()
        if "INFLATION_RATE_MONTHLY" in content and "os.getenv" in content:
            result.pass_test("ML predictor reads INFLATION_RATE_MONTHLY")
        else:
            result.fail_test("ML predictor reads INFLATION_RATE_MONTHLY",
                           "Missing INFLATION_RATE_MONTHLY or os.getenv")
    else:
        result.fail_test("ml/predictor.py exists", "File not found")
    
    # Check ml/features.py
    features_file = Path("inventario-retail/ml/features.py")
    if features_file.exists():
        content = features_file.read_text()
        if "Optional" in content and "inflacion_mensual" in content.lower():
            result.pass_test("DemandFeatures accepts optional inflation parameter")
        else:
            result.fail_test("DemandFeatures accepts optional inflation parameter",
                           "Missing Optional or inflacion_mensual")
    else:
        result.fail_test("ml/features.py exists", "File not found")


def validate_documentation(result: ValidationResult):
    """Validate documentation is updated"""
    result.section("Documentation")
    
    # Check migration guides
    guides = {
        "inventario-retail/R2_JWT_SECRET_MIGRATION_GUIDE.md": "R2 JWT Migration Guide",
        "inventario-retail/R4_ML_INFLATION_MIGRATION_GUIDE.md": "R4 ML Inflation Migration Guide",
    }
    
    for path, name in guides.items():
        guide = Path(path)
        if guide.exists() and len(guide.read_text()) > 1000:
            result.pass_test(f"{name} exists and is complete")
        else:
            result.fail_test(f"{name} exists and is complete",
                           "File missing or too short")
    
    # Check CHANGELOG
    changelog = Path("CHANGELOG.md")
    if changelog.exists():
        content = changelog.read_text()
        if "v0.10.0" in content or "[v0.10.0]" in content:
            result.pass_test("CHANGELOG has v0.10.0 release notes")
            
            # Check all mitigations documented
            mitigations = ["R1", "R2", "R3", "R4", "R6"]
            if all(m in content for m in mitigations):
                result.pass_test("All mitigations documented in CHANGELOG")
            else:
                result.fail_test("All mitigations documented in CHANGELOG",
                               "One or more mitigations missing")
        else:
            result.fail_test("CHANGELOG has v0.10.0 release notes",
                           "v0.10.0 section not found")
    else:
        result.fail_test("CHANGELOG.md exists", "File not found")
    
    # Check ETAPA2 completion document
    doc = Path("ETAPA2_SECURITY_MITIGATIONS_COMPLETE.md")
    if doc.exists() and len(doc.read_text()) > 5000:
        result.pass_test("ETAPA2 completion document exists")
    else:
        result.fail_test("ETAPA2 completion document exists",
                       "File missing or too short")
    
    # Check README
    readme = Path("inventario-retail/README.md")
    if readme.exists():
        content = readme.read_text()
        new_vars = ["OCR_TIMEOUT_SECONDS", "INFLATION_RATE_MONTHLY", "JWT_SECRET_DEPOSITO"]
        if all(var in content for var in new_vars):
            result.pass_test("README documents new environment variables")
        else:
            result.fail_test("README documents new environment variables",
                           "One or more variables missing")
    else:
        result.fail_test("README.md exists", "File not found")


def main():
    """Main validation entry point"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("ETAPA 2 Security Mitigations Validation")
    print("=" * 70)
    print(f"{Colors.RESET}\n")
    
    result = ValidationResult()
    
    # Run all validations
    validate_r1_container_security(result)
    validate_r6_dependency_scanning(result)
    validate_r3_ocr_timeout(result)
    validate_r2_jwt_isolation(result)
    validate_r4_ml_inflation(result)
    validate_documentation(result)
    
    # Print summary and exit
    exit_code = result.summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
