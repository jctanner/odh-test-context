# Test Context: llama-stack-k8s-operator-legacy

## Overview

**Repository**: opendatahub-io/llama-stack-k8s-operator-legacy
**Language**: Go 1.21.0
**Build System**: Makefile + Go modules
**Type**: Kubernetes operator (controller-runtime/Kubebuilder)
**Agent Readiness**: **LOW** - Lint validation works perfectly, but tests require Kubernetes infrastructure and have 0 test specs.

**Note**: This project has been archived and moved to a [new location](https://github.com/llamastack/llama-stack-k8s-operator).

## Container Recipe

This recipe provides a complete, copy-paste guide for running lint validation in a container. Tests cannot run without Kubernetes infrastructure.

### 1. Start Container

```bash
podman run -d --name test-context-llama-stack-k8s-operator-legacy \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.21 \
  sleep infinity
```

If `podman` is not available, use `docker`:

```bash
docker run -d --name test-context-llama-stack-k8s-operator-legacy \
  -v $(pwd):/app \
  -w /app \
  golang:1.21 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-llama-stack-k8s-operator-legacy bash -c \
  "apt-get update && apt-get install -y make git curl"
```

### 3. Download Go Dependencies

```bash
podman exec test-context-llama-stack-k8s-operator-legacy bash -c \
  "cd /app && go mod download"
```

**Result**: ✅ Success - all dependencies download cleanly

### 4. Run Lint (PRIMARY VALIDATION)

```bash
podman exec test-context-llama-stack-k8s-operator-legacy bash -c \
  "cd /app && make lint"
```

**What happens**:
- Downloads golangci-lint v1.63.4 to `./bin/golangci-lint`
- Runs comprehensive linter suite (all linters enabled with specific exclusions)
- Two warnings about Go 1.22+ linters being disabled (expected, safe to ignore)
- Exit code 0 = success

**Result**: ✅ Success - lint passes with 0 violations

**Alternative - with fix**:

```bash
podman exec test-context-llama-stack-k8s-operator-legacy bash -c \
  "cd /app && make lint-fix"
```

This runs golangci-lint with `--fix` to automatically correct issues.

### 5. Build (Optional Validation)

```bash
podman exec test-context-llama-stack-k8s-operator-legacy bash -c \
  "cd /app && make build"
```

**What happens**:
- Installs controller-gen, yq to `./bin/`
- Generates DeepCopy code (via `make generate`)
- Runs `go fmt ./...`
- Runs `go vet ./...`
- Builds `bin/manager` binary

**Result**: ✅ Success - builds cleanly

### 6. Run Tests (NOT VALIDATED)

```bash
podman exec test-context-llama-stack-k8s-operator-legacy bash -c \
  "cd /app && go test ./..."
```

**What happens**:
- Test framework (Ginkgo) starts
- Attempts to bootstrap Kubernetes test environment (envtest)
- Fails: `fork/exec /usr/local/kubebuilder/bin/etcd: no such file or directory`
- Exit code 1

**Result**: ❌ Failure - requires Kubernetes envtest binaries (etcd, kube-apiserver)

**Why tests fail**:
1. Tests use controller-runtime's envtest which needs a full Kubernetes control plane
2. Requires etcd and kube-apiserver binaries from kubebuilder
3. Even if these were available, there are **0 test specs** to run ("Will run 0 of 0 specs")
4. Most packages have `[no test files]`

**Test files found**: Only `controllers/suite_test.go` - just setup/teardown, no actual tests.

### 7. Cleanup

```bash
podman rm -f test-context-llama-stack-k8s-operator-legacy
```

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install | `go mod download` | 0 | ✅ Pass | All dependencies downloaded |
| Lint | `make lint` | 0 | ✅ Pass | 0 violations, 2 Go version warnings |
| Build | `make build` | 0 | ✅ Pass | Generates bin/manager |
| Test | `go test ./...` | 1 | ❌ Fail | Needs K8s infrastructure, 0 specs |

## CI/CD

### GitHub Actions Workflows

**Gating Check (runs on all PRs)**:

`.github/workflows/linters.yaml`:
- Trigger: `pull_request`, `push` to main
- Sets up Go 1.21 (from go.mod)
- Runs: `make lint`
- **This is the only gating check**

**Advisory Check (image building)**:

`.github/workflows/build-image.yml`:
- Trigger: `pull_request_target` (opened, synchronize, closed)
- Builds and pushes PR images to quay.io
- Runs: `make docker-build docker-push`
- **Not gating, just builds images**

### What Gates Merges

Only `make lint` gates merges. Tests are not run in CI.

## Linting

### Configuration

**File**: `.golangci.yml`
**Tool**: golangci-lint v1.63.4
**Policy**: Enable-all with specific exclusions

**Disabled linters**:
- depguard, exhaustruct, forbidigo, gochecknoglobals, gofumpt, gomoddirectives, mnd, nestif, nilnil, paralleltest, tagliatelle, varnamelen, wsl, wrapcheck, exportloopref, nlreturn, err113

**Key settings**:
- Timeout: 10 minutes
- Max line length: 180
- Function length: 100 lines/100 statements
- Import ordering: gci (standard, default, blank, dot)
- Excludes: `apis/` directory

### Run Commands

**Check only**:
```bash
make lint
# or directly:
./bin/golangci-lint run --timeout=5m0s --sort-results
```

**Auto-fix**:
```bash
make lint-fix
# or directly:
./bin/golangci-lint run --fix --sort-results
```

**Format code**:
```bash
make fmt
# Runs: go fmt ./... + golangci-lint with gci for import ordering
```

**Go vet**:
```bash
make vet
# Runs: go vet ./...
```

## Testing

### Framework

- **Ginkgo** v1.16.5 (BDD-style testing)
- **Gomega** v1.18.1 (matcher library)
- **envtest** from controller-runtime (Kubernetes test environment)

### Test Files

Only one test file exists: `controllers/suite_test.go`

This file contains:
- Test suite setup (`TestAPIs` function)
- BeforeSuite hook (bootstraps envtest environment)
- AfterSuite hook (tears down envtest)
- **0 actual test specs**

Other packages have no tests:
- `api/v1alpha1` - no tests
- `pkg/deploy` - no tests
- `pkg/featureflags` - no tests

### Run Commands

**Full test suite** (requires Kubernetes infrastructure):
```bash
make test
```

This runs:
1. `make manifests` - generates CRDs
2. `make generate` - generates DeepCopy code
3. `make fmt` - formats code
4. `make vet` - runs go vet
5. `setup-envtest use 1.24.2` - downloads kubebuilder assets
6. `go test ./... -coverprofile cover.out` with KUBEBUILDER_ASSETS set

**Direct go test**:
```bash
go test ./...
```

Fails with: `unable to start the controlplane: fork/exec /usr/local/kubebuilder/bin/etcd: no such file or directory`

**Single test file**:
```bash
go test ./controllers/suite_test.go
```

Same failure - requires envtest infrastructure.

### Why Tests Cannot Run in Container

1. **Missing binaries**: Tests require etcd and kube-apiserver binaries from kubebuilder-tools
2. **Network setup**: envtest needs to start a local Kubernetes control plane
3. **Version incompatibility**: Latest setup-envtest requires Go 1.25+, this project uses Go 1.21
4. **No actual tests**: Even if infrastructure were available, there are 0 test specs to run

### Test Coverage

Command: `make test` generates `cover.out`
Threshold: None configured
**Reality**: Cannot measure coverage because tests don't run

## Build

### Dependencies

```bash
go mod download
```

### Full Build

```bash
make build
```

Produces: `bin/manager` (the operator binary)

### Container Build

```bash
make docker-build IMG=<your-image>
# Uses podman by default, set IMAGE_BUILDER=docker to use docker
```

### Code Generation

Required before building:

```bash
make manifests  # Generate CRDs, RBAC, webhooks
make generate   # Generate DeepCopy code
```

## Conventions

### Test Files

- **Pattern**: `*_test.go`
- **Framework**: Ginkgo BDD style
- **Structure**: `Describe`, `Context`, `It` blocks
- **Hooks**: `BeforeSuite`, `AfterSuite`

### Test Functions

Standard Go test function convention:
```go
func TestAPIs(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecsWithDefaultAndCustomReporters(t, "Controller Suite", ...)
}
```

### Imports

Dot imports are allowed for Ginkgo/Gomega:
```go
import (
    . "github.com/onsi/ginkgo"
    . "github.com/onsi/gomega"
)
```

This is explicitly allowed in `.golangci.yml` revive configuration.

### Code Organization

- `api/` - CRD definitions (v1alpha1)
- `controllers/` - Reconciler logic
- `pkg/` - Shared packages (deploy, featureflags)
- `config/` - Kustomize manifests
- `hack/` - Scripts and tooling

## Gaps & Caveats

### Critical Gaps

1. **No test specs**: Only test suite setup exists, 0 actual test cases
2. **No unit tests**: Controllers, API types, and packages have no tests
3. **Tests not in CI**: Lint is the only gating check
4. **Infrastructure dependency**: Tests require K8s control plane components
5. **Project archived**: README indicates project moved to new home

### What This Means for Agents

**Can validate**:
- ✅ Code formatting (make fmt)
- ✅ Linting (make lint) - **PRIMARY VALIDATION**
- ✅ Go vet checks (make vet)
- ✅ Build success (make build)
- ✅ Code generation (make generate/manifests)

**Cannot validate**:
- ❌ Unit tests (none exist)
- ❌ Integration tests (require cluster)
- ❌ Behavior correctness (no tests)
- ❌ Regression detection (no test coverage)

### Recommended Agent Workflow

For patch validation:

1. **Run lint** (make lint) - This is the only meaningful validation
2. **Check build** (make build) - Ensures code compiles
3. **Report**: "Lint passed, build succeeded. Note: This repo has no test coverage."

Do not attempt to run tests - they will always fail without Kubernetes infrastructure and contain 0 test cases anyway.

## Agent Readiness Rating

**Rating**: LOW

**Justification**:
- Lint validation works perfectly and is comprehensive
- Build validation works
- Tests exist but have 0 specs and require complex infrastructure
- An agent can lint patches successfully but cannot validate behavior
- No meaningful test coverage to detect regressions

**Best use case**: An agent can ensure patches don't introduce linting violations or break compilation, but cannot verify functional correctness.
