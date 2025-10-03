"""
Integration Tests for ETAPA 2 Security Mitigations
===================================================

Tests para validar R1, R2, R3, R4, R6 mitigations.

Ejecutar con:
    pytest tests/integration/test_etapa2_mitigations.py -v
    
Requiere:
    - Docker containers en ejecución (para R1)
    - Environment variables configuradas (para R2, R3, R4)
"""

import os
import pytest
import yaml
import subprocess
from pathlib import Path


class TestR1ContainerSecurity:
    """R1: Validate containers run as non-root users"""
    
    def test_dockerfiles_have_user_directive(self):
        """Verify all agent Dockerfiles include USER directive"""
        dockerfiles = [
            "inventario-retail/agente_deposito/Dockerfile",
            "inventario-retail/agente_negocio/Dockerfile",
            "inventario-retail/ml/Dockerfile",
            "inventario-retail/web_dashboard/Dockerfile",
        ]
        
        for dockerfile_path in dockerfiles:
            full_path = Path(dockerfile_path)
            assert full_path.exists(), f"Dockerfile not found: {dockerfile_path}"
            
            content = full_path.read_text()
            assert "USER " in content, f"USER directive missing in {dockerfile_path}"
            
            # Extract USER name
            user_lines = [line for line in content.split('\n') if line.strip().startswith('USER ')]
            assert len(user_lines) > 0, f"No USER directive found in {dockerfile_path}"
            
            # Verify it's not root
            for user_line in user_lines:
                user_name = user_line.split()[1]
                assert user_name != "root", f"{dockerfile_path} uses root user"
    
    def test_expected_non_root_users(self):
        """Verify expected non-root user names in Dockerfiles"""
        expected_users = {
            "inventario-retail/agente_deposito/Dockerfile": "agente",
            "inventario-retail/agente_negocio/Dockerfile": "negocio",
            "inventario-retail/ml/Dockerfile": "mluser",
            "inventario-retail/web_dashboard/Dockerfile": "dashboarduser",
        }
        
        for dockerfile_path, expected_user in expected_users.items():
            content = Path(dockerfile_path).read_text()
            assert f"USER {expected_user}" in content, \
                f"Expected USER {expected_user} in {dockerfile_path}"


class TestR6DependencyScanning:
    """R6: Validate Trivy dependency scanning is enforced in CI/CD"""
    
    def test_trivy_job_exists_in_ci(self):
        """Verify trivy-scan-dependencies job exists in CI workflow"""
        ci_file = Path(".github/workflows/ci.yml")
        assert ci_file.exists(), "CI workflow file not found"
        
        content = ci_file.read_text()
        assert "trivy-scan-dependencies" in content, \
            "trivy-scan-dependencies job not found in CI workflow"
    
    def test_trivy_job_configuration(self):
        """Verify Trivy job has correct enforcement configuration"""
        ci_file = Path(".github/workflows/ci.yml")
        ci_config = yaml.safe_load(ci_file.read_text())
        
        # Find trivy job
        jobs = ci_config.get('jobs', {})
        trivy_job = jobs.get('trivy-scan-dependencies')
        
        assert trivy_job is not None, "trivy-scan-dependencies job not found"
        
        # Find Trivy action step
        steps = trivy_job.get('steps', [])
        trivy_steps = [s for s in steps if 'aquasecurity/trivy-action' in str(s.get('uses', ''))]
        
        assert len(trivy_steps) > 0, "Trivy action not found in job"
        
        # Verify exit-code is 1 (enforced)
        trivy_step = trivy_steps[0]
        with_config = trivy_step.get('with', {})
        
        assert with_config.get('exit-code') == '1', \
            "Trivy exit-code should be '1' for enforcement"
        
        # Verify severity includes CRITICAL and HIGH
        severity = with_config.get('severity', '')
        assert 'CRITICAL' in severity, "Trivy should scan for CRITICAL vulnerabilities"
        assert 'HIGH' in severity, "Trivy should scan for HIGH vulnerabilities"


class TestR3OCRTimeout:
    """R3: Validate OCR timeout configuration"""
    
    def test_ocr_timeout_env_var_in_compose(self):
        """Verify OCR_TIMEOUT_SECONDS is in docker-compose"""
        compose_file = Path("inventario-retail/docker-compose.production.yml")
        assert compose_file.exists(), "docker-compose.production.yml not found"
        
        content = compose_file.read_text()
        assert "OCR_TIMEOUT_SECONDS" in content, \
            "OCR_TIMEOUT_SECONDS not found in docker-compose"
    
    def test_ocr_timeout_in_env_template(self):
        """Verify OCR_TIMEOUT_SECONDS is documented in .env template"""
        env_template = Path("inventario-retail/.env.production.template")
        assert env_template.exists(), ".env.production.template not found"
        
        content = env_template.read_text()
        assert "OCR_TIMEOUT_SECONDS" in content, \
            "OCR_TIMEOUT_SECONDS not documented in .env template"
    
    def test_ocr_timeout_default_value(self):
        """Verify OCR_TIMEOUT_SECONDS has reasonable default"""
        compose_file = Path("inventario-retail/docker-compose.production.yml")
        content = compose_file.read_text()
        
        # Check for default value pattern
        assert "OCR_TIMEOUT_SECONDS:-30" in content or "OCR_TIMEOUT_SECONDS=30" in content, \
            "OCR_TIMEOUT_SECONDS should have default value of 30"
    
    def test_ocr_processor_uses_timeout(self):
        """Verify OCR processor code reads OCR_TIMEOUT_SECONDS"""
        main_file = Path("inventario-retail/agente_negocio/main_complete.py")
        assert main_file.exists(), "main_complete.py not found"
        
        content = main_file.read_text()
        assert "OCR_TIMEOUT_SECONDS" in content, \
            "OCR_TIMEOUT_SECONDS not used in main_complete.py"
        assert "asyncio.wait_for" in content, \
            "asyncio.wait_for not found (timeout implementation missing)"


class TestR2JWTIsolation:
    """R2: Validate JWT secret isolation per agent"""
    
    def test_jwt_secret_env_vars_in_compose(self):
        """Verify per-agent JWT secrets in docker-compose"""
        compose_file = Path("inventario-retail/docker-compose.production.yml")
        content = compose_file.read_text()
        
        required_secrets = [
            "JWT_SECRET_DEPOSITO",
            "JWT_SECRET_NEGOCIO",
            "JWT_SECRET_ML",
            "JWT_SECRET_DASHBOARD",
        ]
        
        for secret in required_secrets:
            assert secret in content, \
                f"{secret} not found in docker-compose.production.yml"
    
    def test_jwt_secrets_in_env_template(self):
        """Verify JWT secrets documented in .env template"""
        env_template = Path("inventario-retail/.env.production.template")
        content = env_template.read_text()
        
        required_secrets = [
            "JWT_SECRET_DEPOSITO",
            "JWT_SECRET_NEGOCIO",
            "JWT_SECRET_ML",
            "JWT_SECRET_DASHBOARD",
        ]
        
        for secret in required_secrets:
            assert secret in content, \
                f"{secret} not documented in .env template"
    
    def test_auth_manager_supports_issuer(self):
        """Verify AuthManager supports issuer claim"""
        auth_file = Path("shared/auth.py")
        assert auth_file.exists(), "shared/auth.py not found"
        
        content = auth_file.read_text()
        assert "issuer" in content.lower(), \
            "AuthManager should support issuer parameter"
        assert '"iss"' in content or "'iss'" in content, \
            "JWT token should include 'iss' claim"
    
    def test_per_agent_auth_managers_exist(self):
        """Verify per-agent AuthManager instances exist"""
        auth_file = Path("shared/auth.py")
        content = auth_file.read_text()
        
        managers = [
            "auth_manager_deposito",
            "auth_manager_negocio",
            "auth_manager_ml",
            "auth_manager_dashboard",
        ]
        
        for manager in managers:
            assert manager in content, \
                f"{manager} instance not found in shared/auth.py"
    
    def test_jwt_fallback_pattern(self):
        """Verify JWT secrets use fallback pattern for backward compatibility"""
        compose_file = Path("inventario-retail/docker-compose.production.yml")
        content = compose_file.read_text()
        
        # Check fallback pattern: ${JWT_SECRET_AGENT:-${JWT_SECRET_KEY}}
        fallback_patterns = [
            "JWT_SECRET_DEPOSITO:-",
            "JWT_SECRET_NEGOCIO:-",
            "JWT_SECRET_ML:-",
        ]
        
        for pattern in fallback_patterns:
            assert pattern in content, \
                f"Fallback pattern '{pattern}' not found (backward compatibility missing)"


class TestR4MLInflation:
    """R4: Validate ML inflation rate externalization"""
    
    def test_inflation_env_var_in_compose(self):
        """Verify INFLATION_RATE_MONTHLY in ml-service config"""
        compose_file = Path("inventario-retail/docker-compose.production.yml")
        content = compose_file.read_text()
        
        assert "INFLATION_RATE_MONTHLY" in content, \
            "INFLATION_RATE_MONTHLY not found in docker-compose"
    
    def test_inflation_in_env_template(self):
        """Verify INFLATION_RATE_MONTHLY documented in .env template"""
        env_template = Path("inventario-retail/.env.production.template")
        content = env_template.read_text()
        
        assert "INFLATION_RATE_MONTHLY" in content, \
            "INFLATION_RATE_MONTHLY not documented in .env template"
    
    def test_ml_predictor_reads_inflation(self):
        """Verify ML predictor reads inflation from env var"""
        predictor_file = Path("inventario-retail/ml/predictor.py")
        assert predictor_file.exists(), "ml/predictor.py not found"
        
        content = predictor_file.read_text()
        assert "INFLATION_RATE_MONTHLY" in content, \
            "ML predictor doesn't read INFLATION_RATE_MONTHLY"
        assert "os.getenv" in content, \
            "ML predictor should use os.getenv to read env var"
    
    def test_ml_features_accepts_optional_inflation(self):
        """Verify DemandFeatures accepts optional inflation parameter"""
        features_file = Path("inventario-retail/ml/features.py")
        assert features_file.exists(), "ml/features.py not found"
        
        content = features_file.read_text()
        assert "inflacion_mensual" in content.lower(), \
            "DemandFeatures should have inflacion_mensual parameter"
        assert "Optional" in content, \
            "inflacion_mensual should be Optional type"
    
    def test_inflation_default_value(self):
        """Verify inflation has backward-compatible default"""
        compose_file = Path("inventario-retail/docker-compose.production.yml")
        content = compose_file.read_text()
        
        # Check for default 0.045 (4.5%)
        assert "INFLATION_RATE_MONTHLY:-0.045" in content or \
               "INFLATION_RATE_MONTHLY=0.045" in content, \
            "INFLATION_RATE_MONTHLY should have default value 0.045"


class TestMigrationGuides:
    """Validate migration guides exist and are complete"""
    
    def test_r2_migration_guide_exists(self):
        """Verify R2 JWT migration guide exists"""
        guide = Path("inventario-retail/R2_JWT_SECRET_MIGRATION_GUIDE.md")
        assert guide.exists(), "R2_JWT_SECRET_MIGRATION_GUIDE.md not found"
        
        content = guide.read_text()
        assert len(content) > 1000, "R2 migration guide seems incomplete"
        assert "openssl rand -base64 32" in content, \
            "Secret generation instructions missing"
    
    def test_r4_migration_guide_exists(self):
        """Verify R4 ML inflation migration guide exists"""
        guide = Path("inventario-retail/R4_ML_INFLATION_MIGRATION_GUIDE.md")
        assert guide.exists(), "R4_ML_INFLATION_MIGRATION_GUIDE.md not found"
        
        content = guide.read_text()
        assert len(content) > 1000, "R4 migration guide seems incomplete"
        assert "INDEC" in content or "BCRA" in content, \
            "Argentina inflation source references missing"


class TestDocumentation:
    """Validate documentation is updated"""
    
    def test_changelog_has_v0_10_0(self):
        """Verify CHANGELOG includes v0.10.0 release"""
        changelog = Path("CHANGELOG.md")
        assert changelog.exists(), "CHANGELOG.md not found"
        
        content = changelog.read_text()
        assert "v0.10.0" in content or "[v0.10.0]" in content, \
            "CHANGELOG missing v0.10.0 release notes"
        
        # Verify all mitigations documented
        mitigations = ["R1", "R2", "R3", "R4", "R6"]
        for mitigation in mitigations:
            assert mitigation in content, \
                f"{mitigation} mitigation not documented in CHANGELOG"
    
    def test_etapa2_completion_document_exists(self):
        """Verify ETAPA 2 completion document exists"""
        doc = Path("ETAPA2_SECURITY_MITIGATIONS_COMPLETE.md")
        assert doc.exists(), "ETAPA2_SECURITY_MITIGATIONS_COMPLETE.md not found"
        
        content = doc.read_text()
        assert "COMPLETADO" in content or "COMPLETE" in content, \
            "ETAPA 2 completion status unclear"
        assert "23" in content, \
            "Total effort (23h) not documented"
    
    def test_readme_updated_with_new_vars(self):
        """Verify README documents new environment variables"""
        readme = Path("inventario-retail/README.md")
        assert readme.exists(), "README.md not found"
        
        content = readme.read_text()
        
        new_vars = [
            "OCR_TIMEOUT_SECONDS",
            "INFLATION_RATE_MONTHLY",
            "JWT_SECRET_DEPOSITO",
        ]
        
        for var in new_vars:
            assert var in content, \
                f"{var} not documented in README.md"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "etapa2: tests for ETAPA 2 security mitigations"
    )
    config.addinivalue_line(
        "markers", "r1: tests for R1 container security"
    )
    config.addinivalue_line(
        "markers", "r2: tests for R2 JWT isolation"
    )
    config.addinivalue_line(
        "markers", "r3: tests for R3 OCR timeout"
    )
    config.addinivalue_line(
        "markers", "r4: tests for R4 ML inflation"
    )
    config.addinivalue_line(
        "markers", "r6: tests for R6 dependency scanning"
    )
