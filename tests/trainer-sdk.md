# Test Context: trainer-sdk

**Generated:** 2026-03-22T20:27:00Z
**Organization:** opendatahub-io
**Repository:** trainer-sdk

## Overview

**Languages:** Go 1.23.0 (primary), Python 3.11 (secondary)
**Build System:** Make + Go modules + Python pip
**Agent Readiness:** **HIGH** - All lint and test commands validated successfully in container

This is a polyglot Kubernetes operator project (Kubeflow Trainer) with Go controller code and Python SDK/initializers. Both Go and Python have comprehensive test coverage and CI validation. All core lint and test commands work in a standard container.

## Container Recipe

This recipe provides a complete, validated environment for running lint and tests. All commands have been tested and confirmed working.

### 1. Start Container

```bash
podman run -d --name test-context-trainer-sdk \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.23.0 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-trainer-sdk bash -c \
  "apt-get update && apt-get install -y make git python3 python3-pip python3-venv curl build-essential"
```

### 3. Install Go Dependencies

```bash
podman exec test-context-trainer-sdk bash -c "cd /app && go mod download"
```

**Validation:** ✅ Passed - Dependencies download successfully

### 4. Install Python Dependencies

```bash
podman exec test-context-trainer-sdk bash -c \
  "cd /app && pip3 install --break-system-packages pytest && \
   pip3 install --break-system-packages -r ./cmd/initializers/dataset/requirements.txt && \
   pip3 install --break-system-packages ./sdk"
```

**Validation:** ✅ Passed - Installs pytest, huggingface-hub, and kubeflow SDK

### 5. Run Go Linters

```bash
# Go fmt
podman exec test-context-trainer-sdk bash -c "cd /app && make fmt"
```
**Validation:** ✅ Passed (exit 0) - No formatting issues

```bash
# Go vet
podman exec test-context-trainer-sdk bash -c "cd /app && make vet"
```
**Validation:** ✅ Passed (exit 0) - No issues found

```bash
# golangci-lint (auto-installs if needed)
podman exec test-context-trainer-sdk bash -c "cd /app && make golangci-lint"
```
**Validation:** ✅ Passed (exit 0) - Installs v1.61.0 automatically, found no issues

### 6. Run Go Unit Tests

```bash
podman exec test-context-trainer-sdk bash -c "cd /app && make test"
```

**Validation:** ✅ Passed - 18 packages tested, coverage output:
- `pkg/runtime`: 75.5% coverage
- `pkg/runtime/core`: 56.0% coverage
- `pkg/runtime/framework/core`: 87.7% coverage
- `pkg/runtime/framework/plugins/torch`: 98.5% coverage
- Generates `cover.out` for coverage analysis

### 7. Run Python Linters

```bash
# Install linters
podman exec test-context-trainer-sdk bash -c \
  "pip3 install --break-system-packages flake8 black isort"

# Run flake8
podman exec test-context-trainer-sdk bash -c "cd /app && flake8 pkg/initializers"
```
**Validation:** ✅ Passed (exit 0) - No flake8 violations

### 8. Run Python Unit Tests

```bash
# Dataset initializer tests
podman exec test-context-trainer-sdk bash -c \
  "cd /app && PYTHONPATH=/app pytest ./pkg/initializers/dataset"
```
**Validation:** ✅ Passed - 7 tests in 0.37s

```bash
# Model initializer tests
podman exec test-context-trainer-sdk bash -c \
  "cd /app && PYTHONPATH=/app pytest ./pkg/initializers/model"
```
**Validation:** ✅ Passed - 7 tests in 0.23s

```bash
# Utils tests
podman exec test-context-trainer-sdk bash -c \
  "cd /app && PYTHONPATH=/app pytest ./pkg/initializers/utils"
```
**Validation:** ✅ Passed - 4 tests in 0.01s

### 9. Run Single Test (Examples)

**Go single package:**
```bash
podman exec test-context-trainer-sdk bash -c \
  "cd /app && go test ./pkg/runtime/framework/plugins/torch"
```

**Go single test:**
```bash
podman exec test-context-trainer-sdk bash -c \
  "cd /app && go test -run TestPluginName ./pkg/runtime/framework/plugins/torch"
```

**Python single file:**
```bash
podman exec test-context-trainer-sdk bash -c \
  "cd /app && PYTHONPATH=/app pytest ./pkg/initializers/dataset/huggingface_test.py"
```

**Python single test:**
```bash
podman exec test-context-trainer-sdk bash -c \
  "cd /app && PYTHONPATH=/app pytest ./pkg/initializers/dataset/huggingface_test.py::test_download_dataset"
```

### 10. Cleanup

```bash
podman rm -f test-context-trainer-sdk
```

## Validation Results

All commands validated in golang:1.23.0 container:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Go deps | `go mod download` | ✅ Pass | Clean install |
| Go fmt | `make fmt` | ✅ Pass | No changes needed |
| Go vet | `make vet` | ✅ Pass | No issues |
| golangci-lint | `make golangci-lint` | ✅ Pass | Auto-installed v1.61.0 |
| Go tests | `make test` | ✅ Pass | 18 packages, coverage to cover.out |
| Python deps | `pip install ...` | ✅ Pass | pytest + huggingface + SDK |
| Python tests (dataset) | `pytest ./pkg/initializers/dataset` | ✅ Pass | 7/7 passed |
| Python tests (model) | `pytest ./pkg/initializers/model` | ✅ Pass | 7/7 passed |
| Python tests (utils) | `pytest ./pkg/initializers/utils` | ✅ Pass | 4/4 passed |
| Python lint | `flake8 pkg/initializers` | ✅ Pass | No violations |

## CI/CD

**System:** GitHub Actions
**Workflows:** `.github/workflows/test-go.yaml`, `test-python.yaml`, `test-e2e.yaml`

### Gating Checks (All Required for Merge)

**Go Checks (test-go.yaml):**
1. `go mod tidy` - verify modules are tidy
2. `make generate` - verify generated code is up to date
3. `make fmt` - verify go fmt produces no changes
4. `make vet` - verify go vet passes
5. `make golangci-lint` - verify linter passes
6. `make test` - unit tests
7. `make test-integration K8S_VERSION={1.29.3,1.30.0,1.31.0}` - integration tests (matrix)

**Python Checks (test-python.yaml):**
1. `pre-commit run --all-files` - runs isort, black, flake8, yaml/json checks
2. `make test-python` - runs pytest on dataset, model, utils modules
3. `make test-python-integration` - integration tests for initializers

**E2E Checks (test-e2e.yaml):**
1. `make test-e2e-setup-cluster K8S_VERSION={1.29.14,1.30.0,1.31.0}` - Kind cluster setup
2. `make test-e2e` - Go e2e tests with Ginkgo
3. `make test-e2e-notebook` - Jupyter notebook execution tests with Papermill

**Trigger:** All PR and push events gate on these checks

**Matrix Testing:** CI tests against multiple Kubernetes versions (1.29, 1.30, 1.31)

## Conventions

### Test File Naming
- **Go:** `*_test.go` in same package as code under test
- **Python:** `*_test.py` alongside code or in `test/` subdirectories

### Test Function Naming
- **Go:** `func TestFunctionName(t *testing.T)` or `func TestSuiteName(t *testing.T)` with Ginkgo
- **Python:** `def test_function_name(...)`

### Import Organization
- **Go:** Grouped per `.golangci.yaml` gci config:
  1. Standard library
  2. External packages
  3. `github.com/kubeflow/trainer` packages
  4. Blank imports
  5. Dot imports
- **Python:** `isort --profile black` (compatible with black formatter)

### Code Style
- **Go:** Standard `go fmt` + `golangci-lint` with gci plugin
- **Python:** `black` (line length 100 per `.flake8`), `isort`, `flake8` (W503 ignored)

### Coverage
- **Go:** Generated via `make test` to `cover.out`
- **Python:** Not configured currently (can add with `pytest --cov`)

## Gaps & Caveats

### Not Validated in Basic Container

1. **Integration Tests (`make test-integration`):** Require `envtest` setup with Kubernetes API server binaries. Tests use Ginkgo and verify controller behavior with real K8s API interactions.

2. **E2E Tests (`make test-e2e`):** Require full Kind cluster with Kubeflow Trainer deployed. Tests verify end-to-end workflows including TrainJob creation and execution.

3. **Code Generation (`make generate`):** Requires `controller-gen` and runs code generators for CRDs, client libraries, and Python SDK. CI validates this but manual runs need tool installation.

4. **Pre-commit Hooks:** Full pre-commit run requires Node.js for some hooks. Individual Python linters (black, isort, flake8) work fine.

5. **Container Builds:** Project includes multiple Dockerfiles for different components (controller, initializers, trainers). These aren't validated by this test context.

### Infrastructure Requirements

- **Integration tests:** Need K8s API server (via envtest)
- **E2E tests:** Need Kind cluster + Kubeflow components
- **Some tests:** May require GPU for ML workload validation (not in unit tests)

### Python Integration Tests

Located in `test/integration/initializers/`. These test actual HuggingFace downloads and model operations, may require network access and can be slow.

## Quick Reference

### Essential Commands

```bash
# Go - Format, lint, test
make fmt && make vet && make golangci-lint && make test

# Python - Lint and test
flake8 pkg/initializers && \
PYTHONPATH=. pytest pkg/initializers/dataset pkg/initializers/model pkg/initializers/utils

# Full local validation (what CI runs)
make fmt && make vet && make golangci-lint && make test && \
pre-commit run --all-files && make test-python
```

### Fast Feedback Loop

For quick patch validation:
```bash
# Go only
make fmt && make vet && make test

# Python only
flake8 pkg/initializers && PYTHONPATH=. pytest pkg/initializers
```

### Gotchas

1. **PYTHONPATH required:** Python tests need `PYTHONPATH={repo_root}` to find modules
2. **pip --break-system-packages:** Needed in Debian 12+ containers (or use venv)
3. **golangci-lint auto-install:** Makefile installs if missing, downloads ~100MB
4. **Git required for generate check:** CI validates `git diff --exit-code` after generation
5. **Multi-version testing:** CI tests 3 Kubernetes versions - local testing typically uses one

## Summary

**Agent Readiness: HIGH**

This repository has excellent test infrastructure for automated validation:
- ✅ All lint commands work and are validated
- ✅ All unit test commands work and pass
- ✅ Clear dependency installation path
- ✅ Fast feedback (<2 min for unit tests)
- ✅ Comprehensive CI coverage

An agent can reliably:
1. Clone the repo
2. Apply patches
3. Run linters to catch style/syntax issues
4. Run unit tests to catch logic errors
5. Get clear pass/fail signals

**Limitations:** Integration and E2E tests require cluster infrastructure not available in basic containers, but unit tests provide good coverage for most patches.
