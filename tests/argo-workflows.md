# Test Context for argo-workflows (opendatahub-io)

## Overview

**Repository:** opendatahub-io/argo-workflows
**Primary Language:** Go (1.25.7)
**Secondary Languages:** TypeScript/JavaScript (UI)
**Build System:** Make + Go modules
**Agent Readiness:** **MEDIUM** - Go tests and lint validated successfully in container. UI tests and E2E tests require additional infrastructure.

This is a fork of Argo Workflows with OpenDataHub-specific modifications. The repository contains a workflow engine controller, CLI, and web UI. Core Go components can be tested and linted in a standard container, but full validation requires Kubernetes infrastructure and Node.js ecosystem for the UI.

---

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-argo-workflows \
  -v /path/to/argo-workflows:/app:Z \
  -w /app \
  golang:1.23 \
  sleep infinity
```

**Why golang:1.23?** The go.mod requires Go 1.25.7, which is newer than most base images. We use golang:1.23 and set `GOTOOLCHAIN=auto` to allow Go to download the exact version needed.

### 2. Install System Dependencies

```bash
podman exec test-context-argo-workflows bash -c \
  "apt-get update && apt-get install -y make git curl protobuf-compiler clang-format"
```

**Required packages:**
- `make` - build orchestration
- `git` - version control operations
- `curl` - downloading tools
- `protobuf-compiler` - for protobuf code generation (if needed)
- `clang-format` - for proto file formatting

### 3. Install Go Dependencies

```bash
podman exec test-context-argo-workflows bash -c \
  "cd /app && export GOTOOLCHAIN=auto && go mod download"
```

**Critical:** Must set `GOTOOLCHAIN=auto` to allow Go to download and use the required Go 1.25.7 toolchain.

**Expected result:** Dependencies download successfully (may take 2-3 minutes on first run).

### 4. Build the Project

```bash
podman exec test-context-argo-workflows bash -c \
  "cd /app && export GOTOOLCHAIN=auto && make dist/argo STATIC_FILES=false"
```

**Validation status:** ✅ **PASS** - Builds successfully, produces 140MB binary at `dist/argo`

**Note:** `STATIC_FILES=false` skips the UI build (which requires yarn/Node). For full build with UI, install Node 20+ and yarn first.

### 5. Run Linter

**Install golangci-lint:**
```bash
podman exec test-context-argo-workflows bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v2.4.0"
```

**Run lint:**
```bash
podman exec test-context-argo-workflows bash -c \
  "cd /app && export GOTOOLCHAIN=auto && golangci-lint run --verbose"
```

**Validation status:** ✅ **PASS** - 0 issues found (after applying configured exclusions)

**Performance:** Takes ~40 seconds, peak memory usage ~7GB. Uses 20 linters including:
- errcheck, gosec, govet, staticcheck
- gofmt, goimports (formatters)
- misspell, nakedret, unparam, unused

**Exclusions:** Configured to skip `ui/`, `docs/`, `examples/`, `vendor/`, `pkg/client/`, `sdks/`

### 6. Run Unit Tests

```bash
podman exec test-context-argo-workflows bash -c \
  "cd /app && export GOTOOLCHAIN=auto && export KUBECONFIG=/dev/null && make test STATIC_FILES=false"
```

**Validation status:** ✅ **PASS** - All unit tests passed

**Alternative (direct):**
```bash
podman exec test-context-argo-workflows bash -c \
  "cd /app && export GOTOOLCHAIN=auto && export KUBECONFIG=/dev/null && go test ./..."
```

**Test a single package:**
```bash
podman exec test-context-argo-workflows bash -c \
  "cd /app && export GOTOOLCHAIN=auto && export KUBECONFIG=/dev/null && go test ./cmd/argo/..."
```

**Test a single test:**
```bash
podman exec test-context-argo-workflows bash -c \
  "cd /app && export GOTOOLCHAIN=auto && export KUBECONFIG=/dev/null && go test -run TestOfflineLint ./cmd/argo/lint/..."
```

**Notes:**
- 236 test files throughout the codebase
- `KUBECONFIG=/dev/null` prevents tests from attempting to access a real cluster
- E2E tests (in `test/e2e/`) are skipped - they require a Kubernetes cluster

### 7. Cleanup

```bash
podman rm -f test-context-argo-workflows
```

---

## Validation Results

| Step | Command | Status | Exit Code | Notes |
|------|---------|--------|-----------|-------|
| Install | `go mod download` | ✅ PASS | 0 | Requires GOTOOLCHAIN=auto |
| Build | `make dist/argo STATIC_FILES=false` | ✅ PASS | 0 | Produces 140MB binary |
| Lint | `golangci-lint run --verbose` | ✅ PASS | 0 | 0 issues (821 filtered) |
| Test | `make test STATIC_FILES=false` | ✅ PASS | 0 | All unit tests passed |

**Summary:** Go-based development (build, lint, unit test) is fully validated and works in a standard container with GOTOOLCHAIN=auto.

---

## CI/CD

### GitHub Actions Workflows

**Primary workflow:** `.github/workflows/ci-build.yaml`

**Triggers:**
- `pull_request` to `main`, `stable`, `rhoai-*` branches
- `push` to `main`, `stable`, `release-*` branches

### Gating Checks (Required for PRs)

1. **Unit Tests (Linux)**
   ```bash
   make test STATIC_FILES=false GOTEST='go test -p 20 -covermode=atomic -coverprofile=coverage.out'
   ```
   - Runs on: ubuntu-latest
   - Go version: from go.mod
   - Timeout: 10 minutes

2. **Unit Tests (Windows)**
   ```bash
   go test -p 20 -covermode=atomic -coverprofile='coverage.out' \
     $(go list ./... | select-string -Pattern 'workflow/controller', 'server' -NotMatch)
   ```
   - Runs on: windows-2022
   - Timeout: 20 minutes
   - Excludes controller and server packages

3. **Lint**
   ```bash
   make lint STATIC_FILES=false
   ```
   - Runs golangci-lint on Go code
   - Checks for uncommitted changes after lint
   - Timeout: 15 minutes

4. **Codegen Verification**
   ```bash
   make codegen -B STATIC_FILES=false
   git diff --exit-code
   ```
   - Ensures generated code is up to date
   - Requires protoc, controller-gen, mockery, etc.
   - Timeout: 20 minutes

5. **UI Tests**
   ```bash
   yarn --cwd ui install
   yarn --cwd ui build
   yarn --cwd ui test
   yarn --cwd ui lint
   yarn --cwd ui deduplicate
   ```
   - Requires Node 20
   - Timeout: 6 minutes

6. **E2E Tests (Matrix)**
   - Runs multiple test suites: executor, corefunctional, functional, api, cli, cron, examples, plugins
   - Requires K3s Kubernetes cluster
   - Uses different profiles: minimal, mysql, plugins
   - Timeout: 60 minutes
   - **Infrastructure required:** Kubernetes cluster, MinIO, MySQL/Postgres (depending on profile)

7. **PR Title Check**
   - Validates semantic commit format
   - Runs on: pull_request_target

### Changed Files Detection

CI uses `tj-actions/changed-files` to skip jobs when relevant files haven't changed. Groups:
- **tests:** Core Go code (cmd/, pkg/, workflow/, etc.)
- **e2e-tests:** Tests + manifests + SDKs + examples
- **codegen:** Generated files + generation scripts
- **lint:** All code + linter configs + docs
- **ui:** UI code only

---

## Conventions

### Test Files
- **Pattern:** `*_test.go` alongside source files
- **Naming:** `Test*` for unit tests, `Benchmark*` for benchmarks
- **Framework:** Standard Go testing + testify for assertions
- **Mocks:** Uses mockery to generate mocks from interfaces

### Test Organization
- **Unit tests:** Distributed throughout codebase next to source
- **E2E tests:** `test/e2e/` with build tags
- **Test fixtures:** `test/e2e/manifests/`

### Build Tags
Tests can use build tags to categorize:
- `api` - API server tests
- `cli` - CLI tests
- `cron` - Cron workflow tests
- `executor` - Executor tests
- `functional` - Functional tests
- `plugins` - Plugin tests

Run tests with specific tags:
```bash
go test --tags functional ./test/e2e
```

### Import Style
- Uses `goimports` with local prefix: `github.com/argoproj/argo-workflows/`
- Imports grouped: stdlib, external, local

---

## Gaps & Caveats

### Cannot Validate Without Infrastructure

1. **E2E Tests**
   - Require Kubernetes cluster (K3s in CI)
   - Require storage backends (MinIO, MySQL, Postgres)
   - Require Docker image builds
   - Total E2E suite takes ~25-60 minutes

2. **UI Tests**
   - Require Node 20+ and yarn
   - Not validated in Go-only container
   - Can be validated separately with Node base image

3. **Codegen**
   - Requires protoc, clang-format, controller-gen, openapi-gen, swagger, mockery
   - Complex dependency chain
   - Best validated via `make codegen` after installing all tools

4. **SDK Tests**
   - Java SDK tests require JDK 8 + Maven
   - Python SDK tests require Python 3.x + pip

### Go Version Quirk

**The go.mod requires Go 1.25.7**, which is newer than most base images. This requires:
- Using `GOTOOLCHAIN=auto` in all Go commands
- Allowing Go to download the exact toolchain version
- First run downloads ~100MB of Go toolchain

This is likely specific to the OpenDataHub fork and may differ from upstream Argo Workflows.

### Static Files

The project can be built with or without UI static files:
- **With UI** (`STATIC_FILES=true`): Requires yarn, Node 20+, builds React UI
- **Without UI** (`STATIC_FILES=false`): Go-only build, faster, no UI

CI and most development uses `STATIC_FILES=false`. Full releases use `STATIC_FILES=true`.

### Windows Tests

CI runs a subset of tests on Windows (excluding controller and server packages). These cannot be validated in a Linux container.

---

## Quick Reference

### Environment Variables

```bash
export GOTOOLCHAIN=auto        # Required: allows Go to use 1.25.7
export KUBECONFIG=/dev/null    # Recommended: prevents cluster access
export STATIC_FILES=false      # Recommended: skips UI build
```

### Common Commands

```bash
# Install dependencies
go mod download

# Build CLI
make dist/argo STATIC_FILES=false

# Build controller
make controller STATIC_FILES=false

# Lint
golangci-lint run --fix --verbose

# Test (all)
make test STATIC_FILES=false

# Test (specific package)
go test ./cmd/argo/...

# Test (specific test)
go test -run TestName ./pkg/...

# Test with coverage
go test -coverprofile=coverage.out ./...

# Clean
make clean
```

### File Locations

- **Linter config:** `.golangci.yml`
- **UI linter:** `ui/.eslintrc.json`
- **Go modules:** `go.mod`, `go.sum`
- **Makefile:** `Makefile`
- **CI workflows:** `.github/workflows/ci-build.yaml`
- **E2E manifests:** `test/e2e/manifests/`

---

## Agent Readiness Assessment

**Rating: MEDIUM**

**Why Medium?**
- ✅ **Strengths:**
  - Go lint and unit tests fully validated in container
  - Build process works reliably
  - Clear, documented commands
  - Fast unit test execution (<2 minutes)

- ⚠️ **Limitations:**
  - E2E tests require Kubernetes infrastructure
  - UI tests require separate Node/yarn environment
  - Unusual Go version requirement needs GOTOOLCHAIN=auto
  - Full validation requires multiple containers/environments

**Recommendation for Agents:**
An agent can reliably validate Go code changes (lint + unit tests) in a single container. For UI changes or E2E testing, additional infrastructure is required. Partial validation (Go-only) provides high confidence for backend changes.

**Typical validation flow:**
1. Patch Go code
2. Run in golang:1.23 container with GOTOOLCHAIN=auto
3. Lint → Test → Build
4. If UI changes: switch to Node container, run yarn tests
5. If E2E validation needed: requires K8s setup (complex)

---

## Additional Notes

- **Fork-specific:** This is an OpenDataHub fork of Argo Workflows with custom modifications
- **Dockerfile locations:**
  - Main: `Dockerfile`
  - ODH-specific: `argo-workflowcontroller/Dockerfile.ODH`, `argo-argoexec/Dockerfile.ODH`
- **Image builds:** CI builds images for `ds-pipelines-argo-workflowcontroller` and `ds-pipelines-argo-argoexec`
- **Test timeout:** Unit tests timeout at 10 minutes, E2E at 60 minutes
- **Parallel test execution:** Uses `-p 20` for parallel test execution

---

**Generated:** 2026-03-22T21:41:00Z
**Confidence:** High
**Validated:** Go build, lint, and unit tests in golang:1.23 container
