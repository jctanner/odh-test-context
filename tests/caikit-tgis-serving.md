# Test Context for caikit-tgis-serving

**Repository:** opendatahub-io/caikit-tgis-serving
**Languages:** Python
**Build System:** Poetry
**Agent Readiness:** **LOW** - Dependencies install cleanly, but no linting and tests require full infrastructure (docker-compose or KServe cluster)

---

## Overview

This is a minimal Python 3.11 project using Poetry for dependency management. The repository contains only 2 Python source files and focuses on packaging a containerized Caikit TGIS serving runtime.

**Critical Limitations:**
- ❌ No linting configuration (no flake8, ruff, black, mypy, or pre-commit hooks)
- ❌ No traditional unit tests (no pytest, unittest framework)
- ❌ Only integration/smoke tests that require running infrastructure
- ⚠️  Cannot validate patches in isolation without full environment setup

An agent can install dependencies and verify Python syntax, but **cannot run lint or tests** to validate patches.

---

## Container Recipe

This recipe shows what CAN be validated (dependency install, syntax check, imports) but highlights that **lint and tests cannot be run** without infrastructure.

### 1. Start Container

```bash
podman run -d --name test-context-caikit-tgis-serving \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-caikit-tgis-serving bash -c \
  "apt-get update && apt-get install -y make git"
```

### 3. Install Poetry

```bash
podman exec test-context-caikit-tgis-serving bash -c \
  "pip install poetry"
```

### 4. Install Project Dependencies

**Note:** This takes 3-5 minutes due to large ML packages (torch, transformers, caikit).

```bash
podman exec test-context-caikit-tgis-serving bash -c \
  "cd /app && poetry install --no-root"
```

**Expected:** Installs 100+ packages including caikit, caikit-nlp, caikit-tgis-backend, torch, transformers.

### 5. Validate Python Syntax

```bash
podman exec test-context-caikit-tgis-serving bash -c \
  "cd /app && poetry run python -m py_compile test/smoke-test.py utils/convert.py"
```

**Expected:** Exit code 0, output "Python files compile successfully"

### 6. Validate Imports

```bash
podman exec test-context-caikit-tgis-serving bash -c \
  "cd /app && poetry run python -c 'import caikit; import caikit_nlp; import caikit_tgis_backend; print(\"Imports OK\")'"
```

**Expected:** Exit code 0, output "Imports OK" (may show BETA warning, which is normal)

### 7. Lint Commands

**❌ NOT AVAILABLE** - No linting configured in this repository.

### 8. Test Commands

**❌ CANNOT RUN** - Tests require external infrastructure:

**Option A: Docker Compose Test** (requires running containers)
```bash
# Requires:
# - caikit-tgis-serving:dev image built
# - TGIS image: quay.io/opendatahub/text-generation-inference:stable
# - Model files downloaded and converted
cd test/compose
bash -x smoke-test.sh
```

**Option B: KServe Test** (requires Kubernetes cluster)
```bash
# Requires:
# - Kubernetes cluster with KServe, Istio, Knative installed
# - caikit-tgis-serving image loaded into cluster
# - Model volumes and InferenceService deployed
python test/smoke-test.py
```

**What the tests do:** Make actual inference requests to running Caikit TGIS endpoints (HTTP and gRPC) with a text generation prompt ("At what temperature does liquid Nitrogen boil?") and verify responses.

### 9. Cleanup

```bash
podman rm -f test-context-caikit-tgis-serving
```

---

## Validation Results

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install | `poetry install --no-root` | ✅ PASS | Installed 100+ packages successfully |
| Syntax Check | `poetry run python -m py_compile test/*.py utils/*.py` | ✅ PASS | Both Python files compile |
| Imports | `import caikit; import caikit_nlp` | ✅ PASS | All caikit packages import |
| Lint | N/A | ❌ N/A | No linting configured |
| Tests | `test/smoke-test.py` | ❌ SKIP | Requires infrastructure |

**Summary:** Dependencies install cleanly and Python code is syntactically valid, but **no linting and no testable validation** without full infrastructure.

---

## CI/CD

**System:** GitHub Actions
**Main Workflow:** `.github/workflows/build-and-test.yml` (gating on pull requests)

### Gating Checks

All checks run in the `build-and-test.yml` workflow on pull requests:

1. **Build Image**
   ```bash
   docker build -t kind.local/caikit-tgis-serving:dev .
   ```
   Builds the container image using the Dockerfile.

2. **Compose Smoke Test** (job: `compose-smoke-test`)
   ```bash
   cd test/compose
   bash -x smoke-test.sh
   ```
   Requires:
   - Built caikit-tgis-serving:dev image
   - Pulls quay.io/opendatahub/text-generation-inference:stable
   - Downloads and converts google/flan-t5-small model
   - Runs docker-compose up
   - Runs `python test/smoke-test.py` to test endpoints

3. **KServe Smoke Test** (job: `kserve-smoke-test`)
   ```bash
   # After Kind cluster + KServe setup
   python test/smoke-test.py
   ```
   Requires:
   - Kind cluster with KServe, Istio, Knative
   - Model volume setup (downloads flan-t5-small)
   - InferenceService deployment
   - Tests HTTP inference endpoint

**No Linting:** The CI does not run any linting checks (no flake8, ruff, black, mypy, etc.).

**No Unit Tests:** The CI does not run any traditional unit tests. Only integration/smoke tests against running services.

---

## Build Configuration

**Dependency Management:** Poetry (Python 3.11)

**Install Dependencies:**
```bash
poetry install --no-root
```

**Build Container:**
```bash
# Using podman (or replace with docker)
podman build -t caikit-tgis-serving:dev .
```

**Container Details:**
- Base image: `registry.access.redhat.com/ubi9/ubi-minimal:latest`
- Multi-stage build (poetry-builder + deploy)
- Installs Python 3.11, poetry, and project dependencies
- Runtime entrypoint: `python -m caikit.runtime`

---

## Conventions

**Python Files:**
- Minimal codebase: only 2 .py files
  - `test/smoke-test.py` - Integration test script
  - `utils/convert.py` - Model conversion utility

**Test Naming:**
- No traditional test naming conventions (no `test_*.py` or `*_test.py` with unit tests)
- Only `smoke-test.py` which is an integration test

**Import Style:**
- Standard Python imports (no special conventions)

**No Code Coverage:**
- No coverage measurement configured

---

## Gaps & Caveats

### Critical Gaps

1. **No Linting Configuration**
   - No .flake8, .pylintrc, ruff.toml, or .pre-commit-config.yaml
   - No linting in CI workflows
   - Cannot validate code style or quality

2. **No Traditional Unit Tests**
   - No pytest, unittest, or other test framework
   - Only integration tests that require running services
   - Cannot test code logic in isolation

3. **Tests Require Infrastructure**
   - **Docker Compose test:** Requires caikit + TGIS containers, model files
   - **KServe test:** Requires full Kubernetes cluster with KServe, Istio, Knative
   - Cannot run tests locally without significant setup

4. **Cannot Validate Patches in Isolation**
   - An agent can install deps and check syntax
   - But cannot lint or test to verify patch correctness
   - Would need to build full container and deploy to test environment

### What Works

- ✅ Poetry dependency installation (in container)
- ✅ Python syntax validation
- ✅ Import verification
- ✅ Container build (if Docker/Podman available)

### What Doesn't Work

- ❌ Linting (not configured)
- ❌ Unit tests (don't exist)
- ❌ Integration tests (require infrastructure)
- ❌ Local patch validation (no testable checks available)

---

## Agent Readiness: LOW

**Justification:** While dependencies install cleanly and Python syntax can be validated, there is **no linting** and **no runnable tests** without full infrastructure. An agent can apply patches and verify they don't introduce syntax errors, but cannot validate correctness, style, or functionality.

**For patch validation, an agent would need:**
1. Docker/Podman to build the container
2. Docker Compose OR
3. A Kubernetes cluster with KServe/Istio/Knative

**What an agent CAN do:**
- Install dependencies with Poetry
- Check Python syntax
- Verify imports work
- Build the container image

**What an agent CANNOT do:**
- Lint the code (no linting configured)
- Run unit tests (none exist)
- Run integration tests (require infrastructure)
- Get a clear pass/fail signal on patch correctness

---

## Recommendations for Improving Agent Readiness

To make this repository more agent-friendly:

1. **Add linting:**
   ```toml
   # pyproject.toml
   [tool.ruff]
   line-length = 100
   select = ["E", "F", "I"]
   ```

2. **Add unit tests:**
   - Test the convert.py utility logic
   - Mock external dependencies for smoke-test.py
   - Use pytest framework

3. **Separate unit tests from integration tests:**
   - `tests/unit/` - Can run in any environment
   - `tests/integration/` - Require infrastructure
   - Run unit tests in CI before integration tests

4. **Add pre-commit hooks:**
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       hooks:
         - id: ruff
         - id: ruff-format
   ```

These changes would raise agent readiness from **LOW** to **MEDIUM** or **HIGH**.
