# Code Antipatterns Catalog

Compiled from claude-skills code-reviewer antipatterns and engineering best practices. Quick reference for identifying and fixing common issues.

---

## Structural Antipatterns

### God Class
**Detection:** Class has >20 methods, >500 lines, or handles unrelated concerns.
**Fix:** Split into single-responsibility classes. UserManager → UserRepository + EmailService + PasswordService.

### Long Method
**Detection:** Function >50 lines or requires scrolling to read.
**Fix:** Extract into composed focused functions. `process_order()` → `validate_order()` + `calculate_totals()` + `process_payment()` + `send_notifications()`.

### Deep Nesting
**Detection:** >4 levels of indentation.
**Fix:** Use early returns (guard clauses), extract helper functions, invert conditions.

```python
# BAD
def process(data):
    if data:
        if data.valid:
            if data.ready:
                do_work(data)

# GOOD
def process(data):
    if not data: return
    if not data.valid: return
    if not data.ready: return
    do_work(data)
```

### Feature Envy
**Detection:** Method uses another class's data more than its own.
**Fix:** Move the method to the class whose data it uses.

### Primitive Obsession
**Detection:** Using strings/ints for domain concepts (email as string, money as float).
**Fix:** Create value objects: `Email`, `Money`, `PhoneNumber`.

---

## Logic Antipatterns

### Boolean Blindness
**Detection:** Functions returning bare booleans with unclear meaning.
**Fix:** Return enums or result objects.

```python
# BAD
if check_user(user):  # True means... what?

# GOOD
status = validate_user(user)
if status == ValidationStatus.ACTIVE:
```

### Stringly Typed Code
**Detection:** Using strings where enums/types should be used.
**Fix:** Use enums, constants, or typed objects.

```typescript
// BAD
function setStatus(status: string) { ... }
setStatus("actve")  // Typo compiles fine

// GOOD
enum Status { Active, Inactive, Pending }
function setStatus(status: Status) { ... }
```

### Magic Numbers
**Detection:** Unexplained numeric literals in code.
**Fix:** Extract to named constants.

```python
# BAD
if len(password) < 8:

# GOOD
MIN_PASSWORD_LENGTH = 8
if len(password) < MIN_PASSWORD_LENGTH:
```

---

## Security Antipatterns

### SQL Injection
```python
# BAD
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### Hardcoded Credentials
```python
# BAD
API_KEY = "sk-1234567890abcdef"

# GOOD
API_KEY = os.environ["API_KEY"]
```

### Sensitive Data in Logs
```python
# BAD
logger.info(f"User login: {email}, password: {password}")

# GOOD
logger.info(f"User login: {email}")
```

---

## Performance Antipatterns

### N+1 Queries
```python
# BAD: 1 query for users + N queries for orders
users = User.objects.all()
for user in users:
    orders = Order.objects.filter(user=user)

# GOOD: 1 query with join
users = User.objects.prefetch_related('orders').all()
```

### Unbounded Collections
```python
# BAD: Load everything into memory
all_records = db.query("SELECT * FROM huge_table")

# GOOD: Paginate
records = db.query("SELECT * FROM huge_table LIMIT 100 OFFSET 0")
```

### Missing Indexes
**Detection:** Slow queries on columns used in WHERE, JOIN, ORDER BY.
**Fix:** Add database indexes on frequently queried columns.

---

## Testing Antipatterns

### Testing Implementation, Not Behavior
```python
# BAD: Tests internal method calls
mock_db.save.assert_called_once_with(user)

# GOOD: Tests observable behavior
assert get_user(user_id).name == "Alice"
```

### Test Duplication
**Detection:** Multiple tests with identical setup, differing only in one assertion.
**Fix:** Parameterize tests or extract shared setup.

### Floating Promises (JS/TS)
```typescript
// BAD: Promise result ignored
someAsyncFunction();

// GOOD: Awaited or handled
await someAsyncFunction();
```

---

## Code Quality Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Function length | >50 lines | Extract sub-functions |
| File length | >500 lines | Split into modules |
| Class methods | >20 | Split responsibilities |
| Parameters | >5 | Use options object |
| Nesting depth | >4 levels | Use guard clauses |
| Cyclomatic complexity | >10 branches | Simplify logic |
