# Precompiled Junie Guidelines

Best-of-the-best guidelines compiled from 5 skill collections: Karpathy, Claude Best Practices, Claude Skills, DeerFlow, and Hermes Agent. Optimized for Junie (JetBrains) with Claude Opus 4.6.

---

## Files

| File | Lines | Source | What It Covers |
|------|-------|--------|----------------|
| **AGENTS.md** | 180 | All sources | Core behavioral guidelines: think first, simplicity, surgical changes, goal-driven execution, debugging, planning, research, context management, communication, quality standards |
| **TDD-GUIDE.md** | 149 | hermes-agent, claude-skills | Red-green-refactor cycle, iron law of TDD, coverage priorities, rationalizations table, when-stuck guide |
| **DEBUGGING-GUIDE.md** | 113 | hermes-agent, karpathy | 4-phase systematic debugging, rule of three, decision tree, common bug categories |
| **CODE-REVIEW-CHECKLIST.md** | 178 | claude-skills | Full review checklist: correctness, security, performance, maintainability, testing, language-specific checks, review verdicts |
| **ANTIPATTERNS.md** | 186 | claude-skills | Structural, logic, security, performance, and testing antipatterns with code examples and fixes, quality thresholds |
| **ARCHITECTURE-GUIDE.md** | 171 | claude-skills | Database selection, architecture patterns, monolith vs microservices, ADR template, assessment checklist, tech stack reference |
| **RESEARCH-METHODOLOGY.md** | 125 | deer-flow | 4-phase deep research methodology, search strategies, temporal awareness, quality bar |
| **PLANNING-GUIDE.md** | 154 | hermes-agent | Implementation planning, bite-sized tasks, plan document structure, writing process, common mistakes |
| **GITHUB-WORKFLOW.md** | 193 | hermes-agent | PR lifecycle, branch/commit conventions, CI monitoring, issues management, code review commands |

**Total: 9 files, ~1,450 lines of actionable guidelines.**

---

## How to Use

- **AGENTS.md** → Load always. Core principles for every task.
- **TDD-GUIDE.md** → Load when writing or fixing code with tests.
- **DEBUGGING-GUIDE.md** → Load when investigating bugs or failures.
- **CODE-REVIEW-CHECKLIST.md** → Load when reviewing code or PRs.
- **ANTIPATTERNS.md** → Load when refactoring or improving code quality.
- **ARCHITECTURE-GUIDE.md** → Load when designing systems or making tech decisions.
- **RESEARCH-METHODOLOGY.md** → Load when researching topics or generating content.
- **PLANNING-GUIDE.md** → Load when planning multi-step features or writing implementation plans.
- **GITHUB-WORKFLOW.md** → Load when working with GitHub PRs, issues, branches, or code review.

---

## Sources

- `andrej/` — Karpathy's 4 core coding principles
- `claude-code-best-practice/` — Claude Code workflows and best practices
- `claude-skills/` — 48+ engineering, product, and business skills
- `deer-flow/` — Deep research and analysis methodology
- `hermes-agent/` — Software development skills (TDD, debugging, planning)
