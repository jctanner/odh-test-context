# Test Context: guardrails-detectors

**Agent Readiness: HIGH** - All tests pass in containerized environment. Linting not enforced but test infrastructure is solid and validated.

## Overview

**Repository:** opendatahub-io/guardrails-detectors
**Language:** Python 3.11
**Build System:** pip
**Test Framework:** pytest with coverage
**CI System:** GitHub Actions

**Test Summary:**
- Built-in detector tests: 92 passing
- Huggingface runtime tests: 36 passing
- LLM Judge tests: 26 passing
- **Total: 154 tests**

## Container Recipe

This is the complete, validated recipe for running tests in a container. Follow these steps exactly to validate patches.

### 1. Start Container

```bash
podman run -d --name test-context-guardrails-detectors \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-guardrails-detectors bash -c \
  "apt-get update && apt-get install -y --no-install-recommends build-essential wget git"
```

### 3. Upgrade Pip

```bash
podman exec test-context-guardrails-detectors bash -c \
  "python -m pip install --upgrade pip setuptools wheel"
```

### 4. Install Python Test Dependencies

```bash
podman exec test-context-guardrails-detectors bash -c \
  "pip install pytest pytest-cov"
```

### 5. Install PyTorch

```bash
podman exec test-context-guardrails-detectors bash -c \
  "pip install torch"
```

### 6. Install Project Dependencies

```bash
podman exec test-context-guardrails-detectors bash -c \
  "cd /app && pip install -r detectors/common/requirements.txt -r detectors/common/requirements-dev.txt -r detectors/built_in/requirements.txt"
```

```bash
podman exec test-context-guardrails-detectors bash -c \
  "cd /app && pip install -r detectors/huggingface/requirements.txt"
```

```bash
podman exec test-context-guardrails-detectors bash -c \
  "cd /app && pip install -r detectors/llm_judge/requirements.txt"
```

### 7. Set Environment Variables

All test commands below include necessary environment variables inline.

### 8. Run Tests by Component

**IMPORTANT:** Tests must be run by component directory. Running all tests together causes pytest collection errors due to duplicate test file names.

#### Built-in Detector Tests (92 tests, ~5 seconds)

```bash
podman exec test-context-guardrails-detectors bash -c \
  "cd /app && export PYTHONPATH=/app/detectors/huggingface:/app/detectors/llm_judge:/app/detectors:/app && \
   pytest tests/detectors/builtIn/ --cov=detectors.built_in --cov-report=term-missing -v"
```

**Expected:** ✅ 92 passed, ~33 warnings, 84% coverage

#### Huggingface Runtime Tests (36 tests, ~6 seconds)

```bash
podman exec test-context-guardrails-detectors bash -c \
  "cd /app && export PYTHONPATH=/app/detectors/huggingface:/app/detectors/llm_judge:/app/detectors:/app && \
   export HF_HOME=/tmp/huggingface && \
   export TRANSFORMERS_CACHE=/tmp/transformers_cache && \
   export TOKENIZERS_PARALLELISM=false && \
   pytest tests/detectors/huggingface/ --cov=detectors.huggingface --cov-report=term-missing -v --tb=short"
```

**Expected:** ✅ 36 passed, ~32 warnings, 65% coverage

#### LLM Judge Tests (26 tests, ~1 second)

```bash
podman exec test-context-guardrails-detectors bash -c \
  "cd /app && export PYTHONPATH=/app/detectors/huggingface:/app/detectors/llm_judge:/app/detectors:/app && \
   pytest tests/detectors/llm_judge/ --cov=detectors.llm_judge --cov-report=term-missing -v --tb=short"
```

**Expected:** ✅ 26 passed, ~32 warnings, 63% coverage

### 9. Run Single Test File

Replace `{file}` with the test file path:

```bash
podman exec test-context-guardrails-detectors bash -c \
  "cd /app && export PYTHONPATH=/app/detectors/huggingface:/app/detectors/llm_judge:/app/detectors:/app && \
   pytest {file} -v"
```

Example:
```bash
podman exec test-context-guardrails-detectors bash -c \
  "cd /app && export PYTHONPATH=/app/detectors/huggingface:/app/detectors/llm_judge:/app/detectors:/app && \
   pytest tests/detectors/builtIn/test_regex.py -v"
```

### 10. Run Single Test

Replace `{file}` and `{test_name}` with specific values:

```bash
podman exec test-context-guardrails-detectors bash -c \
  "cd /app && export PYTHONPATH=/app/detectors/huggingface:/app/detectors/llm_judge:/app/detectors:/app && \
   pytest {file}::{test_name} -v"
```

Example:
```bash
podman exec test-context-guardrails-detectors bash -c \
  "cd /app && export PYTHONPATH=/app/detectors/huggingface:/app/detectors/llm_judge:/app/detectors:/app && \
   pytest tests/detectors/builtIn/test_regex.py::TestRegexDetectors::test_builtin_regex_detectors -v"
```

### 11. Cleanup

```bash
podman rm -f test-context-guardrails-detectors
```

## Validation Results

All commands were validated in a live container:

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install | pip install all requirements | ✅ Pass | Dependency conflict warning (coverage version) |
| Built-in tests | pytest tests/detectors/builtIn/ | ✅ Pass | 92/92 tests passed, 84% coverage |
| Huggingface tests | pytest tests/detectors/huggingface/ | ✅ Pass | 36/36 tests passed, 65% coverage |
| LLM Judge tests | pytest tests/detectors/llm_judge/ | ✅ Pass | 26/26 tests passed, 63% coverage |

## CI/CD

### Gating Checks

All PR checks run on `pull_request` to main/incubation/stable branches:

1. **Tier 1 - Built-in detectors unit tests**
   - Triggers on: changes to `detectors/built_in/**`, `detectors/common/**`, `tests/detectors/builtIn/**`
   - Command: `pytest tests/detectors/builtIn/ --cov=detectors.built_in --cov-report=term-missing -v`
   - Python: 3.11
   - System deps: None

2. **Tier 1 - Hugging Face Runtime unit tests**
   - Triggers on: changes to `detectors/huggingface/**`, `detectors/common/**`, `tests/detectors/huggingface/**`
   - Command: `pytest tests/detectors/huggingface/ --cov=detectors.huggingface --cov-report=term-missing -v --tb=short`
   - Python: 3.11
   - System deps: build-essential, wget
   - Timeout: 20 minutes
   - Env vars: `HF_HOME=/tmp/huggingface`, `TRANSFORMERS_CACHE=/tmp/transformers_cache`, `TOKENIZERS_PARALLELISM=false`

3. **Tier 1 - LLM Judge unit tests**
   - Triggers on: changes to `detectors/llm_judge/**`, `detectors/common/**`, `tests/detectors/llm_judge/**`
   - Command: `pytest tests/detectors/llm_judge/ --cov=detectors.llm_judge --cov-report=term-missing -v --tb=short`
   - Python: 3.11
   - System deps: build-essential, wget
   - Timeout: 15 minutes

4. **Tier 1 - Security scan**
   - Triggers on: changes to `detectors/**`, `requirements*.txt`, `*.py`
   - Uses: Trivy filesystem and config scanner
   - Severity: MEDIUM, HIGH, CRITICAL
   - Results uploaded to GitHub Security tab

### Shared Setup Action

All test workflows use `.github/actions/test-setup/action.yaml`:
- Installs Python 3.11
- Caches pip dependencies per component
- Installs system deps if needed
- Sets PYTHONPATH environment variable
- Attempts to run pre-commit if config exists (currently skipped, no config)

## Conventions

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures (path setup, prometheus cleanup)
├── detectors/
│   ├── builtIn/            # Built-in detector tests (92 tests)
│   │   ├── test_custom.py
│   │   ├── test_filetype.py
│   │   ├── test_metrics.py
│   │   └── test_regex.py
│   ├── huggingface/        # Huggingface runtime tests (36 tests)
│   │   ├── test_client_integration.py
│   │   ├── test_method_*.py
│   │   ├── test_metrics.py
│   │   └── test_*.py
│   └── llm_judge/          # LLM Judge tests (26 tests)
│       ├── test_llm_judge_detector.py
│       └── test_performance.py
└── dummy_models/            # Mock models for huggingface tests
```

### Test Naming

- **Files:** `test_*.py`
- **Classes:** `Test*` (e.g., `TestRegexDetectors`, `TestMetrics`)
- **Functions:** `test_*` (standard pytest convention)

### Import Style

Tests use absolute imports from the `detectors` package. The `conftest.py` manipulates `sys.path` to add detector subdirectories. The `PYTHONPATH` environment variable must include all detector submodules.

## Gaps & Caveats

### Known Issues

1. **No Linting Configuration**
   - Pre-commit is installed as a dev dependency
   - CI workflows reference pre-commit but `.pre-commit-config.yaml` does not exist
   - Code style cannot be automatically validated
   - Manual code review is the only quality gate

2. **Dependency Version Conflict**
   - `pytest-cov 7.1.0` requires `coverage>=7.10.6`
   - `requirements-dev.txt` pins `coverage==7.6.1`
   - Tests still pass but this should be resolved

3. **Test Collection Error When Running All Tests**
   - Both `tests/detectors/builtIn/test_metrics.py` and `tests/detectors/huggingface/test_metrics.py` exist
   - Pytest collection fails when running `pytest tests/` due to import file mismatch
   - **Workaround:** Run tests by component directory (as CI does)
   - Not a blocker since CI runs tests separately

4. **Deprecation Warnings**
   - Pydantic deprecation warnings: Field 'example' parameter deprecated in Pydantic V2
   - Regex escape sequence warnings in `detectors/built_in/regex_detectors.py`
   - Tests pass but warnings should eventually be addressed

5. **No Coverage Threshold**
   - Coverage is measured (84%, 65%, 63% for each component)
   - No enforcement of minimum coverage percentage
   - Coverage can regress without detection

### What Works

✅ All tests pass in containerized environment
✅ Tests are well-organized by component
✅ CI setup mirrors local container testing
✅ Good test coverage across all detector types
✅ Comprehensive test fixtures and helpers
✅ Tests use dummy models (no external dependencies)

### What Doesn't Work

❌ No linting - cannot validate code style
❌ Cannot run all tests together (must run by component)
❌ No coverage enforcement
❌ Dependency version conflicts in dev requirements

## Usage for Patch Validation

An agent validating a patch should:

1. **Identify affected detector type** based on changed files
   - Changes to `detectors/built_in/**` → run built-in tests
   - Changes to `detectors/huggingface/**` → run huggingface tests
   - Changes to `detectors/llm_judge/**` → run llm_judge tests
   - Changes to `detectors/common/**` → run all tests

2. **Use the container recipe** above to set up environment

3. **Run component-specific tests** as shown in step 8

4. **Expect warnings** but tests should pass
   - Pydantic deprecation warnings are normal
   - Coverage version conflict warning is expected

5. **Coverage is advisory** - no minimum threshold to enforce

6. **No lint check** - code style cannot be validated

## Quick Reference

### Most Common Test Commands

Run all built-in detector tests:
```bash
export PYTHONPATH=/app/detectors/huggingface:/app/detectors/llm_judge:/app/detectors:/app
pytest tests/detectors/builtIn/ --cov=detectors.built_in --cov-report=term-missing -v
```

Run all huggingface tests:
```bash
export PYTHONPATH=/app/detectors/huggingface:/app/detectors/llm_judge:/app/detectors:/app
export HF_HOME=/tmp/huggingface
export TRANSFORMERS_CACHE=/tmp/transformers_cache
export TOKENIZERS_PARALLELISM=false
pytest tests/detectors/huggingface/ --cov=detectors.huggingface --cov-report=term-missing -v --tb=short
```

Run all llm_judge tests:
```bash
export PYTHONPATH=/app/detectors/huggingface:/app/detectors/llm_judge:/app/detectors:/app
pytest tests/detectors/llm_judge/ --cov=detectors.llm_judge --cov-report=term-missing -v --tb=short
```

### Test Execution Time

- Built-in: ~5 seconds (92 tests)
- Huggingface: ~6 seconds (36 tests)
- LLM Judge: ~1 second (26 tests)
- **Total: ~12 seconds for all 154 tests**

---

**Generated:** 2026-03-22T22:18:50Z
**Validation:** Live container testing on python:3.11
**Confidence:** High - All commands validated and working
