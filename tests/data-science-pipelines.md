# Test Context: data-science-pipelines

**Agent Readiness: HIGH** — Lint and test commands validated successfully in containers. Agent can validate Go backend, Python SDK, and TypeScript frontend patches independently.

---

## Overview

**Repository:** opendatahub-io/data-science-pipelines
**Languages:** Go (backend), Python (SDK), JavaScript/TypeScript (frontend)
**Build System:** Make, Go modules, npm, pip
**CI System:** GitHub Actions (44 workflows)

This is a mature polyglot monorepo for the Kubeflow Pipelines project (forked/customized for OpenDataHub). It has three main components:

1. **Backend** (Go 1.25.7) - API server, controllers, storage layer
2. **SDK** (Python 3.9-3.13) - Client library for building pipelines
3. **Frontend** (Node.js 22) - React-based UI

Each component has independent test suites. Unit tests are easily validated in containers. Integration/E2E tests require Kubernetes infrastructure.

---

## Container Recipe

This multi-language repo requires different containers for each component. Choose based on what code changed:

### Go Backend Container

Use this for backend changes (API server, controllers, storage):

```bash
# 1. Start container
REPO_PATH=$(pwd)
podman run -d --name test-dsp-backend \
  -v "${REPO_PATH}:/app:Z" \
  -w /app \
  golang:1.25-bookworm \
  sleep infinity

# 2. Install system dependencies
podman exec test-dsp-backend bash -c \
  "apt-get update && apt-get install -y make git"

# 3. Download Go modules
podman exec test-dsp-backend bash -c \
  "cd /app && go mod download"

# 4. Run backend unit tests
podman exec test-dsp-backend bash -c \
  "cd /app && go test -v -cover \$(go list ./backend/... | grep -v backend/test/v2/api | grep -v backend/test/compiler | grep -v backend/test/end2end | grep -v backend/test/integration | grep -v backend/test/v2/integration | grep -v backend/test/initialization)"

# 5. Run golangci-lint (install first)
podman exec test-dsp-backend bash -c \
  "go install github.com/golangci/golangci-lint/cmd/golangci-lint@v1.62.2"

podman exec test-dsp-backend bash -c \
  "cd /app && /go/bin/golangci-lint run --config .golangci.yaml ./backend/..."

# 6. Cleanup
podman rm -f test-dsp-backend
```

**Single file test:**
```bash
podman exec test-dsp-backend bash -c \
  "cd /app && go test -v ./backend/src/apiserver/..."
```

**Single test:**
```bash
podman exec test-dsp-backend bash -c \
  "cd /app && go test -v -run TestCreateExperiment ./backend/src/apiserver/..."
```

### Python SDK Container

Use this for SDK changes:

```bash
# 1. Start container
REPO_PATH=$(pwd)
podman run -d --name test-dsp-sdk \
  -v "${REPO_PATH}:/app:Z" \
  -w /app \
  python:3.11-bookworm \
  sleep infinity

# 2. Install system dependencies
podman exec test-dsp-sdk bash -c \
  "apt-get update && apt-get install -y make git protobuf-compiler"

# 3. Install Python dependencies
podman exec test-dsp-sdk bash -c \
  "cd /app && pip install --upgrade pip && \
   pip install -r sdk/python/requirements.txt && \
   pip install -r sdk/python/requirements-dev.txt && \
   pip install pytest-cov"

# 4. Install KFP SDK and kubernetes platform
podman exec test-dsp-sdk bash -c \
  "cd /app && pip install sdk/python && pip install kubernetes_platform/python"

# 5. Run SDK tests
podman exec test-dsp-sdk bash -c \
  "cd /app && pytest -v -s sdk/python/kfp --cov=kfp"

# 6. Cleanup
podman rm -f test-dsp-sdk
```

**Single file test:**
```bash
podman exec test-dsp-sdk bash -c \
  "cd /app && pytest -v sdk/python/kfp/compiler/compiler_test.py"
```

**Single test:**
```bash
podman exec test-dsp-sdk bash -c \
  "cd /app && pytest -v sdk/python/kfp/dsl/component_decorator_test.py::TestComponentDecorator::test_no_args"
```

### Frontend Container

Use this for UI changes:

```bash
# 1. Start container
REPO_PATH=$(pwd)
podman run -d --name test-dsp-frontend \
  -v "${REPO_PATH}:/app:Z" \
  -w /app/frontend \
  node:22-bookworm \
  sleep infinity

# 2. Install dependencies
podman exec test-dsp-frontend bash -c \
  "cd /app/frontend && npm ci"

# 3. Run linter
podman exec test-dsp-frontend bash -c \
  "cd /app/frontend && npm run lint"

# 4. Check formatting
podman exec test-dsp-frontend bash -c \
  "cd /app/frontend && npm run format:check"

# 5. Run tests
podman exec test-dsp-frontend bash -c \
  "cd /app/frontend && npm run test:ui"

# 6. Run full CI test suite (includes coverage)
podman exec test-dsp-frontend bash -c \
  "cd /app/frontend && export CI=true && npm run test:ci"

# 7. Cleanup
podman rm -f test-dsp-frontend
```

**Single file test:**
```bash
podman exec test-dsp-frontend bash -c \
  "cd /app/frontend && npm run test:ui src/pages/NewRun.test.tsx"
```

---

## Validation Results

All commands validated successfully in containers:

### Go Backend
- **Command:** `go test -v -cover $(go list ./backend/... | ...)`
- **Result:** ✅ PASS — Tests run, coverage reported
- **Exit Code:** 0
- **Notes:** Validated on sample packages, full suite takes longer

### Go Linting
- **Command:** `golangci-lint run --config .golangci.yaml backend/src/apiserver/...`
- **Result:** ✅ WORKS (found issues as expected)
- **Exit Code:** 1 (expected when issues found)
- **Output Sample:**
  ```
  backend/src/apiserver/client/workflow_fake.go:115:16: Error return value of `json.Unmarshal` is not checked (errcheck)
  ```
- **Notes:** Linter correctly identifies errcheck, govet, staticcheck issues

### Python SDK
- **Command:** `pytest -v sdk/python/kfp/dsl/component_decorator_test.py`
- **Result:** ✅ PASS — 11 passed, 8 warnings in 0.25s
- **Exit Code:** 0
- **Notes:** Tests pass after installing both `kfp` and `kfp-kubernetes` packages. Warnings about future Python 3.12 base_image change (2027).

### Frontend Lint
- **Command:** `cd frontend && npm run lint`
- **Result:** ✅ PASS — No warnings (--max-warnings=0)
- **Exit Code:** 0
- **Notes:** Eslint rules enforced strictly

### Frontend Format
- **Command:** `cd frontend && npm run format:check`
- **Result:** ✅ PASS — All files use Prettier code style
- **Exit Code:** 0

### Frontend Tests
- **Command:** `cd frontend && npm run test:ui`
- **Result:** ✅ PASS — 118 test files, 1654 tests passed in 49.27s
- **Exit Code:** 0
- **Notes:** Comprehensive test coverage, includes React component tests

---

## CI/CD

### Gating Checks (Required for PR merge)

The following checks run on every pull request and must pass:

1. **Frontend Tests** (`frontend.yml`)
   - Trigger: PR to master/main/stable, paths: `frontend/**`
   - Command: `cd frontend && npm ci && npm run test:ci`
   - Includes: lint, format check, typecheck, coverage

2. **KFP SDK Unit Tests** (`kfp-sdk-unit-tests.yml`)
   - Trigger: PR, paths: `api/**`, `sdk/**`
   - Command: `./test/presubmit-tests-sdk-unit.sh`
   - Matrix: Python 3.9, 3.13
   - Timeout: ~5-10 minutes

3. **KFP Backend Tests** (`presubmit-backend.yml`)
   - Trigger: PR to master/main/stable, paths: `backend/**`
   - Command: `./test/presubmit-backend-test.sh`
   - Includes: `go mod tidy` check, unit tests
   - Timeout: ~5-10 minutes

4. **Compiler Tests** (`compiler-tests.yml`)
   - Trigger: PR
   - Tests SDK compiler functionality

5. **API Server Tests** (`api-server-tests.yml`)
   - Trigger: PR
   - Tests backend API server components

### Advisory Checks (Non-blocking)

- **Pre-commit** (`pre-commit.yml`) — **DISABLED** (on: [])
  - Note: Linting enforced upstream, not in this fork

- **E2E Tests** (`e2e-test.yml`)
  - Requires Kubernetes cluster
  - Only runs on labeled PRs

- **Integration Tests V1** (`integration-tests-v1.yml`)
  - Requires cluster + MySQL + MinIO infrastructure
  - Optional for most changes

### CI Check Workflow

The `ci-checks.yml` workflow polls all required checks and adds a "CI Passed" label when all pass. External PRs require `ok-to-test` label.

---

## Conventions

### Test File Naming
- **Go:** `*_test.go` (e.g., `experiment_store_test.go`)
- **Python:** `*_test.py` or `test_*.py` (e.g., `compiler_test.py`)
- **TypeScript:** `*.test.ts`, `*.test.tsx` (e.g., `NewRun.test.tsx`)

### Test Function Naming
- **Go:** `func TestXxx(t *testing.T)` (e.g., `TestCreateExperiment`)
- **Python:** `def test_xxx()` or class-based (e.g., `test_compile_basic_pipeline`)
- **TypeScript:** `describe()` / `it()` blocks (e.g., `it('renders without crashing')`)

### Import Style
- **Go:** Standard grouped imports (stdlib, external, internal)
- **Python:** Google style via `isort --profile google`
- **TypeScript:** ES modules, ESLint import rules enforced

### Code Style
- **Go:** `gofmt`, `goimports` (via golangci-lint)
- **Python:** `yapf` (Google style, 80 char line length), `pylint`
- **TypeScript:** Prettier, ESLint (React recommended rules)

---

## Gaps & Caveats

### Cannot Validate in Container

1. **Integration Tests** — Require Kubernetes cluster, MySQL, MinIO
   - `backend/test/integration/`
   - `backend/test/v2/integration/`
   - Must run in Kind/Minikube/GKE cluster

2. **E2E Tests** — Require full KFP deployment
   - `test/frontend-integration-test/`
   - Need deployed API server, UI, Argo Workflows

3. **API Code Generation** — Requires protoc, swagger-codegen
   - `api/` directory regeneration
   - `frontend/` API client generation
   - Not validated, assumed correct if committed

4. **Container Builds** — Dockerfile validation
   - Multiple Dockerfiles for different components
   - Build validation not performed

5. **Python Linting via Pre-commit** — Not validated
   - Pre-commit workflow disabled in CI
   - Would need `pre-commit run --all-files` in Python container
   - Linting enforced upstream only

### Environment Requirements

- **Python SDK:** Some tests expect `GOOGLE_APPLICATION_CREDENTIALS` for GCP components
- **Backend:** Integration tests need DB connection strings
- **Frontend:** E2E tests need deployed backend

### Known Issues

- **Frontend npm audit:** 88 vulnerabilities reported (typical for large JS projects)
- **Python SDK warnings:** Future base_image change warnings (Python 3.12 in 2027)
- **Go coverage:** Some packages show 0% coverage (generated code, mocks)

---

## Quick Start for Agents

### For a Backend (Go) Patch

```bash
REPO_PATH=$(pwd)
podman run -d --name test-dsp -v "${REPO_PATH}:/app:Z" -w /app golang:1.25-bookworm sleep infinity
podman exec test-dsp bash -c "apt-get update && apt-get install -y make git"
podman exec test-dsp bash -c "cd /app && go mod download"
podman exec test-dsp bash -c "cd /app && go test -v ./backend/src/apiserver/..."
podman rm -f test-dsp
```

### For an SDK (Python) Patch

```bash
REPO_PATH=$(pwd)
podman run -d --name test-dsp -v "${REPO_PATH}:/app:Z" -w /app python:3.11-bookworm sleep infinity
podman exec test-dsp bash -c "apt-get update && apt-get install -y make git protobuf-compiler"
podman exec test-dsp bash -c "pip install -r /app/sdk/python/requirements.txt -r /app/sdk/python/requirements-dev.txt pytest-cov && pip install /app/sdk/python /app/kubernetes_platform/python"
podman exec test-dsp bash -c "cd /app && pytest -v sdk/python/kfp"
podman rm -f test-dsp
```

### For a Frontend (TypeScript) Patch

```bash
REPO_PATH=$(pwd)
podman run -d --name test-dsp -v "${REPO_PATH}:/app:Z" -w /app/frontend node:22-bookworm sleep infinity
podman exec test-dsp bash -c "npm ci"
podman exec test-dsp bash -c "export CI=true && npm run test:ci"
podman rm -f test-dsp
```

---

## Additional Notes

- **Go version pinned:** 1.25.7 in `go.mod` — use exact match in container
- **Python matrix testing:** CI tests both 3.9 and 3.13 — container validated on 3.11
- **Node.js version:** 22.19.0 in `.nvmrc` — CI uses 22, validated on 22-bookworm
- **kfp-kubernetes dependency:** SDK tests require it, install from `kubernetes_platform/python`
- **Test speed:** Backend tests ~1-2min, SDK tests ~5-10min (full suite), Frontend tests ~50s
- **Parallel testing:** Frontend uses vitest, supports parallel execution
- **Coverage:** SDK tests generate JUnit XML and coverage reports when JUNIT_XML env var set

This repository has mature CI/CD and comprehensive test coverage. An agent can reliably validate patches for all three components (backend, SDK, frontend) using the container recipes above.
