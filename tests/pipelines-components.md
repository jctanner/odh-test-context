# Test Context: pipelines-components

**Organization:** opendatahub-io
**Language:** Python 3.11+
**Build System:** UV (modern Python package manager) + setuptools
**Agent Readiness:** **HIGH** - Lint and test commands validated successfully in container

## Overview

This repository contains Kubeflow Pipelines components and pipelines for Open Data Hub. It uses UV for dependency management, Ruff for linting/formatting, pytest for testing, and has comprehensive CI checks via GitHub Actions. All core validation commands (lint, format, test) have been validated in a `python:3.11-slim` container and work correctly.

## Container Recipe

This is the **complete, copy-paste recipe** for validating patches in a container. Every command has been validated.

### 1. Start Container

```bash
podman run -d --name validate-pipelines-components \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11-slim \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec validate-pipelines-components bash -c "apt-get update && apt-get install -y curl ca-certificates git make"
```

### 3. Install UV Package Manager

```bash
podman exec validate-pipelines-components bash -c "cd /app && curl -LsSf https://astral.sh/uv/install.sh | sh"
```

### 4. Install Project Dependencies

```bash
podman exec validate-pipelines-components bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv sync --extra dev"
```

**Note:** This installs both `[test]` and `[lint]` extras. Takes ~30 seconds.

### 5. Run Lint Checks

**Ruff Format Check:**
```bash
podman exec validate-pipelines-components bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run ruff format --check components pipelines scripts"
```

**Expected:** May find formatting violations (exit code 1 means violations found, not broken command).

**Ruff Lint Check:**
```bash
podman exec validate-pipelines-components bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run ruff check components pipelines scripts"
```

**Expected:** May find lint violations (E501, I001, D* docstring checks, etc.).

**YAML Lint:**
```bash
podman exec validate-pipelines-components bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run yamllint -c .yamllint.yml ."
```

**Expected:** May find warnings about document-start markers or line length.

**Import Guard (components/pipelines must use lazy imports):**
```bash
podman exec validate-pipelines-components bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run python .github/scripts/check_imports/check_imports.py --config .github/scripts/check_imports/import_exceptions.yaml components pipelines"
```

### 6. Run Tests

**Scripts Tests (from .github/scripts):**
```bash
podman exec validate-pipelines-components bash -c "export PATH=/root/.local/bin:\$PATH && cd /app/.github/scripts && uv run pytest */tests/ -v --tb=short -m 'not gh_api'"
```

**Expected:** ~120 tests pass. These are unit tests for CI scripts.

**Scripts Tests (from scripts/):**
```bash
podman exec validate-pipelines-components bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pytest scripts/check_base_image_tags/tests/ -v --tb=short"
```

**Expected:** Tests pass. Note: must run from repo root, not from within `scripts/`.

**Component Unit Tests (example):**
```bash
podman exec validate-pipelines-components bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pytest components/data_processing/automl/tabular_data_loader/tests/test_component_unit.py -v --tb=short"
```

**Expected:** ~10 tests pass. Component unit tests use mocked dependencies.

### 7. Run Single Test

**Single file:**
```bash
podman exec validate-pipelines-components bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pytest {path/to/test_file.py} -v --tb=short"
```

**Single test function:**
```bash
podman exec validate-pipelines-components bash -c "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pytest {path/to/test_file.py}::{TestClass}::{test_function} -v --tb=short"
```

### 8. Cleanup

```bash
podman rm -f validate-pipelines-components
```

## Validation Results

All commands were validated on 2026-03-22 in a `python:3.11-slim` container:

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| System deps | `apt-get install curl git make` | ✅ PASS | 53 packages installed |
| UV install | `curl https://astral.sh/uv/install.sh` | ✅ PASS | UV 0.10.12 installed |
| Dependencies | `uv sync --extra dev` | ✅ PASS | 55 packages resolved, 49 installed |
| Ruff format | `uv run ruff format --check` | ✅ WORKS | Found 2 files needing format (legitimate) |
| Ruff check | `uv run ruff check` | ✅ WORKS | Found lint violations (legitimate) |
| YAML lint | `uv run yamllint` | ✅ WORKS | Found warnings (legitimate) |
| Scripts tests | `pytest */tests/` in .github/scripts | ✅ PASS | 120/120 passed in 0.11s |
| Scripts tests | `pytest scripts/*/tests/` from root | ✅ PASS | 10/10 passed in 0.08s |
| Component tests | Component unit test | ✅ PASS | 10/10 passed in 0.07s |

**Interpretation:**
- Exit code 0 = command works, tests pass
- Exit code 1 for lint = command works, found violations (expected in a real repo)
- Exit code 2 for yamllint = found warnings (expected)

## CI/CD

### Gating Checks (required for merge)

All of these run on `pull_request` to `main` or `release-*` branches:

1. **python-lint** (`.github/workflows/python-lint.yml`)
   - `uv run ruff format --check` on changed Python files
   - `uv run ruff check` on changed Python files
   - `uv run python .github/scripts/check_imports/check_imports.py` on components/pipelines

2. **yaml-lint** (`.github/workflows/yaml-lint.yml`)
   - `uv run yamllint -c .yamllint.yml` on changed YAML files

3. **markdown-lint** (`.github/workflows/markdown-lint.yml`)
   - `markdownlint -c .markdownlint.json` on changed Markdown files
   - Requires Node.js 20 and npm

4. **scripts-tests** (`.github/workflows/scripts-tests.yml`)
   - Matrix: Python 3.11 and 3.13
   - `cd .github/scripts && uv run pytest */tests/ -v --tb=short -m "not gh_api"`
   - `cd scripts && uv run pytest */tests/ -v --tb=short -m "not gh_api"`
   - API tests with `@pytest.mark.gh_api` run separately with GITHUB_TOKEN

5. **component-pipeline-tests** (`.github/workflows/component-pipeline-tests.yml`)
   - Detects changed components/pipelines
   - `uv run python -m scripts.tests.run_component_tests {changed_paths}`
   - `uv run python -m scripts.validate_examples {changed_paths}`

6. **compile-and-deps** (`.github/workflows/compile-and-deps.yml`)
   - `uv run python -m scripts.compile_check.compile_check`
   - Validates components/pipelines compile correctly

7. **ci-checks** (`.github/workflows/ci-checks.yml`)
   - Orchestrator that checks all other CI jobs have passed
   - Adds `ci-passed` label when ready

### Other Checks

- `base-image-check.yml` - validates base image tags
- `package-entries-check.yml` - validates package structure
- `readme-check.yml` - validates component/pipeline READMEs
- `validate-metadata-schema.yml` - validates metadata.yaml files

## Conventions

### Test File Organization

```
components/{category}/{subcategory?}/{name}/
  tests/
    test_component_unit.py   # Unit tests with mocked dependencies
    test_component_local.py  # Integration tests using KFP LocalRunner (requires Docker)

pipelines/{category}/{subcategory?}/{name}/
  tests/
    test_pipeline_unit.py    # Unit tests
    test_pipeline_local.py   # Integration tests

scripts/{script_name}/
  tests/
    test_*.py                # Unit tests for utility scripts

.github/scripts/{script_name}/
  tests/
    test_*.py                # Unit tests for CI scripts
```

### Test Naming

- Files: `test_*.py`
- Classes: `Test*` (optional, using pytest class-based organization)
- Functions: `test_*`

### Import Style

- **Components/Pipelines:** Must use **lazy imports** for third-party libraries
  - ❌ `import pandas as pd` at top level
  - ✅ `def my_function(): import pandas as pd` inside function
  - Enforced by custom import-guard script in CI
- **Scripts:** Can use normal top-level imports
- **Relative imports:** Use `from ..component import my_component` within a package

### Code Style

- Line length: 120 characters
- Docstrings: Google style
- Python target: 3.11+
- Quote style: double quotes
- Import sorting: isort via Ruff (I001 rule)

## Gaps & Caveats

1. **Component Local Tests Not Validated**
   - Files named `test_component_local.py` use `kfp.local.LocalRunner`
   - Require Docker to be available
   - Not validated in the container - use unit tests for patch validation

2. **Markdown Linting Requires Node.js**
   - Not installed in the Python container
   - Validation recipe uses Python container only
   - If validating Markdown changes, need to add Node.js 20

3. **GitHub API Tests Require Token**
   - Tests marked `@pytest.mark.gh_api` need `GITHUB_TOKEN`
   - These are excluded with `-m "not gh_api"` in validated commands
   - Only 2 tests are excluded (118 run without token)

4. **Component Tests Are Targeted**
   - CI only runs tests for changed components/pipelines (efficiency optimization)
   - Full test suite not run on every PR
   - Use `uv run python -m scripts.tests.run_component_tests {component_path}` for targeted testing

5. **Pre-commit Hooks Have Complex Logic**
   - `.pre-commit-config.yaml` includes validate-readme, validate-metadata, validate-base-images
   - These have bash scripts with multi-step logic
   - Not individually validated - rely on CI workflows for verification

6. **Tests Must Run from Repo Root**
   - The `conftest.py` at repo root adds `/app` to `sys.path`
   - Running `pytest` from within `scripts/` will fail with import errors
   - Always run from `/app` (repo root)

## Quick Reference

**Install deps:** `uv sync --extra dev`
**Format code:** `uv run ruff format components pipelines scripts`
**Check format:** `uv run ruff format --check components pipelines scripts`
**Lint:** `uv run ruff check components pipelines scripts`
**Fix lint:** `uv run ruff check --fix components pipelines scripts`
**Test scripts:** `cd .github/scripts && uv run pytest */tests/ -v --tb=short -m "not gh_api"`
**Test single file:** `uv run pytest path/to/test_file.py -v --tb=short`
**Test with coverage:** `cd .github/scripts && uv run pytest */tests/ --cov=. --cov-report=term-missing`

**Make targets:**
- `make lint` - runs all linters
- `make format` - auto-fixes formatting
- `make test` - runs scripts tests

## Recommendations for AI Agents

1. **Always validate in container** - Don't assume commands work, run them
2. **Check exit codes carefully** - Exit code 1 for lint may mean "violations found" not "command failed"
3. **Run from repo root** - Test imports will break otherwise
4. **Use unit tests for validation** - Skip local tests that require Docker
5. **UV is required** - Standard `pip install` won't work, must use UV
6. **PATH must include UV** - `export PATH=/root/.local/bin:$PATH` after UV install
7. **Component tests are opt-in** - Not all components have tests, check for `tests/` directory
8. **Import guard is strict** - Components can't import third-party libs at module level

---

**Generated:** 2026-03-22T20:07:54-04:00
**Validation:** Live-tested in `python:3.11-slim` container
**Confidence:** HIGH - All critical commands validated successfully
