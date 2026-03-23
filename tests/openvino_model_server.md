# Test Context: openvino_model_server (opendatahub-io)

## Overview

**Repository**: opendatahub-io/openvino_model_server
**Languages**: C++, Python, JavaScript
**Build System**: Bazel (primary), Make (wrapper), Docker
**Agent Readiness**: **medium** — Linting validates successfully (style and security checks pass), but testing requires complex Docker-based infrastructure with Bazel build environment for C++ tests or Docker-in-Docker setup for Python integration tests.

This is an OpenVINO Model Server - a C++ inference server with Python client libraries. The codebase uses Bazel for C++ compilation and pytest for Python testing. Most validation must occur inside Docker containers due to complex dependencies.

## Container Recipe

### Quick Start: Lint-Only Validation

For code quality checks without full test execution:

**1. Start container:**
```bash
podman run -d --name test-ovms \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

**2. Install system dependencies:**
```bash
podman exec test-ovms bash -c "apt-get update && apt-get install -y make git protobuf-compiler"
```

**3. Install Python tooling:**
```bash
podman exec test-ovms bash -c "python3 -m pip install --upgrade pip virtualenv"
```

**4. Run style checks (validated ✓):**
```bash
podman exec test-ovms bash -c "cd /app && make style"
```

Expected: Exit code 0, output shows "Spelling check completed", cpplint processing files, clang-format checking, cppclean warnings count.

**5. Run SDL security checks (validated ✓):**
```bash
podman exec test-ovms bash -c "cd /app && make sdl-check"
```

Expected: Exit code 0, output shows hadolint scanning Dockerfiles, bandit checking Python code, license header verification, forbidden functions check.

**6. Cleanup:**
```bash
podman rm -f test-ovms
```

### Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install deps | `apt-get install make git protobuf-compiler && pip install virtualenv` | ✓ PASS | System packages and Python tools install cleanly |
| Style checks | `make style` | ✓ PASS | Runs cpplint, clang-format-check, cppclean, codespell - all pass |
| SDL checks | `make sdl-check` | ✓ PASS | Runs hadolint, bandit, license headers, forbidden functions - all pass |
| Client lib tests | `make test_client_lib` | ✗ FAIL | Requires NumPy compilation, fails in minimal container (exit code 2) |
| Functional tests | `pytest tests/functional/` | ✗ FAIL | Requires Docker-in-Docker, OVMS server, model files, system groups |

**Validated commands**: `make style` and `make sdl-check` both work and return meaningful results.

**Non-validated commands**: Testing commands cannot run without either:
- Full Docker build environment with Bazel for C++ tests
- Docker-in-Docker with OVMS server images and model files for Python integration tests

## CI/CD

### Gating Checks (Required for Merge)

The repository uses GitHub Actions with these required checks on `stable*` branches:

**1. Style Checks** (`.github/workflows/fast-checks.yml`)
```bash
make style
```
- Runs cpplint on C++ code (src/ directory)
- Runs clang-format check (verifies formatting is committed)
- Runs cppclean (checks unnecessary includes, forward declarations)
- Runs codespell (spell checking)
- **Validated**: ✓ Works in Python 3.11 container

**2. SDL Security Checks** (`.github/workflows/fast-checks.yml`)
```bash
make sdl-check
```
- Runs hadolint on Dockerfile.redhat and Dockerfile.ubuntu
- Runs bandit on Python code (demos, clients)
- Checks license headers in all files
- Checks for forbidden functions
- **Validated**: ✓ Works in Python 3.11 container

**3. Client Library Tests** (`.github/workflows/fast-checks.yml`)
```bash
make test_client_lib
```
- Only runs if `client/python/ovmsclient/lib/**` files changed
- Builds Python client library wheel
- Runs pytest on client library tests
- Runs flake8 style checks on client code
- **Validated**: ✗ Fails in minimal container (needs NumPy compilation, full build environment)

**4. Integration Tests** (`.github/workflows/integration-tests.yml`, `.github/workflows/integration-tests-konflux.yml`)
- Triggered by external CI systems (OpenShift CI, Konflux) after image build
- Pulls pre-built container images from Quay.io
- Runs functional tests against built images
- **Validated**: ✗ Requires Docker-in-Docker and pre-built OVMS images

### CI Workflow Details

Fast checks workflow runs on every PR to `stable*` branches:
```yaml
on:
  pull_request:
    branches:
      - 'stable*'
```

Setup:
- Uses `ubuntu-latest` runners
- Python 3.11
- Installs: protobuf-compiler
- Uses virtualenv for Python dependencies

## Build Configuration

### Docker Build (Primary Method)

```bash
make docker_build
```

This multi-stage process:
1. Creates builder image with Bazel and OpenVINO
2. Compiles C++ code with Bazel inside container
3. Runs unit tests (if `RUN_TESTS=1`)
4. Packages into release image

### Build Environment Variables

- `BASE_OS`: ubuntu22, ubuntu24, or redhat (default: ubuntu22)
- `RUN_TESTS`: Set to 1 to run C++ unit tests during build
- `CHECK_COVERAGE`: Set to 1 to generate coverage reports
- `RUN_GPU_TESTS`: Set to 1 to run GPU-specific tests
- `MEDIAPIPE_DISABLE`: Set to 1 to disable MediaPipe support
- `PYTHON_DISABLE`: Set to 1 to disable Python support
- `BAZEL_BUILD_TYPE`: opt or dbg (default: opt)
- `JOBS`: Number of parallel jobs (default: CPU cores)

### Bazel Build (Advanced)

Direct Bazel commands (requires Bazel environment):
```bash
# C++ unit tests
bazel test //src:ovms_test

# C++ unit tests with specific filter
bazel test --test_filter='TestName.*' //src:ovms_test

# Build main binary
bazel build //src:ovms
```

### Python Client Library Build

```bash
cd client/python/ovmsclient/lib
make build  # Creates wheel in dist/
make test   # Runs pytest on library tests
make style  # Runs flake8
```

## Testing

### Test Structure

**C++ Unit Tests** (src/test/):
- Framework: Google Test (gtest)
- Runner: Bazel
- Location: `src/test/*_test.cpp`
- Execution: Inside Docker via `run_unit_tests.sh` or `RUN_TESTS=1 make docker_build`

**Python Integration Tests** (tests/functional/):
- Framework: pytest
- Location: `tests/functional/test_*.py`
- Requirements: Running OVMS Docker container, model files, Docker access
- Fixtures: `tests/functional/conftest.py` sets up Docker containers

**Python Client Library Tests** (client/python/ovmsclient/lib/tests/):
- Framework: pytest
- Location: `tests/test_*.py`, `tfs_compat_*/test_*.py`
- Execution: `cd client/python/ovmsclient/lib && make test`

### Test Commands

**Style/Lint (works in minimal container)**:
```bash
make style      # C++ style + spelling
make sdl-check  # Security checks
```

**C++ Unit Tests (requires Docker build environment)**:
```bash
# Full build with tests
RUN_TESTS=1 make docker_build

# Inside Docker container
./run_unit_tests.sh

# Specific test with Bazel
bazel test --test_filter='ModelManagerTest.*' //src:ovms_test
```

**Python Integration Tests (requires Docker-in-Docker)**:
```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all functional tests (requires OVMS server running)
pytest tests/functional/ -v

# Run single test file
pytest tests/functional/test_batching.py -v

# Run single test
pytest tests/functional/test_batching.py::test_batch_size_auto -v
```

**Python Client Library Tests**:
```bash
cd client/python/ovmsclient/lib
make test  # Builds and tests client library
```

### Test Environment Variables

- `RUN_TESTS=1`: Enable tests in Docker build
- `CHECK_COVERAGE=1`: Enable coverage reporting
- `RUN_GPU_TESTS=1`: Enable GPU tests (requires GPU drivers)
- `TEST_PATH`: Path to functional tests (default: tests/functional/)

## Linting Tools & Configuration

### C++ Linting

**cpplint** (version 1.4.3):
```bash
# Part of make style
cpplint --extensions=hpp,cc,cpp,h \
  --output=vs7 \
  --recursive \
  --linelength=120 \
  --filter=-build/c++11,-runtime/references,... \
  src
```
Filters disabled: build/c++11, runtime/references, whitespace/braces, whitespace/indent, build/include_order, runtime/indentation_namespace, build/namespaces, whitespace/line_length, runtime/string, readability/casting, runtime/explicit, readability/todo

**clang-format** (version 6.0.1):
- Config: `.clang-format`
- Style: Based on LLVM with custom settings
- Key settings: ColumnLimit=0 (no limit), IndentWidth=4, SortIncludes=false
- Check: `make clang-format-check`
- Fix: `make clang-format`

**cppclean** (version >=0.13):
- Script: `ci/cppclean.sh`
- Checks: Unnecessary forward declarations, missing direct includes, unused code
- Thresholds: Enforces specific warning counts for src/ and test/ directories

### Python Linting

**flake8** (version 5.0.1):
```bash
cd client/python/ovmsclient/lib
flake8 ovmsclient tests/ --max-line-length=100 --count
```

**bandit** (Python security):
```bash
# Part of make sdl-check
bandit -r demos/*/python
bandit -r client/python/
```
Config: `client/python/.bandit`

### Other Checks

**codespell** (version 2.3.0):
```bash
# Spell checking
codespell --skip "spelling-whitelist.txt"
```
Whitelist: `spelling-whitelist.txt`

**hadolint** (Dockerfile linter):
```bash
# Part of make sdl-check
./tests/hadolint.sh
```
Scans: Dockerfile.redhat, Dockerfile.ubuntu

## Conventions

### File Naming

- C++ tests: `src/test/*_test.cpp`
- Python functional tests: `tests/functional/test_*.py`
- Python client tests: `*/tests/test_*.py`
- Build files: `BUILD`, `BUILD.bazel`

### Test Naming

- C++ tests: Google Test conventions (`TEST(SuiteName, TestName)`, `TEST_F(FixtureName, TestName)`)
- Python tests: pytest conventions (`test_*` functions, `Test*` classes)

### Code Style

- C++: LLVM-based style with modifications (see `.clang-format`)
- Line length: C++ no limit (ColumnLimit=0), Python 100 chars
- Indentation: 4 spaces
- Include ordering: Manual (SortIncludes disabled)

## Gaps & Caveats

### Known Limitations

1. **No standalone unit tests**: All C++ tests require full Bazel build environment with OpenVINO dependencies
2. **Docker-dependent testing**: Integration tests require Docker-in-Docker, running OVMS server, model files
3. **Complex test setup**: Functional tests have hard dependency on system groups (render, video), Docker daemon
4. **Client library tests fragile**: Require compilation of NumPy and other native extensions, fail in minimal containers
5. **Generated code style violations**: Protobuf-generated Python code doesn't pass flake8 checks
6. **Documentation gaps**: Test execution not well documented, requires reading CI workflows and Makefiles
7. **External CI dependency**: Integration tests triggered by external systems (OpenShift CI, Konflux)

### What Works

- ✓ **Style checks** (`make style`): cpplint, clang-format, cppclean, codespell all validate successfully
- ✓ **Security checks** (`make sdl-check`): hadolint, bandit, license headers, forbidden functions all work
- ✓ **Linting in CI**: Can reproduce all fast-checks workflow lint commands locally

### What Doesn't Work (Without Full Infrastructure)

- ✗ **C++ unit tests**: Require Docker build with Bazel, OpenVINO, all dependencies
- ✗ **Python functional tests**: Require Docker-in-Docker, OVMS server, model files, special system setup
- ✗ **Client library tests**: Require compilation environment for native Python packages
- ✗ **Integration tests**: Require pre-built images from external CI systems

### Recommended Agent Usage

For **patch validation**:
1. **Always run**: `make style` and `make sdl-check` — these validate reliably
2. **If C++ changes**: Note that full test validation requires Docker build (`RUN_TESTS=1 make docker_build`)
3. **If Python client changes**: Note that tests require `make test_client_lib` in build environment
4. **If functional test changes**: Note that tests require Docker-in-Docker and OVMS server

For **continuous validation**: Focus on style and security checks which are fast and reliable. Defer C++ unit tests and integration tests to CI infrastructure.

## Additional Resources

- **Main README**: `README.md` - Server overview and usage
- **CI Workflows**: `.github/workflows/*.yml` - Authoritative source for gating checks
- **Makefile**: `Makefile` - All build and test targets
- **Test Scripts**: `run_unit_tests.sh` - C++ unit test execution
- **Docker Files**: `Dockerfile.ubuntu`, `Dockerfile.redhat` - Build environments
- **Bazel Workspace**: `WORKSPACE`, `BUILD.bazel` - Build configuration

---

**Generated**: 2026-03-22
**Confidence**: High
**Agent Readiness**: Medium (linting works, testing requires infrastructure)
