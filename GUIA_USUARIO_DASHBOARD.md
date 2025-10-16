# 📊 Guía de Usuario - Dashboard Mini Market

**Versión:** 1.0.0 (ETAPA 3)  
**Última actualización:** 16 de octubre de 2025  
**Audience:** Usuarios operacionales, gerentes de tienda, administradores

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Acceso y Autenticación](#acceso-y-autenticación)
3. [Páginas Principales](#páginas-principales)
4. [Filtros y Búsqueda](#filtros-y-búsqueda)
5. [Exportación de Datos](#exportación-de-datos)
6. [Métricas Clave Explicadas](#métricas-clave-explicadas)
7. [FAQ - Preguntas Frecuentes](#faq---preguntas-frecuentes)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Introducción

El **Dashboard Mini Market** es una herramienta centralizada para monitorear:
- Inventario en tiempo real
- Rendimiento de proveedores
- Análisis de ventas y tendencias
- Alertas de incidentes operacionales

**Objetivo Principal:** Facilitar toma de decisiones rápidas basada en datos actualizados.

---

## 🔐 Acceso y Autenticación

### Acceso al Dashboard

1. Abrir en navegador: `http://minimarket.local:8080`
2. El dashboard es **público** (sin login requerido)
3. Las APIs internas requieren **API Key** (header `X-API-Key`)

### API Key para Consultas Avanzadas

Si necesitas acceder a APIs directamente (para integraciones):

```bash
# Formato de request con API Key
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  http://localhost:8080/api/inventory

# Errores comunes:
# 401 → API Key falta o es incorrecta
# 403 → API Key válida pero acceso denegado
```

---

## 📄 Páginas Principales

### 1. **Inicio (Home / Dashboard)**

**URL:** `/`

**Componentes:**

| Sección | Descripción |
|---------|-------------|
| **KPIs Principales** | 4 tarjetas con métricas críticas (total de SKUs, valor inventario, productos bajo stock, tasa error sistema) |
| **Gráfico de Tendencias** | Línea de tiempo de últimas 30 días de inventario |
| **Alertas Recientes** | Listado de últimas 5 alertas con status y timestamp |
| **Proveedores Top 5** | Tabla con mejores proveedores por performance |

**Acciones disponibles:**
- Click en cualquier KPI → Ir a detalles
- Click en alerta → Ver runbook de resolución
- Click en proveedor → Ir a página de proveedores con filtro

### 2. **Proveedores**

**URL:** `/providers`

**Descripción:** Análisis detallado de performance de cada proveedor

**Columnas:**

| Columna | Descripción |
|---------|-------------|
| Proveedor | Nombre del proveedor |
| SKUs Activos | Cantidad de productos surtidos |
| Lead Time (días) | Promedio de días para entrega |
| Calidad (%) | Porcentaje de entregas sin defectos |
| Cumplimiento (%) | Entregas a tiempo vs total |
| Última Entrega | Fecha/hora de última entrega |

**Funcionalidades:**
- Ordenar por cualquier columna
- Buscar por nombre de proveedor
- Ver histórico de 30 días

### 3. **Analytics**

**URL:** `/analytics`

**Descripción:** Análisis profundo con filtros avanzados y gráficos personalizables

#### Filtros Disponibles

```
┌─────────────────────────────────────┐
│ Filtros Activos                     │
├─────────────────────────────────────┤
│ Desde: [YYYY-MM-DD] ▼               │
│ Hasta: [YYYY-MM-DD] ▼               │
│ Proveedor: [Buscar...] ▼            │
│ Categoría: [Seleccionar] ▼          │
│ Estado: [Todos/Activos/Bajo Stock]  │
└─────────────────────────────────────┘
```

#### Gráficos

**Gráfico 1: Movimiento de Inventario**
- Tipo: Línea
- Período: Últimos 30 días
- Métrica: Cantidad de unidades

**Gráfico 2: Rotación por Categoría**
- Tipo: Barras
- Comparación entre categorías
- % de rotación semanal

**Gráfico 3: Top 10 Productos**
- Tabla paginada (5 por página)
- Ordenable por: nombre, rotación, valor, stock

---

## 🔍 Filtros y Búsqueda

### Filtrado por Fechas

```
FORMATOS VÁLIDOS:
✓ 2025-10-16 (YYYY-MM-DD)
✓ 10-16-2025 (MM-DD-YYYY) - se convierte automáticamente
✓ 16/10/2025 (DD/MM/YYYY) - se convierte automáticamente
✗ October 16 (texto) - no soportado

COMPORTAMIENTO:
- Fechas inválidas → Se ignoran, se muestran datos del período completo
- Desde > Hasta → Se intercambian automáticamente
- Si no especificas → Últimos 30 días por defecto
```

### Filtrado por Proveedor

```
BÚSQUEDA:
- Texto libre (hasta 60 caracteres)
- No es case-sensitive
- Busca en nombre completo del proveedor

EJEMPLOS:
✓ "Coca" → Coincide con "Coca Cola"
✓ "Dais" → Coincide con "Daisa"
✓ "alim" → Coincide con "Alimentos SA"
```

### Filtrado por Categoría

```
Categorías disponibles:
- Bebidas
- Lácteos
- Congelados
- Almacén
- Frescos
- Otros

Búsqueda multi-selección disponible (click con Ctrl/Cmd)
```

---

## 💾 Exportación de Datos

### Exportar desde UI (Botón)

1. Ir a la página deseada (Analytics, Proveedores, etc.)
2. Aplicar filtros si es necesario
3. Click en **"Exportar CSV"**
4. Se descarga automáticamente el archivo

### Exportar mediante API (Programático)

**Endpoint:** `/api/export/{tipo}`

#### Tipos Disponibles

```bash
# Resumen general
curl -H "X-API-Key: YOUR_KEY" \
  http://localhost:8080/api/export/summary.csv \
  -o summary_2025-10-16.csv

# Proveedores
curl -H "X-API-Key: YOUR_KEY" \
  http://localhost:8080/api/export/providers.csv \
  -o providers_2025-10-16.csv

# Top productos (con parámetros)
curl -H "X-API-Key: YOUR_KEY" \
  "http://localhost:8080/api/export/top-products.csv?limit=50&start_date=2025-10-01&end_date=2025-10-16&proveedor=Coca" \
  -o top_products.csv
```

#### Parámetros Opcionales

| Parámetro | Ejemplo | Descripción |
|-----------|---------|-------------|
| `limit` | 50 | Máximo de productos (default: 20) |
| `start_date` | 2025-10-01 | Fecha inicio filtro |
| `end_date` | 2025-10-16 | Fecha fin filtro |
| `proveedor` | Coca | Filtrar por proveedor |

---

## 📊 Métricas Clave Explicadas

### Inventario Total en Pesos

```
DEFINICIÓN:
Sumatoria de (cantidad × precio unitario) de todos los SKUs activos

FÓRMULA:
Inventario Total = Σ (cantidad_i × precio_i)

USADO PARA:
- Ver valor total en estantería
- Detectar cambios significativos
- Planificar compras

EJEMPLO:
- 100 botellas de Coca a $50 = $5,000
- 200 paquetes de pan a $20 = $4,000
- Total = $9,000

⚠️ NOTA: NO incluye productos descontinuados o vencidos
```

### Tasa de Rotación

```
DEFINICIÓN:
(Unidades vendidas en período / Inventario promedio) × 100

INTERPRETACIÓN:
< 1.0 = Producto lento (revisar marca)
1.0-3.0 = Normal
> 3.0 = Rotación alta (buena demanda)
> 5.0 = Altísima rotación (aumentar stock?)

EJEMPLO:
- Vendimos 100 botellas en 30 días
- Inventario promedio: 50 botellas
- Rotación = (100 / 50) × 100 = 200% = muy alta rotación
```

### Cumplimiento de Proveedores

```
DEFINICIÓN:
(Entregas a tiempo / Total entregas) × 100

CÁLCULO:
- A tiempo = Entregó en fecha prometida
- Tarde = Pasó fecha prometida
- Muy tarde = >3 días pasado

BENCHMARK:
< 80% = Crítico (acción requerida)
80-95% = Aceptable (monitorear)
> 95% = Excelente

EJEMPLO:
- Coca hizo 100 entregas
- 95 llegaron a tiempo
- Cumplimiento = 95%
```

### Lead Time Promedio

```
DEFINICIÓN:
Promedio de días entre orden y entrega

CÁLCULO:
Lead Time = (Σ días_i) / cantidad_entregas

INTERPRETACIÓN:
- < 2 días = Muy rápido
- 2-5 días = Normal
- > 5 días = Revisar con proveedor

USADO PARA:
- Planificar reabastecimiento
- Tomar decisiones de compra
```

### Tasa de Error de Sistema

```
DEFINICIÓN:
(Errores en transacciones / Total transacciones) × 100

INCLUYE:
- Fallos en OCR
- Errors en predicciones ML
- Problemas de comunicación
- Timeouts de API

OBJETIVOS:
< 0.1% = Normal
0.1-1.0% = Atención requerida
> 1.0% = Crítico (escalar)

NOTA: Ver página de ops si está alto
```

---

## ❓ FAQ - Preguntas Frecuentes

### General

**P: ¿Con qué frecuencia se actualiza el dashboard?**
R: Los datos se actualizan cada 5 minutos. Algunos gráficos son en tiempo real, otros batch.

**P: ¿Por qué algunos números difieren entre dashboard y BD?**
R: Puede haber cache (5 min) o datos en proceso (OCR lento). Si persiste > 30 min, escalas.

**P: ¿Puedo modificar datos desde el dashboard?**
R: No. El dashboard es solo lectura. Modificaciones se hacen en sistema transaccional.

### Filtros

**P: ¿Qué pasa si pongo fecha futura?**
R: Se muestra vacío (no hay datos). El sistema no proyecta.

**P: ¿Puedo filtrar por múltiples proveedores a la vez?**
R: Actualmente no desde la UI. Usa API con múltiples llamadas o exporta y filtra en Excel.

**P: ¿Cómo limpio los filtros?**
R: Click en botón "Limpiar Filtros" o reload de página (F5).

### Exportación

**P: ¿En qué formato se exportan los datos?**
R: CSV (comma-separated values). Abre en Excel, Google Sheets, etc.

**P: ¿Puedo exportar el histórico completo (más de 30 días)?**
R: Sí, usa API directamente con `start_date` y `end_date` en rango deseado.

**P: ¿Los CSV exportados incluyen datos cifrados?**
R: Los datos sensibles (como claves API) están excluidos. Datos operacionales están en texto plano.

### Métricas

**P: ¿Qué diferencia hay entre "Cumplimiento" e "Inventario Disponible"?**
R: 
- Cumplimiento = ¿Llegó a tiempo? (proveedor)
- Disponible = ¿Tenemos en estantería? (stock actual)

**P: ¿Por qué un producto tiene 0% de rotación?**
R: Probablemente es reciente (< 7 días) o fuera de catálogo. Verifica estado.

**P: ¿Cómo interpretar "Lead Time Promedio de 0 días"?**
R: Es data corrupta o proveedor local (entrega mismo día). Escalas si es anomalía.

### Troubleshooting

**P: ¿Qué significa "Error 401"?**
R: Falta API Key o es incorrecta. Ver sección Autenticación.

**P: ¿Qué significa "Error 503"?**
R: Sistema en mantenimiento o sobrecargado. Espera 5 min e intenta de nuevo.

**P: ¿El gráfico está vacío sin razón aparente?**
R: Posibles causas:
  1. Período sin datos (ej: datos muy antiguos)
  2. Filtro muy restrictivo (reduce filtros)
  3. Bug visual (ctrl+shift+del cache, reload)

---

## 🔧 Troubleshooting

### Dashboard No Carga

**Síntoma:** Página en blanco, error de conexión

**Soluciones:**

```
1. Verificar que estás en URL correcta:
   ✓ http://minimarket.local:8080
   ✗ http://localhost (esto es distinto)

2. Limpiar cache del navegador:
   - Chrome: Ctrl+Shift+Del, selecciona "Todos los tiempos"
   - Firefox: Ctrl+Shift+Del, selecciona "Todos"

3. Intentar en navegador diferente:
   - Si funciona en otro → Problema local del navegador
   - Si no funciona en ninguno → Servidor caído (escalas)

4. Verificar conectividad:
   - Abre una terminal: ping minimarket.local
   - Si falla → Problema de DNS o red
```

### Gráficos Están Lentos

**Síntoma:** Página carga pero gráficos tardan > 5 segundos

**Soluciones:**

```
1. Reduce período de datos:
   - Filtra últimos 7 días en vez de 30
   - Menos datos = render más rápido

2. Menos proveedores:
   - Si filtraste por varios, reduce a uno

3. Actualiza navegador:
   - Algunos navegadores antiguos tienen issues de performance

4. Si sigue lento:
   - Abre DevTools (F12) → Network tab
   - Identifica endpoint más lento
   - Reporta en #minimarket-ops
```

### "No Data Available"

**Síntoma:** Tabla/gráfico muestra mensaje de sin datos

**Diagnóstico:**

```
1. ¿El rango de fechas es correcto?
   - Hoy: 16 de octubre
   - Datos disponibles desde: 1 de octubre (primeros 15 días del mes)
   - Si filtraste para "31 de octubre", no hay datos ✓

2. ¿Hay filtros muy restrictivos?
   - Ej: Filtrar por proveedor "XYZ" si no existe
   - Limpia filtros y intenta de nuevo

3. ¿Es data muy antigua?
   - Sistema guarda 1 año de histórico
   - Si buscas data de 2020, no existe
   - Máximo: últimas 52 semanas
```

### Números No Coinciden con Realidad

**Síntoma:** Dashboard muestra X unidades pero cuento en estantería Y

**Causas Posibles:**

| Causa | Síntoma | Acción |
|-------|--------|--------|
| OCR en proceso | Difiere hace < 30 min | Espera 30 min y recarga |
| Recepción no confirmada | Difiere > 2 horas | Revisa módulo de recepción |
| Data corrupta | Difiere muy significativamente | Escalas a equipo técnico |
| Bug de cache | Inconsistencia aleatoria | Limpia cache browser (Ctrl+Shift+Del) |

---

## 🎓 Buenas Prácticas

### Uso Eficiente

```
✓ HACER:
  - Usar filtros para análisis específicos
  - Revisar dashboard cada mañana
  - Exportar datos semanalmente para análisis
  - Reportar anomalías en Slack

✗ NO HACER:
  - No refrescar constantemente (cada 30 seg)
  - No dejar pestaña open sin usar (consume recursos)
  - No compartir API Key por Slack (usa password manager)
  - No depender 100% en dashboard (verifica físicamente)
```

### Análisis de Datos

```
1. Identifica anomalías:
   - Rotación súbitamente 0 = Producto agotado o quitado
   - Lead time 20 días = Problema con proveedor
   - Error rate > 1% = Escalar

2. Correlaciona con eventos:
   - "¿Por qué subió inventario jueves?"
   - Busca recepción en el histórico
   - Correlaciona con orden de compra

3. Planifica acciones:
   - Rotación baja = Promo o descuento
   - Lead time alto = Cambiar proveedor
   - Bajo stock = Aumentar cantidad orden
```

---

## 📞 Soporte

**¿Encontraste un bug?** Abre issue en GitHub o reporta en Slack #minimarket-dashboard

**¿Necesitas funcionalidad nueva?** Contacta a Team Lead con descripción de caso de uso

**¿Problema urgente?** Escala a #minimarket-emergencies en horario de emergencias

---

**Versión:** 1.0.0  
**Última actualización:** 16 de octubre de 2025  
**Próxima revisión:** Q4 2025

