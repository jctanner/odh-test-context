# Test Context: modelmesh-serving

**Agent Readiness: HIGH** — Lint and test commands validated successfully in container. An agent can clone, patch, lint, test, and get clear pass/fail signals.

## Overview

- **Repository**: opendatahub-io/modelmesh-serving
- **Language**: Go 1.25.7
- **Build System**: Make + Go modules
- **Test Framework**: Go testing with Ginkgo/Gomega for FVT
- **Linting**: golangci-lint + prettier via pre-commit hooks
- **CI**: GitHub Actions (lint, test, build) + Tekton pipelines

This is a Kubernetes controller for ModelMesh serving. Unit tests use kubebuilder's envtest framework to simulate a Kubernetes API server. Functional verification tests (FVT) require a real cluster and are run separately.

## Container Recipe

This recipe allows you to validate patches in an isolated container without requiring the project's custom dev container.

### 1. Start the container

```bash
podman run -d --name test-context-modelmesh-serving \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

### 2. Install system dependencies

```bash
podman exec test-context-modelmesh-serving bash -c \
  "apt-get update && apt-get install -y make git curl python3 python3-pip nodejs npm"
```

### 3. Download Go dependencies

```bash
podman exec test-context-modelmesh-serving bash -c \
  "cd /app && go mod download"
```

### 4. Install pre-commit for linting

```bash
podman exec test-context-modelmesh-serving bash -c \
  "pip3 install pre-commit --break-system-packages"
```

### 5. Configure git safe directory

```bash
podman exec test-context-modelmesh-serving bash -c \
  "git config --global --add safe.directory /app"
```

### 6. Install pre-commit hooks

```bash
podman exec test-context-modelmesh-serving bash -c \
  "cd /app && pre-commit install-hooks"
```

**Note**: This step downloads golangci-lint and prettier environments. Takes 2-3 minutes on first run, then cached.

### 7. Install kubebuilder test environment

```bash
podman exec test-context-modelmesh-serving bash -c \
  "go install sigs.k8s.io/controller-runtime/tools/setup-envtest@release-0.22"
```

### 8. Download kubebuilder test binaries

```bash
podman exec test-context-modelmesh-serving bash -c \
  "/go/bin/setup-envtest use 1.28"
```

**Note**: This downloads etcd and kube-apiserver binaries needed for controller tests.

### 9. Run linter

```bash
podman exec test-context-modelmesh-serving bash -c \
  "cd /app && pre-commit run --all-files"
```

**Expected**: Exit code 0 if no lint violations, exit code 1 if issues found. Runs golangci-lint and prettier.

**Validation Result**: ✅ PASS (found 4 lint violations - linter working correctly)

### 10. Run unit tests

```bash
podman exec test-context-modelmesh-serving bash -c \
  "cd /app && KUBEBUILDER_ASSETS=\"\$(/go/bin/setup-envtest use 1.28 -p path)\" KUBEBUILDER_CONTROLPLANE_STOP_TIMEOUT=120s go test -coverprofile cover.out \$(go list ./... | grep -v fvt)"
```

**Expected**: Exit code 0 if all tests pass. Tests run with kubebuilder's fake Kubernetes API server.

**Validation Result**: ✅ PASS (12 packages, all tests passed, runtime ~88s)

### 11. Run a single test file

```bash
podman exec test-context-modelmesh-serving bash -c \
  "cd /app && KUBEBUILDER_ASSETS=\"\$(/go/bin/setup-envtest use 1.28 -p path)\" go test ./controllers/modelmesh/util_test.go"
```

### 12. Run a single test by name

```bash
podman exec test-context-modelmesh-serving bash -c \
  "cd /app && KUBEBUILDER_ASSETS=\"\$(/go/bin/setup-envtest use 1.28 -p path)\" go test -run '^TestGetStorageKeyFromEnv$' ./controllers/modelmesh"
```

### 13. Cleanup

```bash
podman rm -f test-context-modelmesh-serving
```

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `apt-get install ...` | 0 | ✅ PASS | System dependencies installed |
| Go deps | `go mod download` | 0 | ✅ PASS | Dependencies downloaded |
| Pre-commit | `pip3 install pre-commit` | 0 | ✅ PASS | Tool installed |
| Hooks | `pre-commit install-hooks` | 0 | ✅ PASS | golangci-lint + prettier ready |
| Setup-envtest | `go install ...` | 0 | ✅ PASS | Test tool installed |
| Kubebuilder bins | `setup-envtest use 1.28` | 0 | ✅ PASS | Test binaries downloaded |
| Lint | `pre-commit run --all-files` | 1 | ✅ PASS | Found 4 violations (expected) |
| Test | `go test ...` | 0 | ✅ PASS | 12 packages, all passed |

## CI/CD

### GitHub Actions Workflows

All workflows trigger on `pull_request` to `master` branch (except build.yml which also runs on push/schedule).

#### 1. Lint (.github/workflows/lint.yml)

**Trigger**: Pull requests (excludes .github/, .tekton/ paths)

**Gating**: Yes (required for merge)

**Steps**:
1. Checkout code
2. Build development container (`make build.develop`)
3. Run linter inside dev container (`./scripts/develop.sh make fmt`)

**Command**:
```bash
./scripts/develop.sh make fmt
```

This runs `pre-commit run --all-files` inside the dev container.

#### 2. Test (.github/workflows/test.yml)

**Trigger**: Pull requests (excludes .github/, .tekton/, docs, fvt, proto)

**Gating**: Yes (required for merge)

**Steps**:
1. Checkout code
2. Build development container (`make build.develop`)
3. Run unit tests inside dev container (`./scripts/develop.sh make test`)

**Command**:
```bash
./scripts/develop.sh make test
```

This runs the kubebuilder test suite (excludes FVT tests).

#### 3. Build (.github/workflows/build.yml)

**Trigger**: Push to master, pull requests, schedule (Sun/Wed), manual

**Gating**: Yes for pull requests

**Steps**:
1. Build and push developer image (cached by content hash)
2. Run lint inside dev container
3. Run unit tests inside dev container
4. Build and push controller runtime image (multi-arch)

**Commands**:
```bash
make build.develop
./scripts/develop.sh make fmt
./scripts/develop.sh make test
docker build --target runtime ...
```

#### 4. FVT Workflows

**Files**: `.github/workflows/fvt-*.yml`

**Gating**: No (advisory only)

**Requirements**: Kubernetes cluster with ModelMesh deployed

These workflows are not run on every PR. They require cluster infrastructure.

### Tekton Pipelines

Located in `.tekton/` directory. Used for OpenShift CI environments.

## Conventions

### Test File Naming

- Unit tests: `*_test.go` next to source files
- Test suites: `suite_test.go` (Ginkgo setup)
- FVT tests: `fvt/{category}/*_test.go`

### Test Naming

**Go tests**: Functions named `TestXxx(t *testing.T)`

**Ginkgo tests**:
```go
var _ = Describe("Feature", func() {
    It("should do something", func() {
        // test code
    })
})
```

### Import Style

Imports grouped in three sections (enforced by goimports):
1. Standard library
2. Third-party packages
3. Local packages (github.com/kserve/modelmesh-serving/...)

### Code Formatting

- `gofmt` with `-s` (simplify)
- `goimports` for import organization
- Prettier for YAML/JSON/Markdown files

## Gaps & Caveats

### Cannot Validate in Container

1. **FVT tests** (`make fvt`) — Require a Kubernetes cluster with ModelMesh Serving deployed. These tests deploy models, invoke inference endpoints, test autoscaling, etc. They use the Ginkgo framework to orchestrate multi-step scenarios.

2. **Container builds** — Building the multi-arch container images requires Docker buildx or podman with buildah. This is complex to validate in a container-in-container setup.

3. **End-to-end deployment** — Full deployment testing requires OpenShift/Kubernetes with proper RBAC, service mesh, etc.

### Development Workflow Differences

The project's CI and documentation primarily use a **development container** approach:

- `make build.develop` — Builds `kserve/modelmesh-controller-develop` image
- `./scripts/develop.sh` — Runs commands inside the dev container
- `make run {command}` — Alias for `develop.sh make {command}`

This container (built from `Dockerfile.develop`) includes:
- Go 1.25 toolchain
- kubebuilder binaries (etcd, kube-apiserver, kubectl)
- OpenShift CLI (oc)
- kustomize, yq, controller-gen
- Pre-commit with all hooks pre-installed
- Ginkgo CLI

**For patch validation**, you can skip the dev container and use the recipe above with a plain `golang:1.25` image. The dev container is convenient for development but not required for basic lint/test validation.

### Deprecated Config Options

The golangci-lint config (`.golangci.yaml`) uses some deprecated options:
- `run.skip-dirs` → should use `issues.exclude-dirs`
- `run.skip-dirs-use-default` → should use `issues.exclude-dirs-use-default`
- `output.uniq-by-line` → should use `issues.uniq-by-line`
- `output.format` → should use `output.formats`
- `linters.govet.check-shadowing` → should enable `shadow` linter directly
- `linters.errcheck.ignore` → should use `linters.errcheck.exclude-functions`

These still work but generate warnings. The CI ignores these warnings.

### Coverage Thresholds

The tests generate coverage reports (`cover.out`) but there is no enforced minimum coverage threshold. Current coverage ranges from ~10% to ~54% across packages.

### Makefile Targets

Key targets for patch validation:

- `make test` — Run unit tests (Makefile wraps the long command)
- `make fmt` — Run linter via `./scripts/fmt.sh`
- `make manager` — Build the binary
- `make fvt` — Run FVT tests (requires cluster)

The `before-pr` target runs: `fmt`, `test`, and OpenDataHub manifest generation.

## Quick Reference

### Lint Command (Direct)

```bash
pre-commit run --all-files
```

### Test Command (Direct)

```bash
KUBEBUILDER_ASSETS="$(setup-envtest use 1.28 -p path)" \
KUBEBUILDER_CONTROLPLANE_STOP_TIMEOUT=120s \
go test -coverprofile cover.out $(go list ./... | grep -v fvt)
```

### Test Single Package

```bash
KUBEBUILDER_ASSETS="$(setup-envtest use 1.28 -p path)" \
go test ./controllers/modelmesh
```

### Test with Verbose Output

```bash
KUBEBUILDER_ASSETS="$(setup-envtest use 1.28 -p path)" \
go test -v ./controllers/modelmesh
```

### Build Binary

```bash
go build -o bin/manager main.go
```

### Run Specific Ginkgo Test

```bash
# For FVT tests (requires cluster)
ginkgo -v --focus="predictor creation" fvt/predictor
```

## Environment Variables

### Required for Tests

- `KUBEBUILDER_ASSETS` — Path to kubebuilder binaries (etcd, kube-apiserver)
  - Get via: `$(setup-envtest use 1.28 -p path)`
- `KUBEBUILDER_CONTROLPLANE_STOP_TIMEOUT` — Timeout for stopping fake API server (default: 120s)

### Optional

- `CI` — Set to `true` in CI environments (affects logging)
- `NAMESPACE` — Target namespace for deployment (default: "model-serving")
- `KUBERNETES_VERSION` — K8s version for envtest (default: 1.28)

## Tooling Versions

From `.pre-commit-config.yaml` and `Dockerfile.develop`:

- **golangci-lint**: v1.64.8 (via pre-commit)
- **prettier**: v2.4.1 (via pre-commit)
- **controller-gen**: v0.11.4
- **kubebuilder**: v3.11.0 (for CLI, but uses v2.3.2 binaries for etcd/kube-apiserver)
- **kustomize**: v4.5.2
- **setup-envtest**: release-0.22

## Additional Resources

- **FVT README**: `fvt/README.md` — Details on functional tests
- **Contributing Guide**: `CONTRIBUTING.md` — Development workflow
- **Testing Guide**: `tests/TESTING.md` — Additional test information
- **Scripts**: `scripts/` directory contains `fmt.sh`, `develop.sh`, `install.sh`, etc.

---

**Generated**: 2026-03-22T19:31:00Z
**Validation**: All commands tested in `golang:1.25` container
**Agent Readiness**: HIGH
