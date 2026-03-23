# Test Context: modelcar-base-image

**Agent Readiness**: MEDIUM — Tests work and validate successfully, but no linting configured and Go code has no tests.

**Languages**: Go 1.22, Python 3.9+
**Build System**: Multi-stage Containerfile (Go), uv + make (Python)
**Test Framework**: pytest (Python only)

---

## Container Recipe

This is the **complete, copy-paste recipe** for validating patches in a container. An agent should be able to follow these steps verbatim without additional discovery.

### 1. Start Container

Use Python 3.9 as the base (minimum version from `requires-python = ">=3.9"` in pyproject.toml):

```bash
podman run -d --name test-context-modelcar-base-image \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.9 \
  sleep infinity
```

Or with Docker:

```bash
docker run -d --name test-context-modelcar-base-image \
  -v $(pwd):/app \
  -w /app \
  python:3.9 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-modelcar-base-image bash -c \
  "apt-get update && apt-get install -y make git curl"
```

### 3. Install UV Package Manager

```bash
podman exec test-context-modelcar-base-image bash -c \
  "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

This installs uv to `/root/.local/bin/`. All subsequent commands must include this in PATH.

### 4. Install Python Dependencies

```bash
podman exec test-context-modelcar-base-image bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python && uv sync --all-extras"
```

**Expected output**:
- Resolves 12 packages
- Installs 9 packages (pytest, pluggy, iniconfig, packaging, etc.)
- Creates virtual environment at `.venv`
- May warn about hardlink degraded performance (cosmetic, can be ignored)

**Exit code**: 0 (success)

### 5. Run All Tests

```bash
podman exec test-context-modelcar-base-image bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python && uv run pytest -x -s -v"
```

**Expected output**:
```
============================= test session starts ==============================
platform linux -- Python 3.9.25, pytest-8.4.2, pluggy-1.6.0
collected 3 items

tests/embedded_oci_layout_test.py::test_check_embedded_oci_layout PASSED
tests/test_constants.py::test_odh_modelcar_base_image_constant PASSED
tests/test_constants.py::test_embedded_oci_layout_dir_constant PASSED

============================== 3 passed in 0.02s
```

**Exit code**: 0 (success)

### 6. Run a Single Test File

Template:

```bash
podman exec test-context-modelcar-base-image bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python && uv run pytest {file} -v"
```

Example:

```bash
podman exec test-context-modelcar-base-image bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python && uv run pytest tests/test_constants.py -v"
```

**Expected**: 2 tests collected, 2 passed

### 7. Run a Single Test Function

Template:

```bash
podman exec test-context-modelcar-base-image bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python && uv run pytest {file}::{test_name} -v"
```

Example:

```bash
podman exec test-context-modelcar-base-image bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app/python && uv run pytest tests/test_constants.py::test_odh_modelcar_base_image_constant -v"
```

**Expected**: 1 test collected, 1 passed

### 8. Linting

**No linting configured**. No ruff, flake8, pylint, or golangci-lint configurations found.

### 9. Cleanup

Always clean up the container when done:

```bash
podman rm -f test-context-modelcar-base-image
```

---

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install UV | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | ✅ PASS | UV 0.10.12 installed to /root/.local/bin |
| Install Deps | `uv sync --all-extras` | ✅ PASS | 9 packages installed, hardlink warning is cosmetic |
| Run Tests | `uv run pytest -x -s -v` | ✅ PASS | 3/3 tests passed in 0.02s |
| Single File | `uv run pytest tests/test_constants.py -v` | ✅ PASS | 2/2 tests passed |
| Single Test | `uv run pytest tests/test_constants.py::test_odh_modelcar_base_image_constant -v` | ✅ PASS | 1/1 test passed |
| Build | `make build` | ❌ FAIL | Requires 'skopeo' (not needed for validation) |

**Summary**: Install and test commands validated successfully. Build fails due to missing skopeo tool, but this is not required for patch validation (only for publishing Python packages).

---

## CI/CD

### Gating Checks (Required for Merge)

All checks run on `pull_request` trigger:

#### 1. Container Build (build.yaml)

```bash
docker build -f Containerfile -t modelcar-base-image .
```

Builds multi-arch (amd64, arm64) container image using buildah. Uses multi-stage build with ubi8/go-toolset:1.22 to compile Go binary.

#### 2. E2E Python Tests (e2e.yaml - e2e-python job)

```bash
cd python
make sync test
```

Equivalent to:
```bash
uv sync --all-extras
uv run pytest -x -s -v
```

Runs 3 pytest tests in `python/tests/`.

#### 3. E2E KServe Integration (e2e.yaml - e2e-kserve job)

Full KServe deployment with:
- Kind cluster
- cert-manager
- KServe 0.14.0
- Custom InferenceService with ModelCar

**Cannot be validated in isolated container** — requires Kubernetes cluster.

### Advisory Checks (Non-gating)

- **publish.yaml**: Publishes container to quay.io on push to main (not gating)
- **publish-python.yaml**: Publishes Python package to PyPI on tags (not gating)

---

## Conventions

### Test Files

**Location**: `python/tests/`

**Naming**:
- Test files: `test_*.py` or `*_test.py`
- Test functions: `test_*`
- Test classes: `Test*`

**Current tests**:
- `tests/test_constants.py` — Tests package constants (ODH_MODELCAR_BASE_IMAGE, EMBEDDED_OCI_LAYOUT_DIR)
- `tests/embedded_oci_layout_test.py` — Tests embedded OCI layout copying and validation

### Import Style

Absolute imports from `modelcar_base_image` package:

```python
from modelcar_base_image.embedded_oci_layout import embedded_oci_layout
from modelcar_base_image.constants import EMBEDDED_OCI_LAYOUT_DIR
```

### Go Code

Single Go file (`link-model-and-wait.go`) with no external dependencies beyond stdlib. Creates symbolic links for KServe ModelCar sidecar pattern. **No Go tests exist** (no `*_test.go` files).

---

## Gaps & Caveats

### No Linting

No linter configurations found. No `.golangci.yml`, `.flake8`, `ruff` config in `pyproject.toml`, or other linting tools. CI workflows do not run linting checks.

**Impact**: An agent can run tests but cannot validate code quality/style.

### Go Has No Tests

The Go code (`link-model-and-wait.go`) has no unit tests. The only validation is through E2E tests where it's built into a container and deployed to KServe.

**Impact**: Cannot validate Go patches through unit tests, only through container build.

### Build Requires Skopeo

The Python package build process (`make build`) requires the `skopeo` tool to copy the base container image into an OCI layout. This tool is not available in standard Python containers.

**Impact**: Full build cannot be validated in isolated containers. However, this is not a gating check for PRs — the CI handles builds separately. Test validation works without skopeo.

### E2E Tests Need Kubernetes

The full E2E test suite (e2e-kserve job) deploys KServe to a Kind cluster and requires:
- kubectl
- Kind cluster
- cert-manager
- KServe manifests

**Impact**: Cannot validate full E2E tests in isolated containers. Only Python unit tests can be validated.

### No Coverage Measurement

No coverage thresholds or coverage reporting configured in pytest or CI.

---

## Project Structure

```
modelcar-base-image/
├── Containerfile              # Multi-stage Go build (scratch base)
├── link-model-and-wait.go    # Go sidecar for ModelCar (no tests)
├── go.mod                    # Go 1.22
├── python/
│   ├── pyproject.toml        # Python >=3.9, pytest config
│   ├── Makefile              # Targets: sync, test, build, clean
│   ├── src/modelcar_base_image/
│   │   ├── constants.py
│   │   ├── embedded_oci_layout.py
│   │   └── prepare.py        # Requires skopeo
│   └── tests/
│       ├── test_constants.py
│       └── embedded_oci_layout_test.py
├── .github/workflows/
│   ├── build.yaml            # Gating: container build
│   ├── e2e.yaml              # Gating: Python tests + KServe E2E
│   ├── publish.yaml          # Non-gating: publish container
│   └── publish-python.yaml   # Non-gating: publish to PyPI
└── e2e/                      # E2E test manifests for KServe
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Install deps | `cd python && uv sync --all-extras` |
| Run all tests | `cd python && uv run pytest -x -s -v` |
| Run one file | `cd python && uv run pytest {file} -v` |
| Run one test | `cd python && uv run pytest {file}::{test} -v` |
| Build Go binary | `docker build -f Containerfile -t img .` |
| Build Python pkg | `cd python && make build` (requires skopeo) |

**CI truth**: The `e2e.yaml` workflow is authoritative. The e2e-python job runs `make sync test` in the python/ directory, which is the gating check for Python code changes.
