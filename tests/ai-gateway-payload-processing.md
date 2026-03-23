# Test Context: ai-gateway-payload-processing

**Agent Readiness: HIGH** — Lint and test commands validated successfully. An agent can clone, patch, lint, test, and get clear pass/fail signals. Dependencies install cleanly in a standard container.

## Overview

- **Languages:** Go 1.25.0
- **Build System:** Go modules + Make
- **Linting:** golangci-lint v2.9.0, go vet, go fmt
- **Testing:** Go test with testify, envtest for Kubernetes controller testing
- **CI:** GitHub Actions (PR checks on pull_request to main)
- **Test Packages:** 5 packages with tests (api-translation, anthropic, azureopenai, apikey_injection, model-provider-resolver)

## Container Recipe

This is the **complete, copy-paste recipe** for validating patches. Follow these steps exactly.

### 1. Start Container

```bash
podman run -d --name test-ai-gateway \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

Alternative with docker:
```bash
docker run -d --name test-ai-gateway \
  -v $(pwd):/app \
  -w /app \
  golang:1.25 \
  sleep infinity
```

### 2. Verify System Dependencies

```bash
podman exec test-ai-gateway bash -c "make --version && git --version"
```

Expected: make and git are pre-installed in golang:1.25 image.

### 3. Install Go Dependencies

```bash
podman exec test-ai-gateway bash -c "cd /app && go mod download"
```

Expected: No output, exit code 0. Downloads all dependencies from go.sum.

### 4. Run Linting

#### Full Lint (CI equivalent)

```bash
podman exec test-ai-gateway bash -c "cd /app && make lint"
```

Expected output:
```
Downloading github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.9.0
...
/app/bin/golangci-lint run --timeout 5m
0 issues.
```

Exit code 0 = lint passed. Non-zero = lint issues found (not necessarily a broken command).

#### Alternative: Run lint components separately

```bash
# Go vet (static analysis)
podman exec test-ai-gateway bash -c "cd /app && make vet"

# Go fmt (formatting check)
podman exec test-ai-gateway bash -c "cd /app && make fmt"
```

#### Fix Lint Issues

```bash
podman exec test-ai-gateway bash -c "cd /app && make lint-fix"
```

### 5. Run Tests

#### Full Test Suite (CI equivalent)

```bash
podman exec test-ai-gateway bash -c "cd /app && make test"
```

Expected output:
```
Downloading sigs.k8s.io/controller-runtime/tools/setup-envtest@release-0.19
...
ok  	github.com/opendatahub-io/ai-gateway-payload-processing/pkg/plugins/api-translation	1.047s
ok  	github.com/opendatahub-io/ai-gateway-payload-processing/pkg/plugins/api-translation/providers/anthropic	1.015s
ok  	github.com/opendatahub-io/ai-gateway-payload-processing/pkg/plugins/api-translation/providers/azureopenai	1.014s
ok  	github.com/opendatahub-io/ai-gateway-payload-processing/pkg/plugins/apikey_injection	1.483s
ok  	github.com/opendatahub-io/ai-gateway-payload-processing/pkg/plugins/model-provider-resolver	1.045s
```

Exit code 0 = all tests passed. First run downloads envtest (~30s).

#### Run Tests for a Single Package

```bash
podman exec test-ai-gateway bash -c "cd /app && go test ./pkg/plugins/api-translation/... -v"
```

#### Run a Single Test by Name

```bash
podman exec test-ai-gateway bash -c "cd /app && go test ./pkg/plugins/api-translation/... -run TestProcessRequest_NoProvider -v"
```

Template: `go test ./pkg/{package}/... -run {TestName} -v`

#### Run Tests with Coverage

```bash
podman exec test-ai-gateway bash -c "cd /app && make test-unit COVERAGE=true"
```

Prints per-function coverage, removes cover.out after.

### 6. Run Full Verification (CI equivalent)

```bash
podman exec test-ai-gateway bash -c "cd /app && make verify"
```

Runs: `tidy`, `vet`, `fmt`, `lint` in sequence. This is the full pre-merge check.

Expected output ends with:
```
0 issues.
```

Exit code 0 = all checks passed.

### 7. Cleanup

```bash
podman rm -f test-ai-gateway
```

## Validation Results

All commands validated in `golang:1.25` container on 2026-03-22:

| Step | Command | Exit Code | Result |
|------|---------|-----------|--------|
| Install | `go mod download` | 0 | ✅ Dependencies installed |
| Lint | `make lint` | 0 | ✅ 0 issues |
| Test | `make test` | 0 | ✅ All 5 packages passed |
| Verify | `make verify` | 0 | ✅ tidy, vet, fmt, lint all passed |

**Test Summary:**
- `pkg/plugins/api-translation`: 14 tests (plugin_test.go)
- `pkg/plugins/api-translation/providers/anthropic`: Multiple tests (anthropic_test.go)
- `pkg/plugins/api-translation/providers/azureopenai`: Multiple tests (azureopenai_test.go)
- `pkg/plugins/apikey_injection`: Multiple tests (plugin_test.go, reconciler_test.go, store_test.go)
- `pkg/plugins/model-provider-resolver`: Multiple tests (model_store_test.go, plugin_test.go)

## CI/CD

### GitHub Actions Workflows

**Gating Checks (required for merge to main):**

1. **`.github/workflows/ci-pr-checks.yaml`** — Triggered on `pull_request` and `push` to `main`
   - Runs only if Go source files changed (paths-filter)
   - Extracts Go version from go.mod
   - Executes:
     ```bash
     make verify  # tidy, vet, fmt, lint
     make test    # unit tests with envtest
     ```

2. **`.github/workflows/check-typos.yaml`** — Triggered on `pull_request` and `push`
   - Advisory check (typos in code/docs)
   - Uses: `crate-ci/typos@v1.44.0`

### Required Environment

- Go version: Extracted from `go.mod` (currently 1.25.0)
- No external services required (envtest simulates Kubernetes API)
- No secrets required for tests
- CGO_ENABLED=1 for race detection

## Conventions

### Test Files

- **Pattern:** `*_test.go` co-located with source in `pkg/` subdirectories
- **Naming:** `func TestXxx(t *testing.T)` — standard Go test convention
- **Assertions:** Uses `github.com/stretchr/testify/assert` and `testify/require`
- **Framework:** Standard Go testing + testify + envtest (for K8s controller testing)

### Test Examples

```go
// From pkg/plugins/api-translation/plugin_test.go
func TestProcessRequest_NoProvider(t *testing.T) {
    p := NewAPITranslationPlugin()
    req := framework.NewInferenceRequest()
    req.Body["model"] = "gpt-4o"
    err := p.ProcessRequest(context.Background(), framework.NewCycleState(), req)
    assert.NoError(t, err)
}
```

### Import Style

Standard Go imports, grouped:
1. Standard library
2. External dependencies
3. Internal packages (github.com/opendatahub-io/ai-gateway-payload-processing/...)

### Code Organization

```
pkg/
├── external-model/
│   ├── provider/
│   └── state/
└── plugins/
    ├── api-translation/
    │   ├── plugin.go
    │   ├── plugin_test.go
    │   └── providers/
    │       ├── anthropic/
    │       │   ├── anthropic.go
    │       │   └── anthropic_test.go
    │       └── azureopenai/
    │           ├── azureopenai.go
    │           └── azureopenai_test.go
    ├── apikey_injection/
    │   ├── plugin.go
    │   ├── plugin_test.go
    │   ├── reconciler.go
    │   ├── reconciler_test.go
    │   ├── store.go
    │   └── store_test.go
    └── model-provider-resolver/
        ├── model_store.go
        ├── model_store_test.go
        ├── plugin.go
        └── plugin_test.go
```

## Build

### Local Build

```bash
# Download dependencies
go mod download

# Build binary
go build -o ./bbr ./cmd

# Or build container image
make image-local-load
```

### Container Build

The Dockerfile uses multi-stage build:

1. **Builder stage** (`golang:1.25`):
   - Copies go.mod, go.sum
   - Runs `go mod download`
   - Copies source (`cmd/`, `pkg/`)
   - Builds binary: `go build -o /bbr ./cmd`

2. **Deploy stage** (`gcr.io/distroless/static:nonroot`):
   - Copies binary from builder
   - Runs as non-root
   - Entrypoint: `/bbr`

Build command:
```bash
docker buildx build -t quay.io/opendatahub-io/ai-gateway-payload-processing:latest \
  --build-arg BUILDER_IMAGE=golang:1.25 \
  --build-arg BASE_IMAGE=gcr.io/distroless/static:nonroot \
  --build-arg COMMIT_SHA=$(git rev-parse HEAD) \
  --build-arg BUILD_REF=$(git describe --tags --dirty --always) \
  ./
```

## Gaps & Caveats

**None.** All test and lint infrastructure is present and functional.

- ✅ Tests exist and run successfully
- ✅ Lint configured and passes
- ✅ CI configured and validates PRs
- ✅ No external infrastructure required (envtest simulates K8s)
- ✅ All dependencies available in public registries
- ✅ Clear pass/fail signals from all commands

## Quick Reference

### Essential Commands

```bash
# Full validation (what CI runs)
make verify && make test

# Lint only
make lint

# Test only
make test

# Fix lint issues
make lint-fix

# Test with coverage
make test-unit COVERAGE=true

# Run specific test
go test ./pkg/plugins/api-translation/... -run TestProcessRequest_NoProvider -v
```

### Makefile Targets

- `make fmt` — Run go fmt
- `make vet` — Run go vet
- `make lint` — Run golangci-lint
- `make lint-fix` — Run golangci-lint with --fix
- `make tidy` — Run go mod tidy
- `make verify` — Run tidy, vet, fmt, lint
- `make test` — Run unit tests (alias for test-unit)
- `make test-unit` — Run unit tests with envtest
- `make envtest` — Install setup-envtest tool
- `make golangci-lint` — Install golangci-lint tool

### Environment Variables

- `COVERAGE=true` — Enable coverage reporting in `make test-unit`
- `ENVTEST_K8S_VERSION=1.31.0` — Kubernetes version for envtest (default)
- `GO_VERSION` — Override Go version for container builds

## Agent Usage Pattern

For an AI agent validating a patch:

1. **Clone repo** (or it's already cloned)
2. **Apply patch** to working directory
3. **Start container:** `podman run -d --name test-ai-gateway -v $(pwd):/app:Z -w /app golang:1.25 sleep infinity`
4. **Install deps:** `podman exec test-ai-gateway bash -c "cd /app && go mod download"`
5. **Run verification:** `podman exec test-ai-gateway bash -c "cd /app && make verify"`
   - Exit code 0 = lint passed
   - Non-zero = lint issues (examine output for details)
6. **Run tests:** `podman exec test-ai-gateway bash -c "cd /app && make test"`
   - Exit code 0 = all tests passed
   - Non-zero = test failures (examine output for which tests failed)
7. **Cleanup:** `podman rm -f test-ai-gateway`
8. **Report:** Pass/fail based on exit codes from steps 5 and 6

**Expected runtime:** ~2-3 minutes first run (downloads tools), ~30-60 seconds subsequent runs.

**Success criteria:** Both `make verify` and `make test` exit with code 0.
