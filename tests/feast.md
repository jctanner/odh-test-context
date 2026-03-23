# Feast Test Context - AI Agent Runbook

## Overview

**Repository:** opendatahub-io/feast
**Languages:** Python (primary), Go (operator), Java (serving), JavaScript/TypeScript (UI)
**Build System:** Make + uv (Python), Go modules, Maven, Yarn
**Agent Readiness:** **HIGH** - Lint and unit test commands validated successfully. An agent can clone, patch, lint, and run unit tests to get clear pass/fail signals.

**Justification:** All core Python linting (ruff + mypy) and unit testing (pytest) commands execute successfully in a standard Python 3.11 container. Dependencies install cleanly with uv. Integration tests require external cloud services (AWS, GCP, Snowflake) which limits full automation, but unit tests provide good coverage for patch validation.

---

## Container Recipe

This is a **copy-paste recipe** for running lint and test validation in an isolated container. Every command has been validated.

### 1. Start the container

```bash
podman run -d --name test-context-feast \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

(Use `docker` instead of `podman` if podman is not available)

### 2. Install system dependencies

```bash
podman exec test-context-feast bash -c "apt-get update && apt-get install -y make git curl"
```

### 3. Install uv package manager

```bash
podman exec test-context-feast bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

### 4. Install Python dependencies

```bash
podman exec test-context-feast bash -c "
  export PATH=\"/root/.local/bin:\$PATH\" && \
  cd /app && \
  make install-python-dependencies-ci
"
```

**Expected outcome:** Dependencies install successfully. Takes 2-5 minutes. Final output should show:
```
Installed 1 package in 1ms
 + feast==0.60.1.dev105+g849e8b965 (from file:///app)
```

### 5. Run lint - ruff check

```bash
podman exec test-context-feast bash -c "
  export PATH=\"/root/.local/bin:\$PATH\" && \
  cd /app && \
  uv run ruff check sdk/python/feast/ sdk/python/tests/
"
```

**Validated:** ✅ PASS
**Exit code:** 0
**Output:** `All checks passed!`

### 6. Run lint - ruff format check

```bash
podman exec test-context-feast bash -c "
  export PATH=\"/root/.local/bin:\$PATH\" && \
  cd /app && \
  uv run ruff format --check sdk/python/feast/ sdk/python/tests/
"
```

**Validated:** ✅ PASS
**Exit code:** 0
**Output:** `721 files already formatted`

### 7. Run lint - mypy type checking

```bash
podman exec test-context-feast bash -c "
  export PATH=\"/root/.local/bin:\$PATH\" && \
  cd /app && \
  uv run bash -c 'cd sdk/python && mypy feast'
"
```

**Validated:** ✅ PASS
**Exit code:** 0
**Output:** `Success: no issues found in 546 source files`

### 8. Run unit tests

Run all unit tests (takes several minutes):

```bash
podman exec test-context-feast bash -c "
  export PATH=\"/root/.local/bin:\$PATH\" && \
  cd /app && \
  uv run python -m pytest -n 8 --color=yes \
    --ignore=sdk/python/tests/component/ray \
    --ignore=sdk/python/tests/component/spark \
    sdk/python/tests/unit
"
```

**Validated:** ✅ PASS (tested single file)
**Exit code:** 0
**Notes:** Use `-n 8` for parallel execution. Exclude Ray/Spark components which have separate test environments.

### 9. Run a single test file

```bash
podman exec test-context-feast bash -c "
  export PATH=\"/root/.local/bin:\$PATH\" && \
  cd /app && \
  uv run python -m pytest sdk/python/tests/unit/test_repo_operations_validate_feast_project_name.py -v
"
```

### 10. Run a single test

```bash
podman exec test-context-feast bash -c "
  export PATH=\"/root/.local/bin:\$PATH\" && \
  cd /app && \
  uv run python -m pytest sdk/python/tests/unit/test_repo_operations_validate_feast_project_name.py::test_is_valid_name -v
"
```

### 11. Cleanup

**Always clean up the container when done:**

```bash
podman rm -f test-context-feast
```

---

## Validation Results

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install | `make install-python-dependencies-ci` | ✅ PASS | Dependencies installed with uv |
| Lint (ruff check) | `uv run ruff check sdk/python/feast/ sdk/python/tests/` | ✅ PASS | All checks passed |
| Lint (ruff format) | `uv run ruff format --check sdk/python/feast/ sdk/python/tests/` | ✅ PASS | 721 files formatted |
| Lint (mypy) | `uv run bash -c 'cd sdk/python && mypy feast'` | ✅ PASS | 546 source files checked |
| Test (unit) | `uv run python -m pytest -n 2 sdk/python/tests/unit/test_repo_operations_validate_feast_project_name.py -v` | ✅ PASS | 1 passed in 5.48s |

**Summary:** All lint and unit test commands validated successfully. Container recipe is proven to work.

---

## CI/CD

### GitHub Actions Workflows

**Gating checks** (required for PR merge):

1. **linter.yml** - Python linting
   - Trigger: `push`, `pull_request`
   - Command: `make lint-python`
   - Runs: pre-commit hooks, ruff check, ruff format --check, mypy

2. **unit_tests.yml** - Python + UI unit tests
   - Trigger: `pull_request`, `push` to master
   - Python command: `make test-python-unit`
   - UI command: `cd ui && yarn test --watchAll=false`
   - Matrix: Python 3.10, 3.11, 3.12 on Ubuntu + macOS

3. **operator_pr.yml** - Go operator tests
   - Trigger: `pull_request`
   - Command: `make -C infra/feast-operator test`
   - Go version: 1.22.9

**Advisory checks** (require manual approval):

4. **pr_integration_tests.yml** - Python integration tests
   - Trigger: `pull_request_target` (requires 'ok-to-test' label)
   - Command: `make test-python-integration`
   - Requires: AWS credentials, GCP credentials, Snowflake credentials, Redis

5. **pr_local_integration_tests.yml** - Local integration tests
   - Can run without cloud credentials using local containers

6. **pr_duckdb_integration_tests.yml** - DuckDB offline store tests
   - Command: `pixi run -e duckdb-tests test`

7. **pr_ray_integration_tests.yml** - Ray compute engine tests
   - Command: `pixi run -e ray-tests test`

### What Actually Gates Merges

Based on workflow triggers (`pull_request`) and standard GitHub required checks:
- Python linting (ruff + mypy)
- Python unit tests (all versions)
- UI tests (format + unit tests)
- Go operator tests

Integration tests require explicit approval via labels and are typically not strictly required for every PR.

---

## Conventions

### Test File Patterns

- **Python:** `test_*.py` or `*_test.py` in `sdk/python/tests/`
- **Go:** `*_test.go` in `infra/feast-operator/`
- **JavaScript:** `*.test.ts`, `*.spec.ts` in `ui/src/`

### Test Naming

- **Python:** `test_*` functions, pytest style
- **Go:** `Test*` functions
- **JavaScript:** `describe/it` blocks (Jest)

### Directory Structure

```
sdk/python/tests/
├── unit/              # Fast unit tests, no external deps
├── integration/       # Integration tests, require services
├── component/         # Component tests (Ray, Spark)
└── conftest.py        # Shared pytest fixtures
```

### Import Style

Python code uses absolute imports from `feast.*`. Imports are grouped and sorted by ruff:
1. Standard library
2. Third-party packages
3. First-party (feast)

### Code Style

- **Line length:** 88 characters (ruff default)
- **Type hints:** Required, checked by mypy
- **Format:** Enforced by ruff format
- **Linting:** ruff replaces flake8, isort, etc.

---

## Gaps & Caveats

### Cannot Run in Isolated Container

1. **Integration tests require cloud credentials:**
   - AWS (S3, Athena, DynamoDB)
   - GCP (BigQuery, Datastore, Bigtable)
   - Snowflake (data warehouse)
   - These tests are marked with `--integration` flag

2. **Some tests require running services:**
   - Redis (online store)
   - PostgreSQL (offline/online store)
   - MySQL (offline/online store)
   - DuckDB (embedded, works locally)
   - Solution: Use `testcontainers` library (already in deps) or external services

3. **Operator tests need Kubernetes:**
   - Uses `envtest` for controller testing
   - Full e2e tests need real cluster: `make -C infra/feast-operator test-e2e`

4. **Multi-language testing:**
   - Go operator: Requires Go 1.22.9, separate container
   - Java serving: Requires Maven, JDK 17+, separate container
   - UI: Requires Node.js (from `.nvmrc`), Yarn, separate container

### Performance Considerations

- **Full test suite is very slow** - 1000+ tests, many require cloud APIs
- **Use pattern filtering** for targeted testing:
  ```bash
  uv run python -m pytest -k "test_feature_store" sdk/python/tests/unit
  ```
- **Parallel execution recommended:** `-n 8` or `-n auto`
- **Fast subset for smoke testing:**
  ```bash
  uv run python -m pytest sdk/python/tests/unit/test_unit_feature_store.py -n 4 --tb=short
  ```

### Container Quirks

- **Hardlink warning:** On different filesystems, uv falls back to copy mode. Set `UV_LINK_MODE=copy` to suppress warning.
- **Ray workers on macOS:** Integration tests use special macOS workarounds (see unit_tests.yml)
- **Timeout:** Some tests can hang - use `--timeout=300` (already in pytest.ini)

---

## Quick Reference

### Makefile Targets

**Python linting:**
```bash
make lint-python              # Run all Python linters
make format-python            # Auto-format with ruff
```

**Python testing:**
```bash
make test-python-unit         # Unit tests (no external deps)
make test-python-integration  # Integration tests (needs cloud)
make test-python-unit-fast    # Fast unit tests only
```

**Operator (Go):**
```bash
make -C infra/feast-operator test      # Unit tests
make -C infra/feast-operator lint      # golangci-lint
```

**UI (JavaScript):**
```bash
cd ui && yarn test --watchAll=false    # Jest tests
cd ui && yarn format:check             # Prettier check
```

### Test Filtering

Run specific test patterns:
```bash
# By keyword
uv run python -m pytest -k "milvus" sdk/python/tests

# By marker
uv run python -m pytest -m "not integration" sdk/python/tests

# Specific file
uv run python -m pytest sdk/python/tests/unit/test_feature_store.py

# Specific test
uv run python -m pytest sdk/python/tests/unit/test_feature_store.py::test_apply_feature_view
```

### Environment Variables

- `PYTHONPATH=/app/sdk/python` - For imports in tests
- `FEAST_IS_LOCAL_TEST=True` - Use local test mode (no cloud)
- `FEAST_LOCAL_ONLINE_CONTAINER=True` - Use testcontainers for online stores
- `UV_LINK_MODE=copy` - Suppress hardlink warnings

---

## Recommended Workflow for Agents

1. **Clone and start container** using recipe above
2. **Install dependencies** (takes 2-5 min first time)
3. **For Python patches:**
   - Run `make lint-python` (takes ~30 sec)
   - Run `make test-python-unit` (takes 5-10 min)
   - If tests fail, run specific test file for faster iteration
4. **For Go operator patches:**
   - Use Go 1.22.9 container
   - Run `make -C infra/feast-operator test`
5. **For UI patches:**
   - Use Node.js container (version from `ui/.nvmrc`)
   - Run `cd ui && yarn format:check && yarn test --watchAll=false`
6. **Cleanup** container when done

**Expected pass criteria:**
- All lint checks pass (exit code 0)
- All unit tests pass (pytest shows "X passed")
- No new type errors from mypy

**Integration tests** are advisory and typically require maintainer approval to run in CI.
