# Sistema de Gestión de Depósito

## Descripción
Sistema completo de gestión de depósito con control ACID, desarrollado con FastAPI y PostgreSQL.

## Características
- ✅ API REST completa con endpoints CRUD
- ✅ Control ACID de transacciones de stock
- ✅ Base de datos PostgreSQL optimizada
- ✅ Tests de integración completos
- ✅ Datos de ejemplo argentinos realistas
- ✅ Logging y error handling robusto

## Estructura del Proyecto
```
├── agente_deposito/          # Microservicio principal
├── scripts/                  # Scripts de inicialización
├── tests/                    # Tests unitarios e integración
├── data/fixtures/           # Datos de ejemplo
├── config/                  # Configuración
└── logs/                    # Archivos de log
```

## Instalación
```bash
pip install -r requirements.txt
python scripts/init_database.py
```

## Ejecución
```bash
cd agente_deposito
python main.py
```

## API Endpoints
- POST /productos - Crear producto
- GET /productos - Listar productos
- GET /productos/{id} - Obtener producto
- PUT /productos/{id} - Actualizar producto
- DELETE /productos/{id} - Eliminar producto
- POST /stock/update - Actualizar stock
- GET /stock/movements - Historial movimientos
- GET /stock/critical - Stock crítico
