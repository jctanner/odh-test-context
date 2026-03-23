# Test Context: openvino_tokenizers

## Overview

**Repository:** opendatahub-io/openvino_tokenizers
**Languages:** Python 3.11+, C++, JavaScript
**Build System:** py-build-cmake (Python package with CMake C++ extension)
**Agent Readiness:** **MEDIUM** — Linting fully validated and works. Tests require C++ extension built with OpenVINO developer package (complex setup).

This is a hybrid Python/C++ project that provides OpenVINO tokenizer operations. The Python package wraps a C++ extension built with CMake. Tests are comprehensive but require the compiled extension to pass.

---

## Container Recipe

This recipe allows you to lint the codebase and partially validate tests. Full test validation requires building the C++ extension with OpenVINO developer package.

### 1. Start Container

```bash
podman run -d --name test-context-openvino_tokenizers \
  -v /path/to/openvino_tokenizers:/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-openvino_tokenizers bash -c \
  "apt-get update && apt-get install -y git cmake build-essential curl"
```

### 3. Install Poetry (optional, for reference)

```bash
podman exec test-context-openvino_tokenizers bash -c \
  "curl -sSL https://install.python-poetry.org | python3 -"
```

Note: Poetry config has a format issue that prevents `poetry install` from working. Use pip instead.

### 4. Install Python Dependencies

```bash
podman exec test-context-openvino_tokenizers bash -c \
  "cd /app && pip install --upgrade pip"

podman exec test-context-openvino_tokenizers bash -c \
  "cd /app && pip install 'openvino~=2026.0.0.dev' --extra-index-url https://storage.openvinotoolkit.org/simple/wheels/nightly"

podman exec test-context-openvino_tokenizers bash -c \
  "cd /app && pip install 'transformers[sentencepiece]>=4.36.0' 'tiktoken>=0.3.0' 'pytest>=7.0.0' 'pytest-xdist>=3.4.0' 'ruff>=0.1.0' 'bandit>=1.7.0'"
```

### 5. Install Build Dependencies

```bash
podman exec test-context-openvino_tokenizers bash -c \
  "cd /app && pip install 'py-build-cmake==0.4.3' 'cmake~=3.14'"
```

### 6. Build and Install Package (Python-only)

```bash
podman exec test-context-openvino_tokenizers bash -c \
  "cd /app && pip install -e . --no-build-isolation"
```

**Result:** Package installs successfully but without the C++ extension. Tests will fail/skip.

### 7. Run Linting (VALIDATED ✓)

#### Ruff

```bash
podman exec test-context-openvino_tokenizers bash -c \
  "cd /app && ruff check python"
```

**Expected:** `All checks passed!` (exit code 0)
**Validated:** ✓ PASS — 0 errors, 0 warnings

#### Bandit (Security)

```bash
podman exec test-context-openvino_tokenizers bash -c \
  "cd /app && bandit -c pyproject.toml -r python"
```

**Expected:** `No issues identified.` (exit code 0)
**Validated:** ✓ PASS — 3430 lines scanned, no security issues

### 8. Run Tests (PARTIAL)

```bash
podman exec test-context-openvino_tokenizers bash -c \
  "cd /app && pytest tests --tb=short"
```

**Expected:** Many tests fail or skip without C++ extension
**Validated:** ⚠ PARTIAL — 17,343 tests collected, framework works, but most require C++ extension

To run a single test file:
```bash
podman exec test-context-openvino_tokenizers bash -c \
  "cd /app && pytest tests/tokenizers_test.py::test_function_name"
```

### 9. Cleanup

```bash
podman rm -f test-context-openvino_tokenizers
```

---

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| System deps | `apt-get install git cmake build-essential` | ✓ PASS | CMake 3.31.6 installed |
| OpenVINO | `pip install openvino~=2026.0.0.dev` | ✓ PASS | 53.4 MB nightly build |
| Dev deps | `pip install transformers pytest ruff bandit` | ✓ PASS | 40+ packages installed |
| Build | `pip install -e .` | ✓ PASS | Python package only (no C++) |
| Lint (ruff) | `ruff check python` | ✓ PASS | 0 errors, 0 warnings |
| Lint (bandit) | `bandit -c pyproject.toml -r python` | ✓ PASS | 0 security issues |
| Tests | `pytest tests` | ⚠ PARTIAL | Requires C++ extension |

**Summary:** Linting fully validated. Tests require C++ build with OpenVINO developer package.

---

## CI/CD

### GitHub Actions Workflows

All workflows trigger on `pull_request`, `merge_group`, and `push` to master/releases branches.

#### Gating Checks (Required for Merge)

1. **Linux Tests** (`.github/workflows/linux.yml`)
   - Downloads prebuilt OpenVINO from artifacts
   - Builds C++ extension with CMake
   - Builds Python wheel
   - Runs: `poetry run pytest tests`
   - Also runs TensorFlow layer tests from OpenVINO repo

2. **Mac Tests** (`.github/workflows/mac.yml`)
   - Similar to Linux but on macOS 13
   - Runs: `poetry run pytest tests/tokenizers_test.py` (subset)

3. **Windows Tests** (`.github/workflows/windows.yml`)
   - Similar to Linux/Mac but on Windows
   - Runs: `poetry run pytest tests`

4. **SDL/Security Tests** (`.github/workflows/sdl.yml`)
   - Runs: `bandit -c pyproject.toml -r python`
   - Runs Trivy vulnerability scanner
   - Dependency review on PRs

#### Advisory Checks (Non-blocking)

- **Coverity** (`.github/workflows/coverity.yml`) - Static analysis (scheduled)
- **Labeler** (`.github/workflows/labeler.yml`) - Auto-labeling PRs

### CI Commands (Exact)

**Install dependencies:**
```bash
poetry install --extras=transformers --with dev,benchmark
```

**Run tests:**
```bash
poetry run pytest tests
```

**Run TensorFlow tests:**
```bash
poetry run pytest $OPENVINO_REPO/tests/layer_tests/tensorflow_tests/ -n logical -m precommit
poetry run pytest $OPENVINO_REPO/tests/layer_tests/tensorflow2_keras_tests/ -n logical -m precommit
```

**Security scan:**
```bash
bandit -c pyproject.toml -r python
```

---

## Conventions

### Test Files
- **Pattern:** `tests/*.py`
- **Naming:** `test_*` functions
- **Fixtures:** `tests/conftest.py`
- **Parametrization:** Heavy use of `@pytest.mark.parametrize` with HuggingFace model names

### Code Style
- **Linter:** Ruff (configured but NOT run in CI — gap!)
- **Line length:** 119
- **Import style:** Absolute imports, 2 blank lines after imports (isort)
- **Ignored rules:** `C901`, `E501`, `E741`, `W605`

### File Layout
```
openvino_tokenizers/
├── python/openvino_tokenizers/  # Python source
├── src/                          # C++ source
├── tests/                        # Python tests
├── js/                           # JavaScript bindings
├── cmake/                        # CMake modules
└── pyproject.toml                # Python config
```

---

## Gaps & Caveats

1. **Ruff not in CI:** Ruff is configured in `pyproject.toml` but no CI workflow actually runs it. This is a linting gap.

2. **Tests require C++ extension:** Most tests need the compiled C++ extension. CI builds this using OpenVINO developer package downloaded from artifacts. Local builds require:
   - OpenVINO developer package (or nightly wheel)
   - CMake 3.15+
   - C++ compiler (gcc/clang/MSVC)
   - ICU libraries (for Unicode support)

3. **Poetry config issue:** The `pyproject.toml` has a license field format that prevents `poetry install` from working. Use pip instead.

4. **No Makefile:** No convenience targets for common tasks like `make lint`, `make test`, etc.

5. **JavaScript tests not validated:** The `js/tests/*.test.js` tests exist but aren't run in the main CI workflows.

6. **OpenVINO dependency:** Requires OpenVINO 2026.0.0 nightly builds from a custom package index. Not available on PyPI.

7. **Complex build:** The build process is complex:
   - Download/install OpenVINO
   - Configure CMake with OpenVINO paths
   - Build C++ extension
   - Build Python wheel
   - Install and test

---

## How to Run Lint Locally (Validated)

These commands work and have been tested:

```bash
# Ruff linting
ruff check python

# Ruff auto-fix
ruff check --fix python

# Bandit security scan
bandit -c pyproject.toml -r python
```

---

## How to Run Tests Locally (Requires C++ Build)

**Option 1: Using Poetry (recommended by CI)**
```bash
poetry install --extras=transformers --with dev
poetry run pytest tests
```

**Option 2: Using pip**
```bash
pip install -e .[transformers] --extra-index-url https://storage.openvinotoolkit.org/simple/wheels/nightly
pip install pytest pytest-xdist
pytest tests
```

**Run specific test:**
```bash
pytest tests/tokenizers_test.py::test_hf_wordpiece_tokenizers
```

**Run with parallel execution:**
```bash
pytest tests -n auto
```

---

## Notes for Downstream Agents

- **Linting is reliable:** Both ruff and bandit work perfectly and can validate code quality.
- **Tests need infrastructure:** Full test validation requires building the C++ extension with OpenVINO developer package. Consider using CI-built wheel artifacts for validation instead of building from source.
- **Use pip, not poetry:** Due to the pyproject.toml license field issue, use pip for installation.
- **Python-only install works:** You can install the Python package without the C++ extension for import/linting validation.
- **CI is authoritative:** The CI workflows show the exact commands and dependencies needed for full builds.

---

**Generated:** 2026-03-23T00:05:00Z
**Confidence:** High (container-validated)
**Agent Readiness:** Medium
