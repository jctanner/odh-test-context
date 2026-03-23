# Test Context: opendatahub-io/opendatahub-tests

**Generated:** 2026-03-22T19:50:50-04:00

## Overview

Python 3.14 test suite for Open Data Hub (ODH) / Red Hat OpenShift AI (RHOAI) using pytest framework with uv package manager.

**Agent Readiness:** medium — Lint and test collection validated successfully. Tests require OpenShift/RHOAI cluster to execute, but framework validation works without infrastructure.

**Languages:** Python 3.14
**Build System:** uv + Makefile
**Test Framework:** pytest with extensive markers
**CI System:** GitHub Actions (tox-tests, verify_build_container)

## Container Recipe

Complete step-by-step recipe for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-opendatahub-tests \
  -v $(pwd):/app:Z \
  -w /app \
  fedora:43 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-opendatahub-tests bash -c "dnf install -y python3.14 python3-pip git make curl"
```

### 3. Install uv Package Manager

```bash
podman exec test-context-opendatahub-tests bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

### 4. Install Project Dependencies

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv sync"
```

**Expected:** Resolves ~207 packages, installs ~202 packages in 3-4 seconds.

### 5. Run Linters

#### Ruff (Python linter and formatter)

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run ruff check ."
```

**Validated:** ✅ Pass — "All checks passed!"

#### Ruff Format Check

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run ruff format --check ."
```

#### Flake8 (requires plugins)

First install flake8 and custom plugins:

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv pip install flake8 'git+https://github.com/RedHatQE/flake8-plugins.git@v0.0.6' flake8-mutable"
```

Then run flake8:

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run flake8 --config=.flake8"
```

**Validated:** ✅ Pass — No output (no issues found)

#### Mypy Type Checking (requires types)

First install mypy and type stubs:

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv pip install mypy types-PyYAML types-requests"
```

Then run mypy:

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run mypy --exclude '(docs/|.*test.*\\.py\$|utilities/manifests/.*|utilities/plugins/tgis_grpc/.*)' ."
```

**Validated:** ⚠️ Found 18 type errors — Linter works correctly, code has type issues in utilities/*.py files.

### 6. Run Tests

#### Test Collection (validate test discovery)

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run pytest --collect-only"
```

**Validated:** ✅ Pass — Collected 711 tests (131 deselected) in 4.49s

#### Test Setup Plan (validate fixtures)

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run pytest --setup-plan"
```

**Validated:** ✅ Pass — 82 skipped, 131 deselected (tests skip without cluster)

#### Tox (CI validation)

First install tox and dependencies:

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv pip install tox tox-uv python-utility-scripts"
```

Then run tox:

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && tox"
```

**Validated:** ✅ Pass — Both environments passed (unused-code: 5.39s, pytest: 9.10s, total: 14.51s)

### 7. Run Single Test File

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run pytest tests/cluster_health/test_cluster_health.py"
```

### 8. Run Single Test

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run pytest tests/cluster_health/test_cluster_health.py::TestClusterHealth::test_cluster_operators"
```

Or using -k pattern matching:

```bash
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run pytest -k test_cluster_operators"
```

### 9. Cleanup

```bash
podman rm -f test-context-opendatahub-tests
```

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install deps | `uv sync` | ✅ Pass | 202 packages in 3.25s |
| Lint (ruff) | `uv run ruff check .` | ✅ Pass | All checks passed |
| Lint (flake8) | `uv run flake8 --config=.flake8` | ✅ Pass | No issues |
| Lint (mypy) | `uv run mypy .` | ⚠️ Issues | 18 type errors in utilities/ |
| Test collection | `uv run pytest --collect-only` | ✅ Pass | 711 tests collected |
| Test setup | `uv run pytest --setup-plan` | ✅ Pass | 82 skipped (no cluster) |
| Tox | `tox` | ✅ Pass | Both environments OK |

## CI/CD

### Gating Checks (GitHub Actions)

Two workflows run on `pull_request` events and must pass to merge:

#### 1. Tox Tests (.github/workflows/tox-tests.yml)

Runs on every PR (opened, synchronize):

```bash
uv tool install tox --with tox-uv
tox
```

Validates:
- **unused-code environment:** Checks for unused functions using `pyutils-unusedcode`
- **pytest environment:** Validates test collection (`pytest --collect-only`) and setup plan (`pytest --setup-plan`)

#### 2. Build Container (.github/workflows/verify_build_container.yml)

Runs on every PR (opened, synchronize, reopened):

```bash
make build
```

Validates that the Dockerfile builds successfully.

### Pre-commit Hooks

Required on all commits (enforced by `.pre-commit-config.yaml`):

- **Conventional commits** (feat|fix|docs|chore|test|refactor|perf|ci|build|revert)
- **Signed-off-by** trailer (`git commit -s`)
- **Linters:** flake8, ruff, ruff-format, mypy
- **Security:** detect-secrets, gitleaks
- **Docs:** markdownlint
- **Workflows:** actionlint

## Conventions

### Test Organization

```
tests/
├── cluster_health/        # Cluster health validation
├── fixtures/              # Shared pytest fixtures
├── llama_stack/          # LLaMA Stack tests
├── model_explainability/ # Model explainability tests
├── model_registry/       # Model registry tests
├── model_serving/        # Model serving tests
└── workbenches/          # Workbench tests
```

### Test Markers

Extensive marker system for test categorization and selection:

**Priority Markers:**
- `smoke` — Very high priority, core functionality
- `tier1` — High priority tests
- `tier2` — Medium/low priority positive tests
- `tier3` — Negative and destructive tests

**Execution Markers:**
- `parallel` — Can run in parallel with pytest-xdist
- `slow` — Takes more than 10 minutes
- `skip_on_disconnected` — Requires internet access

**Lifecycle Markers:**
- `pre_upgrade` — Run before product upgrade
- `post_upgrade` — Run after product upgrade

**Component Markers:**
- `llama_stack`, `rag`, `model_explainability` — Ownership tags

**Infrastructure Markers:**
- `gpu`, `multinode`, `keda`, `kueue` — Resource requirements

Run specific marker subsets:

```bash
# Smoke tests only
uv run pytest -m smoke

# Tier1 tests
uv run pytest -m tier1

# RAG team tests
uv run pytest -m rag

# Tests that can run in parallel
uv run pytest -m parallel -n auto
```

### File Naming

- **Test files:** `test_*.py`
- **Test classes:** `class TestClassName`
- **Test functions:** `def test_function_name(...)`

### Code Style

- **Line length:** 120 characters (ruff + flake8)
- **Imports:** Absolute imports preferred
- **Type hints:** Enforced by mypy (strict mode)
- **Docstrings:** Required for public functions

## Gaps & Caveats

### Infrastructure Requirements

**Critical:** Tests require OpenShift/RHOAI cluster to execute. Without cluster:
- Test collection works (✅)
- Test setup validation works (✅)
- Actual test execution skips (most tests check for cluster resources)

Tests depend on:
- OpenShift/Kubernetes cluster
- OpenDataHub or RHOAI operators installed
- Model servers (ModelMesh, KServe, vLLM)
- Inference services
- Model registry
- Storage (MinIO, S3)
- GPU resources (for GPU-marked tests)

### Type Checking Issues

Mypy currently reports 18 type errors in 8 files (all in `utilities/`):
- `utilities/monitoring.py` — Prometheus attribute issues
- `utilities/jira.py` — Type mismatch in auth
- `utilities/serving_runtime.py` — Dict/list type issues
- `utilities/general.py` — Return type mismatch
- `utilities/infra.py` — Argument type issues
- `utilities/must_gather_collector.py` — Attribute issues
- `utilities/llmd_utils.py` — Multiple type issues
- `utilities/inference_utils.py` — Type mismatches

These should be fixed but don't block patch validation (mypy errors are in utility code, not tests).

### Coverage

No coverage reporting configured. Tests run but no coverage thresholds enforced.

### Flake8 Plugins

Flake8 requires custom plugins not in standard dependencies:
- `git+https://github.com/RedHatQE/flake8-plugins.git@v0.0.6`
- `flake8-mutable`

Must be installed separately (shown in container recipe).

## Quick Reference

### Validate a Patch (Full CI Simulation)

```bash
# 1. Start container
podman run -d --name test-context-opendatahub-tests -v $(pwd):/app:Z -w /app fedora:43 sleep infinity

# 2. Setup environment
podman exec test-context-opendatahub-tests bash -c "
  dnf install -y python3.14 python3-pip git make curl && \
  curl -LsSf https://astral.sh/uv/install.sh | sh && \
  export PATH=\$HOME/.local/bin:\$PATH && \
  uv sync && \
  uv pip install tox tox-uv python-utility-scripts
"

# 3. Run CI checks (exactly what GitHub Actions runs)
podman exec test-context-opendatahub-tests bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && tox"
podman exec test-context-opendatahub-tests bash -c "cd /app && make build"

# 4. Cleanup
podman rm -f test-context-opendatahub-tests
```

### Validate Linting Only

```bash
podman run -d --name test-lint -v $(pwd):/app:Z -w /app fedora:43 sleep infinity
podman exec test-lint bash -c "dnf install -y python3.14 python3-pip git curl && curl -LsSf https://astral.sh/uv/install.sh | sh"
podman exec test-lint bash -c "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv sync && uv run ruff check ."
podman rm -f test-lint
```

### Local Development (without container)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run linters
uv run ruff check .
uv run ruff format --check .

# Validate test collection
uv run pytest --collect-only

# Run tox (CI simulation)
uv tool install tox --with tox-uv
tox
```

## Additional Resources

- **Dockerfile:** `Dockerfile` — Production container build
- **Pre-commit config:** `.pre-commit-config.yaml` — All pre-commit hooks
- **Pytest config:** `pytest.ini` — Test markers and options
- **Python config:** `pyproject.toml` — Ruff, mypy, project metadata
- **Tox config:** `tox.ini` — CI test environments
- **Makefile:** `Makefile` — Build targets
- **Docs:** `docs/DEVELOPER_GUIDE.md`, `docs/GETTING_STARTED.md`

---

**Summary:** This repository has well-configured linting (ruff + flake8 + mypy) and test collection. An agent can validate patches by running tox and container build. Actual test execution requires OpenShift cluster, but framework validation works without infrastructure. Agent readiness: medium.
