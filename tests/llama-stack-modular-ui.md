# Test Context: llama-stack-modular-ui

**Agent Readiness**: HIGH — Lint and test commands validated successfully. An agent can clone, patch, lint, and test with clear pass/fail signals.

## Overview

This is a polyglot repository with a TypeScript/React frontend and a Go backend-for-frontend (BFF). Both components have comprehensive linting, type checking, and testing infrastructure that work reliably in standard containers.

- **Languages**: TypeScript, JavaScript (frontend), Go (bff)
- **Build Systems**: npm/webpack (frontend), make/go (bff)
- **Test Frameworks**: Jest + Cypress (frontend), Go test with Ginkgo/Gomega (bff)
- **CI**: GitHub Actions with gating checks on PRs

---

## Container Recipe

### Frontend Validation Container

**Base Image**: `node:20`

**1. Start Container**
```bash
podman run -d --name test-llama-stack-frontend \
  -v $(pwd):/app:Z \
  -w /app/frontend \
  node:20 \
  sleep infinity
```

**2. Install Dependencies**
```bash
podman exec test-llama-stack-frontend bash -c "cd /app/frontend && npm install"
```

**3. Run Lint**
```bash
# ESLint (strict: max-warnings 0)
podman exec test-llama-stack-frontend bash -c "cd /app/frontend && npm run test:lint"
# Exit code 0 = pass, non-zero = lint violations
```

**4. Run Type Check**
```bash
# TypeScript type checking
podman exec test-llama-stack-frontend bash -c "cd /app/frontend && npm run test:type-check"
# Exit code 0 = pass, non-zero = type errors
```

**5. Run Unit Tests**
```bash
# Jest unit tests (77 tests)
podman exec test-llama-stack-frontend bash -c "cd /app/frontend && npm run test:jest"
# Look for "Test Suites: X passed" in output
```

**6. Run Single Test File**
```bash
podman exec test-llama-stack-frontend bash -c "cd /app/frontend && npx jest src/app/utilities/__tests__/axios.spec.ts"
```

**7. Run Single Test**
```bash
podman exec test-llama-stack-frontend bash -c "cd /app/frontend && npx jest -t 'test name pattern'"
```

**8. Cleanup**
```bash
podman rm -f test-llama-stack-frontend
```

---

### BFF Validation Container

**Base Image**: `golang:1.23`

**1. Start Container**
```bash
podman run -d --name test-llama-stack-bff \
  -v $(pwd):/app:Z \
  -w /app/bff \
  golang:1.23 \
  sleep infinity
```

**2. Install Dependencies**
```bash
podman exec test-llama-stack-bff bash -c "cd /app/bff && go mod download"
```

**3. Install Build Tools**
```bash
# Install golangci-lint
podman exec test-llama-stack-bff bash -c "cd /app/bff && make golangci-lint"

# Install envtest (optional, for tests)
podman exec test-llama-stack-bff bash -c "cd /app/bff && make envtest"
```

**4. Run Lint**
```bash
podman exec test-llama-stack-bff bash -c "cd /app/bff && make lint"
# Exit code 0 = pass, uses golangci-lint v1.63.4
```

**5. Run Tests**
```bash
podman exec test-llama-stack-bff bash -c "cd /app/bff && make test"
# Runs: go fmt, go vet, go test ./...
# Exit code 0 = pass, tests in cmd/ and internal/api/ packages
```

**6. Run Build**
```bash
podman exec test-llama-stack-bff bash -c "cd /app/bff && make build"
# Produces binary: bin/bff
```

**7. Run Single Package Tests**
```bash
podman exec test-llama-stack-bff bash -c "cd /app/bff && go test ./cmd"
```

**8. Run Single Test**
```bash
podman exec test-llama-stack-bff bash -c "cd /app/bff && go test -run TestFunctionName ./cmd"
```

**9. Cleanup**
```bash
podman rm -f test-llama-stack-bff
```

---

## Validation Results

### Frontend

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install | `npm install` | ✅ Pass | 1990 packages installed in 38s |
| Lint | `npm run test:lint` | ✅ Pass | ESLint: 0 warnings, 0 errors |
| Type Check | `npm run test:type-check` | ✅ Pass | TypeScript: no type errors |
| Unit Tests | `npm run test:jest` | ✅ Pass | 6 suites, 77 tests passed in 1.965s |

**Frontend Test Output Sample**:
```
PASS src/app/utilities/__tests__/useDocumentTitle.spec.ts
PASS src/app/utilities/__tests__/axios.spec.ts
PASS src/app/services/__tests__/llamaStackService.spec.ts
PASS src/app/services/__tests__/authService.spec.ts
PASS src/app/utilities/__tests__/useFetchLlamaModels.spec.ts
PASS src/__tests__/unit/testUtils/hooks.spec.ts

Test Suites: 6 passed, 6 total
Tests:       77 passed, 77 total
```

### BFF

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install | `go mod download` | ✅ Pass | Dependencies downloaded |
| Lint | `make lint` | ✅ Pass | golangci-lint: no issues |
| Test | `make test` | ✅ Pass | 2 packages tested successfully |
| Build | `make build` | ✅ Pass | Binary created: bin/bff |

**BFF Test Output Sample**:
```
ok  	github.com/opendatahub-io/llama-stack-modular-ui/cmd	0.005s
ok  	github.com/opendatahub-io/llama-stack-modular-ui/internal/api	0.003s
```

**Note**: ENVTEST download fails with "401 Unauthorized" from GCS but tests run successfully with empty `ENVTEST_ASSETS`. This is expected in containerized environments.

---

## CI/CD

### Gating Checks

Both workflows trigger on `pull_request` and `push` to `main`.

**Frontend** (`.github/workflows/ui-frontend-build.yml`):
- Node.js 20
- `npm install` → `npm run test` → `npm run clean` → `npm run build`
- `npm run test` includes: lint, type-check, jest, cypress (full suite)
- Checks for uncommitted file changes after build

**BFF** (`.github/workflows/ui-bff-build.yml`):
- Go 1.24.3 (note: go.mod specifies 1.23.5)
- `make clean` → `golangci-lint run` → `make build`
- Uses `golangci/golangci-lint-action@v8` with version v2.1.0
- Checks for uncommitted file changes after build

### Critical Commands (from CI)

**Frontend**:
```bash
cd frontend && npm install
cd frontend && npm run test          # Full suite: lint + type-check + jest + cypress
cd frontend && npm run clean
cd frontend && npm run build
```

**BFF**:
```bash
cd bff && make clean
cd bff && make lint                  # golangci-lint run
cd bff && make build                 # Includes fmt, vet, test, then go build
```

---

## Conventions

### Frontend

**Test File Patterns**:
- Unit tests: `src/__tests__/unit/**/*.spec.ts`
- Inline tests: `**/__tests__/*.spec.ts`, `**/__tests__/*.spec.tsx`
- E2E tests: `src/__tests__/cypress/**/*.ts`

**Test Naming**: Jest describe/it blocks

**Import Style**:
- `~/*` for repository root
- `@app/*` for src/app code
- Enforced by eslint-plugin-no-relative-import-paths

**Code Style**:
- ESLint: max-warnings 0 (strict)
- Prettier: 100 char width, single quotes, trailing commas
- TypeScript strict mode enabled
- No console.log allowed (`no-console` rule)

### BFF

**Test File Pattern**: `*_test.go`

**Test Naming**: `TestXxx` functions, uses Ginkgo `Describe`/`It` for BDD style

**Code Style**:
- `go fmt` enforced
- `go vet` required
- golangci-lint v1.63.4 with default config

---

## Gaps & Caveats

1. **ENVTEST Authentication**: The `setup-envtest` tool fails to download kubebuilder assets from GCS with "401 Unauthorized" in container environments. Tests still run successfully with empty `ENVTEST_ASSETS`, but this warning appears in logs.

2. **Cypress E2E Tests**: Not validated in this analysis. Frontend full test suite (`npm run test`) includes Cypress tests which require:
   - Running dev server: `npm run cypress:server:dev`
   - Waiting for server startup: `wait-on http://localhost:8080`
   - Mock mode: `CY_MOCK=1 CY_WS_PORT=9002`

3. **No golangci-lint Config**: BFF uses default golangci-lint rules (no `.golangci.yml` file found).

4. **Coverage Thresholds**: No explicit coverage thresholds configured, though `npm run test:coverage` is available.

5. **Go Version Mismatch**: CI uses Go 1.24.3 but go.mod specifies 1.23.5. Container validation used 1.23 successfully.

---

## Quick Reference

### Frontend Commands

```bash
# Setup
npm install

# Lint & Format
npm run test:lint         # ESLint (strict)
npm run test:fix          # ESLint auto-fix
npm run format            # Prettier check and write
npm run test:type-check   # TypeScript type checking

# Test
npm run test:jest         # Unit tests only
npm run test:unit         # Unit tests (silent)
npm run test:coverage     # With coverage report
npm run test              # Full suite: lint + type + jest + cypress

# Build
npm run clean             # Remove dist/
npm run build             # webpack production build

# Dev
npm run start:dev         # webpack dev server
```

### BFF Commands

```bash
# Setup
go mod download

# Lint & Format
make fmt                  # go fmt
make vet                  # go vet
make lint                 # golangci-lint
make lint-fix             # golangci-lint --fix

# Test
make test                 # go test ./...
go test ./cmd             # Single package
go test -run TestName ./cmd  # Single test

# Build
make build                # Produces bin/bff
make clean                # Remove bin/

# Run
make run                  # Run with default config
```

---

## For AI Agents

**To validate a patch**:

1. Apply the patch to the working tree
2. Choose the appropriate container recipe above (frontend or bff, or both)
3. Run install → lint → test → build
4. Exit codes: 0 = pass, non-zero = fail
5. Parse output for "X passed" or error messages

**Single file changes**:
- Frontend: `npx jest {changed_file}.spec.ts`
- BFF: `go test {package_containing_change}`

**Expected runtime**:
- Frontend install: ~40s
- Frontend lint: ~5s
- Frontend type-check: ~5s
- Frontend jest: ~2s
- BFF install: ~5s
- BFF lint: ~10s (first run downloads golangci-lint)
- BFF test: ~1s
- BFF build: ~3s

**Reliability**: HIGH. All commands validated in clean containers with reproducible results.
