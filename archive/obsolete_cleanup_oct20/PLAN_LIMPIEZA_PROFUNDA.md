# PLAN DE LIMPIEZA PROFUNDA - CONSOLIDACIÓN DEL REPOSITORIO

**Fecha:** October 18, 2025  
**Objetivo:** Reducir 110 archivos en raíz a <20, eliminar duplicados, consolidar documentación  
**Estado:** EJECUTANDO

---

## 📊 DIAGNÓSTICO ACTUAL

### Problema Identificado
```
RAÍZ DEL PROYECTO: 110 archivos (8.4 GB)
├─ 79 archivos .md (redundancia masiva)
├─ 4 archivos .py (scripts de utilidad)
├─ 4 archivos .sh (backup/restore)
├─ 3 archivos .json (config/reports)
├─ 3 archivos .txt (logs/config)
├─ 16 archivos varios (archives, docs, etc.)
└─ PROBLEMA: Confusión masiva, múltiples versiones, duplicados
```

### Duplicados Identificados
```
PROMPTS & GUÍAS (9+ archivos)
├─ PROMPTS_GITHUB_COPILOT_PRO.md
├─ PROMPTS_GITHUB_COPILOT_PRO_DEFINITIVOS.md ⚠️ DUPLICADO
├─ GUIA_IMPLEMENTACION_PROMPTS_DEFINITIVOS.md ⚠️ DUPLICADO
├─ GUIA_PRACTICA_USO_PROMPTS.md
├─ README_PROMPTS_COPILOT.md ⚠️ REDUNDANTE

QUICK REFERENCES (5 archivos)
├─ QUICK_REFERENCE_PROMPTS.md
├─ QUICK_REFERENCE_PROMPTS_DEFINITIVOS.md ⚠️ DUPLICADO
├─ QUICK_START_REFERENCE.md ⚠️ REDUNDANTE
├─ QUICKSTART_OCT5.md ⚠️ DESACTUALIZADO
├─ README_ETAPA3_QUICK_REF.md ⚠️ OBSOLETO

RESÚMENES DE SESIONES (15 archivos)
├─ RESUMEN_FINAL_SESION_OCT16.md
├─ RESUMEN_SESION_OCT16.md ⚠️ DUPLICADO
├─ SESSION_LOG_OCT17.txt
├─ SESSION_SUMMARY_2025-09-* (múltiples versiones)
└─ ... (mezclados con otros reportes)

PLANES/ÍNDICES (10+ archivos)
├─ PLAN_EJECUCION_GO_LIVE.md
├─ PLAN_EJECUCION_FINAL_DEPLOYMENT.md ⚠️ SIMILAR
├─ PLAN_DESPLIEGUE_INVENTARIO_RETAIL.md ⚠️ SIMILAR
├─ INDICE_MAESTRO_ETAPA2.md
├─ INDICE_MAESTRO_ETAPA2_ETAPA3.md ⚠️ VERSIÓN MÁS NUEVA
├─ MEGA_PLAN_ETAPA_3.md ⚠️ OBSOLETO

DEPLOYMENT (7+ archivos conflictivos)
├─ README_DEPLOY_STAGING.md
├─ README_DEPLOY_STAGING_EXT.md ⚠️ EXTENSIÓN
├─ STAGING_DEPLOYMENT_*.md (4 versiones) ⚠️ CONFLICTIVO
├─ TRACK_A2_PRODUCTION_DEPLOYMENT.md
└─ /deploy, /deployment_* (3 directorios)

ARCHIVES NO CATALOGADOS (4 archivos)
├─ archive.zip (100 KB)
├─ archive(1) (1).zip (172 KB)
├─ archive(2).zip (828 KB)
├─ archive(3).zip (892 KB) ⚠️ ELIMINAR
└─ sistema_multiagente_*.zip (2 archivos) ⚠️ ELIMINAR
```

---

## 🎯 ESTRATEGIA DE CONSOLIDACIÓN

### Estructura Objetivo

```
aidrive_genspark/
├── docs/                              ← DOCUMENTACIÓN CONSOLIDADA
│   ├── REFERENCIAS.md                 ← Índice maestro único
│   ├── guides/
│   │   ├── GUIA_USUARIO_DASHBOARD.md
│   │   ├── GUIA_PROMPTS.md            ← CONSOLIDADO (definitivo)
│   │   ├── API_DOCUMENTATION.md
│   │   └── QUICK_START.md             ← ÚNICO
│   ├── deployment/
│   │   ├── DEPLOYMENT_GUIDE.md        ← CONSOLIDADO
│   │   ├── README_STAGING.md
│   │   └── README_PRODUCTION.md
│   ├── runbooks/                      ← OPERACIONAL
│   │   └── (11 runbooks existentes)
│   ├── adr/                           ← DECISIONES
│   │   └── (6 ADRs existentes)
│   └── archive/                       ← HISTÓRICO
│       ├── SESSION_LOGS/
│       ├── PROMPTS_ARCHIVE/
│       └── OBSOLETE_PLANS/
│
├── AUDITORIA_PRE_DESPLIEGUE/          ← AUDITORÍA ACTUAL
│   ├── FASE_0_BASELINE.md
│   ├── FASE_1_ANALISIS_CODIGO_REPORT.md
│   ├── FASE_4_OPTIMIZACION_REPORT.md
│   ├── FASE_5_HARDENING_REPORT.md
│   ├── FASE_6_DOCUMENTACION_REPORT.md
│   ├── OPCION_C_IMPLEMENTATION_PLAN.md
│   └── ESTADO_ACTUAL.md               ← NUEVO
│
├── inventario-retail/                 ← CÓDIGO PRINCIPAL
│   ├── shared/
│   ├── agente_deposito/
│   ├── agente_negocio/
│   └── web_dashboard/
│
├── tests/                             ← TESTS
├── scripts/                           ← SCRIPTS ÚTILES
└── .github/                           ← CI/CD

ARCHIVOS EN RAÍZ (≤20):
├── README.md                          ← ÍNDICE PRINCIPAL
├── CHANGELOG.md
├── Makefile
├── conftest.py
├── pytest.ini
├── requirements-test.txt
├── requirements.txt
├── docker-compose.*.yml (3 archivos)
├── .github/copilot-instructions.md
└── (scripts útiles del repo)
```

---

## 🗑️ ARCHIVOS A ELIMINAR (CATEGORÍA 1: SIN DUDAS)

### Archives/Zips Duplicados (1.2 MB - BASURA)
```
archive.zip
archive(1) (1).zip
archive(2).zip
archive(3).zip
sistema_multiagente_documentacion_completa.zip
documentacion_sistema_multiagente.zip
```
**Razón:** Archivos de compresión antiguos, sin metadatos, duplicados
**Impacto:** -1.2 MB

### Documentos Word (6 MB - OBSOLETO)
```
Doc1 logica y gestion nego..docx
```
**Razón:** Formato antiguo, contenido duplicado en .md
**Impacto:** -6 MB

### Logs/Outputs de Deployment Fallido
```
deployment_output.log
deployment_results
STAGING_DEPLOYMENT_ATTEMPT1_FAILED.md
STAGING_DEPLOYMENT_IN_PROGRESS.md
STAGING_DEPLOYMENT_PROGRESS.md
STAGING_DEPLOYMENT_STATUS_FINAL.md
```
**Razón:** Intentos fallidos, obsoletos por nuevos planes
**Impacto:** -0.5 MB

### Planes Antiguos/Reemplazados (ETAPA 2)
```
INDICE_MAESTRO_ETAPA2.md          → REEMPLAZADO por ETAPA2_ETAPA3
RESUMEN_EJECUTIVO_ETAPA2.md       → ARCHIVADO
PLAN_DESPLIEGUE_BI_ORCHESTRATOR.md → NO IMPLEMENTADO
MEGA_PLAN_ETAPA_3.md              → REEMPLAZADO por GO_LIVE plan
```
**Razón:** Etapas anteriores completadas, planes más nuevos disponibles
**Impacto:** -0.3 MB

### Esquemas de Test/Analysis (OBSOLETO)
```
PROMPT_TESTING_FRAMEWORK.md       → ARCHIVADO
VALIDACION_CONSISTENCIA_PROMPTS.md → ARCHIVADO
```
**Razón:** Frameworks antiguos, no utilizados
**Impacto:** -0.1 MB

---

## 📦 ARCHIVOS A CONSOLIDAR (CATEGORÍA 2: FUSIONAR)

### Consolidación 1: Guías de Prompts
```
ORIGINALS:
  PROMPTS_GITHUB_COPILOT_PRO.md
  PROMPTS_GITHUB_COPILOT_PRO_DEFINITIVOS.md ← USAR ESTE
  GUIA_IMPLEMENTACION_PROMPTS_DEFINITIVOS.md
  GUIA_PRACTICA_USO_PROMPTS.md
  README_PROMPTS_COPILOT.md

CONSOLIDAR EN:
  docs/guides/GUIA_PROMPTS_COPILOT.md
  
ELIMINAR:
  PROMPTS_GITHUB_COPILOT_PRO.md (versión vieja)
  GUIA_IMPLEMENTACION_PROMPTS_DEFINITIVOS.md (redundante)
  README_PROMPTS_COPILOT.md (redundante)
```

### Consolidación 2: Quick References
```
ORIGINALS:
  QUICK_REFERENCE_PROMPTS.md
  QUICK_REFERENCE_PROMPTS_DEFINITIVOS.md ← USAR ESTE
  QUICK_START_REFERENCE.md
  QUICKSTART_OCT5.md
  README_ETAPA3_QUICK_REF.md

CONSOLIDAR EN:
  docs/guides/QUICK_START.md
  
ELIMINAR:
  Todos menos QUICK_REFERENCE_PROMPTS_DEFINITIVOS.md (más completo)
```

### Consolidación 3: Deployment Guides
```
ORIGINALS:
  README_DEPLOY_STAGING.md
  README_DEPLOY_STAGING_EXT.md
  TRACK_A2_PRODUCTION_DEPLOYMENT.md

CONSOLIDAR EN:
  docs/deployment/DEPLOYMENT_GUIDE.md (índice)
  docs/deployment/README_STAGING.md (STAGING específico)
  docs/deployment/README_PRODUCTION.md (PRODUCTION específico)
  
ELIMINAR:
  README_DEPLOY_STAGING_EXT.md (contenido en README_DEPLOY_STAGING.md)
```

### Consolidación 4: Índices Maestros
```
ORIGINALS:
  INDICE_MAESTRO_ETAPA2.md
  INDICE_MAESTRO_ETAPA2_ETAPA3.md ← USAR ESTE
  INDICE_ANALISIS_OPTIMIZACIONES.md

CONSOLIDAR EN:
  docs/REFERENCIAS.md (índice único con referencias cruzadas)
  docs/archive/OBSOLETE_INDICES/
  
ELIMINAR:
  INDICE_MAESTRO_ETAPA2.md (versión vieja)
  INDICE_ANALISIS_OPTIMIZACIONES.md (contenido subsumido)
```

### Consolidación 5: Session Logs (Archivados)
```
ORIGINALS:
  SESSION_LOG_OCT17.txt
  SESSION_SUMMARY_2025-09-12.md
  SESSION_SUMMARY_2025-09-14.md
  SESSION_SUMMARY_2025-09-15.md
  SESSION_SUMMARY_2025-09-26.md
  SESSION_2_COMPREHENSIVE_REPORT.md
  SESSION_2_EXECUTIVE_SUMMARY.md
  RESUMEN_FINAL_SESION2_ES.md
  ... (15 archivos total)

CONSOLIDAR EN:
  docs/archive/SESSION_LOGS/ (todos archivados con índice)
  
ELIMINAR:
  De la raíz (mover a archive)
```

### Consolidación 6: Progress Reports (Archivados)
```
ORIGINALS:
  PROGRESO_ETAPA3_OCT4.md
  PROGRESO_ETAPA3_OCT7.md
  PROGRESO_ETAPA3_OCT16.md
  RESUMEN_FINAL_ETAPA3_OCT17.md
  RESUMEN_SESION_OCT16.md
  RESUMEN_FINAL_SESION_OCT16.md

CONSOLIDAR EN:
  docs/archive/PROGRESS_REPORTS/ (todos archivados)
  
ELIMINAR:
  De la raíz (mover a archive)
```

---

## ✅ ARCHIVOS A MANTENER EN RAÍZ (NECESARIOS)

```
CRÍTICOS (no mover):
✓ README.md                          ← Punto de entrada
✓ CHANGELOG.md                       ← Historial de versiones
✓ Makefile                           ← Build automation
✓ .github/copilot-instructions.md    ← Configuración

CONFIGURACIÓN (no mover):
✓ pytest.ini
✓ conftest.py
✓ requirements-test.txt
✓ docker-compose.production.yml
✓ docker-compose.analysis.yml
✓ docker-compose.dev.yml (si existe)

DOCUMENTACIÓN CRÍTICA (raíz):
✓ ESPECIFICACION_TECNICA.md          ← Especificación del sistema
✓ DOCUMENTACION_MAESTRA_MINI_MARKET.md ← Documentación general
✓ API_DOCUMENTATION.md               ← API contracts
✓ INFORME_FINAL_SISTEMA_MINIMARKET.md ← Reporte final

AUDITORÍA (raíz):
✓ AUDITORIA_PRE_DESPLIEGUE/          ← Carpeta de auditoría
✓ SECURITY_AUDIT_REPORT_*.md         ← Reportes de seguridad

SCRIPTS ÚTILES (raíz):
✓ backup_minimarket.sh
✓ restore_minimarket.sh
✓ pytest_matplotlib_sitecustomize.py
✓ conftest.py

CONFIGURACIÓN PROYECTO (raíz):
✓ sbom_baseline.json                 ← Software Bill of Materials
✓ coverage.xml                       ← Coverage report
```

---

## 🚀 PLAN DE EJECUCIÓN

### FASE 1: Crear Estructura de Directorios
```bash
mkdir -p docs/{guides,deployment,archive/{SESSION_LOGS,PROGRESS_REPORTS,PROMPTS_ARCHIVE,OBSOLETE_PLANS}}
```

### FASE 2: Mover Archivos a Carpetas (No eliminar aún)
```
Session logs → docs/archive/SESSION_LOGS/
Progress reports → docs/archive/PROGRESS_REPORTS/
Obsolete plans → docs/archive/OBSOLETE_PLANS/
```

### FASE 3: Consolidar Documentación
```
Prompts guides → docs/guides/GUIA_PROMPTS_COPILOT.md
Quick refs → docs/guides/QUICK_START.md
Deployment → docs/deployment/
```

### FASE 4: Crear Índices de Referencias
```
docs/REFERENCIAS.md (índice maestro)
docs/archive/INDEX.md (índice de histórico)
```

### FASE 5: Limpiar Archivos Basura
```
Eliminar archives.zip*
Eliminar documentos Word
Eliminar deployment logs fallidos
```

### FASE 6: Consolidar en Git
```bash
git add docs/
git rm (archivos obsoletos)
git commit -m "cleanup: Consolidate documentation, reduce root clutter"
```

---

## 📊 RESULTADOS ESPERADOS

**ANTES:**
```
110 archivos en raíz
8.4 GB total
79 .md archivos duplicados/redundantes
Confusión máxima
```

**DESPUÉS:**
```
≤20 archivos en raíz (máximo)
7.2 GB total (-1.2 GB = archives)
Documentación clara y consolidada
Estructura lógica
```

**REDUCCIÓN:**
- Archivos: 110 → 18 (-83.6%)
- Duplicados: 20+ → 0 (-100%)
- Confusión: Alta → Nula

---

## 📋 CHECKLIST DE EJECUCIÓN

- [ ] FASE 1: Crear estructura de directorios
- [ ] FASE 2: Mover archivos históricos a archive/
- [ ] FASE 3: Consolidar guías y planes
- [ ] FASE 4: Crear índices de referencias
- [ ] FASE 5: Eliminar archivos basura (.zip, .docx, logs fallidos)
- [ ] FASE 6: Verificar integridad de enlaces
- [ ] FASE 7: Commit a Git con message claro
- [ ] FASE 8: Crear README en docs/archive/
- [ ] FASE 9: Validar estructura final
- [ ] FASE 10: Documentar cambios en CHANGELOG.md

---

## ⚠️ NOTAS IMPORTANTES

1. **Git History Preserved:** Los archivos eliminados seguirán en Git history
2. **Consolidación:** Se fusionarán contenidos relevantes, no se perderán datos
3. **Validación:** Se verificarán enlaces después de mover archivos
4. **Reversible:** Cualquier cambio puede revertirse con Git
5. **Impacto:** Reducción de confusión → Mejor mantenibilidad

---

**Estado:** LISTO PARA EJECUTAR  
**Próximo paso:** Ejecutar FASE 1-5 automáticamente
