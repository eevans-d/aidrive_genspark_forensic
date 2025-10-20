# REFERENCIA RÁPIDA: PROMPTS FORENSES REFINADOS
## GitHub Copilot Pro - Análisis Técnico No-Invasivo

**🔬 PRINCIPIO FORENSE**: Análisis pasivo con evidencia citada (`archivo:línea`)

---

## 🚀 PROMPT 1: ANÁLISIS FORENSE ADAPTATIVO

```markdown
# ANÁLISIS TÉCNICO ADAPTATIVO — DIAGNÓSTICO FORENSE DEL ESTADO REAL

**ROL**: Actúa como **Arquitecto Forense + Ingeniero de Confiabilidad**, con acceso total al repositorio actual.

**MANDATO CRÍTICO**:
- **NO** asumas stack, arquitectura ni intenciones.
- **SÍ** infiere solo desde código, configuraciones y scripts reales.
- **CITA SIEMPRE**: `archivo:línea-inicial–línea-final` para cada dato técnico.
- Si algo no está en el repo: **"NO EVIDENCIADO – TODO: confirmar"**.
- Si hay ambigüedad: **marca como riesgo**.

## 1. STACK TECNOLÓGICO — DETECCIÓN EMPÍRICA
## 2. ARQUITECTURA DEL SISTEMA — MAPA DE LO EXISTENTE  
## 3. REQUISITOS DE DESPLIEGUE — ESPECIFICACIÓN OPERATIVA
## 4. CONFIGURACIÓN ACTUAL — BRECHA ENTRE DEV Y PROD

> **ENTREGABLE**: Markdown estructurado con comandos de verificación y lista de riesgos con severidad.
```

---

## 🌍 PROMPT 2: DESPLIEGUE DINÁMICO GEOECONÓMICO

```markdown
# PLAN DE DESPLIEGUE DINÁMICO — OPTIMIZACIÓN GEOECONÓMICA + RESILIENCIA ANTIFRÁGIL

**ROL**: Actúa como **Ingeniero de Plataformas + Estratega de Costos + Arquitecto de Resiliencia**.

**MANDATO**:
- **NO** recomiendes plataforma sin justificación técnica basada en el stack real.
- **SÍ** infiere región óptima desde latencia a APIs de IA, usuarios y costos.
- **SÍ** diseña un plan que **mejore bajo estrés** (antifrágil).

## 1. PREPARACIÓN PRE-DESPLIEGUE — SANITIZACIÓN EXTREMA
## 2. ESTRATEGIA DE HOSTING DINÁMICA
## 3. DESPLIEGUE AUTOMATIZADO Y VERIFICABLE
## 4. ROLLBACK Y RESILIENCIA

> **ENTREGABLE**: Comandos copy-paste, archivos de configuración reales, tabla de costos con fuentes.
```

---

## 🛡️ PROMPT 3: CONFIGURACIONES AUTOCURATIVAS

```markdown
# CONFIGURACIONES DE PRODUCCIÓN AUTOCURATIVAS

**PRINCIPIO**: La configuración debe **detectar, aislar y corregir** fallos sin intervención humana.

## 1. VARIABLES DE ENTORNO — SEGURIDAD POR DEFECTO
## 2. BASE DE DATOS — RESILIENCIA AUTOMÁTICA
## 3. SEGURIDAD OPERATIVA — DEFENSA EN PROFUNDIDAD
## 4. PERFORMANCE AUTONÓMICA
## 5. CONFIGURACIÓN DE AGENTES — ESTABILIDAD EXTREMA

> **ENTREGABLE**: Código completo de todos los archivos, explicación de cada decisión, comandos para probar.
```

---

## 🔧 PROMPT 4: TROUBLESHOOTING PREDICTIVO

```markdown
# GUÍA DE TROUBLESHOOTING Y MANTENIMIENTO PROACTIVO

**ROL**: Actúa como **Ingeniero de Confiabilidad Autónoma + Analista de Causa Raíz**.

## 1. PREDICCIÓN DE FALLOS — INDICADORES TEMPRANOS
## 2. DIAGNÓSTICO CAUSAL AUTOMÁTICO
## 3. ACCIONES CORRECTIVAS AUTÓNOMAS
## 4. COMANDOS DE MANTENIMIENTO ESENCIALES
## 5. MONITOREO Y ALERTAS BÁSICAS
## 6. BACKUP Y RECOVERY AUTOMATIZADO

> **ENTREGABLE**: Script de predicción de fallos, tabla de correlaciones causa-efecto, comandos de diagnóstico.
```

---

## ⚡ EJECUCIÓN RÁPIDA

### 1. Preparar Contexto
```bash
# Abrir proyecto en IDE con Copilot Pro activado
# Verificar acceso completo al repositorio
# Activar modo de análisis forense (solo lectura)
```

### 2. Ejecutar Secuencia
```bash
# Copiar PROMPT 1 → Pegar en Copilot Chat → Guardar respuesta
# Copiar PROMPT 2 → Continuar en mismo chat → Guardar respuesta  
# Copiar PROMPT 3 → Continuar en mismo chat → Guardar respuesta
# Copiar PROMPT 4 → Continuar en mismo chat → Guardar respuesta
```

### 3. Validar Calidad
```bash
# ✅ Verificar citas archivo:línea en cada dato técnico
# ✅ Confirmar comandos ejecutables sin error
# ✅ Validar configuraciones específicas al stack detectado
# ✅ Revisar que no se sugieran modificaciones de código
```

---

## 🎯 OUTPUTS ESPERADOS

```bash
docs/forensic-analysis/
├── ANALISIS_FORENSE_ADAPTATIVO.md    # Con evidencia citada
├── PLAN_DESPLIEGUE_DINAMICO.md       # Con justificación geoeconómica  
├── CONFIGURACIONES_AUTOCURATIVAS.md  # Con mecanismos de autocorrección
└── TROUBLESHOOTING_PROACTIVO.md      # Con correlaciones causales
```

---

## 🚨 VALIDACIÓN CRÍTICA

### ✅ Respuesta de Alta Calidad:
- Citas específicas: `main.py:45-67`, `requirements.txt:15-23`
- Comandos verificables: `grep -r "DATABASE_URL" .`
- Detección de riesgos: "RIESGO ALTO: API keys hardcodeadas"
- Configuraciones adaptativas al stack real

### ❌ Respuesta Deficiente:
- Sin citas de archivos específicos
- Recomendaciones genéricas
- Comandos incorrectos para el stack
- Configuraciones templátizadas

---

## 🔍 PROYECTOS IDENTIFICADOS EN EL REPO

### 1. 📦 Sistema Inventario Retail Multi-Agente
- **Path**: `/inventario-retail/`
- **Stack**: Python 3.11, FastAPI, SQLite/PostgreSQL, Redis
- **Features**: OCR, ML, Dashboard, AFIP compliance

### 2. 🧠 Business Intelligence Orchestrator  
- **Path**: `/business-intelligence-orchestrator-v3.1/`
- **Stack**: Python, Selenium, BeautifulSoup, PostgreSQL
- **Features**: Web scraping, competitive intelligence

### 3. 🏪 Sistema Retail Argentina Enterprise
- **Path**: `/retail-argentina-system/`
- **Stack**: Python, PostgreSQL, Redis, Docker
- **Features**: AFIP integration, backup automation

### 4. 📊 Dashboards y Interfaces Web
- **Path**: Multiple folders (`inventario_retail_dashboard_*`)
- **Stack**: Flask/FastAPI, HTML/CSS/JS, Docker
- **Features**: Real-time dashboards, mobile responsive

---

## 🚨 TROUBLESHOOTING FORENSE

### Problema: Respuestas Sin Evidencia
**Solución**:
```markdown
"NECESITO citas archivo:línea para cada dato técnico. Sin evidencia = 'NO EVIDENCIADO'."
```

### Problema: Recomendaciones Genéricas
**Solución**:
```markdown
"Basándote ÚNICAMENTE en el código real, NO uses plantillas genéricas."
```

### Problema: Comandos Incorrectos
**Solución**:
```markdown
"Verifica que cada comando sea ejecutable en este stack específico."
```

---

## 💡 PERSONALIZACIÓN CONTEXTUAL

### Para Región Argentina:
```markdown
"Optimizar para usuarios en Argentina, APIs de IA desde región LATAM."
```

### Para Sistemas Agénticos:
```markdown
"Sistema multi-agente con orquestación, tool use y comunicación inter-servicio."
```

### Para Compliance AFIP:
```markdown
"Debe cumplir normativas AFIP Argentina y protección de datos."
```

---

**⏱️ Tiempo Total**: 60-90 minutos por proyecto  
**🎯 Ahorro**: ~85% vs análisis manual  
**🔍 Precisión**: >95% con evidencia citada  
**🛡️ Principio**: PASIVO - Solo observa, NUNCA modifica código