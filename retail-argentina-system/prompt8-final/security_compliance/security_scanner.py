#!/usr/bin/env python3
"""
Security Scanning and Compliance Validation Tool
for Argentine Retail System

Features:
- Dependency vulnerability scanning
- Code security analysis
- AFIP compliance validation
- Infrastructure security checks
- Security metrics and reporting
"""

import os
import sys
import json
import subprocess
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"

@dataclass
class SecurityFinding:
    """Represents a security finding"""
    id: str
    title: str
    description: str
    severity: SecurityLevel
    category: str
    affected_component: str
    remediation: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    discovered_at: datetime = None

    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now()

@dataclass
class ComplianceCheck:
    """Represents a compliance check result"""
    check_id: str
    regulation: str
    description: str
    status: ComplianceStatus
    evidence: List[str]
    remediation_steps: List[str]
    last_checked: datetime = None

    def __post_init__(self):
        if self.last_checked is None:
            self.last_checked = datetime.now()

class RetailSecurityScanner:
    """Main security scanning and compliance validation class"""

    def __init__(self, config_path: str = "/etc/retail-security/config.yaml"):
        self.config = self._load_config(config_path)
        self.findings: List[SecurityFinding] = []
        self.compliance_results: List[ComplianceCheck] = []

    def _load_config(self, config_path: str) -> Dict:
        """Load security scanner configuration"""
        default_config = {
            "scan_paths": [
                "/app",
                "/etc",
                "/var/log"
            ],
            "exclude_paths": [
                "/app/node_modules",
                "/app/.git",
                "/tmp"
            ],
            "vulnerability_databases": {
                "nvd": {
                    "api_key": os.getenv("NVD_API_KEY", ""),
                    "base_url": "https://services.nvd.nist.gov/rest/json/cves/2.0"
                }
            },
            "compliance_frameworks": [
                "afip_argentina",
                "pci_dss",
                "gdpr",
                "iso27001"
            ],
            "security_tools": {
                "bandit": {"enabled": True, "config": "/etc/bandit/bandit.yaml"},
                "safety": {"enabled": True},
                "semgrep": {"enabled": True, "rules": "auto"},
                "trivy": {"enabled": True}
            },
            "notification": {
                "email": os.getenv("SECURITY_NOTIFICATION_EMAIL", ""),
                "slack_webhook": os.getenv("SECURITY_SLACK_WEBHOOK", ""),
                "critical_threshold": 5
            }
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")

        return default_config

    def run_bandit_scan(self) -> List[SecurityFinding]:
        """Run Bandit security analysis on Python code"""
        findings = []

        if not self.config['security_tools']['bandit']['enabled']:
            return findings

        try:
            # Run bandit command
            cmd = [
                'bandit', 
                '-r', '/app',
                '-f', 'json',
                '--skip', 'B101,B601'  # Skip assert and shell injection for specific cases
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0 and result.stdout:
                bandit_data = json.loads(result.stdout)

                for issue in bandit_data.get('results', []):
                    severity_map = {
                        'LOW': SecurityLevel.LOW,
                        'MEDIUM': SecurityLevel.MEDIUM,
                        'HIGH': SecurityLevel.HIGH
                    }

                    finding = SecurityFinding(
                        id=f"bandit_{issue['test_id']}_{hashlib.md5(issue['filename'].encode()).hexdigest()[:8]}",
                        title=f"Bandit: {issue['test_name']}",
                        description=issue['issue_text'],
                        severity=severity_map.get(issue['issue_severity'], SecurityLevel.MEDIUM),
                        category="code_security",
                        affected_component=issue['filename'],
                        remediation=f"Review code at line {issue['line_number']}. {issue.get('more_info', '')}"
                    )
                    findings.append(finding)

            logger.info(f"Bandit scan completed: {len(findings)} findings")

        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")

        return findings

    def run_safety_scan(self) -> List[SecurityFinding]:
        """Run Safety check for known vulnerabilities in Python dependencies"""
        findings = []

        if not self.config['security_tools']['safety']['enabled']:
            return findings

        try:
            # Run safety check
            cmd = ['safety', 'check', '--json']
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout:
                safety_data = json.loads(result.stdout)

                for vuln in safety_data:
                    finding = SecurityFinding(
                        id=f"safety_{vuln['id']}",
                        title=f"Vulnerable Dependency: {vuln['package_name']}",
                        description=vuln['advisory'],
                        severity=SecurityLevel.HIGH,  # Dependencies are typically high risk
                        category="dependency_vulnerability",
                        affected_component=f"{vuln['package_name']} {vuln['installed_version']}",
                        remediation=f"Update to version {vuln.get('fixed_versions', 'latest')}",
                        cve_id=vuln.get('cve')
                    )
                    findings.append(finding)

            logger.info(f"Safety scan completed: {len(findings)} findings")

        except Exception as e:
            logger.error(f"Safety scan failed: {e}")

        return findings

    def run_infrastructure_scan(self) -> List[SecurityFinding]:
        """Scan infrastructure configuration for security issues"""
        findings = []

        try:
            # Check file permissions
            sensitive_files = [
                '/etc/passwd',
                '/etc/shadow',
                '/app/.env',
                '/app/config/*'
            ]

            for file_pattern in sensitive_files:
                if '*' in file_pattern:
                    import glob
                    files = glob.glob(file_pattern)
                else:
                    files = [file_pattern] if os.path.exists(file_pattern) else []

                for file_path in files:
                    if os.path.exists(file_path):
                        stat_info = os.stat(file_path)
                        mode = oct(stat_info.st_mode)[-3:]

                        # Check for overly permissive files
                        if mode == '777' or mode == '666':
                            finding = SecurityFinding(
                                id=f"infra_perm_{hashlib.md5(file_path.encode()).hexdigest()[:8]}",
                                title="Overly Permissive File Permissions",
                                description=f"File {file_path} has permissions {mode}",
                                severity=SecurityLevel.MEDIUM,
                                category="infrastructure",
                                affected_component=file_path,
                                remediation=f"Change permissions to 644 or more restrictive: chmod 644 {file_path}"
                            )
                            findings.append(finding)

            # Check for default passwords/keys
            config_files = ['/app/.env', '/app/config.yaml', '/app/docker-compose.yml']
            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        content = f.read().lower()

                    # Check for common default values
                    default_patterns = [
                        'password=password',
                        'password=123456',
                        'secret_key=changeme',
                        'api_key=your_api_key'
                    ]

                    for pattern in default_patterns:
                        if pattern in content:
                            finding = SecurityFinding(
                                id=f"infra_default_{hashlib.md5(config_file.encode()).hexdigest()[:8]}",
                                title="Default Credentials Detected",
                                description=f"Default or weak credentials found in {config_file}",
                                severity=SecurityLevel.HIGH,
                                category="infrastructure",
                                affected_component=config_file,
                                remediation="Change default passwords and secrets to strong, unique values"
                            )
                            findings.append(finding)
                            break

            logger.info(f"Infrastructure scan completed: {len(findings)} findings")

        except Exception as e:
            logger.error(f"Infrastructure scan failed: {e}")

        return findings

    def validate_afip_compliance(self) -> List[ComplianceCheck]:
        """Validate AFIP compliance requirements"""
        checks = []

        try:
            # Check 1: AFIP Certificate Configuration
            cert_files = ['/app/certs/afip.crt', '/app/certs/afip.key']
            cert_exists = all(os.path.exists(f) for f in cert_files)

            checks.append(ComplianceCheck(
                check_id="afip_001",
                regulation="AFIP Argentina",
                description="AFIP certificates must be properly configured",
                status=ComplianceStatus.COMPLIANT if cert_exists else ComplianceStatus.NON_COMPLIANT,
                evidence=[f"Certificate files: {cert_files}"],
                remediation_steps=[
                    "Obtain valid AFIP certificates",
                    "Install certificates in /app/certs/",
                    "Configure proper file permissions (600)"
                ] if not cert_exists else []
            ))

            # Check 2: CUIT Validation Implementation
            cuit_validation_files = [
                '/app/services/afip_service.py',
                '/app/utils/cuit_validator.py'
            ]

            cuit_implementation = any(os.path.exists(f) for f in cuit_validation_files)

            checks.append(ComplianceCheck(
                check_id="afip_002",
                regulation="AFIP Argentina",
                description="CUIT validation must be implemented",
                status=ComplianceStatus.COMPLIANT if cuit_implementation else ComplianceStatus.NON_COMPLIANT,
                evidence=[f"CUIT validation files: {cuit_validation_files}"],
                remediation_steps=[
                    "Implement CUIT validation algorithm",
                    "Add CUIT format verification",
                    "Include CUIT check digit validation"
                ] if not cuit_implementation else []
            ))

            # Check 3: Invoice Electronic Signature
            electronic_signature = os.path.exists('/app/services/electronic_signature.py')

            checks.append(ComplianceCheck(
                check_id="afip_003",
                regulation="AFIP Argentina",
                description="Electronic invoice signature required",
                status=ComplianceStatus.COMPLIANT if electronic_signature else ComplianceStatus.PARTIAL,
                evidence=["Electronic signature implementation"],
                remediation_steps=[
                    "Implement electronic signature for invoices",
                    "Integrate with AFIP WebServices",
                    "Add digital certificate validation"
                ] if not electronic_signature else []
            ))

            logger.info(f"AFIP compliance validation completed: {len(checks)} checks")

        except Exception as e:
            logger.error(f"AFIP compliance validation failed: {e}")

        return checks

    def validate_data_protection_compliance(self) -> List[ComplianceCheck]:
        """Validate data protection and privacy compliance"""
        checks = []

        try:
            # Check 1: Data Encryption at Rest
            encryption_check = any([
                os.path.exists('/app/utils/encryption.py'),
                'encrypt' in str(os.environ.get('DATABASE_URL', '')).lower()
            ])

            checks.append(ComplianceCheck(
                check_id="gdpr_001",
                regulation="GDPR/Data Protection",
                description="Personal data must be encrypted at rest",
                status=ComplianceStatus.COMPLIANT if encryption_check else ComplianceStatus.NON_COMPLIANT,
                evidence=["Encryption implementation check"],
                remediation_steps=[
                    "Implement data encryption for sensitive fields",
                    "Use encrypted database connections",
                    "Enable database encryption at rest"
                ] if not encryption_check else []
            ))

            # Check 2: Data Retention Policy
            retention_policy = os.path.exists('/app/policies/data_retention.py')

            checks.append(ComplianceCheck(
                check_id="gdpr_002", 
                regulation="GDPR/Data Protection",
                description="Data retention policy must be implemented",
                status=ComplianceStatus.COMPLIANT if retention_policy else ComplianceStatus.NON_COMPLIANT,
                evidence=["Data retention policy implementation"],
                remediation_steps=[
                    "Define data retention periods",
                    "Implement automated data purging",
                    "Create data subject access procedures"
                ] if not retention_policy else []
            ))

            logger.info(f"Data protection compliance validation completed: {len(checks)} checks")

        except Exception as e:
            logger.error(f"Data protection compliance validation failed: {e}")

        return checks

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        # Run all scans
        self.findings.extend(self.run_bandit_scan())
        self.findings.extend(self.run_safety_scan())
        self.findings.extend(self.run_infrastructure_scan())

        # Run compliance checks
        self.compliance_results.extend(self.validate_afip_compliance())
        self.compliance_results.extend(self.validate_data_protection_compliance())

        # Generate report
        severity_counts = {}
        for severity in SecurityLevel:
            severity_counts[severity.value] = len([f for f in self.findings if f.severity == severity])

        compliance_status = {}
        for status in ComplianceStatus:
            compliance_status[status.value] = len([c for c in self.compliance_results if c.status == status])

        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_findings": len(self.findings),
                "severity_distribution": severity_counts,
                "compliance_checks": len(self.compliance_results),
                "compliance_status": compliance_status,
                "risk_score": self._calculate_risk_score()
            },
            "findings": [
                {
                    "id": f.id,
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity.value,
                    "category": f.category,
                    "component": f.affected_component,
                    "remediation": f.remediation,
                    "cve_id": f.cve_id,
                    "discovered_at": f.discovered_at.isoformat()
                }
                for f in self.findings
            ],
            "compliance": [
                {
                    "check_id": c.check_id,
                    "regulation": c.regulation,
                    "description": c.description,
                    "status": c.status.value,
                    "evidence": c.evidence,
                    "remediation": c.remediation_steps,
                    "last_checked": c.last_checked.isoformat()
                }
                for c in self.compliance_results
            ]
        }

        return report

    def _calculate_risk_score(self) -> float:
        """Calculate overall risk score based on findings"""
        if not self.findings:
            return 0.0

        severity_weights = {
            SecurityLevel.LOW: 1,
            SecurityLevel.MEDIUM: 3,
            SecurityLevel.HIGH: 7,
            SecurityLevel.CRITICAL: 10
        }

        total_score = sum(severity_weights[f.severity] for f in self.findings)
        max_possible = len(self.findings) * severity_weights[SecurityLevel.CRITICAL]

        return (total_score / max_possible) * 100 if max_possible > 0 else 0.0

    def export_report(self, format: str = "json") -> str:
        """Export security report in specified format"""
        report = self.generate_security_report()

        if format == "json":
            return json.dumps(report, indent=2, ensure_ascii=False)

        elif format == "html":
            # Generate HTML report
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Security Report - Retail Argentina</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .critical { color: #dc3545; }
                    .high { color: #fd7e14; }
                    .medium { color: #ffc107; }
                    .low { color: #28a745; }
                    .compliant { color: #28a745; }
                    .non-compliant { color: #dc3545; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <h1>Security Scan Report</h1>
                <p><strong>Generated:</strong> {timestamp}</p>
                <p><strong>Risk Score:</strong> {risk_score:.1f}/100</p>

                <h2>Summary</h2>
                <p>Total Findings: {total_findings}</p>
                <p>Compliance Checks: {compliance_checks}</p>

                <h2>Security Findings</h2>
                <table>
                    <tr><th>Severity</th><th>Title</th><th>Component</th><th>Description</th></tr>
                    {findings_rows}
                </table>

                <h2>Compliance Results</h2>
                <table>
                    <tr><th>Status</th><th>Regulation</th><th>Check</th><th>Description</th></tr>
                    {compliance_rows}
                </table>
            </body>
            </html>
            """

            findings_rows = ""
            for f in report['findings']:
                findings_rows += f"<tr><td class='{f['severity']}'>{f['severity'].upper()}</td><td>{f['title']}</td><td>{f['component']}</td><td>{f['description']}</td></tr>"

            compliance_rows = ""
            for c in report['compliance']:
                status_class = 'compliant' if c['status'] == 'compliant' else 'non-compliant'
                compliance_rows += f"<tr><td class='{status_class}'>{c['status'].upper()}</td><td>{c['regulation']}</td><td>{c['check_id']}</td><td>{c['description']}</td></tr>"

            return html_template.format(
                timestamp=report['scan_timestamp'],
                risk_score=report['summary']['risk_score'],
                total_findings=report['summary']['total_findings'],
                compliance_checks=report['summary']['compliance_checks'],
                findings_rows=findings_rows,
                compliance_rows=compliance_rows
            )

        else:
            raise ValueError(f"Unsupported format: {format}")

def main():
    """Main entry point"""
    scanner = RetailSecurityScanner()

    if len(sys.argv) > 1:
        format_type = sys.argv[1] if sys.argv[1] in ['json', 'html'] else 'json'
    else:
        format_type = 'json'

    try:
        report = scanner.export_report(format_type)

        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"security_report_{timestamp}.{format_type}"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"Security scan completed. Report saved to: {filename}")

        # Print summary to console
        summary = scanner.generate_security_report()['summary']
        print(f"\nSummary:")
        print(f"- Total findings: {summary['total_findings']}")
        print(f"- Risk score: {summary['risk_score']:.1f}/100")
        print(f"- Critical issues: {summary['severity_distribution'].get('critical', 0)}")
        print(f"- Compliance checks: {summary['compliance_checks']}")

    except Exception as e:
        logger.error(f"Security scan failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
