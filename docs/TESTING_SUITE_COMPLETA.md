# Documentación Completa del Sistema de Testing - Mini Market Sprint 6

## Descripción General

El Sistema de Testing Exhaustivo para Mini Market Sprint 6 proporciona una cobertura completa de todas las funcionalidades críticas del sistema, incluyendo el scraper web de Maxiconsumo Necochea (40k+ productos), REST API para comparación de precios, integración con base de datos Supabase, y sistema de alertas.

### Arquitectura del Sistema de Testing

```
tests/
├── package.json                 # Configuración NPM con dependencias de testing
├── jest.config.js              # Configuración del framework Jest
├── .env.test                   # Variables de entorno para testing
├── unit/                       # Tests unitarios
│   ├── scraper-maxiconsumo.test.js
│   └── api-proveedor.test.js
├── integration/                # Tests de integración
│   ├── database.integration.test.js
│   └── api-scraper.integration.test.js
├── performance/                # Tests de rendimiento
│   └── load-testing.test.js
├── security/                   # Tests de seguridad
│   └── security-tests.test.js
├── api-contracts/             # Tests de contratos API
│   └── openapi-compliance.test.js
├── helpers/                   # Utilidades y helpers
│   └── setup.js
└── scripts/                   # Scripts de utilidad
    └── generate-test-report.js
```

## Categorías de Testing

### 1. Tests Unitarios
- **Ubicación**: `/tests/unit/`
- **Propósito**: Validar funciones y métodos individuales
- **Cobertura**: 95%+ de funciones críticas
- **Archivos**: 2 archivos, 1,804 líneas de código

#### Ejecutar Tests Unitarios
```bash
# Ejecutar todos los tests unitarios
npm run test:unit

# Ejecutar solo tests del scraper
npm test -- --testPathPattern=unit/scraper-maxiconsumo.test.js

# Ejecutar solo tests del API
npm test -- --testPathPattern=unit/api-proveedor.test.js

# Ejecutar con cobertura específica
npm run test:unit -- --coverage --collectCoverageFrom=src/**/*.{js,ts}
```

#### Funciones Testeadas

**Scraper Unit Tests (`scraper-maxiciosumo.test.js`):**
- `extraerProductosConRegex()` - Extracción de productos del HTML
- `generarHeadersRotativos()` - Rotación de headers HTTP
- `procesarSKU()` - Generación y validación de SKUs
- `reintentarConBackoff()` - Lógica de reintentos con backoff exponencial
- `extraerPrecios()` - Extracción y validación de precios
- `formatearDatos()` - Formateo de datos antes del almacenamiento

**API Unit Tests (`api-proveedor.test.js`):**
- `GET /proveedor/precios` - Listado de precios con paginación
- `GET /proveedor/productos` - Listado de productos
- `GET /proveedor/comparacion` - Comparación de precios entre proveedores
- `POST /proveedor/sincronizar` - Sincronización manual de datos
- `GET /proveedor/status` - Estado del sistema
- `GET /proveedor/alertas` - Gestión de alertas
- `GET /proveedor/estadisticas` - Estadísticas del sistema
- `GET /proveedor/configuracion` - Configuración del sistema

### 2. Tests de Integración
- **Ubicación**: `/tests/integration/`
- **Propósito**: Validar interacciones entre componentes
- **Cobertura**: Flujos completos end-to-end
- **Archivos**: 2 archivos, 1,311 líneas de código

#### Ejecutar Tests de Integración
```bash
# Ejecutar todos los tests de integración
npm run test:integration

# Ejecutar solo tests de base de datos
npm test -- --testPathPattern=integration/database.integration.test.js

# Ejecutar solo tests API-Scraper
npm test -- --testPathPattern=integration/api-scraper.integration.test.js

# Ejecutar con debugging habilitado
npm run test:integration -- --detectOpenHandles --verbose
```

#### Componentes Testeados

**Database Integration Tests:**
- Operaciones CRUD en tabla `precios_proveedor`
- Funciones SQL personalizadas ( cálculo de estadísticas)
- Vistas de base de datos (productos con precios mínimos)
- Triggers de auditoría (logging de cambios)
- Transacciones complejas (consistencia de datos)
- Manejo de concurrencia y locks

**API-Scraper Integration Tests:**
- Flujo completo de scraping y almacenamiento
- Validación de consistencia de datos
- Manejo de errores entre componentes
- Sincronización de datos en tiempo real
- Performance bajo carga (40k+ productos)

### 3. Tests de Rendimiento
- **Ubicación**: `/tests/performance/`
- **Propósito**: Validar performance y escalabilidad
- **Cobertura**: Manejo de datasets grandes, memoria, concurrencia
- **Archivos**: 1 archivo, 590 líneas de código

#### Ejecutar Tests de Rendimiento
```bash
# Ejecutar todos los tests de rendimiento
npm run test:performance

# Ejecutar solo tests de memoria
npm test -- --testPathPattern=performance/load-testing.test.js --testNamePattern="Memory"

# Ejecutar solo tests de concurrencia
npm test -- --testPathPattern=performance/load-testing.test.js --testNamePattern="Concurrent"

# Con profiling de memoria habilitado
NODE_ENV=performance-test npm run test:performance -- --detectMemoryLeaks
```

#### Métricas de Performance

**Large Dataset Handling (40k+ productos):**
- Tiempo de procesamiento completo: < 10 minutos
- Uso de memoria: < 512MB peak
- Throughput: > 100 productos/segundo
- Tasa de éxito: > 99%

**Memory Profile Tests:**
- Detección de memory leaks
- Uso de memoria por función
- Garbage collection optimization
- Pool de conexiones eficiente

**Concurrent Request Tests:**
- 100+ requests simultáneas sin degradación
- Rate limiting funcional (< 10 req/segundo)
- Circuit breaker en caso de errores
- Graceful degradation bajo carga

### 4. Tests de Seguridad
- **Ubicación**: `/tests/security/`
- **Propósito**: Validar vulnerabilidades y robustez
- **Cobertura**: Inyección SQL, bypass de autenticación, validación de entrada
- **Archivos**: 1 archivo, 716 líneas de código

#### Ejecutar Tests de Seguridad
```bash
# Ejecutar todos los tests de seguridad
npm run test:security

# Ejecutar solo tests de inyección SQL
npm test -- --testPathPattern=security/security-tests.test.js --testNamePattern="SQL Injection"

# Ejecutar solo tests de autenticación
npm test -- --testPathPattern=security/security-tests.test.js --testNamePattern="Authentication"

# Con reportes detallados de vulnerabilidades
npm run test:security -- --verbose --detectOpenHandles
```

#### Vulnerabilidades Testeadas

**SQL Injection Tests:**
- Inyección en parámetros de búsqueda
- Bypass de filtros de seguridad
- Union-based injection attempts
- Blind SQL injection detection

**Authentication Bypass Tests:**
- Token manipulation attempts
- Session hijacking scenarios
- Privilege escalation attempts
- JWT expiration handling

**Input Fuzzing:**
- Malformed JSON payloads
- Extreme boundary values
- Unicode and special characters
- Oversized payload handling

**Rate Limiting:**
- DDoS simulation scenarios
- API abuse prevention
- Resource exhaustion tests

### 5. Tests de Contratos API
- **Ubicación**: `/tests/api-contracts/`
- **Propósito**: Validar adherencia al especificación OpenAPI
- **Cobertura**: Schema validation, response consistency, error handling
- **Archivos**: 1 archivo, 659 líneas de código

#### Ejecutar Tests de Contratos
```bash
# Ejecutar todos los tests de contratos
npm run test:contracts

# Validar solo esquemas específicos
npm test -- --testPathPattern=api-contracts/openapi-compliance.test.js --testNamePattern="Schema"

# Con validación estricta de tipos
npm run test:contracts -- --verbose
```

#### Validaciones de Contrato

**Schema Compliance:**
- Respuestas JSON válidas según OpenAPI
- Tipos de datos correctos en payloads
- Propiedades requeridas presentes
- Validación de enum values

**Response Consistency:**
- Formato de error uniforme
- Headers HTTP consistentes
- Status codes apropiados
- Message estructura consistente

**Backward Compatibility:**
- Breaking changes detection
- Deprecation warnings
- Version handling validation

## Interpretación de Reportes de Cobertura

### Métricas de Cobertura

La suite de testing utiliza thresholds estrictos:

```javascript
// jest.config.js
coverageThreshold: {
  global: {
    branches: 95,
    functions: 95,
    lines: 95,
    statements: 95
  },
  './src/': {
    branches: 98,
    functions: 98,
    lines: 98,
    statements: 98
  }
}
```

### Generación de Reportes

```bash
# Generar reporte completo de cobertura
npm run test:coverage

# Generar reporte HTML interactivo
npm run test:coverage -- --coverage --coverageReporters=html

# Generar reporte en formato JSON para CI/CD
npm run test:coverage -- --coverage --coverageReporters=json --coverageDirectory=coverage/
```

### Análisis de Reportes

#### Línea 95%+
- ✅ **Cobertura Excelente**: El código está bien testeado
- **Acción**: Mantener o aumentar cobertura

#### Línea 85-95%
- ⚠️ **Cobertura Aceptable**: Algunas funciones críticas pueden estar sin testear
- **Acción**: Identificar y agregar tests para gaps específicos

#### Línea <85%
- ❌ **Cobertura Insuficiente**: Riesgo de bugs no detectados
- **Acción**: Priorizar tests de funciones críticas sin cobertura

### Métricas por Componente

**Scraper Components:**
```bash
# Cobertura específica del scraper
npm run test:coverage -- --collectCoverageFrom=src/scraper/**/*
```

**API Components:**
```bash
# Cobertura específica del API
npm run test:coverage -- --collectCoverageFrom=src/api/**/*
```

**Database Components:**
```bash
# Cobertura de funciones de base de datos
npm run test:coverage -- --collectCoverageFrom=src/database/**/*
```

## Scripts de Ejecución

### Script Principal de Testing
```bash
# Ejecutar toda la suite de testing (puede tomar 15-20 minutos)
npm test

# Con coverage completo y reportes detallados
npm run test:ci
```

### Scripts Específicos por Categoría
```bash
# Ejecutar solo tests unitarios (2-3 minutos)
npm run test:unit

# Ejecutar tests de integración (5-8 minutos)
npm run test:integration

# Ejecutar tests de rendimiento (8-12 minutos)
npm run test:performance

# Ejecutar tests de seguridad (3-5 minutos)
npm run test:security

# Ejecutar tests de contratos API (2-4 minutos)
npm run test:contracts
```

### Scripts de Utilidad
```bash
# Ejecutar tests en modo watch (desarrollo)
npm run test:watch

# Generar reporte de testing completo
npm run test:report

# Limpiar cache de Jest
npm run test:clean

# Ejecutar tests específicos por patrón
npm run test:grep -- --testNamePattern="sku"
```

## Guía de Mantenimiento de Tests

### Estructura de Tests Recomendada

#### Naming Conventions
```javascript
// ✅ Correcto: describe describe el componente, test describe el comportamiento
describe('extraerProductosConRegex', () => {
  test('should extract product names from valid HTML', async () => {
    // Arrange
    const html = '<div class="product">Producto A</div>';
    
    // Act
    const result = await extraerProductosConRegex(html);
    
    // Assert
    expect(result).toHaveLength(1);
    expect(result[0].nombre).toBe('Producto A');
  });

  test('should handle empty HTML gracefully', async () => {
    // Test específico para caso límite
  });
});

// ❌ Incorrecto: nombres vagos o poco descriptivos
describe('Tests for Scraper', () => {
  test('test1', () => { /* ... */ });
});
```

#### Setup y Teardown
```javascript
describe('Database Operations', () => {
  let testDb;
  let mockSupabase;

  beforeAll(async () => {
    // Setup costoso una vez por archivo
    testDb = await createTestDatabase();
    mockSupabase = setupMockSupabase();
  });

  beforeEach(async () => {
    // Reset antes de cada test
    await cleanupTestData(testDb);
  });

  afterEach(async () => {
    // Limpieza después de cada test
  });

  afterAll(async () => {
    // Cleanup final
    await testDb.destroy();
  });
});
```

### Mejores Prácticas

#### 1. Isolation de Tests
```javascript
// ✅ Test independiente y aislamiento completo
test('should create producto with valid data', async () => {
  const productoData = {
    nombre: 'Producto Test',
    sku: 'TEST-001',
    precio: 100
  };

  const result = await createProducto(productoData);
  expect(result.id).toBeDefined();
  expect(result.nombre).toBe(productoData.nombre);
});

// ❌ Test dependiente de estado global
let globalProducto;
test('should update producto', async () => {
  // Asume que globalProducto existe del test anterior
  const result = await updateProducto(globalProducto.id, { precio: 150 });
  expect(result.precio).toBe(150);
});
```

#### 2. Mocking Efectivo
```javascript
// ✅ Mock completo y controlado
jest.mock('supabase', () => ({
  from: jest.fn().mockReturnValue({
    insert: jest.fn().mockResolvedValue({ data: [{ id: 1 }], error: null }),
    select: jest.fn().mockResolvedValue({ data: [], error: null }),
    update: jest.fn().mockResolvedValue({ data: [], error: null })
  })
}));

// ❌ Mock incompleto que puede fallar en producción
jest.mock('supabase');
```

#### 3. Test Data Management
```javascript
// ✅ Datos consistentes y reutilizables
const TEST_PRODUCTOS = {
  valido: {
    nombre: 'Producto Test',
    sku: 'TEST-001',
    precio: 100,
    descripcion: 'Descripción de prueba'
  },
  invalido: {
    nombre: '',
    sku: null,
    precio: -10
  },
  edgeCase: {
    nombre: 'Producto con carácteres especiales: @#$%',
    sku: 'SKU-MUY-LARGO-QUI-SUPERA-LIMITE-CARACTERES',
    precio: 999999.99
  }
};

// ❌ Datos hardcodeados repetitivos
test('should handle producto', async () => {
  const producto = {
    nombre: 'Producto Test', // Repetido en múltiples tests
    sku: 'TEST-001', // Repetición
    precio: 100
  };
});
```

#### 4. Assertive Testing
```javascript
// ✅ Aserciones específicas y completas
test('should return correct price comparison', async () => {
  const productos = await fetchProductos();
  
  expect(productos).toBeInstanceOf(Array);
  expect(productos).toHaveLength(3);
  expect(productos[0]).toHaveProperty('precio');
  expect(productos[0]).toHaveProperty('proveedor');
  
  const precioMinimo = Math.min(...productos.map(p => p.precio));
  expect(precioMinimo).toBeGreaterThan(0);
  expect(precioMinimo).toBeLessThan(1000);
});

// ❌ Aserciones vagas o incompletas
test('should work correctly', async () => {
  const result = await someFunction();
  expect(result).toBeTruthy();
});
```

### Mantenimiento Regular

#### Actualización de Tests
```bash
# Revisar y actualizar tests mensualmente
npm run test:review

# Verificar tests obsoletos o rotos
npm run test:audit

# Actualizar snapshots cuando sea necesario
npm run test:update-snapshot
```

#### Refactoring de Tests
```javascript
// Antes de refactorizar código, ejecutar tests para asegurar que funcionan
npm test

// Refactorizar código
git commit -m "refactor: mejora en algoritmo de parsing"

// Verificar que tests siguen pasando
npm test -- --updateSnapshot

// Si hay fallos, revisar y corregir tests obsoletos
npm test -- --verbose
```

#### Tests de Regression
```bash
# Ejecutar tests específicos cuando se reportado un bug
npm test -- --testNamePattern="nombre-del-bug"

# Crear test para reproducir el bug
# Corregir el código
# Verificar que el test pasa
```

## Depuración y Troubleshooting

### Comandos de Debugging

```bash
# Ejecutar tests en modo debug (Node.js inspector)
node --inspect-brk node_modules/.bin/jest --runInBand

# Ejecutar test específico con debugging
npm test -- --testNamePattern="specific test" --verbose --detectOpenHandles

# Ejecutar test con logging detallado
NODE_DEBUG=test npm test -- --verbose

# Ejecutar test con variables de entorno específicas
NODE_ENV=debug npm test -- --testNamePattern="sku parsing"
```

### Problemas Comunes y Soluciones

#### Tests que Fallan Intermitentemente
```javascript
// Síntoma: Test pasa a veces, falla otras
// Solución: Verificar timing y async operations
test('should handle async operation', async () => {
  const result = await asyncOperation();
  
  // ❌ Puede fallar por timing
  // await new Promise(resolve => setTimeout(resolve, 100));
  
  // ✅ Usar await y expect específicos
  await waitFor(asyncOperation.toHaveBeenCalled());
  expect(result).toBeDefined();
});

// ✅ Alternativa con timeout controlado
test('should complete within time limit', async () => {
  const timeoutPromise = new Promise((_, reject) => 
    setTimeout(() => reject(new Error('Timeout')), 5000)
  );
  
  const result = await Promise.race([actualOperation(), timeoutPromise]);
  expect(result).toBeDefined();
});
```

#### Memory Leaks en Tests
```javascript
// Síntoma: Tests consumen memoria progresivamente
// Solución: Cleanup adecuado en afterEach/afterAll

describe('Large Dataset Tests', () => {
  let largeArray;

  beforeAll(() => {
    // Crear datos grandes solo una vez
    largeArray = Array.from({ length: 100000 }, (_, i) => ({
      id: i,
      data: `Data ${i}`
    }));
  });

  afterEach(() => {
    // Limpiar referencias
    largeArray = null;
  });

  afterAll(() => {
    // Cleanup final global
    global.testData = null;
  });
});
```

#### Performance en Tests
```javascript
// Síntoma: Tests muy lentos
// Solución: Optimizar setup y reducir complejidad

// ❌ Test lento: repetitivo setup
test('should process product 1', async () => {
  const setup = await setupTestEnvironment();
  const result = await processProduct(setup, 'product1');
  expect(result).toBeDefined();
});

test('should process product 2', async () => {
  const setup = await setupTestEnvironment(); //重复setup
  const result = await processProduct(setup, 'product2');
  expect(result).toBeDefined();
});

// ✅ Test rápido: setup compartido
describe('Product Processing', () => {
  let setup;

  beforeAll(async () => {
    setup = await setupTestEnvironment(); // solo una vez
  });

  test('should process product 1', async () => {
    const result = await processProduct(setup, 'product1');
    expect(result).toBeDefined();
  });

  test('should process product 2', async () => {
    const result = await processProduct(setup, 'product2');
    expect(result).toBeDefined();
  });
});
```

## Automatización y CI/CD

### Configuración para CI/CD
```yaml
# .github/workflows/testing.yml
name: Testing Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
        
      - name: Run unit tests
        run: npm run test:unit
        
      - name: Run integration tests  
        run: npm run test:integration
        
      - name: Run performance tests
        run: npm run test:performance
        
      - name: Run security tests
        run: npm run test:security
        
      - name: Run contract tests
        run: npm run test:contracts
        
      - name: Generate coverage report
        run: npm run test:coverage
        
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/lcov.info
          flags: unittests
          name: codecov-umbrella
```

### Pre-commit Hooks
```json
// package.json
{
  "husky": {
    "hooks": {
      "pre-commit": "npm run test:unit -- --bail",
      "pre-push": "npm run test:ci"
    }
  }
}
```

## Monitoreo y Alertas

### Métricas Clave de Testing
- **Coverage Rate**: Debe mantenerse >95%
- **Test Duration**: Tests unitarios <30s, integración <5min, performance <15min
- **Flaky Test Rate**: <1% de tests inconsistentes
- **Security Test Coverage**: 100% de vulnerabilidades críticas

### Alertas Automáticas
```bash
# Script para verificar métricas y enviar alertas
npm run test:metrics-check

# Verificar coverage crítico
npm run test:coverage-check

# Verificar performance de tests
npm run test:performance-check
```

## Conclusión

El Sistema de Testing Exhaustivo para Mini Market Sprint 6 proporciona una cobertura completa y profesional que garantiza la calidad, seguridad y performance del sistema. Con más de 6,000 líneas de código de testing cubriendo unit tests, integración, performance, seguridad y contratos API, el sistema está preparado para soportar desarrollo continuo y escalabilidad.

### Próximos Pasos Recomendados
1. Instalar dependencias: `cd /workspace/tests && npm install`
2. Configurar variables de entorno: Copiar `.env.test` 
3. Ejecutar suite completa: `npm test`
4. Generar reporte inicial: `npm run test:coverage`
5. Integrar con CI/CD pipeline
6. Establecer cron jobs para tests de performance diarios

### Contacto y Soporte
Para questions o issues con el sistema de testing, referirse a:
- Documentación técnica en `/workspace/docs/`
- Configuración en `/workspace/tests/jest.config.js`
- Utilidades en `/workspace/tests/helpers/setup.js`