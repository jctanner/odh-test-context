# Test Context: spark-operator

**Organization:** opendatahub-io
**Repository:** spark-operator
**Analyzed:** 2026-03-22T20:20:56-04:00
**Agent Readiness:** HIGH — Lint and unit test commands validated successfully in container

## Overview

Kubernetes Operator for Apache Spark written in **Go 1.24.10**. Uses Makefile + Go modules for builds, golangci-lint for linting, and Ginkgo/Gomega + standard Go testing for tests. CI runs via GitHub Actions (primary gating) and Tekton (container builds).

**Agent readiness: HIGH** — All lint and test commands validated in golang:1.24.10 container. E2E tests require Kind cluster but unit tests and linting run without external dependencies.

---

## Container Recipe

This recipe validates lint and unit tests. An agent can use this to verify patches before submitting.

### 1. Start Container

```bash
podman run -d --name test-context-spark-operator \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24.10 \
  sleep infinity
```

**Note:** System dependencies (make, git) are pre-installed in golang:1.24.10.

### 2. Install Dependencies

```bash
podman exec test-context-spark-operator bash -c "cd /app && go mod download"
```

**Status:** ✅ Validated — completes successfully

### 3. Build

```bash
podman exec test-context-spark-operator bash -c "cd /app && make build-operator"
```

**Status:** ✅ Validated — binary built at `bin/spark-operator`

### 4. Run Linting

#### Go Format Check

```bash
podman exec test-context-spark-operator bash -c "cd /app && make go-fmt"
```

**Status:** ✅ Validated — 0 issues
**Output:** `Running go fmt... Go code is formatted.`

#### Go Vet Check

```bash
podman exec test-context-spark-operator bash -c "cd /app && make go-vet"
```

**Status:** ✅ Validated — 0 issues
**Output:** `Running go vet...`

#### Golangci-lint

```bash
podman exec test-context-spark-operator bash -c "cd /app && make go-lint"
```

**Status:** ✅ Validated — 0 issues
**Output:** `Running golangci-lint run... 0 issues.`

**Linters enabled:** copyloopvar, dupword, importas, predeclared, tagalign, unconvert, unused
**Auto-fix:** `make go-lint-fix`

### 5. Run Unit Tests

```bash
podman exec test-context-spark-operator bash -c "cd /app && make unit-test"
```

**Status:** ✅ Validated — all tests passed
**Output:** Tests run across multiple packages with coverage:
- `api/v1beta2`: 5.1% coverage
- `internal/controller/sparkapplication`: 43.9% coverage
- `internal/webhook`: 75.8% coverage
- Coverage report: `cover.html`

**Note:** E2E tests excluded via `grep -v /e2e`

### 6. Run Single Test

Run a specific test file:

```bash
podman exec test-context-spark-operator bash -c "cd /app && go test ./api/v1beta2/ -v"
```

Run a specific test function:

```bash
podman exec test-context-spark-operator bash -c "cd /app && go test ./api/v1beta2/ -run TestSetSparkApplicationDefaultsEmptyModeShouldDefaultToClusterMode -v"
```

### 7. Cleanup

```bash
podman rm -f test-context-spark-operator
```

---

## Validation Results

All commands executed successfully in golang:1.24.10 container:

| Step | Command | Exit Code | Result |
|------|---------|-----------|---------|
| Install deps | `go mod download` | 0 | ✅ Success |
| Build | `make build-operator` | 0 | ✅ Binary built |
| Lint: go fmt | `make go-fmt` | 0 | ✅ 0 issues |
| Lint: go vet | `make go-vet` | 0 | ✅ 0 issues |
| Lint: golangci-lint | `make go-lint` | 0 | ✅ 0 issues |
| Unit tests | `make unit-test` | 0 | ✅ All passed |

**Summary:** Install OK, build OK, lint OK (all 0 issues), tests OK (all unit tests passed)

---

## CI/CD

### GitHub Actions (Primary Gating)

**Workflow:** `.github/workflows/integration.yaml`
**Triggers:** `pull_request`, `push` to `main`, `master`, `release-*` branches

#### Gating Checks

1. **code-check** — Code quality and formatting
   ```bash
   go mod tidy
   make generate
   make verify-codegen
   make go-fmt
   make go-vet
   make go-lint
   ```

2. **build-api-docs** — API documentation generation
   ```bash
   make build-api-docs
   ```

3. **build-spark-operator** — Build and unit test
   ```bash
   make unit-test
   make build-operator
   ```

4. **build-helm-chart** — Helm chart validation
   ```bash
   make manifests
   make detect-crds-drift
   make helm-unittest
   ct lint --target-branch <branch>
   make helm-docs
   ```

5. **e2e-test** — End-to-end tests (matrix: k8s v1.24-v1.32)
   ```bash
   make kind-create-cluster KIND_K8S_VERSION=<version>
   make kind-load-image IMAGE_TAG=local
   make e2e-test
   ```

### Tekton Pipelines

**Files:** `.tekton/spark-operator-ci-pull-request.yaml`, `.tekton/spark-operator-ci-push.yaml`
**Purpose:** Container image builds for Quay/OpenShift
**Trigger:** Pull requests to main, pushes to main

### Advisory Checks

- **openshift-spark-pi-e2e.yaml** — OpenShift Spark Pi example validation (triggers on `examples/openshift/**` changes)
- **openshift-docling-e2e.yaml** — OpenShift Docling example validation (triggers on specific paths)

---

## Conventions

### Test Files

- **Pattern:** `*_test.go`
- **Unit tests:** Standard Go `Test*` functions
- **E2E tests:** Ginkgo `Describe`/`It` blocks in `test/e2e/`
- **Suite files:** `suite_test.go` sets up Ginkgo test suites

### Imports

Enforced by golangci-lint `importas`:

```go
import (
    corev1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    ctrl "sigs.k8s.io/controller-runtime"
)
```

### Test Infrastructure

- **Unit tests:** Use controller-runtime's `envtest` for mocking Kubernetes API
- **E2E tests:** Require Kind cluster with operator deployed via Helm
- **Coverage:** Generated with `go test -coverprofile cover.out`

---

## Gaps & Caveats

1. **E2E tests require infrastructure** — `make e2e-test` needs Kind cluster + Docker/Podman + operator image loaded. Not validated in basic container.

2. **Helm chart tests need tools** — `make helm-unittest` requires Helm plugin. `ct lint` requires chart-testing tool.

3. **Code generation checks** — `make generate` and `make verify-codegen` may modify files. CI checks that generated code is up-to-date.

4. **OpenShift e2e tests** — Path-specific triggers for OpenShift examples. Require Kind cluster configured to mimic OpenShift.

5. **No coverage threshold** — CI does not enforce a minimum coverage percentage.

6. **Matrix testing** — Full CI runs e2e tests on Kubernetes 1.24-1.32. Local validation uses Kind default version.

---

## Quick Reference

### Lint Commands

| Command | Purpose | Auto-fix |
|---------|---------|----------|
| `make go-fmt` | Check Go formatting | `go fmt ./...` |
| `make go-vet` | Run go vet | N/A |
| `make go-lint` | Run golangci-lint | `make go-lint-fix` |

### Test Commands

| Command | Purpose |
|---------|---------|
| `make unit-test` | Run all unit tests (excludes e2e) |
| `go test ./path/to/package/ -v` | Run tests in specific package |
| `go test ./path/ -run TestName -v` | Run specific test function |
| `make e2e-test` | Run e2e tests (requires Kind cluster) |

### Build Commands

| Command | Purpose |
|---------|---------|
| `go mod download` | Download dependencies |
| `make build-operator` | Build operator binary |
| `make docker-build` | Build container image |

### Other Useful Commands

| Command | Purpose |
|---------|---------|
| `make manifests` | Generate CRDs/RBAC/Webhooks |
| `make generate` | Generate DeepCopy methods |
| `make verify-codegen` | Verify generated code is up-to-date |
| `make update-crd` | Copy CRDs to Helm chart |

---

## Downstream Agent Usage

An agent validating a patch should:

1. **Start container** with golang:1.24.10
2. **Install deps** with `go mod download`
3. **Run linters** with `make go-fmt`, `make go-vet`, `make go-lint`
4. **Run unit tests** with `make unit-test`
5. **Build** with `make build-operator`
6. **Cleanup** container

**Expected outcome:** All commands exit 0. Lint should report 0 issues. Tests should pass.

**Skip e2e tests** unless you can provision a Kind cluster with the operator deployed. E2E tests are validated in CI but not required for basic patch validation.

**If CI fails on `make generate` or `make verify-codegen`:** Run those locally and commit the changes. These ensure generated code (CRDs, deepcopy methods) is current.
