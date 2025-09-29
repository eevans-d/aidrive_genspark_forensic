# PROMPTS PARA GITHUB COPILOT PRO
## Análisis Completo para Despliegue de Sistemas Agénticos

---

## PROMPT 1: ANÁLISIS TÉCNICO DEL PROYECTO

```
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

---

## PROMPT 2: PLAN DE DESPLIEGUE PERSONALIZADO

```
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

---

## PROMPT 3: CONFIGURACIONES DE PRODUCCIÓN

```
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

---

## PROMPT 4: TROUBLESHOOTING Y MANTENIMIENTO

```
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

---

## INSTRUCCIONES DE USO

1. **Ejecuta los prompts en orden** (1→2→3→4) en cada repositorio
2. **Copia cada prompt completo** incluyendo los headers y estructura
3. **Pega en GitHub Copilot Pro** con el contexto del repositorio abierto
4. **Guarda la documentación generada** en archivos markdown separados
5. **Repite el proceso** para cada uno de tus 3-4 proyectos

## RESULTADO ESPERADO

Después de ejecutar los 4 prompts obtendrás:
- ✅ Análisis técnico completo
- ✅ Plan de deployment específico  
- ✅ Configuraciones production-ready
- ✅ Guía de mantenimiento completa
- ✅ Scripts automatizados
- ✅ Troubleshooting detallado

---

## PROYECTOS IDENTIFICADOS EN ESTE REPOSITORIO

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

## OUTPUTS RECOMENDADOS

Crear en cada proyecto:
- `ANALISIS_TECNICO_COPILOT.md` (PROMPT 1)
- `PLAN_DESPLIEGUE_COPILOT.md` (PROMPT 2)
- `CONFIGURACIONES_PRODUCCION_COPILOT.md` (PROMPT 3)
- `TROUBLESHOOTING_COPILOT.md` (PROMPT 4)

## NOTAS IMPORTANTES

- 🔥 **Ejecuta con repositorio abierto** en GitHub Copilot Pro
- 📝 **Adapta los prompts** según las necesidades específicas de cada proyecto
- 🛡️ **Revisa outputs** antes de aplicar configuraciones en producción
- 🔄 **Actualiza regularmente** cuando el código del proyecto cambie
- 💾 **Versionea la documentación** junto con el código del proyecto