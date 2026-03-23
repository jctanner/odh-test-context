# Test Context: training-notebooks

**Generated:** 2026-03-23T00:27:52Z
**Repository:** opendatahub-io/training-notebooks
**Agent Readiness:** HIGH — Lint and basic test commands validated successfully in container

## Overview

**Languages:** Python 3.12
**Package Manager:** uv (modern Python package manager, replaces pip/pipenv)
**Build System:** Makefile (for container images), uv (for Python dependencies)
**Test Framework:** pytest with markers for infrastructure requirements
**Linting:** Ruff (format + check) + Pyright, orchestrated via pre-commit hooks

**Agent Readiness Rating: HIGH**
Justification: All linting commands and basic tests validated successfully in a Python 3.12 container. Dependencies install cleanly with `uv sync --locked`. An agent can clone, install, lint, and run basic tests with clear pass/fail signals. Container tests require Docker/Podman infrastructure but are not needed for basic patch validation.

## Container Recipe

This is a complete, copy-paste recipe for validating patches. Follow these steps in order:

### 1. Start Container

```bash
podman run -d --name test-context-training-notebooks \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

**Base Image:** `python:3.12` (Debian Trixie)
**Working Directory:** `/app` (repo bind-mounted from host)

### 2. Install System Dependencies

```bash
podman exec test-context-training-notebooks bash -c "apt-get update && apt-get install -y git make curl"
```

**Note:** These packages are already present in the python:3.12 image.

### 3. Install uv Package Manager

```bash
podman exec test-context-training-notebooks bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

This installs uv to `/root/.local/bin/`. All subsequent commands must have this in PATH.

### 4. Install Project Dependencies

```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv sync --locked"
```

**Expected Output:** `Resolved 94 packages`, `Checked 93 packages`
**Exit Code:** 0
**Validation Status:** ✓ PASSED

### 5. Run Linting — Ruff Check

```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run ruff check ci tests"
```

**Expected Output:** `All checks passed!` (may show 1 warning about noqa comment)
**Exit Code:** 0
**Validation Status:** ✓ PASSED
**Notes:** Lints Python files in `ci/` and `tests/` directories only. Ruff configuration in `pyproject.toml` enables extensive rule sets (B, C4, COM, E, W, F, etc.). Line length is 120.

### 6. Run Linting — Ruff Format

```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run ruff format --check ci tests"
```

**Expected Output:** `38 files already formatted`
**Exit Code:** 0
**Validation Status:** ✓ PASSED

### 7. Run Linting — Pyright Type Checker

```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pyright"
```

**Expected Output:** `0 errors, 0 warnings, 0 informations`
**Exit Code:** 0
**Validation Status:** ✓ PASSED
**Notes:** Pyright installs Node.js automatically on first run. Type checking mode is "off" but still checks for missing imports and unbound variables.

### 8. Run Linting — Pre-commit (All Linters)

```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pre-commit run --all-files"
```

**Expected Output:**
```
uv-lock..................................................................Passed
ruff.....................................................................Passed
ruff-format..............................................................Passed
Run Pyright on all files.................................................Passed
```

**Exit Code:** 0
**Validation Status:** ✓ PASSED
**Notes:** This is the comprehensive lint check. Runs uv-lock, ruff, ruff-format, and pyright. First run installs pre-commit environments (~2 minutes).

### 9. Run Tests — Tutorial Tests

```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pytest tests/pytest_tutorial -v"
```

**Expected Output:** `4 passed in 0.03s`
**Exit Code:** 0
**Validation Status:** ✓ PASSED

### 10. Run Tests — Basic Validation Tests

```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pytest tests/test_main.py::test_image_pipfiles tests/test_main.py::test_files_that_should_be_same_are_same -v"
```

**Expected Output:** `2 passed, 32 subtests passed`
**Exit Code:** 0
**Validation Status:** ✓ PASSED
**Notes:** These tests validate Pipfile configurations and file consistency across the repository.

### 11. Run Single Test File

Template:
```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pytest {file_path}"
```

Example:
```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pytest tests/pytest_tutorial/test_01_intro.py"
```

### 12. Run Single Test

Template:
```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pytest {file_path}::{test_name}"
```

Example:
```bash
podman exec test-context-training-notebooks bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pytest tests/pytest_tutorial/test_01_intro.py::test_hello_world"
```

### 13. Cleanup

```bash
podman rm -f test-context-training-notebooks
```

Always clean up the container when done, even if validation fails partway through.

---

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `uv sync --locked` | 0 | ✓ PASS | 94 packages resolved |
| Lint (ruff check) | `uv run ruff check ci tests` | 0 | ✓ PASS | 1 warning (non-critical) |
| Lint (ruff format) | `uv run ruff format --check ci tests` | 0 | ✓ PASS | 38 files formatted |
| Lint (pyright) | `uv run pyright` | 0 | ✓ PASS | 0 errors, 0 warnings |
| Lint (pre-commit) | `uv run pre-commit run --all-files` | 0 | ✓ PASS | All hooks passed |
| Test (tutorial) | `uv run pytest tests/pytest_tutorial` | 0 | ✓ PASS | 4 passed |
| Test (basic) | `uv run pytest tests/test_main.py::<subset>` | 0 | ✓ PASS | 2 passed, 32 subtests |
| Test (all main) | `uv run pytest tests/test_main.py` | 1 | ⚠ PARTIAL | 2 passed, 1 failed* |

\* One test (`test_make_disable_pushing`) requires make + podman/docker and fails without them. This is expected and does not affect basic patch validation.

---

## CI/CD

**System:** GitHub Actions (primary) + Tekton (image builds)
**Config Files:** `.github/workflows/code-quality.yaml`, `.github/workflows/build-notebooks-pr*.yaml`, `.tekton/*.yaml`

### Gating Checks (on Pull Request)

The `code-quality.yaml` workflow runs three jobs that gate PR merges:

#### Job 1: check-generated-code
```bash
bash ci/generate_code.sh
```
Validates that all generated code is committed. Fails if `git status --porcelain` shows uncommitted changes after running generators.

#### Job 2: pytest-tests
```bash
uv sync --locked
uv run pre-commit run --all-files
uv run pytest
```
Installs dependencies, runs all linters via pre-commit, and runs full pytest suite.

#### Job 3: code-static-analysis

**YAML validation:**
```bash
find . -name "*.yaml" | grep -v './.tekton/' | grep -v './.github/workflows/insta-merge.yaml' | xargs yamllint --strict --config-file ./ci/yamllint-config.yaml
find . -name "*.yml" | grep -v './.tekton/' | xargs yamllint --strict --config-file ./ci/yamllint-config.yaml
```

**JSON validation:**
```bash
bash ./ci/check-json.sh
```

**Dockerfile validation:**
```bash
find . -name "Dockerfile*" | xargs hadolint --config ./ci/hadolint-config.yaml
```

**Kustomize validation:**
```bash
./ci/kustomize.sh
```

### Additional CI Workflows

- **build-notebooks-pr.yaml**: Builds notebook container images on PR (uses matrix for different Python versions and variants)
- **build-notebooks-pr-rhel.yaml**: Builds RHEL-based variants
- **Tekton pipelines**: `.tekton/*.yaml` files define Konflux-based builds for production releases

All `code-quality.yaml` checks are **required** for PR merge.

---

## Conventions

### Test File Naming
- Pattern: `test_*.py` or `*_test.py`
- Location: `tests/` directory and subdirectories

### Test Function/Class Naming
- Functions: `test_*`
- Classes: `Test*`
- Pytest convention, not unittest

### Test Markers
Tests use pytest markers to indicate infrastructure requirements:
- `@pytest.mark.openshift` — requires OpenShift cluster
- `@pytest.mark.cuda` — requires CUDA-capable GPU
- `@pytest.mark.rocm` — requires ROCm-capable AMD GPU

Run tests without infrastructure requirements:
```bash
uv run pytest -m 'not openshift and not cuda and not rocm'
```

### Import Style
- `from __future__ import annotations` at the top of files
- Absolute imports preferred
- Imports grouped and sorted by ruff's isort rules

### Code Style
- Line length: 120 characters
- Quote style: double quotes
- Indent style: spaces (4 spaces)
- Formatting enforced by `ruff format`

---

## Gaps & Caveats

### Container Tests Not Validated
Tests in `tests/containers/` require:
- A running Docker or Podman daemon
- An `--image <digest>` parameter pointing to a pre-built notebook image
- Example: `DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock uv run pytest tests/containers -m 'not openshift and not cuda and not rocm' --image quay.io/opendatahub/workbench-images@sha256:...`

These tests validate notebook container images but are not needed for basic code patch validation.

### Infrastructure-Specific Tests
- **OpenShift:** Many container tests deploy to an OpenShift cluster via `kubectl apply -k`
- **CUDA:** GPU-accelerated tests require NVIDIA CUDA hardware
- **ROCm:** GPU-accelerated tests require AMD ROCm hardware

These tests cannot run in a basic container environment.

### Browser Tests
Tests in `tests/browser/` use Playwright to test JupyterLab UI. Require Playwright installation. See `tests/browser/README.md`.

### Additional CI Tools
The `code-static-analysis` job requires:
- `yamllint` (YAML validation)
- `json_verify` / `yajl-tools` (JSON validation)
- `hadolint` (Dockerfile linting)
- `kustomize` (Kubernetes manifest validation)

These are installed in CI but not in the basic Python container.

### Makefile Image Building
Building notebook images via Makefile (e.g., `make jupyter-minimal-ubi9-python-3.11`) requires:
- Podman or Docker
- Significant disk space for base images and layers
- Multi-stage builds with UBI9, CUDA, or ROCm base images

Not relevant for code patch validation, but essential for image development.

### One Test Requires Make + Container Engine
The test `test_make_disable_pushing` in `tests/test_main.py` validates Makefile behavior and requires:
- `make` (or `gmake`)
- A working container engine (podman or docker)

This test fails in a basic Python container but does not affect linting or other test validation.

---

## Quick Reference

### Install Dependencies
```bash
uv sync --locked
```

### Run All Linters
```bash
uv run pre-commit run --all-files
```

### Run Individual Linters
```bash
uv run ruff check ci tests              # Check for issues
uv run ruff check --fix ci tests        # Auto-fix issues
uv run ruff format --check ci tests     # Check formatting
uv run ruff format ci tests             # Auto-format
uv run pyright                          # Type check
```

### Run All Tests
```bash
uv run pytest
```

### Run Tests Without Infrastructure
```bash
uv run pytest -m 'not openshift and not cuda and not rocm'
```

### Run Specific Test File
```bash
uv run pytest tests/test_main.py
```

### Run Specific Test
```bash
uv run pytest tests/test_main.py::test_image_pipfiles
```

### CI Commands (for reference)
```bash
bash ci/generate_code.sh                # Regenerate generated code
```

---

## Summary

**Agent Readiness: HIGH**

This repository has excellent tooling for automated patch validation:
- ✓ Dependencies install reliably with `uv sync --locked`
- ✓ Linting is comprehensive (ruff + pyright) and validated
- ✓ Basic tests run successfully without infrastructure
- ✓ Pre-commit hooks provide one-command validation
- ✓ CI configuration is clear and well-documented

An AI agent can:
1. Clone the repository
2. Start the Python 3.12 container
3. Install uv and dependencies
4. Run linting via `uv run pre-commit run --all-files`
5. Run basic tests via `uv run pytest tests/test_main.py tests/pytest_tutorial`
6. Get clear pass/fail signals

**Limitations:**
- Container image tests require infrastructure (Docker/Podman, pre-built images)
- Some tests require OpenShift, CUDA, or ROCm
- Full CI validation includes YAML/JSON/Dockerfile linting (requires additional tools)

For **code patch validation** (linting + basic tests), this repository is **agent-ready**.
