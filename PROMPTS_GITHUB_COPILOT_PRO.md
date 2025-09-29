# PROMPTS REFINADOS PARA GITHUB COPILOT PRO
## Análisis Forense Adaptativo para Sistemas Agénticos

**✅ PRINCIPIOS FUNDAMENTALES:**
- ✅ **Modo pasivo/no invasivo**: nunca modifican el repositorio. Solo observan, diagnostican y analizan
- ✅ **Universalmente aplicables**: cualquier proyecto (FastAPI, Express, Django, etc.), no solo específicos  
- ✅ **Crítica autónoma**: el modelo debe cuestionar, no asumir
- ✅ **Adaptación forzada**: cada salida se alinea con la realidad del código, no con plantillas genéricas
- ✅ **Exhaustividad forense**: nada queda fuera; todo se respalda con `archivo:línea`
- ✅ **Acción inmediata**: comandos copy-paste, scripts, tablas, decisiones justificadas

---

## ✅ **PROMPT 1 REFINADO: ANÁLISIS TÉCNICO ADAPTATIVO — DIAGNÓSTICO FORENSE DEL ESTADO REAL**

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

---

## ✅ **PROMPT 2 REFINADO: PLAN DE DESPLIEGUE DINÁMICO — OPTIMIZACIÓN GEOECONÓMICA Y RESILIENCIA ANTIFRÁGIL**

```markdown
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

---

## ✅ **PROMPT 3 REFINADO: CONFIGURACIONES DE PRODUCCIÓN AUTOCURATIVAS — SEGURIDAD, PERFORMANCE Y OBSERVABILIDAD POR DISEÑO**

```markdown
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

---

## ✅ **PROMPT 4 REFINADO: GUÍA DE TROUBLESHOOTING Y MANTENIMIENTO PROACTIVO — DIAGNÓSTICO CAUSAL Y AUTOCURACIÓN**

```markdown
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

---

## 📋 INSTRUCCIONES DE USO REFINADAS

### METODOLOGÍA FORENSE
1. **MODO PASIVO**: Los prompts **JAMÁS** modifican código. Solo analizan y diagnostican.
2. **EVIDENCIA CITADA**: Cada dato técnico debe incluir `archivo:línea-inicial–línea-final`.
3. **CRÍTICA CONSTRUCTIVA**: Cuestiona todo, no asumas nada que no esté evidenciado.
4. **UNIVERSALIDAD**: Aplicable a cualquier stack tecnológico sin sesgos.

### PROCESO DE EJECUCIÓN
1. **Ejecuta los prompts en orden** (1→2→3→4) en cada repositorio
2. **Copia cada prompt completo** manteniendo la estructura markdown
3. **Pega en GitHub Copilot Pro** con el contexto del repositorio abierto
4. **Valida que las respuestas incluyan citas** de archivos específicos
5. **Guarda la documentación generada** con nombres descriptivos
6. **Repite el proceso** para cada proyecto del repositorio

## 🎯 RESULTADO ESPERADO REFINADO

Después de ejecutar los 4 prompts obtendrás:
- ✅ **Análisis forense exhaustivo** con evidencia citada
- ✅ **Plan de deployment geoeconómico** optimizado para latencia/costo
- ✅ **Configuraciones autocurativas** que se corrigen automáticamente
- ✅ **Sistema de troubleshooting predictivo** con correlación causal
- ✅ **Scripts completamente funcionales** validados contra el código real
- ✅ **Documentación universal** aplicable a cualquier stack

---

## 🔍 PROYECTOS IDENTIFICADOS EN ESTE REPOSITORIO

### 1. Sistema Inventario Retail Multi-Agente
- **Ubicación**: `/inventario-retail/`
- **Tipo**: Sistema multi-agente con FastAPI
- **Stack**: Python 3.11, FastAPI, SQLite/PostgreSQL, Redis
- **Características**: OCR, ML, Dashboard web, AFIP compliance

### 2. Business Intelligence Orchestrator
- **Ubicación**: `/business-intelligence-orchestrator-v3.1/`
- **Tipo**: Sistema de web scraping y análisis BI
- **Stack**: Python, Web scraping, Database storage
- **Características**: Competitive intelligence, automated data collection

### 3. Sistema Retail Argentina Enterprise
- **Ubicación**: `/retail-argentina-system/`
- **Tipo**: Sistema retail enterprise con compliance AFIP
- **Stack**: Python, PostgreSQL, Redis, Docker
- **Características**: AFIP integration, backup automation, security compliance

### 4. Dashboards y Interfaces Web
- **Ubicación**: Multiple folders (`inventario_retail_dashboard_*`)
- **Tipo**: Interfaces web para gestión y monitoreo  
- **Stack**: Flask/FastAPI, HTML/CSS/JavaScript, Docker
- **Características**: Real-time dashboards, mobile responsive, API integration

## GUÍA RÁPIDA DE APLICACIÓN

### Para Sistema Inventario Retail Multi-Agente:
```bash
cd inventario-retail/
# Ejecutar PROMPT 1 con contexto de esta carpeta
# Ejecutar PROMPT 2-4 secuencialmente
```

### Para Business Intelligence Orchestrator:
```bash
cd business-intelligence-orchestrator-v3.1/
# Ejecutar PROMPT 1 con contexto de esta carpeta
# Ejecutar PROMPT 2-4 secuencialmente
```

### Para Sistema Retail Argentina:
```bash
cd retail-argentina-system/prompt8-final/
# Ejecutar PROMPT 1 con contexto de esta carpeta
# Ejecutar PROMPT 2-4 secuencialmente
```

## 📊 OUTPUTS REFINADOS RECOMENDADOS

Crear en cada proyecto con metodología forense:
- `ANALISIS_FORENSE_ADAPTATIVO.md` (PROMPT 1) - Con citas `archivo:línea`
- `PLAN_DESPLIEGUE_DINAMICO.md` (PROMPT 2) - Con justificaciones geoeconómicas
- `CONFIGURACIONES_AUTOCURATIVAS.md` (PROMPT 3) - Con mecanismos de autocorrección
- `TROUBLESHOOTING_PROACTIVO.md` (PROMPT 4) - Con correlaciones causales

## 🛡️ VALIDACIÓN DE CALIDAD

### ✅ Indicadores de Éxito:
- **Citas específicas**: Cada dato técnico tiene `archivo:línea-inicial–línea-final`
- **No invasivo**: Ningún prompt sugiere modificar código existente
- **Adaptativo**: Las recomendaciones se basan en el stack real detectado
- **Ejecutable**: Comandos copy-paste que funcionan sin modificación
- **Crítico**: Identifica riesgos y ambigüedades explícitamente

### ❌ Señales de Respuesta Deficiente:
- Recomendaciones genéricas sin evidencia del código
- Ausencia de citas específicas de archivos
- Sugerencias de modificar código (violación del modo pasivo)
- Comandos que no corresponden al stack detectado

## 🚨 NOTAS CRÍTICAS REFINADAS

- 🔥 **MODO FORENSE ESTRICTO**: Los prompts solo observan, nunca modifican
- 📝 **EVIDENCIA OBLIGATORIA**: Sin `archivo:línea`, la información no es válida
- 🛡️ **VALIDAR ANTES DE APLICAR**: Revisar todas las configuraciones en staging
- 🔄 **ACTUALIZACIÓN CONTINUA**: Re-ejecutar cuando el código cambie significativamente
- 💾 **VERSIONADO SINCRONIZADO**: Mantener documentación al día con el código