---
name: notify
description: Send desktop notifications via OSC 777. Use when the user asks to be notified on completion, or after finishing multi-step plans, large refactors, or long builds the user may have walked away from.
origin: https://github.com/mitsuhiko/agent-stuff/blob/main/pi-extensions/notify.ts
metadata:
  category: tools
---

# notify (OSC 777)

Use this skill when the user asks to be notified when work completes.

This skill starts by copying the behavior from `mitsuhiko/agent-stuff` `pi-extensions/notify.ts`: emit an OSC 777 terminal escape sequence (`notify`) with a title and body.

## Activation

Activate when asked to:
- notify on completion
- send a desktop alert when a command finishes
- add end-of-task notifications to scripts/workflows

## Terminal support (from upstream behavior)

Supported terminals:
- Ghostty
- iTerm2
- WezTerm
- rxvt-unicode

Not supported by OSC 777:
- Kitty (uses OSC 99)
- Terminal.app
- Windows Terminal
- Alacritty

## Core command

```bash
notify() {
  local title="$1"
  local body="$2"
  # OSC 777: ESC ] 777 ; notify ; title ; body BEL
  printf '\033]777;notify;%s;%s\a' "$title" "$body"
}
```

## Usage examples

```bash
notify "dotagents" "Build complete"
```

```bash
if make test; then
  notify "dotagents" "Tests passed"
else
  notify "dotagents" "Tests failed"
fi
```

## Guidance

- Notify only when asked; avoid noisy unsolicited notifications.
- Keep body text short (single sentence preferred).
- Avoid putting secrets or sensitive data in notification text.
