# Test Context: guardrails-regex-detector

## Overview

**Repository:** opendatahub-io/guardrails-regex-detector
**Language:** Rust
**Build System:** Cargo
**Agent Readiness:** **medium** - Tests and format check pass, but clippy has 8 lint violations that need fixing. No external CI configured but all validation commands work.

This is a lightweight HTTP server for parsing text using regex patterns to detect PII (SSN, credit cards, email addresses). It integrates with the FMS Guardrails Orchestrator.

---

## Container Recipe

This is a complete, executable recipe for validating patches in a container. Follow these steps verbatim:

### 1. Start the container

```bash
REPO_PATH=/path/to/guardrails-regex-detector
podman run -d --name test-context-guardrails-regex-detector \
  -v "${REPO_PATH}:/app:Z" \
  -w /app \
  rust:1.84.0 \
  sleep infinity
```

If `podman` is not available, use `docker` instead.

### 2. Install required components

```bash
podman exec test-context-guardrails-regex-detector bash -c \
  "rustup component add rustfmt clippy"
```

### 3. Install dependencies and build

```bash
podman exec test-context-guardrails-regex-detector bash -c \
  "cd /app && cargo build"
```

**Expected:** Dependencies download and compile successfully in ~9 seconds.

### 4. Run tests

```bash
podman exec test-context-guardrails-regex-detector bash -c \
  "cd /app && cargo test"
```

**Expected:** 1 test passes
**Output snippet:**
```
running 1 test
test detectors::tests::test_regex_match ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

### 5. Run format check

```bash
podman exec test-context-guardrails-regex-detector bash -c \
  "cd /app && cargo fmt --check"
```

**Expected:** Exit code 0, no output (formatting is correct)

### 6. Run clippy linter

```bash
podman exec test-context-guardrails-regex-detector bash -c \
  "cd /app && cargo clippy --all-targets --all-features -- -D warnings"
```

**Expected:** Exit code 101 (lint violations found)
**Current status:** 8 violations detected:
- 3x `ptr_arg` - using `&String` instead of `&str`
- 2x `needless_return` - unnecessary return statements
- 1x `needless_borrow` - unnecessary reference
- 1x `useless_format` - using `format!` where `.to_string()` would work
- 1x `type_complexity` - complex HashMap type definition

**Note:** This is NOT a broken command - the linter works correctly but found code issues.

### 7. Run a single test by name

```bash
podman exec test-context-guardrails-regex-detector bash -c \
  "cd /app && cargo test test_regex_match"
```

### 8. Build release binary (optional)

```bash
podman exec test-context-guardrails-regex-detector bash -c \
  "cd /app && cargo build --release"
```

**Expected:** Optimized binary built in ~10 seconds at `target/release/regex-detector`

### 9. Clean up

```bash
podman rm -f test-context-guardrails-regex-detector
```

---

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install | `cargo build` | 0 | ✅ PASS | Dependencies compiled in 9.17s |
| Test | `cargo test` | 0 | ✅ PASS | 1 test passed |
| Format | `cargo fmt --check` | 0 | ✅ PASS | No formatting issues |
| Lint | `cargo clippy --all-targets --all-features -- -D warnings` | 101 | ⚠️ VIOLATIONS | 8 lint violations found |
| Release | `cargo build --release` | 0 | ✅ PASS | Optimized build successful |

### Lint Violations Detail

The clippy linter found 8 violations in `src/detectors.rs`:

1. **Lines 38, 50, 62** - `ptr_arg`: Functions accept `&String` but should use `&str`
2. **Lines 90, 92** - `needless_return`: Explicit return statements not needed
3. **Line 80** - `needless_borrow`: Unnecessary reference `&content`
4. **Line 102** - `useless_format`: Use `.to_string()` instead of `format!`
5. **Lines 106-109** - `type_complexity`: Complex HashMap type needs type alias

---

## CI/CD

**System:** Multi-stage Dockerfile (no GitHub Actions)

### Gating Checks

The Dockerfile defines three build stages that serve as CI gates:

```dockerfile
# Stage 1: Tests (line 24-26)
FROM regex-detector-builder AS tests
RUN cargo test

# Stage 2: Lint (line 28-30)
FROM regex-detector-builder AS lint
RUN cargo clippy --all-targets --all-features -- -D warnings

# Stage 3: Format (line 32-34)
FROM regex-detector-builder AS format
RUN cargo fmt --check
```

These stages would gate container builds but no external CI system (GitHub Actions, Tekton, Jenkins) is configured.

### Building with CI validation

To build the container with all checks:

```bash
# Test stage
podman build --target tests -t regex-detector:tests .

# Lint stage (currently fails due to violations)
podman build --target lint -t regex-detector:lint .

# Format stage
podman build --target format -t regex-detector:format .

# Full release build
podman build -t regex-detector:latest .
```

---

## Conventions

### Test Organization
- Tests are inline with source code using `#[cfg(test)]` modules
- Test functions marked with `#[test]` attribute
- Naming convention: `test_*` prefix
- Current test: `src/detectors.rs::tests::test_regex_match`

### Test Execution
- **All tests:** `cargo test`
- **Specific test:** `cargo test test_regex_match`
- **Verbose output:** `cargo test -- --nocapture`
- **Show output:** `cargo test -- --show-output`

### Code Style
- Rust 2021 edition
- Format: enforced by rustfmt (currently passing)
- Lint: clippy with all warnings as errors
- Import style: Standard Rust module system

### Source Structure
```
src/
├── main.rs         - HTTP server setup with Axum framework
└── detectors.rs    - Regex detection logic and tests
```

---

## Gaps & Caveats

### Missing Infrastructure
1. **No GitHub Actions workflows** - All CI validation is defined only in Dockerfile
2. **No pre-commit hooks** - No automated local validation before commits
3. **No coverage measurement** - Cannot track test coverage percentage
4. **Limited CI visibility** - No external CI dashboard or status checks on PRs

### Code Quality Issues
1. **Clippy violations** - 8 lint errors prevent clean clippy run
2. **Test coverage** - Only 1 unit test exists, testing basic regex matching
3. **No integration tests** - No tests for HTTP endpoints or end-to-end flows
4. **No test fixtures** - Test data is hardcoded in test functions

### Testing Limitations
- Tests only cover `regex_match` function, not `email_address_detector`, `ssn_detector`, `credit_card_detector`
- No HTTP endpoint testing (the `/api/v1/text/contents` POST endpoint is untested)
- No validation of JSON request/response handling
- No tests for error cases (invalid regex, empty input, malformed requests)

### Patch Validation Workflow

An agent validating a patch should:

1. ✅ **Can run tests** - `cargo test` works and reports pass/fail
2. ✅ **Can check formatting** - `cargo fmt --check` validates style
3. ⚠️ **Lint check may fail** - Current code has violations, so baseline is "exit 101"
4. ❌ **No PR checks configured** - Cannot see CI status in GitHub UI
5. ❌ **No coverage diff** - Cannot measure if patch improves/degrades coverage

**Recommendation:** Treat exit code 101 from clippy as the baseline. If a patch introduces new violations, the exit code remains 101 but the violation count increases. Parse clippy output to count violations for comparison.

---

## Quick Reference

### Essential Commands

```bash
# Setup (one-time)
rustup component add rustfmt clippy

# Development workflow
cargo build                    # Build debug
cargo test                     # Run all tests
cargo test test_name           # Run specific test
cargo fmt                      # Auto-format code
cargo fmt --check              # Check formatting only
cargo clippy --fix            # Auto-fix lint issues (where possible)

# Validation (what CI would run)
cargo test
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings

# Production
cargo build --release          # Optimized build
```

### Test Output Parsing

Success indicators:
- Tests: `test result: ok. N passed; 0 failed`
- Format: Empty output with exit 0
- Lint: Exit 0 (no violations)

Failure indicators:
- Tests: `test result: FAILED. N passed; M failed`
- Format: Lists files needing formatting
- Lint: Lists violations with line numbers and suggestions

---

## Agent Readiness: MEDIUM

### What Works ✅
- Standard Rust toolchain setup
- Tests run cleanly in container
- Format validation passes
- Build succeeds (debug and release)
- Single test execution works
- All commands are well-defined and repeatable

### What Needs Work ⚠️
- Clippy has existing violations (baseline is "failing")
- No external CI for PR validation
- Limited test coverage
- No integration/E2E tests

### Automation Suitability

An agent can:
- ✅ Clone repo and run tests in container
- ✅ Validate formatting on patches
- ✅ Build debug and release binaries
- ⚠️ Run clippy (but must tolerate baseline violations)
- ❌ Cannot check CI status (no GitHub Actions)
- ❌ Cannot measure coverage impact

**Bottom line:** Suitable for basic patch validation (tests + format), but lint baseline is "failing" and no CI integration exists.
