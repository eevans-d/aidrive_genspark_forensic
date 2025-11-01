# ARCHITECTURE DOCUMENTATION - SISTEMA MINI MARKET SPRINT 6
## Documentación Técnica de Arquitectura Nivel Empresa

**Versión:** 2.0.0  
**Fecha:** 1 de noviembre de 2025  
**Estado:** PRODUCCIÓN ENTERPRISE  
**Target:** Arquitectos, DevOps, Senior Engineers  

---

## 📋 TABLA DE CONTENIDOS

1. [Arquitectura General](#1-arquitectura-general)
2. [Patrones Arquitectónicos](#2-patrones-arquitectónicos)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend Architecture](#4-backend-architecture)
5. [Database Design](#5-database-design)
6. [Integration Architecture](#6-integration-architecture)
7. [Security Architecture](#7-security-architecture)
8. [Performance Architecture](#8-performance-architecture)
9. [Scalability Design](#9-scalability-design)
10. [Deployment Architecture](#10-deployment-architecture)

---

## 1. ARQUITECTURA GENERAL

### 1.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MINI MARKET SPRINT 6 ARCHITECTURE              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │   CLIENTS   │    │   CLIENTS   │    │   CLIENTS   │            │
│  │             │    │             │    │             │            │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘            │
│         │                  │                  │                    │
│         └──────────────────┴──────────────────┘                    │
│                            │                                        │
│                      ┌─────▼─────┐                                 │
│                      │  CDN/WAF  │                                 │
│                      │  Cloudflare                                │
│                      └─────┬─────┘                                 │
│                            │                                        │
│                  ┌─────────▼─────────┐                             │
│                  │   LOAD BALANCER   │                             │
│                  │    (Supabase)     │                             │
│                  └─────────┬─────────┘                             │
│                            │                                        │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    APPLICATION LAYER                         │   │
│  │                                                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │  Frontend   │  │  Edge Fn 1  │  │  Edge Fn N  │         │   │
│  │  │  React/Vite │  │  Scraper    │  │  API        │         │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  │                                                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │ Edge Fn 2   │  │ Edge Fn 3   │  │ Edge Fn 4   │         │   │
│  │  │ Alerts      │  │ Notifications│  │ Reports     │         │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  └────────────────────────────────────────────────────────────┘   │
│                            │                                        │
│                  ┌─────────▼─────────┐                             │
│                  │   DATABASE LAYER  │                             │
│                  │   PostgreSQL      │                             │
│                  │   Supabase        │                             │
│                  └───────────────────┘                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 1.2 Architecture Principles

#### 1.2.1 SOLID Principles Applied
```typescript
// Single Responsibility - Edge Functions
interface ScraperFunction {
    execute(): Promise<ScrapingResult>;
    validate(): boolean;
    cleanup(): Promise<void>;
}

// Open/Closed - Plugin Architecture
interface DataSource {
    extract(): Promise<ProductData[]>;
}

// Liskov Substitution - Abstract Base Classes
abstract class BaseAPI {
    abstract process(): Promise<Result>;
}

// Interface Segregation - Specialized Interfaces
interface ReadOnlyOperations {
    getData(): Promise<Data>;
}

interface WriteOperations {
    updateData(data: Data): Promise<void>;
}

// Dependency Inversion - Service Abstraction
interface IDataProvider {
    getProducts(): Promise<Product[]>;
}
```

#### 1.2.2 Design Patterns Implementation

**Circuit Breaker Pattern:**
```typescript
interface CircuitBreaker {
    execute<T>(operation: () => Promise<T>): Promise<T>;
    getState(): 'CLOSED' | 'OPEN' | 'HALF_OPEN';
}

// Implementation in edge functions
class ScraperCircuitBreaker implements CircuitBreaker {
    private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
    private failures = 0;
    private lastFailureTime = 0;
    
    async execute<T>(operation: () => Promise<T>): Promise<T> {
        if (this.state === 'OPEN') {
            if (Date.now() - this.lastFailureTime > 30000) {
                this.state = 'HALF_OPEN';
            } else {
                throw new Error('Circuit breaker is OPEN');
            }
        }
        
        try {
            const result = await operation();
            this.onSuccess();
            return result;
        } catch (error) {
            this.onFailure();
            throw error;
        }
    }
}
```

**Proxy Pattern:**
```typescript
// API Proxy with caching and rate limiting
class APIProxy implements IAPIService {
    private cache: Map<string, { data: any; expires: number }>;
    private rateLimiter: RateLimiter;
    
    async get(endpoint: string, params?: any): Promise<any> {
        const cacheKey = this.generateCacheKey(endpoint, params);
        
        // Check cache first
        if (this.isCacheValid(cacheKey)) {
            return this.getFromCache(cacheKey);
        }
        
        // Rate limiting
        await this.rateLimiter.acquire();
        
        // Execute request
        const result = await this.executeRequest(endpoint, params);
        
        // Cache result
        this.setCache(cacheKey, result);
        
        return result;
    }
}
```

**Observer Pattern:**
```typescript
// Event system for notifications
interface EventObserver {
    update(event: Event): void;
}

class ScrapingEventSystem {
    private observers: Map<string, EventObserver[]> = new Map();
    
    subscribe(eventType: string, observer: EventObserver): void {
        if (!this.observers.has(eventType)) {
            this.observers.set(eventType, []);
        }
        this.observers.get(eventType)!.push(observer);
    }
    
    notify(eventType: string, event: Event): void {
        const observers = this.observers.get(eventType) || [];
        observers.forEach(observer => observer.update(event));
    }
}
```

### 1.3 Technology Stack

#### Frontend Stack
```
┌─────────────────────────────────────────┐
│              FRONTEND                    │
├─────────────────────────────────────────┤
│  React 18.x                             │
│  ├── State Management: Context API      │
│  ├── Styling: TailwindCSS 3.x          │
│  ├── Build Tool: Vite 4.x              │
│  ├── TypeScript: 5.x                   │
│  └── Testing: Vitest + Cypress         │
├─────────────────────────────────────────┤
│  Architecture:                          │
│  ├── Component-based design             │
│  ├── Single Page Application (SPA)      │
│  ├── Client-side routing               │
│  └── Responsive design (mobile-first)   │
└─────────────────────────────────────────┘
```

#### Backend Stack
```
┌─────────────────────────────────────────┐
│              BACKEND                     │
├─────────────────────────────────────────┤
│  Supabase Edge Functions                │
│  ├── Runtime: Deno 1.x                 │
│  ├── Language: TypeScript              │
│  ├── Framework: Custom (Serverless)     │
│  └── Storage: Supabase Storage         │
├─────────────────────────────────────────┤
│  Database: PostgreSQL 15+              │
│  ├── ORM: Supabase Client              │
│  ├── Migrations: Alembic equivalent    │
│  └── Real-time: Supabase Realtime      │
└─────────────────────────────────────────┘
```

---

## 2. PATRONES ARQUITECTÓNICOS

### 2.1 Microservices Architecture

#### 2.1.1 Service Decomposition
```
┌─────────────────────────────────────────┐
│           SERVICE ARCHITECTURE          │
├─────────────────────────────────────────┤
│                                        │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Web Scraper  │  │   API        │   │
│  │ Service      │  │  Service     │   │
│  │              │  │              │   │
│  │ - Scraping   │  │ - REST APIs  │   │
│  │ - Anti-bot   │  │ - Caching    │   │
│  │ - Rate limit │  │ - Validation │   │
│  └──────┬───────┘  └──────┬───────┘   │
│         │                 │           │
│  ┌──────▼──────────┐  ┌───▼──────┐   │
│  │ Alert Service   │  │Report    │   │
│  │                 │  │Service   │   │
│  │ - Monitoring    │  │          │   │
│  │ - Notifications │  │ - Analytics│   │
│  │ - Escalation    │  │ - Exports │   │
│  └─────────────────┘  └──────────┘   │
│                                        │
│  ┌─────────────────────────────────┐  │
│  │     DATA LAYER                 │  │
│  │                                │  │
│  │ ┌─────────┐ ┌─────────┐       │  │
│  │ │   DB    │ │ Cache   │       │  │
│  │ │PostgreSQL│ │Redis-like│       │  │
│  │ └─────────┘ └─────────┘       │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

#### 2.1.2 Service Communication Patterns

**Synchronous Communication (API Calls):**
```typescript
// Inter-service communication via Supabase API
class ServiceCommunicator {
    async callService(serviceName: string, endpoint: string, data: any): Promise<any> {
        const serviceUrl = this.getServiceUrl(serviceName);
        
        try {
            const response = await fetch(`${serviceUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${await this.getServiceToken()}`
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`Service ${serviceName} responded with ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            // Circuit breaker pattern for resilience
            this.circuitBreaker.recordFailure();
            throw error;
        }
    }
}
```

**Asynchronous Communication (Event-Driven):**
```typescript
// Event-driven architecture using Supabase Realtime
class EventDrivenCommunication {
    private eventBus: EventEmitter;
    
    constructor() {
        this.eventBus = new EventEmitter();
        this.setupEventHandlers();
    }
    
    async publish(eventType: string, data: any): Promise<void> {
        // Publish event to all subscribed services
        this.eventBus.emit(eventType, {
            timestamp: Date.now(),
            data,
            source: this.serviceName
        });
        
        // Store in event history
        await this.storeEvent({
            type: eventType,
            data,
            timestamp: new Date()
        });
    }
    
    subscribe(eventType: string, handler: (data: any) => Promise<void>): void {
        this.eventBus.on(eventType, handler);
    }
}
```

### 2.2 Event Sourcing Pattern

#### 2.2.1 Event Store Implementation
```sql
-- Event store table for maintaining event history
CREATE TABLE event_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    version INTEGER NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Unique constraint to prevent duplicate events
CREATE UNIQUE INDEX idx_event_store_aggregate_version 
ON event_store (aggregate_id, version);

-- Composite index for event queries
CREATE INDEX idx_event_store_timestamp ON event_store (timestamp);
CREATE INDEX idx_event_store_type ON event_store (event_type);
```

#### 2.2.2 Projection System
```typescript
// Projector for maintaining read models
class PriceProjection {
    async project(events: ScrapingEvent[]): Promise<void> {
        for (const event of events) {
            switch (event.type) {
                case 'PRICE_UPDATED':
                    await this.updatePriceProjection(event.data);
                    break;
                case 'PRODUCT_ADDED':
                    await this.createProductProjection(event.data);
                    break;
                case 'ALERT_TRIGGERED':
                    await this.updateAlertProjection(event.data);
                    break;
            }
        }
    }
    
    private async updatePriceProjection(eventData: PriceUpdatedEvent): Promise<void> {
        await this.db.update('price_projections').set({
            current_price: eventData.newPrice,
            price_history: this.appendToHistory(eventData),
            last_updated: new Date()
        }).where({
            product_id: eventData.productId
        });
    }
}
```

### 2.3 CQRS Pattern Implementation

#### 2.3.1 Command Side (Write Operations)
```typescript
// Command handlers for write operations
class ScrapingCommandHandler {
    async handle(command: StartScrapingCommand): Promise<void> {
        // Validate command
        this.validateCommand(command);
        
        // Check business rules
        await this.validateBusinessRules(command);
        
        // Start scraping process
        const scrapingJob = await this.scrapingService.startScraping(command);
        
        // Emit domain events
        this.domainEvents.push(new ScrapingStartedEvent(scrapingJob.id));
    }
}
```

#### 2.3.2 Query Side (Read Operations)
```typescript
// Query handlers for read operations
class PriceQueryHandler {
    async handle(query: GetPricesQuery): Promise<PriceDto[]> {
        // Use read model for fast queries
        const prices = await this.readModel.getPrices({
            category: query.category,
            limit: query.limit,
            offset: query.offset
        });
        
        // Apply caching for performance
        return this.cacheService.getOrSet(
            this.generateCacheKey(query),
            () => this.enrichPrices(prices)
        );
    }
}
```

---

## 3. FRONTEND ARCHITECTURE

### 3.1 React Architecture

#### 3.1.1 Component Hierarchy
```
App.tsx
├── AuthProvider
├── Router
└── Layout
    ├── Header
    │   ├── UserMenu
    │   └── NotificationBell
    ├── Sidebar
    │   ├── NavigationItem[]
    │   └── UserRole
    └── MainContent
        ├── DashboardPage
        │   ├── MetricsCards
        │   ├── Charts
        │   └── RecentAlerts
        ├── ProductsPage
        │   ├── ProductFilters
        │   ├── ProductGrid
        │   └── ProductDetailsModal
        ├── StockPage
        │   ├── StockLevels
        │   ├── LowStockAlerts
        │   └── MovementHistory
        ├── DepositPage
        │   ├── MovementForm
        │   ├── ProductSelector
        │   └── MovementHistory
        ├── TareasPage
        │   ├── TaskList
        │   ├── TaskForm
        │   └── TaskDetails
        └── ProveedoresPage
            ├── ProviderList
            ├── ProviderDetails
            └── ComparisonTools
```

#### 3.1.2 State Management Architecture

**Context API Implementation:**
```typescript
// Global state management with Context API
interface AppState {
    user: User | null;
    isAuthenticated: boolean;
    currentPage: string;
    notifications: Notification[];
    theme: 'light' | 'dark';
}

interface AppContextType {
    state: AppState;
    actions: {
        login: (credentials: LoginCredentials) => Promise<void>;
        logout: () => void;
        setPage: (page: string) => void;
        addNotification: (notification: Notification) => void;
        updateUser: (user: User) => void;
    };
}

// App Context Provider
const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
    const [state, setState] = useState<AppState>({
        user: null,
        isAuthenticated: false,
        currentPage: 'dashboard',
        notifications: [],
        theme: 'light'
    });
    
    const actions = useMemo(() => ({
        login: async (credentials: LoginCredentials) => {
            try {
                const user = await authService.login(credentials);
                setState(prev => ({ 
                    ...prev, 
                    user, 
                    isAuthenticated: true 
                }));
            } catch (error) {
                throw new AuthError('Invalid credentials');
            }
        },
        logout: () => {
            authService.logout();
            setState(prev => ({ 
                ...prev, 
                user: null, 
                isAuthenticated: false 
            }));
        },
        setPage: (page: string) => {
            setState(prev => ({ ...prev, currentPage: page }));
        },
        addNotification: (notification: Notification) => {
            setState(prev => ({
                ...prev,
                notifications: [notification, ...prev.notifications]
            }));
        },
        updateUser: (user: User) => {
            setState(prev => ({ ...prev, user }));
        }
    }), []);
    
    return (
        <AppContext.Provider value={{ state, actions }}>
            {children}
        </AppContext.Provider>
    );
}
```

#### 3.1.3 Custom Hooks Architecture

**Data Fetching Hooks:**
```typescript
// Custom hook for data fetching with caching
function useApiData<T>(
    endpoint: string, 
    options?: UseApiOptions
): UseApiReturn<T> {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const cache = useContext(CacheContext);
    
    const fetchData = useCallback(async () => {
        const cacheKey = generateCacheKey(endpoint, options?.params);
        
        // Check cache first
        if (options?.useCache && cache.has(cacheKey)) {
            const cachedData = cache.get(cacheKey);
            setData(cachedData);
            setLoading(false);
            return;
        }
        
        try {
            setLoading(true);
            setError(null);
            
            const response = await apiClient.get(endpoint, options?.params);
            const result = response.data;
            
            setData(result);
            
            // Update cache
            if (options?.useCache) {
                cache.set(cacheKey, result, options.cacheTTL);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    }, [endpoint, options?.params, options?.useCache, options?.cacheTTL]);
    
    useEffect(() => {
        fetchData();
    }, [fetchData]);
    
    const refetch = useCallback(() => {
        if (options?.useCache) {
            cache.delete(generateCacheKey(endpoint, options?.params));
        }
        fetchData();
    }, [fetchData, endpoint, options?.params, options?.useCache]);
    
    return { data, loading, error, refetch };
}

// Specific hooks for different entities
export function useProducts(filters?: ProductFilters) {
    return useApiData<Product[]>('/api/products', {
        params: filters,
        useCache: true,
        cacheTTL: 5 * 60 * 1000 // 5 minutes
    });
}

export function useStockLevels() {
    return useApiData<StockLevel[]>('/api/stock', {
        useCache: true,
        cacheTTL: 2 * 60 * 1000 // 2 minutes
    });
}
```

### 3.2 Routing Architecture

#### 3.2.1 React Router Setup
```typescript
// Protected route wrapper
interface ProtectedRouteProps {
    children: ReactNode;
    requiredRole?: UserRole;
    fallback?: ReactNode;
}

function ProtectedRoute({ 
    children, 
    requiredRole,
    fallback = <LoginPage />
}: ProtectedRouteProps) {
    const { state } = useContext(AppContext);
    
    if (!state.isAuthenticated) {
        return fallback;
    }
    
    if (requiredRole && state.user?.role !== requiredRole) {
        return <AccessDeniedPage />;
    }
    
    return <>{children}</>;
}

// Route configuration
const routes = [
    {
        path: '/login',
        element: <LoginPage />,
        public: true
    },
    {
        path: '/dashboard',
        element: (
            <ProtectedRoute>
                <DashboardPage />
            </ProtectedRoute>
        ),
        requiredRole: 'admin'
    },
    {
        path: '/products',
        element: (
            <ProtectedRoute>
                <ProductsPage />
            </ProtectedRoute>
        )
    },
    {
        path: '/stock',
        element: (
            <ProtectedRoute>
                <ProtectedRoute requiredRole="deposito">
                    <StockPage />
                </ProtectedRoute>
            </ProtectedRoute>
        )
    },
    {
        path: '/deposito',
        element: (
            <ProtectedRoute>
                <ProtectedRoute requiredRole="deposito">
                    <DepositPage />
                </ProtectedRoute>
            </ProtectedRoute>
        )
    }
];

// Router component with error boundaries
function AppRouter() {
    return (
        <BrowserRouter>
            <ErrorBoundary>
                <Routes>
                    {routes.map(route => (
                        <Route
                            key={route.path}
                            path={route.path}
                            element={route.element}
                        />
                    ))}
                </Routes>
            </ErrorBoundary>
        </BrowserRouter>
    );
}
```

### 3.3 Styling Architecture

#### 3.3.1 TailwindCSS Configuration
```typescript
// tailwind.config.ts
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          // ... color scale
          900: '#1e3a8a'
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          // ... success color scale
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          // ... warning color scale
        },
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          // ... error color scale
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace']
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem'
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out'
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography')
  ]
};
```

#### 3.3.2 Component Styling Patterns
```typescript
// Reusable styled components with Tailwind
interface ButtonProps {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    loading?: boolean;
    disabled?: boolean;
    children: React.ReactNode;
    onClick?: () => void;
}

const Button: FC<ButtonProps> = ({
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    children,
    onClick,
    className = ''
}) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
    
    const variantStyles = {
        primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
        secondary: 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500',
        outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500',
        ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-gray-500'
    };
    
    const sizeStyles = {
        sm: 'px-3 py-2 text-sm',
        md: 'px-4 py-2 text-sm',
        lg: 'px-6 py-3 text-base'
    };
    
    const disabledStyles = disabled || loading ? 'opacity-50 cursor-not-allowed' : '';
    
    return (
        <button
            className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${disabledStyles} ${className}`}
            disabled={disabled || loading}
            onClick={onClick}
        >
            {loading && (
                <svg className="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
            )}
            {children}
        </button>
    );
};
```

---

## 4. BACKEND ARCHITECTURE

### 4.1 Edge Functions Architecture

#### 4.1.1 Function Structure Pattern
```typescript
// Standard edge function structure
interface EdgeFunctionConfig {
    corsHeaders: Record<string, string>;
    rateLimit: {
        windowMs: number;
        max: number;
    };
    validation: {
        schema: z.ZodSchema;
        strict: boolean;
    };
}

abstract class BaseEdgeFunction {
    protected config: EdgeFunctionConfig;
    protected logger: Logger;
    
    constructor() {
        this.config = this.getConfig();
        this.logger = new Logger(this.constructor.name);
    }
    
    protected abstract handler(req: Request): Promise<Response>;
    
    protected getConfig(): EdgeFunctionConfig {
        return {
            corsHeaders: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH'
            },
            rateLimit: {
                windowMs: 60 * 1000, // 1 minute
                max: 100 // requests per window
            },
            validation: {
                schema: z.object({}),
                strict: true
            }
        };
    }
    
    protected async handleRequest(req: Request): Promise<Response> {
        try {
            // CORS preflight
            if (req.method === 'OPTIONS') {
                return new Response(null, { status: 200, headers: this.config.corsHeaders });
            }
            
            // Rate limiting
            if (!(await this.rateLimiter.checkLimit(this.getClientId(req)))) {
                return this.rateLimitResponse();
            }
            
            // Validation
            const body = await req.json();
            const validatedData = this.config.validation.schema.parse(body);
            
            // Execute handler
            const result = await this.handler(new Request(req.url, {
                method: req.method,
                headers: req.headers,
                body: JSON.stringify(validatedData)
            }));
            
            return result;
        } catch (error) {
            this.logger.error('Request handling failed', { error });
            return this.errorResponse(error);
        }
    }
    
    protected successResponse(data: any, status = 200): Response {
        return new Response(JSON.stringify({ success: true, data }), {
            status,
            headers: { ...this.config.corsHeaders, 'Content-Type': 'application/json' }
        });
    }
    
    protected errorResponse(error: any): Response {
        const message = error.message || 'Internal server error';
        const code = error.code || 'INTERNAL_ERROR';
        
        return new Response(JSON.stringify({
            success: false,
            error: { code, message }
        }), {
            status: error.status || 500,
            headers: { ...this.config.corsHeaders, 'Content-Type': 'application/json' }
        });
    }
    
    private getClientId(req: Request): string {
        return req.headers.get('x-client-info') || 
               req.headers.get('authorization')?.split(' ')[1] || 
               req.headers.get('x-forwarded-for') || 
               'unknown';
    }
}
```

#### 4.1.2 Scraper Function Architecture
```typescript
class ScraperMaxiconsumoFunction extends BaseEdgeFunction {
    private scraper: WebScraper;
    private cache: CacheService;
    private rateLimiter: RateLimiter;
    
    constructor() {
        super();
        this.scraper = new WebScraper();
        this.cache = new CacheService();
        this.rateLimiter = new RateLimiter();
    }
    
    protected async handler(req: Request): Promise<Response> {
        const url = new URL(req.url);
        const action = url.searchParams.get('action') || 'scrape';
        
        switch (action) {
            case 'scrape':
                return this.handleScrape(req);
            case 'compare':
                return this.handleCompare(req);
            case 'alerts':
                return this.handleAlerts(req);
            case 'status':
                return this.handleStatus(req);
            case 'health':
                return this.handleHealth(req);
            default:
                throw new Error(`Unknown action: ${action}`);
        }
    }
    
    private async handleScrape(req: Request): Promise<Response> {
        const requestData = await req.json();
        const { categoria, batch_size = 50, test_mode = false } = requestData;
        
        this.logger.info('Starting scraping operation', { categoria, batch_size });
        
        // Circuit breaker check
        if (!this.circuitBreaker.check('scraper')) {
            throw new Error('Scraper circuit breaker is OPEN');
        }
        
        try {
            // Start scraping process
            const scrapingJob = await this.scraper.startScraping({
                categoria,
                batchSize: batch_size,
                testMode: test_mode
            });
            
            // Update cache
            await this.cache.set(`scraping:${categoria}`, {
                status: 'running',
                jobId: scrapingJob.id,
                startedAt: new Date().toISOString()
            }, 30 * 60 * 1000); // 30 minutes
            
            return this.successResponse({
                jobId: scrapingJob.id,
                status: 'started',
                categoria,
                estimatedDuration: scrapingJob.estimatedDuration
            });
        } catch (error) {
            this.circuitBreaker.recordFailure('scraper');
            throw error;
        }
    }
    
    private async handleCompare(req: Request): Promise<Response> {
        const requestData = await req.json();
        const { product_ids, min_difference = 10 } = requestData;
        
        this.logger.info('Starting price comparison', { 
            product_count: product_ids?.length,
            min_difference 
        });
        
        const opportunities = await this.scraper.comparePrices({
            productIds: product_ids,
            minDifference: min_difference
        });
        
        return this.successResponse({
            opportunities,
            summary: {
                total_analyzed: product_ids?.length || 0,
                opportunities_found: opportunities.length,
                total_savings: opportunities.reduce((sum, opp) => sum + opp.potential_savings, 0)
            }
        });
    }
}
```

### 4.2 API Architecture

#### 4.2.1 RESTful API Design
```typescript
// API Router with middleware stack
class APIRouter {
    private middleware: Middleware[] = [];
    private routes: Map<string, RouteHandler> = new Map();
    
    use(middleware: Middleware): this {
        this.middleware.push(middleware);
        return this;
    }
    
    get(path: string, handler: RouteHandler): this {
        this.addRoute('GET', path, handler);
        return this;
    }
    
    post(path: string, handler: RouteHandler): this {
        this.addRoute('POST', path, handler);
        return this;
    }
    
    private addRoute(method: string, path: string, handler: RouteHandler): void {
        const routeKey = `${method}:${path}`;
        this.routes.set(routeKey, handler);
    }
    
    async handleRequest(req: Request): Promise<Response> {
        const url = new URL(req.url);
        const method = req.method;
        const path = url.pathname;
        
        const routeKey = `${method}:${path}`;
        const handler = this.routes.get(routeKey);
        
        if (!handler) {
            return new Response(JSON.stringify({
                success: false,
                error: { code: 'NOT_FOUND', message: 'Route not found' }
            }), { status: 404 });
        }
        
        // Build middleware chain
        const chain = this.middleware.concat([handler]);
        
        try {
            // Execute middleware chain
            let response: Response;
            for (const middleware of chain) {
                response = await middleware(req);
                if (response) break; // Middleware can short-circuit
            }
            
            return response || new Response(null, { status: 204 });
        } catch (error) {
            return this.handleError(error);
        }
    }
}

// Middleware implementations
class AuthMiddleware implements Middleware {
    async handle(req: Request): Promise<Response | null> {
        const authHeader = req.headers.get('Authorization');
        
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return new Response(JSON.stringify({
                success: false,
                error: { code: 'UNAUTHORIZED', message: 'Authentication required' }
            }), { status: 401 });
        }
        
        const token = authHeader.substring(7);
        const user = await this.verifyToken(token);
        
        if (!user) {
            return new Response(JSON.stringify({
                success: false,
                error: { code: 'UNAUTHORIZED', message: 'Invalid token' }
            }), { status: 401 });
        }
        
        // Attach user to request context
        (req as any).user = user;
        return null; // Continue to next middleware
    }
    
    private async verifyToken(token: string): Promise<User | null> {
        // JWT verification logic
        try {
            const decoded = jwt.verify(token, process.env.JWT_SECRET!);
            return await this.userService.findById(decoded.userId);
        } catch (error) {
            return null;
        }
    }
}

class RateLimitMiddleware implements Middleware {
    private rateLimiters: Map<string, RateLimiter> = new Map();
    
    async handle(req: Request): Promise<Response | null> {
        const clientId = this.getClientId(req);
        const limiter = this.getOrCreateRateLimiter(clientId);
        
        if (!(await limiter.tryConsume())) {
            return new Response(JSON.stringify({
                success: false,
                error: { 
                    code: 'RATE_LIMITED', 
                    message: 'Too many requests',
                    retryAfter: limiter.retryAfter()
                }
            }), { 
                status: 429,
                headers: {
                    'Retry-After': limiter.retryAfter().toString()
                }
            });
        }
        
        return null;
    }
}
```

#### 4.2.2 API Versioning Strategy
```typescript
// Version routing
class APIRouterWithVersioning extends APIRouter {
    private versions: Map<string, APIRouter> = new Map();
    
    registerVersion(version: string, router: APIRouter): void {
        this.versions.set(version, router);
    }
    
    async handleRequest(req: Request): Promise<Response> {
        const url = new URL(req.url);
        const pathParts = url.pathname.split('/');
        
        // Extract version from URL: /v1/api/endpoint
        if (pathParts[1]?.startsWith('v')) {
            const version = pathParts[1];
            const router = this.versions.get(version);
            
            if (!router) {
                return new Response(JSON.stringify({
                    success: false,
                    error: { code: 'VERSION_NOT_SUPPORTED', message: `API version ${version} not supported` }
                }), { status: 400 });
            }
            
            // Rewrite URL to remove version
            url.pathname = '/' + pathParts.slice(2).join('/');
            req = new Request(url.toString(), {
                method: req.method,
                headers: req.headers,
                body: req.body
            });
            
            return router.handleRequest(req);
        }
        
        // Default to latest version
        return this.versions.get('v1')!.handleRequest(req);
    }
}

// Version compatibility
class APICompatibilityLayer {
    async migrateRequest(req: Request, fromVersion: string, toVersion: string): Promise<Request> {
        const body = await req.json();
        
        let migratedBody = body;
        
        // Apply migration rules based on version
        if (fromVersion === 'v1' && toVersion === 'v2') {
            migratedBody = this.migrateV1ToV2(body);
        }
        
        return new Request(req.url, {
            method: req.method,
            headers: req.headers,
            body: JSON.stringify(migratedBody)
        });
    }
    
    private migrateV1ToV2(body: any): any {
        return {
            ...body,
            // Migration logic
            price: body.cost, // renamed field
            available: body.in_stock, // renamed field
            added_at: body.created_at // renamed field
        };
    }
}
```

---

## 5. DATABASE DESIGN

### 5.1 Relational Schema

#### 5.1.1 Core Tables Structure
```sql
-- Core schema with proper relationships
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

-- Sprint 6 additions for supplier integration
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
    
    -- Constraint to ensure only one price per product-provider is vigente
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
```

#### 5.1.2 Indexes Strategy
```sql
-- Performance indexes
CREATE INDEX idx_productos_categoria_id ON productos(categoria_id) WHERE categoria_id IS NOT NULL;
CREATE INDEX idx_productos_codigo_barras ON productos(codigo_barras) WHERE codigo_barras IS NOT NULL;
CREATE INDEX idx_productos_sku ON productos(sku) WHERE sku IS NOT NULL;
CREATE INDEX idx_productos_activo ON productos(activo) WHERE activo = TRUE;
CREATE INDEX idx_productos_dimensiones_gin ON productos USING GIN(dimensiones);

CREATE INDEX idx_stock_deposito_producto ON stock_deposito(producto_id);
CREATE INDEX idx_stock_deposito_deposito ON stock_deposito(deposito);
CREATE INDEX idx_stock_deposito_stock_bajo ON stock_deposito(producto_id, stock_actual, stock_minimo) 
    WHERE stock_actual <= stock_minimo;

-- Sprint 6 indexes for supplier data
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
```

### 5.2 Views and Materialized Views

#### 5.2.1 Operational Views
```sql
-- View for active products with stock levels
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

-- View for price opportunities
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

-- View for active alerts
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
```

#### 5.2.2 Materialized Views for Performance
```sql
-- Materialized view for daily statistics
CREATE MATERIALIZED VIEW mv_estadisticas_diarias AS
SELECT 
    DATE(fecha_inicio) as fecha,
    categoria,
    COUNT(*) as total_jobs,
    AVG(productos_encontrados) as promedio_productos_encontrados,
    AVG(productos_procesados) as promedio_productos_procesados,
    AVG(tasa_exito) as tasa_exito_promedio,
    AVG(tiempo_ejecucion_segundos) as tiempo_promedio_segundos,
    MAX(productos_encontrados) as max_productos_encontrados,
    MIN(productos_encontrados) as min_productos_encontrados
FROM estadisticas_scraping
WHERE fecha_inicio >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(fecha_inicio), categoria
ORDER BY fecha DESC, categoria;

-- Index on materialized view
CREATE INDEX idx_mv_estadisticas_diarias_fecha ON mv_estadisticas_diarias(fecha);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_estadisticas_diarias()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_estadisticas_diarias;
END;
$$ LANGUAGE plpgsql;

-- Scheduled refresh (to be called by cron job)
-- SELECT refresh_estadisticas_diarias();
```

### 5.3 Triggers and Functions

#### 5.3.1 Audit Triggers
```sql
-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all relevant tables
CREATE TRIGGER update_productos_updated_at 
    BEFORE UPDATE ON productos 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_proveedores_updated_at 
    BEFORE UPDATE ON proveedores 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_precios_proveedor_updated_at 
    BEFORE UPDATE ON precios_proveedor 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to log changes for audit
CREATE OR REPLACE FUNCTION log_producto_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        table_name,
        operation,
        old_data,
        new_data,
        changed_at
    ) VALUES (
        'productos',
        TG_OP,
        CASE 
            WHEN TG_OP = 'DELETE' THEN row_to_json(OLD)
            ELSE NULL
        END,
        CASE 
            WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN row_to_json(NEW)
            ELSE NULL
        END,
        CURRENT_TIMESTAMP
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER log_producto_changes_trigger
    AFTER INSERT OR UPDATE OR DELETE ON productos
    FOR EACH ROW EXECUTE FUNCTION log_producto_changes();
```

#### 5.3.2 Business Logic Functions
```sql
-- Function to update statistics after scraping
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

-- Function to detect significant price changes
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

-- Function to clean old data
CREATE OR REPLACE FUNCTION fnc_limpiar_datos_antiguos()
RETURNS INTEGER AS $$
DECLARE
    registros_eliminados INTEGER := 0;
BEGIN
    -- Clean old logs (older than 90 days)
    DELETE FROM logs_scraping 
    WHERE timestamp < CURRENT_DATE - INTERVAL '90 days';
    GET DIAGNOSTICS registros_eliminados = ROW_COUNT;
    
    -- Clean old statistics (older than 1 year)
    DELETE FROM estadisticas_scraping 
    WHERE fecha_inicio < CURRENT_DATE - INTERVAL '1 year';
    
    -- Clean processed alerts (older than 30 days)
    DELETE FROM alertas_cambios_precios 
    WHERE procesada = TRUE 
    AND fecha_procesamiento < CURRENT_DATE - INTERVAL '30 days';
    
    RETURN registros_eliminados;
END;
$$ LANGUAGE plpgsql;
```

---

**🏗️ ARCHITECTURE DOCUMENTATION COMPLETE**

Esta documentación arquitectónica proporciona una vista completa y detallada del sistema Mini Market Sprint 6, incluyendo todos los patrones, tecnologías y decisiones de diseño implementadas.

**Próximos pasos:** Revisar y actualizar esta documentación con cada cambio arquitectónico significativo del sistema.

**Mantenimiento:** Actualización trimestral recomendada para mantener sincronización con el estado actual del sistema.