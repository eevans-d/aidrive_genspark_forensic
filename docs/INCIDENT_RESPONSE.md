# INCIDENT_RESPONSE_PLAYBOOK.md

# Incident Response Playbook

**Version**: 1.0  
**Last Updated**: October 19, 2025  
**Status**: Ready for Production

---

## Table of Contents

1. [Incident Severity Levels](#incident-severity-levels)
2. [Incident Response Team](#incident-response-team)
3. [Initial Response Procedures](#initial-response-procedures)
4. [Service-Specific Runbooks](#service-specific-runbooks)
5. [Recovery Procedures](#recovery-procedures)
6. [Communication Protocols](#communication-protocols)
7. [Post-Incident Review](#post-incident-review)

---

## Incident Severity Levels

### Level 1: CRITICAL
**Impact**: Complete service outage or data loss  
**Response Time**: Immediate (< 2 min)  
**Communication**: Every 10 minutes

- All users affected
- Core functionality unavailable
- Data integrity compromised
- Revenue-impacting

**Escalation**: CEO, CTO, VP Engineering  
**Action**: Activate full incident response team

### Level 2: HIGH
**Impact**: Significant degradation or partial outage  
**Response Time**: < 5 minutes  
**Communication**: Every 15 minutes

- Multiple services affected
- Non-core functionality down
- Performance severely degraded
- SLA impact imminent

**Escalation**: VP Engineering, Product Manager  
**Action**: Technical lead + on-call engineer

### Level 3: MEDIUM
**Impact**: Minor degradation or single service issue  
**Response Time**: < 15 minutes  
**Communication**: Hourly

- Single service affected
- Workarounds available
- Limited user impact
- Performance slightly degraded

**Escalation**: Engineering Lead  
**Action**: On-call engineer investigation

### Level 4: LOW
**Impact**: No user impact, monitoring alert only  
**Response Time**: < 1 hour  
**Communication**: Daily

- Monitoring threshold exceeded
- No actual impact observed
- Informational alert
- Can be investigated later

**Action**: Log ticket for investigation

---

## Incident Response Team

### Roles & Responsibilities

#### Incident Commander (IC)
- Makes decisions during incident
- Coordinates team efforts
- Communicates status to stakeholders
- Decides on escalation
- **Decision Authority**: Can declare rollback
- **Primary Contact**: VP Engineering

#### Technical Lead
- Investigates root cause
- Determines impact scope
- Recommends solutions
- Implements fixes
- **Primary Skills**: Architecture, debugging
- **Escalation Path**: VP Engineering

#### Database Administrator
- Monitors database health
- Executes recovery procedures
- Validates data integrity
- Manages backups/restores
- **Contact**: ops-dba@company.com
- **24/7 Available**: Yes

#### DevOps Engineer
- Manages infrastructure
- Deploys fixes
- Manages rollbacks
- Infrastructure scaling
- **Contact**: ops-devops@company.com
- **24/7 Available**: Yes

#### Product Manager
- Communicates with customers
- Provides business context
- Prioritizes fixes
- Manages customer communications
- **Contact**: product-lead@company.com
- **On-Call**: Critical incidents only

#### Communications Lead
- Updates status page
- Sends customer notifications
- Manages media inquiries
- Documents incident timeline
- **Contact**: communications@company.com

### On-Call Schedule

```
Monday - Friday:
  9am - 5pm: Engineering Team
  5pm - 9am: On-Call Rotation

Weekends & Holidays:
  24/7: On-Call Rotation

Escalation Chain:
  1. On-Call Engineer
  2. Engineering Lead
  3. VP Engineering
  4. CTO
```

---

## Initial Response Procedures

### Incident Detection & Triage

#### Step 1: Detect Incident
- **Automated**: Monitoring alerts via Prometheus/Grafana
- **Manual**: Customer reports via support
- **Health Check**: Manual verification via dashboard

#### Step 2: Classify Severity
- Determine affected service(s)
- Estimate user impact
- Assess business impact
- Assign severity level (1-4)

#### Step 3: Activate Response
```bash
# For Level 1-2 Incidents:
1. Open incident in status page
2. Activate incident war room (Zoom/Slack)
3. Notify on-call engineer
4. Notify incident commander
5. Post initial message: "Investigating <service> incident"

# For Level 3-4 Incidents:
1. Create ticket in JIRA
2. Assign to on-call engineer
3. Update status in 1 hour
```

#### Step 4: Information Gathering
```
Collect immediately:
- Error messages and logs
- Service health status
- Recent deployments (last 24h)
- Resource utilization (CPU, memory, disk)
- Traffic patterns (normal vs. current)
- Database query performance
- Network connectivity status
```

### War Room Setup (Level 1-2 Only)

```
Participants:
- Incident Commander
- Technical Lead
- Database Administrator
- DevOps Engineer
- Communications Lead

Tools:
- Zoom for video conference
- Slack #incident-response channel
- Shared Google Doc for timeline
- SSH access to servers
- Monitoring dashboards visible

Cadence:
- Initial: Every 5 minutes
- Updates: Every 15 minutes
- Final: When incident resolved
```

---

## Service-Specific Runbooks

### Dashboard Service Outage

#### Symptoms
- /health endpoint returning 5xx errors
- /metrics endpoint unavailable
- API requests timing out
- Dashboard UI not loading

#### Diagnosis
```bash
# Check service status
docker-compose -f docker-compose.staging.yml ps dashboard

# Check logs
docker-compose -f docker-compose.staging.yml logs dashboard | tail -100

# Check connectivity
curl -v http://localhost:9000/health

# Check resource usage
docker stats dashboard

# Check port binding
netstat -tlnp | grep 9000
```

#### Recovery Steps
```bash
# Step 1: Restart service
docker-compose -f docker-compose.staging.yml restart dashboard

# Wait 30 seconds for startup
sleep 30

# Step 2: Verify recovery
curl http://localhost:9000/health

# Step 3: Monitor for errors
docker-compose -f docker-compose.staging.yml logs -f dashboard

# Step 4: If still failing - rollback
git log --oneline -n 5
git revert <commit-hash>
docker-compose -f docker-compose.staging.yml build dashboard
docker-compose -f docker-compose.staging.yml up -d dashboard
```

**RTO**: 5 minutes (restart) / 10 minutes (rollback)

---

### Database Service Outage

#### Symptoms
- Database connection errors
- Inventory queries failing
- 500 errors from API
- "Cannot connect to database" errors

#### Diagnosis
```bash
# Check database container
docker-compose -f docker-compose.staging.yml ps postgres

# Check logs
docker-compose -f docker-compose.staging.yml logs postgres | tail -100

# Check connectivity
docker exec aidrive-postgres-staging psql -U inventory -d retail -c "SELECT 1"

# Check disk space
docker exec aidrive-postgres-staging df -h /var/lib/postgresql/data

# Check running queries
docker exec aidrive-postgres-staging psql -U inventory -d retail -c \
  "SELECT pid, now() - query_start as duration, query FROM pg_stat_activity \
   WHERE query != '<idle>' ORDER BY query_start;"
```

#### Recovery Steps
```bash
# Step 1: Check locks
docker exec aidrive-postgres-staging psql -U inventory -d retail -c \
  "SELECT * FROM pg_locks WHERE NOT granted;"

# Step 2: Kill long-running queries (if needed)
docker exec aidrive-postgres-staging psql -U inventory -d retail -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity \
   WHERE query_start < now() - interval '10 minutes';"

# Step 3: Restart service
docker-compose -f docker-compose.staging.yml restart postgres

# Step 4: Verify recovery
docker-compose -f docker-compose.staging.yml logs postgres | tail -20

# Step 5: Run integrity check
docker exec aidrive-postgres-staging pg_dump -U inventory retail | \
  docker exec -i aidrive-postgres-staging psql -U inventory -d retail -c "SELECT 1"
```

**RTO**: 2 minutes (restart) / 15 minutes (full recovery)  
**Note**: Contact DBA if corruption detected

---

### Redis Cache Outage

#### Symptoms
- Cache misses increasing
- API latency spiking
- Redis connection errors
- Memory errors in logs

#### Diagnosis
```bash
# Check redis status
docker-compose -f docker-compose.staging.yml ps redis

# Connect to Redis
docker exec aidrive-redis-staging redis-cli -p 6379

# Check memory usage
redis-cli INFO memory | grep -E "used_memory|maxmemory"

# Check number of keys
redis-cli DBSIZE

# Check slow log
redis-cli SLOWLOG GET 10
```

#### Recovery Steps
```bash
# Step 1: Clear cache (if corrupted)
redis-cli FLUSHDB

# Step 2: Restart service
docker-compose -f docker-compose.staging.yml restart redis

# Step 3: Verify operation
docker-compose -f docker-compose.staging.yml logs redis

# Step 4: Check memory
docker exec aidrive-redis-staging redis-cli INFO memory

# Step 5: Monitor performance
docker stats redis
```

**RTO**: 2 minutes (restart) / 5 minutes (full recovery)

---

### High Error Rate (>5%)

#### Diagnosis
```bash
# Check error logs
curl -H "X-API-Key: $API_KEY" http://localhost:9000/metrics | grep errors

# Check recent deployments
git log --oneline -n 10

# Check resources
docker stats

# Check database queries
docker exec aidrive-postgres-staging psql -U inventory -d retail -c \
  "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10"

# Check circuit breaker status
curl -H "X-API-Key: $API_KEY" http://localhost:9000/api/circuit-breaker/status
```

#### Recovery Steps
```bash
# Step 1: Identify error source
docker-compose -f docker-compose.staging.yml logs --tail 500 | grep ERROR

# Step 2: Scale resources (if needed)
docker-compose -f docker-compose.staging.yml up -d --scale dashboard=2

# Step 3: Database optimization (if slow queries)
docker exec aidrive-postgres-staging psql -U inventory -d retail -c \
  "REINDEX DATABASE retail;"

# Step 4: Clear cache (if cache issues)
docker exec aidrive-redis-staging redis-cli FLUSHDB

# Step 5: Rollback (if deployment issue)
git revert <problematic-commit>
docker-compose -f docker-compose.staging.yml build
docker-compose -f docker-compose.staging.yml up -d
```

**RTO**: 5-15 minutes depending on root cause

---

### High Latency (p99 > 2000ms)

#### Diagnosis
```bash
# Check metrics
curl -H "X-API-Key: $API_KEY" http://localhost:9000/metrics | grep latency

# Check resource usage
docker stats

# Check slow queries
docker exec aidrive-postgres-staging psql -U inventory -d retail \
  -c "SELECT query, calls, total_time/calls as avg_time FROM pg_stat_statements \
      ORDER BY total_time DESC LIMIT 10"

# Check network
netstat -s | grep -E "dropped|retransmit"
```

#### Recovery Steps
```bash
# Step 1: Identify bottleneck (DB vs API vs Cache)
# Check if latency is on specific endpoint:
curl -w "@curl-format.txt" -o /dev/null -s \
  -H "X-API-Key: $API_KEY" http://localhost:9000/api/inventory/stats

# Step 2: If database slow
# Create indexes:
docker exec aidrive-postgres-staging psql -U inventory -d retail -c \
  "CREATE INDEX idx_inventory_sku ON inventory(sku); ANALYZE inventory;"

# Step 3: If API slow
# Restart with more resources
docker-compose -f docker-compose.staging.yml stop dashboard
docker update --memory 4g aidrive-dashboard-staging
docker-compose -f docker-compose.staging.yml up -d dashboard

# Step 4: If cache hit rate low
# Review cache strategy
redis-cli INFO stats | grep hits
```

**RTO**: 5-20 minutes

---

## Recovery Procedures

### Database Restore from Backup

```bash
# Step 1: Identify backup
ls -lh /backups/postgresql/

# Step 2: Stop current database
docker-compose -f docker-compose.staging.yml stop postgres

# Step 3: Restore backup
docker exec -i aidrive-postgres-staging psql -U inventory < /backups/postgresql/latest.sql

# Step 4: Restart and verify
docker-compose -f docker-compose.staging.yml up -d postgres
sleep 30
docker exec aidrive-postgres-staging psql -U inventory -d retail -c "SELECT COUNT(*) FROM inventory"

# Step 5: Run integrity checks
docker exec aidrive-postgres-staging pg_dump -U inventory retail | psql -U inventory -d retail
```

**RTO**: 10-20 minutes  
**Data Loss**: Up to 15 minutes

### Complete Service Restart

```bash
# Step 1: Stop all services
docker-compose -f docker-compose.staging.yml stop

# Step 2: Clear caches
docker volume prune -f

# Step 3: Restart all services
docker-compose -f docker-compose.staging.yml up -d

# Step 4: Verify all services
docker-compose -f docker-compose.staging.yml ps

# Step 5: Run health checks
curl http://localhost:9000/health
curl http://localhost:9090/-/healthy
curl http://localhost:3003/api/health
```

**RTO**: 5 minutes  
**Impact**: Complete service interruption for 2-3 minutes

---

## Communication Protocols

### Initial Notification (Level 1-2)

**Within 2 minutes of detection**:

```
Subject: INCIDENT: <Service> Outage

Team,

An incident has been detected at <timestamp>.

Service: <Service Name>
Severity: Level <1-2>
Status: INVESTIGATING
Initial Impact: <Description>

Incident Commander: <Name>
Technical Lead: <Name>

Status: https://status.company.com
Updates: Every 15 minutes

Action Required: <If any>
```

### Status Updates

**Every 15 minutes** (Level 1-2) or **hourly** (Level 3):

```
INCIDENT UPDATE #<N>

Status: INVESTIGATING / IN PROGRESS / RESOLVED
Duration: <Time since incident start>
Affected: <Services/Users>

Actions Taken:
- <Action 1>
- <Action 2>

ETA: <Estimated resolution time or "TBD">

Next Update: <Time>
```

### Resolution Notification

```
INCIDENT RESOLVED

Service: <Service Name>
Duration: <Duration>
Root Cause: <Brief description>
Impact: <Affected users, data>

Resolution:
- <Action 1>
- <Action 2>

Post-Incident Review scheduled for: <Date/Time>
```

---

## Post-Incident Review

### Schedule
- **Level 1**: Within 24 hours
- **Level 2**: Within 48 hours
- **Level 3-4**: Optional

### Meeting Agenda
1. **Timeline Review** (5 min)
   - When was incident detected
   - When was response initiated
   - When was issue resolved

2. **Root Cause Analysis** (10 min)
   - What was the root cause
   - Why was it not caught earlier
   - What monitoring was missed

3. **Impact Assessment** (5 min)
   - How many users affected
   - How much data was impacted
   - What SLAs were breached

4. **Remediation Items** (15 min)
   - What can we do to prevent this
   - What alerts should we add
   - What processes need updating

5. **Action Items** (5 min)
   - Assign owner for each action
   - Set target completion date
   - Schedule follow-up

### Action Items Template
```
Action Item: <Description>
Owner: <Name>
Target Date: <Date>
Priority: <Critical/High/Medium/Low>
Status: Open
```

### Documentation
- Post-incident document added to wiki
- Runbook updated with lessons learned
- Monitoring alerts updated
- Team trained on new procedures

---

## Emergency Contacts

```
Incident Commander: <Phone> <Slack>
On-Call Engineer: <Phone> <Slack>
VP Engineering: <Phone> <Email>
CTO: <Phone> <Email>
Communications: <Email> <Slack>

Status Page: https://status.company.com
Incident Channel: #incident-response
```

---

**Document Version**: 1.0  
**Last Review**: October 19, 2025  
**Next Review**: Q1 2026  
**Status**: ✅ Ready for Production
