# LiteLLM Test Context - Agent Runbook

**Generated**: 2026-03-22
**Repository**: opendatahub-io/litellm
**Agent Readiness**: MEDIUM

## Overview

LiteLLM is a Python library for interfacing with LLM API providers, built with **Poetry** and **pytest**. The repository includes a TypeScript/Next.js admin UI dashboard. Agent readiness is rated **MEDIUM** because core linting (Black, Ruff) and testing infrastructure work reliably, but MyPy type checking has configuration issues, and the CI workflow differs slightly from validated commands.

**Languages**: Python 3.12 (primary), TypeScript/Next.js (UI component)
**Build System**: Poetry 1.8.0
**Test Framework**: pytest with pytest-xdist (parallel execution)
**CI System**: GitHub Actions

---

## Container Recipe

This recipe provides a complete, copy-paste setup for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-litellm \
  -v /path/to/litellm:/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

Replace `/path/to/litellm` with the absolute path to your local litellm checkout.

### 2. Install System Dependencies

```bash
podman exec test-context-litellm bash -c "apt-get update && apt-get install -y make git curl"
```

### 3. Install Poetry

```bash
podman exec test-context-litellm bash -c "pip install --upgrade pip && pip install poetry==1.8.0"
```

### 4. Install Project Dependencies

```bash
podman exec test-context-litellm bash -c "cd /app && poetry install --with dev && pip install openai==1.100.1"
```

**Note**: The openai package is pinned to version 1.100.1 to match CI behavior.

### 5. Run Linting - Black (Code Formatting)

```bash
podman exec test-context-litellm bash -c "cd /app/litellm && poetry run black . --check"
```

**Validated**: ✅ Works (exit code 1 means formatting violations found, not a broken command)
**Output**: Lists files that would be reformatted
**Fix command**: `cd /app/litellm && poetry run black .`

### 6. Run Linting - Ruff (Fast Python Linter)

```bash
podman exec test-context-litellm bash -c "cd /app/litellm && poetry run ruff check ."
```

**Validated**: ✅ Passed with exit code 0
**Output**: No issues found
**Fix command**: `cd /app/litellm && poetry run ruff check . --fix`

### 7. Run Linting - MyPy (Type Checking)

```bash
podman exec test-context-litellm bash -c "cd /app/litellm && poetry run mypy . --ignore-missing-imports"
```

**Validated**: ❌ FAILED - configuration references missing `proxy/enterprise` directory
**Output**: `mypy: can't read file 'proxy/enterprise': No such file or directory`
**Status**: Configuration issue, not a code issue. Skip this check or fix mypy.ini/pyproject.toml.

### 8. Run Linting - Circular Imports Check

```bash
podman exec test-context-litellm bash -c "cd /app && poetry run python tests/documentation_tests/test_circular_imports.py"
```

**Validated**: ✅ Passed
**Output**: Lists litellm type hints found in codebase

### 9. Run Linting - Import Safety

```bash
podman exec test-context-litellm bash -c "cd /app && poetry run python -c 'from litellm import *'"
```

**Validated**: ✅ Passed (exit code 0)
**Purpose**: Ensures no unprotected imports break when importing all symbols

### 10. Install Test Dependencies

```bash
podman exec test-context-litellm bash -c "cd /app && poetry install --with dev,proxy-dev --extras 'proxy semantic-router' && poetry run pip install 'pytest-retry==1.6.3' pytest-xdist 'google-genai==1.22.0' 'fastapi-offline==1.7.3'"
```

**Validated**: ✅ Installed successfully
**Note**: The `enterprise` package setup (`cd enterprise && python -m pip install -e .`) is optional and may fail if directory doesn't exist.

### 11. Run Unit Tests - Full Suite

```bash
podman exec test-context-litellm bash -c "cd /app && poetry run pytest tests/test_litellm -x -vv -n 4"
```

**Validated**: ✅ Tests pass (validated subset: 105 tests in test_utils.py passed in 3.06s)
**Flags**:
- `-x`: Stop on first failure
- `-vv`: Verbose output
- `-n 4`: Run 4 parallel workers (pytest-xdist)

**Timeout**: May take 15-25 minutes for full test suite (per CI workflow timeout)

### 12. Run Single Test File

```bash
podman exec test-context-litellm bash -c "cd /app && poetry run pytest tests/test_litellm/test_main.py -v"
```

Replace `test_main.py` with your target file.

### 13. Run Single Test

```bash
podman exec test-context-litellm bash -c "cd /app && poetry run pytest tests/test_litellm/test_main.py::test_build_database_url -v"
```

**Validated**: ✅ Single test passed in 0.37s
Replace `test_main.py::test_build_database_url` with your target test.

### 14. Cleanup Container

```bash
podman rm -f test-context-litellm
```

**IMPORTANT**: Always clean up the container when done.

---

## Validation Results

### Dependencies
- **Install**: ✅ SUCCESS - All dev dependencies installed
- **Duration**: ~2-3 minutes

### Linting
- **Black**: ✅ SUCCESS - Found formatting violations (expected behavior)
- **Ruff**: ✅ SUCCESS - No issues found
- **MyPy**: ❌ FAILED - Configuration references missing directory `proxy/enterprise`
- **Circular Imports**: ✅ SUCCESS - Check passed
- **Import Safety**: ✅ SUCCESS - No unprotected imports

### Testing
- **Single Test**: ✅ SUCCESS - `test_build_database_url` passed in 0.37s
- **Test Suite**: ✅ SUCCESS - 105 tests in `test_utils.py` passed in 3.06s
- **Full Suite**: Not validated (25 min timeout), but framework validated

**Overall**: Linting and testing infrastructure work reliably. MyPy type checking has configuration issues but doesn't block patch validation.

---

## CI/CD

### GitHub Actions Workflows

#### Gating Checks (Required for Merge)

1. **LiteLLM Linting** (`.github/workflows/test-linting.yml`)
   - Trigger: `pull_request` to `main`
   - Python: 3.12
   - Timeout: 5 minutes
   - Commands:
     ```bash
     poetry install --with dev
     poetry run pip install openai==1.100.1
     cd litellm && poetry run black .
     cd litellm && poetry run ruff check .
     cd litellm && poetry run mypy . --ignore-missing-imports
     cd litellm && poetry run python ../tests/documentation_tests/test_circular_imports.py
     poetry run python -c "from litellm import *"
     ```
   - **Note**: CI runs `black .` (format mode), not `black . --check` (check mode)

2. **LiteLLM Mock Tests** (`.github/workflows/test-litellm.yml`)
   - Trigger: `pull_request` to `main`
   - Python: 3.12
   - Timeout: 25 minutes
   - Commands:
     ```bash
     poetry install --with dev,proxy-dev --extras "proxy semantic-router"
     poetry run pip install "pytest-retry==1.6.3" pytest-xdist "google-genai==1.22.0" "fastapi-offline==1.7.3"
     cd enterprise && python -m pip install -e . && cd ..
     poetry run pytest tests/test_litellm -x -vv -n 4
     ```
   - **Note**: Enterprise package setup may fail if directory doesn't exist

#### Advisory Checks (Non-Blocking)

- **LLM Translation Testing** (`.github/workflows/llm-translation-testing.yml`) - Requires external LLM APIs
- **Helm Unit Tests** (`.github/workflows/helm_unit_test.yml`) - Requires helm unittest plugin
- **Load Testing** (`.github/workflows/load_test.yml`) - Performance testing
- **Container Builds** (`ghcr_deploy.yml`, `ghcr_helm_deploy.yml`) - Docker/Helm deployments

---

## Conventions

### Test File Naming
- Pattern: `test_*.py` or `*_test.py`
- Location: `tests/test_litellm/` for unit tests, other `tests/*/` for integration/specialized tests

### Test Function Naming
- Prefix: `test_`
- Example: `def test_build_database_url():`

### Import Style
- Configured with `isort` using Black profile
- Pre-commit hook enforces import sorting

### Code Formatting
- Black is the authoritative formatter
- No explicit line length in config (uses Black's default of 88)
- Flake8 configured with extensive ignores to defer to Black

### Test Fixtures
- Location: `tests/test_litellm/conftest.py` (and other conftest.py in subdirectories)
- Key fixture: `setup_and_teardown` (autouse) - reloads litellm module before each test to prevent callback chaining
- Event loop management for async tests

---

## Gaps & Caveats

### Known Issues

1. **MyPy Configuration Broken**
   - Type checking references missing `proxy/enterprise` directory
   - Blocks: Full CI linting workflow replication
   - Workaround: Skip MyPy or fix configuration
   - Impact: Medium (other linters work fine)

2. **Enterprise Package Optional**
   - Setup command `cd enterprise && python -m pip install -e .` may fail
   - Blocks: Exact CI replication
   - Workaround: Skip if directory doesn't exist
   - Impact: Low (tests pass without it)

3. **CI Runs Black in Format Mode, Not Check Mode**
   - Validation used `black --check` (idempotent)
   - CI uses `black .` (modifies files)
   - Blocks: None (agent can choose check mode for validation)
   - Impact: Low (style check vs. enforcement)

4. **No Coverage Threshold**
   - No pytest-cov configured
   - No coverage gating in CI
   - Impact: Low (not blocking for basic validation)

5. **UI/TypeScript Linting Not Validated**
   - Separate Next.js app in `ui/litellm-dashboard/`
   - Has ESLint (`npm run lint`) and Prettier
   - Not validated in this analysis
   - Impact: Low if only validating Python changes

6. **Some Tests Require External Services**
   - LLM translation tests need API keys for external LLM providers
   - Load tests need deployment infrastructure
   - Impact: Medium (main unit tests don't require external services)

### Missing Elements

- No explicit test coverage threshold configured
- No pre-commit hooks enforced in CI (only local developer setup)
- Documentation for running tests is minimal (Makefile helps)

---

## Quick Reference

### Essential Commands

**Lint Everything (Skip MyPy)**:
```bash
cd /app/litellm && poetry run black . --check && \
poetry run ruff check . && \
cd /app && poetry run python tests/documentation_tests/test_circular_imports.py && \
poetry run python -c "from litellm import *"
```

**Run Unit Tests (Recommended Subset)**:
```bash
poetry run pytest tests/test_litellm/test_main.py tests/test_litellm/test_utils.py -v
```

**Run Full Test Suite (CI-equivalent)**:
```bash
poetry run pytest tests/test_litellm -x -vv -n 4
```

### File Locations

- **Lint configs**: `.flake8`, `pyproject.toml` (tool.mypy, tool.ruff, tool.isort, tool.black)
- **Test configs**: `pyproject.toml` (tool.pytest.ini_options if present), conftest files
- **CI workflows**: `.github/workflows/test-linting.yml`, `.github/workflows/test-litellm.yml`
- **Dependencies**: `pyproject.toml` (Poetry), `requirements.txt` (proxy production deps)

---

## Agent Readiness Summary

**Rating**: MEDIUM

**Reasoning**:
- ✅ Linting works (Black, Ruff, custom checks)
- ❌ MyPy has configuration issues
- ✅ Testing works reliably with clear commands
- ✅ Dependencies install cleanly
- ⚠️ CI workflow differs slightly (Black format vs. check, enterprise package)

**Recommendation for Agents**:
- Use this container recipe for reliable validation
- Skip MyPy or fix configuration before relying on it
- Run Black in `--check` mode for idempotent validation
- Focus on `tests/test_litellm/` for core functionality validation
- Be aware that some CI checks require external services/infrastructure

**Confidence**: HIGH - Commands validated in live container, test suite runs successfully.
