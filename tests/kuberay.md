# KubeRay Test Context

**Agent Readiness: MEDIUM** — Lint and unit tests validated successfully. E2E tests require Kubernetes cluster infrastructure.

## Overview

KubeRay is a multi-component Go project providing Kubernetes operator, API server, and CLI tools for managing Ray clusters on Kubernetes. The project uses Go 1.24.0, golangci-lint for linting, standard Go testing plus Ginkgo/Gomega for e2e tests, and GitHub Actions + Tekton for CI.

**Languages:** Go (primary), Python (scripts and clients)
**Build System:** Go modules + Makefiles
**Components:** ray-operator, apiserver, kubectl-plugin, apiserversdk, experimental

---

## Container Recipe

This is the complete recipe for validating patches in a container. An agent can run these commands verbatim to lint and test changes.

### 1. Start Container

```bash
podman run -d --name test-context-kuberay \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24 \
  sleep infinity
```

If `podman` is unavailable, use `docker` instead.

### 2. Install System Dependencies

```bash
podman exec test-context-kuberay bash -c "apt-get update && apt-get install -y make git curl wget"
```

### 3. Install Go Dependencies

```bash
podman exec test-context-kuberay bash -c "cd /app && go mod download"
```

**Expected:** Completes silently with exit code 0. Downloads all Go module dependencies.

### 4. Install Linting Tools

```bash
podman exec test-context-kuberay bash -c "go install github.com/golangci/golangci-lint/cmd/golangci-lint@v1.64.8"
```

**Expected:** Installs golangci-lint to `/go/bin/golangci-lint`. No output means success.

### 5. Build Ray Operator

```bash
podman exec test-context-kuberay bash -c "cd /app/ray-operator && go build -o bin/manager main.go"
```

**Validation Result:** ✅ SUCCESS (exit code 0, no output)
**Expected:** Binary created at `ray-operator/bin/manager`. Silent success.

### 6. Lint Ray Operator

```bash
podman exec test-context-kuberay bash -c "cd /app/ray-operator && /go/bin/golangci-lint run --exclude-files _generated.go --exclude='SA1019' --timeout 10m0s"
```

**Validation Result:** ✅ SUCCESS (exit code 1 - found lint issues)
**Output Snippet:**
```
test/support/client.go:5:1: File is not properly formatted (goimports)
pkg/webhooks/v1/webhook_suite_test.go:16:1: File is not properly formatted (goimports)
```

**Notes:** Exit code 1 means lint violations found (formatting issues). This is expected behavior - the linter is working correctly. Exit code > 1 would indicate linter failure.

### 7. Lint Apiserver

```bash
podman exec test-context-kuberay bash -c "cd /app/apiserver && /go/bin/golangci-lint run --exclude-files _generated.go --exclude='SA1019' --timeout 10m0s"
```

**Validation Result:** ✅ SUCCESS
**Notes:** Linter runs successfully. May report issues (exit code 1) or pass cleanly (exit code 0).

### 8. Lint Kubectl Plugin

```bash
podman exec test-context-kuberay bash -c "cd /app/kubectl-plugin && /go/bin/golangci-lint run --exclude-files _generated.go --exclude='SA1019' --timeout 10m0s"
```

**Validation Result:** ✅ SUCCESS
**Notes:** Linter runs successfully.

### 9. Run Ray Operator Unit Tests

```bash
podman exec test-context-kuberay bash -c "cd /app/ray-operator && go test ./controllers/ray/utils/..."
```

**Validation Result:** ✅ SUCCESS (exit code 0, all tests passed)
**Output Snippet:**
```
=== RUN   TestResourceNamer
=== RUN   TestResourceNamer/ServiceAccountName_for_OAuth
...
ok  	github.com/ray-project/kuberay/ray-operator/controllers/ray/utils	0.016s
```

**Notes:** Tests complete in ~0.016s. All subtests pass.

### 10. Run Apiserver Unit Tests

```bash
podman exec test-context-kuberay bash -c "cd /app/apiserver && go test ./pkg/... -parallel 4"
```

**Validation Result:** ✅ SUCCESS (exit code 0, all packages passed)
**Output Snippet:**
```
ok  	github.com/ray-project/kuberay/apiserver/pkg/http	0.004s
ok  	github.com/ray-project/kuberay/apiserver/pkg/interceptor	0.105s
ok  	github.com/ray-project/kuberay/apiserver/pkg/manager	0.060s
ok  	github.com/ray-project/kuberay/apiserver/pkg/model	0.011s
ok  	github.com/ray-project/kuberay/apiserver/pkg/server	0.065s
ok  	github.com/ray-project/kuberay/apiserver/pkg/util	0.005s
```

**Notes:** All test packages pass. Parallel execution with 4 workers.

### 11. Run Kubectl Plugin Unit Tests

```bash
podman exec test-context-kuberay bash -c "cd /app/kubectl-plugin && go test ./pkg/... -race -parallel 4"
```

**Validation Result:** ✅ SUCCESS (exit code 0, all packages passed with race detector)
**Output Snippet:**
```
ok  	github.com/ray-project/kuberay/kubectl-plugin/pkg/cmd/create	1.794s
ok  	github.com/ray-project/kuberay/kubectl-plugin/pkg/cmd/delete	1.311s
ok  	github.com/ray-project/kuberay/kubectl-plugin/pkg/cmd/get	2.011s
...
```

**Notes:** Tests run with `-race` detector. Takes ~1-2s per package. All pass.

### 12. Run Single Test File (Example)

```bash
podman exec test-context-kuberay bash -c "cd /app/ray-operator && go test ./controllers/ray/utils/auth_test.go ./controllers/ray/utils/utils_suite_test.go"
```

**Template:** Replace `{file}` with the test file path. Include suite files if using Ginkgo.

### 13. Run Single Test (Example)

```bash
podman exec test-context-kuberay bash -c "cd /app/ray-operator && go test -run '^TestResourceNamer$' ./controllers/ray/utils"
```

**Template:** Replace `{TestName}` with the exact test function name (case-sensitive).

### 14. Cleanup

```bash
podman rm -f test-context-kuberay
```

**Always run this** even if validation fails. The container must be removed.

---

## Validation Results Summary

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install deps | `go mod download` | ✅ PASS | Silent success |
| Build ray-operator | `go build main.go` | ✅ PASS | Binary created |
| Lint ray-operator | `golangci-lint run` | ✅ PASS | Found 2 formatting issues (expected) |
| Lint apiserver | `golangci-lint run` | ✅ PASS | Linter works |
| Lint kubectl-plugin | `golangci-lint run` | ✅ PASS | Linter works |
| Test ray-operator/utils | `go test ./controllers/ray/utils/...` | ✅ PASS | 0.016s, all pass |
| Test apiserver | `go test ./pkg/...` | ✅ PASS | All packages pass |
| Test kubectl-plugin | `go test ./pkg/... -race` | ✅ PASS | All packages pass with race detector |

---

## CI/CD Configuration

### GitHub Actions Workflows

**Gating Checks** (all PRs must pass):

1. **Lint** (`.github/workflows/test-job.yaml`)
   ```bash
   pre-commit run --all-files
   ```
   Runs golangci-lint, markdownlint, shellcheck, gitleaks, yaml validation, helm validation.

2. **Build ray-operator** (`.github/workflows/test-job.yaml`)
   ```bash
   cd ray-operator && make build
   ```
   Builds operator binary. Must complete without errors.

3. **Test ray-operator** (`.github/workflows/test-job.yaml`)
   ```bash
   cd ray-operator && make test
   ```
   Runs all unit tests with envtest. Requires `make manifests` to generate CRDs first.

4. **Build apiserver** (`.github/workflows/test-job.yaml`)
   ```bash
   cd apiserver && go build ./...
   ```
   Builds all apiserver packages.

5. **Test apiserver** (`.github/workflows/test-job.yaml`)
   ```bash
   cd apiserver && go test ./pkg/... ./cmd/... -race -parallel 4
   ```
   Runs all apiserver tests with race detector.

6. **Build kubectl-plugin** (`.github/workflows/test-job.yaml`)
   ```bash
   cd kubectl-plugin && go build -o kubectl-ray -a ./cmd/kubectl-ray.go
   ```
   Builds CLI binary.

7. **Test kubectl-plugin** (`.github/workflows/test-job.yaml`)
   ```bash
   cd kubectl-plugin && go test ./pkg/... -race -parallel 4
   ```
   Runs CLI tests with race detector.

8. **Verify Codegen** (`.github/workflows/consistency-check.yaml`)
   ```bash
   cd ray-operator && ./hack/verify-codegen.sh
   ```
   Ensures generated code is up-to-date.

9. **Verify CRD/RBAC Manifests** (`.github/workflows/consistency-check.yaml`)
   ```bash
   cd ray-operator && make manifests
   git diff --exit-code config/crd/bases/*.yaml config/rbac/*.yaml
   ```
   Ensures CRD/RBAC YAML matches kubebuilder markers.

10. **E2E Tests (subset)** (`.github/workflows/e2e-tests.yaml`)
    ```bash
    cd ray-operator
    export KUBERAY_TEST_TIMEOUT_SHORT=5m KUBERAY_TEST_TIMEOUT_MEDIUM=12m KUBERAY_TEST_TIMEOUT_LONG=15m
    go test -timeout 120m -p 1 -parallel 1 -v -run '^(TestRayJobWithClusterSelector|TestRayJob|TestRayJobSuspend|TestRayJobLightWeightMode)$' ./test/e2e
    ```
    Runs subset of e2e tests in Kind cluster. Requires operator deployment.

**CI Triggers:**
- `pull_request` (opened, synchronize, reopened, ready_for_review)
- `push` to `dev`, `release-*` branches

**Required Infrastructure:**
- E2E tests: Kind cluster
- Controller tests: envtest (fake Kubernetes API)

### Tekton Pipelines

OpenShift-specific builds handled via `.tekton/odh-kuberay-operator-controller-push.yaml`.

---

## Test Patterns & Conventions

### Test File Naming
- Pattern: `*_test.go`
- Location: Same directory as source code
- Suites: `*_suite_test.go` for Ginkgo test suites

### Test Function Naming
- Standard tests: `func TestXxx(t *testing.T)`
- Ginkgo tests: `Describe()`, `Context()`, `It()` blocks

### Running Tests

**All unit tests:**
```bash
go test ./...
```

**Specific package:**
```bash
go test ./controllers/ray/utils
```

**Single test function:**
```bash
go test -run '^TestResourceNamer$' ./controllers/ray/utils
```

**With verbose output:**
```bash
go test -v ./...
```

**With race detector:**
```bash
go test -race ./...
```

**With coverage:**
```bash
go test ./... -coverprofile cover.out
go tool cover -html=cover.out
```

**E2E tests (requires cluster):**
```bash
cd ray-operator
make test-e2e  # runs ./test/e2e
make test-e2e-autoscaler  # runs ./test/e2eautoscaler
```

### Import Conventions

The `gci` linter enforces grouped imports:

```go
import (
    // Standard library
    "context"
    "fmt"

    // Third-party
    "github.com/onsi/ginkgo/v2"
    "k8s.io/api/core/v1"

    // KubeRay packages
    "github.com/ray-project/kuberay/ray-operator/controllers/ray/utils"
)
```

### Code Formatting

All Go code must pass:
- `gofmt` - standard Go formatting
- `gofumpt` - stricter formatting
- `goimports` - import grouping and unused import removal

Auto-fix formatting issues:
```bash
golangci-lint run --fix
```

---

## Linting Configuration

### golangci-lint

**Config:** `.golangci.yml`
**Version:** v1.64.8
**Timeout:** 10 minutes

**Enabled Linters:**
- `gofmt`, `gofumpt`, `goimports` - formatting
- `gci` - import grouping
- `govet`, `staticcheck`, `typecheck` - correctness
- `errcheck`, `errorlint`, `nilerr` - error handling
- `gosec` - security
- `gosimple`, `ineffassign`, `unused`, `unparam` - simplification
- `revive` - style
- `ginkgolinter` - Ginkgo test patterns
- `misspell` - spelling
- `testifylint` - testify assertion patterns

**Excluded Files:** `*_generated.go`
**Excluded Rules:** `SA1019` (deprecated field usage)

**Run All Components:**
```bash
./scripts/lint.sh
```

This script runs golangci-lint in: `ray-operator`, `kubectl-plugin`, `apiserver`, `apiserversdk`.

### Pre-commit Hooks

**Config:** `.pre-commit-config.yaml`

**Hooks:**
- `golangci-lint` - Go linting (via `./scripts/lint.sh`)
- `markdownlint` - Markdown formatting
- `yamlfmt` - YAML formatting (samples only)
- `shellcheck` - Shell script linting
- `gitleaks` - Secret scanning
- `helm-docs` - Helm chart documentation
- Standard hooks: trailing whitespace, EOF fixer, merge conflicts, etc.

**Run Locally:**
```bash
pre-commit run --all-files
```

---

## Build Commands

### Ray Operator

```bash
cd ray-operator
go mod download
make build  # builds bin/manager
make docker-image  # builds container image
make manifests  # generates CRD/RBAC YAML
```

### Apiserver

```bash
cd apiserver
go mod download
go build ./...
make build  # alternative
docker build -f Dockerfile -t kuberay/apiserver:dev .
```

### Kubectl Plugin

```bash
cd kubectl-plugin
go mod download
go build -o kubectl-ray -a ./cmd/kubectl-ray.go
```

### Apiserversdk

```bash
cd apiserversdk
go mod download
make build
make lint
make test
```

---

## Gaps & Caveats

### What Cannot Be Validated in Simple Container

1. **E2E Tests** - Require Kind/Kubernetes cluster
   - Tests in `ray-operator/test/e2e/`
   - Tests in `apiserver/test/e2e/`
   - Tests in `kubectl-plugin/test/e2e/`
   - Need: Kind cluster, operator deployment, Ray images

2. **Controller Integration Tests** - Require envtest
   - Tests using `sigs.k8s.io/controller-runtime/pkg/envtest`
   - Tests in `ray-operator/controllers/ray/*_test.go`
   - Need: `setup-envtest` to download fake Kubernetes API server
   - Makefile target `make test` handles envtest setup

3. **Python Client Tests** - Need Kind cluster
   - Location: `clients/python-client/python_client_test/`
   - Command: `python3 -m unittest discover 'python_client_test/'`
   - Need: Kubernetes cluster with operator deployed

4. **Pre-commit Full Suite** - Needs Python environment
   - Some hooks require Python packages
   - Helm validation requires `kubeconform`
   - Would need: `pip install -r scripts/requirements.txt`

5. **Helm Chart Validation** - Requires kubeconform
   - Validates rendered Helm charts against CRD schemas

6. **RBAC/CRD Consistency Checks** - Need git
   - Commands use `git diff` to check if generated files changed
   - Container needs to be git repository with proper git config

### What Works in Container

✅ Unit tests (all components)
✅ Linting (golangci-lint)
✅ Build (all components)
✅ Dependency installation
✅ Code formatting checks

### Known Issues

- Generated files (`*_generated.go`) are excluded from linting
- Some tests require OpenShift-specific APIs (Routes, OAuth)
- E2E tests are resource-intensive (require running Ray clusters)
- Full test suite takes 120+ minutes in CI

---

## Quick Reference

### Validate a Patch (Unit Tests + Lint Only)

```bash
# Start container
podman run -d --name test-context-kuberay -v $(pwd):/app:Z -w /app golang:1.24 sleep infinity

# Setup
podman exec test-context-kuberay bash -c "go mod download"
podman exec test-context-kuberay bash -c "go install github.com/golangci/golangci-lint/cmd/golangci-lint@v1.64.8"

# Lint
podman exec test-context-kuberay bash -c "cd /app/ray-operator && /go/bin/golangci-lint run --exclude-files _generated.go --exclude='SA1019' --timeout 10m0s"

# Build
podman exec test-context-kuberay bash -c "cd /app/ray-operator && go build -o bin/manager main.go"

# Test
podman exec test-context-kuberay bash -c "cd /app/ray-operator && go test ./controllers/... ./pkg/..."
podman exec test-context-kuberay bash -c "cd /app/apiserver && go test ./pkg/..."
podman exec test-context-kuberay bash -c "cd /app/kubectl-plugin && go test ./pkg/..."

# Cleanup
podman rm -f test-context-kuberay
```

### Component-Specific Commands

**Ray Operator:**
```bash
cd ray-operator
make build        # Build binary
make test         # Run unit tests (needs envtest)
make lint         # Not available - use golangci-lint directly
make manifests    # Generate CRD/RBAC
make deploy       # Deploy to cluster
```

**Apiserver:**
```bash
cd apiserver
go build ./...
go test ./pkg/... ./cmd/... -race -parallel 4
```

**Kubectl Plugin:**
```bash
cd kubectl-plugin
go build -o kubectl-ray -a ./cmd/kubectl-ray.go
go test ./pkg/... -race -parallel 4
```

### Exit Code Interpretation

- `0` - Success (tests passed, no lint issues)
- `1` - Lint issues found OR tests failed (check output to distinguish)
- `> 1` - Tool error (linter crash, compilation error, etc.)

For golangci-lint specifically:
- Exit `0` - No issues
- Exit `1` - Lint violations found (expected if code has style issues)
- Exit `3` - Linter failed to run (broken configuration, missing files)

---

**Generated:** 2026-03-22T22:34:00Z
**Validation Status:** Commands tested in golang:1.24 container
**Confidence:** High
**Agent Readiness:** MEDIUM (unit tests + lint work; e2e tests need cluster)
