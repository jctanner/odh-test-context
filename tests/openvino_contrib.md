# Test Context: openvino_contrib

**Agent Readiness: LOW** — Tests require full OpenVINO build (multi-hour process) and external dependencies. Only linting can be validated in containers.

## Overview

openvino_contrib is a multi-module repository for OpenVINO extra modules. Languages: C++, Python, Java, TypeScript/JavaScript. Build system: CMake (primary), Gradle (Java), npm (TypeScript). This is NOT a standalone repository — it requires the main OpenVINO repository to be built with `-DOPENVINO_EXTRA_MODULES` pointing to these modules.

**Modules:**
- **nvidia_plugin**: CUDA plugin for NVIDIA GPUs (C++/CUDA)
- **java_api**: Java bindings for OpenVINO (Java/C++)
- **custom_operations**: Custom operation examples (C++/Python)
- **token_merging**: Token merging implementation (Python)
- **openvino_code**: VSCode extension for AI code completion (TypeScript/Python)
- **llama_cpp_plugin**: Llama.cpp integration plugin (C++)

## Container Recipe

### TypeScript/JavaScript Linting (openvino_code)

**Base image:** `node:16`

**Start container:**
```bash
podman run -d --name test-openvino-code \
  -v $(pwd):/app:Z \
  -w /app \
  node:16 \
  sleep infinity
```

**Install dependencies:**
```bash
podman exec test-openvino-code bash -c "cd /app/modules/openvino_code && npm ci"
```

**Run lint (✓ validated):**
```bash
podman exec test-openvino-code bash -c "cd /app/modules/openvino_code && npm run lint:all"
```
- Exit code: 0
- All checks passed
- Includes eslint for main extension and side-panel-ui workspace

**Cleanup:**
```bash
podman rm -f test-openvino-code
```

### Python Linting (openvino_code/server)

**Base image:** `python:3.11`

**Start container:**
```bash
podman run -d --name test-openvino-python \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

**Install linters:**
```bash
podman exec test-openvino-python bash -c "pip install ruff black"
```

**Run ruff (✓ validated):**
```bash
podman exec test-openvino-python bash -c "cd /app/modules/openvino_code/server && ruff check ."
```
- Exit code: 0
- All checks passed

**Run black (✗ finds existing violations):**
```bash
podman exec test-openvino-python bash -c "cd /app/modules/openvino_code/server && black --check ."
```
- Exit code: 1
- Finds 3 files that need reformatting (main.py, src/app.py, src/generators.py)
- This is existing code style debt, not a configuration issue

**Fix with black:**
```bash
podman exec test-openvino-python bash -c "cd /app/modules/openvino_code/server && black ."
```

**Cleanup:**
```bash
podman rm -f test-openvino-python
```

### Tests (NOT validated — require full OpenVINO build)

Tests cannot be validated in containers without building OpenVINO from source. All test commands below require multi-hour build process.

## Validation Results

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| **lint** | `cd modules/openvino_code && npm run lint:all` | ✓ PASS | TypeScript/JavaScript linting passed |
| **lint** | `cd modules/openvino_code/server && ruff check .` | ✓ PASS | Python ruff linting passed |
| **lint** | `cd modules/openvino_code/server && black --check .` | ✗ FAIL | Found 3 files with formatting issues (existing violations) |
| **test** | `pytest modules/token_merging/tests/` | ✗ SKIP | Requires `openvino.runtime` module from full build |
| **test** | `pytest modules/custom_operations/tests/` | ✗ SKIP | Requires `CUSTOM_OP_LIB` env var with built library |
| **test** | `gradle test` (java_api) | ✗ SKIP | Requires full OpenVINO build + testdata |

## CI/CD Configuration

**System:** GitHub Actions

**Gating Workflows:**

1. **code_style.yml** (Java linting)
   - Trigger: PR/push to `modules/java_api/**`
   - Command: `google-java-format --set-exit-if-changed -a -i`
   - Auto-fixes and commits if violations found

2. **linux.yml** (Main build and test)
   - Trigger: PR/push to master
   - Steps:
     1. Clone OpenVINO main repository
     2. Clone openvino_contrib
     3. `cmake -DOPENVINO_EXTRA_MODULES=${OPENVINO_CONTRIB_REPO}/modules ... -B ${BUILD_DIR}`
     4. `cmake --build ${BUILD_DIR} --parallel`
     5. Java tests: `cd modules/java_api && gradle test -Prun_tests -DMODELS_PATH=${TEST_DATA}`
     6. Custom operations: `CUSTOM_OP_LIB=<lib> python -m pytest modules/custom_operations/tests/run_tests.py`
   - Container: `ubuntu:20.04`
   - Requires: ~150 minutes, 16-core runner

3. **openvino_code.yml** (VSCode extension)
   - Trigger: PR to `modules/openvino_code/**`
   - Extension lint: `npm ci && npm run lint:all`
   - Server lint: `ruff check . && black --check .`
   - Node.js 16.x, Python 3.8

4. **token_merging.yml** (Python tests)
   - Trigger: PR/push to `modules/token_merging/**`
   - Command: `pip install modules/token_merging/[tests] && python -m pytest modules/token_merging/tests/`
   - Python 3.11

5. **llama_cpp_plugin_build_and_test.yml**
   - Trigger: PR to `modules/llama_cpp_plugin/**`
   - Build OpenVINO with llama_cpp_plugin
   - Download and convert GPT-2 model to GGUF format
   - Run `llama_cpp_func_tests` and `llama_cpp_e2e_tests`

6. **test_cuda.yml** (NVIDIA plugin - custom runner)
   - Trigger: PR to `modules/nvidia_plugin/**`
   - Runs on custom hardware with CUDA
   - Formatting check: `./modules/nvidia_plugin/utils/check.sh`
   - Build and run functional/unit tests

## Linting Configuration

### TypeScript/JavaScript (openvino_code)
- **Tool:** eslint
- **Config:** `modules/openvino_code/.eslintrc.js`
- **Extends:** airbnb-typescript, eslint:recommended, prettier
- **Run:** `cd modules/openvino_code && npm run lint:all`
- **Fix:** `npm run lint:fix`

### Python (openvino_code/server)
- **Tools:** ruff, black
- **Config:** `modules/openvino_code/server/pyproject.toml`
- **Ruff ignores:** C901, E501, E741, W605, F401, W292
- **Black line length:** 119
- **Run:** `cd modules/openvino_code/server && ruff check . && black --check .`
- **Fix:** `ruff check --fix . && black .`

### C++ (nvidia_plugin, llama_cpp_plugin)
- **Tool:** clang-format (version 9-12)
- **Config:** `.clang-format` (BasedOnStyle: Google, IndentWidth: 4, ColumnLimit: 120)
- **NVIDIA check:** `cd modules/nvidia_plugin && ./utils/check.sh` (git diff-based)
- **NVIDIA fix:** `cd modules/nvidia_plugin && ./utils/format.sh`

### Java (java_api)
- **Tool:** google-java-format
- **Run:** `google-java-format --set-exit-if-changed -a -i modules/java_api/**/*.java`
- **Fix:** `google-java-format -a -i modules/java_api/**/*.java`
- **Note:** CI auto-commits fixes

## Testing Configuration

### ⚠️ IMPORTANT: All tests require OpenVINO to be built first

**Build OpenVINO with contrib modules:**
```bash
# Clone both repositories
git clone https://github.com/openvinotoolkit/openvino.git
git clone https://github.com/openvinotoolkit/openvino_contrib.git

# Configure
cmake -GNinja \
  -DCMAKE_BUILD_TYPE=Release \
  -DOPENVINO_EXTRA_MODULES=$(pwd)/openvino_contrib/modules \
  -DENABLE_PYTHON=ON \
  -DENABLE_TESTS=ON \
  -S openvino \
  -B build

# Build (takes hours)
cmake --build build --parallel

# Install
cmake -DCMAKE_INSTALL_PREFIX=/path/to/install -P build/cmake_install.cmake
```

### Java API Tests
- **Framework:** JUnit with Gradle
- **Location:** `modules/java_api/src/test/java/`
- **Run:** `cd modules/java_api && source <install_dir>/setupvars.sh && gradle test -Prun_tests -DMODELS_PATH=/path/to/testdata -Ddevice=CPU`
- **Requires:** OpenVINO build, testdata repository, Java 11+, Gradle 7.1.1

### Custom Operations Tests
- **Framework:** pytest
- **Location:** `modules/custom_operations/tests/run_tests.py`
- **Run:** `CUSTOM_OP_LIB=/path/to/libuser_ov_extensions.so python -m pytest modules/custom_operations/tests/run_tests.py -k "not sparse_conv"`
- **Requires:** OpenVINO build, custom operations library built, pytest, torch, onnx

### Token Merging Tests
- **Framework:** pytest with unittest
- **Location:** `modules/token_merging/tests/test_precommit.py`
- **Run:** `pip install modules/token_merging/[tests] && python -m pytest modules/token_merging/tests/`
- **Requires:** Full OpenVINO installation with runtime module, torch, diffusers, optimum-intel, open-clip-torch, timm

### NVIDIA Plugin Tests
- **Framework:** gtest (C++)
- **Location:** `modules/nvidia_plugin/tests/`
- **Run:** `ov_nvidia_func_tests --gtest_filter=*smoke*:-*dynamic* && ov_nvidia_unit_tests`
- **Requires:** CUDA 11.8+, cuDNN 8.9.4+, full OpenVINO + NVIDIA plugin build, NVIDIA GPU hardware

### Llama CPP Plugin Tests
- **Framework:** gtest (C++)
- **Run:** `llama_cpp_func_tests && llama_cpp_e2e_tests`
- **Requires:** Full OpenVINO build with llama_cpp_plugin, GGUF model files, libtbb2

## Conventions

**Test file patterns:**
- Python: `test_*.py`, `tests/run_tests.py`
- C++: `*_test.cpp`, `*_tests.cpp`
- Java: `**/*Test.java`

**Test naming:**
- Python: `test_*` functions, `unittest.TestCase` classes
- C++: gtest `TEST()` macros
- Java: JUnit `@Test` annotations

**Module structure:**
Each module is independent with its own:
- README.md
- CMakeLists.txt (C++ modules)
- setup.py or pyproject.toml (Python modules)
- package.json (TypeScript modules)
- build.gradle (Java modules)

## Gaps & Caveats

### Critical Limitations

1. **No standalone testing** — Repository requires main OpenVINO to be cloned and built (multi-hour process)
2. **Hardware dependencies** — NVIDIA plugin requires CUDA GPUs
3. **Complex dependency chain** — Tests need OpenVINO runtime, compiled libraries, test data
4. **No unified test command** — Each module has completely different test infrastructure
5. **Build time** — Full build takes 2-4 hours on 16-core machines

### Code Quality Issues

- **Black formatting violations:** openvino_code/server has 3 files that fail `black --check`
  - main.py
  - src/app.py
  - src/generators.py
- These are existing violations in the repository, not configuration issues

### Testing Gaps

- No unit tests for openvino_code TypeScript extension (only linting)
- Token merging tests require downloading large models from HuggingFace
- Custom operations tests are slow due to ONNX export/inference
- Java tests require external testdata repository

### CI Limitations

- NVIDIA plugin tests run on custom runners (not accessible to external contributors)
- Some tests are marked as skipped or disabled (see gtest_filter patterns)
- No coverage reporting configured

## Recommendations for Downstream Agents

### What CAN be validated automatically:
1. ✅ TypeScript/JavaScript linting for openvino_code
2. ✅ Python linting with ruff for openvino_code/server
3. ⚠️ Python formatting with black (will fail on existing code)

### What CANNOT be validated without full build:
1. ❌ All test suites (Java, Python, C++)
2. ❌ Build validation
3. ❌ Runtime behavior

### Validation Strategy:
For patch validation, an agent should:
1. Run applicable linters based on changed files:
   - `*.ts`, `*.tsx` → `npm run lint:all` in openvino_code
   - `*.py` in openvino_code/server → `ruff check` (black will fail on existing code)
   - `*.java` → google-java-format
   - `*.cpp`, `*.hpp`, `*.cu`, `*.cuh` in nvidia_plugin → `./utils/check.sh`
2. For test validation, defer to CI workflows — building OpenVINO locally is not practical
3. Focus validation on linting and static analysis
4. Flag any changes that would require CI testing

### Patch Application Workflow:
```bash
# 1. Clone repository
git clone https://github.com/opendatahub-io/openvino_contrib.git
cd openvino_contrib

# 2. Apply patch
git apply patch.diff

# 3. Determine affected modules
CHANGED_FILES=$(git diff --name-only HEAD)

# 4. Run module-specific linting
if echo "$CHANGED_FILES" | grep -q "modules/openvino_code/.*\\.ts"; then
  cd modules/openvino_code
  npm ci
  npm run lint:all
fi

if echo "$CHANGED_FILES" | grep -q "modules/openvino_code/server/.*\\.py"; then
  pip install ruff
  cd modules/openvino_code/server
  ruff check .
  # Note: skip black --check since it fails on existing code
fi

if echo "$CHANGED_FILES" | grep -q "modules/java_api/.*\\.java"; then
  # Requires google-java-format installation
  google-java-format --set-exit-if-changed -a -i modules/java_api/**/*.java
fi

# 5. Testing requires full OpenVINO build - not practical for automated validation
echo "⚠️ Tests require full OpenVINO build. Review CI results."
```

### Cost/Benefit Analysis:
- **Low effort, high value:** Linting validation (minutes)
- **High effort, medium value:** Java/openvino_code tests (requires setup but possible)
- **Very high effort, low value:** Full integration tests (hours of build time, better done in CI)
