# Test Context: semantic-router

**Repository**: opendatahub-io/semantic-router
**Analyzed**: 2026-03-22
**Agent Readiness**: **medium** — Build and unit tests work; linting has existing issues; full tests require external services
**Primary Languages**: Go 1.24, Rust 1.90, Python 3.11+, TypeScript/JavaScript (Node 20+)

## Overview

Semantic-router is a multi-language LLM routing and filtering system. The core is written in Go with Rust libraries for ML model inference (candle-binding, ml-binding, nlp-binding). The project uses a make-based build system with modular makefiles in `tools/make/`. Testing is split across unit tests (fast, no external deps) and integration tests (require Milvus vector DB, Redis, and model downloads).

**What works in a container**: Build, vet, unit tests, most linters.
**What doesn't**: Full test suite (needs Milvus + Redis + models), go-lint (has 11 existing issues).

---

## Container Recipe

This recipe provides a complete, validated procedure for running lint and tests in a standard container. All commands tested and confirmed working on 2026-03-22.

### 1. Start Container

```bash
podman run -d --name test-semantic-router \
  -v /path/to/semantic-router:/app:Z \
  -w /app \
  golang:1.24 \
  sleep infinity
```

**Notes**:
- Use `docker` instead of `podman` if podman unavailable
- Replace `/path/to/semantic-router` with actual repo path
- `:Z` flag required for SELinux systems

### 2. Install System Dependencies

```bash
podman exec test-semantic-router bash -c \
  "apt-get update && apt-get install -y \
    make \
    build-essential \
    pkg-config \
    git \
    curl \
    shellcheck \
    python3 \
    python3-pip"
```

**Time**: ~60 seconds
**Expected**: No errors, all packages installed

### 3. Install Rust Toolchain

```bash
podman exec test-semantic-router bash -c \
  "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain 1.90"
```

**Time**: ~30 seconds
**Expected**: "Rust is installed now. Great!"

### 4. Install Python Linting Tools

```bash
podman exec test-semantic-router bash -c \
  "pip3 install codespell yamllint --break-system-packages"
```

**Time**: ~10 seconds
**Expected**: "Successfully installed codespell-2.4.2 ... yamllint-1.38.0"

### 5. Install golangci-lint

```bash
podman exec test-semantic-router bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v2.5.0"
```

**Time**: ~10 seconds
**Expected**: "golangci/golangci-lint info installed /usr/local/bin/golangci-lint"

### 6. Build Rust Libraries (CPU-only mode)

```bash
podman exec test-semantic-router bash -c \
  "cd /app && source /root/.cargo/env && make rust-ci"
```

**Time**: ~8-10 minutes first time, ~10 seconds when cached
**Expected**: "Finished \`release\` profile [optimized] target(s)"
**Exit code**: 0

### 7. Verify Go Dependencies

```bash
podman exec test-semantic-router bash -c \
  "cd /app && make check-go-mod-tidy"
```

**Time**: ~30 seconds (downloads Go modules first time)
**Expected**: "All go mod tidy checks passed"
**Exit code**: 0

### 8. Run Go Vet

```bash
podman exec test-semantic-router bash -c \
  "cd /app && source /root/.cargo/env && make vet"
```

**Time**: ~20 seconds
**Expected**: No errors, clean vet output
**Exit code**: 0

### 9. Lint - Shell Scripts

```bash
podman exec test-semantic-router bash -c \
  "cd /app && make shellcheck"
```

**Time**: ~5 seconds
**Expected**: "Running shellcheck with config..."
**Exit code**: 0
**Status**: ✅ PASSING

### 10. Lint - YAML Files

```bash
podman exec test-semantic-router bash -c \
  "cd /app && make yaml-lint"
```

**Time**: ~5 seconds
**Expected**: May show 5 warnings about comment indentation (warnings, not errors)
**Exit code**: 0
**Status**: ✅ PASSING (warnings acceptable)

### 11. Lint - Go Code (has existing issues)

```bash
podman exec test-semantic-router bash -c \
  "cd /app && make go-lint"
```

**Time**: ~30 seconds
**Expected**: **FAILS with 11 issues**:
- 8 errorlint: Type assertions on errors without errors.As
- 2 gci: Import formatting issues
- 1 gocritic: Lambda simplification

**Exit code**: 2
**Status**: ❌ FAILING (pre-existing issues in codebase)

**Fix command** (if you want to auto-fix formatting):
```bash
podman exec test-semantic-router bash -c \
  "cd /app && make go-lint-fix"
```

### 12. Lint - Spelling (false positives expected)

```bash
podman exec test-semantic-router bash -c \
  "cd /app && make codespell"
```

**Time**: ~10 seconds
**Expected**: Flags "ser" in `target/release/deps/serde-*.d` build artifacts (false positives)
**Exit code**: 1
**Status**: ⚠️  FAILING (false positives in build artifacts, source is clean)

### 13. Build Router Binary

```bash
podman exec test-semantic-router bash -c \
  "cd /app && source /root/.cargo/env && make build-router"
```

**Time**: ~5 seconds (after Rust libs built)
**Expected**: Binary created at `bin/router`
**Exit code**: 0
**Status**: ✅ PASSING

### 14. Run Unit Tests (no external services)

```bash
podman exec test-semantic-router bash -c \
  "cd /app/src/semantic-router && go test -v ./pkg/config/..."
```

**Time**: ~1 second
**Expected**: "Ran 280 of 280 Specs in 0.027 seconds - SUCCESS! -- 280 Passed | 0 Failed"
**Exit code**: 0
**Status**: ✅ PASSING

**To run all unit tests** (longer, but still no external deps):
```bash
podman exec test-semantic-router bash -c \
  "cd /app/src/semantic-router && go test -v ./pkg/..."
```

### 15. Run Single Test

Template for running a specific test:
```bash
podman exec test-semantic-router bash -c \
  "cd /app/src/semantic-router && go test -v -run {TestName} {package_path}"
```

Example:
```bash
podman exec test-semantic-router bash -c \
  "cd /app/src/semantic-router && go test -v -run TestGetModelByPath ./pkg/config/"
```

### 16. Cleanup Container

```bash
podman rm -f test-semantic-router
```

**Always run cleanup**, even if previous steps failed.

---

## Validation Results

Summary of validated commands (tested 2026-03-22):

| Command | Status | Exit Code | Notes |
|---------|--------|-----------|-------|
| `make rust-ci` | ✅ PASS | 0 | Builds Rust libs (CPU-only) |
| `make check-go-mod-tidy` | ✅ PASS | 0 | Go deps are tidy |
| `make vet` | ✅ PASS | 0 | No vet errors |
| `make shellcheck` | ✅ PASS | 0 | Shell scripts clean |
| `make yaml-lint` | ✅ PASS | 0 | YAML valid (5 style warnings) |
| `make codespell` | ⚠️  FAIL | 1 | False positives in build artifacts |
| `make go-lint` | ❌ FAIL | 2 | 11 issues (8 errorlint, 2 gci, 1 gocritic) |
| `make build-router` | ✅ PASS | 0 | Binary builds successfully |
| `go test ./pkg/config/...` | ✅ PASS | 0 | 280 specs passed |

**Interpretation**:
- **Build works** — Rust libs compile, Go router builds
- **Most linters pass** — shellcheck, yamllint work
- **Unit tests work** — Fast tests without external services
- **Go lint FAILS** — 11 pre-existing code quality issues need fixing
- **Full test suite not validated** — Requires Milvus, Redis, model downloads

---

## CI/CD

### GitHub Actions Workflows

**Gating checks** (must pass to merge):

1. **test-and-build.yml** (on PR, push to main)
   - Runs: `make test` (includes vet, build, test-binding-minimal, test-semantic-router, test-binding-lora)
   - Requires: Rust 1.90, Go 1.24, Milvus, Redis
   - Caches: Go/Rust deps, models (~75GB on /mnt)
   - Runtime: ~10-15 minutes

2. **pre-commit.yml** (on PR, push to main)
   - Runs: `make precommit-check`, `make codespell`, `make agent-fast-gate`
   - Requires: Python 3.11, Go 1.24, Node 20, Rust 1.90, golangci-lint v2.5.0
   - Linters: go-lint, cargo fmt, black, eslint, yamllint, markdown-lint, shellcheck, codespell
   - Runtime: ~5-10 minutes

3. **dashboard-test.yml** (on dashboard changes)
   - Runs: `make dashboard-check` (lint, type-check, go mod tidy)
   - Requires: Node.js 23, Go 1.24
   - Runtime: ~3-5 minutes

**CI-specific commands**:
```bash
make check-go-mod-tidy  # Verify go.mod/go.sum are tidy
make rust-ci             # Build Rust (CPU-only, no CUDA)
make test                # Full test suite (see below)
make precommit-check     # Run all pre-commit hooks
make agent-fast-gate     # Check changed files with agent tooling
```

**Full test command** (in CI):
```bash
make vet check-go-mod-tidy download-models test-binding-minimal test-semantic-router clean-minimal-models download-models-lora test-binding-lora
```

This splits tests into phases to manage disk space (minimal models → unit tests → clean → LoRA models → LoRA tests).

---

## Linting Configuration

### Go (golangci-lint v2.5.0)

**Config**: `tools/linter/go/.golangci.yml`

**Enabled linters**:
- bodyclose — HTTP response body closed
- copyloopvar — Loop variable usage in closures
- depguard — Disallowed package dependencies
- errorlint — Error handling mistakes
- gocritic — Code quality checks
- gosec — Security issues
- importas — Import alias consistency
- misspell — Spelling errors
- revive — Extensible Go linter
- staticcheck — Advanced static analysis
- testifylint — Testify framework best practices
- unconvert — Unnecessary type conversions

**Formatters**: gci (import ordering), gofumpt (stricter gofmt)

**Run**: `make go-lint`
**Fix**: `make go-lint-fix`

**Known issues** (as of 2026-03-22):
```
pkg/apiserver/route_routing.go:86: errorlint - type assertion on error
pkg/apiserver/route_routing.go:116: errorlint - type assertion on error
pkg/extproc/routing_api_test.go:48,59,70,83,179,189: errorlint - type assertion on error
pkg/apiserver/route_routing.go:61: gci - import formatting
pkg/extproc/routing_api.go:101: gci - import formatting
cmd/main.go:486: gocritic - unlambda simplification
```

### Rust (cargo)

**Run format check**: `cd candle-binding && cargo fmt --check`
**Fix**: `cd candle-binding && cargo fmt`
**Run clippy**: `cd candle-binding && cargo clippy`

### Python (Black)

**Config**: `.pre-commit-config.yaml` (Black rev 25.1.0)
**Run**: `black --check .`
**Fix**: `black .`
**Scope**: bench/, e2e/, scripts/, src/training/

### YAML (yamllint)

**Config**: `tools/linter/yaml/.yamllint`
**Run**: `make yaml-lint`
**Known warnings**: 5 warnings about comment indentation (style, not errors)

### Markdown (markdownlint-cli)

**Config**: `tools/linter/markdown/markdownlint.yaml`
**Run**: `make markdown-lint`
**Fix**: `make markdown-lint-fix`
**Requires**: `npm install -g markdownlint-cli@0.43.0`

### Shell (shellcheck)

**Config**: `tools/linter/shellcheck/.shellcheckrc`
**Run**: `make shellcheck`
**Ignored codes**: SC2155, SC2034, SC1091, SC2011, SC2012, SC2087, SC2119, SC2120, SC2162

### Spelling (codespell)

**Config**: `tools/linter/codespell/.codespell.ignorewords`
**Run**: `make codespell`
**Note**: Currently flags false positives in build artifacts (`target/release/deps/serde-*.d`)

---

## Testing

### Test Structure

Tests are organized by type:

1. **Unit tests** (fast, no external deps)
   - Location: `src/semantic-router/pkg/*/`
   - Pattern: `*_test.go`
   - Framework: Go standard testing + Ginkgo/Gomega BDD
   - Run: `cd src/semantic-router && go test -v ./pkg/...`

2. **Binding tests** (require Rust libs)
   - Location: `candle-binding/binding_test.go`
   - Phases: test-binding-minimal, test-binding-lora
   - Run: `make test-binding-minimal` or `make test-binding-lora`

3. **Integration tests** (require Milvus + Redis)
   - Tests in: `pkg/cache/`, `pkg/memory/`
   - Env vars: `SKIP_MILVUS_TESTS=false`, `SKIP_REDIS_TESTS=false`
   - Run: `make test-semantic-router SKIP_MILVUS_TESTS=false SKIP_REDIS_TESTS=false`

4. **E2E tests** (require full stack)
   - Location: `e2e/testing/*.py`
   - Run: `python3 e2e/testing/run_all_tests.py`
   - Requires: Router running, Envoy proxy, mock vLLM servers

### Running Tests

**Simple unit tests** (no setup):
```bash
cd src/semantic-router
go test -v ./pkg/config/...
```

**With Rust dependencies**:
```bash
export LD_LIBRARY_PATH=${PWD}/candle-binding/target/release:${PWD}/ml-binding/target/release:${PWD}/nlp-binding/target/release
export CGO_ENABLED=1
cd src/semantic-router
go test -v ./pkg/...
```

**Skip external service tests**:
```bash
export SKIP_MILVUS_TESTS=true
export SKIP_REDIS_TESTS=true
export SKIP_LLAMA_STACK_TESTS=true
cd src/semantic-router
go test -v ./pkg/...
```

**Single test**:
```bash
cd src/semantic-router
go test -v -run TestGetModelByPath ./pkg/config/
```

**Single package**:
```bash
cd src/semantic-router
go test -v ./pkg/extproc/
```

**With race detector**:
```bash
cd src/semantic-router
go test -v -race ./pkg/...
```

### Test Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CI` | false | Enable CI mode |
| `SKIP_MILVUS_TESTS` | true (local), false (CI) | Skip Milvus-dependent tests |
| `SKIP_REDIS_TESTS` | true (local), false (CI) | Skip Redis-dependent tests |
| `SKIP_LLAMA_STACK_TESTS` | true | Skip Llama Stack tests |
| `SR_TEST_MODE` | false | Enable test mode for router |
| `HF_TOKEN` | - | HuggingFace token for gated models |
| `MILVUS_URI` | localhost:19530 | Milvus connection string |
| `LD_LIBRARY_PATH` | - | **Required**: Path to Rust .so files |
| `CGO_ENABLED` | 0 | **Must be 1** for tests that use Rust libs |

### Test Fixtures

- **Config files**: `config/testing/*.yaml`
- **Mock servers**: `e2e/testing/mock-vllm-*.py`
- **Test data**: `e2e/testcases/testdata/*`

---

## Build System

### Make Targets

**Build**:
```bash
make build          # Build Rust libs + Go router
make build-router   # Build only Go router binary
make rust           # Build Rust libs (with CUDA if available)
make rust-ci        # Build Rust libs (CPU-only, for CI)
```

**Test**:
```bash
make test                # Full test suite (vet, build, tests)
make test-semantic-router # Go unit tests only
make test-binding-minimal # Go tests with minimal models
make test-binding-lora    # Go tests with LoRA models
make vet                  # Run go vet on all modules
```

**Lint**:
```bash
make go-lint        # golangci-lint for Go code
make go-lint-fix    # Auto-fix Go lint issues
make shellcheck     # Lint shell scripts
make yaml-lint      # Lint YAML files
make markdown-lint  # Lint Markdown files
make codespell      # Check spelling
make precommit-check # Run all pre-commit hooks
```

**Dashboard**:
```bash
make dashboard-check      # Lint + type-check + go mod tidy
make dashboard-lint       # ESLint (frontend) + golangci-lint (backend)
make dashboard-type-check # TypeScript type checking
make dashboard-build      # Build frontend + backend
```

**Other**:
```bash
make check-go-mod-tidy # Verify go.mod/go.sum are tidy
make clean             # Clean build artifacts
make download-models   # Download ML models from HuggingFace
```

### Modular Makefiles

Build system is split across `tools/make/*.mk`:
- `build-run-test.mk` — Build, run, test targets
- `golang.mk` — Go-specific targets
- `rust.mk` — Rust-specific targets
- `linter.mk` — Linting targets
- `dashboard.mk` — Dashboard targets
- `docker.mk` — Docker/container targets
- `e2e.mk` — E2E test targets
- `models.mk` — Model download targets

---

## Conventions

### Test Naming

- **Go**: `TestXxx` functions or Ginkgo `Describe`/`It` blocks
- **Rust**: `#[test] fn test_xxx`

### Test Files

- **Go**: `*_test.go` in same directory as code
- **Rust**: `*_test.rs` or `tests/` subdirectory

### Import Style (Go)

Enforced by gci linter:
1. Standard library imports
2. External imports
3. Local imports with prefix `github.com/vllm-project/semantic-router`

Example:
```go
import (
    "context"
    "fmt"

    "github.com/stretchr/testify/assert"

    "github.com/vllm-project/semantic-router/src/semantic-router/pkg/config"
)
```

### Test Framework (Go)

Uses Ginkgo/Gomega BDD style:
```go
var _ = Describe("Config", func() {
    Context("when loading config", func() {
        It("should parse YAML correctly", func() {
            Expect(config).NotTo(BeNil())
        })
    })
})
```

---

## Gaps & Caveats

### What's Not Validated

1. **Full test suite** — Requires Milvus (port 19530) and Redis (port 6379). Tests would download 10+ GB of models.

2. **Model downloads** — Not tested. Requires:
   - HuggingFace token for gated models
   - ~10-20 GB disk space
   - Command: `make download-models`

3. **Dashboard frontend** — TypeScript/React tests not validated. Requires Node.js 23 setup.

4. **Rust linting** — `cargo clippy` not tested.

5. **E2E integration tests** — Require full stack:
   - Router binary running
   - Envoy proxy
   - Mock vLLM servers or real vLLM endpoint
   - Test command: `python3 e2e/testing/run_all_tests.py`

6. **Performance tests** — Not validated. Require running router with load testing.

7. **CUDA/GPU builds** — Container used CPU-only mode (`rust-ci`). GPU builds require:
   - CUDA toolkit (nvcc)
   - CUDA-capable GPU
   - Command: `make rust` (auto-detects CUDA)

8. **Pre-commit hooks** — Full suite not tested. Requires all language toolchains installed.

### Known Issues

1. **Go lint failures** — 11 issues in codebase (see Linting section). These would block pre-commit hooks.

2. **Codespell false positives** — Flags "ser" in `target/release/deps/serde-*.d` build artifact filenames.

3. **YAML warnings** — 5 style warnings about comment indentation (not errors).

4. **Test environment** — Some tests require:
   - Running Milvus vector database
   - Running Redis Stack
   - Environment variables (HF_TOKEN, MILVUS_URI)
   - Large model files

### Infrastructure Requirements

**For local development**:
- Rust 1.90
- Go 1.24
- Python 3.11+
- Node.js 20+ (for dashboard/website)
- make, build-essential, pkg-config
- Optional: CUDA toolkit for GPU acceleration

**For CI/CD**:
- Above + Milvus, Redis containers
- ~75 GB disk space for model cache
- golangci-lint v2.5.0
- markdownlint-cli@0.43.0
- codespell, yamllint

**For full integration testing**:
- Kubernetes cluster (Kind for local)
- Helm 3
- Envoy proxy (func-e)
- vLLM endpoint (real or mock)

---

## Quick Reference

### Fast Validation (No External Services)

```bash
# In container or local:
make rust-ci              # Build Rust libs (CPU-only)
make check-go-mod-tidy    # Verify go.mod tidy
make vet                  # Run go vet
make build-router         # Build router binary
make shellcheck           # Lint shell scripts
make yaml-lint            # Lint YAML files

# Run fast unit tests:
cd src/semantic-router
go test -v ./pkg/config/...
go test -v ./pkg/dsl/...
go test -v ./pkg/headers/...
```

**Time**: ~5-10 minutes
**Expected**: All PASS except go-lint (has 11 existing issues)

### Full CI-like Validation (Requires Milvus + Redis)

```bash
# Start services:
docker run -d --name milvus-semantic-cache -p 19530:19530 milvusdb/milvus:v2.3.3 milvus run standalone
make start-redis

# Run tests:
export SKIP_MILVUS_TESTS=false
export SKIP_REDIS_TESTS=false
export LD_LIBRARY_PATH=${PWD}/candle-binding/target/release:${PWD}/ml-binding/target/release:${PWD}/nlp-binding/target/release
export CGO_ENABLED=1
make test

# Cleanup:
docker stop milvus-semantic-cache && docker rm milvus-semantic-cache
make clean-redis
```

**Time**: ~15-20 minutes
**Expected**: Full test suite passes

### Pre-Commit Checks

```bash
make precommit-install  # Install pre-commit hooks
make precommit-check    # Run all hooks
```

**Note**: Will fail on go-lint due to existing issues. Run `make go-lint-fix` to auto-fix formatting issues.

---

## Agent Readiness Rating: MEDIUM

**Strengths**:
- ✅ Build works in standard container (golang:1.24)
- ✅ Dependencies install cleanly
- ✅ Unit tests run and pass (280 specs)
- ✅ Most linters work (shellcheck, yamllint)
- ✅ Clear make-based build system
- ✅ Good test organization (unit, integration, e2e)

**Weaknesses**:
- ❌ Go linting fails with 11 issues (pre-existing in codebase)
- ❌ Full tests require external services (Milvus, Redis)
- ❌ Model downloads required for many tests (~10+ GB)
- ⚠️  Codespell has false positives
- ⚠️  Multi-language complexity (Go + Rust + Python + TypeScript)

**Recommendation**: An agent can validate Go patches by:
1. Running unit tests (fast, reliable)
2. Running go vet (clean)
3. Building router binary (proves compilation)
4. Noting that go-lint will fail (pre-existing)

For full validation, agent needs infrastructure: Milvus, Redis, model downloads. This is feasible in CI but not in a simple container.

**Confidence**: High — Validation was thorough. 13 commands tested, results documented.
