# syntax=docker/dockerfile:1.6
FROM python:3.12-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema mínimas (opcional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para dashboard
RUN groupadd -r dashboarduser && useradd --no-log-init -r -g dashboarduser dashboarduser && \
    mkdir -p /app/logs /app/cache && \
    chown -R dashboarduser:dashboarduser /app

# Configurar timeout y retries para descargas de paquetes grandes
ENV PIP_DEFAULT_TIMEOUT=600
ENV PIP_RETRIES=5

# Configurar PyPI mirror (Tsinghua) para mayor confiabilidad
RUN mkdir -p /root/.pip && \
    echo "[global]" > /root/.pip/pip.conf && \
    echo "index-url = https://pypi.tuna.tsinghua.edu.cn/simple" >> /root/.pip/pip.conf && \
    echo "trusted-host = pypi.tuna.tsinghua.edu.cn" >> /root/.pip/pip.conf

# Instalar requirements
COPY web_dashboard/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Copiar código con ownership (incluir forensic module)
COPY --chown=dashboarduser:dashboarduser . /app

# Cambiar a usuario no-root
USER dashboarduser

# Puerto de la app
EXPOSE 8080

# Variables por defecto seguras (pueden ser sobreescritas)
ENV DASHBOARD_RATELIMIT_ENABLED=true \
    DASHBOARD_RATELIMIT_MAX=100 \
    DASHBOARD_API_KEY=change-me

# Comando de ejecución (uvicorn)
CMD ["uvicorn", "web_dashboard.dashboard_app:app", "--host", "0.0.0.0", "--port", "8080"]
