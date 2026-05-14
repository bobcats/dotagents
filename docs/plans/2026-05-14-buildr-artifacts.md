# buildr-artifacts Implementation Plan

> REQUIRED SUB-SKILL: Use superpowers:executing-plans skill to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Pi extension named `buildr-artifacts` that publishes local or inline HTML artifacts to Buildr S3 artifact storage and returns a shareable URL.

**Architecture:** Implement the extension as focused TypeScript modules under `pi-extensions/buildr-artifacts/`, copying Bolt's artifact validation behavior without importing Bolt source. Use `@aws-sdk/client-s3` for runtime uploads and `@20minutes/s3rver` for fake-S3 tests. Bundle the extension for install so the copied `~/.pi/agent/extensions/buildr-artifacts/index.ts` does not require a copied `node_modules` tree.

**Tech Stack:** TypeScript, Pi extension API (`@mariozechner/pi-coding-agent`), TypeBox (`@sinclair/typebox`), AWS SDK v3 S3 client, Node test runner, `@20minutes/s3rver`, esbuild.

---

## File Structure

Create or modify these files:

- Create: `pi-extensions/buildr-artifacts/artifact-files.ts`
  - Safe path validation, directory walking, content-type allowlist, symlink rejection, and file limits.
- Create: `pi-extensions/buildr-artifacts/artifact-share.ts`
  - Slug generation, URL generation, upload loop, path sharing, and inline HTML sharing.
- Create: `pi-extensions/buildr-artifacts/config.ts`
  - Env parsing, S3 client config, default bucket/base URL, and upload function creation.
- Create: `pi-extensions/buildr-artifacts/index.ts`
  - Pi extension registration for the `share_artifact` tool and `/share_artifact` command.
- Create: `pi-extensions/buildr-artifacts/artifact-files.test.ts`
  - Unit tests for artifact collection and rejection rules.
- Create: `pi-extensions/buildr-artifacts/artifact-share.test.ts`
  - Fake-S3 integration tests for upload keys/content types/URLs.
- Create: `pi-extensions/buildr-artifacts/config.test.ts`
  - Unit tests for env defaults and endpoint/path-style behavior.
- Create: `pi-extensions/buildr-artifacts/index.test.ts`
  - Extension registration and command/tool validation tests.
- Create: `pi-extensions/buildr-artifacts/s3rver.d.ts`
  - Minimal local type declaration for `@20minutes/s3rver` if the package does not ship types.
- Modify: `package.json`
  - Add dependencies/devDependencies and include buildr-artifacts tests in `test:ts`.
- Modify: `tsconfig.json`
  - Include local declaration files if needed.
- Modify: `scripts/build.py`
  - Bundle `buildr-artifacts` at build time with esbuild, leaving other extensions copied as-is.
- Modify: `tests/test_build.py`
  - Cover the new extension bundling path without requiring a real network install.
- Modify: `README.md`
  - Add `buildr-artifacts` to the Pi Extensions list and document `/share_artifact`.

## Dependency Strategy

The dotagents installer copies extensions into `~/.pi/agent/extensions/`; it does not install extension-local `node_modules`. To keep the installed extension usable from any project, bundle `@aws-sdk/client-s3` into the installed `build/extensions/buildr-artifacts/index.ts` using esbuild. Keep Pi/TypeBox imports external, matching existing dotagents extension behavior.

Add these root dev dependencies:

```json
{
  "devDependencies": {
    "@20minutes/s3rver": "^4.0.3",
    "@aws-sdk/client-s3": "^3.1046.0",
    "esbuild": "^0.25.0"
  }
}
```

---

### Task 1: Add dependencies and test script coverage

**Files:**
- Modify: `package.json`
- Modify: `pnpm-lock.yaml`

- [ ] **Step 1: Add package dependencies**

Run:

```bash
cd /Users/mikeastock/code/buildr/dotagents
pnpm add -D @aws-sdk/client-s3@^3.1046.0 @20minutes/s3rver@^4.0.3 esbuild@^0.25.0
```

Expected: `package.json` and `pnpm-lock.yaml` update.

- [ ] **Step 2: Leave `test:ts` pointed at existing tests for now**

Do not add the `pi-extensions/buildr-artifacts/*.test.ts` glob until at least one buildr-artifacts test file exists. This keeps the baseline test command runnable before implementation starts.

- [ ] **Step 3: Run the existing test suite**

Run:

```bash
pnpm test:ts
```

Expected: existing tests pass before adding new failing tests.

- [ ] **Step 4: Commit dependency setup**

```bash
git add package.json pnpm-lock.yaml
git commit -m "build: add buildr artifacts test dependencies"
```

---

### Task 2: Implement artifact file collection with tests

**Files:**
- Create: `pi-extensions/buildr-artifacts/artifact-files.test.ts`
- Create: `pi-extensions/buildr-artifacts/artifact-files.ts`

- [ ] **Step 1: Write failing artifact file tests**

Create `pi-extensions/buildr-artifacts/artifact-files.test.ts`:

```ts
import assert from "node:assert/strict";
import { mkdir, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { mkdtempSync } from "node:fs";
import { describe, it } from "node:test";

import {
  artifactContentTypeForExtension,
  collectArtifactFiles,
  readArtifactFileSafely,
} from "./artifact-files.js";

function tempDir(): string {
  return mkdtempSync(join(tmpdir(), "buildr-artifacts-files-"));
}

describe("artifactContentTypeForExtension", () => {
  it("returns exact content types for supported extensions", () => {
    assert.equal(artifactContentTypeForExtension(".html"), "text/html");
    assert.equal(artifactContentTypeForExtension(".css"), "text/css");
    assert.equal(artifactContentTypeForExtension(".js"), "application/javascript");
    assert.equal(artifactContentTypeForExtension(".png"), "image/png");
    assert.equal(artifactContentTypeForExtension(".woff2"), "font/woff2");
  });
});

describe("collectArtifactFiles", () => {
  it("collects a single html file as index.html", async () => {
    const root = tempDir();
    const file = join(root, "report.html");
    await writeFile(file, "<h1>Report</h1>");

    const files = collectArtifactFiles(file);

    assert.equal(files.length, 1);
    assert.equal(files[0].relativePath, "index.html");
    assert.equal(readArtifactFileSafely(files[0]).toString("utf8"), "<h1>Report</h1>");
  });

  it("rejects a non-html single file", async () => {
    const root = tempDir();
    const file = join(root, "report.txt");
    await writeFile(file, "not html");

    assert.throws(() => collectArtifactFiles(file), /Single file must be an \.html file/);
  });

  it("collects a directory with root index.html and assets", async () => {
    const root = tempDir();
    await mkdir(join(root, "assets"));
    await writeFile(join(root, "index.html"), "<script src=\"assets/app.js\"></script>");
    await writeFile(join(root, "assets", "app.js"), "console.log('ok');");

    const files = collectArtifactFiles(root);

    assert.deepEqual(files.map((file) => file.relativePath), ["assets/app.js", "index.html"]);
  });

  it("rejects a directory without root index.html", async () => {
    const root = tempDir();
    await writeFile(join(root, "page.html"), "<h1>Missing index</h1>");

    assert.throws(() => collectArtifactFiles(root), /Directory must contain an index\.html/);
  });

  it("rejects unsupported extensions in directory uploads", async () => {
    const root = tempDir();
    await writeFile(join(root, "index.html"), "<h1>OK</h1>");
    await writeFile(join(root, "secret.env"), "TOKEN=abc");

    assert.throws(() => collectArtifactFiles(root), /Unsupported file extension/);
  });

  it("rejects symlinks", async () => {
    const root = tempDir();
    await writeFile(join(root, "index.html"), "<h1>OK</h1>");
    await writeFile(join(root, "target.js"), "console.log('target');");
    await symlink(join(root, "target.js"), join(root, "linked.js"));

    assert.throws(() => collectArtifactFiles(root), /symlink paths are not allowed/);
  });
});
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
node --import tsx --test pi-extensions/buildr-artifacts/artifact-files.test.ts
```

Expected: FAIL because `artifact-files.ts` does not exist.

- [ ] **Step 3: Implement artifact file collection**

Create `pi-extensions/buildr-artifacts/artifact-files.ts` by adapting Bolt's `src/artifacts/artifact-files.ts` without the workspace-root dependency. Use this structure:

```ts
import {
  closeSync,
  constants as fsConstants,
  fstatSync,
  lstatSync,
  openSync,
  readdirSync,
  readFileSync,
  type Stats,
} from "node:fs";
import { extname, join, relative, resolve } from "node:path";

const CONTENT_TYPES: Record<string, string> = {
  ".css": "text/css",
  ".gif": "image/gif",
  ".html": "text/html",
  ".ico": "image/x-icon",
  ".jpeg": "image/jpeg",
  ".jpg": "image/jpeg",
  ".js": "application/javascript",
  ".json": "application/json",
  ".pdf": "application/pdf",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ttf": "font/ttf",
  ".txt": "text/plain",
  ".webp": "image/webp",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".xml": "application/xml",
};

const ALLOWED_ARTIFACT_EXTENSIONS = new Set(Object.keys(CONTENT_TYPES));
const DEFAULT_MAX_ARTIFACT_FILES = 2000;
const DEFAULT_MAX_ARTIFACT_DEPTH = 20;
const MAX_ARTIFACT_FILE_BYTES = 1_073_741_824;

export interface ArtifactShareLimitOverrides {
  maxFiles?: number;
  maxDepth?: number;
}

export interface CollectedArtifactFile {
  relativePath: string;
  absolutePath: string;
  expectedDev: number;
  expectedIno: number;
  expectedSizeBytes: number;
}

interface ArtifactCollectionLimits {
  maxFiles: number;
  maxDepth: number;
}

export function artifactContentTypeForExtension(ext: string): string {
  return CONTENT_TYPES[ext.toLowerCase()] ?? "application/octet-stream";
}

export function collectArtifactFiles(
  hostPath: string,
  limitOverrides: ArtifactShareLimitOverrides = {},
): CollectedArtifactFile[] {
  const resolvedHostPath = resolve(hostPath);
  const limits = resolveArtifactCollectionLimits(limitOverrides);
  const state = { fileCount: 0 };
  const stat = lstatNoSymlink(resolvedHostPath, `Path does not exist: ${resolvedHostPath}`);

  if (stat.isFile()) {
    if (extname(resolvedHostPath).toLowerCase() !== ".html") {
      throw new Error(`Single file must be an .html file: ${resolvedHostPath}`);
    }

    const files: CollectedArtifactFile[] = [];
    pushCollectedArtifactFile(files, "index.html", resolvedHostPath, stat, state, limits);
    return files;
  }

  if (!stat.isDirectory()) {
    throw new Error(`Path is neither a file nor a directory: ${resolvedHostPath}`);
  }

  const indexPath = join(resolvedHostPath, "index.html");
  const indexStat = lstatNoSymlink(
    indexPath,
    `Directory must contain an index.html at its root: ${resolvedHostPath}`,
  );

  if (!indexStat.isFile()) {
    throw new Error(`index.html must be a regular file: ${indexPath}`);
  }

  const files: CollectedArtifactFile[] = [];
  walkDir(resolvedHostPath, resolvedHostPath, 0, files, state, limits);
  assertArtifactFilesWithinSizeLimit(files);
  return files;
}

function resolveArtifactCollectionLimits(
  overrides: ArtifactShareLimitOverrides = {},
): ArtifactCollectionLimits {
  return {
    maxDepth: resolvePositiveInteger(overrides.maxDepth, DEFAULT_MAX_ARTIFACT_DEPTH, "maxDepth"),
    maxFiles: resolvePositiveInteger(overrides.maxFiles, DEFAULT_MAX_ARTIFACT_FILES, "maxFiles"),
  };
}

function resolvePositiveInteger(value: number | undefined, fallback: number, name: string): number {
  const resolved = value ?? fallback;
  if (!Number.isInteger(resolved) || resolved <= 0) {
    throw new Error(`${name} must be a positive integer`);
  }
  return resolved;
}

function lstatNoSymlink(path: string, missingError: string): Stats {
  try {
    const stat = lstatSync(path);
    if (stat.isSymbolicLink()) throw new Error(`symlink paths are not allowed: ${path}`);
    return stat;
  } catch (error) {
    const nodeError = error as NodeJS.ErrnoException;
    if (nodeError.code === "ENOENT" || nodeError.code === "ENOTDIR") {
      throw new Error(missingError, { cause: error });
    }
    if (nodeError.code === "ELOOP") {
      throw new Error(`symlink paths are not allowed: ${path}`, { cause: error });
    }
    throw error;
  }
}

function walkDir(
  baseDir: string,
  currentDir: string,
  depth: number,
  files: CollectedArtifactFile[],
  state: { fileCount: number },
  limits: ArtifactCollectionLimits,
): void {
  for (const entryName of readdirSync(currentDir).sort()) {
    const fullPath = join(currentDir, entryName);
    const entryStat = lstatNoSymlink(fullPath, `Path does not exist: ${fullPath}`);

    if (entryStat.isDirectory()) {
      if (depth + 1 > limits.maxDepth) {
        throw new Error(`Artifact depth limit exceeded (${limits.maxDepth}): ${fullPath}`);
      }
      walkDir(baseDir, fullPath, depth + 1, files, state, limits);
      continue;
    }

    if (entryStat.isFile()) {
      assertAllowedArtifactExtension(fullPath);
      pushCollectedArtifactFile(files, relative(baseDir, fullPath), fullPath, entryStat, state, limits);
      continue;
    }

    throw new Error(`Only regular files and directories are allowed: ${fullPath}`);
  }
}

function assertAllowedArtifactExtension(filePath: string): void {
  const extension = extname(filePath).toLowerCase();
  if (ALLOWED_ARTIFACT_EXTENSIONS.has(extension)) return;
  throw new Error(`Unsupported file extension for artifact sharing: ${filePath} (${extension || "none"})`);
}

function pushCollectedArtifactFile(
  files: CollectedArtifactFile[],
  relativePath: string,
  absolutePath: string,
  stat: Stats,
  state: { fileCount: number },
  limits: ArtifactCollectionLimits,
): void {
  state.fileCount += 1;
  if (state.fileCount > limits.maxFiles) {
    throw new Error(`Artifact file count limit exceeded (${limits.maxFiles} files): ${absolutePath}`);
  }
  files.push({ absolutePath, expectedDev: stat.dev, expectedIno: stat.ino, expectedSizeBytes: stat.size, relativePath });
}

function openReadonlyNoFollow(path: string): number {
  const noFollowFlag = typeof fsConstants.O_NOFOLLOW === "number" ? fsConstants.O_NOFOLLOW : 0;
  try {
    return openSync(path, fsConstants.O_RDONLY | noFollowFlag);
  } catch (error) {
    const nodeError = error as NodeJS.ErrnoException;
    if (nodeError.code === "ELOOP") throw new Error(`symlink paths are not allowed: ${path}`, { cause: error });
    if (nodeError.code === "ENOENT") throw new Error(`Path does not exist: ${path}`, { cause: error });
    throw error;
  }
}

export function readArtifactFileSafely(file: CollectedArtifactFile): Buffer {
  const fd = openReadonlyNoFollow(file.absolutePath);
  try {
    const openedStat = fstatSync(fd);
    if (!openedStat.isFile()) throw new Error(`Path is not a regular file: ${file.absolutePath}`);
    if (
      openedStat.dev !== file.expectedDev ||
      openedStat.ino !== file.expectedIno ||
      openedStat.size !== file.expectedSizeBytes
    ) {
      throw new Error(`Path changed while sharing artifact: ${file.absolutePath}`);
    }
    return readFileSync(fd);
  } finally {
    closeSync(fd);
  }
}

export function assertArtifactFilesWithinSizeLimit(files: CollectedArtifactFile[]): void {
  for (const file of files) {
    if (file.expectedSizeBytes > MAX_ARTIFACT_FILE_BYTES) {
      throw new Error(`Artifact file too large (>1 GiB): ${file.absolutePath}`);
    }
  }
}
```

- [ ] **Step 4: Run artifact file tests**

Run:

```bash
node --import tsx --test pi-extensions/buildr-artifacts/artifact-files.test.ts
```

Expected: artifact file tests pass.

- [ ] **Step 5: Commit artifact file collection**

```bash
git add pi-extensions/buildr-artifacts/artifact-files.ts pi-extensions/buildr-artifacts/artifact-files.test.ts
git commit -m "feat(buildr-artifacts): collect artifact files safely"
```

---

### Task 3: Implement artifact sharing against fake S3

**Files:**
- Create: `pi-extensions/buildr-artifacts/artifact-share.test.ts`
- Create: `pi-extensions/buildr-artifacts/artifact-share.ts`
- Create: `pi-extensions/buildr-artifacts/s3rver.d.ts`

- [ ] **Step 1: Add minimal `@20minutes/s3rver` types**

Create `pi-extensions/buildr-artifacts/s3rver.d.ts`:

```ts
declare module "@20minutes/s3rver" {
  interface S3rverBucketConfig {
    name: string;
    configs?: Array<string | Buffer>;
  }

  interface S3rverOptions {
    address?: string;
    port?: number;
    silent?: boolean;
    directory?: string;
    resetOnClose?: boolean;
    allowMismatchedSignatures?: boolean;
    configureBuckets?: S3rverBucketConfig[];
  }

  export default class S3rver {
    constructor(options?: S3rverOptions);
    run(): Promise<{ address: string; port: number }>;
    close(): Promise<void>;
  }
}
```

- [ ] **Step 2: Write failing fake-S3 tests**

Create `pi-extensions/buildr-artifacts/artifact-share.test.ts`:

```ts
import assert from "node:assert/strict";
import { GetObjectCommand, HeadObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { mkdtempSync } from "node:fs";
import { afterEach, describe, it } from "node:test";
import S3rver from "@20minutes/s3rver";

import { createS3ArtifactUpload, shareArtifactFromHostPath, shareArtifactFromHtml } from "./artifact-share.js";

const BUCKET = "test-artifacts";
let servers: S3rver[] = [];

async function getFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => {
        if (address && typeof address === "object") resolve(address.port);
        else reject(new Error("Could not allocate test port"));
      });
    });
  });
}

async function startFakeS3(): Promise<{ endpoint: string; client: S3Client }> {
  const directory = mkdtempSync(join(tmpdir(), "buildr-artifacts-s3-"));
  const port = await getFreePort();
  const server = new S3rver({
    address: "127.0.0.1",
    allowMismatchedSignatures: true,
    configureBuckets: [{ name: BUCKET }],
    directory,
    port,
    resetOnClose: true,
    silent: true,
  });
  await server.run();
  servers.push(server);

  const endpoint = `http://127.0.0.1:${port}`;
  const client = new S3Client({
    credentials: { accessKeyId: "S3RVER", secretAccessKey: "S3RVER" },
    endpoint,
    forcePathStyle: true,
    region: "us-east-1",
  });
  return { endpoint, client };
}

async function objectBody(client: S3Client, key: string): Promise<string> {
  const result = await client.send(new GetObjectCommand({ Bucket: BUCKET, Key: key }));
  return result.Body?.transformToString() ?? "";
}

async function objectContentType(client: S3Client, key: string): Promise<string | undefined> {
  const result = await client.send(new HeadObjectCommand({ Bucket: BUCKET, Key: key }));
  return result.ContentType;
}

afterEach(async () => {
  await Promise.all(servers.map((server) => server.close()));
  servers = [];
});

describe("shareArtifactFromHtml", () => {
  it("uploads inline HTML as index.html and returns the artifact URL", async () => {
    const { client } = await startFakeS3();
    const upload = createS3ArtifactUpload(BUCKET, client);

    const result = await shareArtifactFromHtml({
      baseUrl: "https://artifacts.example.test",
      html: "<h1>Hello</h1>",
      slug: "fixed-slug",
      upload,
    });

    assert.equal(result.url, "https://artifacts.example.test/fixed-slug/");
    assert.equal(await objectBody(client, "fixed-slug/index.html"), "<h1>Hello</h1>");
  });
});

describe("shareArtifactFromHostPath", () => {
  it("uploads a single HTML file as index.html", async () => {
    const { client } = await startFakeS3();
    const upload = createS3ArtifactUpload(BUCKET, client);
    const root = mkdtempSync(join(tmpdir(), "buildr-artifacts-html-"));
    const htmlPath = join(root, "report.html");
    await writeFile(htmlPath, "<h1>Report</h1>");

    const result = await shareArtifactFromHostPath({
      baseUrl: "https://artifacts.example.test",
      hostPath: htmlPath,
      slug: "file-slug",
      upload,
    });

    assert.equal(result.url, "https://artifacts.example.test/file-slug/");
    assert.equal(await objectBody(client, "file-slug/index.html"), "<h1>Report</h1>");
  });

  it("uploads a directory bundle with content types", async () => {
    const { client } = await startFakeS3();
    const upload = createS3ArtifactUpload(BUCKET, client);
    const root = mkdtempSync(join(tmpdir(), "buildr-artifacts-dir-"));
    await mkdir(join(root, "assets"));
    await writeFile(join(root, "index.html"), "<script src=\"assets/app.js\"></script>");
    await writeFile(join(root, "assets", "app.js"), "console.log('ok');");

    await shareArtifactFromHostPath({
      baseUrl: "https://artifacts.example.test",
      hostPath: root,
      slug: "dir-slug",
      upload,
    });

    assert.equal(await objectBody(client, "dir-slug/index.html"), "<script src=\"assets/app.js\"></script>");
    assert.equal(await objectBody(client, "dir-slug/assets/app.js"), "console.log('ok');");
    assert.equal(await objectContentType(client, "dir-slug/index.html"), "text/html");
    assert.equal(await objectContentType(client, "dir-slug/assets/app.js"), "application/javascript");
  });

  it("returns explicit index.html for localhost:9000 base URLs", async () => {
    const { client } = await startFakeS3();
    const upload = createS3ArtifactUpload(BUCKET, client);

    const result = await shareArtifactFromHtml({
      baseUrl: "http://localhost:9000/test-artifacts",
      html: "<h1>Local</h1>",
      slug: "local-slug",
      upload,
    });

    assert.equal(result.url, "http://localhost:9000/test-artifacts/local-slug/index.html");
  });
});
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```bash
node --import tsx --test pi-extensions/buildr-artifacts/artifact-share.test.ts
```

Expected: FAIL because `artifact-share.ts` does not exist.

- [ ] **Step 4: Implement artifact sharing**

Create `pi-extensions/buildr-artifacts/artifact-share.ts`:

```ts
import { randomBytes } from "node:crypto";
import { extname } from "node:path";
import { PutObjectCommand, type S3Client } from "@aws-sdk/client-s3";

import {
  artifactContentTypeForExtension,
  assertArtifactFilesWithinSizeLimit,
  collectArtifactFiles,
  readArtifactFileSafely,
  type ArtifactShareLimitOverrides,
} from "./artifact-files.js";

const ADJECTIVES = ["agile", "amber", "bold", "brave", "bright", "calm", "clear", "clever", "cobalt", "crisp", "daring", "deep", "eager", "fast", "fresh", "golden", "green", "happy", "ivory", "keen", "lively", "lucid", "maple", "merry", "noble", "onyx", "opal", "quick", "quiet", "rapid", "silver", "solar", "steady", "swift", "tidy", "vivid"];
const NOUNS = ["anchor", "badge", "beacon", "brook", "canvas", "cedar", "comet", "ember", "field", "forge", "garden", "harbor", "kernel", "lantern", "meadow", "orbit", "panda", "pixel", "river", "rocket", "signal", "summit", "thicket", "tiger", "valley", "window"];

export type ArtifactUploadFn = (
  key: string,
  body: Buffer,
  contentType: string,
  signal?: AbortSignal,
) => Promise<void>;

export interface ShareArtifactFromHostPathInput {
  hostPath: string;
  baseUrl: string;
  upload: ArtifactUploadFn;
  signal?: AbortSignal;
  slug?: string;
  limits?: ArtifactShareLimitOverrides;
}

export interface ShareArtifactFromHtmlInput {
  html: string;
  baseUrl: string;
  upload: ArtifactUploadFn;
  signal?: AbortSignal;
  slug?: string;
}

export interface ShareArtifactResult {
  slug: string;
  url: string;
}

export function createS3ArtifactUpload(bucketName: string, client: S3Client): ArtifactUploadFn {
  return async (key, body, contentType, signal) => {
    await client.send(
      new PutObjectCommand({
        Body: body,
        Bucket: bucketName,
        CacheControl: "public, max-age=31536000, immutable",
        ContentType: contentType,
        Key: key,
      }),
      { abortSignal: signal },
    );
  };
}

export function generateArtifactSlug(): string {
  const adjective = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)];
  const noun = NOUNS[Math.floor(Math.random() * NOUNS.length)];
  return `${adjective}-${noun}-${randomBytes(2).toString("hex")}`;
}

export async function shareArtifactFromHtml(input: ShareArtifactFromHtmlInput): Promise<ShareArtifactResult> {
  throwIfAborted(input.signal);
  const baseUrl = input.baseUrl.replace(/\/+$/, "");
  const slug = input.slug ?? generateArtifactSlug();
  await input.upload(`${slug}/index.html`, Buffer.from(input.html, "utf8"), "text/html", input.signal);
  return { slug, url: buildArtifactUrl(baseUrl, slug) };
}

export async function shareArtifactFromHostPath(input: ShareArtifactFromHostPathInput): Promise<ShareArtifactResult> {
  throwIfAborted(input.signal);
  const baseUrl = input.baseUrl.replace(/\/+$/, "");
  const files = collectArtifactFiles(input.hostPath, input.limits);
  assertArtifactFilesWithinSizeLimit(files);
  const slug = input.slug ?? generateArtifactSlug();

  for (const file of files) {
    throwIfAborted(input.signal);
    const key = `${slug}/${file.relativePath}`;
    const body = readArtifactFileSafely(file);
    const contentType = artifactContentTypeForExtension(extname(file.relativePath));
    await input.upload(key, body, contentType, input.signal);
  }

  return { slug, url: buildArtifactUrl(baseUrl, slug) };
}

function throwIfAborted(signal: AbortSignal | undefined): void {
  if (signal?.aborted) throw new Error("Operation aborted");
}

function buildArtifactUrl(baseUrl: string, slug: string): string {
  return `${baseUrl}/${slug}${shouldUseExplicitIndexHtml(baseUrl) ? "/index.html" : "/"}`;
}

function shouldUseExplicitIndexHtml(baseUrl: string): boolean {
  try {
    const parsed = new URL(baseUrl);
    return ["localhost", "127.0.0.1", "::1"].includes(parsed.hostname) && parsed.port === "9000";
  } catch {
    return false;
  }
}
```

- [ ] **Step 5: Run fake-S3 tests**

Run:

```bash
node --import tsx --test pi-extensions/buildr-artifacts/artifact-files.test.ts pi-extensions/buildr-artifacts/artifact-share.test.ts
```

Expected: buildr artifact file and fake-S3 sharing tests pass.

- [ ] **Step 6: Commit artifact sharing**

```bash
git add pi-extensions/buildr-artifacts/artifact-share.ts pi-extensions/buildr-artifacts/artifact-share.test.ts pi-extensions/buildr-artifacts/s3rver.d.ts
git commit -m "feat(buildr-artifacts): upload artifacts to s3"
```

---

### Task 4: Add configuration resolution

**Files:**
- Create: `pi-extensions/buildr-artifacts/config.test.ts`
- Create: `pi-extensions/buildr-artifacts/config.ts`

- [ ] **Step 1: Write failing config tests**

Create `pi-extensions/buildr-artifacts/config.test.ts`:

```ts
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { resolveArtifactConfig, resolveS3ClientConfig } from "./config.js";

describe("resolveArtifactConfig", () => {
  it("uses Buildr production defaults", () => {
    assert.deepEqual(resolveArtifactConfig({}), {
      baseUrl: "https://artifacts.buildrtools.com",
      bucketName: "buildr-bizops-artifacts",
    });
  });

  it("respects explicit bucket and base URL", () => {
    assert.deepEqual(
      resolveArtifactConfig({ ARTIFACTS_S3_BUCKET: "custom-bucket", ARTIFACTS_BASE_URL: "https://cdn.example.test/" }),
      { baseUrl: "https://cdn.example.test", bucketName: "custom-bucket" },
    );
  });
});

describe("resolveS3ClientConfig", () => {
  it("defaults forcePathStyle on when an endpoint is configured", () => {
    assert.deepEqual(resolveS3ClientConfig({ ARTIFACTS_S3_ENDPOINT: "http://127.0.0.1:4568" }), {
      endpoint: "http://127.0.0.1:4568",
      forcePathStyle: true,
      region: undefined,
    });
  });

  it("lets ARTIFACTS_S3_FORCE_PATH_STYLE override endpoint default", () => {
    assert.deepEqual(
      resolveS3ClientConfig({ ARTIFACTS_S3_ENDPOINT: "http://127.0.0.1:4568", ARTIFACTS_S3_FORCE_PATH_STYLE: "false", AWS_REGION: "us-west-2" }),
      { endpoint: "http://127.0.0.1:4568", forcePathStyle: false, region: "us-west-2" },
    );
  });
});
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
node --import tsx --test pi-extensions/buildr-artifacts/config.test.ts
```

Expected: FAIL because `config.ts` does not exist.

- [ ] **Step 3: Implement config**

Create `pi-extensions/buildr-artifacts/config.ts`:

```ts
import { S3Client, type S3ClientConfig } from "@aws-sdk/client-s3";
import { createS3ArtifactUpload, type ArtifactUploadFn } from "./artifact-share.js";

export interface ArtifactConfig {
  bucketName: string;
  baseUrl: string;
}

export interface ArtifactRuntimeConfig extends ArtifactConfig {
  upload: ArtifactUploadFn;
}

const DEFAULT_BUCKET = "buildr-bizops-artifacts";
const DEFAULT_BASE_URL = "https://artifacts.buildrtools.com";

export function resolveArtifactConfig(env: NodeJS.ProcessEnv): ArtifactConfig {
  return {
    bucketName: env.ARTIFACTS_S3_BUCKET ?? DEFAULT_BUCKET,
    baseUrl: (env.ARTIFACTS_BASE_URL ?? DEFAULT_BASE_URL).replace(/\/+$/, ""),
  };
}

export function resolveS3ClientConfig(env: NodeJS.ProcessEnv): S3ClientConfig {
  const endpoint = env.ARTIFACTS_S3_ENDPOINT ?? env.AWS_ENDPOINT_URL_S3;
  const forcePathStyle = parseBooleanEnv(env.ARTIFACTS_S3_FORCE_PATH_STYLE) ?? Boolean(endpoint);
  return { endpoint, forcePathStyle, region: env.AWS_REGION };
}

export function createArtifactRuntimeConfig(env: NodeJS.ProcessEnv = process.env): ArtifactRuntimeConfig {
  const artifactConfig = resolveArtifactConfig(env);
  const client = new S3Client(resolveS3ClientConfig(env));
  return {
    ...artifactConfig,
    upload: createS3ArtifactUpload(artifactConfig.bucketName, client),
  };
}

function parseBooleanEnv(value: string | undefined): boolean | undefined {
  if (value === undefined) return undefined;
  const normalized = value.trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) return true;
  if (["0", "false", "no", "off"].includes(normalized)) return false;
  return undefined;
}
```

- [ ] **Step 4: Run config tests**

Run:

```bash
node --import tsx --test pi-extensions/buildr-artifacts/*.test.ts
```

Expected: current buildr-artifacts TypeScript tests pass.

- [ ] **Step 5: Commit config**

```bash
git add pi-extensions/buildr-artifacts/config.ts pi-extensions/buildr-artifacts/config.test.ts
git commit -m "feat(buildr-artifacts): resolve artifact storage config"
```

---

### Task 5: Register the Pi tool and slash command

**Files:**
- Create: `pi-extensions/buildr-artifacts/index.test.ts`
- Create: `pi-extensions/buildr-artifacts/index.ts`

- [ ] **Step 1: Write failing registration and validation tests**

Create `pi-extensions/buildr-artifacts/index.test.ts`:

```ts
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import buildrArtifacts, { _test } from "./index.js";

describe("share_artifact input validation", () => {
  it("rejects both path and html", () => {
    assert.throws(() => _test.normalizeShareArtifactInput({ path: "report.html", html: "<h1>Report</h1>" }), /exactly one/);
  });

  it("rejects neither path nor html", () => {
    assert.throws(() => _test.normalizeShareArtifactInput({}), /exactly one/);
  });

  it("normalizes a leading @ in path inputs", () => {
    assert.deepEqual(_test.normalizeShareArtifactInput({ path: "@dist/index.html" }), { kind: "path", path: "dist/index.html" });
  });

  it("accepts inline html", () => {
    assert.deepEqual(_test.normalizeShareArtifactInput({ html: "<h1>Hi</h1>" }), { kind: "html", html: "<h1>Hi</h1>" });
  });
});

describe("buildr-artifacts extension registration", () => {
  it("registers the share_artifact tool and command", () => {
    const tools: string[] = [];
    const commands: string[] = [];

    buildrArtifacts({
      registerTool(tool: { name: string }) {
        tools.push(tool.name);
      },
      registerCommand(name: string) {
        commands.push(name);
      },
    } as any);

    assert.deepEqual(tools, ["share_artifact"]);
    assert.deepEqual(commands, ["share_artifact"]);
  });
});
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
node --import tsx --test pi-extensions/buildr-artifacts/index.test.ts
```

Expected: FAIL because `index.ts` does not exist.

- [ ] **Step 3: Implement extension entrypoint**

Create `pi-extensions/buildr-artifacts/index.ts`:

```ts
import { resolve } from "node:path";
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type, type Static } from "@sinclair/typebox";

import { shareArtifactFromHostPath, shareArtifactFromHtml, type ShareArtifactResult } from "./artifact-share.js";
import { createArtifactRuntimeConfig, type ArtifactRuntimeConfig } from "./config.js";

const shareArtifactSchema = Type.Object({
  label: Type.Optional(Type.String({ description: "Brief description of what you're sharing." })),
  path: Type.Optional(Type.String({ description: "Path to a local .html file or directory containing index.html." })),
  html: Type.Optional(Type.String({ description: "Inline HTML content to publish as index.html." })),
});

type ShareArtifactParams = Static<typeof shareArtifactSchema>;

type NormalizedShareArtifactInput =
  | { kind: "path"; path: string }
  | { kind: "html"; html: string };

export function normalizeShareArtifactInput(params: Pick<ShareArtifactParams, "path" | "html">): NormalizedShareArtifactInput {
  const path = typeof params.path === "string" && params.path.trim() ? params.path.trim().replace(/^@/, "") : undefined;
  const html = typeof params.html === "string" && params.html.trim() ? params.html : undefined;

  if (Boolean(path) === Boolean(html)) {
    throw new Error("share_artifact requires exactly one of path or html.");
  }

  return path ? { kind: "path", path } : { kind: "html", html: html! };
}

async function shareArtifact(
  params: ShareArtifactParams,
  ctx: { cwd: string },
  runtimeConfig: ArtifactRuntimeConfig,
  signal?: AbortSignal,
): Promise<ShareArtifactResult> {
  const input = normalizeShareArtifactInput(params);
  if (input.kind === "html") {
    return shareArtifactFromHtml({ baseUrl: runtimeConfig.baseUrl, html: input.html, signal, upload: runtimeConfig.upload });
  }

  return shareArtifactFromHostPath({
    baseUrl: runtimeConfig.baseUrl,
    hostPath: resolve(ctx.cwd, input.path),
    signal,
    upload: runtimeConfig.upload,
  });
}

export default function buildrArtifacts(pi: ExtensionAPI) {
  const runtimeConfigFactory = () => createArtifactRuntimeConfig(process.env);

  pi.registerTool({
    name: "share_artifact",
    label: "Share Artifact",
    description:
      "Share an HTML artifact and return a shareable URL. Uploads inline HTML, an .html file, or a directory containing index.html to Buildr artifact storage.",
    promptSnippet: "Share browser-viewable HTML artifacts and return a URL.",
    promptGuidelines: [
      "Use share_artifact when the user asks to create, publish, or share an HTML report, dashboard, prototype, or other browser-viewable artifact.",
    ],
    parameters: shareArtifactSchema,
    async execute(_toolCallId, params, signal, onUpdate, ctx) {
      onUpdate?.({ content: [{ type: "text", text: "Uploading artifact..." }] });
      const result = await shareArtifact(params, ctx, runtimeConfigFactory(), signal);
      return {
        content: [{ type: "text", text: result.url }],
        details: { label: params.label, slug: result.slug, url: result.url },
      };
    },
  });

  pi.registerCommand("share_artifact", {
    description: "Upload an HTML artifact and show the shareable URL",
    handler: async (args, ctx) => {
      const trimmedArgs = args.trim();
      const params: ShareArtifactParams = trimmedArgs
        ? { path: trimmedArgs }
        : { html: await requireInlineHtml(ctx) };

      const result = await shareArtifact(params, ctx, runtimeConfigFactory(), ctx.signal);
      const message = `Artifact shared: ${result.url}`;
      ctx.ui.notify(message, "info");
      pi.sendMessage({ customType: "buildr-artifacts", content: message, display: true, details: result });
    },
  });
}

async function requireInlineHtml(ctx: { hasUI?: boolean; ui: { editor(title: string, initial?: string): Promise<string | undefined> } }): Promise<string> {
  if (!ctx.hasUI) {
    throw new Error("/share_artifact with no path requires an interactive UI to enter inline HTML.");
  }
  const html = await ctx.ui.editor("HTML artifact", "<!doctype html>\n<html>\n<body>\n\n</body>\n</html>\n");
  if (!html?.trim()) {
    throw new Error("No HTML provided.");
  }
  return html;
}

export const _test = { normalizeShareArtifactInput };
```

Adjust types if `ExtensionCommandContext` does not expose `signal`; commands can pass `undefined` if needed.

- [ ] **Step 4: Run extension tests**

Run:

```bash
node --import tsx --test pi-extensions/buildr-artifacts/*.test.ts
```

Expected: all buildr-artifacts TypeScript tests pass.

- [ ] **Step 5: Add buildr-artifacts tests to `test:ts`**

Change `package.json` from:

```json
"test:ts": "node --import tsx --test pi-extensions/handoff/index.test.ts pi-extensions/openai-fast/config.test.ts pi-extensions/openai-fast/index.test.ts"
```

to:

```json
"test:ts": "node --import tsx --test pi-extensions/handoff/index.test.ts pi-extensions/openai-fast/config.test.ts pi-extensions/openai-fast/index.test.ts pi-extensions/buildr-artifacts/*.test.ts"
```

- [ ] **Step 6: Run the full TypeScript test script**

Run:

```bash
pnpm test:ts
```

Expected: all existing and buildr-artifacts TypeScript tests pass.

- [ ] **Step 7: Commit extension registration**

```bash
git add package.json pi-extensions/buildr-artifacts/index.ts pi-extensions/buildr-artifacts/index.test.ts
git commit -m "feat(buildr-artifacts): register share artifact extension"
```

---

### Task 6: Bundle buildr-artifacts for installed extension runtime

**Files:**
- Modify: `scripts/build.py`
- Modify: `tests/test_build.py`

- [ ] **Step 1: Write failing build-system test**

Add this test to `BuildExtensionsTests` in `tests/test_build.py`:

```python
    def test_build_extensions_bundles_marked_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "pi-extensions"
            ext_dir = source / "buildr-artifacts"
            ext_dir.mkdir(parents=True)
            (ext_dir / "index.ts").write_text("import './helper.js';\nexport default function () {}\n")
            (ext_dir / "helper.ts").write_text("export const value = 1\n")
            (ext_dir / ".bundle").write_text("true\n")

            calls = []
            self.build.PI_EXTENSIONS_DIR = source
            self.build.BUILD_DIR = root / "build"
            self.build.bundle_extension = lambda name, source_path, dest_path: calls.append((name, source_path, dest_path)) or dest_path.mkdir(parents=True) or (dest_path / "index.ts").write_text("// bundled\n")

            self.build.build_extensions()

            self.assertEqual(calls, [("buildr-artifacts", ext_dir, self.build.BUILD_DIR / "extensions" / "buildr-artifacts")])
            self.assertEqual((self.build.BUILD_DIR / "extensions" / "buildr-artifacts" / "index.ts").read_text(), "// bundled\n")
```

- [ ] **Step 2: Run Python tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_build.py
```

Expected: FAIL because `.bundle` handling and `bundle_extension` do not exist.

- [ ] **Step 3: Implement bundle support**

Modify `scripts/build.py`:

```python
import subprocess
```

Add helpers near `build_extension`:

```python
def should_bundle_extension(source: Path) -> bool:
    return (source / ".bundle").exists()


def bundle_extension(name: str, source: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "pnpm",
            "exec",
            "esbuild",
            str(source / "index.ts"),
            "--bundle",
            "--platform=node",
            "--format=esm",
            "--outfile=" + str(dest / "index.ts"),
            "--external:@mariozechner/pi-coding-agent",
            "--external:@mariozechner/pi-ai",
            "--external:@mariozechner/pi-tui",
            "--external:@sinclair/typebox",
        ],
        cwd=ROOT,
        check=True,
    )
```

Change `build_extension`:

```python
def build_extension(name: str, source: Path) -> bool:
    """Build a single Pi extension from a source directory."""
    entrypoint = source / "index.ts"
    if not entrypoint.exists():
        print(f"    Warning: {source} has no index.ts, skipping")
        return False

    dest = BUILD_DIR / "extensions" / name
    if dest.exists():
        shutil.rmtree(dest)

    if should_bundle_extension(source):
        bundle_extension(name, source, dest)
    else:
        shutil.copytree(source, dest)
    return True
```

- [ ] **Step 4: Mark buildr-artifacts for bundling**

Create `pi-extensions/buildr-artifacts/.bundle`:

```text
true
```

- [ ] **Step 5: Run build-system tests**

Run:

```bash
python3 -m unittest tests/test_build.py
```

Expected: PASS.

- [ ] **Step 6: Run build to prove bundling works**

Run:

```bash
make build
```

Expected:

- output includes `buildr-artifacts`
- `build/extensions/buildr-artifacts/index.ts` exists
- installed build artifact does not need local helper files

- [ ] **Step 7: Commit build bundling support**

```bash
git add scripts/build.py tests/test_build.py pi-extensions/buildr-artifacts/.bundle
git commit -m "build: bundle buildr artifacts extension"
```

---

### Task 7: Document the extension

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README extension list**

Change the Pi Extensions section from:

```md
This repo now ships these first-class Pi extensions:
- `pi-extensions/handoff/`
- `pi-extensions/openai-fast/`
- `pi-extensions/session-query/`
```

to:

```md
This repo now ships these first-class Pi extensions:
- `pi-extensions/buildr-artifacts/`
- `pi-extensions/handoff/`
- `pi-extensions/openai-fast/`
- `pi-extensions/session-query/`
```

- [ ] **Step 2: Add usage documentation**

Add below the `openai-fast` sentence:

```md
`buildr-artifacts` adds a `share_artifact` tool and `/share_artifact` command for publishing local HTML artifacts to Buildr artifact storage.

Examples:

```bash
/share_artifact ./report.html
/share_artifact ./dist
```

With no arguments, `/share_artifact` opens an editor for inline HTML.

Configuration defaults:

- `ARTIFACTS_S3_BUCKET=buildr-bizops-artifacts`
- `ARTIFACTS_BASE_URL=https://artifacts.buildrtools.com`

It uses normal AWS SDK credential resolution on the local machine. For local S3-compatible endpoints, set `ARTIFACTS_S3_ENDPOINT`; path-style addressing defaults on when an endpoint is configured.
```

Escape nested code fences correctly in the actual edit.

- [ ] **Step 3: Run markdown-free verification**

Run:

```bash
rg -n "buildr-artifacts|share_artifact" README.md
```

Expected: README includes the extension and command docs.

- [ ] **Step 4: Commit docs**

```bash
git add README.md
git commit -m "docs: document buildr artifacts extension"
```

---

### Task 8: Final verification

**Files:**
- All changed files

- [ ] **Step 1: Run TypeScript tests**

Run:

```bash
pnpm test:ts
```

Expected: PASS.

- [ ] **Step 2: Run TypeScript typecheck**

Run:

```bash
pnpm typecheck
```

Expected: PASS.

- [ ] **Step 3: Run build-system tests**

Run:

```bash
python3 -m unittest tests/test_build.py
```

Expected: PASS.

- [ ] **Step 4: Run build**

Run:

```bash
make build
```

Expected: PASS and `build/extensions/buildr-artifacts/index.ts` exists.

- [ ] **Step 5: Inspect git status**

Run:

```bash
git status --short
```

Expected: clean working tree after commits, or only intentionally uncommitted files if the user requested no commits.

- [ ] **Step 6: Optional manual fake-S3 smoke test**

If desired, add a temporary local script or use the tests to start `@20minutes/s3rver`, then run Pi from source:

```bash
pi -e /Users/mikeastock/code/buildr/dotagents/pi-extensions/buildr-artifacts/index.ts
```

In Pi, run:

```text
/share_artifact /path/to/report.html
```

Expected: command uploads to the configured endpoint and reports a URL.
