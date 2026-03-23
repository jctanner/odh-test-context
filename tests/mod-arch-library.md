# Test Context: mod-arch-library

**Generated:** 2026-03-22T19:19:00-04:00
**Agent Readiness:** HIGH - Lint and test commands validated successfully in container

## Overview

Modular Architecture Essentials - A TypeScript/JavaScript monorepo with 4 npm workspaces providing libraries for building scalable micro-frontend applications. Contains a small Go backend (BFF) in mod-arch-starter.

- **Languages:** TypeScript (primary), JavaScript, Go
- **Build System:** npm workspaces (monorepo)
- **Test Framework:** Jest (JS/TS), Go test (Go)
- **CI:** GitHub Actions
- **Node Version:** 22.x
- **Go Version:** 1.24.3

**Why High Readiness:** All primary lint and test commands validated successfully in a Node.js 22 container. Build, lint, and test all pass with exit code 0. Go tests also pass. Only minor issue: Go code has 5 unused function violations.

---

## Container Recipe

This recipe provides everything needed to validate patches in an isolated container.

### 1. Start Container

```bash
podman run -d \
  --name test-mod-arch-library \
  -v "$(pwd)":/app:Z \
  -w /app \
  node:22-bookworm \
  sleep infinity
```

Or with Docker:

```bash
docker run -d \
  --name test-mod-arch-library \
  -v "$(pwd)":/app \
  -w /app \
  node:22-bookworm \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-mod-arch-library bash -c \
  "apt-get update -qq && apt-get install -y -qq rsync make git"
```

**Required packages:**
- `rsync` - for copying assets in mod-arch-shared build
- `make` - for Go Makefile targets
- `git` - for various build/test operations

### 3. Install Project Dependencies

```bash
podman exec test-mod-arch-library bash -c \
  "cd /app && npm ci --ignore-scripts"
```

**Important:** Use `--ignore-scripts` to skip the automatic build during install. The build will fail during npm install due to cross-workspace dependencies that haven't been built yet.

**Validation Result:** ✅ SUCCESS (exit 0)
- Installed 1180 packages
- 16 known vulnerabilities (4 low, 3 moderate, 9 high) - acceptable for validation
- Some deprecation warnings for eslint 8.x, glob 7.x

### 4. Build All Packages

```bash
podman exec test-mod-arch-library bash -c \
  "cd /app && npm run build"
```

This builds all 4 workspaces in order:
1. `mod-arch-core` - TypeScript → JavaScript compilation
2. `mod-arch-shared` - TypeScript + asset copying (requires rsync)
3. `mod-arch-kubeflow` - TypeScript + style/image copying
4. `mod-arch-installer` - Template syncing + TypeScript

**Validation Result:** ✅ SUCCESS (exit 0)
- All workspaces built successfully
- No TypeScript errors

### 5. Run Linting

```bash
podman exec test-mod-arch-library bash -c \
  "cd /app && npm run lint"
```

Runs ESLint across all workspaces with:
- Max warnings: 0 (strict mode)
- Checks: TypeScript, React, imports, hooks, prettier formatting
- Extensions: `.js,.ts,.jsx,.tsx`

**Validation Result:** ✅ SUCCESS (exit 0)
- No lint violations found
- Checked all 4 workspaces

**Fix violations:**

```bash
podman exec test-mod-arch-library bash -c \
  "cd /app && npm run lint:fix"
```

### 6. Run All Tests

```bash
podman exec test-mod-arch-library bash -c \
  "cd /app && npm run test"
```

Runs tests for all workspaces:
- `mod-arch-core`: 63 tests (lint + unit + type-check)
- `mod-arch-shared`: 26 tests (lint + unit + type-check)
- `mod-arch-kubeflow`: 0 tests (uses --passWithNoTests)
- `mod-arch-installer`: flavor template tests

**Validation Result:** ✅ SUCCESS (exit 0)
- 11 test suites passed
- 89 tests passed total
- Type checking passed for all packages

### 7. Run Single Test File

```bash
podman exec test-mod-arch-library bash -c \
  "cd /app/mod-arch-core && npx jest hooks/__tests__/useModularArchContext.test.tsx"
```

**Pattern:** `cd /app/mod-arch-<workspace> && npx jest {file}`

**Validation Result:** ✅ SUCCESS
- 1 test suite, 3 tests passed

### 8. Run Single Test by Name

```bash
podman exec test-mod-arch-library bash -c \
  "cd /app/mod-arch-core && npx jest -t 'should return full context'"
```

**Pattern:** `cd /app/mod-arch-<workspace> && npx jest -t '{test_name}'`

### 9. Run Tests with Coverage

```bash
podman exec test-mod-arch-library bash -c \
  "cd /app && npm run test:jest -- --coverage --workspace=mod-arch-core"
```

Coverage reports saved to `jest-coverage/` in each workspace.

### 10. Go Backend Testing (Optional)

The repo includes a Go BFF in `mod-arch-starter/bff`. To test it, install Go:

```bash
podman exec test-mod-arch-library bash -c \
  "curl -sL https://go.dev/dl/go1.24.3.linux-amd64.tar.gz -o /tmp/go.tar.gz && \
   tar -C /usr/local -xzf /tmp/go.tar.gz"
```

**Run Go tests:**

```bash
podman exec test-mod-arch-library bash -c \
  "cd /app/mod-arch-starter/bff && PATH=/usr/local/go/bin:\$PATH make test"
```

**Validation Result:** ✅ SUCCESS (exit 0)
- 2 packages tested (cmd, internal/api)
- Tests pass despite envtest asset fetch warning

**Run Go linting:**

```bash
podman exec test-mod-arch-library bash -c \
  "cd /app/mod-arch-starter/bff && PATH=/usr/local/go/bin:\$PATH make lint"
```

**Validation Result:** ⚠️ FOUND ISSUES (exit 2)
- 5 unused code violations
- Command works but code needs cleanup

### 11. Cleanup Container

```bash
podman rm -f test-mod-arch-library
```

---

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `npm ci --ignore-scripts` | 0 | ✅ PASS | 1180 packages installed |
| Build | `npm run build` | 0 | ✅ PASS | All 4 workspaces built |
| Lint | `npm run lint` | 0 | ✅ PASS | No violations |
| Test | `npm run test` | 0 | ✅ PASS | 89 tests passed |
| Single test | `npx jest <file>` | 0 | ✅ PASS | 3 tests passed |
| Go test | `make test` (bff) | 0 | ✅ PASS | 2 packages tested |
| Go lint | `make lint` (bff) | 2 | ⚠️ ISSUES | 5 unused violations |

**Summary:** All primary validation commands pass. Go lint finds code quality issues but tests work.

---

## CI/CD Configuration

**System:** GitHub Actions (`.github/workflows/test.yml`)

**Gating Checks** (all required for merge):

1. **Lint PR Title**
   - Validates semantic commit format
   - Types: feat, fix, perf, revert, refactor, style, docs, test, chore, ci, build

2. **Install Dependencies**
   ```bash
   npm ci
   ```

3. **Run Linting**
   ```bash
   npm run lint
   ```

4. **Run All Tests**
   ```bash
   npm run test
   ```

5. **Build All Packages**
   ```bash
   npm run build
   ```

6. **Test Coverage (mod-arch-core)**
   ```bash
   npm run test:jest -- --coverage --workspace=mod-arch-core
   ```

7. **Test Coverage (mod-arch-shared)**
   ```bash
   npm run test:jest -- --coverage --workspace=mod-arch-shared
   ```

8. **Individual Package Tests**
   - Matrix: mod-arch-core, mod-arch-shared, mod-arch-kubeflow
   - Commands: `npm run test:core`, `npm run test:shared`, `npm run test:kubeflow`

**Trigger:** Pull requests and pushes to main branch
**Node Version:** 22.x (matrix)

---

## Project Structure

### Workspaces

1. **mod-arch-core** - Core functionality, API utilities, context providers, hooks
2. **mod-arch-shared** - Shared UI components and utilities
3. **mod-arch-kubeflow** - Kubeflow-specific themes and styling
4. **mod-arch-installer** - Project scaffolding and templates

### Test Locations

```
mod-arch-core/
  __tests__/unit/          # Unit tests
  context/__tests__/       # Context tests
  hooks/__tests__/         # Hook tests
  api/__tests__/           # API tests

mod-arch-shared/
  __tests__/unit/          # Unit tests
  utilities/__tests__/     # Utility tests

mod-arch-installer/
  flavors/default/frontend/src/app/standalone/__tests__/

mod-arch-starter/
  bff/cmd/*_test.go        # Go tests
  bff/internal/api/*_test.go
```

### Configuration Files

- **ESLint:** `.eslintrc.cjs` in each workspace
- **Jest:** `jest.config.js` in each workspace with tests
- **TypeScript:** `tsconfig.json` in each workspace
- **Go lint:** `mod-arch-starter/bff/.golangci.yaml`
- **Pre-commit:** `.husky/pre-commit` (runs lint-staged)

---

## Conventions

### Test File Naming

- **JavaScript/TypeScript:** `*.test.tsx`, `*.test.ts`, `*.spec.ts` in `__tests__/` directories
- **Go:** `*_test.go` alongside source files

### Test Function Naming

- **Jest:** `describe()` blocks with `it()` or `test()` assertions
- **Go:** Functions starting with `Test*`

### Import Style

- Absolute imports using `~` alias for src root
- Example: `import { X } from '~/api/types'`
- Enforced by `eslint-plugin-no-relative-import-paths`
- Import ordering enforced by ESLint

### Code Style

- **Prettier:** Single quotes, trailing commas, 100 char line width
- **Naming:** camelCase (variables/functions), PascalCase (types/components)
- **No console.log** - ESLint error
- **Strict null checks** - TypeScript

### Commit Messages

- **Format:** Conventional commits (semantic-release)
- **Types:** feat, fix, perf, refactor, style, docs, test, chore, ci, build
- **PR titles:** Must match semantic format (checked in CI)

---

## Gaps & Caveats

### Known Issues

1. **mod-arch-kubeflow has no tests**
   - Uses `--passWithNoTests` flag
   - Not blocking but should be addressed

2. **Go lint violations**
   - 5 unused functions in mod-arch-starter/bff
   - Linter works but code needs cleanup:
     - `forbiddenResponse()` in errors.go
     - `getHandlerOverride()`, `handlerWithOverride()`, `logHandlerOverride()` in extensions.go
     - `setupApiTest()` in test_utils.go

3. **Deprecated npm packages**
   - eslint 8.x (8.57.1) - should upgrade to 9.x
   - glob 7.x - should upgrade to latest
   - inflight, rimraf 3.x - deprecated

4. **Known vulnerabilities**
   - 16 vulnerabilities (4 low, 3 moderate, 9 high)
   - Run `npm audit fix` to address non-breaking fixes
   - Review and update dependencies

5. **envtest assets**
   - Warning: "401 Unauthorized" when fetching kubebuilder-tools
   - Doesn't affect test execution (tests pass without it)

### What Works

✅ Full validation pipeline: install → build → lint → test
✅ All TypeScript/JavaScript tests pass
✅ ESLint with zero warnings
✅ Type checking passes
✅ Single test file execution
✅ Go tests pass
✅ Pre-commit hooks configured
✅ CI configuration complete and gating

### What Doesn't Work

❌ Go lint has violations (code quality issue, not tool issue)
⚠️ npm ci without --ignore-scripts fails (workspace build order)

---

## Quick Reference

### Common Commands

```bash
# Full validation sequence
npm ci --ignore-scripts
npm run build
npm run lint
npm run test

# Per-workspace operations
npm run test:core
npm run build:shared
npm run lint:fix

# Coverage
npm run test:jest -- --coverage

# Single test
cd mod-arch-core && npx jest hooks/__tests__/useModularArchContext.test.tsx

# Go testing
cd mod-arch-starter/bff
make test
make lint
```

### Files to Check After Patching

- TypeScript source: `mod-arch-*/src/**/*.{ts,tsx}`
- Test files: `mod-arch-*/__tests__/**/*.test.{ts,tsx}`
- Go source: `mod-arch-starter/bff/**/*.go`
- Config: `package.json`, `tsconfig.json`, `.eslintrc.cjs`

### Exit Codes

- `0` - Success
- `1` - General failure (tests failed, build error)
- `2` - Lint violations found (linter ran but found issues)

---

## Agent Workflow

For automated patch validation:

1. **Apply patch** to the repository
2. **Start container** (Node 22 + rsync + make + git)
3. **Install deps** (`npm ci --ignore-scripts`)
4. **Build** (`npm run build`) - verify no TypeScript errors
5. **Lint** (`npm run lint`) - verify no violations introduced
6. **Test** (`npm run test`) - verify all tests pass
7. **Cleanup** (remove container)

If all steps pass with exit code 0, the patch is validated. If any step fails, the patch needs revision.

**Expected runtime:** ~3-5 minutes (first run with npm install), ~1-2 minutes (subsequent runs with cached deps)
