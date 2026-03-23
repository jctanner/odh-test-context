# Test Context for llama-stack-client-python

**Agent Readiness: MEDIUM** - Linting and build commands fully validated. Tests exist and run but require mock infrastructure for full pass rate.

## Overview

- **Repository**: opendatahub-io/llama-stack-client-python
- **Language**: Python 3.12+
- **Build System**: uv (modern Python package manager) with hatchling
- **Test Framework**: pytest with pytest-asyncio, pytest-xdist
- **Linting**: ruff (linter + formatter), mypy, pyright
- **CI System**: GitHub Actions (pre-commit.yml gates PRs)

This is a Python SDK client library with 2765+ unit tests. The official test script is disabled due to OpenAPI spec issues with mock servers, but pytest works directly with partial success (121/137 tests pass without infrastructure).

## Container Recipe

### 1. Start Container

```bash
podman run -d --name test-context-llama-stack-client-python \
  -v /path/to/llama-stack-client-python:/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

Replace `/path/to/llama-stack-client-python` with the actual repository path.

### 2. Install System Dependencies

```bash
podman exec test-context-llama-stack-client-python bash -c \
  "apt-get update && apt-get install -y curl git ca-certificates"
```

Note: These are already present in python:3.12 image.

### 3. Install uv Package Manager

```bash
podman exec test-context-llama-stack-client-python bash -c \
  "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

This installs uv to `$HOME/.local/bin/`.

### 4. Install Project Dependencies

```bash
podman exec test-context-llama-stack-client-python bash -c \
  "export PATH=\"\$HOME/.local/bin:\$PATH\" && cd /app && uv sync --all-extras"
```

**Expected Output**: Installs 70 packages in ~700ms. Creates `.venv/` virtual environment.

**Validation Result**: ✅ SUCCESS - Installed 70 packages successfully.

### 5. Build Project

```bash
podman exec test-context-llama-stack-client-python bash -c \
  "export PATH=\"\$HOME/.local/bin:\$PATH\" && cd /app && uv build"
```

**Expected Output**:
```
Building source distribution...
Building wheel from source distribution...
Successfully built dist/llama_stack_client-0.3.0a6.tar.gz
Successfully built dist/llama_stack_client-0.3.0a6-py3-none-any.whl
```

**Validation Result**: ✅ SUCCESS - Build creates both .tar.gz and .whl.

### 6. Run Linter (Ruff)

```bash
podman exec test-context-llama-stack-client-python bash -c \
  "export PATH=\"\$HOME/.local/bin:\$PATH\" && cd /app && uv run ruff check ."
```

**Expected Output**: May report lint violations (fixable with `--fix`).

**Validation Result**: ✅ SUCCESS - Found 4 lint issues (expected behavior).
- Exit code 1 means violations found, not command failure
- All 4 issues are auto-fixable with `uv run ruff check --fix .`

**Auto-fix Command**:
```bash
podman exec test-context-llama-stack-client-python bash -c \
  "export PATH=\"\$HOME/.local/bin:\$PATH\" && cd /app && uv run ruff check --fix ."
```

### 7. Run Formatter (Ruff Format)

```bash
podman exec test-context-llama-stack-client-python bash -c \
  "export PATH=\"\$HOME/.local/bin:\$PATH\" && cd /app && uv run ruff format"
```

**Validation Result**: ✅ SUCCESS - Formatter available and functional.

### 8. Test Package Import

```bash
podman exec test-context-llama-stack-client-python bash -c \
  "export PATH=\"\$HOME/.local/bin:\$PATH\" && cd /app && uv run python -c 'import llama_stack_client' && echo 'Import successful'"
```

**Validation Result**: ✅ SUCCESS - Package imports correctly.

### 9. Run Tests

**Full test suite (2765+ tests)**:
```bash
podman exec test-context-llama-stack-client-python bash -c \
  "export PATH=\"\$HOME/.local/bin:\$PATH\" && cd /app && uv run pytest tests/ --tb=short -n auto"
```

**Single test file**:
```bash
podman exec test-context-llama-stack-client-python bash -c \
  "export PATH=\"\$HOME/.local/bin:\$PATH\" && cd /app && uv run pytest tests/test_client.py -v --tb=short"
```

**Single test**:
```bash
podman exec test-context-llama-stack-client-python bash -c \
  "export PATH=\"\$HOME/.local/bin:\$PATH\" && cd /app && uv run pytest tests/test_client.py::TestLlamaStackClient::test_copy -v --tb=short"
```

**Validation Result**: ⚠️ PARTIAL SUCCESS
- For `tests/test_client.py`: 121 passed, 14 failed, 2 skipped (3.83s)
- Failed tests require mock Prism server on `http://127.0.0.1:4010`
- Test framework works correctly; failures are due to missing infrastructure
- Official `./scripts/test` is disabled (exits 0) due to OpenAPI spec issues

### 10. Cleanup

```bash
podman rm -f test-context-llama-stack-client-python
```

**Always run this**, even if validation steps fail.

## Validation Results Summary

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install | `uv sync --all-extras` | ✅ PASS | 70 packages installed |
| Build | `uv build` | ✅ PASS | Created .tar.gz and .whl |
| Lint | `uv run ruff check .` | ✅ PASS | Found 4 fixable issues (expected) |
| Import | `uv run python -c 'import llama_stack_client'` | ✅ PASS | Package imports correctly |
| Test | `uv run pytest tests/test_client.py` | ⚠️ PARTIAL | 121/137 passed without mock server |

## CI/CD

### Gating Checks (Block PRs)

**Pre-commit workflow** (`.github/workflows/pre-commit.yml`):
- Triggered on: `pull_request`, `push` to `main`
- Runs: `pre-commit run --all-files`
- Includes: ruff (linter), ruff-format, check-merge-conflict, check-added-large-files, end-of-file-fixer

### Advisory Checks (Manual Trigger Only)

**CI workflow** (`.github/workflows/ci.yml`):
- Triggered on: `workflow_dispatch` (manual only, NOT on PRs)
- Jobs:
  1. **lint**: `./scripts/lint` (runs `uv run ruff check .` + import test)
  2. **build**: `uv build`
  3. **test**: `./scripts/test` (currently disabled, exits 0)

**Important**: The ci.yml workflow does NOT run on pull requests. Only pre-commit.yml gates PRs.

## Conventions

### Test Files
- Pattern: `test_*.py` or `*_test.py`
- Location: `tests/` directory
- Naming: `test_*` functions, `Test*` classes
- Total: 2765+ tests across multiple files

### Code Style
- Line length: 120 characters
- Linter: ruff with isort rules
- Formatter: ruff format
- Type checking: mypy (strict mode), pyright
- Import sorting: length-sort, combine-as-imports
- Known first-party: `llama_stack_client`, `tests`

### Test Configuration
- Framework: pytest with plugins (pytest-asyncio, pytest-xdist, respx, time-machine)
- Parallel execution: `-n auto` (pytest-xdist)
- Async mode: `asyncio_mode = "auto"`
- Warnings: treated as errors (`filterwarnings = ["error"]`)
- Fixtures: `tests/conftest.py`

## Gaps & Caveats

1. **Official test script disabled**: `./scripts/test` exits immediately with code 0 and message:
   ```
   Tests are currently disabled because the OpenAPI spec has quite a few 'issues'
   resulting in none of the auto-mock servers working.
   ```

2. **Mock server requirement**: Full test suite needs Prism mock server on port 4010. Without it:
   - 121 tests pass
   - 14 tests fail (retry behavior tests)
   - 2 tests skip
   - This is for `test_client.py` only; full suite has 2765+ tests

3. **Mypy commented out**: The `./scripts/lint` script has mypy commented out (line 10-11). Type checking not enforced in CI lint job, though mypy config exists in pyproject.toml.

4. **No coverage tracking**: No coverage command or threshold configured.

5. **CI workflow quirk**: `ci.yml` only runs on `workflow_dispatch` (manual trigger), not on pull requests. Pre-commit.yml is the only PR-blocking workflow.

6. **Multi-version testing**: Official test script runs tests with both Pydantic v1 and v2, and Python 3.13. Simple `pytest` command only tests current environment.

## Recommended Patch Validation Workflow

For validating patches to this repository:

1. **Lint check** (required, fast):
   ```bash
   uv run ruff check .
   ```
   Exit code 0 = clean, exit code 1 = violations found.

2. **Auto-fix lint issues** (optional):
   ```bash
   uv run ruff check --fix .
   uv run ruff format
   ```

3. **Build check** (required):
   ```bash
   uv build
   ```
   Ensures package is buildable.

4. **Import check** (required):
   ```bash
   uv run python -c 'import llama_stack_client'
   ```
   Ensures no import-time errors.

5. **Test subset** (recommended):
   ```bash
   uv run pytest tests/test_client.py -v --tb=short
   ```
   Runs 137 tests in ~4s. Expect 121 pass, 14 fail without mock server.

6. **Full test suite** (optional, slow):
   ```bash
   uv run pytest tests/ --tb=short -n auto
   ```
   Runs all 2765+ tests. Requires significant time and may need mock infrastructure.

## Environment Variables

- `PATH="$HOME/.local/bin:$PATH"` - Required for uv commands in container
- `UV_LINK_MODE=copy` - Suppresses hardlink warnings in containers
- `TEST_API_BASE_URL` - Optional, overrides mock server requirement for tests
- `UV_PYTHON` - Optional, specify Python version (e.g., `3.13`)
- `DEFER_PYDANTIC_BUILD=false` - Used in official test script

## Quick Reference

### Essential Commands

```bash
# Setup
uv sync --all-extras

# Lint
uv run ruff check .

# Lint + fix
uv run ruff check --fix .

# Format
uv run ruff format

# Build
uv build

# Test single file
uv run pytest tests/test_client.py -v --tb=short

# Test full suite
uv run pytest tests/ --tb=short -n auto

# Import check
uv run python -c 'import llama_stack_client'
```

### Pre-commit Hooks

```bash
# Run pre-commit checks (same as CI)
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
```

## Container Recipe Summary

**Base Image**: `python:3.12`

**Setup**:
1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Install deps: `uv sync --all-extras`

**Validation Commands** (all working):
- Lint: `uv run ruff check .` ✅
- Build: `uv build` ✅
- Test: `uv run pytest tests/test_client.py -v --tb=short` ⚠️ (121/137 pass)

**Agent Readiness**: MEDIUM - An agent can validate lint and build. Tests run but require mock infrastructure for full coverage.
