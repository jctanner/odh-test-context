# Test Context: rhoai-mcp

**Agent Readiness: HIGH** — Lint and test commands validated successfully. An agent can clone, patch, lint, test, and get clear pass/fail signals.

## Overview

- **Repository**: opendatahub-io/rhoai-mcp
- **Language**: Python 3.10+
- **Build System**: uv (modern Python package manager)
- **Test Framework**: pytest with pytest-asyncio and pytest-cov
- **Linter**: ruff (lint + format)
- **Type Checker**: mypy
- **CI System**: GitHub Actions

This is an MCP (Model Context Protocol) server for Red Hat OpenShift AI. It provides tools for AI agents to interact with Kubernetes clusters running RHOAI. The codebase is well-tested with 520 unit/integration tests achieving 48% coverage.

## Container Recipe

This recipe was validated live on 2026-03-22. Every command ran successfully.

### 1. Start Container

```bash
podman run -d --name test-context-rhoai-mcp \
  -v /path/to/rhoai-mcp:/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

**Alternative with docker:**
```bash
docker run -d --name test-context-rhoai-mcp \
  -v /path/to/rhoai-mcp:/app \
  -w /app \
  python:3.12 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-rhoai-mcp bash -c \
  "apt-get update && apt-get install -y curl git"
```

### 3. Install uv Package Manager

```bash
podman exec test-context-rhoai-mcp bash -c \
  "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

This installs uv to `$HOME/.local/bin/`. You must add it to PATH in subsequent commands.

### 4. Install Project Dependencies

```bash
podman exec test-context-rhoai-mcp bash -c \
  "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv sync"
```

**Result**: Installs 54 packages in ~242ms (after download). Creates `.venv/` directory.

### 5. Run Lint Check

```bash
podman exec test-context-rhoai-mcp bash -c \
  "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run ruff check src/"
```

**Expected Result**: `All checks passed!` (exit code 0)

**If lint fails**: The linter found style violations. To auto-fix:
```bash
podman exec test-context-rhoai-mcp bash -c \
  "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run ruff check --fix src/"
```

### 6. Run Format Check

```bash
podman exec test-context-rhoai-mcp bash -c \
  "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run ruff format --check src/"
```

**Expected Result**: `95 files already formatted` (exit code 0)

**If format fails**: Auto-format with:
```bash
podman exec test-context-rhoai-mcp bash -c \
  "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run ruff format src/"
```

### 7. Run Type Check

```bash
podman exec test-context-rhoai-mcp bash -c \
  "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run mypy src/"
```

**Expected Result**: `Success: no issues found in 95 source files` (exit code 0)

### 8. Run Tests

```bash
podman exec test-context-rhoai-mcp bash -c \
  "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run pytest tests/ --ignore=tests/evals -v --tb=short --cov=src/rhoai_mcp --cov-report=term"
```

**Expected Result**: `520 passed in 6.74s` with 48% coverage (exit code 0)

**Run a single test file:**
```bash
podman exec test-context-rhoai-mcp bash -c \
  "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run pytest tests/test_config.py -v"
```

**Run a specific test:**
```bash
podman exec test-context-rhoai-mcp bash -c \
  "export PATH=\$HOME/.local/bin:\$PATH && cd /app && uv run pytest tests/test_config.py::test_auth_mode_validation -v"
```

### 9. Cleanup

```bash
podman rm -f test-context-rhoai-mcp
```

## Validation Results

All commands were validated in a Python 3.12 container on 2026-03-22:

| Step | Command | Exit Code | Result |
|------|---------|-----------|--------|
| Install deps | `uv sync` | 0 | ✅ 54 packages installed in 242ms |
| Lint | `uv run ruff check src/` | 0 | ✅ All checks passed |
| Format | `uv run ruff format --check src/` | 0 | ✅ 95 files already formatted |
| Typecheck | `uv run mypy src/` | 0 | ✅ No issues in 95 source files |
| Tests | `uv run pytest tests/ --ignore=tests/evals ...` | 0 | ✅ 520 tests passed in 6.74s (48% coverage) |

## CI/CD

**System**: GitHub Actions (`.github/workflows/ci.yml`)

**Gating Checks** (all required to merge):

1. **Lint**: `uv run ruff check src/`
2. **Format**: `uv run ruff format --check src/`
3. **Typecheck**: `uv run mypy src/`
4. **Tests**: `uv run pytest tests/ --ignore=tests/evals -v --tb=short --cov=src/rhoai_mcp --cov-report=xml --cov-report=term`

The CI workflow runs on:
- Pull requests to `main`
- Pushes to `main`
- Manual workflow dispatch

Tests run in a matrix on Python 3.10, 3.11, and 3.12.

**Other Workflows**:
- `.github/workflows/container-build.yml`: Builds and publishes container images
- `.github/workflows/eval.yml`: Runs LLM-based evaluation tests (advisory, not gating)

## Conventions

### Test File Patterns

- Test files: `tests/**/test_*.py`
- Test functions: `test_*` prefix
- Fixtures: `tests/conftest.py` and domain-specific `conftest.py` files

### Test Organization

```
tests/
├── composites/          # High-level composite tool tests
│   ├── cluster/
│   ├── meta/
│   ├── neuralnav/
│   └── training/
├── domains/             # Domain-specific tests
│   ├── inference/
│   ├── model_registry/
│   ├── notebooks/
│   ├── prompts/
│   ├── projects/
│   └── training/
├── integration/         # Integration tests
├── training/            # Training workflow tests
└── utils/               # Utility tests
```

### Async Testing

Tests use `pytest-asyncio` with `asyncio_mode = "auto"` configured in `pyproject.toml`. Async test functions are automatically detected and run.

### Test Markers

- `@pytest.mark.eval`: Evaluation tests that require LLM providers (ignored in CI)
- `@pytest.mark.live`: Tests requiring a live OpenShift cluster

### Import Style

- Absolute imports from `src/rhoai_mcp`
- First-party imports configured in ruff isort settings
- All code requires type hints (mypy `disallow_untyped_defs = true`)

### Code Quality Standards

- **Line length**: 100 characters (ruff config)
- **Python version**: 3.10+ (uses modern type hints)
- **Linter rules**: E (pycodestyle errors), W (warnings), F (Pyflakes), I (isort), B (bugbear), C4 (comprehensions), UP (pyupgrade), ARG (unused-arguments), SIM (simplify)
- **Ignored rules**: E501 (line length handled by formatter), B008, B904

## Gaps & Caveats

**None identified**. This repository has excellent test infrastructure:

✅ Comprehensive linting (ruff check + format)
✅ Type checking (mypy)
✅ 520 unit/integration tests with 48% coverage
✅ Fast test suite (6.74s)
✅ No external dependencies required for unit tests
✅ CI validates all checks on Python 3.10, 3.11, 3.12
✅ Clear test organization by domain
✅ Async test support built-in

**Evaluation Tests**: The `evals/` directory contains LLM-based evaluation tests that require external LLM providers (OpenAI, Anthropic, Google). These are marked with `@pytest.mark.eval` and ignored in CI via `--ignore=tests/evals`. They're advisory tests for measuring agent performance, not gating checks.

**Live Cluster Tests**: Some tests are marked `@pytest.mark.live` and require a live OpenShift cluster. These are not run in CI but can be run locally by developers with cluster access.

## Quick Reference for Agents

**Validate a patch in one command**:
```bash
# Start container, install deps, run all checks
podman run --rm -v $(pwd):/app:Z -w /app python:3.12 bash -c "
  apt-get update -qq && apt-get install -y -qq curl git > /dev/null 2>&1 && \
  curl -LsSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1 && \
  export PATH=\$HOME/.local/bin:\$PATH && \
  uv sync && \
  uv run ruff check src/ && \
  uv run ruff format --check src/ && \
  uv run mypy src/ && \
  uv run pytest tests/ --ignore=tests/evals -v --tb=short
"
```

**Local development workflow** (without container):
```bash
# First time setup
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=$HOME/.local/bin:$PATH
uv sync

# Run checks (same as CI)
uv run ruff check src/
uv run ruff format --check src/
uv run mypy src/
uv run pytest tests/ --ignore=tests/evals -v --tb=short

# Auto-fix issues
uv run ruff check --fix src/
uv run ruff format src/
```

**Makefile shortcuts**:
```bash
make install     # Install dependencies
make lint        # Run ruff check
make format      # Format code
make typecheck   # Run mypy
make check       # Run lint + typecheck
make test        # Run tests
```

## Notes for Downstream Agents

1. **Package manager**: This project uses `uv`, not `pip`. Always use `uv sync` to install dependencies and `uv run` to execute commands in the virtual environment.

2. **Test scope**: The CI command `--ignore=tests/evals` is critical. The `evals/` directory contains evaluation tests that require LLM API keys and are not part of gating checks.

3. **Python version**: Tests run on 3.10, 3.11, and 3.12. The container recipe uses 3.12 (latest supported), but patches should work on all three versions.

4. **Coverage**: 48% coverage is baseline. Patches should not significantly decrease coverage.

5. **Type safety**: This project enforces strict type checking. All functions must have type hints.

6. **No external deps**: Unit/integration tests run without external services (databases, clusters, APIs). They use mocks and fixtures.

7. **Fast feedback**: The entire check suite (lint + format + typecheck + tests) completes in under 10 seconds on modern hardware.
