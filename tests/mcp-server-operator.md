# Test Context: mcp-server-operator

**Repository:** opendatahub-io/mcp-server-operator
**Analyzed:** 2026-03-22
**Language:** Go 1.23.0
**Type:** Kubernetes operator (Kubebuilder/controller-runtime)
**Agent Readiness:** ✅ **HIGH** - All lint and test commands validated successfully in container

---

## Overview

This is a Kubebuilder-generated Kubernetes operator that manages MCP (Model Context Protocol) server instances on OpenShift clusters. The project has:
- ✅ Comprehensive linting with golangci-lint (24+ enabled linters)
- ✅ Unit tests with 76.4% coverage using Ginkgo/Gomega and envtest
- ✅ Clean CI/CD via GitHub Actions (lint + test)
- ✅ Well-structured Makefile with clear targets
- ⚠️  E2E tests require Kind cluster (not runnable in simple container)

An AI agent can validate patches by running lint and unit tests in a standard golang:1.23 container with no external dependencies.

---

## Container Recipe

This is the **complete, copy-paste recipe** for validating patches. All commands validated live.

### 1. Start Container

```bash
podman run -d --name test-context-mcp-server-operator \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.23 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-mcp-server-operator bash -c \
  "apt-get update && apt-get install -y make git"
```

### 3. Install Go Dependencies

```bash
podman exec test-context-mcp-server-operator bash -c \
  "cd /app && go mod download"
```

**Expected:** No output (success). Downloads all Go modules listed in go.mod.

### 4. Run Linting

#### Option A: Via Makefile (recommended)
```bash
podman exec test-context-mcp-server-operator bash -c \
  "cd /app && make lint"
```

**Expected:** Downloads golangci-lint v1.63.4 to `bin/` on first run, then executes linting. Exit code 0 if clean.

**First run output:**
```
Downloading github.com/golangci/golangci-lint/cmd/golangci-lint@v1.63.4
(downloads dependencies...)
```

**Subsequent runs:** Silent if no issues found.

#### Option B: Direct invocation (after make lint has run once)
```bash
podman exec test-context-mcp-server-operator bash -c \
  "cd /app && ./bin/golangci-lint run"
```

#### Option C: Individual linters
```bash
# Format check
podman exec test-context-mcp-server-operator bash -c \
  "cd /app && go fmt ./..."

# Static analysis
podman exec test-context-mcp-server-operator bash -c \
  "cd /app && go vet ./..."
```

**Validated Results:**
- ✅ `make lint` → Exit 0, no issues
- ✅ `go fmt ./...` → Exit 0, code formatted
- ✅ `go vet ./...` → Exit 0, no issues

### 5. Run Tests

```bash
podman exec test-context-mcp-server-operator bash -c \
  "cd /app && make test"
```

**What this does:**
1. Runs `make manifests` (generates CRDs and RBAC YAML)
2. Runs `make generate` (generates DeepCopy methods)
3. Runs `go fmt ./...` and `go vet ./...`
4. Downloads `setup-envtest` tool to `bin/` (first run only)
5. Downloads Kubernetes API server binaries to `bin/k8s/1.32.0-linux-amd64/` (first run only)
6. Runs `go test $(go list ./... | grep -v /e2e) -coverprofile cover.out`

**Expected output (abbreviated):**
```
Downloading sigs.k8s.io/controller-tools/cmd/controller-gen@v0.17.2
/app/bin/controller-gen rbac:roleName=manager-role crd webhook paths="./..." output:crd:artifacts:config=config/crd/bases
/app/bin/controller-gen object:headerFile="hack/boilerplate.go.txt" paths="./..."
go fmt ./...
go vet ./...
Downloading sigs.k8s.io/controller-runtime/tools/setup-envtest@release-0.20
Setting up envtest binaries for Kubernetes version 1.32...
/app/bin/k8s/1.32.0-linux-amd64KUBEBUILDER_ASSETS="/app/bin/k8s/1.32.0-linux-amd64" go test $(go list ./... | grep -v /e2e) -coverprofile cover.out
	github.com/opendatahub-io/mcp-server-operator/api/v1		coverage: 0.0% of statements
	github.com/opendatahub-io/mcp-server-operator/cmd		coverage: 0.0% of statements
?   	github.com/opendatahub-io/mcp-server-operator/pkg/cluster/gvk	[no test files]
	github.com/opendatahub-io/mcp-server-operator/test/utils		coverage: 0.0% of statements
ok  	github.com/opendatahub-io/mcp-server-operator/internal/controller	6.277s	coverage: 76.4% of statements
```

**Exit code:** 0 (success)

**Validated Result:** ✅ All unit tests pass, 76.4% coverage in controller package

### 6. Run Tests for a Single Package

```bash
podman exec test-context-mcp-server-operator bash -c \
  "cd /app && KUBEBUILDER_ASSETS=./bin/k8s/1.32.0-linux-amd64 go test ./internal/controller -v"
```

**Note:** After `make test` has run once, the envtest binaries are cached in `bin/k8s/`. You must set `KUBEBUILDER_ASSETS` to point to them.

**Expected:** Verbose output showing individual test cases passing.

### 7. Run a Specific Test

```bash
podman exec test-context-mcp-server-operator bash -c \
  "cd /app && KUBEBUILDER_ASSETS=./bin/k8s/1.32.0-linux-amd64 go test ./internal/controller -run TestMCPServerReconciler_reconcileMCPServerDeployment"
```

**Pattern:** Use `-run <regex>` to match test function names.

**Ginkgo focus (alternative):**
```bash
podman exec test-context-mcp-server-operator bash -c \
  "cd /app && KUBEBUILDER_ASSETS=./bin/k8s/1.32.0-linux-amd64 go test ./internal/controller -ginkgo.focus 'Verify MCPServer Deployment'"
```

**Pattern:** Use `-ginkgo.focus '<substring>'` to match test descriptions.

**Validated Result:** ✅ Both methods work for running specific tests

### 8. Build

```bash
podman exec test-context-mcp-server-operator bash -c \
  "cd /app && make build"
```

**What this does:**
1. Runs `make manifests generate fmt vet`
2. Runs `go build -o bin/manager cmd/main.go`

**Expected output:**
```
/app/bin/controller-gen rbac:roleName=manager-role crd webhook paths="./..." output:crd:artifacts:config=config/crd/bases
/app/bin/controller-gen object:headerFile="hack/boilerplate.go.txt" paths="./..."
go fmt ./...
go vet ./...
go build -o bin/manager cmd/main.go
```

**Exit code:** 0
**Artifact:** `bin/manager` binary created

**Validated Result:** ✅ Build succeeds, binary created

### 9. Cleanup

```bash
podman rm -f test-context-mcp-server-operator
```

---

## Validation Results

All commands validated live in `golang:1.23` container on 2026-03-22:

| Step | Command | Exit Code | Result |
|------|---------|-----------|--------|
| **Install** | `go mod download` | 0 | ✅ Clean |
| **Lint** | `make lint` | 0 | ✅ No issues |
| **Lint (direct)** | `./bin/golangci-lint run` | 0 | ✅ No issues |
| **Format** | `go fmt ./...` | 0 | ✅ Clean |
| **Vet** | `go vet ./...` | 0 | ✅ Clean |
| **Test** | `make test` | 0 | ✅ 76.4% coverage |
| **Test (package)** | `go test ./internal/controller` | 0 | ✅ Passed |
| **Test (specific)** | `go test -run TestName` | 0 | ✅ Passed |
| **Build** | `make build` | 0 | ✅ Binary created |

**Summary:** Install ✓, Lint ✓, Test ✓, Build ✓. Container recipe is production-ready.

---

## CI/CD

### GitHub Actions Workflows

Both workflows trigger on `push` and `pull_request` events and are **gating** (required for merge).

#### 1. Lint Workflow (`.github/workflows/lint.yml`)

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-go@v5
  with:
    go-version-file: go.mod
- uses: golangci/golangci-lint-action@v6
  with:
    version: v1.63.4
```

**What runs:** `golangci-lint run` with caching

#### 2. Test Workflow (`.github/workflows/test.yml`)

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-go@v5
  with:
    go-version-file: go.mod
- run: |
    go mod tidy
    make test
```

**What runs:**
1. `go mod tidy` (ensures go.mod/go.sum are clean)
2. `make test` (full unit test suite)

**Note:** Both jobs run on `ubuntu-latest`. Go version is read from `go.mod` (currently 1.23.0).

---

## Conventions

### Test Files
- **Pattern:** `*_test.go`
- **Location:** `internal/controller/*_test.go`, `test/e2e/*_test.go`
- **Framework:** Ginkgo v2 (BDD style) + Gomega (assertions)

### Test Structure
```go
// Test suite setup
var _ = BeforeSuite(func() {
    // Initialize envtest environment
})

var _ = AfterSuite(func() {
    // Cleanup
})

// Individual test
func TestMCPServerReconciler_reconcileMCPServerDeployment(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Test Description")
}

// Ginkgo specs (in separate files)
var _ = Describe("MCPServer Deployment", func() {
    It("should create a deployment with default values", func() {
        // Test logic with Gomega assertions
        Expect(err).NotTo(HaveOccurred())
    })
})
```

### Import Style
- Grouped: standard library, third-party, internal packages
- Ginkgo uses dot imports for BDD DSL: `. "github.com/onsi/ginkgo/v2"`

### Code Generation
This repo uses Kubebuilder/controller-runtime code generation:
- `make manifests` → Generates CRDs, RBAC YAML in `config/`
- `make generate` → Generates DeepCopy methods for API types
- Generated files have `// +kubebuilder:...` markers

---

## Gaps & Caveats

### 1. E2E Tests Require Kubernetes Cluster
- **Location:** `test/e2e/`
- **Command:** `make test-e2e` → `go test ./test/e2e/ -v -ginkgo.v`
- **Requirement:** Kind cluster must be running
- **Impact:** E2E tests **cannot** be validated in a simple container
- **Workaround:** `make test` excludes E2E tests (via `grep -v /e2e`)

### 2. Coverage Gaps
- **Controller package:** 76.4% ✅
- **API package (`api/v1`):** 0% (generated code, not typically tested)
- **Cmd package (`cmd`):** 0% (main.go entrypoint)
- **Utils package (`test/utils`):** 0%
- **No coverage threshold enforced** in CI or Makefile

### 3. Test Dependencies
- **envtest binaries:** `make test` downloads Kubernetes API server binaries (~50MB) to `bin/k8s/1.32.0-linux-amd64/` on first run. These are cached.
- **Tools:** golangci-lint, controller-gen, setup-envtest all downloaded to `bin/` on first run.
- **First run is slow** (~2-3 minutes for downloads). Subsequent runs are fast (~6 seconds).

### 4. Individual Test Files Cannot Be Run Directly
Go test files have inter-package dependencies. You **must** run tests by package:
- ✅ `go test ./internal/controller`
- ❌ `go test ./internal/controller/mcpserver_test.go` (will fail with "undefined" errors)

---

## Quick Reference

### Essential Commands

```bash
# Install dependencies
go mod download

# Lint (downloads tools on first run)
make lint

# Test (downloads tools + K8s binaries on first run)
make test

# Build
make build

# Format code
go fmt ./...

# Static analysis
go vet ./...

# Fix lint issues
make lint-fix
```

### Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `KUBEBUILDER_ASSETS` | `./bin/k8s/1.32.0-linux-amd64` | Path to envtest K8s binaries (required for tests) |
| `LOCALBIN` | `./bin` | Tool installation directory |
| `CONTAINER_TOOL` | `podman` or `docker` | Container engine for image builds |

### File Locations

| Path | Description |
|------|-------------|
| `.golangci.yml` | golangci-lint configuration (24+ linters enabled) |
| `Makefile` | Build automation (lint, test, build targets) |
| `go.mod` | Go 1.23.0, controller-runtime dependencies |
| `internal/controller/` | Reconciler logic + unit tests |
| `test/e2e/` | End-to-end tests (require Kind cluster) |
| `config/crd/bases/` | Generated CRD YAML |
| `bin/` | Downloaded tools (golangci-lint, controller-gen, envtest, K8s binaries) |

---

## Troubleshooting

### "text file busy" error during make lint
**Cause:** Parallel runs of `make lint` trying to write the same binary.
**Fix:** Wait for first run to complete, or run `./bin/golangci-lint run` directly.

### "KUBEBUILDER_ASSETS not set" during go test
**Cause:** Running `go test` directly without setting `KUBEBUILDER_ASSETS`.
**Fix:** Use `make test` (sets it automatically) or set manually:
```bash
export KUBEBUILDER_ASSETS=./bin/k8s/1.32.0-linux-amd64
go test ./internal/controller
```

### "Failed to set up envtest binaries"
**Cause:** Kubernetes version not available from envtest mirrors.
**Fix:** Check `ENVTEST_K8S_VERSION` in Makefile (currently 1.32). Version is auto-detected from `go.mod`.

### Tests fail with "no matches for kind X"
**Cause:** CRDs not registered in envtest scheme.
**Fix:** Ensure `suite_test.go` includes all required CRDs in `testEnv.CRDInstallOptions.Paths`.

---

## For AI Agents

**Primary validation workflow:**
1. Start `golang:1.23` container with repo mounted to `/app`
2. Install `make` and `git`
3. Run `go mod download`
4. Run `make lint` → expect exit 0
5. Run `make test` → expect exit 0, coverage output
6. Run `make build` → expect exit 0, `bin/manager` created
7. Cleanup container

**Patch validation:**
1. Apply patch to repo
2. Run steps 3-6 above
3. Report lint errors (if exit != 0) or test failures
4. Check if coverage decreased (parse `cover.out`)

**Limitations:**
- E2E tests (`test/e2e/`) cannot be validated (require cluster)
- First run is slow (downloads tools + K8s binaries)
- Subsequent runs are fast (~6s for tests)

**Coverage parsing:**
```bash
go tool cover -func=cover.out | grep total
```

Expected: `total: (statements) 76.4%` or higher after patches.
