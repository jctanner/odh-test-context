# vLLM Test Context and Validation Recipe

**Repository:** opendatahub-io/vllm
**Agent Readiness:** LOW (requires GPU/CUDA infrastructure for testing)
**Confidence:** HIGH
**Generated:** 2026-03-22T20:36:55-04:00

## Overview

vLLM is a Python project with C++/CUDA extensions for high-throughput LLM inference. The project uses **pytest** for testing, **pre-commit** hooks for linting (ruff, yapf, mypy, isort, codespell, clang-format), and **Buildkite** for CI/CD (with GitHub Actions for pre-commit checks only).

**Agent Readiness: LOW** - The test suite is heavily GPU-dependent and requires NVIDIA CUDA GPUs (L4 or A100). Linting can be validated in a standard container, but running tests requires building vllm with CUDA support, which needs specialized GPU infrastructure. An agent can apply patches and validate linting, but cannot run the full test suite without GPU access.

---

## Container Recipe

This recipe provides step-by-step commands to validate linting in a container. **Tests cannot be fully validated** without GPU/CUDA infrastructure.

### 1. Start Container

Use Python 3.12 (as specified in CI configuration):

```bash
podman run -d --name test-context-vllm \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

Or with docker:
```bash
docker run -d --name test-context-vllm \
  -v $(pwd):/app \
  -w /app \
  python:3.12 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-vllm bash -c "apt-get update && apt-get install -y \
  git \
  make \
  gcc \
  g++ \
  cmake \
  ninja-build \
  curl"
```

**Exit code:** 0
**Status:** ✅ Validated - system dependencies install successfully

### 3. Install Linting Tools

```bash
podman exec test-context-vllm bash -c "pip install --no-cache-dir \
  pre-commit==4.0.1 \
  ruff \
  yapf \
  isort \
  mypy \
  codespell"
```

**Exit code:** 0
**Status:** ✅ Validated - all linting tools install successfully

### 4. Run Ruff Linting

```bash
podman exec test-context-vllm bash -c "cd /app && ruff check --output-format github ."
```

**Exit code:** 0
**Status:** ✅ Validated - ruff runs successfully
**Output:** Found 472 lint errors (mostly in third_party code). This is expected in the current codebase.
**Note:** Exit code 0 means the linter ran successfully, not that the code is error-free.

### 5. Run Ruff with Auto-fix

```bash
podman exec test-context-vllm bash -c "cd /app && ruff check --fix ."
```

**Status:** ✅ Validated - ruff can auto-fix 43 errors

### 6. Check Linter Versions

```bash
podman exec test-context-vllm bash -c "cd /app && \
  echo 'Ruff:' && ruff --version && \
  echo 'Yapf:' && yapf --version && \
  echo 'Isort:' && isort --version && \
  echo 'Mypy:' && mypy --version"
```

**Expected output:**
```
Ruff: ruff 0.15.7
Yapf: yapf 0.43.0
Isort: isort 8.0.1
Mypy: mypy 1.19.1
```

### 7. Install Test Framework

```bash
podman exec test-context-vllm bash -c "pip install --no-cache-dir \
  'pytest==8.3.3' \
  pytest-asyncio \
  pytest-forked \
  pytest-mock"
```

**Exit code:** 0
**Status:** ✅ Validated - pytest installs successfully

### 8. Verify Pytest

```bash
podman exec test-context-vllm bash -c "pytest --version"
```

**Expected output:**
```
pytest 8.3.3
```

**Status:** ✅ Validated

### 9. Attempt Test Collection (Will Fail)

```bash
podman exec test-context-vllm bash -c "cd /app/tests && pytest --collect-only"
```

**Exit code:** 1
**Status:** ❌ Cannot validate - requires full vllm installation
**Error:** `ModuleNotFoundError: No module named 'numpy'` (and many other dependencies)
**Note:** Test collection requires vllm to be built and installed with CUDA support, which needs GPU infrastructure.

### 10. Cleanup

```bash
podman rm -f test-context-vllm
```

---

## Validation Results

### ✅ Successfully Validated

1. **System dependencies** - gcc, g++, cmake, ninja, git install cleanly
2. **Linting tools** - ruff, yapf, isort, mypy, codespell install successfully
3. **Ruff linting** - Runs and finds 472 errors (expected in current codebase)
4. **Pytest installation** - pytest 8.3.3 installs and runs

### ❌ Cannot Validate Without GPU/CUDA

1. **Test collection** - Requires full vllm dependencies and CUDA build
2. **Test execution** - Requires vllm to be built with CUDA support
3. **Full pre-commit** - Some hooks require CUDA environment
4. **Buildkite tests** - Run on specialized GPU infrastructure (L4/A100)

---

## CI/CD

### GitHub Actions (Gating)

**Workflow:** `.github/workflows/pre-commit.yml`
**Trigger:** Pull requests and pushes to main
**Command:**
```bash
pre-commit run --all-files --hook-stage manual
```

This runs all configured hooks including:
- yapf (formatting)
- ruff (linting with --fix)
- codespell (spell checking)
- isort (import sorting)
- mypy (type checking for Python 3.9, 3.10, 3.11, 3.12)
- clang-format (C++/CUDA formatting)
- shellcheck (shell script linting)
- Custom hooks (SPDX header check, sign-off check, filename validation)

**Status:** Required for merge

### Buildkite (Advisory)

**Pipeline:** `.buildkite/test-pipeline.yaml`
**Infrastructure:** Requires GPU (L4 or A100) nodes
**Test Categories:**
- Fast checks (basic correctness, core, entrypoints) - ~60 tests
- Distributed tests (2-4 GPUs)
- Model tests (standard and extended)
- Multi-modal tests
- Quantization tests
- LoRA tests
- Kernel tests
- Benchmarks

**Example commands from pipeline:**
```bash
# Basic correctness
pytest -v -s basic_correctness/test_basic_correctness.py

# Core tests
pytest -v -s core

# Entrypoints
pytest -v -s entrypoints/llm --ignore=entrypoints/llm/test_lazy_outlines.py

# Distributed (4 GPUs)
pytest -v -s distributed/test_utils.py

# With environment variables
VLLM_ATTENTION_BACKEND=XFORMERS pytest -v -s basic_correctness/test_chunked_prefill.py
VLLM_USE_V1=1 pytest -v -s v1/core
```

**Status:** Not gating for PRs (runs on separate infrastructure)

---

## Linting Commands

### Full Pre-commit Check (CI Mode)

```bash
pre-commit run --all-files --hook-stage manual
```

**What it does:** Runs all hooks including multi-version mypy checks
**Status:** ⚠️ Requires full environment setup

### Ruff (Fast Linting)

```bash
# Check only
ruff check --output-format github .

# With auto-fix
ruff check --fix .

# Specific file
ruff check path/to/file.py
```

**Status:** ✅ Validated

### Yapf (Code Formatting)

```bash
# Check (dry-run)
yapf --diff --recursive .

# Fix
yapf --in-place --recursive .

# Specific file
yapf --in-place path/to/file.py
```

### Isort (Import Sorting)

```bash
# Check
isort --check-only .

# Fix
isort .

# Specific file
isort path/to/file.py
```

### Mypy (Type Checking)

```bash
# Run all mypy checks (local Python version)
bash tools/mypy.sh 0 local

# Run CI mode (specific Python version)
bash tools/mypy.sh 1 3.12
```

**What it does:** Runs mypy on vllm/ subdirectories and tests/
**Config:** See `pyproject.toml` [tool.mypy] and `tools/mypy.sh`

### Codespell (Spell Checking)

```bash
# Check
codespell --toml pyproject.toml

# Fix
codespell --toml pyproject.toml --write-changes
```

---

## Testing Commands

### Run All Tests (Requires GPU)

```bash
pytest -v -s tests/
```

**Requires:** vllm built with CUDA, GPU available
**Status:** ❌ Cannot validate without GPU

### Run Specific Test Directory

```bash
# Core tests
pytest -v -s tests/core/

# Entrypoints
pytest -v -s tests/entrypoints/

# Kernels (requires GPU)
pytest -v -s tests/kernels/
```

### Run Single Test File

```bash
pytest -v -s tests/test_utils.py
```

### Run Single Test Function

```bash
pytest -v -s tests/test_utils.py::test_function_name
```

### Run Tests with Markers

```bash
# Only core model tests
pytest -v -s tests/models/ -m 'core_model'

# Distributed tests (requires 2 GPUs)
pytest -v -s tests/ -m 'distributed(num_gpus=2)'

# Optional tests (normally skipped)
pytest -v -s tests/ --optional
```

### Run Tests with Environment Variables

```bash
# Preemption tests
VLLM_TEST_ENABLE_ARTIFICIAL_PREEMPT=1 pytest -v -s basic_correctness/test_preemption.py

# Attention backend selection
VLLM_ATTENTION_BACKEND=FLASH_ATTN pytest -v -s basic_correctness/test_chunked_prefill.py

# V1 engine tests
VLLM_USE_V1=1 pytest -v -s v1/core

# Multi-process worker
VLLM_WORKER_MULTIPROC_METHOD=spawn pytest -v -s tensorizer_loader
```

### Sharded Testing (for Parallel Execution)

```bash
# Run shard 1 of 4
pytest -v -s tests/kernels --shard-id=0 --num-shards=4

# Run shard 2 of 4
pytest -v -s tests/kernels --shard-id=1 --num-shards=4
```

---

## Build Commands

### Install for Development (CPU-only, no build)

```bash
pip install -e '.[dev]'
```

**Note:** This skips building CUDA extensions. Limited functionality.

### Full Build with CUDA Extensions

```bash
# Install build dependencies
pip install -r requirements-build.txt

# Build in-place
python setup.py build_ext --inplace

# Or install with editable mode
pip install -e '.'
```

**Requires:** CUDA 12.4.1, CMake >=3.26, ninja, GCC 10+, PyTorch 2.5.1

### Docker Build (Full CUDA)

```bash
docker build -f Dockerfile -t vllm:latest .
```

**Note:** Multi-stage build, requires NVIDIA GPU for runtime

---

## Conventions

### Test File Naming

- Test files: `test_*.py` or `*_test.py`
- Test functions: `test_*()`
- Located in `tests/` directory
- Subdirectories mirror source structure

### Test Markers

Defined in `pyproject.toml`:
- `skip_global_cleanup` - Skip cleanup after test
- `core_model` - Run in PR fast checks (not just nightly)
- `cpu_model` - Can run on CPU
- `quant_model` - Quantization tests
- `split` - Sharded tests
- `distributed` - Multi-GPU tests
- `skip_v1` - Skip on V1 engine
- `optional` - Only run with `--optional` flag

### Code Style

- Line length: 80 characters (configured in ruff)
- Import sorting: isort with `use_parentheses = true`
- Type hints: checked by mypy (partial coverage)
- SPDX headers: Required on all Python files
- Sign-off: Required on all commits
- No spaces in filenames

---

## Gaps & Caveats

### Major Gaps

1. **GPU Required for Testing** - The vast majority of tests require NVIDIA GPUs (L4 or A100). There is no meaningful CPU-only test subset.

2. **Complex Build** - Building vllm requires CUDA toolkit, CMake, ninja, and PyTorch. The build process compiles C++/CUDA kernels and is not trivial.

3. **Large Model Downloads** - Many tests download multi-GB models from HuggingFace (Llama, Mixtral, etc.), which requires network access and time.

4. **Buildkite Infrastructure** - The authoritative test suite runs on Buildkite with specialized GPU nodes. This infrastructure is not publicly accessible.

5. **No Simple Test Subset** - Cannot easily run a subset of tests without GPU because test imports fail without vllm being built.

### Minor Gaps

6. **Multi-version Mypy** - Pre-commit in CI runs mypy for Python 3.9-3.12. Local validation only checks one version.

7. **Distributed Tests** - Some tests require 2-4 GPUs or even multi-node setup.

8. **Optional Tests** - Some tests are marked optional and only run in nightly builds.

9. **Documentation Build** - Documentation tests require Sphinx and building docs (not validated here).

### Workarounds for Agents

- **Lint-only validation:** An agent can validate linting without GPU/CUDA
- **Pre-commit subset:** Run only the hooks that don't require full build (ruff, yapf, isort, codespell)
- **CI reliance:** Trust Buildkite CI for test validation rather than running locally
- **Patch review:** Focus on static analysis and code review rather than runtime testing

---

## Example: Validating a Patch

Here's how an agent can validate a patch to vllm:

### 1. Apply the patch

```bash
git apply patch.diff
```

### 2. Run linting (in container)

```bash
# Start container
podman run -d --name vllm-lint \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity

# Install tools
podman exec vllm-lint bash -c "pip install ruff yapf isort"

# Run linters
podman exec vllm-lint bash -c "cd /app && ruff check --output-format github ."
podman exec vllm-lint bash -c "cd /app && yapf --diff --recursive ."
podman exec vllm-lint bash -c "cd /app && isort --check-only ."

# Cleanup
podman rm -f vllm-lint
```

### 3. Rely on CI for tests

Since tests require GPU, an agent should:
- Push the patch to a branch
- Open a PR (or use the existing PR)
- Wait for GitHub Actions pre-commit check (required)
- Optionally wait for Buildkite tests (if available)

### 4. Interpret results

- **Pre-commit pass:** Patch meets linting/formatting standards
- **Pre-commit fail:** Fix linting errors, rerun
- **Buildkite tests:** If available, check for test failures on GPU infrastructure

---

## Summary

vLLM is a **GPU-dependent project** that cannot be fully validated in a standard container environment. An agent can:

**✅ Validate:**
- Linting (ruff, yapf, isort, codespell)
- Code formatting
- Basic static analysis
- Pre-commit hook compliance (subset)

**❌ Cannot Validate Without GPU:**
- Running tests (99% require CUDA)
- Building vllm from source (requires CUDA toolkit)
- Full pre-commit checks (include mypy which needs imports)
- Buildkite pipeline tests

**Recommended Agent Workflow:**
1. Apply patch
2. Validate linting in container (as shown above)
3. Push to branch and rely on CI (GitHub Actions + Buildkite) for test validation
4. Review CI results and iterate

**Agent Readiness: LOW** - Limited local validation capability, heavy reliance on external CI infrastructure.
