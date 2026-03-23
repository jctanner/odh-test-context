# Test Context: vllm-orchestrator-gateway

**Generated:** 2026-03-22T20:39:00Z
**Organization:** opendatahub-io
**Agent Readiness:** medium - Lint and build commands work. Tests run but have 1 failing test due to code bug. Formatting and clippy violations need fixing.

## Overview

This is a Rust 1.84.0 project that builds a gateway service for vLLM orchestration. The build system is cargo, with CI enforcing rustfmt formatting, clippy linting, unit tests, and release builds.

**Languages:** Rust
**Build System:** cargo
**Test Framework:** Rust built-in test framework
**Linters:** rustfmt, clippy

## Container Recipe

This recipe provides everything needed to validate patches in an isolated environment.

### 1. Start Container

```bash
podman run -d --name test-context-vllm-orchestrator-gateway \
  -v $(pwd):/app:Z \
  -w /app \
  rust:1.84.0 \
  sleep infinity
```

If `podman` is unavailable, use `docker` instead.

### 2. Install Dependencies

Dependencies are automatically fetched and built by cargo. No separate install step needed.

```bash
podman exec test-context-vllm-orchestrator-gateway bash -c "cd /app && cargo fetch"
```

Or let the first `cargo build` or `cargo test` command handle it automatically.

### 3. Run Linters

#### Format Check

```bash
podman exec test-context-vllm-orchestrator-gateway bash -c "cd /app && cargo fmt --all -- --check"
```

**Expected:** Exit code 1 (formatting violations found in current codebase)
**Validated:** ✅ Command works. Found formatting issues in `src/config.rs` and `src/main.rs`.

To auto-fix formatting:

```bash
podman exec test-context-vllm-orchestrator-gateway bash -c "cd /app && cargo fmt --all"
```

#### Clippy Linting

```bash
podman exec test-context-vllm-orchestrator-gateway bash -c "cd /app && cargo clippy --all-targets --all-features -- -D warnings"
```

**Expected:** Exit code 101 (4 warnings treated as errors with -D flag)
**Validated:** ✅ Command works. Found 4 issues:
- `expect_fun_call` in src/config.rs:57
- `needless_return` in src/main.rs:198
- `len_zero` in src/main.rs:310
- `manual_strip` in src/main.rs:530-531

### 4. Run Tests

#### All Tests

```bash
podman exec test-context-vllm-orchestrator-gateway bash -c "cd /app && cargo test --verbose"
```

**Expected:** Exit code 101 (3 pass, 1 fail)
**Validated:** ✅ Command works. Test failure is a legitimate bug: `test_validate_multiple_same_server_output_detectors` should panic but doesn't.

#### Single Test

```bash
podman exec test-context-vllm-orchestrator-gateway bash -c "cd /app && cargo test --verbose test_validate_registered_detectors"
```

### 5. Build

```bash
podman exec test-context-vllm-orchestrator-gateway bash -c "cd /app && cargo build --release --verbose"
```

**Expected:** Exit code 0 (success)
**Validated:** ✅ Build completes in ~18 seconds.

### 6. Cleanup

```bash
podman rm -f test-context-vllm-orchestrator-gateway
```

## Validation Results

All commands were validated in a live `rust:1.84.0` container:

| Step | Command | Exit Code | Result |
|------|---------|-----------|--------|
| Install | `cargo fetch` | 0 | ✅ 120+ crates downloaded |
| Format | `cargo fmt --all -- --check` | 1 | ✅ Found violations (expected) |
| Clippy | `cargo clippy --all-targets --all-features -- -D warnings` | 101 | ✅ Found 4 warnings |
| Test | `cargo test --verbose` | 101 | ⚠️ 3 passed, 1 failed (code bug) |
| Build | `cargo build --release --verbose` | 0 | ✅ Success |

**Summary:** Linting and build infrastructure work correctly. One test fails due to a bug in the config validation logic (not a test infrastructure issue).

## CI/CD

**System:** GitHub Actions
**Config:** `.github/workflows/tests.yaml`

### Gating Checks (Required for Merge)

All commands run on `pull_request` to `main`, `incubation`, and `stable` branches:

1. **Format Check**
   ```bash
   cargo fmt --all -- --check
   ```

2. **Clippy**
   ```bash
   cargo clippy --all-targets --all-features -- -D warnings
   ```

3. **Tests**
   ```bash
   cargo test --verbose
   ```

4. **Build**
   ```bash
   cargo build --release --verbose
   ```

### Advisory Checks (Non-blocking)

- **Trivy Security Scan:** Filesystem vulnerability scan via `aquasecurity/trivy-action@0.28.0`

### CI Environment

- **Rust Toolchain:** 1.84.0 (pinned in `rust-toolchain.toml`)
- **Components:** rustfmt, clippy
- **Caching:** Cargo registry, git, and target directory cached with `actions/cache@v4`

## Conventions

### Test Structure

- **Location:** Tests are inline in source files within `#[cfg(test)]` modules
- **Current Tests:** 4 tests in `src/config.rs` (lines 111-237)
- **Naming:** Test functions use `test_` prefix with `#[test]` attribute
- **Panic Tests:** Tests expected to panic use `#[should_panic]` attribute

### Test Patterns

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_something() {
        // test code
    }

    #[test]
    #[should_panic]
    fn test_validation_failure() {
        // code expected to panic
    }
}
```

### Running Specific Tests

```bash
# Run all tests in config module
cargo test config::tests

# Run a specific test
cargo test test_validate_registered_detectors

# Run with pattern matching
cargo test validate
```

## Gaps & Caveats

1. **Test Failure:** `test_validate_multiple_same_server_output_detectors` fails - the validation function has a bug where it incorrectly inserts into the wrong HashSet (line 96 in src/config.rs uses `seen_output.insert` but should check `seen_output` not `seen_input`).

2. **Formatting Violations:** Code needs `cargo fmt --all` to fix formatting before it will pass CI.

3. **Clippy Warnings:** 4 clippy warnings need to be addressed:
   - Replace `expect(&format!(...))` with `unwrap_or_else`
   - Remove unnecessary `let` binding before return
   - Replace `.len() > 0` with `!is_empty()`
   - Use `strip_prefix()` instead of manual string slicing

4. **Limited Test Coverage:** Only `src/config.rs` has tests. No tests for `src/main.rs` or `src/api.rs`.

5. **No Integration Tests:** Only unit tests exist. No tests that exercise the HTTP endpoints or orchestrator integration.

6. **No Coverage Reporting:** No code coverage metrics configured in CI.

7. **Runtime Dependencies:** The application requires external services (FMS Guardrails Orchestrator, detectors, vLLM) for runtime operation, but these are not needed for unit tests.

## Patch Validation Workflow

To validate a patch:

1. **Apply patch** to the repository
2. **Start container** (step 1 of Container Recipe)
3. **Run format check** - must pass for CI
4. **Run clippy** - must pass for CI (no warnings allowed with -D flag)
5. **Run tests** - currently 1 test fails on main branch, patches should not add new failures
6. **Run build** - must complete successfully
7. **Cleanup container**

A patch is **ready to merge** if:
- Format check passes (exit code 0)
- Clippy passes (exit code 0)
- Tests pass or maintain existing pass/fail ratio (3/4 passing is current baseline)
- Build succeeds (exit code 0)

## Additional Notes

- **Rust Version:** Pinned to 1.84.0 via `rust-toolchain.toml` - this is automatically respected by rustup
- **Components:** `rustfmt` and `clippy` are declared in the toolchain file and auto-installed
- **Build Time:** Release build takes ~18 seconds in container (first build takes longer for dependency compilation)
- **Container Image:** `rust:1.84.0` (Debian-based, ~1.5GB) includes rustup, cargo, and standard Rust toolchain
- **No System Dependencies:** Pure Rust project with no system library dependencies beyond libc/openssl (provided by base image)
