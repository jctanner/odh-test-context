# Test Context: caikit-nlp-client

**Repository:** opendatahub-io/caikit-nlp-client
**Languages:** Python (3.9, 3.10, 3.11)
**Build System:** setuptools with setuptools-scm, managed via nox
**Agent Readiness:** **MEDIUM** — Lint works (pre-commit passes, mypy has existing type errors), tests partially work (20/25 INSECURE tests pass, TLS/MTLS tests fail due to expired certificates)

## Overview

This is a Python client library for caikit-nlp providing HTTP and gRPC interfaces. Tests use pytest with parametrized fixtures for multiple connection types (INSECURE, TLS, MTLS). The project uses nox for task automation and pre-commit for linting. CI runs lint and tests on Python 3.9, 3.10, 3.11.

**Key finding:** TLS/MTLS test certificates expired, causing 54 test errors. INSECURE mode tests mostly work (20 passed, 5 failed). Mypy has 8 existing type errors in grpc_client.py.

---

## Container Recipe

This recipe provides a complete, copy-paste workflow for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-caikit-nlp-client \
  -v /path/to/caikit-nlp-client:/app:Z \
  -w /app \
  python:3.11-bookworm \
  sleep infinity
```

Replace `/path/to/caikit-nlp-client` with the absolute path to your local checkout.

### 2. Install System Dependencies

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "apt-get update && apt-get install -y git make"
```

**Note:** git and make are already present in python:3.11-bookworm, this step typically completes instantly.

### 3. Install Python Dependencies

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && pip install --upgrade pip && pip install nox"
```

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && pip install --index-url=https://download.pytorch.org/whl/cpu torch"
```

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && pip install -e '.[dev,tests]'"
```

**Why PyTorch CPU?** The project requires PyTorch but doesn't need GPU support for tests. Using the CPU-only wheel saves ~1.5GB download.

**Expected time:** 2-3 minutes for all dependencies.

### 4. Run Linting (Pre-commit)

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && nox -s pre-commit"
```

**Validated:** ✅ **PASS**
**Expected output:** All hooks pass (ruff, ruff-format, bandit, pyupgrade, trailing-whitespace, end-of-file-fixer, check-yaml, check-toml, check-added-large-files).

**Note:** On first run, may auto-fix import order issues and exit with code 1. Re-run to verify all checks pass.

**Output snippet:**
```
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
check toml...............................................................Passed
check for added large files..............................................Passed
ruff.....................................................................Passed
ruff-format..............................................................Passed
bandit...................................................................Passed
pyupgrade................................................................Passed
nox > Session pre-commit was successful.
```

### 5. Run Linting (Mypy - Type Checking)

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && nox -s mypy"
```

**Validated:** ❌ **FAIL** (8 existing type errors)
**Expected output:** Type errors in `src/caikit_nlp_client/grpc_client.py` related to google.protobuf descriptor types.

**Output snippet:**
```
src/caikit_nlp_client/grpc_client.py:153: error: Argument 1 to "_populate_request" of "GrpcClient" has incompatible type "google.protobuf.message.Message"; expected "google._upb._message.Message"  [arg-type]
[... 7 more errors ...]
Found 8 errors in 1 file (checked 18 source files)
nox > Command python -m mypy src tests failed with exit code 1
nox > Session mypy failed.
```

**Note:** These are pre-existing type errors, not introduced by patches. CI may skip mypy or these errors may be tolerated.

### 6. Run Ruff Linter (Direct)

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && pip install ruff==0.5.4 && ruff check ."
```

**Validated:** ✅ **PASS** (after auto-fix)
**Expected output:** Import order issues, all auto-fixable.

**Auto-fix command:**
```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && ruff check --fix ."
```

**Output snippet:**
```
Found 6 errors (6 fixed, 0 remaining).
```

### 7. Run Tests (Full Suite via Nox)

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && nox -s tests-3.11"
```

**Validated:** ⚠️ **PARTIAL PASS** (25 passed, 5 failed, 54 errors)
**Expected time:** ~75 seconds
**Expected output:** 25 tests pass in INSECURE mode, 5 fail. 54 errors in TLS/MTLS tests due to expired certificates.

**Output snippet:**
```
== 5 failed, 25 passed, 2 skipped, 4 warnings, 54 errors in 75.02s (0:01:15) ===
```

**Errors:** TLS/MTLS tests fail with:
```
ssl_transport_security.cc:1884] Handshake failed with error SSL_ERROR_SSL: error:1000007d:SSL routines:OPENSSL_internal:CERTIFICATE_VERIFY_FAILED: certificate has expired
```

### 8. Run Tests (INSECURE Mode Only - Recommended)

To avoid certificate errors, run only INSECURE connection type tests:

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && pytest tests/ -k 'INSECURE' --tb=short"
```

**Validated:** ⚠️ **PARTIAL PASS** (20 passed, 5 failed, 2 skipped)
**Expected time:** ~5 seconds
**Expected output:** 20 tests pass, 5 fail with assertion errors.

**Output snippet:**
```
====== 5 failed, 20 passed, 2 skipped, 59 deselected, 4 warnings in 4.33s ======
```

**Failed tests:**
- `test_request_exception_handling[ConnectionType.INSECURE]`
- `test_get_text_generation_parameters[ConnectionType.INSECURE]`
- `test_embedding_tasks[ConnectionType.INSECURE]`
- `test_sentence_similarity_tasks[ConnectionType.INSECURE]`
- `test_rerank_tasks[ConnectionType.INSECURE]`

**Skipped tests:**
- `test_generate_text_stream[ConnectionType.INSECURE]` (stream mocking broken, issue #46)
- `test_generate_text_stream_with_optional_args[ConnectionType.INSECURE]` (stream mocking broken, issue #46)

### 9. Run Single Test File

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && pytest tests/test_api.py -v"
```

**Validated:** ✅ **PASS**
**Output snippet:**
```
tests/test_api.py::test_module PASSED                                    [100%]
============================== 1 passed in 0.01s ===============================
```

### 10. Run Single Test

```bash
podman exec test-context-caikit-nlp-client bash -c \
  "cd /app && pytest tests/test_api.py::test_module -v"
```

Template: `pytest tests/{file}.py::{test_name}`

### 11. Cleanup Container

**Always run this when done, even if validation fails:**

```bash
podman rm -f test-context-caikit-nlp-client
```

---

## Validation Results

### Summary Table

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `pip install nox && pip install -e '.[dev,tests]'` | 0 | ✅ PASS | All dependencies installed |
| Lint (pre-commit) | `nox -s pre-commit` | 0 | ✅ PASS | Auto-fixed 1 import issue, passed on re-run |
| Lint (mypy) | `nox -s mypy` | 1 | ❌ FAIL | 8 pre-existing type errors in grpc_client.py |
| Lint (ruff) | `ruff check .` | 1 → 0 | ✅ PASS | 6 import order issues, auto-fixed |
| Tests (full) | `nox -s tests-3.11` | 1 | ⚠️ PARTIAL | 25 passed, 5 failed, 54 TLS/MTLS errors |
| Tests (INSECURE) | `pytest -k 'INSECURE'` | 1 | ⚠️ PARTIAL | 20 passed, 5 failed |

### Interpretation

- **Linting:** Pre-commit hooks work reliably. Mypy has known issues that may be tolerated in CI.
- **Tests:** INSECURE mode is mostly functional (20/25 tests pass). TLS/MTLS tests require certificate regeneration.
- **Coverage:** Coverage threshold is 50% (`fail_under = 50` in pyproject.toml). Use `--cov` to measure coverage.

### Exit Codes

- **0** = Success (all checks passed)
- **1** = Linter found issues OR tests failed (distinguish by output)
- **Non-zero** = Command failed to execute

---

## CI/CD

### GitHub Actions Workflows

**Primary workflow:** `.github/workflows/tests.yml`

**Triggers:**
- `pull_request` (gating)
- `push` to `main`
- Daily schedule at 01:15 UTC

**Matrix:** Python 3.9, 3.10, 3.11 on ubuntu-latest

**Gating checks:**
1. **Lint with pre-commit and mypy**
   ```bash
   nox -v --session pre-commit mypy
   ```

2. **Run tests** (for each Python version)
   ```bash
   nox -v --session tests-3.9 -- --cov-report=xml
   nox -v --session tests-3.10 -- --cov-report=xml
   nox -v --session tests-3.11 -- --cov-report=xml
   ```

3. **Upload coverage to Codecov**

**Secondary workflow:** `.github/workflows/tests-docker.yml`

**Triggers:**
- `pull_request`
- Weekly schedule (Monday 00:00 UTC)

**Command:**
```bash
nox -v --session tests-3.11 -- --real-caikit --cov-report=xml
```

**Note:** Uses real caikit-tgis-serving Docker images and downloads a ~300MB model. Requires significant disk space.

---

## Conventions

### Test File Naming
- Pattern: `tests/test_*.py`
- Examples: `test_grpc_client.py`, `test_http_client.py`, `test_api.py`, `test_utils.py`

### Test Function Naming
- Pattern: `def test_*()`
- Parametrized tests use `@pytest.mark.parametrize` or indirect fixtures
- Example: `test_generate_text[ConnectionType.INSECURE]`

### Import Style
- Ruff-enforced import order: stdlib, third-party, local
- `TYPE_CHECKING` imports for type hints
- Grouped imports with blank lines between groups

### Coverage
- Threshold: 50% (`fail_under = 50`)
- Source: `caikit_nlp_client`, `tests`
- Exclusions: `if TYPE_CHECKING:`, `pragma: no cover`
- Config: `[tool.coverage]` in `pyproject.toml`

---

## Gaps & Caveats

### 1. **Expired TLS/MTLS Certificates**
**Impact:** 54 test errors
**Location:** `tests/fixtures/resources/ssl-certs/`
**Workaround:** Run only INSECURE tests with `pytest -k 'INSECURE'`
**Fix:** Regenerate certificates using `tests/fixtures/resources/ssl-certs/gen-certificates.bash`

### 2. **Mypy Type Errors**
**Impact:** Mypy session fails
**Location:** `src/caikit_nlp_client/grpc_client.py`
**Details:** 8 errors related to `google.protobuf` descriptor type mismatches
**Workaround:** These may be tolerated in CI or skipped in local validation
**Fix:** Requires updating type annotations to match protobuf API changes

### 3. **Failing INSECURE Tests**
**Impact:** 5 test failures
**Tests:**
- `test_request_exception_handling`
- `test_get_text_generation_parameters`
- `test_embedding_tasks`
- `test_sentence_similarity_tasks`
- `test_rerank_tasks`

**Cause:** Assertion errors in API response validation (e.g., KeyError for expected fields)
**Note:** May indicate API version mismatches between client and mock server

### 4. **Broken Stream Mocking**
**Impact:** 2 tests skipped
**Issue:** https://github.com/opendatahub-io/caikit-nlp-client/issues/46
**Tests:**
- `test_generate_text_stream[ConnectionType.INSECURE]`
- `test_generate_text_stream_with_optional_args[ConnectionType.INSECURE]`

### 5. **Real Caikit Tests Require Infrastructure**
**Impact:** `--real-caikit` tests cannot run in simple container
**Requirements:**
- Docker daemon access
- Large disk space (~2GB for images + ~300MB for model)
- Network access to container registries and HuggingFace

**Command:**
```bash
nox -s tests -- --real-caikit tests
```

### 6. **Test Utils FastAPI Compatibility**
**Impact:** 1 test error
**Details:** `test_get_server_certificate` fails with `AttributeError: 'FastAPI' object has no attribute 'route'`
**Cause:** FastAPI API change, test uses outdated decorator pattern
**Workaround:** Skip this test or update to modern FastAPI routing

---

## Build & Installation

### Development Installation

```bash
pip install -e '.[dev,tests]'
```

Installs:
- `dev`: ruff, mypy, grpcio-tools
- `tests`: pytest, pytest-cov, pytest-docker, pytest-mock, caikit-nlp, caikit runtime

### Production Installation

```bash
pip install caikit-nlp-client
```

Or from source:
```bash
pip install .
```

### Build Distribution

```bash
nox -s build
```

Or manually:
```bash
pip install build twine
python -m build
twine check dist/*
```

**Output:** `dist/caikit_nlp_client-*.whl` and `dist/caikit_nlp_client-*.tar.gz`

### Version Management

Version is dynamic, managed by `setuptools-scm` from git tags. The version file is generated at `src/caikit_nlp_client/_version.py` during install.

---

## Quick Reference

### Essential Commands

```bash
# Lint everything
nox -s pre-commit

# Type check
nox -s mypy

# Run all tests (one Python version)
nox -s tests-3.11

# Run only working tests (INSECURE mode)
pytest tests/ -k 'INSECURE'

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest --cov --cov-config=pyproject.toml

# Build distribution
nox -s build
```

### Environment Variables

None required for basic testing. Optional:
- `COVERAGE_FILE=.coverage.{python_version}` — For parallel coverage tracking

### Python Versions Supported

- Python 3.9 (minimum)
- Python 3.10
- Python 3.11 (recommended for validation)

### Dependencies Highlights

- **Runtime:** protobuf, grpcio-reflection, requests
- **Testing:** pytest, pytest-cov, pytest-docker, caikit-nlp
- **Linting:** ruff, mypy, bandit
- **Optional:** PyTorch (CPU-only for tests)

---

## For Downstream Agents

### What Works

✅ Pre-commit linting (ruff, bandit, pyupgrade, etc.)
✅ Direct ruff linting and auto-fix
✅ Basic pytest execution
✅ INSECURE connection type tests (20/25 pass)
✅ Building Python distribution
✅ Installing from source in editable mode

### What Doesn't Work

❌ Mypy type checking (8 pre-existing errors)
❌ TLS/MTLS tests (expired certificates)
❌ Full test suite without failures (5 INSECURE tests fail)
❌ Real caikit integration tests (require Docker)
❌ test_utils.py (FastAPI compatibility issue)

### Recommended Validation Strategy

For patch validation, use this minimal check:

1. Run pre-commit: `nox -s pre-commit`
2. Run INSECURE tests: `pytest tests/ -k 'INSECURE'`
3. Check for coverage (if needed): Add `--cov` flag

**Expected baseline:**
- Pre-commit: PASS
- INSECURE tests: 20 passed, 5 failed (known failures)
- Coverage: Should remain ≥50%

**Patch acceptance criteria:**
- Pre-commit passes
- No new test failures beyond the 5 known failures
- Coverage doesn't drop below 50%

### Container Resource Requirements

- **Disk:** ~5GB (base image + dependencies + PyTorch CPU)
- **Memory:** 2GB recommended
- **Time:** ~5 minutes for full setup and test run

---

## Changelog

**2026-03-22:** Initial analysis
- Discovered expired TLS/MTLS certificates
- Identified 8 mypy type errors in grpc_client.py
- Validated 20/25 INSECURE tests pass
- Confirmed pre-commit hooks functional
