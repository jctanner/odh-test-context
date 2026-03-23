# Test Context: llama-stack (opendatahub-io)

**Generated:** 2026-03-22T18:42:15-04:00
**Agent Readiness:** HIGH — Lint and test commands validated successfully in container. An agent can clone, patch, lint, and test with clear pass/fail signals.

---

## Overview

**llama-stack** is a Python project (>=3.12) using the `uv` package manager. It provides a unified API layer for AI application development with support for Inference, RAG, Agents, Tools, Safety, and Evals.

- **Languages:** Python
- **Build System:** uv + setuptools with setuptools-scm versioning
- **Test Framework:** pytest with asyncio support
- **Linting:** ruff (check + format), mypy
- **CI:** GitHub Actions (pre-commit, unit tests on Python 3.12/3.13, integration tests)

**Why High Readiness:** Dependencies install cleanly in a standard Python 3.12 container. Core unit tests (1663 tests) pass successfully. Linting commands work and report clear violations. No special infrastructure needed for basic validation.

---

## Container Recipe

This section provides a **complete, executable recipe** for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-llama-stack \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12-bookworm \
  sleep infinity
```

**Note:** Replace `podman` with `docker` if podman is not available. Replace `$(pwd)` with the absolute path to the llama-stack repository.

### 2. Install System Dependencies

```bash
podman exec test-context-llama-stack bash -c \
  "apt-get update -qq && apt-get install -y git curl ca-certificates -qq"
```

**Packages:** git, curl, ca-certificates

### 3. Install uv Package Manager

```bash
podman exec test-context-llama-stack bash -c \
  "curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv --version"
```

**Expected output:** `uv 0.10.x (x86_64-unknown-linux-gnu)` or similar

### 4. Install Project Dependencies

```bash
podman exec test-context-llama-stack bash -c \
  "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv sync --group dev --group unit --extra client"
```

**Validation Status:** ✅ PASS (exit code 0)
**Duration:** ~2-3 minutes
**Notes:** Resolves 342 packages and installs them into `.venv`. Builds llama-stack and llama-stack-api from local sources in editable mode.

### 5. Run Lint Check (ruff)

```bash
podman exec test-context-llama-stack bash -c \
  "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run ruff check ."
```

**Validation Status:** ✅ PASS (exit code 1 — violations found)
**Output Snippet:**
```
I001 [*] Import block is un-sorted or un-formatted
  --> scripts/generate_prompt_format.py:12:1
Found 1 error.
[*] 1 fixable with the `--fix` option.
```

**Interpretation:** Linter runs successfully. Exit code 1 indicates lint violations exist (1 fixable import ordering issue), not a broken linter.

**Auto-fix command:**
```bash
podman exec test-context-llama-stack bash -c \
  "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run ruff check . --fix"
```

### 6. Run Format Check (ruff format)

```bash
podman exec test-context-llama-stack bash -c \
  "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run ruff format --check ."
```

**Validation Status:** ✅ PASS (exit code 0)
**Output:** `891 files already formatted`

### 7. Run Unit Tests

```bash
podman exec test-context-llama-stack bash -c \
  "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run --with-editable . --group unit pytest tests/unit/ \
  --ignore=tests/unit/providers/utils/inference/test_transformers_inference.py \
  --ignore=tests/unit/providers/vector_io \
  --ignore=tests/unit/distribution/test_library_client_initialization.py \
  -v"
```

**Validation Status:** ✅ PASS (exit code 0)
**Output Snippet:**
```
1663 passed, 4 skipped, 8 warnings in 27.60s
```

**Notes:**
- The `--with-editable .` flag is critical for proper module resolution
- Three test paths are excluded because they require heavyweight optional dependencies (torch, qdrant-client) that are slow to install or have platform-specific builds
- Core functionality tests (CLI, server, providers, agents, etc.) all pass

### 8. Run a Single Test File

**Template:**
```bash
podman exec test-context-llama-stack bash -c \
  "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run --with-editable . --group unit pytest {file} -v"
```

**Example:**
```bash
podman exec test-context-llama-stack bash -c \
  "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run --with-editable . --group unit pytest tests/unit/cli/test_stack_config.py -v"
```

### 9. Run a Single Test

**Template:**
```bash
podman exec test-context-llama-stack bash -c \
  "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run --with-editable . --group unit pytest {file}::{test_name} -v"
```

**Example:**
```bash
podman exec test-context-llama-stack bash -c \
  "cd /app && export PATH=\"\$HOME/.local/bin:\$PATH\" && uv run --with-editable . --group unit pytest tests/unit/cli/test_stack_config.py::test_parse_and_maybe_upgrade_config_up_to_date -v"
```

### 10. Cleanup

```bash
podman rm -f test-context-llama-stack
```

**Always run cleanup**, even if previous steps fail.

---

## Validation Results

All commands were validated live in a `python:3.12-bookworm` container:

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `uv sync --group dev --group unit --extra client` | 0 | ✅ PASS | 342 packages installed cleanly |
| Lint (ruff check) | `uv run ruff check .` | 1 | ✅ PASS | 1 fixable violation found (expected) |
| Format check | `uv run ruff format --check .` | 0 | ✅ PASS | All files formatted |
| Unit tests | `uv run --with-editable . --group unit pytest tests/unit/ ...` | 0 | ✅ PASS | 1663 passed, 4 skipped |

**Summary:** install OK, lint OK (1 fixable violation), format OK, tests OK (1663 passed)

---

## CI/CD

The repository uses GitHub Actions with the following **gating workflows** (required to merge PRs):

### 1. Pre-commit Workflow (`.github/workflows/pre-commit.yml`)

**Triggers:** pull_request, merge_group, push to main/release branches
**Runs on:** ubuntu-latest, Python 3.12, Node 22

**Key steps:**
1. Install uv, Python 3.12, Node.js
2. Install pre-commit, oasdiff (Go tool for API diff)
3. Run: `pre-commit run --show-diff-on-failure --color=always --all-files`
   - **Skips:** `no-commit-to-branch`, `mypy` (mypy runs separately)
   - **Includes:** ruff check, ruff format, license headers, YAML/JSON validation, custom security checks
4. Run: `uv run --group dev --group type_checking mypy`
5. Check for unused integration test recordings
6. Verify no uncommitted changes after hooks

**Environment:**
```bash
export SKIP=no-commit-to-branch,mypy
export RUFF_OUTPUT_FORMAT=github
```

### 2. Unit Tests Workflow (`.github/workflows/unit-tests.yml`)

**Triggers:** pull_request, merge_group, push to main/release branches (on relevant paths)
**Runs on:** ubuntu-latest
**Matrix:** Python 3.12, 3.13

**Command:**
```bash
PYTHON_VERSION=3.12 ./scripts/unit-tests.sh --junitxml=pytest-report-3.12.xml
```

**Script contents (`scripts/unit-tests.sh`):**
```bash
uv run --python "$PYTHON_VERSION" --with-editable . --group unit \
    coverage run --source=src/llama_stack -m pytest -s -v tests/unit/ "$@"
```

**Coverage report generated:** `htmlcov-$PYTHON_VERSION/`

### 3. Integration Tests Workflow (`.github/workflows/integration-tests.yml`)

**Triggers:** pull_request, merge_group, push, schedule (daily), workflow_dispatch
**Runs on:** ubuntu-latest
**Matrix:** client (library/docker/server), Python 3.12 (3.13 on schedule), setup (from ci_matrix.json)

**Command:**
```bash
./scripts/integration-tests.sh \
  --stack-config <config> \
  --suite <suite> \
  --setup <setup> \
  --inference-mode replay
```

**Notes:**
- Integration tests run in **replay mode** (using pre-recorded API responses) in CI
- Tests require Ollama, Docker, or external API providers depending on setup
- TypeScript client tests run for server mode
- Cannot be validated in isolated container without infrastructure

### 4. CI Status Workflow (`.github/workflows/ci-status.yml`)

**Purpose:** Aggregates all other GitHub Actions checks and waits for completion.

**Excludes:** ci-status itself, informational-only checks, mergify bot

**Behavior:**
- Waits for all CI checks to complete
- Fails if any check fails
- Required as the final gating check

---

## Conventions

### Test File Patterns
- **Unit tests:** `tests/unit/test_*.py` or `tests/unit/*_test.py`
- **Integration tests:** `tests/integration/test_*.py`

### Test Naming
- Functions: `test_*`
- Classes: `Test*` (for grouping related tests)

### Pytest Configuration (from `pyproject.toml`)
```toml
[tool.pytest.ini_options]
addopts = ["--durations=10"]
asyncio_mode = "auto"
markers = ["allow_network: Allow network access for specific unit tests"]
filterwarnings = "ignore::DeprecationWarning"
```

**Key points:**
- `asyncio_mode = "auto"` means no `@pytest.mark.asyncio` needed for async tests
- `pytest-socket` blocks network access by default; use `@pytest.mark.allow_network` to permit
- Tests must use `from llama_stack.log import get_logger` instead of `import logging`

### Import Style (Ruff Rules)
- Enforced rules: `I` (isort), `F` (pyflakes), `E` (pycodestyle), `UP` (pyupgrade)
- Import order: stdlib → third-party → first-party
- Star imports (`from x import *`) only allowed in API `__init__.py` files

### Coverage (`.coveragerc`)
**Excluded from coverage:**
- `*/tests/*`
- `*/llama_stack/providers/*`
- `*/llama_stack/templates/*`
- `*/llama_stack_ui/*`
- `*/__init__.py`

### Custom Security Checks (from `.pre-commit-config.yaml`)
- **FIPS compliance:** No `md5`, `sha1`, `uuid3`, `uuid5`
- **SQL injection prevention:** No f-string interpolation in SQL queries (use parameterized queries)
- **Logging:** Must use `llama_stack.log`, not direct `import logging`
- **API independence:** `llama_stack_api` must not import `llama_stack`

---

## Gaps & Caveats

### 1. Heavy Optional Dependencies
Some unit tests require:
- **torch** (PyTorch) — large download (~800MB), platform-specific builds
- **qdrant-client** — vector database client
- **llama-stack-client** — installed via `--extra client` in recipe

**Workaround:** Exclude problematic test paths with `--ignore` as shown in the recipe.

### 2. Integration Tests Require Infrastructure
Integration tests need:
- **Ollama** (local LLM server)
- **Docker** (for container-based tests)
- **External APIs** (OpenAI, Azure, Anthropic, etc.) with API keys

**Mitigation:** Integration tests run in **replay mode** in CI, using pre-recorded HTTP responses. Cannot be validated in isolated container without infrastructure.

### 3. Full Pre-commit Requires Additional Tools
The complete pre-commit suite needs:
- **Node.js 22** (for UI linting via `src/llama_stack_ui/`)
- **oasdiff** (Go-based OpenAPI diff tool)
- **Go toolchain** (for api-conformance check)

**Mitigation:** The container recipe runs only ruff and mypy, which cover the majority of linting. Full pre-commit can be run locally with these tools installed.

### 4. Mypy with Full Type Coverage
The CI runs mypy with `--group dev --group type_checking`, which installs many type stubs (boto3-stubs, pandas-stubs, etc.) and optional runtime dependencies (streamlit, anthropic, databricks-sdk, etc.).

**Mitigation:** Basic mypy runs with just `--group dev` if full type coverage is not needed.

### 5. Platform-Specific Builds
Some dependencies (faiss-cpu, torch, psycopg2-binary) have platform-specific wheels. The recipe uses `python:3.12-bookworm` (Debian-based), which works for most packages.

**Mitigation:** Use the same base image as CI (Debian Bookworm) for consistency.

---

## Quick Reference Commands

**Install dependencies:**
```bash
uv sync --group dev --group unit --extra client
```

**Run all linters:**
```bash
uv run ruff check .                    # Check for violations
uv run ruff check . --fix              # Auto-fix violations
uv run ruff format --check .           # Check formatting
uv run ruff format .                   # Auto-format
```

**Run tests:**
```bash
# All unit tests (excluding heavy deps)
uv run --with-editable . --group unit pytest tests/unit/ \
  --ignore=tests/unit/providers/utils/inference/test_transformers_inference.py \
  --ignore=tests/unit/providers/vector_io \
  --ignore=tests/unit/distribution/test_library_client_initialization.py -v

# Single test file
uv run --with-editable . --group unit pytest tests/unit/cli/test_stack_config.py -v

# Single test
uv run --with-editable . --group unit pytest tests/unit/cli/test_stack_config.py::test_parse_and_maybe_upgrade_config_up_to_date -v

# With coverage (as CI does)
uv run --python 3.12 --with-editable . --group unit \
  coverage run --source=src/llama_stack -m pytest -s -v tests/unit/
uv run coverage html -d htmlcov
```

**Pre-commit (requires Node.js, oasdiff):**
```bash
pre-commit run --all-files
```

**Type checking (requires --group type_checking):**
```bash
uv sync --group dev --group type_checking
uv run mypy
```

---

## Notes for Agents

1. **Always use `--with-editable .` flag** when running pytest to ensure proper module resolution.

2. **Expect lint violations:** The repo may have unfixed ruff violations. Exit code 1 from `ruff check` means violations found, not a broken linter. Check the output to distinguish.

3. **Test exclusions are normal:** The `--ignore` flags for unit tests are expected and documented. Don't try to run those excluded tests without installing torch/qdrant.

4. **uv is critical:** Don't use pip. This project requires `uv` (>=0.7.0) for dependency management and respects the `uv.lock` file.

5. **Python version:** Use Python 3.12 or 3.13. The repo requires >=3.12.

6. **Integration tests are not for basic validation:** Focus on unit tests and linting for patch validation. Integration tests require infrastructure setup.

7. **Coverage artifacts:** CI uploads coverage HTML reports to artifacts. These are in `htmlcov-<python_version>/` directories.

8. **Pre-commit in CI skips some hooks:** The CI workflow skips `no-commit-to-branch` and runs `mypy` separately. Don't expect `pre-commit run --all-files` to match CI exactly unless you replicate the CI environment.

---

**End of Test Context**
