# Test Context: codeflare-operator

**Repository:** opendatahub-io/codeflare-operator
**Languages:** Go
**Build System:** make + go
**Agent Readiness:** medium - Linting fully validated and works, build works, tests require special infrastructure

## Overview

Go 1.23.0 Kubernetes operator using controller-runtime framework. Linting is fully functional and validated. Build works perfectly. Tests require envtest infrastructure with kubebuilder-tools (etcd, kube-apiserver) which complicates simple container-based validation.

## Container Recipe

This recipe provides a complete, copy-paste setup for validating patches in a container. Linting and build validation work perfectly. Tests require additional infrastructure noted below.

### 1. Start Container

```bash
podman run -d --name test-context-codeflare-operator \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.23 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-codeflare-operator bash -c \
  "apt-get update && apt-get install -y make git curl"
```

### 3. Install Go Dependencies

```bash
podman exec test-context-codeflare-operator bash -c \
  "cd /app && go mod download"
```

### 4. Install Linting Tools

```bash
# Install golangci-lint
podman exec test-context-codeflare-operator bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v1.61.0"

# Install yamllint (optional, for YAML validation)
podman exec test-context-codeflare-operator bash -c \
  "apt-get install -y python3-pip && pip3 install yamllint --break-system-packages"
```

### 5. Build the Project

```bash
podman exec test-context-codeflare-operator bash -c \
  "cd /app && go build -o bin/manager main.go"
```

**Expected result:** Creates bin/manager binary (~73M), exit code 0

### 6. Run Linting (VALIDATED ✓)

```bash
# Go formatting check
podman exec test-context-codeflare-operator bash -c \
  "cd /app && go fmt ./..."

# Go vet
podman exec test-context-codeflare-operator bash -c \
  "cd /app && go vet ./..."

# golangci-lint (runs errcheck, gosimple, govet, ineffassign, staticcheck, typecheck, unused)
podman exec test-context-codeflare-operator bash -c \
  "cd /app && golangci-lint run --config .golangci.yaml ./..."

# YAML linting
podman exec test-context-codeflare-operator bash -c \
  "cd /app && yamllint --config-file .yamllint.yaml ."
```

**Expected result:** All commands exit with code 0 and no output (clean pass)

### 7. Run Tests (REQUIRES INFRASTRUCTURE)

**Warning:** Tests require envtest with kubebuilder-tools (etcd, kube-apiserver, kubectl). These cannot be easily validated in a basic container.

```bash
# Unit tests (requires envtest infrastructure)
podman exec test-context-codeflare-operator bash -c \
  "cd /app && make test-unit"

# Component tests (requires envtest infrastructure)
podman exec test-context-codeflare-operator bash -c \
  "cd /app && make test-component"
```

**Expected result:** Tests will fail with "exec: etcd: executable file not found in $PATH" unless envtest is properly configured with kubebuilder-tools.

**Alternative for CI:** Use the official CI container image which has envtest pre-configured:
```bash
podman run -it --rm \
  -v $(pwd):/app:Z \
  -w /app \
  quay.io/opendatahub/pre-commit-go-toolchain:v0.2 \
  bash -c "make test-unit"
```

### 8. Run Single Test

```bash
# Run single test file
podman exec test-context-codeflare-operator bash -c \
  "cd /app && go test -v ./pkg/controllers/raycluster_webhook_test.go"

# Run specific test by name (Ginkgo focus)
podman exec test-context-codeflare-operator bash -c \
  "cd /app && go test -v ./pkg/controllers/ -ginkgo.focus 'Expected no errors on call to Default function'"
```

### 9. Cleanup

```bash
podman rm -f test-context-codeflare-operator
```

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install deps | `go mod download` | ✓ PASS | Dependencies downloaded successfully |
| Build | `go build -o bin/manager main.go` | ✓ PASS | Created 73M binary |
| Lint (fmt) | `go fmt ./...` | ✓ PASS | No formatting issues |
| Lint (vet) | `go vet ./...` | ✓ PASS | No vet issues |
| Lint (golangci) | `golangci-lint run` | ✓ PASS | All 7 linters passed |
| Lint (yaml) | `yamllint .` | ✓ PASS | No YAML issues |
| Unit tests | `make test-unit` | ✗ FAIL | Requires envtest with kubebuilder-tools (etcd, kube-apiserver) |
| Component tests | `make test-component` | Not tested | Requires same infrastructure as unit tests |
| E2E tests | `make test-e2e` | Not tested | Requires KinD cluster with GPU support |

## CI/CD

### Gating Checks (Required for PR Merge)

All of these run on pull requests and must pass:

1. **Pre-commit checks** (`.github/workflows/precommit.yml`)
   ```bash
   pre-commit run --all-files
   ```
   Runs: trailing-whitespace, check-merge-conflict, end-of-file-fixer, check-added-large-files, check-case-conflict, check-json, check-symlinks, detect-private-key, yamllint, go-fmt, golangci-lint, go-mod-tidy

2. **Unit tests** (`.github/workflows/unit_tests.yml`)
   ```bash
   make test-unit
   ```

3. **Component tests** (`.github/workflows/component_tests.yaml`)
   ```bash
   make test-component
   ```

4. **Verify imports** (`.github/workflows/verify_generated_files.yml`)
   ```bash
   make verify-imports
   ```
   Ensures imports are organized using openshift-goimports

5. **Verify manifests** (`.github/workflows/verify_generated_files.yml`)
   ```bash
   make manifests && git diff --exit-code
   ```
   Ensures generated RBAC, webhooks, and CRDs are up to date

### Advisory Checks

- **E2E tests** (`.github/workflows/e2e_tests.yaml`) - Runs on GPU hardware with KinD cluster

### CI Container Image

GitHub Actions workflows use `quay.io/opendatahub/pre-commit-go-toolchain:v0.2` which includes:
- Go 1.23
- pre-commit
- golangci-lint
- envtest with kubebuilder-tools

## Conventions

### Test File Patterns

- **Pattern:** `*_test.go`
- **Location:** `pkg/controllers/*_test.go` and `test/e2e/*_test.go`
- **Framework:** Ginkgo/Gomega (BDD style)
- **Suite files:** `suite_test.go` contains test suite setup

### Test Naming

Ginkgo BDD style with structured blocks:
```go
var _ = Describe("Feature", func() {
    Context("when condition", func() {
        It("should behave in expected way", func() {
            // test code
        })
    })
})
```

Standard Go test functions: `func TestAPIs(t *testing.T)` wrap Ginkgo suites

### Import Organization

Imports are organized by openshift-goimports into three groups:
1. Standard library
2. Third-party packages
3. Internal packages (github.com/project-codeflare/codeflare-operator/...)

Run `make imports` to organize or `make verify-imports` to check.

### Code Quality

- **go fmt**: Enforced by pre-commit and CI
- **go vet**: Enforced by make build and CI
- **golangci-lint**: 7 linters enabled (errcheck, gosimple, govet, ineffassign, staticcheck, typecheck, unused)
- **yamllint**: Enforced for all YAML files (custom config in .yamllint.yaml)

## Gaps & Caveats

### Test Infrastructure Requirements

1. **Unit/Component tests need envtest:**
   - Requires kubebuilder-tools (etcd, kube-apiserver, kubectl)
   - Can't be validated in basic container without downloading and configuring these tools
   - Official CI image has this pre-configured: `quay.io/opendatahub/pre-commit-go-toolchain:v0.2`

2. **E2E tests need full cluster:**
   - Requires KinD (Kubernetes in Docker)
   - Requires GPU hardware (tests run on `gpu-t4-4-core` runners)
   - Requires NVidia GPU operator
   - Requires deployment of CodeFlare stack (KubeRay, Kueue)
   - Not suitable for simple container validation

3. **External dependencies:**
   - kubebuilder-tools downloaded from GCS bucket (may require auth)
   - Tests may fail in isolated environments without GCS access

### What Works for Quick Validation

✓ **Linting** - All linters work perfectly in basic container
✓ **Build** - Building manager binary works
✓ **Formatting** - go fmt, go vet work
✗ **Tests** - Require special infrastructure

### Recommendations for Agents

**For patch validation:**
1. Use linting as primary validation (all 4 linters pass = good signal)
2. Ensure build succeeds
3. For comprehensive testing, use the official CI container image or actual CI pipeline
4. Don't rely on unit tests for quick validation without proper envtest setup

**Quick validation workflow:**
```bash
go mod download
go build -o bin/manager main.go
go fmt ./...
go vet ./...
golangci-lint run --config .golangci.yaml ./...
```

If all of the above pass, the patch is likely good. For full validation, rely on CI.

## Additional Notes

- **Container build:** Uses `podman` by default (`make image-build`)
- **Base image (production):** `registry.access.redhat.com/ubi9/go-toolset:1.23`
- **Generated files:** Manifests and RBAC generated via `make manifests` using controller-gen
- **Import organization required:** Changes to .go files trigger verify-imports check in CI
- **Coverage:** Generated in `cover.out` by unit tests (39.4% in validation run, but incomplete due to envtest issues)
- **Makefile targets:** Extensive Makefile with ~40 targets for various operations
- **Pre-commit hooks:** Defined in `.pre-commit-config.yaml` - run locally via `pre-commit run --all-files`

## Quick Reference

### Essential Commands

```bash
# Install dependencies
go mod download

# Build
make build
# OR: go build -o bin/manager main.go

# Lint (all commands should produce no output on success)
go fmt ./...
go vet ./...
golangci-lint run --config .golangci.yaml ./...
yamllint --config-file .yamllint.yaml .

# Test (requires envtest infrastructure)
make test-unit
make test-component

# Format imports
make imports

# Verify everything matches CI expectations
make verify-imports
make manifests && git diff --exit-code
```

### CI Gating Summary

For a PR to merge, all of these must pass:
1. pre-commit checks (linting, formatting)
2. unit tests
3. component tests
4. import organization verification
5. manifest generation verification

The pre-commit and linting checks can be validated in a basic container. Tests require special infrastructure.
