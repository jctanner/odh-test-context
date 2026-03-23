# MLServer Test Context - Validation Runbook

## Overview

**Repository**: opendatahub-io/MLServer
**Language**: Python (3.9-3.12)
**Build System**: Poetry 2.1.1
**Test Framework**: pytest with tox
**Agent Readiness**: **HIGH** - Lint and test commands validated successfully. An agent can clone, patch, lint, and test with clear pass/fail signals.

This repository provides a production-ready ML model serving framework with comprehensive linting and testing infrastructure. All core validation commands work in a standard Python 3.12 container.

---

## Container Recipe

This section provides a **complete, copy-paste recipe** for validating patches in a container.

### 1. Start Container

```bash
podman run -d \
  --name test-context-mlserver \
  -v /path/to/MLServer:/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

Replace `/path/to/MLServer` with the actual repository path.

### 2. Install System Dependencies

```bash
podman exec test-context-mlserver bash -c "apt-get update && apt-get install -y make git"
```

Note: The python:3.12 base image already includes make and git, so this step typically completes instantly.

### 3. Install Poetry

```bash
podman exec test-context-mlserver bash -c "pip install --no-cache-dir poetry==2.1.1"
```

**Expected outcome**: Poetry 2.1.1 installed (takes ~30 seconds).

### 4. Install Development Dependencies

```bash
podman exec test-context-mlserver bash -c "cd /app && poetry install --sync --only dev"
```

**Expected outcome**: Installs black, flake8, mypy, pytest, and other dev tools (takes ~2-3 minutes).

### 5. Install Project Dependencies

```bash
podman exec test-context-mlserver bash -c "cd /app && poetry install --sync --no-root"
```

**Expected outcome**: Installs all runtime dependencies including FastAPI, gRPC, TensorFlow, etc. (takes ~3-5 minutes).

### 6. Run Linters

**Black (code formatter check):**
```bash
podman exec test-context-mlserver bash -c "cd /app && poetry run black --check ."
```

**Validation status**: ✅ **PASSED** (359 files checked, all formatted correctly)
**Expected output**: `All done! ✨ 🍰 ✨ 359 files would be left unchanged.`

**Flake8 (style checker):**
```bash
podman exec test-context-mlserver bash -c "cd /app && poetry run flake8 ."
```

**Validation status**: ✅ **PASSED** (no style violations)
**Expected output**: (no output = clean)

**Mypy (type checker):**
```bash
podman exec test-context-mlserver bash -c "cd /app && poetry run mypy ./mlserver"
```

**Validation status**: ✅ **PASSED** (101 source files, no type errors)
**Expected output**: `Success: no issues found in 101 source files`

### 7. Run Tests

**Run all tests (full suite):**
```bash
podman exec test-context-mlserver bash -c "cd /app && poetry run python -m pytest tests/ -n auto"
```

**Run single test file:**
```bash
podman exec test-context-mlserver bash -c "cd /app && poetry run python -m pytest tests/test_types.py -v"
```

**Validation status**: ✅ **PASSED** (7 tests in sample file)
**Expected output**: `======================== 7 passed, 42 warnings in 0.02s ========================`

**Run single test:**
```bash
podman exec test-context-mlserver bash -c "cd /app && poetry run python -m pytest tests/test_types.py::test_tensor_data -v"
```

**Run with tox (ODH environment - recommended for CI parity):**
```bash
podman exec test-context-mlserver bash -c "cd /app && poetry run tox run -e odh-mlserver"
```

**Note**: This runs the full OpenDataHub test suite, which may take 10-15 minutes. For quick validation, use pytest directly.

### 8. Cleanup

```bash
podman rm -f test-context-mlserver
```

---

## Validation Results

All commands were validated in a live container on 2026-03-22:

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Poetry Install | `pip install poetry==2.1.1` | ✅ PASS | Installed successfully |
| Dev Dependencies | `poetry install --sync --only dev` | ✅ PASS | ~60 packages installed |
| Project Dependencies | `poetry install --sync --no-root` | ✅ PASS | Full stack installed |
| Black Lint | `poetry run black --check .` | ✅ PASS | 359 files, all formatted |
| Flake8 Lint | `poetry run flake8 .` | ✅ PASS | No violations |
| Mypy Type Check | `poetry run mypy ./mlserver` | ✅ PASS | 101 files, no errors |
| Pytest | `poetry run pytest tests/test_types.py -v` | ✅ PASS | 7 tests passed |

**Summary**: ✅ All core validation commands work. An agent can reliably lint and test patches.

---

## CI/CD

### GitHub Actions (Primary CI)

**Trigger**: Pull requests and pushes to `master`, `release-*`, `rhoai-staging` branches.

**Gating Checks** (required for merge):

1. **Code Generation Check**:
   ```bash
   make generate-dataplane
   make generate-model-repository
   make lint-no-changes
   ```
   Ensures generated gRPC/protobuf code is up-to-date.

2. **Lint Check** (runs on Python 3.9, 3.10, 3.11, 3.12):
   ```bash
   poetry install --sync --only dev
   make lint
   ```
   Runs black, flake8, and mypy across all supported Python versions.

3. **Core Tests** (test-mlserver job):
   ```bash
   poetry install --only test
   poetry run tox -e odh-mlserver
   ```
   Tests MLServer core without optional runtimes. Runs on Ubuntu 24.04 and MacOS.

4. **Runtime Tests** (test-runtimes job):
   ```bash
   poetry run tox -c ./runtimes/{sklearn,xgboost,lightgbm,onnx}
   ```
   Tests each ML runtime individually on Python 3.9-3.12.

**Advisory Checks** (run on push, not required for PRs):

- `test-all-runtimes`: Full integration test with all runtimes installed together
- `licenses`: Checks dependency licenses with pip-licenses

### Tekton Pipelines (OpenShift/OpenDataHub CI)

**Config**: `.tekton/mlserver-pull-request.yaml`

**Trigger**: Pull requests to `master`

**Actions**:
- Multi-arch container build (uses `odh-konflux-central` pipeline)
- Builds with runtimes: lightgbm, onnx, sklearn, xgboost
- Publishes to `quay.io/opendatahub/mlserver:odh-pr-{revision}`

**Note**: Tekton focuses on container builds; test validation happens in GitHub Actions.

---

## Conventions

### Test File Naming
- Pattern: `tests/**/*.py` with `test_*.py` naming
- Structure: Organized by feature (batching, codecs, grpc, kafka, metrics, parallel, rest)

### Test Function Naming
- Functions: `test_*` prefix
- Classes: `Test*` prefix
- Async tests: Decorated with pytest async fixtures

### Import Style
- Uses `--import-mode=importlib` (configured in pyproject.toml)
- Absolute imports preferred

### Test Organization
Tests are split into categories due to flakiness when run in parallel:
- **Parallel-safe**: Most tests run with `-n auto`
- **Serial**: metrics, kafka, parallel, grpc, env, cli (run separately)

### Docker Requirements
Some tests require Docker daemon access for integration testing (Kafka, model loading, etc.).

---

## Gaps & Caveats

### Known Gaps

1. **Runtime Coverage**: Only core MLServer tested in validation. Runtime-specific tests (sklearn, xgboost, etc.) require additional ML library dependencies.

2. **Docker Integration**: Tests requiring Docker (Kafka integration, environment tests) not validated without Docker socket access.

3. **Flaky Tests**: CI configuration notes that kafka, parallel, grpc, env, and cli tests are flaky when run in parallel with the full suite. These are run separately in CI.

4. **Coverage Enforcement**: No coverage threshold configured. Coverage collection not enforced in CI.

5. **Conda Support**: `USE_CONDA` environment variable used in some tests; not validated in container environment.

6. **Excluded Runtimes**: ODH builds exclude mlflow, huggingface, and alibi-explain/detect runtimes per `odh-all-runtimes` tox environment.

### Special Requirements

- **MacOS**: Requires OpenMP library (`brew install libomp`)
- **Large Test Suite**: `test-all-runtimes` requires significant disk space (uses maximize-build-space action in CI)
- **Python Version Matrix**: Full CI runs on Python 3.9, 3.10, 3.11, 3.12

### Environment Variables

Required for tests:
```bash
GITHUB_SERVER_URL=https://github.com
GITHUB_REPOSITORY=opendatahub-io/MLServer
GITHUB_REF=refs/heads/master
USE_CONDA=false
DOCKER_HOST=<passthrough for Docker tests>
```

### Time Estimates

- Lint (all tools): ~1-2 minutes
- Core tests (pytest only): ~5-10 minutes
- Full tox suite (odh-mlserver): ~10-15 minutes
- All runtimes integration: ~20-30 minutes

---

## Quick Reference

### Makefile Targets

```bash
make install-dev    # Install all dependencies including runtimes
make lint           # Run black, flake8, mypy on all code
make test           # Run full tox test suite
make fmt            # Auto-format code with black
make generate       # Regenerate gRPC/protobuf code
make clean          # Remove build artifacts
```

### Tox Environments

```bash
tox run -e py3              # Basic pytest run
tox run -e mlserver         # MLServer core tests
tox run -e odh-mlserver     # OpenDataHub MLServer (no conda)
tox run -e odh-all-runtimes # ODH with core runtimes
tox run -e licenses         # Generate license report
```

### Pytest Patterns

```bash
# Run all tests in parallel
pytest tests/ -n auto

# Run single file
pytest tests/test_types.py -v

# Run single test
pytest tests/test_types.py::test_tensor_data -v

# Run with keyword filter
pytest -k "grpc" tests/

# Show print statements
pytest tests/test_types.py -v -s
```

---

## Conclusion

**Agent Readiness: HIGH**

This repository has excellent test infrastructure. An agent can:
- ✅ Clone and install dependencies reliably
- ✅ Run linters (black, flake8, mypy) with clear pass/fail
- ✅ Run tests (pytest) with good isolation
- ✅ Validate patches using the same commands as CI

**Recommended Validation Flow for Agents**:
1. Apply patch
2. Run `poetry run black --check .` (fast, catches formatting)
3. Run `poetry run flake8 .` (fast, catches style issues)
4. Run `poetry run mypy ./mlserver` (medium, catches type errors)
5. Run `poetry run pytest tests/ -n auto` (slower, validates functionality)

Total validation time: ~10-15 minutes for full suite, ~2-3 minutes for lint-only.
