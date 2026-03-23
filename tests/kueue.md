# Test Context for opendatahub-io/kueue

**Generated:** 2026-03-22T22:35:00Z

## Overview

**Repository:** opendatahub-io/kueue (ODH fork of kubernetes-sigs/kueue)
**Language:** Go 1.24.0
**Build System:** Makefile + go toolchain
**Agent Readiness:** **HIGH** - Lint and test commands validated successfully in container

This is an OpenDataHub fork of the Kueue project (a Kubernetes job queueing system). All basic validation commands (lint, test, build) work cleanly in a standard golang:1.24.0 container. Integration and e2e tests require additional infrastructure but unit tests and linting provide good patch validation coverage.

---

## Container Recipe

This recipe provides a complete, copy-paste workflow for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-kueue \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24.0 \
  sleep infinity
```

Alternative with docker:
```bash
docker run -d --name test-context-kueue \
  -v $(pwd):/app \
  -w /app \
  golang:1.24.0 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-kueue bash -c "apt-get update && apt-get install -y make git curl"
```

### 3. Install Project Dependencies

```bash
podman exec test-context-kueue bash -c "cd /app && go mod download"
```

**Expected:** Silent success (downloads all Go modules defined in go.mod)

### 4. Build Project

```bash
podman exec test-context-kueue bash -c "cd /app && go build -o /tmp/kueue ./cmd/kueue/main.go"
```

**Expected:** Produces ~108MB binary at /tmp/kueue
**Validation status:** ✅ Passed (exit code 0, binary created)

Alternative via Makefile:
```bash
podman exec test-context-kueue bash -c "cd /app && make build"
```

### 5. Run Linters

#### Install golangci-lint

```bash
podman exec test-context-kueue bash -c "cd /app && make golangci-lint"
```

#### Run golangci-lint

```bash
podman exec test-context-kueue bash -c "cd /app && ./bin/golangci-lint run --timeout 15m0s"
```

**Expected:** May find legitimate lint violations in code
**Validation status:** ✅ Works correctly (found 1 unused function)

**Note:** Exit code 1 means lint violations found, not a broken linter. To check specific directories:

```bash
podman exec test-context-kueue bash -c "cd /app && ./bin/golangci-lint run --timeout 5m0s ./pkg/..."
```

#### Auto-fix with golangci-lint

```bash
podman exec test-context-kueue bash -c "cd /app && ./bin/golangci-lint run --fix --timeout 15m0s"
```

#### Run go fmt

```bash
podman exec test-context-kueue bash -c "cd /app && go fmt ./..."
```

**Expected:** Silent if no formatting issues
**Validation status:** ✅ Passed (no formatting issues)

#### Run go vet

```bash
podman exec test-context-kueue bash -c "cd /app && go vet ./..."
```

**Expected:** Silent if no issues
**Validation status:** ✅ Passed (no issues found)

### 6. Run Unit Tests

#### All unit tests

```bash
podman exec test-context-kueue bash -c "cd /app && go test ./pkg/..."
```

**Expected:** All tests pass (87 packages)
**Validation status:** ✅ Passed (all tests passed in ~20 seconds)

**Note:** Add `-race` flag for race detection (default in Makefile):

```bash
podman exec test-context-kueue bash -c "cd /app && go test -race ./pkg/..."
```

#### Quick unit tests (no race detection)

```bash
podman exec test-context-kueue bash -c "cd /app && go test -short ./pkg/..."
```

#### Run tests for single package

```bash
podman exec test-context-kueue bash -c "cd /app && go test ./pkg/cache"
```

#### Run specific test

```bash
podman exec test-context-kueue bash -c "cd /app && go test -run TestSpecificFunction ./pkg/cache"
```

#### With coverage

```bash
podman exec test-context-kueue bash -c "cd /app && go test ./pkg/... -coverpkg=./... -coverprofile /tmp/cover.out"
```

### 7. Run Integration Tests (requires additional setup)

**⚠️ Not validated in basic container - requires envtest and CRDs**

```bash
podman exec test-context-kueue bash -c "cd /app && make test-integration"
```

**Setup required:**
- envtest (simulated K8s API server)
- External CRDs (jobset, kubeflow, ray-operator, appwrapper, etc.)
- Environment variables: KUBEBUILDER_ASSETS, ENVTEST_K8S_VERSION

### 8. Run E2E Tests (requires Kind cluster)

**⚠️ Not validated - requires Kind cluster and infrastructure**

```bash
podman exec test-context-kueue bash -c "cd /app && make test-e2e"
```

**Setup required:**
- Kind cluster
- Container image built and loaded
- External operator CRDs

### 9. Cleanup

```bash
podman rm -f test-context-kueue
```

---

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install deps | `go mod download` | ✅ Pass | All dependencies downloaded |
| Build | `go build ./cmd/kueue/main.go` | ✅ Pass | 108MB binary produced |
| Lint (golangci-lint) | `./bin/golangci-lint run ./pkg/...` | ✅ Pass | Found 1 unused function (legitimate) |
| Lint (fmt) | `go fmt ./pkg/...` | ✅ Pass | No formatting issues |
| Lint (vet) | `go vet ./pkg/...` | ✅ Pass | No issues found |
| Test (unit) | `go test -short ./pkg/...` | ✅ Pass | 87 packages, all passed |

**Summary:** All basic validation commands work in standard golang:1.24.0 container.

---

## CI/CD

### GitHub Actions Workflows

This ODH fork has minimal CI workflows focused on image building:

1. **Build and Publish image** (`.github/workflows/odh-build-and-publish-kueue-image.yaml`)
   - Trigger: Manual workflow_dispatch
   - Command: `make image-push`
   - Registry: quay.io/opendatahub
   - Platform: linux/amd64
   - Status: Not gating (manual trigger only)

2. **ODH Release** (`.github/workflows/odh-release.yml`)
   - Trigger: Manual
   - Status: Advisory

3. **Krew Release** (`.github/workflows/krew-release.yml`)
   - For kubectl plugin distribution
   - Status: Advisory

**Important:** The upstream kubernetes-sigs/kueue project has extensive CI (unit tests, integration tests, e2e tests across multiple Kubernetes versions), but these workflows are not present in this ODH fork. The fork carries ODH-specific patches (CARRY commits) on top of upstream releases.

### Gating Checks

None configured in this fork. For upstream kueue, the following would typically gate:
- Unit tests
- Integration tests
- E2E tests (K8s 1.30, 1.31, 1.32)
- Linting via golangci-lint
- Code generation verification

---

## Conventions

### Test File Naming

- Unit tests: `*_test.go` files alongside source code
- Integration tests: `test/integration/{component}/...`
- E2E tests: `test/e2e/{suite}/...`
- Performance tests: `test/performance/...`

### Test Function Naming

- Go standard: `func TestXxx(t *testing.T)`
- Ginkgo BDD: `Describe("Component", func() { It("should...", func() {...}) })`

### Import Organization

Enforced by `gci` linter:

```go
import (
    // Standard library
    "context"
    "fmt"

    // Third-party
    "github.com/onsi/ginkgo/v2"
    "k8s.io/client-go/rest"

    // This project (sigs.k8s.io/kueue prefix)
    "sigs.k8s.io/kueue/pkg/cache"
    "sigs.k8s.io/kueue/pkg/controller/core"
)
```

### Code Headers

All Go files must have Apache 2.0 license header (enforced by goheader linter):

```go
/*
Copyright The Kubernetes Authors.

Licensed under the Apache License, Version 2.0 (the "License");
...
*/
```

### Test Organization

- **singlecluster tests:** Core functionality on single cluster
- **multikueue tests:** Multi-cluster job dispatching
- **e2e tests:** End-to-end scenarios with real Kubernetes
- **performance tests:** Scalability and performance benchmarks

---

## Gaps & Caveats

### 1. No Automated Testing CI in ODH Fork

The ODH fork does not include CI workflows for automated testing. Upstream kueue has extensive CI via Prow and GitHub Actions, but these are not maintained in the fork. This means:

- **Impact:** Patches are not automatically validated before merge
- **Workaround:** Run tests locally or in container before creating PR
- **Severity:** Medium (tests work fine, just not automated)

### 2. Integration Tests Require Setup

Integration tests use envtest (simulated K8s API server) and require:

- `make envtest` to install setup-envtest
- `make dep-crds` to copy external operator CRDs
- Environment variable `KUBEBUILDER_ASSETS`

**Commands:**
```bash
make envtest dep-crds
make test-integration
```

**Status:** Not validated in basic container (requires additional tools)

### 3. E2E Tests Require Infrastructure

E2E tests require:

- Kind cluster (via `make kind`)
- Container image built and loaded into Kind
- External CRDs deployed (JobSet, Kubeflow training operators, Ray operator, AppWrapper, etc.)
- Multiple Kubernetes versions tested (1.30, 1.31, 1.32)

**Commands:**
```bash
make kind-image-build  # Build and load into Kind
make test-e2e          # Run e2e tests
```

**Status:** Not validated (requires cluster infrastructure)

### 4. Code Generation Not Validated

The project uses code generation for:

- CRD manifests (controller-gen)
- DeepCopy methods (controller-gen)
- Client-go libraries (code-generator)
- API reference docs

**Commands:**
```bash
make generate   # Generate code
make manifests  # Generate CRDs/RBAC
make verify     # Verify all generated code is up-to-date
```

**Status:** Not validated in container

### 5. Shell Script Linting Not Validated

Project includes shellcheck configuration (`.shellcheckrc`) and scripts in `hack/`:

```bash
make shell-lint
```

**Status:** Not validated (shellcheck not installed in validation container)

### 6. ODH-Specific Patches

This fork carries ODH-specific patches (visible in git log as "CARRY:" commits):

- External AppWrapper framework
- VAP enforcement on PyTorchJobs
- Image configuration for RHOAI
- CVE fixes

These patches must be maintained across upstream rebases.

---

## Quick Reference

### Essential Commands

```bash
# Install dependencies
go mod download

# Build
make build                          # Build manager binary
go build ./cmd/kueue/main.go       # Direct build

# Lint
make ci-lint                        # Full lint (15m timeout)
make lint-fix                       # Auto-fix lint issues
go fmt ./...                        # Format code
go vet ./...                        # Run go vet

# Test
go test ./pkg/...                   # All unit tests
go test -short ./pkg/...            # Quick unit tests
make test                           # Unit tests with coverage
make test-integration               # Integration tests (requires setup)
make test-e2e                       # E2E tests (requires Kind)

# Code generation
make generate                       # Generate code
make manifests                      # Generate CRDs
make verify                         # Verify everything is up-to-date
```

### Test Filtering

```bash
# Run tests in specific package
go test ./pkg/cache

# Run specific test function
go test -run TestCacheSnapshot ./pkg/cache

# Run tests matching pattern
go test -run "TestCache.*" ./pkg/...

# Skip slow tests
go test -short ./pkg/...

# With race detection
go test -race ./pkg/...

# With coverage
go test -coverprofile=coverage.out ./pkg/...
```

### Ginkgo-Specific (for integration/e2e)

```bash
# Install ginkgo CLI
make ginkgo

# Run with Ginkgo
./bin/ginkgo -r test/integration/singlecluster/

# Run specific suite
./bin/ginkgo test/integration/singlecluster/controller/core/

# Label filtering
./bin/ginkgo --label-filter="!slow && !redundant" test/integration/...

# Parallel execution
./bin/ginkgo -procs=4 test/integration/...
```

### Makefile Targets

```bash
make help                           # Show all targets
make all                            # generate + fmt + vet + build
make verify                         # Full verification (lint, fmt, toc, etc.)
make test                           # Unit tests with coverage
make test-integration               # Integration tests
make test-integration-baseline      # Fast integration tests
make test-integration-extended      # Slow integration tests
make test-e2e                       # E2E tests
make test-multikueue-e2e            # MultiKueue e2e tests
make build                          # Build manager binary
make image-build                    # Build container image
make kueuectl                       # Build kubectl plugin
```

---

## Additional Resources

- **Upstream Project:** https://github.com/kubernetes-sigs/kueue
- **Documentation:** https://kueue.sigs.k8s.io/
- **ODH Fork:** https://github.com/opendatahub-io/kueue
- **Go Version:** 1.24.0 (specified in go.mod)
- **Kubernetes Versions Supported:** 1.25+
- **Test Framework:** Ginkgo/Gomega (BDD testing framework)
- **Code Generation:** controller-gen, code-generator

---

## Agent Readiness Assessment

**Rating: HIGH**

**Justification:**
- ✅ All basic commands (lint, test, build) validated in standard container
- ✅ Dependencies install cleanly with `go mod download`
- ✅ Unit tests pass (87 packages, 0 failures)
- ✅ Linting works correctly (golangci-lint, fmt, vet)
- ✅ Build succeeds (108MB binary)
- ✅ Clear command patterns for single file/test execution
- ⚠️ Integration/e2e tests require additional setup (envtest, Kind)
- ⚠️ No automated CI in this fork (upstream has extensive CI)

**Agent Capability:**
An agent can clone this repo, apply a patch, and get clear pass/fail signals from:
1. Linting (golangci-lint, fmt, vet)
2. Unit tests (go test ./pkg/...)
3. Build (make build)

Integration and e2e tests require infrastructure setup but unit tests provide good coverage for most patches.

**Confidence: HIGH** - All validation steps completed successfully in isolated container.
