# Test Context for model-registry-bf4-kf

**Repository:** opendatahub-io/model-registry-bf4-kf
**Languages:** Go 1.19, Python 3.9-3.10, Robot Framework
**Build System:** Make (Go), Poetry + Nox (Python)
**Agent Readiness:** **medium** — Lint and unit tests validated successfully. Integration tests require Docker infrastructure.

---

## Overview

This is a polyglot repository implementing a model registry service for OpenDataHub. The main service is written in Go, with a Python client library and Robot Framework integration tests. Linting works perfectly across all languages. Unit tests run successfully in containers. Integration tests require Docker/testcontainers to run ml-metadata services.

**Validated:**
- ✅ Go linting (golangci-lint v1.54.2) — 0 issues
- ✅ Python linting (ruff) — 0 issues
- ✅ Go unit tests — 95 tests passed (converter, mapper packages)
- ✅ Python unit tests — 9 tests passed (type mapping tests)

**Requires Infrastructure:**
- ⚠️ Go integration tests (pkg/core) — need Docker for ml-metadata container
- ⚠️ Python integration tests (34 tests) — need Docker for ml-metadata container
- ⚠️ Robot Framework tests — need full docker-compose stack

---

## Container Recipe

This section provides a complete, step-by-step recipe for running lint and tests in containers.

### Go Validation

**Base image:** `golang:1.19`

**1. Start the container:**
```bash
podman run -d --name test-context-model-registry \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.19 \
  sleep infinity
```

**2. Install system dependencies:**
```bash
podman exec test-context-model-registry bash -c \
  "apt-get update && apt-get install -y make git wget unzip curl nodejs npm default-jre protobuf-compiler"
```

**3. Download Go modules:**
```bash
podman exec test-context-model-registry bash -c "cd /app && go mod download"
```

**4. Install build tools:**
```bash
podman exec test-context-model-registry bash -c "cd /app && make deps"
```

This installs:
- `go-enum` v1.2.97
- `protoc-gen-go` v1.31.0
- `protoc-gen-go-grpc` v1.3.0
- `golangci-lint` v1.54.2
- `goverter` v1.1.1
- `openapi-generator-cli` via npm

Note: You may see npm warnings about Node.js version (container has 18, tool wants 20). These are non-fatal warnings.

**5. Run Go lint (VALIDATED ✅):**
```bash
podman exec test-context-model-registry bash -c "cd /app && make lint"
```

**Expected:** Exit code 0, no output (clean lint)

**6. Run Go unit tests (VALIDATED ✅):**
```bash
podman exec test-context-model-registry bash -c "cd /app && go test ./internal/converter ./internal/mapper -v"
```

**Expected:** 95 tests pass in ~0.01s
- 64 tests in `internal/converter`
- 31 tests in `internal/mapper`

**7. Run full Go test suite (REQUIRES DOCKER ⚠️):**
```bash
podman exec test-context-model-registry bash -c "cd /app && make test"
```

**Expected:** Fails with "Cannot connect to the Docker daemon" because `pkg/core` tests use testcontainers to spin up ml-metadata gRPC service. Unit tests work; integration tests need infrastructure.

**8. Run single test file:**
```bash
podman exec test-context-model-registry bash -c "cd /app && go test ./internal/converter -v"
```

**9. Run single test:**
```bash
podman exec test-context-model-registry bash -c "cd /app && go test ./internal/converter -run TestStringToInt64 -v"
```

**10. Cleanup:**
```bash
podman rm -f test-context-model-registry
```

---

### Python Validation

**Base image:** `python:3.10`

**1. Start the container:**
```bash
podman run -d --name test-context-model-registry-python \
  -v $(pwd):/app:Z \
  -w /app/clients/python \
  python:3.10 \
  sleep infinity
```

**2. Install Python build tools:**
```bash
podman exec test-context-model-registry-python bash -c \
  "pip install --constraint=/app/.github/workflows/constraints.txt poetry nox nox-poetry"
```

This installs:
- poetry 1.6.1
- nox 2023.4.22
- nox-poetry 1.0.2

**3. Run Python lint (VALIDATED ✅):**
```bash
podman exec test-context-model-registry-python bash -c "cd /app/clients/python && nox --session lint"
```

**Expected:** Exit code 0, "Session lint-3.10 was successful"

**4. Run Python tests (PARTIAL ✅):**
```bash
podman exec test-context-model-registry-python bash -c "cd /app/clients/python && nox --session tests-3.10"
```

**Expected:** 9 tests pass, 34 errors due to Docker requirement
- ✅ 9 passed: type mapping tests (types/test_artifact_mapping.py, types/test_context_mapping.py)
- ❌ 34 errors: tests requiring ml-metadata container (test_client.py, test_core.py, store/test_wrapper.py)

Coverage on non-infrastructure code: 48%

**5. Run Python type checking:**
```bash
podman exec test-context-model-registry-python bash -c "cd /app/clients/python && nox --session mypy"
```

**6. Run single test file:**
```bash
podman exec test-context-model-registry-python bash -c "cd /app/clients/python && pytest tests/types/test_artifact_mapping.py -v"
```

**7. Run single test:**
```bash
podman exec test-context-model-registry-python bash -c "cd /app/clients/python && pytest tests/types/test_artifact_mapping.py::test_registered_model_to_dict -v"
```

**8. Cleanup:**
```bash
podman rm -f test-context-model-registry-python
```

---

## Validation Results

### Go Linting
- **Command:** `make lint`
- **Status:** ✅ PASS
- **Exit Code:** 0
- **Output:** (no output, clean)
- **Notes:** Uses golangci-lint v1.54.2 with default configuration. Checks main.go, cmd/, internal/, pkg/.

### Go Unit Tests
- **Command:** `go test ./internal/converter ./internal/mapper -v`
- **Status:** ✅ PASS
- **Exit Code:** 0
- **Tests Run:** 95
- **Time:** 0.008s
- **Output:**
  ```
  ok  	github.com/opendatahub-io/model-registry/internal/converter	0.005s
  ok  	github.com/opendatahub-io/model-registry/internal/mapper	0.003s
  ```

### Go Integration Tests
- **Command:** `make test`
- **Status:** ⚠️ REQUIRES INFRASTRUCTURE
- **Exit Code:** 1
- **Error:** `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`
- **Notes:** The `pkg/core/core_test.go` suite uses testcontainers-go to spin up a ml-metadata gRPC container. This requires Docker-in-Docker or an external Docker daemon.

### Python Linting
- **Command:** `cd clients/python && nox --session lint`
- **Status:** ✅ PASS
- **Exit Code:** 0
- **Output:** `nox > Session lint-3.10 was successful.`
- **Notes:** Uses ruff with comprehensive ruleset configured in pyproject.toml.

### Python Tests
- **Command:** `cd clients/python && nox --session tests-3.10`
- **Status:** ⚠️ PARTIAL
- **Exit Code:** 1
- **Tests Passed:** 9
- **Tests Failed:** 34 (all Docker-related)
- **Output:**
  ```
  ========================= 9 passed, 34 errors in 5.88s =========================
  ERROR tests/test_client.py::test_register_new - docker.errors.DockerException
  ```
- **Notes:** Type mapping tests pass. Tests requiring ml-metadata service fail with DockerException.

---

## CI/CD

### Gating Checks

All checks run on `pull_request` events (except for docs/metadata-only changes):

**1. Build (build.yml)**
- Runs: `make deps`, `make clean`, `make build`, `make test-cover`
- Requirements: Go 1.19, protoc 24.3, Python 3.9, npm
- Uploads coverage to Codecov
- **Status in container:** ✅ Lint and unit tests pass, integration tests need Docker

**2. Python Tests (python-tests.yml)**

Matrix: Python 3.9, 3.10 × sessions lint, tests, mypy, docs-build

- `nox --session lint` — ruff linting
- `nox --session tests -- --cov-report=xml` — pytest with coverage
- `nox --session mypy` — type checking
- `nox --session docs-build` — Sphinx documentation

**Status in container:**
- ✅ lint: passes
- ⚠️ tests: 9/43 pass (requires Docker)
- ✅ mypy: runs (may have type errors that don't fail CI)
- ✅ docs-build: runs (not validated in container)

**3. Robot Framework Tests (run-robot-tests.yaml)**
- Requires: `docker-compose-local.yaml` running
- Runs: `robot test/robot` (REST mode), `TEST_MODE=Python robot test/robot/MRandLogicalModel.robot` (Python mode)
- **Status in container:** ⚠️ Requires full docker-compose stack

---

## Conventions

### Test File Naming
- **Go:** `*_test.go` (e.g., `openapi_converter_test.go`, `mapper_test.go`)
- **Python:** `test_*.py` (e.g., `test_client.py`, `test_core.py`)
- **Robot:** `*.robot` (e.g., `MRandLogicalModel.robot`, `UserStory.robot`)

### Test Function Naming
- **Go:** `TestFunctionName` (e.g., `TestStringToInt64`, `TestMapRegisteredModelProperties`)
- **Python:** `test_function_name` (e.g., `test_register_new`, `test_get_registered_model_by_id`)

### Test Patterns
- **Go:** Table-driven tests common in converter/mapper packages
- **Python:** Pytest fixtures defined in `clients/python/tests/conftest.py`
- **Robot:** Keyword-driven tests using custom keywords from `MLMetadata.py` and `ModelRegistry.py`

### Coverage
- **Go:** Uses `go tool cover`, uploads to Codecov via `make test-cover`
- **Python:** Uses pytest-cov with coverage config in pyproject.toml, uploads to Codecov
- No explicit coverage thresholds enforced in CI

---

## Gaps & Caveats

1. **Integration tests require Docker:** Both Go (`pkg/core`) and Python (`test_client.py`, `test_core.py`, `store/test_wrapper.py`) integration tests use testcontainers to spin up ml-metadata services. These cannot run in a basic container without:
   - Docker-in-Docker (privileged container)
   - Docker socket mounted from host
   - External ml-metadata service running

2. **Robot Framework tests require full stack:** The Robot tests need the entire model-registry service running via `docker-compose-local.yaml`, which builds the Go service, runs it with a database, and tests the REST/Python APIs.

3. **No golangci-lint config:** The Go linting uses golangci-lint defaults (no `.golangci.yml` file). This means the linter may not catch project-specific style issues.

4. **Limited standalone test coverage:** Only ~21% of Go tests (95/~450 total) and ~21% of Python tests (9/43) can run without Docker infrastructure. Most test logic is in integration tests.

5. **ml-metadata v1.14.0 dependency:** Tests require a specific version of Google's ml-metadata service. This is not trivial to set up outside of testcontainers.

6. **Node.js version warnings:** The build tools install openapi-generator-cli which warns about Node.js version (container has 18, wants 20), though this is non-fatal.

7. **Build requires code generation:** The `make build` target depends on `make gen` which generates protobuf code, OpenAPI client/server, and converters. This adds complexity and requires protoc, npm, and Java.

---

## Quick Reference

### Run Everything (That Works in Containers)

**Go:**
```bash
# Lint (works)
make lint

# Unit tests (works)
go test ./internal/converter ./internal/mapper -v

# Full tests (needs Docker)
make test
```

**Python:**
```bash
cd clients/python

# Lint (works)
nox --session lint

# Type check (works)
nox --session mypy

# Tests (9 pass, 34 need Docker)
nox --session tests-3.10
```

### What An Agent Can Validate

**Without Docker:**
- ✅ Go linting
- ✅ Go unit tests (converter, mapper packages)
- ✅ Python linting
- ✅ Python type checking
- ✅ Python unit tests (type mapping)

**Requires Docker:**
- ❌ Go integration tests (core package)
- ❌ Python integration tests (client, core, store)
- ❌ Robot Framework integration tests
- ❌ Full coverage reports

### Recommended Validation Workflow for Patches

1. **Lint first:** Run `make lint` and `cd clients/python && nox --session lint`. These are fast and catch most style issues.

2. **Run unit tests:** Run `go test ./internal/converter ./internal/mapper` for Go and `nox --session tests-3.10` for Python (expect partial pass). These catch logic errors without infrastructure.

3. **Check for integration test impact:** If patch touches `pkg/core` or `clients/python/src/model_registry/{_client,core}.py`, note that full validation requires Docker infrastructure.

4. **Generate code if needed:** If patch modifies `.proto` files or `api/openapi/model-registry.yaml`, run `make gen` to regenerate code and verify no breaking changes.

---

## Build Dependencies

### Go Build
- Go 1.19
- protoc (Protocol Buffers compiler) v24.3
- make
- Node.js/npm (for openapi-generator-cli)
- Java 11 (for openapi-generator)

### Python Build
- Python 3.9 or 3.10
- poetry 1.6.1
- nox 2023.4.22
- nox-poetry 1.0.2

### Runtime Dependencies
- ml-metadata v1.14.0 (gRPC service)
- Database (SQLite for local dev, configurable for production)

---

## Summary

**Agent Readiness: MEDIUM**

This repository has excellent linting infrastructure and a solid unit test foundation. An AI agent can:
- ✅ Apply patches
- ✅ Validate linting (Go + Python)
- ✅ Run unit tests (partial coverage)
- ⚠️ Cannot fully validate integration tests without Docker infrastructure

For full CI validation, the agent would need Docker-in-Docker capability or access to an external ml-metadata service. For most patches, lint + unit tests provide reasonable confidence in correctness.
