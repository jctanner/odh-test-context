# Test Context: elyra-examples

## Overview

**Repository:** opendatahub-io/elyra-examples
**Languages:** Python
**Build System:** make + pip + setuptools
**Agent Readiness:** **medium** - Lint commands validate successfully, but tests require external Elyra package dependency not included in test requirements.

This is an examples repository containing Jupyter notebook pipelines and custom component catalog connectors for Elyra. The repository structure includes independent Python packages in subdirectories, each with their own setup.py. Only linting is run in CI - tests exist but require the Elyra framework to be installed.

## Container Recipe

Use this recipe to validate patches in an isolated environment.

### 1. Start Container

```bash
podman run -d --name test-context-elyra-examples \
  -v /path/to/elyra-examples:/app:Z \
  -w /app \
  python:3.10 \
  sleep infinity
```

**Notes:**
- Replace `/path/to/elyra-examples` with the absolute path to your local repository
- Python 3.10 chosen from CI-tested versions (3.7, 3.8, 3.9, 3.10)
- Use `docker` instead of `podman` if podman is not available

### 2. Install Dependencies

```bash
podman exec test-context-elyra-examples bash -c "cd /app && pip install -r test_requirements.txt"
```

**Installs:**
- `flake8>=3.5.0,<3.9.0` - Python linter
- `nbqa` - Apply code quality tools to Jupyter notebooks
- `importlib-metadata<5.0` - Compatibility package

### 3. Run Linting (Validated ✓)

All lint commands validated successfully with exit code 0.

#### Lint Python Scripts

```bash
podman exec test-context-elyra-examples bash -c "cd /app && flake8 ."
```

**Validated:** ✓ Exit code 0, no output
**Config:** `.flake8` with max-line-length=120, custom ignore rules

#### Lint Binder Notebooks

```bash
podman exec test-context-elyra-examples bash -c "cd /app && nbqa flake8 --ignore=H102 binder/getting-started/*.ipynb"
```

**Validated:** ✓ Exit code 0, no output

#### Lint Pipeline Notebooks

```bash
podman exec test-context-elyra-examples bash -c "cd /app && nbqa flake8 --ignore=H102,E402 pipelines/*/*.ipynb"
```

**Validated:** ✓ Exit code 0, no output

#### Run All Lint Checks

```bash
podman exec test-context-elyra-examples bash -c "cd /app && make lint"
```

**Validated:** ✓ Exit code 0
**Output:** Runs all three lint commands sequentially

### 4. Run Tests (Cannot Validate ✗)

Tests exist but require the Elyra package which is not included in test_requirements.txt.

#### Example: Test Artifactory Connector

```bash
# This will FAIL without installing elyra
podman exec test-context-elyra-examples bash -c "cd /app/component-catalog-connectors/artifactory-connector && \
  pip install -r test_requirements.txt && \
  pip install -e . && \
  python -m pytest tests/ -v"
```

**Validated:** ✗ Exit code 2
**Error:** `ModuleNotFoundError: No module named 'elyra'`
**Reason:** Tests import from `elyra.pipeline.catalog_connector` which requires the Elyra package

#### To Actually Run Tests (Not Validated)

You would need to install Elyra first:

```bash
podman exec test-context-elyra-examples bash -c "pip install elyra"
```

Then install and test each connector separately:

```bash
podman exec test-context-elyra-examples bash -c "cd /app/component-catalog-connectors/artifactory-connector && \
  pip install -r test_requirements.txt && \
  pip install -e . && \
  python -m pytest tests/ -v"
```

**Not validated in this analysis** because installing Elyra pulls in many dependencies and was not attempted.

### 5. Test a Single File or Test

```bash
# Single file (requires elyra installed)
podman exec test-context-elyra-examples bash -c "cd /app/component-catalog-connectors/artifactory-connector && \
  python -m pytest tests/test_connector.py -v"

# Single test (requires elyra installed)
podman exec test-context-elyra-examples bash -c "cd /app/component-catalog-connectors/artifactory-connector && \
  python -m pytest tests/test_connector.py::TestArtifactoryComponentCatalogConnector::test__get_hash_keys -v"
```

### 6. Cleanup

```bash
podman rm -f test-context-elyra-examples
```

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `pip install -r test_requirements.txt` | 0 | ✓ | Installed flake8, nbqa, importlib-metadata |
| Lint scripts | `flake8 .` | 0 | ✓ | No lint errors |
| Lint binder notebooks | `nbqa flake8 --ignore=H102 binder/getting-started/*.ipynb` | 0 | ✓ | No lint errors |
| Lint pipeline notebooks | `nbqa flake8 --ignore=H102,E402 pipelines/*/*.ipynb` | 0 | ✓ | No lint errors |
| Lint (make target) | `make lint` | 0 | ✓ | All lint checks pass |
| Test artifactory connector | `pytest tests/` | 2 | ✗ | ModuleNotFoundError: No module named 'elyra' |

**Summary:** Linting fully validated (5/5 commands pass). Tests cannot run without external Elyra dependency.

## CI/CD

**System:** GitHub Actions
**Config:** `.github/workflows/build.yaml`
**Trigger:** Push and pull requests to `main` branch

### Gating Checks

Only **linting** is gating:

```yaml
- name: Lint
  run: make lint
```

**Matrix:** Python 3.7, 3.8, 3.9, 3.10 on ubuntu-latest

### What's NOT in CI

- **Tests are not run** - The CI workflow only validates linting
- No coverage checks
- No build/install validation
- No integration tests

This means pull requests can merge with passing lint but potentially broken tests.

## Conventions

### Test Files

- **Pattern:** `tests/test_*.py`
- **Location:** `component-catalog-connectors/*/tests/`
- **Framework:** pytest
- **Naming:** Classes named `Test*`, methods named `test_*`

### Notebooks

- **Extensions:** `.ipynb`
- **Locations:** `binder/getting-started/*.ipynb`, `pipelines/*/*.ipynb`
- **Linting:** Uses `nbqa` to apply flake8 to notebook code cells
- **Ignore rules:** H102 for binder notebooks, H102+E402 for pipeline notebooks

### Python Code

- **Max line length:** 120 characters
- **Import style:** Absolute imports, grouped (standard library, third-party, local)
- **Excluded from linting:** `__init__.py`, some component resource directories

## Gaps & Caveats

### Critical Gaps

1. **Tests not run in CI** - Tests exist but are not executed in GitHub Actions workflow
2. **Missing test infrastructure** - Tests require `elyra` package which is not in `test_requirements.txt`
3. **No root test command** - Makefile has `lint` target but no `test` target
4. **Incomplete test coverage** - Only some connectors have tests:
   - ✓ artifactory-connector
   - ✓ kfp-example-components-connector
   - ✓ mlx-connector
   - ✗ airflow-example-components-connector (no tests/ directory)
   - ✗ connector-template (template only)

### Documentation Gaps

5. **No test documentation** - README doesn't explain how to run tests or install dependencies
6. **No dependency specification** - Not clear which version of `elyra` is required for testing
7. **No coverage threshold** - No coverage configuration or requirements defined

### Structural Issues

8. **Monorepo with independent packages** - Each connector is independent, requires separate installation
9. **Examples vs. library confusion** - Repository contains both example pipelines (not testable) and library code (connectors, which are testable)

### Agent Impact

**For automated patch validation:**
- ✓ Linting can be validated reliably
- ✗ Tests cannot be run without installing Elyra (many dependencies)
- ✗ No way to validate connector functionality without external infrastructure
- ⚠️  Partial validation possible: lint passes + manual inspection

## Recommendations for Agents

### What Can Be Validated

1. **Linting:** Run `make lint` - fully reliable, matches CI
2. **Syntax:** Python syntax validation via `flake8`
3. **Style compliance:** Code style via flake8 configuration
4. **Notebook linting:** Notebook code cells via nbqa + flake8

### What Cannot Be Validated

1. **Unit tests** - Require Elyra installation
2. **Integration tests** - None present
3. **Functional correctness** - Would require running pipelines in Elyra/Kubeflow/Airflow

### Safe Patch Validation Strategy

For a patch to this repository, an AI agent should:

1. **Run `make lint`** - This is what CI checks
2. **Inspect changed files** - Understand what changed
3. **If connector code changed:**
   - Note that tests exist but cannot be run without infrastructure
   - Recommend manual testing by maintainer
4. **If example notebooks changed:**
   - Verify linting passes
   - Note that notebooks are examples, not tested automatically
5. **If tests changed:**
   - Acknowledge test changes but note they cannot be validated without Elyra

### Decision Logic

- **Lint passes + Python files only changed** → Safe to approve (matches CI)
- **Lint passes + Notebooks changed** → Safe to approve (matches CI)
- **Lint passes + Connector code changed** → Partial validation only, flag for review
- **Lint passes + Tests changed** → Cannot validate, flag for review
- **Lint fails** → Reject (fails CI)
