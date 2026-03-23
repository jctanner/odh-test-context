# Test Context: kube-auth-proxy

**Organization**: opendatahub-io
**Repository**: kube-auth-proxy
**Generated**: 2026-03-22T22:28:00Z

## Overview

Go 1.25.3 project using Makefile build system with golangci-lint for linting and Ginkgo/Gomega BDD testing framework. **Agent readiness: HIGH** - All core validation commands (deps, build, lint, test) work perfectly in a standard golang:1.25-bookworm container with 218 unit tests passing and 0 lint issues.

**Languages**: Go
**Build System**: Make + Go toolchain
**Test Framework**: Go testing + Ginkgo/Gomega BDD
**Linter**: golangci-lint v2.6.2

---

## Container Recipe

This section provides a **complete, step-by-step recipe** for validating patches in an isolated container. Each command is validated and ready to execute.

### 1. Start Container

```bash
podman run -d --name test-context-kube-auth-proxy \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.25-bookworm \
  sleep infinity
```

**Image**: `golang:1.25-bookworm`
**Rationale**: Matches the build image used in Dockerfile. Go 1.25.3 is specified in go.mod.

### 2. Install System Dependencies

```bash
podman exec test-context-kube-auth-proxy bash -c "apt-get update && apt-get install -y make git curl"
```

**Note**: These are pre-installed in golang:1.25-bookworm but listed for completeness.

### 3. Install Go Dependencies

```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && go mod download"
```

**Status**: ✅ Validated (exit code 0)
**Output**: Silent success (no output indicates success)

### 4. Install golangci-lint

```bash
podman exec test-context-kube-auth-proxy bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v2.6.2"
```

**Status**: ✅ Validated
**Version**: v2.6.2 (matches CI configuration)

### 5. Build Project

```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && make build"
```

**Status**: ✅ Validated (exit code 0)
**Output**:
```
CGO_ENABLED=0 go build -a -installsuffix cgo -ldflags="-X github.com/opendatahub-io/kube-auth-proxy/v1/pkg/version.VERSION=2.0.0-dev" -o kube-auth-proxy github.com/opendatahub-io/kube-auth-proxy/v1
```

**Artifacts**: Creates `kube-auth-proxy` binary in project root

### 6. Run Linter

```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && GO111MODULE=on golangci-lint run"
```

**Status**: ✅ Validated (exit code 0)
**Output**: `0 issues.`

**Auto-fix command** (not validated but available):
```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && GO111MODULE=on golangci-lint run --fix"
```

### 7. Run Unit Tests

```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && GO111MODULE=on go test -v -race ./..."
```

**Status**: ✅ Validated (exit code 0)
**Results**: 218 tests passed, 0 failures
**Runtime**: ~30 seconds

**Sample output**:
```
=== RUN   TestK8sTokenAuthentication_ValidToken
--- PASS: TestK8sTokenAuthentication_ValidToken (0.00s)
...
Running Suite: Main Suite - /app
SUCCESS! -- 218 Passed | 0 Failed | 0 Pending | 0 Skipped
```

**Alternative** (via Makefile, includes lint):
```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && make test"
```

### 8. Run Single Test File

```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && GO111MODULE=on go test -v -race {file}"
```

**Example**:
```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && GO111MODULE=on go test -v -race ./pkg/cookies/cookies_test.go"
```

### 9. Run Single Test Function

```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && GO111MODULE=on go test -v -race -run {test_name} ./..."
```

**Example** (run specific test):
```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && GO111MODULE=on go test -v -race -run TestK8sTokenAuthentication_ValidToken ./..."
```

### 10. Run Integration Tests

```bash
podman exec test-context-kube-auth-proxy bash -c "cd /app && GO111MODULE=on go test -tags integration -v -race ./..."
```

**Status**: ⚠️ Not validated (may require external services)
**Note**: Integration tests are excluded from default test run via `//go:build integration` build tag

### 11. Cleanup Container

```bash
podman rm -f test-context-kube-auth-proxy
```

---

## Validation Results

All commands were executed in a `golang:1.25-bookworm` container with the repository mounted at `/app`.

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install Deps | `go mod download` | 0 | ✅ Pass | Silent success |
| Build | `make build` | 0 | ✅ Pass | Binary created |
| Lint | `golangci-lint run` | 0 | ✅ Pass | 0 issues found |
| Test | `go test -v -race ./...` | 0 | ✅ Pass | 218 tests passed |
| Verify Generate | `make verify-generate` | 1 | ⚠️ Fail | Requires committed generated files |

**Summary**: Install OK, build OK, lint OK (0 issues), tests OK (218 passed). Code generation check requires generated files to be committed and in sync.

---

## CI/CD

### Primary CI: GitHub Actions

**Config**: `.github/workflows/ci.yml`
**Triggers**: Push and pull_request on all branches

#### Gating Checks (Required for Merge)

1. **Verify Code Generation**
   ```bash
   make verify-generate
   ```
   Ensures generated documentation matches code structs (uses go generate)

2. **Lint**
   ```bash
   golangci-lint run --timeout=5m
   ```
   Uses golangci-lint-action@v7 with version v2.6.2

3. **Build**
   ```bash
   make build
   ```
   Builds kube-auth-proxy binary

4. **Test**
   ```bash
   make test
   ```
   Runs `golangci-lint run && go test -v -race ./...` with coverage

5. **Docker Build**
   ```bash
   make build-docker
   ```
   Builds multi-arch Docker image (amd64 only for PRs, all archs for releases)

6. **FIPS Compliance** (`.github/workflows/fips-compliance.yml`, PRs to main only)
   ```bash
   docker build -f Dockerfile.redhat -t kube-auth-proxy:fips-test .
   check-payload scan local --path /tmp/container-fs
   ```
   Verifies FIPS compliance using OpenShift check-payload tool

#### Advisory Checks (Non-blocking)

- **CodeQL Analysis** (`.github/workflows/codeql.yml`): Security vulnerability scanning

### Secondary CI: Tekton (OpenShift CI)

**Config**: `.tekton/kube-auth-proxy-pull-request.yaml`, `.tekton/kube-auth-proxy-push.yaml`
**Purpose**: OpenShift-specific CI/CD pipelines

---

## Linting

### Configuration

**Tool**: golangci-lint v2.6.2
**Config File**: `.golangci.yml`

**Enabled Linters**:
- bodyclose
- copyloopvar
- dogsled
- goconst
- gocritic
- goprintffuncname
- gosec
- govet
- ineffassign
- misspell
- prealloc
- revive
- staticcheck
- unconvert
- unused

**Formatters**:
- gofmt
- goimports

**Exclusions**:
- Test files (`*_test.go`) have relaxed rules
- `third_party/` and `builtin/` directories excluded
- `examples/` directory excluded

### Commands

**Run linter**:
```bash
GO111MODULE=on golangci-lint run
```
or
```bash
make lint
```

**Auto-fix issues**:
```bash
GO111MODULE=on golangci-lint run --fix
```
or
```bash
make lint-fix
```

**Pre-commit hooks** (`.pre-commit-config.yaml`):
```bash
pre-commit run --all-files
```

---

## Testing

### Test Framework

**Primary**: Go standard testing + Ginkgo v2 BDD framework + Gomega matchers
**Total Tests**: 218 unit tests (validated)

### Test Organization

- **Unit tests**: Default (no build tags), run with `go test ./...`
- **Integration tests**: Tagged with `//go:build integration`, run with `go test -tags integration ./...`
- **Suite files**: `*_suite_test.go` files set up Ginkgo test suites per package

### Test Directories

```
.
├── *_test.go                          # Root-level tests
├── pkg/**/*_test.go                   # Package unit tests
├── kube-rbac-proxy/**/*_test.go      # RBAC proxy tests
└── test/integration/**/*_test.go     # Integration tests
```

### Running Tests

**All unit tests** (default, excludes integration):
```bash
GO111MODULE=on go test -v -race ./...
```

**With coverage**:
```bash
GO111MODULE=on go test -coverprofile=c.out -v -race ./...
```

**Via Makefile** (includes lint):
```bash
make test
```

**Integration tests only**:
```bash
GO111MODULE=on go test -tags integration -v -race ./...
```

**Single package**:
```bash
GO111MODULE=on go test -v -race ./pkg/cookies
```

**Single test file**:
```bash
GO111MODULE=on go test -v -race ./pkg/cookies/cookies_test.go
```

**Single test function**:
```bash
GO111MODULE=on go test -v -race -run TestCookieName ./...
```

**Ginkgo-specific single test** (by description):
```bash
GO111MODULE=on go test -v -race -ginkgo.focus="validates token"
```

### Test Infrastructure

**Mocking**:
- OIDC provider: `github.com/oauth2-proxy/mockoidc`
- Redis: `github.com/alicebob/miniredis/v2`

**Fixtures**: `testdata/` directory contains test configuration files

**Environment Variables**:
- `GO111MODULE=on` (required, enforces module mode)
- `COVER=true` (optional, enables coverage in Makefile)
- `CC_TEST_REPORTER_ID` (optional, for CodeClimate integration)

---

## Build

### Standard Build

```bash
make build
```

**Equivalent to**:
```bash
CGO_ENABLED=0 go build -a -installsuffix cgo \
  -ldflags="-X github.com/opendatahub-io/kube-auth-proxy/v1/pkg/version.VERSION=${VERSION}" \
  -o kube-auth-proxy \
  github.com/opendatahub-io/kube-auth-proxy/v1
```

**Output**: `kube-auth-proxy` binary in project root

### FIPS Build

```bash
make build-fips
```

**Equivalent to**:
```bash
CGO_ENABLED=1 GOEXPERIMENT=strictfipsruntime \
  go build -a -tags strictfipsruntime \
  -ldflags="-X github.com/opendatahub-io/kube-auth-proxy/v1/pkg/version.VERSION=${VERSION}" \
  -o kube-auth-proxy \
  github.com/opendatahub-io/kube-auth-proxy/v1
```

**Requirements**: CGO enabled, FIPS-compliant crypto libraries

### Container Build

**Standard multi-arch**:
```bash
make build-docker
```

**FIPS-compliant (Red Hat)**:
```bash
make build-docker-fips
```

**Base images**:
- Standard: `docker.io/library/golang:1.25-bookworm` (build), custom runtime
- FIPS: `registry.access.redhat.com/ubi9/go-toolset:1.25` (build), `ubi9/ubi-minimal` (runtime)

### Build Artifacts

1. `kube-auth-proxy` - Main OAuth2/OIDC proxy binary
2. `kube-rbac-proxy/_output/kube-rbac-proxy` - Embedded RBAC proxy
3. `entrypoint` - Container entrypoint (cmd/entrypoint)

---

## Conventions

### Test File Naming

- Pattern: `*_test.go`
- Suite files: `*_suite_test.go` (Ginkgo suite setup)
- Integration tests: `//go:build integration` build tag at top of file

### Test Function Naming

**Go standard tests**:
```go
func TestFunctionName(t *testing.T)
func TestFunctionName_Scenario(t *testing.T)  // Table-driven or sub-tests
```

**Ginkgo BDD tests**:
```go
Describe("Feature", func() {
    Context("when condition", func() {
        It("should do something", func() {
            // test code
        })
    })
})
```

### Import Style

Standard Go convention with grouped imports:
```go
import (
    // Standard library
    "fmt"
    "testing"

    // External dependencies
    "github.com/onsi/ginkgo/v2"
    "github.com/onsi/gomega"

    // Internal packages
    "github.com/opendatahub-io/kube-auth-proxy/v1/pkg/apis/options"
)
```

### Code Organization

```
.
├── cmd/                    # Command-line binaries
│   └── entrypoint/        # Container entrypoint
├── pkg/                    # Library code (public API)
│   ├── apis/              # API definitions
│   ├── authentication/    # Auth implementations
│   ├── cookies/           # Cookie handling
│   ├── middleware/        # HTTP middleware
│   ├── providers/         # OAuth/OIDC providers
│   └── sessions/          # Session management
├── providers/              # Provider configurations
├── kube-rbac-proxy/       # Embedded RBAC proxy subproject
├── test/integration/       # Integration tests
└── testdata/              # Test fixtures
```

---

## Gaps & Caveats

1. **Integration tests not validated**: Tests tagged with `//go:build integration` exist but were not validated. They may require external services (OIDC providers, Redis, Kubernetes API).

2. **verify-generate requires committed files**: The `make verify-generate` check fails in a clean container because generated documentation must be committed to the repository. The command works but expects generated files to match committed versions.

3. **FIPS compliance check not validated**: FIPS builds require OpenShift's `check-payload` tool which was not available during validation. Standard builds work perfectly.

4. **Multi-architecture builds not validated**: Only amd64 was tested. Project supports amd64, arm64, ppc64le, s390x but cross-compilation was not validated.

5. **kube-rbac-proxy subproject**: The embedded kube-rbac-proxy has its own tests but they were not separately validated. They run as part of `go test ./...`.

6. **No coverage threshold enforced**: While coverage is collected in CI, there's no configured minimum threshold.

---

## Quick Reference

### Patch Validation Workflow

```bash
# 1. Start container
podman run -d --name test-context-kube-auth-proxy \
  -v $(pwd):/app:Z -w /app golang:1.25-bookworm sleep infinity

# 2. Install tools
podman exec test-context-kube-auth-proxy bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v2.6.2"

# 3. Install dependencies
podman exec test-context-kube-auth-proxy bash -c "cd /app && go mod download"

# 4. Run lint
podman exec test-context-kube-auth-proxy bash -c "cd /app && GO111MODULE=on golangci-lint run"

# 5. Run tests
podman exec test-context-kube-auth-proxy bash -c "cd /app && GO111MODULE=on go test -v -race ./..."

# 6. Build
podman exec test-context-kube-auth-proxy bash -c "cd /app && make build"

# 7. Cleanup
podman rm -f test-context-kube-auth-proxy
```

### Local Development Commands

```bash
# Install dependencies
go mod download

# Build binary
make build

# Run linter
make lint

# Auto-fix lint issues
make lint-fix

# Run unit tests
make test

# Run tests with coverage
COVER=true make test

# Run integration tests
make test-integration

# Generate docs
make generate

# Verify generated docs
make verify-generate

# Build Docker image
make build-docker
```

---

## Agent Readiness: HIGH

**Rationale**: All core validation commands (dependency install, build, lint, test) work perfectly in a standard Go container with zero configuration. 218 unit tests pass, linter reports 0 issues, and builds complete successfully. The project uses modern Go tooling and follows best practices. Integration tests require build tags but unit tests provide comprehensive coverage.

**Confidence**: High

**Recommendation**: This repository is ready for automated patch validation. An agent can clone, patch, lint, test, and get clear pass/fail signals without any infrastructure dependencies.
