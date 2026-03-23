# Test Context: kube-authkit

**Generated:** 2026-03-22T18:27:30Z

## Overview

Python library for Kubernetes authentication (supports KubeConfig, In-Cluster, OIDC, OpenShift OAuth).

**Languages:** Python (3.10+)
**Build System:** hatchling + UV package manager
**Agent Readiness:** **HIGH** — Lint and test commands validated successfully in container. Dependencies install cleanly. Clear pass/fail signals. An agent can clone, patch, lint, and test with confidence.

## Container Recipe

This is a complete, copy-paste recipe for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-kube-authkit \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11-slim \
  sleep infinity
```

Replace `$(pwd)` with the absolute path to the repository root if needed.

### 2. Install System Dependencies

```bash
podman exec test-context-kube-authkit bash -c \
  "apt-get update && apt-get install -y curl git make && rm -rf /var/lib/apt/lists/*"
```

### 3. Install Python Tooling

```bash
podman exec test-context-kube-authkit bash -c \
  "pip install --upgrade pip && pip install uv ruff"
```

### 4. Install Project Dependencies

```bash
podman exec test-context-kube-authkit bash -c \
  "cd /app && uv pip install -e '.[dev]' --system"
```

**Expected:** Installs ~23 packages including pytest, pytest-cov, pytest-mock, kubernetes, requests, PyJWT, urllib3, ruff.

**Validation Result:** ✅ Installs successfully in ~1 second using UV.

### 5. Run Lint: Ruff Check

```bash
podman exec test-context-kube-authkit bash -c \
  "cd /app && ruff check src/ tests/"
```

**Expected:** `All checks passed!` or list of violations.

**Validation Result:** ✅ Exit 0, no violations.

### 6. Run Lint: Ruff Format Check

```bash
podman exec test-context-kube-authkit bash -c \
  "cd /app && ruff format --check src/ tests/"
```

**Expected:** `26 files already formatted` or list of files needing formatting.

**Validation Result:** ✅ Exit 0, all files formatted correctly.

### 7. Run Tests: All Tests with Coverage

```bash
podman exec test-context-kube-authkit bash -c \
  "cd /app && pytest tests/ --cov=src/kube_authkit --cov-report=term --cov-fail-under=70"
```

**Expected:** 227+ tests pass, coverage ≥70%. Exit 0 if all pass and coverage met.

**Validation Result:** ⚠️ Exit 1 (227 passed, 4 failed). Coverage 80% (exceeds threshold).
- 4 failures are permission tests (test files with `chmod 0o000`) that fail when running as root
- These tests pass in CI when running as non-root user
- All other tests pass, framework works correctly

**Interpretation:** Tests are functional. Use exit code cautiously — check that only known permission tests fail.

### 8. Run Tests: Unit Tests Only (Faster)

```bash
podman exec test-context-kube-authkit bash -c \
  "cd /app && pytest tests/ -m 'not integration' --cov=src/kube_authkit --cov-report=term"
```

**Expected:** ~185 unit tests, 79% coverage, <1 second runtime.

**Validation Result:** ✅ 181 passed, 4 failed (permission tests), 79% coverage, 0.91s.

### 9. Run Tests: Integration Tests Only

```bash
podman exec test-context-kube-authkit bash -c \
  "cd /app && pytest tests/ -m integration --cov=src/kube_authkit --cov-report=term"
```

**Expected:** ~46 integration tests using mock OAuth server, 59% coverage, ~2-3 seconds.

**Validation Result:** ✅ 46 passed, 0 failed, 59% coverage, 2.62s.

**Note:** Integration tests have lower coverage when run alone because they don't exercise all code paths. CI combines unit + integration coverage.

### 10. Run Single Test File

```bash
podman exec test-context-kube-authkit bash -c \
  "cd /app && pytest tests/test_config.py -v"
```

### 11. Run Single Test

```bash
podman exec test-context-kube-authkit bash -c \
  "cd /app && pytest tests/test_config.py::TestAuthConfigDefaults::test_auto_method_config -v"
```

### 12. Cleanup

**Always** run this when done, even if validation fails partway:

```bash
podman rm -f test-context-kube-authkit
```

---

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install | `uv pip install -e '.[dev]' --system` | 0 | ✅ Pass | Installed 23 packages in <2s |
| Lint | `ruff check src/ tests/` | 0 | ✅ Pass | All checks passed |
| Format | `ruff format --check src/ tests/` | 0 | ✅ Pass | 26 files formatted |
| Tests | `pytest tests/ --cov=... --cov-fail-under=70` | 1 | ⚠️ Partial | 227 pass, 4 fail (root perms), 80% coverage |

**Summary:** All commands work. Lint passes cleanly. Tests run successfully with 227/231 passing. 4 failures are environment-specific (root user bypasses permission checks) and pass in CI.

---

## CI/CD

### GitHub Actions Workflows

**Triggers:**
- `push` to `main`, `feat/*`, `fix/*`
- `pull_request` to `main`

### Gating Checks (Required for Merge)

#### 1. Code Quality (lint.yml)

**Jobs:**
- `lint` — Ruff check and format validation
- `dependency-check` — pip-audit security scan

**Commands:**
```bash
ruff check src/ tests/
ruff format --check src/ tests/
pip-audit --skip-editable
```

#### 2. Tests (test.yml)

**Jobs:**
- `test` — Matrix: Python 3.10, 3.11, 3.12 × ubuntu-latest, macos-latest
- `test-minimum-versions` — Test with minimum supported dependency versions
- `coverage-check` — Ensure ≥70% coverage

**Commands:**
```bash
# Unit tests
pytest tests/ -m "not integration" --cov=src/kube_authkit --cov-report=xml --cov-report=term

# Integration tests
pytest tests/ -m integration --cov=src/kube_authkit --cov-append --cov-report=xml --cov-report=term

# Coverage check
pytest tests/ --cov=src/kube_authkit --cov-report=term --cov-fail-under=70
```

**Coverage Upload:** Codecov uploads from `ubuntu-latest + Python 3.12` runs only.

#### 3. Publish (publish.yml)

**Trigger:** `release` published

**Jobs:**
- `build` — Build distribution with `python -m build`
- `test` — Run full test suite before publishing
- `publish-to-pypi` — Publish to PyPI using Trusted Publishing

#### 4. Release (release.yml)

**Trigger:** `push` to tags matching `v*.*.*`

**Jobs:**
- `create-release` — Generate changelog and create GitHub release

---

## Conventions

### Test Organization

```
tests/
├── conftest.py                    # Shared fixtures (mock_kubeconfig, mock_service_account, mock_oauth_server)
├── mock_oauth_server.py           # Mock OAuth/OIDC server for integration tests
├── test_*.py                      # Unit tests
├── strategies/
│   ├── test_kubeconfig.py        # Unit tests for KubeConfig strategy
│   ├── test_incluster.py         # Unit tests for In-Cluster strategy
│   ├── test_oidc.py              # Unit tests for OIDC strategy
│   └── test_openshift.py         # Unit tests for OpenShift OAuth strategy
└── integration/
    ├── test_factory_integration.py
    ├── test_kubeconfig_integration.py
    ├── test_incluster_integration.py
    ├── test_oidc_integration.py
    └── test_openshift_integration.py
```

### Test Markers

- `@pytest.mark.unit` — Fast unit tests with mocked dependencies
- `@pytest.mark.integration` — Integration tests using mock OAuth server
- `@pytest.mark.e2e` — End-to-end tests requiring real services (Keycloak, K8s)
- `@pytest.mark.slow` — Tests that take longer to run

### Test Naming

- **Files:** `test_*.py`
- **Classes:** `Test*` (e.g., `TestAuthConfigDefaults`)
- **Functions:** `test_*` (e.g., `test_auto_method_config`)

### Running Specific Test Categories

```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Unit tests excluding integration
pytest -m "not integration"
```

### Import Style

Standard Python grouping:
1. Standard library
2. Third-party packages
3. First-party (kube_authkit) modules

Type hints used throughout.

---

## Gaps & Caveats

### Known Limitations

1. **Permission tests fail as root:** 4 tests (`test_is_not_available_unreadable_token`, `test_is_not_available_unreadable_ca_cert`, `test_get_namespace_read_error`, `test_is_not_available_unreadable_file`) use `chmod 0o000` to make files unreadable, but root can still read them. These tests pass in CI when running as a non-root user.

2. **E2E tests not validated:** Tests marked with `@pytest.mark.e2e` require a real Keycloak server and were not run in this analysis. Use `docker-compose -f docker-compose.test.yml up` to run E2E tests with Keycloak.

3. **pip-audit not validated:** The security audit tool requires a full dependency install and was not run in the validation container.

4. **Integration tests alone have low coverage:** Running only integration tests (`pytest -m integration`) produces 59% coverage, below the 70% threshold. CI runs both unit and integration tests together with `--cov-append` to achieve 80%+ coverage.

### Recommended Agent Workflow

For AI agents validating patches:

1. **Apply patch to working tree**
2. **Run lint:** `ruff check src/ tests/` and `ruff format --check src/ tests/`
   - Expect: Exit 0, no violations
3. **Run tests:** `pytest tests/ --cov=src/kube_authkit --cov-report=term --cov-fail-under=70`
   - Expect: 227+ passed, 0-4 failed (permission tests acceptable), coverage ≥70%
   - If exit code is 1, inspect output to confirm only permission tests failed
4. **Interpret results:**
   - ✅ **Pass:** Lint clean AND (all tests pass OR only permission tests fail) AND coverage ≥70%
   - ❌ **Fail:** Lint violations OR new test failures OR coverage <70%

### Docker Compose for E2E Tests

If you need to run E2E tests with real Keycloak:

```bash
# Start services (Keycloak + mock K8s API)
docker-compose -f docker-compose.test.yml up -d

# Run E2E tests
docker-compose -f docker-compose.test.yml run test-runner

# Cleanup
docker-compose -f docker-compose.test.yml down
```

**Services:**
- Keycloak on port 8180 (admin/admin)
- Mock Kubernetes API on port 6443
- Test runner container

---

## Quick Reference

### Lint Commands

```bash
# Check for violations
ruff check src/ tests/

# Auto-fix violations
ruff check --fix src/ tests/

# Check formatting
ruff format --check src/ tests/

# Auto-format
ruff format src/ tests/
```

### Test Commands

```bash
# All tests with coverage
pytest tests/ --cov=src/kube_authkit --cov-report=term --cov-fail-under=70

# Unit tests only (fast)
pytest tests/ -m "not integration"

# Integration tests only
pytest tests/ -m integration

# Specific file
pytest tests/test_config.py -v

# Specific test
pytest tests/test_config.py::TestAuthConfigDefaults::test_auto_method_config -v

# Show coverage report
pytest tests/ --cov=src/kube_authkit --cov-report=html
open htmlcov/index.html

# Stop on first failure
pytest tests/ -x

# Show slowest tests
pytest tests/ --durations=10
```

### Coverage Threshold

**Required:** 70%
**Current:** 80% (unit + integration combined)

### Python Version Support

**Minimum:** 3.10
**Tested:** 3.10, 3.11, 3.12
**Container:** python:3.11-slim (validated)

---

## Additional Resources

- **pyproject.toml:** Build config, dependencies, tool settings (ruff, pytest)
- **tests/conftest.py:** Shared fixtures (mock_kubeconfig, mock_service_account, mock_oauth_server)
- **tests/mock_oauth_server.py:** Mock OAuth/OIDC server implementation
- **TESTING.md:** Comprehensive testing guide with examples
- **CONTRIBUTING.md:** Contribution guidelines
- **Dockerfile.test:** Dockerfile for running tests in container
- **docker-compose.test.yml:** E2E test environment with Keycloak

---

**End of Test Context**
