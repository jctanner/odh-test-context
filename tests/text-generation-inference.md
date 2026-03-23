# Test Context: text-generation-inference (opendatahub-io)

**Agent Readiness: MEDIUM** — Python unit tests validated successfully (35/35 passed), but Rust formatting violations exist, integration tests require infrastructure, and no Rust unit tests found.

---

## Overview

**Languages:** Rust, Python
**Build System:** Cargo (Rust workspace), Poetry (Python), Docker multi-stage
**Test Framework:** pytest (Python), cargo test (Rust - no tests found)
**CI System:** GitHub Actions (build.yml, test.yml)
**Python Version:** 3.11+
**Rust Version:** 1.77.2 (via rust-toolchain.toml)

This is a multi-language inference server project with:
- **Rust components**: router (HTTP/gRPC server), launcher (process orchestration)
- **Python components**: server (inference backend using PyTorch/Transformers), integration tests
- **Protobuf**: gRPC interface definitions compiled to Python/Rust

---

## Container Recipe

This recipe provides a complete, copy-paste setup for validating patches in an isolated environment.

### 1. Start Container

```bash
podman run -d --name test-context-tgi \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-tgi bash -c "apt-get update && apt-get install -y \
  make git gcc g++ curl unzip protobuf-compiler"
```

### 3. Install Python Test Dependencies

```bash
podman exec test-context-tgi bash -c "pip install --upgrade pip && \
  pip install pytest pytest-asyncio"
```

### 4. Install PyTorch (CPU version for testing)

```bash
podman exec test-context-tgi bash -c \
  "pip install 'torch==2.2.1+cpu' --index-url https://download.pytorch.org/whl/cpu --no-cache-dir"
```

### 5. Generate Protobuf Files and Install Server

```bash
podman exec test-context-tgi bash -c "cd /app/server && make gen-server"
```

```bash
podman exec test-context-tgi bash -c \
  "cd /app/server && pip install -e '.[accelerate]' --no-cache-dir"
```

**Note:** Editable install (`-e`) is required for protobuf imports to resolve correctly.

### 6. Run Python Unit Tests (✓ VALIDATED)

```bash
podman exec test-context-tgi bash -c \
  "cd /app && pytest -sv --ignore=server/tests/test_utils.py server/tests"
```

**Expected Result:** 35 tests pass in ~24 seconds

### 7. Run Single Test File

```bash
podman exec test-context-tgi bash -c \
  "cd /app && pytest -sv server/tests/test_logit_processors.py"
```

### 8. Run Single Test

```bash
podman exec test-context-tgi bash -c \
  "cd /app && pytest -sv server/tests/test_logit_processors.py::test_alignment_repetition_penalty_logits_processor"
```

### 9. Install Rust (for linting Rust code)

```bash
podman exec test-context-tgi bash -c \
  "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain 1.77.2"
```

### 10. Run Rust Formatting Check (⚠ FAILS - violations exist)

```bash
podman exec test-context-tgi bash -c \
  ". \$HOME/.cargo/env && rustup component add rustfmt && cd /app && cargo fmt --check"
```

**Expected Result:** Exit code 1 with formatting violations in `launcher/src/main.rs` and `router/src/main.rs`

### 11. Fix Rust Formatting

```bash
podman exec test-context-tgi bash -c \
  ". \$HOME/.cargo/env && cd /app && cargo fmt"
```

### 12. Cleanup

```bash
podman rm -f test-context-tgi
```

---

## Validation Results

### ✓ Python Unit Tests (PASSED)

**Command:** `pytest -sv --ignore=server/tests/test_utils.py server/tests`
**Exit Code:** 0
**Tests:** 35 passed in 24.04s
**Coverage:**
- `test_logit_processors.py`: 6 tests (temperature, top-k, top-p, repetition penalty, etc.)
- `test_prompt_cache.py`: 28 tests (cache eviction, PEFT adapters, safetensors loading)
- `test_utils/test_convert.py`: 1 test (model conversion from PyTorch to safetensors)

**Sample Output:**
```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.2, pluggy-1.6.0
collected 35 items

server/tests/test_logit_processors.py::test_alignment_repetition_penalty_logits_processor PASSED
...
============================= 35 passed in 24.04s ==============================
```

### ⚠ Rust Formatting (FAILED - violations exist)

**Command:** `cargo fmt --check`
**Exit Code:** 1
**Issues Found:**
- `launcher/src/main.rs`: Line 181 (long chain formatting), 188 (function call formatting), 495 (trailing whitespace), 523 (trailing whitespace), 824 (function signature formatting)
- `router/src/main.rs`: Line 7 (import grouping)
- Missing `pb.rs` files (expected - generated during build)

**Sample Output:**
```
Diff in /app/launcher/src/main.rs at line 181:
-        PathBuf::from(home).join(".cache").join("huggingface").join("hub")
+        PathBuf::from(home)
+            .join(".cache")
+            .join("huggingface")
+            .join("hub")
```

**Fix:** Run `cargo fmt` to auto-fix all violations.

### ✗ Integration Tests (NOT VALIDATED)

**Command:** `make integration-tests` (internally runs `pytest -sv text_generation_tests/test_server.py`)
**Reason:** Requires running text-generation-server with a loaded model (e.g., bloom-560m), which needs:
- Running gRPC server on localhost
- Model weights downloaded from HuggingFace
- GPU or CPU resources for inference

**CI Approach:** GitHub Actions builds a full `cpu-tests` Docker image with server, router, and launcher installed, then runs integration tests against a test server.

---

## CI/CD Configuration

### GitHub Actions Workflows

#### build.yml (Gating)
**Trigger:** `pull_request`, `push` to `main`
**Job:** Build `server-release` Docker image
**Command:**
```bash
docker build --target=server-release \
  --build-arg GIT_COMMIT_HASH=$(git rev-parse HEAD) \
  -t quay.io/wxpe/text-gen-server .
```
**Gating:** Yes (must pass to merge)

#### test.yml (Gating)
**Trigger:** `pull_request`, `push` to `main`
**Jobs:**
1. **build** — Build `cpu-tests` Docker image
2. **test-python** — Run `make python-tests`
   - Command: `docker run cpu-tests:0 pytest -sv --ignore=server/tests/test_utils.py server/tests`
3. **integration-tests** — Run `make integration-tests`
   - Command: `docker run cpu-tests:0 -w /usr/src/integration_tests make test`
   - Runs: `pytest -sv text_generation_tests/test_server.py`

**Gating:** Yes (both jobs must pass to merge)

---

## Conventions

### Test File Naming
- **Python:** `test_*.py` in `server/tests/` and `integration_tests/text_generation_tests/`
- **Rust:** `*_test.rs` or `#[cfg(test)]` modules (none found)

### Test Function Naming
- **Python:** `test_*` functions, pytest style
- **Rust:** `#[test]` attribute (none found)

### Import Style
- **Python:** Standard imports
- **Rust:** Configured for `group_imports = StdExternalCrate`, `imports_granularity = Crate` (requires nightly Rust for these features)

### Dependency Management
- **Python:** Poetry (`poetry.lock`, `pyproject.toml`)
- **Rust:** Cargo workspace (`Cargo.toml`, `Cargo.lock`)

### Protobuf Generation
- **Python:** `make gen-server` in `server/` directory
- **Rust:** Happens during `cargo build` via `build.rs`

---

## Gaps & Caveats

### No Python Linting Configured
The project does **not** configure any Python linting tools in `pyproject.toml`:
- No `ruff`, `flake8`, `pylint`, `mypy`, or `black`
- No pre-commit hooks

To add Python linting, install manually:
```bash
pip install ruff
ruff check server/
```

### Rustfmt Violations Exist
The current codebase has **rustfmt violations** that will fail `cargo fmt --check`. These must be fixed before CI passes if formatting checks are enforced.

### No Rust Unit Tests
The Rust components (router, launcher) have **zero unit tests**. Only integration tests exist (Python-based, calling the compiled binaries).

### Integration Tests Require Infrastructure
Cannot validate integration tests in a simple container because they require:
- A running `text-generation-server` process
- A loaded ML model (e.g., `bigscience/bloom-560m`)
- gRPC server listening on `localhost:8033`

CI solves this by:
1. Building the full `cpu-tests` Docker image (includes server, router, launcher)
2. Running the server inside the container
3. Running integration tests against it

### Docker-Only Testing Workflow
The Makefile targets `python-tests` and `integration-tests` both require Docker and run tests inside containers. This makes local testing more complex than a simple `pytest` command.

### Rustfmt Feature Warnings
The rustfmt config uses **unstable features** (`imports_granularity`, `group_imports`) that require nightly Rust. The project uses stable 1.77.2, so these features are ignored with warnings.

---

## Quick Reference

### Commands Cheat Sheet

| Task | Command |
|------|---------|
| Install Python server | `cd server && make gen-server && pip install -e '.[accelerate]'` |
| Run Python unit tests | `pytest -sv --ignore=server/tests/test_utils.py server/tests` |
| Run single test | `pytest -sv {file}::{test_name}` |
| Check Rust formatting | `cargo fmt --check` |
| Fix Rust formatting | `cargo fmt` |
| Build server Docker image | `make build` (or `docker build --target=server-release .`) |
| Build test Docker image | `make build-test-image` |
| Run Python tests (Docker) | `make python-tests` |
| Run integration tests (Docker) | `make integration-tests` |

### Environment Variables

- `CUDA_VISIBLE_DEVICES=""` — Disable GPU for CPU-only testing
- `HF_HUB_CACHE=/transformers_cache` — HuggingFace model cache location
- `BUILD_EXTENSIONS=True` — Enable custom CUDA kernel compilation (requires GPU)

---

## Agent Usage Recommendations

### For Patch Validation (Python Code)

1. **Spin up container** with recipe steps 1-5
2. **Run Python unit tests** (step 6) — fast, reliable, no infrastructure needed
3. **Check for regressions** — all 35 tests should pass
4. **Optionally lint** — install `ruff` and run basic checks (not enforced by CI)

### For Patch Validation (Rust Code)

1. **Spin up container** with Rust installed (steps 1-2, 9)
2. **Check formatting** (step 10) — `cargo fmt --check`
3. **Auto-fix violations** (step 11) — `cargo fmt`
4. **Note:** Cannot run full `cargo build` without protoc and build setup

### For Full CI Simulation

Use the Dockerfile approach (requires significant time/resources):
```bash
make build-test-image  # Builds cpu-tests Docker image
make python-tests      # Runs in container
make integration-tests # Runs in container (requires model download)
```

### Limitations for AI Agents

- **Integration tests:** Require model downloads (~1GB+) and running server — skip for quick validation
- **Rust build:** Full compilation needs protoc, many dependencies — use `cargo fmt` for quick checks
- **No linting enforcement:** Python code has no enforced linting, so style issues may exist
- **Docker dependency:** CI tests run in Docker, making local reproduction more complex

---

## Summary

**Agent Readiness: MEDIUM**

✓ **What works:**
- Python unit tests are fast, reliable, and validate core logic (35 tests)
- Test setup is well-documented (Makefile targets, pyproject.toml)
- Rust formatting checks work (though violations exist)

⚠ **What's tricky:**
- Integration tests need infrastructure (skip for quick validation)
- No Python linting configured (agents should add their own)
- Rustfmt violations exist in current codebase
- Docker-based testing workflow adds complexity

**Bottom line:** An agent can validate Python patches with confidence. For Rust patches, formatting checks work but full build/test requires more setup. Integration tests should be deferred to CI.
