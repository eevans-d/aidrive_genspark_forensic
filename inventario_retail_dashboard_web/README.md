# 🎯 Dashboard Web Interactivo - Sistema Inventario Retail Argentino

Dashboard web completo con interface responsive, WebSockets tiempo real, integración ML y optimizado para uso retail argentino.

## 🚀 Características Principales

### 📊 Dashboard Operativo
- **Métricas Tiempo Real**: KPIs, disponibilidad, cobertura, inflación
- **Alertas Inteligentes**: Stock crítico, productos agotándose
- **Recomendaciones Compra**: Qué comprar HOY con cantidades exactas
- **Gráficos Interactivos**: Predicciones demanda, estado stock

### 📱 Mobile-First Design  
- **Responsive**: Optimizado tablet/móvil warehouse
- **Touch-Friendly**: Botones grandes, gestos táctiles
- **Offline Ready**: Service Worker para funcionalidad básica
- **PWA Support**: Instalable como app nativa

### ⚡ Performance Avanzado
- **WebSockets**: Updates tiempo real sin refresh
- **Redis Cache**: Consultas optimizadas
- **Lazy Loading**: Carga progresiva contenido
- **Compression**: Gzip, minificación automática

### 🇦🇷 Contexto Argentino
- **Timezone**: America/Argentina/Buenos_Aires
- **Moneda**: Formato ARS ($1.234,56)
- **Inflación**: 4.5% mensual integrada
- **Validación CUIT**: Algoritmo verificación automática

## 📁 Estructura Proyecto

```
inventario-retail-web/
├── app/
│   ├── main.py              # Aplicación Flask principal
│   ├── routes/              # Rutas organizadas
│   └── utils/               # Utilities y helpers
├── templates/
│   ├── base.html            # Layout base responsive
│   ├── dashboard.html       # Dashboard principal
│   ├── productos.html       # Gestión productos
│   ├── ocr.html             # Interface OCR
│   └── reportes.html        # Generación reportes
├── static/
│   ├── css/                 # Estilos responsive
│   ├── js/                  # JavaScript interactivo
│   └── img/                 # Assets
├── config/
│   └── nginx.conf           # Reverse proxy
├── requirements.txt         # Dependencias Python
├── Dockerfile              # Container web app
├── docker-compose.yml      # Stack completo
└── deploy.sh               # Script deployment
```

## 🔧 Instalación Rápida

### Método 1: Docker (Recomendado)

```bash
# Clonar o descargar archivos
cd inventario-retail-web

# Ejecutar script deployment automático
chmod +x deploy.sh
./deploy.sh

# O manual:
docker-compose up -d
```

### Método 2: Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Variables entorno
export FLASK_ENV=development
export DATABASE_URL=postgresql://user:pass@localhost/inventario_retail
export REDIS_URL=redis://localhost:6379/0

# Ejecutar aplicación
python app/main.py
```

## 🌐 Endpoints Principales

### Dashboard Web
```bash
GET  /                      # Dashboard principal
GET  /productos             # Gestión productos
GET  /ocr                   # Interface OCR facturas  
GET  /reportes              # Generación reportes
POST /upload-factura        # Upload OCR
```

### API REST
```bash
GET  /api/dashboard-data    # Datos dashboard JSON
GET  /api/productos-autocomplete  # Búsqueda productos
POST /api/generar-reporte   # Crear reportes
```

### WebSocket Events
```javascript
// Conectar
socket.emit('request_dashboard_update')

// Recibir
socket.on('dashboard_update', data => { ... })
socket.on('factura_procesada', data => { ... })
```

## 👥 Usuarios de Prueba

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| admin | admin123 | Administrador |
| empleado | emp123 | Empleado |
| gerente | ger123 | Gerente |

## 🔗 Integración APIs Backend

El dashboard se integra automáticamente con:

- **Agente Depósito** (puerto 8000): CRUD productos, stock
- **Agente Negocio** (puerto 8001): OCR facturas, pricing
- **ML Predictor** (puerto 8002): Predicciones, recomendaciones
- **Schedulers** (puerto 8003): Tareas automáticas

## 📱 Funcionalidades Mobile

### Optimizaciones Táctiles
- Botones mínimo 44px (Apple guidelines)
- Zoom disabled en inputs (iOS)
- Touch feedback visual
- Swipe gestures personalizados

### PWA Features
```javascript
// Service Worker automático
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
}

// Instalable como app
window.addEventListener('beforeinstallprompt', e => {
    // Show install banner
})
```

## 🎨 Customización UI

### Colores Argentina
```css
:root {
    --argentina-celeste: #74ACDF;
    --argentina-sol: #F9A602;
    --primary-color: #0d6efd;
}
```

### Responsive Breakpoints
```css
/* Mobile */ @media (max-width: 768px)
/* Tablet */ @media (769px - 1024px)  
/* Desktop */ @media (min-width: 1025px)
```

## ⚡ Performance Optimizations

### Redis Cache Strategy
```python
# Cache automático 30 segundos
@cache_with_ttl(30)
def get_dashboard_data():
    return fetch_from_apis()

# Invalidación inteligente
def invalidate_product_cache(product_id):
    redis.delete(f"product:{product_id}")
```

### WebSocket Optimizations
```javascript
// Throttling updates
const throttledUpdate = throttle(updateDashboard, 1000)

// Connection management
socket.on('disconnect', () => {
    // Retry logic
    setTimeout(connectSocket, 5000)
})
```

## 📊 Monitoring & Analytics

### Health Checks
```bash
# Docker health check
curl -f http://localhost:5000/health

# Service status
docker-compose ps
```

### Performance Metrics
```python
# Built-in metrics
/api/metrics              # Prometheus format
/api/dashboard-stats      # JSON stats
```

## 🔒 Security Features

### Authentication
- Session-based authentication
- CSRF protection automática
- Rate limiting por IP
- Input sanitization

### Data Protection
```python
# Sensitive data masking
def mask_cuit(cuit):
    return f"{cuit[:2]}-****-{cuit[-1:]}"
```

## 🐛 Troubleshooting

### Problemas Comunes

**Dashboard no carga**
```bash
# Verificar servicios
docker-compose ps
docker-compose logs dashboard-web
```

**WebSockets no conectan**
```bash
# Verificar Redis
redis-cli ping
# Verificar puertos
netstat -an | grep 5000
```

**Performance lento**
```bash
# Cache hit rate
redis-cli info stats | grep keyspace_hits
# Query analysis
docker-compose logs postgres
```

## 📈 Roadmap Futuras Mejoras

- [ ] Notificaciones Push nativas
- [ ] Export PDF reportes avanzados  
- [ ] Integración WhatsApp Business
- [ ] Dashboard analytics avanzado
- [ ] Multi-idioma (ES/EN)
- [ ] Dark mode automático

## 🤝 Soporte

Para soporte técnico:
1. Verificar logs: `docker-compose logs -f`
2. Estado servicios: `docker-compose ps`
3. Restart: `docker-compose restart dashboard-web`

## 📄 Licencia

Sistema Inventario Retail Argentino - Uso Interno
© 2025 - Desarrollo personalizado para operaciones retail argentinas

---

**🇦🇷 ¡El futuro del retail argentino inteligente comienza ahora!**
