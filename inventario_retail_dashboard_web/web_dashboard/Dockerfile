# Dockerfile - Dashboard Web Sistema Inventario Retail Argentino
FROM python:3.11-slim

# Metadata
LABEL maintainer="Sistema Inventario Retail Argentino"
LABEL version="1.0"
LABEL description="Dashboard Web Interactivo para gestión de inventario"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorio uploads
RUN mkdir -p uploads

# Exponer puerto
EXPOSE 5000

# Comando de inicio
CMD ["python", "app.py"]
