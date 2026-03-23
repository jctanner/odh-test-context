# Test Context: workload-variant-autoscaler

**Organization**: opendatahub-io
**Repository**: workload-variant-autoscaler
**Analyzed**: 2026-03-22T20:43:00Z
**Agent Readiness**: HIGH ✅

Kubernetes controller for workload variant autoscaling in LLM inference workloads. Written in Go 1.24.0 using controller-runtime. Lint and unit tests validated successfully in container.

---

## Overview

- **Languages**: Go 1.24.0
- **Build System**: Makefile + Go modules
- **Test Framework**: Ginkgo v2 + Gomega (BDD-style testing)
- **Linting**: golangci-lint v2.8.0 (default config), go fmt, go vet
- **CI/CD**: GitHub Actions (gating: lint + unit tests + smoke E2E on PRs)
- **Agent Readiness**: **HIGH** - Lint and unit tests run successfully in standard Go container

**Why HIGH**: Both lint and unit test commands validated successfully in a golang:1.24.0 container. Dependencies install cleanly, build completes, linter finds 0 issues, all unit tests pass. Agents can reliably validate patches using these commands. E2E tests require infrastructure but unit test coverage is comprehensive.

---

## Container Recipe

Complete step-by-step recipe for validating patches in a container. This section is self-contained - you can copy these commands directly.

### 1. Start Container

```bash
docker run -d --name test-wva \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24.0 \
  sleep infinity
```

Or with podman:
```bash
podman run -d --name test-wva \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24.0 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
docker exec test-wva bash -c "apt-get update && apt-get install -y make git"
```

**Expected**: make already installed, git upgrades successfully.

### 3. Install Project Dependencies

```bash
docker exec test-wva bash -c "cd /app && go mod download"
```

**Expected**: Silent success (exit 0, no output).

### 4. Build

```bash
docker exec test-wva bash -c "cd /app && make build"
```

**Expected Output**:
```
/app/bin/controller-gen rbac:roleName=manager-role crd webhook paths="./..." output:crd:artifacts:config=config/crd/bases
/app/bin/controller-gen object:headerFile="hack/boilerplate.go.txt" paths="./..."
go fmt ./...
go vet ./...
go build -o bin/manager cmd/main.go
```

**What it does**: Downloads controller-gen tool, generates CRD/RBAC manifests, formats code, vets code, compiles binary to `bin/manager`.

**Exit code**: 0

### 5. Lint

```bash
docker exec test-wva bash -c "cd /app && make lint"
```

**Expected Output**:
```
Downloading golangci-lint v2.8.0
golangci/golangci-lint info installed /app/bin/golangci-lint
/app/bin/golangci-lint run
0 issues.
```

**Exit code**: 0 if no issues, non-zero if linter finds problems.

**Fix command** (if lint fails):
```bash
docker exec test-wva bash -c "cd /app && make lint-fix"
```

### 6. Run Tests

```bash
docker exec test-wva bash -c "cd /app && make test"
```

**Expected Output** (truncated):
```
Setting up envtest binaries for Kubernetes version 1.34...
KUBEBUILDER_ASSETS="/app/bin/k8s/1.34.1-linux-amd64" PATH=/app/bin:... go test $(go list ./... | grep -v /e2e) -coverprofile cover.out
ok  	github.com/llm-d/llm-d-workload-variant-autoscaler/api/v1alpha1	0.017s	coverage: 39.4% of statements
ok  	github.com/llm-d/llm-d-workload-variant-autoscaler/internal/actuator	6.326s	coverage: 66.1% of statements
...
(33 test packages)
```

**What it does**: Downloads envtest binaries (Kubernetes API server for testing), runs all unit tests excluding e2e tests, generates coverage report.

**Exit code**: 0 if all tests pass, non-zero if any test fails.

**Duration**: ~1-2 minutes.

### 7. Run Single Test File

```bash
docker exec test-wva bash -c "cd /app && go test ./internal/actuator/actuator_test.go"
```

### 8. Run Single Test by Name

```bash
docker exec test-wva bash -c "cd /app && go test -run 'TestActuatorSuite' ./internal/actuator/..."
```

For Ginkgo tests, use `-ginkgo.focus`:
```bash
docker exec test-wva bash -c "cd /app && go test ./internal/actuator/... -ginkgo.focus='Actuator.*should scale'"
```

### 9. Cleanup

```bash
docker rm -f test-wva
```

Or with podman:
```bash
podman rm -f test-wva
```

---

## Validation Results

All commands validated in golang:1.24.0 container on 2026-03-22.

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| **System deps** | `apt-get install make git` | 0 | ✅ PASS | make already installed, git upgraded |
| **Go deps** | `go mod download` | 0 | ✅ PASS | Silent success, all modules downloaded |
| **Build** | `make build` | 0 | ✅ PASS | Generated CRDs, built bin/manager |
| **Lint** | `make lint` | 0 | ✅ PASS | golangci-lint found 0 issues |
| **Test** | `make test` | 0 | ✅ PASS | All 33 unit test packages passed |

**Summary**: install OK, dependencies OK, build OK, lint OK (0 issues), tests OK (all unit tests passed)

---

## CI/CD

### Gating Checks (Required for PR Merge)

These checks **must pass** before a PR can be merged:

#### 1. lint-and-test
- **Trigger**: All PRs to main/dev branches
- **Workflow**: `.github/workflows/ci-pr-checks.yaml`
- **Commands**:
  ```bash
  go mod download
  make build  # includes fmt, vet, code generation
  make test
  ```
- **What it validates**: Code compiles, passes linting (golangci-lint, go fmt, go vet), all unit tests pass
- **Duration**: ~5-10 minutes

#### 2. e2e-tests (smoke)
- **Trigger**: PRs with code changes (skips doc-only PRs)
- **Workflow**: `.github/workflows/ci-pr-checks.yaml`
- **Commands**:
  ```bash
  make docker-build IMG=<local-image>
  make deploy-e2e-infra  # creates Kind cluster, deploys WVA + llm-d
  make test-e2e-smoke    # runs smoke test subset
  ```
- **What it validates**: Controller deploys to Kind cluster, basic autoscaling works
- **Duration**: ~15-20 minutes
- **Infrastructure**: Requires Kind cluster with simulated GPU nodes, Prometheus, Gateway API CRDs

**Full E2E Suite** (optional, triggered by comment):
- Comment `/trigger-e2e-full` on PR (requires write access)
- Runs `make test-e2e-full` instead of smoke tests
- Duration: ~30-35 minutes
- Includes scale-to-zero, saturation-based scaling, parallel load tests

### Advisory Checks (Non-Gating)

- **Typo Checker**: AI-powered typo checking on changed files
- **Signed Commits**: Verifies commit signatures (workflow: `ci-signed-commits.yaml`)

---

## Test Structure

### Unit Tests
- **Location**: `*_test.go` files throughout `api/`, `internal/`, `pkg/`
- **Framework**: Ginkgo v2 + Gomega
- **Pattern**: Each package with `suite_test.go` for Ginkgo suite setup
- **Run command**: `make test` (excludes e2e tests)
- **Dependencies**: envtest (fake Kubernetes API server) - installed automatically by `make test`
- **Coverage**: Varies by package (39%-100%), overall coverage in `cover.out`

Example test packages:
- `api/v1alpha1/`: CRD type validation tests
- `internal/controller/`: Controller reconciliation logic tests
- `internal/actuator/`: Deployment actuator tests
- `pkg/solver/`: Allocation solver algorithm tests

### E2E Tests
- **Location**: `test/e2e/`
- **Framework**: Ginkgo v2 with Kubernetes client-go
- **Run command**: `make test-e2e-smoke` or `make test-e2e-full`
- **Dependencies**:
  - Kind cluster (3 nodes, emulated GPUs)
  - llm-d Gateway API CRDs
  - Prometheus + Prometheus Adapter OR KEDA
  - vLLM simulator or real vLLM deployments
- **Labels**:
  - `smoke`: Quick sanity tests (~5-10 min)
  - `full`: Comprehensive test suite (~30 min)
  - `flaky`: Known flaky tests (excluded from CI)
- **Cannot run in basic container** - requires full Kubernetes cluster

Example E2E tests:
- `smoke_test.go`: Basic VA creation and HPA generation
- `saturation_test.go`: Saturation-based autoscaling triggers
- `scale_to_zero_test.go`: Scale-to-zero and scale-from-zero
- `parallel_load_scaleup_test.go`: Concurrent load handling

### Test File Naming
- `*_test.go`: Test files
- `suite_test.go`: Ginkgo suite setup (BeforeSuite/AfterSuite)
- Test functions: `Test*` (standard Go) or `Describe/Context/It` (Ginkgo BDD)

---

## Linting

### Tools

1. **golangci-lint v2.8.0**
   - Config: None (uses defaults)
   - Run: `make lint`
   - Fix: `make lint-fix`
   - Auto-installed by Makefile to `bin/golangci-lint`

2. **go fmt**
   - Run: `go fmt ./...` (part of `make build` and `make test`)
   - Fixes formatting automatically

3. **go vet**
   - Run: `go vet ./...` (part of `make build` and `make test`)
   - Checks for suspicious constructs

### Pre-commit Hooks
Optional for developers (`.pre-commit-config.yaml`):
- shellcheck (shell scripts)
- hadolint (Dockerfiles)
- markdownlint (Markdown files)
- yamllint (YAML files)

Install: `pip install pre-commit && pre-commit install`

---

## Build Commands

### Local Development

**Build binary**:
```bash
make build
```
Output: `bin/manager`

**Run controller locally** (requires kubeconfig):
```bash
make run
```

**Generate CRDs and RBAC**:
```bash
make manifests
```

**Generate DeepCopy methods**:
```bash
make generate
```

### Docker/Container Builds

**Build container image**:
```bash
make docker-build IMG=ghcr.io/llm-d/llm-d-workload-variant-autoscaler:v0.1.0
```

**Push container image**:
```bash
make docker-push IMG=ghcr.io/llm-d/llm-d-workload-variant-autoscaler:v0.1.0
```

**Multi-arch build** (requires buildx):
```bash
make docker-buildx IMG=ghcr.io/llm-d/llm-d-workload-variant-autoscaler:v0.1.0
```

---

## Conventions

### Import Style
Standard Go import grouping:
```go
import (
    // Standard library
    "context"
    "fmt"

    // Third-party packages
    "github.com/onsi/ginkgo/v2"
    "k8s.io/apimachinery/pkg/types"

    // Local packages
    "github.com/llm-d/llm-d-workload-variant-autoscaler/api/v1alpha1"
)
```

### Test Patterns

**Ginkgo BDD style** (controller tests):
```go
var _ = Describe("Controller", func() {
    Context("when reconciling", func() {
        It("should create HPA", func() {
            Expect(err).NotTo(HaveOccurred())
        })
    })
})
```

**Standard Go tests** (package tests):
```go
func TestSolver(t *testing.T) {
    result := Solve(input)
    assert.Equal(t, expected, result)
}
```

### Code Generation
Uses controller-gen for:
- CRD manifests: `config/crd/bases/*.yaml`
- RBAC: ClusterRole, Role manifests
- DeepCopy methods: `zz_generated.deepcopy.go` files

Generated on `make build` and `make manifests`.

---

## Gaps & Caveats

### Known Gaps

1. **No golangci-lint configuration** - uses default linter set. No custom rules or disabled linters.

2. **E2E tests require infrastructure** - cannot run in basic container:
   - Need Kind cluster (3 nodes, GPU labels)
   - Need llm-d Gateway API components
   - Need Prometheus + metrics stack
   - Need vLLM simulator or real vLLM

3. **Some packages lack unit tests** - coverage: 0.0% for:
   - `cmd/` (main entry point)
   - `internal/collector/` (metrics collector)
   - `internal/logging/` (logging utilities)
   - `internal/metrics/` (Prometheus metrics)

4. **No coverage threshold enforcement** - CI doesn't fail on coverage drops.

5. **Test isolation** - E2E tests require namespace cleanup between runs. Suite includes cleanup logic but leftover resources can cause flakes.

### Workarounds

**For E2E validation without infrastructure**:
- Run only unit tests: `make test`
- Unit tests have good coverage of core logic (60-90% for most packages)
- Actuator, solver, and engine logic well-tested without cluster

**For local E2E testing**:
- Install Kind: `curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.25.0/kind-linux-amd64 && chmod +x kind && sudo mv kind /usr/local/bin/`
- Run: `make test-e2e-smoke-with-setup CREATE_CLUSTER=true`
- Cleanup: `make undeploy-wva-emulated-on-kind DELETE_CLUSTER=true`

---

## Quick Reference

### Most Common Commands

| Task | Command | Duration |
|------|---------|----------|
| Install deps | `go mod download` | 30s |
| Build | `make build` | 1-2m |
| Lint | `make lint` | 30s |
| Unit tests | `make test` | 1-2m |
| Single test | `go test ./path/to/package/...` | <1m |
| E2E smoke (local) | `make test-e2e-smoke-with-setup` | 15m |
| E2E full (local) | `make test-e2e-full-with-setup` | 30m |

### File Locations

| Item | Path |
|------|------|
| Main entry point | `cmd/main.go` |
| CRD types | `api/v1alpha1/` |
| Controller logic | `internal/controller/` |
| Unit tests | `*_test.go` throughout |
| E2E tests | `test/e2e/` |
| Generated CRDs | `config/crd/bases/` |
| Makefile | `Makefile` (root) |
| Go modules | `go.mod`, `go.sum` |

### Environment Variables

- `KUBEBUILDER_ASSETS`: Set by `make test` to envtest binaries path
- `KUBECONFIG`: Path to kubeconfig for E2E tests (default: `~/.kube/config`)
- `IMG`: Container image for builds (default: `ghcr.io/llm-d/llm-d-workload-variant-autoscaler:latest`)
- `ENVIRONMENT`: Test environment (default: `kind-emulator` for E2E)

---

## For Downstream Agents

### Patch Validation Recipe

**Minimum validation** (unit tests only, ~3 minutes):
1. Start golang:1.24.0 container with repo mounted to `/app`
2. Install: `apt-get update && apt-get install -y make git`
3. Deps: `go mod download`
4. Lint: `make lint` → must exit 0
5. Test: `make test` → must exit 0

**Recommended validation** (if build is needed):
1-3. Same as above
4. Build: `make build` → must exit 0
5. Lint: `make lint` → must exit 0
6. Test: `make test` → must exit 0

**Full validation** (requires Kind + infrastructure, ~20 minutes):
1-6. Same as recommended
7. E2E smoke: `make test-e2e-smoke-with-setup CREATE_CLUSTER=true`
8. Cleanup: `make undeploy-wva-emulated-on-kind DELETE_CLUSTER=true`

### Expected Pass/Fail Signals

**Build failure** (non-zero exit):
- Syntax errors
- Import errors
- Code generation fails

**Lint failure** (non-zero exit from `make lint`):
- golangci-lint issues (see output for specifics)
- go fmt needed (code not formatted)
- go vet warnings

**Test failure** (non-zero exit from `make test`):
- Test assertions failed (see Ginkgo output for failing specs)
- Test panic/crash
- Timeout (envtest setup hangs)

**Success signal**:
- All commands exit 0
- Lint output: "0 issues"
- Test output: "ok" for all packages, no "FAIL" lines

### Single Test Execution

**By package**:
```bash
go test ./internal/actuator/...
```

**By test name**:
```bash
go test -run TestActuator ./internal/actuator/...
```

**Ginkgo focus**:
```bash
go test ./internal/actuator/... -ginkgo.focus='Direct actuator'
```

**With coverage**:
```bash
go test ./internal/actuator/... -coverprofile=coverage.out
```

---

**Generated**: 2026-03-22T20:43:00Z
**Agent Readiness**: HIGH ✅
**Confidence**: HIGH ✅

This repository is ready for automated patch validation via lint + unit tests in a standard Go container.
