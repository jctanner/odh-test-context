# Test Context: gpt-researcher

**Agent Readiness: LOW** - Tests require external API keys and linting is not configured. Limited automated validation possible.

## Overview

- **Repository**: opendatahub-io/gpt-researcher
- **Primary Language**: Python 3.11+
- **Build System**: pip/Poetry (hybrid setup.py + pyproject.toml)
- **Test Framework**: pytest with pytest-asyncio
- **CI System**: GitHub Actions (tests disabled for PRs)
- **Analyzed**: 2026-03-22T18:17:00Z

This repository is a Python project for GPT-powered research agents. Most tests are integration tests requiring OPENAI_API_KEY and TAVILY_API_KEY, making automated validation challenging without API access. No linting tools are configured.

---

## Container Recipe

This is the **validated, executable recipe** for running tests in an isolated container.

### 1. Start Container

```bash
podman run -d \
  --name test-context-gpt-researcher \
  -v /path/to/gpt-researcher:/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-gpt-researcher bash -c \
  "apt-get update && apt-get install -y git build-essential"
```

### 3. Install Python Dependencies

```bash
# Upgrade pip
podman exec test-context-gpt-researcher bash -c \
  "pip install --upgrade pip"

# Install test framework
podman exec test-context-gpt-researcher bash -c \
  "pip install pytest pytest-asyncio"

# Install project dependencies (takes 2-3 minutes)
podman exec test-context-gpt-researcher bash -c \
  "pip install -r /app/requirements.txt"

# Install additional test dependencies
podman exec test-context-gpt-researcher bash -c \
  "pip install faiss-cpu"

# Install project in editable mode
podman exec test-context-gpt-researcher bash -c \
  "pip install -e /app"
```

**Expected Result**: ~200 packages installed successfully. Warnings about `requests` dependency versions are non-blocking.

### 4. Run Tests (Unit Tests - No API Keys Required)

```bash
# Run unit tests that work without API keys
podman exec test-context-gpt-researcher bash -c \
  "cd /app && PYTHONPATH=/app:/app/backend python -m pytest tests/test_logging.py tests/test_logs.py -v"
```

**Expected Result**: `3 passed, 1 warning in ~0.7s`
- test_logging.py::test_custom_logs_handler PASSED
- test_logging.py::test_content_update PASSED
- test_logs.py::test_logs_creation PASSED

### 5. Run Integration Tests (Require API Keys)

```bash
# These will FAIL without OPENAI_API_KEY set
podman exec test-context-gpt-researcher bash -c \
  "cd /app && PYTHONPATH=/app:/app/backend python -m pytest tests/report-types.py -v"
```

**Expected Result**: `2 failed` with error: `openai.OpenAIError: The api_key client option must be set`

To run with API keys (if available):
```bash
podman exec -e OPENAI_API_KEY=sk-... -e TAVILY_API_KEY=... test-context-gpt-researcher bash -c \
  "cd /app && PYTHONPATH=/app:/app/backend python -m pytest tests/report-types.py -v"
```

### 6. Run Single Test File

```bash
podman exec test-context-gpt-researcher bash -c \
  "cd /app && PYTHONPATH=/app:/app/backend python -m pytest tests/test_logging.py -v"
```

### 7. Run Single Test

```bash
podman exec test-context-gpt-researcher bash -c \
  "cd /app && PYTHONPATH=/app:/app/backend python -m pytest tests/test_logging.py::test_custom_logs_handler -v"
```

### 8. Cleanup

```bash
podman rm -f test-context-gpt-researcher
```

---

## Validation Results

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| **Install Deps** | `pip install -r requirements.txt` | 0 | ✅ PASS | 200+ packages installed successfully |
| **Install Test Deps** | `pip install pytest pytest-asyncio faiss-cpu` | 0 | ✅ PASS | Test framework ready |
| **Install Package** | `pip install -e .` | 0 | ✅ PASS | gpt-researcher package installed |
| **Unit Tests** | `pytest tests/test_logging.py tests/test_logs.py` | 0 | ✅ PASS | 3 tests passed |
| **Integration Tests** | `pytest tests/report-types.py` | 1 | ⚠️ EXPECTED FAIL | Requires OPENAI_API_KEY (not available) |

**Summary**: Dependencies install cleanly. Unit tests pass. Integration tests fail as expected without API keys.

---

## CI/CD Configuration

### GitHub Actions Workflows

**File**: `.github/workflows/docker-build.yml`
- **Trigger**: `workflow_dispatch` (manual only - **PR triggers commented out**)
- **Purpose**: Run tests via docker-compose
- **Command**:
  ```bash
  docker-compose --profile test run --rm gpt-researcher-tests
  ```
  This runs:
  ```bash
  pip install pytest pytest-asyncio faiss-cpu && \
  python -m pytest tests/report-types.py && \
  python -m pytest tests/vector-store.py
  ```
- **Status**: ❌ **NOT GATING** - Tests do not run on pull requests

**File**: `.github/workflows/build.yml`
- **Trigger**: `push` to master branch
- **Purpose**: Build and push Docker image to AWS ECR
- **Command**: `docker build` + `docker push`
- **Status**: No testing or linting performed

**File**: `.github/workflows/deploy.yml`
- **Purpose**: Deploy to AWS infrastructure
- **Status**: Not relevant for testing

### Key Findings

- ⚠️ **No gating checks configured** - PRs can merge without passing tests
- ⚠️ **Test workflow disabled for PRs** - Only manual `workflow_dispatch` trigger
- ⚠️ **Only 2 test files run in CI** - Not the full test suite
- ⚠️ **Both CI tests require API keys** - report-types.py and vector-store.py need OPENAI_API_KEY

---

## Linting

**Status**: ❌ **NOT CONFIGURED**

No linting tools found:
- ❌ No ruff configuration
- ❌ No flake8 configuration
- ❌ No pylint configuration
- ❌ No mypy configuration
- ❌ No black configuration
- ❌ No pre-commit hooks

**Recommendation**: Add ruff for modern Python linting:
```toml
# Add to pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "UP"]
```

---

## Testing

### Framework

- **Tool**: pytest 9.0.2
- **Async Support**: pytest-asyncio
- **Config**: `pyproject.toml` (lines 54-59)

```toml
[tool.pytest.ini_options]
asyncio_mode = "strict"
addopts = "-v"
testpaths = ["tests"]
python_files = "test_*.py"
asyncio_fixture_loop_scope = "function"  # Warning: unknown config option
```

### Test Inventory

```
tests/
├── test_logging.py              (2 tests, ✅ unit, no API keys)
├── test_logs.py                 (1 test,  ✅ unit, no API keys)
├── test_logging_output.py       (1 test,  ⚠️ requires API keys)
├── test_researcher_logging.py   (⚠️ requires API keys)
├── test_quick_search.py         (⚠️ requires API keys)
├── test_mcp.py                  (⚠️ requires OPENAI_API_KEY, TAVILY_API_KEY)
├── report-types.py              (2 tests, ⚠️ requires API keys - run by CI)
├── vector-store.py              (⚠️ requires API keys - run by CI)
├── test_security_fix.py         (❌ broken - imports non-existent functions)
├── research_test.py             (⚠️ requires API keys)
└── test-*.py                    (utility/manual test scripts)
```

### Running Tests

**All unit tests (no API keys needed):**
```bash
PYTHONPATH=/app:/app/backend python -m pytest \
  tests/test_logging.py \
  tests/test_logs.py \
  -v
```

**Single test file:**
```bash
PYTHONPATH=/app:/app/backend python -m pytest tests/test_logging.py -v
```

**Single test:**
```bash
PYTHONPATH=/app:/app/backend python -m pytest tests/test_logging.py::test_custom_logs_handler -v
```

**With API keys (for integration tests):**
```bash
export OPENAI_API_KEY=sk-...
export TAVILY_API_KEY=tvly-...
export PYTHONPATH=/app:/app/backend
python -m pytest tests/report-types.py -v
```

### Critical Requirements

⚠️ **PYTHONPATH must be set**: Tests import from `backend` and `gpt_researcher` modules which require `PYTHONPATH=/app:/app/backend` to resolve correctly.

### Test Dependencies

Required packages (installed separately from requirements.txt):
- `pytest`
- `pytest-asyncio`
- `faiss-cpu` (for vector store tests)

---

## Build & Development Setup

### Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Using Poetry (if preferred)
poetry install
```

### Install in Development Mode

```bash
pip install -e .
```

### Docker Build

```bash
docker build -t gptresearcher/gpt-researcher .
```

**Base Image**: `python:3.12-slim-bookworm` (Dockerfile line 3)

**System Dependencies** (from Dockerfile):
- chromium + chromium-driver
- firefox-esr + geckodriver
- build-essential

### Environment Variables

Required for testing:
- `OPENAI_API_KEY` - OpenAI API key (most tests)
- `TAVILY_API_KEY` - Tavily search API key (search tests)
- `LANGCHAIN_API_KEY` - Optional, for langchain integration
- `PYTHONPATH=/app:/app/backend` - For module imports

Optional (application runtime):
- `GOOGLE_API_KEY` - For image generation
- `IMAGE_GENERATION_ENABLED` - Enable/disable image generation
- `LOGGING_LEVEL` - Log level (default: INFO)

---

## Conventions

### Test Files

- **Pattern**: `test_*.py` (preferred) or `test-*.py` (some files)
- **Location**: `tests/` directory
- **Inconsistency**: Mix of underscores (test_logging.py) and hyphens (test-loaders.py)

### Test Functions

- **Naming**: `test_*` prefix
- **Async Tests**: Decorated with `@pytest.mark.asyncio`
- **Parametrized**: Use `@pytest.mark.parametrize` for multiple test cases

Example:
```python
@pytest.mark.asyncio
@pytest.mark.parametrize("report_type", ["research_report", "subtopic_report"])
async def test_gpt_researcher(report_type):
    # Test implementation
```

### Imports

Tests use absolute imports from project packages:
```python
from backend.server.server_utils import CustomLogsHandler
from gpt_researcher.agent import GPTResearcher
```

### Mocking

Uses `unittest.mock.AsyncMock` for async dependencies:
```python
from unittest.mock import AsyncMock
mock_websocket = AsyncMock()
mock_websocket.send_json = AsyncMock()
```

---

## Gaps & Caveats

### Critical Issues

1. **❌ No linting configured** - No code quality checks (ruff, flake8, pylint, mypy, black)
2. **❌ Tests disabled for PRs** - GitHub Actions workflow only runs on manual trigger
3. **❌ Most tests require API keys** - Integration tests need OPENAI_API_KEY and TAVILY_API_KEY
4. **❌ Broken test file** - `test_security_fix.py` imports non-existent functions
5. **⚠️ Module import issues** - Requires `PYTHONPATH=/app:/app/backend` workaround

### Limitations

6. **⚠️ Only 2 test files run in CI** - docker-compose test profile runs report-types.py and vector-store.py only
7. **⚠️ No coverage metrics** - No code coverage tracking or thresholds
8. **⚠️ No Makefile** - No standardized dev commands (make test, make lint, etc.)
9. **⚠️ Inconsistent test naming** - Mix of hyphens and underscores in test file names
10. **⚠️ No pre-commit hooks** - No automated checks before commits

### Dependency Warnings

11. **ℹ️ Version conflicts** - urllib3/chardet version warnings from requests package (non-blocking)
12. **ℹ️ Unknown pytest option** - `asyncio_fixture_loop_scope` not recognized by current pytest version

---

## Agent Readiness Assessment

**Rating: LOW**

### Why Low?

- ❌ **No linting** - Cannot validate code quality automatically
- ❌ **Tests require API keys** - Cannot run most tests without external service credentials
- ❌ **No gating CI** - Tests don't block merges even if they were to run
- ⚠️ **Limited unit test coverage** - Only 3-4 tests work without API keys
- ⚠️ **Module import issues** - Requires PYTHONPATH workaround

### What Works?

- ✅ Dependencies install cleanly in a standard container
- ✅ A few unit tests (3) can run without API keys
- ✅ Test framework (pytest) is properly configured
- ✅ Clear test file organization in `tests/` directory

### What an Agent Can Do

An agent working with this repository can:
1. ✅ Apply patches to Python code
2. ✅ Install dependencies in a container
3. ✅ Run the 3 unit tests that don't need API keys
4. ❌ **Cannot run linting** (not configured)
5. ❌ **Cannot run most tests** (require API keys)
6. ❌ **Cannot validate integration changes** (tests need external services)

### Recommendations for Improvement

To reach **MEDIUM** readiness:
1. Add ruff/flake8 linting configuration
2. Add more unit tests that don't require API keys
3. Enable test workflow for pull requests
4. Add pre-commit hooks

To reach **HIGH** readiness:
1. Mock external API calls in integration tests
2. Add test coverage requirements (80%+)
3. Make tests pass without API keys (use fixtures/mocks)
4. Enable linting as a gating CI check
5. Fix broken test_security_fix.py

---

## Quick Reference

### Validated Commands

```bash
# Install everything
pip install -r requirements.txt && \
pip install pytest pytest-asyncio faiss-cpu && \
pip install -e .

# Run unit tests (no API keys)
PYTHONPATH=/app:/app/backend python -m pytest \
  tests/test_logging.py tests/test_logs.py -v

# Run integration tests (requires API keys)
export OPENAI_API_KEY=sk-...
export TAVILY_API_KEY=tvly-...
PYTHONPATH=/app:/app/backend python -m pytest tests/report-types.py -v

# Run single test
PYTHONPATH=/app:/app/backend python -m pytest \
  tests/test_logging.py::test_custom_logs_handler -v
```

### Container One-Liner

```bash
podman run --rm -v $(pwd):/app:Z -w /app python:3.11 bash -c \
  "pip install -q pytest pytest-asyncio && \
   pip install -q -r requirements.txt && \
   pip install -q -e . && \
   PYTHONPATH=/app:/app/backend python -m pytest tests/test_logging.py tests/test_logs.py -v"
```

Expected: `3 passed, 1 warning in ~0.7s`

---

**Generated**: 2026-03-22 by Claude Code Test Context Analyzer
**Confidence**: High (validated in container)
