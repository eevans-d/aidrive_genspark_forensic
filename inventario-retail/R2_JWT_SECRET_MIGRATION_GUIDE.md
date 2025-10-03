# R2 JWT Secret Isolation - Migration Guide

## Overview

**Risk**: All agents sharing a single JWT secret (`JWT_SECRET_KEY`) creates a security vulnerability. If one agent is compromised, all agents become vulnerable.

**Mitigation (R2)**: Implement per-agent JWT secrets with backward compatibility.

## Architecture Changes

### Before (Single Secret)
```
JWT_SECRET_KEY → [deposito, negocio, ml, dashboard]
```

### After (Isolated Secrets, Backward Compatible)
```
JWT_SECRET_DEPOSITO  → [deposito]
JWT_SECRET_NEGOCIO   → [negocio]
JWT_SECRET_ML        → [ml]
JWT_SECRET_DASHBOARD → [dashboard]
                    ↓ (fallback if not set)
                JWT_SECRET_KEY (legacy)
```

## Implementation

### 1. Code Changes

**`shared/auth.py`**:
- Added `JWT_SECRET_DEPOSITO`, `JWT_SECRET_NEGOCIO`, `JWT_SECRET_ML`, `JWT_SECRET_DASHBOARD` with fallback to `JWT_SECRET_KEY`
- Modified `AuthManager.__init__()` to accept optional `secret_key` and `issuer` parameters
- Added `issuer` claim to JWT tokens for origin validation
- Created agent-specific instances: `auth_manager_deposito`, `auth_manager_negocio`, etc.
- Added `get_auth_manager_for_agent(agent_name)` helper function

**`docker-compose.production.yml`**:
- Updated all agent services to use agent-specific secrets with fallback:
  ```yaml
  - JWT_SECRET_KEY=${JWT_SECRET_DEPOSITO:-${JWT_SECRET_KEY}}
  - JWT_SECRET_DEPOSITO=${JWT_SECRET_DEPOSITO:-${JWT_SECRET_KEY}}
  ```

**`.env.production.template`**:
- Added new environment variables with generation instructions

### 2. Deployment Strategy (Zero-Downtime)

#### Option A: Gradual Migration (RECOMMENDED)

1. **Phase 1**: Deploy code changes with fallback behavior
   ```bash
   # .env.production - keep existing JWT_SECRET_KEY
   JWT_SECRET_KEY=your-existing-secret
   # New variables not set yet → will use JWT_SECRET_KEY as fallback
   ```
   - **Impact**: None, backward compatible
   - **Validation**: All agents continue working with shared secret

2. **Phase 2**: Enable per-agent secrets one by one
   ```bash
   # .env.production - start with one agent
   JWT_SECRET_KEY=your-existing-secret
   JWT_SECRET_DEPOSITO=new-secure-deposito-secret
   ```
   - **Impact**: Only deposito uses new secret, others still use global
   - **Validation**: Test deposito endpoints, verify JWT issuer claim

3. **Phase 3**: Complete migration
   ```bash
   # .env.production - all agents with unique secrets
   JWT_SECRET_KEY=your-existing-secret  # Keep for emergency fallback
   JWT_SECRET_DEPOSITO=new-secure-deposito-secret
   JWT_SECRET_NEGOCIO=new-secure-negocio-secret
   JWT_SECRET_ML=new-secure-ml-secret
   JWT_SECRET_DASHBOARD=new-secure-dashboard-secret
   ```
   - **Impact**: Full isolation achieved
   - **Validation**: Test inter-agent communication, verify all endpoints

#### Option B: Full Cutover (Higher Risk)

1. Generate all secrets at once
2. Deploy with all new secrets simultaneously
3. Validate entire system

**⚠️ Risk**: If any secret is misconfigured, multiple agents may fail.

### 3. Secret Generation

Use strong random secrets (256 bits):
```bash
# Generate secrets for all agents
openssl rand -base64 32  # JWT_SECRET_DEPOSITO
openssl rand -base64 32  # JWT_SECRET_NEGOCIO
openssl rand -base64 32  # JWT_SECRET_ML
openssl rand -base64 32  # JWT_SECRET_DASHBOARD
```

### 4. Usage in Agent Code

#### Existing code (still works, uses global secret):
```python
from shared.auth import auth_manager

token = auth_manager.create_access_token({"user": "admin", "role": "deposito"})
```

#### New pattern (recommended, uses agent-specific secret):
```python
from shared.auth import get_auth_manager_for_agent

auth = get_auth_manager_for_agent("deposito")
token = auth.create_access_token({"user": "admin", "role": "deposito"})
# Token now includes "iss": "deposito" claim
```

## Validation

### Check Active Configuration
```bash
# Inside any container
echo $JWT_SECRET_KEY
echo $JWT_SECRET_DEPOSITO  # Should be different if configured
```

### Verify JWT Tokens
```python
import jwt
from shared.auth import JWT_SECRET_DEPOSITO, JWT_ALGORITHM

# Decode a token from deposito agent
payload = jwt.decode(token, JWT_SECRET_DEPOSITO, algorithms=[JWT_ALGORITHM])
print(payload.get("iss"))  # Should print "deposito"
```

### Test Isolation
1. Create token with `auth_manager_deposito`
2. Try to verify with `auth_manager_negocio` (should fail if secrets differ)
3. Expected: `jwt.InvalidSignatureError`

## Rollback Plan

If issues arise, rollback is simple:

1. **Remove agent-specific secrets from `.env.production`**:
   ```bash
   # Comment out or remove
   # JWT_SECRET_DEPOSITO=...
   # JWT_SECRET_NEGOCIO=...
   # etc.
   ```

2. **Keep only global secret**:
   ```bash
   JWT_SECRET_KEY=your-existing-secret
   ```

3. **Restart services**:
   ```bash
   docker compose -f docker-compose.production.yml restart
   ```

4. **Validate**: All agents now use `JWT_SECRET_KEY` (fallback behavior)

## Benefits

- **Security**: Compromise of one agent doesn't affect others
- **Auditability**: JWT `iss` claim identifies token origin
- **Flexibility**: Can rotate secrets per agent independently
- **Zero downtime**: Backward compatible fallback mechanism
- **Compliance**: Aligns with least-privilege principle

## ROI Calculation

- **Severity**: 8/10 (critical security risk)
- **Impact**: 9/10 (all agents vulnerable if one compromised)
- **Effort**: 8h implementation + 2h validation
- **ROI**: 1.6 (meets threshold)

## Next Steps

1. Review this guide with security team
2. Choose deployment strategy (gradual recommended)
3. Schedule maintenance window (optional, not required for gradual)
4. Generate secrets using `openssl rand -base64 32`
5. Update `.env.production` following chosen strategy
6. Deploy and validate
7. Monitor for 24-48h
8. Complete migration for all agents

## Related Documentation

- `CHANGELOG.md`: Version history with R2 mitigation
- `.env.production.template`: Environment variable reference
- `shared/auth.py`: Implementation details
- `docker-compose.production.yml`: Container configuration
