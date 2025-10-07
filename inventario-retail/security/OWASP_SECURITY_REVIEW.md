# 🔒 OWASP Security Review - Mini Market Sistema

**Fecha:** Octubre 7, 2025  
**Versión:** 1.0  
**Autor:** DevOps Team  
**Estado:** Análisis inicial  
**Alcance:** Sistema Mini Market v0.10.0  
**Referencias:** OWASP Top 10 - 2021

---

## 📊 RESUMEN EJECUTIVO

Este documento presenta los resultados de una revisión de seguridad del Sistema Mini Market basada en OWASP Top 10 (2021). El análisis cubre los 4 componentes principales: agente_deposito, agente_negocio, ml_service y web_dashboard.

### Hallazgos clave

| Categoría | Nivel de Riesgo | Componentes Afectados | Mitigación |
|-----------|-----------------|----------------------|------------|
| A01 - Broken Access Control | 🟠 ALTO | Dashboard, API | Requiere atención |
| A02 - Cryptographic Failures | 🟡 MEDIO | Auth, JWT | Parcialmente mitigado |
| A03 - Injection | 🟡 MEDIO | SQL, Templates | Parcialmente mitigado |
| A04 - Insecure Design | 🟢 BAJO | Arquitectura | Diseño adecuado |
| A05 - Security Misconfiguration | 🟠 ALTO | Docker, Endpoints | Requiere atención |
| A06 - Vulnerable Components | 🟢 BAJO | Dependencies | Mitigado con R6 |
| A07 - Auth Failures | 🟡 MEDIO | JWT, API Keys | Parcialmente mitigado |
| A08 - Software/Data Integrity | 🟡 MEDIO | CI/CD, Updates | Requiere atención |
| A09 - Logging/Monitoring | 🟢 BAJO | Observability | Implementado |
| A10 - SSRF | 🟢 BAJO | External requests | No aplica |

### Estadísticas de hallazgos

- **CRÍTICO:** 0 hallazgos (0%)
- **ALTO:** 2 hallazgos (20%)
- **MEDIO:** 4 hallazgos (40%)
- **BAJO:** 4 hallazgos (40%)

---

## A01: BROKEN ACCESS CONTROL

### 🟠 ALTO RIESGO

**Hallazgos:**

1. **Dashboard sin control de acceso granular**
   - Solo verificación de API key para todo el panel
   - Sin RBAC para diferentes niveles de usuario
   - Sin restricción de endpoints por roles

2. **API endpoints con permisos excesivos**
   - Todos los endpoints protegidos con la misma API key
   - Sin diferenciación entre operaciones de lectura/escritura
   - Sin validación del origen de la solicitud

3. **Falta de autorización basada en JWT**
   - Se valida autenticación (JWT válido) pero no autorización (permisos)
   - Usuarios con JWT válido tienen acceso completo a todos los recursos

**Recomendaciones:**

1. Implementar un sistema RBAC (Role-Based Access Control)
   ```python
   class RoleBasedAuth(BaseAuth):
       def verify_permissions(self, user_id, required_role):
           user_roles = self.get_user_roles(user_id)
           return required_role in user_roles
   ```

2. Separar API keys por nivel de acceso
   ```python
   # Ejemplo en FastAPI
   @app.get("/api/private/admin", dependencies=[Depends(admin_api_key_auth)])
   def admin_endpoint():
       return {"status": "admin only"}
   ```

3. Implementar middleware de verificación de permisos para todos los endpoints
   ```python
   @app.middleware("http")
   async def verify_permissions(request, call_next):
       token = request.headers.get("Authorization")
       endpoint = request.url.path
       if not permissions.has_access(token, endpoint):
           return JSONResponse(status_code=403, content={"detail": "Forbidden"})
       return await call_next(request)
   ```

---

## A02: CRYPTOGRAPHIC FAILURES

### 🟡 MEDIO RIESGO

**Hallazgos:**

1. **JWT implementación mejorada en ETAPA 2 (R2)**
   - ✅ Separación de JWT secrets por servicio: JWT_SECRET_DEPOSITO, JWT_SECRET_NEGOCIO, etc.
   - ✅ Incorporación de claim "iss" (issuer) para validación
   - ⚠️ Sin rotación automática de secretos (aún manual)

2. **Falta de cifrado en reposo para datos sensibles**
   - Passwords almacenados con hash pero sin salt
   - Configuraciones sensibles en archivos .env sin cifrar
   - Sin implementación de cifrado para datos sensibles en BD

3. **Sin HTTPS forzado en entorno local/desarrollo**
   - Comunicaciones en texto plano entre servicios
   - HTTPS configurado pero no forzado (redirect)

**Recomendaciones:**

1. Implementar rotación automática de JWT secrets
   ```python
   # Ejemplo de servicio de rotación
   def rotate_jwt_secrets():
       new_secrets = generate_secure_secrets()
       update_env_variables(new_secrets)
       notify_services_for_reload()
   ```

2. Mejorar el cifrado de datos sensibles
   ```python
   from cryptography.fernet import Fernet
   
   def encrypt_sensitive_data(data):
       key = get_encryption_key()
       cipher = Fernet(key)
       return cipher.encrypt(data.encode()).decode()
   ```

3. Forzar HTTPS en todos los entornos
   ```python
   # Middleware de redirect HTTP->HTTPS
   @app.middleware("http")
   async def https_redirect(request, call_next):
       if settings.FORCE_HTTPS and request.url.scheme == "http":
           url = request.url.replace(scheme="https")
           return RedirectResponse(url=str(url))
       return await call_next(request)
   ```

---

## A03: INJECTION

### 🟡 MEDIO RIESGO

**Hallazgos:**

1. **Uso de SQLAlchemy ORM reduce riesgo de SQL Injection**
   - ✅ La mayoría de consultas utilizan ORM con parámetros
   - ⚠️ Algunas consultas raw SQL en reportes de analytics
   - ⚠️ Conexión directa a PostgreSQL en agente_deposito/db.py

2. **Posible Template Injection en generación de reportes**
   - Sistema de templates para reportes usa string.format()
   - Entrada de usuario en nombres de reportes no sanitizada
   - Ejemplo: `report_template.format(**user_data)`

3. **Log Injection en líneas de registro**
   - Datos de usuario sin sanitizar en logs
   - Ejemplo: `logger.info(f"User {user_input} logged in")`

**Recomendaciones:**

1. Eliminar consultas SQL raw
   ```python
   # Reemplazar:
   result = conn.execute(f"SELECT * FROM products WHERE category='{category}'")
   
   # Por:
   result = session.query(Product).filter(Product.category == category).all()
   ```

2. Usar motores de template seguros
   ```python
   from jinja2 import Template, StrictUndefined
   
   template = Template(template_string, undefined=StrictUndefined)
   report = template.render(user_data=user_data)
   ```

3. Sanitizar entradas en logs
   ```python
   import re
   
   def sanitize_log(input_string):
       return re.sub(r'[\n\r\t]', '', str(input_string))
   
   logger.info(f"User {sanitize_log(user_input)} logged in")
   ```

---

## A04: INSECURE DESIGN

### 🟢 BAJO RIESGO

**Hallazgos:**

1. **Arquitectura de microservicios con buena segregación**
   - ✅ Separación clara entre agentes con responsabilidades específicas
   - ✅ Comunicación entre servicios con autenticación JWT
   - ✅ Principio de mínimo privilegio en conexiones a BD

2. **Rate limiting implementado en el Dashboard**
   - ✅ Protección contra abuso de API
   - ✅ Configurable mediante variables de entorno

3. **Validación de datos en APIs**
   - ✅ Uso de Pydantic para validación de schema
   - ✅ Error handling adecuado para datos inválidos

**Recomendaciones:**

1. Implementar circuit breakers para mejorar resiliencia
   ```python
   from pybreaker import CircuitBreaker
   
   service_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)
   
   @service_breaker
   def call_external_service():
       # Llamada al servicio externo
   ```

2. Extender rate limiting a todos los servicios
   ```python
   from fastapi import Depends, HTTPException
   from fastapi_limiter import FastAPILimiter
   from fastapi_limiter.depends import RateLimiter
   
   @app.get("/api/endpoint", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
   def rate_limited_endpoint():
       return {"message": "This endpoint is rate limited"}
   ```

3. Implementar dead letter queues para mensajes fallidos
   ```python
   def process_message(message):
       try:
           # Procesar mensaje
       except Exception as e:
           send_to_dead_letter_queue(message, str(e))
   ```

---

## A05: SECURITY MISCONFIGURATION

### 🟠 ALTO RIESGO

**Hallazgos:**

1. **Endpoints de métricas y health sin autenticación**
   - `/metrics` accesible sin autenticación
   - `/health` expone detalles de sistema
   - Potencial de fuga de información sensible

2. **Variables de entorno default inseguras**
   - Varios `DEFAULT_TO_EMPTY_STRING` en docker-compose
   - Sin validación de variables críticas al inicio
   - Sin secretos gestionados (todo en .env)

3. **Headers de seguridad incompletos**
   - Sin CSP (Content Security Policy)
   - Sin HSTS en entorno local
   - Sin X-Content-Type-Options

4. **Contenedores Docker sin hardening completo**
   - R1 mitigado (ejecución como non-root)
   - Sin límites de recursos (CPU/memory)
   - Sin read-only filesystems donde aplique

**Recomendaciones:**

1. Proteger endpoints de diagnóstico
   ```python
   @app.get("/metrics", dependencies=[Depends(api_key_auth)])
   def metrics():
       return generate_metrics()
   ```

2. Validación estricta de variables de entorno
   ```python
   def validate_env_vars():
       required_vars = ["JWT_SECRET_KEY", "POSTGRES_PASSWORD"]
       for var in required_vars:
           if not os.getenv(var):
               raise ValueError(f"Required environment variable {var} is not set")
   ```

3. Implementar headers de seguridad completos
   ```python
   @app.middleware("http")
   async def add_security_headers(request, call_next):
       response = await call_next(request)
       response.headers["Content-Security-Policy"] = "default-src 'self'"
       response.headers["X-Content-Type-Options"] = "nosniff"
       response.headers["X-Frame-Options"] = "DENY"
       if settings.ENABLE_HSTS:
           response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
       return response
   ```

4. Mejorar configuración de contenedores
   ```yaml
   services:
     dashboard:
       # ...
       read_only: true
       tmpfs:
         - /tmp
       security_opt:
         - no-new-privileges:true
       resources:
         limits:
           cpus: '0.50'
           memory: 512M
   ```

---

## A06: VULNERABLE COMPONENTS

### 🟢 BAJO RIESGO

**Hallazgos:**

1. **R6 ya mitigado en ETAPA 2**
   - ✅ Trivy scan en CI/CD con fail en vulnerabilidades CRITICAL/HIGH
   - ✅ Exclusión de vulnerabilidades sin fix (ignore-unfixed: true)
   - ✅ Previene dependencias vulnerables en producción

2. **requirements.txt con versiones fijas**
   - ✅ Todas las dependencias con versiones específicas
   - ✅ Sin uso de rangos (>=) que podrían introducir vulnerabilidades

3. **Imágenes base actualizadas**
   - ✅ python:3.11-slim como base para todos los servicios
   - ✅ Actualizaciones de sistema operativo incluidas en Dockerfiles

**Recomendaciones:**

1. Implementar análisis de dependencias regular
   ```bash
   # Añadir a CI/CD o cron
   safety check -r requirements.txt --full-report
   ```

2. Actualizar imágenes base periódicamente
   ```bash
   # Script de actualización
   docker pull python:3.11-slim
   docker-compose build --no-cache
   ```

3. Implementar Software Bill of Materials (SBOM)
   ```bash
   # Generar SBOM con Syft
   syft /app -o json > sbom.json
   ```

---

## A07: AUTHENTICATION FAILURES

### 🟡 MEDIO RIESGO

**Hallazgos:**

1. **Sistema de API Keys simple**
   - API Key única para todo el Dashboard
   - Sin expiración ni rotación automática
   - Sin distinción entre clientes

2. **JWT mejorado en ETAPA 2 (R2)**
   - ✅ Diferentes secretos por servicio
   - ⚠️ Sin validación de tiempo de expiración (exp claim)
   - ⚠️ Sin revocación de tokens

3. **Sin protección contra fuerza bruta**
   - No hay rate limiting específico en endpoints de auth
   - Sin bloqueo temporal tras intentos fallidos

**Recomendaciones:**

1. Implementar JWT completo con expiración
   ```python
   def create_token(data, service):
       expiry = datetime.utcnow() + timedelta(hours=1)
       payload = {
           **data,
           "exp": expiry,
           "iss": service,
           "jti": str(uuid.uuid4())
       }
       return jwt.encode(payload, get_secret_for_service(service), algorithm="HS256")
   ```

2. Sistema de API Keys avanzado
   ```python
   class APIKeyAuth:
       def __init__(self, role="default", expires_in_days=30):
           self.role = role
           self.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
           self.key_id = str(uuid.uuid4())
           self.api_key = self.generate_key()
       
       def generate_key(self):
           # Generar key segura
   ```

3. Protección contra fuerza bruta
   ```python
   login_limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/login")
   @login_limiter.limit("5/minute")
   def login():
       # Login logic
   ```

---

## A08: SOFTWARE AND DATA INTEGRITY FAILURES

### 🟡 MEDIO RIESGO

**Hallazgos:**

1. **Sin verificación de integridad en actualizaciones de ML**
   - Modelos de ML cargados sin verificación de checksum
   - Datos de entrenamiento sin validación de integridad

2. **CI/CD con GitHub Actions mejorado**
   - ✅ R6 implementado (Trivy scan)
   - ⚠️ Sin verificación de integridad de dependencias
   - ⚠️ Sin firma de imágenes Docker

3. **Actualizaciones de inflation rate sin logging de auditoría**
   - R4 implementado (externalización a env var)
   - Sin registro de quién cambió valores y cuándo

**Recomendaciones:**

1. Verificación de integridad para modelos ML
   ```python
   def load_model(model_path, expected_hash):
       actual_hash = compute_sha256(model_path)
       if actual_hash != expected_hash:
           raise IntegrityError(f"Model hash mismatch: {actual_hash} != {expected_hash}")
       return joblib.load(model_path)
   ```

2. Implementar firma de imágenes Docker
   ```yaml
   jobs:
     build:
       steps:
         - uses: actions/checkout@v3
         - name: Sign Docker image
           uses: sigstore/cosign-installer@main
         - run: cosign sign ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.build-push.outputs.digest }}
   ```

3. Auditoría de cambios críticos
   ```python
   def update_inflation_rate(new_rate, user_id):
       old_rate = get_current_inflation_rate()
       set_inflation_rate(new_rate)
       audit_log.info(
           f"Inflation rate changed from {old_rate} to {new_rate} by user {user_id} at {datetime.utcnow()}"
       )
   ```

---

## A09: SECURITY LOGGING AND MONITORING FAILURES

### 🟢 BAJO RIESGO

**Hallazgos:**

1. **Stack de observabilidad completo en ETAPA 3**
   - ✅ Prometheus para métricas
   - ✅ Loki para logs centralizados
   - ✅ Grafana para visualización
   - ✅ Alertmanager para notificaciones

2. **Logging implementado en todos los servicios**
   - ✅ Structured logging con JSON
   - ✅ Niveles de log configurables por entorno
   - ✅ request_id para correlación

3. **15 alerting rules configuradas**
   - ✅ Alertas para disponibilidad, performance, errores
   - ✅ Configuración de severidades (CRITICAL, HIGH, MEDIUM)
   - ✅ Notificaciones a Slack

**Recomendaciones:**

1. Añadir logging de eventos de seguridad
   ```python
   def log_security_event(event_type, user_id, details, severity="INFO"):
       security_logger.log(
           level=severity,
           msg={
               "event_type": event_type,
               "user_id": user_id,
               "details": details,
               "timestamp": datetime.utcnow().isoformat()
           }
       )
   ```

2. Implementar alertas específicas de seguridad
   ```yaml
   - alert: BruteForceAttempt
     expr: rate(failed_login_attempts_total[5m]) > 10
     for: 1m
     labels:
       severity: critical
     annotations:
       summary: "Possible brute force attack"
       description: "High rate of failed login attempts detected"
   ```

3. Logging de eventos de auditoría
   ```python
   class AuditMiddleware:
       async def __call__(self, request, call_next):
           start_time = time.time()
           response = await call_next(request)
           
           audit_logger.info({
               "method": request.method,
               "path": request.url.path,
               "status_code": response.status_code,
               "user_id": request.state.user_id if hasattr(request.state, "user_id") else None,
               "duration_ms": (time.time() - start_time) * 1000
           })
           
           return response
   ```

---

## A10: SERVER SIDE REQUEST FORGERY (SSRF)

### 🟢 BAJO RIESGO

**Hallazgos:**

1. **Uso limitado de solicitudes externas**
   - Sistema principalmente interno sin llamadas externas
   - Excepción: webhook para notificaciones Slack

2. **Sin entrada de usuario para URLs**
   - No hay endpoints que procesen URLs proporcionadas por usuarios
   - No hay riesgo directo de SSRF

**Recomendaciones:**

1. Validación de URLs para futuros desarrollos
   ```python
   def is_url_safe(url):
       parsed_url = urlparse(url)
       if parsed_url.hostname in ["localhost", "127.0.0.1"] or parsed_url.hostname.startswith("192.168."):
           return False
       return True
   ```

2. Implementar listas blancas para conexiones externas
   ```python
   ALLOWED_EXTERNAL_HOSTS = ["api.slack.com", "hooks.slack.com"]
   
   def validate_external_request(url):
       parsed_url = urlparse(url)
       if parsed_url.hostname not in ALLOWED_EXTERNAL_HOSTS:
           raise SecurityException(f"Host not allowed: {parsed_url.hostname}")
   ```

3. Proxying seguro para solicitudes externas
   ```python
   def safe_external_request(url, method="GET", data=None):
       validate_external_request(url)
       return requests.request(method, url, data=data, timeout=10)
   ```

---

## 📋 PLAN DE REMEDIACIÓN

### Prioridad Alta (Próximos 30 días)

1. **A01 - Broken Access Control**
   - Implementar RBAC para Dashboard y API
   - Separar API keys por nivel de acceso

2. **A05 - Security Misconfiguration**
   - Proteger endpoints de métricas y health
   - Implementar headers de seguridad completos
   - Mejorar configuración de contenedores

### Prioridad Media (Próximos 60 días)

1. **A02 - Cryptographic Failures**
   - Implementar rotación automática de JWT secrets
   - Mejorar el cifrado de datos sensibles

2. **A03 - Injection**
   - Eliminar consultas SQL raw
   - Implementar sanitización de inputs en logs

3. **A07 - Authentication Failures**
   - Implementar JWT completo con expiración
   - Añadir protección contra fuerza bruta

4. **A08 - Software/Data Integrity**
   - Verificación de integridad para modelos ML
   - Auditoría de cambios críticos

### Prioridad Baja (Backlog)

1. **A04 - Insecure Design**
   - Implementar circuit breakers
   - Extender rate limiting a todos los servicios

2. **A09 - Security Logging**
   - Añadir logging de eventos de seguridad
   - Implementar alertas específicas de seguridad

3. **A10 - SSRF**
   - Preparar validaciones para futuros desarrollos

---

## 🔄 SEGUIMIENTO

Este documento se revisará y actualizará mensualmente como parte del ciclo de mejora continua de seguridad. Las remediaciones implementadas se documentarán y validarán con pruebas adecuadas.

**Próxima revisión:** Noviembre 7, 2025

---

*Documento generado por DevOps Security Team como parte de ETAPA 3 - Fase 1 (T1.3.1)*