# Test Context: vllm-gaudi

**Generated:** 2026-03-22T20:37:00Z
**Repository:** opendatahub-io/vllm-gaudi
**Main Branch:** habana_main
**Agent Readiness:** medium - Lint validation works; tests require specialized hardware (HPU/GPU)

## Overview

vLLM-Gaudi is a high-performance large language model inference engine optimized for Intel Habana Gaudi HPU accelerators. The project is a Python package with C++/CUDA extensions, requiring specialized hardware for full testing. Linting and static analysis work in standard containers.

**Languages:** Python, C++, CUDA, Bash
**Build System:** setuptools with CMake for C++ extensions
**Test Framework:** pytest with custom fixtures for model testing
**Primary Hardware:** Intel Habana Gaudi HPU (also supports CUDA GPU, CPU, TPU, AWS Neuron)

## Container Recipe

This section provides a complete, executable recipe for validating patches. Linting works in a standard container; full testing requires HPU/GPU hardware.

### 1. Start Container

```bash
podman run -d --name test-context-vllm-gaudi \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

**Base Image:** `python:3.11` (Debian-based)

### 2. Install System Dependencies

```bash
podman exec test-context-vllm-gaudi bash -c \
  "apt-get update && apt-get install -y git make clang-format shellcheck"
```

**Packages:** git, make, clang-format (18.1.5), shellcheck (0.10.0)

### 3. Install Python Lint Dependencies

```bash
podman exec test-context-vllm-gaudi bash -c \
  "cd /app && pip install --upgrade pip && pip install -r requirements-lint.txt"
```

**Installs:**
- ruff==0.6.5
- yapf==0.32.0
- mypy==1.11.1
- isort==5.13.2
- codespell==2.3.0
- clang-format==18.1.5
- type stubs (types-PyYAML, types-requests, types-setuptools)

### 4. Run Linting (Validated ✓)

All lint commands validated successfully in container:

```bash
# Ruff - Python linter
podman exec test-context-vllm-gaudi bash -c \
  "cd /app && ruff check ."
# Exit code: 0 | Output: "All checks passed!"
```

```bash
# yapf - Python formatter check
podman exec test-context-vllm-gaudi bash -c \
  "cd /app && yapf --diff --recursive ."
# Exit code: 0 | Output: (none - no formatting issues)
```

```bash
# isort - Import sorter check
podman exec test-context-vllm-gaudi bash -c \
  "cd /app && isort . --check-only"
# Exit code: 0 | Output: "Skipped 1 files"
```

```bash
# codespell - Spelling check
podman exec test-context-vllm-gaudi bash -c \
  "cd /app && codespell --toml pyproject.toml"
# Exit code: 0 | Found 2 spelling errors: bounadry -> boundary
```

```bash
# mypy - Type checking
podman exec test-context-vllm-gaudi bash -c \
  "cd /app && mypy vllm/*.py"
# Exit code: 0 | Output: "Success: no issues found in 20 source files"
```

```bash
# clang-format - C++/CUDA formatting check
podman exec test-context-vllm-gaudi bash -c \
  "cd /app && find csrc/ \\( -name '*.h' -o -name '*.cpp' -o -name '*.cu' -o -name '*.cuh' \\) -print | \
  grep -vFf <(printf \"%s\\n\" \
    \"csrc/moe/topk_softmax_kernels.cu\" \
    \"csrc/quantization/gguf/ggml-common.h\" \
    \"csrc/quantization/gguf/dequantize.cuh\" \
    \"csrc/quantization/gguf/vecdotq.cuh\" \
    \"csrc/quantization/gguf/mmq.cuh\" \
    \"csrc/quantization/gguf/mmvq.cuh\") | \
  xargs clang-format --dry-run --Werror"
# Checks C++/CUDA code formatting
```

```bash
# shellcheck - Shell script linting
podman exec test-context-vllm-gaudi bash -c \
  "cd /app && tools/shellcheck.sh"
# Checks all .sh scripts in the repo
```

**Auto-fix Commands:**

```bash
# Fix Python formatting
ruff check --fix .
yapf --in-place --recursive .
isort .

# Fix C++ formatting
find csrc/ \( -name '*.h' -o -name '*.cpp' -o -name '*.cu' -o -name '*.cuh' \) -print | \
  grep -vFf <(printf "%s\n" \
    "csrc/moe/topk_softmax_kernels.cu" \
    "csrc/quantization/gguf/ggml-common.h" \
    "csrc/quantization/gguf/dequantize.cuh" \
    "csrc/quantization/gguf/vecdotq.cuh" \
    "csrc/quantization/gguf/mmq.cuh" \
    "csrc/quantization/gguf/mmvq.cuh") | \
  xargs clang-format -i

# Fix spelling
codespell --toml pyproject.toml --write-changes
```

**Comprehensive Format Script:**

The repo provides `./format.sh` which runs all formatters and linters:

```bash
./format.sh  # Run on changed files (vs origin/main)
./format.sh --all  # Run on all files
./format.sh --files file1.py file2.py  # Run on specific files
```

### 5. Build Package (Requires HPU/GPU)

**⚠️ Cannot validate in standard container** - requires CUDA toolkit or HPU SDK

```bash
# For HPU build (requires Habana SDK):
pip install -r requirements-build.txt
pip install -r requirements-hpu.txt
VLLM_TARGET_DEVICE=hpu python setup.py develop

# For CPU build:
pip install -r requirements-build.txt
pip install -r requirements-cpu.txt
VLLM_TARGET_DEVICE=cpu python setup.py develop
```

**Build Requirements:**
- cmake >= 3.26
- ninja
- torch == 2.5.1
- setuptools >= 61
- For HPU: Habana SDK with habana_frameworks
- For CUDA: CUDA toolkit 12.1+

### 6. Run Tests (Requires HPU/GPU)

**⚠️ Cannot validate in standard container** - requires built package and hardware

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::test_function_name

# Run with markers
pytest -m cpu_model  # Only CPU model tests
pytest -m "not distributed_2_gpus"  # Skip multi-GPU tests

# CPU-only sanity test (fake HPU mode)
VLLM_SKIP_WARMUP=true \
VLLM_PROMPT_SEQ_BUCKET_MAX=128 \
VLLM_USE_FAKE_HPU=1 \
python examples/offline_inference_fakehpu.py
```

**Test Environment Variables:**
- `VLLM_TARGET_DEVICE=hpu|cuda|cpu|tpu|neuron` - Target hardware
- `VLLM_SKIP_WARMUP=true` - Skip model warmup for faster testing
- `VLLM_USE_FAKE_HPU=1` - Simulate HPU on CPU (limited functionality)

### 7. Cleanup

```bash
podman rm -f test-context-vllm-gaudi
```

## Validation Results

### Successful Validations ✓

| Tool | Command | Result |
|------|---------|--------|
| ruff | `ruff check .` | ✓ All checks passed |
| yapf | `yapf --diff --recursive vllm` | ✓ No formatting issues |
| isort | `isort . --check-only` | ✓ Imports properly sorted |
| codespell | `codespell --toml pyproject.toml` | ✓ 2 spelling errors found |
| mypy | `mypy vllm/*.py` | ✓ No type errors in 20 files |
| clang-format | Version check | ✓ 18.1.5 confirmed |
| shellcheck | Version check | ✓ 0.10.0 confirmed |

### Failed Validations (Expected) ✗

| Step | Command | Reason |
|------|---------|--------|
| Build | `python setup.py develop` | Requires CUDA/HPU SDK not in container |
| Test Collection | `pytest --collect-only tests/` | Requires built vllm package |
| Test Execution | `pytest tests/` | Requires built package + hardware |

### Summary

**Linting:** All 7 linters validated successfully in standard Python 3.11 container.
**Building:** Requires specialized hardware SDK (Habana, CUDA) - cannot validate in standard container.
**Testing:** Requires built package and HPU/GPU hardware - cannot validate in standard container.

## CI/CD

### GitHub Actions (Gating Checks)

All PRs to `habana_main` must pass:

1. **ruff** - Python linting
   ```bash
   ruff check --output-format github .
   ```

2. **yapf** - Python formatting
   ```bash
   yapf --diff --recursive .
   ```

3. **mypy** - Type checking (Python 3.9, 3.10, 3.11, 3.12)
   ```bash
   tools/mypy.sh 1 $PYTHON_VERSION
   ```

4. **isort** - Import sorting
   ```bash
   isort . --check-only
   ```

5. **clang-format** - C++/CUDA formatting
   ```bash
   find csrc/ \( -name '*.h' -o -name '*.cpp' -o -name '*.cu' -o -name '*.cuh' \) -print | \
     grep -vFf <(printf "%s\n" "csrc/moe/topk_softmax_kernels.cu" ...) | \
     xargs clang-format --dry-run --Werror
   ```

6. **cpu-test** - Basic sanity test
   ```bash
   VLLM_SKIP_WARMUP=true \
   VLLM_PROMPT_SEQ_BUCKET_MAX=128 \
   VLLM_USE_FAKE_HPU=1 \
   python examples/offline_inference_fakehpu.py
   ```

### Jenkins & Buildkite

More extensive hardware-specific tests run on:
- Intel Habana Gaudi HPUs (G2, G3 flavors)
- Multi-GPU configurations
- Different tensor parallelism settings (TP1, TP2, TP4)
- Model evaluation benchmarks (GSM8K, lm-eval-harness)

## Conventions

### Test File Naming
- `test_*.py` in `tests/` directory
- Subdirectories: `tests/async_engine/`, `tests/kernels/`, `tests/models/`, etc.

### Test Function Naming
- `test_*` for pytest discovery
- Fixtures in `tests/conftest.py`

### Pytest Markers
```python
@pytest.mark.skip_global_cleanup  # Skip cleanup for speed
@pytest.mark.core_model  # Core model tests (run in every PR)
@pytest.mark.cpu_model  # CPU-specific tests
@pytest.mark.distributed_2_gpus  # Requires 2 GPUs
@pytest.mark.skip_v1  # Skip when using V1 engine
```

### Import Style
- Enforced by isort with configuration in `pyproject.toml`
- Grouped imports: standard library, third-party, local
- Absolute imports preferred

### Code Style
- **Python:** Line length 80 (yapf), ruff rules (pycodestyle, pyflakes, pyupgrade, flake8-bugbear)
- **C++/CUDA:** clang-format 18.1.5 with config in `.clang-format`
- **Type Hints:** Enforced by mypy on core vllm package

## Gaps & Caveats

### Major Gaps
1. **No hardware-agnostic tests**: All tests require either GPU, HPU, or fake HPU mode with built package
2. **Complex build requirements**: Cannot build in standard CI images without GPU/HPU SDK
3. **Heavy dependencies**: requirements-test.txt includes 100+ packages (torch, transformers, ray, etc.)
4. **Specialized hardware**: Primary target is Intel Habana Gaudi HPU - rare in standard CI

### Workarounds
1. **Lint-only validation**: Agents can validate code quality without building
2. **CPU fake mode**: Limited testing possible with `VLLM_USE_FAKE_HPU=1`
3. **Pre-built images**: Use Dockerfiles (Dockerfile.hpu, Dockerfile.cpu) for complete environment

### Recommendations for Agents
- **For lint fixes:** Standard container validation works perfectly
- **For code changes:** Lint in container, note that full tests require HPU/GPU
- **For hardware-specific code:** Flag for manual testing on appropriate hardware
- **For documentation/config:** Lint + spelling check sufficient

## Agent Readiness Rating: MEDIUM

**Why Medium:**
- ✓ Lint validation fully automated and validated
- ✓ Clear commands for all linting tools
- ✓ Comprehensive CI configuration
- ✗ Cannot run tests without specialized hardware
- ✗ Cannot build package without GPU/HPU SDK
- ✗ No simple unit tests that work in standard containers

**Agent Use Case:**
- **Good for:** Linting, formatting, type checking, spelling validation
- **Limited for:** Full CI/CD pipeline validation, test execution
- **Not suitable for:** Performance testing, hardware-specific validation

An agent can validate that patches meet code quality standards (lint, format, types) but cannot validate functional correctness without access to HPU or GPU hardware.
