# openai-fast Port Design

## Goal
Port `@pi-extensions/openai-fast/` from `~/code/personal/dotfiles` into `~/code/buildr/dotagents` as a production-ready Pi extension while keeping the user-facing UX unchanged.

## Scope
This port will preserve:
- extension path: `pi-extensions/openai-fast/`
- command: `/fast [on|off|status]` with bare `/fast` toggling the current state
- flag: `--fast`
- config basename: `openai-fast.json`
- supported-model gating for fast mode
- provider payload mutation via `service_tier: "priority"`
- footer indicator behavior (`⚡`) for supported active models
- persisted fast-mode state in the global config file
- focused tests covering config resolution and core behavior

This port will adapt repo integration to `dotagents` by updating test wiring and extension documentation.

## Config Contract
Config basename: `openai-fast.json`

Config locations:
- project override file: `.pi/extensions/openai-fast.json`
- global canonical file: `~/.pi/agent/extensions/openai-fast.json`

Config shape:
```json
{
  "persistState": true,
  "active": false,
  "supportedModels": ["openai/gpt-5.4", "openai-codex/gpt-5.4"]
}
```

Rules:
- `persistState` and `active` are read from and written to the global config only.
- project config may override `supportedModels` only.
- `supportedModels` precedence is `project > global > defaults`.
- project config is resolved strictly from the current working directory at `.pi/extensions/openai-fast.json`.
- `supportedModels` is an array of `provider/modelId` strings.
- default supported models preserved from the source extension are `openai/gpt-5.4` and `openai-codex/gpt-5.4`.

## Architecture
The extension will keep the same two-file structure used in the source implementation:
- `pi-extensions/openai-fast/index.ts` for extension registration, state handling, footer patching, command/flag registration, and provider request interception
- `pi-extensions/openai-fast/config.ts` for config path resolution, config parsing, defaults, and config file reads/writes

This keeps behavior isolated and easy to test, and matches the existing multi-file extension pattern already used in `dotagents`.

## Data Flow
1. On `session_start`, the extension resolves config from the current working directory and the user home directory.
2. The global config file remains the canonical location for persisted `active` state.
3. The project config file may override supported model keys.
4. If fast mode is active and the current model is supported, the extension injects `service_tier: "priority"` into `before_provider_request` payloads.
5. The footer patch renders `⚡` inline only when fast mode is active for a supported model.
6. Bare `/fast` toggles the current fast-mode state.
7. `/fast on` persists `active: true` to the global config when `persistState` is enabled.
8. `/fast off` persists `active: false` to the global config when `persistState` is enabled.
9. On startup, persisted global `active` state is loaded first; if `--fast` is present, it overrides startup state to active for the session and also writes `active: true` back to the global config when `persistState` is enabled.
10. Project config only overrides `supportedModels`; it does not own persisted active state.

## Files
### New files
- `docs/design/2026-04-09-openai-fast-port.md`
- `pi-extensions/openai-fast/index.ts`
- `pi-extensions/openai-fast/config.ts`
- `pi-extensions/openai-fast/index.test.ts`
- `pi-extensions/openai-fast/config.test.ts`

### Modified files
- `package.json` to include the new extension tests in repo test wiring
- `README.md` to list `openai-fast` among the shipped Pi extensions and keep extension guidance current

## Error Handling
- Invalid or unreadable config files will be ignored with warning logs, matching the source behavior.
- Unsupported models will never receive the fast payload mutation or footer indicator.
- `/fast` invalid arguments will return a usage error.
- If no model is selected, status messaging will explain that state rather than attempting fast-mode application.

## State Precedence
1. Supported model list precedence is `project config > global config > defaults`.
2. Persisted active state: global config is the only canonical source.
3. Startup override: `--fast` wins over persisted startup state and writes the resulting active state back to the global config when persistence is enabled.

## Testing
Focused tests will cover:
- config resolution precedence between global and project config
- supported model parsing
- service tier payload mutation
- footer indicator string insertion behavior
- supported/unsupported state descriptions

Verification will use targeted extension tests plus repo type-checking:
- `pnpm test:ts`
- `pnpm typecheck`

## Non-Goals
- Renaming the command, extension directory, or config file
- Changing fast-mode semantics
- General refactors of unrelated Pi extension infrastructure
- Adding compatibility shims beyond the current canonical behavior
