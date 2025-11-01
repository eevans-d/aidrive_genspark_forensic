# DOCUMENTACIÓN TÉCNICA ACTUALIZADA - SISTEMA MINI MARKET
## Arquitectura, APIs y Configuración Final

**Versión:** 2.0.0 FINAL - SISTEMA COMPLETADO  
**Fecha de Actualización:** 1 de noviembre de 2025  
**Estado:** ✅ SISTEMA 100% DESPLEGADO Y OPERATIVO EN PRODUCCIÓN  
**URL Producción:** https://lefkn5kbqv2o.space.minimax.io  
**Target:** Desarrolladores, Arquitectos, DevOps, Operadores de Producción  

---

## 📋 TABLA DE CONTENIDOS

1. [Arquitectura del Sistema](#1-arquitectura-del-sistema)
2. [Diagramas de Flujo Actualizados](#2-diagramas-de-flujo-actualizados)
3. [Documentación APIs Completas](#3-documentación-apis-completas)
4. [Esquemas de Base de Datos](#4-esquemas-de-base-de-datos)
5. [Documentación de Configuración](#5-documentación-de-configuración)
6. [Deployment y Infraestructura](#6-deployment-y-infraestructura)
7. [Monitoreo y Observabilidad](#7-monitoreo-y-observabilidad)
8. [Seguridad y Compliance](#8-seguridad-y-compliance)

---

## 1. ARQUITECTURA DEL SISTEMA

### 1.1 Vista General de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA MINI MARKET 2.0                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐│
│  │   CLIENT LAYER  │    │   CLIENT LAYER  │    │   CLIENT LAYER  ││
│  │                 │    │                 │    │                 ││
│  │  Desktop (Web)  │    │  Mobile (Web)   │    │  Tablet (Web)   ││
│  │  • Sidebar Nav  │    │ • Bottom Nav    │    │ • Hybrid Nav    ││
│  │  • Full Desktop │    │ • Touch First   │    │ • Responsive    ││
│  └─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘│
│            │                      │                      │        │
│            └──────────────────────┼──────────────────────┘        │
│                                   │                             │
│  ┌────────────────────────────────▼─────────────────────────────┐│
│  │                    APPLICATION TIER                           ││
│  │                                                             ││
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐    ││
│  │  │  React SPA    │  │   Auth Layer  │  │  State Mgmt   │    ││
│  │  │               │  │               │  │               │    ││
│  │  │ • React 18    │  │ • JWT Tokens  │  │ • Context API│    ││
│  │  │ • TypeScript  │  │ • RBAC        │  │ • React Query│    ││
│  │  │ • TailwindCSS │  │ • Sessions    │  │ • Cache Mgmt │    ││
│  │  │ • Vite Build  │  │ • Security    │  │ • Optimistic │    ││
│  │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘    ││
│  │          │                  │                  │            ││
│  │  ┌───────▼──────────┐  ┌───▼──────┐  ┌────────▼──────┐     ││
│  │  │   Edge Functions │  │  Cron    │  │   Storage     │     ││
│  │  │                 │  │  Jobs    │  │               │     ││
│  │  │ • Scraping Svc  │  │         │  │ • File Store  │     ││
│  │  │ • API Gateway   │  │ • Daily  │  │ • Exports     │     ││
│  │  │ • Alert System  │  │ • Weekly │  │ • Backups     │     ││
│  │  │ • Report Gen    │  │ • Hourly │  │ • Logs        │     ││
│  │  └───────┬─────────┘  └─────────┘  └───────────────┘     ││
│  │          │                                               ││
│  └──────────┼───────────────────────────────────────────────┘│
│             │                                               │
│  ┌──────────▼───────────────────────────────────────────────┐│
│  │                   DATA TIER                              ││
│  │                                                             ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      ││
│  │  │ PostgreSQL  │  │  Functions  │  │   Triggers  │      ││
│  │  │             │  │             │  │             │      ││
│  │  │ • 17 Tables │  │ • 7 PL/pgSQL│  │ • 24 Audit  │      ││
│  │  │ • Indexes   │  │ • Business  │  │ • Auto      │      ││
│  │  │ • Views     │  │   Logic     │  │   Update    │      ││
│  │  │ • Partitions│  │ • Validations│  │ • Cleanup   │      ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Componentes Principales

#### **Frontend Layer**
```
React SPA (Single Page Application)
├── Build System: Vite 4.x
├── UI Framework: React 18.x
├── Language: TypeScript 5.x
├── Styling: TailwindCSS 3.x
├── State Management: Context API + React Query
├── Routing: React Router v6
├── Forms: React Hook Form + Zod validation
├── Charts: Recharts + Chart.js
├── Date Handling: date-fns
└── Testing: Vitest + React Testing Library

Responsive Design System:
├── Breakpoints: 
│   ├── Mobile: <768px
│   ├── Tablet: 768px-1024px
│   └── Desktop: >1024px
├── Navigation Patterns:
│   ├── Desktop: Persistent sidebar
│   ├── Mobile: Bottom navigation
│   └── Tablet: Adaptive navigation
└── Component Library:
    ├── Design tokens (colors, spacing, typography)
    ├── Base components (Button, Input, Modal)
    ├── Business components (ProductCard, StockAlert)
    └── Layout components (Header, Sidebar, Footer)
```

#### **Backend Layer**
```
Supabase Edge Functions (Deno Runtime)
├── Runtime: Deno 1.x
├── Language: TypeScript
├── Framework: Custom serverless
├── HTTP Server: Native fetch API
├── Database: Supabase PostgreSQL client
├── Authentication: Supabase Auth
├── Storage: Supabase Storage
└── Real-time: Supabase Realtime

Edge Functions Deployed:
├── scraper-maxiconsumo (997 líneas)
│   ├── Web scraping engine
│   ├── Anti-detection mechanisms
│   ├── Rate limiting
│   └── Data processing
├── api-minimarket (Core system)
│   ├── REST API gateway
│   ├── Business logic handlers
│   ├── Authentication middleware
│   └── Response formatting
├── api-proveedor (910 líneas)
│   ├── Provider integration APIs
│   ├── Price comparison algorithms
│   ├── Opportunity detection
│   └── Analytics endpoints
├── alertas-stock (Alert system)
│   ├── Stock monitoring
│   ├── Alert generation
│   ├── Notification dispatch
│   └── Escalation logic
├── notificaciones-tareas (Task system)
│   ├── Task creation/management
│   ├── Notification scheduling
│   ├── Escalation handling
│   └── Performance tracking
└── reportes-automaticos (Reports)
    ├── Automated report generation
    ├── Data aggregation
    ├── Export formatting
    └── Distribution logic
```

#### **Database Layer**
```
PostgreSQL 15+ (Supabase Hosted)
├── Schema Design:
│   ├── Core tables (11 tables)
│   ├── Sprint 6 additions (6 tables)
│   ├── Audit tables (partitioned)
│   └── Analytics tables (materialized views)
├── Indexes Strategy:
│   ├── B-tree indexes for equality searches
│   ├── GIN indexes for JSONB operations
│   ├── Partial indexes for filtered queries
│   └── Composite indexes for complex queries
├── Functions (PL/pgSQL):
│   ├── Business logic encapsulation
│   ├── Data validation functions
│   ├── Analytics computations
│   └── Maintenance operations
├── Triggers (24 triggers):
│   ├── Audit trail triggers
│   ├── Automatic timestamp updates
│   ├── Data consistency enforcement
│   └── Performance optimization triggers
└── Views & Materialized Views:
    ├── Operational views (real-time data)
    ├── Analytical views (aggregated data)
    ├── Security views (filtered data)
    └── Performance views (cached queries)
```

---

## 2. DIAGRAMAS DE FLUJO ACTUALIZADOS

### 2.1 Flujo de Scraping de Precios

```mermaid
graph TD
    A[Cron Job Triggered<br/>00:00-06:00 Daily] --> B{System Health Check}
    B -->|Healthy| C[Load Product Categories]
    B -->|Unhealthy| D[Send Alert & Retry Later]
    
    C --> E[Initialize Scraper Engine]
    E --> F[Anti-Detection Setup]
    F --> G[Select Category<br/>Bebidas, Snacks, etc.]
    
    G --> H[Process Category Batch<br/>50 products per batch]
    H --> I{More products in category?}
    
    I -->|Yes| J[Apply Rate Limiting<br/>2-5 seconds delay]
    J --> K[Make HTTP Request]
    K --> L{Response OK?}
    
    L -->|Yes| M[Parse Product Data]
    L -->|No| N{Retry Attempts < 3?}
    N -->|Yes| O[Wait with Backoff]
    O --> J
    N -->|No| P[Log Error & Continue]
    P --> I
    
    M --> Q[Extract Price & Product Info]
    Q --> R[Match with Local Database<br/>SKU/EAN/Fuzzy Logic]
    R --> S{Match Found?}
    
    S -->|Yes| T[Update Price in Database]
    S -->|No| U[Create New Product Entry]
    S -->|Uncertain| V[Flag for Manual Review]
    
    T --> W[Calculate Price Changes]
    W --> X{Change > 15%?}
    X -->|Yes| Y[Generate Alert]
    X -->|No| Z[Store in History]
    
    U --> Z
    V --> Z
    Y --> AA[Add to Alert Queue]
    AA --> Z
    Z --> BB[Update Progress Stats]
    BB --> I
    
    I -->|No| CC[Process Next Category]
    CC --> G
    
    DD[All Categories Complete] --> EE[Generate Execution Report]
    EE --> FF[Update System Statistics]
    FF --> GG[Send Completion Notifications]
    GG --> HH[Activate Next Cron Job]
    
    style A fill:#e1f5fe
    style HH fill:#c8e6c9
    style D fill:#ffcdd2
    style Y fill:#fff3e0
```

### 2.2 Flujo de Gestión de Stock

```mermaid
graph TD
    A[Personal de Depósito] --> B[Access System]
    B --> C[Select Operation<br/>Entrada/Salida]
    
    C --> D[Product Search Interface]
    D --> E[Scan Barcode/Code]
    E --> F[Search Local Database]
    F --> G{Product Found?}
    
    G -->|Yes| H[Display Product Info]
    G -->|No| I[Manual Product Entry]
    I --> J[Create Product Record]
    J --> H
    
    H --> K[Enter Quantity]
    K --> L[Select Location/Area]
    L --> M[Add Optional Notes]
    M --> N[Submit Movement]
    
    N --> O[Validate Data]
    O --> P{Valid?}
    
    P -->|Yes| Q[Update Stock Levels]
    P -->|No| R[Show Validation Errors]
    R --> N
    
    Q --> S[Record Movement History]
    S --> T{Stock Below Minimum?}
    
    T -->|Yes| U[Generate Low Stock Alert]
    T -->|No| V[Update Dashboard Stats]
    
    U --> W[Add to Alert Queue]
    W --> X[Send Notifications]
    X --> Y[Log in Activity Feed]
    Y --> V
    
    V --> Z[Update Real-time Display]
    Z --> AA[Show Success Confirmation]
    AA --> BB[Return to Dashboard]
    
    style A fill:#e3f2fd
    style U fill:#fff3e0
    style BB fill:#e8f5e8
```

### 2.3 Flujo de Sistema de Tareas

```mermaid
graph TD
    A[User Creates Task] --> B[Task Creation Form]
    B --> C[Enter Task Details]
    C --> D[Set Priority & Due Date]
    D --> E[Assign to User/Team]
    E --> F[Submit Task]
    
    F --> G[Validate Task Data]
    G --> H{Valid?}
    
    H -->|Yes| I[Store in Database]
    H -->|No| J[Show Validation Errors]
    J --> C
    
    I --> K[Generate Task ID]
    K --> L[Log Creation Event]
    L --> M[Schedule Notifications]
    
    M --> N[Add to Daily Review Queue]
    N --> O[Cron Job: Check Pending Tasks<br/>Every 2 Hours]
    
    O --> P[Query Overdue Tasks]
    P --> Q[Check Notification Frequency]
    Q --> R{Sent in last 2 hours?}
    
    R -->|Yes| S[Skip Notification]
    R -->|No| T[Generate Alert]
    
    T --> U[Send Notification]
    U --> V[Update Notification Log]
    V --> W[Escalate if Critical]
    
    W --> X[Mark as Notified]
    X --> Y[Update Task Status]
    Y --> Z[Check for Auto-Completion]
    
    Z --> AA{Completion Criteria Met?}
    AA -->|Yes| BB[Auto-Complete Task]
    AA -->|No| CC[Wait for Manual Action]
    
    BB --> DD[Log Completion Event]
    CC --> EE[Continue Monitoring]
    
    FF[User Completes Task] --> GG[Log Completion]
    GG --> HH[Update Task Status]
    HH --> II[Notify Assignees]
    II --> JJ[Update Performance Metrics]
    
    style O fill:#e1f5fe
    style T fill:#fff3e0
    style BB fill:#c8e6c9
```

### 2.4 Flujo de API Requests

```mermaid
sequenceDiagram
    participant Client
    participant LoadBalancer
    participant API Gateway
    participant Auth Middleware
    participant Rate Limiter
    participant Business Logic
    participant Database
    
    Client->>LoadBalancer: HTTP Request
    LoadBalancer->>API Gateway: Forward Request
    
    API Gateway->>Auth Middleware: Validate Token
    Auth Middleware->>Auth Middleware: Check JWT Signature
    Auth Middleware->>Rate Limiter: Check Rate Limits
    
    alt Rate Limit OK
        Rate Limiter->>Business Logic: Process Request
        Business Logic->>Database: Query Data
        Database->>Business Logic: Return Data
        Business Logic->>API Gateway: Format Response
        API Gateway->>Client: 200 OK + Data
    else Rate Limit Exceeded
        Rate Limiter->>API Gateway: Rate Limit Error
        API Gateway->>Client: 429 Too Many Requests
    else Auth Failed
        Auth Middleware->>API Gateway: Auth Error
        API Gateway->>Client: 401 Unauthorized
    end
    
    Note over Client,Database: All requests include:<br/>- CORS headers<br/>- Security headers<br/>- Request ID for tracing<br/>- Timestamp for auditing
```

---

## 3. DOCUMENTACIÓN APIS COMPLETAS

### 3.1 OpenAPI 3.1 Specification

```yaml
openapi: 3.1.0
info:
  title: Mini Market API v2.0
  description: |
    Sistema completo de gestión para mini market con integración de proveedores,
    gestión de stock, sistema de tareas y dashboard operativo.
    
    ## Features
    - Gestión de productos y categorías
    - Integración con proveedores externos
    - Sistema de stock y depósito
    - Gestión de tareas pendientes
    - Dashboard y reportes
    - Sistema de alertas
    
    ## Authentication
    API utiliza autenticación JWT Bearer token.
    Obtén tu token desde `/auth/login`
    
  version: 2.0.0
  contact:
    name: Mini Market Support
    email: support@minimarket.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://htvlwhisjpdagqkqnpxg.supabase.co/functions/v1
    description: Production server
  - url: http://localhost:54321/functions/v1
    description: Local development server

security:
  - bearerAuth: []

paths:
  /api-minimarket:
    get:
      summary: Health check del sistema
      tags: [System]
      security: []
      responses:
        '200':
          description: Sistema operativo
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "operational"
                  version:
                    type: string
                    example: "2.0.0"
                  timestamp:
                    type: string
                    format: date-time
                  services:
                    type: object
                    properties:
                      database:
                        type: string
                        example: "healthy"
                      scraper:
                        type: string
                        example: "ready"

  /api-minimarket/categorias:
    get:
      summary: Listar categorías
      tags: [Categories]
      parameters:
        - name: activo
          in: query
          schema:
            type: boolean
          description: Filtrar por estado activo
        - name: limite
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 50
          description: Número máximo de resultados
        - name: offset
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
          description: Offset para paginación
      responses:
        '200':
          description: Lista de categorías
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Categoria'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
        
    post:
      summary: Crear nueva categoría
      tags: [Categories]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CategoriaInput'
      responses:
        '201':
          description: Categoría creada
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Categoria'
        '400':
          description: Error de validación
        '401':
          description: No autorizado

  /api-minimarket/categorias/{id}:
    get:
      summary: Obtener categoría por ID
      tags: [Categories]
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Detalles de categoría
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Categoria'
        '404':
          description: Categoría no encontrada
    
    put:
      summary: Actualizar categoría
      tags: [Categories]
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CategoriaInput'
      responses:
        '200':
          description: Categoría actualizada
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Categoria'
        '404':
          description: Categoría no encontrada
    
    delete:
      summary: Eliminar categoría
      tags: [Categories]
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: Categoría eliminada
        '404':
          description: Categoría no encontrada

  /api-minimarket/productos:
    get:
      summary: Listar productos con filtros
      tags: [Products]
      parameters:
        - name: categoria_id
          in: query
          schema:
            type: string
            format: uuid
          description: Filtrar por categoría
        - name: activo
          in: query
          schema:
            type: boolean
          description: Filtrar por estado activo
        - name: search
          in: query
          schema:
            type: string
          description: Búsqueda por nombre o código
        - name: stock_bajo
          in: query
          schema:
            type: boolean
          description: Filtrar productos con stock bajo
        - name: limite
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 50
        - name: offset
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
      responses:
        '200':
          description: Lista de productos
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Producto'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
                  filters_applied:
                    type: object
        
    post:
      summary: Crear nuevo producto
      tags: [Products]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProductoInput'
      responses:
        '201':
          description: Producto creado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Producto'

  /api-minimarket/productos/{id}:
    get:
      summary: Obtener producto por ID
      tags: [Products]
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Detalles del producto
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/Producto'
                  - type: object
                    properties:
                      stock_actual:
                        type: integer
                      ultima_actualizacion:
                        type: string
                        format: date-time
                      alertas_activas:
                        type: array
                        items:
                          type: string
        
    put:
      summary: Actualizar producto
      tags: [Products]
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProductoInput'
      responses:
        '200':
          description: Producto actualizado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Producto'

  /api-minimarket/proveedores:
    get:
      summary: Listar proveedores
      tags: [Suppliers]
      parameters:
        - name: activo
          in: query
          schema:
            type: boolean
        - name: limite
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 50
      responses:
        '200':
          description: Lista de proveedores
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Proveedor'
                  pagination:
                    $ref: '#/components/schemas/Pagination'

  /api-minimarket/precios:
    get:
      summary: Obtener historial de precios
      tags: [Prices]
      parameters:
        - name: producto_id
          in: query
          required: true
          schema:
            type: string
            format: uuid
        - name: fecha_desde
          in: query
          schema:
            type: string
            format: date
        - name: fecha_hasta
          in: query
          schema:
            type: string
            format: date
        - name: limite
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 1000
            default: 100
      responses:
        '200':
          description: Historial de precios
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/PrecioHistory'

    post:
      summary: Actualizar precios desde proveedor
      tags: [Prices]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                proveedor_id:
                  type: string
                  format: uuid
                force_update:
                  type: boolean
                  default: false
                categories:
                  type: array
                  items:
                    type: string
      responses:
        '202':
          description: Actualización iniciada
          content:
            application/json:
              schema:
                type: object
                properties:
                  job_id:
                    type: string
                    format: uuid
                  status:
                    type: string
                    example: "started"
                  estimated_duration:
                    type: integer
                    description: Minutos estimados

  /api-minimarket/stock:
    get:
      summary: Obtener estado actual de stock
      tags: [Stock]
      parameters:
        - name: deposito
          in: query
          schema:
            type: string
            default: "principal"
        - name: stock_bajo
          in: query
          schema:
            type: boolean
        - name: categoria_id
          in: query
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Estado de stock
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      allOf:
                        - $ref: '#/components/schemas/Producto'
                        - type: object
                          properties:
                            stock_actual:
                              type: integer
                            stock_minimo:
                              type: integer
                            ubicacion_fisica:
                              type: string
                            ultima_actualizacion:
                              type: string
                              format: date-time
                  summary:
                    type: object
                    properties:
                      total_productos:
                        type: integer
                      productos_stock_bajo:
                        type: integer
                      valor_total_inventario:
                        type: number
                        format: decimal

    post:
      summary: Registrar movimiento de stock
      tags: [Stock]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MovimientoStock'
      responses:
        '201':
          description: Movimiento registrado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MovimientoStock'

  /api-minimarket/deposito:
    get:
      summary: Historial de movimientos del depósito
      tags: [Deposit]
      parameters:
        - name: fecha_desde
          in: query
          schema:
            type: string
            format: date
        - name: fecha_hasta
          in: query
          schema:
            type: string
            format: date
        - name: tipo_movimiento
          in: query
          schema:
            type: string
            enum: [entrada, salida]
        - name: usuario_id
          in: query
          schema:
            type: string
            format: uuid
        - name: limite
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 50
      responses:
        '200':
          description: Historial de movimientos
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/MovimientoDeposito'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
                  summary:
                    type: object
                    properties:
                      total_movimientos:
                        type: integer
                      entradas_total:
                        type: integer
                      salidas_total:
                        type: integer
                      valor_movimientos:
                        type: object
                        properties:
                          entradas:
                            type: number
                          salidas:
                            type: number

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Categoria:
      type: object
      properties:
        id:
          type: string
          format: uuid
        codigo:
          type: string
          maxLength: 20
        nombre:
          type: string
          maxLength: 100
        descripcion:
          type: string
        parent_id:
          type: string
          format: uuid
        nivel:
          type: integer
          minimum: 1
        activo:
          type: boolean
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    CategoriaInput:
      type: object
      required: [nombre, codigo]
      properties:
        codigo:
          type: string
          maxLength: 20
        nombre:
          type: string
          maxLength: 100
        descripcion:
          type: string
        parent_id:
          type: string
          format: uuid
        margen_minimo:
          type: number
          format: decimal
          minimum: 0
          maximum: 100
        margen_maximo:
          type: number
          format: decimal
          minimum: 0
          maximum: 100

    Producto:
      type: object
      properties:
        id:
          type: string
          format: uuid
        nombre:
          type: string
          maxLength: 255
        descripcion:
          type: string
        codigo_barras:
          type: string
          maxLength: 100
        sku:
          type: string
          maxLength: 50
        categoria_id:
          type: string
          format: uuid
        marca:
          type: string
          maxLength: 100
        contenido_neto:
          type: string
          maxLength: 50
        dimensiones:
          type: object
        precio_sugerido:
          type: number
          format: decimal
          minimum: 0
        activo:
          type: boolean
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    ProductoInput:
      type: object
      required: [nombre, categoria_id]
      properties:
        nombre:
          type: string
          maxLength: 255
        descripcion:
          type: string
        codigo_barras:
          type: string
          maxLength: 100
        sku:
          type: string
          maxLength: 50
        categoria_id:
          type: string
          format: uuid
        marca:
          type: string
          maxLength: 100
        contenido_neto:
          type: string
          maxLength: 50
        dimensiones:
          type: object
        precio_sugerido:
          type: number
          format: decimal
          minimum: 0
        observaciones:
          type: string

    Proveedor:
      type: object
      properties:
        id:
          type: string
          format: uuid
        nombre:
          type: string
          maxLength: 255
        direccion:
          type: string
        telefono:
          type: string
          maxLength: 20
        email:
          type: string
          format: email
        sitio_web:
          type: string
          format: uri
        activo:
          type: boolean
        configuracion:
          type: object
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    PrecioHistory:
      type: object
      properties:
        id:
          type: string
          format: uuid
        producto_id:
          type: string
          format: uuid
        precio_compra:
          type: number
          format: decimal
        precio_venta:
          type: number
          format: decimal
        fecha_vigencia:
          type: string
          format: date-time
        proveedor_id:
          type: string
          format: uuid
        observaciones:
          type: string

    MovimientoStock:
      type: object
      required: [producto_id, tipo_movimiento, cantidad]
      properties:
        producto_id:
          type: string
          format: uuid
        tipo_movimiento:
          type: string
          enum: [entrada, salida, ajuste]
        cantidad:
          type: integer
          minimum: 1
        ubicacion_fisica:
          type: string
          maxLength: 100
        observaciones:
          type: string

    MovimientoDeposito:
      type: object
      properties:
        id:
          type: string
          format: uuid
        producto_id:
          type: string
          format: uuid
        tipo_movimiento:
          type: string
          enum: [entrada, salida]
        cantidad:
          type: integer
        usuario_id:
          type: string
          format: uuid
        ubicacion_fisica:
          type: string
        observaciones:
          type: string
        created_at:
          type: string
          format: date-time

    Pagination:
      type: object
      properties:
        total:
          type: integer
        limite:
          type: integer
        offset:
          type: integer
        has_next:
          type: boolean
        has_prev:
          type: boolean

  responses:
    BadRequest:
      description: Error de validación
      content:
        application/json:
          schema:
            type: object
            properties:
              success:
                type: boolean
                example: false
              error:
                type: object
                properties:
                  code:
                    type: string
                    example: "VALIDATION_ERROR"
                  message:
                    type: string
                  details:
                    type: array
                    items:
                      type: object

    Unauthorized:
      description: No autorizado
      content:
        application/json:
          schema:
            type: object
            properties:
              success:
                type: boolean
                example: false
              error:
                type: object
                properties:
                  code:
                    type: string
                    example: "UNAUTHORIZED"
                  message:
                    type: string
                    example: "Token de autenticación requerido"

    NotFound:
      description: Recurso no encontrado
      content:
        application/json:
          schema:
            type: object
            properties:
              success:
                type: boolean
                example: false
              error:
                type: object
                properties:
                  code:
                    type: string
                    example: "NOT_FOUND"
                  message:
                    type: string

    InternalError:
      description: Error interno del servidor
      content:
        application/json:
          schema:
            type: object
            properties:
              success:
                type: boolean
                example: false
              error:
                type: object
                properties:
                  code:
                    type: string
                    example: "INTERNAL_ERROR"
                  message:
                    type: string

tags:
  - name: System
    description: Endpoints del sistema
  - name: Categories
    description: Gestión de categorías
  - name: Products
    description: Gestión de productos
  - name: Suppliers
    description: Gestión de proveedores
  - name: Prices
    description: Gestión de precios
  - name: Stock
    description: Gestión de stock
  - name: Deposit
    description: Operaciones de depósito
```

### 3.2 Endpoints Específicos del Proveedor

```typescript
// API del Proveedor (Maxiconsumo Necochea)
const PROVEEDOR_API_ENDPOINTS = {
  // Health check
  '/api-proveedor/status': {
    method: 'GET',
    description: 'Estado del servicio de proveedor',
    response: {
      status: 'operational' | 'degraded' | 'down',
      last_scraping: string,
      products_count: number,
      uptime: number
    }
  },

  // Precios actuales
  '/api-proveedor/precios': {
    method: 'GET',
    description: 'Obtener precios actuales del proveedor',
    params: {
      categoria?: string,
      limite?: number,
      offset?: number
    },
    response: {
      data: Array<{
        sku: string,
        nombre: string,
        precio: number,
        categoria: string,
        disponible: boolean,
        ultima_actualizacion: string
      }>,
      pagination: PaginationInfo
    }
  },

  // Productos disponibles
  '/api-proveedor/productos': {
    method: 'GET',
    description: 'Catálogo completo de productos',
    params: {
      categoria?: string,
      marca?: string,
      search?: string,
      disponible?: boolean,
      limite?: number
    },
    response: {
      data: Array<ProductoProveedor>,
      categorias: Array<string>,
      marcas: Array<string>
    }
  },

  // Comparación de precios
  '/api-proveedor/comparacion': {
    method: 'GET',
    description: 'Comparación con precios del sistema',
    params: {
      product_ids?: string[],
      min_difference?: number
    },
    response: {
      oportunidades: Array<{
        producto_id: string,
        precio_proveedor: number,
        precio_sistema: number,
        diferencia_absoluta: number,
        diferencia_porcentual: number,
        confianza_match: number
      }>,
      resumen: {
        total_analizados: number,
        oportunidades_encontradas: number,
        ahorro_potencial: number
      }
    }
  },

  // Sincronización manual
  '/api-proveedor/sincronizar': {
    method: 'POST',
    auth: true,
    body: {
      categorias?: string[],
      force_update?: boolean,
      test_mode?: boolean
    },
    response: {
      job_id: string,
      status: 'started',
      estimated_duration: number,
      categorias_incluidas: string[]
    }
  },

  // Alertas activas
  '/api-proveedor/alertas': {
    method: 'GET',
    description: 'Alertas de cambios de precios',
    response: {
      alertas: Array<{
        id: string,
        producto: string,
        precio_anterior: number,
        precio_nuevo: number,
        cambio_porcentual: number,
        severidad: 'baja' | 'media' | 'alta' | 'critica',
        fecha_alerta: string
      }>
    }
  },

  // Estadísticas del scraper
  '/api-proveedor/estadisticas': {
    method: 'GET',
    auth: true,
    response: {
      ultima_ejecucion: {
        fecha: string,
        productos_encontrados: number,
        productos_procesados: number,
        tasa_exito: number,
        tiempo_ejecucion: number
      },
      resumen_mensual: {
        total_ejecuciones: number,
        productos_promedio: number,
        disponibilidad_promedio: number
      }
    }
  }
}
```

---

## 4. ESQUEMAS DE BASE DE DATOS

### 4.1 Esquema Completo Actualizado

```sql
-- ============================================================================
-- ESQUEMA COMPLETO BASE DE DATOS - SISTEMA MINI MARKET V2.0
-- ============================================================================
-- Actualizado: 1 de noviembre de 2025
-- Estado: PRODUCCIÓN ENTERPRISE
-- ============================================================================

-- ============================================================================
-- 1. TABLAS PRINCIPALES (Core System)
-- ============================================================================

-- Tabla de categorías
CREATE TABLE categorias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    parent_id UUID REFERENCES categorias(id),
    nivel INTEGER NOT NULL DEFAULT 1,
    margen_minimo DECIMAL(5,2) DEFAULT 0,
    margen_maximo DECIMAL(5,2) DEFAULT 100,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de productos
CREATE TABLE productos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    codigo_barras VARCHAR(100) UNIQUE,
    sku VARCHAR(50) UNIQUE,
    categoria_id UUID REFERENCES categorias(id),
    marca VARCHAR(100),
    contenido_neto VARCHAR(50),
    dimensiones JSONB,
    activo BOOLEAN DEFAULT TRUE,
    precio_sugerido DECIMAL(12,2),
    observaciones TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de proveedores
CREATE TABLE proveedores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(255) NOT NULL,
    direccion TEXT,
    telefono VARCHAR(20),
    email VARCHAR(100),
    sitio_web VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    configuracion JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de stock de depósito
CREATE TABLE stock_deposito (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id UUID REFERENCES productos(id) ON DELETE CASCADE,
    deposito VARCHAR(100) DEFAULT 'principal',
    stock_actual INTEGER DEFAULT 0,
    stock_minimo INTEGER DEFAULT 0,
    stock_maximo INTEGER DEFAULT 0,
    ubicacion_fisica VARCHAR(100),
    ultima_actualizacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de movimientos de depósito
CREATE TABLE movimientos_deposito (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id UUID REFERENCES productos(id),
    tipo_movimiento VARCHAR(20) CHECK (tipo_movimiento IN ('entrada', 'salida', 'ajuste')),
    cantidad INTEGER NOT NULL,
    usuario_id UUID,
    ubicacion_fisica VARCHAR(100),
    observaciones TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de productos faltantes
CREATE TABLE productos_faltantes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id UUID REFERENCES productos(id),
    fecha_deteccion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resuelto BOOLEAN DEFAULT FALSE,
    fecha_resolucion TIMESTAMPTZ,
    proveedor_sugerido UUID REFERENCES proveedores(id),
    notas TEXT
);

-- Tabla de tareas pendientes
CREATE TABLE tareas_pendientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(50) NOT NULL,
    prioridad VARCHAR(20) DEFAULT 'media' CHECK (prioridad IN ('baja', 'media', 'alta', 'critica')),
    estado VARCHAR(20) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'en_progreso', 'completada', 'cancelada')),
    asignado_a UUID,
    creado_por UUID NOT NULL,
    fecha_vencimiento TIMESTAMPTZ,
    fecha_completado TIMESTAMPTZ,
    notas_completado TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de notificaciones de tareas
CREATE TABLE notificaciones_tareas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tarea_id UUID REFERENCES tareas_pendientes(id),
    tipo VARCHAR(50) NOT NULL,
    destinatario UUID,
    mensaje TEXT NOT NULL,
    enviada BOOLEAN DEFAULT FALSE,
    fecha_envio TIMESTAMPTZ,
    intentos INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de personal
CREATE TABLE personal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    rol VARCHAR(50) NOT NULL CHECK (rol IN ('admin', 'deposito', 'ventas', 'supervisor')),
    activo BOOLEAN DEFAULT TRUE,
    fecha_ingreso DATE DEFAULT CURRENT_DATE,
    configuracion JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. TABLAS SPRINT 6 (Integración Proveedores)
-- ============================================================================

-- Tabla de precios por proveedor
CREATE TABLE precios_proveedor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id UUID REFERENCES productos(id) ON DELETE CASCADE,
    proveedor_id UUID REFERENCES proveedores(id) ON DELETE CASCADE,
    precio_compra DECIMAL(12,2) NOT NULL,
    precio_anterior DECIMAL(12,2),
    fecha_vigencia_desde TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    fecha_vigencia_hasta TIMESTAMPTZ,
    moneda VARCHAR(3) DEFAULT 'ARS',
    es_precio_vigente BOOLEAN DEFAULT TRUE,
    descuento_volumen JSONB,
    condiciones_pago VARCHAR(100),
    tiempo_entrega_dias INTEGER DEFAULT 1,
    cantidad_minima_pedido INTEGER DEFAULT 1,
    notas TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT one_vigente_price_per_product_provider 
        CHECK (
            NOT EXISTS (
                SELECT 1 FROM precios_proveedor pp2 
                WHERE pp2.producto_id = precios_proveedor.producto_id 
                AND pp2.proveedor_id = precios_proveedor.proveedor_id 
                AND pp2.es_precio_vigente = TRUE 
                AND pp2.id != precios_proveedor.id
            )
        )
);

-- Tabla de comparación de precios
CREATE TABLE comparacion_precios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id UUID REFERENCES productos(id) ON DELETE CASCADE,
    precio_proveedor DECIMAL(12,2) NOT NULL,
    precio_sistema DECIMAL(12,2) NOT NULL,
    diferencia_absoluta DECIMAL(12,2) NOT NULL,
    diferencia_porcentual DECIMAL(5,2) NOT NULL,
    proveedor_id UUID REFERENCES proveedores(id) ON DELETE CASCADE,
    fecha_comparacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    stock_disponible BOOLEAN DEFAULT TRUE,
    confianza_match DECIMAL(3,2) DEFAULT 0.95,
    estrategia_match VARCHAR(50),
    activa BOOLEAN DEFAULT TRUE,
    metadata JSONB
);

-- Tabla de alertas de cambios de precios
CREATE TABLE alertas_cambios_precios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id UUID REFERENCES productos(id) ON DELETE CASCADE,
    precio_anterior DECIMAL(12,2) NOT NULL,
    precio_nuevo DECIMAL(12,2) NOT NULL,
    cambio_absoluto DECIMAL(12,2) NOT NULL,
    cambio_porcentual DECIMAL(5,2) NOT NULL,
    proveedor_id UUID REFERENCES proveedores(id) ON DELETE CASCADE,
    severidad VARCHAR(20) CHECK (severidad IN ('baja', 'media', 'alta', 'critica')),
    fecha_alerta TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    procesada BOOLEAN DEFAULT FALSE,
    fecha_procesamiento TIMESTAMPTZ,
    notas TEXT,
    metadata JSONB
);

-- Tabla de estadísticas de scraping
CREATE TABLE estadisticas_scraping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    categoria VARCHAR(100),
    productos_encontrados INTEGER DEFAULT 0,
    productos_procesados INTEGER DEFAULT 0,
    productos_exitosos INTEGER DEFAULT 0,
    productos_fallidos INTEGER DEFAULT 0,
    tiempo_ejecucion_segundos INTEGER,
    tasa_exito DECIMAL(5,2),
    fecha_inicio TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMPTZ,
    error_mensaje TEXT,
    metadata JSONB
);

-- Tabla de logs de scraping
CREATE TABLE logs_scraping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    nivel VARCHAR(20) CHECK (nivel IN ('debug', 'info', 'warn', 'error')),
    mensaje TEXT NOT NULL,
    categoria VARCHAR(100),
    producto_sku VARCHAR(100),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Tabla de configuración de proveedor
CREATE TABLE configuracion_proveedor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proveedor_id UUID REFERENCES proveedores(id) ON DELETE CASCADE,
    clave VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    descripcion TEXT,
    tipo_dato VARCHAR(50) DEFAULT 'string' CHECK (tipo_dato IN ('string', 'number', 'boolean', 'json')),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(proveedor_id, clave)
);

-- ============================================================================
-- 3. ÍNDICES ESTRATÉGICOS
-- ============================================================================

-- Índices para performance
CREATE INDEX idx_productos_categoria_id ON productos(categoria_id) WHERE categoria_id IS NOT NULL;
CREATE INDEX idx_productos_codigo_barras ON productos(codigo_barras) WHERE codigo_barras IS NOT NULL;
CREATE INDEX idx_productos_sku ON productos(sku) WHERE sku IS NOT NULL;
CREATE INDEX idx_productos_activo ON productos(activo) WHERE activo = TRUE;
CREATE INDEX idx_productos_nombre_gin ON productos USING GIN(to_tsvector('spanish', nombre));
CREATE INDEX idx_productos_dimensiones_gin ON productos USING GIN(dimensiones);

CREATE INDEX idx_stock_deposito_producto ON stock_deposito(producto_id);
CREATE INDEX idx_stock_deposito_deposito ON stock_deposito(deposito);
CREATE INDEX idx_stock_deposito_stock_bajo ON stock_deposito(producto_id, stock_actual, stock_minimo) 
    WHERE stock_actual <= stock_minimo;

CREATE INDEX idx_movimientos_deposito_producto ON movimientos_deposito(producto_id);
CREATE INDEX idx_movimientos_deposito_fecha ON movimientos_deposito(created_at DESC);
CREATE INDEX idx_movimientos_deposito_tipo ON movimientos_deposito(tipo_movimiento);

CREATE INDEX idx_tareas_pendientes_estado ON tareas_pendientes(estado) WHERE estado = 'pendiente';
CREATE INDEX idx_tareas_pendientes_vencimiento ON tareas_pendientes(fecha_vencimiento) 
    WHERE estado IN ('pendiente', 'en_progreso');
CREATE INDEX idx_tareas_pendientes_prioridad ON tareas_pendientes(prioridad);

-- Índices Sprint 6
CREATE INDEX idx_precios_proveedor_producto ON precios_proveedor(producto_id);
CREATE INDEX idx_precios_proveedor_proveedor ON precios_proveedor(proveedor_id);
CREATE INDEX idx_precios_proveedor_vigente ON precios_proveedor(es_precio_vigente) WHERE es_precio_vigente = TRUE;
CREATE INDEX idx_precios_proveedor_fecha ON precios_proveedor(fecha_vigencia_desde);

CREATE INDEX idx_comparacion_precios_producto ON comparacion_precios(producto_id);
CREATE INDEX idx_comparacion_precios_proveedor ON comparacion_precios(proveedor_id);
CREATE INDEX idx_comparacion_precios_ahorro ON comparacion_precios(diferencia_porcentual DESC) WHERE diferencia_porcentual > 0;
CREATE INDEX idx_comparacion_precios_activa ON comparacion_precios(activa) WHERE activa = TRUE;

CREATE INDEX idx_alertas_cambios_precios_producto ON alertas_cambios_precios(producto_id);
CREATE INDEX idx_alertas_cambios_precios_severidad ON alertas_cambios_precios(severidad);
CREATE INDEX idx_alertas_cambios_precios_procesada ON alertas_cambios_precios(procesada) WHERE procesada = FALSE;
CREATE INDEX idx_alertas_cambios_precios_fecha ON alertas_cambios_precios(fecha_alerta DESC);

CREATE INDEX idx_estadisticas_scraping_job ON estadisticas_scraping(job_id);
CREATE INDEX idx_estadisticas_scraping_fecha ON estadisticas_scraping(fecha_inicio DESC);

CREATE INDEX idx_logs_scraping_job ON logs_scraping(job_id);
CREATE INDEX idx_logs_scraping_nivel ON logs_scraping(nivel);
CREATE INDEX idx_logs_scraping_timestamp ON logs_scraping(timestamp DESC);

-- ============================================================================
-- 4. VISTAS OPERACIONALES
-- ============================================================================

-- Vista para productos con stock
CREATE VIEW vista_productos_con_stock AS
SELECT 
    p.id,
    p.nombre,
    p.codigo_barras,
    p.sku,
    p.marca,
    p.precio_sugerido,
    c.nombre as categoria,
    COALESCE(s.stock_actual, 0) as stock_actual,
    COALESCE(s.stock_minimo, 0) as stock_minimo,
    COALESCE(s.stock_maximo, 0) as stock_maximo,
    CASE 
        WHEN COALESCE(s.stock_actual, 0) = 0 THEN 'sin_stock'
        WHEN COALESCE(s.stock_actual, 0) <= s.stock_minimo THEN 'stock_bajo'
        ELSE 'stock_ok'
    END as estado_stock,
    p.created_at,
    p.updated_at
FROM productos p
LEFT JOIN stock_deposito s ON p.id = s.producto_id AND s.deposito = 'principal'
LEFT JOIN categorias c ON p.categoria_id = c.id
WHERE p.activo = TRUE;

-- Vista para oportunidades de ahorro
CREATE VIEW vista_oportunidades_ahorro AS
SELECT 
    cp.id,
    cp.producto_id,
    p.nombre as producto_nombre,
    p.codigo_barras,
    p.sku,
    pr.nombre as proveedor_nombre,
    cp.precio_proveedor,
    cp.precio_sistema,
    cp.diferencia_absoluta,
    cp.diferencia_porcentual,
    cp.fecha_comparacion,
    cp.confianza_match,
    CASE 
        WHEN cp.diferencia_porcentual >= 25 THEN 'excelente'
        WHEN cp.diferencia_porcentual >= 15 THEN 'buena'
        WHEN cp.diferencia_porcentual >= 10 THEN 'regular'
        ELSE 'baja'
    END as calidad_oportunidad,
    cp.activa
FROM comparacion_precios cp
JOIN productos p ON cp.producto_id = p.id
JOIN proveedores pr ON cp.proveedor_id = pr.id
WHERE cp.activa = TRUE 
AND cp.diferencia_porcentual > 5
AND p.activo = TRUE
ORDER BY cp.diferencia_porcentual DESC;

-- Vista para alertas activas
CREATE VIEW vista_alertas_activas AS
SELECT 
    acp.id,
    acp.producto_id,
    p.nombre as producto_nombre,
    p.codigo_barras,
    p.sku,
    pr.nombre as proveedor_nombre,
    acp.precio_anterior,
    acp.precio_nuevo,
    acp.cambio_absoluto,
    acp.cambio_porcentual,
    acp.severidad,
    acp.fecha_alerta,
    CASE 
        WHEN acp.severidad = 'critica' AND acp.fecha_alerta < NOW() - INTERVAL '1 hour' THEN 'vencida'
        WHEN acp.severidad = 'alta' AND acp.fecha_alerta < NOW() - INTERVAL '4 hours' THEN 'vencida'
        WHEN acp.procesada = TRUE THEN 'procesada'
        ELSE 'activa'
    END as estado_alerta
FROM alertas_cambios_precios acp
JOIN productos p ON acp.producto_id = p.id
JOIN proveedores pr ON acp.proveedor_id = pr.id
WHERE acp.procesada = FALSE
AND p.activo = TRUE
ORDER BY 
    CASE acp.severidad
        WHEN 'critica' THEN 1
        WHEN 'alta' THEN 2
        WHEN 'media' THEN 3
        WHEN 'baja' THEN 4
    END,
    acp.fecha_alerta DESC;

-- ============================================================================
-- 5. FUNCIONES PL/pgSQL
-- ============================================================================

-- Función para actualizar estadísticas de scraping
CREATE OR REPLACE FUNCTION fnc_actualizar_estadisticas_scraping(
    p_job_id UUID,
    p_categoria VARCHAR(100),
    p_productos_encontrados INTEGER,
    p_productos_procesados INTEGER,
    p_productos_exitosos INTEGER,
    p_productos_fallidos INTEGER,
    p_tiempo_ejecucion INTEGER,
    p_fecha_fin TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
) RETURNS UUID AS $$
DECLARE
    v_tasa_exito DECIMAL(5,2);
    v_stat_id UUID;
BEGIN
    -- Calculate success rate
    v_tasa_exito := CASE 
        WHEN p_productos_procesados > 0 
        THEN (p_productos_exitosos::DECIMAL / p_productos_procesados::DECIMAL) * 100
        ELSE 0
    END;
    
    -- Insert statistics record
    INSERT INTO estadisticas_scraping (
        job_id,
        categoria,
        productos_encontrados,
        productos_procesados,
        productos_exitosos,
        productos_fallidos,
        tiempo_ejecucion_segundos,
        tasa_exito,
        fecha_fin
    ) VALUES (
        p_job_id,
        p_categoria,
        p_productos_encontrados,
        p_productos_procesados,
        p_productos_exitosos,
        p_productos_fallidos,
        p_tiempo_ejecucion,
        v_tasa_exito,
        p_fecha_fin
    ) RETURNING id INTO v_stat_id;
    
    RETURN v_stat_id;
END;
$$ LANGUAGE plpgsql;

-- Función para detectar cambios significativos de precios
CREATE OR REPLACE FUNCTION fnc_deteccion_cambios_significativos(
    p_producto_id UUID,
    p_precio_nuevo DECIMAL(12,2),
    p_proveedor_id UUID
) RETURNS VOID AS $$
DECLARE
    v_precio_anterior DECIMAL(12,2);
    v_cambio_absoluto DECIMAL(12,2);
    v_cambio_porcentual DECIMAL(5,2);
    v_severidad VARCHAR(20);
BEGIN
    -- Get previous price for this product from same provider
    SELECT precio_compra INTO v_precio_anterior
    FROM precios_proveedor
    WHERE producto_id = p_producto_id
    AND proveedor_id = p_proveedor_id
    AND es_precio_vigente = TRUE
    AND fecha_vigencia_hasta IS NULL
    ORDER BY created_at DESC
    LIMIT 1;
    
    -- Only proceed if we found a previous price
    IF v_precio_anterior IS NOT NULL THEN
        -- Calculate changes
        v_cambio_absoluto := p_precio_nuevo - v_precio_anterior;
        v_cambio_porcentual := (v_cambio_absoluto / v_precio_anterior) * 100;
        
        -- Determine severity
        v_severidad := CASE 
            WHEN ABS(v_cambio_porcentual) >= 50 THEN 'critica'
            WHEN ABS(v_cambio_porcentual) >= 25 THEN 'alta'
            WHEN ABS(v_cambio_porcentual) >= 15 THEN 'media'
            WHEN ABS(v_cambio_porcentual) >= 10 THEN 'baja'
            ELSE NULL
        END;
        
        -- Create alert if significant change detected
        IF v_severidad IS NOT NULL THEN
            INSERT INTO alertas_cambios_precios (
                producto_id,
                precio_anterior,
                precio_nuevo,
                cambio_absoluto,
                cambio_porcentual,
                proveedor_id,
                severidad
            ) VALUES (
                p_producto_id,
                v_precio_anterior,
                p_precio_nuevo,
                v_cambio_absoluto,
                v_cambio_porcentual,
                p_proveedor_id,
                v_severidad
            );
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. TRIGGERS
-- ============================================================================

-- Función para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar triggers de updated_at
CREATE TRIGGER update_productos_updated_at 
    BEFORE UPDATE ON productos 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_proveedores_updated_at 
    BEFORE UPDATE ON proveedores 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_precios_proveedor_updated_at 
    BEFORE UPDATE ON precios_proveedor 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_personal_updated_at 
    BEFORE UPDATE ON personal 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tareas_pendientes_updated_at 
    BEFORE UPDATE ON tareas_pendientes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 7. DATOS INICIALES
-- ============================================================================

-- Insertar categorías principales
INSERT INTO categorias (codigo, nombre, descripcion, nivel) VALUES
('BEBIDAS', 'Bebidas', 'Bebidas frías y calientes', 1),
('SNACKS', 'Snacks y golosinas', 'Chips, galletas, chocolates', 1),
('LACTEOS', 'Lácteos', 'Leches, quesos, yogures', 1),
('CARNES', 'Carnes y embutidos', 'Carnes frescas y procesadas', 1),
('PANADERIA', 'Panadería', 'Pan, facturas, integrales', 1),
('LIMPIEZA', 'Limpieza', 'Productos de limpieza y higiene', 1),
('CONGELADOS', 'Congelados', 'Alimentos congelados', 1),
('ALIMENTOS', 'Alimentos básicos', 'Arroz, pastas, conservas', 1),
('PERFUMERIA', 'Perfumería', 'Perfumes, cosméticos', 1);

-- Insertar proveedores
INSERT INTO proveedores (nombre, direccion, telefono, email, sitio_web) VALUES
('Maxiconsumo Necochea', 'Necochea, Buenos Aires', '2262-XXXXX', 'info@maxiconsumo.com.ar', 'https://maxiconsumo.com.ar'),
('Distribuidora Local', 'Centro de la ciudad', '2262-XXXXX', 'ventas@distlocal.com', NULL),
('Mayorista Norte', 'Avenida Principal 123', '2262-XXXXX', 'mayorista@norte.com', NULL);

-- Insertar personal inicial
INSERT INTO personal (nombre, email, rol) VALUES
('Administrador Sistema', 'admin@minimarket.com', 'admin'),
('Encargado Depósito', 'deposito@minimarket.com', 'deposito'),
('Vendedor Senior', 'ventas@minimarket.com', 'ventas');

COMMIT;
```

---

## 5. DOCUMENTACIÓN DE CONFIGURACIÓN

### 5.1 Variables de Entorno

```env
# ============================================================================
# CONFIGURACIÓN SISTEMA MINI MARKET V2.0
# ============================================================================

# ----------------------------------------------------------------------------
# SUPABASE CONFIGURATION
# ----------------------------------------------------------------------------
SUPABASE_URL=https://htvlwhisjpdagqkqnpxg.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ----------------------------------------------------------------------------
# DATABASE CONFIGURATION
# ----------------------------------------------------------------------------
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.htvlwhisjpdagqkqnpxg.supabase.co:5432/postgres
DB_POOL_SIZE=20
DB_TIMEOUT=30000
DB_SSL_MODE=require

# ----------------------------------------------------------------------------
# EDGE FUNCTIONS CONFIGURATION
# ----------------------------------------------------------------------------
# Scraping Configuration
SCRAPER_MAX_DELAY=5000
SCRAPER_MIN_DELAY=2000
SCRAPER_USER_AGENT_ROTATION=true
SCRAPER_CAPTCHA_BYPASS=true
SCRAPER_CONCURRENT_REQUESTS=3
SCRAPER_RETRY_ATTEMPTS=3
SCRAPER_TIMEOUT=30000

# Provider Configuration
PROVIDER_MAXICONSUMO_URL=https://maxiconsumo.com.ar
PROVIDER_MAXICONSUMO_CATEGORIES=bebidas,snacks,lacteos,carnes,panaderia,limpieza,congelados,alimentos,perfumeria
PROVIDER_BATCH_SIZE=50
PROVIDER_RATE_LIMIT_PER_MINUTE=12

# ----------------------------------------------------------------------------
# API CONFIGURATION
# ----------------------------------------------------------------------------
API_RATE_LIMIT_PUBLIC=100
API_RATE_LIMIT_PRIVATE=10
API_CACHE_TTL_SECONDS=300
API_MAX_REQUEST_SIZE=10485760
API_REQUEST_TIMEOUT=30000

# JWT Configuration
JWT_SECRET=[YOUR-SUPER-SECRET-JWT-KEY]
JWT_EXPIRATION=24h
JWT_REFRESH_EXPIRATION=7d

# ----------------------------------------------------------------------------
# CACHE CONFIGURATION
# ----------------------------------------------------------------------------
CACHE_DRIVER=memory
CACHE_PREFIX=minimarket
CACHE_DEFAULT_TTL=3600
CACHE_MAX_SIZE=100
CACHE_CLEANUP_INTERVAL=300

# ----------------------------------------------------------------------------
# LOGGING CONFIGURATION
# ----------------------------------------------------------------------------
LOG_LEVEL=info
LOG_FORMAT=json
LOG_FILE_ENABLED=false
LOG_MAX_FILES=30
LOG_MAX_SIZE=100MB

# Performance Logging
PERFORMANCE_LOGGING=true
SLOW_QUERY_THRESHOLD=1000
MEMORY_USAGE_LOGGING=true

# ----------------------------------------------------------------------------
# SECURITY CONFIGURATION
# ----------------------------------------------------------------------------
CORS_ORIGINS=https://lefkn5kbqv2o.space.minimax.io,http://localhost:3000
CSRF_PROTECTION=true
RATE_LIMITING=true
SECURITY_HEADERS=true

# Input Validation
MAX_STRING_LENGTH=1000
MAX_ARRAY_LENGTH=100
ALLOWED_FILE_TYPES=pdf,jpg,png,csv,xlsx
MAX_FILE_SIZE=10485760

# ----------------------------------------------------------------------------
# NOTIFICATION CONFIGURATION
# ----------------------------------------------------------------------------
EMAIL_ENABLED=false
EMAIL_FROM=noreply@minimarket.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=[your-email@gmail.com]
SMTP_PASS=[your-app-password]

# Push Notifications (Future)
PUSH_NOTIFICATIONS_ENABLED=false
VAPID_PUBLIC_KEY=[your-vapid-public-key]
VAPID_PRIVATE_KEY=[your-vapid-private-key]

# ----------------------------------------------------------------------------
# MONITORING CONFIGURATION
# ----------------------------------------------------------------------------
MONITORING_ENABLED=true
HEALTH_CHECK_INTERVAL=300
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=85
ALERT_THRESHOLD_DISK=90

# Metrics Collection
METRICS_ENABLED=true
METRICS_RETENTION_DAYS=30
PERFORMANCE_METRICS=true
BUSINESS_METRICS=true

# ----------------------------------------------------------------------------
# BACKUP CONFIGURATION
# ----------------------------------------------------------------------------
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=minimarket-backups
BACKUP_COMPRESSION=true

# ----------------------------------------------------------------------------
# DEVELOPMENT CONFIGURATION
# ----------------------------------------------------------------------------
NODE_ENV=production
DEBUG_MODE=false
HOT_RELOAD=false
SOURCE_MAPS=true

# Testing Configuration
TEST_DATABASE_URL=postgresql://postgres:[TEST-PASSWORD]@localhost:5432/minimarket_test
TEST_TIMEOUT=30000
COVERAGE_THRESHOLD=80

# ----------------------------------------------------------------------------
# FEATURE FLAGS
# ----------------------------------------------------------------------------
FEATURE_AUTO_SCRAPING=true
FEATURE_ADVANCED_ALERTS=true
FEATURE_REPORTING=true
FEATURE_ANALYTICS=true
FEATURE_API_V2=true

# Experimental Features
FEATURE_ML_PRICING=false
FEATURE_VOICE_COMMANDS=false
FEATURE_AR_SCANNING=false

# ----------------------------------------------------------------------------
# EXTERNAL INTEGRATIONS
# ----------------------------------------------------------------------------
# Weather API (for inventory predictions)
WEATHER_API_KEY=[your-weather-api-key]
WEATHER_API_URL=https://api.openweathermap.org/data/2.5

# Payment Gateway (Future e-commerce)
STRIPE_PUBLIC_KEY=pk_test_[your-stripe-public-key]
STRIPE_SECRET_KEY=sk_test_[your-stripe-secret-key]

# Analytics
GOOGLE_ANALYTICS_ID=GA-[your-tracking-id]
MIXPANEL_TOKEN=[your-mixpanel-token]

# ----------------------------------------------------------------------------
# PERFORMANCE TUNING
# ----------------------------------------------------------------------------
# Database
DB_CONNECTION_POOL_SIZE=20
DB_QUERY_TIMEOUT=30
DB_STATEMENT_TIMEOUT=60000

# Memory Management
MAX_MEMORY_USAGE=512MB
GARBAGE_COLLECTION_INTERVAL=300
OBJECT_POOL_SIZE=100

# API Performance
API_COMPRESSION=true
API_KEEP_ALIVE_TIMEOUT=5
API_MAX_HEADER_LENGTH=8192
```

### 5.2 Configuración de Edge Functions

```typescript
// config/edge-functions.config.ts
export const EDGE_FUNCTIONS_CONFIG = {
  // Scraper Maxiconsumo Configuration
  scraper_maxiconsumo: {
    runtime: 'deno',
    memory: '512MB',
    timeout: 900, // 15 minutes
    concurrency: 3,
    retryAttempts: 3,
    retryDelay: 1000,
    
    scraping: {
      maxDelay: parseInt(process.env.SCRAPER_MAX_DELAY || '5000'),
      minDelay: parseInt(process.env.SCRAPER_MIN_DELAY || '2000'),
      userAgentRotation: process.env.SCRAPER_USER_AGENT_ROTATION === 'true',
      concurrentRequests: parseInt(process.env.SCRAPER_CONCURRENT_REQUESTS || '3'),
      timeout: parseInt(process.env.SCRAPER_TIMEOUT || '30000'),
      
      providers: {
        maxiconsumo: {
          url: process.env.PROVIDER_MAXICONSUMO_URL || 'https://maxiconsumo.com.ar',
          categories: (process.env.PROVIDER_MAXICONSUMO_CATEGORIES || 'bebidas,snacks,lacteos').split(','),
          batchSize: parseInt(process.env.PROVIDER_BATCH_SIZE || '50'),
          rateLimit: parseInt(process.env.PROVIDER_RATE_LIMIT_PER_MINUTE || '12')
        }
      }
    }
  },

  // API Mini Market Configuration
  api_minimarket: {
    runtime: 'deno',
    memory: '256MB',
    timeout: 30,
    cors: {
      origin: (process.env.CORS_ORIGINS || 'https://lefkn5kbqv2o.space.minimax.io').split(','),
      credentials: true
    },
    
    authentication: {
      jwtSecret: process.env.JWT_SECRET,
      expiration: process.env.JWT_EXPIRATION || '24h',
      refreshExpiration: process.env.JWT_REFRESH_EXPIRATION || '7d'
    },
    
    rateLimit: {
      public: parseInt(process.env.API_RATE_LIMIT_PUBLIC || '100'),
      private: parseInt(process.env.API_RATE_LIMIT_PRIVATE || '10'),
      windowMs: 60000 // 1 minute
    },
    
    cache: {
      ttl: parseInt(process.env.API_CACHE_TTL_SECONDS || '300'),
      maxSize: 100
    }
  },

  // Alerts Stock Configuration
  alertas_stock: {
    runtime: 'deno',
    memory: '128MB',
    timeout: 60,
    
    thresholds: {
      lowStock: 10,
      criticalStock: 5,
      overstock: 1000
    },
    
    notifications: {
      emailEnabled: process.env.EMAIL_ENABLED === 'true',
      pushEnabled: process.env.PUSH_NOTIFICATIONS_ENABLED === 'true'
    }
  },

  // Notifications Tareas Configuration
  notificaciones_tareas: {
    runtime: 'deno',
    memory: '128MB',
    timeout: 60,
    
    scheduling: {
      intervalMinutes: 120, // Every 2 hours
      maxRetries: 3,
      retryDelay: 300000 // 5 minutes
    },
    
    escalation: {
      criticalHours: 1,
      highHours: 4,
      mediumHours: 24
    }
  },

  // Reports Configuration
  reportes_automaticos: {
    runtime: 'deno',
    memory: '256MB',
    timeout: 300,
    
    schedules: {
      daily: '0 8 * * *', // 8 AM daily
      weekly: '0 9 * * 1', // 9 AM Monday
      monthly: '0 10 1 * *' // 10 AM first day of month
    },
    
    formats: ['pdf', 'xlsx', 'csv'],
    retentionDays: 90
  }
};

// Environment-specific overrides
export const getConfig = (environment: string = 'production') => {
  const baseConfig = EDGE_FUNCTIONS_CONFIG;
  
  if (environment === 'development') {
    return {
      ...baseConfig,
      scraper_maxiconsumo: {
        ...baseConfig.scraper_maxiconsumo,
        scraping: {
          ...baseConfig.scraper_maxiconsumo.scraping,
          maxDelay: 1000,
          minDelay: 500,
          concurrentRequests: 1
        }
      },
      api_minimarket: {
        ...baseConfig.api_minimarket,
        rateLimit: {
          ...baseConfig.api_minimarket.rateLimit,
          public: 1000,
          private: 100
        }
      }
    };
  }
  
  if (environment === 'staging') {
    return {
      ...baseConfig,
      scraper_maxiconsumo: {
        ...baseConfig.scraper_maxiconsumo,
        scraping: {
          ...baseConfig.scraper_maxiconsumo.scraping,
          maxDelay: 3000
        }
      }
    };
  }
  
  return baseConfig;
};
```

---

Esta documentación técnica actualizada proporciona una vista completa y actualizada del sistema Mini Market, incluyendo la arquitectura detallada, diagramas de flujo, especificaciones de API completas, esquemas de base de datos actualizados y toda la configuración necesaria para deployment y operación del sistema.
