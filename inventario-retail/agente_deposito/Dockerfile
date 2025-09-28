FROM python:3.11-slim

# Configuración para Argentina
ENV TZ=America/Argentina/Buenos_Aires
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash agente && \
    mkdir -p /app/logs /app/uploads && \
    chown -R agente:agente /app

USER agente
WORKDIR /app

# Instalar dependencias Python
COPY --chown=agente:agente ../requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY --chown=agente:agente . ./
COPY --chown=agente:agente ../shared ../shared

# Variables de entorno por defecto
ENV PYTHONPATH=/app
ENV PATH=/home/agente/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]