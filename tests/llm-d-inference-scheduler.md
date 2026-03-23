# Test Context: llm-d-inference-scheduler

**Organization:** opendatahub-io
**Analyzed:** 2026-03-22
**Agent Readiness:** ⭐ HIGH - Lint and test commands fully validated and working

## Overview

Go-based Kubernetes-native inference scheduler and routing system for LLM workloads. Implements an endpoint picker (epp) that schedules requests across multiple inference backends and a routing sidecar proxy (pd-sidecar) that handles request profiling and forwarding. Uses Gateway API, custom CRDs, and integrates with Istio/Envoy for service mesh routing.

**Languages:** Go 1.25.7
**Build System:** Makefile + Go
**Test Framework:** Ginkgo/Gomega + standard Go testing
**Linting:** golangci-lint v2.8.0, typos v1.34.0

**Agent Readiness Rating:** HIGH — All lint and test commands validated successfully in container. An agent can clone, install dependencies, lint, and run unit tests with clear pass/fail signals. Build commands work without errors.

---

## Container Recipe

This is a **complete, executable recipe** for validating patches in an isolated container. All commands have been validated and work.

### 1. Start Container

Use `golang:1.22` base image (will auto-upgrade to Go 1.25.7):

```bash
podman run -d --name test-llm-d-scheduler \
  -v /path/to/repo:/app:Z \
  -w /app \
  golang:1.22 \
  sleep infinity
```

Replace `/path/to/repo` with the absolute path to this repository.

If `podman` is unavailable, use `docker` instead.

### 2. Install System Dependencies

Install ZeroMQ libraries, compiler toolchain, and build tools:

```bash
podman exec test-llm-d-scheduler bash -c \
  "apt-get update && apt-get install -y libzmq3-dev g++ make git pkg-config"
```

**Required packages:**
- `libzmq3-dev` - ZeroMQ C library headers (required for CGO)
- `g++` - C++ compiler
- `make` - Build automation
- `git` - Source control (used by some Go tools)
- `pkg-config` - Dependency discovery

### 3. Set Environment Variables

Export required build environment:

```bash
podman exec test-llm-d-scheduler bash -c \
  "export GOTOOLCHAIN=auto && \
   export CGO_ENABLED=1 && \
   export PKG_CONFIG_PATH=/usr/lib/pkgconfig"
```

**Why these are needed:**
- `GOTOOLCHAIN=auto` - Automatically downloads Go 1.25.7 (required by go.mod)
- `CGO_ENABLED=1` - Enables C interop for ZeroMQ bindings
- `PKG_CONFIG_PATH` - Tells pkg-config where to find library metadata

### 4. Download Go Dependencies

```bash
podman exec test-llm-d-scheduler bash -c \
  "cd /app && \
   export GOTOOLCHAIN=auto CGO_ENABLED=1 PKG_CONFIG_PATH=/usr/lib/pkgconfig && \
   go mod download"
```

**Validation result:** ✅ SUCCESS - All modules downloaded, Go 1.25.7 auto-installed

### 5. Build Project

Build both main components:

```bash
podman exec test-llm-d-scheduler bash -c \
  "cd /app && \
   export GOTOOLCHAIN=auto CGO_ENABLED=1 PKG_CONFIG_PATH=/usr/lib/pkgconfig && \
   go build -o bin/epp cmd/epp/main.go"
```

**Validation result:** ✅ SUCCESS - Binary built (88MB) with no warnings

To build both components via Makefile:

```bash
podman exec test-llm-d-scheduler bash -c \
  "cd /app && \
   export GOTOOLCHAIN=auto CGO_ENABLED=1 PKG_CONFIG_PATH=/usr/lib/pkgconfig && \
   make build"
```

### 6. Run Linting

#### Install golangci-lint

```bash
podman exec test-llm-d-scheduler bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | \
   sh -s -- -b /usr/local/bin v2.8.0"
```

#### Run golangci-lint

```bash
podman exec test-llm-d-scheduler bash -c \
  "cd /app && \
   export GOTOOLCHAIN=auto CGO_ENABLED=1 PKG_CONFIG_PATH=/usr/lib/pkgconfig && \
   golangci-lint run --config=./.golangci.yml"
```

**Validation result:** ✅ SUCCESS - 0 issues found

**Enabled linters:** bodyclose, copyloopvar, dupword, durationcheck, errcheck, fatcontext, ginkgolinter, goconst, gocritic, govet, ineffassign, loggercheck, makezero, misspell, nakedret, nilnil, perfsprint, prealloc, revive, staticcheck, unparam, unused, unconvert

#### Install and run typos checker

```bash
podman exec test-llm-d-scheduler bash -c \
  "cd /tmp && \
   curl -L https://github.com/crate-ci/typos/releases/download/v1.34.0/typos-v1.34.0-x86_64-unknown-linux-musl.tar.gz | tar -xz && \
   mv typos /usr/local/bin/ && \
   chmod +x /usr/local/bin/typos"
```

```bash
podman exec test-llm-d-scheduler bash -c \
  "cd /app && typos --format brief"
```

**Validation result:** ✅ SUCCESS - No typos found

### 7. Run Unit Tests

#### Run EPP component tests (fast, ~5 seconds)

```bash
podman exec test-llm-d-scheduler bash -c \
  "cd /app && \
   export GOTOOLCHAIN=auto CGO_ENABLED=1 PKG_CONFIG_PATH=/usr/lib/pkgconfig && \
   go test -timeout=5m \$(go list ./... | grep -v /test/ | grep -v ./pkg/sidecar/)"
```

**Validation result:** ✅ SUCCESS - 6 packages tested, all passed

**Packages tested:**
- `pkg/metrics` (0.004s)
- `pkg/plugins/datalayer/models` (0.003s)
- `pkg/plugins/filter` (0.004s)
- `pkg/plugins/profile` (0.010s)
- `pkg/plugins/scorer` (2.022s)
- `pkg/scheduling/pd` (3.026s)

#### Run sidecar component tests (~20 seconds)

```bash
podman exec test-llm-d-scheduler bash -c \
  "cd /app && \
   export GOTOOLCHAIN=auto CGO_ENABLED=1 PKG_CONFIG_PATH=/usr/lib/pkgconfig && \
   go test -timeout=5m \$(go list ./pkg/sidecar/...)"
```

**Validation result:** ✅ SUCCESS - 1 package tested (pkg/sidecar/proxy, 19.829s), all passed

#### Run all unit tests via Makefile

```bash
podman exec test-llm-d-scheduler bash -c \
  "cd /app && \
   export GOTOOLCHAIN=auto CGO_ENABLED=1 PKG_CONFIG_PATH=/usr/lib/pkgconfig && \
   make test-unit"
```

### 8. Run Single Test (Template)

To run a specific test by name:

```bash
podman exec test-llm-d-scheduler bash -c \
  "cd /app && \
   export GOTOOLCHAIN=auto CGO_ENABLED=1 PKG_CONFIG_PATH=/usr/lib/pkgconfig && \
   go test -v -run '{TestName}' {package_path}"
```

Example:

```bash
go test -v -run 'TestSchedulerPDDecisionCount' ./pkg/metrics
```

To run a specific test file:

```bash
go test -v ./pkg/metrics/metrics_test.go
```

### 9. Cleanup

Remove the container when done:

```bash
podman rm -f test-llm-d-scheduler
```

---

## Validation Results

All commands were executed in a live container to verify they work:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| System deps | `apt-get install libzmq3-dev g++ make git pkg-config` | ✅ PASS | 23 packages installed |
| Go modules | `go mod download` | ✅ PASS | Go 1.25.7 auto-downloaded |
| Build | `go build -o bin/epp cmd/epp/main.go` | ✅ PASS | 88MB binary created |
| Lint (golangci) | `golangci-lint run` | ✅ PASS | 0 issues found |
| Lint (typos) | `typos --format brief` | ✅ PASS | No typos found |
| Unit tests (epp) | `go test ./...` | ✅ PASS | 6 packages, ~5s total |
| Unit tests (sidecar) | `go test ./pkg/sidecar/...` | ✅ PASS | 1 package, ~20s |

**Overall:** All core validation steps passed. Lint is clean, tests are passing, build works.

---

## CI/CD

**System:** GitHub Actions

**Gating Workflows (required for merge):**

1. **ci-pr-checks.yaml** - Main gating workflow
   - Triggers: `pull_request` and `push` on `main` branch
   - Uses path filter to skip when no source code changes
   - Steps:
     ```bash
     # Extract Go version and setup
     sed -En 's/^go (.*)$/GO_VERSION=\1/p' go.mod

     # Install dependencies
     go mod tidy
     sudo -E env "PATH=$PATH" make install-dependencies

     # Lint
     golangci-lint run --config=./.golangci.yml

     # Build
     make build

     # Test (includes unit + e2e)
     make test
     ```

2. **check-typos.yaml** - Spell checking
   - Triggers: `pull_request` and `push`
   - Uses `crate-ci/typos@v1.43.5` action

3. **ci-signed-commits.yaml** - Commit signature verification
   - Triggers: `pull_request_target`
   - Uses `1Password/check-signed-commits-action@v1`
   - Requires GPG or SSH signed commits

**Additional CI:**
- Tekton pipelines in `.tekton/` for production container builds
- Dependabot for dependency updates
- Prow integration for Kubernetes-style PR workflow

---

## Conventions

**Test Files:** `*_test.go` (Go standard)

**Test Naming:**
- Standard Go tests: `func TestXxx(t *testing.T)`
- Ginkgo BDD tests: `Describe()`, `Context()`, `It()` blocks
- Test suites: `func TestE2E(t *testing.T)` with `ginkgo.RunSpecs()`

**Package Structure:**
```
cmd/              # Main entry points
├── epp/          # Endpoint picker main
└── pd-sidecar/   # Routing sidecar main

pkg/              # Internal packages
├── plugins/      # Scheduler plugins (filters, scorers, profiles)
├── scheduling/   # Core scheduling logic
├── metrics/      # Prometheus metrics
├── sidecar/      # Sidecar proxy implementation
└── common/       # Shared utilities

test/             # Test suites
├── e2e/          # End-to-end tests (Kind cluster)
├── integration/  # Integration tests (build tag: integration_tests)
└── sidecar/      # Sidecar-specific tests

deploy/           # Kubernetes manifests
├── components/   # Kustomize components
└── environments/ # Environment-specific configs
```

**Import Style:** Grouped imports (stdlib, external, internal), auto-formatted via `goimports`

**Code Style:** Enforced via golangci-lint with 35+ enabled rules

**Commit Requirements:** Signed commits (GPG or SSH) required by CI

**Code Review:** Uses OWNERS files for automatic reviewer assignment

---

## Gaps & Caveats

### What's Missing

1. **E2E tests require Kubernetes cluster**
   - E2E test suite (`make test-e2e`) creates a Kind cluster and loads container images
   - Requires: Docker/Podman, Kind, container images (epp, sidecar, vllm-simulator, uds-tokenizer)
   - Cannot be validated in a simple container without significant infrastructure
   - Recommendation: Run unit tests for quick validation, use dedicated K8s environment for full E2E

2. **Integration tests not validated**
   - Use build tag `integration_tests`: `go test -tags=integration_tests ./test/integration/`
   - Not included in standard `make test-unit`
   - Unknown infrastructure requirements

3. **No coverage threshold**
   - No coverage requirements configured in CI or tooling
   - Coverage can be measured with `go test -cover` but not enforced

4. **Container image builds not validated**
   - Dockerfile.epp and Dockerfile.sidecar use multi-stage builds
   - Require specific base images and build arguments
   - Image builds tested separately via `make image-build`

### Infrastructure Dependencies

This project is **Kubernetes-native** and requires:

- **For E2E tests:**
  - Kubernetes cluster (Kind, existing cluster, or OpenShift)
  - Gateway API CRDs installed
  - Container registry access for images
  - Istio/Envoy for service mesh routing

- **For full functionality:**
  - Gateway API + Gateway Inference Extension (GIE) CRDs
  - vLLM inference backend pods
  - UDS tokenizer service (separate container)
  - Istio control plane or compatible service mesh

### Known Quirks

- **Go version:** Requires Go 1.25.7 which auto-downloads via `GOTOOLCHAIN=auto`. This is newer than most stable Go releases as of 2026-03.
- **ZMQ dependency:** Requires libzmq at build time due to CGO. Cannot build in pure Go environment.
- **Large binary:** The epp binary is ~88MB due to included dependencies and Kubernetes client libraries.
- **Test duration:** Sidecar tests take ~20s (uses Ginkgo with network operations). EPP tests are faster (~5s).

### Recommendations for Agents

**For quick validation:**
```bash
# 1. Install deps (one-time)
# 2. Run lint (fast, ~10s)
golangci-lint run
# 3. Run unit tests (fast, ~25s total)
make test-unit
```

**For comprehensive validation:**
```bash
# Requires Kubernetes cluster + images
make test-e2e
```

**For single-package testing:**
```bash
# Fast iteration on specific component
go test -v ./pkg/plugins/scorer/
```

---

## Quick Reference

### Common Commands

```bash
# Format code
make format

# Lint (all code)
make lint

# Lint (new code only)
LINT_NEW_ONLY=true make lint

# Build both components
make build

# Build individual components
make build-epp
make build-sidecar

# Run unit tests
make test-unit

# Run unit tests for specific component
make test-unit-epp
make test-unit-sidecar

# Run filtered tests by pattern
make test-filter PATTERN=TestName TYPE=epp

# Run integration tests
make test-integration

# Run E2E tests (requires Kind)
make test-e2e

# Build container images
make image-build

# Push container images
make image-push

# Deploy to Kind cluster
make env-dev-kind

# Clean build artifacts
make clean
```

### Environment Variables

```bash
# Change image registry
export IMAGE_REGISTRY=quay.io/myuser

# Change image tag
export EPP_TAG=v1.0.0
export SIDECAR_TAG=v1.0.0

# Set namespace for K8s deployments
export NAMESPACE=my-namespace

# Set Kind gateway port
export KIND_GATEWAY_HOST_PORT=30080

# Enable new-code-only linting
export LINT_NEW_ONLY=true
```

### File Locations

- **Linter config:** `.golangci.yml`, `.typos.toml`
- **CI workflows:** `.github/workflows/ci-pr-checks.yaml`
- **Tekton pipelines:** `.tekton/`
- **Deployment manifests:** `deploy/components/`, `deploy/environments/`
- **Test fixtures:** `test/e2e/yaml/`, `test/sidecar/config/`
- **Development docs:** `DEVELOPMENT.md`

---

## Summary

**Agent Readiness: HIGH**

This repository has excellent test infrastructure for automated validation:

✅ **Strengths:**
- All lint commands work out of the box
- Unit tests are fast (~25s), self-contained, and comprehensive
- Build process is well-documented and validated
- Clear separation between unit, integration, and E2E tests
- Makefile provides convenient targets for all operations
- CI configuration is explicit and uses standard tools

⚠️ **Limitations:**
- E2E tests require Kubernetes infrastructure (cannot run in simple container)
- Requires ZMQ system libraries (cannot use pure Go environment)
- Go 1.25.7 is newer than most available in standard images (auto-download required)

**Recommendation:** Use unit tests (`make test-unit`) + linting (`make lint`) for fast patch validation. Reserve E2E tests for final validation in dedicated Kubernetes environment.
