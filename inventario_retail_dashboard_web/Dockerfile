# Dashboard Web Interactivo - Sistema Inventario Retail Argentino
FROM python:3.11-slim

# Información imagen
LABEL maintainer="Sistema Inventario Retail ARG"
LABEL version="1.0"
LABEL description="Dashboard Web Interactivo para gestión inventario retail argentino"

# Variables entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production
ENV FLASK_APP=app.main:app

# Crear usuario no-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependencias sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Directorio trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p uploads logs static/uploads

# Permisos usuario
RUN chown -R appuser:appuser /app
USER appuser

# Exponer puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Comando por defecto
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "app.main:app"]
