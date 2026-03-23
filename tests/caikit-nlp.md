# Test Context for caikit-nlp

## Overview

**Repository**: opendatahub-io/caikit-nlp
**Language**: Python 3.9-3.10
**Build System**: Python setuptools with tox automation
**Agent Readiness**: **MEDIUM** - Lint commands validated successfully (100% pass), test infrastructure works but has 10 pre-existing test failures (383/393 tests pass, 94% coverage). An agent can validate patches with lint checks reliably, and can run tests but should be aware of baseline failures.

## Container Recipe

This is a complete, validated recipe for running lint and tests in a container. All commands have been tested and verified.

### 1. Start Container

```bash
podman run -d --name test-context-caikit-nlp \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.9 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-caikit-nlp bash -c \
  "apt-get update -qq && apt-get install -y -qq git make"
```

Git is required for setuptools-scm to determine package version from git tags.

### 3. Install Python Setup Requirements

```bash
podman exec test-context-caikit-nlp bash -c \
  "cd /app && pip install --upgrade pip && pip install -r setup_requirements.txt"
```

This installs `tox>=4.4.2` and `build>=0.10.0` which are needed to run all validation commands.

### 4. Run Format Checks (VALIDATED ✓)

```bash
podman exec test-context-caikit-nlp bash -c "cd /app && tox -e fmt"
```

**Exit Code**: 0
**Status**: PASSED
**Duration**: ~15 seconds
**What it does**: Runs pre-commit hooks (prettier, black, isort) to check code formatting.
**Note**: In CI mode this fails if files need formatting. Running locally will auto-format files.

### 5. Run Pylint (VALIDATED ✓)

```bash
podman exec test-context-caikit-nlp bash -c "cd /app && tox -e lint"
```

**Exit Code**: 0
**Status**: PASSED (10.00/10 score)
**Duration**: ~21 seconds (after deps installed)
**What it does**: Runs pylint against the `caikit_nlp` directory with configuration from `.pylintrc`.

### 6. Run Tests (VALIDATED ⚠)

```bash
podman exec test-context-caikit-nlp bash -c "cd /app && tox -e py39"
```

**Exit Code**: 1 (due to test failures)
**Status**: PARTIAL - 383 passed, 10 failed, 1 skipped, 94% coverage
**Duration**: ~103 seconds (~70s dependency install + ~33s test execution)
**Known Failures**: 10 tests in `tests/modules/text_embedding/test_crossencoder.py::test_truncation` with various parameters
**What it does**: Installs all project dependencies in a tox virtualenv, then runs pytest with coverage.

**Important**: The 10 test failures are pre-existing issues in the codebase, not infrastructure problems. When validating patches, compare test results against this baseline.

### 7. Run Single Test File

```bash
podman exec test-context-caikit-nlp bash -c \
  "cd /app && .tox/py39/bin/pytest tests/data_model/test_generation.py -v"
```

Replace `tests/data_model/test_generation.py` with the path to any test file.

### 8. Run Single Test Function

```bash
podman exec test-context-caikit-nlp bash -c \
  "cd /app && .tox/py39/bin/pytest tests/data_model/test_generation.py::test_sampling_parameters_from_proto_and_back -v"
```

Use `{file}::{test_name}` syntax to run a specific test function.

### 9. Build Package (VALIDATED ✓)

```bash
podman exec test-context-caikit-nlp bash -c "cd /app && tox -e build"
```

**Exit Code**: 0
**Status**: PASSED
**Duration**: ~4 seconds
**Output**: Produces `dist/caikit_nlp-*.whl` and `dist/caikit_nlp-*.tar.gz`

### 10. Cleanup

```bash
podman rm -f test-context-caikit-nlp
```

**Always run this** to remove the container when validation is complete.

## Validation Results

All commands were validated in a live container:

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `pip install -r setup_requirements.txt` | 0 | ✓ PASS | Installed tox and build |
| Format check | `tox -e fmt` | 0 | ✓ PASS | prettier, black, isort all passed |
| Lint | `tox -e lint` | 0 | ✓ PASS | pylint 10.00/10 score |
| Build | `tox -e build` | 0 | ✓ PASS | Built wheel and tar.gz |
| Tests | `tox -e py39` | 1 | ⚠ PARTIAL | 383/393 passed (94% coverage) |

## CI/CD

### Gating Checks (GitHub Actions)

All of these checks must pass for a PR to merge:

1. **Build Caikit NLP Library** (`.github/workflows/build-library.yml`)
   - Trigger: `push` and `pull_request` to `main`, `release-*`
   - Matrix: Python 3.9 and 3.10
   - Command: `tox -e py39` or `tox -e py310`

2. **Lint and Format** (`.github/workflows/lint-code.yml`)
   - Trigger: `push` and `pull_request` to `main`, `release-*`
   - Commands:
     ```bash
     tox -e fmt
     tox -e lint
     ```

3. **Build Image** (`.github/workflows/build-image.yml`)
   - Trigger: `push` and `pull_request` to `main`, `release-*`
   - Command: `docker build -t caikit-nlp:latest .`

### CI Environment Setup

```bash
python -m pip install --upgrade pip
python -m pip install -r setup_requirements.txt
```

## Conventions

**Test File Naming**: `test_*.py` in `tests/` directory
**Test Function Naming**: `test_*` (standard pytest)
**Import Organization**: Grouped with headers via isort
- Future imports first
- Standard library
- Third party
- First party (caikit, alog, aconfig, etc.)
- Local (caikit_nlp, tests)

**Code Formatting**: Black with 100 character line limit
**Naming Conventions**:
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`

**Pytest Configuration** (from `tox.ini`):
```bash
pytest --durations=42 --cov=caikit_nlp --cov-report=term --cov-report=html tests
```

## Gaps & Caveats

### Known Test Failures

The test suite currently has **10 failing tests** in `tests/modules/text_embedding/test_crossencoder.py`:
- `test_truncation[1]` through `test_truncation[511]` (various truncation parameters)
- All failures are `AssertionError` at line 518 of the test file

These failures appear to be pre-existing issues in the codebase. When validating patches:
- If you get 383 passes / 10 failures → baseline (no regression)
- If you get fewer than 383 passes → potential regression
- If you get more than 383 passes → potential fix!

### Environment Variables

Tests can be configured with these environment variables (all optional):
- `LOG_LEVEL` - Logging level (default: "off")
- `LOG_FILTERS` - Log filters (default: "urllib3:off")
- `LOG_THREAD_ID` - Include thread ID in logs (true/false)
- `PYTORCH_ENABLE_MPS_FALLBACK` - PyTorch MPS fallback setting

### Performance Considerations

- **Heavy dependencies**: Installing test dependencies takes ~70 seconds due to large ML libraries (torch, transformers, etc.)
- **Test duration**: Full test suite runs in ~32 seconds after installation
- **Coverage**: Current coverage is 94% (2403 statements, 153 missing)

### Python Version Limitations

- **Supported**: Python 3.9, 3.10
- **Not supported**: Python 3.11+ (TGIS backend compatibility issue)

### Missing Configuration

- No explicit coverage threshold requirement found
- No coverage gates in CI (tests pass with any coverage level)

### Infrastructure Requirements

- Git repository (needed for setuptools-scm version detection)
- ~2GB disk space for dependencies
- Internet access for downloading ML models and dependencies

## Quick Reference

**Validate a patch completely**:
```bash
# Start container
podman run -d --name test-context-caikit-nlp -v $(pwd):/app:Z -w /app python:3.9 sleep infinity

# Setup
podman exec test-context-caikit-nlp bash -c "apt-get update -qq && apt-get install -y -qq git make"
podman exec test-context-caikit-nlp bash -c "cd /app && pip install -q --upgrade pip && pip install -q -r setup_requirements.txt"

# Validate (all three commands)
podman exec test-context-caikit-nlp bash -c "cd /app && tox -e fmt && tox -e lint && tox -e py39"

# Cleanup
podman rm -f test-context-caikit-nlp
```

**Expected baseline** (clean codebase):
- Format: PASS
- Lint: PASS (10.00/10)
- Tests: 383 passed, 10 failed, 1 skipped

**Signs of regression**:
- Format failures (files need formatting)
- Lint score < 10.00 or new errors/warnings
- Test count < 383 passed or new failures beyond the 10 baseline failures
