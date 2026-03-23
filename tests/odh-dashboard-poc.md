# Test Context: odh-dashboard-poc

## Overview

**Repository:** opendatahub-io/odh-dashboard-poc
**Languages:** Go
**Build System:** go modules + Makefile
**Agent Readiness:** **low** - Tests exist but have compilation errors preventing execution. No CI configuration.

This is a minimal Go HTTP API backend with a single test file that currently cannot run due to code errors. The repository structure suggests a planned monorepo with multiple dashboard components, but only `dashboard-model-registry/backend` contains actual implementation code.

## Container Recipe

This recipe provides a complete, step-by-step process to validate patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-odh-dashboard-poc \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.22 \
  sleep infinity
```

> **Note:** Use `docker` instead of `podman` if podman is not available. The golang:1.22 image already includes `make`.

### 2. Install Dependencies

```bash
podman exec test-context-odh-dashboard-poc bash -c \
  "cd /app/dashboard-model-registry/backend && go mod download"
```

**Expected:** No output on success. Downloads all Go module dependencies.

### 3. Verify Dependencies

```bash
podman exec test-context-odh-dashboard-poc bash -c \
  "cd /app/dashboard-model-registry/backend && go mod tidy && go mod verify"
```

**Expected output:**
```
all modules verified
```

**Validation result:** ✓ SUCCESS

### 4. Run Linting - go fmt

```bash
podman exec test-context-odh-dashboard-poc bash -c \
  "cd /app/dashboard-model-registry/backend && go fmt ./..."
```

**Expected:** No output if all files are already formatted.

**Validation result:** ✓ SUCCESS (no files needed formatting)

### 5. Run Linting - go vet

```bash
podman exec test-context-odh-dashboard-poc bash -c \
  "cd /app/dashboard-model-registry/backend && go vet ./..."
```

**Expected:** Exit code 0 if no issues found.

**Validation result:** ✗ FAILED

**Error output:**
```
# github.com/opendatahub-io/odh-dashboard-poc/dashboard-model-registry/internal/application
vet: internal/application/healthcheck__handler_test.go:23:30: not enough arguments in call to app.HealthcheckHandler
	have (*httptest.ResponseRecorder, *http.Request)
	want (http.ResponseWriter, *http.Request, httprouter.Params)
```

**Issue:** The test file calls `HealthcheckHandler` with 2 arguments but the function expects 3 (the handler signature uses `httprouter` which requires a `httprouter.Params` third argument).

### 6. Run Tests

```bash
podman exec test-context-odh-dashboard-poc bash -c \
  "cd /app/dashboard-model-registry/backend && go test -race -vet=off ./..."
```

**Validation result:** ✗ FAILED (compilation error)

**Error output:**
```
# github.com/opendatahub-io/odh-dashboard-poc/dashboard-model-registry/internal/application
internal/application/healthcheck__handler_test.go:23:29: not enough arguments in call to app.HealthcheckHandler
	have (*httptest.ResponseRecorder, *http.Request)
	want (http.ResponseWriter, *http.Request, httprouter.Params)
FAIL	github.com/opendatahub-io/odh-dashboard-poc/dashboard-model-registry/internal/application [build failed]
```

**Issue:** Same as go vet - test compilation fails due to wrong function signature.

### 7. Run Single Test File

If the test file is fixed, you can run a single test file:

```bash
podman exec test-context-odh-dashboard-poc bash -c \
  "cd /app/dashboard-model-registry/backend && go test -race -vet=off ./internal/application/healthcheck__handler_test.go"
```

### 8. Run Single Test by Name

To run a specific test function:

```bash
podman exec test-context-odh-dashboard-poc bash -c \
  "cd /app/dashboard-model-registry/backend && go test -race -vet=off ./... -run TestHealthcheckHandler"
```

### 9. Run with Coverage

```bash
podman exec test-context-odh-dashboard-poc bash -c \
  "cd /app/dashboard-model-registry/backend && go test -race -vet=off -cover ./..."
```

### 10. Cleanup

**Always** remove the container when done:

```bash
podman rm -f test-context-odh-dashboard-poc
```

## Validation Results

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install | `go mod download` | ✓ PASS | Dependencies installed |
| Verify | `go mod tidy && go mod verify` | ✓ PASS | All modules verified |
| Format | `go fmt ./...` | ✓ PASS | No files needed formatting |
| Vet | `go vet ./...` | ✗ FAIL | Found error in test file |
| Test | `go test -race -vet=off ./...` | ✗ FAIL | Compilation error |

**Summary:** Dependencies install cleanly, code formatting is correct, but the test suite has a compilation error preventing execution.

## CI/CD

**Status:** No CI configuration found.

**Missing:**
- No `.github/workflows/` directory
- No Tekton pipelines
- No Jenkinsfile
- No other CI system detected

**Impact:** There are no automated checks running on pull requests or commits. An agent cannot determine what checks must pass before merge.

## Conventions

### Test File Naming
- Pattern: `*_test.go`
- Example: `healthcheck__handler_test.go` (note: double underscore appears to be a typo)

### Test Function Naming
- Pattern: `TestFunctionName(t *testing.T)`
- Example: `TestHealthcheckHandler`

### Package Structure
```
dashboard-model-registry/backend/
├── cmd/              # Application entrypoints
│   ├── config/       # Configuration
│   └── root/         # Main application
└── internal/         # Private application code
    ├── application/  # HTTP handlers and routing
    ├── data/         # Data models
    ├── integrations/ # External integrations (k8s, http)
    ├── utils/        # Helper utilities
    └── validation/   # Input validation
```

### Import Style
Full module paths: `github.com/opendatahub-io/odh-dashboard-poc/dashboard-model-registry/internal/application`

## Gaps & Caveats

### Critical Issues

1. **Broken Test Suite**
   - The only test file has a compilation error
   - Test calls `app.HealthcheckHandler(rr, r)` but should call `app.HealthcheckHandler(rr, r, httprouter.Params{})`
   - Tests cannot run until this is fixed

2. **No CI/CD**
   - No automated testing or linting on pull requests
   - No way to determine what checks are required for merge
   - Agents cannot validate patches against CI requirements

### Coverage Issues

3. **Minimal Test Coverage**
   - Only 1 test file (`healthcheck__handler_test.go`)
   - 19 total Go source files
   - Most packages have `[no test files]`
   - No integration or end-to-end tests

4. **No Advanced Linting**
   - Only basic `go fmt` and `go vet`
   - No `golangci-lint` configuration
   - No pre-commit hooks

### Repository Structure

5. **Mostly Empty Repository**
   - `dashboard-appshell/backend/` - empty (only README)
   - `dashboard-appshell/frontend/` - empty (only README)
   - `dashboard-model-registry/frontend/` - empty (only README)
   - Only `dashboard-model-registry/backend/` has implementation code

6. **No Code Coverage Requirements**
   - No coverage thresholds defined
   - No coverage reporting in place

## What Works

Despite the gaps, the following aspects are functional:

- ✓ Go module dependency management works correctly
- ✓ Code formatting is consistent (go fmt passes)
- ✓ Project structure follows Go conventions
- ✓ Basic Makefile targets exist (`run`, `audit`)
- ✓ Test infrastructure is present (just needs bug fix)

## Recommended Fixes

For an agent working on this repository:

1. **Fix the test file** - Add `httprouter.Params{}` as the third argument to `HealthcheckHandler` calls
2. **Add CI configuration** - Create `.github/workflows/ci.yml` with lint and test jobs
3. **Add golangci-lint** - Configure comprehensive linting
4. **Expand test coverage** - Add tests for other handlers and packages
5. **Add integration tests** - Test the full HTTP API

## Quick Reference

### Validate a Patch

```bash
# Start container
podman run -d --name test-context-odh-dashboard-poc -v $(pwd):/app:Z -w /app golang:1.22 sleep infinity

# Install deps
podman exec test-context-odh-dashboard-poc bash -c "cd /app/dashboard-model-registry/backend && go mod download"

# Run checks (will fail until test is fixed)
podman exec test-context-odh-dashboard-poc bash -c "cd /app/dashboard-model-registry/backend && go fmt ./... && go vet ./..."

# Cleanup
podman rm -f test-context-odh-dashboard-poc
```

### Working Directory

All commands must run in: `dashboard-model-registry/backend/`

### Exit Codes

- `go fmt ./...` - Returns 0 if successful, lists files if changes made
- `go vet ./...` - Returns 0 if no issues, 1 if issues found
- `go test ./...` - Returns 0 if all tests pass, 1 if any fail or won't compile
