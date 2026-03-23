# Test Context: rhaii-cluster-validation

**Generated**: 2026-03-23T00:13:00Z
**Repository**: opendatahub-io/rhaii-cluster-validation
**Languages**: Go 1.25.0
**Build System**: Go modules + Makefile
**Agent Readiness**: **HIGH** - All lint and test commands validated successfully in a clean container.

---

## Overview

This is a Go project that provides a Kubernetes cluster validation agent for GPU, RDMA, and network checks. The project has comprehensive unit tests, strict linting configuration, and well-defined CI/CD pipelines. All validation commands have been tested in a golang:1.25 container and work correctly.

**Why HIGH readiness**: Dependencies install cleanly, build succeeds, linting passes with 0 issues, all 7 test packages pass (including with race detector enabled), and go.mod is properly maintained. An agent can clone, patch, lint, and test with clear pass/fail signals.

---

## Container Recipe

This is a **complete, copy-paste recipe** for validating patches in an isolated container.

### 1. Start Container

Use the official Go 1.25 image (matches go.mod version):

```bash
podman run -d --name validate-rhaii \
  -v /path/to/rhaii-cluster-validation:/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

Replace `/path/to/rhaii-cluster-validation` with the actual repository path.

If `podman` is not available, use `docker` instead.

### 2. Install System Dependencies

Install golangci-lint (linter used by CI):

```bash
podman exec validate-rhaii bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v2.11.3"
```

### 3. Install Project Dependencies

Download Go modules:

```bash
podman exec validate-rhaii bash -c "cd /app && go mod download"
```

**Expected result**: No output on success. Downloads all dependencies listed in go.mod/go.sum.

### 4. Build

Build the validator binary:

```bash
podman exec validate-rhaii bash -c "cd /app && CGO_ENABLED=0 go build -o bin/rhaii-validator ./cmd/agent/"
```

**Expected result**: No output on success. Creates `bin/rhaii-validator` binary (~36MB).

Verify the build:

```bash
podman exec validate-rhaii bash -c "cd /app && ./bin/rhaii-validator --version"
```

**Expected output**: `kubectl-rhaii_validate version dev`

### 5. Lint

Run golangci-lint (as CI does):

```bash
podman exec validate-rhaii bash -c "cd /app && golangci-lint run ./..."
```

**Expected result**: `0 issues.` (validated successfully)

Also check Go formatting:

```bash
podman exec validate-rhaii bash -c "cd /app && go fmt ./..."
```

**Expected result**: No output if all files are properly formatted.

### 6. Test

Run all unit tests with race detector (exact CI command):

```bash
podman exec validate-rhaii bash -c "cd /app && go test ./... -count=1 -race"
```

**Expected result**: All 7 packages pass:
- `pkg/checks/gpu`
- `pkg/checks/networking`
- `pkg/checks/rdma`
- `pkg/config`
- `pkg/controller`
- `pkg/jobrunner`
- `pkg/runner`

**Note**: Race detector adds ~1s per package (total runtime ~7-10s).

Run without race detector (faster):

```bash
podman exec validate-rhaii bash -c "cd /app && go test ./... -v"
```

### 7. Run Single Test File

Test a specific package:

```bash
podman exec validate-rhaii bash -c "cd /app && go test ./pkg/config -v"
```

### 8. Run Single Test

Test a specific test function:

```bash
podman exec validate-rhaii bash -c "cd /app && go test ./pkg/config -run TestLoad_DefaultsOnly -v"
```

**Pattern**: `go test ./{package} -run {TestFunctionName} -v`

### 9. Verify go.mod Tidy (CI requirement)

CI verifies that go.mod and go.sum are up to date:

```bash
podman exec validate-rhaii bash -c "cd /app && go mod tidy && git diff --exit-code go.mod go.sum"
```

**Expected result**: Exit code 0 (no changes). If there are changes, go.mod needs to be tidied.

### 10. Cleanup

Always remove the container when done:

```bash
podman rm -f validate-rhaii
```

---

## Validation Results

All commands were validated live in a golang:1.25 container:

| Step | Command | Exit Code | Result |
|------|---------|-----------|--------|
| Dependencies | `go mod download` | 0 | ✅ Success |
| Build | `CGO_ENABLED=0 go build -o bin/rhaii-validator ./cmd/agent/` | 0 | ✅ Success (36MB binary) |
| Lint | `golangci-lint run ./...` | 0 | ✅ Success (0 issues) |
| Tests (basic) | `go test ./... -count=1` | 0 | ✅ Success (7 packages) |
| Tests (race) | `go test ./... -count=1 -race` | 0 | ✅ Success (7 packages) |
| Verify tidy | `go mod tidy && git diff --exit-code go.mod go.sum` | 0 | ✅ Success (already tidy) |

**Output snippets**:

**Tests (basic)**:
```
ok  	github.com/opendatahub-io/rhaii-cluster-validation/pkg/checks/gpu	0.002s
ok  	github.com/opendatahub-io/rhaii-cluster-validation/pkg/checks/networking	0.009s
ok  	github.com/opendatahub-io/rhaii-cluster-validation/pkg/checks/rdma	0.008s
ok  	github.com/opendatahub-io/rhaii-cluster-validation/pkg/config	0.009s
ok  	github.com/opendatahub-io/rhaii-cluster-validation/pkg/controller	0.010s
ok  	github.com/opendatahub-io/rhaii-cluster-validation/pkg/jobrunner	0.007s
ok  	github.com/opendatahub-io/rhaii-cluster-validation/pkg/runner	0.002s
```

**Lint**:
```
0 issues.
```

---

## CI/CD

### GitHub Actions Workflows

The project uses GitHub Actions with two **gating workflows** (both trigger on `pull_request` to `main`):

#### 1. CI Workflow (`.github/workflows/ci.yaml`)

**Gating checks**:

```bash
# Build
make build

# Test with race detector
go test ./... -count=1 -race

# Lint
golangci-lint run ./...

# Verify go.mod is tidy
go mod tidy
git diff --exit-code go.mod go.sum
```

All four checks must pass for PR to merge.

#### 2. E2E Workflow (`.github/workflows/e2e.yaml`)

**Gating checks**:

```bash
# Build binary
make build

# Verify version flag works
./bin/rhaii-validator --version

# Run agent locally (expects check failures, validates no runtime errors)
./bin/rhaii-validator run --node-name ci-runner

# Build container image
docker build -t rhaii-validator:ci .

# Run container (expects check failures, validates no runtime errors)
docker run --rm rhaii-validator:ci run --node-name ci-container
```

**Note**: E2E tests expect exit code 1 (check failures) because CI runners have no GPU/RDMA hardware. What's validated is:
- No panics or runtime errors
- Valid JSON output structure
- Correct status values (`PASS`, `FAIL`, `WARN`, `SKIP`)

#### 3. Release Workflow (`.github/workflows/release.yaml`)

**Advisory only** (triggers on push/tags, not gating for PRs).

### Required Status Checks

For a PR to merge, both `CI / build-and-test` and `E2E / e2e-local` must pass.

---

## Conventions

### Test Files

**Pattern**: `*_test.go` (Go standard)

**Location**: Co-located with source files in `pkg/` subdirectories

**Examples**:
- `pkg/config/loader_test.go`
- `pkg/checks/gpu/driver_test.go`
- `pkg/checks/rdma/devices_test.go`

### Test Functions

**Naming**: `TestFunctionName` pattern (Go standard)

**Example**:
```go
func TestLoad_DefaultsOnly(t *testing.T) {
    cfg, err := Load(PlatformAKS, "")
    if err != nil {
        t.Fatalf("Load(AKS, '') returned error: %v", err)
    }
    // assertions...
}
```

### Import Style

Standard Go import grouping:
1. Standard library
2. External packages
3. Internal packages (from this repo)

No special import aliases or conventions.

### Project Layout

```
rhaii-cluster-validation/
├── cmd/agent/           # Main entrypoint (produces binary)
├── pkg/                 # Library code (all packages)
│   ├── checks/          # Validation checks (gpu, rdma, networking)
│   ├── config/          # Configuration loading
│   ├── controller/      # Kubernetes controller logic
│   ├── jobrunner/       # Job execution
│   └── runner/          # Main runner orchestration
├── deploy/              # Kubernetes manifests
├── test/                # Integration test docs
├── .github/workflows/   # CI/CD definitions
├── Makefile             # Build automation
├── go.mod / go.sum      # Go dependencies
└── .golangci.yml        # Linter config
```

---

## Gaps & Caveats

**None identified**. This project has:
- ✅ Comprehensive unit tests
- ✅ Well-defined linting
- ✅ Clear CI/CD requirements
- ✅ Standard Go conventions
- ✅ All commands validated in container

### What Works

- All dependencies install cleanly from standard Go module proxy
- Build produces working binary
- All unit tests pass (including race detector)
- Linting is clean
- go.mod is properly maintained

### Quirks

- **E2E tests expect failures**: The E2E workflow in CI expects exit code 1 because validation checks fail on runners without GPU/RDMA hardware. This is intentional - the tests verify the agent handles missing hardware gracefully and produces valid JSON output.

- **No mocking framework**: Tests use the standard Go testing package without external mocking libraries. File I/O tests use `t.TempDir()` for isolation.

- **golangci-lint config is minimal**: Only disables `errcheck` (intentional - `fmt.Fprintf` to output writers follows a logging pattern where errors are deliberately unchecked).

---

## Quick Reference

### Essential Commands

```bash
# Install deps
go mod download

# Build
CGO_ENABLED=0 go build -o bin/rhaii-validator ./cmd/agent/

# Lint
golangci-lint run ./...

# Test (CI version)
go test ./... -count=1 -race

# Test (faster, no race detector)
go test ./... -v

# Verify go.mod tidy
go mod tidy && git diff --exit-code go.mod go.sum
```

### Makefile Targets

The Makefile provides convenience wrappers:

```bash
make build       # Build binary
make test        # Run tests (without race detector)
make lint        # Run golangci-lint
make fmt         # Format code with go fmt
make container   # Build container image
```

**Note**: `make test` runs `go test ./... -v` (no `-race` flag). CI uses the explicit `go test ./... -count=1 -race` command.

---

## Agent Workflow Example

A downstream AI agent validating a patch would:

1. **Clone repo** (or use existing checkout)
2. **Start container**: `podman run -d --name validate-rhaii -v $(pwd):/app:Z -w /app golang:1.25 sleep infinity`
3. **Install golangci-lint**: `podman exec validate-rhaii bash -c "curl -sSfL ... | sh -s -- -b /usr/local/bin v2.11.3"`
4. **Apply patch**: (agent's patch application logic)
5. **Install deps**: `podman exec validate-rhaii bash -c "cd /app && go mod download"`
6. **Build**: `podman exec validate-rhaii bash -c "cd /app && CGO_ENABLED=0 go build -o bin/rhaii-validator ./cmd/agent/"`
7. **Lint**: `podman exec validate-rhaii bash -c "cd /app && golangci-lint run ./..."`
8. **Test**: `podman exec validate-rhaii bash -c "cd /app && go test ./... -count=1 -race"`
9. **Verify tidy**: `podman exec validate-rhaii bash -c "cd /app && go mod tidy && git diff --exit-code go.mod go.sum"`
10. **Report results**: Pass/fail based on exit codes
11. **Cleanup**: `podman rm -f validate-rhaii`

**Expected results**:
- Build: exit code 0
- Lint: exit code 0, output `0 issues.`
- Test: exit code 0, all packages `ok`
- Tidy: exit code 0 (no changes)

Any non-zero exit code indicates a problem with the patch.
