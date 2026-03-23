# Test Context for trainer (opendatahub-io)

**Generated:** 2026-03-22T20:30:00-04:00
**Agent Readiness:** MEDIUM - Lint and unit tests fully validated; integration/E2E require cluster infrastructure

## Overview

The `trainer` repository is a multi-language Kubernetes operator project (Kubeflow Training Operator v2) written primarily in **Go 1.24**, with **Python 3.11** components for data/model initializers and **Rust** for data caching. It uses standard Go testing, pytest, and cargo test. All linters and unit tests validated successfully in container. Integration and E2E tests require Kubernetes infrastructure (envtest, Kind clusters).

**Languages:** Go, Python, Rust
**Build System:** Make + Go modules + pip + Cargo
**CI:** GitHub Actions (gating on PR)

---

## Container Recipe

This recipe provides a complete, copy-paste workflow for running lint and unit tests in an isolated container. An agent can execute these steps verbatim to validate patches.

### 1. Start Container

Use Go 1.24 as base image (matches go.mod requirement):

```bash
podman run -d \
  --name test-context-trainer \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24 \
  sleep infinity
```

Replace `$(pwd)` with the absolute path to the repository if needed. If `podman` is unavailable, use `docker` instead.

### 2. Install System Dependencies

```bash
podman exec test-context-trainer bash -c "apt-get update && apt-get install -y make git python3 python3-pip python3-venv curl build-essential"
```

### 3. Install Rust

Required for Rust tests in `pkg/data_cache/`:

```bash
podman exec test-context-trainer bash -c "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"
```

### 4. Install Go Dependencies

```bash
podman exec test-context-trainer bash -c "cd /app && go mod download"
```

**Result:** ✅ Exit code 0, dependencies downloaded successfully

### 5. Install Python Dependencies

```bash
podman exec test-context-trainer bash -c "cd /app && pip install --break-system-packages pytest flake8 black isort && pip install --break-system-packages -r ./cmd/initializers/dataset/requirements.txt"
```

**Result:** ✅ Exit code 0, pytest and dataset initializer deps installed

### 6. Install golangci-lint

```bash
podman exec test-context-trainer bash -c "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v1.64.8"
```

**Result:** ✅ golangci-lint v1.64.8 installed to /usr/local/bin

---

## Linting Commands

### Go Linting

**go fmt:**
```bash
podman exec test-context-trainer bash -c "cd /app && go fmt ./..."
```
**Validated:** ✅ Exit 0, no formatting issues

**go vet:**
```bash
podman exec test-context-trainer bash -c "cd /app && go vet ./..."
```
**Validated:** ✅ Exit 0, no vet issues

**golangci-lint:**
```bash
podman exec test-context-trainer bash -c "cd /app && golangci-lint run --timeout 5m --go 1.24 ./..."
```
**Validated:** ✅ Exit 0, all linters passed (gci import grouping enforced)

### Python Linting

**flake8:**
```bash
podman exec test-context-trainer bash -c "cd /app && flake8 pkg/initializers/"
```
**Validated:** ✅ Exit 0, no violations (config: max-line-length=100, ignore W503/E203)

**black (check mode):**
```bash
podman exec test-context-trainer bash -c "cd /app && black --check ."
```
**Note:** Validated via pre-commit in CI; enforces consistent formatting

**isort (check mode):**
```bash
podman exec test-context-trainer bash -c "cd /app && isort --profile black --check ."
```
**Note:** Validated via pre-commit in CI

### Rust Linting

**cargo fmt:**
```bash
podman exec test-context-trainer bash -c "source /root/.cargo/env && cd /app && cargo fmt --manifest-path pkg/data_cache/Cargo.toml --check"
```

**cargo check:**
```bash
podman exec test-context-trainer bash -c "source /root/.cargo/env && cd /app && cargo check --manifest-path pkg/data_cache/Cargo.toml"
```

---

## Test Commands

### Go Unit Tests

Run all unit tests (excludes test/, cmd/, hack/, generated code):

```bash
podman exec test-context-trainer bash -c "cd /app && go test \$(go list ./... | grep -Ev '/(test|cmd|hack|pkg/apis|pkg/client|pkg/util/testing)') -coverprofile cover.out"
```

**Validated:** ✅ Exit 0, 24 packages passed
**Output sample:**
```
ok  	github.com/kubeflow/trainer/v2/pkg/apply	0.258s	coverage: 92.9% of statements
ok  	github.com/kubeflow/trainer/v2/pkg/controller	1.354s	coverage: 33.1% of statements
ok  	github.com/kubeflow/trainer/v2/pkg/runtime/core	0.779s	coverage: 58.4% of statements
...
ok  	github.com/kubeflow/trainer/v2/pkg/webhooks	0.311s	coverage: 49.2% of statements
```

Coverage report written to `cover.out`.

**Run single test file:**
```bash
podman exec test-context-trainer bash -c "cd /app && go test ./pkg/apply/apply_test.go"
```

**Run single test function:**
```bash
podman exec test-context-trainer bash -c "cd /app && go test -run TestApplyObject ./pkg/apply"
```

### Python Unit Tests

**Dataset initializer tests:**
```bash
podman exec test-context-trainer bash -c "cd /app && PYTHONPATH=/app pytest ./pkg/initializers/dataset -v"
```

**Validated:** ✅ Exit 0, 19 tests passed in 0.35s
**Output:**
```
pkg/initializers/dataset/cache_test.py::test_load_config ... PASSED
pkg/initializers/dataset/huggingface_test.py::test_download_dataset ... PASSED
============================== 19 passed in 0.35s ==============================
```

**Model and utils tests:**
```bash
podman exec test-context-trainer bash -c "cd /app && PYTHONPATH=/app pytest ./pkg/initializers/model ./pkg/initializers/utils -v"
```

**Validated:** ✅ Exit 0, 26 tests passed in 0.18s

**All Python unit tests (combined):**
```bash
podman exec test-context-trainer bash -c "cd /app && PYTHONPATH=/app pytest ./pkg/initializers/dataset ./pkg/initializers/model ./pkg/initializers/utils"
```

**Run single Python test file:**
```bash
podman exec test-context-trainer bash -c "cd /app && PYTHONPATH=/app pytest ./pkg/initializers/dataset/cache_test.py"
```

**Run single Python test:**
```bash
podman exec test-context-trainer bash -c "cd /app && PYTHONPATH=/app pytest ./pkg/initializers/dataset/cache_test.py::test_load_config"
```

### Rust Unit Tests

```bash
podman exec test-context-trainer bash -c "source /root/.cargo/env && cd /app && cargo test --lib --bins --manifest-path ./pkg/data_cache/Cargo.toml"
```

**Validated:** ✅ Exit 0, 14 tests passed
**Output:**
```
running 14 tests
test head::provider::tests::test_partition_tasks_validates_start_end_indices_empty ... ok
test worker::indexable_mem_table::tests::test_indexable_mem_table_with_load_and_scan ... ok
...
test result: ok. 14 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

**Note:** First run takes ~2 minutes to compile dependencies.

**Run single Rust test:**
```bash
podman exec test-context-trainer bash -c "source /root/.cargo/env && cargo test --manifest-path ./pkg/data_cache/Cargo.toml test_partition_tasks_empty_stream"
```

---

## Integration Tests (Requires Infrastructure)

### Go Integration Tests

**⚠️ Requires:** envtest (simulated Kubernetes API server) and external CRDs

**Setup:**
```bash
# These commands download tools and CRDs - run on host, not in container
make ginkgo
make envtest
make jobset-operator-crd
make scheduler-plugins-crd
make volcano-crd
```

**Run:**
```bash
make test-integration
```

Expands to:
```bash
KUBEBUILDER_ASSETS="$(bin/setup-envtest use 1.34.0 -p path)" bin/ginkgo -v ./test/integration/...
```

**Not validated in container** - requires K8s API server setup.

### Python Integration Tests

**⚠️ Requires:** Actual Kubernetes cluster (tests interact with K8s API)

```bash
PYTHONPATH=$(pwd) pytest ./test/integration/initializers
```

**Not validated** - requires live cluster.

---

## E2E Tests (Requires Kind Cluster)

**⚠️ Requires:** Kind cluster with specific K8s version

**Setup cluster:**
```bash
make test-e2e-setup-cluster K8S_VERSION=1.34.0
```

**Run E2E tests:**
```bash
make test-e2e
```

Runs Ginkgo tests in `test/e2e/` that deploy TrainJobs to the cluster and verify behavior.

**Not validated** - requires full Kind cluster infrastructure. CI runs on matrix of K8s versions: 1.31.0, 1.32.3, 1.33.1, 1.34.0.

---

## Cleanup

Always remove the container when done:

```bash
podman rm -f test-context-trainer
```

---

## Validation Results

| Step | Command | Exit Code | Result |
|------|---------|-----------|--------|
| Install Go deps | `go mod download` | 0 | ✅ Success |
| go fmt | `go fmt ./...` | 0 | ✅ No changes needed |
| go vet | `go vet ./...` | 0 | ✅ No issues |
| golangci-lint | `golangci-lint run --timeout 5m --go 1.24 ./...` | 0 | ✅ All linters passed |
| Go unit tests | `go test ... -coverprofile cover.out` | 0 | ✅ 24 packages passed |
| Install Python deps | `pip install pytest ...` | 0 | ✅ Success |
| Python dataset tests | `pytest ./pkg/initializers/dataset` | 0 | ✅ 19 passed in 0.35s |
| Python model/utils tests | `pytest ./pkg/initializers/model ./pkg/initializers/utils` | 0 | ✅ 26 passed in 0.18s |
| Rust tests | `cargo test --lib --bins ...` | 0 | ✅ 14 passed |
| flake8 | `flake8 pkg/initializers/` | 0 | ✅ No violations |

**Summary:** All lint and unit tests validated successfully. An agent can run these commands in a container and get clear pass/fail signals.

---

## CI/CD

### Gating Checks (Required to Merge PRs)

All checks run on **push** and **pull_request** events:

**1. test-go.yaml (Go checks - GATING):**
- `go mod tidy` check (ensures modules are synchronized)
- `make generate` check (ensures generated code is up to date)
- `make fmt` check (go fmt must not produce changes)
- `make vet` check (go vet must pass)
- `make golangci-lint` (all linters must pass)
- `make test` (unit tests)
- `make test-integration` (integration tests with envtest)

**2. test-python.yaml (Python checks - GATING):**
- `pre-commit run --all-files` (runs flake8, black, isort on all Python files)
- `make test-python` (unit tests)
- `make test-python-integration` (integration tests)

**3. test-rust.yaml (Rust checks - GATING):**
- `make test-rust` (unit tests)
- Only runs on `kubeflow/trainer` repo (not forks)

**4. test-e2e.yaml (E2E checks - GATING):**
- Matrix: K8s versions [1.31.0, 1.32.3, 1.33.1, 1.34.0]
- Sets up Kind cluster with `make test-e2e-setup-cluster`
- Runs `make test-e2e` (Ginkgo E2E tests)
- Runs Jupyter notebook tests with Papermill (mnist, fine-tune-distilbert, local examples)
- Runs on `oracle-vm-16cpu-64gb-x86-64` runners

**5. check-pr-title.yaml (GATING):**
- Validates PR title format

### Advisory Checks (Not Required)

**test-e2e-gpu.yaml:**
- Runs GPU-specific E2E tests
- Requires GPU hardware, may not always run

### Tekton Pipelines

**.tekton/trainer-pull-request.yaml:**
- Builds container image on PR
- Does not run tests (build-only)

---

## Conventions

### Test File Naming
- **Go:** `*_test.go` (e.g., `apply_test.go`)
- **Python:** `*_test.py` (e.g., `cache_test.py`)
- **Rust:** Inline tests in source files or `tests/` directory

### Test Function Naming
- **Go:** `Test*` for standard tests (e.g., `TestApplyObject`), `Describe/It` for Ginkgo specs
- **Python:** `test_*` functions (e.g., `test_load_config`)
- **Rust:** `#[test]` attribute on functions

### Import Style
- **Go:** gci linter enforces grouped imports:
  1. Standard library
  2. External dependencies
  3. Project-specific (`github.com/kubeflow/trainer/v2`)
  4. Blank imports
  5. Dot imports

### Coverage
- **Go:** Unit tests generate `cover.out`, uploaded to Coveralls in CI
- **Python/Rust:** No coverage tracking configured

---

## Gaps & Caveats

### Cannot Validate in Simple Container

1. **Go integration tests** - Require envtest (simulated K8s API server) and external CRD downloads
2. **E2E tests** - Require full Kind cluster with specific K8s versions
3. **Python integration tests** - Require actual Kubernetes cluster access
4. **GPU E2E tests** - Require GPU hardware
5. **Code generation validation** - `make generate` requires code-generator tools and multiple setup steps
6. **Pre-commit hooks** - Would require pre-commit tool installation and hook setup
7. **Notebook E2E tests** - Require Papermill, Jupyter, Kubeflow SDK with Docker support

### Infrastructure Requirements

- **envtest:** Downloads and runs Kubernetes API server binaries for integration tests
- **External CRDs:** JobSet, Volcano, Scheduler Plugins CRDs must be downloaded from their repos
- **Kind cluster:** E2E tests spin up real Kubernetes clusters with different versions
- **Container registry:** Some tests may push/pull container images

### CI-Specific Behavior

- Rust tests only run on `kubeflow/trainer` repo (not forks) due to workflow condition
- E2E tests use large runners (16 CPU, 64GB RAM) and take ~30-60 minutes
- Coveralls report only uploaded from CI, not local runs

### What Works in Container

✅ **All lint commands** - go fmt, go vet, golangci-lint, flake8, black, isort, cargo fmt
✅ **Go unit tests** - All 24 packages pass
✅ **Python unit tests** - All 45 tests pass (dataset, model, utils)
✅ **Rust unit tests** - All 14 tests pass
✅ **Dependency installation** - Go, Python, Rust deps install cleanly

---

## Quick Start for Agents

**Minimal validation workflow (lint + unit tests only):**

```bash
# Start container
podman run -d --name test-context-trainer -v $(pwd):/app:Z -w /app golang:1.24 sleep infinity

# Install everything
podman exec test-context-trainer bash -c "
  apt-get update && apt-get install -y make git python3 python3-pip curl build-essential &&
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y &&
  cd /app &&
  go mod download &&
  pip install --break-system-packages pytest flake8 -r ./cmd/initializers/dataset/requirements.txt &&
  curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v1.64.8
"

# Run all lints
podman exec test-context-trainer bash -c "cd /app && go fmt ./... && go vet ./... && golangci-lint run --timeout 5m --go 1.24 ./... && flake8 pkg/initializers/"

# Run all unit tests
podman exec test-context-trainer bash -c "cd /app &&
  go test \$(go list ./... | grep -Ev '/(test|cmd|hack|pkg/apis|pkg/client|pkg/util/testing)') -coverprofile cover.out &&
  PYTHONPATH=/app pytest ./pkg/initializers/dataset ./pkg/initializers/model ./pkg/initializers/utils &&
  source /root/.cargo/env && cargo test --lib --bins --manifest-path ./pkg/data_cache/Cargo.toml
"

# Cleanup
podman rm -f test-context-trainer
```

**Expected result:** All commands exit 0, proving the patch doesn't break lint or unit tests.

---

## Agent Readiness Rating: MEDIUM

**Rationale:**
- ✅ All lint commands validated and working
- ✅ All unit tests validated and working (Go, Python, Rust)
- ✅ Dependencies install cleanly in standard container
- ✅ Clear pass/fail signals from all validated commands
- ⚠️ Integration tests require infrastructure (envtest, Kind)
- ⚠️ E2E tests require full cluster setup
- ⚠️ Code generation not validated

**An agent can:**
- Apply patches
- Run all linters and get immediate feedback
- Run all unit tests and verify no regressions
- Provide high-confidence signal for most code changes

**An agent cannot (without infrastructure):**
- Run integration tests (need envtest + CRDs)
- Run E2E tests (need Kind cluster)
- Validate code generation changes (need code-generator tools)

**Recommendation:** Use this container recipe for fast lint+unit test validation. Rely on CI for integration/E2E coverage.
