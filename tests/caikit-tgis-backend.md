# Test Context: caikit-tgis-backend

## Overview

**Repository:** opendatahub-io/caikit-tgis-backend
**Language:** Python
**Build System:** setuptools with setuptools_scm
**Agent Readiness:** **HIGH** - All lint and test commands validated successfully in container. No external infrastructure required.

This is a Python library providing a Caikit module backend for models running in TGIS (Text Generation Inference Service). The project has comprehensive test coverage (88%), well-configured linting (pylint 10/10), and automated formatting checks. All validation commands work cleanly in a standard Python 3.9 container.

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d \
  --name test-context-caikit-tgis-backend \
  -v /path/to/caikit-tgis-backend:/app:Z \
  -w /app \
  python:3.9 \
  sleep infinity
```

Note: Replace `/path/to/caikit-tgis-backend` with the actual repository path. Git and make are pre-installed in python:3.9.

### 2. Install Dependencies

```bash
# Upgrade pip
podman exec test-context-caikit-tgis-backend bash -c "cd /app && python -m pip install --upgrade pip"

# Install tox and build tools
podman exec test-context-caikit-tgis-backend bash -c "cd /app && pip install -r setup_requirements.txt"

# Install package in editable mode (for direct pytest usage)
podman exec test-context-caikit-tgis-backend bash -c "cd /app && pip install -e ."
```

### 3. Run Linting

#### Format Check (prettier, black, isort)

```bash
podman exec test-context-caikit-tgis-backend bash -c "cd /app && tox -e fmt"
```

**Validated:** ✅ SUCCESS - All formatters (prettier, black, isort) passed

#### Pylint

```bash
podman exec test-context-caikit-tgis-backend bash -c "cd /app && tox -e lint"
```

**Validated:** ✅ SUCCESS - Code rated 10.00/10 by pylint

### 4. Run Tests

#### Full Test Suite

```bash
podman exec test-context-caikit-tgis-backend bash -c "cd /app && tox -e 3.9"
```

**Validated:** ✅ SUCCESS - 50 passed, 1 skipped in 13.36s with 88% coverage

#### Single Test File

```bash
podman exec test-context-caikit-tgis-backend bash -c "cd /app && python -m pytest tests/test_tgis_connection.py"
```

**Validated:** ✅ SUCCESS - 11 tests passed in 0.89s

#### Single Test Function

```bash
podman exec test-context-caikit-tgis-backend bash -c "cd /app && python -m pytest tests/test_tgis_connection.py::test_happy_path_no_tls -v"
```

**Validated:** ✅ SUCCESS - 1 test passed in 0.29s

### 5. Cleanup

```bash
podman rm -f test-context-caikit-tgis-backend
```

## Validation Results

All commands were validated in a live container environment:

| Step | Command | Result | Details |
|------|---------|--------|---------|
| Install | `pip install -r setup_requirements.txt` | ✅ PASS | Installed tox, build, and all dependencies |
| Format | `tox -e fmt` | ✅ PASS | prettier, black, isort all passed |
| Lint | `tox -e lint` | ✅ PASS | pylint rated code 10.00/10 (501 statements analyzed) |
| Test | `tox -e 3.9` | ✅ PASS | 50 passed, 1 skipped, 88% coverage |
| Single File | `pytest tests/test_tgis_connection.py` | ✅ PASS | 11 passed in 0.89s |
| Single Test | `pytest {file}::{test}` | ✅ PASS | 1 passed in 0.29s |

**Coverage Report:**
- caikit_tgis_backend/__init__.py: 100%
- load_balancing_proxy.py: 96%
- tgis_connection.py: 98%
- tgis_backend.py: 92%
- managed_tgis_subprocess.py: 84%
- **Overall: 88%**

## CI/CD

### Workflows

**1. Lint and Format** (`.github/workflows/lint-code.yml`)
- **Trigger:** pull_request, push to main
- **Python Version:** 3.9
- **Gating:** Yes
- **Commands:**
  ```bash
  python -m pip install --upgrade pip
  python -m pip install -r setup_requirements.txt
  tox -e fmt
  tox -e lint
  ```

**2. Build and Test** (`.github/workflows/build-library.yml`)
- **Trigger:** pull_request, push to main
- **Python Versions:** 3.8, 3.9, 3.10, 3.11 (matrix)
- **Gating:** Yes (all versions)
- **Commands:**
  ```bash
  python -m pip install --upgrade pip
  python -m pip install -r setup_requirements.txt
  tox -e ${{ matrix.python-version }}
  ```

### Gating Checks

All of the following must pass for PR merge:
1. ✅ Format check (`tox -e fmt`)
2. ✅ Pylint (`tox -e lint`)
3. ✅ Tests on Python 3.8
4. ✅ Tests on Python 3.9
5. ✅ Tests on Python 3.10
6. ✅ Tests on Python 3.11

## Conventions

### Test Files
- **Location:** `tests/` directory
- **Naming:** `test_*.py` (e.g., `test_tgis_backend.py`, `test_tgis_connection.py`)
- **Fixtures:** Defined in `tests/conftest.py`
- **Mocks:** `tests/tgis_mock.py` provides TGISMock server for gRPC testing

### Test Functions
- **Naming:** `test_*` (e.g., `test_happy_path_no_tls`, `test_load_prompt_artifacts_ok`)
- **Framework:** pytest with pytest-cov for coverage
- **Markers:** Tests can be skipped with `@pytest.mark.skip`

### Import Style
Configured via `.isort.cfg` with black profile:
- **Groups (in order):**
  1. Future
  2. Standard library
  3. Third Party
  4. First Party (caikit, alog, aconfig, py_to_proto, import_tracker)
  5. Local (caikit_tgis_backend, tests)
- **Headers:** Each group has a comment header (e.g., `# Standard`, `# Third Party`)

### Code Style
- **Formatter:** black (line length 100)
- **Import Sorter:** isort (black-compatible profile)
- **Linter:** pylint with `.pylintrc` configuration
- **Naming:**
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`

### Coverage
- **Config:** `.coveragerc`
- **Excludes:** `caikit_tgis_backend/protobufs/*` and `tests/**` from coverage reports
- **Current:** 88% overall coverage
- **No explicit threshold:** No minimum coverage enforcement configured

## Linting Tools

### 1. Pylint
- **Config:** `.pylintrc`
- **Run:** `tox -e lint` or `pylint caikit_tgis_backend`
- **Scope:** Full project (`caikit_tgis_backend/` directory, excludes `protobufs/`)
- **Disabled checks:** Many docstring and style checks disabled for flexibility
- **Python version:** 3.9+
- **Result:** Code currently rated 10.00/10

### 2. Black
- **Config:** `.pre-commit-config.yaml` (rev: 22.3.0)
- **Run:** `tox -e fmt` or `pre-commit run black --all-files`
- **Excludes:** Generated protobuf files (`*_pb2.py`, `*_pb2_grpc.py`)
- **Auto-fix:** Yes - black reformats files in place

### 3. isort
- **Config:** `.isort.cfg`
- **Run:** `tox -e fmt` or `pre-commit run isort --all-files`
- **Profile:** black (compatible with black formatting)
- **Excludes:** Generated protobuf files
- **Auto-fix:** Yes - isort reorders imports in place

### 4. Prettier
- **Config:** `.prettierrc.yaml`
- **Run:** `tox -e fmt` or `pre-commit run prettier --all-files`
- **Scope:** Markdown, YAML, JSON files
- **Auto-fix:** Yes - prettier reformats files in place

## Testing

### Framework
- **Tool:** pytest (>=6.2.5, <7.0)
- **Plugins:** pytest-cov, pytest-html
- **Config:** Defined in `pyproject.toml` (if any) and `tox.ini`

### Test Dependencies
Required packages (from `tox.ini`):
- pytest>=6.2.5,<7.0
- pytest-cov>=2.10.1,<3.0
- pytest-html>=3.1.1,<4.0
- tls_test_tools>=0.1.1
- grpcio-tools>=1.35.0,<2.0
- Flask>=2.2.3,<3

### Environment Variables
Optional environment variables for logging control (configured in `conftest.py`):
- `LOG_LEVEL` (default: "off")
- `LOG_FILTERS` (default: "urllib3:off")
- `LOG_THREAD_ID` (default: false)
- `LOG_FORMATTER`
- `LOG_CHANNEL_WIDTH`

### Test Structure
- **Unit tests:** No external services required - uses mocks
- **Fixtures:** `tests/conftest.py` configures global test setup (logging)
- **Mocks:** `tests/tgis_mock.py` provides:
  - `TGISMock` - Base mock TGIS server
  - `tgis_mock_insecure` - Fixture for insecure gRPC
  - `tgis_mock_tls` - Fixture for TLS gRPC
  - `tgis_mock_mtls` - Fixture for mTLS gRPC
  - `tgis_mock_insecure_health_delay` - Fixture for delayed health checks

### Running Tests

**Via tox (recommended):**
```bash
tox -e 3.9              # Run all tests with Python 3.9
tox -e 3.8              # Run all tests with Python 3.8
```

**Direct pytest (after installing package):**
```bash
# All tests with coverage
pytest --cov=caikit_tgis_backend --cov-report=term --cov-report=html tests

# Single file
pytest tests/test_tgis_connection.py

# Single test
pytest tests/test_tgis_connection.py::test_happy_path_no_tls

# Verbose output
pytest -v tests/

# Show test durations
pytest --durations=10 tests/
```

## Build System

### Configuration
- **Tool:** setuptools with setuptools_scm
- **Config:** `pyproject.toml`
- **Version Management:** Git tags via setuptools_scm
- **Version File:** Auto-generated to `caikit_tgis_backend/_version.py`

### Build Commands

**Via tox:**
```bash
tox -e build          # Creates wheel in dist/
tox -e twinecheck     # Validates wheel with twine
```

**Direct build:**
```bash
python -m build       # Creates both wheel and sdist
```

### Dependencies
**Runtime:**
- caikit>=0.16.0,<0.24.0
- grpcio>=1.35.0,<2.0
- requests>=2.28.2,<3

**Build:**
- setuptools>=60
- setuptools-scm>=8.0
- build>=0.10.0,<2.0

## Gaps & Caveats

**None identified.** This project has excellent test infrastructure:

✅ Comprehensive test coverage (88%)
✅ All tests use mocks - no external infrastructure needed
✅ Clear CI configuration
✅ Well-documented linting setup
✅ All commands validated successfully in container
✅ Works with standard Python 3.9 base image
✅ Fast test execution (~13 seconds for full suite)

The project is **agent-ready for automated patch validation**.

## Quick Reference

**Install and test:**
```bash
pip install -r setup_requirements.txt
tox -e fmt              # Check formatting
tox -e lint             # Run pylint
tox -e 3.9              # Run tests with coverage
```

**Direct pytest (after `pip install -e .`):**
```bash
pytest tests/                                          # All tests
pytest tests/test_tgis_connection.py                   # Single file
pytest tests/test_tgis_connection.py::test_happy_path  # Single test
pytest --cov=caikit_tgis_backend tests/                # With coverage
```

**Build:**
```bash
tox -e build           # Build wheel
tox -e twinecheck      # Validate wheel
```

---

*Generated: 2026-03-22*
*Validation: All commands tested in python:3.9 container*
*Agent Readiness: HIGH*
