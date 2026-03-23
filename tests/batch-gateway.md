# Test Context: batch-gateway

**Repository:** opendatahub-io/batch-gateway
**Language:** Go 1.25.0
**Build System:** Makefile + Go modules
**Agent Readiness:** **HIGH** - Lint and test commands fully validated in container

---

## Overview

Batch Gateway is a high-performance system for processing large-scale batch inference jobs in Kubernetes environments. It provides an OpenAI-compatible API with two main binaries: `batch-gateway-apiserver` and `batch-gateway-processor`.

**Why HIGH readiness?**
- All dependencies install cleanly in golang:1.25 container
- Build succeeds for both binaries
- Golangci-lint runs successfully (finds legitimate code issues to fix)
- All 206 unit tests pass with race detector enabled
- Clear, executable commands for every validation step

**Caveats:**
- Golangci-lint found ~15 errcheck violations (code quality issues, not blocking)
- Integration tests require mock servers (not validated)
- E2E tests require deployed cluster (not validated)

---

## Container Recipe

This recipe provides a **complete, copy-paste workflow** for validating patches in an isolated container.

### 1. Start Container

```bash
# Using podman (or replace with docker)
podman run -d --name test-context-batch-gateway \
  -v /path/to/batch-gateway:/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

Replace `/path/to/batch-gateway` with your actual repository path.

### 2. Install System Dependencies

```bash
podman exec test-context-batch-gateway bash -c \
  "apt-get update && apt-get install -y make git"
```

**Expected:** Make and git are already present in golang:1.25 (Debian-based).

### 3. Install Go Dependencies

```bash
podman exec test-context-batch-gateway bash -c \
  "cd /app && go mod download"
```

**Expected:** Silent success (no output). Downloads ~50 dependencies.

**Validation result:** ✅ Passed (exit code 0)

### 4. Build Project

```bash
podman exec test-context-batch-gateway bash -c \
  "cd /app && make build"
```

**Expected output:**
```
Building batch-gateway-apiserver...
Binary built at ./bin/batch-gateway-apiserver
Building batch-gateway-processor...
Binary built at ./bin/batch-gateway-processor
All binaries built successfully
```

**Validation result:** ✅ Passed (exit code 0)

### 5. Install Linter

```bash
podman exec test-context-batch-gateway bash -c \
  "cd /app && go install github.com/golangci/golangci-lint/cmd/golangci-lint@v1.63.4"
```

**Expected:** Downloads and installs golangci-lint to `/go/bin/`. Takes ~30 seconds.

**Validation result:** ✅ Passed (exit code 0)

### 6. Run Linting

```bash
podman exec test-context-batch-gateway bash -c \
  "cd /app && /go/bin/golangci-lint run ./..."
```

**Expected:** Linter runs and reports code issues. Exit code 1 = violations found.

**Sample output:**
```
pkg/clients/http/http_client_test.go:157:28: Error return value of `(*encoding/json.Encoder).Encode` is not checked (errcheck)
internal/database/redis/redis_ds_client_test.go:1276:23: Error return value of `exchClient.PQEnqueue` is not checked (errcheck)
cmd/batch-processor/main.go:63:10: Error return value of `fs.Parse` is not checked (errcheck)
```

**Validation result:** ⚠️ Linter works correctly, found 15+ legitimate errcheck violations

**Interpretation:** The linter is functioning properly. These are real code quality issues (unchecked error returns) that should be fixed, but they don't prevent patch validation. A patch that introduces new unchecked errors would be caught.

**Alternative lint commands:**
```bash
# Run go fmt
podman exec test-context-batch-gateway bash -c "cd /app && go fmt ./..."

# Run go vet
podman exec test-context-batch-gateway bash -c "cd /app && go vet ./..."

# Or use Makefile targets
podman exec test-context-batch-gateway bash -c "cd /app && make lint"
podman exec test-context-batch-gateway bash -c "cd /app && make fmt"
podman exec test-context-batch-gateway bash -c "cd /app && make vet"
```

### 7. Run Tests

```bash
podman exec test-context-batch-gateway bash -c \
  "cd /app && timeout 300 go test -race -v ./... 2>&1"
```

**Expected:** All 206 tests pass. Takes ~30 seconds. Race detector enabled.

**Validation result:** ✅ All tests passed (exit code 0)

**Test summary:**
- 206 individual test cases
- Packages: internal/apiserver/batch, internal/database/postgresql, internal/database/redis, internal/files_store/fs, internal/files_store/s3, internal/processor/*, pkg/clients/*
- All tests use table-driven patterns with subtests

**Run a single package:**
```bash
podman exec test-context-batch-gateway bash -c \
  "cd /app && go test -race ./internal/apiserver/batch/..."
```

**Run a single test:**
```bash
podman exec test-context-batch-gateway bash -c \
  "cd /app && go test -race -run '^TestBatchHandler$' ./internal/apiserver/batch/..."
```

**Using Makefile:**
```bash
# Run tests with summary
podman exec test-context-batch-gateway bash -c "cd /app && make test"

# Run with coverage
podman exec test-context-batch-gateway bash -c "cd /app && make test-coverage"

# Run benchmarks
podman exec test-context-batch-gateway bash -c "cd /app && make bench"
```

### 8. Integration Tests (Optional - Requires Mock Servers)

Integration tests use the `//go:build integration` tag and spawn their own mock inference servers:

```bash
podman exec test-context-batch-gateway bash -c \
  "cd /app && go test -v -tags=integration ./internal/inference/..."
```

**Note:** Not validated in basic container - these tests start HTTP mock servers but should work.

**Or use Makefile:**
```bash
podman exec test-context-batch-gateway bash -c "cd /app && make test-integration"
```

### 9. E2E Tests (Requires Deployed Cluster)

E2E tests require a live batch-gateway deployment:

```bash
# Set TEST_BASE_URL to your deployed instance
podman exec test-context-batch-gateway bash -c \
  "cd /app/test/e2e && TEST_BASE_URL=http://localhost:8080 go test -v -count=1 ./..."
```

**Note:** Not validated - requires actual cluster deployment.

### 10. Cleanup

**Always clean up the container when done:**

```bash
podman rm -f test-context-batch-gateway
```

---

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `go mod download` | 0 | ✅ Pass | Silent success |
| Build | `make build` | 0 | ✅ Pass | Both binaries built |
| Install linter | `go install golangci-lint@v1.63.4` | 0 | ✅ Pass | Installed to /go/bin |
| Lint | `golangci-lint run ./...` | 1 | ⚠️ Issues found | 15+ errcheck violations (legitimate) |
| Format | `go fmt ./...` | 0 | ✅ Pass | No formatting issues |
| Vet | `go vet ./...` | 0 | ✅ Pass | No issues |
| Test | `go test -race -v ./...` | 0 | ✅ Pass | 206 tests passed |

**Summary:** Install OK, build OK, lint OK (found code quality issues), tests OK (206/206 passed)

---

## CI/CD

### GitHub Actions Workflows

**Gating Check: Pre-commit** (`.github/workflows/pre-commit.yml`)
- **Trigger:** `pull_request_target` (runs on all PRs)
- **Go version:** 1.25 (from go.mod)
- **Action:** `j178/prek-action@v1` runs all pre-commit hooks
- **Commands executed:**
  1. `trailing-whitespace` - remove trailing whitespace
  2. `end-of-file-fixer` - ensure files end with newline
  3. `check-yaml` - validate YAML syntax
  4. `check-added-large-files` - prevent large file commits
  5. `check-merge-conflict` - detect merge conflict markers
  6. `check-case-conflict` - detect case-insensitive filename conflicts
  7. `go-fmt` - format Go code
  8. `go-unit-tests` - run `go test ./...`
  9. `go-build` - build all packages
  10. `go-mod-tidy` - ensure go.mod is tidy
  11. `golangci-lint --timeout=5m` - run linter

**Advisory: Docker Build** (`.github/workflows/docker.yml`)
- **Trigger:** `push` to main, tags (not PRs)
- **Commands:**
  - Uses `docker/bake-action@v7` with `docker-bake.hcl`
  - Builds multi-arch images: apiserver and processor
  - Pushes to `ghcr.io/llm-d-incubation/batch-gateway-{apiserver,processor}`

**Prow Commands** (`.github/workflows/prow-github.yml`)
- Provides `/lgtm`, `/approve`, etc. commands for PRs
- Uses reusable workflow from `llm-d/llm-d-infra`

### Required Status Checks

The **pre-commit** workflow is the primary gating check. PRs must pass:
- All linting (golangci-lint)
- All formatting (go fmt)
- All unit tests (go test)
- Build validation (go build)
- Go module tidiness (go mod tidy)

---

## Conventions

### Test Files
- **Pattern:** `*_test.go`
- **Location:** Adjacent to source files in same package
- **Naming:** `TestFunctionName` for test functions
- **Style:** Table-driven tests with `t.Run()` for subtests

### Test Types
1. **Unit tests:** Default (no build tag or `//go:build !integration`)
2. **Integration tests:** `//go:build integration` tag
3. **E2E tests:** Located in `test/e2e/` directory

### Project Layout
```
batch-gateway/
├── cmd/
│   ├── apiserver/          # API server binary
│   └── batch-processor/    # Processor binary
├── internal/               # Private application code
│   ├── apiserver/         # API server implementation
│   ├── database/          # Database clients (postgresql, redis)
│   ├── files_store/       # File storage (s3, filesystem)
│   ├── processor/         # Batch processor logic
│   └── util/              # Utilities
├── pkg/                    # Public libraries
│   └── clients/           # HTTP and inference clients
├── test/
│   └── e2e/               # E2E tests
├── charts/                # Helm charts
├── docker/                # Dockerfiles
└── scripts/               # Build and deploy scripts
```

### Import Style
Standard Go import grouping:
1. Standard library
2. External packages
3. Internal packages

### Logging
Uses `k8s.io/klog/v2` for structured logging.

---

## Gaps & Caveats

### Known Gaps

1. **Linting violations exist:** Golangci-lint found ~15 errcheck violations (unchecked error returns in test files and main.go). These are legitimate code quality issues that should be addressed but don't prevent patch validation.

2. **Integration tests not validated:** Tests with `//go:build integration` tag require running mock servers. They should work but weren't validated in the container environment.

3. **E2E tests require infrastructure:** Tests in `test/e2e/` require a deployed batch-gateway instance with PostgreSQL, Redis, and S3 backends. Cannot be run in a basic container.

4. **No custom golangci-lint config:** The project uses golangci-lint default configuration (no `.golangci.yml` file). This means the linter rules are not explicitly documented.

5. **Pre-commit framework not validated:** The `.pre-commit-config.yaml` hooks were not validated in the container (would require installing the pre-commit framework). However, the individual commands they execute were validated.

### Workarounds for Patch Validation

An agent validating patches should:

1. **For linting:** Run `golangci-lint run ./...` and check that the patch doesn't introduce NEW violations. Existing violations can be ignored.

2. **For tests:** Run unit tests only (`go test -race ./...`). Integration and E2E tests require infrastructure not available in basic validation.

3. **For builds:** Both binaries must build successfully (`make build`).

4. **For formatting:** Code must pass `go fmt ./...` and `go vet ./...`.

### Infrastructure Requirements (Not in Basic Container)

- **Integration tests:** Mock HTTP servers (spawn automatically)
- **E2E tests:**
  - PostgreSQL database
  - Redis instance
  - S3-compatible storage
  - Deployed batch-gateway apiserver
  - Kubernetes cluster (for full deployment testing)

---

## Quick Command Reference

```bash
# Install dependencies
go mod download

# Build all binaries
make build

# Lint
golangci-lint run ./...
# or
make lint

# Format
go fmt ./...
# or
make fmt

# Vet
go vet ./...
# or
make vet

# Test (unit only)
go test -race -v ./...
# or
make test

# Test (with coverage)
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
# or
make test-coverage

# Test (single package)
go test -race ./internal/apiserver/batch/...

# Test (single test)
go test -race -run '^TestBatchHandler$' ./internal/apiserver/batch/...

# Integration tests
go test -v -tags=integration ./internal/inference/...
# or
make test-integration

# E2E tests (requires deployed instance)
cd test/e2e && TEST_BASE_URL=http://localhost:8080 go test -v -count=1 ./...
# or
make test-e2e

# All CI checks
make ci
# Equivalent to: make fmt vet lint test

# Clean
make clean
```

---

## Patch Validation Workflow

For an agent validating a patch against this repository:

1. **Setup** (one-time):
   ```bash
   podman run -d --name validator -v /path/to/repo:/app:Z -w /app golang:1.25 sleep infinity
   podman exec validator bash -c "go mod download"
   podman exec validator bash -c "go install github.com/golangci/golangci-lint/cmd/golangci-lint@v1.63.4"
   ```

2. **Validate patch**:
   ```bash
   # Apply patch to repo (outside container)
   cd /path/to/repo && git apply patch.diff

   # Build
   podman exec validator bash -c "cd /app && make build"

   # Lint (check for NEW violations only)
   podman exec validator bash -c "cd /app && /go/bin/golangci-lint run ./..."

   # Test
   podman exec validator bash -c "cd /app && go test -race ./..."
   ```

3. **Cleanup**:
   ```bash
   podman rm -f validator
   ```

**Pass criteria:**
- Build succeeds (exit code 0)
- Tests pass (exit code 0)
- Lint doesn't introduce new violations (compare before/after)
- Code is formatted (go fmt returns no changes)

---

## Additional Notes

- **Go version:** 1.25.0 is cutting-edge (as of 2026-03-22). Ensure your container image supports it.
- **Race detector:** Tests use `-race` flag to detect data races. This increases test runtime but is valuable for concurrent code.
- **Build optimization:** Binaries use `-ldflags '-s -w'` to strip debug info and reduce size.
- **Container tool:** Works with both `podman` and `docker` - just replace in commands.
- **Makefile:** Provides convenient targets but all can be done with raw Go commands.
- **Pre-commit hooks:** Configured but not required to validate patches - just run the individual commands.

---

**Generated:** 2026-03-22T21:38:57Z
**Confidence:** HIGH
**Agent Readiness:** HIGH
