# GUÍA PRÁCTICA: CÓMO USAR LOS PROMPTS DE GITHUB COPILOT PRO

## 🎯 OBJETIVO
Esta guía te muestra paso a paso cómo aplicar los 4 prompts de GitHub Copilot Pro para obtener documentación completa de despliegue para tus proyectos agénticos.

---

## 📋 PRERREQUISITOS

### 1. Acceso a GitHub Copilot Pro
- Suscripción activa a GitHub Copilot Pro
- Acceso al chat de Copilot en IDE o web

### 2. Repositorio con Contexto
- Tu proyecto debe estar abierto en GitHub Codespaces, VS Code, o similar
- Copilot debe tener acceso completo al código del repositorio
- Recomendado: tener archivos clave abiertos (README, requirements, etc.)

### 3. Tiempo Estimado
- **Por proyecto**: 45-60 minutos
- **PROMPT 1**: 10-15 minutos
- **PROMPT 2**: 15-20 minutos  
- **PROMPT 3**: 10-15 minutos
- **PROMPT 4**: 10-15 minutos

---

## 🚀 PROCESO PASO A PASO

### PASO 1: PREPARACIÓN DEL CONTEXTO

#### 1.1 Abrir el Proyecto
```bash
# En tu IDE, abrir la carpeta del proyecto específico
# Ejemplo para inventario-retail:
cd /ruta/a/tu/repo/inventario-retail
code .  # O tu editor favorito
```

#### 1.2 Archivos Clave a Tener Abiertos
```bash
# Asegúrate de tener estos archivos visibles en el editor:
- README.md
- requirements.txt (o package.json)
- docker-compose.yml (si existe)
- .env.example o .env.template
- Dockerfile (si existe)
- Archivo principal (main.py, app.js, etc.)
```

#### 1.3 Activar GitHub Copilot
- Abrir chat de Copilot (Ctrl+Shift+I o Cmd+Shift+I)
- Verificar que puede ver el contexto del proyecto

---

### PASO 2: EJECUTAR PROMPT 1 - ANÁLISIS TÉCNICO

#### 2.1 Copiar y Pegar PROMPT 1
```
Abre GitHub Copilot Chat y pega exactamente esto:

# ANÁLISIS TÉCNICO COMPLETO DEL PROYECTO

Analiza este repositorio y proporciona:

## 1. STACK TECNOLÓGICO
- Framework principal y versión exacta
- Dependencias críticas y sus versiones
- Base de datos utilizada (tipo y versión)
- APIs externas integradas
- Servicios de terceros conectados
- Librerías de IA/ML utilizadas

## 2. ARQUITECTURA DEL SISTEMA
- Estructura de carpetas clave
- Puntos de entrada principales (main files)
- Servicios y módulos core
- Integraciones agénticas específicas
- Patrones de arquitectura implementados

## 3. REQUISITOS DE DESPLIEGUE
- Variables de entorno necesarias (lista completa)
- Configuraciones de base de datos requeridas
- Puertos y servicios que debe exponer
- Recursos mínimos (RAM, CPU, storage)
- Certificados SSL o HTTPS necesarios

## 4. DEPENDENCIAS DE SISTEMA
- Versión específica de runtime (Node.js/Python/etc)
- Servicios del sistema operativo necesarios
- Herramientas de build requeridas
- Comandos de instalación global necesarios

## 5. CONFIGURACIÓN ACTUAL
- Archivos de configuración existentes
- Scripts de package.json/requirements.txt
- Variables de entorno ya definidas
- Configuraciones de desarrollo vs producción

Formato: Markdown estructurado con comandos específicos ejecutables.
```

#### 2.2 Espera la Respuesta Completa
- Copilot analizará todo el contexto del proyecto
- Generará un análisis técnico detallado
- **Tiempo aproximado**: 2-3 minutos

#### 2.3 Guardar el Output
```bash
# Crear archivo con la respuesta
touch ANALISIS_TECNICO_COPILOT.md
# Copiar toda la respuesta de Copilot al archivo
```

---

### PASO 3: EJECUTAR PROMPT 2 - PLAN DE DESPLIEGUE

#### 3.1 Copiar y Pegar PROMPT 2
```
En el mismo chat de Copilot, continúa con:

# PLAN DE DESPLIEGUE PERSONALIZADO

Basándote en el análisis anterior del repositorio, genera:

## 1. PREPARACIÓN PRE-DESPLIEGUE
- Checklist completo de verificación de código
- Configuraciones específicas para producción
- Variables de entorno para producción (con valores ejemplo)
- Scripts de build optimizados para deployment
- Archivos que deben ser excluidos (.gitignore, .dockerignore)

## 2. ESTRATEGIA DE HOSTING PARA ARGENTINA
- Recomendación específica de plataforma (Vercel, Railway, Render, Fly.io)
- Justificación técnica de la recomendación
- Configuración paso a paso para la plataforma elegida
- Costos estimados mensuales en USD
- Límites del plan gratuito y cuándo upgrader

## 3. PROCESO DE DESPLIEGUE DETALLADO
- Comandos git exactos para preparar el deploy
- Configuración de repositorio para auto-deploy
- Pasos manuales necesarios (si los hay)
- Configuración de dominio personalizado
- Setup de base de datos en producción

## 4. VERIFICACIÓN POST-DESPLIEGUE
- URLs y endpoints para testear
- Comandos para verificar que todo funciona
- Logs críticos a revisar
- Tests de funcionalidad básicos

## 5. ROLLBACK Y RECOVERY
- Cómo hacer rollback si algo falla
- Backup de configuraciones
- Recovery plan básico

Incluye comandos copy-paste ready y configuraciones exactas.
```

#### 3.2 Guardar el Output
```bash
touch PLAN_DESPLIEGUE_COPILOT.md
# Copiar respuesta al archivo
```

---

### PASO 4: EJECUTAR PROMPT 3 - CONFIGURACIONES

#### 4.1 Copiar y Pegar PROMPT 3
```
Continúa en el chat:

# CONFIGURACIONES DE PRODUCCIÓN ESPECÍFICAS

Genera configuraciones production-ready para este proyecto:

## 1. VARIABLES DE ENTORNO COMPLETAS
- Lista exhaustiva de todas las ENV vars necesarias
- Descripción de cada variable y su propósito
- Valores de ejemplo seguros (sin exponer secretos)
- Variables específicas por entorno (dev/staging/prod)
- Template de .env.production

## 2. CONFIGURACIÓN DE BASE DE DATOS
- Connection strings para producción
- Configuración de connection pooling
- Migrations necesarias para producción
- Seeds o data inicial requerida
- Configuración de backup automático

## 3. CONFIGURACIÓN DE SEGURIDAD
- CORS setup específico para este proyecto
- Rate limiting adecuado
- Validación de inputs implementada
- Headers de seguridad necesarios
- Configuración de autenticación/autorización

## 4. OPTIMIZACIÓN DE PERFORMANCE
- Configuración de caching apropiada
- Compression y minification setup
- Optimización de static assets
- CDN configuration (si es necesario)
- Database query optimization

## 5. ARCHIVOS DE CONFIGURACIÓN COMPLETOS
Genera el código completo para:
- Dockerfile (si aplica)
- docker-compose.yml (si aplica) 
- Archivo de configuración del servidor
- Scripts de package.json optimizados
- Configuración de CI/CD básica (.github/workflows)

## 6. CONFIGURACIÓN ESPECÍFICA DE IA/AGENTES
- Variables de entorno para APIs de IA
- Configuración de timeouts y rate limits
- Manejo de errores de APIs externas
- Configuración de fallbacks

Proporciona código funcional y completo para cada archivo.
```

#### 4.2 Guardar el Output
```bash
touch CONFIGURACIONES_PRODUCCION_COPILOT.md
# Copiar respuesta al archivo
```

---

### PASO 5: EJECUTAR PROMPT 4 - TROUBLESHOOTING

#### 5.1 Copiar y Pegar PROMPT 4
```
Finaliza con:

# GUÍA DE TROUBLESHOOTING Y MANTENIMIENTO

Crea documentación completa para:

## 1. PROBLEMAS COMUNES DE DESPLIEGUE
Para este proyecto específico, identifica:
- Top 5 errores más probables durante deployment
- Solución paso a paso para cada error
- Comandos específicos de diagnóstico
- Logs exactos a revisar y dónde encontrarlos
- Señales de alerta temprana

## 2. COMANDOS DE MANTENIMIENTO ESENCIALES
- Health checks específicos para este sistema
- Comandos para restart de servicios
- Update de dependencias seguro
- Limpieza de logs y archivos temporales
- Verificación de integridad de base de datos

## 3. MONITORING Y ALERTAS BÁSICAS
- Métricas críticas a monitorear para este proyecto
- Setup de logging estructurado
- Alertas simples con herramientas gratuitas
- Dashboard básico con métricas clave
- Thresholds de alerta recomendados

## 4. MANTENIMIENTO DE SISTEMAS AGÉNTICOS
- Monitoreo de APIs de IA utilizadas
- Verificación de quotas y rate limits
- Performance de modelos de IA
- Logs específicos de agentes
- Troubleshooting de timeouts de IA

## 5. ESCALABILIDAD Y OPTIMIZACIÓN
- Señales de que necesitas más recursos
- Cómo hacer upgrade de plan de hosting
- Optimizaciones de código para mejor performance
- Estrategias de caching para reducir costos de APIs
- Migration path para crecimiento

## 6. BACKUP Y RECOVERY AUTOMATIZADO
- Script de backup completo para este proyecto
- Procedimiento de restore paso a paso
- Backup de configuraciones y secretos
- Testing de recovery procedures
- Cronograma de backups recomendado

## 7. SCRIPTS DE AUTOMATIZACIÓN
Genera scripts ejecutables para:
- Deployment completo
- Health check automatizado
- Backup automático
- Update de dependencias
- Rollback rápido

Incluye código funcional y procedimientos step-by-step detallados.
```

#### 5.2 Guardar el Output
```bash
touch TROUBLESHOOTING_COPILOT.md
# Copiar respuesta al archivo
```

---

## 📁 ORGANIZACIÓN DE ARCHIVOS RESULTANTES

### Estructura Recomendada
```bash
tu-proyecto/
├── docs/                              # Crear si no existe
│   ├── deployment/                    # Nueva carpeta
│   │   ├── ANALISIS_TECNICO_COPILOT.md
│   │   ├── PLAN_DESPLIEGUE_COPILOT.md
│   │   ├── CONFIGURACIONES_PRODUCCION_COPILOT.md
│   │   └── TROUBLESHOOTING_COPILOT.md
│   └── ...otros docs existentes
├── .env.production.template           # Crear desde PROMPT 3
├── docker-compose.production.yml      # Crear desde PROMPT 3
└── scripts/                          # Crear si no existe
    ├── deploy.sh                     # Crear desde PROMPTs 2-3
    ├── health-check.sh               # Crear desde PROMPT 4
    └── backup.sh                     # Crear desde PROMPT 4
```

---

## 🔍 VALIDACIÓN DE RESULTADOS

### Checklist de Calidad
- [ ] **PROMPT 1**: ¿Identificó correctamente el stack tecnológico?
- [ ] **PROMPT 1**: ¿Listó todas las dependencias críticas?
- [ ] **PROMPT 2**: ¿Recomendó plataforma adecuada para Argentina?
- [ ] **PROMPT 2**: ¿Incluyó comandos copy-paste?
- [ ] **PROMPT 3**: ¿Generó archivos de configuración completos?
- [ ] **PROMPT 3**: ¿Incluyó configuraciones de seguridad?
- [ ] **PROMPT 4**: ¿Identificó problemas comunes específicos del proyecto?
- [ ] **PROMPT 4**: ¿Incluyó scripts ejecutables?

### Señales de Éxito
✅ **Buena respuesta**:
- Específica para tu proyecto
- Incluye comandos ejecutables
- Menciona tecnologías reales del código
- Proporciona configuraciones completas

❌ **Respuesta genérica**:
- Muy general, podría aplicar a cualquier proyecto
- Sin comandos específicos
- No menciona las tecnologías de tu stack
- Configuraciones incompletas

---

## 💡 CONSEJOS PARA MEJORES RESULTADOS

### 1. Contexto Rico
```bash
# Antes de usar los prompts, asegúrate de:
- Tener múltiples archivos del proyecto abiertos
- Incluir archivos de configuración (.env, docker, etc.)
- Mostrar la estructura de carpetas en el explorador
```

### 2. Conversación Continua
- Usa el mismo chat para los 4 prompts
- Copilot mantendrá el contexto entre prompts
- Puedes hacer preguntas de seguimiento

### 3. Personalización
```bash
# Adapta los prompts agregando:
"Este proyecto es para el mercado argentino y debe cumplir con AFIP"
"El sistema maneja datos sensibles bancarios"
"Debe funcionar 24/7 sin interrupciones"
```

### 4. Validación Cruzada
- Compara outputs con documentación existente
- Verifica que los comandos sean correctos
- Testea configuraciones en ambiente de prueba

---

## 🚨 PROBLEMAS COMUNES Y SOLUCIONES

### Problema 1: Respuesta Muy Genérica
**Síntoma**: Copilot da respuestas que podrían aplicar a cualquier proyecto

**Solución**:
```bash
# Añade más contexto específico:
"Para el proyecto que estás viendo, que es un sistema multi-agente 
de inventario retail con FastAPI, OCR de facturas AFIP, y ML..."
```

### Problema 2: Comandos Incorrectos
**Síntoma**: Los comandos generados no funcionan

**Solución**:
- Verifica que Copilot tenga acceso a archivos reales
- Pregunta específicamente: "¿Estos comandos son correctos para el proyecto actual?"

### Problema 3: Configuraciones Incompletas
**Síntoma**: Los archivos de configuración no incluyen todas las variables

**Solución**:
```bash
# Pregunta de seguimiento:
"¿Puedes revisar el código y asegurarte de que incluiste TODAS 
las variables de entorno que se usan en el proyecto?"
```

---

## 📊 MÉTRICAS DE ÉXITO

### Por Proyecto Completado
- ✅ 4 archivos de documentación generados
- ✅ Al menos 3 scripts ejecutables funcionando
- ✅ Configuraciones validadas en test
- ✅ Plan de despliegue paso a paso documentado

### Tiempo Ahorrado
- **Sin prompts**: 8-12 horas de documentación manual
- **Con prompts**: 1-2 horas de aplicación + validación
- **Ahorro**: ~80% del tiempo de documentación

---

Esta guía práctica te permitirá aplicar sistemáticamente los prompts a todos tus proyectos y obtener documentación de despliegue completa y profesional.