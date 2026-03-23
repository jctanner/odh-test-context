# Test Context: codeflare-operator-poc

## Overview

**Repository**: opendatahub-io/codeflare-operator-poc
**Language**: Go 1.23.0
**Build System**: Makefile + go
**Agent Readiness**: **medium** — Linting commands validated successfully. Tests require Kubernetes control plane binaries (envtest) which are not easily available in standard containers but work in the CI environment.

## Container Recipe

This recipe allows you to validate patches in an isolated container. **Note**: Unit/component tests require special setup (see Gaps section).

### 1. Start Container

```bash
podman run -d --name test-context-codeflare-operator-poc \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.23 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-codeflare-operator-poc bash -c \
  "apt-get update && apt-get install -y make git curl"
```

### 3. Install Go Dependencies

```bash
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && go mod download"
```

**Validation**: Exit code 0, no errors.

### 4. Install Linters

```bash
podman exec test-context-codeflare-operator-poc bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v1.61.0"
```

### 5. Run go fmt

```bash
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && go fmt ./..."
```

**Validation**: Exit code 0, no formatting changes. Indicates code follows Go formatting standards.

### 6. Run go vet

```bash
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && go vet ./..."
```

**Validation**: Exit code 0, no issues found.

### 7. Run golangci-lint

```bash
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && golangci-lint run --timeout=10m"
```

**Validation**: Exit code 0, no lint issues. Runs 7 linters: errcheck, gosimple, govet, ineffassign, staticcheck, typecheck, unused.

### 8. Build

```bash
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && go build -o /tmp/manager main.go"
```

**Validation**: Exit code 0, binary created successfully.

### 9. Run Unit Tests (⚠️ Requires Special Setup)

```bash
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && make test-unit"
```

**Validation**: **FAILED** — Tests require Kubernetes control plane binaries (etcd, kube-apiserver) via envtest. The `setup-envtest` tool fails to download these with "401 Unauthorized" from Google Cloud Storage in standard containers.

**Workaround**: Use the CI container image `quay.io/opendatahub/pre-commit-go-toolchain:v0.2` which has envtest pre-configured, or run tests in an environment with cluster access.

### 10. Run Single Test File

```bash
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && go test -v ./pkg/controllers/raycluster_controller_test.go"
```

Note: Same envtest requirement applies.

### 11. Run Single Test by Name

```bash
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && go test -v ./pkg/controllers/ -ginkgo.focus='RayCluster Reconciler'"
```

Note: Tests use Ginkgo BDD framework. Use `-ginkgo.focus` to filter by test description.

### 12. Cleanup

```bash
podman rm -f test-context-codeflare-operator-poc
```

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Dependencies | `go mod download` | ✅ PASS | Exit 0 |
| Build | `go build -o /tmp/manager main.go` | ✅ PASS | Exit 0 |
| go fmt | `go fmt ./...` | ✅ PASS | Exit 0, no changes |
| go vet | `go vet ./...` | ✅ PASS | Exit 0, no issues |
| golangci-lint | `golangci-lint run --timeout=10m` | ✅ PASS | Exit 0, all checks pass |
| yamllint | `yamllint --strict -c .yamllint.yaml .` | ✅ PASS | Exit 0, YAML valid |
| Unit tests | `make test-unit` | ❌ FAIL | Envtest binaries unavailable (401 from GCS) |
| Component tests | `make test-component` | ❌ FAIL | Same envtest requirement |

## CI/CD

### Gating Checks (Required for Merge)

All triggered on `pull_request` and `push`:

1. **Pre-commit** (`.github/workflows/precommit.yml`)
   ```bash
   pre-commit run --all-files
   ```
   Runs go-fmt, golangci-lint, go-mod-tidy, yamllint, and other checks.

2. **Unit Tests** (`.github/workflows/unit_tests.yml`)
   ```bash
   make test-unit
   ```
   Runs `go test -v ./pkg/controllers/ -coverprofile cover.out` with envtest.

3. **Component Tests** (`.github/workflows/component_tests.yaml`)
   ```bash
   make test-component
   ```
   Uses Ginkgo CLI: `$(GINKGO) -v ./pkg/controllers/`

4. **Verify Imports** (`.github/workflows/verify_generated_files.yml`)
   ```bash
   make verify-imports
   ```
   Checks that imports are organized per openshift-goimports style.

5. **Verify Manifests** (`.github/workflows/verify_generated_files.yml`)
   ```bash
   make manifests && git diff --exit-code
   ```
   Ensures generated RBAC and CRD manifests are up to date.

### Advisory Checks

- **E2E Tests** (`.github/workflows/e2e_tests.yaml`) — Requires Kubernetes cluster
  ```bash
  make test-e2e
  ```

### CI Container

CI workflows run in `quay.io/opendatahub/pre-commit-go-toolchain:v0.2` which includes:
- Go 1.23+
- pre-commit
- golangci-lint
- envtest binaries pre-configured

## Conventions

### Test Files
- **Pattern**: `*_test.go`
- **Unit tests**: `pkg/controllers/*_test.go`
- **E2E tests**: `test/e2e/*_test.go`
- **Suite setup**: `pkg/controllers/suite_test.go`

### Test Framework
- **Ginkgo/Gomega** for BDD-style tests
- **envtest** for controller-runtime testing (in-memory Kubernetes API)
- Tests dynamically download CRDs:
  - RayCluster: `github.com/ray-project/kuberay`
  - Route: `github.com/openshift/api`

### Test Naming
- Unit tests: `func TestAPIs(t *testing.T)` + Ginkgo specs
- Ginkgo specs: `Describe("X") { Context("Y") { It("Z") } }`
- Focus with: `-ginkgo.focus='pattern'`
- Skip with: `-ginkgo.skip='pattern'`

### Import Organization
- **Tool**: openshift-goimports
- **Style**: stdlib → external → local groups
- **Verify**: `make verify-imports`
- **Fix**: `make imports`

### Coverage
- Generated with: `go test -coverprofile cover.out`
- Reported as percentage (39.4% observed in validation)
- No enforced threshold

## Gaps & Caveats

### 1. Tests Require envtest Binaries
**Impact**: Cannot run unit/component tests in standard containers.

Unit and component tests use controller-runtime's `envtest` which requires Kubernetes control plane binaries (etcd, kube-apiserver, kubectl). The `setup-envtest` tool attempts to download these from Google Cloud Storage but fails with "401 Unauthorized" in standard environments.

**Solutions**:
- Use the CI container: `quay.io/opendatahub/pre-commit-go-toolchain:v0.2`
- Pre-install envtest binaries in your container
- Run tests in an environment with GCS access

### 2. E2E Tests Require Kubernetes Cluster
**Impact**: Cannot validate E2E tests without cluster infrastructure.

E2E tests (`make test-e2e`) require:
- Kubernetes cluster (kind/OpenShift)
- KubeRay operator installed
- Kueue installed
- AppWrapper CRDs

These are set up via `test/e2e/setup.sh` but require actual cluster access.

### 3. Pre-commit Requires Python
**Impact**: Full pre-commit validation requires Python tooling.

The `pre-commit run --all-files` command used in CI requires the Python `pre-commit` package. Individual checks (go-fmt, golangci-lint) can be run standalone, but the full CI check requires Python setup.

### 4. No Coverage Threshold
**Impact**: Tests generate coverage but don't enforce minimums.

Coverage is measured but not gated on. Tests can pass with declining coverage.

### 5. Import Verification Requires Special Tool
**Impact**: Cannot validate import organization without openshift-goimports.

The `make verify-imports` check requires `openshift-goimports` which must be installed separately. This is a specialized tool for import grouping.

## Alternative: CI Container Recipe

For full test validation including unit/component tests, use the CI container:

```bash
podman run -d --name test-context-codeflare-operator-poc \
  -v $(pwd):/app:Z \
  -w /app \
  -e KUBEBUILDER_ASSETS=/usr/local/kubebuilder/bin \
  -e XDG_CACHE_HOME=/cache \
  -e GOCACHE=/cache/go-build \
  -e GOMODCACHE=/cache/go-mod \
  quay.io/opendatahub/pre-commit-go-toolchain:v0.2 \
  sleep infinity
```

Then run:

```bash
# All pre-commit checks
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && pre-commit run --all-files"

# Unit tests
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && make test-unit"

# Component tests
podman exec test-context-codeflare-operator-poc bash -c \
  "cd /app && make test-component"
```

This container has envtest pre-configured and all CI tooling installed.

## Quick Reference

### Lint Commands
```bash
go fmt ./...                          # Format check/fix
go vet ./...                          # Go vet
golangci-lint run --timeout=10m      # Full lint suite
yamllint --strict -c .yamllint.yaml . # YAML validation
make verify-imports                   # Import organization check
make imports                          # Fix import organization
```

### Test Commands
```bash
make test-unit                        # Unit tests (requires envtest)
make test-component                   # Component tests (requires envtest)
make test-e2e                         # E2E tests (requires cluster)
go test -v ./pkg/controllers/         # Direct test run
go test -v {file} -ginkgo.focus='{pattern}'  # Single test
```

### Build Commands
```bash
go mod download                       # Install dependencies
make build                            # Build manager binary
make manifests                        # Generate RBAC/CRD manifests
make image-build                      # Build container image
```

### CI Simulation
```bash
# Run all gating checks locally (requires CI container)
pre-commit run --all-files
make test-unit
make test-component
make verify-imports
make manifests && git diff --exit-code
```

## Summary

This is a **medium-readiness** repository for automated patch validation:

**✅ Works Well**:
- Linting (go fmt, go vet, golangci-lint) validated successfully
- Build process straightforward
- Clear Makefile targets for all operations
- Comprehensive CI coverage

**⚠️ Limitations**:
- Tests require Kubernetes control plane binaries (envtest) not available in standard containers
- E2E tests need full cluster infrastructure
- Full CI simulation requires the specialized CI container image

**Recommendation**: For patch validation, run linting in a standard `golang:1.23` container (fully validated). For test validation, use the `quay.io/opendatahub/pre-commit-go-toolchain:v0.2` container which has all necessary tooling pre-installed.
