# Test Context for llm-d-kv-cache

## Overview

**Repository**: opendatahub-io/llm-d-kv-cache
**Languages**: Go (primary), Python, C++/CUDA
**Build System**: Makefile with Go build
**Agent Readiness**: **MEDIUM** — Lint and unit tests work reliably; E2E tests require container infrastructure

**Justification**: Core validation (lint + unit tests) runs cleanly in a standard container. E2E tests need Docker/Podman testcontainers, and embedded tokenizer tests require Python 3.12 + vLLM setup. An agent can validate Go code changes effectively but may struggle with full integration tests.

---

## Container Recipe

This recipe provides a complete, copy-paste setup for validating patches. Follow these steps in order.

### 1. Start Container

Pull the base image and start container with repo mounted:

```bash
podman pull golang:1.24
podman run -d --name test-context-llm-d-kv-cache \
  -v /path/to/llm-d-kv-cache:/app:Z \
  -w /app \
  golang:1.24 \
  sleep infinity
```

Replace `/path/to/llm-d-kv-cache` with the actual path to your repository clone.

### 2. Install System Dependencies

```bash
podman exec test-context-llm-d-kv-cache bash -c "
  apt-get update && \
  apt-get install -y libzmq3-dev pkg-config python3-dev python3-venv clang-format git make curl
"
```

**What this installs**:
- `libzmq3-dev`: ZeroMQ library for messaging
- `pkg-config`: For build configuration
- `python3-dev`, `python3-venv`: Python development headers and virtual environment
- `clang-format`: C++ code formatting
- `git`, `make`: Build utilities

### 3. Download Go Dependencies

```bash
podman exec test-context-llm-d-kv-cache bash -c "cd /app && go mod download"
```

**Expected**: No output (silent success) or progress messages. Exit code 0.

### 4. Install golangci-lint

```bash
podman exec test-context-llm-d-kv-cache bash -c "
  curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | \
  sh -s -- -b /usr/local/bin v2.1.6
"
```

**Expected**: `golangci/golangci-lint info installed /usr/local/bin/golangci-lint`

### 5. Build (Go-only, no Python dependencies)

```bash
podman exec test-context-llm-d-kv-cache bash -c "cd /app && make build-uds"
```

**Expected output**:
```
Checking if ZMQ is already installed...
✅ ZMQ is already installed.
==== Building (UDS-only, no embedded tokenizers) ====
✅ UDS-only build succeeded
```

**Exit code**: 0
**Status**: ✅ **VALIDATED**

### 6. Lint

```bash
podman exec test-context-llm-d-kv-cache bash -c "cd /app && golangci-lint run"
```

**Expected output**:
```
0 issues.
```

**Alternative**: Use Makefile target:
```bash
podman exec test-context-llm-d-kv-cache bash -c "cd /app && make lint"
```

**Exit code**: 0
**Status**: ✅ **VALIDATED** — Passed with 0 issues

### 7. Run Unit Tests (UDS-only mode)

```bash
podman exec test-context-llm-d-kv-cache bash -c "cd /app && make unit-test-uds"
```

**Expected output** (summary):
```
PASS
ok  	github.com/llm-d/llm-d-kv-cache/pkg/kvcache	0.011s
PASS
ok  	github.com/llm-d/llm-d-kv-cache/pkg/tokenization	20.064s
PASS
ok  	github.com/llm-d/llm-d-kv-cache/pkg/utils	0.002s
```

**Exit code**: 0
**Tests run**: 47+ test cases across multiple packages
**Status**: ✅ **VALIDATED** — All tests passed

**Alternative** (direct go test):
```bash
podman exec test-context-llm-d-kv-cache bash -c "cd /app && go test -v ./pkg/..."
```

### 8. Run Single Test File

To run tests in a specific package:
```bash
podman exec test-context-llm-d-kv-cache bash -c "
  cd /app && go test -v ./pkg/kvcache/kvblock/
"
```

### 9. Run Single Test

To run a specific test by name:
```bash
podman exec test-context-llm-d-kv-cache bash -c "
  cd /app && go test -v -run TestLongestPrefixScorer ./pkg/kvcache/
"
```

### 10. Cleanup

Always remove the container when done:
```bash
podman rm -f test-context-llm-d-kv-cache
```

---

## Validation Results

### ✅ Dependency Install
- **Command**: `go mod download`
- **Exit Code**: 0
- **Status**: Success (silent, no errors)

### ✅ Build (UDS-only)
- **Command**: `make build-uds`
- **Exit Code**: 0
- **Status**: Success
- **Notes**: Go code builds without Python embedded tokenizers

### ✅ Lint
- **Command**: `golangci-lint run`
- **Exit Code**: 0
- **Issues Found**: 0
- **Status**: Success

### ✅ Unit Tests
- **Command**: `make unit-test-uds`
- **Exit Code**: 0
- **Tests Passed**: 47+ test cases
- **Duration**: ~20 seconds
- **Status**: Success
- **Output Sample**:
  ```
  === RUN   TestLongestPrefixScorer
  --- PASS: TestLongestPrefixScorer (0.00s)
  === RUN   TestCostAwareIndexBehavior
  --- PASS: TestCostAwareIndexBehavior (0.02s)
  === RUN   TestUdsTokenizerSuite
  --- PASS: TestUdsTokenizerSuite (20.02s)
  ```

### ⚠️ E2E Tests (Not Validated)
- **Command**: `make e2e-test-uds`
- **Requirements**: Docker/Podman testcontainers, UDS tokenizer image build
- **Status**: Requires complex container-in-container setup
- **Notes**: E2E tests use testcontainers to spin up the UDS tokenizer service. Validation skipped.

### ⚠️ Python Tests (Not Validated)
- **Command**: `make uds-tokenizer-service-test`
- **Requirements**: Python venv, pytest, UDS tokenizer dependencies
- **Status**: Not validated in this analysis
- **Notes**: Python tests require setting up a separate venv in `services/uds_tokenizer/.venv`

---

## CI/CD

### GitHub Actions Workflow: ci-pr-checks.yaml

**Triggers**: Pull requests to `main` or `dev` branches

**Gating Checks** (all required to merge):

1. **Pre-commit hooks**
   ```bash
   pre-commit run --all-files --hook-stage manual
   ```
   Runs ruff (Python linter), typos (spell check), clang-format, actionlint

2. **Go linting with CGo**
   ```bash
   export CGO_CFLAGS="$(python3.12-config --cflags)"
   export CGO_LDFLAGS="$(python3.12-config --ldflags --embed) -ldl -lm"
   export CGO_ENABLED=1
   make precommit
   ```
   Runs `go mod tidy` + `golangci-lint run` + copyright header checks

3. **C/C++/CUDA formatting**
   ```bash
   make clang
   ```

4. **Build**
   ```bash
   make build
   ```
   Builds both UDS-only and embedded binaries

5. **Tests**
   ```bash
   make test
   ```
   Runs unit tests (UDS-only) and e2e tests (requires testcontainers)

**System Dependencies** (installed in CI):
- libzmq3-dev
- pkg-config
- python3.12, python3.12-dev, python3.12-venv (from ppa:deadsnakes/ppa)
- clang-format

**Go Version**: Extracted from go.mod (currently 1.24.1)

---

## Conventions

### Test File Naming
- Go: `*_test.go` (e.g., `index_test.go`, `redis_test.go`)
- Python: `test_*.py` (e.g., `test_integration.py`)

### Test Function Naming
- Go: `TestFunctionName` for individual tests, `TestSuiteName` for test suites
- Uses `testify/suite` and `testify/assert` packages
- Example: `TestCostAwareIndexBehavior`, `TestUdsTokenizerSuite`

### Import Style
- Standard Go import grouping: stdlib, external packages, internal packages
- Auto-formatted by `goimports` and `gofumpt` (via golangci-lint)

### Code Style
- Line length: 130 characters max (enforced by `lll` linter)
- Go code: Follows golangci-lint rules (50+ linters enabled)
- Python code: Formatted by `ruff format`, linted by `ruff check`
- C++/CUDA: Formatted by `clang-format` with `.clang-format` config

### Coverage
- No explicit coverage threshold configured
- Coverage not measured in standard test run

---

## Gaps & Caveats

### E2E Tests Require Container Infrastructure
E2E tests use [testcontainers-go](https://github.com/testcontainers/testcontainers-go) to spin up Redis mock and UDS tokenizer service containers. Requires:
- Docker or Podman socket access
- Ability to build and run images (`make image-build-uds`)
- `DOCKER_HOST` environment variable set correctly

**Impact**: An agent running in a basic container cannot run E2E tests without Docker-in-Docker or Podman socket passthrough.

### Embedded Tokenizer Tests Require Python + vLLM
Tests tagged with `embedded_tokenizers` require:
- Python 3.12 (exactly, not 3.13)
- vLLM 0.14.0 installed (large download, ~2GB+ of dependencies)
- CGo environment variables set:
  ```bash
  export CGO_ENABLED=1
  export CGO_CFLAGS="$(python3.12-config --cflags)"
  export CGO_LDFLAGS="$(python3.12-config --ldflags --embed) -ldl -lm"
  export PYTHONPATH=...
  ```

**Commands**:
```bash
make unit-test-embedded
make e2e-test-embedded
```

**Impact**: Complex setup. Validation used Python 3.13 and skipped these tests.

### Python Linting Not Independently Validated
Python linting runs via pre-commit hooks:
```bash
ruff check --output-format github --fix
ruff format
```

**Impact**: Not validated separately. Assumes pre-commit hook setup works.

### Some Tests Require External Model Downloads
Tests may require HuggingFace models in `tests/e2e/redis_mock/testdata/local-llama3/`:
```bash
make download-local-llama3
```

Uses `hf` CLI to download RedHatAI/Meta-Llama-3-8B-Instruct-FP8.

**Impact**: Large download (~8GB+). Skipped in validation.

### CI Uses Python 3.12, Validation Used 3.13
CI workflow explicitly installs Python 3.12 from `ppa:deadsnakes/ppa`. Validation used Python 3.13 (default in golang:1.24 image). Tests passed, but edge cases may differ.

**Recommendation**: For exact CI reproduction, use Python 3.12.

---

## Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| Install deps | `go mod download` |
| Build (Go-only) | `make build-uds` |
| Build (with Python) | `make build-embedded` |
| Lint | `make lint` |
| Unit tests (Go-only) | `make unit-test-uds` |
| Unit tests (with Python) | `make unit-test-embedded` |
| E2E tests (UDS) | `make e2e-test-uds` |
| E2E tests (embedded) | `make e2e-test-embedded` |
| All tests | `make test` |
| Pre-commit checks | `make precommit` |
| C/C++ formatting | `make clang` |
| Python tests | `make uds-tokenizer-service-test` |

### File Locations

| Type | Location |
|------|----------|
| Go source | `pkg/`, `examples/` |
| Go tests | `pkg/**/*_test.go`, `tests/` |
| Python source | `services/uds_tokenizer/` |
| Python tests | `services/uds_tokenizer/tests/` |
| Linter config (Go) | `.golangci.yml` |
| Linter config (Python) | `.pre-commit-config.yaml` |
| Build config | `Makefile` |
| CI config | `.github/workflows/ci-pr-checks.yaml` |
| Test fixtures | `pkg/tokenization/testdata/`, `tests/e2e/redis_mock/testdata/` |

---

## Notes for Downstream Agents

1. **Start with UDS-only tests**: `make unit-test-uds` is the most reliable validation. No Python dependencies, fast, comprehensive.

2. **Lint is cheap**: `golangci-lint run` completes in seconds and catches most code quality issues.

3. **E2E tests are complex**: If E2E tests fail, check Docker/Podman availability and testcontainers setup. May be environmental, not code-related.

4. **Two build modes**: Always clarify whether a change affects Go-only code (`build-uds`) or embedded tokenizers (`build-embedded`).

5. **Python 3.12 vs 3.13**: If Python tests behave unexpectedly, verify Python version. CI uses 3.12 exactly.

6. **Pre-commit hooks cover more than linting**: They also check spelling (typos), GitHub Actions syntax (actionlint), and copyright headers.

7. **CGo is finicky**: If build fails with CGo errors, verify `python3.12-config` exists and returns valid flags.

8. **Container cleanup is critical**: Always run `podman rm -f test-context-llm-d-kv-cache` even if validation fails midway.

---

**Generated**: 2026-03-22T22:59:12Z
**Confidence**: High
**Agent Readiness**: Medium
