# Pi Migration Selective Port Implementation Plan

> REQUIRED: Use the `executing-plans` skill to implement this plan task-by-task.

**Goal:** Selectively port high-value changes from `brian/pi-migration` onto current `main` in small, reviewable PRs.

**Current status (2026-04-07):**
- ✅ PR-1 merged: restore `skill-overrides` support — https://github.com/bobcats/dotagents/pull/1
- ✅ PR-2 merged: superpower skill guidance port — https://github.com/bobcats/dotagents/pull/2
- ✅ Catalog actions done on `main`: add `brave-search`, remove `mcporter`

---

### Task 1: Baseline Diff Inventory and Concept Buckets

- [x] **Step 1: Capture branch delta summary**
- [x] **Step 2: Bucket changes into concepts**
- [x] **Step 3: Freeze scope for first PR**
- [x] **Step 4: Commit planning artifact**

### Task 2: PR-1 Restore `skill-overrides` Support (from PR #10)

- [x] **Step 1: Create clean port branch**
- [x] **Step 2: Port PR #10 behavior exactly**
- [x] **Step 3: Add default overrides file**
- [x] **Step 4: Verify build path** (`mise exec python@3.11 -- make build`)
- [x] **Step 5: Manual override smoke test**
- [x] **Step 6: Commit + PR + merge** (PR #1)

### Task 3: PR-2 Superpower Skill Ports (High-Value Subset)

Files ported:
- `skills/brainstorming/SKILL.md`
- `skills/writing-plans/SKILL.md`
- `skills/executing-plans/SKILL.md`
- `skills/code-review/SKILL.md`
- `skills/test-driven-development/SKILL.md`

- [x] **Step 1: Start branch**
- [x] **Step 2: Port selected skill edits only**
- [x] **Step 3: Verify build** (`mise exec python@3.11 -- make build`)
- [x] **Step 4: Commit + PR + merge** (PR #2)

### Task 4: PR-3 Catalog-Level Changes (Optional, Explicitly Scoped)

- [x] **Step 1: Decide inclusion list explicitly**
  - Included now: `brave-search` add, `mcporter` remove
- [x] **Step 2: Port one concept at a time**
  - Done as two focused changes on `main`
- [x] **Step 3: Verify install/build experience**
  - `mise exec python@3.11 -- make build` passes after both changes
- [x] **Step 4: Commit changes**

### Task 5: Exclusions and Guardrails

- [x] **Step 1: Keep PRs product-focused**
- [x] **Step 2: Run branch hygiene checks before PRs**
- [x] **Step 3: Include verification evidence in PR descriptions**

---

## Concept Chunking Summary

- [x] **Concept A — Build infrastructure** (`skill-overrides`)
- [x] **Concept B — Superpower workflow quality**
- [x] **Concept C — Catalog expansion/adoption** (`brave-search`)
- [x] **Concept D — Catalog cleanup/deprecations** (`mcporter` removal)
- [ ] **Concept E — Historical experiments/docs** (intentionally not ported)

---

## Remaining Work

No required migration work remains from the scoped plan. 
If desired, next phase can evaluate additional optional skill adoptions from `brian/pi-migration` one-by-one.
