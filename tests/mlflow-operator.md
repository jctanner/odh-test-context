# Test Context: mlflow-operator

**Agent Readiness: HIGH** — Lint and test commands validated successfully in container. An agent can clone, patch, lint, test, and get clear pass/fail signals.

## Overview

- **Repository:** opendatahub-io/mlflow-operator
- **Language:** Go 1.24.6
- **Build System:** Go modules + Makefile
- **Test Framework:** Ginkgo v2 (BDD) + Gomega
- **Project Type:** Kubernetes operator (kubebuilder-based)
- **Analyzed:** 2026-03-22T23:15:59Z

This is a Kubernetes operator that manages MLflow deployments. It uses kubebuilder patterns with controller-runtime, embeds Helm charts, and requires code generation for CRDs and deepcopy methods.

## Container Recipe

This recipe provides a complete, validated workflow for running lint and tests in a container. All commands have been tested and work.

### 1. Start Container

```bash
podman run -d --name test-context-mlflow-operator \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-mlflow-operator bash -c \
  "apt-get update -qq && apt-get install -y -qq make git"
```

### 3. Download Go Dependencies

```bash
podman exec test-context-mlflow-operator bash -c \
  "cd /app && go mod download"
```

**Validation:** ✅ Exit code 0

### 4. Install Build Tools

```bash
# Install controller-gen for CRD/RBAC generation
podman exec test-context-mlflow-operator bash -c \
  "cd /app && make controller-gen"

# Install golangci-lint for linting
podman exec test-context-mlflow-operator bash -c \
  "cd /app && make golangci-lint"

# Install setup-envtest for test environment
podman exec test-context-mlflow-operator bash -c \
  "cd /app && make setup-envtest"
```

**Validation:** ✅ All tools installed successfully

### 5. Generate Code (Required Before Build/Test)

```bash
# Generate CRD manifests
podman exec test-context-mlflow-operator bash -c \
  "cd /app && make manifests"

# Generate deepcopy methods
podman exec test-context-mlflow-operator bash -c \
  "cd /app && make generate"
```

**Validation:** ✅ Exit code 0 for both commands

### 6. Build

```bash
podman exec test-context-mlflow-operator bash -c \
  "cd /app && go build -o bin/manager cmd/main.go"
```

**Validation:** ✅ Exit code 0, binary created successfully

### 7. Run Linters

```bash
# golangci-lint (primary linter)
podman exec test-context-mlflow-operator bash -c \
  "cd /app && ./bin/golangci-lint run"

# go fmt
podman exec test-context-mlflow-operator bash -c \
  "cd /app && go fmt ./..."

# go vet
podman exec test-context-mlflow-operator bash -c \
  "cd /app && go vet ./..."
```

**Validation:**
- ✅ golangci-lint: 0 issues
- ✅ go fmt: no formatting issues
- ✅ go vet: no warnings

**Auto-fix:** For fixable issues, run:
```bash
podman exec test-context-mlflow-operator bash -c \
  "cd /app && ./bin/golangci-lint run --fix"
```

### 8. Run Tests

```bash
podman exec test-context-mlflow-operator bash -c \
  "cd /app && KUBEBUILDER_ASSETS=\"/app/bin/k8s/1.34.1-linux-amd64\" \
  go test \$(go list ./... | grep -v /e2e) -coverprofile cover.out"
```

**Validation:**
- ✅ Exit code 0
- ✅ All tests passed
- ✅ Coverage: 62.0%

**Output:**
```
ok  	github.com/opendatahub-io/mlflow-operator/internal/controller	5.702s	coverage: 62.0% of statements
```

### 9. Run Single Test

Run a specific test by name:
```bash
podman exec test-context-mlflow-operator bash -c \
  "cd /app && KUBEBUILDER_ASSETS=\"/app/bin/k8s/1.34.1-linux-amd64\" \
  go test ./internal/controller -run TestMlflowToHelmValues_Storage -v"
```

Run all tests in a specific package:
```bash
podman exec test-context-mlflow-operator bash -c \
  "cd /app && KUBEBUILDER_ASSETS=\"/app/bin/k8s/1.34.1-linux-amd64\" \
  go test ./internal/controller -v"
```

**Validation:** ✅ Single test execution works correctly

### 10. Cleanup

```bash
podman rm -f test-context-mlflow-operator
```

## Validation Results

All commands were validated in a `golang:1.24` container:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Dependencies | `go mod download` | ✅ Pass | All modules downloaded |
| Build Tools | `make controller-gen golangci-lint setup-envtest` | ✅ Pass | All tools installed |
| Code Gen | `make manifests generate` | ✅ Pass | CRDs and deepcopy generated |
| Build | `go build -o bin/manager cmd/main.go` | ✅ Pass | Binary created |
| Lint | `./bin/golangci-lint run` | ✅ Pass | 0 issues found |
| Format | `go fmt ./...` | ✅ Pass | No formatting issues |
| Vet | `go vet ./...` | ✅ Pass | No warnings |
| Unit Tests | `go test $(go list ./... \| grep -v /e2e)` | ✅ Pass | 62.0% coverage |

**Critical Note:** The `KUBEBUILDER_ASSETS` environment variable must use an **absolute path** in containers. The relative path that works in Makefile (`$(shell ...)`) does not resolve correctly in container exec contexts.

## CI/CD

### Gating Checks (Required for PR Merge)

All checks run on `pull_request` triggers:

1. **Lint** (`.github/workflows/lint.yml`)
   - Runs golangci-lint v2.5.0 via GitHub Action
   - Triggers on: Go file changes, .github changes
   - Command: Uses `golangci/golangci-lint-action@v8`

2. **Tests** (`.github/workflows/test.yml`)
   - Runs unit tests (excludes e2e)
   - Triggers on: Go files, go.mod, go.sum, Makefile
   - Commands:
     ```bash
     go mod tidy
     make test
     ```

3. **Verify Generated Code** (`.github/workflows/verify-codegen.yml`)
   - Ensures generated code is up-to-date
   - Triggers on: Go files, go.mod, config, api changes
   - Commands:
     ```bash
     make manifests
     make generate
     git diff --exit-code
     ```
   - Fails if running codegen produces uncommitted changes

4. **Verify Manifest Builds** (`.github/workflows/verify-kustomize.yml`)
   - Validates kustomize and Helm manifests build correctly
   - Triggers on: config, charts, Makefile changes
   - Requires: Helm v3.14.0
   - Command: `make verify-manifests`

5. **Validate Sample CRs** (`.github/workflows/validate-samples.yaml`)
   - Validates sample custom resources against CRDs
   - Triggers on: config/samples, api, crd changes
   - Requires: Kind cluster
   - Commands:
     ```bash
     make manifests
     make validate-samples
     ```

6. **E2E Tests** (`.github/workflows/test-e2e.yml`)
   - Full end-to-end operator testing
   - Triggers on: cmd, config, test, Dockerfile, go files
   - Requires: Kind cluster
   - Commands:
     ```bash
     make docker-build IMG=localhost/mlflow-operator:v0.0.1
     kind load docker-image localhost/mlflow-operator:v0.0.1
     go mod tidy
     make test-e2e
     ```

### Additional CI Systems

- **Tekton Pipelines:** `.tekton/mlflow-operator-pull-request.yaml` and `.tekton/mlflow-operator-push.yaml`

## Conventions

### Test Files
- Pattern: `*_test.go`
- Location: `internal/controller/*_test.go`, `test/e2e/*_test.go`
- Framework: Ginkgo v2 BDD style with Gomega assertions

### Test Naming
- Ginkgo BDD: `Describe()`, `Context()`, `It()`, `Entry()` blocks
- Table-driven tests using Ginkgo's `DescribeTable()` and `Entry()`
- Standard Go tests: `Test*` prefix (e.g., `TestMlflowToHelmValues_Storage`)

### Package Structure
```
mlflow-operator/
├── api/                      # CRD type definitions
│   ├── mlflowconfig/v1/     # MLflowConfig CRD
│   └── v1/                   # MLflow CRD
├── cmd/main.go              # Operator entrypoint
├── internal/controller/      # Reconciliation logic
├── config/                   # Kustomize manifests
│   ├── crd/bases/           # Generated CRDs
│   ├── manager/             # Operator deployment
│   └── overlays/            # Platform-specific configs
├── charts/mlflow/           # Embedded Helm chart
├── test/
│   ├── e2e/                 # E2E tests (require cluster)
│   └── scripts/             # Test utilities
└── hack/                    # Build scripts
```

### Import Style
Standard Go convention:
1. Standard library imports
2. External dependencies
3. Internal packages

### Coverage
- Generated via `go test -coverprofile cover.out`
- Current coverage: 62.0% (unit tests only)
- No enforced threshold

## Gaps & Caveats

### Cannot Validate in Simple Container
1. **E2E Tests** — Require Kind cluster with operator deployed. The `make test-e2e` target:
   - Builds and loads operator image into Kind
   - Deploys the operator
   - Runs Ginkgo specs that create MLflow CRs and verify reconciliation
   - Cannot run in standard container without nested Docker/podman

2. **Sample Validation** — Requires Kubernetes cluster to apply CRDs and validate sample CRs

3. **Manifest Verification** — Script checks kustomize builds for multiple overlays (dev, kind, odh, openshift, rhoai) and Helm chart rendering

### External Dependencies
- **envtest binaries:** Downloaded by setup-envtest (etcd, kube-apiserver, kubectl ~170MB)
- **controller-gen:** Required for CRD/RBAC generation
- **kustomize:** Required for manifest builds
- **Kind cluster:** Required for E2E and sample validation

### Path Issues in Containers
- The Makefile uses `$(shell ...)` to get envtest binary paths dynamically
- This doesn't work in `podman exec` contexts
- **Solution:** Use absolute paths for `KUBEBUILDER_ASSETS` in containers
- Correct: `KUBEBUILDER_ASSETS="/app/bin/k8s/1.34.1-linux-amd64"`
- Won't work: `KUBEBUILDER_ASSETS="$(./bin/setup-envtest use 1.34 -p path)"`

### Code Generation Required
The project uses code generation extensively:
- `make manifests` — Generates CRDs and RBAC from Go code markers
- `make generate` — Generates deepcopy methods for Kubernetes types
- Both must run before build/test
- CI verifies generated code is committed (fails if out of sync)

## Quick Reference

### Makefile Targets (Host)
```bash
make help              # Show all targets
make lint              # Run golangci-lint
make lint-fix          # Auto-fix linting issues
make test              # Run unit tests (excludes e2e)
make test-e2e          # Run e2e tests (requires Kind)
make build             # Build operator binary
make docker-build      # Build container image
make manifests         # Generate CRDs and RBAC
make generate          # Generate deepcopy code
make verify-manifests  # Verify manifest builds
make validate-samples  # Validate sample CRs (requires cluster)
```

### Direct Commands (Container)
```bash
# Lint
./bin/golangci-lint run
./bin/golangci-lint run --fix
go fmt ./...
go vet ./...

# Test
KUBEBUILDER_ASSETS="/app/bin/k8s/1.34.1-linux-amd64" \
  go test $(go list ./... | grep -v /e2e) -coverprofile cover.out

# Test specific package
KUBEBUILDER_ASSETS="/app/bin/k8s/1.34.1-linux-amd64" \
  go test ./internal/controller -v

# Test specific test
KUBEBUILDER_ASSETS="/app/bin/k8s/1.34.1-linux-amd64" \
  go test ./internal/controller -run TestMlflowToHelmValues_Storage -v

# Build
go build -o bin/manager cmd/main.go
```

## Agent Usage Recommendations

**For patch validation:**
1. Use the container recipe above verbatim
2. After applying patches, run: codegen → lint → test
3. If codegen changes files, fail with "regenerate code with make manifests generate"
4. Parse test output for `FAIL` vs `PASS` to determine success
5. Coverage can decrease if patch adds untested code (not necessarily a failure)

**For understanding test failures:**
- Ginkgo outputs structured test results with `[FAIL]` markers
- Check for `BeforeSuite` failures (usually envtest setup issues)
- Table-driven test failures show which `Entry()` failed
- Controller tests may fail due to missing CRD manifests (run `make manifests`)

**For E2E validation:**
- Not possible in basic container
- Requires Kind cluster + operator deployment
- See `.github/workflows/test-e2e.yml` for complete setup
- E2E tests live in `test/e2e/` and use cluster-scoped resources
