# Test Context: kubeflow-sdk (opendatahub-io)

**Generated:** 2026-03-22T18:33:00Z

## Overview

Python SDK for Kubeflow to manage ML workloads and interact with Kubeflow APIs. Pure Python package using UV as package manager with hatchling build backend. CI uses Python 3.11.

**Agent Readiness:** **HIGH** — All lint and test commands validated successfully in container. Clear pass/fail signals. No external infrastructure required for unit tests.

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-kubeflow-sdk \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11-slim \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-kubeflow-sdk bash -c "apt-get update && apt-get install -y make git curl"
```

### 3. Install UV Package Manager

```bash
podman exec test-context-kubeflow-sdk bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

### 4. Set PATH and Sync Dependencies

```bash
podman exec test-context-kubeflow-sdk bash -c "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv sync --extra spark"
```

**Expected Result:** `Resolved 129 packages` — Dependencies installed including git-based packages from kubeflow repos.

### 5. Run Linting - Ruff Check

```bash
podman exec test-context-kubeflow-sdk bash -c "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run ruff check --show-fixes --output-format=github ."
```

**Expected Result:** Exit 0, no output (clean) — No lint violations.

### 6. Run Linting - Ruff Format Check

```bash
podman exec test-context-kubeflow-sdk bash -c "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run ruff format --check kubeflow"
```

**Expected Result:** Exit 0, `94 files already formatted` — All files properly formatted.

### 7. Run Type Checking - Ty

```bash
podman exec test-context-kubeflow-sdk bash -c "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run ty check kubeflow/hub"
```

**Expected Result:** Exit 0, `All checks passed!` — Type checking passed for hub module.

### 8. Run Unit Tests with Coverage

```bash
podman exec test-context-kubeflow-sdk bash -c "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run coverage run --source=kubeflow -m pytest ./kubeflow/"
```

**Expected Result:** Exit 0, `548 passed in ~65s` — All unit tests pass.

### 9. Generate Coverage Report

```bash
podman exec test-context-kubeflow-sdk bash -c "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run coverage report --omit='*_test.py' --skip-covered --skip-empty"
```

**Expected Result:** `TOTAL ... 60%` — Coverage report showing ~60% overall coverage.

### 10. Run Single Test File (Example)

```bash
podman exec test-context-kubeflow-sdk bash -c "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run pytest kubeflow/trainer/algorithms_test.py"
```

### 11. Run Single Test (Example)

```bash
podman exec test-context-kubeflow-sdk bash -c "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run pytest kubeflow/trainer/algorithms_test.py::test_get_pytorch_image"
```

### 12. Cleanup Container

```bash
podman rm -f test-context-kubeflow-sdk
```

## Validation Results

All commands validated successfully in `python:3.11-slim` container:

| Step | Command | Exit Code | Result |
|------|---------|-----------|--------|
| Install system deps | `apt-get install make git curl` | 0 | ✓ 53 packages installed |
| Install UV | `curl ... uv/install.sh \| sh` | 0 | ✓ uv 0.10.12 installed |
| Sync dependencies | `uv sync --extra spark` | 0 | ✓ 129 packages resolved |
| Ruff check | `uv run ruff check .` | 0 | ✓ No violations |
| Ruff format | `uv run ruff format --check kubeflow` | 0 | ✓ 94 files formatted |
| Type check | `uv run ty check kubeflow/hub` | 0 | ✓ All checks passed |
| Unit tests | `uv run coverage run -m pytest` | 0 | ✓ 548 passed in 65.81s |
| Coverage report | `uv run coverage report` | 0 | ✓ 60% coverage |

**Summary:** install OK, lint OK (no violations), format OK, type check OK, tests OK (548 passed), coverage 60%

## CI/CD

The following checks gate pull requests:

### Required Checks

1. **Unit Test - Python** (`.github/workflows/test-python.yaml`)
   - Trigger: All PRs and pushes to main
   - Python version: 3.11
   - Commands:
     ```bash
     make verify  # Runs: uv lock --check, ruff check, ruff format --check, ty check
     make test-python report=xml  # Runs: uv sync --extra spark && uv run coverage run -m pytest
     ```
   - Uploads coverage to Coveralls

2. **Validate Lockfile Security** (`.github/workflows/validate-lockfile.yaml`)
   - Trigger: When `uv.lock` or `pyproject.toml` change
   - Commands:
     ```bash
     uv lock --check  # Verify lockfile is in sync
     trivy scan uv.lock  # Check for CVE regressions vs base branch
     ```
   - Blocks PRs that introduce HIGH/CRITICAL CVEs

3. **Check PR Title** (`.github/workflows/check-pr-title.yaml`)
   - Trigger: All PRs
   - Validates conventional commit format
   - Allowed types: `chore`, `fix`, `feat`, `revert`
   - Allowed scopes: `ci`, `docs`, `deps`, `examples`, `scripts`, `test`, `trainer`

4. **Documentation** (`.github/workflows/docs.yaml`)
   - Trigger: When docs/, kubeflow/, or doc configs change
   - Commands:
     ```bash
     uv sync --group docs
     uv run sphinx-build -b html docs/source docs/_build/html
     ```

### Advisory Checks (Non-blocking)

- **E2E Tests** — Require Kind cluster with Spark operator (manual trigger)
- **Snyk Security Scan** — Vulnerability scanning (advisory)
- **Trivy CVE Scan** — Container/dependency scanning (advisory)

## Conventions

**Test Files:**
- Pattern: `*_test.py` (co-located with source code)
- Location: Tests live alongside the code they test (e.g., `kubeflow/trainer/algorithms_test.py`)
- Total: 548 tests

**Test Functions:**
- Naming: `test_*` functions
- Framework: pytest with pytest-mock plugin
- Markers available:
  - `@pytest.mark.integration` — Requires Kubernetes cluster
  - `@pytest.mark.slow` — Slow-running tests
  - `@pytest.mark.smoke` — CRD-only smoke tests
  - `@pytest.mark.timeout` — Tests with timeout limits
  - `@pytest.mark.options` — Spark options pattern tests

**Import Style:**
- Absolute imports from `kubeflow` package
- First-party imports grouped and sorted (enforced by ruff isort rules)
- Example:
  ```python
  from kubeflow.trainer.api import TrainerClient
  from kubeflow.trainer.types import TrainingJob
  ```

**Code Style:**
- Line length: 100 characters
- Quote style: Double quotes
- Target: Python 3.10+
- Formatter: Ruff (Black-compatible)
- Linter: Ruff (replaces flake8, isort, pyupgrade)

**Coverage:**
- Current: 60% overall
- 41 files have 100% coverage (excluded from reports with `--skip-covered`)
- Low coverage areas: docker/podman adapters (16-21%), transformers (18%)
- No enforced threshold, but 60% is the baseline

## Gaps & Caveats

1. **E2E Tests Not Validated** — E2E tests require a Kind cluster with Spark operator installed. These are not run in the container validation and require infrastructure setup. See `.github/workflows/test-e2e.yaml` for setup scripts.

2. **Integration Tests Require Cluster** — Tests marked with `@pytest.mark.integration` expect a Kubernetes cluster. These are skipped by default when running the full test suite locally.

3. **Low Coverage in Container Backends** — The docker/podman local execution adapters have 16-21% test coverage. This doesn't block validation but indicates these code paths are less tested.

4. **Git Dependencies** — The project depends on unreleased versions of kubeflow APIs pulled directly from GitHub (trainer, katib, spark-operator). UV handles these during `uv sync`, but network access is required.

5. **Documentation Build Not Validated** — The sphinx documentation build was not validated in the container. It requires `uv sync --group docs` and has additional dependencies (sphinx, furo, myst-parser, etc.). Validated in CI but not in the container recipe above.

6. **Type Checking Partial** — The `ty` type checker only runs on `kubeflow/hub` module, not the entire codebase. Other modules may have type issues not caught by CI.

## Quick Reference

**Install UV (if not using container):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

**Common Commands:**
```bash
# Full verification (what CI runs)
make verify

# Run tests with coverage
make test-python

# Run tests for XML coverage report
make test-python report=xml

# Install dev dependencies
make install-dev

# Run specific test file
uv run pytest kubeflow/trainer/algorithms_test.py

# Run specific test
uv run pytest kubeflow/trainer/algorithms_test.py::test_get_pytorch_image -v

# Run tests with marker
uv run pytest -m "not integration"  # Skip integration tests

# Auto-fix lint issues
uv run ruff check --fix .
uv run ruff format kubeflow

# Check lockfile is in sync
uv lock --check

# Update lockfile after pyproject.toml changes
uv lock

# Build package (not required for testing)
uv build
```

**Project Structure:**
```
kubeflow-sdk/
├── kubeflow/              # Main package
│   ├── hub/              # Model registry client
│   ├── optimizer/        # Hyperparameter optimization
│   ├── spark/            # Spark integration
│   ├── trainer/          # ML training orchestration
│   └── common/           # Shared utilities
├── docs/                 # Sphinx documentation
├── examples/             # Usage examples
├── .github/workflows/    # CI configuration
├── pyproject.toml        # Package config, dependencies, tool config
├── uv.lock              # Locked dependencies
└── Makefile             # Build targets
```

**Dependencies:**
- Core: kubernetes, pydantic, kubeflow-trainer-api, kubeflow-katib-api
- Optional extras: docker, podman, rhai, spark, hub
- Dev: pytest, coverage, ruff, pre-commit, PyGithub, git-cliff

**Python Version Support:**
- Minimum: 3.10
- CI tested: 3.11
- Supported: 3.10, 3.11, 3.12

## Agent Recommendations

**For downstream agents validating patches:**

1. **Use the container recipe** — The validated commands in the Container Recipe section are proven to work. Run them exactly as written.

2. **Run full verification** — Always run both lint (`make verify`) and tests (`make test-python`) to match what CI does.

3. **Check exit codes** — All commands should exit 0. Non-zero exit from ruff indicates lint violations, not broken commands.

4. **Timeout tests at 5 minutes** — The full test suite runs in ~66 seconds. If tests hang beyond 5 minutes, kill them.

5. **Skip integration tests** — Use `uv run pytest -m "not integration"` if you don't have a K8s cluster available. The default run already skips them (they require explicit marking).

6. **Coverage threshold** — 60% is the current level. Patches should not significantly reduce coverage, but there's no hard enforcement.

7. **Lockfile hygiene** — If you modify `pyproject.toml`, run `uv lock` and commit the updated `uv.lock`. CI will fail if they're out of sync.

8. **PR title format** — Follow conventional commits: `type(scope): description`. Valid types: chore, fix, feat, revert. CI checks this.

9. **Git dependencies** — Be aware that `uv sync` pulls from GitHub repos. Network issues or upstream changes can affect dependency resolution.

10. **Fast feedback loop** — For quick iteration, run `uv run ruff check .` (2-3 seconds) before running the full test suite (66 seconds).
