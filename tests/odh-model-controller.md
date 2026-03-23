# Test Context for odh-model-controller

## Overview

**Repository:** opendatahub-io/odh-model-controller
**Language:** Go 1.25.7
**Build System:** Make + Go modules
**Test Framework:** Ginkgo v2 + Gomega + envtest
**Agent Readiness:** **HIGH** - All lint and test commands validated successfully in container

This is a Kubernetes operator (controller) built with Kubebuilder that extends KServe functionality for OpenShift. The test suite uses envtest to run controller tests against a real Kubernetes API server.

## Container Recipe

This is a **complete, copy-paste recipe** for validating patches. An agent can follow these steps verbatim.

### 1. Start Container

Use `golang:1.23` base image (Go 1.25.7 will be auto-downloaded via GOTOOLCHAIN):

```bash
podman run -d --name test-context-odh-model-controller \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.23 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-odh-model-controller bash -c \
  "apt-get update && apt-get install -y make git wget curl"
```

### 3. Set Go Toolchain

The project requires Go 1.25.7. Set `GOTOOLCHAIN=auto` to enable automatic download:

```bash
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && go version"
```

Expected output: `go version go1.25.7 linux/amd64`

### 4. Download Go Dependencies

```bash
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && go mod download"
```

**Expected result:** Exit code 0, all dependencies downloaded.

### 5. Install Build Tools

Install golangci-lint and envtest tools:

```bash
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && make golangci-lint envtest"
```

**Expected result:** Tools installed in `bin/` directory.

### 6. Download envtest Binaries

Download Kubernetes control plane binaries for testing:

```bash
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && ./bin/setup-envtest use 1.31.0 --bin-dir ./bin"
```

**Expected result:** Binaries downloaded to `bin/k8s/1.31.0-linux-amd64/`

### 7. Run Lint

**Command:**
```bash
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && make lint"
```

**Expected result:**
- Exit code: 0
- Output: `0 issues.`

**Validation status:** ✅ **PASSED** - 0 issues found

Alternative commands:
```bash
# Run fmt
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && make fmt"

# Run vet
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && make vet"

# Auto-fix lint issues
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && make lint-fix"
```

### 8. Run Tests

**Command:**
```bash
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && make test"
```

**Expected result:**
- 17 test packages will run
- All should show `ok` status
- Exit code may be 1 due to "no such tool 'covdata'" warnings (these are informational, not failures)
- Look for lines like:
  ```
  ok    github.com/opendatahub-io/odh-model-controller/internal/controller/core    36.834s    coverage: 6.3% of statements in ./...
  ok    github.com/opendatahub-io/odh-model-controller/internal/controller/nim     10.957s    coverage: 6.0% of statements in ./...
  ```

**Validation status:** ✅ **PASSED** - All 17/17 test packages passed

**Interpreting exit codes:**
- The command may exit with code 1 due to "covdata" tool warnings
- These warnings are about Go 1.25 coverage tooling, NOT test failures
- Check the output for `ok` vs `FAIL` on each package line
- If all packages show `ok`, tests passed successfully

### 9. Run Single Test File

```bash
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && \
   KUBEBUILDER_ASSETS=\$(./bin/setup-envtest use 1.31.0 --bin-dir ./bin -p path) \
   POD_NAMESPACE=default \
   go test ./internal/controller/comparators"
```

Replace `./internal/controller/comparators` with the package path containing the test file.

### 10. Run Single Test by Name

```bash
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && \
   KUBEBUILDER_ASSETS=\$(./bin/setup-envtest use 1.31.0 --bin-dir ./bin -p path) \
   POD_NAMESPACE=default \
   go test ./internal/controller/core -ginkgo.focus 'ConfigMap controller'"
```

Replace `'ConfigMap controller'` with the test description (from Describe/It blocks).

### 11. Build

```bash
podman exec test-context-odh-model-controller bash -c \
  "export GOTOOLCHAIN=auto && cd /app && make build"
```

**Expected result:** Binary created at `bin/manager`

**Validation status:** ✅ **PASSED** - Build successful

### 12. Cleanup

**ALWAYS run this when done:**

```bash
podman rm -f test-context-odh-model-controller
```

## Validation Results

All commands were validated in a `golang:1.23` container:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install deps | `go mod download` | ✅ PASS | Required GOTOOLCHAIN=auto |
| Build | `make build` | ✅ PASS | Binary created successfully |
| Lint | `make lint` | ✅ PASS | 0 issues found |
| Tests | `make test` | ✅ PASS | 17/17 packages passed |

**Test results breakdown:**
- Total test packages: 17
- Passed: 17
- Failed: 0
- Coverage: 0.2% - 18.5% per package (varies by module)

**Lint results:**
- golangci-lint: 0 issues
- gofmt: no formatting issues
- go vet: no issues

## CI/CD Configuration

### GitHub Actions Workflows

Three **gating checks** run on every push/PR:

#### 1. Lint (`.github/workflows/lint.yml`)

**Trigger:** push, pull_request
**Runs:** golangci-lint v2.11.3

```bash
# CI runs via GitHub Action
golangci/golangci-lint-action@v7
```

**Local equivalent:**
```bash
make lint
```

**Required to merge:** Yes

#### 2. Tests (`.github/workflows/test.yml`)

**Trigger:** push, pull_request
**Runs:**
1. Check go.mod is tidy
2. Run unit tests

```bash
go mod tidy
git diff --exit-code || exit 1
make test
```

**Required to merge:** Yes

**Important:** The workflow fails if `go mod tidy` would make changes. Always run `go mod tidy` before committing dependency changes.

#### 3. Validate Manifests (`.github/workflows/validate-manifests.yml`)

**Trigger:** push, pull_request
**Runs:** Kustomize validation on all kustomization.yaml files

```bash
./hack/validate-manifests.sh
```

**Required to merge:** Yes

**Note:** Requires kustomize 5.7.1. The script finds all `kustomization.yaml` files and validates they can build.

### Advisory Checks

#### E2E Tests (`.github/workflows/test-e2e.yml`)

**Trigger:** Manual or specific events
**Runs:** End-to-end tests in Kind cluster

```bash
make test-e2e
```

**Required to merge:** No (requires infrastructure)

## Test Framework Details

### Structure

- **Framework:** Ginkgo v2 (BDD-style) + Gomega (matchers)
- **Controller testing:** envtest (real Kubernetes API server)
- **Test files:** `*_test.go` in `internal/` and `test/` directories
- **Test count:** 48 test files across 17 packages

### Test Patterns

Tests use Ginkgo BDD style:

```go
Describe("ConfigMap controller", func() {
    Context("when a storage config secret is created", func() {
        It("should create a ConfigMap", func() {
            // test code
        })
    })
})
```

### Test Suites

Each test suite has:
- `BeforeSuite`: Starts envtest Kubernetes API
- `AfterSuite`: Stops envtest
- `AfterEach`: Cleans up test resources

### Required Environment

Tests need:
- `KUBEBUILDER_ASSETS`: Path to envtest binaries (etcd, kube-apiserver, kubectl)
- `POD_NAMESPACE`: Namespace for test resources (usually "default")
- `GOTOOLCHAIN`: Set to "auto" for Go 1.25.7 download

### Test Categories

1. **Unit tests** (`internal/controller/comparators`, `internal/controller/resources`): Fast, no Kubernetes
2. **Controller tests** (`internal/controller/core`, `internal/controller/nim`): Use envtest, slower
3. **Webhook tests** (`internal/webhook/*/v1`): Test admission webhooks with envtest
4. **E2E tests** (`test/e2e/`): Require real cluster, excluded from `make test`

## Linting Configuration

### golangci-lint (`.golangci.yml`)

**Version:** v2.11.3

**Enabled linters (25):**
- Code quality: errcheck, ineffassign, staticcheck, unused, unconvert, unparam
- Complexity: gocyclo, gocognit
- Style: gofmt, goimports, misspell, revive
- Testing: ginkgolinter
- Duplication: dupl
- Constants: goconst
- Performance: prealloc
- And more...

**Formatters:**
- gofmt
- goimports

**Auto-fix available:** `make lint-fix` will automatically fix many issues

**Exclusions:**
- Line length (lll) excluded for `api/` and `internal/` paths
- Duplication (dupl) excluded for `internal/`
- Generated code excluded

## Conventions

### File Naming

- Test files: `*_test.go`
- Controller files: `*_controller.go`
- Webhook files: `*_webhook.go`
- Suite setup: `suite_test.go`

### Test Naming

- Test functions: `TestXxx(t *testing.T)` with Ginkgo `RunSpecs`
- BDD blocks: `Describe`, `Context`, `It`, `BeforeEach`, `AfterEach`
- Focused tests: `FDescribe`, `FIt` (avoid committing these)
- Pending tests: `PDescribe`, `PIt`

### Code Organization

Follows Kubebuilder conventions:

```
api/                    # API type definitions (CRDs)
cmd/                    # Main entry point
config/                 # Kustomize manifests, CRDs, RBAC
internal/controller/    # Controller reconciliation logic
internal/webhook/       # Admission webhooks
test/                   # Shared test utilities, fixtures, e2e
```

### Import Style

Standard library, third-party, internal separated by blank lines:

```go
import (
    "context"
    "fmt"

    "github.com/onsi/ginkgo/v2"
    "github.com/onsi/gomega"

    "github.com/opendatahub-io/odh-model-controller/api/v1"
)
```

## Gaps & Caveats

### 1. Go Version Requirement

The project requires Go 1.25.7, which is a pre-release/development version. You MUST set `GOTOOLCHAIN=auto` to allow Go to download this version automatically.

### 2. E2E Tests Not Included

The `make test` command excludes E2E tests (`test/e2e/`). These require:
- A running Kubernetes cluster (Kind, OpenShift, etc.)
- Specific infrastructure (KServe, Istio, etc.)
- Run with: `make test-e2e` (requires Kind cluster)

### 3. envtest Binary Download

Tests require Kubernetes control plane binaries (23MB etcd, 90MB kube-apiserver, 56MB kubectl). The first test run downloads these automatically via `setup-envtest`. Subsequent runs are faster.

### 4. Test Exit Code Issue

`make test` exits with code 1 due to "no such tool 'covdata'" warnings from Go 1.25. These are informational warnings about coverage tooling, NOT test failures. Always check the output for `ok` vs `FAIL` on each package line.

**Example of successful run despite exit code 1:**
```
ok    github.com/opendatahub-io/odh-model-controller/internal/controller/core    36.834s    coverage: 6.3%
ok    github.com/opendatahub-io/odh-model-controller/internal/controller/nim     10.957s    coverage: 6.0%
[...all packages show 'ok'...]
make: *** [Makefile:112: test] Error 1
```

### 5. Generated Code

Some files are generated by controller-gen:
- CRDs in `config/crd/bases/`
- DeepCopy methods (`zz_generated.deepcopy.go`)
- Webhook configurations
- RBAC manifests

Run `make manifests generate` to regenerate. These should be committed to the repo.

### 6. Container Build

The Containerfile uses `registry.access.redhat.com/ubi9/go-toolset:1.25` which may not be publicly accessible. For local builds, use `make container-build` with podman or docker.

### 7. Coverage Percentages

Coverage is relatively low (0.2-18.5% per package). This is common for Kubernetes controllers where much of the code interacts with external systems that are mocked or require integration testing.

## Quick Reference

### Essential Commands

```bash
# Install dependencies
go mod download

# Lint
make lint

# Fix lint issues
make lint-fix

# Test (unit + controller tests)
make test

# Build binary
make build

# Build container
make container-build

# Generate manifests
make manifests generate

# Install CRDs to cluster
make install

# Deploy controller to cluster
make deploy

# Run locally (requires kubeconfig)
make run
```

### Environment Variables

```bash
export GOTOOLCHAIN=auto                    # Required for Go 1.25.7
export KUBEBUILDER_ASSETS=/app/bin/k8s/1.31.0-linux-amd64
export POD_NAMESPACE=default
```

### Useful Targets

```bash
make help              # List all make targets
make fmt               # Run gofmt
make vet               # Run go vet
make build-server      # Build model-serving-api
make test-e2e          # Run e2e tests (requires Kind)
```

---

**Generated:** 2026-03-22T23:46:21Z
**Confidence:** High
**Agent Readiness:** High - All commands validated successfully in container
