# Test Context: opendatahub-io/kubeflow

**Generated:** 2026-03-22T22:36:15Z

## Overview

Go-based Kubernetes controllers for Jupyter notebooks in Kubeflow/OpenDataHub. Two main components: notebook-controller (upstream Kubeflow) and odh-notebook-controller (OpenDataHub variant). Uses kubebuilder framework with ginkgo/gomega testing.

**Languages:** Go (primary), Python (utility scripts only)
**Build System:** Make + Go toolchain
**Agent Readiness:** **HIGH** - Lint and test commands validated successfully in container. All unit tests pass, linters work correctly.

## Container Recipe

This recipe provides a complete, copy-paste workflow for validating patches in a clean container environment.

### 1. Start Container

```bash
podman run -d --name kubeflow-validation \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.22 \
  sleep infinity
```

**Note:** Uses `golang:1.22` as base. Go 1.25.7 is required by go.mod and will be auto-downloaded via `GOTOOLCHAIN=auto`.

### 2. Install System Dependencies

```bash
podman exec kubeflow-validation bash -c \
  "apt-get update -qq && apt-get install -y -qq make git curl python3 python3-pip"
```

### 3. Install Linters

```bash
# Install golangci-lint v2.8.0
podman exec kubeflow-validation bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v2.8.0"

# Install flake8 for Python
podman exec kubeflow-validation bash -c \
  "pip3 install flake8 --break-system-packages -q"
```

### 4. Download Go Dependencies

```bash
# notebook-controller
podman exec kubeflow-validation bash -c \
  "cd /app/components/notebook-controller && GOTOOLCHAIN=auto go mod download"

# odh-notebook-controller
podman exec kubeflow-validation bash -c \
  "cd /app/components/odh-notebook-controller && GOTOOLCHAIN=auto go mod download"
```

**Expected:** Go 1.25.7 will be downloaded automatically on first run.

### 5. Build

```bash
# Build notebook-controller
podman exec kubeflow-validation bash -c \
  "cd /app/components/notebook-controller && GOTOOLCHAIN=auto go build -o bin/manager main.go"

# Build odh-notebook-controller
podman exec kubeflow-validation bash -c \
  "cd /app/components/odh-notebook-controller && GOTOOLCHAIN=auto go build -o bin/manager main.go"
```

**Expected:** Exit code 0. Binaries in `bin/manager`.

### 6. Run Linters

#### golangci-lint (notebook-controller)

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/notebook-controller && GOTOOLCHAIN=auto golangci-lint run --timeout=5m"
```

**Validated:** Exit code 1 (found 64 lines of issues: errcheck, staticcheck, etc.)
**Result:** Linter working correctly, found legitimate code quality issues.

#### golangci-lint (odh-notebook-controller)

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/odh-notebook-controller && GOTOOLCHAIN=auto golangci-lint run --timeout=5m"
```

**Validated:** Exit code 1 (found 3 issues: 1 staticcheck, 2 unused)
**Result:** Linter working correctly.

#### go fmt

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/notebook-controller && GOTOOLCHAIN=auto go fmt ./..."

podman exec kubeflow-validation bash -c \
  "cd /app/components/odh-notebook-controller && GOTOOLCHAIN=auto go fmt ./..."
```

**Validated:** Exit code 0. No formatting issues.

#### go vet

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/notebook-controller && GOTOOLCHAIN=auto go vet ./..."

podman exec kubeflow-validation bash -c \
  "cd /app/components/odh-notebook-controller && GOTOOLCHAIN=auto go vet ./..."
```

**Validated:** Exit code 0. No vet issues.

#### go mod verify

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/notebook-controller && GOTOOLCHAIN=auto go mod verify"

podman exec kubeflow-validation bash -c \
  "cd /app/components/odh-notebook-controller && GOTOOLCHAIN=auto go mod verify"
```

**Validated:** Exit code 0. All modules verified.

#### flake8 (Python)

```bash
podman exec kubeflow-validation bash -c \
  "cd /app && flake8 components/"
```

**Validated:** Exit code 1 (found style violations in utility scripts)
**Result:** Python linting works but violations appear to be accepted/ignored.

### 7. Run Tests

#### notebook-controller (unit tests)

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/notebook-controller && GOTOOLCHAIN=auto make test"
```

**Validated:** Exit code 0
**Result:** 1 spec passed, 0 failed, coverage 34.8%
**Notes:** Some "no such tool 'covdata'" warnings appear but don't affect execution.

#### odh-notebook-controller (unit tests - RBAC false)

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/odh-notebook-controller && GOTOOLCHAIN=auto make test-with-rbac-false"
```

**Validated:** Exit code 0
**Result:** 102 of 104 specs passed (2 skipped), coverage 69.8%
**Duration:** ~90 seconds

#### odh-notebook-controller (unit tests - RBAC true)

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/odh-notebook-controller && GOTOOLCHAIN=auto make test-with-rbac-true"
```

**Validated:** Exit code 0
**Result:** 104 of 104 specs passed, coverage 71.1%
**Duration:** ~103 seconds

#### Run both RBAC test suites together

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/odh-notebook-controller && GOTOOLCHAIN=auto make test"
```

**Expected:** Runs both test-with-rbac-false and test-with-rbac-true sequentially.

### 8. Run Single Test File

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/notebook-controller && \
   GOTOOLCHAIN=auto \
   KUBEBUILDER_ASSETS=\"\$(./bin/setup-envtest use 1.32 -p path)\" \
   go test -v ./controllers/notebook_controller_test.go"
```

### 9. Run Single Test (ginkgo focus)

```bash
podman exec kubeflow-validation bash -c \
  "cd /app/components/odh-notebook-controller && \
   GOTOOLCHAIN=auto \
   KUBEBUILDER_ASSETS=\"\$(./bin/setup-envtest use 1.32 -p path)\" \
   go test -v ./controllers/... -ginkgo.focus='should create the Notebook StatefulSet'"
```

### 10. Cleanup

```bash
podman rm -f kubeflow-validation
```

## Validation Results

All commands validated in golang:1.22 container on 2026-03-22:

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install | apt-get install make git curl python3 | 0 | ✅ PASS | System deps OK |
| Install | go mod download | 0 | ✅ PASS | Go 1.25.7 auto-downloaded |
| Build | go build -o bin/manager | 0 | ✅ PASS | Binary builds cleanly |
| Lint | golangci-lint run (notebook) | 1 | ✅ PASS | Found 64 lines of issues |
| Lint | golangci-lint run (odh) | 1 | ✅ PASS | Found 3 issues |
| Lint | go fmt | 0 | ✅ PASS | No formatting issues |
| Lint | go vet | 0 | ✅ PASS | No vet issues |
| Lint | go mod verify | 0 | ✅ PASS | All modules verified |
| Lint | flake8 | 1 | ✅ PASS | Found Python style issues |
| Test | make test (notebook) | 0 | ✅ PASS | 1 spec, 34.8% coverage |
| Test | make test (odh, RBAC false) | 0 | ✅ PASS | 102 specs, 69.8% coverage |
| Test | make test (odh, RBAC true) | 0 | ✅ PASS | 104 specs, 71.1% coverage |

**Summary:** All validation successful. Lint and test commands work correctly in clean container. Exit code 1 for linters indicates legitimate issues found, not command failure.

## CI/CD Configuration

### GitHub Actions (Gating on PR)

The following workflows gate pull requests to `main` and `v1.10-branch`:

#### code-quality.yaml

```bash
# golangci-lint for both components
cd components/notebook-controller && golangci-lint run --timeout=5m --only-new-issues
cd components/odh-notebook-controller && golangci-lint run --timeout=5m --only-new-issues

# go mod verify
cd components/{component} && go mod verify

# go mod tidy check (fails if uncommitted changes)
cd components/{component} && go mod tidy && git diff --exit-code

# govulncheck vulnerability scan
cd components/{component} && make govulncheck

# Check generated code hasn't changed
bash ci/generate_code.sh && git diff --exit-code

# Kustomize manifest validation
./ci/kustomize.sh
```

**Trigger:** `on: pull_request` to main/v1.10-branch
**Required:** Yes, all checks must pass to merge
**Validated:** golangci-lint, go mod verify, go fmt/vet all validated in container

#### notebook_controller_unit_test.yaml

```bash
cd components/notebook-controller && make test
```

**Trigger:** `on: pull_request` when notebook-controller files change
**Required:** Yes
**Validated:** ✅ All tests pass (1 spec)

#### odh_notebook_controller_unit_test.yaml

```bash
cd components/odh-notebook-controller && make test
```

**Trigger:** `on: pull_request` when odh-notebook-controller files change
**Required:** Yes
**Validated:** ✅ All tests pass (206 total specs across two RBAC modes)

#### Integration Tests (notebook_controller_integration_test.yaml)

```bash
# Builds container, creates KinD cluster, deploys controller, runs basic tests
cd components/notebook-controller
make docker-build
kind create cluster
kind load docker-image
kubectl apply -f manifests
```

**Trigger:** `on: pull_request` when notebook-controller files change
**Required:** Likely gating
**Validated:** ❌ Requires KinD cluster - cannot run in basic container

### Tekton (OpenShift CI)

`.tekton/odh-notebook-controller-pull-request.yaml` triggers multi-arch container builds using Konflux pipelines on OpenShift. Not directly relevant to local validation.

## Test Framework Details

### Structure

Tests use **ginkgo** (BDD framework) + **gomega** (matchers) + **envtest** (lightweight K8s API):

```go
var _ = Describe("Notebook Controller", func() {
    It("should create the Notebook StatefulSet", func() {
        // test code
        Expect(err).NotTo(HaveOccurred())
    })
})
```

### Test Files

- `components/notebook-controller/controllers/*_test.go` - 4 test files
- `components/odh-notebook-controller/controllers/*_test.go` - 9 test files
- `components/odh-notebook-controller/e2e/*_test.go` - 5 E2E test files (require cluster)

### Running Tests

- **All tests:** `make test`
- **Single file:** `go test -v {file}`
- **Single test:** `go test -v ./controllers/... -ginkgo.focus="{pattern}"`
- **Coverage:** Auto-generated as `cover.out` or `cover-rbac-{true,false}.out`

### RBAC Test Modes

`odh-notebook-controller` runs tests twice:
1. `SET_PIPELINE_RBAC=false` - 102 specs run (2 skipped)
2. `SET_PIPELINE_RBAC=true` - 104 specs run (0 skipped)

This tests different authorization configurations for data science pipelines.

## Conventions

### File Naming

- Test files: `*_test.go`
- Controllers: `*_controller.go`
- Webhooks: `*_webhook.go`

### Test Naming

- Functions: `Test*` (standard Go)
- Ginkgo blocks: `Describe("Component", func() { It("should do X", ...) })`

### Import Style

Standard Go imports with kubebuilder/controller-runtime patterns:

```go
import (
    ctrl "sigs.k8s.io/controller-runtime"
    "sigs.k8s.io/controller-runtime/pkg/client"
)
```

### Code Generation

Before committing changes, regenerate manifests and code:

```bash
cd components/notebook-controller
make manifests generate fmt

cd components/odh-notebook-controller
make manifests generate fmt
```

Or run the CI script: `bash ci/generate_code.sh`

## Gaps & Caveats

### Integration Tests Not Runnable in Container

Integration tests (`.github/workflows/*_integration_test.yaml`) require:
- KinD (Kubernetes in Docker) cluster
- Container image building and loading
- Istio installation
- kubectl/kustomize

These cannot run in a simple validation container. They're tested in CI only.

### E2E Tests Require Full Cluster

E2E tests in `components/odh-notebook-controller/e2e/` require:
- Live Kubernetes/OpenShift cluster
- Deployed notebook controllers
- Network access to created notebook pods

Use `make e2e-test` only when running against a real cluster.

### Go Version Auto-Download

The go.mod requires Go 1.25.7, which is newer than golang:1.22 base image. Using `GOTOOLCHAIN=auto` automatically downloads the correct version on first use. This adds ~30 seconds to initial runs but is cached afterward.

### Coverage Tool Warnings

Tests produce warnings like `go: no such tool "covdata"` due to Go toolchain version mismatches. These don't affect test execution or results - all tests pass despite the warnings.

### Python Linting Violations Accepted

`flake8` finds numerous violations in `concatenate_license.py` files, but these appear to be accepted. The `.flake8` config ignores some rules (E111, E114) but not all violations.

### No Pre-Commit Hooks

Unlike some projects, this repo doesn't use `.pre-commit-config.yaml`. Developers must remember to run `make manifests generate fmt` before committing.

### semgrep Not in CI

A comprehensive `semgrep.yaml` config exists but isn't run in GitHub Actions. It may be used locally or in Tekton pipelines.

## Quick Reference

### Component Locations

- **notebook-controller:** `components/notebook-controller/` (upstream Kubeflow)
- **odh-notebook-controller:** `components/odh-notebook-controller/` (OpenDataHub variant)
- **Common code:** `components/common/`

### Key Commands

```bash
# Lint all
cd components/notebook-controller && GOTOOLCHAIN=auto golangci-lint run --timeout=5m
cd components/odh-notebook-controller && GOTOOLCHAIN=auto golangci-lint run --timeout=5m

# Test all
cd components/notebook-controller && GOTOOLCHAIN=auto make test
cd components/odh-notebook-controller && GOTOOLCHAIN=auto make test

# Build all
cd components/notebook-controller && GOTOOLCHAIN=auto make build
cd components/odh-notebook-controller && GOTOOLCHAIN=auto make build

# Regenerate code
bash ci/generate_code.sh
```

### Environment Variables

- `GOTOOLCHAIN=auto` - Required for Go 1.25.7
- `KUBEBUILDER_ASSETS=$(./bin/setup-envtest use 1.32 -p path)` - For tests
- `SET_PIPELINE_RBAC=true|false` - ODH controller test mode

### Coverage Thresholds

No explicit thresholds configured, but current coverage:
- notebook-controller: ~35%
- odh-notebook-controller: ~70%

## Summary

**Agent Readiness: HIGH**

This repository is highly suitable for automated patch validation:

✅ **Pros:**
- All lint commands validated and working
- All unit tests pass with good coverage
- Clean container recipe with minimal dependencies
- Fast test execution (~2-3 minutes for all unit tests)
- Clear separation of unit vs integration tests
- Comprehensive CI configuration

⚠️ **Considerations:**
- Integration tests require cluster infrastructure (run in CI only)
- Go version auto-download adds initial overhead
- Two components must be tested separately
- Code generation must be run before committing changes

**Recommendation:** An agent can successfully validate patches by running lint and unit tests in a container. Integration tests should be left to CI.
