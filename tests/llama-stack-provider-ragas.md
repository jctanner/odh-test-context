# Test Context: llama-stack-provider-ragas

## Overview

**Repository:** opendatahub-io/llama-stack-provider-ragas
**Languages:** Python 3.12+, JavaScript (docs only)
**Build System:** hatchling (Python) + uv package manager
**Agent Readiness:** **MEDIUM** — Lint commands fully validated and working. All tests are integration tests requiring external infrastructure (Llama Stack server, Kubeflow pipelines, Ollama models), so patch validation is limited to linting only.

## Container Recipe

This is the complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-llama-stack-provider-ragas \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

**Alternative with docker:**
```bash
docker run -d --name test-context-llama-stack-provider-ragas \
  -v $(pwd):/app \
  -w /app \
  python:3.12 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "apt-get update && apt-get install -y git curl"
```

**Note:** git and curl are already included in python:3.12 image.

### 3. Install uv Package Manager

```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "curl -LsSf https://astral.sh/uv/0.8.11/install.sh | sh"
```

**Validation Result:** ✅ Installed to /root/.local/bin

### 4. Install Project Dependencies

```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app && uv sync --extra dev"
```

**Validation Result:** ✅ Installed 182 packages successfully in 628ms
**Output:** Using CPython 3.12.13, created .venv, resolved 185 packages

### 5. Build Package (Optional)

```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app && uv build"
```

**Validation Result:** ✅ Built dist/llama_stack_provider_ragas-0.5.1.tar.gz and .whl

### 6. Run Linting (Primary Validation)

**Ruff Check:**
```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app && uv run ruff check ."
```

**Validation Result:** ✅ All checks passed!

**Ruff Format Check:**
```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app && uv run ruff format --check ."
```

**Validation Result:** ✅ 25 files already formatted

**Pre-commit (All Hooks):**
```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app && uv run pre-commit run --all-files --show-diff-on-failure"
```

**Validation Result:** ✅ All 10 hooks passed
**Hooks:** trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files, check-merge-conflict, debug-statements, ruff-check, ruff-format, mypy, pytest

### 7. Run Tests (Limited - No Unit Tests)

**Non-Integration Tests (CI Command):**
```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app && \
   KUBEFLOW_BASE_IMAGE=dummy uv run pytest -v -m 'not integration_test' --tb=short --maxfail=3"
```

**Validation Result:** ✅ Exit code 5 (no tests collected) - This is expected
**Output:** collected 10 items / 10 deselected / 0 selected
**Note:** All 10 tests are marked as `@pytest.mark.integration_test`, so this command correctly finds zero non-integration tests. Pre-commit treats exit code 5 as success.

**Integration Tests (Requires Infrastructure):**
```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app && \
   uv run pytest -v"
```

**Validation Result:** ❌ Fails without infrastructure
**Error:** `kubernetes.config.config_exception.ConfigException: Invalid kube-config file. No configuration found.`
**Requires:**
- Llama Stack server running (default: http://localhost:8321)
- Kubeflow pipelines endpoint
- Ollama models: granite3.3:2b, all-minilm:latest
- Environment variables: KUBEFLOW_LLAMA_STACK_URL, KUBEFLOW_PIPELINES_ENDPOINT, KUBEFLOW_NAMESPACE, KUBEFLOW_BASE_IMAGE, KUBEFLOW_RESULTS_S3_PREFIX, KUBEFLOW_S3_CREDENTIALS_SECRET_NAME

### 8. Run Single Test File

```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app && \
   uv run pytest -v tests/test_inline_evaluation.py"
```

**Note:** Will fail without infrastructure (Llama Stack server)

### 9. Run Single Test

```bash
podman exec test-context-llama-stack-provider-ragas bash -c \
  "export PATH=/root/.local/bin:\$PATH && cd /app && \
   uv run pytest -v tests/test_inline_evaluation.py::test_single_metric_evaluation"
```

**Note:** Will fail without infrastructure

### 10. Cleanup

```bash
podman rm -f test-context-llama-stack-provider-ragas
```

**Always run cleanup**, even if validation fails.

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `uv sync --extra dev` | 0 | ✅ Pass | 182 packages installed |
| Build | `uv build` | 0 | ✅ Pass | .tar.gz and .whl created |
| Ruff check | `uv run ruff check .` | 0 | ✅ Pass | All checks passed |
| Ruff format | `uv run ruff format --check .` | 0 | ✅ Pass | 25 files formatted |
| Pre-commit | `uv run pre-commit run --all-files` | 0 | ✅ Pass | All 10 hooks passed |
| Non-integration tests | `pytest -m 'not integration_test'` | 5 | ✅ Pass | 0 tests collected (expected) |
| Integration tests | `pytest -v` | 1 | ❌ Fail | Requires Kubeflow/Llama Stack |

## CI/CD

**System:** GitHub Actions
**Config:** `.github/workflows/ci.yml`, `.github/workflows/docs.yml`

### Gating Checks (Required for Merge)

**Pre-commit Checks** (runs on all PRs and pushes to main/develop):

```bash
# Step 1: Install dependencies
uv sync --extra dev

# Step 2: Install pre-commit
uv run pip install pre-commit

# Step 3: Run all pre-commit hooks
uv run pre-commit run --all-files --show-diff-on-failure
```

**Validation:** ✅ Validated successfully in container

**CI Environment:**
- Python: 3.12
- uv: 0.8.11
- OS: ubuntu-latest

### Advisory Checks (Non-Gating)

**Documentation Build** (triggers only on doc file changes):

```bash
npm install -g @antora/cli@3.1 @antora/site-generator@3.1
npm install @asciidoctor/tabs
antora antora-playbook.yml
```

**Validation:** Not validated (requires Node.js, only for docs)

## Conventions

### Test File Naming
- **Pattern:** `test_*.py`
- **Location:** `tests/` directory
- **Fixtures:** `tests/conftest.py`

### Test Function Naming
- **Pattern:** `test_*`
- **Example:** `test_single_metric_evaluation`, `test_remote_evaluation_job_run`

### Integration Test Marker
All tests in this repo are marked with:
```python
pytestmark = pytest.mark.integration_test
```

Files:
- `tests/test_inline_evaluation.py`
- `tests/test_kubeflow_integration.py`
- `tests/test_remote_evaluation.py`
- `tests/test_remote_wrappers.py`

### Import Style
Absolute imports from package:
```python
from llama_stack_provider_ragas.config import RagasProviderInlineConfig
from llama_stack_provider_ragas.constants import PROVIDER_ID_INLINE
```

### Python Version
- **Required:** >=3.12
- **CI Uses:** 3.12

## Gaps & Caveats

### 🔴 Critical Gaps

1. **No Unit Tests:** All 10 tests are integration tests requiring external infrastructure. Zero tests can run in isolation.

2. **Integration Test Requirements:**
   - Llama Stack server (default: http://localhost:8321)
   - Kubeflow pipelines endpoint with valid credentials
   - Ollama models: `granite3.3:2b`, `all-minilm:latest`
   - Kubernetes cluster access
   - S3-compatible storage for results

3. **Environment Variables Required for Integration Tests:**
   ```bash
   KUBEFLOW_LLAMA_STACK_URL
   KUBEFLOW_PIPELINES_ENDPOINT
   KUBEFLOW_NAMESPACE
   KUBEFLOW_BASE_IMAGE
   KUBEFLOW_RESULTS_S3_PREFIX
   KUBEFLOW_S3_CREDENTIALS_SECRET_NAME
   ```

### ⚠️ Validation Limitations

1. **Patch Validation:** Agents can validate linting/formatting but cannot run tests without infrastructure.

2. **CI Behavior:** Pre-commit test hook runs `pytest -m "not integration_test"`, which collects 0 tests and exits with code 5. The hook script treats this as success: `[ $ret = 5 ] && exit 0 || exit $ret`.

3. **Mypy Standalone:** Running `mypy src/` directly finds 2 errors, but pre-commit's mypy hook passes due to `types-requests` in `additional_dependencies`.

### ✅ What Works

1. **Linting:** Fully functional and validated
   - Ruff check and format
   - Mypy (via pre-commit)
   - YAML validation
   - Trailing whitespace, EOF fixes

2. **Build:** Package builds successfully with `uv build`

3. **Dependency Install:** Clean install with `uv sync --extra dev`

## Recommended Workflow for Agents

### For Patch Validation (Automated)

1. **Spin up container** (python:3.12)
2. **Install uv** (curl script)
3. **Install dependencies** (`uv sync --extra dev`)
4. **Run pre-commit** (`uv run pre-commit run --all-files --show-diff-on-failure`)
5. **Interpret results:**
   - ✅ All checks pass → Patch is valid
   - ❌ Ruff/format/mypy fails → Linting issues to fix
   - ⚠️ Pytest hook shows "5 passed" → Expected (no unit tests)

### For Manual Testing (Requires Infrastructure)

1. **Set up Llama Stack server** (e.g., local Ollama + Llama Stack)
2. **Set up Kubeflow pipelines** (or mock the endpoints)
3. **Set environment variables** (see list above)
4. **Run integration tests:** `uv run pytest -v`

### For Development

1. **Install pre-commit hooks:** `uv run pre-commit install`
2. **Run linting before commit:** `uv run pre-commit run --all-files`
3. **Build package:** `uv build`
4. **Install in editable mode:** `uv pip install -e ".[dev]"`

## Agent Readiness Rating: MEDIUM

**Justification:**
- ✅ Lint commands fully validated and working
- ✅ Pre-commit hooks run successfully
- ✅ Build system works
- ✅ Dependency install clean
- ❌ Zero unit tests available for automated validation
- ❌ All tests require complex external infrastructure
- ⚠️ Agents can validate code quality but not functionality

**Bottom Line:** Agents can clone, patch, lint, and get clear pass/fail signals for code quality. However, they cannot validate that patches don't break functionality without access to Llama Stack, Kubeflow, and Ollama infrastructure.
