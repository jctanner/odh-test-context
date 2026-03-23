# Test Context: llama-stack-provider-instructlab-train

## Overview

**Repository**: opendatahub-io/llama-stack-provider-instructlab-train
**Languages**: Python 3.10+
**Build System**: uv (Python package manager)
**Agent Readiness**: **MEDIUM** - Linting fully validated and works perfectly. No unit tests present; only integration test that requires full Llama Stack infrastructure.

## Container Recipe

This section provides a complete, step-by-step recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-llama-stack-provider \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.10 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-llama-stack-provider bash -c \
  "apt-get update && apt-get install -y git curl ca-certificates"
```

### 3. Install uv Package Manager

```bash
podman exec test-llama-stack-provider bash -c \
  "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

### 4. Install Ruff for Linting (Workaround)

The full `uv sync` command fails due to a git dependency requiring authentication. For lint-only validation, install ruff directly:

```bash
podman exec test-llama-stack-provider bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && uv pip install ruff==0.9.4"
```

**Note**: If you have access to the git dependency, you can run the full install:

```bash
podman exec test-llama-stack-provider bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && uv sync && uv pip install -e ."
```

### 5. Run Linting (Primary Validation)

**Ruff Check (lint):**
```bash
podman exec test-llama-stack-provider bash -c \
  "cd /app && /app/.venv/bin/ruff check ."
```
- **Validated**: ✅ Exit code 0
- **Expected output**: "All checks passed!"

**Ruff Format (formatting check):**
```bash
podman exec test-llama-stack-provider bash -c \
  "cd /app && /app/.venv/bin/ruff format --check ."
```
- **Validated**: ✅ Exit code 0
- **Expected output**: "4 files already formatted"

### 6. Run Pre-commit Hooks (Optional, Comprehensive)

Install pre-commit and run all hooks:

```bash
podman exec test-llama-stack-provider bash -c \
  "export PATH=\"/root/.local/bin:\$PATH\" && uv pip install pre-commit"

podman exec test-llama-stack-provider bash -c \
  "cd /app && /app/.venv/bin/pre-commit run --all-files"
```
- **Validated**: ✅ Exit code 0
- **Hooks run**: check-merge-conflict, trailing-whitespace, check-added-large-files, end-of-file-fixer, ruff, ruff-format

### 7. Testing

**No unit tests present in this repository.**

The project only includes an integration test in CI that:
1. Starts a Llama Stack server using `uv run llama stack run run.yaml --image-type venv`
2. Waits for health endpoint at `http://localhost:8321/v1/health`
3. Verifies provider is loaded by checking server logs for "inline::instructlab_train"

This integration test **cannot be run in isolation** as it requires:
- Full Llama Stack installation and dependencies
- Provider configuration in `run.yaml` and `providers.d/`
- Background server process management

### 8. Cleanup

```bash
podman rm -f test-llama-stack-provider
```

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| **Install (full)** | `uv sync` | ❌ Failed | Git dependency requires authentication |
| **Install (workaround)** | `uv pip install ruff==0.9.4` | ✅ Passed | Enables linting validation |
| **Lint (ruff check)** | `ruff check .` | ✅ Passed | All checks passed, exit code 0 |
| **Lint (ruff format)** | `ruff format --check .` | ✅ Passed | 4 files already formatted |
| **Pre-commit** | `pre-commit run --all-files` | ✅ Passed | All hooks passed |
| **Unit Tests** | N/A | ⚠️ N/A | No unit tests present |
| **Integration Test** | CI workflow only | ⚠️ Not Validated | Requires full Llama Stack infrastructure |

## CI/CD

### GitHub Actions Workflows

#### 1. Pre-commit (`pre-commit.yml`)
- **Trigger**: Pull requests, pushes to main
- **Gating**: Yes
- **Python Version**: 3.11
- **Commands**:
  ```bash
  pre-commit run --all-files
  git diff --exit-code  # Verify no uncommitted changes
  ```
- **Purpose**: Enforce code style and formatting standards via ruff

#### 2. Test External Providers (`test-external-providers.yml`)
- **Trigger**: Pull requests, pushes to main
- **Gating**: Yes
- **Python Version**: 3.10
- **Commands**:
  ```bash
  uv sync
  uv pip install -e .
  source .venv/bin/activate
  LLAMA_STACK_LOG_FILE=server.log nohup uv run llama stack run run.yaml --image-type venv &
  # Wait for health check at http://localhost:8321/v1/health
  # Verify provider loaded in server.log
  ```
- **Purpose**: Integration test to verify provider loads in Llama Stack server

## Conventions

### Project Structure
```
src/llama_stack_provider_instructlab_train/
├── __init__.py
├── adapter.py       # Main provider adapter implementation
├── config.py        # Provider configuration
└── provider.py      # Provider interface

providers.d/
└── inline/
    └── post_training/
        └── instructlab_train.yaml  # Provider manifest
```

### Python Version
- **Required**: Python >= 3.10
- **CI uses**: Python 3.10 (integration test), Python 3.11 (pre-commit)
- **Specified in**: `.python-version` file (3.10)

### Code Style
- **Linter**: Ruff v0.9.4
- **Configuration**: Minimal config in `pyproject.toml` - only excludes `*.ipynb` files
- **Pre-commit hooks**: Enforced on all commits
- **Auto-fix available**: `ruff check --fix .` and `ruff format .`

### Dependencies
- **Package Manager**: uv (modern, fast Python package manager)
- **Lock file**: `uv.lock` (committed to repository)
- **Key Dependencies**: llama-stack, instructlab-training, pydantic, fastapi, httpx

## Gaps & Caveats

### Critical Gaps

1. **No Unit Tests**
   - Repository contains no pytest tests or test files
   - Only integration test validates end-to-end functionality
   - Individual components (adapter, config, provider) are not tested in isolation
   - No test coverage measurement or reporting

2. **Git Dependency Authentication**
   - `pyproject.toml` includes: `llama-stack @ git+https://github.com/astefanutti/llama-stack.git@feat-658-1238`
   - This is a fork/branch, not the main llama-stack repository
   - `uv sync` fails in containers without git credentials
   - **Workaround**: Install ruff directly for linting, or configure git authentication

3. **Integration Test Requires Infrastructure**
   - Integration test cannot be run outside of CI
   - Requires full Llama Stack installation with all dependencies
   - Needs background server process management
   - Depends on provider configuration files being correctly structured

### Minor Gaps

4. **No Test Documentation**
   - No testing strategy documented
   - No contribution guide for adding tests
   - No examples of how to test provider functionality

5. **Limited Build Documentation**
   - README.md is minimal (single line)
   - No developer setup guide
   - No troubleshooting information

### Validation Limitations

6. **Cannot Validate Integration Test in Container**
   - The CI integration test starts a real Llama Stack server
   - This requires:
     - All project dependencies installed (fails due to git auth)
     - Llama Stack runtime environment
     - Network access for health checks
     - Process management for background server
   - **Impact**: Agents can validate linting but not integration functionality

## Recommendations for AI Agents

### For Patch Validation (Automated)

1. **Linting is the primary validation mechanism** - it works reliably in containers
2. **Use the workaround**: Install ruff directly rather than full `uv sync`
3. **Expected workflow**:
   ```bash
   # Start container
   # Install system deps (git, curl)
   # Install uv
   # Install ruff directly: uv pip install ruff==0.9.4
   # Run linting: ruff check . && ruff format --check .
   # Exit code 0 = patch is clean
   ```

### For Understanding Changes

1. **Focus on source files**: All logic is in `src/llama_stack_provider_instructlab_train/`
2. **Key files**:
   - `adapter.py` - Main provider implementation
   - `config.py` - Configuration schema
   - `provider.py` - Provider interface
3. **Provider manifest**: `providers.d/inline/post_training/instructlab_train.yaml`

### For Determining Test Coverage

1. **Linting coverage**: 100% - all Python files are linted
2. **Unit test coverage**: 0% - no unit tests exist
3. **Integration test coverage**: Partial - only tests that provider loads, not functionality
4. **Overall validation**: Rely on linting for code quality, integration test validates basic loading

### For Risk Assessment

**Low Risk**: Linting failures (ruff will catch them)
**Medium Risk**: Logic errors, incorrect provider behavior (no unit tests to catch)
**High Risk**: Integration issues with Llama Stack (only caught in CI, not locally)

## Quick Reference

### Validate a Patch (Container)

```bash
# Start
podman run -d --name test-patch -v $(pwd):/app:Z -w /app python:3.10 sleep infinity

# Install tools
podman exec test-patch bash -c "apt-get update && apt-get install -y git curl && curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH=/root/.local/bin:\$PATH && uv pip install ruff==0.9.4"

# Lint
podman exec test-patch bash -c "/app/.venv/bin/ruff check ."
podman exec test-patch bash -c "/app/.venv/bin/ruff format --check ."

# Cleanup
podman rm -f test-patch
```

### Manual Pre-commit (Local Development)

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### CI Commands (Reference)

```bash
# What CI actually runs:
pre-commit run --all-files

# Integration test (requires infrastructure):
uv sync
uv pip install -e .
source .venv/bin/activate
LLAMA_STACK_LOG_FILE=server.log nohup uv run llama stack run run.yaml --image-type venv &
curl -s http://localhost:8321/v1/health
grep "inline::instructlab_train" server.log
```
