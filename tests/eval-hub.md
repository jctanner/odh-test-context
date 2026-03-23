# Test Context: eval-hub

**Agent Readiness: HIGH** — All lint and test commands validated successfully in container. Agent can clone, patch, lint, test, and get clear pass/fail signals.

## Overview

- **Repository**: opendatahub-io/eval-hub
- **Languages**: Go 1.25.0 (primary), Python 3.11+ (python-server), JavaScript (docs tooling)
- **Build System**: Make, go build, uv (Python package manager)
- **Test Framework**: go test (stdlib + godog for BDD integration tests), pytest (Python)
- **CI**: GitHub Actions (required checks: lint, vet, fmt, tests with coverage, API docs)
- **Analyzed**: 2026-03-22T22:09:00Z

The eval-hub is an evaluation hub REST API service for ML model benchmarking. It uses Go for the main service, Python for a wrapper server binary, and JavaScript for API documentation tooling.

---

## Container Recipe

This is a **complete, validated recipe** for running lint and tests in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-eval-hub \
  -v /path/to/eval-hub:/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

**Base Image**: `golang:1.25` (Debian-based, includes Go 1.25 toolchain)

### 2. Install System Dependencies

```bash
podman exec test-context-eval-hub bash -c \
  "apt-get update && apt-get install -y make git python3 python3-pip curl"
```

### 3. Install Go Dependencies

```bash
podman exec test-context-eval-hub bash -c "cd /app && go mod download"
```

**Expected**: No output on success. Downloads ~200+ dependencies from go.mod.

### 4. Install Python Tools (uv)

```bash
podman exec test-context-eval-hub bash -c \
  "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

**Expected**: Installs uv to `/root/.local/bin/uv`. Add to PATH for subsequent commands.

### 5. Install Python Dev Dependencies

```bash
podman exec test-context-eval-hub bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python-server && uv pip install '.[dev]'"
```

**Expected**: Installs ruff, mypy, pytest, and other dev tools to `.venv`.

### 6. Build Go Binary (Optional Verification)

```bash
podman exec test-context-eval-hub bash -c \
  "cd /app && go build -race -o bin/eval-hub ./cmd/eval_hub"
```

**Expected**: Creates `bin/eval-hub` (130MB with race detector). Validates code compiles.

---

## Lint Commands

### Go: vet

```bash
podman exec test-context-eval-hub bash -c "cd /app && go vet ./..."
```

**Validated**: ✅ Passed with no output
**What it checks**: Go static analysis for suspicious constructs (nil dereferences, unreachable code, etc.)
**Exit code**: 0 = pass, non-zero = issues found

### Go: fmt

```bash
podman exec test-context-eval-hub bash -c "cd /app && go fmt ./..."
```

**Validated**: ✅ No formatting issues
**What it checks**: Go code formatting (gofmt standard)
**Exit code**: 0 = pass. Outputs modified files if any.

**CI enforcement**:
```bash
go fmt ./... && git diff --exit-code -- '*.go'
```
Fails if fmt made changes (code not pre-formatted).

### Python: ruff (lint)

```bash
podman exec test-context-eval-hub bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python-server && uv run ruff check ."
```

**Validated**: ✅ All checks passed
**What it checks**: Python linting (pycodestyle errors/warnings, pyflakes, isort, flake8-bugbear, comprehensions, pyupgrade)
**Config**: `python-server/pyproject.toml` `[tool.ruff.lint]`
**Exit code**: 0 = pass, 1 = issues found

**Auto-fix**:
```bash
uv run ruff check --fix .
```

### Python: ruff (format)

```bash
podman exec test-context-eval-hub bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python-server && uv run ruff format --check ."
```

**What it checks**: Python code formatting (Black-compatible)
**Auto-fix**:
```bash
uv run ruff format .
```

### Python: mypy (type checking)

```bash
podman exec test-context-eval-hub bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python-server && uv run mypy --exclude '(build|setup\\.py)' ."
```

**Validated**: ✅ Success: no issues found in 3 source files
**What it checks**: Static type checking for Python code
**Exit code**: 0 = pass, 1 = type errors found

---

## Test Commands

### Go: Unit Tests

```bash
podman exec test-context-eval-hub bash -c \
  "cd /app && go test -v ./auth/... ./internal/... ./cmd/..."
```

**Validated**: ✅ All tests passed
**What it tests**: Go unit tests across auth, internal, and cmd packages
**Test files**: `*_test.go` in each package
**Output**: Verbose test results. Passes include timing (e.g., `ok github.com/eval-hub/eval-hub/auth 0.036s`)
**Exit code**: 0 = all passed, 1 = failures

**Single package**:
```bash
go test -v ./auth/...
```

**Single test**:
```bash
go test -v -run TestComputeResourceAttributesSuite ./auth/...
```

**With coverage**:
```bash
go test -v -race -coverprofile=coverage.out -covermode=atomic ./internal/... ./cmd/...
```

### Go: Integration Tests (FVT)

```bash
podman exec test-context-eval-hub bash -c \
  "cd /app && go test -v -race ./tests/features/..."
```

**Validated**: ✅ All scenarios passed (0.332s)
**What it tests**: Functional verification tests using godog (Cucumber/Gherkin BDD framework)
**Test files**: `tests/features/*.feature` (Gherkin), `tests/features/*_test.go` (step definitions)
**Features tested**: Collections, Evaluations, Providers, Health, Metrics endpoints
**Output**: Colored Gherkin scenario results with Given/When/Then steps
**Exit code**: 0 = all scenarios passed, 1 = failures

**Environment**: Uses in-memory SQLite database, starts embedded HTTP server on random port.

**Run with server** (alternative):
```bash
make test-fvt-server  # Starts server, runs tests, stops server
```

**Generate HTML report**:
```bash
GODOG_FORMAT=cucumber GODOG_OUTPUT=cucumber-fvt.json go test -v -race ./tests/features/...
node -e "require('cucumber-html-reporter').generate({theme:'bootstrap',jsonFile:'cucumber-fvt.json',output:'cucumber-report.html'})"
```

### Python: Unit Tests

```bash
podman exec test-context-eval-hub bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python-server && uv run pytest tests/ -m unit --tb=short -v"
```

**Validated**: ✅ 3 passed in 0.03s
**What it tests**: Python wrapper server entry point (evalhub_server.main)
**Test files**: `python-server/tests/test_*.py`
**Markers**: `@pytest.mark.unit` (filter with `-m unit`)
**Output**: Pytest verbose output with pass/fail per test
**Exit code**: 0 = all passed, non-zero = failures

**Single test**:
```bash
uv run pytest tests/test_main.py::test_setuptools_entrypoint_forwards_argv -v
```

**All tests** (no marker filter):
```bash
uv run pytest tests/ -v
```

---

## Validation Results

All commands were **validated in a live container** with the following results:

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install | `go mod download` | 0 | ✅ Pass | Dependencies downloaded |
| Build | `go build -race -o bin/eval-hub ./cmd/eval_hub` | 0 | ✅ Pass | 130MB binary created |
| Lint | `go vet ./...` | 0 | ✅ Pass | No issues found |
| Lint | `go fmt ./...` | 0 | ✅ Pass | No formatting changes needed |
| Lint | `cd python-server && uv run ruff check .` | 0 | ✅ Pass | All checks passed |
| Lint | `cd python-server && uv run mypy --exclude '(build\|setup\\.py)' .` | 0 | ✅ Pass | No type errors |
| Test | `go test -v ./auth/... ./internal/... ./cmd/...` | 0 | ✅ Pass | All unit tests passed |
| Test | `go test -v -race ./tests/features/...` | 0 | ✅ Pass | All integration tests passed |
| Test | `cd python-server && uv run pytest tests/ -m unit -v` | 0 | ✅ Pass | 3 Python tests passed |

**Summary**: All validation passed. Deps OK, build OK, all linters OK, all tests OK.

---

## CI/CD

### Gating Checks (Required for Merge)

These checks run on **all pull requests** and must pass:

1. **Format Check**
   ```bash
   make fmt
   git diff --exit-code -- '*.go'
   ```
   Fails if `go fmt` made any changes (code must be pre-formatted).

2. **Linter**
   ```bash
   make lint  # Runs: go vet ./...
   ```

3. **Vet**
   ```bash
   make vet  # Runs: go vet ./...
   ```

4. **All Tests with Coverage**
   ```bash
   make clean test-all-coverage
   ```
   Runs: unit tests, integration tests, coverage for all packages.
   Uploads coverage to Codecov (requires `CODECOV_TOKEN` secret).

5. **API Documentation Verification**
   ```bash
   npm ci
   make documentation
   git diff --exit-code
   ```
   Generates OpenAPI docs with redocly-cli, fails if docs not up-to-date.

6. **Commitizen** (commit message format)
   Enforced via pre-commit hook. Conventional Commits format required.

### Advisory Checks (Non-Blocking)

- **Gosec Security Scanner**: Runs on all PRs, uploads SARIF to GitHub Security tab
- **Docker Build**: Runs on push events only (not PRs)

### Coverage Threshold

From `codecov.yml`:
- **Red to Yellow**: 50%
- **Yellow to Green**: 75%

Current coverage includes unit tests for `./internal/...`, `./cmd/...`, and integration tests (`./tests/features/...`).

---

## Conventions

### Test File Naming

- **Go**: `*_test.go` (e.g., `rules_test.go`, `server_test.go`)
- **Python**: `test_*.py` (e.g., `test_main.py`)
- **Gherkin/BDD**: `*.feature` (e.g., `collections.feature`, `evaluations.feature`)

### Test Function Naming

- **Go**: `func TestXxx(t *testing.T)` or `func TestXxxSuite(t *testing.T)` for table-driven tests
- **Python**: `def test_xxx(...)` with `@pytest.mark.unit` decorator
- **Gherkin**: `Scenario: Description` with Given/When/Then steps

### Import Style

- **Go**: Standard library first, then external packages, then local packages. Grouped with blank lines.
- **Python**: Managed by ruff (isort rules): stdlib, third-party, local imports.

### Commit Messages

Enforced by Commitizen (pre-commit hook):
- Format: `<type>(<scope>): <description>`
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, etc.
- Example: `feat(collections): add support for benchmark metadata`

---

## Make Targets (Quick Reference)

| Target | Command | Description |
|--------|---------|-------------|
| `make help` | Shows all targets | Display available make targets |
| `make build` | `go build -race ...` | Build binaries with race detector |
| `make lint` | `go vet ./...` | Run go vet linter |
| `make fmt` | `go fmt ./...` | Format Go code |
| `make test` | `go test ./auth/... ./internal/... ./cmd/...` | Run unit tests |
| `make test-fvt` | `go test -race ./tests/features/...` | Run integration tests |
| `make test-all` | `make test test-fvt` | Run all tests |
| `make test-coverage` | `go test -coverprofile=...` | Unit tests with coverage |
| `make test-all-coverage` | Unit + FVT coverage | All tests with coverage |
| `make clean` | Remove build artifacts | Clean bin/ directory |

**Python-specific**:
- `cd python-server && uv run pytest tests/ -m unit -v` — Python unit tests
- `cd python-server && uv run ruff check .` — Python linting
- `cd python-server && uv run mypy .` — Python type checking

---

## Cleanup

```bash
podman rm -f test-context-eval-hub
```

Always clean up the container when done, even if validation fails partway through.

---

## Gaps & Caveats

**None identified**. All test and lint infrastructure is functional and validated.

- ✅ Comprehensive test suite with unit and integration tests
- ✅ All linters configured and working
- ✅ CI enforces all quality checks
- ✅ Coverage reporting to Codecov
- ✅ Tests run with in-memory database, no external dependencies required
- ✅ Python and Go tests both validated

---

## Additional Notes

### Python Server

The `python-server/` directory contains a Python wrapper package (`eval-hub-server`) that bundles the compiled Go binary and provides a Python entry point. This allows the Go server to be installed via `pip install eval-hub-server` and run as `eval-hub-server` command.

### Pre-commit Hooks

The repository uses pre-commit (`.pre-commit-config.yaml`) with:
- ruff (lint + format) for Python
- mypy for Python type checking
- pytest unit tests for Python (runs on Python file changes)
- go test (unit + integration) for Go (runs on Go file changes)
- Standard checks (trailing whitespace, EOF fixer, YAML/JSON/TOML validation)
- Commitizen for commit message format

Install with:
```bash
pre-commit install
```

### Test Data

Integration tests use fixtures in `tests/features/test_data/` including:
- JSON request/response payloads
- YAML configuration files
- Sample benchmark definitions

### Godog/BDD Integration Tests

The integration tests use Cucumber/Gherkin syntax for behavior-driven testing:
- **Features**: Collections, Evaluations, Providers, Health, Metrics
- **Test Server**: Embedded HTTP server on random port with in-memory SQLite
- **Step Definitions**: `tests/features/step_definitions_test.go` implements Given/When/Then steps
- **Scenarios**: Cover CRUD operations, validation, error handling, query parameters, pagination

Example scenario:
```gherkin
Scenario: Create a collection of benchmarks
  Given the service is running
  When I send a POST request to "/api/v1/evaluations/collections" with body "file:/collection.json"
  Then the response code should be 202
  And the array at path "benchmarks" in the response should have length 1
```

### Coverage Reports

After running `make test-all-coverage`:
- `bin/coverage.out` — Unit test coverage (internal, cmd packages)
- `bin/coverage-init.out` — Init binary coverage
- `bin/coverage-fvt.out` — Integration test coverage
- `bin/coverage.html`, `bin/coverage-fvt.html` — HTML reports (open in browser)

View coverage:
```bash
go tool cover -html=bin/coverage.out
```

---

## Summary

**This repository is highly agent-ready** with:
- ✅ All lint commands validated and passing
- ✅ All test commands validated and passing
- ✅ Clear, executable commands with no external dependencies
- ✅ Comprehensive CI enforcement
- ✅ In-container validation successful

An AI agent can clone this repo, apply patches, run the validated commands above, and receive clear pass/fail signals for patch validation.
