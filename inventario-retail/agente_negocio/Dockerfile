FROM python:3.11-slim

# Configuración para Argentina
ENV TZ=America/Argentina/Buenos_Aires
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar dependencias del sistema incluyendo Tesseract para OCR
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash negocio && \
    mkdir -p /app/logs /app/uploads /app/models && \
    chown -R negocio:negocio /app

USER negocio
WORKDIR /app

# Instalar dependencias Python
COPY --chown=negocio:negocio ../requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY --chown=negocio:negocio . ./
COPY --chown=negocio:negocio ../shared ../shared

# Variables de entorno por defecto
ENV PYTHONPATH=/app
ENV PATH=/home/negocio/.local/bin:$PATH
ENV TESSERACT_CMD=/usr/bin/tesseract

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]