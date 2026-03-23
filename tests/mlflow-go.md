# Test Context: mlflow-go

**Organization:** opendatahub-io
**Repository:** mlflow-go
**Analyzed:** 2026-03-22T23:09:30Z

## Overview

MLflow Go SDK - A Go client library for MLflow tracking and prompt registry APIs.

- **Languages:** Go 1.24
- **Build System:** Makefile + Go modules
- **Agent Readiness:** **HIGH** — Lint and unit tests validated successfully in container. Integration tests require MLflow server but are fully automated in CI.
- **Confidence:** High

## Container Recipe

This is a complete, validated recipe for running lint and tests in a container. Every command below was tested and confirmed working.

### 1. Start Container

```bash
podman run -d \
  --name test-context-mlflow-go \
  -v /path/to/mlflow-go:/app:Z \
  -w /app \
  golang:1.24 \
  sleep infinity
```

Replace `/path/to/mlflow-go` with the absolute path to your repository clone.

### 2. Install System Dependencies

```bash
podman exec test-context-mlflow-go bash -c \
  "apt-get update -qq && apt-get install -y -qq make git curl"
```

**Validated:** ✅ Exit code 0

### 3. Install Go Dependencies

```bash
podman exec test-context-mlflow-go bash -c \
  "cd /app && go mod download && go mod tidy"
```

**Validated:** ✅ Exit code 0
Downloads `google.golang.org/protobuf` and other dependencies.

### 4. Run Linting

#### golangci-lint (comprehensive linting)

```bash
podman exec test-context-mlflow-go bash -c \
  "cd /app && make lint"
```

**Validated:** ✅ Exit code 0 — **0 issues found**

This command:
- Installs `golangci-lint` v2.1.6 to `bin/` (lazy install, cached after first run)
- Runs `golangci-lint run ./...`
- Checks: gocritic, gosec, misspell, prealloc, revive, unconvert, unparam
- Formatters: gofmt, goimports

#### go vet (standard Go static analysis)

```bash
podman exec test-context-mlflow-go bash -c \
  "cd /app && make vet"
```

**Validated:** ✅ Exit code 0 — no issues

Equivalent to: `go vet ./...`

#### Format Check

```bash
podman exec test-context-mlflow-go bash -c \
  "cd /app && gofmt -l ."
```

**Validated:** ✅ Exit code 0 — empty output (code is formatted)

If this returns any filenames, the code needs formatting. Fix with:

```bash
podman exec test-context-mlflow-go bash -c \
  "cd /app && make fmt"
```

#### Tidy Check

```bash
podman exec test-context-mlflow-go bash -c \
  "cd /app && go mod tidy && git diff --exit-code go.mod go.sum"
```

Ensures `go.mod` and `go.sum` are tidy. CI enforces this.

### 5. Run Unit Tests

```bash
podman exec test-context-mlflow-go bash -c \
  "cd /app && go test -v -race ./..."
```

**Validated:** ✅ Exit code 0 — **All tests passed**

Output summary:
- `internal/errors` — PASS (1.017s)
- `internal/transport` — PASS (1.242s)
- `mlflow` — PASS (1.025s)
- `mlflow/promptregistry` — PASS (1.075s)
- `mlflow/tracking` — PASS (1.059s)

Equivalent to: `make test/unit`

### 6. Run a Single Test File

```bash
podman exec test-context-mlflow-go bash -c \
  "cd /app && go test -v -race ./internal/errors/..."
```

Replace `./internal/errors/...` with your package path.

### 7. Run a Single Test

```bash
podman exec test-context-mlflow-go bash -c \
  "cd /app && go test -v -race -run TestAPIError_Error ./internal/errors/..."
```

Replace `TestAPIError_Error` with your test function name (regex supported).

### 8. Cleanup

```bash
podman rm -f test-context-mlflow-go
```

**Always run this** when done to remove the container.

## Validation Results

All commands validated in `golang:1.24` container:

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| System deps | `apt-get install make git curl` | 0 | ✅ PASS | Installed successfully |
| Go modules | `go mod download && go mod tidy` | 0 | ✅ PASS | All deps resolved |
| Lint | `make lint` | 0 | ✅ PASS | 0 issues |
| Vet | `make vet` | 0 | ✅ PASS | No issues |
| Format | `gofmt -l .` | 0 | ✅ PASS | Properly formatted |
| Unit tests | `go test -v -race ./...` | 0 | ✅ PASS | All tests passed |

**Integration tests** not validated in this container because they require a running MLflow server (Python-based). See "Integration Tests" section below for details.

## CI/CD

The repository uses **GitHub Actions** with 5 gating jobs on all pull requests:

### Job 1: lint

```bash
make lint
make vet
gofmt -l .
test -z "$(gofmt -l .)" || exit 1
go mod tidy
git diff --exit-code go.mod go.sum || exit 1
```

All linting, vetting, formatting, and tidy checks.

### Job 2: test-unit

```bash
make test/unit
```

Runs `go test -v -race ./...` (unit tests only, no integration tests).

### Job 3: test-integration

```bash
make test/integration-ci
```

Starts MLflow server (SQLite backend) on port 5001, runs integration tests with `-tags=integration`, then stops server and cleans up.

### Job 4: test-integration-postgres

```bash
make test/integration-ci-postgres
```

Starts PostgreSQL container, starts MLflow with PostgreSQL backend, runs integration tests, cleans up.

### Job 5: test-integration-midstream

```bash
make test/integration-ci-midstream MLFLOW_MIDSTREAM_REF=master
```

Tests against the Red Hat midstream fork of MLflow (opendatahub-io/mlflow) with workspace features enabled.

**All jobs are gating** (required to merge PRs).

## Integration Tests

Integration tests use the build tag `//go:build integration` and require a running MLflow server.

### Running Integration Tests Locally

You have two options:

#### Option 1: Manual (two terminals)

Terminal 1 — Start MLflow server:
```bash
make dev/up
```

Terminal 2 — Run integration tests:
```bash
make test/integration
```

Press Ctrl+C in terminal 1 to stop the server when done.

#### Option 2: CI-style (automated cleanup)

```bash
make test/integration-ci
```

This automatically:
1. Installs `uv` (Python package installer) to `bin/`
2. Starts MLflow server on port 5001 with isolated test database
3. Runs integration tests
4. Stops server and deletes test database

### Environment Variables

Integration tests read:
- `MLFLOW_TRACKING_URI` — MLflow server URL (default: from env, fallback to localhost:5000)
- `MLFLOW_INSECURE_SKIP_TLS_VERIFY` — Set to `true` for local dev with self-signed certs

### Infrastructure Requirements

Integration tests require:
- **MLflow server** (Python-based, version 3.9.0 by default)
- **uv** package installer (auto-installed to `bin/` by Makefile)
- **PostgreSQL** (optional, for `test/integration-ci-postgres` variant)
- **Docker** (optional, for PostgreSQL variant)

The CI jobs fully automate this infrastructure setup and teardown.

## Conventions

### Test Files

- **Pattern:** `*_test.go`
- **Location:** Alongside source code in each package, plus `test/integration/`
- **Naming:** Test functions start with `Test*` (e.g., `TestAPIError_Error`)

### Test Separation

- **Unit tests:** No build tag, can run anywhere with `go test ./...`
- **Integration tests:** Tagged `//go:build integration`, require MLflow server

### Import Style

Standard Go import grouping. Generated protobuf code in `internal/gen/` is excluded from linting.

### Code Coverage

```bash
go test -v -race -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

No enforced threshold, but coverage can be measured with standard Go tools.

## Gaps & Caveats

1. **Integration tests require infrastructure** — A downstream agent running in a basic Go container cannot execute integration tests without first starting a MLflow server. The CI jobs solve this by fully automating the server lifecycle.

2. **No explicit build command** — This is a library, not an application. Go compiles code on-demand when running tests. There's no standalone binary to build.

3. **PostgreSQL variant needs Docker** — `make test/integration-ci-postgres` uses `docker run` to start a postgres:16 container. It won't work in environments without Docker/Podman.

4. **Python dependency for MLflow** — The integration test infrastructure depends on Python tooling (uv, mlflow package). The Makefile handles this transparently via lazy installation.

5. **Generated code** — `internal/gen/mlflowpb/` contains generated protobuf code. To regenerate, run `make gen` (requires `protoc` installed). This is not typically needed for patch validation.

## Agent Readiness Summary

**Rating: HIGH**

A downstream agent can:
- ✅ Spin up a `golang:1.24` container
- ✅ Install deps with `go mod download`
- ✅ Run lint with `make lint` (validates in ~1-2 minutes)
- ✅ Run unit tests with `go test -v -race ./...` (validates in ~5 seconds)
- ✅ Get clear pass/fail signals from all commands

Limitations:
- ❌ Cannot run integration tests without MLflow server infrastructure
- ✅ But CI runs integration tests on every PR, so they're well-covered

**Recommendation:** For patch validation, run lint + unit tests in container (both validated and fast). Rely on CI for integration test coverage.

## Quick Reference

### Essential Commands

```bash
# Lint
make lint

# Unit tests
make test/unit

# Single test
go test -v -race -run TestName ./package/...

# Format code
make fmt

# Tidy modules
go mod tidy

# Check everything (lint + vet + unit tests)
make check
```

### CI Equivalents

To replicate CI locally:

```bash
# Job 1: lint
make lint && make vet && test -z "$(gofmt -l .)" && go mod tidy && git diff --exit-code go.mod go.sum

# Job 2: test-unit
make test/unit

# Job 3: test-integration (automated)
make test/integration-ci

# Job 4: test-integration-postgres (automated)
make test/integration-ci-postgres

# Job 5: test-integration-midstream (automated)
make test/integration-ci-midstream
```

All integration jobs (`test/integration-ci*`) handle server lifecycle automatically.

---

**End of Test Context Documentation**
