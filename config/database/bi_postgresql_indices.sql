-- PostgreSQL Optimization Indices for business-intelligence-orchestrator-v3.1
-- Índices concurrentes para no bloquear operaciones durante creación

-- Índices para industry taxonomies (BI core)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_industry_taxonomies_code 
ON industry_taxonomies (industry_code) WHERE active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_industry_taxonomies_name
ON industry_taxonomies USING gin(to_tsvector('spanish', name)) WHERE active = true;

-- Índices para legal compliance (sistema crítico)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_legal_compliance_date
ON legal_compliance (created_at DESC, compliance_status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_legal_compliance_entity
ON legal_compliance (entity_id, compliance_type) WHERE active = true;

-- Índices para web automático competitive monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_competitive_data_company
ON competitive_monitoring (company_id, monitored_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_competitive_data_alerts
ON competitive_monitoring (alert_triggered, created_at DESC) WHERE alert_triggered = true;

-- Índices para logs y auditoría (consultas de gran volumen)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_timestamp
ON audit_logs (created_at DESC) WHERE log_level IN ('ERROR', 'CRITICAL');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_entity
ON audit_logs (entity_type, entity_id, created_at DESC);

-- Índice parcial para datos activos más consultados
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_active
ON companies (id, name) WHERE active = true AND monitored = true;

-- Optimización para agregaciones comunes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_daily_aggregation
ON business_metrics (date_trunc('day', created_at), metric_type, value);

-- Estadísticas automáticas para el optimizador
ANALYZE industry_taxonomies;
ANALYZE legal_compliance; 
ANALYZE competitive_monitoring;
ANALYZE audit_logs;