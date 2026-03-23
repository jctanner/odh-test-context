# Test Context: opendatahub-io/base-images

**Generated:** 2026-03-22T21:36:00Z

## Overview

Python project building container base images for Open Data Hub. Uses `uv` (Astral's modern Python package manager), pytest with testcontainers, and comprehensive linting with ruff + pyright.

**Languages:** Python 3.12
**Build System:** uv (package management), Make + Podman/Docker (container images)
**Agent Readiness:** **medium** - Lint validates perfectly, tests exist and framework works, but actual tests require container images to validate. An agent can lint patches with high confidence but cannot fully test without building/providing container images.

---

## Container Recipe

This is the **complete, copy-paste recipe** for validating patches in a container. Every command below has been validated and works.

### 1. Start Container

```bash
podman run -d --name test-context-base-images \
  -v /path/to/base-images:/app:Z \
  -w /app \
  python:3.12-bookworm \
  sleep infinity
```

**Note:** Replace `/path/to/base-images` with the actual repository path. Use `docker` instead of `podman` if needed.

### 2. Install System Dependencies

```bash
podman exec test-context-base-images bash -c "apt-get update && apt-get install -y curl git ca-certificates"
```

### 3. Install UV Package Manager

```bash
podman exec test-context-base-images bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

This installs `uv` to `/root/.local/bin/`. You must add this to PATH in subsequent commands.

### 4. Install Project Dependencies

```bash
podman exec test-context-base-images bash -c "cd /app && /root/.local/bin/uv sync --locked"
```

**Expected output:**
- Resolves 94 packages
- Installs 93 packages including pytest, ruff, pyright, testcontainers, docker, podman, kubernetes, etc.
- Takes ~2-3 seconds (after downloads)

**Exit code:** 0 (success)

### 5. Run Linters

#### Ruff - Check Code Style

```bash
podman exec test-context-base-images bash -c "cd /app && /root/.local/bin/uv run ruff check ci/ tests/"
```

**Expected output:** `All checks passed!` (may have 1 warning about invalid noqa comment)
**Exit code:** 0 (success)
**What it checks:** 70+ linting rules including pycodestyle, pyflakes, bugbear, comprehensions, imports, etc.

#### Ruff - Check Formatting

```bash
podman exec test-context-base-images bash -c "cd /app && /root/.local/bin/uv run ruff format --check ci/ tests/"
```

**Expected output:** `20 files already formatted`
**Exit code:** 0 (success)

#### Pyright - Type Checking

```bash
podman exec test-context-base-images bash -c "cd /app && /root/.local/bin/uv run pyright --pythonversion 3.12 ci/ tests/"
```

**Expected output:** `0 errors, 0 warnings, 0 informations`
**Exit code:** 0 (success)

#### Pre-commit - All Hooks

```bash
podman exec test-context-base-images bash -c "cd /app && PATH=/root/.local/bin:\$PATH /root/.local/bin/uv run pre-commit run --all-files"
```

**Expected output:**
```
uv-lock..................................................................Passed
ruff.....................................................................Passed
ruff-format..............................................................Passed
Run Pyright on all files.................................................Passed
```

**Exit code:** 0 (success)
**Note:** Requires PATH adjustment for pyright hook to find `uv` binary.

### 6. Run Tests

```bash
podman exec test-context-base-images bash -c "cd /app && /root/.local/bin/uv run pytest"
```

**Expected output:**
```
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-8.3.4, pluggy-1.5.0
...
================== 6 passed, 7 skipped, 2 warnings in 11.48s ===================
```

**Exit code:** 0 (success)
**Status:** 6 tests pass (Python unit tests in ci/), 7 tests skip (container image tests in tests/containers/ - require `--image` parameter)

**To test specific container images:**
```bash
podman exec test-context-base-images bash -c "cd /app && /root/.local/bin/uv run pytest --image=quay.io/opendatahub/base-images:cpu-ubi9-python-3.11-2025a_20250122"
```

This will run container validation tests against the specified image.

### 7. Verify Code Generation

```bash
podman exec test-context-base-images bash -c "cd /app && python3 scripts/dockerfile_fragments.py && git status --porcelain"
```

**Expected output:** (empty - no files modified)
**Exit code:** 0 (success)
**Purpose:** Ensures generated code (Dockerfile fragments) is up-to-date.

### 8. Run Single Test File

```bash
podman exec test-context-base-images bash -c "cd /app && /root/.local/bin/uv run pytest tests/containers/base_image_test.py"
```

### 9. Run Single Test Function

```bash
podman exec test-context-base-images bash -c "cd /app && /root/.local/bin/uv run pytest tests/containers/base_image_test.py::TestBaseImage::test_oc_command_runs -v"
```

**Note:** Without `--image` parameter, most tests in base_image_test.py will skip.

### 10. Cleanup

```bash
podman rm -f test-context-base-images
```

---

## Validation Results

All commands validated successfully on 2026-03-22:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install | `uv sync --locked` | ✅ PASS | 93 packages installed |
| Lint (ruff check) | `uv run ruff check ci/ tests/` | ✅ PASS | 1 warning (noqa comment) |
| Lint (ruff format) | `uv run ruff format --check ci/ tests/` | ✅ PASS | 20 files formatted |
| Lint (pyright) | `uv run pyright ci/ tests/` | ✅ PASS | 0 errors, 0 warnings |
| Lint (pre-commit) | `uv run pre-commit run --all-files` | ✅ PASS | Requires PATH fix |
| Test | `uv run pytest` | ✅ PASS | 6 passed, 7 skipped |
| Codegen | `python3 scripts/dockerfile_fragments.py` | ✅ PASS | No files changed |

**Summary:** All validation commands work. Linting is fully automated and reliable. Tests run but most require `--image` parameter to test actual container images.

---

## CI/CD

GitHub Actions workflows gate pull requests:

### Gating Checks (Required for Merge)

**1. check-generated-code** (`.github/workflows/code-quality.yaml`)
```bash
bash ci/generate_code.sh
git status --porcelain  # must be empty
```
Ensures generated Dockerfile fragments are up-to-date.

**2. pytest-tests** (`.github/workflows/code-quality.yaml`)
```bash
uv sync --locked
uv run pre-commit run --all-files
uv run pytest
```
Runs all linters and tests.

**3. code-static-analysis** (`.github/workflows/code-quality.yaml`)
```bash
# YAML validation
yamllint --strict --config-file ./ci/yamllint-config.yaml *.yaml *.yml

# JSON validation
bash ./ci/check-json.sh

# Dockerfile linting
hadolint --config ./ci/hadolint-config.yaml Dockerfile*
```

**4. build-notebooks-pr** (`.github/workflows/build-notebooks-pr.yaml`)

Builds container images for changed Dockerfiles (uses cached builds to determine what changed).

### Advisory Checks (Non-blocking)

**security** (`.github/workflows/security.yaml`)
- Trivy filesystem scan
- Uploads results to GitHub Security tab

---

## Conventions

**Test Files:** `tests/**/*_test.py`

**Test Naming:**
- Classes: `TestBaseImage`, `TestSomething`
- Functions: `test_elf_files_can_link_runtime_libs`, `test_oc_command_runs`

**Import Style:**
- Ruff enforces import sorting (isort rules)
- Order: stdlib, third-party, local
- Absolute imports preferred

**Type Hints:**
- Pyright validates type hints with `typeCheckingMode = "off"` but specific checks enabled
- Uses `from __future__ import annotations` for modern type syntax

**Markers:**
- `@pytest.mark.openshift` - tests requiring OpenShift cluster (currently unregistered)
- Tests skip dynamically based on image type (cuda, rocm, workbench, etc.)

---

## Gaps & Caveats

### 1. Tests Require Container Images

The main test suite (`tests/containers/base_image_test.py`) validates container images:
- Without `--image=<container-image>`, 7/13 tests skip
- Tests validate: ELF linking, file permissions, oc/skopeo commands, pip install, FIPS mode
- Requires Docker/Podman runtime access

**Workaround:** Run `pytest` without `--image` to validate test framework. Supply `--image` to test actual images.

### 2. Pre-commit Hook PATH Issue

The pyright pre-commit hook requires `uv` in PATH:

```bash
# Won't work:
uv run pre-commit run --all-files

# Will work:
PATH=/root/.local/bin:$PATH uv run pre-commit run --all-files
```

### 3. Unknown Pytest Marker

`@pytest.mark.openshift` is used but not registered in pytest config. Generates warning but doesn't fail tests.

**Fix:** Add to pyproject.toml:
```toml
[tool.pytest.ini_options]
markers = [
    "openshift: tests requiring OpenShift cluster"
]
```

### 4. No Coverage Configured

No pytest-cov configuration or coverage thresholds defined. Coverage plugin is installed but not used.

### 5. Container Runtime Required

Tests use `testcontainers` library and need:
- Docker or Podman socket access
- Ability to pull/run containers
- May need `TESTCONTAINERS_RYUK_DISABLED=true` for rootless podman

### 6. Image Tests Skip Without Images

Without building/pulling the actual base images, most tests skip. The test framework is validated, but not the actual image validation logic.

---

## Quick Reference

**Install deps:** `uv sync --locked`
**Lint (all):** `uv run pre-commit run --all-files` (with PATH fix)
**Lint (ruff):** `uv run ruff check ci/ tests/`
**Format (ruff):** `uv run ruff format ci/ tests/`
**Type check:** `uv run pyright ci/ tests/`
**Test (all):** `uv run pytest`
**Test (single file):** `uv run pytest tests/containers/base_image_test.py`
**Test (with image):** `uv run pytest --image=<container-image>`
**Codegen check:** `bash ci/generate_code.sh && git status --porcelain`

**Container engine:** Podman or Docker (auto-detected in Makefile)
**Python version:** 3.12 (`.python-version`)
**Package manager:** uv (replaces pip/poetry/pipenv)

---

## For Downstream Agents

**Can validate automatically:**
- ✅ Lint violations (ruff, pyright)
- ✅ Code formatting (ruff format)
- ✅ Type errors (pyright)
- ✅ Pre-commit hooks
- ✅ Generated code freshness
- ✅ Test framework functionality

**Cannot validate without infrastructure:**
- ❌ Container image tests (need --image parameter and container runtime)
- ❌ OpenShift deployment tests (need cluster access)
- ❌ Full integration tests

**Recommended validation strategy:**
1. Run all linters (high confidence, fast, no infrastructure needed)
2. Run `pytest` without `--image` to validate Python code changes
3. If Dockerfiles changed, consider building images and running full tests

**Time estimates:**
- Dependency install: ~3-5 seconds (with cached downloads)
- Lint (all): ~10-15 seconds
- Tests (without images): ~12 seconds
- Full validation: ~30 seconds
