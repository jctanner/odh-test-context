# Test Context: llama-stack-provider-kfp-trainer

**Generated:** 2026-03-22T18:56:00-04:00

## Overview

**Repository:** opendatahub-io/llama-stack-provider-kfp-trainer
**Language:** Python 3.11
**Build System:** setuptools (pyproject.toml)
**Test Framework:** pytest via tox
**Linter:** ruff
**Type Checker:** mypy

**Agent Readiness: HIGH** — All lint and test commands validated successfully in container. Dependencies install cleanly. Tests pass with clear exit codes. No external infrastructure required for unit tests (moto mocks AWS services). An agent can clone, patch, lint, and test with unambiguous pass/fail signals.

---

## Container Recipe

This is the complete, copy-paste recipe for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-kfp-trainer \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11-slim \
  sleep infinity
```

If `podman` is unavailable, replace with `docker`.

### 2. Install System Dependencies

```bash
podman exec test-kfp-trainer bash -c "apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*"
```

**Why git?** Required by the Containerfile and some Python dependencies.

### 3. Install Python Dependencies

```bash
podman exec test-kfp-trainer bash -c "cd /app && python -m pip install --upgrade pip"
podman exec test-kfp-trainer bash -c "cd /app && pip install tox"
```

**Why tox?** CI uses tox to manage isolated environments for linting, type checking, and testing. This matches the GitHub Actions workflow exactly.

### 4. Run Linting

```bash
podman exec test-kfp-trainer bash -c "cd /app && tox -e lint"
```

**Expected output:**
- Exit code: 0
- Output: "All checks passed!" and "10 files left unchanged"
- Duration: ~1-2 seconds

**What it does:**
1. Creates isolated virtualenv with ruff
2. Runs `ruff check .` (linting)
3. Runs `ruff format .` (formatting)

**Validation status:** ✅ PASSED (exit 0, no issues found)

**Note:** CI enforces that linting produces no git diff. If ruff format changes files, the CI check fails. For patch validation, check exit code only.

### 5. Run Type Checking

```bash
podman exec test-kfp-trainer bash -c "cd /app && tox -e mypy"
```

**Expected output:**
- Exit code: 0
- Output: "Success: no issues found in 7 source files"
- Duration: ~150 seconds (first run installs project dependencies)

**What it does:**
1. Creates isolated virtualenv with mypy, boto3-stubs
2. Installs project in editable mode (`-e .`)
3. Runs `mypy src/`

**Validation status:** ✅ PASSED (exit 0, no type errors)

### 6. Run Tests

```bash
podman exec test-kfp-trainer bash -c "cd /app && tox -e test"
```

**Expected output:**
- Exit code: 0
- Output: "3 passed, 3 warnings in 4.50s"
- Duration: ~130 seconds (first run installs dependencies including moto, pytest)

**What it does:**
1. Creates isolated virtualenv with pytest, moto[s3]
2. Installs project in editable mode
3. Runs `pytest` (configured to test `tests/` directory)

**Validation status:** ✅ PASSED (3/3 tests passed)

**Warnings:** The test run shows warnings from pydantic and deprecated SWIG imports. These are not test failures — just library deprecation notices. They don't affect test results.

### 7. Run Single Test File (Optional)

```bash
podman exec test-kfp-trainer bash -c "cd /app && .tox/test/bin/pytest tests/unit/test_s3.py -v"
```

**Template:** Replace `tests/unit/test_s3.py` with `{file}` path.

**Validation status:** ✅ PASSED (3/3 tests in file passed)

### 8. Run Single Test (Optional)

```bash
podman exec test-kfp-trainer bash -c "cd /app && .tox/test/bin/pytest tests/unit/test_s3.py::test_upload_download -v"
```

**Template:** Replace `tests/unit/test_s3.py::test_upload_download` with `{file}::{test_name}`.

**Validation status:** ✅ PASSED (1 test passed)

### 9. Cleanup

```bash
podman rm -f test-kfp-trainer
```

**Always run this** even if validation fails partway through.

---

## Validation Results

All commands were executed successfully in a clean `python:3.11-slim` container:

| Step | Command | Exit Code | Result | Duration | Notes |
|------|---------|-----------|--------|----------|-------|
| System deps | `apt-get install git` | 0 | ✅ PASS | ~5s | 31 packages installed |
| Upgrade pip | `pip install --upgrade pip` | 0 | ✅ PASS | ~2s | 24.0 → 26.0.1 |
| Install tox | `pip install tox` | 0 | ✅ PASS | ~10s | tox 4.50.3 + deps |
| Lint | `tox -e lint` | 0 | ✅ PASS | 1.45s | All checks passed |
| Type check | `tox -e mypy` | 0 | ✅ PASS | 149s | No issues in 7 files |
| Test | `tox -e test` | 0 | ✅ PASS | 131s | 3/3 tests passed |
| Single file | `pytest tests/unit/test_s3.py -v` | 0 | ✅ PASS | 4s | 3/3 tests passed |
| Single test | `pytest test_s3.py::test_upload_download` | 0 | ✅ PASS | 3s | 1/1 test passed |

**Summary:** Install OK, lint OK (no issues), mypy OK (no issues), tests OK (3/3 passed). Container recipe is fully functional.

---

## CI/CD

### Gating Checks (Required for Merge)

All workflows trigger on `push` to `main` and `pull_request` to `main`. Python 3.11 is used throughout.

#### 1. Lint (.github/workflows/lint.yml)

**Command:** `tox -e lint`

**Steps:**
1. Setup Python 3.11
2. Install tox
3. Run `tox -e lint`
4. **Fail if git diff is not clean** — if ruff format changed files, CI fails

**Why it matters:** This is stricter than just checking exit code. Patches must be pre-formatted with ruff.

**Validation:** ✅ Command works, exits 0, produces no git changes

#### 2. Mypy (.github/workflows/mypy.yml)

**Command:** `tox -e mypy`

**Steps:**
1. Setup Python 3.11
2. Install tox
3. Run `tox -e mypy`

**Why it matters:** Type checking prevents runtime type errors. All code in `src/` must pass mypy.

**Validation:** ✅ Command works, exits 0, no type errors

#### 3. Unit Tests (.github/workflows/test.yml)

**Command:** `tox -e test`

**Steps:**
1. Setup Python 3.11
2. Install tox
3. Run `tox -e test`

**Why it matters:** Unit tests verify core functionality. Uses moto to mock AWS S3 — no real infrastructure needed.

**Validation:** ✅ Command works, exits 0, 3/3 tests pass

### Advisory Checks (Not Gating)

#### 4. End-to-End Server Startup (.github/workflows/e2e.yml)

**Status:** `continue-on-error: true` — **NOT a gating check**

**Command:** `./scripts/run-{mode}-server.sh` (where mode = local or remote)

**Steps:**
1. Setup Python 3.11
2. Run `./scripts/prepare-venv.sh` (creates .venv, installs deps)
3. Start server in background
4. Poll `http://localhost:8321/v1/health` for "OK" response (30 attempts, 1s apart)
5. Stop server

**Matrix:** Runs on ubuntu-latest + macos-latest × local + remote (4 jobs total)

**Why not gating?** E2E tests require Llama Stack server setup, may need model checkpoints or external resources. Marked as informational only.

**Validation:** ⚠️ Not validated — requires Llama Stack server infrastructure

---

## Conventions

### Test File Naming

**Pattern:** `tests/**/*test_*.py`

**Example:** `tests/unit/test_s3.py`

**Function naming:** `def test_upload_download():`

### Test Organization

```
tests/
└── unit/
    └── test_s3.py  (3 tests)
```

Only unit tests exist. No integration or e2e tests in standard test suite.

### Import Style

Absolute imports from package root:

```python
from llama_stack_provider_kfp_trainer.s3 import Client
```

Source code is in `src/llama_stack_provider_kfp_trainer/`.

### Mock Patterns

Tests use `moto` library to mock AWS services:

```python
from moto import mock_aws

@mock_aws
def test_upload_download():
    c = Client(bucket="test-bucket", region_name="us-east-1").create_bucket()
    # ... test code
```

No real AWS credentials or infrastructure required.

---

## Gaps & Caveats

### 1. Minimal Test Coverage

**Issue:** Only 3 unit tests total, all in `tests/unit/test_s3.py`. Tests only cover S3 client functionality.

**Impact:** Low confidence that patches to `pipeline.py`, `provider.py`, `scheduler.py`, etc. won't break untested code paths.

**Workaround:** Lint and type checking provide some safety. Focus validation on whether patch breaks existing tests, not on comprehensive coverage.

### 2. No Coverage Measurement

**Issue:** No coverage reports, no coverage thresholds configured.

**Impact:** Can't measure whether a patch adds tests for new code.

**Workaround:** None. Coverage analysis not available.

### 3. E2E Tests Not Runnable in Standard CI

**Issue:** E2E workflow has `continue-on-error: true`, requires Llama Stack server setup.

**Impact:** Can't validate end-to-end behavior in automated patch testing.

**Workaround:** Focus on unit tests + lint + mypy. E2E validation requires manual testing or special infrastructure.

### 4. No Pre-commit Hooks

**Issue:** No `.pre-commit-config.yaml`, so developers may commit unformatted code.

**Impact:** Lint check may fail if patch author didn't run ruff format locally.

**Workaround:** Always run `tox -e lint` after applying patch. If it changes files, patch needs reformatting.

### 5. No Makefile

**Issue:** No `Makefile` with convenience targets like `make test`, `make lint`.

**Impact:** Must remember exact tox commands or CI workflow commands.

**Workaround:** Use tox directly (`tox -e lint`, `tox -e test`, `tox -e mypy`).

### 6. Test Dependencies Not in pyproject.toml

**Issue:** Test dependencies (pytest, moto) are only in `tox.ini`, not in `pyproject.toml` `[project.optional-dependencies]`.

**Impact:** Can't install test deps with `pip install -e ".[test]"` — must use tox.

**Workaround:** Always use tox for testing. Direct pytest usage requires tox environment setup first.

---

## Quick Reference

### Commands Summary

```bash
# Lint (ruff check + format)
tox -e lint

# Type check (mypy)
tox -e mypy

# Run all tests
tox -e test

# Run single test file (after tox -e test setup)
.tox/test/bin/pytest tests/unit/test_s3.py -v

# Run single test by name
.tox/test/bin/pytest tests/unit/test_s3.py::test_upload_download -v

# Run all checks (lint + mypy + test)
tox -e lint,mypy,test
```

### Exit Code Interpretation

- **0** = Pass (all checks passed, tests passed)
- **1** = Fail (lint violations, type errors, or test failures)

### Tox Environments

- `lint` — Runs ruff check and format
- `mypy` — Runs type checking on src/
- `test` — Runs pytest on tests/

Defined in `tox.ini` with `envlist = lint, mypy, test`.

---

## Agent Instructions

### For Patch Validation

1. **Apply patch** to working tree
2. **Run in container:** `tox -e lint,mypy,test`
3. **Check exit code:**
   - Exit 0 = Patch validation PASSED
   - Exit 1 = Patch validation FAILED (check output for details)
4. **Report results** with specific failure info (which check failed, why)

### For Test Output Parsing

**Lint output:**
- Success: "All checks passed!" and "X files left unchanged"
- Failure: ruff will list files with violations

**Mypy output:**
- Success: "Success: no issues found in X source files"
- Failure: mypy will list files with type errors

**Test output:**
- Success: "X passed" at end of pytest output
- Failure: "X failed, X passed" or "FAILED" markers in output

### For Single Test Execution

If a patch touches `tests/unit/test_s3.py`, can run just that file:

```bash
tox -e test -- tests/unit/test_s3.py -v
```

Or use the tox virtualenv directly:

```bash
.tox/test/bin/pytest tests/unit/test_s3.py -v
```

---

## Additional Context

### Project Purpose

Llama Stack Post Training Provider using KubeFlow Pipelines. Demonstrates how KFP pipelines using `torchtune` can define training workloads for both local and remote execution.

### Dependencies

**Core dependencies:**
- llama-stack >= 0.2.5
- kfp (KubeFlow Pipelines)
- torchtune == 0.5.0
- torchao == 0.8.0
- torch
- kubernetes
- boto3

**Dev dependencies (via tox):**
- ruff (linting/formatting)
- mypy (type checking)
- boto3-stubs (mypy type stubs)
- pytest (testing)
- moto[s3] (AWS mocking)

### Python Version

**Required:** >= 3.10 (specified in pyproject.toml)
**Used in CI:** 3.11 (all workflows)
**Containerfile:** python:3.11-slim

### Configuration Files

- `pyproject.toml` — Project metadata, dependencies, mypy config
- `tox.ini` — Tox environments (lint, mypy, test), pytest config
- `.github/workflows/*.yml` — CI configuration

---

**End of Test Context**
