# Code Review Checklist

Compiled from claude-skills code-reviewer references. Systematic review across all quality dimensions.

---

## Pre-Review Checks

### Build and Tests
- [ ] Code compiles without errors
- [ ] All existing tests pass
- [ ] New tests included for new functionality
- [ ] No unintended files (build artifacts, IDE configs)

### PR Hygiene
- [ ] Clear title and description
- [ ] Changes scoped appropriately (not too large)
- [ ] Commits follow conventional format
- [ ] Branch up to date with base

### Scope
- [ ] Changes match stated purpose
- [ ] No unrelated changes bundled in
- [ ] Breaking changes documented
- [ ] Migration path provided if needed

---

## Correctness

### Logic
- [ ] Algorithm implements requirements correctly
- [ ] Edge cases handled (null, empty, boundary values)
- [ ] Off-by-one errors checked
- [ ] Correct operators (== vs ===, & vs &&)
- [ ] Loop termination conditions correct
- [ ] Recursion has proper base cases

### Data Handling
- [ ] Data types appropriate for use case
- [ ] Numeric overflow/underflow considered
- [ ] Date/time handles timezones
- [ ] Unicode and i18n handled
- [ ] Data validation at entry points

### State Management
- [ ] State transitions are valid
- [ ] Race conditions addressed
- [ ] Concurrent access handled
- [ ] State cleanup on errors/exit

### Error Handling
- [ ] Errors caught at appropriate levels
- [ ] Error messages are actionable
- [ ] Errors don't expose sensitive info
- [ ] Recovery or graceful degradation implemented
- [ ] Resources cleaned up in error paths

---

## Security

### Input Validation
- [ ] All user input validated and sanitized
- [ ] Input length limits enforced
- [ ] File uploads validated (type, size, content)

### Injection Prevention
- [ ] SQL queries parameterized
- [ ] Command execution uses safe APIs
- [ ] HTML output escaped (XSS prevention)
- [ ] XML parsing disables external entities

### Auth & Data Protection
- [ ] Authentication required for protected resources
- [ ] Authorization checked before operations
- [ ] Sensitive data encrypted at rest and in transit
- [ ] Secrets not hardcoded
- [ ] Logs don't contain sensitive data
- [ ] Rate limiting implemented
- [ ] CORS configured correctly

---

## Performance

### Efficiency
- [ ] Appropriate data structures used
- [ ] Algorithms have acceptable complexity
- [ ] Database queries optimized
- [ ] N+1 query problems avoided
- [ ] Indexes used where beneficial

### Resources
- [ ] Memory usage bounded, no leaks
- [ ] File handles properly closed
- [ ] Database connections pooled
- [ ] Network calls minimized
- [ ] Async processing for long operations

---

## Maintainability

### Code Quality
- [ ] Functions have single responsibility
- [ ] Classes follow SOLID principles
- [ ] Code is DRY
- [ ] No dead code or commented-out code
- [ ] Magic numbers replaced with constants

### Naming & Structure
- [ ] Names descriptive and consistent
- [ ] Functions <50 lines preferred
- [ ] Nesting depth <4 levels
- [ ] Related code grouped together
- [ ] Dependencies minimal and explicit

---

## Testing

- [ ] New code has unit tests
- [ ] Critical paths have integration tests
- [ ] Edge cases and error conditions tested
- [ ] Tests are independent
- [ ] Test names describe what is tested
- [ ] External dependencies mocked appropriately

---

## Language-Specific Checks

### TypeScript/JavaScript
- [ ] Types explicit (avoid `any`)
- [ ] Null checks present (`?.`, `??`)
- [ ] Async/await errors handled
- [ ] No floating promises

### Python
- [ ] Type hints for public APIs
- [ ] Context managers for resources (`with`)
- [ ] Specific exception handling (not bare `except`)
- [ ] No mutable default arguments

### Go
- [ ] Errors checked and handled
- [ ] Goroutine leaks prevented
- [ ] Context propagation correct
- [ ] Defer statements in right order

### Kotlin
- [ ] Null safety leveraged
- [ ] Coroutine cancellation handled
- [ ] Data classes used appropriately
- [ ] Sealed classes for state

---

## Review Verdicts

| Score | Verdict |
|-------|---------|
| 90+ with no high issues | Approve |
| 75+ with ≤2 high issues | Approve with suggestions |
| 50-74 | Request changes |
| <50 or critical issues | Block |

---

## When to Block

- Security vulnerabilities present
- Critical logic errors
- No tests for risky changes
- Breaking changes without migration
- Significant performance regressions
