# 🛒 Sistema Multiagente Inventario Retail Argentino

Sistema robusto y modular para gestión de inventario, compras, ML y dashboard web, optimizado para retail argentino y listo para producción.

## 🚀 Características Principales
- **Microservicios independientes:** Depósito, Negocio, ML, Dashboard
- **Seguridad avanzada:** JWT, roles, rate limiting, headers
- **Integración ML:** Recomendaciones de compra, predicción de demanda
- **Dashboard web interactivo:** KPIs, alertas, gráficos, mobile-first
- **Despliegue sencillo:** Docker Compose, scripts automatizados
- **Documentación y onboarding guiado**

## 🏗️ Estructura del Proyecto
```
├── inventario-retail/
│   ├── agente_deposito/
│   ├── agente_negocio/
│   ├── ml/
│   └── ...
├── inventario_retail_dashboard_web/
│   ├── app/
│   ├── templates/
│   └── static/
├── integrations/
├── shared/
├── tests/
└── ...
```

## 📦 Instalación Rápida
1. Clona el repo y crea entorno virtual:
   ```bash
   git clone https://github.com/eevans-d/aidrive_genspark_forensic.git
   cd aidrive_genspark_forensic
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Configura variables de entorno:
   ```bash
   cp inventario-retail/agente_deposito/.env.example inventario-retail/agente_deposito/.env
   cp inventario-retail/agente_negocio/.env.example inventario-retail/agente_negocio/.env
   cp inventario-retail/ml/.env.example inventario-retail/ml/.env
   # Edita los valores sensibles
   ```
3. Despliega servicios:
   ```bash
   docker-compose -f inventario_retail_dashboard_web/docker-compose.yml up -d
   # O inicia manualmente cada microservicio
   ```

## 🔑 Autenticación y Pruebas
- Obtén token JWT usando `/api/v1/auth/login` en cada servicio
- Ejecuta `smoke_test_staging.sh` para validar endpoints críticos

## 📚 Documentación y Guías
- Guía de despliegue: `README_DEPLOY_STAGING.md`
- Guía dashboard web: `inventario_retail_dashboard_web/DEPLOYMENT_GUIDE.md`
- Documentación endpoints: ver carpetas de cada microservicio

## 🧑‍💻 Onboarding Rápido
- Sigue los pasos de instalación y despliegue
- Consulta las guías específicas para cada módulo
- Revisa los archivos `.env.example` para configuración segura

## 🛡️ Seguridad y Robustez
- JWT y roles en todos los endpoints
- Rate limiting y headers de seguridad
- Logging centralizado y manejo global de errores

## 📝 Contacto y Soporte
- Email: soporte@inventarioretail.com
- Issues: GitHub Issues

---
Sistema listo para producción, optimizado para robustez, facilidad de uso y contexto argentino.