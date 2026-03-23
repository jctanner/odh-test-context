# OpenVINO Test Context

**Agent Readiness: LOW** — Python linting can be validated in containers, but full C++ build and tests require 60-90 minutes of compilation and are impractical for quick patch validation.

## Overview

OpenVINO is a large C++ inference runtime with Python and JavaScript bindings. The project uses CMake for builds and has extensive CI coverage across multiple platforms.

- **Languages**: C++ (core), Python (bindings/API), JavaScript (bindings), Shell scripts
- **Build System**: CMake 3.13+
- **Test Framework**: gtest (C++), pytest (Python)
- **CI System**: GitHub Actions (50+ workflows)

## Container Recipe

This recipe allows validation of Python linting without the full C++ build. C++ validation requires infrastructure beyond container scope.

### 1. Start Container

```bash
podman run -d --name openvino-validator \
  -v $(pwd):/app:Z \
  -w /app \
  ubuntu:22.04 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec openvino-validator bash -c "
  apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    python3 \
    python3-pip \
    clang-format-15 \
    shellcheck \
    curl \
    wget \
    ca-certificates \
    software-properties-common
"
```

### 3. Install Python Linting Dependencies

```bash
podman exec openvino-validator bash -c "
  cd /app && \
  python3 -m pip install --no-cache-dir \
    -r src/bindings/python/requirements_test.txt
"
```

**Expected**: Installation completes successfully. Installs flake8, mypy, black, pytest, and supporting tools.

### 4. Run Python API Linting (flake8)

```bash
podman exec openvino-validator bash -c "
  cd /app/src/bindings/python && \
  python3 -m flake8 ./src/openvino --config=setup.cfg
"
```

**Expected**: Exit code 0. May show one A005 warning about types.py shadowing builtin (this is expected and accepted in CI).

**Validation Result**: ✅ **PASSED** — Found 1 acceptable warning (A005), consistent with CI behavior.

### 5. Run Python Samples Linting (flake8)

```bash
podman exec openvino-validator bash -c "
  cd /app/samples/python && \
  python3 -m flake8 ./ --config=setup.cfg
"
```

**Expected**: Exit code 0, no output (clean).

**Validation Result**: ✅ **PASSED** — No issues found.

### 6. Run Python Type Checking (mypy)

```bash
podman exec openvino-validator bash -c "
  cd /app/src/bindings/python && \
  python3 -m mypy ./src/openvino --config-file ./setup.cfg
"
```

**Expected**: "Success: no issues found in 105 source files"

**Validation Result**: ✅ **PASSED** — All type checks passed.

### 7. Auto-fix Python Code Style (if needed)

```bash
# For Python API
podman exec openvino-validator bash -c "
  cd /app/src/bindings/python && \
  python3 -m black -l 160 -S ./src/openvino
"

# For Python samples
podman exec openvino-validator bash -c "
  cd /app/samples/python && \
  python3 -m black -l 160 -S ./
"
```

### 8. Cleanup

```bash
podman rm -f openvino-validator
```

---

## Full Build and Test (Not Container-Validated)

The following steps are required for C++ linting and testing but were **not validated in container** due to time/resource constraints:

### Prerequisites

- 16+ CPU cores recommended
- 32GB+ RAM
- 20GB+ free disk space
- 90+ minutes build time

### Build Steps

```bash
# 1. Initialize submodules (10-15 minutes)
git submodule update --init --recursive

# 2. Install build dependencies (Ubuntu/Debian)
sudo ./install_build_dependencies.sh

# 3. Configure CMake
cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DENABLE_PYTHON=ON \
  -DENABLE_TESTS=ON \
  -DENABLE_WHEEL=ON \
  -B build

# 4. Build (60-90 minutes on 16 cores)
cmake --build build --parallel

# 5. Install Python wheel (if built)
pip install build/wheel/openvino-*.whl
```

### C++ Linting

```bash
# Requires CMake configuration first
cmake -DENABLE_PYTHON=ON -DENABLE_TESTS=ON -B build

# clang-format check
cmake --build build --target clang_format_fix_all -j8

# ShellCheck
cmake --build build --target ov_shellcheck -j8

# Naming convention check (requires clang-14 and libclang-14-dev)
cmake --build build --target ncc_all -j8
```

### C++ Tests

```bash
# After successful build:
cd build

# Core unit tests
./bin/intel64/Release/ov_core_unit_tests --gtest_print_time=1

# Inference unit tests
./bin/intel64/Release/ov_inference_unit_tests --gtest_print_time=1

# Or run all tests via ctest
ctest --parallel 8 --output-on-failure
```

### Python Tests

```bash
# Requires built and installed openvino wheel
export PYTHONPATH=$(pwd)/bin/intel64/Release/python:$PYTHONPATH

# Python API tests
cd src/bindings/python
pytest tests -m "not template_extension" -v -k 'not _cuda'

# ONNX frontend tests
pytest ../../../src/frontends/onnx/tests -v \
  --ignore=tests/test_zoo_models.py \
  -k 'not _cuda'
```

### Run Single Test

```bash
# Python test file
pytest src/bindings/python/tests/test_runtime/test_core.py -v

# Python single test
pytest src/bindings/python/tests/test_runtime/test_core.py::test_function_name -v

# C++ single test
./bin/intel64/Release/ov_core_unit_tests --gtest_filter=TestSuite.TestName
```

---

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| **Install** | `apt-get install` + `pip install` | ✅ PASS | All Python tooling installed successfully |
| **Lint: Python API** | `flake8 ./src/openvino` | ✅ PASS | 1 expected A005 warning (acceptable) |
| **Lint: Python Samples** | `flake8 ./` | ✅ PASS | Clean, no issues |
| **Lint: Python Types** | `mypy ./src/openvino` | ✅ PASS | 105 files checked, all passed |
| **Build** | `cmake --build` | ⏭️ SKIP | Requires submodules + 60-90 min compile |
| **Test** | `pytest tests` | ⏭️ SKIP | Requires built artifacts |

**Summary**: Python linting tools validated successfully. C++ build and tests skipped due to infrastructure requirements.

---

## CI/CD

### Gating Checks (GitHub Actions)

All pull requests must pass:

1. **Code Style** (`.github/workflows/code_style.yml`)
   - clang-format-15 for C++ code
   - ShellCheck for shell scripts
   - Naming convention checker (ncc)

2. **Python Checks** (`.github/workflows/py_checks.yml`)
   - flake8 on Python API, samples, and tests
   - mypy type checking on Python API
   - Only runs when Python files change

3. **Build** (`.github/workflows/ubuntu_22.yml` and others)
   - Full CMake build on multiple platforms
   - Debian/RPM package generation
   - Wheel building for Python

4. **Tests** (various `job_*_tests.yml` workflows)
   - C++ unit tests (gtest)
   - Python unit tests (pytest)
   - CPU functional tests
   - GPU tests (if GPU available)
   - Layer tests (TensorFlow, PyTorch, ONNX)
   - Model tests
   - Samples tests

### Smart CI System

OpenVINO uses a "Smart CI" system that analyzes changed files and only runs relevant tests. For example:

- Changes to `src/bindings/python/**` trigger Python checks and tests
- Changes to `src/plugins/intel_cpu/**` trigger CPU plugin tests
- Documentation-only changes (`*.md`, `*.rst`) skip most tests

---

## Conventions

### Test File Naming

- **C++**: `*_test.cpp` (e.g., `core_test.cpp`)
- **Python**: `test_*.py` (e.g., `test_core.py`)

### Test Function Naming

- **C++**: `TEST(TestSuite, TestName)` or `TEST_F(FixtureClass, TestName)`
- **Python**: `def test_function_name()` or `class TestClassName` with `def test_method_name()`

### Code Style

- **C++**: Google C++ Style Guide enforced by clang-format
- **Python**:
  - Max line length: 160
  - Google docstring convention
  - Double quotes for strings
  - Enforced by flake8 + black

### Import Style

- **Python**: Absolute imports from `openvino` package
  ```python
  from openvino.runtime import Core
  from openvino.preprocess import PrePostProcessor
  ```

---

## Gaps & Caveats

1. **Submodule Dependency**: ~20 git submodules must be initialized before build (10-15 min download time)

2. **Long Build Time**: C++ compilation takes 60-90 minutes on a well-equipped machine (16 cores, 32GB RAM)

3. **No Quick C++ Validation**: Unlike pure Python projects, there's no fast lint-only path for C++ changes. Every validation requires full build.

4. **Test Artifact Dependency**: All tests require built artifacts. Cannot run tests without successful build.

5. **Hardware Requirements**: Some tests require specific hardware:
   - GPU tests need Intel integrated or discrete GPU
   - NPU tests need Intel NPU
   - Skipped if hardware unavailable

6. **Model Dependencies**: Layer tests and model tests download models from external sources, requiring network access and significant disk space

7. **Platform-Specific Tests**: CI runs on Linux (Ubuntu 20/22/24, Fedora, Debian), Windows, macOS (Intel/ARM), Android, WebAssembly — full validation requires all platforms

8. **Python Wheel Dependency**: Python tests import from the `openvino` package, which must be built as a wheel and installed first

---

## Recommendations for Patch Validation

### For Python-Only Changes

Use the container recipe above. Validates in **~5 minutes**:
- ✅ flake8 linting
- ✅ mypy type checking
- ✅ black formatting

### For C++ Changes

**Option 1: Local Build** (if you have resources)
- Clone repository
- Initialize submodules
- Run full build pipeline
- Run relevant C++ unit tests
- **Time**: 90+ minutes first build, 10-20 minutes incremental

**Option 2: Rely on CI**
- Push to PR
- Wait for GitHub Actions CI
- Review failing checks
- **Time**: 30-60 minutes per iteration

### For Mixed Changes

Validate Python locally (fast), push for full C++ CI validation.

---

## Quick Reference

```bash
# Python linting (fast, no build required)
cd src/bindings/python
python3 -m flake8 ./src/openvino --config=setup.cfg
python3 -m mypy ./src/openvino --config-file ./setup.cfg

# C++ linting (requires CMake config)
cmake -DENABLE_TESTS=ON -B build
cmake --build build --target clang_format_fix_all -j8

# Full build
git submodule update --init --recursive
cmake -DCMAKE_BUILD_TYPE=Release -DENABLE_PYTHON=ON -DENABLE_TESTS=ON -B build
cmake --build build --parallel

# Run all tests
ctest --test-dir build --parallel 8

# Run specific test
./build/bin/intel64/Release/ov_core_unit_tests --gtest_filter=Core.*
```
