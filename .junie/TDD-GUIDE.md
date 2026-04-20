# TDD Guide — Test-Driven Development

Compiled from hermes-agent TDD skill and claude-skills TDD guide. Strict red-green-refactor methodology.

---

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over. No exceptions.

---

## Red-Green-Refactor Cycle

### RED — Write Failing Test

Write one minimal test showing what should happen.

**Good test:**
```python
def test_retries_failed_operations_3_times():
    attempts = 0
    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception('fail')
        return 'success'

    result = retry_operation(operation)
    assert result == 'success'
    assert attempts == 3
```

**Requirements:**
- One behavior per test
- Clear descriptive name ("and" in name? Split it)
- Real code, not mocks (unless truly unavoidable)
- Name describes behavior, not implementation

### Verify RED — Watch It Fail (MANDATORY)

Confirm:
- Test fails (not errors from typos)
- Failure message is expected
- Fails because the feature is missing

Test passes immediately? You're testing existing behavior. Fix the test.

### GREEN — Minimal Code

Write the simplest code to pass the test. Nothing more.

**Cheating is OK in GREEN:** hardcode return values, copy-paste, duplicate code, skip edge cases. We'll fix it in REFACTOR.

### Verify GREEN — Watch It Pass (MANDATORY)

- Run the specific test → passes
- Run ALL tests → no regressions
- Output pristine (no errors, warnings)

Test fails? Fix the code, not the test.

### REFACTOR — Clean Up

After green only:
- Remove duplication
- Improve names
- Extract helpers
- Simplify expressions

Keep tests green throughout. Don't add behavior.

If tests fail during refactor: Undo immediately. Take smaller steps.

---

## When to Use TDD

**Always:** New features, bug fixes, refactoring, behavior changes.

**Exceptions (ask user first):** Throwaway prototypes, generated code, configuration files.

---

## Coverage Analysis Priority

| Priority | Description | Action |
|----------|-------------|--------|
| P0 | Uncovered error paths (auth, payments) | Test immediately |
| P1 | Core logic branches (else branches, guards) | Test next |
| P2 | Utility/helper functions | Test when time allows |

Target: 80%+ coverage. Focus on P0 items first.

---

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. Keeping unverified code is debt. |
| "Need to explore first" | Fine. Throw away exploration, start with TDD. |
| "Test hard = skip it" | Hard to test = hard to use. Simplify the design. |
| "TDD will slow me down" | TDD faster than debugging. Always. |

---

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know how to test | Write the wished-for API. Write assertion first. |
| Test too complicated | Design too complicated. Simplify the interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup huge | Extract helpers. Still complex? Simplify the design. |

---

## Verification Checklist

Before marking work complete:

- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

---

## Testing Anti-Patterns

- **Testing mock behavior instead of real behavior** — mocks verify interactions, not replace the system
- **Testing implementation details** — test what, not how
- **Shared mutable state between tests** — each test must be independent
- **Overly specific assertions** — assert behavior, not exact strings/timestamps
- **Test names that don't describe behavior** — `test_1`, `test_it_works` tell nothing
