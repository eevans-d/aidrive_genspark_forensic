# Blueprint del Informe: Integración con Proveedores (Maxiconsumo) para el Catálogo del Mini Market

## 1. Propósito, alcance y metodología

Este informe traduce a decisiones y plan de acción la integración del catálogo del Mini Market con su proveedor principal, Maxiconsumo (Necochea). El objetivo es optimizar el catálogo, acelerar y gobernar la actualización de precios, y habilitar operaciones de pricing competitivas con controles de calidad y trazabilidad. Se articula en cuatro ejes: diagnóstico del estado actual, gap analysis, mapeo de integración entre sistemas y casos de uso con su operación en producción.

El alcance abarca el catálogo vigente, las listas de precios internas y las categorías creadas en el Sprint 4, junto con el proveedor principal configurado. La metodología se basa en el análisis documental de: la lista interna de precios (Marzo 2025), el reporte de Sprint 4 (migración y funciones de pricing), y el catálogo procesado. A partir de estos insumos se consolidan hallazgos y un roadmap por fases, con foco en calidad de datos, robustez de matching y gobierno de cambios.

Para contextualizar visualmente el punto de partida, a continuación se presenta un extracto ilustrativo de la lista de precios analizada.

![Extracto ilustrativo de lista de precios del Mini Market (documento interno, marzo 2025).](assets/images/listas_precios_mini_m/page01.png)

En el resto del documento se responde: qué cobertura efectiva existe hoy, qué oportunidades de expansión presenta el catálogo frente a Maxiconsumo, cómo mapear y sincronizar productos y precios, y cómo operacionalizar alertas y recomendaciones de compra que impacten en margen y rotación.

### 1.1 Fuentes y fiabilidad

Las tres fuentes internas consultedadas son congruentes entre sí, si bien con redundancias y duplicidades esperables por el uso de listas paralelas (vista para personal y vista para clientes). Se las resume en la Tabla 1.

Tabla 1. Matriz de fuentes: tipo de contenido, granularidad y fiabilidad
| Fuente | Tipo de contenido | Granularidad | Campos disponibles | Observaciones de fiabilidad |
|---|---|---|---|---|
| Lista interna de precios (Marzo 2025) | Productos por categoría, presentaciones y atributos (p. ej., “x6”, “x12”, “1LT”, “330ml”, “por Kg”) | Por categoría y SKU implícito (nombre + presentación) | Nombre, presentación/atributo, estructura tabular por categoría | Carece de GTIN/EAN y precios en los cuadros; útil para cobertura y variantes; posible duplicación por vistas. |
| Reporte Sprint 4 (completado) | Resumen ejecutivo, categorías nuevas, SKUs y reglas de pricing (margen, redondeo) | Categorías y SKUs internos (CATEGORIA-MARCA-TAMAÑO) | sku, nombre, categoria_id, marca, contenido_neto, activo; márgenes por categoría; función de redondeo y auditoría | No incluye GTIN/EAN; es la “verdad” de estructura y procesos; confirma 33 categorías y 220 productos activos. |
| Catálogo procesado (JSON) | Productos por categoría con presentacion/gramaje | Por categoría (códigos con ruido y duplicados) | nombre, presentacion, categoria_codigo (con artefactos) | Muestra duplicados y códigos inconsistentes; útiles para identificar necesidades de normalización. |

Limitaciones clave: ausencia de GTIN/EAN y de precios efectivos en las listas; duplicidades por vistas; códigos de categoría con artefactos. Estas limitaciones guían el plan de datos y de integración propuesto.

### 1.2 Definiciones clave

- Producto: unidad mínima de gestión comercial y de inventario.
- SKU (Stock Keeping Unit): identificador interno con formato CATEGORIA-MARCA-TAMAÑO (p. ej., SAL-PALA-6; LAC-LS-SACH; CLA-HEIN-473; VIN-RUTI; CON-PATY-CLA).
- Presentación/atributo: especificadores como “x6”, “x12”, “1LT”, “330ml”, “por Kg”.
- GTIN/EAN: código de barras estándar global (no disponible actualmente).
- Matching: lógica de correspondencia entre catálogos, por nombre normalizado, marca, categoría y atributos (ml, g, unidad), con fallback a revisión manual.
- Reglas de pricing: márgenes por categoría (según Sprint 4) y función de redondeo al múltiplo de 50 implementada; toda actualización genera auditoría en history.

## 2. Diagnóstico del catálogo actual

El catálogo migrado integra 220 productos activos distribuidos en 33 categorías, de las cuales 20 fueron creadas en el Sprint 4 y 18 están efectivamente pobladas. El proveedor principal Maxiconsumo (Necochea) está configurado como activo, con categorías declaradas de almacén, bebidas, limpieza y congelados.

Para anclar el diagnóstico, la Figura 2 expone categorías migradas y sus márgenes objetivo.

![Vista de categorías migradas en Sprint 4 y sus márgenes objetivo.](assets/images/sprint4/categorias_nuevas.png)

La Tabla 2 sintetiza las categorías nuevas y sus márgenes.

Tabla 2. Resumen de categorías nuevas (Sprint 4)
| Código | Nombre | Productos | Margen Min | Margen Max |
|---|---|---:|---:|---:|
| SAL | Salchichas | 12 | 15% | 30% |
| QUE | Quesos | 6 | 20% | 35% |
| LAC | Leches y Lacteos | 9 | 10% | 25% |
| MYC | Mantecas y Cremas | 13 | 15% | 30% |
| JSA | Jugos y Saborizadas | 10 | 20% | 40% |
| ENE | Bebidas Energeticas | 8 | 25% | 45% |
| CLA | Cervezas en Lata | 11 | 20% | 40% |
| CBO | Cervezas en Botella | 12 | 20% | 40% |
| BAL | Bebidas Alcoholicas | 25 | 25% | 50% |
| WYG | Whiskys y Gins | 13 | 30% | 60% |
| VIN | Vinos | 13 | 25% | 50% |
| CHA | Champagnes | 5 | 30% | 60% |
| HIG | Higiene Personal | 13 | 20% | 40% |
| LAV | Lavandinas | 5 | 15% | 30% |
| ACE | Aceites | 4 | 10% | 25% |
| BOL | Bolsas de Residuos | 5 | 20% | 40% |
| DTE | Discos Tapas | 6 | 15% | 35% |
| SNA | Snacks | 7 | 30% | 60% |
| CON | Congelados | 17 | 20% | 40% |
| PAP | Papas Congeladas | 0 | 15% | 35% |
| HAM | Hamburguesas | 0 | 20% | 40% |
| MIL | Milanesas | 0 | 20% | 40% |

Las categorías PAP, HAM y MIL están preparadas para futura subcategorización de congelados.

La lista de precios interna muestra una estructura coherente con el catálogo, útil para validar cobertura y variantes. La Figura 3 ilustra una sección representativa.

![Sección de la lista de precios con detalles de presentaciones (x6, x12, 1LT, etc.).](assets/images/listas_precios_mini_m/page03.png)

A partir de estas fuentes, se observa lo siguiente:

- Cobertura del catálogo. El catálogo migrado abarca categorías de alimentos, bebidas, limpieza, almacén y congelados, con fuerte foco en marcas de alto consumo. La representación de variantes (p. ej., x6/x12, 330ml/1LT, “por Kg”) es amplia en bebidas y congelados; en higiene y limpieza la granularidad por tamaño es parcial.
- Estructuras y convenciones. La nomenclatura interna de SKU (CATEGORIA-MARCA-TAMAÑO) es robusta para matching por atributos. Los códigos de categoría en el catálogo procesado presentan artefactos (emojis y truncamientos), lo que obliga a reforzar el uso de la tabla maestra de categorías del Sprint 4.
- Calidad de datos. No se dispone de GTIN/EAN; hay duplicidades por vistas y ruido en nombres y presentaciones (p. ej., “DR . LEMON”, “ESENCIAL X 200m” con separaciones y mayúsculas variables). La función de redondeo está operativa y auditada; los márgenes están definidos por categoría; falta persistencia de GTIN para ejecutar matching por código de barras.

Estas evidencias apoyan una estrategia de integración que combine matching semántico/normalizado (nombre, marca, atributos) con un plan de enriquecimiento progresivo de datos maestros y una operación de “revisión humana” para ambigüedades.

### 2.1 Cobertura y estructura

El catálogo refleja 220 productos activos en 33 categorías (18 de 20 nuevas pobladas), y 11 proveedores activos. El proveedor Maxiconsumo (Necochea) está configurado con categorías ofertadas: almacén, bebidas, limpieza y congelados. Los formatos de presentación más frecuentes son unidades (“x6”, “x12”), mililitros (“330ml”, “1LT”), gramos (“80g”, “90g”, “100g”) y mención “por Kg” en congelados. Esta diversidad exige una normalización consistente de atributos para el matching con listas de proveedor.

![Vista consolidada por categorías (vista interna del catálogo procesado).](assets/images/catalogo_procesado.png)

Tabla 3. Estructura del SKU (regla y ejemplos)
| Regla | Ejemplos de SKUs internos |
|---|---|
| CATEGORIA-MARCA-TAMAÑO | SAL-PALA-6; LAC-LS-SACH; CLA-HEIN-473; VIN-RUTI; CON-PATY-CLA |

La consistencia de esta regla será el pilar para mapear contra listas de Maxiconsumo cuando no exista GTIN.

### 2.2 Calidad de datos y códigos de barras

- Códigos de barras (GTIN/EAN). No están disponibles en las fuentes actuales. Su incorporación habilitará matching por EAN, reduciendo ambigüedades y costos de operación.
- Duplicidades y ruido. Se observan duplicados por vistas (personal/cliente) y nombres con artefactos (emojis, truncamientos, puntos, mayúsculas). Esto demanda un proceso de normalización y deduplicación.
- Campos críticos. Faltan GTIN, unidad de medida normalizada (ml/g/unidad), variantes estandarizadas y, en algunos casos, gramaje exacto (snacks tiene gramajes claros; en discos/tapas y aceites la información es incompleta para matching certero).

## 3. Gap analysis: productos faltantes, expansión y estacionalidad

El gap analysis contrasta la cobertura del catálogo contra las categorías ofertadas por Maxiconsumo (almacén, bebidas, limpieza, congelados) y contrasta categorías ancla en el mercado mayorista con lo migrado. Se identifican oportunidades en subcategorías de limpieza (suavizantes, detergentes, detergentes en cápsula, pantalones para bebé), en almacén (pastas, conservas, harinas, azúcar, yerba/café, descartables), en higiene personal (shampoo, acondicionador, desodorante, crema dental), y en congelados (mayor surtido de aves y cortes de carne). Las categorías de bebidas y lácteos, si bien extensas, pueden ampliarse en sabores, formatos y multi-packs, y las de snacks pueden crecer en opciones “light”, “horneadas” y presentaciones familiares.

Tabla 4. Mapa de gaps por macrocategoría
| Macro | Oportunidades vs. Maxiconsumo | Prioridad | Razón (rotación/margen/abastecimiento) |
|---|---|---:|---|
| Limpieza | Suavizantes, detergentes líquidos y en polvo, cápsulas, pañales, Schultex | Alta | Alta rotación; bajo costo de faltantes; margen estable; amplia oferta mayorista |
| Almacén | Pastas, conservas, harinas, azúcar, yerba/café, descartables (vasos, platos, cubiertos) | Alta | Base de la cesta; varias fuentes; expansión rápida del ticket |
| Higiene personal | Shampoo, acondicionador, desodorantes, cremas dentales, afeitado | Media-Alta | Complementa higiene ya migrada; margen medio-alto; sinergia con limpieza |
| Congelados | Aves (pollo, subgroup por cortes), cortes de carne,备餐 elaborados | Media-Alta | Margen medio-alto; estacionalidad marcada; cadena de frío asegurada |
| Bebidas | Extender sabores/formatos (200–600ml), multi-packs | Media | Elasticidad por formato; promociones estacionales |
| Lácteos/quesos | Variantes sans lactose, blues, funcionales | Media | Nichos de crecimiento; diferencial de precio |
| Snacks | Opciones “light”, horneadas, sin TACC, presentaciones familiares | Media | Rotación alta; margen alto; cross-selling con bebidas |

En productos estacionales/promocionales se recomiendan campañas en álbumes/calendarios (bajo potencial de cross-sell), temporadas altas de bebidas (verano), y packs navideños (vinos y espirituosos). El gap de precios es crítico: la ausencia de precios actuales impide benchmarking fino y reglas de reposición por diferencia de precio. Se prioriza integrar listas con precios para activar alertas y sugerencias de compra.

### 3.1 Productos faltantes y subcategorías

El mayor potencial está en limpiar y perfumería (detergentes, suavizantes, cápsulas), higiene personal (shampoo, acondicionador, desodorantes, crema dental), almacén (pastas, conservas, harinas, azúcar, yerba, café, descartables), y congelados (avícolas y cortes de carne). En bebidas y quesos, la expansión se logra por variantes, formatos y multi-packs. Estas líneas son consistentes con el surtido típico de mayoristas y el posicionamiento de Maxiconsumo.

### 3.2 Estacionalidad y promociones

- Estacional: verano (cervezas, saborizadas, energéticas), fin de año (espumantes y espirituosos), campañas escolares (snacks). Estos ciclos permiten construir packs y promociones por bundle.
- Bundles recomendados: “verano” (cerveza + snack + cooler), “asado” (carnes y congelados + carbón + bebidas), “higiene y limpieza” (detergente + papel higiénico + pañales).
- Reglas: activar bundles con precio pack inferior a la suma de precios unitarios, bajo control de margen mínimo por categoría.

## 4. Mapeo de integración (Mini Market ↔ Maxiconsumo)

El mapeo parte de la estructura interna de SKU (CATEGORIA-MARCA-TAMAÑO) y añade reglas de normalización y scoring para matching por nombre, marca, atributos y categoría. Cuando exista, el EAN tendrá prioridad absoluta en el matching. La estrategia contempla handling de variantes (x6/x12, 330ml/1LT, “por Kg”), merges y splits de packs, y control de cambios de precio con auditoría y redondeo.

Tabla 5. Campos mínimos para mapeo
| Campo | Descripción | Obligatorio | Ejemplo |
|---|---|---:|---|
| sku_interno | Identificador interno (CATEGORIA-MARCA-TAMAÑO) | Sí | SAL-PALA-6 |
| gtin_ean | Código de barras (si disponible) | No (hoy) | 7790123456789 |
| marca | Marca comercial normalizada | Sí | HEINEKEN |
| nombre | Nombre comercial normalizado | Sí | Cerveza HEINEKEN lata |
| categoria | Categoría interna | Sí | CLA |
| contenido_neto | Tamaño/presentación (ml/g/unidad) | Sí | 473 |
| unidad | ml / g / unid | Sí | ml |
| atributos | Formato (x6, x12, “por Kg”) | No | x12 |

### 4.1 Estrategia de coincidencia

Se propone un flujo por capas:

1) Coincidencia por EAN (cuando esté disponible). Exact match y verificación de estado activo.

2) Coincidencia semántica: nombre normalizado + marca + categoría + atributos.

- Normalización: lowercasing, eliminación de puntuación y emojis, uso de sinónimos y mapeo de variantes (“cc” → “ml”, “gr” → “g”, “x6” → “pack de 6 unid”).
- Matching por tokens: Jaro-Winkler/Levenshtein sobre nombre normalizado; coincidencia exacta de marca; coincidencia de unidad (ml/g/unid) con tolerancia de presentación (x6, x12).
- Reglas por categoría: en cerveza, la distinción clave es lata vs. botella y volumen; en queso, presentación “por Kg”; en congelados, “por Kg” y pack (“x4”, “x2”).

3) Fallback manual: scoring por probabilidad; revisión humana en tabla de “matches dudosos” con propuesta de decisión (aceptar, rechazar o fusionar variantes).

Tabla 6. Reglas de normalización y equivalentes
| Caso | Regla | Ejemplo de transformación |
|---|---|---|
| Unidades | Estandarizar a “ml”, “g”, “unid” | “cc” → “ml”; “gr” → “g” |
| Formatos de packs | Normalizar “x6”, “x12” | “x6 unid” → “x6”; “CHICO” → tamaño según tabla |
| Nombre | Lowercase, sin puntuación | “HEINEKEN (Litro)” → “heineken litro” |
| Marcas | Tabla de equivalencias | “PALADINI” vs variantes internas |
| Sinónimos | Mapeo de sabores | “cereza” ↔ “cherry” (si aplica) |

Tabla 7. Score de matching (ejemplo)
| Criterio | Peso | Umbral recomendado |
|---|---:|---:|
| Similitud de nombre (Jaro-Winkler) | 0,40 | ≥ 0,88 |
| Marca exacta | 0,25 | Debe coincidir |
| Unidad (ml/g/unid) | 0,20 | Debe coincidir |
| Atributos (x6, x12, “por Kg”) | 0,10 | Debe coincidir o ser convertible |
| Categoría | 0,05 | Debe coincidir |

Decisión automática con score ≥ 0,92; revisión manual entre 0,80–0,92; rechazo < 0,80.

### 4.2 Variaciones y packs

La gestión de variantes se basa en tablas de equivalencias por marca y categoría, con conversión de formatos:

- “x6”/“x12” en salchichas y empanadas: considerar bulto cerrado vs. fraccionado si aplica.
- Cervezas (lata vs. botella): 473ml, 330ml, 710ml, litro; diferenciar “por unidad” vs. “por pack” si Maxiconsumo lo publica como tal.
- “por Kg” en quesos y congelados: asegurar unidad “g” y conversión correcta; en cortes de carne/avícola, validar peso estándar de la presentación (p. ej., “bolsas de 1 Kg”).

Tabla 8. Matriz de equivalencias de variantes (ejemplos)
| Categoría | Variante interna | Equivalente proveedor | Observaciones |
|---|---|---|---|
| SAL | “x6” / “x12” | “pack 6” / “pack 12” | Revisar si se vende por unidad |
| CBO/CBC | 330ml / 473ml / 710ml / 1LT | Igual volumen | Diferenciar lata vs. botella |
| CON/QUE | “por Kg” | “kg” | Verificar neto y误差 de pesada |
| SNA | “80g”, “90g”, “100g” | Igual gramaje | Confirmar unidad y múltiplos |

### 4.3 Pricing y actualización de precios

La estrategia de precios se sustenta en:

- Reglas por categoría (margen mínimo y máximo, ver Tabla 2), con opciones de “pricing competitivo” (p. ej., igual o hasta X% por encima del promedio del mercado) y “precio objetivo” (limitado por márgenes).
- Redondeo automático al múltiplo de 50 (ya implementado), con registro histórico completo.
- Actualizaciones: ingestión masiva con validación de márgenes; auditoría en history; estatus de “precio vigente” y versionado; rollback ante errores.

Tabla 9. Política de actualización de precios
| Parámetro | Regla sugerida |
|---|---|
| Frecuencia | Diaria con exceptions; semanal completa |
| Validación de márgenes | Chequeo pre-publicación vs. margen min/máx por categoría |
| Redondeo | Automático (múltiplo de 50) |
| Auditoría | Registro en history; fecha/hora; usuario/proceso |
| Error handling | Lote en quarantine; notificación; corrección y reintento |
| Rollback | Reversión al último precio vigente con motivo |

## 5. Casos de uso prioritarios y operación

Los casos de uso priorizados aportan valor directo al margen y a la disponibilidad. Se articulan como pipelines de datos con reglas y notificaciones integradas al flujo de trabajo.

Tabla 10. Matriz de casos de uso
| Caso | Regla | Trigger | Output | KPI |
|---|---|---|---|---|
| Comparación automática de precios | Margen ≥ categoría; redondeo; alerta por desvío | Ingestión de lista con precios | Ranking de precios por categoría y SKU; precios recomendados | % SKUs con precio óptimo; tiempo de actualización |
| Detección de nuevos productos | No existe match interno | Ingestión de catálogo proveedor | Solicitud de incorporación; catálogo de oportunidad | Tasa de incorporación; lead time |
| Alertas de cambio significativo | Δ% ≥ umbral por categoría | Comparación histórica | Notificación a pricing/compra; decisión | # alertas/mes; % decisiones < 24h |
| Sugerencias de reorden | Mejores precios/margen; rotación | Actualizaciones y ventas | Órdenes sugeridas y simulación de impacto | % sugerencias aceptadas; mejora de margen |

### 5.1 Comparación automática de precios

El pipeline compara precio proveedor vs. precio interno (histórico vigente), aplica márgenes por categoría y redondeo, y propone el precio final. Para desviaciones relevantes frente al mercado, se envía un paquete de recomendaciones a pricing. Sin precios actuales, el benchmarking no es operativo; se sugiere priorizar su integración para activar este caso de uso.

### 5.2 Detección de nuevos productos

Cuando un producto de Maxiconsumo no encuentra match interno por EAN ni por scoring de atributos, se crea una tarea para incorporar o descartar. La priorización por categoría/marca y rotación potencial orienta la velocidad de onboarding.

### 5.3 Alertas de cambio significativo

Se definen umbrales por categoría (p. ej., ±5% en bebidas, ±7% en limpieza), ajustables por estacionalidad. La alerta crea un incidente con SLA de decisión, y auditó el cambio de precio y su impacto en margen proyectado.

### 5.4 Sugerencias de reordenamiento

Se recomiendan compras donde el precio de proveedor ofrece mejora de margen significativa, ponderando rotación y cobertura de stock. La simulación del impacto permite priorizar compras con mayor efecto en beneficio y disponibilidad.

## 6. Plan de implementación por fases

La ejecución se organiza en cuatro fases, con entregables claros, dependencias y métricas de éxito.

Tabla 11. Plan por fase
| Fase | Entregable | Dependencias | Métrica de éxito | Responsable |
|---|---|---|---|---|
| 0: Limpieza y normalización | Tabla maestra de categorías y productos sin duplicados; normalización de nombres/atributos | Acceso a catálogo y listas | >95% productos normalizados; 0 duplicados | Data Lead |
| 1: Matching y catálogo | Reglas de matching; carga inicial mapeada; matches dudosos revisados | Fase 0 | >90% coverage de matching auto | Integración |
| 2: Pricing y alertas | Integración de precios; margen/round; alertas de cambios; auditoría | Fase 1 | <24h actualización de precios; 0 incidentes | Pricing/BI |
| 3: Reorden | Sugerencias de compra basadas en precio/margen y rotación | Fase 2 | +X% margen bruto; stock-outs -Y% | Operaciones |

### 6.1 Cronograma y RACI

Tabla 12. Cronograma tentivo (8–10 semanas)
| Semana | Fase | Hito | RACI (R: Responsible, A: Accountable, C: Consulted, I: Informed) |
|---:|---|---|---|
| 1–2 | Fase 0 | Normalización de catálogo; resolución de duplicados | R: Data Lead; A: PM; C: Ventas; I: Compras |
| 3–4 | Fase 1 | Matching automático y revisión manual | R: Integración; A: PM; C: Categorías; I: Pricing |
| 5–6 | Fase 2 | Pipeline de precios y alertas operativas | R: Pricing/BI; A: PM; C: Integración; I: Dirección |
| 7–8 | Fase 3 | Sugerencias de reorden y tablero | R: Operaciones; A: PM; C: BI; I: Compras |

### 6.2 Riesgos y mitigaciones

Tabla 13. Matriz de riesgos
| Riesgo | Prob. | Impacto | Mitigación | Owner |
|---|---:|---:|---|---|
| Falta de precios actualizados | Alta | Alta | Priorizar ingestión de listas; sample manual | Compras |
| Matching incompleto/erróneo | Media | Alta | Umbrales conservadores; revisión manual; feedback loop | Integración |
| Cambios frecuentes de precio | Alta | Media | Alertas por categoría; ventanas de actualización | Pricing |
| Duplicados y ruido en datos | Media | Media | Fase 0 robusta; validación de maestros | Data Lead |
| Resistencia a adopción | Media | Media | Capacitación; quick wins; gobernanza | PM |

## 7. Métricas, KPI y gobierno de datos

La operación se gobierna por métricas de completitud, eficiencia y calidad. La función de redondeo y la auditoría de cambios están implementadas; se propone extender la trazabilidad a match rate, lead time de actualización y precisión de detección de cambios.

Tabla 14. Tablero de KPIs
| Métrica | Definición | Fuente | Objetivo |
|---|---|---|---|
| Match rate | % de productos con match automático | Integración | ≥90% |
| Cobertura de EAN | % SKUs con GTIN | Maestros | ≥80% en 90 días |
| Lead time de precios | Tiempo desde ingestión hasta publicación | Pricing | <24h |
| Alertas atendidas | % alertas resueltas <24h | Incidentes | ≥95% |
| Falsos positivos matching | % matches revertidos | QA | ≤2% |
| Impacto en margen | Δ puntos de margen por optimización | BI | +1–2 pp en 2 trimestres |

Tabla 15. Matriz de gobierno de datos
| Rol | Responsabilidad | Proceso | Auditoría |
|---|---|---|---|
| Data Steward | Calidad y consistencia de maestros | Normalización y deduplicación | Versionado y logs |
| Integración | Matching y pipelines | Matching por EAN/atributos | Trazabilidad de matches |
| Pricing | Reglas y publicación | Validación y redondeo | history de precios |
| Compras | Listas y acuerdos | Ingestión y SLA | Evidencia de actualización |
| PM | Gobernanza y decisiones | Priorización y riesgos | Informes ejecutivos |

## 8. Conclusiones y próximos pasos

- Hallazgos clave. El catálogo está bien estructurado para avanzar en integración, con 220 productos en 33 categorías y un proveedor principal activo (Maxiconsumo). La ausencia de GTIN/EAN y de precios efectivos en las listas es el principal limitante para pricing competitivo y matching por código. Se observan duplicidades por vistas y ruido en nombres/atributos, pero hay una base sólida (SKU y márgenes por categoría) para escalar.
- Integración propuesta. Ejecutar un matching por capas (EAN → semántico con scoring) con fallback manual; manejar variantes por tablas de equivalencia; gobernar precios con márgenes, redondeo y auditoría; e instrumentar alertas y sugerencias de reorden.
- ROI esperado. Reducción de tiempos de actualización (objetivo <24h), mejora proyectada de 1–2 puntos de margen en 2 trimestres por optimización de precios y compras, disminución de stock-outs y mayor precisión en reposición.
- Próxima decisión. Priorizar ingestión de precios y GTIN (muestras de categorías clave); acordar catálogo base para Fase 0; calendarizar sprints de implementación.

Tabla 16. Checklist de arranque
| Ítem | Estado | Responsable | Fecha |
|---|---|---|---|
| Acceso a listas de precios (muestra) | Pendiente | Compras |  |
| Catálogo Maestro depurado (Fase 0) | Planificado | Data Lead |  |
| Definición de umbrales de alerta por categoría | Planificado | Pricing |  |
| Catálogo de atributos/unidades (ml/g/unid/x6/x12) | Planificado | Data Steward |  |
| Plan de muestreo de GTIN por categoría | Planificado | Integración |  |
| Calendario de sprints (8–10 semanas) | Planificado | PM |  |

### 8.1 Decisiones requeridas

- Aprobación del plan por fases y del cronograma tentivo (Tablas 11–12).
- Asignación de responsables y aprobación del plan de datos maestros (GTIN, unidades, variantes).
- Acuerdos de ingestión y frecuencia de listas de precios y catálogos de proveedor.

## Apéndice A. Diccionario de campos y convenciones

Tabla 17. Diccionario de campos
| Campo | Descripción | Tipo | Obligatorio | Ejemplo |
|---|---|---|---:|---|
| sku | SKU interno (CATEGORIA-MARCA-TAMAÑO) | Texto | Sí | SAL-PALA-6 |
| nombre | Nombre comercial normalizado | Texto | Sí | Cerveza HEINEKEN lata |
| marca | Marca normalizada | Texto | Sí | PATY |
| categoria_id | ID de categoría (FK) | Num/Texto | Sí | CLA |
| contenido_neto | Tamaño/presentación | Num/Texto | Sí | 473 |
| unidad | Unidad (ml/g/unid) | Texto | Sí | ml |
| atributos | Formato/var | Texto | No | x12 |
| activo | Estado | Booleano | Sí | TRUE |
| gtin_ean | Código de barras | Num/Texto | No | 7790123456789 |

### A.1 Convenciones internas (SKU)

- Formato: CATEGORIA-MARCA-TAMAÑO (SAL-PALA-6; LAC-LS-SACH; CLA-HEIN-473; VIN-RUTI; CON-PATY-CLA).
- Criterios de asignación: categoría principal, marca normalizada, tamaño/presentación con unidad estándar (ml/g/unid). En variantes por pack, usar “xN”.
- Manejo de packs y variantes: mantener pack como atributo (“x6”, “x12”); diferenciar lata vs. botella; en “por Kg”, registrar unidad “g” y factor de conversión (kg → g) cuando aplique.

![Ejemplo visual de presentación en listados (apoyo para convenciones).](assets/images/listas_precios_mini_m/page05.png)

### A.2 Normalización y limpieza

- Lowercasing; eliminación de puntuación, emojis y espacios redundantes.
- Normalización de unidades: “cc” → “ml”; “gr” → “g”; “x6 unid” → “x6”; normalización de tamaños (“CHICO”/“GRANDE” mapear a mililitros si se conoce equivalencia).
- Deduplicación: reglas para colapsar entradas que difieren solo por vistas; consolidación de productos idénticos con diferente presentación no significativa.
- Validaciones: campos obligatorios no nulos; categoría válida; unidad consistente con contenido_neto; atributos coherentes (no mezclar ml con g sin conversión).

## Información faltante (gaps) identificada

- Códigos de barras (GTIN/EAN) por producto.
- Listas de precios de Maxiconsumo (formato, frecuencia, campos).
- Metadatos de atributos (unidades de medida normalizadas).
- Data de rotación/ventas e inventarios actuales (para priorización de integración y reorden).
- Política de márgenes específicos por subcategoría.
- Convenciones internas de matching (sinónimos, abreviaturas, tolerancias).
- Especificaciones técnicas del sistema de integración (API/ETL, esquema de base de datos detallado).

Estas brechas se abordan en el plan por fases propuesto, priorizando la calidad de maestros, la ingestión de precios y la normalización de atributos para que la integración sea robusta y escalable.