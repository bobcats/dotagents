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

- [ ] **Step 1: Create PR branch for build/frontmatter baseline**

Run: `git checkout -b pr/baseline-build-overrides upstream/main`
Expected: branch created from `upstream/main`.

- [ ] **Step 2: Cherry-pick build baseline commit**

Run: `git cherry-pick 4f7c46f`
Expected: cherry-pick applies cleanly.

- [ ] **Step 3: Verify build still works**

Run: `make build`
Expected: build succeeds.

- [ ] **Step 4: Push and open PR for build baseline**

Run:
```bash
git push -u origin pr/baseline-build-overrides
gh pr create --base main --head pr/baseline-build-overrides --title "feat(build): restore skill frontmatter overrides" --body "Isolates build/frontmatter override behavior required by migrated skills."
```
Expected: branch pushed and PR URL returned.

- [ ] **Step 5: Create PR branch for linear skill replacement**

Run: `git checkout -b pr/skill-linear-cli upstream/main`
Expected: branch created from `upstream/main`.

- [ ] **Step 6: Cherry-pick linear replacement commit**

Run: `git cherry-pick f96a8d6`
Expected: cherry-pick applies cleanly.

- [ ] **Step 7: Verify build and push/open PR**

Run:
```bash
make build
git push -u origin pr/skill-linear-cli
gh pr create --base main --head pr/skill-linear-cli --title "feat(skills): replace linear skill with linear-cli" --body "Replaces deprecated linear skill with linear-cli skill."
```
Expected: build succeeds and PR URL returned.

- [ ] **Step 8: Create PR branch for mcporter removal**

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

- [ ] `buildkite-cli` — `1a32e6a` — `feat(skills): port buildkite-cli skill from pi-migration`
- [ ] `document-writing` — `a7a7da5` — `feat(skills): port document-writing skill from pi-migration`
- [ ] `creating-pr` — `2377d8e` — `feat(skills): port creating-pr skill from pi-migration`
- [ ] `frontend-design` — `0e63d40` — `feat(skills): port frontend-design skill from pi-migration`
- [ ] `go` — `93fa9ad` — `feat(skills): port go skill from pi-migration`
- [ ] `github` — `ad929a9` — `feat(skills): port github skill from pi-migration`
- [ ] `issue-writing` — `e676ca8` — `feat(skills): port issue-writing skill from pi-migration`
- [ ] `typescript` — `5d52b64` — `feat(skills): port typescript skill from pi-migration`
- [ ] `mermaid` — `ef0c817` — `feat(skills): port mermaid skill from pi-migration`
- [ ] `notify` — `c04bb1d` — `feat(skills): port notify skill from pi-migration`
- [ ] `postgres` — `704c510` — `feat(skills): port postgres skill from pi-migration`
- [ ] `python` — `d0d088c` — `feat(skills): port python skill from pi-migration`
- [ ] `qa-brainstorm` — `d15a8b5` — `feat(skills): port qa-brainstorm skill from pi-migration`
- [ ] `qa-execute` — `5d088f2` — `feat(skills): port qa-execute skill from pi-migration`
- [ ] `qa-plan` — `65e5e28` — `feat(skills): port qa-plan skill from pi-migration`
- [ ] `rails` — `6dbd377` — `feat(skills): port rails skill from pi-migration`
- [ ] `react` — `722f55e` — `feat(skills): port react skill from pi-migration`
- [ ] `playwright-cli` — `ec0cd1a` — `feat(skills): port playwright-cli skill from pi-migration`
- [ ] `refactoring` — `0397bb4` — `feat(skills): port refactoring skill from pi-migration`
- [ ] `remove-slop` — `9ad26e1` — `feat(skills): port remove-slop skill from pi-migration`
- [ ] `ruby` — `5fe832c` — `feat(skills): port ruby skill from pi-migration`
- [ ] `rust` — `9a6bf83` — `feat(skills): port rust skill from pi-migration`
- [ ] `sorbet` — `6ec2012` — `feat(skills): port sorbet skill from pi-migration`
- [ ] `sql` — `62fb194` — `feat(skills): port sql skill from pi-migration`
- [ ] `summarize` — `bd0bfa6` — `feat(skills): port summarize skill from pi-migration`
- [ ] `tmux` — `4f3c215` — `feat(skills): port tmux skill from pi-migration`
- [ ] `ast-grep` — `a64cec9` — `feat(skills): update ast-grep skill from pi-migration`
- [ ] `branch-quiz` — `9414ed6` — `feat(skills): update branch-quiz skill from pi-migration`
- [ ] `fetch-ci-build` — `b2b0ae5` — `feat(skills): update fetch-ci-build skill from pi-migration`
- [ ] `semantic-commit` — `33a0b36` — `feat(skills): update semantic-commit skill from pi-migration`
- [ ] `sentry-issue` — `4c2da1f` — `feat(skills): update sentry-issue skill and helper scripts from pi-migration`
- [ ] `systematic-debugging` — `79995d2` — `feat(skills): update systematic-debugging skill from pi-migration`
- [ ] `verification-before-completion` — `ef02f00` — `feat(skills): update verification-before-completion skill from pi-migration`

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
gh pr create --base main --head pr/skill-brave-search --title "feat(skills): port and merge brave-search skill" --body "Ports brave-search skill and follow-up merge adjustments from pi-migration."
```
Expected: PR URL returned.

- [ ] **Step 2: Create and open receiving-code-review PR (2 commits)**

Run:
```bash
git checkout -b pr/skill-receiving-code-review upstream/main
git cherry-pick 69d559e 78edf0b
make build
git push -u origin pr/skill-receiving-code-review
gh pr create --base main --head pr/skill-receiving-code-review --title "docs(skills): strengthen receiving-code-review execution gates" --body "Includes pi-migration update plus explicit analyze-vs-implement confirmation guidance."
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

- After baseline and skill PRs merge, decide whether to open a separate docs-only PR for migration planning artifacts:
  - `docs/plans/2026-04-06-pi-migration-selective-port.md`
  - `docs/plans/2026-04-07-full-skill-parity-from-pi-migration.md`
