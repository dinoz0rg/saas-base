# GitHub Workflow Guide

Consolidated from Hermes Agent GitHub skills (PR workflow, issues, code review, repo management, auth). Adapted for Junie.

---

## Authentication

Before any GitHub operation, detect available auth:

```bash
# Prefer gh CLI; fall back to GITHUB_TOKEN + curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"  # Requires GITHUB_TOKEN env var
fi
```

Extract owner/repo from remote:
```bash
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## Branch & Commit Conventions

### Branch Naming
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

### Commit Messages (Conventional Commits)
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```
Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

---

## Pull Request Lifecycle

### 1. Create Branch
```bash
git fetch origin
git checkout main && git pull origin main
git checkout -b feat/my-feature
```

### 2. Commit Changes
```bash
git add src/file.py tests/test_file.py
git commit -m "feat: add feature description"
```

### 3. Push & Create PR

```bash
git push -u origin HEAD

# With gh:
gh pr create --title "feat: description" --body "## Summary\n- What changed\n\nCloses #42"

# With curl:
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d '{"title":"feat: description","body":"Closes #42","head":"BRANCH","base":"main"}'
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`

### 4. Monitor CI

```bash
# With gh:
gh pr checks --watch

# With curl:
SHA=$(git rev-parse HEAD)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status
```

### 5. Auto-Fix CI Failures

Loop (max 3 attempts, then ask user):
1. Check CI status → identify failures
2. Read failure logs (`gh run view <ID> --log-failed`)
3. Fix the code
4. `git add . && git commit -m "fix: resolve CI failure" && git push`
5. Re-check CI status

### 6. Merge

```bash
# With gh (squash merge + delete branch):
gh pr merge --squash --delete-branch

# Enable auto-merge:
gh pr merge --auto --squash --delete-branch
```

---

## Issues Management

### Create Issue
```bash
# With gh:
gh issue create --title "Bug: description" --body "Steps to reproduce..." --label "bug"

# With curl:
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues \
  -d '{"title":"Bug: description","body":"Steps...","labels":["bug"]}'
```

### Search & List Issues
```bash
gh issue list --state open --label "bug"
gh issue list --assignee @me
gh issue view 42
```

### Close with PR Reference
Link PRs to issues using `Closes #N`, `Fixes #N`, or `Resolves #N` in PR body or commit message.

---

## Code Review

### Review Local Changes (Pre-Push)
```bash
# Review your own diff before pushing
git diff --stat
git diff              # unstaged
git diff --cached     # staged

# Check for common issues
git diff --check      # whitespace errors
```

### Review a PR
```bash
# With gh:
gh pr diff 42
gh pr review 42 --approve
gh pr review 42 --request-changes --body "Issue: ..."
gh pr review 42 --comment --body "Suggestion: ..."

# Leave inline comment:
gh api repos/$OWNER/$REPO/pulls/42/comments \
  -f body="Consider using X instead" \
  -f path="src/file.py" \
  -F line=25 \
  -f commit_id="$(gh pr view 42 --json headRefOid -q .headRefOid)"
```

### Review Checklist
When reviewing, check for:
- Correctness — does it do what it claims?
- Tests — are edge cases covered?
- Security — no secrets, SQL injection, XSS?
- Performance — no N+1 queries, unnecessary loops?
- Style — matches existing codebase conventions?

See `CODE-REVIEW-CHECKLIST.md` for the full checklist.

---

## Quick Reference

| Action | gh CLI | curl fallback |
|--------|--------|---------------|
| List my PRs | `gh pr list --author @me` | `curl .../pulls?state=open` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` |
| Add PR comment | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments` |
| Request review | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers` |
| Close PR | `gh pr close N` | `curl -X PATCH .../pulls/N` |
| Check out PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |
| List issues | `gh issue list` | `curl .../issues?state=open` |
| Create issue | `gh issue create --title "..."` | `curl -X POST .../issues` |
