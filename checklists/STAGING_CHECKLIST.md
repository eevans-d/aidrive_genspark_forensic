# Deployment Checklist - DÍA 4-5 Staging Deployment

## Status: PHASE 1 - HORAS 1-2 ✅

**Date**: October 19, 2025  
**Environment**: Staging  
**System**: aidrive_genspark_forensic (Resilience Hardening Framework)

---

## 1. PRE-DEPLOYMENT VERIFICATION

### 1.1 Code Status ✅
- [x] Feature branch `feature/resilience-hardening` is up-to-date
- [x] All DÍA 1-3 commits integrated (12 commits, 10,265 lines)
- [x] 4 Circuit Breakers fully implemented
  - [x] OpenAI Circuit Breaker (DÍA 1 HORAS 1-4)
  - [x] Database Circuit Breaker (DÍA 1 HORAS 4-7)
  - [x] Redis Circuit Breaker (DÍA 3 HORAS 1-3)
  - [x] S3 Circuit Breaker (DÍA 3 HORAS 3-5)
- [x] Integration layer complete (DÍA 3 HORAS 7-8, 28/28 checks passed)
- [x] DegradationManager orchestrates all 4 services

### 1.2 Testing Status ✅
- [x] Unit tests for all CBs (70+ test cases)
- [x] Integration tests created (test_integration_dia3.py, 450+ lines)
- [x] Validation scripts passing (88/88 checks)
- [x] Smoke tests written (smoke_test_staging.py, 35+ test cases)
- [x] Performance benchmarks established
- [x] Security tests included

### 1.3 Documentation Status ✅
- [x] Architecture documentation complete
- [x] Circuit breaker design documented
- [x] Service integration matrix documented
- [x] Feature availability matrix documented (16 features)
- [x] Deployment guide created
- [x] Operations runbook created

---

## 2. INFRASTRUCTURE SETUP

### 2.1 Docker Compose Configuration ✅
- [x] docker-compose.staging.yml created (284 lines)
- [x] All services configured:
  - [x] PostgreSQL 15-alpine with persistence
  - [x] Redis 7-alpine with LRU eviction
  - [x] LocalStack for S3 mocking
  - [x] Prometheus for metrics collection
  - [x] Grafana for visualization
  - [x] Dashboard API service
- [x] Health checks configured for each service
- [x] Volume persistence configured
- [x] Network isolation setup (staging-network)
- [x] Environment variables templated

### 2.2 Service Configuration Files Needed
- [ ] inventario-retail/prometheus/prometheus.staging.yml (create)
- [ ] inventario-retail/grafana/provisioning/* (create)
- [ ] inventario-retail/Dockerfile.dashboard (verify/update for staging)
- [ ] scripts/init-s3.sh (create for S3 bucket initialization)

### 2.3 Environment File
- [ ] .env.staging created with all required variables:
  - [ ] Database credentials (STAGING_DB_*)
  - [ ] Redis configuration (STAGING_REDIS_*)
  - [ ] S3 configuration (STAGING_S3_*)
  - [ ] Circuit breaker thresholds (all 4 services)
  - [ ] Degradation manager settings
  - [ ] API keys and security tokens

---

## 3. DATABASE SETUP

### 3.1 PostgreSQL Initialization ✅
- [x] Database docker-compose service configured
- [x] Health checks configured
- [x] Persistence volume configured
- [ ] Init scripts in place:
  - [ ] Create inventario_retail_staging database
  - [ ] Create required schemas
  - [ ] Initialize circuit breaker tracking tables
  - [ ] Set up connection pooling (20 connections)

### 3.2 Database Monitoring
- [ ] PostgreSQL metrics exposed to Prometheus
- [ ] Query performance monitored
- [ ] Connection pool status tracked
- [ ] Database CB status visible in Grafana

---

## 4. REDIS SETUP

### 4.1 Redis Configuration ✅
- [x] Redis docker-compose service configured
- [x] Persistence (AOF) enabled
- [x] Memory limits set (512MB)
- [x] Eviction policy configured (allkeys-lru)
- [x] Health checks configured
- [ ] Redis modules loaded if needed:
  - [ ] Redis Search (optional for future)
  - [ ] Redis JSON (optional for future)

### 4.2 Redis Monitoring
- [ ] Redis metrics exposed to Prometheus
- [ ] Cache hit/miss ratios tracked
- [ ] Memory usage monitored
- [ ] Redis CB status visible in Grafana

---

## 5. S3/OBJECT STORAGE SETUP

### 5.1 LocalStack Configuration ✅
- [x] LocalStack docker-compose service configured
- [x] S3 service enabled
- [x] AWS credentials configured (test/test)
- [x] Health checks configured
- [x] Volume persistence configured
- [ ] Init script to create bucket:
  - [ ] Create `inventario-retail-bucket-staging` bucket
  - [ ] Configure CORS for staging
  - [ ] Set up bucket versioning
  - [ ] Configure lifecycle policies

### 5.2 S3/LocalStack Monitoring
- [ ] S3 metrics exposed (upload/download/delete counts)
- [ ] Storage usage tracked
- [ ] Request latency monitored
- [ ] S3 CB status visible in Grafana

---

## 6. METRICS & MONITORING

### 6.1 Prometheus Setup ✅
- [x] Prometheus docker-compose service configured
- [x] Storage configured (7 days retention)
- [ ] prometheus.staging.yml scrape config:
  - [ ] Dashboard API targets (port 8080/metrics)
  - [ ] Database targets (via postgres_exporter if available)
  - [ ] Redis targets (via redis_exporter if available)
  - [ ] S3/LocalStack targets (if metrics exposed)
  - [ ] Scrape intervals configured (15s default, 30s for slow services)

### 6.2 Grafana Setup ✅
- [x] Grafana docker-compose service configured
- [ ] Grafana provisioning:
  - [ ] Datasources configured (Prometheus)
  - [ ] Dashboards created:
    - [ ] Main system health dashboard
    - [ ] Circuit breaker status dashboard
    - [ ] Service performance dashboard
    - [ ] Degradation levels dashboard
    - [ ] Feature availability dashboard

### 6.3 Dashboard Metrics Exposed ✅
- [x] Prometheus /metrics endpoint configured
- [x] Metrics identified:
  - dashboard_requests_total (by endpoint, status, method)
  - dashboard_errors_total (by error type)
  - dashboard_request_duration_ms (p50, p95, p99)
  - circuit_breaker_state (by service)
  - health_score (by service)
  - degradation_level (current)
  - feature_availability (by feature)

---

## 7. SECURITY CONFIGURATION

### 7.1 API Security ✅
- [x] API Key authentication required
- [x] X-API-Key header validation
- [x] Rate limiting configured (100 req/60s)
- [x] Request timeout set (30s)
- [ ] Security headers configured:
  - [ ] Strict-Transport-Security (HSTS)
  - [ ] Content-Security-Policy (CSP)
  - [ ] X-Content-Type-Options
  - [ ] X-Frame-Options
  - [ ] X-XSS-Protection

### 7.2 Secrets Management
- [ ] Environment variables stored securely
- [ ] Database password secured
- [ ] OpenAI API key secured
- [ ] AWS credentials (test/test for staging only)
- [ ] Grafana admin password secured

### 7.3 Network Security
- [x] Internal docker network (staging-network)
- [x] No service exposed except Dashboard (port 8080)
- [ ] Firewall rules configured:
  - [ ] Only Dashboard port accessible from outside
  - [ ] Database only accessible from Dashboard
  - [ ] Redis only accessible from Dashboard
  - [ ] LocalStack only accessible from Dashboard
  - [ ] Prometheus/Grafana accessible only internally

---

## 8. LOGGING & OBSERVABILITY

### 8.1 Structured Logging ✅
- [x] Structured logging enabled
- [x] JSON log format configured
- [x] request_id tracking enabled
- [ ] Log aggregation setup:
  - [ ] Logs written to /logs/staging
  - [ ] Log rotation configured
  - [ ] Log level monitoring

### 8.2 Tracing (Optional for DÍA 4-5)
- [ ] Distributed tracing setup (if time permits)
- [ ] Trace collection from all services
- [ ] Request tracing across service boundaries

---

## 9. DEPLOYMENT PROCESS

### 9.1 Initial Deployment
- [ ] Pull latest code from feature/resilience-hardening
- [ ] Create .env.staging file with all configurations
- [ ] Build Dashboard docker image:
  ```bash
  docker build -f inventario-retail/Dockerfile.dashboard -t ghcr.io/eevans-d/aidrive_genspark:staging .
  ```
- [ ] Start docker-compose stack:
  ```bash
  docker-compose -f docker-compose.staging.yml up -d
  ```
- [ ] Wait for all services to be healthy (verify with healthchecks)

### 9.2 Initialization Steps
- [ ] Initialize S3 bucket (if init script not auto-run)
- [ ] Initialize PostgreSQL database (if init scripts not auto-run)
- [ ] Verify Redis is empty and ready
- [ ] Initialize Prometheus scrape targets
- [ ] Initialize Grafana datasources and dashboards

### 9.3 Verification Steps
- [ ] All containers running: `docker-compose ps`
- [ ] All services healthy: check health endpoints
- [ ] Dashboard accessible: `curl http://localhost:8080/health -H "X-API-Key: ..."`
- [ ] Metrics endpoint accessible: `curl http://localhost:8080/metrics -H "X-API-Key: ..."`
- [ ] Prometheus scraping metrics: check Prometheus UI (localhost:9091)
- [ ] Grafana accessible: http://localhost:3001

---

## 10. SMOKE TESTING

### 10.1 Manual Smoke Tests
- [ ] Test database connectivity from Dashboard
- [ ] Test Redis connectivity from Dashboard
- [ ] Test S3/LocalStack connectivity from Dashboard
- [ ] Test OpenAI CB (configuration only, no real API calls)
- [ ] Verify health endpoint returns all 4 services
- [ ] Verify degradation level is OPTIMAL when all healthy

### 10.2 Automated Smoke Tests ✅
- [x] smoke_test_staging.py created (35+ test cases)
- [ ] Run smoke tests:
  ```bash
  pytest tests/staging/smoke_test_staging.py -v
  ```
- [ ] All 35+ tests should pass:
  - Connectivity tests (4 tests)
  - Health check tests (4 tests)
  - Circuit breaker tests (4 tests)
  - Degradation level tests (5 tests)
  - Feature availability tests (4 tests)
  - Metrics tests (4 tests)
  - Performance tests (2 tests)
  - Security tests (3 tests)
  - Rate limiting tests (2 tests)
  - Logging tests (2 tests)
  - End-to-end tests (3 tests)
  - Deployment checklist tests (3 tests)

### 10.3 Performance Testing
- [ ] Health check latency < 100ms
- [ ] API response time < 500ms
- [ ] Database queries < 200ms (when healthy)
- [ ] Redis operations < 5ms (when healthy)
- [ ] S3 operations < 5s (when healthy)
- [ ] Concurrent load test (10+ concurrent requests)

### 10.4 Failure Mode Testing
- [ ] Simulate database failure:
  - [ ] Stop PostgreSQL container
  - [ ] Verify degradation level changes to DEGRADED/LIMITED
  - [ ] Verify read-only mode activated
  - [ ] Verify RC retries with exponential backoff
- [ ] Simulate Redis failure:
  - [ ] Stop Redis container
  - [ ] Verify degradation level changes
  - [ ] Verify cache bypass active
  - [ ] Verify features requiring cache are disabled
- [ ] Simulate S3 failure:
  - [ ] Stop LocalStack container
  - [ ] Verify degradation level changes
  - [ ] Verify file operations disabled
  - [ ] Verify system still functional
- [ ] Simulate OpenAI CB OPEN:
  - [ ] Manually trigger CB OPEN state
  - [ ] Verify AI features disabled
  - [ ] Verify system still functional

---

## 11. MONITORING & ALERTING

### 11.1 Dashboard Creation
- [ ] Health Status Dashboard
  - [ ] Current health score (0-100)
  - [ ] Current degradation level
  - [ ] Service status (4 services)
  - [ ] Feature availability
- [ ] Circuit Breaker Dashboard
  - [ ] CB state for each service (CLOSED, OPEN, HALF_OPEN)
  - [ ] Failure counts
  - [ ] Last failure timestamp
  - [ ] Time to recovery
- [ ] Performance Dashboard
  - [ ] Request rate
  - [ ] Error rate
  - [ ] Latency (p50, p95, p99)
  - [ ] Resource usage

### 11.2 Alert Rules
- [ ] Database CB OPEN (critical)
- [ ] OpenAI CB OPEN (warning)
- [ ] Redis CB OPEN (warning)
- [ ] S3 CB OPEN (info)
- [ ] Degradation level < OPTIMAL (warning)
- [ ] Degradation level < DEGRADED (critical)
- [ ] Error rate > 5% (warning)
- [ ] Latency p95 > 500ms (warning)

---

## 12. DOCUMENTATION & RUNBOOKS

### 12.1 Create Documentation
- [ ] STAGING_DEPLOYMENT_GUIDE.md
  - [ ] Prerequisites
  - [ ] Step-by-step deployment
  - [ ] Verification procedures
  - [ ] Troubleshooting guide
- [ ] STAGING_RUNBOOK.md
  - [ ] Common operations (start, stop, restart services)
  - [ ] Failure scenarios and responses
  - [ ] Monitoring and alerting
  - [ ] Scaling procedures
- [ ] STAGING_TROUBLESHOOTING.md
  - [ ] Dashboard not starting
  - [ ] Database connection issues
  - [ ] Redis connectivity problems
  - [ ] S3/LocalStack issues
  - [ ] Metrics not appearing
  - [ ] High latency issues

### 12.2 Team Training
- [ ] Training document for operations team
- [ ] Dashboard navigation guide
- [ ] Alert response procedures
- [ ] Escalation procedures

---

## 13. GO-LIVE PREPARATION (DÍA 5)

### 13.1 Production Deployment Plan
- [ ] Prepare production docker-compose.yml
- [ ] Set up production environment variables
- [ ] Configure real AWS S3 bucket (not LocalStack)
- [ ] Configure real database with backups
- [ ] Configure real monitoring/alerting
- [ ] Prepare rollback procedures

### 13.2 Production Readiness Checklist
- [ ] All staging tests passing
- [ ] Performance benchmarks met
- [ ] Security audit passed
- [ ] Documentation complete
- [ ] Team trained
- [ ] Rollback procedures documented
- [ ] Monitoring/alerting operational

### 13.3 Rollback Plan
- [ ] Document previous version/commit
- [ ] Database rollback procedures
- [ ] Data recovery procedures
- [ ] Service restart procedures

---

## 14. SIGN-OFF & APPROVAL

### 14.1 Testing Sign-Off
- [ ] All smoke tests passing: ___________  Date: _______
- [ ] Performance tests passing: ___________  Date: _______
- [ ] Security audit completed: ___________  Date: _______

### 14.2 Deployment Authorization
- [ ] Tech Lead approval: ___________  Date: _______
- [ ] Operations approval: ___________  Date: _______
- [ ] Product Owner approval: ___________  Date: _______

### 14.3 Post-Deployment Validation
- [ ] Staging deployment successful: ___________  Date: _______
- [ ] All services healthy: ___________  Date: _______
- [ ] Monitoring/alerting operational: ___________  Date: _______
- [ ] Team ready for go-live: ___________  Date: _______

---

## 15. METRICS & SUCCESS CRITERIA

### 15.1 Deployment Success Metrics
- [x] Code quality: 100% (all tests passing)
- [ ] Staging deployment: 100% successful
- [ ] Smoke tests: 100% passing (35/35)
- [ ] Performance: All benchmarks met
- [ ] Uptime: 99.9%+ (target for production)
- [ ] Error rate: < 0.1%
- [ ] Latency p95: < 500ms

### 15.2 Monitoring Coverage
- [ ] 4 Circuit Breakers: 100% monitored
- [ ] 6 Services: 100% monitored (DB, Redis, S3, API, Prometheus, Grafana)
- [ ] 16 Features: 100% tracked in feature_availability metric
- [ ] 5 Degradation Levels: 100% trackable

### 15.3 Feature Availability Matrix
| Feature | OPTIMAL | DEGRADED | LIMITED | MINIMAL | EMERGENCY |
|---------|---------|----------|---------|---------|-----------|
| Inventory Management | ✅ | ✅ | ✅ | ✅ | ❌ |
| AI Recommendations | ✅ | ✅ | ❌ | ❌ | ❌ |
| Real-time Updates | ✅ | ✅ | ❌ | ❌ | ❌ |
| Redis Cache | ✅ | ✅ | ❌ | ❌ | ❌ |
| Session Storage | ✅ | ✅ | ✅ | ❌ | ❌ |
| Rate Limiting | ✅ | ✅ | ❌ | ❌ | ❌ |
| S3 Uploads | ✅ | ❌ | ❌ | ❌ | ❌ |
| File Storage | ✅ | ✅ | ❌ | ❌ | ❌ |
| Image Processing | ✅ | ❌ | ❌ | ❌ | ❌ |
| Backup Operations | ✅ | ❌ | ❌ | ❌ | ❌ |
| Full AI Pipeline | ✅ | ✅ | ❌ | ❌ | ❌ |
| Advanced Analytics | ✅ | ✅ | ❌ | ❌ | ❌ |
| Real-time Inventory | ✅ | ✅ | ❌ | ❌ | ❌ |
| Basic Analytics | ✅ | ✅ | ✅ | ❌ | ❌ |
| Read-only Access | ✅ | ✅ | ✅ | ✅ | ✅ |
| Minimal Access | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## APPENDIX A: ENVIRONMENT VARIABLES

### Database Configuration
```
STAGING_DB_USER=inventario_user
STAGING_DB_PASSWORD=staging_secure_pass_2025
STAGING_DB_NAME=inventario_retail_staging
STAGING_DB_PORT=5433
```

### Redis Configuration
```
STAGING_REDIS_HOST=redis
STAGING_REDIS_PORT=6379
STAGING_REDIS_DB=0
```

### S3/LocalStack Configuration
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_ENDPOINT_URL=http://localstack:4566
S3_BUCKET_NAME=inventario-retail-bucket-staging
```

### Circuit Breaker Configuration
```
OPENAI_CB_FAILURE_THRESHOLD=5
OPENAI_CB_RECOVERY_TIMEOUT=30
OPENAI_CB_HALF_OPEN_REQUESTS=2

DB_CB_FAILURE_THRESHOLD=3
DB_CB_RECOVERY_TIMEOUT=20
DB_CB_HALF_OPEN_REQUESTS=1

REDIS_CB_FAILURE_THRESHOLD=5
REDIS_CB_RECOVERY_TIMEOUT=15
REDIS_CB_HALF_OPEN_REQUESTS=2

S3_CB_FAILURE_THRESHOLD=4
S3_CB_RECOVERY_TIMEOUT=25
S3_CB_HALF_OPEN_REQUESTS=2
```

### Degradation Manager Configuration
```
HEALTH_CHECK_INTERVAL=10
DEGRADATION_RECOVERY_PREDICTION=true
SERVICE_WEIGHTS=database:0.50,openai:0.30,redis:0.15,s3:0.05
OPTIMAL_THRESHOLD=90
DEGRADED_THRESHOLD=70
LIMITED_THRESHOLD=60
MINIMAL_THRESHOLD=40
```

---

## APPENDIX B: USEFUL COMMANDS

### Docker Compose Operations
```bash
# Start all services
docker-compose -f docker-compose.staging.yml up -d

# Stop all services
docker-compose -f docker-compose.staging.yml down

# View logs
docker-compose -f docker-compose.staging.yml logs -f dashboard

# Restart specific service
docker-compose -f docker-compose.staging.yml restart redis

# View service status
docker-compose -f docker-compose.staging.yml ps
```

### Testing
```bash
# Run all smoke tests
pytest tests/staging/smoke_test_staging.py -v

# Run specific test class
pytest tests/staging/smoke_test_staging.py::TestStagingConnectivity -v

# Run with coverage
pytest tests/staging/smoke_test_staging.py --cov=inventario-retail/web_dashboard
```

### Health Checks
```bash
# Check health endpoint
curl -H "X-API-Key: staging-api-key-2025" http://localhost:8080/health

# Check metrics endpoint
curl -H "X-API-Key: staging-api-key-2025" http://localhost:8080/metrics

# Check Prometheus
curl http://localhost:9091/graph

# Check Grafana
open http://localhost:3001
```

---

**Document Version**: 1.0  
**Last Updated**: October 19, 2025 - 14:00 UTC  
**Status**: DÍA 4-5 HORAS 1-2 IN PROGRESS ✅
