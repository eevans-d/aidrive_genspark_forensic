# 🚀 INVENTARIO RETAIL - WEB DASHBOARD SYSTEM
## Guía de Despliegue y Onboarding

### 📝 Resumen del Sistema
Dashboard web interactivo para inventario retail argentino:
- KPIs y métricas en tiempo real (WebSockets)
- Diseño mobile-first para tablets y warehouse
- Integración con APIs backend (depósito, negocio, ML)
- Despliegue sencillo vía Docker

### ⚡ Despliegue Rápido (Recomendado)
```bash
cd inventario_retail_dashboard_web/
chmod +x deploy.sh
./deploy.sh
```

### 🛠️ Despliegue Manual
1. Descarga el sistema:
   ```bash
   cp -r inventario_retail_dashboard_web/ ~/inventario-dashboard/
   cd ~/inventario-dashboard/
   ```
2. Levanta con Docker Compose:
   ```bash
   docker-compose up -d
   ```
3. Accede al dashboard:
   - URL: http://localhost:5000
   - Login por defecto: admin/admin123

### 🌟 Características Clave
- Redis Cache Intelligence (TTL + invalidación)
- OCR avanzado (EasyOCR, Tesseract, PaddleOCR)
- ML para recomendaciones de compra
- Web dashboard real-time y responsive

### 🧑‍💻 Onboarding Rápido
- Sigue los pasos de despliegue rápido
- Consulta el README principal para integración y seguridad
- Revisa los endpoints y documentación en cada microservicio

---
Para soporte, consulta README principal o abre un issue en GitHub.
