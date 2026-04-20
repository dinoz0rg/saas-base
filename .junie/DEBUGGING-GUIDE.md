# Systematic Debugging Guide

Compiled from hermes-agent systematic-debugging skill and Karpathy principles. Root-cause-first methodology.

---

## Core Rule

**NO fixes without root cause investigation first.**

If you catch yourself thinking "just try this and see" — STOP. That's guessing, not debugging.

---

## Phase 1: Investigate

1. **Read error messages carefully** — don't skip past them, they often contain the answer
2. **Reproduce consistently** — if you can't trigger it reliably, gather more data, don't guess
3. **Check recent changes** — git diff, recent commits, new dependencies
4. **Trace data flow** — where does the bad value originate? Keep tracing upstream until you find the source

---

## Phase 2: Analyze Patterns

- Find working examples of similar code in the codebase
- Compare working vs broken — list every difference, however small
- Don't assume "that can't matter"
- Check logs, stack traces, and system state at the point of failure

---

## Phase 3: Hypothesis & Test

- Form a single, specific hypothesis: "I think X is the root cause because Y"
- Make the SMALLEST possible change to test it — one variable at a time
- If it didn't work, form a NEW hypothesis — don't pile fixes on top of each other
- Document each hypothesis and result

---

## Phase 4: Fix

1. Create a failing test that reproduces the bug
2. Implement a single fix addressing the root cause
3. Verify: reproduction test passes, full suite passes
4. Check for similar patterns elsewhere in the codebase

---

## Rule of Three

If 3+ fix attempts fail, **STOP**:
- Question the architecture
- Re-examine your assumptions
- Discuss with the user before attempting more fixes

---

## Red Flags — Return to Phase 1

Stop and restart investigation if you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "I don't fully understand but this might work"
- "It works on my machine"
- "Let me add a try/catch around it"

---

## Debugging Decision Tree

```
Error occurs
  ├── Can reproduce? 
  │   ├── YES → Trace data flow → Find root cause → Fix
  │   └── NO → Add logging/monitoring → Gather more data → Retry
  ├── Error message clear?
  │   ├── YES → Follow the message → Verify fix
  │   └── NO → Check logs → Check stack trace → Binary search
  └── Recent change caused it?
      ├── YES → git bisect or diff → Identify exact change → Fix
      └── NO → Check environment → Check dependencies → Check data
```

---

## Common Bug Categories

| Category | Investigation Approach |
|----------|----------------------|
| Off-by-one | Check loop bounds, array indices, range endpoints |
| Null/undefined | Trace where value should be set, check all paths |
| Race condition | Add logging with timestamps, check async ordering |
| State corruption | Track all mutations, check concurrent access |
| Type mismatch | Check implicit conversions, strict equality |
| Resource leak | Check open/close pairs, error path cleanup |
| Encoding issue | Check charset at every boundary (file, network, DB) |

---

## Verification Checklist

After fixing a bug:

- [ ] Root cause identified and documented
- [ ] Failing test reproduces the original bug
- [ ] Fix addresses root cause (not symptoms)
- [ ] Reproduction test now passes
- [ ] Full test suite passes
- [ ] No new warnings or errors introduced
- [ ] Similar patterns checked elsewhere in codebase
