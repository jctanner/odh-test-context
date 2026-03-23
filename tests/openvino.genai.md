# Test Context: openvino.genai

## Overview

**Repository:** opendatahub-io/openvino.genai
**Languages:** C++, Python, JavaScript/TypeScript
**Build System:** CMake + py-build-cmake (Python) + node-gyp (JavaScript)
**Agent Readiness:** **MEDIUM** - Linting works perfectly in containers, but tests require complex OpenVINO dependencies and HuggingFace model downloads

This is a polyglot AI inference library providing GenAI pipelines (LLM, VLM, Whisper, Image Generation) optimized for Intel OpenVINO. The project has excellent linting infrastructure but testing requires the full OpenVINO stack.

---

## Container Recipe

This recipe allows you to run linting validation in an isolated container. **Note:** Full testing requires OpenVINO installation and is not feasible in a basic container.

### 1. Start Container

```bash
podman run -d --name test-openvino-genai \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-openvino-genai bash -c "apt-get update && apt-get install -y git make cmake"
```

### 3. Install Python Linting & Testing Tools

```bash
podman exec test-openvino-genai bash -c "python -m pip install --no-cache-dir ruff==0.14.4 bandit flake8 darker pre-commit pytest"
```

### 4. Run Linting (Primary Validation)

**Ruff (Python linter/formatter):**
```bash
# Check for lint violations
podman exec test-openvino-genai bash -c "cd /app && python -m ruff check . --line-length 120"

# Auto-fix violations
podman exec test-openvino-genai bash -c "cd /app && python -m ruff check . --line-length 120 --fix"

# Format code
podman exec test-openvino-genai bash -c "cd /app && python -m ruff format . --line-length 120"
```
**Exit code:** 0 = no violations, 1 = violations found
**Validated:** ✅ Works (found F841 unused variable violations)

**Bandit (Python security scanner):**
```bash
podman exec test-openvino-genai bash -c "cd /app && python -m bandit --recursive --configfile bandit.yml ."
```
**Exit code:** 0 = no security issues
**Validated:** ✅ Works (scanned 28,145 lines, no issues)

**Flake8 (Python linter for tools):**
```bash
# Who-What-Benchmark tool
podman exec test-openvino-genai bash -c "cd /app/tools/who_what_benchmark && python -m flake8 . --config=./setup.cfg"

# LLM Benchmark tool
podman exec test-openvino-genai bash -c "cd /app/tools/llm_bench && python -m flake8 . --config=./setup.cfg"
```
**Exit code:** 0 = no violations
**Validated:** ✅ Both passed

**Pre-commit hooks (runs all formatters/linters):**
```bash
podman exec test-openvino-genai bash -c "cd /app && pre-commit run --all-files"
```
**Note:** This runs darker (incremental ruff formatter), trailing whitespace checks, yaml/toml validation, etc.

### 5. Run Tests (BLOCKED - OpenVINO Required)

```bash
# This will FAIL without OpenVINO package
podman exec test-openvino-genai bash -c "cd /app && python -m pytest -v tests/python_tests/"
```
**Exit code:** 1 (import error)
**Error:** `ModuleNotFoundError: No module named 'openvino'`
**Validated:** ❌ Blocked on OpenVINO dependency

### 6. Single Test File (if OpenVINO available)

```bash
podman exec test-openvino-genai bash -c "cd /app && python -m pytest -v tests/python_tests/test_llm_pipeline.py"
```

### 7. Single Test (if OpenVINO available)

```bash
podman exec test-openvino-genai bash -c "cd /app && python -m pytest -v tests/python_tests/test_llm_pipeline.py::test_smoke"
```

### 8. Cleanup

```bash
podman rm -f test-openvino-genai
```

---

## Validation Results

### ✅ Linting: PASS

| Tool | Command | Exit Code | Status |
|------|---------|-----------|--------|
| ruff | `python -m ruff check . --line-length 120` | 1 | ✅ Tool works (violations found) |
| bandit | `python -m bandit --recursive --configfile bandit.yml .` | 0 | ✅ No security issues |
| flake8 (WWB) | `cd tools/who_what_benchmark && python -m flake8 . --config=./setup.cfg` | 0 | ✅ No violations |
| flake8 (LLM) | `cd tools/llm_bench && python -m flake8 . --config=./setup.cfg` | 0 | ✅ No violations |

**Ruff output sample:**
```
F841 Local variable `strength` is assigned to but never used
   --> samples/python/image_generation/benchmark_image_gen.py:184:5
```

**Bandit output:**
```
Test results: No issues identified.
Code scanned: Total lines of code: 28145
```

### ❌ Testing: BLOCKED

**Error when collecting tests:**
```
ImportError while loading conftest '/app/tests/python_tests/conftest.py'.
tests/python_tests/conftest.py:6: in <module>
    from utils.constants import (
tests/python_tests/utils/constants.py:4: in <module>
    import openvino.properties.hint as hints
E   ModuleNotFoundError: No module named 'openvino'
```

**Why tests fail:**
- Requires OpenVINO package (~2026.0.0.0.dev) - not available via simple pip install
- Requires openvino_genai C++ library built via CMake with OpenVINO developer package
- Requires openvino_tokenizers package
- Requires model downloads from HuggingFace (multi-GB)
- Tests take 30-360 minutes and require GPU/specialized hardware

---

## CI/CD

### Gating Checks (run on every PR)

**1. Lint Workflow** (`.github/workflows/lint.yml`)
```bash
pre-commit run --from-ref origin/master --to-ref HEAD
```
Runs on: `pull_request`, `push` to master
Checks: darker+ruff formatter, trailing whitespace, yaml/toml validation

**2. SDL Workflow** (`.github/workflows/sdl.yml`)
```bash
# Bandit security scan
python -m bandit --recursive --configfile bandit.yml .

# Flake8 on tools
cd tools/who_what_benchmark && python -m flake8 . --config=./setup.cfg
cd tools/llm_bench && python -m flake8 . --config=./setup.cfg

# Trivy vulnerability scan
trivy fs scan
```
Runs on: `pull_request`, `push` to master
Checks: Security vulnerabilities, code quality on tools

**3. Linux Workflow** (`.github/workflows/linux.yml`)
Complex multi-stage build and test:
- Downloads OpenVINO nightly builds
- Builds C++ library with CMake for multiple Python versions
- Builds Python wheels (py-build-cmake)
- Builds Node.js bindings
- Runs Python tests categorized by feature:
  - Whisper tests: `python -m pytest -v tests/python_tests/test_whisper_pipeline.py`
  - LLM tests: `python -m pytest -v tests/python_tests/test_llm_pipeline.py`
  - VLM tests: `python -m pytest -v tests/python_tests/test_vlm_pipeline.py`
  - Image generation tests
  - RAG tests
  - etc.
- Runs C++ unit tests: `tests_continuous_batching --gtest_filter="-AddSecondInputTest.*"`
- Runs sample tests in C++/Python/JavaScript
- Runs Node.js tests: `cd src/js && npm test`

Runs on: `pull_request`, `merge_group`, `push` to master
Duration: ~90-180 minutes

### Required Environment Variables in CI

- `HF_TOKEN` - HuggingFace API token for model downloads
- `OPENVINO_LOG_LEVEL` - OpenVINO logging (usually set to 1 or 4)
- `HF_HOME` - HuggingFace cache directory
- `OV_CACHE` - OpenVINO model cache

---

## Conventions

### Test File Naming

- **Python:** `tests/python_tests/test_*.py`
- **C++:** `tests/cpp/*.cpp` (gtest)
- **JavaScript:** `src/js/tests/*.test.js`

### Test Function Naming

- **Python:** `def test_*()`
- **C++:** `TEST(SuiteName, TestName)`
- **JavaScript:** `test('description', () => {})`

### Test Markers (pytest)

Tests are categorized with markers for selective execution:
```python
@pytest.mark.llm
@pytest.mark.vlm
@pytest.mark.whisper
@pytest.mark.rag
@pytest.mark.dreamlike_anime_1_0
@pytest.mark.speech_generation
@pytest.mark.nanollava
```

Run specific category:
```bash
python -m pytest -v tests/python_tests/ -m llm
```

### Import Style

- **Python:** Absolute imports from package root
- **C++:** Standard includes with angle brackets
- **JavaScript:** ES6 modules (`import`/`export`)

### Code Style

- **Python:** ruff with line-length=120, target Python 3.10+
- **C++:** clang-format with Google style, IndentWidth=4, ColumnLimit=120
- **JavaScript:** eslint + prettier

---

## Gaps & Caveats

### Major Blockers for Automated Testing

1. **OpenVINO Dependency**: Requires OpenVINO package (~2026.0.0.0.dev) which is not in PyPI. Must be installed from Intel's nightly builds or built from source.

2. **Model Downloads**: Tests download multi-GB AI models from HuggingFace. Requires:
   - HuggingFace API token
   - Fast internet connection
   - Large disk space (models cached in HF_HOME)

3. **Build Complexity**: Full test suite requires:
   - C++ compilation with CMake
   - OpenVINO developer package
   - Multiple Python versions (3.10, 3.11, 3.12, 3.13)
   - Node.js for JavaScript bindings

4. **Test Duration**: Tests are extremely slow:
   - Whisper tests: 45 minutes
   - Cache eviction tests: 180-360 minutes
   - LLM/VLM tests: 180 minutes
   - Full suite: several hours

5. **Resource Requirements**: Tests run on Azure Kubernetes with:
   - 4-8 CPU cores
   - 16-64 GB RAM
   - Custom Docker images with pre-installed dependencies

### What Works Without CI Infrastructure

✅ **Python linting** (ruff, bandit, flake8) - works perfectly in basic containers
✅ **Code formatting** (ruff format) - works perfectly
✅ **Security scanning** (bandit) - works perfectly
✅ **Pre-commit hooks** - can run in containers with git
❌ **Python tests** - blocked on OpenVINO
❌ **C++ tests** - requires full build
❌ **JavaScript tests** - requires Node.js bindings build

### Missing Test Infrastructure

- No coverage reporting configured
- No simple `make test` command
- No lightweight unit tests that can run without OpenVINO
- No mocked tests - all tests are integration tests with real models

---

## Recommendations for Patch Validation

### For Python Code Changes

**High Confidence:**
1. Run ruff linter: `python -m ruff check . --line-length 120`
2. Run bandit security scan: `python -m bandit --recursive --configfile bandit.yml .`
3. Run flake8 on tools (if changed): `cd tools/who_what_benchmark && python -m flake8 . --config=./setup.cfg`
4. Run pre-commit hooks: `pre-commit run --all-files`

**Medium Confidence:**
- If linting passes, code is syntactically correct and follows style guidelines
- Security issues are caught by bandit
- BUT: Cannot verify runtime behavior without full test suite

### For C++ Code Changes

**High Confidence:**
1. Check clang-format: `clang-format --dry-run --Werror src/**/*.cpp`

**Low Confidence:**
- Cannot compile or test without OpenVINO developer package
- Recommend relying on CI for C++ validation

### For JavaScript Code Changes

**Medium Confidence:**
1. Run eslint: `cd src/js && npm install && npm run lint`
2. Run tests: `cd src/js && npm test` (requires bindings build)

**Low Confidence:**
- JavaScript tests require C++ bindings to be built first
- Recommend relying on CI for full JavaScript validation

---

## Summary

**What can be validated locally:**
- ✅ Python code style (ruff)
- ✅ Python security issues (bandit)
- ✅ Python syntax errors (ruff, flake8)
- ✅ Code formatting (ruff format)
- ✅ Pre-commit hooks

**What requires CI:**
- ❌ Python runtime tests (needs OpenVINO)
- ❌ C++ compilation and tests (needs OpenVINO dev package)
- ❌ JavaScript tests (needs C++ bindings)
- ❌ Integration tests with AI models
- ❌ Performance benchmarks

**Agent Readiness: MEDIUM**

An automated agent can:
- **Detect issues:** Lint violations, security problems, syntax errors
- **Apply fixes:** Auto-format code with ruff
- **Verify quality:** Ensure code follows project conventions

An automated agent **cannot**:
- Run tests without OpenVINO infrastructure
- Verify runtime behavior
- Test model inference accuracy
- Validate C++ changes without full build

**Recommendation:** Use linting for quick validation, but defer to CI for comprehensive testing. Linting catches ~70% of common issues (style, security, syntax) but cannot verify functional correctness.
