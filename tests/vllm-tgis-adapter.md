# Test Context: vllm-tgis-adapter

**Organization**: opendatahub-io
**Repository**: vllm-tgis-adapter
**Languages**: Python (3.9, 3.10, 3.11, 3.12)
**Build System**: setuptools with setuptools_scm, nox for automation
**Agent Readiness**: **MEDIUM** - Linting fully functional ✅, testing requires complex vLLM build from source ⚠️

## Overview

vLLM adapter for TGIS-compatible gRPC server. Python project using pytest for tests, ruff for linting/formatting, mypy for type checking, and nox for session management. The adapter is tightly coupled to specific vLLM API versions (v0.10.0-v0.11.2), requiring vLLM to be built from source for testing.

**Key characteristics**:
- Pre-commit hooks enforce comprehensive linting (ruff, codespell, pyupgrade, formatters)
- Tests require specific vLLM version compatibility - standard pip install gets incompatible version
- CI builds vLLM from source at specific tags with CPU support
- Custom setuptools build step generates protobuf/gRPC files

---

## Container Recipe

**This is the primary section for patch validation.** Follow these steps to validate lint and test changes in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-vllm-tgis-adapter \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

Alternative with docker:
```bash
docker run -d --name test-vllm-tgis-adapter \
  -v $(pwd):/app \
  -w /app \
  python:3.12 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "apt-get update && apt-get install -y git make build-essential"
```

### 3. Install Python Build Tools

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "pip install --no-cache-dir uv nox"
```

### 4. Install Project Dependencies

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && pip install --no-cache-dir -e '.[dev]'"
```

**Expected**: Installs vllm-tgis-adapter with all dev dependencies including ruff, mypy, pytest, etc. **Note**: This installs vLLM 0.18.0 from PyPI which is incompatible with tests.

### 5. Run Lint Checks

#### 5a. Pre-commit (All Hooks)

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && pre-commit run --all-files"
```

**Validated**: ✅ PASS (exit code 0)
**Output**: All 18 hooks pass - ruff, ruff-format, codespell, pre-commit-hooks, pyupgrade, TOML/YAML formatters

#### 5b. Ruff Linting

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && ruff check ."
```

**Validated**: ✅ PASS (exit code 0)
**Output**: "All checks passed!"

#### 5c. Ruff Formatting Check

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && ruff format --check ."
```

**Validated**: ✅ PASS (implied by pre-commit)

#### 5d. Type Checking (Mypy)

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && python -m mypy"
```

**Validated**: ✅ PASS (exit code 0)
**Output**: Some `import-untyped` warnings for grpc modules (expected and allowed)

#### 5e. Nox Lint Session

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && nox -s lint-3.12"
```

**Validated**: ✅ PASS (exit code 0)
**Output**: "Session lint-3.12 was successful"

### 6. Run Tests (⚠️ REQUIRES vLLM BUILD)

#### 6a. Basic Test Run (Will Fail)

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && pytest --cov --cov-config=pyproject.toml --no-cov-on-fail tests"
```

**Validated**: ❌ FAIL (exit code 4)
**Error**: `ImportError: cannot import name 'maybe_register_tokenizer_info_endpoint' from 'vllm.entrypoints.openai.api_server'`
**Reason**: Standard pip-installed vLLM (0.18.0) incompatible with adapter code expecting vLLM 0.10.x-0.11.x API

#### 6b. To Run Tests Successfully: Build vLLM from Source

Tests require building vLLM from source at a compatible version. Here's the process from CI:

```bash
# Inside container, install vLLM build dependencies
podman exec test-vllm-tgis-adapter bash -c "apt-get install -y ccache libnuma-dev libdnnl-dev opencl-dev"

# Clone vLLM at specific version
git clone https://github.com/vllm-project/vllm /tmp/vllm
cd /tmp/vllm
git checkout v0.11.2  # or v0.10.0, v0.10.1.1, v0.10.2, v0.11.0

# Create venv and install build deps
python -m venv .venv
source .venv/bin/activate
.github/scripts/install_vllm_build_deps.py pyproject.toml

# Build vLLM for CPU
export VLLM_TARGET_DEVICE=cpu
python setup.py bdist_wheel

# Set override for tests
export VLLM_VERSION_OVERRIDE=$(find dist -name '*.whl' -exec realpath {} \;)

# Now run tests with compatible vLLM
nox -s tests-3.12
```

**Note**: This is complex and not validated in this analysis. See `.github/workflows/tests.yaml` for exact CI implementation.

### 7. Run Single Test File

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && pytest tests/test_init.py -v"
```

### 8. Run Single Test

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && pytest tests/test_init.py::test_function_name -v"
```

Or using keyword matching:

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && pytest -k test_function_name -v"
```

### 9. Run Tests with Environment Variables (if vLLM compatible)

```bash
podman exec test-vllm-tgis-adapter bash -c \
  "cd /app && env \
    VLLM_TARGET_DEVICE=cpu \
    VLLM_USE_V1=1 \
    VLLM_ALLOW_LONG_MAX_MODEL_LEN=1 \
    pytest --cov --cov-config=pyproject.toml --no-cov-on-fail tests"
```

### 10. Cleanup Container

```bash
podman rm -f test-vllm-tgis-adapter
```

Or with docker:

```bash
docker rm -f test-vllm-tgis-adapter
```

---

## Validation Results

| Step | Command | Status | Exit Code | Notes |
|------|---------|--------|-----------|-------|
| System deps | `apt-get install git make build-essential` | ✅ PASS | 0 | Installed successfully |
| Install uv/nox | `pip install uv nox` | ✅ PASS | 0 | Installed successfully |
| Install dev deps | `pip install -e '.[dev]'` | ✅ PASS | 0 | Installed vLLM 0.18.0 (incompatible) |
| Pre-commit | `pre-commit run --all-files` | ✅ PASS | 0 | All 18 hooks passed |
| Ruff check | `ruff check .` | ✅ PASS | 0 | No violations |
| Mypy | `python -m mypy` | ✅ PASS | 0 | Type checking OK (with warnings) |
| Nox lint | `nox -s lint-3.12` | ✅ PASS | 0 | All checks passed |
| Pytest | `pytest --cov tests` | ❌ FAIL | 4 | ImportError - vLLM API mismatch |

**Summary**: Linting is 100% functional. Testing requires building vLLM from source at compatible version (v0.10.x-v0.11.x).

---

## CI/CD

**System**: GitHub Actions
**Main Workflow**: `.github/workflows/tests.yaml`
**Triggers**: pull_request, push to main, merge_group, workflow_dispatch, weekly schedule

### Gating Checks

All of these must pass for PR merge:

#### 1. Lint

```bash
nox --envdir ~/.nox --reuse-venv=yes -v -s lint-3.12
```

**Environment**:
```bash
export RUFF_OUTPUT_FORMAT=github
```

**What it does**: Runs pre-commit hooks (ruff, ruff-format, codespell, pre-commit-hooks, pyupgrade, formatters)

#### 2. Tests

```bash
nox --envdir ~/.nox --reuse-venv=yes -v -s tests-3.12 -- --cov-report=xml
```

**Matrix**: Python 3.12 × vLLM versions [v0.10.0, v0.10.1.1, v0.10.2, v0.11.0, v0.11.2]

**Environment**:
```bash
export VLLM_TARGET_DEVICE=cpu
export UV_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu
export UV_INDEX_STRATEGY=unsafe-best-match
export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1
export VLLM_USE_V1=1
export VLLM_VERSION_OVERRIDE=/path/to/built/vllm.whl
```

**Special setup**:
1. Install system deps: `ccache libnuma-dev libdnnl-dev opencl-dev`
2. Clone vLLM at specific ref
3. Build vLLM for CPU with custom build script
4. Set `VLLM_VERSION_OVERRIDE` to built wheel
5. Run tests via nox

#### 3. Build

```bash
nox --envdir ~/.nox --reuse-venv=yes -s build-3.12
```

**What it does**: Builds wheel with `python -m build`, validates with `twine check`

### CI Caching

- Nox environments: `~/.nox` keyed by Python version, noxfile.py hash, vLLM ref
- HuggingFace hub cache: `~/.cache/huggingface/hub`
- ccache: `~/.cache/ccache`

---

## Conventions

### Test Files

- **Pattern**: `test_*.py` in `tests/` directory
- **Function naming**: `test_*` functions
- **Fixtures**: Defined in `tests/conftest.py`
- **Markers**:
  - `@pytest.mark.hf_data` - tests that download from HuggingFace (skipped by default)

### Import Style

- Absolute imports
- isort configured via ruff with `known-first-party = ["vllm_tgis_adapter"]`
- Import order enforced by ruff

### Code Style

- Ruff for both linting and formatting
- Configuration in `pyproject.toml` under `[tool.ruff]`
- Comprehensive rule selection: `select = ["ALL"]` with specific ignores
- Format: ruff-format (black-compatible)

### Type Checking

- mypy configured for `src/` and `tests/`
- `check_untyped_defs = false`
- Allows missing imports for grpc modules
- Optional but encouraged (CI runs via `nox -s lint -- --mypy`)

---

## Gaps & Caveats

### 🚨 Critical Gaps

1. **Tests require specific vLLM version built from source**
   - Standard `pip install vllm` gets v0.18.0 (incompatible)
   - Adapter expects vLLM v0.10.0-v0.11.2 API
   - Must build vLLM from source following CI workflow steps

2. **Tight coupling to vLLM API**
   - ImportError: `maybe_register_tokenizer_info_endpoint` not in vLLM 0.18.0
   - No version pin in `pyproject.toml` - uses `vllm>=0.10.0` which allows incompatible versions
   - CI controls exact vLLM version via git checkout and custom build

3. **Complex test setup requirements**
   - Tests start actual gRPC and HTTP servers
   - Require vLLM engine initialization
   - Use threading and asyncio for server management
   - Fixtures in `conftest.py` manage server lifecycle

### ⚠️ Testing Limitations

- **Cannot validate tests** without building compatible vLLM from source
- **HuggingFace downloads**: Some tests download model data (skipped by default with `-k "not hf_data"`)
- **Resource requirements**: Tests involve model loading and server startup (CPU-only mode available)
- **Environment variables**: Multiple vLLM-specific env vars required for CPU testing

### ✅ What Works Well

- **Linting is fully functional** - All pre-commit hooks, ruff, mypy work perfectly
- **Well-documented CI** - `.github/workflows/tests.yaml` has exact reproduction steps
- **Nox automation** - Clean session management for lint, test, build
- **Type checking** - mypy configured and working (with some allowed warnings)

### 📝 Missing Documentation

- No explicit vLLM version compatibility matrix
- No documented minimum/maximum vLLM versions
- No local development guide for building vLLM
- README mentions CPU build but lacks step-by-step instructions

---

## Quick Reference

### Lint Commands (All Work ✅)

```bash
# Pre-commit (recommended)
pre-commit run --all-files

# Direct ruff
ruff check .
ruff format .

# With auto-fix
ruff check --fix .

# Type checking
python -m mypy

# Via nox (isolated environment)
nox -s lint-3.12
nox -s lint-3.12 -- --mypy  # Include type checking
```

### Test Commands (⚠️ Requires vLLM Build)

```bash
# All tests
pytest --cov --cov-config=pyproject.toml --no-cov-on-fail tests

# Skip HuggingFace downloads
pytest -k "not hf_data" tests

# Single file
pytest tests/test_init.py

# Single test
pytest tests/test_init.py::test_version
pytest -k test_version

# Via nox
nox -s tests-3.12

# With coverage report
pytest --cov --cov-report=xml tests
```

### Build Commands

```bash
# Via nox
nox -s build-3.12

# Direct
python -m build

# Install for development
pip install -e '.[dev]'
```

### Available Nox Sessions

```bash
nox --list

# Output:
# * tests-3.12, tests-3.11, tests-3.10, tests-3.9
# * lint-3.12, lint-3.11, lint-3.10, lint-3.9
# - build-3.12, build-3.11, build-3.10, build-3.9
# - dev-3.12, dev-3.11, dev-3.10, dev-3.9
```

---

## For Downstream Agents

### ✅ You CAN Reliably

- Apply patches and validate linting
- Run all pre-commit hooks
- Check code formatting with ruff
- Validate type checking with mypy
- Build the package
- Verify protobuf generation works

### ❌ You CANNOT Easily

- Run tests without building vLLM from source
- Validate test changes without complex setup
- Test against multiple vLLM versions without CI environment
- Determine if a patch breaks tests (without vLLM build)

### 💡 Recommended Workflow for Patch Validation

1. **Always validate linting** (100% reliable):
   ```bash
   pre-commit run --all-files
   ruff check .
   python -m mypy
   ```

2. **For test changes**: Note that tests cannot be validated locally without building vLLM. Mark patch as "linting validated, tests require CI".

3. **For lint-only changes**: Full validation possible in container using recipe above.

4. **For dependency changes**: Check if vLLM version compatibility affected.

### 🎯 Agent Readiness: MEDIUM

- **High confidence** for lint validation
- **Low confidence** for test validation
- **Medium overall** - can validate 50% of changes (lint) but not tests

---

**Generated**: 2026-03-22T20:47:30-04:00
**Validation Container**: python:3.12
**Confidence**: High (for linting), Low (for testing)
