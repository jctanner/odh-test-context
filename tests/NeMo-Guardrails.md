# Test Context: NeMo-Guardrails (opendatahub-io)

**Generated:** 2026-03-22T21:28:36Z
**Agent Readiness:** `medium` — Lint and tests work with caveats (lock file sync, some test configs missing)
**Languages:** Python (3.10, 3.11, 3.12, 3.13)
**Build System:** Poetry 1.8.2
**Test Count:** ~2794 test functions across multiple directories

---

## Container Recipe

This section provides a complete, step-by-step recipe for running lint and tests in an isolated container. Copy and execute these commands verbatim.

### 1. Start Container

```bash
podman run -d --name test-context-nemo-guardrails \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

**Base image:** `python:3.11` (Debian-based, matches CI lint workflow)
**Working directory:** `/app` (repo mounted here)

### 2. Install System Dependencies

```bash
podman exec test-context-nemo-guardrails bash -c "apt-get update && apt-get install -y make git curl"
```

**Note:** `make`, `git`, and `curl` are pre-installed in `python:3.11`, but this ensures they're present.

### 3. Install Poetry

```bash
podman exec test-context-nemo-guardrails bash -c \
  "curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.8.2 python -"
```

**Poetry version:** 1.8.2 (pinned to match CI)

### 4. Regenerate Lock File (IMPORTANT)

```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && poetry lock --no-update"
```

**Why:** The `poetry.lock` file may be out of sync with `pyproject.toml`. This regenerates the lock file without updating dependency versions. This step took ~30 seconds in validation.

**Expected output:**
```
Resolving dependencies...
Writing lock file
```

### 5. Configure Poetry and Install Dependencies

```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && poetry config virtualenvs.in-project true && poetry install --with dev"
```

**Duration:** ~5-10 minutes (large dependency tree: langchain, fastapi, pytest, ruff, pyright, etc.)
**Result:** Creates `.venv/` in project root with all dev dependencies installed.

### 6. Lint: Ruff Check

```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && poetry run ruff check ."
```

**✅ Validated:** Exit code 1 (found 1 unused import)
**Expected:** Lint violations are reported. Exit code 1 means issues found, not a broken command.
**Sample output:**
```
F401 [*] `os` imported but unused
  --> scripts/filter_guardrails.py:18:8
Found 1 error.
[*] 1 fixable with the `--fix` option.
```

**Auto-fix:**
```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && poetry run ruff check --fix ."
```

### 7. Lint: Ruff Format Check

```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && poetry run ruff format --check ."
```

**✅ Validated:** Exit code 1 (found 3 files needing reformatting)
**Sample output:**
```
Would reformat: scripts/discover_required_models.py
Would reformat: scripts/filter_guardrails.py
Would reformat: scripts/pre_download_required_models.py
3 files would be reformatted, 661 files already formatted
```

**Auto-fix:**
```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && poetry run ruff format ."
```

### 8. Lint: Pyright Type Checking

```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && poetry run pyright"
```

**✅ Validated:** Exit code 0 (0 errors, 1 warning)
**Sample output:**
```
File or directory "/app/nemoguardrails/benchmark" does not exist.
/app/nemoguardrails/tracing/adapters/filesystem.py:63:20 - warning: Import "aiofiles" could not be resolved
0 errors, 1 warning, 0 informations
```

**Note:** Pyright only checks select directories configured in `pyproject.toml`. Warning about `aiofiles` is benign (optional dependency).

### 9. Run Tests (Full Suite)

```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && timeout 300 poetry run pytest tests/ -v"
```

**⚠️ Validated:** Exit code 1 (1741 passed, 5 failed, 70 skipped in ~60s)
**Duration:** ~60-120 seconds for full test suite
**Note:** 5 test failures due to missing `tests/test_configs/simple_rails` directory. This appears to be a test setup issue, not a broken test framework. 1741/1746 tests pass successfully.

**Sample output:**
```
============================= test session starts ==============================
...
FAILED tests/test_guardrail_checks_api.py::test_user_message_passes - Assertion...
Invalid config path /app/tests/test_configs/simple_rails.
============ 5 failed, 1741 passed, 70 skipped in 62.03s (0:01:02) =============
```

### 10. Run Single Test File

```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && poetry run pytest tests/test_callbacks.py -v"
```

**✅ Validated:** Exit code 0 (6 passed in 1.39s)

**Template for any file:**
```bash
poetry run pytest {file_path} -v
```

### 11. Run Single Test Function

```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && poetry run pytest tests/test_callbacks.py::test_token_usage_tracking_with_usage_metadata -v"
```

**✅ Validated:** Exit code 0 (1 passed in 0.75s)

**Template:**
```bash
poetry run pytest {file_path}::{test_function_name} -v
```

### 12. Run Tests with Coverage

```bash
podman exec test-context-nemo-guardrails bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && cd /app && poetry run pytest tests/ --cov=nemoguardrails --cov-report=xml:coverage.xml --cov-report=term-missing -v"
```

**✅ Validated:** Coverage reporting works (12% coverage from subset)
**Note:** This is the command used in CI for Python 3.11 with coverage reporting.

### 13. Cleanup

```bash
podman rm -f test-context-nemo-guardrails
```

**Always run this** to remove the container when done.

---

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Container Start | `podman run ... python:3.11` | ✅ Pass | Container started successfully |
| System Deps | `apt-get install make git curl` | ✅ Pass | Already present in base image |
| Install Poetry | `curl ... poetry 1.8.2` | ✅ Pass | Poetry 1.8.2 installed |
| Lock Regen | `poetry lock --no-update` | ✅ Pass | Lock file was out of sync, now fixed |
| Install Deps | `poetry install --with dev` | ✅ Pass | ~5-10 min, all deps installed |
| Ruff Check | `poetry run ruff check .` | ✅ Pass | Exit 1 (found 1 unused import) |
| Ruff Format | `poetry run ruff format --check .` | ✅ Pass | Exit 1 (3 files need formatting) |
| Pyright | `poetry run pyright` | ✅ Pass | Exit 0 (0 errors, 1 warning) |
| Test Single File | `poetry run pytest tests/test_callbacks.py` | ✅ Pass | 6 passed in 1.39s |
| Test Single Func | `poetry run pytest tests/test_callbacks.py::test_...` | ✅ Pass | 1 passed in 0.75s |
| Test Suite | `poetry run pytest tests/ -v` | ⚠️ Partial | 1741 passed, 5 failed (missing configs), 70 skipped |
| Coverage | `poetry run pytest --cov=...` | ✅ Pass | Coverage reporting works |

**Summary:** Install OK (after lock regen), lint OK (found issues), type-check OK (1 warning), tests OK (1741/1746 passed, 5 failed on missing configs)

---

## CI/CD

### GitHub Actions (Gating)

**Workflow:** `.github/workflows/lint.yml` (triggers on PR, push to main/develop)
**Command:** `poetry run make pre_commit`
**What it runs:**
- `ruff check --fix` (linting)
- `ruff format` (formatting)
- `pyright` (type checking)
- YAML validation
- Trailing whitespace fixer
- End-of-file fixer
- License header insertion

**Workflow:** `.github/workflows/pr-tests.yml` (triggers on PR, excluding .md/.github changes)
**Command:** `poetry run pytest -v` (with coverage on Python 3.11)
**Matrix:** Python 3.10, 3.11, 3.12, 3.13 on Ubuntu
**Duration:** ~60-120 seconds per Python version

### GitLab CI (Gating)

**Config:** `.gitlab-ci.yml`
**Jobs:** `python3.10`, `python3.11`, `python3.12`, `python3.13`
**Command:** `make test` → `poetry run pytest tests/`
**Runs on:** python:3.10, python:3.11, python:3.12, python:3.13 Docker images
**Triggers:** All pushes

### Tekton (Container Build)

**Config:** `.tekton/odh-trustyai-nemo-guardrails-server-release-push.yaml`
**Purpose:** Builds container images for OpenShift
**Triggers:** Push to `develop` branch
**Dockerfile:** `Dockerfile.server`
**Platforms:** linux/x86_64, linux-m2xlarge/arm64

---

## Conventions

### Test Files
- **Pattern:** `test_*.py` or `*_test.py`
- **Locations:** `tests/`, `docs/colang-2/examples`, `benchmark/tests`
- **Count:** ~2794 test functions total
- **Framework:** pytest with pytest-asyncio for async tests

### Test Naming
- **Functions:** `test_<descriptive_name>` in snake_case
- **Example:** `test_token_usage_tracking_with_usage_metadata`

### Code Style
- **Linter:** Ruff 0.14.6 (replaces flake8, isort, black)
- **Line length:** 120 characters
- **Quotes:** Double quotes (like Black)
- **Indentation:** 4 spaces
- **Imports:** Sorted and grouped (I001, I002 rules)
- **Enabled rules:** E4, E7, E9, F (Pyflakes), W291-293 (whitespace), I001-002 (imports)
- **Ignored rules:** F821 (undefined name), F841 (unused variable)

### Type Checking
- **Tool:** Pyright 1.1.405
- **Scope:** Partial (specific directories only, see `pyproject.toml` [tool.pyright])
- **Included paths:** `nemoguardrails/rails/`, `nemoguardrails/actions/`, `nemoguardrails/llm/`, and others
- **Excluded paths:** `nemoguardrails/llm/providers/trtllm/`

### License Headers
- **Required:** Apache 2.0 license header on all `.py` files
- **Auto-inserted:** By pre-commit hook using `insert-license`
- **Template:** See `LICENSE.md`

---

## Gaps & Caveats

1. **Lock File Out of Sync:** The `poetry.lock` file may be out of sync with `pyproject.toml`. Agents must run `poetry lock --no-update` before `poetry install` if encountering lock file errors. This adds ~30 seconds to setup time.

2. **Missing Test Configs:** 5 tests fail due to missing `tests/test_configs/simple_rails` directory. These appear to be test infrastructure issues, not code issues. 1741 other tests pass successfully.

3. **Large Test Suite:** ~2794 tests total across all test paths. Full execution takes 60-120 seconds. Consider running subsets for faster feedback (e.g., `pytest tests/test_callbacks.py`).

4. **Skipped Tests:** 70 tests are skipped (out of ~1746 in `tests/`). These may require specific environment variables, external services, or optional dependencies.

5. **Optional Dependencies:** Some optional dependencies (e.g., `aiofiles`) cause pyright warnings. These are not critical and can be ignored.

6. **No Coverage Threshold:** The project reports coverage but has no enforced threshold. Coverage appears to be ~12% based on subset validation.

7. **Benchmark Directory Missing:** Pyright config references `nemoguardrails/benchmark` which doesn't exist in the repo. This causes a warning but doesn't break type checking.

8. **Pre-commit Hook Complexity:** The `make pre_commit` target runs all pre-commit hooks including license insertion, which may modify files. An agent validating patches should be aware files may be auto-modified.

---

## Quick Reference

### Common Commands

**Full lint check:**
```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run pyright
```

**Auto-fix lint issues:**
```bash
poetry run ruff check --fix .
poetry run ruff format .
```

**Run all tests:**
```bash
poetry run pytest tests/ -v
```

**Run tests with coverage (matches CI):**
```bash
poetry run pytest --cov=nemoguardrails tests/ --cov-report=xml:coverage.xml -v
```

**Run single test file:**
```bash
poetry run pytest tests/test_callbacks.py -v
```

**Run single test:**
```bash
poetry run pytest tests/test_callbacks.py::test_token_usage_tracking_with_usage_metadata -v
```

### Environment Setup (Local)

```bash
# Install Poetry 1.8.2
curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.8.2 python -

# Configure Poetry to use in-project virtualenv
poetry config virtualenvs.in-project true

# Regenerate lock file if out of sync
poetry lock --no-update

# Install dependencies
poetry install --with dev

# Install pre-commit hooks (optional)
poetry run pre-commit install
```

### Test Paths

- **Main tests:** `tests/` (unit and integration tests)
- **Documentation examples:** `docs/colang-2/examples` (runnable pytest examples)
- **Benchmark tests:** `benchmark/tests` (performance tests)

All three paths are configured in `pytest.ini` under `testpaths`.

---

## Agent Readiness Assessment

**Rating:** `medium`

**Justification:**
An AI agent can successfully validate patches in this repository with the following workflow:
1. Start container with `python:3.11`
2. Install Poetry 1.8.2
3. Run `poetry lock --no-update` to fix lock file
4. Run `poetry install --with dev`
5. Run lint commands (ruff check, ruff format, pyright)
6. Run test subset or full test suite

**Caveats:**
- Lock file regeneration adds ~30 seconds to setup
- 5 tests fail due to missing test configs (not critical)
- Full test suite takes 60-120 seconds
- Large dependency install (~5-10 minutes first time)

**Recommended for automated patch validation:** Yes, with awareness of the lock file issue and the few failing tests. An agent should run lint checks and a test subset for quick feedback, then optionally run the full test suite for comprehensive validation.

**Not recommended for:** Real-time validation (too slow), infrastructure-less environments (requires container runtime).

---

## Additional Notes

- **Multi-language Support:** While primarily Python, the project includes a TypeScript VSCode extension (`vscode_extension/`) and a Node.js chat UI (`chat-ui/`), but these are not part of the main Python test/lint infrastructure.

- **Documentation:** The project has Sphinx-based documentation in `docs/`. Build with `poetry run sphinx-build -b html docs _build/docs`. Documentation build is not part of PR gating checks.

- **Tox Support:** The project has a `tox.ini` for testing across Python 3.10-3.13, but tox is not used in CI. CI uses Poetry directly with matrix builds.

- **Makefile Targets:** The `Makefile` provides convenience targets (`make test`, `make pre_commit`, `make docs`) but these are thin wrappers around Poetry commands.

- **Container Images:** The project builds container images (`Dockerfile`, `Dockerfile.server`) for deployment, but these are not used for testing. Testing uses the Poetry environment directly.

---

**End of Test Context**
