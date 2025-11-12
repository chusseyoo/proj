# Minor Inconsistencies - Resolution Document

Generated: November 12, 2025  
Purpose: Address questions 10-12 from DOCUMENTATION_INCONSISTENCIES.md

---

## 10. Repository Method Naming: `find_by_id()` vs `get_by_id()`

### The Difference

Both methods retrieve an entity by primary key, but handle "not found" differently:

**`get_by_id(pk)`**
- **Returns:** Domain entity (always)
- **Not Found:** Raises domain exception (e.g., `UserNotFoundError`)
- **Use When:** Failure to find is an error condition
- **Example:** Getting user to display profile (404 if not found)

**`find_by_id(pk)`**
- **Returns:** Domain entity OR `None`
- **Not Found:** Returns `None` (no exception)
- **Use When:** Absence is a valid scenario
- **Example:** Checking if entity exists before creating

### Implementation Pattern

**Standard Repository Implementation:**
```python
class UserRepository:
    def get_by_id(self, user_id: int) -> User:
        """
        Get user by ID. Raises if not found.
        
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            user_model = UserModel.objects.get(user_id=user_id)
            return self._to_domain(user_model)
        except UserModel.DoesNotExist:
            raise UserNotFoundError(f"User with ID {user_id} not found")
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """
        Find user by ID. Returns None if not found.
        
        Returns:
            User domain entity or None
        """
        try:
            return self.get_by_id(user_id)
        except UserNotFoundError:
            return None
```

**Note:** `find_by_id` delegates to `get_by_id` and catches the exception. This keeps logic DRY.

### Usage Examples

**Scenario 1: Display User Profile (use `get_by_id`)**
```python
# Application Service
def get_user_profile(self, user_id: int) -> User:
    # User MUST exist; exception bubbles up to API (becomes 404)
    user = self.user_repository.get_by_id(user_id)
    return user
```

**Scenario 2: Check if User Exists Before Creating (use `find_by_id`)**
```python
# Application Service
def register_user(self, email: str) -> User:
    # Check if user with email already exists (valid scenario)
    existing = self.user_repository.find_by_email(email)
    if existing is not None:
        raise EmailAlreadyExistsError(email)
    
    # Create new user
    return self.user_repository.create(...)
```

**Scenario 3: Optional Lookup (use `find_by_id`)**
```python
# Domain Service
def enrich_data_with_user_info(self, user_id: Optional[int]) -> dict:
    # User might not exist; return partial data if missing
    user = self.user_repository.find_by_id(user_id) if user_id else None
    return {
        'user_name': user.get_full_name() if user else 'Unknown',
        # ... other data
    }
```

### Naming Convention Consistency

**Enforced Pattern Across All Repositories:**

| Method | Returns | Not Found | When to Use |
|--------|---------|-----------|-------------|
| `get_by_id(pk)` | Entity | Exception | Required lookup |
| `find_by_id(pk)` | Entity \| None | None | Optional lookup |
| `get_by_email(email)` | Entity | Exception | Required lookup |
| `find_by_email(email)` | Entity \| None | None | Optional lookup |
| `exists_by_id(pk)` | bool | False | Existence check only |
| `exists_by_email(email)` | bool | False | Existence check only |

**Rule of Thumb:**
- `get_*` → Raises exception if not found
- `find_*` → Returns `None` if not found
- `exists_*` → Returns boolean (never raises)

### Where They Should Be Used

**Application Services (Use `get_*`):**
- When retrieving entity for display/update
- When entity MUST exist for operation to proceed
- Let exception bubble to API layer (becomes HTTP 404)

**Domain Services (Use `find_*`):**
- When absence is a valid business scenario
- When checking optional relationships
- When implementing "if exists, do X; else do Y" logic

**Application Services - Validation (Use `exists_*`):**
- Checking uniqueness before creation
- Simple boolean checks
- Performance optimization (no entity hydration)

### Documentation Update

**Add to `repositories_guide.md`:**

```markdown
## Repository Method Patterns

### Lookup Methods

**Pattern 1: `get_by_*` - Required Lookup**
- Returns domain entity (always)
- Raises domain exception if not found
- Use when entity MUST exist

**Pattern 2: `find_by_*` - Optional Lookup**
- Returns domain entity OR `None`
- No exception if not found
- Use when absence is valid scenario

**Pattern 3: `exists_by_*` - Existence Check**
- Returns boolean
- Never raises exception
- Use for simple existence checks

**Implementation:**
```python
def get_by_id(self, entity_id: int) -> Entity:
    try:
        model = Model.objects.get(id=entity_id)
        return self._to_domain(model)
    except Model.DoesNotExist:
        raise EntityNotFoundError(f"Entity {entity_id} not found")

def find_by_id(self, entity_id: int) -> Optional[Entity]:
    try:
        return self.get_by_id(entity_id)
    except EntityNotFoundError:
        return None

def exists_by_id(self, entity_id: int) -> bool:
    return Model.objects.filter(id=entity_id).exists()
```

**Usage Guidelines:**
- Service layer should prefer `get_*` for required lookups
- Domain logic should prefer `find_*` for optional lookups
- Use `exists_*` only when you don't need the entity itself
```

---

## 11. Email Normalization Location

### Current Implementation Analysis

**You're correct!** Email normalization is already happening in the value object:

**File:** `domain/value_objects/email.py`
```python
@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        # Normalize to lowercase
        object.__setattr__(self, 'value', self.value.lower())
        
        # Validate format
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
    
    def _is_valid_email(self, email: str) -> bool:
        # Email regex validation
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def domain(self) -> str:
        return self.value.split('@')[1]
```

### Why This Is the Correct Approach

**Pros of Value Object Normalization:**
1. ✅ **Single Responsibility** - Email value object owns email rules
2. ✅ **Guarantee** - Impossible to create invalid or non-normalized email
3. ✅ **Type Safety** - `Email` type guarantees valid, normalized email
4. ✅ **DRY** - No duplication across service/model layers
5. ✅ **Testable** - Value object tested in isolation
6. ✅ **Domain-Driven** - Business rule lives in domain layer

**If it were in the service layer:**
- ❌ Easy to forget normalization in one service
- ❌ Requires defensive checks everywhere
- ❌ No type-level guarantee

**If it were in the model layer:**
- ❌ Ties domain rule to infrastructure (Django ORM)
- ❌ Can't test without database
- ❌ Violates DDD layering (domain depends on infrastructure)

### Current Flow

```
Input: "User@Example.COM"
    ↓
Email("User@Example.COM")
    ↓ (__post_init__)
Normalize: "user@example.com"
    ↓
Validate format
    ↓
Return: Email(value="user@example.com")
```

**Service Layer:**
```python
# Services just use the value object
email = Email(user_data['email'])  # Normalization happens here
user = User(email=email, ...)
```

**No Additional Normalization Needed:**
- Services receive already-normalized `Email` object
- Models receive already-normalized `Email` object
- Repository converts `Email.value` to string for ORM

### Documentation Clarification

**Update to `models_guide.md`:**

```markdown
### Email Validation

**Normalization Handled by Value Object:**
Email normalization (lowercase conversion) is handled by the `Email` value object in the domain layer. The `User.save()` method does NOT need to normalize email because:

1. Email is passed as `Email` value object (already normalized)
2. Repository converts `Email.value` to string (already lowercase)
3. Domain layer guarantees no denormalized emails exist

**Flow:**
```
Raw input → Email VO (normalizes + validates) → Entity → Repository → ORM Model
```

**No redundant normalization:**
```python
# ❌ Don't do this (value object already did it)
def save(self, *args, **kwargs):
    self.email = self.email.lower()  # Redundant!
    super().save(*args, **kwargs)

# ✅ Trust the value object
# Model receives already-normalized email from repository
```
```

**Update to `services_guide.md`:**

```markdown
### Email Normalization

Email normalization is **centralized in the `Email` value object** (domain layer). Services do not need to perform normalization:

```python
# Service layer
def register_user(self, user_data: dict) -> User:
    # Email automatically normalized when creating value object
    email = Email(user_data['email'])  # Lowercase happens here
    
    # Check uniqueness (email is already normalized)
    if self.user_repository.exists_by_email(str(email)):
        raise EmailAlreadyExistsError(...)
    
    # Create user
    user = User(email=email, ...)
    return self.user_repository.create(user)
```

**Why?**
- Single source of truth (value object)
- Type safety (Email type guarantees normalization)
- No duplication across services
```

### Recommendation: Document, Don't Change

**Status:** ✅ Implementation is correct as-is  
**Action:** Update documentation to clarify normalization happens in value object  
**No Code Changes Needed**

---

## 12. Transaction Management for All Registrations

### Current Implementation

```python
@transaction.atomic
def register_lecturer(self, lecturer_data: Dict) -> Dict:
    # Create User + LecturerProfile
    ...

@transaction.atomic
def register_student(self, student_data: Dict, admin_user: User) -> Dict:
    # Create User + StudentProfile
    ...

@transaction.atomic  # ← Question: Why?
def register_admin(self, admin_data: Dict, creator_admin: User) -> Dict:
    # Create User only (no profile)
    ...
```

### Why Transactions for All Roles?

**Admin Registration (Single Table):**
- Technically doesn't need transaction (single INSERT)
- But using `@transaction.atomic` is still beneficial:

**Reasons:**

1. **Consistency Across Methods**
   - All registration methods behave the same way
   - Easier to understand and maintain
   - No "why does this one not have transaction?" questions

2. **Future-Proofing**
   - If admin registration later needs audit log entry
   - If system event needs to be recorded
   - If welcome email needs transactional inbox pattern
   - Transaction already in place

3. **Explicit Intent**
   - Clearly signals "this is a database operation"
   - Shows method participates in data persistence
   - Documents atomicity guarantee

4. **Negligible Overhead**
   - Single-query transactions are very cheap
   - Transaction START → INSERT → COMMIT is minimal overhead
   - No performance impact in practice

5. **Safety Net**
   - Protects against future multi-step additions
   - Prevents accidental partial commits
   - Developer doesn't have to remember to add later

6. **Testing Benefits**
   - Test cleanup easier (rollback in teardown)
   - Consistent test patterns across all registration tests
   - Database state more predictable

### Technical Analysis

**With Transaction (Current):**
```sql
BEGIN;
INSERT INTO users (...) VALUES (...);
COMMIT;
```

**Without Transaction (Alternative):**
```sql
INSERT INTO users (...) VALUES (...);
-- Autocommit mode, immediate commit
```

**Performance Difference:** Negligible (microseconds)

**Safety Difference:** Significant (future-proof)

### When NOT to Use Transactions

**Don't Use Transactions For:**
- ❌ Read-only queries (SELECT)
- ❌ External API calls (not rollbackable)
- ❌ Long-running operations (holds locks)
- ❌ File I/O (not transactional)

**Do Use Transactions For:**
- ✅ Multiple related writes
- ✅ Single writes that might expand
- ✅ Consistency-critical operations
- ✅ Operations where partial failure is unacceptable

### Recommendation: Keep Current Implementation

**Status:** ✅ Current implementation is correct  
**Rationale:** Consistency, safety, and future-proofing outweigh minimal overhead  
**Action:** Update documentation to explain rationale

### Documentation Update

**Update to `services_guide.md`:**

```markdown
### Transaction Management

**When to Use Transactions:**
- ✅ Lecturer registration (User + LecturerProfile)
- ✅ Student registration (User + StudentProfile)
- ✅ Admin registration (User only)

**Why Transaction for Admin (Single Table)?**

Although admin registration only creates a User (no profile), we still use `@transaction.atomic`:

1. **Consistency**: All registration methods behave the same way
2. **Future-Proofing**: Easy to add audit logs, events, etc. later
3. **Explicit Intent**: Clearly marks database operations
4. **Negligible Overhead**: Single-query transactions are very cheap
5. **Safety Net**: Protects against future multi-step additions

**Transaction Pattern:**
```python
from django.db import transaction

@transaction.atomic
def register_admin(admin_data, creator_admin):
    # Step 1: Validate
    # Step 2: Create User
    user = user_repository.create(user_data)
    
    # Future steps easily added here:
    # Step 3: Log event (future)
    # Step 4: Send notification (future)
    
    # All-or-nothing: if any step fails, entire operation rolls back
    return {'user': user}
```

**Email Sending (Outside Transaction):**
```python
@transaction.atomic
def register_lecturer(lecturer_data):
    user = user_repository.create(...)
    profile = lecturer_repository.create(...)
    # Transaction commits here

# Send email AFTER transaction commits
email_service.send_welcome_email(user.email)
```

**Why Email Outside:**
- Email sending can fail without affecting registration
- Transaction shouldn't hold locks during slow I/O
- Email can be retried separately if needed
```

---

## Summary of Resolutions

### 10. Repository Method Naming
- **Decision:** Maintain `get_*` (raises) vs `find_*` (returns None) pattern
- **Action:** Document pattern in repositories_guide.md
- **Usage:** Application services prefer `get_*`; domain logic uses `find_*`

### 11. Email Normalization
- **Decision:** Keep normalization in `Email` value object (correct as-is)
- **Rationale:** Single responsibility, type safety, DRY principle
- **Action:** Document in models_guide.md and services_guide.md

### 12. Transaction Management
- **Decision:** Keep `@transaction.atomic` on all registrations (including admin)
- **Rationale:** Consistency, future-proofing, explicit intent, safety
- **Action:** Document rationale in services_guide.md

---

**Status**: ✅ All minor inconsistencies resolved with clear rationale
