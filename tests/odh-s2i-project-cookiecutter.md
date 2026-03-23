# Test Context: odh-s2i-project-cookiecutter

**Generated**: 2026-03-22T19:44:23-04:00
**Repository**: opendatahub-io/odh-s2i-project-cookiecutter

## Overview

Cookiecutter template repository for creating OpenShift S2I-compatible data science projects. **Python** project using **pytest** for testing.

**Agent Readiness**: **MEDIUM** - Tests exist and run successfully, but no linting or CI/CD configured. Some tests fail due to template structure variations.

---

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-odh-s2i-project-cookiecutter \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

**Base Image**: `python:3.11`
**Working Directory**: `/app` (repository root bind-mounted)

### 2. Install Dependencies

```bash
podman exec test-context-odh-s2i-project-cookiecutter bash -c \
  "cd /app && pip install -r requirements.txt"
```

**Dependencies Installed**:
- pytest-9.0.2 (test framework)
- cookiecutter-2.7.1 (template engine)
- mkdocs-1.6.1 (documentation)
- mkdocs-cinder-1.2.0 (documentation theme)

**Expected**: Exit code 0, ~30 packages installed

### 3. Run All Tests

```bash
podman exec test-context-odh-s2i-project-cookiecutter bash -c \
  "cd /app && python -m pytest tests/ -v"
```

**Expected Results**:
- 18 tests collected
- 8 tests pass
- 10 tests fail (expected - see notes below)
- Exit code 1 (due to test failures)

**Note**: Test failures are expected because tests validate generated cookiecutter templates. Some tests expect `setup.py` files that only exist in certain template branches (e.g., the `cds` branch). The failures indicate template structure differences, not broken test infrastructure.

### 4. Run Single Test File

```bash
podman exec test-context-odh-s2i-project-cookiecutter bash -c \
  "cd /app && python -m pytest tests/test_creation.py -v"
```

Replace `tests/test_creation.py` with any test file path.

### 5. Run Single Test

```bash
podman exec test-context-odh-s2i-project-cookiecutter bash -c \
  "cd /app && python -m pytest tests/test_creation.py::TestCookieSetup::test_readme -v"
```

Replace `TestCookieSetup::test_readme` with the desired test class and method name.

### 6. Cleanup

```bash
podman rm -f test-context-odh-s2i-project-cookiecutter
```

Always run this after validation to remove the container.

---

## Validation Results

### Install Dependencies
- **Command**: `pip install -r requirements.txt`
- **Exit Code**: 0
- **Status**: ✅ SUCCESS
- **Output**: Successfully installed pytest-9.0.2, cookiecutter-2.7.1, and 30+ dependencies

### Run Tests
- **Command**: `python -m pytest tests/ -v`
- **Exit Code**: 1
- **Status**: ⚠️ PARTIAL (framework works, some tests fail as expected)
- **Results**: 18 tests collected, 8 passed, 10 failed
- **Output**:
  ```
  platform linux -- Python 3.11.15, pytest-9.0.2, pluggy-1.6.0
  collected 18 items

  tests/test_creation.py::TestCookieSetup::test_project_name PASSED
  tests/test_creation.py::TestCookieSetup::test_author FAILED
  tests/test_creation.py::TestCookieSetup::test_readme PASSED
  tests/test_creation.py::TestCookieSetup::test_setup FAILED
  ...
  ```

**Interpretation**: Test framework runs correctly. Failures occur because:
- Tests check for `setup.py` files in generated projects
- The default template (simple branch) doesn't include `setup.py`
- Different template branches have different structures
- This is expected behavior for a multi-branch cookiecutter template

---

## CI/CD

**Status**: ❌ No CI/CD configured

No GitHub Actions workflows, Tekton pipelines, Jenkins files, or other CI automation detected. The repository has no automated testing on pull requests or commits.

**Implication**: Patches cannot be automatically validated. Manual testing required.

---

## Linting

**Status**: ❌ No linting configured

No linter configuration files found:
- No `.flake8`
- No `ruff` configuration in `pyproject.toml`
- No `pylintrc` or `.pylintrc`
- No `mypy.ini` or mypy config
- No `.pre-commit-config.yaml`

**Implication**: Code style and quality are not automatically enforced.

---

## Testing Framework

**Framework**: pytest
**Test Directory**: `tests/`
**Test Files**:
- `tests/conftest.py` - pytest fixtures for template generation
- `tests/test_creation.py` - tests that validate generated cookiecutter projects

### How Tests Work

1. Tests use a `default_baked_project` fixture defined in `conftest.py`
2. Fixture generates cookiecutter projects in temporary directories
3. Tests verify the generated project structure:
   - Files exist (README.md, LICENSE, requirements.txt, etc.)
   - Jinja templates are fully rendered (no `{{` or `{%` remain)
   - Metadata is correct (author, license type, project name)
   - Directory structure matches expectations

### Test Conventions

- **File Pattern**: `test_*.py`
- **Class Pattern**: `TestXxx` classes with `@pytest.mark.usefixtures` decorator
- **Method Pattern**: `test_xxx` methods
- **Fixtures**: Parameterized fixtures in `conftest.py`

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Single file
python -m pytest tests/test_creation.py -v

# Single test
python -m pytest tests/test_creation.py::TestCookieSetup::test_readme -v

# With specific markers (none defined in this project)
python -m pytest -m <marker_name>
```

---

## Build & Setup

**Build System**: None (Cookiecutter template, not a buildable application)
**Install Command**: `pip install -r requirements.txt`
**Build Command**: N/A

This repository is a Cookiecutter template for generating other projects. It doesn't build an application itself.

---

## Conventions

### File Structure
```
.
├── cookiecutter.json           # Template variables
├── {{ cookiecutter.repo_name }}/  # Template directory
│   ├── *.py files              # Template Python files
│   ├── *.ipynb                 # Jupyter notebooks
│   └── README.md               # Template README
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest fixtures
│   └── test_creation.py        # Template validation tests
├── docs/                       # Documentation
├── requirements.txt            # Python dependencies
└── README.md                   # Project README
```

### Test Patterns
- Tests use pytest class-based organization
- Fixtures create temporary cookiecutter projects
- Tests validate generated output, not template source

### Import Style
- Standard Python imports
- Grouped: stdlib, third-party, local
- No special import conventions enforced

---

## Gaps & Caveats

### Missing Infrastructure
1. **No CI/CD** - No automated testing on PRs or commits
2. **No Linting** - No code quality enforcement
3. **No Coverage** - No test coverage measurement
4. **No Pre-commit Hooks** - No local validation before commits

### Test Limitations
1. **Some Tests Fail** - 10 out of 18 tests fail due to template branch differences
2. **Branch-Specific** - Tests may expect files from different template branches
3. **No Integration Tests** - Tests only validate template generation, not actual S2I builds

### Documentation Gaps
1. **No CONTRIBUTING.md** - No contributor guidelines
2. **No Development Setup** - README doesn't explain how to run tests
3. **Minimal Inline Docs** - Limited code comments

### Agent Validation Impact
- ✅ Can install dependencies
- ✅ Can run tests
- ⚠️ Cannot run linting (none configured)
- ⚠️ Cannot validate against CI checks (none configured)
- ⚠️ Test results may be ambiguous (expected failures vs. real failures)

---

## Recommendations for Patch Validation

When validating patches to this repository:

1. **Always run the full test suite** - Some tests may fail, but check that the failure count doesn't increase
2. **Check for new template files** - If a patch adds files to `{{ cookiecutter.repo_name }}/`, ensure they're properly templated
3. **Verify Jinja syntax** - Template files should use `{{ cookiecutter.variable }}` syntax correctly
4. **Test multiple branches** - This template has multiple branches (simple, cds) with different structures
5. **Manual validation recommended** - Since there's no CI, consider generating a project from the modified template and testing it manually

### Safe Patch Validation Workflow

```bash
# 1. Start container
podman run -d --name test-odh-s2i -v $(pwd):/app:Z -w /app python:3.11 sleep infinity

# 2. Install deps
podman exec test-odh-s2i bash -c "cd /app && pip install -r requirements.txt"

# 3. Run tests (baseline)
podman exec test-odh-s2i bash -c "cd /app && python -m pytest tests/ -v" > baseline.txt

# 4. Apply patch
# (patch application happens here)

# 5. Run tests again
podman exec test-odh-s2i bash -c "cd /app && python -m pytest tests/ -v" > patched.txt

# 6. Compare results
diff baseline.txt patched.txt

# 7. Cleanup
podman rm -f test-odh-s2i
```

---

## Summary

**Agent Readiness: MEDIUM**

- ✅ Tests exist and run
- ✅ Dependencies install cleanly
- ✅ Container recipe works
- ❌ No linting
- ❌ No CI/CD
- ⚠️ Some tests fail (expected)

**Bottom Line**: An agent can validate patches by running tests in a container, but should expect some baseline test failures. No automated linting or CI validation available. Manual review recommended for template syntax and structure changes.
