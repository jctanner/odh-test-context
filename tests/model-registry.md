# Model Registry - Test Context & Validation Runbook

**Repository:** opendatahub-io/model-registry
**Analyzed:** 2026-03-22
**Agent Readiness:** **medium** — Lint and build validated successfully. Unit tests work in container. Most tests require external infrastructure (MySQL/PostgreSQL via testcontainers, Kubernetes clusters for E2E).

---

## Overview

**Languages:** Go 1.25.7 (primary), Python 3.10-3.14 (client), TypeScript (UI)
**Build System:** Makefile + Go modules (Go), Poetry + Nox (Python), npm (TypeScript)
**Test Frameworks:** Go testing (unit/integration), pytest + nox (Python)

### What an agent can do:
- ✅ Lint Go code with golangci-lint and go vet
- ✅ Build the Go binary
- ✅ Run pure Go unit tests (e.g., converter package)
- ✅ Lint Python code with ruff and mypy
- ⚠️ Run integration tests (requires Docker for testcontainers)
- ⚠️ Run Python E2E tests (requires Kubernetes cluster, model-registry deployment, Minio)

---

## Container Recipe

This is a **complete, copy-paste recipe** for validating Go patches in a container.

### Step 1: Start Container

```bash
podman run -d \
  --name test-context-model-registry \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.25.7 \
  sleep infinity
```

**Base image:** `golang:1.25.7` (Debian-based, includes make, git, curl, wget pre-installed)

### Step 2: Install System Dependencies

```bash
podman exec test-context-model-registry bash -c \
  "apt-get update && apt-get install -y npm"
```

**Required:** npm (for openapi-generator-cli, if running code generation)
**Pre-installed:** make, git, curl, wget

### Step 3: Install Go Dependencies

```bash
podman exec test-context-model-registry bash -c \
  "cd /app && go mod download"
```

**Result:** ✅ Validated — downloads all Go module dependencies.

### Step 4: Install golangci-lint

```bash
podman exec test-context-model-registry bash -c \
  "cd /app && curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b ./bin v2.9.0"
```

**Result:** ✅ Validated — installs golangci-lint v2.9.0 to ./bin/

### Step 5: Run go vet

```bash
podman exec test-context-model-registry bash -c \
  "cd /app && go vet \$(go list ./... | grep -vF github.com/kubeflow/model-registry/internal/db/filter)"
```

**Result:** ✅ Validated — exit code 0, no vet issues.
**Note:** Excludes `internal/db/filter` package due to participle struct tags.

### Step 6: Run golangci-lint

```bash
# Lint main.go
podman exec test-context-model-registry bash -c \
  "cd /app && ./bin/golangci-lint run main.go --timeout 3m"

# Lint all packages
podman exec test-context-model-registry bash -c \
  "cd /app && ./bin/golangci-lint run cmd/... internal/... ./pkg/... --timeout 3m"
```

**Result:** ✅ Validated — exit code 0, "0 issues." output.
**Note:** No .golangci.yaml config in root; uses golangci-lint defaults.

### Step 7: Build the Binary

```bash
podman exec test-context-model-registry bash -c \
  "cd /app && go build -buildvcs=false"
```

**Result:** ✅ Validated — exit code 0, creates `model-registry` binary (34M).
**Note:** Skips VCS stamping with `-buildvcs=false`. Assumes generated code already exists (if not, run `make gen` first, which requires npm and openapi-generator).

### Step 8: Run Unit Tests

```bash
# Pure unit tests (no external dependencies)
podman exec test-context-model-registry bash -c \
  "cd /app && go test ./internal/converter -count=1"
```

**Result:** ✅ Validated — exit code 0, "ok" in 0.011s.

```bash
# Full test suite (requires testcontainers - will fail in simple container)
podman exec test-context-model-registry bash -c \
  "cd /app && go test \$(go list ./internal/... ./pkg/... | grep -v controller)"
```

**Result:** ❌ Requires Docker — fails with "panic: rootless Docker not found".
**Why:** Most tests use testcontainers-go to spin up MySQL/PostgreSQL containers.
**Workaround:** Use Docker-in-Docker or bind-mount Docker socket (`-v /var/run/docker.sock:/var/run/docker.sock`).

### Step 9: Run Single Test or Package

```bash
# Single package
podman exec test-context-model-registry bash -c \
  "cd /app && go test ./internal/converter -v"

# Single test function
podman exec test-context-model-registry bash -c \
  "cd /app && go test -run TestMapEmbedMDCustomProperties ./internal/converter -v"

# With filter pattern
podman exec test-context-model-registry bash -c \
  "cd /app && go test -run TestMap ./internal/converter -v"
```

### Step 10: Cleanup

```bash
podman rm -f test-context-model-registry
```

**Always clean up the container when done.**

---

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Dependencies | `go mod download` | 0 | ✅ Pass | All modules downloaded |
| Go vet | `go vet $(go list ...)` | 0 | ✅ Pass | No vet issues |
| Lint (main.go) | `golangci-lint run main.go --timeout 3m` | 0 | ✅ Pass | 0 issues |
| Lint (packages) | `golangci-lint run cmd/... internal/... ./pkg/... --timeout 3m` | 0 | ✅ Pass | 0 issues |
| Build | `go build -buildvcs=false` | 0 | ✅ Pass | 34M binary created |
| Unit tests | `go test ./internal/converter` | 0 | ✅ Pass | Pure unit tests work |
| Integration tests | `go test $(go list ...)` | 1 | ❌ Fail | Requires testcontainers/Docker |

**Summary:** Install OK, vet OK, lint OK (0 issues), build OK (34M binary), unit tests OK. Integration tests require Docker/testcontainers.

---

## CI/CD

### Gating Checks (GitHub Actions)

These workflows run on all pull requests and must pass to merge:

#### 1. **prepare** (`.github/workflows/prepare.yml`)
```bash
make clean build/prepare
```
- Runs: `make gen` (code generation), `make vet`, `make lint`
- Checks for uncommitted file changes after generation
- Ensures code is properly formatted and generated code is in sync

#### 2. **build** (`.github/workflows/build.yml`)
```bash
make build/compile
make test-cover
make -C catalog test-cover
```
- Compiles the Go binary
- Runs main registry unit tests with coverage
- Runs catalog unit tests with coverage
- Uploads coverage to Codecov

#### 3. **python-lint** (`.github/workflows/python-tests.yml`)
```bash
cd clients/python
nox --python=3.10 --session=lint
nox --python=3.10 --session=mypy
```
- Runs ruff linter on Python client
- Runs mypy type checker

#### 4. **python-test** (`.github/workflows/python-tests.yml`)
```bash
cd clients/python
nox --python=3.12 --session=tests
```
- Runs Python unit tests

#### 5. **python-e2e** (`.github/workflows/python-tests.yml`)
```bash
# Requires: kind cluster, model-registry deployed, Minio, OCI registry
cd clients/python
kubectl port-forward -n kubeflow service/model-registry-service 8080:8080 &
kubectl port-forward -n minio svc/minio 9000:9000 &
nox --python=3.12 --session=e2e -- --cov-report=xml
```
- Deploys model-registry to kind cluster
- Runs end-to-end tests against live deployment
- Tests with MySQL and PostgreSQL databases
- Tests with Minio S3 storage

#### 6. **controller-test** (`.github/workflows/controller-test.yml`)
Only runs when controller paths change:
```bash
cd cmd/controller && go mod tidy
cd pkg/inferenceservice-controller && go mod tidy
make controller/test
```
- Runs controller unit tests with KUBEBUILDER_ASSETS

### What CI Actually Tests

**On every PR:**
- Go code generation is up to date
- Go vet passes
- golangci-lint passes (0 issues)
- Go build succeeds
- Go unit tests pass (with coverage)
- Python lint (ruff) passes
- Python type checking (mypy) passes
- Python unit tests pass
- Python E2E tests pass (against Kubernetes)

**On specific path changes:**
- Controller tests (when `cmd/controller/**` changes)
- CSI tests (when `cmd/csi/**` changes)

---

## Conventions

### Test File Naming
- **Go:** `*_test.go` (adjacent to source files)
- **Python:** `tests/**/*.py` or `test_*.py`

### Test Function Naming
- **Go:** `func TestFunctionName(t *testing.T)`
- **Python:** `def test_function_name()` or pytest markers like `@pytest.mark.e2e`

### Import Style
- **Go:** Grouped imports (stdlib, external, internal)
- **Python:** Absolute imports from `model_registry` package

### Test Patterns
- **Go:** Uses `testcontainers-go` for integration tests with MySQL/PostgreSQL
- **Python:** Uses `pytest` with `nox` for orchestration, supports E2E markers
- **Coverage:** Tracked via Codecov for both Go and Python

### Test Markers (Python)
```python
@pytest.mark.e2e  # End-to-end tests (require Kubernetes)
@pytest.mark.fuzz  # Fuzz/property-based tests
```

---

## Gaps & Caveats

### 1. **Integration Tests Require Docker**
Most Go tests use `testcontainers-go` to run MySQL and PostgreSQL containers. These fail in a simple container with:
```
panic: rootless Docker not found
```

**Workaround:**
- Use Docker-in-Docker
- Bind-mount Docker socket: `-v /var/run/docker.sock:/var/run/docker.sock`
- Run on host with Docker available
- Or run only pure unit tests like `go test ./internal/converter`

### 2. **Python E2E Tests Require Full Infrastructure**
Python E2E tests require:
- Kubernetes cluster (kind)
- model-registry deployment
- Minio S3 storage
- OCI registry
- Port-forwarding to services

These cannot run in a simple container validation.

### 3. **Code Generation Not Validated**
The `make gen` target (required for full build) was not validated because it requires:
- npm and openapi-generator-cli
- Complex setup with Go code generation tools (goverter, genqlient)
- Database migrations for GORM code generation

The validation used existing generated code.

### 4. **Controller Tests Require Kubernetes**
Controller tests need `KUBEBUILDER_ASSETS` environment variable set by `setup-envtest`. They cannot run without Kubernetes test environment.

### 5. **No Root golangci-lint Config**
The project doesn't have a `.golangci.yaml` in the root directory. It uses golangci-lint defaults. There is a config in `clients/ui/bff/.golangci.yaml` for the UI BFF component.

### 6. **Catalog Tests Also Need Testcontainers**
The catalog (`make -C catalog test`) also uses testcontainers for PostgreSQL, so it has the same Docker dependency as the main tests.

---

## Python Client Testing

The Python client (`clients/python/`) uses a separate test infrastructure:

### Setup
```bash
cd clients/python
poetry install
```

### Lint
```bash
# Using nox (recommended)
nox --session=lint

# Direct
poetry run ruff check
```

### Type Check
```bash
# Using nox
nox --session=mypy

# Direct
poetry run mypy .
```

### Unit Tests
```bash
nox --session=tests
```

### E2E Tests (Requires Kubernetes)
```bash
# Requires: kind cluster, model-registry deployed, port-forwarding active
nox --session=e2e
```

### Fuzz Tests
```bash
nox --session=fuzz
```

**Config:** `clients/python/pyproject.toml` defines ruff, mypy, pytest settings.
**Test markers:** Use `--e2e` flag or `@pytest.mark.e2e` decorator.

---

## Quick Reference

### Validate a Go Patch (Minimal)
```bash
# In container or on host with Go 1.25.7
go mod download
go vet $(go list ./... | grep -vF internal/db/filter)
curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b ./bin v2.9.0
./bin/golangci-lint run cmd/... internal/... ./pkg/... --timeout 3m
go build -buildvcs=false
go test ./internal/converter  # Pure unit tests
```

### Validate a Python Patch
```bash
cd clients/python
poetry install
nox --session=lint
nox --session=mypy
nox --session=tests
```

### Full CI Simulation (Requires Docker/Kubernetes)
```bash
# Go
make deps
make clean build/prepare  # gen + vet + lint
make build/compile
make test-cover
make -C catalog test-cover

# Python (requires Kubernetes cluster)
cd clients/python
nox --session=lint
nox --session=mypy
nox --session=tests
nox --session=e2e  # Needs K8s cluster with model-registry deployed
```

### Run a Single Go Test
```bash
go test -run TestFunctionName ./path/to/package -v
```

### Run Python Tests with Filter
```bash
cd clients/python
poetry run pytest -k "test_pattern" tests/
```

---

## Agent Recommendations

**For automated patch validation:**

1. **Always run:** go vet, golangci-lint, go build
   - These work in any container with Go 1.25.7
   - Fast feedback (< 2 minutes combined)
   - Catches most code quality issues

2. **Conditionally run:** Pure unit tests like `internal/converter`
   - Works without external dependencies
   - Provides some test coverage signal

3. **Skip or flag as "requires infrastructure":** Integration tests, E2E tests
   - Needs Docker for Go integration tests
   - Needs Kubernetes for Python E2E tests
   - Not practical in simple container validation

4. **For Python patches:** Run nox lint and mypy
   - Fast static analysis
   - Works without Kubernetes

**Agent readiness: medium** — An agent can provide strong linting and build validation. Test validation is limited to pure unit tests unless Docker/Kubernetes infrastructure is available.
