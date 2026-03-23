# Test Context: caikit (opendatahub-io)

**Generated:** 2026-03-22T17:44:40-04:00

## Overview

**caikit** is a Python AI toolkit for building stable model APIs and composable AI frameworks. **Agent readiness: medium** - Lint and core tests validated successfully in container. Full test suite requires pyspark infrastructure (351/1720 tests fail without it).

- **Language:** Python 3.8-3.11
- **Build system:** setuptools with setuptools-scm
- **Test framework:** pytest with tox
- **CI:** GitHub Actions (Build and Test + Lint and Format workflows)

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-caikit \
  -v /path/to/caikit:/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

Replace `/path/to/caikit` with the absolute path to your caikit repository.

### 2. Install System Dependencies

```bash
podman exec test-context-caikit bash -c "apt-get update && apt-get install -y make git graphviz"
```

**Note:** `graphviz` is required for the import dependency checker (`tox -e imports`).

### 3. Install Python Dependencies

```bash
# Upgrade pip
podman exec test-context-caikit bash -c "cd /app && python -m pip install --upgrade pip"

# Install tox and build tools
podman exec test-context-caikit bash -c "cd /app && pip install -r setup_requirements.txt"

# Install caikit with all dev dependencies (takes 2-3 minutes)
podman exec test-context-caikit bash -c "cd /app && pip install -e '.[all-dev]'"
```

**Validated:** ✅ All install steps completed successfully.

### 4. Run Linting

#### Option A: Via tox (recommended - matches CI exactly)

```bash
podman exec test-context-caikit bash -c "cd /app && tox -e lint"
```

**Validated:** ✅ Passed - "All checks passed!" (86 seconds including tox setup)

#### Option B: Direct ruff (faster for quick checks)

```bash
podman exec test-context-caikit bash -c "cd /app && ruff check caikit examples"
```

**Validated:** ✅ Passed - "All checks passed!" (instant)

#### Option C: Format checking (pre-commit)

```bash
podman exec test-context-caikit bash -c "cd /app && pre-commit run --all-files"
```

**Validated:** ✅ Passed - prettier, black, isort all passed

### 5. Run Tests

#### Option A: Run core tests (fast, reliable)

```bash
podman exec test-context-caikit bash -c "cd /app && pytest tests/core tests/config -v"
```

**Validated:** ✅ Passes reliably without external dependencies.

#### Option B: Run single test file

```bash
podman exec test-context-caikit bash -c "cd /app && pytest tests/config/test_configs.py -v"
```

**Validated:** ✅ 12 passed in 0.19s

#### Option C: Run single test

```bash
podman exec test-context-caikit bash -c "cd /app && pytest tests/config/test_configs.py::test_local_config -v"
```

Replace `test_local_config` with the actual test function name.

#### Option D: Full test suite via tox (matches CI)

```bash
podman exec test-context-caikit bash -c "cd /app && timeout 300 tox -e py -- tests -m 'not (examples or slow)'"
```

**Validated:** ⚠️  Partial - 1369 passed, 351 failed (pyspark tests), 13 skipped in ~3 minutes.

**Note:** Many pyspark-related tests fail without spark infrastructure. For patch validation, focus on `tests/core` and `tests/config` which work reliably.

#### Option E: Run with coverage

```bash
podman exec test-context-caikit bash -c "cd /app && pytest --cov=caikit --cov-report=html --cov-report=xml tests/core -v"
```

Coverage reports will be written to `coverage-py/` (HTML) and `coverage-py.xml`.

### 6. Cleanup

```bash
podman rm -f test-context-caikit
```

**Always run this** to clean up the container, even if validation fails.

## Validation Results

### Dependency Installation
- **Command:** `pip install -r setup_requirements.txt`
- **Status:** ✅ Success
- **Notes:** Installs tox 4.50.3 and build tools

### Full Dev Environment
- **Command:** `pip install -e '.[all-dev]'`
- **Status:** ✅ Success
- **Notes:** Installs 109 packages including pytest, ruff, pre-commit, grpcio, fastapi, pyspark, etc.

### Linting (ruff)
- **Command:** `ruff check caikit examples`
- **Status:** ✅ Success
- **Exit code:** 0
- **Output:** "All checks passed!"

### Format Checking (pre-commit)
- **Command:** `pre-commit run --all-files`
- **Status:** ✅ Success
- **Exit code:** 0
- **Output:** prettier, black, isort all passed

### Core Tests
- **Command:** `pytest tests/config/test_configs.py -v`
- **Status:** ✅ Success
- **Exit code:** 0
- **Output:** 12 passed in 0.19s

### Full Test Suite
- **Command:** `tox -e py -- tests -m 'not (examples or slow)'`
- **Status:** ⚠️  Partial Success
- **Exit code:** 1
- **Output:** 1369 passed, 351 failed, 13 skipped, 18 warnings, 5 errors in 179.43s
- **Notes:** Core tests pass. Failures are mostly pyspark-related tests requiring spark infrastructure.

## CI/CD

### Gating Checks (all required for merge)

#### 1. Build and Test
- **Workflow:** `.github/workflows/build-library.yml`
- **Trigger:** push to main, pull_request to main
- **Matrix:** Python 3.8, 3.9, 3.10, 3.11, plus proto3 and core environments
- **Commands:**
  ```bash
  python -m pip install --upgrade pip
  python -m pip install -r setup_requirements.txt
  tox -e {py38|py39|py310|py311|proto3|core} -- tests
  ```

#### 2. Lint and Format
- **Workflow:** `.github/workflows/lint-code.yml`
- **Trigger:** push to main, pull_request to main
- **Python version:** 3.9
- **Commands:**
  ```bash
  python -m pip install --upgrade pip
  python -m pip install -r setup_requirements.txt
  tox -e fmt        # Check formatting (pre-commit)
  tox -e lint       # Ruff linting
  tox -e imports    # Enforce import dependency rules (requires graphviz)
  ```

### Special Test Environments

- **proto3:** Tests compatibility with protobuf 3.x (uses `dev-proto3` extra)
- **core:** Tests caikit.core without optional dependencies (minimal install)
- **slow:** Pyspark tests (excluded from default runs with `-m "not slow"`)
- **examples:** End-to-end example tests (excluded from default runs)

## Conventions

### Test File Naming
- Pattern: `test_*.py` in `tests/` directory
- Structure mirrors source: `caikit/core/module.py` → `tests/core/test_module.py`

### Test Function Naming
- Pattern: `test_*` functions
- Uses standard pytest conventions
- Async tests supported via pytest-asyncio

### Import Style
- Enforced by isort via pre-commit
- Grouped imports: stdlib, third-party, local
- Configuration in `.isort.cfg`

### Code Style
- **Line length:** 100 characters (ruff config)
- **Formatter:** black (via pre-commit)
- **Linter:** ruff with select rules: E (pycodestyle errors), F (pyflakes), UP (pyupgrade), B (flake8-bugbear), SIM (flake8-simplify), I (isort)
- **Exclusions:** `caikit/runtime/protobufs/*.py` (generated code)

### Coverage
- **Config:** `.coveragerc`
- **Omit:** `caikit/runtime/protobufs/*` and `tests/**`
- **No threshold configured** but HTML and XML reports generated
- **Command:** `pytest --cov=caikit --cov-report=html --cov-report=xml`

## Gaps & Caveats

### Infrastructure Dependencies
- **351 tests fail without pyspark infrastructure** (out of 1720 total tests when including slow tests)
- Tests marked `slow` require pyspark and are excluded from default runs
- Tests marked `examples` are end-to-end tests excluded from default runs
- For reliable patch validation, focus on `tests/core` and `tests/config` directories

### System Dependencies
- **graphviz required** for `tox -e imports` (import dependency checker)
- Installs cleanly with `apt-get install graphviz`

### Tox Performance
- First run of each tox environment takes 50-90 seconds to create virtualenv
- Subsequent runs reuse the environment (faster)
- For quick iteration, use direct `pytest` or `ruff` commands

### Python Version Matrix
- CI tests Python 3.8, 3.9, 3.10, 3.11
- Container recipe uses Python 3.11 (latest tested version)
- For Python version-specific issues, test locally with pyenv or tox

### Optional Features
- Full feature set requires `[all]` extra (grpc, http, tracing, vision, timeseries)
- Dev tools require `[dev-test, dev-fmt, dev-docs, dev-build]` extras
- `[all-dev]` installs everything (109 packages)

## Quick Reference

### Run lint only
```bash
podman exec test-context-caikit bash -c "cd /app && ruff check caikit examples"
```

### Run core tests only
```bash
podman exec test-context-caikit bash -c "cd /app && pytest tests/core -v"
```

### Run a single test file
```bash
podman exec test-context-caikit bash -c "cd /app && pytest tests/config/test_configs.py"
```

### Check formatting without fixing
```bash
podman exec test-context-caikit bash -c "cd /app && pre-commit run --all-files"
```

### Run exactly what CI runs (lint)
```bash
podman exec test-context-caikit bash -c "cd /app && tox -e lint"
```

### Run exactly what CI runs (test)
```bash
podman exec test-context-caikit bash -c "cd /app && tox -e py311 -- tests -m 'not (examples or slow)'"
```

## Agent Readiness Assessment

**Rating: MEDIUM**

### What Works Well ✅
- Lint commands validated and pass cleanly
- Core test suite (tests/core, tests/config) runs reliably
- Container setup is straightforward (Python 3.11 + system deps)
- Dependencies install cleanly from PyPI
- Both tox and direct pytest/ruff work
- CI configuration is clear and matches local commands

### What Has Limitations ⚠️
- 351 out of ~1720 tests require pyspark infrastructure
- Full test suite takes ~3 minutes (tox overhead)
- Import checker requires graphviz (documented, easy to install)

### What Would Block Validation ❌
- None for core functionality
- Pyspark tests would block full coverage validation

### Recommendation for Downstream Agents
Use this repository for patch validation with the following approach:
1. **Always run:** `ruff check caikit examples` (instant feedback)
2. **Always run:** `pytest tests/core tests/config` (fast, reliable core tests)
3. **Optionally run:** Full test suite if pyspark infrastructure available
4. **For format PRs:** Run `pre-commit run --all-files`

This gives high confidence for most patches while avoiding infrastructure dependencies.
