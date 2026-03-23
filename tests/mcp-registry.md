# Test Context for mcp-registry

**Generated:** 2026-03-22T19:03:00-04:00

## Overview

**Repository:** opendatahub-io/mcp-registry
**Language:** Go 1.23.x
**Build System:** Go modules
**Agent Readiness:** **HIGH** - All lint and test commands validated successfully in container

The mcp-registry is a Go-based API service for the Model Context Protocol. It has comprehensive linting (70+ enabled linters), complete test coverage with both unit and integration tests, and all validation commands work perfectly in a standard golang:1.23 container with no external dependencies required for testing.

---

## Container Recipe

This is the complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-mcp-registry \
  -v /path/to/mcp-registry:/app:Z \
  -w /app \
  golang:1.23 \
  sleep infinity
```

Replace `/path/to/mcp-registry` with the absolute path to the repository.

### 2. Install Dependencies

```bash
podman exec test-context-mcp-registry bash -c "cd /app && go mod download"
```

**Validation result:** ✅ Success (exit code 0)

### 3. Install golangci-lint

```bash
podman exec test-context-mcp-registry bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v1.61.0"
```

**Validation result:** ✅ Success (golangci-lint v1.61.0 installed)

### 4. Build Application

```bash
podman exec test-context-mcp-registry bash -c "cd /app && go build ./cmd/registry"
```

**Validation result:** ✅ Success (binary built)

### 5. Run Linters

**Run golangci-lint:**
```bash
podman exec test-context-mcp-registry bash -c "cd /app && golangci-lint run --timeout=5m"
```

**Validation result:** ✅ Success (0 issues found)

**Check formatting:**
```bash
podman exec test-context-mcp-registry bash -c "cd /app && gofmt -s -l ."
```

**Validation result:** ✅ Success (0 files need formatting)

**Fix formatting (if needed):**
```bash
podman exec test-context-mcp-registry bash -c "cd /app && gofmt -s -w ."
```

### 6. Run Unit Tests

```bash
podman exec test-context-mcp-registry bash -c \
  "cd /app && go test -v -race -coverprofile=coverage.out -covermode=atomic ./internal/..."
```

**Validation result:** ✅ Success (18+ tests passed)
**Tests run:**
- TestHealthHandler (2 subtests + integration test)
- TestPublishHandler (12 subtests)
- TestPublishHandlerBearerTokenParsing (4 subtests)
- TestPublishHandlerAuthMethodSelection (4 subtests)
- TestServersHandler (9 subtests + 2 integration tests)

### 7. Run Integration Tests

**Using the test script:**
```bash
podman exec test-context-mcp-registry bash -c \
  "cd /app && chmod +x ./integrationtests/run_tests.sh && ./integrationtests/run_tests.sh"
```

**Validation result:** ✅ Success (13 tests passed)

**Or with coverage:**
```bash
podman exec test-context-mcp-registry bash -c \
  "cd /app && go test -v -race -coverprofile=integration-coverage.out -covermode=atomic ./integrationtests/..."
```

**Validation result:** ✅ Success (13 tests passed)

**Tests run:**
- TestPublishIntegration (10 subtests)
- TestPublishIntegrationWithComplexPackages (1 subtest)
- TestPublishIntegrationEndToEnd (1 subtest)

### 8. Run Single Test File

```bash
podman exec test-context-mcp-registry bash -c \
  "cd /app && go test -v ./internal/api/handlers/v0/health_test.go"
```

**Validation result:** ✅ Success

### 9. Run Single Test by Name

```bash
podman exec test-context-mcp-registry bash -c \
  "cd /app && go test -v -run 'TestHealthHandler' ./internal/api/handlers/v0/..."
```

**Validation result:** ✅ Success

**Run specific subtest:**
```bash
podman exec test-context-mcp-registry bash -c \
  "cd /app && go test -v -run 'TestHealthHandler/returns_health_status_with_github_client_id' ./internal/api/handlers/v0/..."
```

### 10. Cleanup

```bash
podman rm -f test-context-mcp-registry
```

---

## Validation Results

All commands were validated in a `golang:1.23` container:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install | `go mod download` | ✅ Pass | Dependencies installed cleanly |
| Build | `go build ./cmd/registry` | ✅ Pass | Binary built successfully |
| Lint Install | Install golangci-lint v1.61.0 | ✅ Pass | Linter installed |
| Lint | `golangci-lint run --timeout=5m` | ✅ Pass | 0 issues found |
| Format Check | `gofmt -s -l .` | ✅ Pass | 0 files need formatting |
| Unit Tests | `go test ./internal/...` | ✅ Pass | 18+ tests passed |
| Integration Tests | `./integrationtests/run_tests.sh` | ✅ Pass | 13 tests passed |
| Single File Test | `go test health_test.go` | ✅ Pass | Works correctly |
| Single Test Run | `go test -run TestHealthHandler` | ✅ Pass | Pattern matching works |

**Summary:** All validation steps passed. No external dependencies (MongoDB, etc.) required for testing - tests use in-memory database.

---

## CI/CD

### GitHub Actions Workflows

The repository has three GitHub Actions workflows that run on push and pull requests to `main` and `develop` branches:

**1. ci.yml - Main CI Pipeline**

Gating checks (all required):
```bash
# Lint
golangci-lint run --timeout=5m

# Format check
gofmt -s -l .

# Build
go build -v ./cmd/...

# Vulnerability scan
govulncheck ./...

# Unit tests
go test -v -race -coverprofile=coverage.out -covermode=atomic ./internal/...

# Integration tests
chmod +x ./integrationtests/run_tests.sh
./integrationtests/run_tests.sh
go test -v -race -coverprofile=integration-coverage.out -covermode=atomic ./integrationtests/...
```

**2. unit-tests.yml - Unit Test Workflow**

```bash
go mod download
go mod verify
go test -v -race -coverprofile=coverage.out -covermode=atomic ./internal/...
```

**3. integration-tests.yml - Integration Test Workflow**

```bash
go mod download
go mod verify
mkdir -p /tmp/test-data
chmod +x ./integrationtests/run_tests.sh
./integrationtests/run_tests.sh
go test -v -race -coverprofile=integration-coverage.out -covermode=atomic ./integrationtests/...
```

All workflows upload coverage to Codecov (advisory, not required).

### Tekton Pipelines

Additional CI configured in `.tekton/`:
- `mcp-registry-pull-request.yaml` - PR validation
- `mcp-registry-push.yaml` - Post-merge pipeline

---

## Linting Configuration

### golangci-lint (v1.61.0)

Config file: `.golangci.yml`

**70+ enabled linters including:**
- Standard: errcheck, gosimple, govet, ineffassign, staticcheck, typecheck, unused
- Security: gosec
- Style: gofmt, goimports, revive, stylecheck
- Complexity: cyclop, funlen, gocognit, gocyclo
- Best practices: errname, errorlint, bodyclose, contextcheck, misspell

**Timeout:** 5 minutes

**Test file exemptions:** Test files (`*_test.go`) have relaxed rules for:
- mnd (magic numbers)
- funlen (function length)
- gocyclo (cyclomatic complexity)
- errcheck (error checking)
- dupl (duplicate code)
- gosec (security)

**Command:**
```bash
golangci-lint run --timeout=5m
```

### gofmt

**Check formatting:**
```bash
gofmt -s -l .
```

**Fix formatting:**
```bash
gofmt -s -w .
```

---

## Testing

### Test Framework

- **Go testing package** with **testify/assert** for assertions
- **httptest** for HTTP handler testing
- **Table-driven tests** as standard pattern
- **Race detector** enabled for all test runs

### Test Structure

**Unit tests:** `./internal/api/handlers/v0/*_test.go`
- TestHealthHandler - health endpoint tests
- TestPublishHandler - publish endpoint tests
- TestServersHandler - server listing tests
- Uses external test packages (`package v0_test`)
- Uses httptest.NewRecorder for HTTP testing

**Integration tests:** `./integrationtests/publish_integration_test.go`
- TestPublishIntegration - full publish flow
- TestPublishIntegrationWithComplexPackages - complex configurations
- TestPublishIntegrationEndToEnd - end-to-end scenarios
- Uses in-memory database (no external services needed)

### Running Tests

**All tests:**
```bash
go test -v -race ./internal/... ./integrationtests/...
```

**Unit tests only:**
```bash
go test -v -race -coverprofile=coverage.out -covermode=atomic ./internal/...
```

**Integration tests only:**
```bash
./integrationtests/run_tests.sh
# or
go test -v -race ./integrationtests/...
```

**Single package:**
```bash
go test -v ./internal/api/handlers/v0/...
```

**Single test file:**
```bash
go test -v ./internal/api/handlers/v0/health_test.go
```

**Single test by name:**
```bash
go test -v -run TestHealthHandler ./internal/api/handlers/v0/...
```

**Single subtest:**
```bash
go test -v -run 'TestHealthHandler/returns_health_status_with_github_client_id' ./internal/api/handlers/v0/...
```

**With coverage:**
```bash
go test -race -coverprofile=coverage.out -covermode=atomic ./...
go tool cover -html=coverage.out -o coverage.html
```

### Test Patterns

**Table-driven tests:**
```go
testCases := []struct {
    name           string
    config         *config.Config
    expectedStatus int
    expectedBody   v0.HealthResponse
}{
    {
        name: "returns health status with github client id",
        config: &config.Config{...},
        expectedStatus: http.StatusOK,
        expectedBody: v0.HealthResponse{...},
    },
}

for _, tc := range testCases {
    t.Run(tc.name, func(t *testing.T) {
        // test implementation
    })
}
```

**HTTP handler testing:**
```go
req, err := http.NewRequestWithContext(context.Background(), http.MethodGet, "/health", nil)
rr := httptest.NewRecorder()
handler.ServeHTTP(rr, req)
assert.Equal(t, http.StatusOK, rr.Code)
```

---

## Build Configuration

### Go Version

**Required:** Go 1.23.0 or later (specified in `go.mod`)

### Build Commands

**Install dependencies:**
```bash
go mod download
```

**Verify dependencies:**
```bash
go mod verify
```

**Build binary:**
```bash
go build ./cmd/registry
```

**Build all commands:**
```bash
go build -v ./cmd/...
```

### Docker Build

**Dockerfile:** Multi-stage build using `golang:1.23-alpine` and `alpine:latest`

```bash
docker build -t registry .
```

**Run with docker-compose:**
```bash
docker compose up
```

This starts the registry service and MongoDB on port 8080.

---

## Conventions

### Test Files

- Pattern: `*_test.go`
- Location: Alongside source files or in `integrationtests/`
- Package naming: External test packages use `_test` suffix (e.g., `package v0_test`)

### Test Functions

- Naming: `Test*` (e.g., `TestHealthHandler`)
- Subtests: Use `t.Run(name, func(t *testing.T) {...})`
- Table-driven tests are the standard pattern

### Import Style

Managed by `gci` linter:
1. Standard library imports
2. Third-party packages
3. Local packages (github.com/modelcontextprotocol/registry/...)

### Package Structure

```
cmd/              # Application entry points (main.go files)
internal/         # Private application code
  ├── api/        # HTTP server and handlers
  ├── auth/       # Authentication logic
  ├── config/     # Configuration management
  ├── database/   # Database implementations
  ├── docs/       # Generated API docs
  ├── model/      # Data models
  └── service/    # Business logic
integrationtests/ # Integration test suite
tools/            # CLI utilities (publisher tool)
```

### Code Coverage

- Unit tests: Reported to Codecov
- Integration tests: Reported separately to Codecov
- No enforced coverage threshold
- Race detector enabled for all tests

---

## Gaps & Caveats

**None identified.** This repository has:
- ✅ Complete linting configuration
- ✅ Comprehensive unit and integration tests
- ✅ All tests self-contained (no external dependencies for testing)
- ✅ Clear CI configuration
- ✅ All commands validated successfully

The only external dependency for production is MongoDB, but tests use an in-memory database implementation, so patch validation can run in a simple Go container with no additional services.

---

## Quick Reference

**Fast validation (lint + test):**
```bash
# In container
go mod download
golangci-lint run --timeout=5m
go test -race ./internal/... ./integrationtests/...
```

**Expected results:**
- Dependencies: Downloads cleanly
- Lint: 0 issues
- Tests: All pass (31+ tests total)
- Time: ~30 seconds in container

**Agent readiness: HIGH** - All commands work perfectly, no infrastructure required.
