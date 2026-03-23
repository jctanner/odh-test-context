# Test Context: llama-stack-provider-trustyai-garak

**Generated:** 2026-03-22T18:58:00-04:00
**Organization:** opendatahub-io
**Agent Readiness:** HIGH

## Overview

Python 3.12+ project implementing Garak red-teaming as an external evaluation provider for Llama Stack. Uses pytest for testing with 318 tests covering configuration, inline/remote providers, shield scanning, and intents-based testing.

**Agent Readiness Rating: HIGH**
All gating checks validated successfully. Tests pass cleanly (318/318) with clear exit codes. Dependencies install without issues in standard Python 3.12 container. CI enforces tests and critical security scans only—linting tools are present but not gating.

---

## Container Recipe

This is a **complete, copy-paste recipe** for validating patches in an isolated container.

### 1. Start the container

```bash
REPO_PATH="/path/to/llama-stack-provider-trustyai-garak"
podman run -d \
  --name test-context-llama-stack-garak \
  -v "${REPO_PATH}:/app:Z" \
  -w /app \
  python:3.12 \
  sleep infinity
```

**Alternative base image (matches Containerfile):**
```bash
# Use Red Hat UBI9 Python 3.12 if available
podman run -d \
  --name test-context-llama-stack-garak \
  -v "${REPO_PATH}:/app:Z" \
  -w /app \
  registry.access.redhat.com/ubi9/python-312:latest \
  sleep infinity
```

### 2. Install dependencies

```bash
podman exec test-context-llama-stack-garak bash -c "
  cd /app && \
  python -m pip install --upgrade pip && \
  python -m pip install -e '.[dev,inline,server]'
"
```

**Expected:** ~2-3 minutes to install 200+ dependencies. Exit code 0.

### 3. Run gating checks

#### Tests (GATING - required to merge)

```bash
podman exec test-context-llama-stack-garak bash -c "cd /app && pytest tests -v"
```

**Expected output:**
```
======================== 318 passed, 1 warning in 2.16s ========================
Exit code: 0
```

**Success criteria:** All 318 tests pass. Exit code 0. One FutureWarning from kfp library is expected (not a failure).

#### Security scan (GATING - fails on CRITICAL vulns)

This runs in CI but requires Trivy to be installed. Not typically run locally.

```bash
# If you have trivy installed:
trivy fs --severity CRITICAL --exit-code 1 .
```

### 4. Run a single test file (optional)

```bash
podman exec test-context-llama-stack-garak bash -c "cd /app && pytest tests/test_config.py -v"
```

### 5. Run a single test (optional)

```bash
podman exec test-context-llama-stack-garak bash -c "
  cd /app && pytest tests/test_config.py::TestGarakInlineConfig::test_default_config -v
"
```

### 6. Run with coverage (optional)

```bash
podman exec test-context-llama-stack-garak bash -c "
  cd /app && pytest tests --cov=src/llama_stack_provider_trustyai_garak --cov-report=term-missing
"
```

### 7. Cleanup

```bash
podman rm -f test-context-llama-stack-garak
```

---

## Validation Results

All commands were validated in a live `python:3.12` container:

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Dependencies | `pip install -e ".[dev,inline,server]"` | 0 | ✅ PASS | ~200+ packages installed |
| Tests | `pytest tests -v` | 0 | ✅ PASS | 318 passed, 1 warning in 2.16s |
| Black (linter) | `black --check .` | 1 | ⚠️ NOT GATING | 41 files need reformatting (not enforced) |
| Isort (linter) | `isort --check-only .` | 1 | ⚠️ NOT GATING | Import sorting violations (not enforced) |

**Key Finding:** Linting tools (black, isort) are installed but **not configured or enforced in CI**. They would fail if run, but they are not gating checks. Only tests and security scans gate merges.

---

## CI/CD

### Gating Checks (Required for Merge)

#### 1. Run Tests (`.github/workflows/run-tests.yml`)

**Triggers:** Pull requests and pushes to `main`

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev,inline,server]"

- name: Run tests
  env:
    PYTHONPATH: src
  run: |
    pytest tests -v
```

**Pass criteria:** Exit code 0, all tests pass

#### 2. Trivy Security Scan (`.github/workflows/security.yml`)

**Triggers:** Pull requests and pushes to `main`

```yaml
- name: Check for critical vulnerabilities
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    scan-ref: '.'
    format: 'table'
    severity: 'CRITICAL'
    exit-code: '1'  # Fail if critical vulnerabilities found
```

**Pass criteria:** No CRITICAL severity vulnerabilities found

### Advisory Checks (Non-Gating)

- Trivy scans for HIGH/MEDIUM/LOW severities (SARIF uploaded to GitHub Security tab)
- Container build and publish (`.github/workflows/build-and-publish.yaml`) - runs on tag push

### Python Version

CI uses **Python 3.12** (specified in all workflows). Project requires Python >= 3.12.

---

## Conventions

### Test Files

- **Location:** `tests/` directory
- **Naming:** `test_*.py` (11 test files, ~7000 lines total)
- **Fixtures:** Shared fixtures in `tests/conftest.py`

### Test Naming

- **Functions:** `test_*` prefix
- **Classes:** `Test*` prefix with `test_*` methods
- **Example:**
  ```python
  class TestGarakInlineConfig:
      def test_default_config(self):
          ...
  ```

### Test Structure

- Uses `unittest.mock` for mocking (Mock, AsyncMock, patch)
- Async tests use `pytest-asyncio` with `@pytest.mark.asyncio` (deprecated) or async fixtures
- Parametrized tests use `@pytest.mark.parametrize`
- Fixtures provide mocked dependencies (file API, benchmarks API, safety API, shields API)

### Import Style

- Absolute imports from `src/` package
- Example: `from llama_stack_provider_trustyai_garak.config import GarakInlineConfig`

### Configuration

- Uses Pydantic models for config validation
- Test configuration in `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  python_files = "test_*.py"
  pythonpath = ["src"]
  addopts = "-v"
  ```

---

## Gaps & Caveats

1. **No Linter Enforcement**
   Black and isort are installed in dev dependencies but not configured or run in CI. The codebase has formatting and import sorting violations that would fail if these tools were enforced. Patches should prioritize test correctness over code style.

2. **No Coverage Threshold**
   Coverage can be measured (`pytest --cov`) but there's no enforced minimum coverage percentage.

3. **Tekton Pipeline**
   `.tekton/` directory contains pipeline configs for internal Red Hat workflows (container builds, DSP releases). These are **not** PR gates and don't affect patch validation.

4. **No Pre-Commit Hooks**
   No `.pre-commit-config.yaml` found. Developers can commit without local validation.

5. **Fast Tests**
   All 318 tests run in ~2-4 seconds. No slow integration tests requiring external infrastructure (databases, clusters). Tests use mocks extensively.

6. **Optional Dependencies**
   Project has multiple install extras:
   - `[dev]` - pytest, black, isort
   - `[inline]` - garak and dependencies for inline execution
   - `[server]` - llama-stack server components

   The container recipe installs all three for complete validation.

---

## Quick Reference

### Run all tests
```bash
pytest tests -v
```

### Run tests for a specific module
```bash
pytest tests/test_config.py -v
```

### Run a single test
```bash
pytest tests/test_config.py::TestGarakInlineConfig::test_default_config -v
```

### Run with coverage
```bash
pytest tests --cov=src/llama_stack_provider_trustyai_garak --cov-report=term-missing
```

### Install for development
```bash
pip install -e ".[dev,inline,server]"
```

### Build container
```bash
podman build -f Containerfile -t llama-stack-provider-trustyai-garak .
```

---

## Test Breakdown

- **318 tests total** across 11 test files
- **Test execution time:** ~2-4 seconds (very fast)
- **Test distribution:**
  - `test_evalhub_adapter.py`: 126 tests (evalhub integration, KFP pipelines, intents)
  - `test_remote_provider.py`: 57 tests (remote provider, KFP integration)
  - `test_pipeline_steps.py`: 39 tests (pipeline step execution)
  - `test_utils.py`: 31 tests (utility functions, result parsing)
  - `test_intents_with_shields.py`: 18 tests (intents with shield testing)
  - `test_intents.py`: 17 tests (intents taxonomy loading)
  - `test_version.py`: 14 tests (version management)
  - `test_config.py`: 10 tests (configuration validation)
  - `test_shield_scan.py`: 9 tests (shield orchestrator)
  - `test_inline_provider.py`: 4 tests (inline provider)

---

## Support & Documentation

- **Repository:** https://github.com/trustyai-explainability/llama-stack-provider-trustyai-garak
- **Issues:** https://github.com/trustyai-explainability/llama-stack-provider-trustyai-garak/issues
- **Tutorial:** https://trustyai.org/docs/main/red-teaming-introduction
- **Llama Stack:** https://llamastack.github.io/
- **Garak:** https://reference.garak.ai/en/latest/index.html
