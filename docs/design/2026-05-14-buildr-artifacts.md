# buildr-artifacts Pi Extension Design

## Goal

Add a local Pi extension named `buildr-artifacts` that lets a developer publish browser-viewable HTML artifacts to Buildr artifact storage and receive a shareable URL.

## User Interface

The extension lives at `pi-extensions/buildr-artifacts/` and installs through the existing dotagents extension install flow.

It exposes two entry points with the same public name:

1. Tool: `share_artifact`
   - Accepts `path` for a local `.html` file or a directory containing `index.html`.
   - Accepts `html` for inline HTML content.
   - Accepts optional `label` for human-readable context.
   - Requires exactly one of `path` or `html`.
   - Returns the artifact URL in tool content and structured details.

2. Slash command: `/share_artifact`
   - `/share_artifact path/to/file.html` uploads a local HTML file.
   - `/share_artifact path/to/dist-dir` uploads a local directory bundle.
   - `/share_artifact` with no args opens an editor for inline HTML, then uploads it.
   - Reports the URL through Pi UI notifications/messages.

## Storage Configuration

Runtime uses the AWS SDK S3 client and normal local AWS credential resolution.

Defaults:

- `ARTIFACTS_S3_BUCKET=buildr-bizops-artifacts`
- `ARTIFACTS_BASE_URL=https://artifacts.buildrtools.com`

Optional local/test endpoint support:

- `ARTIFACTS_S3_ENDPOINT` or `AWS_ENDPOINT_URL_S3`
- `ARTIFACTS_S3_FORCE_PATH_STYLE`
- `ARTIFACTS_AWS_REGION` with `AWS_REGION` as fallback
- `ARTIFACTS_AWS_ACCESS_KEY_ID`, `ARTIFACTS_AWS_SECRET_ACCESS_KEY`, and optional `ARTIFACTS_AWS_SESSION_TOKEN`

If an endpoint is configured, path-style addressing defaults on unless explicitly disabled. This supports fake S3 and local S3-compatible services.

## Artifact Packaging Behavior

The implementation mirrors Bolt's artifact sharing behavior while remaining self-contained in dotagents.

Rules:

- A single `.html` file uploads as `<slug>/index.html`.
- A directory must contain root `index.html`.
- Directory uploads preserve relative asset paths.
- Supported file extensions and content types are exactly:
  - `.css`: `text/css`
  - `.gif`: `image/gif`
  - `.html`: `text/html`
  - `.ico`: `image/x-icon`
  - `.jpeg`: `image/jpeg`
  - `.jpg`: `image/jpeg`
  - `.js`: `application/javascript`
  - `.json`: `application/json`
  - `.pdf`: `application/pdf`
  - `.png`: `image/png`
  - `.svg`: `image/svg+xml`
  - `.ttf`: `font/ttf`
  - `.txt`: `text/plain`
  - `.webp`: `image/webp`
  - `.woff`: `font/woff`
  - `.woff2`: `font/woff2`
  - `.xml`: `application/xml`
- Unsupported extensions reject the upload.
- Symlinks are rejected.
- Only regular files and directories are allowed.
- Limits match Bolt defaults: at most 2,000 files, maximum directory depth 20, and maximum individual file size 1 GiB.
- Each upload sets `ContentType` and immutable public cache headers.
- The resulting URL is `${ARTIFACTS_BASE_URL}/${slug}/` except when the base URL hostname is `localhost`, `127.0.0.1`, or `::1` and the port is exactly `9000`; that local MinIO-compatible case returns `${baseUrl}/${slug}/index.html`.

## Implementation Shape

Create focused files under `pi-extensions/buildr-artifacts/`:

- `index.ts`: registers `share_artifact` tool and `/share_artifact` command.
- `config.ts`: resolves environment, S3 client config, bucket, and base URL.
- `artifact-files.ts`: validates and collects artifact files safely.
- `artifact-share.ts`: slug generation, upload loop, and URL generation.
- `slug-words.ts`: adjective/noun word lists or a compact local slug generator.

The extension should not import from the Bolt repository. Shared behavior is copied/adapted so local Pi usage does not depend on Bolt source layout.

## Testing Strategy

Use `@20minutes/s3rver` as the fake S3 server for integration-style tests. The tests should configure `S3Client` against the local fake endpoint with path-style addressing and fake credentials.

Coverage:

- input validation rejects both `path` and `html`.
- input validation rejects neither `path` nor `html`.
- non-HTML single files are rejected.
- directories without `index.html` are rejected.
- inline HTML uploads as `<slug>/index.html`.
- local HTML file uploads as `<slug>/index.html`.
- directory bundles upload asset files with correct content types.
- returned URLs match the configured base URL.
- the extension registers the `share_artifact` tool and `/share_artifact` command.

Verification commands:

```bash
cd ~/code/buildr/dotagents
pnpm test:ts
pnpm typecheck
```
