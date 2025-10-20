# GUÍA PRÁCTICA: ANÁLISIS FORENSE CON GITHUB COPILOT PRO
## Metodología Adaptativa No-Invasiva para Sistemas Agénticos

## 🎯 OBJETIVO REFINADO
Esta guía implementa **análisis forense pasivo** usando GitHub Copilot Pro para obtener documentación técnica exhaustiva sin modificar código existente. Cada dato debe estar respaldado por evidencia específica (`archivo:línea`).

---

## 📋 PRERREQUISITOS FORENSES

### 1. Acceso a GitHub Copilot Pro
- Suscripción activa con capacidades de análisis de repositorio completo
- Acceso al chat con contexto de workspace extendido

### 2. Repositorio en Modo de Solo Lectura
- Proyecto abierto en GitHub Codespaces, VS Code, o IDE compatible
- **CRÍTICO**: Modo forense = **NUNCA** modificar archivos durante análisis
- Contexto completo del repositorio disponible para Copilot

### 3. Tiempo Estimado por Análisis Forense
- **Por proyecto**: 60-90 minutos (más exhaustivo que versión anterior)
- **PROMPT 1**: 15-20 minutos (análisis forense detallado)
- **PROMPT 2**: 20-25 minutos (optimización geoeconómica)  
- **PROMPT 3**: 15-20 minutos (configuraciones autocurativas)
- **PROMPT 4**: 15-20 minutos (troubleshooting predictivo)

---

## 🔬 METODOLOGÍA FORENSE PASO A PASO

### FASE 1: PREPARACIÓN DEL CONTEXTO FORENSE

#### 1.1 Establecer Entorno de Análisis
```bash
# Asegurar modo de solo lectura - NO MODIFICAR ARCHIVOS
cd /ruta/a/proyecto/target
# Verificar que tienes permisos de lectura completa
find . -name "*.py" -o -name "*.js" -o -name "*.json" | wc -l
find . -name "requirements*.txt" -o -name "package*.json" | head -5
```

#### 1.2 Archivos de Evidencia Críticos
```bash
# Estos archivos DEBEN estar visibles para análisis forense:
- README.md / README.rst (documentación del proyecto)
- requirements.txt / package.json / pyproject.toml (dependencias)
- main.py / app.py / server.js (puntos de entrada)
- config/ .env.* settings.py (configuraciones)
- Dockerfile docker-compose.yml (containerización)
- .github/ workflows/ (CI/CD existente)
```

#### 1.3 Activación de Contexto Forense
- Abrir Copilot Chat con comando específico: **"Analizar repositorio en modo forense - solo lectura"**
- Verificar que Copilot confirme acceso a la estructura completa del proyecto

---

### FASE 2: ANÁLISIS FORENSE ADAPTATIVO (PROMPT 1)

#### 2.1 Ejecutar Análisis Técnico Forense
```markdown
Copiar exactamente este prompt en Copilot Chat:

# ANÁLISIS TÉCNICO ADAPTATIVO — DIAGNÓSTICO FORENSE DEL ESTADO REAL

**ROL**: Actúa como **Arquitecto Forense + Ingeniero de Confiabilidad**, con acceso total al repositorio actual.

**MANDATO CRÍTICO**:
- **NO** asumas stack, arquitectura ni intenciones.
- **SÍ** infiere solo desde código, configuraciones y scripts reales.
- **CITA SIEMPRE**: `archivo:línea-inicial–línea-final` para cada dato técnico.
- Si algo no está en el repo: **"NO EVIDENCIADO – TODO: confirmar"**.
- Si hay ambigüedad: **marca como riesgo**.

## 1. STACK TECNOLÓGICO — DETECCIÓN EMPÍRICA
- Lenguaje(s) principal(es) y versión(es) exacta(s) (de `runtime.txt`, `pyproject.toml`, `package.json`, etc.)
- Framework(s) web y versión(es) (FastAPI, Express, Django, etc.)
- Base de datos: tipo, versión, driver, modo de conexión (PostgreSQL/SQLite/Mongo/etc.)
- APIs externas integradas: endpoints reales, proveedores, métodos de autenticación
- Librerías de IA/agentes: nombre, versión, patrón de uso (síncrono, streaming, tool use)

## 2. ARQUITECTURA DEL SISTEMA — MAPA DE LO EXISTENTE
- Estructura de carpetas con lógica ejecutable (ignora boilerplate)
- Puntos de entrada reales: archivos que inician el sistema (`main.py`, `server.js`, etc.)
- Módulos core: identificados por acoplamiento o uso frecuente
- Patrones arquitectónicos detectados: microservicios, monolito, event-driven, agéntico, etc.
- Integraciones agénticas: orquestación, autonomía, comunicación, memoria, tool use

## 3. REQUISITOS DE DESPLIEGUE — ESPECIFICACIÓN OPERATIVA
- Variables de entorno **usadas en runtime** (no solo declaradas)
- Puertos y protocolos expuestos (HTTP, WebSocket, gRPC, métricas, healthchecks)
- Recursos mínimos estimados (CPU, RAM, disco) basados en patrones de uso
- Dependencias del sistema: paquetes del SO, binarios, permisos
- Requisitos de red: CORS, proxy, SSL/TLS, dominios

## 4. CONFIGURACIÓN ACTUAL — BRECHA ENTRE DEV Y PROD
- Archivos de configuración existentes (`config/`, `.env*`, `settings.py`, etc.)
- Diferencias observables entre entornos (si existen)
- Scripts de build/test/deploy: comandos reales en `package.json`, `Makefile`, etc.
- Hardcoding detectado: valores fijos que deberían ser configurables

> **ENTREGABLE**: Markdown estructurado con comandos de verificación (ej: `grep -r "os.getenv" .`) y lista de riesgos con severidad (`CRÍTICO`/`ALTO`/`MEDIO`).
```

#### 2.2 Validación de Respuesta Forense
- ✅ **Verificar**: Cada dato técnico incluye cita específica `archivo:línea`
- ✅ **Confirmar**: No se sugieren modificaciones de código
- ✅ **Evaluar**: Los comandos de verificación son ejecutables
- ⚠️ **Alertar**: Si hay información sin evidencia → marcar como "NO EVIDENCIADO"

#### 2.3 Guardar Evidencia
```bash
# Crear archivo de análisis forense
mkdir -p docs/forensic-analysis/
touch docs/forensic-analysis/ANALISIS_FORENSE_ADAPTATIVO.md
# Copiar TODA la respuesta de Copilot con las citas de archivos
```

---

### FASE 3: OPTIMIZACIÓN GEOECONÓMICA (PROMPT 2)

#### 3.1 Ejecutar Plan de Despliegue Dinámico
```markdown
Continuar en el mismo chat de Copilot:

# PLAN DE DESPLIEGUE DINÁMICO — OPTIMIZACIÓN GEOECONÓMICA + RESILIENCIA ANTIFRÁGIL

**ROL**: Actúa como **Ingeniero de Plataformas + Estratega de Costos + Arquitecto de Resiliencia**, con acceso total al repositorio.

**MANDATO**:
- **NO** recomiendes plataforma sin justificación técnica basada en el stack real.
- **SÍ** infiere región óptima desde latencia a APIs de IA, usuarios y costos.
- **SÍ** diseña un plan que **mejore bajo estrés** (antifrágil): fallbacks, degradación elegante, auto-reconfiguración.

## 1. PREPARACIÓN PRE-DESPLIEGUE — SANITIZACIÓN EXTREMA
- Checklist de saneamiento: secrets externalizados, hardcoding eliminado, scripts idempotentes
- Archivos de exclusión: `.dockerignore`, `.gitignore` específicos para este proyecto
- Build optimizado: layer caching, tree-shaking, compilación nativa (si aplica)

## 2. ESTRATEGIA DE HOSTING DINÁMICA
- Recomendación de plataforma (Vercel, Render, Fly.io, AWS, etc.) **justificada por stack, latencia y costo**
- Costo estimado mensual (USD) en plan mínimo viable + umbral de upgrade
- Configuración exacta para auto-deploy: branch, build command, root dir

## 3. DESPLIEGUE AUTOMATIZADO Y VERIFICABLE
- Comandos git + CI/CD necesarios (incluso si no existe CI aún)
- Setup de base de datos en producción: migraciones, seeds, conexión segura
- Configuración de dominio personalizado y HTTPS (con proveedor sugerido)

## 4. ROLLBACK Y RESILIENCIA
- Procedimiento de rollback basado en la arquitectura (git revert, blue/green, etc.)
- Backup mínimo viable: qué guardar, cómo y con qué frecuencia
- Plan de contingencia ante fallo de APIs de IA o servicios externos

> **ENTREGABLE**: Comandos copy-paste, archivos de configuración reales, tabla de costos con fuentes, diagrama de flujo en Mermaid.
```

#### 3.2 Guardar Plan Optimizado
```bash
touch docs/forensic-analysis/PLAN_DESPLIEGUE_DINAMICO.md
# Copiar respuesta con justificaciones geoeconómicas
```

---

### FASE 4: CONFIGURACIONES AUTOCURATIVAS (PROMPT 3)

#### 4.1 Ejecutar Configuraciones de Producción
```markdown
Continuar en el chat:

# CONFIGURACIONES DE PRODUCCIÓN AUTOCURATIVAS

**PRINCIPIO**: La configuración debe **detectar, aislar y corregir** fallos sin intervención humana.

## 1. VARIABLES DE ENTORNO — SEGURIDAD POR DEFECTO
- Genera `.env.prod.template` con valores por defecto **seguros** y comentarios explicativos
- Valida en runtime: `if not API_KEY: raise ConfigError("Falta API_KEY crítica")`
- Variables por entorno: `dev` (verbose), `staging` (estructurado), `prod` (mínimo)

## 2. BASE DE DATOS — RESILIENCIA AUTOMÁTICA
- Connection string con retry, timeout, pool size
- Migraciones idempotentes con rollback automático
- Backup diario con rotación, cifrado y verificación de integridad
- Health check: endpoint que verifica conexión + latency < 100ms

## 3. SEGURIDAD OPERATIVA — DEFENSA EN PROFUNDIDAD
- CORS: solo orígenes explícitos (nunca `*`)
- Rate limiting: por IP + por API key (si aplica)
- Headers de seguridad: HSTS, CSP, X-Frame-Options, etc.
- Validación de inputs: esquemas Pydantic/Zod en todas las entradas

## 4. PERFORMANCE AUTONÓMICA
- Caching: Redis para respuestas de agentes (TTL + invalidación semántica)
- Compresión: Brotli + Gzip fallback
- Query optimization: índices sugeridos basados en queries reales

## 5. CONFIGURACIÓN DE AGENTES — ESTABILIDAD EXTREMA
- Timeouts: LLM (30s), tool use (15s), orquestación (60s)
- Rate limiting adaptativo (reduce velocidad si hay errores 429)
- Fallbacks: si falla modelo primario → usa secundario
- Logging estructurado: con `trace_id` para rastrear decisiones

> **ENTREGABLE**: Código completo de todos los archivos, explicación de cada decisión, comandos para probar.
```

#### 4.2 Guardar Configuraciones
```bash
touch docs/forensic-analysis/CONFIGURACIONES_AUTOCURATIVAS.md
# Copiar configuraciones con mecanismos de autocorrección
```

---

### FASE 5: TROUBLESHOOTING PREDICTIVO (PROMPT 4)

#### 5.1 Ejecutar Análisis de Confiabilidad
```markdown
Finalizar con:

# GUÍA DE TROUBLESHOOTING Y MANTENIMIENTO PROACTIVO

**ROL**: Actúa como **Ingeniero de Confiabilidad Autónoma + Analista de Causa Raíz**.

## 1. PREDICCIÓN DE FALLOS — INDICADORES TEMPRANOS
- Aumento de latencia en llamadas a LLM
- Degradación en calidad de salida (hallucinaciones)
- Quotas de API acercándose al 90%
- Uso de RAM > 80% sostenido

## 2. DIAGNÓSTICO CAUSAL AUTOMÁTICO
- Mapa de dependencias dinámico: si falla `/api/agent`, ¿es por LLM, DB o tool?
- Correlación de eventos: "El fallo coincidió con un deploy de `utils.py`"
- Hipótesis generadas automáticamente con evidencia

## 3. ACCIONES CORRECTIVAS AUTÓNOMAS
- Scripts de autocorrección: reinicia worker si RAM > 90%
- Rollback predictivo: si métricas empeoran tras deploy → revertir en <2 min

## 4. COMANDOS DE MANTENIMIENTO ESENCIALES
- Health checks específicos para este sistema
- Comandos para restart, update de dependencias, limpieza de logs
- Verificación de integridad de base de datos

## 5. MONITOREO Y ALERTAS BÁSICAS
- Métricas críticas: latencia p95, tasa de error, uso de tokens, conexiones WS
- Alertas con umbrales: p95 > 2s, errores > 1%, tokens > 90% quota
- Dashboard básico con métricas clave

## 6. BACKUP Y RECOVERY AUTOMATIZADO
- Script de backup completo con rotación y cifrado
- Procedimiento de restore paso a paso
- Testing de recovery en staging

> **ENTREGABLE**: Script de predicción de fallos, tabla de correlaciones causa-efecto, comandos de diagnóstico, alertas configurables.
```

#### 5.2 Guardar Análisis Predictivo
```bash
touch docs/forensic-analysis/TROUBLESHOOTING_PROACTIVO.md
# Copiar análisis con correlaciones causales
```

---

## 📁 ESTRUCTURA FORENSE RESULTANTE

### Organización de Evidencia Técnica
```bash
proyecto-target/
├── docs/
│   └── forensic-analysis/                    # Nueva metodología
│       ├── ANALISIS_FORENSE_ADAPTATIVO.md    # Con citas archivo:línea
│       ├── PLAN_DESPLIEGUE_DINAMICO.md       # Con justificaciones geoeconómicas
│       ├── CONFIGURACIONES_AUTOCURATIVAS.md  # Con mecanismos de autocorrección  
│       └── TROUBLESHOOTING_PROACTIVO.md      # Con correlaciones causales
├── config/
│   ├── .env.prod.template                   # Generado por PROMPT 3
│   └── production-configs/                   # Archivos autocurativos
└── scripts/
    ├── forensic-deploy.sh                   # Comandos validados
    ├── health-check-predictive.sh           # Monitoreo proactivo
    └── backup-automated.sh                  # Recovery automatizado
```

---

## 🔍 VALIDACIÓN FORENSE DE RESULTADOS

### Checklist de Calidad Forense
- [ ] **PROMPT 1**: ¿Cada dato técnico incluye cita `archivo:línea-inicial–línea-final`?
- [ ] **PROMPT 1**: ¿Se marcaron elementos "NO EVIDENCIADO" cuando correspondía?
- [ ] **PROMPT 2**: ¿La recomendación de plataforma está justificada por el stack detectado?
- [ ] **PROMPT 2**: ¿Los comandos son específicos para la arquitectura real?
- [ ] **PROMPT 3**: ¿Las configuraciones incluyen mecanismos de autocorrección?
- [ ] **PROMPT 3**: ¿Los archivos son funcionales y no genéricos?
- [ ] **PROMPT 4**: ¿El troubleshooting incluye correlaciones causales específicas?
- [ ] **PROMPT 4**: ¿Los scripts son ejecutables sin modificaciones?

### 🎯 Indicadores de Análisis Forense Exitoso
✅ **Respuesta de alta calidad**:
- Citas específicas: `requirements.txt:15-23`, `main.py:45-67`
- Comandos verificables: `grep -r "DATABASE_URL" .`
- Detección de riesgos: "RIESGO ALTO: hardcoded API keys en config.py:12"
- Evidencia empírica: "Detectado FastAPI 0.104.1 en requirements.txt:8"
- Configuraciones adaptativas al stack real

❌ **Respuesta genérica deficiente**:
- Sin citas de archivos específicos
- Recomendaciones aplicables a cualquier proyecto
- Comandos que no corresponden al stack detectado
- Configuraciones templátizadas sin adaptación
- Ausencia de análisis de riesgo

---

## 💡 TÉCNICAS AVANZADAS PARA ANÁLISIS FORENSE

### 1. Maximizar Contexto para Copilot
```bash
# Antes de ejecutar prompts, preparar contexto rico:
find . -name "*.py" -exec wc -l {} + | sort -n | tail -10  # Archivos más grandes
find . -name "requirements*.txt" -exec cat {} \;           # Todas las dependencias
ls -la .env* config/ settings/                           # Archivos de configuración
```

### 2. Conversación Forense Continua  
- Usar el mismo chat para los 4 prompts
- Copilot mantendrá contexto y podrá correlacionar información
- Hacer preguntas de seguimiento para clarificar evidencia

### 3. Preguntas de Validación Forense
```markdown
# Preguntas adicionales recomendadas:
"¿Puedes verificar que TODOS los datos incluyan citas archivo:línea?"
"¿Hay configuraciones hardcodeadas que representen riesgos de seguridad?"
"¿Los comandos generados funcionarán con el stack detectado?"
"¿Qué evidencia específica respalda la recomendación de plataforma?"
```

### 4. Personalización Contextual
```markdown
# Personalizar prompts añadiendo contexto específico:
"Este sistema maneja datos financieros y debe cumplir PCI DSS"
"La aplicación tiene picos de 10,000 usuarios simultáneos"
"Debe funcionar en región LATAM con APIs de OpenAI"
```

---

## 🚨 PROBLEMAS COMUNES Y SOLUCIONES FORENSES

### Problema 1: Respuestas Sin Evidencia
**Síntoma**: Copilot proporciona datos técnicos sin citar archivos específicos

**Solución Forense**:
```markdown
"Para cada dato técnico que mencionas, NECESITO la cita exacta archivo:línea. 
Si no puedes encontrar evidencia en el código, marca como 'NO EVIDENCIADO'."
```

### Problema 2: Recomendaciones Genéricas
**Síntoma**: Configuraciones que podrían aplicar a cualquier proyecto

**Solución Forense**:
```markdown
"Basándote ÚNICAMENTE en el código que estás analizando, adapta las 
configuraciones al stack específico detectado. NO uses plantillas genéricas."
```

### Problema 3: Comandos Incorrectos
**Síntoma**: Scripts que no funcionan con la arquitectura real

**Solución Forense**:
```markdown
"Verifica que cada comando sea ejecutable en el proyecto actual. 
Proporciona evidencia de por qué ese comando es correcto para este stack."
```

### Problema 4: Ausencia de Análisis de Riesgo
**Síntoma**: No se identifican problemas de seguridad o configuración

**Solución Forense**:
```markdown
"Identifica TODOS los riesgos de seguridad, hardcoding, y configuraciones 
inseguras con severidad CRÍTICO/ALTO/MEDIO y cita la ubicación exacta."
```

---

## 📊 MÉTRICAS DE ÉXITO FORENSE

### Por Análisis Completado
- ✅ 4 documentos con evidencia citada (`archivo:línea`)
- ✅ Al menos 5 comandos de verificación ejecutables
- ✅ Identificación de 3+ riesgos con severidad asignada
- ✅ Configuraciones adaptadas al stack específico detectado
- ✅ Plan de despliegue con justificación geoeconómica

### Tiempo y Precisión
- **Análisis tradicional**: 12-16 horas de investigación manual
- **Análisis forense con prompts**: 60-90 minutos + validación
- **Ahorro de tiempo**: ~85% con mayor precisión
- **Precisión mejorada**: Evidencia citada y verificable

### Calidad de Evidencia
- **Citas específicas**: >95% de datos técnicos con `archivo:línea`
- **Comandos verificables**: 100% ejecutables sin error
- **Adaptación contextual**: Configuraciones específicas al stack real
- **Detección de riesgos**: Identificación proactiva de vulnerabilidades

---

## 🛡️ PRINCIPIOS FORENSES CRÍTICOS

### 1. Modo Solo Lectura Estricto
- **NUNCA** modificar archivos durante el análisis
- **SOLO** observar, diagnosticar y documentar
- **VALIDAR** que Copilot no sugiera cambios de código

### 2. Evidencia Obligatoria
- Todo dato técnico DEBE incluir `archivo:línea-inicial–línea-final`
- Sin evidencia = "NO EVIDENCIADO – TODO: confirmar"
- Ambigüedades = "RIESGO: requiere validación manual"

### 3. Adaptación Forzada
- Configuraciones específicas al stack detectado
- NO usar plantillas genéricas
- Justificar cada recomendación con evidencia del código

### 4. Crítica Constructiva
- Cuestionar configuraciones inseguras
- Identificar hardcoding y malas prácticas
- Proponer soluciones basadas en el contexto real

---

Esta metodología forense refinada garantiza análisis técnicos exhaustivos, evidenciados y adaptados a la realidad específica de cada proyecto, eliminando suposiciones y maximizando la precisión operativa.