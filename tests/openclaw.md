# Test Context: openclaw

**Organization**: opendatahub-io
**Repository**: openclaw
**Analyzed**: 2026-03-22T23:47:20Z
**Agent Readiness**: **HIGH** - Lint and test commands validated successfully in container. An agent can clone, patch, lint, test, and get clear pass/fail signals.

## Overview

openclaw is a multi-channel AI gateway with extensible messaging integrations. It's a TypeScript/Node.js monorepo (73 workspace projects) using pnpm, vitest for testing, and oxlint for linting. Also includes Swift apps (iOS/macOS) and an Android app.

**Languages**: TypeScript, JavaScript, Swift, Kotlin, Python
**Build System**: pnpm + tsdown + custom scripts
**Test Framework**: vitest
**Linter**: oxlint (primary), oxfmt (formatter), swiftlint, ruff

## Container Recipe

This section provides a complete, copy-paste recipe for running lint and tests in a container.

### 1. Start container with repo mounted

```bash
podman run -d --name test-context-openclaw \
  -v /path/to/openclaw:/app:Z \
  -w /app \
  node:22-bookworm \
  sleep infinity
```

**Base image**: `node:22-bookworm` (Debian 12 with Node.js 22.x)
**Why**: Repository requires Node.js >= 22.16.0 per package.json engines field

### 2. Install system dependencies

```bash
podman exec test-context-openclaw bash -c \
  "apt-get update && apt-get install -y git make python3 curl"
```

**Note**: These packages are already installed in node:22-bookworm, but included for completeness.

### 3. Install pnpm

```bash
podman exec test-context-openclaw bash -c \
  "npm install -g pnpm@10.23.0"
```

**Why**: Repository uses pnpm@10.23.0 as package manager (specified in package.json packageManager field)

### 4. Install project dependencies

```bash
podman exec test-context-openclaw bash -c \
  "cd /app && pnpm install --frozen-lockfile"
```

**Duration**: ~10-12 seconds with cache, ~600 seconds cold
**Expected**: 1342 packages installed, exit code 0
**Warnings**: Some nested dependency build warnings are expected and non-blocking

### 5. Run lint

```bash
podman exec test-context-openclaw bash -c \
  "cd /app && pnpm lint"
```

**Expected output**:
```
Found 0 warnings and 0 errors.
Finished in 4.4s on 5210 files with 136 rules using 22 threads.
```

**Exit code**: 0 = pass, non-zero = lint violations found
**Command**: Uses oxlint (fast Rust-based linter) with type-aware checking

### 6. Run format check

```bash
podman exec test-context-openclaw bash -c \
  "cd /app && pnpm format:check"
```

**Expected output**:
```
Checking formatting...

All matched files use the correct format.
Finished in 3585ms on 8241 files using 22 threads.
```

**Exit code**: 0 = pass, non-zero = formatting issues found
**Command**: Uses oxfmt (fast Rust-based formatter)

### 7. Bundle UI components (required for tests)

```bash
podman exec test-context-openclaw bash -c \
  "cd /app && pnpm canvas:a2ui:bundle"
```

**Expected output**:
```
<DIR>/a2ui.bundle.js  chunk │ size: 457.10 kB
✔ rolldown v1.0.0-rc.9 Finished in 57.39 ms
```

**Why**: Tests require pre-built UI bundle (a2ui.bundle.js)

### 8. Run tests

Full test suite (may take several minutes):
```bash
podman exec test-context-openclaw bash -c \
  "cd /app && pnpm test"
```

Run a single test file:
```bash
podman exec test-context-openclaw bash -c \
  "cd /app && pnpm vitest run test/appcast.test.ts"
```

Run a specific test by name:
```bash
podman exec test-context-openclaw bash -c \
  "cd /app && pnpm vitest run -t 'your test name'"
```

**Expected**: Test summary showing passed/failed counts
**Exit code**: 0 = all tests passed, non-zero = tests failed
**Note**: Default test run excludes `*.live.test.ts` and `*.e2e.test.ts` which require external services

### 9. Cleanup

```bash
podman rm -f test-context-openclaw
```

Always clean up the container when done.

## Validation Results

All commands were validated in `node:22-bookworm` container:

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Install | `pnpm install --frozen-lockfile` | 0 | ✅ Pass | 1342 packages, 11.4s |
| Lint | `pnpm lint` | 0 | ✅ Pass | 0 warnings, 0 errors, 4.4s |
| Format | `pnpm format:check` | 0 | ✅ Pass | All files formatted correctly, 3.6s |
| Bundle | `pnpm canvas:a2ui:bundle` | 0 | ✅ Pass | UI bundle created, 57ms |
| Test | `pnpm vitest run test/*.test.ts` (sample) | 0 | ✅ Pass | 3/3 tests passed, 1.12s |

**Summary**: install OK, lint OK (0 issues), format OK, bundle OK, tests OK (sampled)

## CI/CD

**System**: GitHub Actions
**Primary workflow**: `.github/workflows/ci.yml`

### Gating Checks (Required for Merge)

These checks must pass on all pull requests:

1. **check** - Combined static analysis
   ```bash
   pnpm check
   ```
   Runs: lint (oxlint), format check (oxfmt), type check (TypeScript), plugin-sdk exports validation, and custom boundary checks

2. **test (Linux, sharded)** - Unit and integration tests
   ```bash
   pnpm canvas:a2ui:bundle && pnpm test
   ```
   Runs on 2 shards in parallel with controlled heap limits

3. **test:extensions** - Extension-specific tests
   ```bash
   pnpm test:extensions
   ```

4. **test:channels** - Channel integration tests
   ```bash
   pnpm test:channels
   ```

5. **test:contracts** - Contract tests for plugins and channels
   ```bash
   pnpm test:contracts
   ```

6. **protocol:check** - Protocol schema validation
   ```bash
   pnpm protocol:check
   ```

7. **build-smoke** - Build and CLI smoke test
   ```bash
   pnpm build && node openclaw.mjs --help
   ```

8. **secrets** - Detect leaked secrets and audit dependencies
   ```bash
   pre-commit run --all-files detect-private-key
   pre-commit run --all-files pnpm-audit-prod
   ```

### Advisory Checks (Run on Specific Changes)

These run only when relevant files change:

- **test (Windows, 6 shards)** - When Node.js code changes
- **test (macOS)** - When macOS/Swift code changes
- **Swift lint + build + test** - When Swift code changes
- **Android build + test** - When Android code changes
- **test (Bun runtime)** - On push to main only

### CI Optimizations

- **Docs-only detection**: Skips heavy jobs when only docs change
- **Scope detection**: Skips platform-specific jobs when irrelevant
- **Extension change detection**: Only tests changed extensions
- **Sharding**: Linux (2 shards), Windows (6 shards) for parallel execution
- **Artifact caching**: Shares `dist/` build across jobs on push events

## Conventions

**Test Files**:
- Pattern: `**/*.test.ts`
- Locations: `src/**/*.test.ts`, `extensions/**/*.test.ts`, `test/**/*.test.ts`
- Excluded: `**/*.live.test.ts`, `**/*.e2e.test.ts` (require external services)

**Test Naming**:
- Uses vitest `describe` / `test` / `it` blocks
- Example: `test('should validate appcast format', () => { ... })`

**Import Style**:
- ES modules (`import`/`export`)
- Path aliases: `openclaw/plugin-sdk`, `openclaw/plugin-sdk/*`
- Relative imports for local files

**Code Structure**:
- Monorepo with 73 workspace projects
- Core: `src/`
- Extensions: `extensions/`
- Apps: `apps/macos/`, `apps/ios/`, `apps/android/`
- Tests: `test/` and co-located with source
- Scripts: `scripts/`

**Coverage Thresholds** (vitest.config.ts):
- Lines: 70%
- Functions: 70%
- Branches: 55%
- Statements: 70%

**Linter Rules**:
- Configured in `.oxlintrc.json`
- Strict: `typescript/no-explicit-any` = error
- Categories: correctness, perf, suspicious all set to error
- Type-aware checking enabled

## Gaps & Caveats

1. **Platform-specific builds not validated**:
   - Swift/macOS/iOS builds require macOS with Xcode (Xcode 26.1 in CI)
   - Android builds require Android SDK + Gradle 8.11.1
   - These cannot be validated in a standard Linux container

2. **Live/E2E tests excluded**:
   - Tests matching `*.live.test.ts` and `*.e2e.test.ts` require external services
   - Examples: live model APIs, gateway network tests, Docker-based integration tests
   - Run explicitly with `pnpm test:live` or `pnpm test:e2e`

3. **Pre-commit hooks**:
   - Require Python with `pre-commit` package installed
   - Run additional checks: shellcheck, actionlint, detect-secrets, ruff, pytest
   - Not validated in container recipe above

4. **Test execution time**:
   - Full test suite can take several minutes on large codebase
   - 5210+ source files, 73 workspace projects
   - CI uses sharding and parallel execution to mitigate

5. **Dependency warnings**:
   - Nested dependency `@tloncorp/api` emits TypeScript errors during install
   - These are warnings from optional dependencies and do not block build/test
   - 16 vulnerabilities reported by nested `npm audit` (not blocking per project config)

6. **Build dependencies**:
   - Full build (`pnpm build`) requires additional steps beyond container validation
   - Generates protocol definitions, bundles plugins, writes metadata
   - Container validation focused on lint + test (core patch validation use case)

## Quick Reference

**Install dependencies**:
```bash
pnpm install --frozen-lockfile
```

**Run all static checks** (lint + format + types + custom):
```bash
pnpm check
```

**Run tests**:
```bash
pnpm canvas:a2ui:bundle  # Required pre-step
pnpm test                # All unit tests
pnpm test:fast           # Alias for unit tests
pnpm test:e2e            # E2E tests (requires setup)
```

**Run single test file**:
```bash
pnpm vitest run path/to/file.test.ts
```

**Run tests matching pattern**:
```bash
pnpm vitest run -t 'pattern'
```

**Lint**:
```bash
pnpm lint           # Check
pnpm lint:fix       # Fix + format
```

**Format**:
```bash
pnpm format:check   # Check
pnpm format         # Fix
```

**Build**:
```bash
pnpm build
```

**Coverage**:
```bash
pnpm test:coverage
```

## Additional Commands

**TypeScript type check only**:
```bash
pnpm tsgo  # Part of pnpm check
```

**Docs checks**:
```bash
pnpm check:docs          # Format + lint + links + i18n
pnpm lint:docs           # Markdown lint
pnpm lint:docs:fix       # Auto-fix markdown
```

**Python skills**:
```bash
python -m ruff check skills     # Lint
python -m pytest -q skills      # Test
```

**Custom boundary checks** (part of `pnpm check`):
```bash
pnpm lint:plugins:no-extension-imports
pnpm lint:extensions:no-src-outside-plugin-sdk
pnpm lint:web-search-provider-boundaries
```

**Protocol validation**:
```bash
pnpm protocol:check     # Verify schema + Swift codegen
pnpm protocol:gen       # Generate schema
```

**Release checks** (CI only):
```bash
pnpm release:check
pnpm release:openclaw:npm:check
```

## Container Recipe Summary

For quick copy-paste into an agent workflow:

```bash
# Start container
podman run -d --name test-context-openclaw \
  -v $(pwd):/app:Z -w /app node:22-bookworm sleep infinity

# Install pnpm
podman exec test-context-openclaw npm install -g pnpm@10.23.0

# Install dependencies
podman exec test-context-openclaw pnpm install --frozen-lockfile

# Lint
podman exec test-context-openclaw pnpm lint

# Format check
podman exec test-context-openclaw pnpm format:check

# Test (bundle + run)
podman exec test-context-openclaw pnpm canvas:a2ui:bundle
podman exec test-context-openclaw pnpm test

# Cleanup
podman rm -f test-context-openclaw
```

**Expected timeline**:
- Install deps: ~10s (cached) to ~600s (cold)
- Lint: ~4s
- Format: ~4s
- Bundle: ~1s
- Tests: Variable (sample: ~1s, full suite: several minutes)

---

**End of Test Context**
