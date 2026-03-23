# Test Context: fms-guardrails-orchestrator

## Overview

**Repository**: opendatahub-io/fms-guardrails-orchestrator
**Language**: Rust (edition 2024)
**Build System**: Cargo
**Toolchain**: 1.92.0
**Agent Readiness**: **HIGH** - All lint and test commands validated successfully in container.

This is a Foundation Model Stack Guardrails Orchestrator server for invocation of detectors on text generation input/output. The project has comprehensive test coverage (120 tests), strict linting with clippy and rustfmt, and all validation commands work in a standard Rust container.

## Container Recipe

This section provides a complete recipe for validating patches. All commands have been validated.

### 1. Start Container

```bash
podman run -d --name test-context-fms-guardrails-orchestrator \
  -v $(pwd):/app:Z \
  -w /app \
  rust:1.92 \
  sleep infinity
```

If `podman` is unavailable, use `docker` instead.

### 2. Install System Dependencies

```bash
podman exec test-context-fms-guardrails-orchestrator bash -c \
  "apt-get update && apt-get install -y curl unzip protobuf-compiler"
```

This installs:
- `protobuf-compiler` (protoc) - required for gRPC code generation
- `curl`, `unzip` - utility tools

### 3. Install Nightly Rustfmt

```bash
podman exec test-context-fms-guardrails-orchestrator bash -c \
  "rustup component add --toolchain nightly-x86_64-unknown-linux-gnu rustfmt"
```

Nightly rustfmt is required for formatting checks (CI uses nightly for fmt).

### 4. Build Project

```bash
podman exec test-context-fms-guardrails-orchestrator bash -c \
  "cd /app && cargo build"
```

**Expected**: Build completes in ~30 seconds (first build). Compiles protobuf definitions from `protos/` directory and builds the orchestrator binary.

### 5. Run Format Check (Lint)

```bash
podman exec test-context-fms-guardrails-orchestrator bash -c \
  "cd /app && cargo +nightly fmt --check --all"
```

**Expected**: No output if formatting is correct. Exit code 0 = pass.

**To auto-fix formatting issues**:
```bash
podman exec test-context-fms-guardrails-orchestrator bash -c \
  "cd /app && cargo +nightly fmt --all"
```

### 6. Run Clippy Linter

```bash
podman exec test-context-fms-guardrails-orchestrator bash -c \
  "cd /app && cargo clippy --no-deps --all-targets --all-features"
```

**Expected**: "Finished `dev` profile" with no warnings. Exit code 0 = pass.

Note: CI sets `RUSTFLAGS="-Dwarnings"` which treats warnings as errors. Clippy must produce zero warnings.

### 7. Run Tests

```bash
podman exec test-context-fms-guardrails-orchestrator bash -c \
  "cd /app && cargo test"
```

**Expected**:
- 34 unit tests pass (in lib)
- 86 integration tests pass across 12 test files
- Total: 120 tests passed
- Completes in ~10 seconds

**Test files**:
- `tests/chat_completions_streaming.rs` (16 tests)
- `tests/chat_completions_unary.rs` (8 tests)
- `tests/chat_detection.rs` (4 tests)
- `tests/classification_with_text_gen.rs` (7 tests)
- `tests/completions_streaming.rs` (15 tests)
- `tests/completions_unary.rs` (8 tests)
- `tests/context_docs_detection.rs` (4 tests)
- `tests/detection_on_generation.rs` (4 tests)
- `tests/generation_with_detection.rs` (4 tests)
- `tests/streaming_classification_with_gen.rs` (8 tests)
- `tests/streaming_content_detection.rs` (4 tests)
- `tests/text_content_detection.rs` (4 tests)

### 8. Run Single Test File

To run tests from a specific file:

```bash
podman exec test-context-fms-guardrails-orchestrator bash -c \
  "cd /app && cargo test --test chat_detection"
```

Replace `chat_detection` with the test file stem (filename without `.rs` extension).

### 9. Run Single Test Function

To run a specific test function:

```bash
podman exec test-context-fms-guardrails-orchestrator bash -c \
  "cd /app && cargo test no_detections"
```

Replace `no_detections` with any test function name. Cargo will run all tests matching that name.

### 10. Cleanup

```bash
podman rm -f test-context-fms-guardrails-orchestrator
```

Always clean up the container when done.

## Validation Results

All commands were validated in a `rust:1.92` container:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install deps | `apt-get install protobuf-compiler` | ✅ Pass | Installed protoc 3.21.12 |
| Install nightly | `rustup component add nightly rustfmt` | ✅ Pass | Nightly 1.96.0 |
| Build | `cargo build` | ✅ Pass | Completed in 29.56s |
| Format check | `cargo +nightly fmt --check --all` | ✅ Pass | No formatting issues |
| Lint | `cargo clippy --no-deps --all-targets --all-features` | ✅ Pass | 0 warnings |
| Test | `cargo test` | ✅ Pass | 120/120 tests passed in ~10s |

## CI/CD Configuration

**CI System**: GitHub Actions (`.github/workflows/test.yml`)

**Triggers**:
- Push to `main`, `incubation`, `stable` branches
- Pull requests to same branches (when not draft)

**Gating Checks** (all required for merge):
1. **Build**: `cargo build`
2. **Format**: `cargo +nightly fmt --check --all`
3. **Lint**: `cargo clippy --no-deps --all-targets --all-features`
4. **Test**: `cargo test`

**CI Environment**:
- Runner: `ubuntu-latest`
- Rust toolchain: 1.92.0 (from `rust-toolchain.toml`)
- Protoc version: 26.0 (installed from GitHub releases)
- Environment variables:
  - `CARGO_TERM_COLOR=always`
  - `RUSTFLAGS="-Dwarnings"` (treats warnings as compilation errors)
  - `PROTOC_VERSION="26.0"`

**Workflow Steps**:
1. Install nightly rustfmt component
2. Install protoc 26.0
3. Checkout code
4. Cache Rust dependencies (`~/.cargo/registry`, `~/.cargo/git`, `target/`)
5. Run build
6. Run formatter check
7. Run clippy linter
8. Run tests

## Conventions

### Test File Patterns
- **Integration tests**: `tests/*.rs` - each file is a separate test binary
- **Unit tests**: Inline in source files with `#[test]` attribute or in `src/**/tests.rs` modules
- **Test utilities**: `tests/common/` - shared test helpers (mod.rs, orchestrator.rs, etc.)
- **Test resources**: `tests/resources/` - test configuration and fixtures

### Test Naming
- Test functions use descriptive names: `no_detections`, `input_detectors`, `client_error`, etc.
- Async tests use `#[test(tokio::test)]` attribute
- Tests return `Result<(), anyhow::Error>` for error handling

### Import Style
Per `rustfmt.toml`:
- `group_imports = "StdExternalCrate"` - groups std, external, and crate imports
- `imports_granularity = "Crate"` - merges imports from same crate

### Code Organization
- Library code: `src/lib.rs` and modules in `src/`
- Binary: `src/main.rs`
- Proto definitions: `protos/` - compiled via `build.rs` using tonic-build
- Configuration: `config/config.yaml` (example server config)

## Project-Specific Notes

### Protocol Buffers
The project uses gRPC with tonic. Protocol buffer definitions in `protos/` are compiled at build time via `build.rs`. The `protoc` compiler must be available in the system PATH.

### Test Infrastructure
Tests use the `mocktail` crate (from IBM GitHub) to create HTTP mock servers. The `TestOrchestratorServer` in `tests/common/orchestrator.rs` provides test harness for spinning up the orchestrator with mock detector services.

Test configuration is loaded from `tests/test_config.yaml` which defines mock detectors, chunkers, and generation services.

### Running the Server
To run the orchestrator server locally:

```bash
cargo run --bin fms-guardrails-orchestr8
```

Requires a valid configuration file. Set `ORCHESTRATOR_CONFIG` environment variable to point to config file, or use default `config/config.yaml`.

### Pre-commit Hooks
The repo uses pre-commit hooks (`.pre-commit-config.yaml`):
- `cargo +nightly fmt` - format check
- `cargo check` - compilation check
- `cargo clippy -- -D warnings` - lint with warnings as errors

To install: `pre-commit install` (requires pre-commit to be installed via pip).

## Gaps & Caveats

**None identified**. This repository has:
- ✅ Comprehensive test coverage (120 tests)
- ✅ Clear CI configuration
- ✅ Working lint and format commands
- ✅ All commands validated in container
- ✅ Good documentation in README.md
- ✅ Standard Rust project structure

The project is in excellent shape for automated patch validation.
