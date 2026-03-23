# Test Context: data-science-pipelines-operator

**Repository:** opendatahub-io/data-science-pipelines-operator
**Analysis Date:** 2026-03-22
**Agent Readiness:** ⭐ **HIGH** - Lint and test commands validated successfully in container

## Overview

Go-based Kubernetes operator for Data Science Pipelines. Uses standard Go testing framework with build tags, golangci-lint for linting, and kubebuilder/envtest for controller testing. All gating CI checks (lint, unit tests, functional tests) can be validated locally in a standard container.

**Languages:** Go 1.25.7
**Build System:** Makefile + Go modules
**Test Framework:** Go testing with build tags (test_unit, test_functional, test_integration)

## Container Recipe

This is a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-dspo \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.22 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-dspo bash -c "apt-get update && apt-get install -y make git curl"
```

### 3. Download Go Dependencies

**Important:** This project requires Go 1.25.7. Use `GOTOOLCHAIN=auto` to automatically download it.

```bash
podman exec test-context-dspo bash -c "cd /app && GOTOOLCHAIN=auto go mod download"
```

### 4. Install Linter

```bash
podman exec test-context-dspo bash -c "cd /app && GOTOOLCHAIN=auto go install github.com/golangci/golangci-lint/cmd/golangci-lint@v1.64.8"
```

### 5. Run Linter (Gating Check)

```bash
podman exec test-context-dspo bash -c "cd /app && GOTOOLCHAIN=auto /go/bin/golangci-lint run --timeout=5m"
```

**Expected:** No output (clean pass)
**Status:** ✅ Validated - passes with no errors

### 6. Build Project

```bash
podman exec test-context-dspo bash -c "cd /app && GOTOOLCHAIN=auto make build"
```

**Expected:** Binary created at `bin/manager` (~56MB)
**Status:** ✅ Validated - builds successfully

### 7. Run Unit Tests (Gating Check)

```bash
podman exec test-context-dspo bash -c "cd /app && GOTOOLCHAIN=auto make unittest"
```

**Expected:** All tests pass, ~54.9% coverage
**Status:** ✅ Validated - all tests pass
**Note:** You may see `go: no such tool "covdata"` errors - these are non-fatal. Tests pass successfully.

Alternative without coverage profiling (cleaner output):
```bash
podman exec test-context-dspo bash -c "cd /app && GOTOOLCHAIN=auto go test ./controllers/... --tags=test_unit -v"
```

### 8. Run Functional Tests (Gating Check)

```bash
podman exec test-context-dspo bash -c "cd /app && \
  export SSL_CERT_FILE=/app/controllers/testdata/tls/ca-bundle.crt && \
  export DSPO_NAMESPACE=opendatahub && \
  GOTOOLCHAIN=auto make functest"
```

**Expected:** All tests pass, ~59.2% coverage
**Status:** ✅ Validated - all tests pass
**Note:** Same `covdata` error may appear but is non-fatal.

### 9. Run a Single Test

To run a specific test function:

```bash
podman exec test-context-dspo bash -c "cd /app && \
  GOTOOLCHAIN=auto go test ./controllers -run TestDeployAPIServer --tags=test_unit -v"
```

To run a single test file:

```bash
podman exec test-context-dspo bash -c "cd /app && \
  GOTOOLCHAIN=auto go test ./controllers/apiserver_test.go --tags=test_unit -v"
```

### 10. Cleanup

```bash
podman rm -f test-context-dspo
```

## Validation Results

All commands were executed in a `golang:1.22` container with `GOTOOLCHAIN=auto` to automatically download Go 1.25.7.

| Step | Command | Exit Code | Result |
|------|---------|-----------|--------|
| **Dependencies** | `go mod download` | 0 | ✅ Success |
| **Build** | `make build` | 0 | ✅ Success - 56MB binary |
| **Lint** | `golangci-lint run` | 0 | ✅ Success - no errors |
| **Unit Tests** | `make unittest` | 0 | ✅ Success - 54.9% coverage |
| **Functional Tests** | `make functest` | 0 | ✅ Success - 59.2% coverage |

### Lint Output
```
(no output - clean pass)
```

### Unit Test Summary
```
PASS
coverage: 54.9% of statements
ok  	github.com/opendatahub-io/data-science-pipelines-operator/controllers
```

### Functional Test Summary
```
ok  	github.com/opendatahub-io/data-science-pipelines-operator/controllers	16.642s	coverage: 59.2% of statements
```

## CI/CD

### Gating Checks (Required for PR Merge)

These run on every pull request and must pass:

1. **Pre-commit Lint** (`.github/workflows/precommit.yml`)
   - Trigger: `pull_request`
   - Command: `pre-commit run --all-files`
   - Includes: golangci-lint, go fmt, yamllint, go-build, go-mod-tidy
   - Go version: Set from `go.mod`
   - Lint command: `golangci-lint run --timeout=5m`

2. **Unit Tests** (`.github/workflows/unittests.yml`)
   - Trigger: `pull_request`
   - Command: `make unittest`
   - Go version: Set from `go.mod`

3. **Functional Tests** (`.github/workflows/functests.yml`)
   - Trigger: `pull_request`
   - Command: `make functest`
   - Environment: `SSL_CERT_FILE=$GITHUB_WORKSPACE/controllers/testdata/tls/ca-bundle.crt`

### Advisory Checks (Non-blocking)

- **Build PR Image** - Builds container image for testing
- **Integration Tests** - Requires Kind cluster with minio/mariadb/operator deployed
  - Only runs on labeled PRs or manually
  - Command: `make integrationtest`
  - Requires Kubernetes cluster infrastructure

## Linting Configuration

### golangci-lint

**Config:** `.golangci.yaml`
**Version:** v1.64.8 (from CI workflow)
**Timeout:** 5 minutes
**Enabled Linters:**
- errcheck
- gosimple
- govet
- ineffassign
- staticcheck
- typecheck
- unused
- revive

**Run Command:**
```bash
golangci-lint run --timeout=5m
```

**Exclusions:**
- `controllers/dspipeline_params.go` - SA1019 (deprecated warnings)
- `revive` dot-imports rule disabled

### Pre-commit Hooks

**Config:** `.pre-commit-config.yaml`

Additional checks:
- `go fmt` - Code formatting
- `go build` - Build verification
- `go-mod-tidy` - Module cleanup
- `yamllint --strict` - YAML file linting
- Standard pre-commit hooks (trailing whitespace, merge conflicts, etc.)

## Testing Configuration

### Test Structure

Tests are organized by build tags:

- **Unit tests** (`--tags=test_unit`): Located in `controllers/*_test.go`
  - Test individual functions/components in isolation
  - Use envtest for Kubernetes API mocking
  - No external dependencies required
  - Run via: `make unittest`

- **Functional tests** (`--tags=test_functional`): Located in `controllers/*_test.go`
  - Test controller behavior with simulated Kubernetes environment
  - Require SSL cert files from `controllers/testdata/tls/`
  - Run via: `make functest`

- **Integration tests** (`--tags=test_integration`): Located in `tests/*_test.go`
  - Test full operator deployment on real Kubernetes cluster
  - Require: MariaDB, MinIO, DSP operator deployed
  - Run via: `make integrationtest`
  - **Cannot be validated in standard container**

### Running Tests

**All unit tests:**
```bash
GOTOOLCHAIN=auto make unittest
```

**All functional tests:**
```bash
SSL_CERT_FILE=controllers/testdata/tls/ca-bundle.crt \
DSPO_NAMESPACE=opendatahub \
GOTOOLCHAIN=auto make functest
```

**Specific test:**
```bash
GOTOOLCHAIN=auto go test ./controllers -run TestDeployAPIServer --tags=test_unit -v
```

**With coverage:**
```bash
GOTOOLCHAIN=auto go test ./controllers/... --tags=test_unit -coverprofile=cover.out
```

### Test Dependencies

- `envtest` - Kubebuilder testing framework (auto-installed by Makefile)
- `controller-gen` - Code generation tool (auto-installed by Makefile)
- Test fixtures in `controllers/testdata/`

## Build Configuration

### Standard Build

```bash
GOTOOLCHAIN=auto make build
```

This runs:
1. `make manifests` - Generate CRDs and RBAC
2. `make generate` - Generate DeepCopy methods
3. `go fmt ./...` - Format code
4. `go vet ./...` - Vet code
5. `go build -o bin/manager main.go` - Build binary

### Container Build

```bash
podman build -t quay.io/opendatahub/data-science-pipelines-operator:main .
```

**Base image:** `registry.access.redhat.com/ubi9/go-toolset:1.25`
**Build args:**
- `FIPS_ENABLED=1` (default) - FIPS-compliant build
- `FIPS_ENABLED=0` - Non-FIPS for local development (e.g., Apple Silicon)
- `TARGETARCH=amd64` (default)

## Conventions

### File Naming
- Test files: `*_test.go`
- Build tags at top of test files: `//go:build test_unit`

### Test Naming
- Test functions: `TestFunctionName(t *testing.T)`
- Subtests: `t.Run("subtest name", func(t *testing.T) {...})`

### Import Organization
Groups in order:
1. Standard library
2. External packages
3. Internal packages (from this repo)

### Code Generation
- API types in `api/v1/`
- Controllers in `controllers/`
- Generated code marked with `// +kubebuilder:` annotations
- Run `make generate` and `make manifests` after API changes

## Gaps & Caveats

### Known Issues

1. **Coverage Tool Error**
   - `go: no such tool "covdata"` appears during coverage profiling
   - This is a known issue with Go 1.25.x coverage tooling
   - **Does not affect test execution** - tests pass successfully
   - Can be avoided by running tests without `-coverprofile` flag

2. **Integration Tests**
   - Require full Kubernetes cluster with dependencies deployed
   - Cannot be validated in standard container
   - Need: MariaDB, MinIO, DSP operator, Argo Workflows
   - Tested in CI via Kind cluster setup

3. **YAML Linting**
   - `yamllint` requires Python pre-commit setup
   - Not validated in container recipe above
   - Runs in CI via pre-commit workflow

### Missing

- No coverage threshold defined in CI or configuration
- No mutation testing
- Integration tests only run on labeled PRs (not every PR)

## Quick Reference

### Common Commands

```bash
# Dependencies
GOTOOLCHAIN=auto go mod download
GOTOOLCHAIN=auto go mod tidy

# Code generation
make manifests  # Generate CRDs
make generate   # Generate DeepCopy

# Quality checks
GOTOOLCHAIN=auto golangci-lint run
go fmt ./...
go vet ./...

# Testing
make unittest        # Unit tests only
make functest        # Functional tests only
make test            # All tests (requires envtest)

# Build
make build           # Build binary
make podman-build    # Build container

# Deploy (requires cluster)
make deploy IMG=<image>
make undeploy
```

### Environment Variables

- `GOTOOLCHAIN=auto` - Required to use Go 1.25.7
- `SSL_CERT_FILE` - Path to CA bundle for functional tests
- `DSPO_NAMESPACE` - Namespace for test resources (default: opendatahub)
- `KUBEBUILDER_ASSETS` - Set automatically by envtest

---

**Agent Readiness Rating: HIGH**

This repository has excellent patch validation capabilities:
- ✅ Lint commands validated and working
- ✅ Unit tests validated and passing
- ✅ Functional tests validated and passing
- ✅ Build process validated
- ✅ All gating CI checks can be run locally
- ⚠️ Integration tests require cluster infrastructure (expected for K8s operators)

An AI agent can clone this repo, apply a patch, and get definitive pass/fail signals from lint and tests in a standard container environment.
