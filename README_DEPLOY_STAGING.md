# 🚀 Guía de Despliegue en Staging

## 1. Preparar entorno
- Clona el repo:
  ```bash
  git clone https://github.com/eevans-d/aidrive_genspark_forensic.git
  cd aidrive_genspark_forensic
  ```
- Crea y activa entorno virtual:
  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```

## 2. Configurar variables de entorno
- Copia `.env.example` a `.env` en cada servicio:
  ```bash
  cp inventario-retail/agente_deposito/.env.example inventario-retail/agente_deposito/.env
  cp inventario-retail/agente_negocio/.env.example inventario-retail/agente_negocio/.env
  cp inventario-retail/ml/.env.example inventario-retail/ml/.env
  ```
- Edita los valores sensibles (`JWT_SECRET`, `DB_URL`, etc.) siguiendo los comentarios de cada `.env.example`.

## 3. Levantar servicios
- Usar Docker Compose (recomendado):
  ```bash
  docker-compose -f inventario_retail_dashboard_web/docker-compose.yml up -d
  ```
- O iniciar manualmente cada servicio:
  ```bash
  cd inventario-retail/agente_deposito && uvicorn main_complete:app --host 0.0.0.0 --port 8001
  cd inventario-retail/agente_negocio && uvicorn main_complete:app --host 0.0.0.0 --port 8002
  cd inventario-retail/ml && uvicorn main_ml_service:app --host 0.0.0.0 --port 8003
  ```

## 4. Emitir token JWT para pruebas
- Usa el endpoint `/api/v1/auth/login` en cada servicio:
  ```bash
  curl -X POST http://localhost:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}'
  ```
- Copia el `access_token` para usar en los siguientes tests.

## 5. Ejecutar pruebas de humo
- Ejecuta el script `smoke_test_staging.sh` para validar endpoints críticos:
  ```bash
  bash smoke_test_staging.sh
  ```
- Verifica que los endpoints protegidos devuelven 401 sin token y 200 con token.
- Revisa los resultados y logs de los servicios.

## 6. Validar logs y métricas
- Revisa los logs de cada servicio para errores y advertencias.
- Valida que el rate limiting y los headers de seguridad estén activos.
- Consulta la documentación de endpoints en cada microservicio para detalles avanzados.

---
Sistema listo para staging y producción. Para dudas, consulta el README principal o abre un issue en GitHub.
