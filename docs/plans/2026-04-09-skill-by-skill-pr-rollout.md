# Skill-by-Skill PR Rollout Implementation Plan

> REQUIRED: Use the `executing-plans` skill to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the current migration branch into reviewable PRs, with one PR per skill (at minimum), and a small set of required non-skill baseline PRs.

**Architecture:** Build each PR from `upstream/main` using cherry-picks from `main`, so every PR is isolated and clean. Use a standard per-PR loop (branch, cherry-pick, verify, push, open PR) and track completion in a manifest checklist. Keep cross-cutting changes in separate baseline PRs to avoid coupling many skills into one review.

**Tech Stack:** git, GitHub CLI (`gh`), Make (`make build`), markdown planning docs.

---

## Task 1: Prepare clean PR workflow baseline

**Files:**
- Modify: `docs/plans/2026-04-09-skill-by-skill-pr-rollout.md`
- Modify: `docs/plans/2026-04-09-skill-by-skill-pr-rollout.md` (checkbox progress only)
- Test: N/A (workflow verification via git/gh commands)

- [x] **Step 1: Fetch latest upstream and confirm divergence**

Run: `git fetch upstream --prune && git log --oneline --reverse upstream/main..main | wc -l`
Expected: command succeeds and returns a positive commit count.

- [x] **Step 2: Verify working tree is clean before branch work**

Run: `git status --short`
Expected: no output.
Observed: one untracked file (`docs/plans/2026-04-09-skill-by-skill-pr-rollout.md`) created by this plan task; no unrelated changes.

- [x] **Step 3: Confirm required tools are available**

Run: `gh --version && make --version`
Expected: both commands print installed versions.

- [x] **Step 4: Commit progress checkpoint (plan initialization)**

```bash
git add docs/plans/2026-04-09-skill-by-skill-pr-rollout.md
git commit -m "docs(plan): add skill-by-skill PR rollout plan"
```

## Task 2: Open required non-skill baseline PRs first

**Files:**
- Modify: `scripts/build.py` (via cherry-pick)
- Modify: `skill-overrides.toml` (via cherry-pick)
- Modify: `configs/AGENTS.md` (via cherry-pick)
- Delete: `skills/mcporter/SKILL.md` (via cherry-pick)
- Delete: `skills/linear/SKILL.md` (via cherry-pick)
- Create: `skills/linear-cli/SKILL.md` (via cherry-pick)
- Test: repository build output via `make build`

- [x] **Step 1: Create PR branch for build/frontmatter baseline**

Run: `git checkout -b pr/baseline-build-overrides upstream/main`
Expected: branch created from `upstream/main`.

- [x] **Step 2: Cherry-pick build baseline commit**

Run: `git cherry-pick 4f7c46f`
Expected: cherry-pick applies cleanly.

- [x] **Step 3: Verify build still works**

Run: `make build`
Expected: build succeeds.

- [x] **Step 4: Push and open PR for build baseline**
  - PR: https://github.com/buildrtech/dotagents/pull/14

Run:
```bash
git push -u origin pr/baseline-build-overrides
gh pr create --base main --head pr/baseline-build-overrides --title "feat(build): restore skill frontmatter overrides" --body "Isolates build/frontmatter override behavior required by migrated skills."
```
Expected: branch pushed and PR URL returned.

- [x] **Step 5: Create PR branch for linear skill replacement**

Run: `git checkout -b pr/skill-linear-cli upstream/main`
Expected: branch created from `upstream/main`.

- [x] **Step 6: Cherry-pick linear replacement commit**

Run: `git cherry-pick f96a8d6`
Expected: cherry-pick applies cleanly.

- [x] **Step 7: Verify build and push/open PR**
  - PR: https://github.com/buildrtech/dotagents/pull/15

Run:
```bash
make build
git push -u origin pr/skill-linear-cli
gh pr create --base main --head pr/skill-linear-cli --title "feat(skills): replace linear skill with linear-cli" --body "Replaces deprecated linear skill with linear-cli skill."
```
Expected: build succeeds and PR URL returned.

- [ ] **Step 8: Create PR branch for mcporter removal**
  - Deferred by user for now (intentionally skipped in this pass).

Run: `git checkout -b pr/skill-remove-mcporter upstream/main`
Expected: branch created from `upstream/main`.

- [ ] **Step 9: Cherry-pick mcporter removal and open PR**

Run:
```bash
git cherry-pick 7f6e6b8
make build
git push -u origin pr/skill-remove-mcporter
gh pr create --base main --head pr/skill-remove-mcporter --title "chore(skills): remove mcporter skill" --body "Removes obsolete mcporter skill from the repository."
```
Expected: build succeeds and PR URL returned.

## Task 3: Execute standard one-skill-per-PR loop for single-commit skills

**Files:**
- Modify/Create/Delete: files inside each targeted `skills/<name>/...` path via cherry-pick
- Test: `make build` per PR branch

- [ ] **Step 1: For each single-commit skill in the manifest below, run the standard PR loop exactly**

Standard loop for each skill row:
```bash
# 1) Branch from upstream/main
git checkout -b pr/skill-<name> upstream/main

# 2) Apply commit
git cherry-pick <commit>

# 3) Verify build
make build

# 4) Verify only intended scope changed
git diff --name-only upstream/main...HEAD

# 5) Push and open PR
git push -u origin pr/skill-<name>
gh pr create --base main --head pr/skill-<name> --title "<suggested-title>" --body "<short scope summary>"
```
Expected: each run ends with a PR URL and clean branch state.

- [ ] **Step 2: Complete all single-commit skill PRs in this manifest**

- [x] `buildkite-cli` — source commit `1a32e6a`
  - PR: https://github.com/buildrtech/dotagents/pull/16
- [x] `document-writing` — source commit `a7a7da5`
  - PR: https://github.com/buildrtech/dotagents/pull/17
- [x] `creating-pr` — source commit `2377d8e`
  - PR: https://github.com/buildrtech/dotagents/pull/18
- [ ] `frontend-design` — source commit `0e63d40`
- [ ] `go` — source commit `93fa9ad`
- [ ] `github` — source commit `ad929a9`
- [ ] `issue-writing` — source commit `e676ca8`
- [ ] `typescript` — source commit `5d52b64`
- [ ] `mermaid` — source commit `ef0c817`
- [ ] `notify` — source commit `c04bb1d`
- [ ] `postgres` — source commit `704c510`
- [ ] `python` — source commit `d0d088c`
- [ ] `qa-brainstorm` — source commit `d15a8b5`
- [ ] `qa-execute` — source commit `5d088f2`
- [ ] `qa-plan` — source commit `65e5e28`
- [ ] `rails` — source commit `6dbd377`
- [ ] `react` — source commit `722f55e`
- [ ] `playwright-cli` — source commit `ec0cd1a`
- [ ] `refactoring` — source commit `0397bb4`
- [ ] `remove-slop` — source commit `9ad26e1`
- [ ] `ruby` — source commit `5fe832c`
- [ ] `rust` — source commit `9a6bf83`
- [ ] `sorbet` — source commit `6ec2012`
- [ ] `sql` — source commit `62fb194`
- [ ] `summarize` — source commit `bd0bfa6`
- [ ] `tmux` — source commit `4f3c215`
- [ ] `ast-grep` — source commit `a64cec9`
- [ ] `branch-quiz` — source commit `9414ed6`
- [ ] `fetch-ci-build` — source commit `b2b0ae5`
- [ ] `semantic-commit` — source commit `33a0b36`
- [ ] `sentry-issue` — source commit `4c2da1f`
- [ ] `systematic-debugging` — source commit `79995d2`
- [ ] `verification-before-completion` — source commit `ef02f00`

- [ ] **Step 3: Commit progress checkpoint (single-commit manifest complete)**

```bash
git add docs/plans/2026-04-09-skill-by-skill-pr-rollout.md
git commit -m "docs(plan): mark single-commit skill PR checklist progress"
```

## Task 4: Execute multi-commit skill PRs

**Files:**
- Modify/Create/Delete: targeted skill files per PR branch via cherry-pick
- Test: `make build` per PR branch

- [ ] **Step 1: Create and open brave-search PR (2 commits)**

Run:
```bash
git checkout -b pr/skill-brave-search upstream/main
git cherry-pick 786eb42 accc595
make build
git push -u origin pr/skill-brave-search
gh pr create --base main --head pr/skill-brave-search --title "feat(skills): add brave-search skill" --body "Adds a dedicated brave-search skill with merged follow-up adjustments and usage guidance."
```
Expected: PR URL returned.

- [ ] **Step 2: Create and open receiving-code-review PR (2 commits)**

Run:
```bash
git checkout -b pr/skill-receiving-code-review upstream/main
git cherry-pick 69d559e 78edf0b
make build
git push -u origin pr/skill-receiving-code-review
gh pr create --base main --head pr/skill-receiving-code-review --title "docs(skills): strengthen receiving-code-review execution gates" --body "Adds explicit analyze-vs-implement confirmation guidance and tighter review-response workflow."
```
Expected: PR URL returned.

- [ ] **Step 3: Create and open writing-plans PR (3 commits)**

Run:
```bash
git checkout -b pr/skill-writing-plans upstream/main
git cherry-pick 610ec43 c946dc8 5b13da4
make build
git push -u origin pr/skill-writing-plans
gh pr create --base main --head pr/skill-writing-plans --title "docs(skills): tighten writing-plans execution semantics" --body "Refines planning guidance, language-specific references, and executable-only checkbox rules."
```
Expected: PR URL returned.

- [ ] **Step 4: Create and open executing-plans PR (2 commits)**

Run:
```bash
git checkout -b pr/skill-executing-plans upstream/main
git cherry-pick 610ec43 5b13da4
make build
git push -u origin pr/skill-executing-plans
gh pr create --base main --head pr/skill-executing-plans --title "docs(skills): enforce executable-only task handling in executing-plans" --body "Adds strict handling for executable vs deferred plan sections and optional-checkbox rejection."
```
Expected: PR URL returned.

- [ ] **Step 5: Create and open brainstorming PR (2 commits)**

Run:
```bash
git checkout -b pr/skill-brainstorming upstream/main
git cherry-pick 4c17415 610ec43
make build
git push -u origin pr/skill-brainstorming
gh pr create --base main --head pr/skill-brainstorming --title "fix(skills): refine brainstorming flow and planning handoff" --body "Fixes brainstorming skill and aligns design-to-planning handoff expectations."
```
Expected: PR URL returned.

- [ ] **Step 6: Commit progress checkpoint (multi-commit skills complete)**

```bash
git add docs/plans/2026-04-09-skill-by-skill-pr-rollout.md
git commit -m "docs(plan): mark multi-commit skill PR checklist progress"
```

## Task 5: Final verification and handoff summary

**Files:**
- Modify: `docs/plans/2026-04-09-skill-by-skill-pr-rollout.md` (final checkboxes + PR links)
- Test: git/gh verification commands

- [ ] **Step 1: Verify all PR branches are pushed**

Run: `git branch --list 'pr/*'`
Expected: all planned `pr/*` branches are listed.

- [ ] **Step 2: Verify open PR inventory**

Run: `gh pr list --limit 200 --author @me --state open`
Expected: all created PRs are visible.

- [ ] **Step 3: Add PR URLs under each checklist item in this plan**

Run: manually edit this plan file and append each PR link under its corresponding skill checklist entry.
Expected: every completed item has a PR URL.

- [ ] **Step 4: Commit final rollout status**

```bash
git add docs/plans/2026-04-09-skill-by-skill-pr-rollout.md
git commit -m "docs(plan): record skill-by-skill PR rollout status"
```

## Follow-ups

- After baseline and skill PRs merge, decide whether to open a separate docs-only PR for older planning artifacts currently in `docs/plans/`.
