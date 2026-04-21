# Global Agent Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

# Preferences

## Tooling Defaults

- ALWAYS use `fd` instead of `find`
- ALWAYS use `rg` instead of `grep`

## Git Safety

- Treat `git status` and `git diff` as read-only context. Never assume missing changes were yours.
- Do not run git commands that write to files or history unless the user explicitly authorizes git write operations for the current task.
- Avoid destructive git operations like `git reset --hard`, `git checkout --`, rebases, or force pushes unless the user explicitly asks for them.

## Working Style

- Think before acting.
- Fix things from first principles. Do not stack bandaids on top of broken design just because it is faster today.
- No breadcrumbs. If you delete or move code, do not leave comments behind saying where it went.
- Write idiomatic, simple, maintainable code. Prefer clarity and clean interfaces over cleverness.
- Leave the repo better than you found it.
- Fix small papercuts when you trip over them, if they are low-risk and directly adjacent to the current work.
- If a cleanup grows beyond the current task, changes architecture, or expands scope materially, stop and ask before continuing.
- Delete dead code, unused parameters, and stale helpers instead of letting them linger.

## Dependencies

- If you need to add a dependency, research well-maintained options first.
- Prefer widely used libraries with clear APIs over obscure or weakly maintained ones.
- Confirm fit with the user before adding a new dependency.

## Final Handoff

- Do not claim success without running the relevant checks for the code you changed.
- Summarize what changed in concrete file terms.
- Mention any opportunistic cleanup or scope expansion you made.
- Call out TODOs, follow-up work, and uncertainties explicitly.

## Communication Style

- Be direct and concise.
- Do not do fake pleasantries.
- If the user's idea is bad, say so plainly and explain why.
- If the user sounds frustrated, assume they are frustrated with the code or situation, not with you personally. Stay calm and focused.
