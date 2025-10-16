# 🏛️ GDPR Compliance & Data Protection - Mini Market Dashboard

**Versión:** 1.0.0  
**Status:** Implementation Guide  
**Objetivo:** Cumplimiento total con GDPR (UE Regulation 2016/679)  
**Aplicable:** Argentina (puede aplicarse PDPA local)  

---

## 📋 Tabla de Contenidos

1. [GDPR Overview](#gdpr-overview)
2. [Data Inventory](#data-inventory)
3. [Legal Basis](#legal-basis)
4. [Data Subject Rights](#data-subject-rights)
5. [Privacy by Design](#privacy-by-design)
6. [Data Protection Impact](#data-protection-impact)
7. [Incident Response](#incident-response)
8. [Documentation & Audit](#documentation--audit)

---

## 🌍 GDPR Overview

### Scope
```
✅ Applicable to:
  • Systems processing personal data of EU residents
  • Mini Market Dashboard stores user data
  • API keys tied to individuals (users)
  • Transaction logs with email/phone

✅ Key Principles:
  • Lawfulness, fairness & transparency
  • Purpose limitation
  • Data minimization
  • Accuracy & integrity
  • Storage limitation
  • Integrity & confidentiality
  • Accountability
```

### Critical Timelines
```
GDPR Right Response Times:
• Erasure Request: 30 days
• Access Request: 45 days
• Rectification Request: 30 days
• Portability Request: 30 days (or reject)
• Breach Notification: 72 hours to authority
```

---

## 📊 Data Inventory

### Personal Data Collected

#### Category 1: User Account Data
```json
{
  "table": "users",
  "fields": {
    "user_id": "unique identifier",
    "email": "contact information (PERSONAL)",
    "phone": "contact information (PERSONAL)",
    "password_hash": "security (not personal per se)",
    "created_at": "timestamp",
    "last_login": "timestamp",
    "role": "job function (PERSONAL)"
  },
  "retention": "For duration of account + 3 months after deletion",
  "legal_basis": "Contractual necessity",
  "third_parties": "None shared externally"
}
```

#### Category 2: Activity Logs
```json
{
  "table": "audit_log",
  "fields": {
    "user_id": "identifies individual (PERSONAL)",
    "event_timestamp": "timestamp",
    "action": "what they did",
    "ip_address": "may identify individual (PERSONAL)",
    "user_agent": "browser info"
  },
  "retention": "90 days for operational logs, 1 year for legal holds",
  "legal_basis": "Legitimate interest (security, fraud prevention)",
  "third_parties": "Security team only"
}
```

#### Category 3: Sensitive Data (if applicable)
```json
{
  "table": "encrypted_data_access_log",
  "fields": {
    "user_id": "identifies individual",
    "decrypted_column": "what sensitive field accessed",
    "access_timestamp": "when",
    "reason": "why (GDPR Article 9)"
  },
  "retention": "1 year minimum",
  "legal_basis": "Explicit consent OR special circumstances",
  "third_parties": "None"
}
```

### Data Flow Diagram
```
┌─────────────────┐
│  User Creates   │
│   Account       │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  GDPR: Consent collection           │
│  • Privacy notice shown             │
│  • Explicit opt-in required         │
│  • Terms accepted                   │
└────────┬────────────────────────────┘
         │
         ↓
┌──────────────────────────────────┐
│  Data Stored Securely            │
│  • Encrypted at rest             │
│  • Access logged                 │
│  • Retention policy applied      │
└────────┬─────────────────────────┘
         │
         ├──→ Processed by Mini Market System
         │
         ├──→ Retained per policy
         │
         └──→ Deleted on request (Right to Erasure)
```

---

## ⚖️ Legal Basis

### GDPR Article 6 - Lawfulness
```
Para procesar datos personales, necesitas UNA de estas bases:

[✅] 6.1(a) Consent
     Cuando: Datos no necesarios para servicio
     Ejemplo: Marketing emails, analytics
     Cómo: Explicit opt-in (no pre-checked)
     Revoke: User puede cambiar en settings

[✅] 6.1(b) Contract
     Cuando: Datos necesarios para prestar servicio
     Ejemplo: Email, username, transaction history
     Cómo: Automático al crear cuenta
     Revoke: No (necesario para servicio)

[✅] 6.1(f) Legitimate Interest
     Cuando: Beneficio comercial sin daño a user
     Ejemplo: Fraud detection, security audit logs
     Cómo: Debe hacer Legitimate Interest Assessment (LIA)
     Revoke: User puede optar

[❌] 6.1(d) Vital Interest
     No aplicable para sistema comercial

[❌] 6.1(e) Public Task
     No aplicable para Mini Market
```

### Legitimate Interest Assessment (LIA) Template

```
Para datos de security audit (Activity Logs):

1. Purpose:
   "Detect fraudulent access, unauthorized data access,
    and maintain system security"

2. Necessity:
   "Essential for business and user protection. Without
    logs, cannot detect/prevent fraud"

3. Balancing Test:
   Nuestro Interés (Security) vs Derechos Usuario:
   ✓ Logs solo internos (no compartidos)
   ✓ Anonimizados después de 90 días
   ✓ Encriptados en almacenamiento
   ✓ Acceso restringido a security team
   ✓ Usuario puede acceder a sus logs (GDPR Art 15)
   
   Conclusión: Legitimate Interest válido ✅

4. Mitigation:
   ✓ Privacy notice en signup
   ✓ Opt-out mechanism for future processing
   ✓ Regular review de retention
```

---

## 👤 Data Subject Rights (Derechos del Usuario)

### Right 1: Access (Artículo 15)
```python
# GDPR: "Right to know what data we have about you"

Implementación:
✅ Endpoint: GET /api/gdpr/my-data
   Requiere: Autenticación + Verificación identidad
   Retorna: JSON con TODOS los datos personales

Código ejemplo:
@app.get("/api/gdpr/my-data")
async def get_my_data(request: Request):
    """
    Export all personal data for this user
    GDPR Article 15 - Right of Access
    """
    user_id = request.state.user.id
    
    # Collect data from all tables
    data = {
        "user_profile": db.query(User).filter(...).one(),
        "activity_logs": db.query(AuditLog).filter(...).all(),
        "transactions": db.query(Transaction).filter(...).all(),
        "encrypted_access": db.query(EncryptedAccess).filter(...).all(),
    }
    
    # Export as JSON/CSV/XML
    return JSONResponse(content=data)

Timeline: 45 calendar days from request
```

### Right 2: Rectification (Artículo 16)
```python
# GDPR: "Right to correct inaccurate data about you"

Implementación:
✅ Endpoint: PUT /api/gdpr/correct-data
   Requiere: User-initiated change + audit log
   Audita: ¿Qué cambió? ¿Quién? ¿Cuándo?

@app.put("/api/gdpr/correct-data")
async def correct_data(request: Request, corrections: dict):
    """
    User can correct their data
    GDPR Article 16 - Right of Rectification
    """
    user_id = request.state.user.id
    
    # Allowed fields to correct
    allowed_fields = ["email", "phone", "name", "address"]
    
    # Log before state
    before = db.query(User).get(user_id)
    
    # Apply corrections
    for field in corrections:
        if field in allowed_fields:
            setattr(user, field, corrections[field])
    
    # Audit log
    log_gdpr_event(
        event_type="RECTIFICATION",
        user_id=user_id,
        fields_changed=list(corrections.keys()),
        before_data=before,
        after_data=user
    )
    
    db.commit()

Timeline: 30 calendar days from request
```

### Right 3: Erasure (Artículo 17 - "Right to Be Forgotten")
```python
# GDPR: "Right to have your data deleted"

Implementación:
✅ Endpoint: DELETE /api/gdpr/erase-my-data
   Requiere: Verificación identidad + Confirmación 
   Nota: Datos legales se pueden retener (contabilidad, etc)

@app.delete("/api/gdpr/erase-my-data")
async def erase_user_data(request: Request, confirmation: str):
    """
    Delete user data per GDPR Article 17
    
    Exceptions:
    - Legal obligation (tax records, 7 years)
    - Legitimate interest (fraud prevention, 1 year)
    - User explicitly requested deletion
    """
    user_id = request.state.user.id
    
    # Verify confirmation
    if confirmation != "I understand this is irreversible":
        raise HTTPException(status_code=400)
    
    # Create deletion record (for legal compliance)
    deletion_record = DeletionRecord(
        user_id=user_id,
        requested_at=datetime.utcnow(),
        requested_by=user_id,
        reason="User request"
    )
    db.add(deletion_record)
    
    # Pseudonymize/Delete data
    user = db.query(User).get(user_id)
    user.email = f"deleted_{user_id}@erased.local"
    user.phone = "ERASED"
    user.password_hash = "ERASED"
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    
    # Cascade delete non-legal data
    db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id,
        ActivityLog.event_timestamp < datetime.utcnow() - timedelta(days=90)
    ).delete()
    
    # Log GDPR event
    log_gdpr_event(
        event_type="ERASURE",
        user_id=user_id,
        reason="User request"
    )
    
    db.commit()
    
    return {"status": "User data erased"}

Timeline: 30 calendar days from request
Legal exceptions: Tax records (7 years), Security logs (1 year after user deletion)
```

### Right 4: Portability (Artículo 20)
```python
# GDPR: "Right to export your data in structured format"

Implementación:
✅ Endpoint: GET /api/gdpr/export-my-data?format=json
   Formats: JSON, CSV, XML
   Requiere: Autenticación

@app.get("/api/gdpr/export-my-data")
async def export_user_data(request: Request, format: str = "json"):
    """
    Export user data in portable format
    GDPR Article 20 - Data Portability
    """
    user_id = request.state.user.id
    
    # Gather all user data
    data = {
        "profile": db.query(User).get(user_id).to_dict(),
        "activities": [a.to_dict() for a in db.query(ActivityLog).filter(...)],
        "transactions": [t.to_dict() for t in db.query(Transaction).filter(...)],
    }
    
    # Format export
    if format == "json":
        export = json.dumps(data, indent=2)
        filename = f"my_data_{user_id}.json"
        media_type = "application/json"
    elif format == "csv":
        export = convert_to_csv(data)
        filename = f"my_data_{user_id}.csv"
        media_type = "text/csv"
    
    # Log export
    log_gdpr_event("DATA_PORTABILITY_REQUEST", user_id)
    
    return FileResponse(
        path=filename,
        filename=filename,
        media_type=media_type
    )

Timeline: 30 calendar days from request
```

### Right 5: Object (Artículo 21)
```python
# GDPR: "Right to object to processing"

Implementación:
✅ Endpoint: POST /api/gdpr/object-processing
   Tipos: Marketing, analytics, profiling

@app.post("/api/gdpr/object-processing")
async def object_to_processing(
    request: Request,
    processing_type: str  # "marketing", "analytics", "profiling"
):
    """
    User can object to non-essential processing
    GDPR Article 21 - Right to Object
    """
    user_id = request.state.user.id
    
    user = db.query(User).get(user_id)
    
    if processing_type == "marketing":
        user.consent_marketing = False
    elif processing_type == "analytics":
        user.consent_analytics = False
    elif processing_type == "profiling":
        user.consent_profiling = False
    
    db.commit()
    
    return {"message": f"Objection to {processing_type} recorded"}
```

---

## 🔒 Privacy by Design

### Data Minimization
```
Collect ONLY what's necessary:

❌ WRONG: Collect email, phone, address, DOB, SSN, everything
✅ RIGHT: Collect only email (for login) + username

Current Implementation:
- User table: id, email, phone, password_hash, created_at, role
  • Email: Required for authentication & notifications ✅
  • Phone: Optional for 2FA (user consents) ✅
  • Password: Required for authentication ✅
  • Role: Required for authorization ✅

Review: Do we really need all these? Remove unnecessary fields.
```

### Encryption & Security
```
✅ Implemented:
  • Encryption at rest (AES-256-CBC)
  • Encryption in transit (TLS 1.2+)
  • Passwords hashed (Argon2)
  • API keys not stored in plaintext

Policy:
- Change encryption key yearly
- Rotate TLS certificates
- Audit encryption access logs
```

### Data Retention Policy
```python
class DataRetentionPolicy:
    """
    GDPR Article 5(1)(e) - Storage Limitation
    Delete data when no longer needed
    """
    
    # User Account Data
    user_account_data = {
        "retention_period": "Duration of contract + 3 months",
        "reason": "Contractual necessity + right to erasure",
        "deletion_trigger": "User requests erasure or account inactive 2 years"
    }
    
    # Activity Logs (Security)
    activity_logs = {
        "retention_period": "90 days active + 1 year legal hold",
        "reason": "Legitimate interest (security, fraud prevention)",
        "deletion_trigger": "Automatic deletion per policy"
    }
    
    # Transaction Records
    transaction_records = {
        "retention_period": "7 years",
        "reason": "Legal obligation (tax/accounting)",
        "deletion_trigger": "Never (legal requirement)"
    }
    
    # Marketing Consent Records
    marketing_records = {
        "retention_period": "Duration of marketing relationship",
        "reason": "Consent management",
        "deletion_trigger": "User withdraws consent or no contact 5 years"
    }
    
    @staticmethod
    async def cleanup_expired_data():
        """Run nightly to delete expired personal data"""
        # Delete activity logs older than 90 days
        db.query(ActivityLog).filter(
            ActivityLog.created_at < datetime.utcnow() - timedelta(days=90)
        ).delete()
        
        # Pseudonymize deleted user records
        db.query(User).filter(
            User.is_deleted == True,
            User.deleted_at < datetime.utcnow() - timedelta(days=30)
        ).update({
            User.email: "deleted@erased.local",
            User.phone: None
        })
        
        db.commit()
```

---

## 📋 Data Protection Impact Assessment (DPIA)

```markdown
# DPIA Mini Market Dashboard

## High Risk Processing?
✓ Yes - Encrypted data access logging

## DPIA Required per Article 35:
✓ Systematic monitoring
✓ Evaluation of sensitive data
✓ Profiling / automated decision making (if applicable)
✓ Large scale processing (potentially)

## Assessment:

### 1. Processing Activities
- Activity logging of all API requests
- Encryption key access tracking
- User data access audit

### 2. Data Security Risk
**Low Risk** (mitigated):
- Encryption implemented ✅
- Access logging implemented ✅
- Retention policies defined ✅
- Breach procedures documented ✅

### 3. Data Subject Risk
**Low Risk**:
- No automated decision making
- No profiling
- User has rights to access/deletion
- Data minimized appropriately

### 4. Mitigation Measures
✅ Encryption at rest & transit
✅ Access controls (authentication + authorization)
✅ Audit logging
✅ Data retention policies
✅ Breach notification procedures
✅ Privacy notices
✅ Consent management

### Conclusion
APPROVED - Processing can proceed with implemented safeguards.
Review annually or when:
- Processing scope changes
- New data categories added
- Technical changes made
```

---

## 🚨 Incident Response (Breach Notification)

### Timeline
```
Personal Data Breach occurs
         ↓
    [WITHOUT UNDUE DELAY, max 72 hours]
         ↓
    Notify Supervisory Authority
    (GDPR Article 33)
         ↓
    [IF high risk]
         ↓
    Notify Data Subjects
    (GDPR Article 34)
```

### Implementation
```python
@app.post("/api/admin/report-breach")
async def report_security_breach(
    request: Request,
    breach_details: BreachReport
):
    """
    GDPR Article 33 & 34 - Breach Notification
    """
    # Log breach
    breach_record = SecurityBreach(
        reported_at=datetime.utcnow(),
        reported_by=request.state.user.id,
        description=breach_details.description,
        data_categories=breach_details.affected_data,
        affected_individuals=breach_details.affected_count,
        breach_timestamp=breach_details.discovery_time,
        likelyhood_of_harm=assess_harm_risk(breach_details)
    )
    db.add(breach_record)
    db.commit()
    
    # Assess likelihood of high risk
    if breach_record.likelyhood_of_harm == "HIGH":
        # Notify affected users within 72 hours
        affected_users = find_affected_users(breach_details)
        
        for user in affected_users:
            send_notification_email(
                to=user.email,
                subject="Security Breach Notification",
                body=f"""
                We inform you of a security incident affecting your account.
                
                What happened: {breach_details.description}
                When discovered: {breach_record.reported_at}
                Data affected: {', '.join(breach_details.affected_data)}
                
                Actions we took:
                {format_remediation_steps(breach_details)}
                
                Your rights:
                - You can access your data at: {get_gdpr_portal_url()}
                - You can request deletion at: {get_gdpr_portal_url()}
                - Report to authority: [GDPR_AUTHORITY_CONTACT]
                """
            )
    
    return {"status": "Breach recorded", "record_id": breach_record.id}

def assess_harm_risk(breach: BreachReport) -> str:
    """
    Evaluate if breach poses high risk to data subjects
    High Risk if:
    - Encrypted AND key compromised
    - Large number of individuals affected
    - Sensitive data (financial, health)
    - Vulnerable individuals
    """
    score = 0
    if "encrypted_data" in breach.affected_data:
        score += 2
    if breach.affected_count > 100:
        score += 2
    if any(cat in breach.affected_data for cat in ["bank", "health", "ssn"]):
        score += 3
    
    return "HIGH" if score >= 3 else "LOW"
```

---

## 📚 Documentation & Audit

### Records to Maintain
```
GDPR Article 5(1)(a) - Accountability

✅ Processing Records:
   • What data collected
   • For what purpose
   • Legal basis
   • Who has access
   • Retention period
   
✅ Consent Records:
   • When consent obtained
   • What was consented to
   • How user gave consent (signed, checkbox, etc)
   • Can be withdrawn anytime
   
✅ Breach Records:
   • What happened
   • When discovered
   • Who notified
   • What remediation taken
   
✅ Request Records:
   • Data access requests (Article 15)
   • Erasure requests (Article 17)
   • Rectification requests (Article 16)
   • Timeline to respond
   • Actions taken

Implementation:
```python
class GDPRCompliance:
    @staticmethod
    def log_consent_given(user_id: str, consent_type: str):
        """Record explicit consent"""
        record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            given_at=datetime.utcnow(),
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent"),
            consent_version="1.0"
        )
        db.add(record)
        db.commit()
    
    @staticmethod
    def log_gdpr_request(request_type: str, user_id: str):
        """Record GDPR requests"""
        record = GDPRRequestLog(
            request_type=request_type,
            user_id=user_id,
            requested_at=datetime.utcnow(),
            deadline=calculate_deadline(request_type),
            status="PENDING"
        )
        db.add(record)
        db.commit()
```

---

## ✅ Compliance Checklist

```
GDPR COMPLIANCE CHECKLIST - Mini Market Dashboard

Legal Basis:
☐ Identified legal basis for all processing (Art 6)
☐ Documented lawfulness (contract/consent/legitimate interest)
☐ Privacy notices displayed at signup
☐ Consent forms explicit (not pre-checked)

Data Subject Rights:
☐ Article 15 - Access implemented
☐ Article 16 - Rectification implemented
☐ Article 17 - Erasure implemented
☐ Article 18 - Restriction available
☐ Article 20 - Portability implemented
☐ Article 21 - Objection mechanism

Data Protection:
☐ Encryption at rest (AES-256)
☐ Encryption in transit (TLS 1.2+)
☐ Access controls (auth + authz)
☐ Audit logging

Governance:
☐ Data Protection Officer assigned
☐ Data Processing Agreements (DPAs) with vendors
☐ DPIA completed for high-risk processing
☐ Retention policies documented

Incident Response:
☐ Breach response procedure documented
☐ 72-hour notification timeline understood
☐ Contact info for supervisory authority
☐ User notification templates prepared

Documentation:
☐ Records of processing maintained
☐ Consent records stored
☐ Breach records logged
☐ GDPR request log maintained

Status: ✅ COMPLIANT (when all checkboxes complete)
```

---

**Status:** Document de implementación de GDPR completado ✅

Próximo paso: Implementación de endpoints GDPR en FastAPI
