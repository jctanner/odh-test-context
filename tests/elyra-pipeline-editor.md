# Test Context: elyra-pipeline-editor

**Generated:** 2026-03-22T18:07:00Z
**Organization:** opendatahub-io
**Repository:** elyra-pipeline-editor

## Overview

TypeScript/JavaScript monorepo for pipeline editing UI components. Built with Lerna, uses Jest for unit tests and Cypress for integration tests. Two packages: `@elyra/pipeline-editor` (React component library) and `@elyra/pipeline-services` (data services).

**Agent Readiness:** `HIGH` — All lint and test commands validated successfully. An agent can clone, install dependencies, build, lint, and run tests in a standard Node.js 14 container with clear pass/fail signals.

**Languages:** TypeScript, JavaScript
**Build System:** Lerna + Yarn Workspaces
**Node Version:** 12, 14, 15 (CI matrix); Node 14 recommended

---

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-elyra-pipeline-editor \
  -v $(pwd):/app:Z \
  -w /app \
  node:14 \
  sleep infinity
```

**Image:** `node:14` (matches CI matrix, includes yarn 1.22.19)
**Mount:** Current directory → `/app` (read-write with SELinux label)

### 2. Install Dependencies

```bash
podman exec test-context-elyra-pipeline-editor bash -c "cd /app && yarn install --frozen-lockfile"
```

**Expected result:** Installs in ~80s with many peer dependency warnings (safe to ignore — Storybook/React version mismatches that don't affect build or tests).

**Validation:** Exit code 0, ends with `Done in XX.XXs`

### 3. Build

```bash
podman exec test-context-elyra-pipeline-editor bash -c "cd /app && yarn build"
```

**Expected result:** Builds both packages in ~20s using Lerna. `@elyra/pipeline-services` uses `tsc`, `@elyra/pipeline-editor` uses `microbundle`.

**Validation:** Exit code 0, output includes:
```
lerna success run Ran npm script 'build' in 2 packages in 19.7s:
lerna success - @elyra/pipeline-editor
lerna success - @elyra/pipeline-services
```

### 4. Lint

```bash
podman exec test-context-elyra-pipeline-editor bash -c "cd /app && yarn lint"
```

**Expected result:** ESLint checks all `.ts`, `.tsx`, `.js`, `.jsx` files with `--max-warnings=0` (strict mode).

**Validation:** Exit code 0, output: `Done in 6.65s.` (no warnings or errors printed)

**Note:** Lint failure (exit code != 0) means code violations. Check output for specific issues.

### 5. Format Check

```bash
podman exec test-context-elyra-pipeline-editor bash -c "cd /app && yarn format:check"
```

**Expected result:** Prettier validates all code formatting.

**Validation:** Exit code 0, output includes `All matched files use Prettier code style!`

**Auto-fix:** Run `yarn format` to auto-format files (use in patch workflow).

### 6. Unit Tests

```bash
podman exec test-context-elyra-pipeline-editor bash -c "cd /app && yarn test"
```

**Expected result:** Runs 203 tests across 22 test suites in ~31s. All tests should pass.

**Validation:** Exit code 0, output includes:
```
Test Suites: 22 passed, 22 total
Tests:       203 passed, 203 total
Snapshots:   9 passed, 9 total
```

**Note:** Some console warnings during tests (form validation errors in test scenarios) are expected and safe.

### 7. Run Single Test File (Optional)

```bash
podman exec test-context-elyra-pipeline-editor bash -c "cd /app && yarn test packages/pipeline-editor/src/PipelineEditor/index.test.tsx"
```

### 8. Run Single Test (Optional)

```bash
podman exec test-context-elyra-pipeline-editor bash -c "cd /app && yarn test -t 'test name pattern'"
```

### 9. Coverage (Optional)

```bash
podman exec test-context-elyra-pipeline-editor bash -c "cd /app && yarn test:cover"
```

Generates coverage report in `coverage/` directory. No threshold enforced.

### 10. Cleanup

```bash
podman rm -f test-context-elyra-pipeline-editor
```

**Always run cleanup**, even if validation fails partway through.

---

## Validation Results

All commands validated live in `node:14` container on 2026-03-22:

| Step | Command | Result | Time | Notes |
|------|---------|--------|------|-------|
| Install | `yarn install --frozen-lockfile` | ✅ PASS | 82s | Peer dep warnings expected |
| Build | `yarn build` | ✅ PASS | 20s | Both packages built |
| Lint | `yarn lint` | ✅ PASS | 7s | 0 warnings (strict) |
| Format | `yarn format:check` | ✅ PASS | 2s | All files formatted |
| Test | `yarn test` | ✅ PASS | 31s | 203/203 passed |

**Summary:** All validation commands succeeded. Agent can apply patches and get reliable pass/fail signals for lint and tests.

---

## CI/CD

**System:** GitHub Actions
**Config:** `.github/workflows/build.yaml`
**Triggers:** `push`, `pull_request`

### Gating Checks (All Required)

1. **lint** — `yarn lint` (ESLint with --max-warnings=0)
2. **format:check** — `yarn format:check` (Prettier)
3. **test** — `yarn test` (Jest unit tests, matrix: Node 12/14/15)
4. **test-coverage** — `yarn test:cover` (Jest with coverage, uploads to Codecov)
5. **test-integration** — `yarn test:cypress` (Cypress E2E tests with Storybook)

All checks must pass before merge. CI caches `node_modules` and Cypress binary.

### CI Environment Variables

- `FORCE_COLOR=true` — Enable colored output
- `NODE_OPTIONS=--openssl-legacy-provider` — Required for Cypress tests (OpenSSL compatibility)

### Matrix Testing

Unit tests run on Node 12, 14, and 15. Dependencies installed with latest Node, tests run with matrix version.

---

## Linting Configuration

### ESLint

**Config:** `.eslintrc.js`
**Extends:** `react-app`, `plugin:jest/recommended`, `plugin:jest/style`, `plugin:testing-library/react`, `plugin:jest-dom/recommended`
**Plugins:** `import`, `header`

**Run:** `yarn lint`
**Fix:** `yarn lint:fix`
**Scope:** All `.ts`, `.tsx`, `.js`, `.jsx` files (respects `.gitignore`)

**Key Rules:**
- License header enforcement (Apache 2.0) — warns if missing
- Import order: alphabetical, grouped by builtin/external/internal/parent/sibling
- Newlines between import groups
- No extraneous dependencies (except in test/config files)
- Testing library best practices

**Strict Mode:** `--max-warnings=0` in CI — all warnings treated as errors.

### Prettier

**Config:** `.prettierrc` (empty — uses defaults)
**Run:** `yarn format:check`
**Fix:** `yarn format`
**Scope:** `**/*.{tsx,ts,js,css,html,json}` (respects `.gitignore`)

**Defaults:** 2-space indent, single quotes, semicolons, trailing commas (es5)

---

## Testing Configuration

### Jest (Unit Tests)

**Framework:** Jest with `ts-jest` preset
**Config:** `jest.config.js` (root) + `jest.config.base.js` + package-level configs
**Test Pattern:** `**/*.test.{ts,tsx}`
**Exclude:** `**/*.snap.test.{ts,tsx}`

**Run All:** `yarn test`
**Coverage:** `yarn test:cover`
**Single File:** `yarn test {file}`
**Single Test:** `yarn test -t '{test_name}'`
**Watch:** `yarn test --watch`

**Test Environment:**
- `@elyra/pipeline-services` — `node` (default)
- `@elyra/pipeline-editor` — `jsdom` (for React component tests)

**Setup:**
- `@testing-library/jest-dom` for DOM matchers
- `packages/pipeline-editor/jest.setup.js` for jsdom-specific setup

**Current Status:** 203 tests in 22 suites, all passing in 31s

**Coverage Collection:**
- Includes: `**/*.{ts,tsx}`
- Excludes: `**/src/index.ts`, `**/*.d.ts`, `**/test-utils.{ts,tsx}`, test files
- Reporters: `lcov`, `text`
- No threshold enforced

### Cypress (Integration Tests)

**Config:** `cypress.json`
**Base URL:** `http://localhost:6006` (Storybook)
**Tests:** `cypress/integration/**/*.ts`

**Run:** `yarn test:cypress` (starts Storybook, then runs Cypress)
**Interactive:** `yarn test:cypress:dev` (opens Cypress UI)

**Note:** Integration tests not validated in container — require Storybook server and Cypress binary installation. CI handles orchestration with `start-server-and-test`.

---

## Build Configuration

**System:** Lerna monorepo with Yarn Workspaces
**Lerna Config:** `lerna.json` (version 3.22.1, useWorkspaces)
**Packages:** `packages/*`

### Install

```bash
yarn install --frozen-lockfile
```

Runs preinstall hook: `npx force-resolutions -y` (overrides vulnerable dependencies per `resolutions` in `package.json`)

### Build

```bash
yarn build
```

Runs `lerna run build` in all packages:
- `@elyra/pipeline-services` — `tsc` (TypeScript compilation)
- `@elyra/pipeline-editor` — `microbundle --css inline -f cjs` (bundled library with inlined CSS)

Build output:
- `packages/pipeline-services/dist/`
- `packages/pipeline-editor/dist/`

### Other Commands

- `yarn clean` — Remove build artifacts and node_modules
- `yarn watch` — Watch mode for development (parallel)
- `yarn link-all` — Link packages (for local development)

---

## Conventions

### Test Files

**Pattern:** `**/*.test.{ts,tsx}`
**Location:** Co-located with source files in `src/` directories
**Naming:** `ComponentName.test.tsx`, `utils.test.ts`

### Test Structure

Jest standard:
```typescript
describe('ComponentName', () => {
  it('should do something', () => {
    // test
  });
});
```

React Testing Library for component tests:
```typescript
import { render, screen } from '@testing-library/react';
```

### Import Style

Enforced by ESLint:
1. React imports first
2. Builtin modules (node:*)
3. External packages (alphabetical)
4. Internal packages (@iris/*)
5. Parent/sibling/index imports (relative)
6. Type imports (if separate)

Newlines between groups. Alphabetically sorted within groups.

### Code Style

- TypeScript strict mode
- Apache 2.0 license header required in all source files
- Prettier formatting (2-space indent, single quotes)
- No default exports (prefer named exports)

---

## Gaps & Caveats

1. **Cypress tests not container-validated** — Integration tests require Storybook server and Cypress binary. CI handles this, but local container validation skipped. Tests run in CI before merge.

2. **No coverage threshold** — Coverage is collected and uploaded to Codecov, but no enforcement of minimum coverage percentage.

3. **Peer dependency warnings** — Many warnings during `yarn install` due to Storybook expecting React 16/17 but packages use different versions. Warnings are safe to ignore — all builds and tests pass.

4. **Node version flexibility** — CI tests on 12/14/15, all pass. Node 14 recommended for consistency.

5. **Storybook not in validation** — `yarn sb:start` launches Storybook dev server, but not included in validation recipe (not a gating check).

6. **No pre-commit hooks active** — Husky configured for `lint-staged` but not validated in container (requires git repo setup).

---

## Quick Reference

**Validate a patch:**
```bash
# Start container
podman run -d --name test-elyra -v $(pwd):/app:Z -w /app node:14 sleep infinity

# Full validation
podman exec test-elyra bash -c "cd /app && yarn install --frozen-lockfile && yarn build && yarn lint && yarn format:check && yarn test"

# Cleanup
podman rm -f test-elyra
```

**Expected output:** All commands exit 0, tests show `203 passed`, lint shows `Done in X.XXs` with no errors.

**Agent workflow:**
1. Apply patch to repo
2. Run container recipe steps 1-6
3. Check exit codes (0 = pass, non-zero = fail)
4. Parse test output for pass/fail counts
5. Report results
6. Cleanup container (step 10)

**Failure interpretation:**
- Lint exit code != 0 → Code style violations (check output for specifics)
- Test exit code != 0 → Test failures (parse output for which tests failed)
- Build exit code != 0 → Compilation errors (TypeScript or bundling issues)
