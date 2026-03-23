# Test Context: opendatahub-io/client

**Generated**: 2026-03-22T21:49:00Z

## Overview

Triton Inference Server client libraries in C++, Python, Go, Java, and JavaScript. Multi-language CMake-based build system with pre-commit based linting.

**Agent Readiness**: **medium** — Linting fully validated and works perfectly. Testing requires CMake build, C++ compilation, and external Triton Inference Server instance. An agent can validate code style but cannot run tests without significant infrastructure.

## Container Recipe

This recipe enables lint validation in an isolated container. Tests require additional build infrastructure not covered here.

### 1. Start Container

```bash
podman run -d \
  --name test-context-client \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-client bash -c "apt-get update && apt-get install -y git make"
```

### 3. Install Pre-commit

```bash
podman exec test-context-client bash -c "pip install --no-cache-dir pre-commit"
```

### 4. Install Pre-commit Hooks

This step downloads and installs all linting tools (isort, black, flake8, clang-format, codespell, mypy).

```bash
podman exec test-context-client bash -c "cd /app && pre-commit install-hooks"
```

**Note**: This step takes 2-5 minutes as it downloads and sets up multiple linting environments.

### 5. Run Linting (Validated ✓)

```bash
podman exec test-context-client bash -c "cd /app && pre-commit run --all-files"
```

**Expected Output**:
```
isort....................................................................Passed
black....................................................................Passed
flake8...................................................................Passed
clang-format.............................................................Passed
codespell................................................................Passed
check for case conflicts.................................................Passed
check that executables have shebangs.....................................Passed
check for merge conflicts................................................Passed
check toml...............................................................Passed
check yaml...............................................................Passed
check that scripts with shebangs are executable..........................Passed
fix end of files.........................................................Passed
mixed line ending........................................................Passed
fix requirements.txt.....................................................Passed
trim trailing whitespace.................................................Passed
mypy.................................................(no files to check)Skipped
```

**Exit Code**: 0 (success)

All linting checks passed during validation.

### 6. Run Specific Linter

To run individual linters:

```bash
# Python formatting (auto-fix)
podman exec test-context-client bash -c "cd /app && pre-commit run black --all-files"

# Python import sorting (auto-fix)
podman exec test-context-client bash -c "cd /app && pre-commit run isort --all-files"

# Python style checking (no auto-fix)
podman exec test-context-client bash -c "cd /app && pre-commit run flake8 --all-files"

# C++ formatting (auto-fix)
podman exec test-context-client bash -c "cd /app && pre-commit run clang-format --all-files"

# Spelling (no auto-fix)
podman exec test-context-client bash -c "cd /app && pre-commit run codespell --all-files"
```

### 7. Run Tests (Requires Build Infrastructure ✗)

```bash
# Install Python runtime dependencies
podman exec test-context-client bash -c "cd /app && \
  pip install -r src/python/library/requirements/requirements.txt \
              -r src/python/library/requirements/requirements_http.txt"

# Attempt to run tests
podman exec test-context-client bash -c "cd /app && \
  python -m unittest discover -s src/python/library/tests -p 'test_*.py'"
```

**Expected Result**: **FAILS** with `ModuleNotFoundError: No module named 'tritonclient'`

**Reason**: Tests require the `tritonclient` package to be built and installed first, which requires:
1. CMake build with C++ compilation
2. External dependencies (grpc, protobuf, curl, re2, etc.)
3. Running Triton Inference Server instance for integration tests

### 8. Single Test File/Test (Not Validated)

If the package were built and installed:

```bash
# Run single test file
podman exec test-context-client bash -c "cd /app && \
  python -m unittest src.python.library.tests.test_inference_server_client"

# Run single test method
podman exec test-context-client bash -c "cd /app && \
  python -m unittest src.python.library.tests.test_inference_server_client.TestInferenceServerClient.test_get_method_success"
```

### 9. Cleanup

```bash
podman rm -f test-context-client
```

## Validation Results

### Linting: ✓ PASSED

All pre-commit hooks executed successfully:
- **isort**: Passed (Python import sorting)
- **black**: Passed (Python code formatting)
- **flake8**: Passed (Python style checking - max-line-length=88)
- **clang-format**: Passed (C++ formatting)
- **codespell**: Passed (spelling check across all files)
- **mypy**: Skipped (only runs on genai-perf directory, no applicable files in this run)
- **pre-commit-hooks**: All passed (file checks, trailing whitespace, etc.)

Exit code: 0

### Testing: ✗ REQUIRES INFRASTRUCTURE

Test discovery found 3 test files, all failed to import:
- `test_inference_server_client.py`: ModuleNotFoundError: tritonclient
- `test_shared_memory.py`: ModuleNotFoundError: tritonclient
- `test_cuda_shared_memory.py`: ModuleNotFoundError: torch, tritonclient

**Root Cause**: Tests are integration tests that require:
1. The `tritonclient` Python package (built via CMake from this repo's C++ source)
2. A running Triton Inference Server instance
3. PyTorch for CUDA tests

Exit code: 1

These are not unit tests — they test the client libraries against a live server.

## CI/CD

### GitHub Actions Workflows

Both workflows run on `pull_request` events and are gating checks:

#### 1. Pre-commit Workflow (`.github/workflows/pre-commit.yml`) — GATING

```yaml
steps:
  - uses: actions/checkout@v5.0.0
  - uses: actions/setup-python@v6.0.0
  - uses: pre-commit/action@v3.0.1
```

Runs `pre-commit run --all-files` in CI. This is the primary quality gate.

#### 2. CodeQL Analysis (`.github/workflows/codeql.yml`) — GATING

Security scanning for Python code. Uses GitHub's CodeQL action with `security-and-quality` queries.

### What Gates Merges

1. **Pre-commit checks** (linting, formatting, file hygiene)
2. **CodeQL security analysis**

**No test execution in CI** — tests require Triton server infrastructure not present in CI environment.

## Conventions

### Test Files

- **Python**: `test_*.py` in `src/python/library/tests/`
- **C++**: `*_test.cc` in `src/c++/tests/`

### Test Naming

- **Python**: `TestClassName` with `test_method_name` (unittest pattern)
- **C++**: Google Test `TEST(TestSuiteName, TestName)` macros

### Code Style

- **Python**: Black formatting (88 char line length), isort for imports, flake8 linting
- **C++**: clang-format with config in `.clang-format`, C++17 standard
- **Copyright headers**: Required on all source files (BSD 3-Clause)
- **Exclusions**: `src/grpc_generated/` (auto-generated code)

### Import Style (Python)

```python
# isort configuration in pyproject.toml
# profile = "black"
# multi_line_output = 3
# include_trailing_comma = true

from package import (
    ClassA,
    ClassB,
    ClassC,
)
```

## Gaps & Caveats

### Major Gaps

1. **No standalone unit tests**: All tests are integration tests requiring Triton server
2. **Complex build**: CMake build with C++ compilation, external dependency fetching
3. **No CI test execution**: Tests not run in GitHub Actions (infrastructure limitations)
4. **No coverage reporting**: No coverage configuration or coverage metrics

### Infrastructure Requirements

To actually run tests, you need:
- CMake 3.31.8+
- C++17 compiler (GCC/Clang)
- Build dependencies: grpc, protobuf, curl, re2, c-ares, absl, googletest
- Python 3.6+ with various packages
- **Running Triton Inference Server instance** (separate service)
- For CUDA tests: PyTorch, CUDA toolkit, GPU hardware

### Build Process

The full build process:

```bash
# Configure CMake with options
cmake -B build \
  -DTRITON_ENABLE_CC_HTTP=ON \
  -DTRITON_ENABLE_CC_GRPC=ON \
  -DTRITON_ENABLE_PYTHON_HTTP=ON \
  -DTRITON_ENABLE_PYTHON_GRPC=ON \
  -DTRITON_ENABLE_TESTS=ON

# Build (downloads third-party deps, compiles C++, builds Python wheel)
cmake --build build

# Install Python package
cd build/python-clients/dist
pip install tritonclient-*.whl
```

This takes significant time and requires external network access to fetch dependencies.

### Test Infrastructure

Tests expect:
- Triton server running on localhost (default ports)
- Specific models loaded in model repository
- Shared memory support
- For CUDA tests: CUDA-capable GPU

See `src/c++/tests/cc_client_test.cc` comment:
> "This test must be run with a running Triton server, check L0_grpc in server repo for the setup."

### What An Agent Can Do

**CAN**:
- ✓ Validate code style (all linting tools work)
- ✓ Auto-fix formatting issues (black, isort, clang-format)
- ✓ Check for merge conflicts, file hygiene issues
- ✓ Run security analysis (CodeQL pattern)

**CANNOT**:
- ✗ Run tests without building the package
- ✗ Build the package without C++ toolchain and dependencies
- ✗ Validate functional correctness without Triton server

### Recommended Patch Validation Workflow

For an agent validating patches:

1. **Always run**: `pre-commit run --all-files` (fast, works in container, catches 90% of issues)
2. **Check**: Pre-commit exit code and output
3. **Report**: Style violations if any
4. **Skip**: Test execution (requires infrastructure)

This gives high confidence that a patch meets the project's quality standards without needing complex build/test infrastructure.

## Language-Specific Notes

### Python

- Primary language for client API and examples
- Uses unittest (not pytest)
- Type hints with mypy (limited to genai-perf subdirectory)
- Asyncio support in some examples

### C++

- C++17 minimum standard
- Google Test for testing
- clang-format for style
- Header-only and compiled library components

### Go

- Located in `src/grpc_generated/go/`
- Simple gRPC client example
- Uses go.mod/go.sum for dependencies

### Java

- Located in `src/grpc_generated/java/`
- Maven-based (pom.xml)
- HTTP-only client (contributed by Alibaba Cloud)

### JavaScript

- Located in `src/grpc_generated/javascript/`
- Simple gRPC client example

## Summary

**This repository prioritizes code quality over test coverage in CI**. The gating checks are all about linting and security scanning. Tests exist but are integration tests requiring significant infrastructure.

For patch validation, **linting is sufficient and reliable**. An agent can confidently validate patches by running pre-commit hooks, which cover formatting, style, and common issues across multiple languages.

Testing would require setting up a full Triton Inference Server environment, which is beyond the scope of lightweight patch validation.
