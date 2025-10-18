# REVISIÓN DETALLADA: TEMPLATES DE IMPLEMENTACIÓN

**Fecha:** October 18, 2025  
**Documento:** Explicación arquitectónica de OPCIÓN C templates  
**Propósito:** Entender cómo funcionan los 3 módulos resilience

---

## 📋 ÍNDICE DE TEMPLATES

```
1. circuit_breakers.py         (~350 líneas) - Patrón Circuit Breaker
2. degradation_manager.py      (~400 líneas) - Sistema de Degradación
3. fallbacks.py                (~350 líneas) - Estrategias de Fallback
```

---

## 1️⃣ CIRCUIT_BREAKERS.PY - PATRÓN CIRCUIT BREAKER

### 🎯 Propósito

Prevenir **cascading failures** (fallos en cascada) cuando servicios externos no responden.

### ⚙️ Cómo Funciona

```python
# PROBLEMA SIN CIRCUIT BREAKER:
OpenAI API cae → Agente intenta reintentar
→ Cientos de llamadas fallidas → Timeout
→ Usuario espera 30s
→ Los reintentos sobrecargan el servicio caído
→ TODO el sistema se ralentiza

# CON CIRCUIT BREAKER:
OpenAI API cae → CircuitBreaker detecta 5 fallos
→ ABRE el circuito (trip)
→ Retorna fallback INMEDIATAMENTE (sin esperar)
→ Ahorra conexiones y mejora UX
→ Después de 60s intenta half-open (prueba reconexión)
```

### 📊 Estados del Circuit Breaker

```
CLOSED (normal)
  ↓ (5 fallos = trigger)
OPEN (falla detectada)
  ↓ (espera 60 segundos)
HALF-OPEN (prueba reconexión)
  ↓ (éxito = vuelve a CLOSED)
  ↓ (fallo = vuelve a OPEN)
```

### 🔧 Configuración de Breakers

```python
# OPENAI BREAKER:
CircuitBreaker(fail_max=5, timeout_duration=60)
└─ Se abre después de 5 fallos
└─ Intenta reconectar después de 60 segundos

# DATABASE BREAKER:
CircuitBreaker(fail_max=3, timeout_duration=30)
└─ Más sensible (3 fallos = abre)
└─ Recovery más rápido (30 segundos)

# REDIS BREAKER:
CircuitBreaker(fail_max=5, timeout_duration=20)
└─ Menos crítico que DB
└─ Recovery más rápido (cache es reemplazable)

# S3 BREAKER:
CircuitBreaker(fail_max=5, timeout_duration=30)
└─ Uploads se pueden diferir
└─ Configuración moderada
```

### 📈 Prometheus Metrics Incluidas

```python
circuit_breaker_state         # 0=closed, 1=open, 2=half-open
circuit_breaker_failures_total    # Contador de fallos
circuit_breaker_fallback_calls_total  # Cuántas veces se usó fallback
```

**Visualización Grafana:**
```
Dashboard: Circuit Breakers Status
├─ Gauge: Estado actual de cada breaker
├─ Graph: Timeline de aperturas
└─ Counter: Cantidad de fallos y fallbacks
```

### 💡 Ejemplo de Uso

```python
# EN AGENTE_NEGOCIO/SERVICES/OPENAI_SERVICE.PY:

from shared.circuit_breakers import openai_breaker

@openai_breaker
async def enhance_prices_with_ai(prices: List[float]) -> Dict:
    """
    Si OpenAI está caído:
    - CircuitBreaker lo detecta rápidamente
    - Retorna precio enhancePROMPT sin esperar
    - Usuario obtiene precio base (malo pero rápido)
    """
    # Llamada a OpenAI
    response = await openai.ChatCompletion.create(...)
    return response

# CUANDO SE EJECUTA:
try:
    result = enhance_prices_with_ai([100, 200, 300])
except CircuitBreakerListener:
    # El circuit está OPEN
    # Se ejecuta el fallback automáticamente
    result = openai_fallback([100, 200, 300])
```

---

## 2️⃣ DEGRADATION_MANAGER.PY - GRACEFUL DEGRADATION

### 🎯 Propósito

Mantener el sistema operativo pero con **funcionalidad reducida** cuando fallan componentes.

### 5️⃣ Niveles de Degradación

```
NIVEL 1 (OPTIMAL)
├─ Estado: Todos servicios up
├─ Funcionalidad: 100%
├─ Ejemplo: OpenAI ✓, DB ✓, Redis ✓
└─ UX: Perfecta

NIVEL 2 (DEGRADED)
├─ Estado: Redis caído
├─ Funcionalidad: 85% (sin cache)
├─ Reducción: Más lento (DB directo)
└─ UX: Aceptable

NIVEL 3 (LIMITED)
├─ Estado: OpenAI + Redis caídos
├─ Funcionalidad: 60% (sin IA features)
├─ Ejemplo: Pricing sin enhancement
└─ UX: Limitada pero útil

NIVEL 4 (MINIMAL)
├─ Estado: DB con conexiones limitadas
├─ Funcionalidad: 30% (solo lectura)
├─ Escrituras: Bloqueadas
└─ UX: Solo visualización

NIVEL 5 (EMERGENCY)
├─ Estado: Múltiples fallos críticos
├─ Funcionalidad: 10% (solo status page)
├─ Sistema: Prácticamente no funciona
└─ UX: "Sistema en mantenimiento"
```

### 🔄 Cómo Funciona el Auto-Recovery

```python
# Loop cada 30 segundos:

def auto_recovery_loop():
    while True:
        sleep(30)
        
        # Evaluar salud de cada componente
        redis_ok = check_redis()
        db_ok = check_database()
        openai_ok = check_openai()
        
        # Calcular nivel necesario
        new_level = evaluate_health(redis_ok, db_ok, openai_ok)
        
        # Si mejora, pasar a nivel superior
        if new_level < current_level:
            # Recuperación detectada
            set_level(new_level)
            logger.info(f"Recovery: {current_level} → {new_level}")
```

### 📊 Transiciones de Estados

```
Si Redis vuelve ONLINE:
  DEGRADED (nivel 2) → auto-detección (30s)
  → Vuelve a OPTIMAL (nivel 1)

Si OpenAI vuelve ONLINE pero Redis sigue caído:
  LIMITED (nivel 3) → DEGRADED (nivel 2)

Si TODO cae:
  Cae automáticamente a MINIMAL o EMERGENCY
```

### 💻 Integración con FastAPI

```python
# EN AGENTE_NEGOCIO/APP.PY:

from shared.degradation_manager import degradation_manager, DegradationLevel

@app.on_event("startup")
async def startup():
    # Inicia auto-recovery loop
    await degradation_manager.start_auto_recovery()

@app.get("/prices/{product_id}")
async def get_prices(product_id: int):
    level = degradation_manager.current_level
    
    if level == DegradationLevel.OPTIMAL:
        # Usar todas las features
        return full_response()
    elif level == DegradationLevel.DEGRADED:
        # Usar menos cache
        return cached_response()
    elif level == DegradationLevel.LIMITED:
        # Sin OpenAI enhancements
        return basic_response()
    elif level == DegradationLevel.EMERGENCY:
        # Solo status
        return {"status": "system_degraded"}
```

### 🎛️ Control Manual (si es necesario)

```python
from shared.degradation_manager import degradation_manager, DegradationLevel

# Forzar nivel (por ej., durante mantenimiento)
degradation_manager.set_level(DegradationLevel.MINIMAL)

# Ver estado actual
print(degradation_manager.current_level)  # Enum value
print(degradation_manager.current_level.name)  # "MINIMAL"

# Recuperar automáticamente cuando se arregle
# (auto_recovery_loop lo detectará en 30s)
```

---

## 3️⃣ FALLBACKS.PY - ESTRATEGIAS DE FALLBACK

### 🎯 Propósito

Definir qué retornar cuando un servicio está caído.

### 🎁 Fallbacks Incluidos

#### OpenAI Fallbacks

```python
def openai_fallback():
    """Cuando OpenAI está caído"""
    return {
        "enhancement": "unavailable",
        "message": "AI enhancement temporarily unavailable",
        "fallback": "Using baseline pricing"
    }

def openai_ocr_enhancement_fallback():
    """Cuando OCR enhancement está caído"""
    return {
        "ocr_enhanced": False,
        "raw_text": extracted_raw_text,
        "message": "OCR enhancement unavailable - returning raw extraction"
    }

def openai_pricing_fallback(original_price):
    """Cuando pricing enhancement cae, usa fórmula básica"""
    # En lugar de usar IA: markup del 30%
    return original_price * 1.3
```

#### Database Fallbacks

```python
def db_read_fallback(product_id):
    """Intenta leer desde cache, sino error"""
    cached = redis.get(f"product:{product_id}")
    if cached:
        return json.loads(cached)
    return {"error": "Product unavailable - DB down"}

def db_write_fallback(data):
    """Bloquea escrituras cuando DB está caído"""
    return {
        "error": "Write operations unavailable",
        "message": "Database temporarily down",
        "action": "Try again later"
    }
```

#### Redis Fallbacks

```python
def cache_read_fallback(key):
    """Si Redis cae, fetch desde DB directamente"""
    # Query DB en lugar de cache
    return db.query(f"SELECT * WHERE key = {key}")
```

#### S3 Fallbacks

```python
def s3_upload_fallback(file_data):
    """Si S3 cae, guarda localmente y reintenta después"""
    # Guardar en local queue para retry
    local_queue.append({
        "file": file_data,
        "timestamp": now(),
        "retry_count": 0
    })
    return {
        "status": "queued",
        "message": "Upload queued - will retry when S3 is available"
    }
```

### 🔧 FallbackFactory

```python
from shared.fallbacks import FallbackFactory

# Crear fallback genérico
fb = FallbackFactory.create_generic_fallback(
    service_name="external_api",
    default_value={"status": "unavailable"}
)

# Usar en decorador
@with_fallback(fb)
def external_api_call():
    pass
```

---

## 🔗 CÓMO SE INTEGRAN LOS 3 MÓDULOS

```
REQUEST LLEGA A ENDPOINT
  ↓
┌─────────────────────────────────────────┐
│ ¿Circuit Breaker está OPEN?             │
└──────────┬────────────────────┬─────────┘
           NO                   SÍ
           ↓                    ↓
      Llamar OpenAI        circuit_breaker_listener
           ↓                    ↓
      Éxito? SÍ             Retornar FALLBACK
           ↓                 inmediatamente
      ✓ Response               ↓
      ✓ Update metrics    (sin esperar)
      ✓ Reset breaker
           ↓
┌─────────────────────────────────────────┐
│ Evaluar Degradation Level               │
└──────────┬────────────────────┬─────────┘
     Si hay cambios        No
           ↓                 ↓
    Auto-recovery      Continuar
    (en 30s)           con nivel actual
           ↓                 ↓
    Prometheus         Return Response
    Metrics Updated     con features según
                        degradation level
```

---

## 📊 TABLA COMPARATIVA DE CONFIGURACIÓN

| Aspecto | OpenAI | DB | Redis | S3 |
|---------|--------|----|----- |-----|
| **fail_max** | 5 fallos | 3 fallos | 5 fallos | 5 fallos |
| **timeout** | 60s | 30s | 20s | 30s |
| **Criticidad** | ALTA | CRÍTICA | MEDIA | BAJA |
| **Recovery esperado** | Lento | Rápido | Muy rápido | Rápido |
| **Fallback** | API alt o basemap | Cache o error | DB directo | Queue local |

---

## 🎓 CONCEPTOS CLAVE

### Circuit Breaker vs Fallback
```
CIRCUIT BREAKER: Previene llamadas cuando está caído
FALLBACK: Define qué hacer cuando está caído

Analogía: 
- Circuit Breaker = Breaker eléctrico (corta el circuito)
- Fallback = Generador de respaldo (proporciona energía alternativa)
```

### Graceful Degradation vs Circuit Breaker
```
CIRCUIT BREAKER: Protege contra fallos
GRACEFUL DEGRADATION: Continúa funcionando con menos features

Analogía:
- Circuit Breaker = Airbag (reacción inmediata)
- Graceful Degradation = Dirección asistida caída (sigue funcionando)
```

### Prometheus Metrics
```
- Para DEBUGGING: Ver cuándo falla cada servicio
- Para ALERTING: Crear alertas cuando circuit abre
- Para TRENDING: Analizar patrones de fallos
```

---

## ⚙️ PARÁMETROS AJUSTABLES

### Según Criticidad del Servicio

```python
# CRÍTICO (DB):
fail_max=3           # Rápido para detectar
timeout_duration=30  # Recovery pronto

# IMPORTANTE (OpenAI):
fail_max=5           # Menos sensible
timeout_duration=60  # Tiempo para recuperación

# OPCIONAL (Redis):
fail_max=5           # Puede fallar más
timeout_duration=20  # Cache es reemplazable
```

### Según Ambiente

```
PRODUCTION:
- Stricter (fail_max más bajo)
- Timeouts más largos (esperar más antes de asumir caído)

STAGING:
- Más permisivo
- Timeouts más cortos (detectar rápido)

DEVELOPMENT:
- Muy permisivo
- Circuit breakers posiblemente desactivados
```

---

## 🧪 TESTING STRATEGY

```python
# Unit Tests
test_circuit_breaker_opens_on_failures()
test_circuit_breaker_half_open_after_timeout()

# Integration Tests
test_degradation_cascade()  # Si A falla → B degrada
test_auto_recovery()        # Cuando A se recupera

# Load Tests
test_circuit_breaker_under_high_load()
test_fallback_performance()

# Chaos Tests (POST-LAUNCH)
test_multiple_simultaneous_failures()
test_partial_recovery_scenarios()
```

---

## 📈 MONITOREO EN PRODUCTION

### Dashboards Necesarios

```
1. Circuit Breaker Status
   ├─ Gauge: Estado de cada breaker
   ├─ Counter: Fallos detectados
   └─ Heatmap: Momentos de apertura

2. Degradation Levels
   ├─ Timeline: Transiciones de niveles
   ├─ Duration: Cuánto tiempo en cada nivel
   └─ Impact: Requests affected

3. Fallback Usage
   ├─ Counter: Cuántas veces se ejecutó cada fallback
   ├─ Latency: Diferencia (fallback vs normal)
   └─ User Impact: Degradación de UX
```

### Alertas Recomendadas

```
🔴 CRÍTICA:
- Circuit Breaker abierto > 5 minutos

🟠 ADVERTENCIA:
- Degradation Level > 2 (LIMITED)
- Fallback calls > 10% de requests

🟡 INFO:
- Circuit Breaker aperturas/cierres
- Transiciones de degradation level
```

---

## 🚀 IMPLEMENTACIÓN ROADMAP (DÍA 1-5)

**DÍA 1:** Circuit breakers (OpenAI + DB)  
**DÍA 2:** Redis + S3 breakers + Integration  
**DÍA 3-5:** Degradation manager + Testing  

---

## 📚 REFERENCIAS

- Martin Fowler - Circuit Breaker Pattern: https://martinfowler.com/bliki/CircuitBreaker.html
- PyBreaker Documentation: https://github.com/danielfm/pybreaker
- Graceful Degradation: https://en.wikipedia.org/wiki/Fault_tolerance

---

*Documento: Revisión de Templates - OPCIÓN C Implementation*  
*Última actualización: October 18, 2025*  
*Estado: Listo para implementación (DÍA 1)*
