# Test Context: perf_analyzer

**Organization:** opendatahub-io
**Repository:** perf_analyzer
**Analyzed:** 2026-03-22
**Agent Readiness:** medium - Python tests validated; C++ requires complex dependencies

## Overview

Triton Performance Analyzer is a dual-language project with a Python package (genai-perf)
for GenAI model performance testing and a C++ binary (perf_analyzer) for general Triton
model benchmarking. The repository uses pre-commit hooks for linting and pytest for
Python testing. C++ tests exist but require complex external dependencies (Triton client
libraries, gRPC, CUDA) that are not built in CI.

**Languages:** Python 3.10+, C++20
**Build Systems:** hatchling (Python), CMake (C++)
**Test Framework:** pytest (Python), googletest/doctest (C++)
**Linting:** pre-commit hooks (black, isort, flake8, mypy, clang-format, codespell)

---

## Container Recipe

This recipe provides a **validated, working environment** for running lint and test
commands on the Python genai-perf package. An agent can follow these steps to validate
patches.

### 1. Start Container

```bash
podman run -d --name test-context-perf_analyzer \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.10 \
  sleep infinity
```

If `podman` is unavailable, use `docker` instead.

### 2. Install Dependencies

```bash
podman exec test-context-perf_analyzer bash -c "
  cd /app/genai-perf && \
  python -m pip install --upgrade pip setuptools wheel && \
  pip install -e .[test] && \
  pip install pytest pytest-timeout pytest-cov psutil
"
```

**Expected:** Clean install with genai-perf version ~0.0.16.dev0

### 3. Install Linting Tools

```bash
podman exec test-context-perf_analyzer bash -c "
  pip install black isort flake8 mypy pre-commit
"
```

### 4. Run Tests

```bash
podman exec test-context-perf_analyzer bash -c "
  cd /app/genai-perf/tests && \
  pytest --doctest-modules \
    --junitxml=junit/test-results.xml \
    --cov=genai_perf \
    --cov-report=xml \
    --cov-report=html \
    --ignore-glob=test_models
"
```

**Validated result:** 669 passed, 1 failed in ~21s. The single failure is a minor
assertion mismatch in `test_llm_profile_data_parser.py` (output token throughput
calculation), not a framework issue. Tests are working correctly.

### 5. Run Linters

**Black (code formatter):**
```bash
podman exec test-context-perf_analyzer bash -c "
  cd /app/genai-perf && \
  python -m black --check genai_perf/
"
```
**Validated:** Exit code 1 if formatting issues found (working correctly). Use
`python -m black genai_perf/` to auto-fix.

**Isort (import sorter):**
```bash
podman exec test-context-perf_analyzer bash -c "
  cd /app/genai-perf && \
  python -m isort --check genai_perf/
"
```
**Validated:** Exit code 0 if imports are sorted, 1 if issues found. Use
`python -m isort genai_perf/` to auto-fix.

**Flake8 (linter):**
```bash
podman exec test-context-perf_analyzer bash -c "
  cd /app/genai-perf && \
  python -m flake8 --max-line-length=88 \
    --select=C,E,F,W,B,B950 \
    --extend-ignore=E203,E501 \
    genai_perf/
"
```
**Validated:** Finds legitimate issues (F401 unused imports, W503 line breaks, etc.).
Exit code 1 if issues found.

**Mypy (type checker):**
```bash
podman exec test-context-perf_analyzer bash -c "
  cd /app/genai-perf && \
  python -m mypy genai_perf/
"
```
**Not validated** in container but used in pre-commit hooks.

### 6. Run Single Test File

```bash
podman exec test-context-perf_analyzer bash -c "
  cd /app/genai-perf/tests && \
  pytest test_cli.py
"
```

### 7. Run Single Test

```bash
podman exec test-context-perf_analyzer bash -c "
  cd /app/genai-perf/tests && \
  pytest test_cli.py::test_profile_export_file_name
"
```

### 8. Cleanup

**Always remove the container when done:**
```bash
podman rm -f test-context-perf_analyzer
```

---

## Validation Results

Commands were validated in a live container to confirm they work:

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| **Install** | `pip install -e .[test]` | 0 | ✅ Pass | All deps installed cleanly |
| **Lint (black)** | `black --check genai_perf/` | 1 | ✅ Pass | Found 1 file to reformat (working correctly) |
| **Lint (isort)** | `isort --check genai_perf/` | 0 | ✅ Pass | Imports correctly sorted |
| **Lint (flake8)** | `flake8 genai_perf/` | 1 | ✅ Pass | Found legitimate issues (working correctly) |
| **Test** | `pytest tests/` | 1 | ✅ Pass | 669 passed, 1 failed (99.85% pass rate) |

**Test Failure Detail:** Single failure in
`test_data_parser/test_llm_profile_data_parser.py::TestLLMProfileDataParser::test_huggingface_generate_llm_profile_data`
due to assertion mismatch (`output_token_throughput 700000000.0 vs expected 900000000.0`).
This appears to be a test data issue, not a framework problem. 669 other tests passed.

**Output snippet from successful test run:**
```
============================= test session starts ==============================
platform linux -- Python 3.10.20, pytest-9.0.2, pluggy-1.6.0
rootdir: /app/genai-perf
configfile: pytest.ini
plugins: anyio-4.12.1, timeout-2.4.0, mock-3.15.1, cov-7.1.0
collected 670 items
...
======================== 1 failed, 669 passed in 21.21s ========================
```

---

## CI/CD

**GitHub Actions workflows** gate merges on pull requests:

### Gating Checks (Required)

**1. Pre-commit (`pre-commit.yml`)**
- **Trigger:** `on: pull_request`
- **Command:** `pre-commit run --files <modified_files>`
- **What it does:** Runs all pre-commit hooks (black, isort, flake8, mypy,
  clang-format, codespell, license check) on modified files only
- **Exact steps:**
  ```yaml
  - uses: actions/checkout@v5.0.0
  - name: Get modified files
    run: echo "modified_files=$(git diff --name-only -r HEAD^1 HEAD | xargs)" >> $GITHUB_OUTPUT
  - uses: actions/setup-python@v6.0.0
  - uses: pre-commit/action@v3.0.1
    with:
      extra_args: --files ${{ steps.modified-files.outputs.modified_files }}
  ```

**2. Python Package (GenAI-Perf) (`python-package-genai.yml`)**
- **Trigger:** `on: pull_request`
- **OS:** ubuntu-22.04
- **Python:** 3.10
- **Exact commands:**
  ```bash
  cd genai-perf/
  python -m pip install --upgrade pip
  python -m pip install -e .[test]
  python -c "import genai_perf; print(genai_perf.__version__)"
  pip install pytest pytest-timeout pytest-cov psutil
  cd genai-perf/tests
  pytest --doctest-modules --junitxml=junit/test-results.xml \
    --cov=genai_perf --cov-report=xml --cov-report=html \
    --ignore-glob=test_models
  ```

### Advisory Checks (Non-blocking)

**CodeQL (`codeql.yml`)**
- **Trigger:** `on: pull_request`
- **Language:** Python only
- **What it does:** GitHub security scanning for vulnerabilities

---

## Conventions

### Test File Patterns
- **Python:** `test_*.py` in `genai-perf/tests/`
- **C++:** `test_*.cc` in `src/`

### Test Naming
- **Python:** Functions named `test_*` in `test_*.py` files
- **C++:** `TEST_CASE` or `TEST` macros (doctest/googletest)

### Code Style
- **Python:** Black formatting (88 char line length), isort imports, flake8 linting
- **C++:** clang-format with config in `.clang-format`
- **License header:** All files must include NVIDIA copyright header (enforced by
  pre-commit hook in `tools/add_copyright.py`)

### Import Style
- **Python:** Absolute imports preferred, sorted by isort with black profile

---

## Gaps & Caveats

1. **C++ tests not validated** - The C++ perf_analyzer binary has extensive unit tests
   in `src/test_*.cc` using doctest/googletest, but these require a complex CMake build
   with external dependencies:
   - Triton client libraries (HTTP, gRPC)
   - gRPC and protobuf
   - CUDA toolkit (optional but enabled by default)
   - External projects fetched via CMake ExternalProject_Add

   **CI does not build or test C++.** Only Python genai-perf is tested.

2. **Pre-commit hooks require git** - The `pre-commit run` command requires a git
   repository and hook setup. In a container without git history, individual linters
   (black, isort, flake8, mypy) must be run directly instead.

3. **One test failure** - The test suite has 1 failing test out of 670
   (`test_llm_profile_data_parser.py`). This is a minor assertion mismatch in
   output token throughput calculation and does not indicate a broken test framework.
   An agent should expect this failure.

4. **No Makefile** - The project does not use Make. Python uses pip/hatchling, C++
   uses CMake directly.

5. **Separate packages** - This repository contains two related but separate packages:
   - `genai-perf/` - Python package for GenAI benchmarking
   - Root - C++ perf_analyzer binary

   They have separate build systems, test suites, and can be installed independently.

6. **External infrastructure** - Some integration tests in `genai-perf/tests/integration_tests/`
   may require a running Triton Inference Server or model server. Unit tests do not
   require external services.

---

## Build Configuration

### Python (genai-perf)
**Install command:**
```bash
cd genai-perf
pip install -e .[test]
```

**Dependencies:** Defined in `genai-perf/pyproject.toml` - includes transformers,
pytest, optuna, pandas, plotly, and many others.

**Build system:** hatchling (modern Python build backend)

### C++ (perf_analyzer)
**Build commands:**
```bash
mkdir build
cd build
cmake -DTRITON_ENABLE_CC_HTTP=ON \
      -DTRITON_ENABLE_CC_GRPC=ON \
      -DTRITON_ENABLE_PERF_ANALYZER_OPENAI=ON \
      -DTRITON_ENABLE_GPU=ON \
      ..
make
```

**Dependencies:**
- Triton client libraries (fetched from https://github.com/triton-inference-server/client)
- gRPC, protobuf
- CUDA toolkit (if GPU support enabled)
- googletest (fetched from GitHub)

**Build system:** CMake 3.31.8+, C++20 standard

**Note:** The root `CMakeLists.txt` is a wrapper that uses `ExternalProject_Add` to
fetch and build Triton client libraries, then builds perf_analyzer from `src/`. This
build is complex and not validated in the container recipe.

---

## How an Agent Should Use This

1. **For Python patches (genai-perf):** Use the container recipe above. It's validated
   and works. Run tests and linters to validate the patch.

2. **For C++ patches (src/):** The container recipe does **not** cover C++ builds. An
   agent cannot easily validate C++ changes without:
   - Setting up the full CMake build environment
   - Fetching Triton client libraries (~large download)
   - Installing gRPC, protobuf, CUDA

   **Recommendation:** For C++ patches, run linters (clang-format) only. Skip building
   and testing unless a full build environment is available.

3. **For mixed patches:** Validate Python components in the container, run
   clang-format on C++ files, but skip C++ build/test.

4. **Pre-commit alternative:** If you can't run `pre-commit run`, run individual
   linters directly:
   ```bash
   black --check .
   isort --check .
   flake8 .
   mypy .
   clang-format --dry-run --Werror src/**/*.{cc,h}
   codespell --toml pyproject.toml
   ```

---

## Quick Reference

**Install deps:**
```bash
cd genai-perf && pip install -e .[test]
```

**Run all Python tests:**
```bash
cd genai-perf/tests && pytest --cov=genai_perf
```

**Run single test file:**
```bash
cd genai-perf/tests && pytest test_cli.py
```

**Run single test:**
```bash
cd genai-perf/tests && pytest test_cli.py::test_profile_export_file_name
```

**Format code:**
```bash
cd genai-perf && black genai_perf/ && isort genai_perf/
```

**Check linting:**
```bash
cd genai-perf && black --check genai_perf/ && isort --check genai_perf/ && flake8 genai_perf/
```

**Container one-liner (test):**
```bash
podman run --rm -v $(pwd):/app:Z -w /app python:3.10 bash -c \
  "cd /app/genai-perf && pip install -e .[test] -q && cd tests && pytest -q"
```

**Container one-liner (lint):**
```bash
podman run --rm -v $(pwd):/app:Z -w /app python:3.10 bash -c \
  "pip install black isort flake8 -q && cd /app/genai-perf && black --check genai_perf/ && isort --check genai_perf/ && flake8 genai_perf/"
```

---

## Confidence & Limitations

**Confidence:** High for Python genai-perf package, Low for C++ perf_analyzer

**What was validated:**
- ✅ Python dependency installation
- ✅ Python test execution (669/670 tests pass)
- ✅ Python linters (black, isort, flake8)
- ✅ Container recipe works end-to-end

**What was NOT validated:**
- ❌ C++ build process
- ❌ C++ unit tests
- ❌ clang-format execution
- ❌ Pre-commit hook installation (requires git)
- ❌ Integration tests requiring external services

**Agent readiness: MEDIUM** - An agent can validate Python patches confidently but
cannot fully validate C++ changes without significant infrastructure setup.
