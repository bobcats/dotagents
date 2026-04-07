# Full Skill Parity from `brian/pi-migration` Implementation Plan

> REQUIRED: Use the `executing-plans` skill to implement this plan task-by-task.

**Goal:** Reconcile `origin/main` with `brian/pi-migration` skill-by-skill until every skill delta is intentionally resolved.

**Architecture:** Execute one skill at a time on short-lived branches. For each skill: inspect diff, port/add/remove, run build verification, commit, open PR to fork, merge, then continue.

**Tech Stack:** git, GitHub PRs, `make build`, `mise exec python@3.11 -- make build`.

---

## Phase 0 — Rules and Guardrails

- [ ] **Step 1: Treat each skill as an isolated unit of work**

For each skill, use a dedicated branch name: `feat/port-skill-<name>` or `chore/resolve-skill-<name>`.

- [ ] **Step 2: Verify after every skill**

Run:
```bash
mise exec python@3.11 -- make build
```
Expected: build succeeds.

- [ ] **Step 3: Keep PR scope single-skill**

Before opening each PR, run:
```bash
git diff --name-only origin/main...HEAD
git status --short
```
Expected: only the target skill files (plus any required minimal metadata/docs).

---

## Phase 1 — Skills Missing on `main` (Add from `brian/pi-migration`)

### Task 1: `buildkite-cli` (ADD)
- [ ] Inspect: `git diff --name-status origin/main...brian/pi-migration -- skills/buildkite-cli`
- [ ] Port: `git checkout brian/pi-migration -- skills/buildkite-cli`
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 2: `creating-pr` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 3: `document-writing` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 4: `frontend-design` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 5: `github` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 6: `go` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 7: `issue-writing` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 8: `linear-cli` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 9: `mermaid` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 10: `notify` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 11: `playwright-cli` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 12: `postgres` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 13: `python` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 14: `qa-brainstorm` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 15: `qa-execute` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 16: `qa-plan` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 17: `rails` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 18: `react` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 19: `refactoring` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 20: `remove-slop` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 21: `ruby` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 22: `rust` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 23: `sorbet` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 24: `sql` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 25: `summarize` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 26: `tmux` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 27: `typescript` (ADD)
- [ ] Inspect
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

---

## Phase 2 — Skills Present on Both but Different (Update `main` to match)

### Task 28: `ast-grep` (UPDATE)
- [ ] Compare: `git diff origin/main...brian/pi-migration -- skills/ast-grep`
- [ ] Port selected diff (or full dir)
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 29: `branch-quiz` (UPDATE)
- [ ] Compare
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 30: `fetch-ci-build` (UPDATE)
- [ ] Compare
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 31: `receiving-code-review` (UPDATE)
- [ ] Compare
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 32: `semantic-commit` (UPDATE)
- [ ] Compare
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 33: `sentry-issue` (UPDATE)
- [ ] Compare
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 34: `systematic-debugging` (UPDATE)
- [ ] Compare
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 35: `verification-before-completion` (UPDATE)
- [ ] Compare
- [ ] Port
- [ ] Verify build
- [ ] Commit + PR + merge

---

## Phase 3 — Skills Present on `main` but Not in `brian/pi-migration` (Explicit Decision)

### Task 36: `dispatching-parallel-agents` (DECIDE keep/remove)
- [ ] Confirm intent: keep as deliberate divergence OR remove for strict parity
- [ ] Apply decision
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 37: `linear` (DECIDE keep/remove)
- [ ] Confirm intent
- [ ] Apply decision
- [ ] Verify build
- [ ] Commit + PR + merge

### Task 38: `requesting-code-review` (DECIDE keep/remove)
- [ ] Confirm intent
- [ ] Apply decision
- [ ] Verify build
- [ ] Commit + PR + merge

---

## Completion Criteria

- [ ] Every Task 1–38 checked off
- [ ] `git diff --name-only origin/main...brian/pi-migration -- skills` is either empty or contains only explicitly approved divergences
- [ ] All merged to `origin/main`
- [ ] Final summary committed to plan file
