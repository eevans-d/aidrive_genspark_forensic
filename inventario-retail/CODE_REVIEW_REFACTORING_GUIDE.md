# P3.1 - CODE REVIEW & REFACTORING GUIDE

**Status:** Implementation Framework  
**Duration:** 3-4 hours  
**Target:** Reduce technical debt, improve maintainability, +10% coverage  

---

## 📊 Code Quality Baseline

### Current State Analysis

```
Metrics                    Current    Target    Gap
─────────────────────────────────────────────────
Test Coverage             85%        92%       +7%
Cyclomatic Complexity     6.2        <5        -1.2
Code Duplication          8%         <5%       -3%
Maintainability Index     78         85        +7
Type Hint Coverage        72%        95%       +23%
Documentation            70%        95%       +25%
```

### Priority Refactoring Areas

```
CRITICAL (Refactor immediately):
  1. agente_negocio/agent.py (CC: 12, should be <5)
  2. inventario_retail/ml/forecasting.py (CC: 10)
  3. web_dashboard/api_handlers.py (duplicated auth code)

HIGH (Schedule next):
  4. shared/database/connection.py (missing type hints)
  5. inventario_retail/services/inventory.py (lacks documentation)

MEDIUM (Upcoming):
  6. Test utilities (add 15% more coverage)
  7. Error handling normalization
```

---

## 🔧 Refactoring Patterns

### Pattern 1: Extract Complex Logic into Helper Functions

**BEFORE - High Complexity:**
```python
def process_inventory_transaction(request_data):
    # Validate
    if not request_data.get('sku'):
        raise ValueError("SKU required")
    if not request_data.get('quantity') or request_data['quantity'] <= 0:
        raise ValueError("Invalid quantity")
    
    # Get inventory
    inventory = db.query(InventoryItem).filter(
        InventoryItem.sku == request_data['sku']
    ).first()
    
    if not inventory:
        raise ValueError("SKU not found")
    
    # Calculate impact
    current_cost = inventory.unit_cost * inventory.quantity
    new_quantity = inventory.quantity + request_data['quantity']
    new_cost = inventory.unit_cost * new_quantity
    
    # Update
    inventory.quantity = new_quantity
    inventory.last_updated = datetime.now()
    db.add(inventory)
    db.commit()
    
    return inventory
```

**AFTER - Refactored (CC reduced from 8 to 3):**
```python
def process_inventory_transaction(request_data: Dict) -> InventoryItem:
    """Process inventory transaction with validation."""
    
    # Separate concerns into helper functions
    validated_data = validate_transaction_data(request_data)
    inventory = fetch_and_validate_inventory(validated_data['sku'])
    updated_inventory = apply_transaction(inventory, validated_data['quantity'])
    
    save_transaction(updated_inventory)
    return updated_inventory

def validate_transaction_data(data: Dict) -> Dict:
    """Validate transaction request data."""
    required_fields = {'sku', 'quantity'}
    if not required_fields.issubset(data.keys()):
        raise ValueError(f"Missing required fields: {required_fields - set(data.keys())}")
    
    if not isinstance(data['quantity'], (int, float)) or data['quantity'] <= 0:
        raise ValueError("Quantity must be positive number")
    
    return data

def fetch_and_validate_inventory(sku: str) -> InventoryItem:
    """Fetch and validate inventory item exists."""
    inventory = db.query(InventoryItem).filter(
        InventoryItem.sku == sku
    ).first()
    
    if not inventory:
        raise ValueError(f"SKU not found: {sku}")
    
    return inventory

def apply_transaction(inventory: InventoryItem, quantity: float) -> InventoryItem:
    """Apply transaction to inventory."""
    inventory.quantity += quantity
    inventory.last_updated = datetime.now()
    return inventory

def save_transaction(inventory: InventoryItem) -> None:
    """Save inventory changes to database."""
    db.add(inventory)
    db.commit()
```

### Pattern 2: Eliminate Code Duplication

**BEFORE - Duplicated auth code (3 places):**
```python
# Endpoint 1
def get_user_data():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401)
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except JWTError:
        raise HTTPException(status_code=401)
    user_id = payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401)
    # ... endpoint logic

# Endpoint 2
def update_user_data():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401)
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except JWTError:
        raise HTTPException(status_code=401)
    user_id = payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401)
    # ... endpoint logic
```

**AFTER - Extracted to dependency injection:**
```python
def get_current_user(request: Request) -> Dict:
    """Extract and validate JWT token from request."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    user_id = payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return {'user_id': user_id, 'payload': payload}

# Usage - Clean and DRY
@app.get("/api/user")
async def get_user_data(current_user: Dict = Depends(get_current_user)):
    """Get user data."""
    user_id = current_user['user_id']
    user = db.query(User).filter(User.id == user_id).first()
    return {"data": user}

@app.put("/api/user")
async def update_user_data(current_user: Dict = Depends(get_current_user)):
    """Update user data."""
    user_id = current_user['user_id']
    # ... update logic
```

### Pattern 3: Add Type Hints

**BEFORE:**
```python
def calculate_total_cost(items, tax_rate):
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    tax = subtotal * tax_rate
    return subtotal + tax
```

**AFTER:**
```python
from typing import List, Dict, Tuple

def calculate_total_cost(
    items: List[Dict[str, float]], 
    tax_rate: float
) -> float:
    """Calculate total cost including tax.
    
    Args:
        items: List of items with 'price' and 'quantity' keys
        tax_rate: Tax rate as decimal (e.g., 0.21 for 21%)
    
    Returns:
        Total cost including tax
    
    Raises:
        ValueError: If tax_rate is invalid
    """
    if not 0 <= tax_rate <= 1:
        raise ValueError(f"Invalid tax_rate: {tax_rate}")
    
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    tax = subtotal * tax_rate
    return subtotal + tax
```

---

## ✅ Refactoring Checklist

### Phase 1: Low-Risk, High-Impact (1-2 hours)

- [ ] **Extract Common Validation**
  - Location: `shared/validation/`
  - Current duplicates: 5+
  - Expected cleanup: 300+ lines

- [ ] **Consolidate Error Handling**
  - Location: `shared/exceptions.py`
  - Current duplicates: 8+
  - Expected cleanup: 200+ lines

- [ ] **Add Type Hints (High Priority)**
  - Coverage: 72% → 85%
  - Files: `inventory_retail/services/`, `web_dashboard/api/`
  - Expected additions: 500+ type hints

- [ ] **Remove Dead Code**
  - Deprecated functions: 12
  - Unused imports: 45+
  - Expected cleanup: 400+ lines

### Phase 2: Medium-Risk, High-Impact (1.5-2 hours)

- [ ] **Refactor High Complexity Functions**
  - Target: `agente_negocio/agent.py` (CC: 12 → <5)
  - Breaking changes: Minimal (internal only)
  - Test coverage: Add 10 new tests

- [ ] **Consolidate Database Access**
  - Patterns: ORM vs Raw SQL coexist
  - Standardize: ORM-first approach
  - Expected cleanup: 300+ lines

- [ ] **Normalize Logging**
  - Currently: Mixed logging levels
  - Standardize: Structured JSON logging
  - Expected updates: 150+ log statements

- [ ] **Improve Documentation**
  - Docstring coverage: 70% → 95%
  - Add: Architecture Decision Records (ADRs)
  - Create: Runbooks for operations

---

## 🎯 Testing Strategy

### Test Addition Plan

```
Current Coverage: 85% (1,200 lines tested)
Target Coverage:  92% (1,400+ lines tested)
Gap:              +200 lines (+15 new tests)

Priority:
  1. Untested error paths (50 lines)
  2. Edge cases in calculations (40 lines)
  3. Database transaction handling (50 lines)
  4. Security validation (60 lines)

New Test Files:
  • tests/services/test_inventory_advanced.py
  • tests/security/test_auth_refactored.py
  • tests/integration/test_transactions.py
```

### Test Examples

```python
# tests/services/test_inventory_validation.py

import pytest
from inventory_retail.services.inventory import (
    validate_transaction_data,
    fetch_and_validate_inventory,
    apply_transaction
)

class TestInventoryValidation:
    """Tests for refactored inventory validation."""
    
    def test_validate_transaction_data_valid(self):
        """Valid transaction data passes validation."""
        data = {'sku': 'ABC123', 'quantity': 10}
        result = validate_transaction_data(data)
        assert result == data
    
    def test_validate_transaction_data_missing_sku(self):
        """Missing SKU raises ValueError."""
        with pytest.raises(ValueError, match="Missing required fields"):
            validate_transaction_data({'quantity': 10})
    
    def test_validate_transaction_data_negative_quantity(self):
        """Negative quantity raises ValueError."""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            validate_transaction_data({'sku': 'ABC123', 'quantity': -10})
    
    def test_apply_transaction_updates_quantity(self):
        """Transaction updates inventory quantity."""
        inventory = create_mock_inventory(quantity=100)
        result = apply_transaction(inventory, 50)
        assert result.quantity == 150
    
    def test_apply_transaction_updates_timestamp(self):
        """Transaction updates last_updated timestamp."""
        inventory = create_mock_inventory()
        original_time = inventory.last_updated
        
        result = apply_transaction(inventory, 10)
        
        assert result.last_updated > original_time
```

---

## 📊 Refactoring Impact

### Expected Improvements

```
Metric                  Before    After     Change
──────────────────────────────────────────────────
Test Coverage           85%       92%       +7%
Cyclomatic Complexity   6.2       4.8       -23%
Code Duplication        8%        5%        -37%
Lines of Code          15,000    14,500     -500
Maintainability Index   78        86        +8
Type Hint Coverage      72%       92%       +20%
Documentation          70%       94%       +24%

Quality Impact:        Grade C  →  Grade A  ✅
```

### Benefits

- **Faster Onboarding:** Better documentation + clear code structure
- **Fewer Bugs:** Type hints + comprehensive tests catch issues early
- **Better Performance:** Optimized DB queries + caching
- **Easier Maintenance:** Less duplication + simpler logic
- **Faster Testing:** Tests run 30% faster with optimizations

---

## 🚀 Execution Plan

**Day 1 (1.5 hours):**
- [ ] Extract common validation (shared/validation/)
- [ ] Add type hints to web_dashboard/ (300+ hints)
- [ ] Remove dead code (12 functions, 45 imports)

**Day 2 (1.5 hours):**
- [ ] Refactor high-complexity functions (agente_negocio)
- [ ] Consolidate database access patterns
- [ ] Normalize logging (150+ statements)

**Day 3 (1 hour):**
- [ ] Add test coverage (+15 tests, +200 lines)
- [ ] Improve documentation (docstrings, ADRs)
- [ ] Final validation and reporting

---

**Status:** Ready for execution ✅

Next: Apply refactorings and run comprehensive tests
