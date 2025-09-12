# 🏪 Dashboard Web Sistema Inventario Retail Argentino

Sistema de dashboard web interactivo para gestión completa de inventario retail optimizado para el mercado argentino.

## 🚀 Características Principales

### 📊 Dashboard Operativo
- **KPIs en tiempo real**: Stock, valor inventario, disponibilidad, cobertura
- **Alertas inteligentes**: Stock crítico, productos sin movimiento, sobrestockeados
- **Recomendaciones ML**: Qué comprar HOY con cantidades optimizadas
- **Charts interactivos**: Predicciones demanda, stock por categoría
- **Updates automáticos**: WebSocket para datos en tiempo real

### 📦 Gestión de Productos
- **CRUD completo**: Crear, editar, eliminar productos
- **Filtros avanzados**: Por categoría, estado, stock
- **Búsqueda inteligente**: Autocompletado por nombre/código
- **Export/Import**: Excel, CSV para integración externa
- **Predicciones individuales**: Forecast por producto

### 🤖 OCR Inteligente
- **Drag & Drop**: Subir facturas arrastrando archivos
- **Multi-formato**: JPG, PNG, PDF hasta 16MB
- **Procesamiento automático**: Extracción datos argentinos
- **Validación CUIT/CUIL**: Formato argentino específico
- **Corrección manual**: Interface para ajustar errores OCR

### 📈 Reportes Avanzados
- **Reportes rápidos**: Stock bajo, ventas día, predicciones ML
- **Constructor personalizado**: Filtros por período, categoría, tipo
- **Multi-formato**: PDF, Excel, CSV, vista web
- **Programación automática**: Reportes recurrentes
- **Historial completo**: Acceso a reportes anteriores

## 🛠️ Tecnologías

### Backend
- **Flask 2.3**: Framework web Python
- **Socket.IO**: WebSocket para tiempo real
- **PostgreSQL**: Base de datos principal
- **Redis**: Cache y sesiones
- **SQLAlchemy**: ORM para base de datos

### Frontend
- **HTML5/CSS3**: Interface responsive
- **JavaScript ES6+**: Interactividad moderna
- **Chart.js**: Gráficos interactivos
- **Font Awesome**: Iconografía completa
- **CSS Grid/Flexbox**: Layout responsive

### DevOps
- **Docker**: Containerización completa
- **Docker Compose**: Orquestación servicios
- **Nginx**: Reverse proxy y SSL
- **Gunicorn**: WSGI server producción

## 📋 Instalación Rápida

### 1. Prerrequisitos
```bash
# Instalar Docker y Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Instalación Automática
```bash
# Clonar/descargar archivos del dashboard
cd dashboard_web_inventario

# Ejecutar script de instalación
chmod +x install.sh
./install.sh
```

### 3. Verificación
```bash
# Verificar servicios funcionando
docker-compose ps

# Ver logs
docker-compose logs -f dashboard
```

## 🌐 Acceso al Sistema

Una vez instalado, el dashboard estará disponible en:

- **HTTPS (Recomendado)**: https://localhost
- **HTTP**: http://localhost  
- **Directo**: http://localhost:5000

### Credenciales por Defecto
- **Usuario**: admin
- **Contraseña**: admin123

## 🎯 Guía de Uso

### Dashboard Principal
1. **Acceder** a https://localhost
2. **Monitorear** KPIs en tiempo real
3. **Revisar** alertas críticas
4. **Confirmar** recomendaciones compra
5. **Generar** lista compras automática

### Gestión Productos
1. **Navegar** a "Productos" en menú
2. **Buscar/Filtrar** productos existentes
3. **Agregar** nuevos productos
4. **Editar** stock y precios
5. **Exportar** datos para proveedores

### Procesamiento OCR
1. **Ir** a "Facturas OCR"
2. **Arrastrar** facturas al área upload
3. **Esperar** procesamiento automático
4. **Revisar** datos extraídos
5. **Aplicar** cambios al inventario

### Generación Reportes
1. **Acceder** a "Reportes"
2. **Seleccionar** tipo y período
3. **Configurar** filtros necesarios
4. **Generar** vista previa
5. **Descargar** en formato deseado

## ⚙️ Configuración Avanzada

### Variables de Entorno
```bash
# Database
DATABASE_URL=postgresql://inventario:password123@localhost:5432/inventario_retail

# Redis
REDIS_URL=redis://localhost:6379/0

# Flask
FLASK_ENV=production
SECRET_KEY=tu-clave-secreta-aqui

# ML Settings
INFLACION_MENSUAL=0.045  # 4.5% mensual
TIMEZONE=America/Argentina/Buenos_Aires
```

### Personalización Tema
```css
/* Colores principales en /static/css/styles.css */
:root {
    --primary-color: #0066cc;      /* Azul principal */
    --secondary-color: #75c7ff;    /* Azul claro */
    --success-color: #28a745;      /* Verde éxito */
    --warning-color: #ffc107;      /* Amarillo alerta */
    --danger-color: #dc3545;       /* Rojo crítico */
}
```

## 🔧 Comandos Útiles

```bash
# Gestión de servicios
docker-compose up -d          # Iniciar servicios
docker-compose down           # Parar servicios
docker-compose restart        # Reiniciar servicios
docker-compose logs -f        # Ver logs en tiempo real

# Base de datos
docker-compose exec postgres psql -U inventario -d inventario_retail
docker-compose exec postgres pg_dump -U inventario inventario_retail > backup.sql

# Redis
docker-compose exec redis redis-cli
docker-compose exec redis redis-cli flushall

# Actualizaciones
docker-compose pull          # Actualizar imágenes
docker-compose build         # Reconstruir aplicación
```

## 📊 Monitoreo y Performance

### Métricas Clave
- **Response Time**: <200ms endpoints principales
- **Cache Hit Rate**: >90% consultas frecuentes
- **WebSocket Connections**: Monitoreo conexiones activas
- **Database Performance**: Query times <100ms

### Logs Importantes
```bash
# Dashboard logs
docker-compose logs dashboard | grep ERROR

# Database performance
docker-compose logs postgres | grep "slow query"

# Redis cache stats
docker-compose exec redis redis-cli info stats
```

## 🛡️ Seguridad

### Configuración SSL
```bash
# Generar certificados propios (producción)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/nginx.key \
    -out ssl/nginx.crt
```

### Backup Automático
```bash
# Configurar cron para backup diario
0 2 * * * docker-compose exec postgres pg_dump -U inventario inventario_retail > /backups/inventario_$(date +%Y%m%d).sql
```

## 🐛 Troubleshooting

### Problemas Comunes

**Dashboard no carga**
```bash
# Verificar servicios
docker-compose ps
docker-compose logs dashboard

# Reiniciar si es necesario
docker-compose restart dashboard
```

**Base de datos no conecta**
```bash
# Verificar PostgreSQL
docker-compose logs postgres
docker-compose exec postgres pg_isready

# Recrear si es necesario
docker-compose down
docker volume rm inventario_postgres_data
docker-compose up -d
```

**Redis cache no funciona**
```bash
# Verificar Redis
docker-compose exec redis redis-cli ping
docker-compose logs redis

# Limpiar cache
docker-compose exec redis redis-cli flushall
```

## 📞 Soporte

Para soporte técnico:
- **Logs detallados**: `docker-compose logs -f`
- **Estado servicios**: `docker-compose ps`
- **Configuración**: Revisar variables entorno

## 🚀 Próximas Mejoras

- [ ] Dashboard móvil nativo
- [ ] Integración WhatsApp alertas
- [ ] API REST completa
- [ ] Módulo multi-sucursal
- [ ] Análisis competencia automático

---

**© 2025 Sistema Inventario Retail Argentino - Dashboard Web Interactivo**
