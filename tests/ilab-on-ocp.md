# Test Context: ilab-on-ocp

## Overview

**Repository**: opendatahub-io/ilab-on-ocp
**Languages**: Python 3.12, Go 1.21
**Build System**: UV package manager, Makefile
**Agent Readiness**: **MEDIUM** — Lint commands work and can validate code style. Build succeeds. However, no Python unit tests exist, and Go e2e tests require OpenShift cluster infrastructure. An agent can lint patches but cannot functionally test them.

## Container Recipe

This recipe provides a complete, executable environment for validating patches through linting and build verification. Copy-paste these commands to validate changes.

### 1. Start Container

```bash
podman run -d --name test-context-ilab-on-ocp \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

**Note**: Replace `$(pwd)` with the absolute path to the repository if running from a different directory. If `podman` is not available, use `docker` instead.

### 2. Install System Dependencies

```bash
podman exec test-context-ilab-on-ocp bash -c "apt-get update && apt-get install -y curl git make"
```

### 3. Install UV Package Manager

```bash
podman exec test-context-ilab-on-ocp bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

### 4. Install Python Dependencies

```bash
podman exec test-context-ilab-on-ocp bash -c "cd /app && export PATH=/root/.local/bin:\$PATH && uv sync --group lint"
```

**Expected**: Installs 67 packages including ruff 0.8.2, pre-commit 4.0.1, and all project dependencies.

### 5. Run Pre-commit Hooks (All Linters)

```bash
podman exec test-context-ilab-on-ocp bash -c "cd /app && export PATH=/root/.local/bin:\$PATH && uv run pre-commit run --all-files"
```

**Status**: ✅ Validated
**Expected**: All hooks pass (trailing-whitespace, end-of-file-fixer, check-yaml, check-merge-conflict, detect-private-key, ruff, ruff-format, yamllint)
**First Run**: Pre-commit will install hook environments, which takes ~2-3 minutes. Subsequent runs are fast.

### 6. Run Ruff Linter (Check Only)

```bash
podman exec test-context-ilab-on-ocp bash -c "cd /app && export PATH=/root/.local/bin:\$PATH && uv run ruff check ."
```

**Status**: ⚠️ Validated (found existing violations)
**Expected**: May report lint violations. Current codebase has 2 known issues:
- `eval/mt_bench.py:4:32: F401` — unused import `typing.Optional`
- `training/components.py:183:28: F541` — f-string without placeholders

**Auto-fix**: `uv run ruff check --fix .`

### 7. Run Ruff Formatter (Check Only)

```bash
podman exec test-context-ilab-on-ocp bash -c "cd /app && export PATH=/root/.local/bin:\$PATH && uv run ruff format --check ."
```

**Status**: ✅ Validated
**Expected**: "13 files already formatted"
**Auto-fix**: `uv run ruff format .`

### 8. Validate Pipeline Generation (Build)

```bash
podman exec test-context-ilab-on-ocp bash -c "cd /app && export PATH=/root/.local/bin:\$PATH && uv run make pipeline"
```

**Status**: ✅ Validated
**Expected**: Generates `pipeline.yaml` from `pipeline.py`. Exit code 0. May show SyntaxWarnings about invalid escape sequences (non-fatal).

### 9. Verify Pipeline is Up-to-Date (CI Gating Check)

```bash
podman exec test-context-ilab-on-ocp bash -c "cd /app && export PATH=/root/.local/bin:\$PATH && uv run make pipeline && git diff --exit-code pipeline.yaml"
```

**Status**: ✅ Validated
**Expected**: Exit code 0 if `pipeline.yaml` is current. Non-zero if regeneration produces changes (meaning pipeline.py changed but pipeline.yaml wasn't updated).

### 10. Cleanup

```bash
podman rm -f test-context-ilab-on-ocp
```

## Running Individual Files/Tests

### Lint a Single File

```bash
podman exec test-context-ilab-on-ocp bash -c "cd /app && export PATH=/root/.local/bin:\$PATH && uv run ruff check <file.py>"
```

### Format a Single File

```bash
podman exec test-context-ilab-on-ocp bash -c "cd /app && export PATH=/root/.local/bin:\$PATH && uv run ruff format <file.py>"
```

### Run Pre-commit on Staged Files Only

```bash
podman exec test-context-ilab-on-ocp bash -c "cd /app && export PATH=/root/.local/bin:\$PATH && uv run pre-commit run"
```

## Validation Results

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install | `uv sync --group lint` | ✅ Pass | Installed 67 packages |
| Pre-commit | `uv run pre-commit run --all-files` | ✅ Pass | All 8 hooks passed |
| Ruff check | `uv run ruff check .` | ⚠️ Found issues | 2 lint violations in existing code |
| Ruff format | `uv run ruff format --check .` | ✅ Pass | 13 files formatted |
| Build | `uv run make pipeline` | ✅ Pass | pipeline.yaml generated |
| Python tests | N/A | ❌ None exist | No Python unit tests |
| Go tests | `go test ./pipeline/e2e/` | ❌ Needs infra | Requires OpenShift cluster |

## CI/CD

### Gating Checks (Required for PR Merge)

The `.github/workflows/pre_commit.yaml` workflow runs on every pull request and enforces:

1. **Pre-commit hooks pass**
   ```bash
   uv run pre-commit run --all-files
   ```
   Runs: trailing-whitespace, end-of-file-fixer, check-yaml, check-merge-conflict, detect-private-key, ruff (with import sorting), ruff-format, yamllint

2. **Pipeline is up-to-date**
   ```bash
   uv run make pipeline
   git diff --exit-code
   ```
   Fails if `pipeline.py` was modified but `pipeline.yaml` wasn't regenerated

3. **Requirements.txt is in sync**
   ```bash
   # CI checks if pyproject.toml changed but requirements.txt didn't
   uv pip compile pyproject.toml --generate-hashes > requirements.txt
   ```
   Fails if `pyproject.toml` changed but `requirements.txt` wasn't updated

### Advisory Checks

- **build-main.yml**: Builds container image on main branch (not gating for PRs)

## Conventions

### Code Style

- **Import sorting**: Ruff automatically sorts imports via pre-commit hook (`--select I`)
- **Formatting**: Ruff format enforces consistent Python style
- **Line endings**: Unix-style (LF), enforced by pre-commit
- **Trailing whitespace**: Removed by pre-commit
- **YAML**: Validated by yamllint with custom config (`.yamllint.yaml`)

### Test Structure

- **Python tests**: None exist
- **Go tests**: `tests/pipeline/e2e/*_test.go`
  - Test function naming: `func Test*` (e.g., `TestPipelineRun`)
  - Requires environment variables: `ENABLE_ILAB_PIPELINE_TEST=true`, `PIPELINE_SERVER_URL`, `BEARER_TOKEN`, `PIPELINE_DISPLAY_NAME`
  - Run command: `cd tests && go test -run TestPipelineRun -v -timeout 180m ./pipeline/e2e/`

### File Organization

- `pipeline.py` — Defines the Kubeflow pipeline
- `pipeline.yaml` — Generated pipeline spec (committed to repo)
- `sdg/` — Synthetic data generation components
- `training/` — Training components
- `eval/` — Evaluation components
- `utils/` — Utility functions
- `tests/pipeline/e2e/` — Go e2e tests
- `manifests/` — Kubernetes manifests

## Gaps & Caveats

### Critical Gaps

1. **No Python unit tests** — The codebase has no tests for individual Python functions, modules, or components. An agent can validate syntax and style but cannot verify functional correctness of code changes.

2. **Go e2e tests require infrastructure** — The only tests are Go-based e2e tests that require:
   - OpenShift cluster with admin access
   - RHOAI (Red Hat OpenShift AI) installed
   - Data Science Pipelines configured
   - InstructLab pipeline imported
   - Pipeline server URL, bearer token, and credentials

   These tests validate end-to-end pipeline execution, not individual code changes. They cannot run in a container or CI environment without cluster access.

3. **Current codebase has lint violations** — Running `uv run ruff check .` reveals 2 existing violations:
   - Unused import in `eval/mt_bench.py`
   - F-string without placeholders in `training/components.py`

   These may need to be fixed before merging new changes, depending on ruff configuration.

### Limitations

- **No test coverage measurement** — No coverage.py or similar tooling configured
- **No integration tests** — No way to test component interactions in isolation
- **No mock patterns** — No mocking infrastructure for external dependencies (Kubernetes, KServe, etc.)
- **Pipeline validation is manual** — No automated tests verify `pipeline.yaml` correctness

### What Works

- ✅ Linting (ruff) catches syntax errors, unused imports, style violations
- ✅ Formatting (ruff format) enforces consistent style
- ✅ YAML validation catches invalid YAML syntax
- ✅ Pre-commit hooks prevent committing common issues
- ✅ Pipeline generation can be validated (file changes detected)
- ✅ Container build can be tested via Dockerfile

### What Doesn't Work in Container

- ❌ Running Go e2e tests (needs OpenShift cluster)
- ❌ Testing actual pipeline execution (needs RHOAI)
- ❌ Validating model serving (needs KServe)
- ❌ Testing distributed training (needs GPU nodes)

## Recommendations for Downstream Agents

1. **For patch validation**: Run `uv run pre-commit run --all-files` to catch style/lint issues. This is the same check CI runs.

2. **For build validation**: Run `uv run make pipeline` and verify exit code 0.

3. **For comprehensive validation**: Run both pre-commit and build, then check `git diff` to ensure pipeline.yaml wasn't modified.

4. **For auto-fixing issues**: Use `uv run ruff check --fix .` and `uv run ruff format .` to automatically fix many lint/format violations.

5. **Limitations**: Accept that functional testing is not possible without OpenShift infrastructure. Focus on static analysis and style validation.

6. **Existing violations**: The codebase has 2 known ruff violations. If your patch introduces new violations, they may be rejected even if the existing ones remain.

## Quick Validation Script

For downstream agents, here's a one-liner to validate a patch:

```bash
podman run --rm -v $(pwd):/app:Z -w /app python:3.12 bash -c "
  apt-get update -qq && apt-get install -y -qq curl git make > /dev/null 2>&1 &&
  curl -LsSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1 &&
  export PATH=/root/.local/bin:\$PATH &&
  uv sync --group lint > /dev/null 2>&1 &&
  echo '=== Running pre-commit ===' &&
  uv run pre-commit run --all-files &&
  echo '=== Running ruff check ===' &&
  uv run ruff check . &&
  echo '=== Validating pipeline ===' &&
  uv run make pipeline &&
  git diff --exit-code pipeline.yaml &&
  echo '=== All checks passed ==='
"
```

**Expected runtime**: ~5 minutes (first run with cache cold). ~30 seconds on subsequent runs with cached layers.

**Exit code**: 0 if all checks pass, non-zero if any check fails.
