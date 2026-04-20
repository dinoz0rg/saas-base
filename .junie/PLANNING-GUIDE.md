# Implementation Planning Guide

Adapted from Hermes Agent writing-plans and plan-mode skills. Optimized for Junie.

---

## When to Plan

**Always plan before:**
- Implementing multi-step features
- Breaking down complex requirements
- Any task touching 3+ files

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)

## Plan-Only Mode

When the user asks for a plan (not execution):
- Do not implement code or edit project files
- You may inspect the repo with read-only tools
- Deliver a markdown plan (see structure below)
- If the request is underspecified, ask a brief clarifying question

---

## Bite-Sized Task Granularity

**Each task = 2–5 minutes of focused work. One action per step.**

- "Write the failing test" — step
- "Run it to verify failure" — step
- "Implement minimal code to pass" — step
- "Run tests to verify pass" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

---

## Plan Document Structure

### Header (Required)

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2–3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS
````

---

## Writing Process

1. **Understand requirements** — Read specs, acceptance criteria, constraints
2. **Explore the codebase** — Understand project structure, find similar patterns, check existing tests
3. **Design approach** — Architecture pattern, file organization, dependencies, testing strategy
4. **Write tasks** — In order: setup → core functionality (TDD) → edge cases → integration → cleanup
5. **Add complete details** — Exact file paths, complete code examples, exact commands with expected output, verification steps
6. **Review the plan:**
   - [ ] Tasks are sequential and logical
   - [ ] Each task is bite-sized (2–5 min)
   - [ ] File paths are exact
   - [ ] Code examples are complete (copy-pasteable)
   - [ ] Commands are exact with expected output
   - [ ] No missing context
   - [ ] DRY, YAGNI, TDD principles applied

---

## Common Mistakes

| Mistake | Bad | Good |
|---------|-----|------|
| Vague tasks | "Add authentication" | "Create User model with email and password_hash fields" |
| Incomplete code | "Add validation function" | Full function code included |
| Missing verification | "Test it works" | `pytest tests/test_auth.py -v` → expected: 3 passed |
| Missing file paths | "Create the model file" | `src/models/user.py` |

---

## Remember

```
Bite-sized tasks (2–5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
```

**A good plan makes implementation obvious.**
