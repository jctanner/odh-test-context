# Test Context: gateway-api-inference-extension

**Organization:** opendatahub-io
**Repository:** gateway-api-inference-extension
**Analyzed:** 2026-03-22

## Overview

Go 1.24.0 Kubernetes controller project using kubebuilder/controller-runtime framework. Implements Gateway API extensions for AI inference workload optimization. Build system: Makefile + Docker/Podman multi-stage builds.

**Agent Readiness: HIGH** - Lint and unit tests validated successfully in a standard container. Deps install cleanly, all linters pass, 53 test packages pass with race detection in ~60s.

## Container Recipe

This is the complete, validated recipe to run lint and tests in isolation. An agent should be able to execute these steps verbatim.

### 1. Start Container

```bash
# Use the exact Go version from go.mod
podman run -d \
  --name test-context-gateway-api-inference-extension \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24 \
  sleep infinity
```

**Note:** The golang:1.24 image already includes make, git, and gcc. If using a minimal base image, install these first:

```bash
podman exec test-context-gateway-api-inference-extension bash -c \
  "apt-get update && apt-get install -y make git gcc"
```

### 2. Install Dependencies

```bash
podman exec test-context-gateway-api-inference-extension bash -c \
  "cd /app && go mod download"
```

**Validated:** ✅ Exit code 0, completes in ~5 seconds

### 3. Run Linters

#### Standard Linter (golangci-lint)

```bash
podman exec test-context-gateway-api-inference-extension bash -c \
  "cd /app && make lint"
```

**Validated:** ✅ Exit code 0, 0 issues
**Notes:** Auto-installs golangci-lint v2.3.0 to bin/ on first run. Configured in `.golangci.yml` with 28 enabled linters including copyloopvar, errcheck, ginkgolinter, govet, staticcheck, etc.

#### API Linter (Kubernetes API conventions)

```bash
podman exec test-context-gateway-api-inference-extension bash -c \
  "cd /app && make api-lint"
```

**Validated:** ✅ Exit code 0, 0 issues
**Notes:** This is the **gating CI check** that runs on all PRs. Uses custom golangci-kube-api-linter plugin built from golangci-lint. Configured in `.golangci-kal.yml`.

#### Go Formatting Check

```bash
podman exec test-context-gateway-api-inference-extension bash -c \
  "cd /app && go fmt ./..."
```

**Validated:** ✅ Exit code 0, no formatting issues
**Auto-fix:** Same command formats files in-place

#### Go Vet (Static Analysis)

```bash
podman exec test-context-gateway-api-inference-extension bash -c \
  "cd /app && go vet ./..."
```

**Validated:** ✅ Exit code 0, no issues

### 4. Run Tests

#### All Unit Tests

```bash
podman exec test-context-gateway-api-inference-extension bash -c \
  "cd /app && CGO_ENABLED=1 go test ./pkg/... -race -coverprofile cover.out"
```

**Validated:** ✅ All 53 test packages passed
**Runtime:** ~60 seconds
**Coverage:** 10-100% across packages (40-80% typical)
**Notes:** Uses race detector (requires CGO_ENABLED=1). Tests pkg/bbr/*, pkg/epp/*, and all subdirectories.

#### Single Test File

```bash
podman exec test-context-gateway-api-inference-extension bash -c \
  "cd /app && CGO_ENABLED=1 go test ./pkg/epp/util/env -race"
```

**Template:** Replace `./pkg/epp/util/env` with any test package path

#### Single Test Function

```bash
podman exec test-context-gateway-api-inference-extension bash -c \
  "cd /app && CGO_ENABLED=1 go test ./pkg/epp/util/env -race -run TestGetEnvFloat"
```

**Template:** Replace `TestGetEnvFloat` with any test function name (must start with `Test`)

#### View Coverage Report

```bash
podman exec test-context-gateway-api-inference-extension bash -c \
  "cd /app && go tool cover -func=cover.out | tail -20"
```

### 5. Cleanup

```bash
podman rm -f test-context-gateway-api-inference-extension
```

**Always run this** even if previous steps fail.

## Validation Results

All commands were validated on 2026-03-22 in a fresh container:

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Install | `go mod download` | 0 | ✅ Pass | ~5s, no errors |
| Lint | `make lint` | 0 | ✅ Pass | 0 issues, auto-installs golangci-lint |
| API Lint | `make api-lint` | 0 | ✅ Pass | 0 issues, **gating CI check** |
| Format | `go fmt ./...` | 0 | ✅ Pass | No formatting issues |
| Vet | `go vet ./...` | 0 | ✅ Pass | No static analysis issues |
| Unit Tests | `go test ./pkg/... -race` | 0 | ✅ Pass | 53 packages, ~60s runtime |

**Summary:** install OK, lint OK (0 issues), api-lint OK (0 issues), fmt OK, vet OK, tests OK (53 packages passed)

## CI/CD

### Gating Checks

The following check **must pass** before a PR can merge:

- **kube-api-lint** (`.github/workflows/kal.yml`)
  - Trigger: pull_request (opened, edited, synchronize, reopened)
  - Command: `make api-lint`
  - Uses: golangci-kube-api-linter with `.golangci-kal.yml` config
  - Validates: Kubernetes API conventions and best practices

### Advisory Checks

- **non-main-gatekeeper** (`.github/workflows/non-main-gatekeeper.yml`)
  - Trigger: pull_request on non-main branches
  - Action: Adds `do-not-merge/hold` and `do-not-merge/cherry-pick-not-approved` labels
  - Purpose: Prevent accidental merges to non-main branches

### Other CI

- **cloudbuild.yaml**: Google Cloud Build for image building/pushing (releases, not gating)

### Missing CI Workflows

No unit test or integration test CI workflows are visible in `.github/workflows/`. The project may use:
- **Prow** (common for kubernetes-sigs projects)
- External CI system
- Local test enforcement via reviews

## Conventions

### Test Files

- Pattern: `**/*_test.go`
- Naming: `Test*` functions (standard Go) or Ginkgo `Describe`/`It` blocks
- Location:
  - Unit tests: `pkg/**/*_test.go`
  - Integration tests: `test/integration/**/*_test.go`
  - E2E tests: `test/e2e/**/*_test.go`
  - CEL validation: `test/cel/**/*_test.go`

### Import Organization

Enforced by `gci` formatter (run `make fmt-imports`):

```go
import (
    // Standard library
    "context"
    "fmt"

    // Third-party
    "github.com/onsi/ginkgo/v2"
    "k8s.io/client-go/kubernetes"

    // Project imports
    "sigs.k8s.io/gateway-api-inference-extension/pkg/epp"
)
```

### Code Generation

This project uses extensive code generation:

- **CRDs:** `controller-gen` generates Kubernetes CustomResourceDefinitions
- **Clients:** `k8s.io/code-generator` generates typed clients, listers, informers
- **DeepCopy:** Auto-generated `zz_generated.deepcopy.go` files

**Regenerate:** `make generate` (not validated in container, requires controller-gen, code-generator)

## Gaps & Caveats

### Cannot Validate in Simple Container

1. **Integration Tests** (`make test-integration`)
   - Requires: `envtest` with Kubernetes 1.31.0 binaries
   - Tests: `test/integration/epp/...`
   - Would need: envtest setup-envtest binary and downloaded assets

2. **E2E Tests** (`make test-e2e`)
   - Requires: Full Kubernetes cluster (kind recommended)
   - Environment variables: `MANIFEST_PATH`, `E2E_IMAGE`, `USE_KIND`
   - Tests: `test/e2e/epp/...`
   - Would need: kind cluster, container image, model server deployment

3. **Full Test Suite** (`make test`)
   - Runs: generate, fmt, vet, envtest, image-build, verify-crds, verify-helm-charts, then tests
   - Requires: Docker/Podman buildx for image building
   - Would need: Full build toolchain

4. **Code Generation** (`make generate`)
   - Requires: controller-gen, code-generator, specific versions
   - Would need: GOBIN setup and version-specific tools

### Infrastructure Dependencies

- **Container registry:** For image-build targets
- **Kubernetes cluster:** For integration/e2e tests
- **Model server:** For e2e inference tests (vLLM or compatible)

### Coverage Threshold

No explicit coverage threshold is configured. Coverage is measured and reported but not enforced.

### CI Completeness

Only API linting is visibly gated in GitHub Actions. Unit/integration tests may run in external CI (Prow) or rely on local enforcement.

## Additional Make Targets

For reference, other useful Makefile targets (not all validated):

- `make fmt-imports`: Run gci import formatter
- `make fmt-verify`: Check formatting without modifying files
- `make verify`: Run all verification checks (vet, fmt-verify, generate, lint, api-lint, verify-all)
- `make verify-crds`: Validate CRD manifests with kubectl-validate
- `make verify-helm-charts`: Validate Helm charts
- `make image-build`: Build container image with Docker buildx
- `make image-load`: Build and load image to local Docker registry
- `make image-kind`: Build and load image to kind cluster

## Test Framework Details

### Ginkgo/Gomega

The project uses Ginkgo v2.25.3 and Gomega v1.38.2 for BDD-style tests. Example structure:

```go
var _ = Describe("ComponentName", func() {
    It("should do something", func() {
        Expect(result).To(Equal(expected))
    })
})
```

### Race Detector

All unit tests run with `-race` flag to detect data races. This requires `CGO_ENABLED=1` and adds ~2-5x runtime overhead.

### Mocks

Mock implementations are in `pkg/*/mocks/` directories. The project uses both hand-written mocks and generated mocks (mockery or similar).

## Quick Reference

**Clone & Validate:**

```bash
git clone https://github.com/opendatahub-io/gateway-api-inference-extension.git
cd gateway-api-inference-extension
podman run -d --name test -v $(pwd):/app:Z -w /app golang:1.24 sleep infinity
podman exec test bash -c "cd /app && go mod download && make lint && make api-lint && CGO_ENABLED=1 go test ./pkg/... -race"
podman rm -f test
```

**Expected Output:**
- Lint: `0 issues.`
- API Lint: `0 issues.`
- Tests: `ok  	sigs.k8s.io/gateway-api-inference-extension/pkg/...` (53 packages)

**Total Runtime:** ~90 seconds (download: ~5s, lint: ~20s, api-lint: ~5s, tests: ~60s)

---

**Agent Readiness: HIGH** - Copy-paste ready for automated patch validation.
