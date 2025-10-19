#!/bin/bash
# Setup .env.staging file with all required variables
# Run this before deployment

set -e

ENV_FILE=".env.staging"
WORKSPACE="/home/eevan/ProyectosIA/aidrive_genspark"

echo "Setting up staging environment file..."

if [ -f "$ENV_FILE" ]; then
    echo ".env.staging already exists. Skipping creation."
    exit 0
fi

cat > "$ENV_FILE" << 'EOF'
# Environment Configuration for Staging Deployment
# DÍA 4-5 Staging Environment Setup
# Date: October 19, 2025

# ============================================================================
# CORE ENVIRONMENT CONFIGURATION
# ============================================================================
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=info

# ============================================================================
# API SERVICE CONFIGURATION
# ============================================================================
API_HOST=0.0.0.0
API_PORT=8080
API_WORKERS=4
REQUEST_TIMEOUT=30
ASYNC_TIMEOUT=60

# ============================================================================
# DATABASE CONFIGURATION (PostgreSQL)
# ============================================================================
STAGING_DB_USER=inventario_user
STAGING_DB_PASSWORD=staging_secure_pass_2025
STAGING_DB_NAME=inventario_retail_staging
STAGING_DB_PORT=5433
DATABASE_URL=postgresql://inventario_user:staging_secure_pass_2025@postgres:5432/inventario_retail_staging
DB_POOL_SIZE=20
DB_POOL_TIMEOUT=30

# ============================================================================
# REDIS CACHE CONFIGURATION
# ============================================================================
STAGING_REDIS_HOST=redis
STAGING_REDIS_PORT=6379
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_POOL_SIZE=10
REDIS_TIMEOUT=5
CACHE_TTL_SECONDS=300

# ============================================================================
# AWS S3 / LOCALSTACK CONFIGURATION
# ============================================================================
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_ENDPOINT_URL=http://localstack:4566
S3_BUCKET_NAME=inventario-retail-bucket-staging
STAGING_S3_PORT=4566
S3_TIMEOUT=10

# ============================================================================
# OPENAI CIRCUIT BREAKER CONFIGURATION
# ============================================================================
OPENAI_API_KEY=sk-test-staging-no-real-calls-in-ci
OPENAI_CB_FAILURE_THRESHOLD=5
OPENAI_CB_RECOVERY_TIMEOUT=30
OPENAI_CB_HALF_OPEN_REQUESTS=2
OPENAI_TIMEOUT=30
OPENAI_ENABLED=false

# ============================================================================
# DATABASE CIRCUIT BREAKER CONFIGURATION
# ============================================================================
DB_CB_FAILURE_THRESHOLD=3
DB_CB_RECOVERY_TIMEOUT=20
DB_CB_HALF_OPEN_REQUESTS=1
DB_CONNECTION_RETRY_ATTEMPTS=3
DB_DEGRADED_MODE_ENABLED=true

# ============================================================================
# REDIS CIRCUIT BREAKER CONFIGURATION
# ============================================================================
REDIS_CB_FAILURE_THRESHOLD=5
REDIS_CB_RECOVERY_TIMEOUT=15
REDIS_CB_HALF_OPEN_REQUESTS=2
REDIS_CACHE_BYPASS_ENABLED=true

# ============================================================================
# S3 CIRCUIT BREAKER CONFIGURATION
# ============================================================================
S3_CB_FAILURE_THRESHOLD=4
S3_CB_RECOVERY_TIMEOUT=25
S3_CB_HALF_OPEN_REQUESTS=2
S3_UPLOAD_TIMEOUT=10
S3_FALLBACK_ENABLED=true

# ============================================================================
# DEGRADATION MANAGER CONFIGURATION
# ============================================================================
HEALTH_CHECK_INTERVAL=10
DEGRADATION_RECOVERY_PREDICTION=true
SERVICE_WEIGHTS=database:0.50,openai:0.30,redis:0.15,s3:0.05
OPTIMAL_THRESHOLD=90
DEGRADED_THRESHOLD=70
LIMITED_THRESHOLD=60
MINIMAL_THRESHOLD=40

# ============================================================================
# SECURITY & API KEY CONFIGURATION
# ============================================================================
DASHBOARD_API_KEY=staging-api-key-2025
STAGING_DASHBOARD_API_KEY=staging-api-key-2025
DASHBOARD_RATELIMIT_ENABLED=true
DASHBOARD_RATELIMIT_REQUESTS=100
DASHBOARD_RATELIMIT_WINDOW=60
DASHBOARD_ENABLE_HSTS=true
DASHBOARD_FORCE_HTTPS=false

# ============================================================================
# MONITORING & METRICS CONFIGURATION
# ============================================================================
METRICS_ENABLED=true
STRUCTURED_LOGGING=true
PROMETHEUS_ENABLED=true
STAGING_PROMETHEUS_PORT=9091

# ============================================================================
# GRAFANA CONFIGURATION
# ============================================================================
STAGING_GRAFANA_PASSWORD=admin_staging_2025
STAGING_GRAFANA_PORT=3001

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================
MAX_RETRY_ATTEMPTS=3
BATCH_SIZE=50
WORKERS_POOL_SIZE=10

# ============================================================================
# FEATURE FLAGS
# ============================================================================
FEATURE_AI_ENABLED=true
FEATURE_CACHING_ENABLED=true
FEATURE_REALTIME_ENABLED=true
FEATURE_S3_ENABLED=true
FEATURE_ADVANCED_ANALYTICS_ENABLED=true

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_FORMAT=json
LOG_OUTPUT_PATH=/app/logs/staging
REQUEST_ID_HEADER=X-Request-ID
PRESERVE_REQUEST_ID=true
EOF

echo "✓ .env.staging file created successfully"
echo ""
echo "Environment variables configured:"
echo "  - Database: PostgreSQL at postgres:5432"
echo "  - Cache: Redis at redis:6379"
echo "  - Storage: LocalStack at localstack:4566"
echo "  - API: Dashboard at 0.0.0.0:8080"
echo "  - Metrics: Prometheus at http://localhost:9091"
echo "  - Visualization: Grafana at http://localhost:3001"
echo ""
