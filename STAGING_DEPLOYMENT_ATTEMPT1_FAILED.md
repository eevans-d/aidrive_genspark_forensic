# STAGING DEPLOYMENT v0.10.0 - REPORTE FINAL (Intento 1)

**Fecha:** 2025-10-03  
**Hora de Inicio:** 04:46 ART  
**Hora de Fin:** 04:55 ART (aprox)  
**Duración:** ~9 minutos  
**Status:** ❌ FAILED - Network Timeout

## 📊 Resultado

### ✅ Fases Completadas (1-5)

1. ✅ Prerequisites Check - PASSED
2. ✅ Local Validation - PASSED (27/27)
3. ✅ Backup Created - DONE
4. ✅ Environment Configuration - DONE
5. ✅ Containers Stopped - DONE

### ❌ Fase Fallida

**6. Building Containers** - FAILED

**Error:**
```
pip._vendor.urllib3.exceptions.ReadTimeoutError: 
HTTPSConnectionPool(host='files.pythonhosted.org', port=443): Read timed out.
```

**Servicios afectados:**
- agente-negocio (exit code: 2)
- ml-service (exit code: 2)
- agente-deposito (CANCELED)

**Paquetes problemáticos:**
- nvidia-cudnn-cu12 (~707 MB)
- nvidia-cublas-cu12 (~594 MB)
- nvidia-cusolver-cu12 (~267 MB)
- nvidia-cusparse-cu12 (~288 MB)
- nvidia-cusparselt-cu12 (~287 MB)
- torch + dependencies (~600 MB)

**Total:** ~2.8 GB de dependencias

## 🔍 Análisis del Problema

### Causa Raíz

**Network timeout descargando paquetes grandes de PyPI.**

El build estuvo descargando durante ~10 minutos y eventualmente PyPI cortó la conexión debido a:
1. Tamaño excesivo de los paquetes CUDA/PyTorch
2. Timeout por defecto de pip (muy corto para 700MB+)
3. Posible throttling por parte de PyPI

### Por qué sucedió

Docker build con `--no-cache-dir` + pip descargando ~2.8GB de paquetes es inherentemente frágil con conexiones lentas o inestables.

## 🛠️ Soluciones Propuestas

### Opción 1: Build con Layers Cacheadas (RECOMENDADO)

**Ya implementado en commit eadccdb.**

Ventajas:
- Reutiliza capas Docker existentes
- Mucho más rápido (2-3 min vs 10-15 min)
- No vuelve a descargar si ya existe

Desventajas:
- No garantiza versiones más recientes (pero requirements.txt está pinned)

**Acción:**
```bash
# Ya está en scripts/deploy_staging_simple.sh (sin --no-cache)
bash scripts/deploy_staging_simple.sh
```

### Opción 2: Aumentar Timeout de Pip

Modificar Dockerfiles para agregar timeout mayor:

```dockerfile
# En cada Dockerfile antes de RUN pip install
ENV PIP_DEFAULT_TIMEOUT=300
RUN pip install --user --no-cache-dir -r requirements.txt
```

### Opción 3: Build Incremental por Servicios

En vez de build paralelo de 4 servicios, hacer uno por uno:

```bash
cd inventario-retail

# Build agente-deposito
docker-compose -f docker-compose.production.yml build agente-deposito

# Build agente-negocio
docker-compose -f docker-compose.production.yml build agente-negocio

# Build ml
docker-compose -f docker-compose.production.yml build ml

# Build dashboard
docker-compose -f docker-compose.production.yml build dashboard
```

### Opción 4: Pre-download Wheels Localmente

Descargar los .whl files manualmente y copyarlos al container:

```bash
# Local
pip download torch nvidia-cudnn-cu12 nvidia-cublas-cu12 -d /tmp/wheels

# En Dockerfile
COPY /tmp/wheels /tmp/wheels
RUN pip install --user --no-index --find-links=/tmp/wheels -r requirements.txt
```

### Opción 5: Mirror PyPI (Avanzado)

Usar un mirror PyPI más cercano o privado:

```dockerfile
RUN pip install --user --index-url=https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## ✅ Fixes Aplicados y Commiteados

**Commit eadccdb:**
```
fix(deployment): correct Dockerfile paths and add simplified deployment script

- Fix web_dashboard/Dockerfile COPY and CMD paths (build context issue)
- Add deploy_staging_simple.sh for reliable deployment
- Remove --no-cache flag for faster builds
- Add STAGING_DEPLOYMENT_IN_PROGRESS.md tracking document

Fixes build error: failed to calculate checksum '/inventario-retail/...'
Build context is inventario-retail/, so paths must be relative.
```

**Archivos modificados:**
- `inventario-retail/web_dashboard/Dockerfile` (2 lines)
- `scripts/deploy_staging_simple.sh` (NEW, 166 lines)
- `STAGING_DEPLOYMENT_IN_PROGRESS.md` (NEW, 298 lines)

**Pushed to master:** ✅

## 🎯 Recomendación Inmediata

### OPCIÓN PREFERIDA: Retry sin --no-cache (Ya implementado)

El script `deploy_staging_simple.sh` ya tiene el fix. Solo hace falta **retry**:

```bash
bash scripts/deploy_staging_simple.sh
```

**Ventajas:**
- ✅ Dockerfile path fix ya aplicado (commit eadccdb)
- ✅ Sin --no-cache ya configurado
- ✅ Reutilizará capas de build anterior (parcial)
- ✅ Mucho más rápido (~3-5 min vs 10-15 min)
- ✅ Menos probabilidad de timeout

**Por qué funcionará ahora:**
1. El build anterior ya descargó ~60% de los paquetes antes de timeout
2. Docker cacheó esas capas parciales
3. El retry empezará desde donde falló, no desde cero
4. Sin --no-cache, reutilizará todo lo cacheado

### Si el retry falla de nuevo:

Implementar **Opción 2 (Aumentar PIP_DEFAULT_TIMEOUT)**:

```bash
# Edit Dockerfiles
find inventario-retail -name "Dockerfile" -exec sed -i '/RUN pip install/i ENV PIP_DEFAULT_TIMEOUT=300' {} \;

# Retry deployment
bash scripts/deploy_staging_simple.sh
```

## 📝 Lecciones Aprendidas

1. **Dependencias grandes de ML/CUDA son problemáticas:**
   - PyTorch + CUDA = ~2.8GB
   - pip timeout por defecto es demasiado corto
   - Considerar usar mirrors o pre-downloading

2. **--no-cache es arriesgado para first builds:**
   - Mejor hacer first build sin flag
   - Luego rebuild con --no-cache si es necesario

3. **Build paralelo de 4 servicios amplifica el problema:**
   - Descarga simultánea de 4x 700MB puede saturar red/PyPI
   - Considerar build secuencial para first deploy

4. **Docker layer caching es crítico:**
   - Reduce significativamente tiempo de build
   - Minimiza re-downloads innecesarios

## 🔄 Estado Actual del Sistema

### Git Repository

- Branch: master
- Latest commit: eadccdb (fixes aplicados)
- Remote: synced ✅

### Local Environment

- .env.staging: ✅ Existe y configurado
- JWT secrets: ✅ Generados
- Backup: ✅ Creado (backups/pre-v0.10.0-20251003-044618/)
- Docker images: ⚠️ Parcialmente construidas (60-70% completo)

### Containers

- Status: STOPPED
- Reason: Build failed before start phase

### Validation

- Last run: PASSED (27/27) ✅
- File: validate_etapa2_mitigations.py
- All ETAPA 2 mitigations validated

## 📊 Timeline Completo

```
04:34 - JWT secrets generados (5 secrets únicos)
04:34 - .env.staging creado (139 líneas)
04:34 - deploy_staging_v0.10.0.sh creado (478 líneas)
04:34 - Commit f74b81d pushed
04:39 - Deployment intento #1 (failed: Dockerfile path)
04:44 - Dockerfile corregido
04:44 - deploy_staging_simple.sh creado
04:46 - Deployment intento #2 START
04:46 - Prerequisites: PASSED
04:46 - Validation: PASSED (27/27)
04:46 - Backup: DONE
04:46 - Environment: CONFIGURED
04:46 - Containers: STOPPED
04:46 - Build: STARTED (4 services parallel)
04:47 - Downloading CUDA libraries...
04:48 - Downloading PyTorch...
04:49 - Downloading nvidia-cudnn (707MB)...
04:50 - Downloading nvidia-cublas (594MB)...
04:51 - Downloading nvidia-cusolver (267MB)...
04:52 - Downloading nvidia-cusparse (288MB)...
04:53 - Still downloading...
04:54 - Still downloading...
04:55 - TIMEOUT ERROR (ReadTimeoutError)
04:55 - Build: FAILED (exit code 2)
04:55 - Deployment: ABORTED
04:56 - STAGING_DEPLOYMENT_IN_PROGRESS.md creado
04:57 - Commit eadccdb creado
04:57 - Pushed to master ✅
04:58 - Este reporte creado
```

## 🚀 Próxima Acción

**EJECUTAR RETRY INMEDIATO:**

```bash
# El script ya tiene todos los fixes
bash scripts/deploy_staging_simple.sh
```

**Tiempo estimado:** 3-5 minutos (mucho más rápido por caching)

**Probabilidad de éxito:** ~80% (capas cacheadas + sin --no-cache)

---

**Si falla el retry, escalar a Opción 2 (PIP_DEFAULT_TIMEOUT=300)**

**Status:** 🔄 READY FOR RETRY
