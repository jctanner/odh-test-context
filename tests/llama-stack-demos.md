# Test Context: llama-stack-demos

**Organization:** opendatahub-io
**Analyzed:** 2026-03-22T18:42:00-04:00
**Agent Readiness:** `medium` — Linting works perfectly; tests require external llama-stack server infrastructure

---

## Overview

**Languages:** Python 3.12+
**Build System:** uv (modern Python package manager)
**Primary Purpose:** Demo scripts and integration tests for llama-stack on OpenDataHub

This repository has functional linting via pre-commit hooks, but testing requires a running llama-stack server. An AI agent can validate code quality (linting) but cannot execute integration tests without infrastructure.

---

## Container Recipe

This is the complete, copy-paste recipe to validate patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-llama-stack-demos \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-llama-stack-demos bash -c \
  "apt-get update && apt-get install -y git make"
```

Git and make are typically pre-installed in the python:3.12 image, but this ensures they're available.

### 3. Install Python Package Manager (uv)

```bash
podman exec test-context-llama-stack-demos bash -c \
  "cd /app && pip install uv"
```

### 4. Install Project Dependencies

```bash
podman exec test-context-llama-stack-demos bash -c \
  "cd /app && uv sync"
```

**Expected output:** `Installed 143 packages in ~2s`

This creates a virtual environment at `.venv/` with all dependencies from `uv.lock`.

### 5. Run Linter (Pre-commit)

```bash
podman exec test-context-llama-stack-demos bash -c \
  "cd /app && git config --global --add safe.directory /app && \
   .venv/bin/pre-commit install && \
   .venv/bin/pre-commit run --all-files"
```

**Validated:** ✅ **PASS**
**Expected output:**
```
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check for added large files..............................................Passed
```

**What it checks:**
- No trailing whitespace
- Files end with a newline
- No files larger than 500KB committed

### 6. Run Tests

```bash
podman exec test-context-llama-stack-demos bash -c \
  "cd /app && export REMOTE_BASE_URL=<llama-stack-endpoint> && \
   .venv/bin/python tests/eval_tests/tests.py"
```

**Validated:** ❌ **REQUIRES INFRASTRUCTURE**
**Why it fails:** Tests require `REMOTE_BASE_URL` pointing to a running llama-stack server. Without this, you get:
```
REMOTE_BASE_URL environment variable not set
ERROR:mcp_test:REMOTE_BASE_URL environment variable not set
```

**What the tests do:**
- Load queries from JSON files in `tests/eval_tests/queries/`
- Connect to llama-stack server via client
- Register MCP (Model Context Protocol) tool groups
- Execute queries against the tools
- Verify tool calls and inference responses
- Generate metrics and plots

**Required environment variables:**
- `REMOTE_BASE_URL` — llama-stack server endpoint (required)
- `ANSIBLE_MCP_SERVER_URL` — Ansible MCP server (optional)
- `GITHUB_MCP_SERVER_URL` — GitHub MCP server (optional)
- `OCP_MCP_SERVER_URL` — OpenShift MCP server (optional)
- `CUSTOM_MCP_SERVER_URL` — Custom MCP server (optional)

### 7. Test Single File/Test

Not applicable — the test framework doesn't support running individual tests. It's an all-or-nothing integration test suite.

### 8. Cleanup

```bash
podman rm -f test-context-llama-stack-demos
```

---

## Validation Results

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install uv | `pip install uv` | ✅ PASS | uv-0.10.12 installed |
| Install deps | `uv sync` | ✅ PASS | 143 packages installed in 1.93s |
| Lint | `.venv/bin/pre-commit run --all-files` | ✅ PASS | All 3 hooks passed |
| Test | `.venv/bin/python tests/eval_tests/tests.py` | ❌ FAIL | Requires REMOTE_BASE_URL env var |

**Summary:** Dependency install and linting work perfectly. Tests require a llama-stack server and cannot be validated in isolation.

---

## CI/CD

### GitHub Actions

**Workflow:** `.github/workflows/pre-commit.yaml`
**Trigger:** `pull_request` to `main` branch
**Runner:** `ubuntu-latest`
**Python version:** 3.12

**Steps:**
1. Checkout code
2. Setup Python 3.12
3. Run pre-commit hooks via `pre-commit/action@v3.0.1`

**Gating checks:**
- ✅ **pre-commit** (required) — Runs all configured pre-commit hooks

**What's NOT in CI:**
- No test execution
- No code coverage
- No Python-specific linters (ruff, flake8, mypy)
- No build step

---

## Conventions

### File Naming

**Demo scripts:** `demos/*/*.py`
**Test files:** `tests/eval_tests/*.py`
**Test queries:** `tests/eval_tests/queries/*.json`

No pytest naming conventions (no `test_*.py` or `*_test.py` pattern) because this doesn't use pytest.

### Test Structure

Tests are custom integration tests, not pytest-based. The main test script is `tests/eval_tests/tests.py`, which:
- Loads query objects from JSON files
- Each query specifies a prompt and expected tool call
- Tests execute queries against MCP tool servers
- Results are logged and metrics are generated

### Import Style

Standard Python imports. No special conventions observed.

---

## Gaps & Caveats

### Major Gaps

1. **No unit tests** — Only integration tests that require external infrastructure
2. **Tests not run in CI** — CI only checks linting, not functionality
3. **No Python linters** — No ruff, flake8, pylint, or mypy configured
4. **No type checking** — Python 3.12 with type hints but no mypy validation
5. **No code coverage** — No coverage measurement configured
6. **Minimal README** — Documentation is sparse ("Coming soon......")

### What Works

- Pre-commit hooks for basic code hygiene (whitespace, EOF, file size)
- Dependency management via uv (modern, fast)
- Project structure is clean and organized

### What Requires Infrastructure

- **All tests** — Require a running llama-stack server
- **MCP tool servers** — Tests optionally use Ansible, GitHub, OpenShift, and custom MCP servers
- **Query execution** — Tests make real API calls, not mocked

### Agent Considerations

An AI agent validating patches against this repo can:
- ✅ Install dependencies reliably
- ✅ Run pre-commit hooks to check code hygiene
- ✅ Verify Python syntax and imports
- ❌ Cannot run integration tests without llama-stack infrastructure
- ❌ Cannot measure code coverage
- ❌ Cannot run Python-specific linters (none configured)

**Recommendation for agents:** Use this repo for linting-only validation. Tests require infrastructure provisioning beyond standard container environments.

---

## Quick Commands Reference

All commands assume you're inside the container with repo at `/app` and venv activated.

**Install dependencies:**
```bash
uv sync
```

**Run linter:**
```bash
.venv/bin/pre-commit run --all-files
```

**Run linter on specific files:**
```bash
.venv/bin/pre-commit run --files demos/01_foundations/*.py
```

**Run tests (requires infrastructure):**
```bash
export REMOTE_BASE_URL=http://llama-stack-server:8080
.venv/bin/python tests/eval_tests/tests.py
```

**Run tests with specific tool variation:**
```bash
.venv/bin/python tests/eval_tests/tests.py --functions tools/tools_only_params.py
```

**Check Python syntax without running:**
```bash
.venv/bin/python -m py_compile demos/**/*.py
```

---

## Build Targets (Makefile)

The Makefile contains container build targets, not test/lint targets:

```bash
make build_llamastack  # Build llama-stack container
make build_mcp         # Build MCP server container
make build_ui          # Build Streamlit UI container
make run_ui            # Run UI container
make run_mcp           # Run MCP tools
make setup_local       # Set up local development environment
```

These are for running the demos, not for validating patches.

---

## Dependencies

**Key Python packages (from pyproject.toml):**
- `llama-stack-client==0.5.0` — Client for llama-stack
- `llama-stack==0.5.0` — Llama stack framework
- `pre-commit>=4.2.0` — Pre-commit hooks
- `streamlit>=1.44.1` — UI framework for demos
- `openai>=1.75.0` — OpenAI API compatibility
- `python-dotenv>=1.1.0` — Environment variable loading

**Total dependencies:** 143 packages (via uv.lock)

---

## Agent Readiness: Medium

**Strengths:**
- Clean dependency installation via uv
- Pre-commit linting works and passes
- Well-structured codebase
- Python 3.12 modern codebase

**Weaknesses:**
- No tests that can run without infrastructure
- No Python-specific linters
- No type checking
- No code coverage

**Bottom line:** An agent can validate code quality (linting) but cannot execute functional tests. Suitable for patch validation if linting-only validation is acceptable.
