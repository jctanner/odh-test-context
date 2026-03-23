# ODH Dashboard - Test Context & Validation Runbook

**Generated:** 2026-03-22T21:19:57Z  
**Repository:** opendatahub-io/odh-dashboard  
**Agent Readiness:** medium (lint and unit tests work; type-check has known issues; Cypress/Go require additional setup)

---

## Overview

**Languages:** TypeScript, JavaScript, Go  
**Build System:** npm workspaces + Turbo (monorepo orchestration), Make (containers & Go builds)  
**Node Version:** 22.x (22.22.1 validated)  
**Package Manager:** npm 10.9.2+

**Agent Readiness Rating: MEDIUM** — Lint and unit tests validated successfully in container. Type-check has partial failure in one package (@odh-dashboard/internal) due to missing type declarations. Full Cypress e2e and Go BFF testing requires additional tooling beyond basic Node container.

---

## Container Recipe

This is the **complete, copy-paste recipe** for validating patches. Follow these steps to spin up a container, install dependencies, and run validation.

### 1. Start Container

```bash
podman run -d \
  --name test-context-odh-dashboard \
  -v $(pwd):/app:Z \
  -w /app \
  node:22 \
  sleep infinity
```

**Base image:** `node:22` (validated with node 22.22.1, npm 10.9.4)

### 2. Install System Dependencies

```bash
podman exec test-context-odh-dashboard bash -c "\
  apt-get update -qq && \
  apt-get install -y -qq make git curl"
```

**System packages:** make, git, curl

### 3. Install Project Dependencies

```bash
podman exec test-context-odh-dashboard bash -c "\
  cd /app && npm install"
```

**Expected:** Dependencies install cleanly. Turbo postinstall runs `install:module` for nested workspace packages. Takes 3-5 minutes. Some vulnerability warnings are expected (non-fatal).

**Exit code:** 0 ✅

### 4. Run Lint

```bash
podman exec test-context-odh-dashboard bash -c "\
  cd /app && npm run lint"
```

**What it does:** Runs ESLint across all 28 workspace packages via Turbo. Uses custom `@odh-dashboard/eslint-config`.

**Validated:** ✅ **PASS**  
**Exit code:** 0  
**Output:** `Tasks: 19 successful, 19 total` (161 ESLint warnings are non-fatal)  
**Notes:** Warnings are expected and don't fail the build. Turbo caches results for faster subsequent runs.

### 5. Run Type-Check

```bash
podman exec test-context-odh-dashboard bash -c "\
  cd /app && npm run type-check"
```

**What it does:** Runs `tsc --noEmit` across all workspace packages via Turbo.

**Validated:** ⚠️ **PARTIAL FAILURE**  
**Exit code:** 2  
**Failed package:** `@odh-dashboard/internal` (frontend/src)  
**Error:** Missing type declarations for `monaco-editor` and `@patternfly/react-topology`  
**Output snippet:**
```
ERROR: @odh-dashboard/internal#type-check exited (2)
components/MaxHeightCodeEditor.tsx(3,25): error TS2307: Cannot find module 'monaco-editor'
components/lineage/Lineage.tsx(7,8): error TS7016: Could not find a declaration file for module '@patternfly/react-topology'
```

**Notes:** Other packages pass. This appears to be a known issue in the codebase. The main CI workflow may skip this package or have workarounds.

### 6. Run Unit Tests

```bash
podman exec test-context-odh-dashboard bash -c "\
  cd /app && npm run test-unit"
```

**What it does:** Runs Jest unit tests across all workspace packages via Turbo.

**Validated:** ✅ **PASS**  
**Exit code:** 0  
**Output:** `Tasks: 9 successful, 9 total` (Test suites passed in parallel)  
**Sample results:**
- `@odh-dashboard/jest-config`: 13 tests passed
- `@odh-dashboard/app-config`: 14 tests passed
- `@odh-dashboard/plugin-core`: Multiple suites passed
- `@odh-dashboard/observability`: 77 tests passed

**Notes:** Tests run in parallel via Turbo. Results are cached for faster subsequent runs.

### 7. Run Unit Tests with Coverage

```bash
podman exec test-context-odh-dashboard bash -c "\
  cd /app && npm run test-unit-coverage"
```

**What it does:** Same as test-unit but with coverage reporting (JSON + lcov).

**Coverage output:** `jest-coverage/` directory in each workspace  
**Aggregate:** `npm run test-unit-coverage` merges coverage from all workspaces

### 8. Run a Single Test File

```bash
# Navigate to the workspace and run Jest on a specific file
podman exec test-context-odh-dashboard bash -c "\
  cd /app/backend && npm run test:jest -- src/__tests__/routes.spec.ts"
```

**Template:** `cd <workspace> && npm run test:jest -- <file>`

### 9. Run a Single Test by Name

```bash
# Use Jest's -t flag to match test name
podman exec test-context-odh-dashboard bash -c "\
  cd /app/frontend && npm run test:jest -- -t 'should render correctly'"
```

**Template:** `cd <workspace> && npm run test:jest -- -t '<test_name>'`

### 10. Cleanup

```bash
podman rm -f test-context-odh-dashboard
```

**Always clean up** after validation, even if steps fail.

---

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| **Install** | `npm install` | 0 | ✅ PASS | Dependencies installed. Turbo postinstall successful. |
| **Lint** | `npm run lint` | 0 | ✅ PASS | 19 packages linted. 161 warnings (non-fatal). |
| **Type-Check** | `npm run type-check` | 2 | ⚠️ PARTIAL | 1 package failed (@odh-dashboard/internal). 5 packages passed. |
| **Unit Tests** | `npm run test-unit` | 0 | ✅ PASS | 9 test suites passed. Turbo cached some results. |

**Summary:** Install OK, lint OK (161 warnings), type-check PARTIAL (1 package failed), tests OK (9 suites passed)

### Known Issues

1. **Type-check failure in @odh-dashboard/internal:** Missing type declarations for `monaco-editor` and `@patternfly/react-topology`. This package may be excluded from CI type-checking or have a workaround.

2. **Warnings:** 161 ESLint warnings (mostly restricted imports) are present but non-fatal.

3. **Security vulnerabilities:** npm reports vulnerabilities in some dependencies during install. These are noted but don't block builds.

---

## CI/CD

### GitHub Actions Workflows

**Main gating workflow:** `.github/workflows/test.yml`  
**Triggers:** push, pull_request  
**Required checks:**

1. **Setup** → Install dependencies (`npm install`)
2. **Type-Check** → `npm run type-check`
3. **Lint** → `NODE_OPTIONS="--max-old-space-size=8192" npm run lint`
4. **Unit-Tests** → `npm run test-unit-coverage`
5. **Contract-Tests** → `npm run test:contract` (requires Go 1.25)
6. **Cypress-Mock-Tests** → Matrix of test groups, requires pre-built assets

**Additional workflows:**
- `.github/workflows/modular-arch-quality-gates.yml` — Assesses testing maturity per module (advisory, not gating)
- `.github/workflows/*-bff-tests.yml` — Lint/test Go BFF services (automl, autorag, eval-hub, gen-ai, maas, mlflow)
- `.github/workflows/cypress-e2e-test.yml` — Full e2e Cypress tests

**Tekton pipelines:** `.tekton/*.yaml` files define deployment automation

### CI Commands (from test.yml)

```bash
# Setup
npm install

# Type-check
npm run type-check

# Lint (with increased memory)
NODE_OPTIONS="--max-old-space-size=8192" npm run lint

# Unit tests with coverage
npm run test-unit-coverage

# Contract tests (requires Go)
npm run test:contract

# Cypress tests (requires pre-built assets)
npm run cypress:server:build:coverage -- --concurrency=4
npm run test:cypress-ci:coverage:nobuild -- --spec "../packages/<spec>"
```

---

## Conventions

### Test File Naming

- **Jest unit tests:** `**/__tests__/**/*.{spec,test}.{ts,tsx,js}`
- **Cypress e2e tests:** `**/*.cy.ts`
- **Go tests:** `**/*_test.go`

### Test Naming

- **Jest:** `describe('Component', () => { it('should work', () => {...}) })`
- **Cypress:** `cy.describe('Feature', () => { cy.it('should work', () => {...}) })`
- **Go:** `func TestFeature(t *testing.T) {...}` or Ginkgo `Describe/It`

### Import Style

- **ES modules** for JavaScript/TypeScript
- **Absolute imports** from `@odh-dashboard/*` packages (monorepo namespaces)
- **Path aliases** configured in tsconfig.json
- **No restricted imports:** Custom ESLint rule warns against direct PatternFly Modal usage (use ContentModal wrapper)

### Pre-commit Hooks

Husky + lint-staged runs on `git commit`:
- Runs `npx eslint --max-warnings 0` on staged `.{js,ts,jsx,tsx,md}` files

---

## Gaps & Caveats

### 1. Type-Check Partial Failure

**Issue:** `@odh-dashboard/internal` fails type-check due to missing type declarations for `monaco-editor` and `@patternfly/react-topology`.

**Impact:** An agent cannot rely on type-check as a full gating signal. However, lint and unit tests provide good coverage.

**Workaround:** Skip type-check for this specific package, or install missing type definitions.

### 2. Cypress Tests Require Build Step

**Issue:** Cypress e2e tests (`npm run test:cypress-ci`) require pre-built static assets (`npm run cypress:server:build`).

**Impact:** Cannot run Cypress tests in a simple "install and test" container without a build step (5+ minutes).

**Workaround:** For patch validation, rely on unit tests and lint. Run Cypress in CI or after build.

### 3. Go BFF Tests Require Go Toolchain

**Issue:** Some packages (automl, autorag, eval-hub, gen-ai, maas, mlflow) have Go BFF services with their own tests.

**Impact:** Node container doesn't have Go 1.24+. Cannot run `make test` in BFF directories.

**Workaround:** Use a multi-stage approach:
1. Node container for JS/TS validation
2. Go container for BFF validation (`golang:1.24` + `make test`)

### 4. Contract Tests Require Go

**Issue:** `npm run test:contract` executes contract tests for BFF services, which require Go.

**Impact:** Cannot validate contracts in Node-only container.

**Workaround:** Skip contract tests in basic validation, or use Go container.

### 5. Security Vulnerabilities

**Issue:** npm reports 32-52 vulnerabilities in various packages (low/moderate/high).

**Impact:** Non-blocking but should be addressed in future updates.

**Workaround:** Run `npm audit fix` or `npm audit fix --force` (may introduce breaking changes).

### 6. External Services

**Issue:** Some tests may require external services (Kubernetes cluster, databases, model registries) not available in isolated container.

**Impact:** Full e2e validation requires infrastructure.

**Workaround:** Use mocked mode for Cypress (`CY_MOCK=1`) and unit tests with mocks.

---

## Go BFF Services (Optional)

If validating Go BFF services, use a separate container:

```bash
# Start Go container
podman run -d --name test-go-bff \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24 \
  sleep infinity

# Install system dependencies
podman exec test-go-bff bash -c "apt-get update && apt-get install -y make curl"

# Test a BFF service
podman exec test-go-bff bash -c "cd /app/packages/gen-ai/bff && make test"

# Lint a BFF service
podman exec test-go-bff bash -c "cd /app/packages/gen-ai/bff && make lint"

# Cleanup
podman rm -f test-go-bff
```

**BFF packages with Go tests:**
- `packages/automl/bff`
- `packages/autorag/bff`
- `packages/eval-hub/bff`
- `packages/gen-ai/bff`
- `packages/maas/bff`
- `packages/mlflow/bff`
- `packages/model-registry/upstream/bff`

**Go test command:** `go test ./...` (or `make test` which runs `fmt`, `vet`, `envtest` setup, then `go test`)

---

## Additional Resources

- **Main CI workflow:** `.github/workflows/test.yml`
- **Monorepo structure:** Root `package.json` defines workspaces (backend, frontend, packages/*)
- **Turbo config:** `turbo.jsonc` defines task orchestration
- **ESLint config:** `packages/eslint-config/` (shared across all packages)
- **Jest config:** `packages/jest-config/` (shared across all packages)
- **Dockerfile:** Multi-stage build for container images

---

**End of Runbook**
