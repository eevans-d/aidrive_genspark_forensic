# 🚀 Quick Reference Guide - Audit Framework

## Quick Start

### Run Complete Audit
```bash
cd /home/runner/work/aidrive_genspark_forensic/aidrive_genspark_forensic
python3 audit_framework/run_audit.py
```

### Run Individual Stages
```bash
# Stage 0: Ingestion & Validation
python3 audit_framework/run_audit.py --stage=0

# Stage 1: Structural Mapping
python3 audit_framework/run_audit.py --stage=1

# Stage 2: Risk Analysis
python3 audit_framework/run_audit.py --stage=2
```

## Generated Reports

All reports are in `audit_framework/reports/`:

| File | Size | Description |
|------|------|-------------|
| `FINAL_AUDIT_REPORT.json` | 11.5 KB | Executive summary with Top-7 risks |
| `stage0_profile.json` | 5.3 KB | Project profile (100% completeness) |
| `stage1_dependencies.json` | 3.4 KB | Dependency graph analysis |
| `stage1_fsm_analysis.json` | 3.6 KB | State machine analysis |
| `stage1_jwt_analysis.json` | 7.2 KB | JWT security analysis |
| `stage2_risks_detected.json` | 8.9 KB | Detailed risk detection |
| `stage2_risks_prioritized.json` | 22.2 KB | Risks with scoring & ROI |
| `control_envelope.json` | 1.3 KB | Execution metrics |

## Key Findings Summary

### Top-3 Critical Risks

1. **R1_CONTAINER_ROOT_EXECUTION** (Score: 11.90)
   - 6 containers running as root
   - 3h effort, ROI: 26.67

2. **R5_FORENSIC_CASCADE_FAILURE** (Score: 10.99)
   - No partial recovery in 5-phase audit
   - 5h effort, ROI: 9.60

3. **R2_JWT_SINGLE_SECRET** (Score: 10.75)
   - Single JWT shared across 4 agents
   - 8h effort, ROI: 6.75

### Metrics
- **Services Analyzed:** 7 (4 agents + 3 infrastructure)
- **Dependencies:** 12 (0 cycles)
- **FSMs Analyzed:** 5
- **Total Risks:** 7 (3 critical, 4 high)
- **Average Score:** 9.57/10
- **Total Mitigation Effort:** 31 hours

## Architecture Overview

```
nginx:80/443 → web_dashboard:8080
                ├→ agente_deposito:8001 → postgres:5432, redis:6379
                ├→ agente_negocio:8002 → postgres:5432, redis:6379
                └→ ml_service:8003 → postgres:5432, redis:6379
```

## Command Reference

### Test Individual Components
```bash
# Test control envelope
python3 audit_framework/lib/control_envelope.py

# Test scoring formulas
python3 audit_framework/lib/scoring.py

# Test profile extraction
python3 audit_framework/stage0_ingestion/project_profile.py

# Test validation
python3 audit_framework/stage0_ingestion/validation.py

# Test dependency graph
python3 audit_framework/stage1_mapping/dependency_graph.py

# Test FSM analysis
python3 audit_framework/stage1_mapping/fsm_analyzer.py

# Test JWT analysis
python3 audit_framework/stage1_mapping/jwt_analyzer.py

# Test risk detection
python3 audit_framework/stage2_risk_analysis/risk_detector.py

# Test risk scoring
python3 audit_framework/stage2_risk_analysis/risk_scoring.py
```

### View Reports
```bash
# View final report
cat audit_framework/reports/FINAL_AUDIT_REPORT.json | python3 -m json.tool

# View project profile
cat audit_framework/reports/stage0_profile.json | python3 -m json.tool

# View top risks
cat audit_framework/reports/stage2_risks_prioritized.json | python3 -m json.tool | grep -A 5 '"id":'
```

## FREEZE Compliance Verification

```bash
# Verify no changes to core logic
git status inventario-retail/
# Should show: "nothing to commit, working tree clean"

# Check audit framework only
git status audit_framework/
# Should show only audit framework files
```

## Expected Output

### Stage 0 Output
```
ETAPA 0: INGESTA Y VALIDACIÓN
[1/2] Extrayendo ProjectProfile...
✓ ProjectProfile extracted
  Completeness: 100.0%
  Services: 7
  Critical Flows: 4

[2/2] Validando consistencia...
✓ All validations passed
```

### Stage 1 Output
```
ETAPA 1: MAPEO ESTRUCTURAL MULTI-AGENTE
[1/3] Analizando grafo de dependencias...
✓ Dependency graph analyzed
  Services: 7
  Dependencies: 12
  Cycles: 0

[2/3] Analizando máquinas de estado...
✓ FSM analysis completed
  FSMs: 5
  Critical Findings: 3

[3/3] Analizando comunicación JWT...
✓ JWT communication analyzed
  JWT Flows: 3
  Attack Vectors: 4
```

### Stage 2 Output
```
ETAPA 2: ANÁLISIS DE RIESGO ESPECÍFICO
[1/2] Detectando riesgos multi-vector...
✓ Risks detected: 7
  - R1_CONTAINER_ROOT_EXECUTION (Severity: 10/10)
  - R2_JWT_SINGLE_SECRET (Severity: 9/10)
  ...

[2/2] Calculando scores y priorizando...
✓ Risks scored and prioritized
  Average Score: 9.57
  High ROI Count: 7
```

## Troubleshooting

### Missing Profile Error
```
Error: Profile file not found
Solution: Run stage 0 first
python3 audit_framework/run_audit.py --stage=0
```

### Import Errors
```
Error: ModuleNotFoundError
Solution: Ensure you're in repo root
cd /home/runner/work/aidrive_genspark_forensic/aidrive_genspark_forensic
```

### Validation Errors
```
Error: Profile validation failed
Check: audit_framework/reports/stage0_profile.json
Fix: Update validation.py if needed
```

## File Structure

```
audit_framework/
├── README.md                          # Full documentation
├── AUDIT_RESULTS_SUMMARY.md          # Executive summary
├── QUICK_REFERENCE.md                # This file
├── run_audit.py                      # Main orchestrator
├── lib/
│   ├── control_envelope.py           # Iteration control
│   └── scoring.py                    # Risk scoring formulas
├── stage0_ingestion/
│   ├── project_profile.py            # Profile extraction
│   └── validation.py                 # Profile validation
├── stage1_mapping/
│   ├── dependency_graph.py           # Dependency analysis
│   ├── fsm_analyzer.py               # State machine analysis
│   └── jwt_analyzer.py               # JWT security analysis
├── stage2_risk_analysis/
│   ├── risk_detector.py              # Multi-vector detection
│   └── risk_scoring.py               # Risk prioritization
└── reports/                          # Generated reports (8 files)
```

## Next Steps

### Immediate Actions (Week 1)
```bash
# 1. Fix container root execution (3h)
# Edit Dockerfiles: Add USER directives
# Priority: CRITICAL, ROI: 26.67

# 2. Add dependency scanning (2h)
# Add to CI/CD: safety, snyk
# Priority: HIGH, ROI: 28.00

# 3. Fix WebSocket cleanup (3h)
# Update dashboard: Add connection cleanup
# Priority: HIGH, ROI: 14.00
```

### Documentation Review
```bash
# Read full analysis
cat audit_framework/AUDIT_RESULTS_SUMMARY.md

# Review framework docs
cat audit_framework/README.md

# Check individual reports
ls -lh audit_framework/reports/
```

## Performance

- **Execution Time:** ~15 seconds
- **Iterations Used:** 3/22 (13.6%)
- **Memory Usage:** <100MB
- **CPU Usage:** Low

## Compliance

✅ FREEZE constraints respected:
- No directory renames
- No heavy dependencies
- No broad refactors
- No core logic changes

✅ Non-invasive:
- Only creates files in `audit_framework/`
- Zero modifications to `inventario-retail/`
- All analysis is read-only

## Support

For issues or questions:
1. Check `audit_framework/README.md`
2. Review `audit_framework/AUDIT_RESULTS_SUMMARY.md`
3. Run individual components to isolate issues
4. Verify FREEZE compliance with `git status`

---

**Last Updated:** 2025-10-02  
**Framework Version:** Etapas 0-2 (Parte 1/2)
