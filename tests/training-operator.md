# Training Operator Test Context

**Agent Readiness: medium** — Go and Python unit tests work perfectly. Linting mostly works (flake8/black/isort pass, but golangci-lint fails on generated code). Integration tests require Kubernetes cluster infrastructure.

## Overview

- **Repository**: opendatahub-io/training-operator
- **Languages**: Go (primary), Python (SDK)
- **Build System**: Makefile + Go tooling + pip
- **Go Version**: 1.25 (from go.mod)
- **Python Versions**: 3.10, 3.11 (tested in CI)
- **Test Frameworks**: Go testing + Ginkgo/Gomega, pytest
- **CI Systems**: GitHub Actions (gating), Tekton (OpenShift builds)

This is a Kubernetes operator for training ML models. The core operator is Go-based with a Python SDK for users. Tests validate controller logic (Go unit tests with envtest) and SDK behavior (Python unit tests with mocked k8s client). Integration tests require a real Kubernetes cluster.

---

## Container Recipe

This is a complete, copy-paste recipe for running lint and tests in a container.

### 1. Start Container

```bash
podman run -d --name test-context-training-operator \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

**Alternative**: Use `docker` instead of `podman` if unavailable.

### 2. Install System Dependencies

```bash
podman exec test-context-training-operator bash -c \
  "apt-get update && apt-get install -y make git curl python3 python3-pip python3-venv"
```

### 3. Install Go Dependencies

```bash
podman exec test-context-training-operator bash -c \
  "cd /app && go mod download"
```

**Expected**: Exit 0, no output.

### 4. Install Go Test Tooling

```bash
podman exec test-context-training-operator bash -c \
  "go install sigs.k8s.io/controller-runtime/tools/setup-envtest@release-0.19"
```

**Expected**: Exit 0. Installs `setup-envtest` to `/go/bin/setup-envtest`.

### 5. Install Python Dependencies

```bash
podman exec test-context-training-operator bash -c \
  "pip3 install --break-system-packages pytest python-dateutil urllib3 kubernetes retrying setuptools"
```

**Expected**: Exit 0. Installs pytest and kubernetes client libraries.

### 6. Run Go Linters

#### go fmt

```bash
podman exec test-context-training-operator bash -c \
  "cd /app && go fmt ./..."
```

**Validated**: ✅ Exit 0. May output filenames that would be formatted (e.g., `pkg/controller.v1/mpi/mpijob_controller.go`). This is informational, not a failure.

#### go vet

```bash
podman exec test-context-training-operator bash -c \
  "cd /app && go vet ./..."
```

**Validated**: ✅ Exit 0. No issues found.

#### golangci-lint

```bash
podman exec test-context-training-operator bash -c \
  "cd /app && make golangci-lint"
```

**Validated**: ❌ Exit 1. **Known issue**: Fails with type errors in auto-generated client code:
```
pkg/client/applyconfiguration/kubeflow.org/v1/mpijob.go:44:4: b.Kind undefined
(type *MPIJobApplyConfiguration has no field or method Kind) (typecheck)
```

This appears to be a code generation bug. The generated code in `pkg/client/applyconfiguration/` has missing fields. You may need to run `make generate` first, or this is a known issue in the repo. **For patch validation, you can skip golangci-lint if your patch doesn't touch Go code, or run it knowing it will fail on existing issues.**

### 7. Run Python Linters

#### flake8

```bash
podman exec test-context-training-operator bash -c \
  "pip3 install --break-system-packages flake8 && cd /app && flake8 sdk/python/kubeflow/training/api/"
```

**Validated**: ✅ Exit 0. No style violations. Config: `.flake8` (max-line-length=100).

#### black

```bash
podman exec test-context-training-operator bash -c \
  "pip3 install --break-system-packages black && cd /app && black --check sdk/python/kubeflow/training/api/"
```

**Validated**: ✅ Exit 0. All files formatted correctly. Auto-fix: `black sdk/python/kubeflow/training/api/`.

#### isort

```bash
podman exec test-context-training-operator bash -c \
  "pip3 install --break-system-packages isort && cd /app && isort --check --profile black sdk/python/kubeflow/training/api/"
```

**Validated**: ✅ Exit 0. Imports sorted correctly. Auto-fix: `isort --profile black sdk/python/kubeflow/training/api/`.

### 8. Run Go Unit Tests

```bash
podman exec test-context-training-operator bash -c \
  "cd /app && export PATH=/go/bin:\$PATH && \
   KUBEBUILDER_ASSETS=\$(setup-envtest use 1.31 -p path) \
   go test ./pkg/apis/kubeflow.org/v1/... ./pkg/cert/... ./pkg/common/... \
            ./pkg/config/... ./pkg/controller.v1/... ./pkg/core/... \
            ./pkg/util/... ./pkg/webhooks/... -coverprofile cover.out"
```

**Validated**: ✅ Exit 0. **All tests passed**.

**Output snippet**:
```
ok  	github.com/kubeflow/training-operator/pkg/controller.v1/jax	20.913s	coverage: 66.5%
ok  	github.com/kubeflow/training-operator/pkg/controller.v1/mpi	32.972s	coverage: 77.7%
ok  	github.com/kubeflow/training-operator/pkg/controller.v1/pytorch	31.736s	coverage: 74.6%
ok  	github.com/kubeflow/training-operator/pkg/controller.v1/tensorflow	44.374s	coverage: 79.9%
ok  	github.com/kubeflow/training-operator/pkg/controller.v1/xgboost	28.946s	coverage: 66.2%
```

**Timeout**: Tests take ~3 minutes total. Use timeout of 5 minutes to be safe.

### 9. Run Python Unit Tests

```bash
podman exec test-context-training-operator bash -c \
  "cd /app && export PYTHONPATH=/app/sdk/python && \
   pytest ./sdk/python/kubeflow/training/api/training_client_test.py -v"
```

**Validated**: ✅ Exit 0. **132 tests passed in 0.75s**.

**Output snippet**:
```
sdk/python/kubeflow/training/api/training_client_test.py::test_create_job PASSED
sdk/python/kubeflow/training/api/training_client_test.py::test_get_job PASSED
sdk/python/kubeflow/training/api/training_client_test.py::test_delete_job PASSED
...
============================= 132 passed in 0.75s ==============================
```

**Note**: Using `PYTHONPATH` instead of `pip install -e './sdk/python'` because editable install has issues in the container. This works reliably for testing.

### 10. Run Single Test (Examples)

#### Go: Run one test function

```bash
podman exec test-context-training-operator bash -c \
  "cd /app && KUBEBUILDER_ASSETS=\$(setup-envtest use 1.31 -p path) \
   go test -run TestMPIJobDefaulting ./pkg/apis/kubeflow.org/v1/..."
```

#### Go: Run one test file

```bash
podman exec test-context-training-operator bash -c \
  "cd /app && KUBEBUILDER_ASSETS=\$(setup-envtest use 1.31 -p path) \
   go test ./pkg/apis/kubeflow.org/v1/mpi_defaults_test.go"
```

#### Python: Run one test function

```bash
podman exec test-context-training-operator bash -c \
  "cd /app && export PYTHONPATH=/app/sdk/python && \
   pytest ./sdk/python/kubeflow/training/api/training_client_test.py::test_create_job -v"
```

#### Python: Run tests matching a pattern

```bash
podman exec test-context-training-operator bash -c \
  "cd /app && export PYTHONPATH=/app/sdk/python && \
   pytest ./sdk/python/kubeflow/training/api/training_client_test.py -k 'create_job' -v"
```

### 11. Cleanup

```bash
podman rm -f test-context-training-operator
```

**Always run this** even if earlier steps failed, to avoid leaving containers running.

---

## Validation Results

### Summary Table

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install | `go mod download` | ✅ Pass | Dependencies installed |
| Lint | `go fmt ./...` | ✅ Pass | 1 file needs formatting (informational) |
| Lint | `go vet ./...` | ✅ Pass | No issues |
| Lint | `make golangci-lint` | ❌ Fail | Type errors in generated code |
| Test | Go unit tests | ✅ Pass | All tests passed, 66-79% coverage |
| Install | Python deps | ✅ Pass | pytest, kubernetes installed |
| Lint | `flake8` | ✅ Pass | No violations |
| Lint | `black --check` | ✅ Pass | All formatted |
| Lint | `isort --check` | ✅ Pass | Imports sorted |
| Test | Python unit tests | ✅ Pass | 132 tests passed in 0.75s |

### Detailed Results

#### Go Tests (make test)

**Exit Code**: 0
**Duration**: ~3 minutes
**Tests Run**: Multiple packages tested
**Coverage**: 66.5% (jax), 77.7% (mpi), 74.6% (pytorch), 79.9% (tensorflow), 66.2% (xgboost)

The tests use `setup-envtest` which provides a simulated Kubernetes API server. Tests validate:
- Default values for job CRDs
- Webhook validation logic
- Controller reconciliation logic
- Job status updates
- Pod and service creation

#### Python Tests (pytest)

**Exit Code**: 0
**Duration**: 0.75s
**Tests Run**: 132
**Test File**: `sdk/python/kubeflow/training/api/training_client_test.py`

Tests validate the Python SDK `TrainingClient` class with mocked Kubernetes client:
- `create_job()` - creating PyTorchJob, TFJob, etc.
- `get_job()` - retrieving job status
- `delete_job()` - cleanup
- `wait_for_job_conditions()` - polling for completion
- `update_job()` - patching job specs
- `list_jobs()` - listing jobs in namespace
- `get_job_logs()` - streaming pod logs

#### golangci-lint Failure

The linter fails on generated client code in `pkg/client/applyconfiguration/`. The errors look like:

```
pkg/client/applyconfiguration/kubeflow.org/v1/mpijob.go:44:4: b.Kind undefined
(type *MPIJobApplyConfiguration has no field or method Kind) (typecheck)
```

**Root cause**: The code generator appears to have produced incomplete structs missing required fields.

**Workaround options**:
1. Run `make generate` to regenerate code (may fix it)
2. Skip golangci-lint if your patch doesn't touch Go code
3. Exclude generated files from linting (requires config change)

**For patch validation**: If your patch only modifies Python SDK or docs, you can ignore this failure. If modifying Go code, check that your changes don't introduce new linter errors beyond the existing ones.

---

## CI/CD

### Gating Checks (GitHub Actions)

All PRs must pass these workflows:

#### 1. test-go.yaml - Go Code Generation Check

**Trigger**: push, pull_request
**Commands**:
```bash
go mod tidy
make generate
make fmt
make vet
make golangci-lint
```

**Purpose**: Ensures generated code (CRDs, manifests, SDK) is up to date. Checks that running `make generate` doesn't produce diffs.

**Note**: Currently fails on golangci-lint due to generated code issues (see above).

#### 2. unittests.yaml - Go Unit Tests

**Trigger**: push, pull_request
**Matrix**: Kubernetes 1.28.3, 1.29.3, 1.30.0, 1.31.0
**Command**:
```bash
make test ENVTEST_K8S_VERSION=1.31.0
```

**Purpose**: Validates controller logic against multiple Kubernetes API versions.

#### 3. test-python.yaml - Python SDK Tests

**Trigger**: push, pull_request
**Matrix**: Python 3.10, 3.11
**Commands**:
```bash
pip install pytest python-dateutil urllib3 kubernetes
pip install -U './sdk/python[huggingface]'
pytest ./sdk/python/kubeflow/training/api/training_client_test.py
```

**Purpose**: Validates Python SDK against multiple Python versions.

**Note**: The `[huggingface]` extras install large dependencies (PyTorch, transformers) which may be slow.

#### 4. pre-commit.yaml - Pre-commit Hooks

**Trigger**: pull_request, push to main
**Command**:
```bash
pre-commit run --all-files
```

**Purpose**: Runs all pre-commit hooks: check-yaml, check-json, end-of-file-fixer, trailing-whitespace, isort, black, flake8.

**Config**: `.pre-commit-config.yaml` with exclusions for generated files.

#### 5. integration-tests.yaml - E2E Tests

**Trigger**: pull_request
**Matrix**: Kubernetes versions, gang schedulers (none, scheduler-plugins, volcano), Python versions
**Commands**:
```bash
# Sets up kind cluster, installs gang schedulers
pytest -s sdk/python/test/e2e --log-cli-level=debug --namespace=default
```

**Purpose**: End-to-end tests that create real Kubernetes jobs and validate behavior.

**Requirements**:
- kind cluster
- Gang schedulers (optional, matrix tests with/without)
- Custom Docker images (JAX job example)

**Cannot run in basic container** - requires cluster infrastructure.

### Tekton Pipelines

**Files**: `.tekton/odh-training-operator-pull-request.yaml`, `.tekton/odh-training-operator-push.yaml`

These run on OpenShift (via PipelinesAsCode) and build container images using the `odh-konflux-central` pipeline. They validate PRs to the `stable` branch for OpenDataHub releases.

---

## Conventions

### File Naming

- **Go tests**: `*_test.go` (e.g., `mpi_defaults_test.go`)
- **Python tests**: `test_*.py` (e.g., `test_e2e_pytorchjob.py`)

### Test Function Naming

- **Go**: `Test*` (e.g., `TestMPIJobDefaulting`) or Ginkgo `Describe`/`It` blocks
- **Python**: `test_*` (e.g., `test_create_job`)

### Import Style

- **Go**: Standard Go import grouping (stdlib, external, internal)
- **Python**: `isort` with `--profile black` (groups: stdlib, third-party, first-party; sorted alphabetically)

### Code Style

- **Go**: `go fmt` formatting, `golangci-lint` rules (when working)
- **Python**: `black` (line length 100 per `.flake8`), `flake8` (ignore W503)

### Coverage

- **Go**: Coverage tracked via `-coverprofile cover.out`, ranges 66-79% across packages
- **Python**: Coverage not explicitly tracked in unit tests, but `pytest --cov` available
- **No enforced threshold** - coverage is monitored but not gating

### Generated Code

The following paths contain auto-generated code and should NOT be edited manually:
- `pkg/apis/kubeflow.org/v1/openapi_generated.go`
- `pkg/apis/kubeflow.org/v1/zz_*.go`
- `pkg/client/` (entire directory)
- `sdk/python/kubeflow/training/models/` (OpenAPI-generated models)

Regenerate via `make generate` after modifying API types in `pkg/apis/`.

---

## Gaps & Caveats

### Known Issues

1. **golangci-lint fails on generated code**: Type errors in `pkg/client/applyconfiguration/`. This is likely a bug in code generation. Run `make generate` to attempt to fix, or skip golangci-lint if patching non-Go code.

2. **Python SDK editable install fails**: `pip install -e './sdk/python'` fails in container due to setuptools issues. Workaround: use `PYTHONPATH=/app/sdk/python` instead.

3. **Huggingface extras timeout**: Installing `sdk/python[huggingface]` downloads 3GB+ of PyTorch dependencies and times out in constrained environments. For unit tests, huggingface extras are NOT required.

### Infrastructure Requirements

**Cannot run in basic container**:
- **Integration tests** (`sdk/python/test/e2e/`) require:
  - kind cluster
  - Gang schedulers (scheduler-plugins or volcano)
  - Custom Docker images built and loaded into kind
- **Full pre-commit validation** requires:
  - pre-commit framework installed
  - All hook dependencies (including non-Python tools)

**Can run in basic container**:
- ✅ Go unit tests (via envtest simulated API)
- ✅ Python unit tests (mock Kubernetes client)
- ✅ Go linters (fmt, vet)
- ✅ Python linters (flake8, black, isort)

### Test Isolation

- **Go tests** are fully isolated (use envtest simulated k8s API)
- **Python unit tests** are isolated (mock all k8s client calls)
- **Python E2E tests** require real cluster and are NOT isolated

### Missing Configuration

- No `.golangci.yml` config file - golangci-lint uses defaults with CLI flags in Makefile
- No Python coverage threshold configured
- No pyproject.toml - Python SDK uses older setup.py style

---

## Quick Reference

### Run All Validation (One Command)

```bash
# Start container and run full validation suite
podman run -d --name test-context-training-operator -v $(pwd):/app:Z -w /app golang:1.25 sleep infinity && \
podman exec test-context-training-operator bash -c "
  apt-get update && apt-get install -y make git curl python3 python3-pip python3-venv && \
  cd /app && go mod download && \
  go install sigs.k8s.io/controller-runtime/tools/setup-envtest@release-0.19 && \
  pip3 install --break-system-packages pytest python-dateutil urllib3 kubernetes retrying setuptools flake8 black isort && \
  echo '=== Go fmt ===' && go fmt ./... && \
  echo '=== Go vet ===' && go vet ./... && \
  echo '=== Go tests ===' && export PATH=/go/bin:\$PATH && KUBEBUILDER_ASSETS=\$(setup-envtest use 1.31 -p path) go test ./pkg/apis/kubeflow.org/v1/... ./pkg/cert/... ./pkg/common/... ./pkg/config/... ./pkg/controller.v1/... ./pkg/core/... ./pkg/util/... ./pkg/webhooks/... -coverprofile cover.out && \
  echo '=== Python lint ===' && flake8 sdk/python/kubeflow/training/api/ && black --check sdk/python/kubeflow/training/api/ && isort --check --profile black sdk/python/kubeflow/training/api/ && \
  echo '=== Python tests ===' && export PYTHONPATH=/app/sdk/python && pytest ./sdk/python/kubeflow/training/api/training_client_test.py -v
" && \
podman rm -f test-context-training-operator
```

### Minimal Validation (Fast)

If you only care about tests passing (skip linters):

```bash
podman run -d --name test-context-training-operator -v $(pwd):/app:Z -w /app golang:1.25 sleep infinity && \
podman exec test-context-training-operator bash -c "
  apt-get update && apt-get install -y python3 python3-pip && \
  cd /app && go mod download && \
  go install sigs.k8s.io/controller-runtime/tools/setup-envtest@release-0.19 && \
  pip3 install --break-system-packages pytest python-dateutil urllib3 kubernetes && \
  export PATH=/go/bin:\$PATH && KUBEBUILDER_ASSETS=\$(setup-envtest use 1.31 -p path) go test ./pkg/controller.v1/... && \
  export PYTHONPATH=/app/sdk/python && pytest ./sdk/python/kubeflow/training/api/training_client_test.py
" && \
podman rm -f test-context-training-operator
```

### Clean Up Stuck Container

```bash
podman rm -f test-context-training-operator
```

---

## For Downstream Agents

**If you are an AI agent reading this to validate a patch**:

1. **Determine scope**: Is the patch Go, Python, docs, or config?
   - Go code → run Go tests + linters
   - Python SDK → run Python tests + linters
   - Docs/config → skip tests, maybe run YAML validation

2. **Use the container recipe above** (sections 1-9) as your validation script.

3. **Interpret results**:
   - Go tests must pass (exit 0)
   - Python tests must pass (exit 0)
   - `go fmt` and `go vet` must pass
   - `golangci-lint` may fail due to existing issues - compare before/after
   - Python linters must pass (flake8, black, isort)

4. **Known false positives**:
   - golangci-lint errors in `pkg/client/applyconfiguration/` are pre-existing
   - `go fmt` listing a file is informational, not a failure

5. **Cannot validate**:
   - Integration tests (need cluster)
   - Pre-commit hooks (need framework installed)
   - Full docker build (too slow for quick validation)

6. **Timeout recommendations**:
   - Go tests: 5 minutes (usually ~3 min)
   - Python tests: 1 minute (usually <1 sec)
   - Total validation: 10 minutes max
