# CONFIGURACIONES DE PRODUCCIÓN - BI ORCHESTRATOR
## Resultado de aplicar PROMPT 3 con GitHub Copilot Pro

---

## 1. VARIABLES DE ENTORNO COMPLETAS

### Core Configuration
```bash
# === APLICACIÓN BASE ===
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
PYTHONPATH=/app/src

# === WEB SCRAPING CONFIG ===
MAX_CONCURRENT_REQUESTS=20
DOWNLOAD_DELAY=1
RANDOMIZE_DOWNLOAD_DELAY=true
RESPECT_ROBOTS_TXT=true
USER_AGENT_ROTATION=true
HEADLESS_BROWSER=true
BROWSER_TIMEOUT=30

# === BROWSER SETTINGS ===
CHROME_BIN=/usr/bin/chromium
CHROME_PATH=/usr/bin/chromium
WINDOW_SIZE=1920,1080
CHROME_OPTIONS=--no-sandbox,--disable-dev-shm-usage,--disable-gpu

# === PROXY CONFIGURATION ===
PROXY_ENABLED=true
PROXY_ROTATION=true
PROXY_POOL_SIZE=50
PROXY_SERVICE_URL=http://proxy-service:8080

# === DATABASE ===
DATABASE_URL=postgresql://user:pass@host:5432/bi_orchestrator_prod
REDIS_URL=redis://:password@host:6379/1

# === AI ANALYSIS ===
OPENAI_API_KEY=sk-tu-clave-openai-produccion
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4000
OPENAI_TIMEOUT=30
OPENAI_RATE_LIMIT_PER_MINUTE=60
OPENAI_DAILY_BUDGET_USD=100

# === LEGAL & COMPLIANCE ===
RATE_LIMIT_ENABLED=true
DEFAULT_CRAWL_DELAY=2
MAX_REQUESTS_PER_DOMAIN=100
RESPECT_ROBOTS_TXT=true

# === MONITORING ===
PROMETHEUS_ENABLED=true
HEALTH_CHECK_INTERVAL=60
ALERT_EMAIL=admin@empresa.com.ar
```

---

## 2. CONFIGURACIÓN DE SEGURIDAD

### Rate Limiting y Compliance
```python
# src/legal/compliance_config.py
COMPLIANCE_CONFIG = {
    'rate_limiting': {
        'enabled': True,
        'default_delay': 2,  # seconds
        'max_requests_per_minute': 30,
        'max_requests_per_hour': 1000,
        'max_requests_per_domain': 100
    },
    'robots_txt': {
        'respect': True,
        'cache_duration': 3600,  # 1 hour
        'user_agent': 'BI-Orchestrator-Bot/1.0'
    },
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ],
    'headers': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
}
```

---

## 3. DOCKER CONFIGURATION

### Dockerfile.production
```dockerfile
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libxtst6 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash scraper && \
    mkdir -p /app /data /logs && \
    chown -R scraper:scraper /app /data /logs

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=scraper:scraper . .

# Configure Chrome environment
ENV CHROME_BIN=/usr/bin/chromium \
    CHROME_PATH=/usr/bin/chromium \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

USER scraper

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["python", "src/main.py"]
```

---

## 4. CONFIGURACIÓN ESPECÍFICA DE SCRAPING

### Competitive Intelligence Configuration
```json
{
  "competitors": {
    "automotive": [
      {
        "name": "Toyota Argentina",
        "urls": [
          {"url": "https://www.toyota.com.ar/precios", "type": "pricing"},
          {"url": "https://www.toyota.com.ar/modelos", "type": "products"}
        ],
        "scraping_rules": {
          "rate_limit": 2,
          "scrape_frequency": "daily",
          "active": true
        }
      }
    ],
    "retail": [
      {
        "name": "MercadoLibre",
        "urls": [
          {"url": "https://www.mercadolibre.com.ar/categorias", "type": "categories"}
        ],
        "scraping_rules": {
          "rate_limit": 1,
          "scrape_frequency": "hourly",
          "active": true
        }
      }
    ]
  },
  "global_settings": {
    "max_pages_per_site": 100,
    "timeout_per_page": 30,
    "retry_attempts": 3,
    "respect_robots_txt": true
  }
}
```

Este archivo de configuraciones proporciona la base para deployar el BI Orchestrator en producción con todas las consideraciones de compliance, seguridad y performance necesarias para web scraping empresarial.