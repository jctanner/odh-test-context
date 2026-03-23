# Test Context: llama-stack-k8s-operator

**Organization**: opendatahub-io
**Analyzed**: 2026-03-22T22:48:00Z
**Agent Readiness**: medium - Lint and unit tests validated successfully in container. E2E tests require k8s cluster infrastructure.

## Overview

Go-based Kubernetes operator for LlamaStack distributions. Uses kubebuilder/operator-sdk patterns with controller-runtime. Build system: Make + Go 1.25.5+. Testing: Go testing with testify and envtest. Linting: golangci-lint v2.8.0 with comprehensive configuration.

**Agent readiness: medium** - All lint and unit test commands validated successfully in a standard golang:1.22 container with GOTOOLCHAIN=auto. E2E tests require Kubernetes infrastructure (kind cluster with local registry). Good unit test coverage (31-83% across packages). Clear test patterns and well-configured linting.

---

## Container Recipe

This recipe was **live-validated** and all commands executed successfully.

### 1. Start Container

```bash
podman run -d --name test-llama-stack-k8s-operator \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.22 \
  sleep infinity
```

**Note**: Use `golang:1.22` as base image. Go 1.25.5 will be auto-downloaded via `GOTOOLCHAIN=auto`.

### 2. Install System Dependencies

```bash
podman exec test-llama-stack-k8s-operator bash -c \
  "apt-get update && apt-get install -y make git curl"
```

### 3. Install Go Dependencies

```bash
podman exec test-llama-stack-k8s-operator bash -c \
  "cd /app && GOTOOLCHAIN=auto go mod download"
```

**Expected**: Downloads Go 1.25.5 automatically and all module dependencies (~3370 lines in go.mod).

### 4. Generate Manifests (Required for Tests)

The test suite requires generated manifests and code:

```bash
podman exec test-llama-stack-k8s-operator bash -c \
  "cd /app && GOTOOLCHAIN=auto make manifests generate"
```

**Note**: This downloads controller-gen and generates CRDs and DeepCopy code. Required before running tests.

### 5. Run Linting

```bash
podman exec test-llama-stack-k8s-operator bash -c \
  "cd /app && GOTOOLCHAIN=auto make lint"
```

**Validated**: ✓ Exit code 0, 0 issues found
**Time**: ~3-4 minutes on first run (downloads golangci-lint v2.8.0)
**Output**: `0 issues.`

Alternative direct commands:

```bash
# Go fmt
podman exec test-llama-stack-k8s-operator bash -c \
  "cd /app && GOTOOLCHAIN=auto go fmt ./..."

# Go vet
podman exec test-llama-stack-k8s-operator bash -c \
  "cd /app && GOTOOLCHAIN=auto go vet ./..."
```

**Validated**: ✓ Both passed with no output

### 6. Run Unit Tests

```bash
podman exec test-llama-stack-k8s-operator bash -c \
  "cd /app && GOTOOLCHAIN=auto make test"
```

**Validated**: ✓ Exit code 0, all packages passed
**Time**: ~16 seconds (after initial tool downloads)
**Output snippet**:
```
ok  	github.com/llamastack/llama-stack-k8s-operator/controllers	9.845s	coverage: 59.9% of statements
ok  	github.com/llamastack/llama-stack-k8s-operator/pkg/compare	0.017s	coverage: 31.8% of statements
ok  	github.com/llamastack/llama-stack-k8s-operator/pkg/deploy	5.897s	coverage: 47.1% of statements
ok  	github.com/llamastack/llama-stack-k8s-operator/pkg/deploy/plugins	0.025s	coverage: 83.0% of statements
```

**Note**: The `make test` command excludes E2E tests and generates a `cover.out` file.

### 7. Run Single Package Tests

```bash
podman exec test-llama-stack-k8s-operator bash -c \
  "cd /app && GOTOOLCHAIN=auto KUBEBUILDER_ASSETS=/app/bin/k8s/1.31.0-linux-amd64 go test ./pkg/compare -v"
```

**Validated**: ✓ Exit code 0, all tests in package passed

Replace `./pkg/compare` with any package path:
- `./controllers`
- `./pkg/deploy`
- `./pkg/deploy/plugins`
- `./pkg/cluster`

### 8. Run Single Test

```bash
podman exec test-llama-stack-k8s-operator bash -c \
  "cd /app && GOTOOLCHAIN=auto KUBEBUILDER_ASSETS=/app/bin/k8s/1.31.0-linux-amd64 go test ./pkg/compare -run TestHasUnexpectedServiceChanges/only_managed_port_changed -v"
```

**Validated**: ✓ Exit code 0, single test passed

Pattern: `go test {package} -run {TestName}` or `go test {package} -run {TestName/SubtestName}`

### 9. Cleanup

```bash
podman rm -f test-llama-stack-k8s-operator
```

---

## Validation Results

All commands validated in live container:

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Dependencies | `GOTOOLCHAIN=auto go mod download` | 0 | ✓ Pass | Auto-downloaded Go 1.25.5 |
| Manifests | `make manifests generate` | 0 | ✓ Pass | Generated CRDs and DeepCopy |
| Format | `go fmt ./...` | 0 | ✓ Pass | No formatting issues |
| Vet | `go vet ./...` | 0 | ✓ Pass | No warnings |
| Lint | `make lint` | 0 | ✓ Pass | 0 issues, downloads golangci-lint v2.8.0 |
| Unit Tests | `make test` | 0 | ✓ Pass | All packages passed, 31-83% coverage |
| Single Package | `go test ./pkg/compare` | 0 | ✓ Pass | All tests in package passed |
| Single Test | `go test ./pkg/compare -run TestName` | 0 | ✓ Pass | Specific test passed |

**Summary**: install OK, fmt OK, vet OK, lint OK (0 issues), tests OK (all packages passed, 31-83% coverage)

---

## CI/CD Checks

### GitHub Actions (Gating)

**pre-commit** (on PRs to `main`):
```bash
pre-commit run --show-diff-on-failure --color=always --all-files
```
- Runs: `make lint`, `make generate manifests`, `make build-installer`, `make api-docs`
- Also runs: YAML checks, JSON checks, trailing whitespace, EOF fixer, private key detection
- **Gating**: Yes - Fails if uncommitted changes or lint issues

**code-coverage** (on PRs to `odh` branch):
```bash
make test
limgo -coverfile=cover.out -outfmt=md -outfile=/tmp/covcheck.md -v=4 -config=.limgo.json
```
- Runs unit tests with coverage reporting via limgo
- **Gating**: Yes - Coverage results uploaded to artifacts and PR summary

**e2e-tests** (on PRs to `main`):
```bash
# Create kind cluster with local registry
kind create cluster --config kind-config.yaml
# Build and push operator image
docker build -t kind-registry:5000/llama-stack-k8s-operator:latest .
docker push kind-registry:5000/llama-stack-k8s-operator:latest
# Deploy operator
make deploy IMG=kind-registry:5000/llama-stack-k8s-operator:latest
# Run e2e tests
make test-e2e
```
- **Gating**: Yes - Requires kind cluster, 30m timeout
- **Cannot be validated in simple container** - requires k8s infrastructure

### Tekton (Gating on `odh` branch)

Multi-arch container build pipeline via ODH Konflux central:
- Triggers on PRs to `odh` branch
- Builds images for linux/amd64 and linux/arm64
- Uses pipeline from opendatahub-io/odh-konflux-central

---

## Project Conventions

### Test File Naming
- Pattern: `*_test.go`
- Examples: `llamastackdistribution_controller_test.go`, `comparison_test.go`, `deploy_test.go`

### Test Function Naming
- Standard Go convention: `Test*` functions
- Subtests: `t.Run("descriptive name", func(t *testing.T) {...})`
- Example from code:
  ```go
  func TestHasUnexpectedServiceChanges(t *testing.T) {
      t.Run("no changes detected", func(t *testing.T) { ... })
      t.Run("only managed port changed", func(t *testing.T) { ... })
  }
  ```

### Import Grouping
Enforced by `gci` linter:
1. Standard library
2. Third-party packages
3. Local packages (github.com/llamastack/llama-stack-k8s-operator/...)

### Test Setup Patterns
- Controller tests: Use `suite_test.go` with `TestMain` to set up envtest environment
- E2E tests: Use `setup_test.go` with `TestMain` to set up cluster client
- Testify assertions: `assert.Equal()`, `assert.NoError()`, etc.

---

## Gaps & Caveats

### Cannot Validate Without Infrastructure
- **E2E tests** (`make test-e2e`): Require kind cluster with local registry, operator deployment, and Ollama service
- **Pre-commit full workflow**: Requires Python pre-commit tool installation (not validated)
- **Container image builds**: Require buildx/manifest tools (not validated)

### Test Coverage Gaps
- `pkg/cluster`: 0% coverage (no unit tests)
- `pkg/featureflags`: No test files
- Overall coverage enforced at 0% via `.limgo.json` (permissive)

### Tool Download Overhead
First run of `make test` or `make lint` downloads tools to `./bin/`:
- golangci-lint v2.8.0 (~3-4 min download)
- controller-gen v0.17.2
- setup-envtest (downloads k8s 1.31.0 binaries)
- yq v4.45.3

Subsequent runs are fast (~16s for tests, ~30s for lint).

### Go Version Requirement
- Requires Go 1.25.5+ (specified in go.mod)
- Base golang:1.22 image works with `GOTOOLCHAIN=auto`
- Go 1.25.5 is auto-downloaded on first `go` command

### KUBEBUILDER_ASSETS
- Required for controller tests (uses envtest)
- `make test` sets it automatically via setup-envtest
- Direct `go test` invocations need it explicitly: `KUBEBUILDER_ASSETS=/app/bin/k8s/1.31.0-linux-amd64`

---

## Quick Reference

**Validate a patch in container**:
```bash
# Start container
podman run -d --name test-llama-stack-k8s-operator -v $(pwd):/app:Z -w /app golang:1.22 sleep infinity

# Install deps, run lint and tests
podman exec test-llama-stack-k8s-operator bash -c "
  apt-get update && apt-get install -y make git curl &&
  cd /app &&
  GOTOOLCHAIN=auto go mod download &&
  GOTOOLCHAIN=auto make manifests generate &&
  GOTOOLCHAIN=auto make lint &&
  GOTOOLCHAIN=auto make test
"

# Cleanup
podman rm -f test-llama-stack-k8s-operator
```

**Test a specific package**:
```bash
podman exec test-llama-stack-k8s-operator bash -c \
  "cd /app && GOTOOLCHAIN=auto KUBEBUILDER_ASSETS=/app/bin/k8s/1.31.0-linux-amd64 go test ./pkg/deploy -v"
```

**Test a specific test case**:
```bash
podman exec test-llama-stack-k8s-operator bash -c \
  "cd /app && GOTOOLCHAIN=auto KUBEBUILDER_ASSETS=/app/bin/k8s/1.31.0-linux-amd64 go test ./controllers -run TestLlamaStackDistribution -v"
```

**Check what E2E tests require** (cannot run in simple container):
- kind cluster with registry
- Operator deployed to cluster
- Ollama deployed via `./hack/deploy-quickstart.sh`
- 30m timeout
- See `.github/workflows/run-e2e-test.yml` for full setup

---

## File Locations

- **Linter config**: `.golangci.yml`
- **Pre-commit config**: `.pre-commit-config.yaml`
- **Coverage config**: `.limgo.json`
- **Makefile**: `Makefile` (primary build/test interface)
- **CRD definitions**: `config/crd/bases/`
- **API types**: `api/v1alpha1/`
- **Controllers**: `controllers/`
- **Shared packages**: `pkg/`
- **Unit tests**: Co-located with source (`*_test.go`)
- **E2E tests**: `tests/e2e/`
- **Test fixtures**: `controllers/suite_test.go` (envtest setup)

---

**Generated by**: Repository analysis and live container validation
**Confidence**: High - All unit test and lint commands validated successfully in isolated container
**Recommended for**: Automated patch validation where unit tests and linting are sufficient. E2E testing requires additional infrastructure setup.
