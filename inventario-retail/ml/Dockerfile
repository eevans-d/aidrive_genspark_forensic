FROM python:3.11-slim

# Configuración para Argentina
ENV TZ=America/Argentina/Buenos_Aires
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash mluser && \
    mkdir -p /app/logs /app/models /app/data && \
    chown -R mluser:mluser /app

USER mluser
WORKDIR /app

# Instalar dependencias Python
COPY --chown=mluser:mluser ../requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY --chown=mluser:mluser . ./
COPY --chown=mluser:mluser ../shared ../shared

# Variables de entorno por defecto
ENV PYTHONPATH=/app
ENV PATH=/home/mluser/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

EXPOSE 8003

CMD ["uvicorn", "main_ml_service:app", "--host", "0.0.0.0", "--port", "8003"]