# Test Context: llama-stack-provider-kft

**Generated:** 2026-03-22T22:52:38Z
**Repository:** opendatahub-io/llama-stack-provider-kft
**Languages:** Python 3.10+
**Build System:** uv + setuptools
**Agent Readiness:** **MEDIUM** - Linting fully validated, but no unit tests exist

## Overview

This repository is a Llama Stack Remote Post Training Provider for Distributed InstructLab Training using the Kubeflow Trainer. It's a Python 3.10+ project using the modern `uv` package manager. The codebase has **excellent linting infrastructure** (ruff via pre-commit hooks) but **no unit tests whatsoever**. An agent can validate code quality through linting, but cannot verify functional correctness through tests.

## Container Recipe

This is a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-llama-stack-provider-kft \
  -v /path/to/llama-stack-provider-kft:/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

Replace `/path/to/llama-stack-provider-kft` with the actual repository path.

### 2. Install System Dependencies

```bash
podman exec test-context-llama-stack-provider-kft bash -c "apt-get update && apt-get install -y git curl make"
```

Note: These are already present in python:3.11 image but included for completeness.

### 3. Install uv Package Manager

```bash
podman exec test-context-llama-stack-provider-kft bash -c "pip install --no-cache-dir uv"
```

### 4. Install Project Dependencies

```bash
podman exec test-context-llama-stack-provider-kft bash -c "cd /app && uv sync"
```

**Expected:** Resolves ~133 packages, downloads and installs dependencies. Exit code 0.

### 5. Install Project in Editable Mode

```bash
podman exec test-context-llama-stack-provider-kft bash -c "cd /app && uv pip install -e ."
```

**Expected:** Builds and installs llama-stack-provider-kft. Exit code 0.

### 6. Lint - Ruff Check

```bash
podman exec test-context-llama-stack-provider-kft bash -c "cd /app && uv run ruff check ."
```

**Validated:** ✅ PASS
**Expected Output:** "All checks passed!"
**Exit Code:** 0

**What it does:** Checks for code quality issues, unused imports, syntax errors, etc.

### 7. Lint - Ruff Format

```bash
podman exec test-context-llama-stack-provider-kft bash -c "cd /app && uv run ruff format --check ."
```

**Validated:** ✅ PASS
**Expected Output:** "9 files already formatted"
**Exit Code:** 0

**What it does:** Verifies code is properly formatted according to ruff's style rules.

### 8. Lint - All Pre-commit Hooks

```bash
podman exec test-context-llama-stack-provider-kft bash -c "cd /app && .venv/bin/pre-commit run --all-files"
```

**Validated:** ✅ PASS
**Expected:** All 9 hooks pass:
- check-merge-conflict
- trailing-whitespace
- check-added-large-files
- end-of-file-fixer
- check-toml
- ruff
- ruff-format
- uv-lock
- uv-export

**Exit Code:** 0

### 9. Auto-fix Lint Issues (if needed)

```bash
podman exec test-context-llama-stack-provider-kft bash -c "cd /app && uv run ruff check --fix . && uv run ruff format ."
```

**What it does:** Automatically fixes linting issues and formats code.

### 10. Tests - None Available

**NO UNIT TESTS EXIST IN THIS REPOSITORY**

The only test is an integration test in CI that:
1. Starts the llama-stack server: `uv run llama stack run run.yaml --image-type venv`
2. Waits for health endpoint: `curl http://localhost:8321/v1/health`
3. Validates provider loading via log grep

This integration test requires the server to start but does not test actual training functionality (which requires a Kubernetes cluster).

### 11. Cleanup

```bash
podman rm -f test-context-llama-stack-provider-kft
```

Always run this when done, even if validation fails.

## Validation Results

All commands were validated in a live container:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install deps | `uv sync` | ✅ PASS | 133 packages resolved |
| Editable install | `uv pip install -e .` | ✅ PASS | Project built successfully |
| Ruff check | `uv run ruff check .` | ✅ PASS | No issues found |
| Ruff format | `uv run ruff format --check .` | ✅ PASS | All files formatted |
| Pre-commit hooks | `.venv/bin/pre-commit run --all-files` | ✅ PASS | 9/9 hooks passed |
| Server start | `uv run llama stack run run.yaml --image-type venv` | ✅ PASS | Starts and loads config |

## CI/CD

All CI workflows run on `pull_request` and `push` to `main`.

### Gating Checks

1. **Pre-commit** (`.github/workflows/pre-commit.yml`)
   - **Python version:** 3.11
   - **Command:** `pre-commit run --all-files`
   - **What it gates:** Code quality via ruff, file formatting, toml syntax, uv.lock consistency
   - **Verified:** Uncommitted changes after pre-commit cause failure

2. **Docker Build** (`.github/workflows/build-and-publish-image.yml`)
   - **Platforms:** linux/amd64, linux/arm64
   - **Command:** `docker build -t quay.io/opendatahub/llama-stack-provider-kft .`
   - **What it gates:** Container builds successfully
   - **Publishes to:** quay.io (only on push to main)

3. **Integration Test** (`.github/workflows/test-external-providers.yml`)
   - **Python version:** 3.10
   - **Commands:**
     ```bash
     uv sync
     uv pip install -e .
     uv run llama stack run run.yaml --image-type venv &
     curl -s http://localhost:8321/v1/health
     grep "remote::instructlab_kft" server.log
     ```
   - **What it gates:** Server starts and loads InstructLab KFT provider
   - **What it doesn't test:** Actual training functionality (requires K8s cluster)

## Conventions

### Code Style
- **Linter:** ruff (version 0.9.4)
- **Format:** ruff-format (enforced via pre-commit)
- **Config:** `pyproject.toml` with `[tool.ruff]` section
- **Exclusions:** `*.ipynb` files excluded from ruff checks

### Source Structure
- **Main source:** `src/llama_stack_provider_kft/`
  - `kft_adapter.py` - Core adapter logic (15KB, largest module)
  - `provider.py` - Provider interface
  - `config.py` - Configuration handling
  - `__init__.py` - Package initialization
- **Utilities:** `utils/` directory
  - `ilab_kft.py` - CLI interface for cluster setup
  - `data_upload.py` - Data/model upload to cluster PVC
  - `cluster_setup.py` - Cluster configuration utilities

### Package Management
- **Manager:** uv (modern Python package manager)
- **Lock file:** `uv.lock` (must be kept in sync via pre-commit hook)
- **Python version:** 3.10+ (specified in `.python-version` and `pyproject.toml`)
- **CI uses:** Python 3.10 for integration tests, 3.11 for pre-commit

### Container Build
- **Base image:** `registry.access.redhat.com/ubi9/python-311`
- **Build:** Multi-stage (builder creates wheel, runtime installs it)
- **Port:** 8321 (llama-stack server)
- **User:** 1001 (non-root)

## Gaps & Caveats

### Critical Gaps

1. **No Unit Tests**
   - The repository has zero test files
   - No pytest configuration or any testing framework
   - No way to validate functional correctness of code changes
   - **Impact:** Agents can only validate code quality (linting), not behavior

2. **No Test Coverage**
   - No coverage measurement configured
   - No coverage thresholds enforced
   - Cannot determine what code is exercised by patches

3. **Limited Integration Testing**
   - Only integration test validates server startup
   - Does not test actual training job submission or execution
   - Cannot test Kubernetes API interactions without a cluster

### Infrastructure Requirements

4. **Kubernetes Cluster Needed for Real Testing**
   - The provider manages Kubeflow PyTorchJobs in Kubernetes
   - Real training tests require:
     - Running Kubernetes cluster with Kubeflow Training Operator
     - PVCs for model, data, and output
     - GPU nodes (for actual training)
   - **Impact:** Full validation requires infrastructure not available in container

5. **External Dependencies**
   - Requires `oc` CLI for cluster setup utilities
   - Depends on external registries (quay.io, registry.redhat.io)
   - InstructLab training images must be available

### Documentation Gaps

6. **No Local Development Testing Guide**
   - README shows how to use the provider but not how to test changes
   - No instructions for running against a local/test cluster
   - No mock patterns for testing Kubernetes interactions

### Recommendations for Improving Agent Readiness

To reach **HIGH** agent readiness, the repository should add:

1. **Unit tests with pytest**
   ```bash
   # Example structure
   tests/
     test_config.py          # Test configuration parsing
     test_kft_adapter.py     # Test adapter logic with mocked K8s client
     test_provider.py        # Test provider interface
     conftest.py             # Shared fixtures
   ```

2. **Mocked Kubernetes tests**
   - Use `unittest.mock` or `pytest-mock` to test K8s API interactions
   - Mock PyTorchJob creation, status checking, log retrieval
   - Test error handling without requiring a real cluster

3. **Coverage enforcement**
   - Add `pytest-cov` to measure coverage
   - Set minimum threshold (e.g., 80%)
   - Add to CI gating checks

4. **Local testing instructions**
   - Document how to run tests against kind/minikube
   - Provide example test configurations
   - Include instructions for running integration tests locally

## Using This Context as an Agent

If you're an AI agent using this context to validate patches:

### You CAN:
- ✅ Apply patches to the repository
- ✅ Run linting with `uv run ruff check .` and `uv run ruff format --check .`
- ✅ Auto-fix lint issues with `uv run ruff check --fix .` and `uv run ruff format .`
- ✅ Validate all pre-commit hooks pass
- ✅ Verify the project builds (`uv pip install -e .`)
- ✅ Verify the server starts (integration test)
- ✅ Get clear pass/fail signal on code quality

### You CANNOT:
- ❌ Run unit tests (none exist)
- ❌ Measure test coverage (not configured)
- ❌ Validate functional correctness of changes
- ❌ Test Kubernetes interactions (requires cluster)
- ❌ Test actual training jobs (requires GPU cluster with Kubeflow)

### Recommended Workflow:
1. Apply patch to repository
2. Run dependency install: `uv sync && uv pip install -e .`
3. Run all linting: `.venv/bin/pre-commit run --all-files`
4. If lint fails, auto-fix: `uv run ruff check --fix . && uv run ruff format .`
5. Verify build works: `uv pip install -e .`
6. Report: "Linting passed, build succeeded. ⚠️  No unit tests to validate behavior."

### Known Issues:
- uv may emit warnings about hardlink failures when container and host are on different filesystems (safe to ignore)
- Server startup test requires network access to download dependencies
- Pre-commit hooks will download and cache hook environments on first run (takes 1-2 minutes)

---

**Summary:** This repository has **excellent linting infrastructure** that is fully validated and ready for automated use. However, the **complete absence of unit tests** means agents can only validate code quality, not functional correctness. Agent readiness is **MEDIUM** - sufficient for enforcing style and catching syntax errors, but insufficient for validating behavior changes.
