# Test Context: base-containers (opendatahub-io)

**Generated:** 2026-03-22T21:35:00Z

## Overview

**Repository:** opendatahub-io/base-containers
**Languages:** Python, Containerfile
**Build System:** podman/docker + custom scripts
**Test Framework:** pytest
**Agent Readiness:** **MEDIUM** - Lint and type checks work perfectly in a standard Python container. Integration tests require building container images with podman, which needs significant disk space (~30GB for CUDA images) and resources.

This repository builds ODH midstream base container images (Python and CUDA variants). The codebase consists of Containerfile templates, build scripts, and pytest-based integration tests that validate built images.

---

## Container Recipe

This recipe allows an agent to validate Python code changes (tests/, scripts/) by running lint and type checks. Full integration tests require building container images first.

### 1. Start Container

```bash
podman run -d --name test-context-base-containers \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

**Note:** Use `docker` instead of `podman` if podman is not available. The `:Z` flag is for SELinux relabeling; omit on non-SELinux systems if needed.

### 2. Install System Dependencies

```bash
podman exec test-context-base-containers bash -c "apt-get update -qq && apt-get install -y wget"
```

### 3. Install Hadolint (for Containerfile linting)

```bash
podman exec test-context-base-containers bash -c "
  wget -qO /usr/local/bin/hadolint \
    https://github.com/hadolint/hadolint/releases/download/v2.14.0/hadolint-Linux-x86_64 && \
  chmod +x /usr/local/bin/hadolint
"
```

### 4. Install Python Dependencies

```bash
podman exec test-context-base-containers bash -c "cd /app && pip install -e '.[dev]'"
```

**Expected:** Installs pytest, ruff, mypy, tox and all dependencies. Exit code 0.

### 5. Run Linting (Validated ✓)

**Ruff check:**
```bash
podman exec test-context-base-containers bash -c "cd /app && ruff check tests/"
```
**Expected:** `All checks passed!` - Exit code 0

**Ruff format check:**
```bash
podman exec test-context-base-containers bash -c "cd /app && ruff format --check tests/"
```
**Expected:** `5 files already formatted` - Exit code 0

**Containerfile linting:**
```bash
podman exec test-context-base-containers bash -c "cd /app && ./scripts/lint-containerfile.sh"
```
**Expected:** All 7 Containerfiles pass linting - Exit code 0

**Alternative: Run all lint checks via tox:**
```bash
podman exec test-context-base-containers bash -c "cd /app && tox -e lint"
```
**Expected:** `lint: OK` - Exit code 0

### 6. Run Type Checking (Validated ✓)

```bash
podman exec test-context-base-containers bash -c "cd /app && mypy tests/"
```
**Expected:** `Success: no issues found in 5 source files` - Exit code 0

**Alternative: Via tox:**
```bash
podman exec test-context-base-containers bash -c "cd /app && tox -e type"
```
**Expected:** `type: OK` - Exit code 0

### 7. Run Tests (Requires Container Images)

**Without built images (tests will skip):**
```bash
podman exec test-context-base-containers bash -c "cd /app && pytest tests/ -v"
```
**Expected:** Tests skip with message: `PYTHON_IMAGE environment variable not set`

**To run tests with images:**

First, build an image (requires podman on host, not in container):
```bash
./scripts/build.sh python-3.12
```

Then run tests:
```bash
podman exec test-context-base-containers bash -c "
  cd /app && \
  PYTHON_IMAGE=localhost/odh-midstream-python-base:3.12 \
  PYTHON_VERSION=3.12 \
  pytest tests/test_python_image.py tests/test_common.py -v
"
```

**Expected:** Tests pass if image is correctly built.

### 8. Run Single Test File

```bash
podman exec test-context-base-containers bash -c "cd /app && pytest tests/test_python_image.py -v"
```

### 9. Run Single Test

```bash
podman exec test-context-base-containers bash -c "cd /app && pytest tests/test_python_image.py::test_accelerator_label_cpu -v"
```

### 10. Cleanup

```bash
podman rm -f test-context-base-containers
```

**Always clean up**, even if validation fails partway through.

---

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install | `pip install -e '.[dev]'` | ✓ PASS | All dependencies installed successfully |
| Lint | `ruff check tests/` | ✓ PASS | No linting violations |
| Lint | `ruff format --check tests/` | ✓ PASS | All files properly formatted |
| Lint | `./scripts/lint-containerfile.sh` | ✓ PASS | All 7 Containerfiles pass hadolint |
| Lint | `tox -e lint` | ✓ PASS | Combined lint checks (3.29s) |
| Type | `mypy tests/` | ✓ PASS | No type errors with strict config |
| Type | `tox -e type` | ✓ PASS | Type checking (6.05s) |
| Test | `pytest tests/ -v` | ⊘ SKIP | Requires PYTHON_IMAGE/CUDA_IMAGE env vars |

**Summary:** Lint and type checks are fully functional. Integration tests require pre-built container images.

---

## CI/CD

**System:** GitHub Actions + Tekton

**Gating Checks (all required for merge):**

1. **lint** - Runs ruff check and format validation on Python code
   ```bash
   ruff check tests/
   ruff format --check tests/
   ```

2. **type-check** - Runs mypy type checking
   ```bash
   mypy tests/
   ```

3. **lint-containerfiles** - Runs hadolint on all Containerfiles
   ```bash
   hadolint <containerfile> --config .hadolint.yaml
   ```

4. **test-python-image** - Builds and tests Python base images (matrix: 3.12)
   ```bash
   ./scripts/build.sh python-3.12
   pytest tests/test_python_image.py tests/test_common.py -v
   ```

5. **test-cuda-image** - Builds and tests CUDA base images (matrix: 12.8, 12.9, 13.0, 13.1)
   ```bash
   ./scripts/build.sh cuda-12.8
   pytest tests/test_cuda_image.py tests/test_common.py -v
   ```

6. **ci-status** - Aggregator job that ensures all checks pass

**CI Workflow:** `.github/workflows/ci.yml`

The CI uses intelligent path-based filtering to only build/test images affected by changes. Common file changes (scripts/, requirements-build.txt, test files) trigger all image builds. Changes to specific version directories only trigger those versions.

**CUDA builds require ~30GB disk space** - CI uses free-disk-space actions to clean up GitHub runner before building.

**Advisory Checks:**
- `check-cuda-versions` - Weekly scan for new NVIDIA CUDA releases (creates issues automatically)

---

## Conventions

**Test Files:** `test_*.py` in `tests/` directory

**Test Functions:** Named `test_*`, use pytest framework

**Import Style:** Absolute imports, sorted with isort (integrated in ruff)

**Type Hints:** Required in non-test code. Strict mypy configuration:
- `disallow_untyped_defs = true`
- `disallow_incomplete_defs = true`
- Tests have relaxed type requirements

**Test Patterns:**
- Tests use session-scoped fixtures (`python_container`, `cuda_container`)
- Containers start once per test session and are reused via `podman exec`
- Tests MUST be idempotent (read-only) - no state modification
- ContainerRunner helper class in `conftest.py` provides utilities

**Linting Configuration:**
- Ruff: Python 3.12 target, 100 char line length, strict rules (security, bugbear, comprehensions, pylint)
- Hadolint: ODH-specific label requirements, trusted registries configured
- Ignores: Template files use ARG for flexibility, intentional layer caching patterns

---

## Gaps & Caveats

**Integration Tests Require Infrastructure:**
- Tests need pre-built container images (PYTHON_IMAGE, CUDA_IMAGE env vars)
- Building images requires podman/docker on the host
- CUDA images require ~30GB disk space and significant build time
- Tests cannot run in a simple Python container without images

**No Unit Tests:**
- All tests are integration tests validating running containers
- No isolated unit tests for Python helper code
- ContainerRunner class itself has no unit tests

**Build Process:**
- `./scripts/build.sh` is the build entry point but requires podman/docker
- Manual builds use `podman build --build-arg-file <type>/<version>/app.conf`
- Build args stored in version-specific config files (e.g., `python/3.12/app.conf`)

**Validation Limitations:**
- This analysis validated Python linting/type checking only
- Container builds were not validated (require resources)
- Image tests were not run (require built images)
- Tekton pipelines were not analyzed

**What an Agent Can Do:**
- ✓ Validate Python code changes with lint/type checks in ~10 seconds
- ✓ Check Containerfile syntax with hadolint
- ✗ Cannot run integration tests without building images first
- ✗ Cannot build CUDA images in constrained environments

**Recommended Agent Workflow:**
1. For Python code changes: Run lint + type checks (fast, reliable)
2. For Containerfile changes: Run hadolint (fast, reliable)
3. For integration validation: Recommend manual testing or defer to CI

---

## Quick Reference

**Install dev dependencies:**
```bash
pip install -e '.[dev]'
```

**Run all lint checks:**
```bash
tox -e lint
# OR individually:
ruff check tests/
ruff format --check tests/
./scripts/lint-containerfile.sh
```

**Run type checking:**
```bash
tox -e type
# OR:
mypy tests/
```

**Run tests (requires images):**
```bash
# Build image first:
./scripts/build.sh python-3.12

# Run tests:
PYTHON_IMAGE=localhost/odh-midstream-python-base:3.12 \
PYTHON_VERSION=3.12 \
pytest tests/test_python_image.py tests/test_common.py -v
```

**Auto-fix linting issues:**
```bash
ruff check --fix tests/
ruff format tests/
```

**Build containers:**
```bash
./scripts/build.sh python-3.12    # Build Python 3.12 image
./scripts/build.sh cuda-12.8      # Build CUDA 12.8 image
./scripts/build.sh all            # Build all images
```

---

## Contact & Resources

**Repository:** https://github.com/opendatahub-io/base-containers
**CI Config:** `.github/workflows/ci.yml`
**Lint Config:** `pyproject.toml` (ruff, mypy), `.hadolint.yaml` (hadolint)
**Test Config:** `pyproject.toml`, `tox.ini`, `tests/conftest.py`
**Documentation:** `AGENTS.md`, `docs/DEVELOPMENT.md`, `docs/RATIONALE.md`

**Python Version:** 3.12 (required)
**Container Runtime:** podman (preferred) or docker
**Image Registry:** quay.io/opendatahub (published images)
