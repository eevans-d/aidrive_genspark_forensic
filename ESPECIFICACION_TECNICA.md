# Especificación Técnica: Sistema Mini Market (aidrive_genspark)

**Versión:** 1.0
**Fecha:** 2025-09-23
**Estado:** Documento Base Consolidado

## 1. Resumen del Proyecto

### 1.1. Objetivo
El proyecto `aidrive_genspark` contiene un ecosistema de software cuyo componente principal es un **Sistema de Gestión para un Mini Market de uso interno**. El sistema está diseñado para optimizar las operaciones diarias, automatizando la asignación de proveedores, la gestión de pedidos y el análisis de stock a través de una combinación de lógica de negocio, procesamiento de lenguaje natural y un dashboard interactivo.

### 1.2. Foco del Negocio
La prioridad del sistema es la **funcionalidad práctica y la simplicidad operativa**, dejando en segundo plano la robustez a nivel empresarial y las integraciones con sistemas de cumplimiento fiscal (AFIP), que no son requeridas para este caso de uso interno.

### 1.3. Componentes Principales
1.  **Lógica de Proveedores (Agente Negocio):** Un módulo inteligente que asigna productos a proveedores específicos según una jerarquía de reglas de negocio.
2.  **Procesador de Lenguaje Natural (PLN):** Permite a los empleados registrar pedidos y movimientos de stock usando comandos en español.
3.  **Integración OCR:** Procesa facturas escaneadas para registrar entradas de stock y asignar proveedores automáticamente.
4.  **API y Dashboard Web:** Una API basada en FastAPI que expone los datos y un dashboard web para la visualización de KPIs, tendencias y estado del inventario.
5.  **Base de Datos:** Un sistema de persistencia basado en SQLite para almacenar toda la información operativa.

## 2. Lógica de Negocio: Gestión de Proveedores

El núcleo del sistema es su capacidad para asignar automáticamente un proveedor a cada producto.

### 2.1. Proveedores Configurados
El sistema está pre-configurado con 12 proveedores específicos del mini market:

| Código | Proveedor | Especialidad |
| :--- | :--- | :--- |
| **BC** | Bodega Cedeira | Vinos y Alcohol (excepto cerveza) |
| **CO** | Coca Cola | Gaseosas (Línea Coca-Cola) |
| **Q** | Quilmes | Cervezas y Gaseosas (Línea PepsiCo) |
| **FA** | Fargo | Panificados, Distribuidor (Lácteos, Pastas) |
| **LS** | La Serenísima | Lácteos y derivados |
| **ACE** | Aceitumar (MDP) | Conservas y Frutos Secos |
| **TER** | Terrabusi (Mondelez) | Galletitas y Golosinas |
| **LV** | La Virginia | Infusiones (Café, Té, Yerba) |
| **FR** | Frutas y Verduras ("Bicho") | Productos Frescos |
| **MU** | Multienvase (MDP) | Descartables |
| **GA** | Galletitera (MDP) | Panadería Local |
| **MAX** | Maxiconsumo | Mayorista General (Proveedor por defecto) |

### 2.2. Algoritmo de Asignación Jerárquica
El sistema utiliza un algoritmo de 4 niveles para determinar el proveedor con la máxima precisión:

1.  **Nivel 1 (Confianza 0.95): Coincidencia de Marca Directa.** Si el producto es una marca propia del proveedor (ej: "Leche La Serenísima").
2.  **Nivel 2 (Confianza 0.90): Coincidencia de Sub-Marca.** Si el producto es una marca distribuida por un proveedor especialista (ej: "Galletitas Oreo" -> Terrabusi).
3.  **Nivel 3 (Confianza 0.80): Coincidencia por Categoría.** Si el producto pertenece a una categoría especializada (ej: "Vino Malbec" -> Bodega Cedeira).
4.  **Nivel 4 (Confianza 0.50): Asignación por Defecto.** Si ninguna regla anterior aplica, se asigna al proveedor mayorista general (`MAX` - Maxiconsumo).

## 3. Interacción y Casos de Uso

### 3.1. Comandos de Lenguaje Natural
El sistema está diseñado para ser operado mediante frases comunes en español, facilitando su adopción por parte de los empleados.

-   **Para realizar pedidos:**
    -   `"Pedir Coca Cola x 6"`
    -   `"Falta Sprite lima limón"`
    -   `"Anotar Salchichas Paladini para el pedido"`

-   **Para registrar movimientos de stock (entradas/salidas):**
    -   `"Dejé 4 bananas del ecuador en el depósito"`
    -   `"Ingreso 12 Coca Cola del distribuidor"`
    -   `"Saqué 6 productos para el kiosco"`

### 3.2. Integración con OCR
El sistema puede procesar facturas digitalizadas para automatizar la entrada de mercancía. El flujo es el siguiente:
1.  Se recibe una imagen o PDF de una factura.
2.  Un sistema OCR (previamente implementado) extrae los productos y cantidades.
3.  El sistema de lógica de negocio recibe esta lista de productos.
4.  Para cada producto, se aplica el algoritmo de asignación de proveedor.
5.  Se genera un movimiento de entrada de stock en la base de datos, asociando cada producto a su proveedor correcto.

## 4. API del Dashboard y Visualización

El sistema cuenta con una API (FastAPI) y un dashboard web para monitorear la operación.

### 4.1. Autenticación
El acceso a los endpoints de la API está protegido y requiere una **API Key** que debe ser enviada en la cabecera HTTP `X-API-Key`.

### 4.2. Endpoints Principales
-   `GET /`: Página principal del dashboard.
-   `GET /analytics`: Vista de analíticas con filtros por fecha y proveedor.
-   `GET /api/summary`: Devuelve un resumen general del estado del negocio (total de pedidos, movimientos, etc.).
-   `GET /api/top-products`: Retorna un ranking de los productos más pedidos, con filtros.
-   `GET /api/trends`: Muestra tendencias de ventas mensuales.
-   `GET /api/stock-by-provider`: Informa el volumen de stock agrupado por proveedor.
-   `GET /api/export/...`: Endpoints para exportar datos en formato CSV.
-   `GET /health`: Endpoint público para verificar el estado del servicio.
-   `GET /metrics`: Expone métricas en formato Prometheus para monitoreo avanzado.

## 5. Persistencia de Datos (SQLite)

La información se almacena en una base de datos SQLite con un esquema bien definido para garantizar la integridad de los datos.

-   **Tablas Principales:**
    -   `proveedores`: Almacena los 12 proveedores maestros.
    -   `productos`: Catálogo de todos los productos que maneja el mini market.
    -   `pedidos` y `detalle_pedidos`: Guardan el historial de pedidos a proveedores.
    -   `movimientos_stock`: Registra cada entrada y salida de productos del inventario, proporcionando trazabilidad completa.
    -   `facturas_ocr`: Almacena un registro de las facturas procesadas por el sistema OCR.

## 6. Stack Tecnológico y Despliegue

-   **Lenguaje:** Python.
-   **Framework web/API:** FastAPI (API principal y servidor de plantillas Jinja2 para el dashboard; no se usa Flask).
-   **Base de Datos:** SQLite.
-   **Despliegue:** El sistema está contenerizado con Docker y se gestiona a través de `docker-compose.yml` para un despliegue sencillo.
-   **CI/CD:** El proyecto cuenta con un pipeline de Integración Continua en GitHub Actions que ejecuta pruebas y validaciones de forma automática.
