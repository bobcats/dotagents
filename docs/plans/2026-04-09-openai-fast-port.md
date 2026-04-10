# openai-fast Port Implementation Plan

> REQUIRED SUB-SKILL: Use superpowers:executing-plans skill to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port `@pi-extensions/openai-fast/` into `dotagents` as a production-ready Pi extension while preserving the `/fast` UX, config contract, and fast-mode behavior.

**Architecture:** Keep the extension split into a small config module plus the extension entrypoint. Port the proven behavior from `~/code/personal/dotfiles/pi-extensions/openai-fast/`, cover the config and helper behavior with focused tests first, then wire repo integration so `dotagents` ships and verifies the extension cleanly.

**Tech Stack:** TypeScript, `@mariozechner/pi-coding-agent`, `@mariozechner/pi-tui`, Node `node:test`, `tsx`, `pnpm`, existing `scripts/build.py`

---

## File Structure

### New files
- `pi-extensions/openai-fast/config.ts` — config constants, parsing helpers, file IO, and precedence resolution for global/project config
- `pi-extensions/openai-fast/config.test.ts` — focused tests for config precedence and parsing
- `pi-extensions/openai-fast/index.ts` — `/fast` command, `--fast` flag, footer patching, provider payload mutation, a tiny injected config-IO seam for tests, and test exports
- `pi-extensions/openai-fast/index.test.ts` — focused tests for helper behavior and extension registration surface
- `docs/plans/2026-04-09-openai-fast-port.md` — this implementation plan

### Modified files
- `package.json` — run the new extension tests as part of `pnpm test:ts`
- `README.md` — document `openai-fast` in the shipped Pi extensions list and extension workflow guidance

## Task 1: Port the config contract with tests first

**Files:**
- Create: `pi-extensions/openai-fast/config.test.ts`
- Create: `pi-extensions/openai-fast/config.ts`

- [ ] **Step 1: Write the failing config tests**

```ts
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, it } from "node:test";
import { resolveFastConfig, parseSupportedModelKey } from "./config.js";

describe("openai-fast config", () => {
  it("uses the global config as canonical for persisted state and project config for supported models", () => {
    const root = mkdtempSync(join(tmpdir(), "openai-fast-config-"));
    const cwd = join(root, "project");
    const homeDir = join(root, "home");

    mkdirSync(join(homeDir, ".pi", "agent", "extensions"), { recursive: true });
    mkdirSync(join(cwd, ".pi", "extensions"), { recursive: true });

    writeFileSync(
      join(homeDir, ".pi", "agent", "extensions", "openai-fast.json"),
      JSON.stringify({ persistState: false, active: false, supportedModels: ["openai/gpt-5.4"] }),
    );
    writeFileSync(
      join(cwd, ".pi", "extensions", "openai-fast.json"),
      JSON.stringify({ persistState: true, active: true, supportedModels: ["openai/gpt-5.5"] }),
    );

    const config = resolveFastConfig(cwd, homeDir);

    assert.equal(config.persistState, false);
    assert.equal(config.active, false);
    assert.deepEqual(config.supportedModels, [{ provider: "openai", id: "gpt-5.5" }]);
  });

  it("parses provider/model keys and rejects invalid entries", () => {
    assert.deepEqual(parseSupportedModelKey("openai/gpt-5.4"), {
      provider: "openai",
      id: "gpt-5.4",
    });
    assert.equal(parseSupportedModelKey("bad"), undefined);
  });
});
```

- [ ] **Step 2: Run the config test to verify it fails**

Run: `node --import tsx --test pi-extensions/openai-fast/config.test.ts`

Expected: FAIL with `Cannot find module './config.js'` or missing export errors.

- [ ] **Step 3: Write the minimal config implementation**

Create `pi-extensions/openai-fast/config.ts` with the source extension’s config contract:

```ts
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

export const FAST_CONFIG_BASENAME = "openai-fast.json";
export const DEFAULT_SUPPORTED_MODEL_KEYS = ["openai/gpt-5.4", "openai-codex/gpt-5.4"] as const;

export interface FastSupportedModel {
  provider: string;
  id: string;
}

export interface FastConfigFile {
  persistState?: boolean;
  active?: boolean;
  supportedModels?: string[];
}

export interface ResolvedFastConfig {
  configPath: string;
  persistState: boolean;
  active: boolean | undefined;
  supportedModels: FastSupportedModel[];
}

export const DEFAULT_CONFIG_FILE: FastConfigFile = {
  persistState: true,
  active: false,
  supportedModels: [...DEFAULT_SUPPORTED_MODEL_KEYS],
};

export function getConfigPaths(cwd: string, homeDir: string = homedir()) {
  return {
    projectConfigPath: join(cwd, ".pi", "extensions", FAST_CONFIG_BASENAME),
    globalConfigPath: join(homeDir, ".pi", "agent", "extensions", FAST_CONFIG_BASENAME),
  };
}

export function parseSupportedModelKey(value: string): FastSupportedModel | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const slashIndex = trimmed.indexOf("/");
  if (slashIndex <= 0 || slashIndex >= trimmed.length - 1) return undefined;

  const provider = trimmed.slice(0, slashIndex).trim();
  const id = trimmed.slice(slashIndex + 1).trim();
  if (!provider || !id) return undefined;
  return { provider, id };
}
```

Then finish the file with the source implementation’s helpers:
- `parseSupportedModels()`
- `readConfigFile()`
- `writeConfigFile()`
- `resolveFastConfig()`
- `ensureGlobalConfigFile()`

Keep the exact precedence from the spec: `project supportedModels > global supportedModels > defaults`, while `persistState` and `active` remain global-only.

- [ ] **Step 4: Run the config test to verify it passes**

Run: `node --import tsx --test pi-extensions/openai-fast/config.test.ts`

Expected: PASS

- [ ] **Step 5: Add one more focused regression test before moving on**

Extend `pi-extensions/openai-fast/config.test.ts` with a test that verifies `resolveFastConfig()` creates the global config file on first use and falls back to the default supported models when neither config provides `supportedModels`.

Run: `node --import tsx --test pi-extensions/openai-fast/config.test.ts`

Expected: PASS

- [ ] **Step 6: Commit the config slice**

```bash
git add pi-extensions/openai-fast/config.ts pi-extensions/openai-fast/config.test.ts
git commit -m "feat: port openai-fast config"
```

## Task 2: Port the fast-mode helpers and extension surface with tests first

**Files:**
- Create: `pi-extensions/openai-fast/index.test.ts`
- Create: `pi-extensions/openai-fast/index.ts`
- Read for reference only: `/Users/mikeastock/code/personal/dotfiles/pi-extensions/openai-fast/index.ts`

- [ ] **Step 1: Write the failing helper and registration tests**

Create `pi-extensions/openai-fast/index.test.ts` with focused behavior tests:

```ts
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { visibleWidth } from "@mariozechner/pi-tui";
import openaiFast, { _test } from "./index.js";

describe("openai-fast helpers", () => {
  it("builds footer right-side candidates with thinking level", () => {
    assert.deepEqual(
      _test.buildFooterRightSideCandidates(
        { provider: "openai-codex", id: "gpt-5.4", reasoning: true } as any,
        "medium",
      ),
      ["(openai-codex) gpt-5.4 • medium", "gpt-5.4 • medium"],
    );
  });

  it("injects the fast indicator without changing footer width", () => {
    const originalLine = "cwd branch                      (openai-codex) gpt-5.4 • medium";
    const updatedLine = _test.injectFastIntoFooterLine(
      originalLine,
      { provider: "openai-codex", id: "gpt-5.4", reasoning: true } as any,
      "medium",
      "⚡",
    );

    assert.equal(updatedLine, "cwd branch                 (openai-codex) gpt-5.4 • medium • ⚡");
    assert.equal(visibleWidth(updatedLine), visibleWidth(originalLine));
  });

  it("adds priority service tier to provider payloads", () => {
    assert.deepEqual(_test.applyFastServiceTier({ model: "gpt-5.4" }), {
      model: "gpt-5.4",
      service_tier: "priority",
    });
  });

  it("describes unsupported active state", () => {
    assert.equal(
      _test.describeCurrentState(
        { model: { provider: "openai", id: "gpt-4.1" } as any },
        true,
        [{ provider: "openai", id: "gpt-5.4" }],
      ),
      "Fast mode is on, but openai/gpt-4.1 does not support it. Supported models: openai/gpt-5.4.",
    );
  });
});

describe("openai-fast extension registration", () => {
  it("registers the fast flag, command, and lifecycle hooks", () => {
    const flags: string[] = [];
    const commands: string[] = [];
    const events: string[] = [];

    openaiFast({
      registerFlag(name: string) {
        flags.push(name);
      },
      registerCommand(name: string) {
        commands.push(name);
      },
      on(name: string) {
        events.push(name);
      },
      getFlag() {
        return false;
      },
    } as any);

    assert.deepEqual(flags, ["fast"]);
    assert.deepEqual(commands, ["fast"]);
    assert.deepEqual(events.sort(), [
      "before_provider_request",
      "model_select",
      "session_shutdown",
      "session_start",
    ]);
  });
});
```

- [ ] **Step 2: Run the helper test to verify it fails**

Run: `node --import tsx --test pi-extensions/openai-fast/index.test.ts`

Expected: FAIL with `Cannot find module './index.js'` or missing export errors.

- [ ] **Step 3: Port the extension entrypoint minimally**

Create `pi-extensions/openai-fast/index.ts` with the same structure as the source extension:

```ts
import { FooterComponent, type ExtensionAPI, type ExtensionContext } from "@mariozechner/pi-coding-agent";
import { truncateToWidth, visibleWidth } from "@mariozechner/pi-tui";
import {
  DEFAULT_CONFIG_FILE,
  DEFAULT_SUPPORTED_MODEL_KEYS,
  FAST_CONFIG_BASENAME,
  getConfigPaths,
  parseSupportedModelKey,
  parseSupportedModels,
  readConfigFile,
  resolveFastConfig,
  writeConfigFile,
  type FastSupportedModel,
  type ResolvedFastConfig,
} from "./config.js";

const FAST_COMMAND = "fast";
const FAST_FLAG = "fast";
const FAST_COMMAND_ARGS = ["on", "off", "status"] as const;
const FAST_SERVICE_TIER = "priority";
```

Implement the helper functions and extension wiring from the source file:
- `isFastSupportedModel()`
- `describeSupportedModels()`
- `describeCurrentState()`
- `getFastIndicator()`
- `buildFooterRightSideCandidates()`
- `injectFastIntoFooterLine()`
- footer patch/unpatch helpers
- `applyFastServiceTier()`
- `createOpenaiFastExtension(configApi = { resolveFastConfig, readConfigFile, writeConfigFile })` so tests can inject temp config behavior without touching the real home directory
- default export as `createOpenaiFastExtension()` registering `--fast`, `/fast`, `before_provider_request`, `session_start`, `model_select`, and `session_shutdown`
- `_test` export exposing the helper functions/constants used by the tests

Keep the runtime semantics unchanged:
- bare `/fast` toggles
- `/fast on|off|status` behaves exactly like the source extension
- `--fast` enables fast mode on startup and persists `active: true` when persistence is enabled
- provider payloads only change when fast mode is active and the current model is supported
- invalid config stays warning-only, not fatal

- [ ] **Step 4: Run the helper and config tests to verify they pass**

Run:
- `node --import tsx --test pi-extensions/openai-fast/index.test.ts`
- `node --import tsx --test pi-extensions/openai-fast/config.test.ts`

Expected: PASS for both

- [ ] **Step 5: Add focused regression tests for unsupported models and startup override**

Add these tests to `pi-extensions/openai-fast/index.test.ts`:

```ts
it("does not render the fast indicator for unsupported models", () => {
  assert.equal(
    _test.getFastIndicator(
      {
        model: { provider: "openai", id: "gpt-4.1" } as any,
        ui: { theme: { fg: (_color: string, text: string) => `[${_color}]${text}` } },
      } as any,
      true,
      [{ provider: "openai", id: "gpt-5.4" }],
    ),
    undefined,
  );
});

it("--fast overrides persisted startup state and writes active true back to global config", async () => {
  const notifications: string[] = [];
  const writes: Array<{ path: string; config: unknown }> = [];
  let sessionStartHandler: ((event: unknown, ctx: any) => Promise<void>) | undefined;

  const extension = _test.createOpenaiFastExtension({
    resolveFastConfig() {
      return {
        configPath: "/tmp/home/.pi/agent/extensions/openai-fast.json",
        persistState: true,
        active: false,
        supportedModels: [{ provider: "openai", id: "gpt-5.4" }],
      };
    },
    readConfigFile() {
      return { persistState: true, active: false, supportedModels: ["openai/gpt-5.4"] };
    },
    writeConfigFile(path: string, config: unknown) {
      writes.push({ path, config });
    },
  });

  extension({
    registerFlag() {},
    registerCommand() {},
    on(name: string, handler: any) {
      if (name === "session_start") sessionStartHandler = handler;
    },
    getFlag(name: string) {
      return name === "fast" ? true : false;
    },
  } as any);

  await sessionStartHandler?.({}, {
    cwd: "/tmp/project",
    model: { provider: "openai", id: "gpt-5.4" },
    ui: { notify(message: string) { notifications.push(message); } },
  });

  assert.equal(notifications[0], "Fast mode is on for openai/gpt-5.4.");
  assert.deepEqual(writes, [
    {
      path: "/tmp/home/.pi/agent/extensions/openai-fast.json",
      config: { persistState: true, active: true, supportedModels: ["openai/gpt-5.4"] },
    },
  ]);
});
```

This test must use the injected `createOpenaiFastExtension()` seam rather than the real filesystem so it stays hermetic and verifies the exact startup override/writeback behavior from the spec.

Run: `node --import tsx --test pi-extensions/openai-fast/index.test.ts`

Expected: PASS

- [ ] **Step 6: Commit the extension slice**

```bash
git add pi-extensions/openai-fast/index.ts pi-extensions/openai-fast/index.test.ts
git commit -m "feat: port openai-fast extension"
```

## Task 3: Wire repo integration and document the extension

**Files:**
- Modify: `package.json`
- Modify: `README.md`

- [ ] **Step 1: Update the TypeScript test script to include the new tests**

Change `package.json` so `test:ts` runs the current handoff test plus the new openai-fast tests:

```json
{
  "scripts": {
    "typecheck": "tsc --noEmit",
    "test:ts": "node --import tsx --test pi-extensions/handoff/index.test.ts pi-extensions/openai-fast/config.test.ts pi-extensions/openai-fast/index.test.ts"
  }
}
```

- [ ] **Step 2: Update the README extension list and setup guidance**

Edit `README.md` so the Pi Extensions section lists all shipped extensions explicitly:

```md
## Pi Extensions

This repo now ships these first-class Pi extensions:
- `pi-extensions/handoff/`
- `pi-extensions/openai-fast/`
- `pi-extensions/session-query/`
```

Also add one short sentence near the Pi Extensions / Adding Pi Extensions guidance noting that `openai-fast` provides `/fast` for OpenAI priority service-tier requests.

- [ ] **Step 3: Run the repo-level TypeScript tests**

Run: `pnpm test:ts`

Expected: PASS, including handoff and both openai-fast test files

- [ ] **Step 4: Run type-checking**

Run: `pnpm typecheck`

Expected: PASS with no TypeScript errors

- [ ] **Step 5: Commit the integration slice**

```bash
git add package.json README.md
git commit -m "chore: wire openai-fast tests and docs"
```

## Task 4: Verify the repo builds and the extension is included in shipped output

**Files:**
- Verify generated output: `build/extensions/openai-fast/index.ts`
- Modify only if verification exposes a real issue: `scripts/build.py`, `package.json`, `README.md`, or `pi-extensions/openai-fast/*`

- [ ] **Step 1: Run the build pipeline**

Run: `make build`

Expected: PASS and build output lists `openai-fast` under extensions

- [ ] **Step 2: Verify the built extension was copied to the build output**

Run: `test -f build/extensions/openai-fast/index.ts`

Expected: exit code `0`

- [ ] **Step 3: Re-run the final verification set**

Run:
- `pnpm test:ts`
- `pnpm typecheck`

Expected: PASS for both

- [ ] **Step 4: Fix only real integration issues if any verification step failed**

If something fails, make the smallest fix in the relevant file, then re-run only the failing command first, followed by the full verification set.

- [ ] **Step 5: Commit any final verification fixes**

```bash
git add build package.json README.md pi-extensions/openai-fast scripts/build.py
if ! git diff --cached --quiet; then
  git commit -m "fix: finalize openai-fast port"
fi
```
