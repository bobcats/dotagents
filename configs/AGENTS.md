# Global Agent Guidelines

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
