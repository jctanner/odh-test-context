# Test Context: kube-rbac-proxy

**Agent Readiness: HIGH** — Lint and unit tests validated successfully. Deps install cleanly, build works. E2E tests require Kubernetes cluster but unit tests provide good coverage.

## Overview

- **Repository:** opendatahub-io/kube-rbac-proxy
- **Language:** Go 1.25.7 (go.mod) / 1.25.8 (CI)
- **Build System:** Make + Go modules
- **Test Framework:** Go testing package
- **Linter:** golangci-lint v2 (latest version in CI)
- **CI System:** GitHub Actions
- **Confidence:** High — all commands validated in golang:1.25 container

## Container Recipe

This is the copy-paste recipe for validating patches in a container:

### 1. Start Container

```bash
podman run -d --name test-context-kube-rbac-proxy \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-kube-rbac-proxy bash -c \
  "apt-get update && apt-get install -y make git curl -qq"
```

### 3. Install Go Dependencies

```bash
podman exec test-context-kube-rbac-proxy bash -c \
  "cd /app && go mod download"
```

**Validation:** ✅ SUCCESS (exit 0, no output)

### 4. Install golangci-lint

```bash
podman exec test-context-kube-rbac-proxy bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin latest"
```

**Note:** Use `latest` version (not v2.1.0) to support Go 1.25.7. Validated with v2.11.4.

### 5. Build

```bash
podman exec test-context-kube-rbac-proxy bash -c \
  "cd /app && make build"
```

**Validation:** ✅ SUCCESS (exit 0)
- Creates `_output/kube-rbac-proxy` binary
- Uses CGO_ENABLED=0 for static binary
- Embeds version info via ldflags

### 6. Check License Headers

```bash
podman exec test-context-kube-rbac-proxy bash -c \
  "cd /app && make check-license"
```

**Validation:** ✅ SUCCESS (exit 0, ">> checking license headers")

### 7. Run Linter

```bash
podman exec test-context-kube-rbac-proxy bash -c \
  "cd /app && golangci-lint run"
```

**Validation:** ✅ SUCCESS (exit 0, "0 issues.")
- Config file: `.golangci.yaml`
- Excludes: test/, third_party, builtin, examples
- Runs all enabled linters with version 2 config

### 8. Run Unit Tests

```bash
podman exec test-context-kube-rbac-proxy bash -c \
  "cd /app && make test-unit"
```

**Validation:** ✅ SUCCESS (exit 0, all tests passed)
- Command expands to: `go test -v -race -count=1 $(go list ./... | grep -v /test/e2e)`
- 8 packages tested
- Race detection enabled
- Tests in: cmd/kube-rbac-proxy/app/, pkg/authz/, pkg/filters/, pkg/hardcodedauthorizer/, pkg/proxy/, pkg/tls/

### 9. Run Single Test File

```bash
podman exec test-context-kube-rbac-proxy bash -c \
  "cd /app && go test -v ./pkg/proxy/proxy_test.go ./pkg/proxy/proxy.go"
```

**Validation:** ✅ SUCCESS (test single file pattern works)

### 10. Run Single Test by Name

```bash
podman exec test-context-kube-rbac-proxy bash -c \
  "cd /app && go test -v -run TestReloader ./pkg/tls/..."
```

**Validation:** ✅ SUCCESS (test name filtering works)

### 11. Generate Code (CI Check)

```bash
podman exec test-context-kube-rbac-proxy bash -c \
  "cd /app && make generate && git diff --exit-code"
```

**Validation:** ✅ Partial (generate works, git diff not tested in container)
- Builds binary, installs embedmd tool
- Generates examples and docs
- CI checks for uncommitted generated files

### 12. E2E Tests (Requires Cluster)

**NOT VALIDATED** — requires Kubernetes cluster

```bash
# Requires kind cluster to be running first
podman exec test-context-kube-rbac-proxy bash -c \
  "cd /app && make test-e2e"
```

Command expands to: `go test -timeout 55m -v ./test/e2e/`

### 13. Cleanup

```bash
podman rm -f test-context-kube-rbac-proxy
```

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Dependencies | `go mod download` | 0 | ✅ | Clean download |
| Build | `make build` | 0 | ✅ | Binary created |
| License Check | `make check-license` | 0 | ✅ | All headers present |
| Lint | `golangci-lint run` | 0 | ✅ | 0 issues |
| Unit Tests | `make test-unit` | 0 | ✅ | All passed, 8 packages |
| Generate | `make generate` | 0 | ✅ | Docs/examples generated |
| E2E Tests | `make test-e2e` | — | ⚠️ | Requires kind cluster |

## CI/CD Gating Checks

GitHub Actions workflow (`.github/workflows/build.yml`) runs on push and pull_request:

### Required Checks (All Must Pass)

1. **check-license** — Verifies Apache 2.0 license headers in all .go files
   ```bash
   make check-license
   ```

2. **generate** — Ensures generated files are up to date
   ```bash
   make generate && git diff --exit-code
   ```

3. **lint** — golangci-lint via action (latest version)
   ```bash
   golangci-lint run
   ```

4. **build** — Builds binary
   ```bash
   make build
   ```

5. **unit-tests** — Runs all unit tests with race detection
   ```bash
   make test-unit
   ```

6. **e2e-tests** — Runs integration tests in kind cluster
   ```bash
   # CI sets up kind v0.30.0 cluster first
   make test-e2e
   ```

All checks must pass before publish job runs.

## Test Conventions

### Test File Naming
- Pattern: `*_test.go`
- Location: Alongside source files or in `test/` directory
- Examples: `proxy_test.go`, `auth_test.go`, `main_test.go`

### Test Function Naming
- Pattern: `Test*` (Go standard)
- Subtests: Use `t.Run("description", func(t *testing.T) {...})`
- Example: `TestGeneratingAuthorizerAttributes` with subtests for different configs

### Running Tests

**All unit tests:**
```bash
make test-unit
# Expands to: go test -v -race -count=1 $(go list ./... | grep -v /test/e2e)
```

**Single package:**
```bash
go test -v ./pkg/proxy/...
```

**Single file:**
```bash
go test -v ./pkg/proxy/proxy_test.go ./pkg/proxy/proxy.go
```

**Single test:**
```bash
go test -v -run TestReloader ./pkg/tls/...
```

**With coverage:**
```bash
go test -coverprofile=coverage.out ./...
```

### E2E Tests

Located in `test/e2e/`, requires Kubernetes cluster:
- Uses kind v0.30.0 in CI
- Config: `test/e2e/kind-config/kind-config.yaml`
- Timeout: 55 minutes
- Tests: Basics, HTTP2, TLS, OIDC, static auth, token masking, etc.

## Build Information

**Build command:**
```bash
make build
```

**Output:** `_output/kube-rbac-proxy` (static binary, CGO_ENABLED=0)

**Cross-build for all architectures:**
```bash
make crossbuild
# Builds for: linux-amd64, linux-arm, linux-arm64, linux-ppc64le, linux-s390x, darwin-amd64, windows-amd64
```

**Container image:**
```bash
make container
# Uses distroless/static:nonroot base image
```

## Gaps & Caveats

1. **E2E tests require infrastructure** — Cannot validate in basic container. Need:
   - Kubernetes cluster (kind, minikube, or real cluster)
   - kubectl configured
   - Container image loaded into cluster

2. **Generate check is environment-dependent** — CI verifies generated files are committed via `git diff --exit-code`. Local validation requires clean git state.

3. **No coverage threshold** — Project doesn't enforce coverage percentage, but tests use `-race` flag for race detection.

4. **golangci-lint version dependency** — Must use v2.11.4+ to support Go 1.25.7. Older versions fail with "Go language version too low" error.

5. **No pre-commit hooks** — All checks run in CI but not enforced locally via git hooks.

## Quick Start for Agents

To validate a patch:

```bash
# 1. Start container
podman run -d --name test-kube-rbac-proxy -v $(pwd):/app:Z -w /app golang:1.25 sleep infinity

# 2. Install deps
podman exec test-kube-rbac-proxy bash -c "apt-get update && apt-get install -y make git curl -qq && \
  go mod download && \
  curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin latest"

# 3. Validate
podman exec test-kube-rbac-proxy bash -c "cd /app && \
  make check-license && \
  golangci-lint run && \
  make build && \
  make test-unit"

# 4. Cleanup
podman rm -f test-kube-rbac-proxy
```

Expected result: All commands exit 0, no lint issues, all tests pass.
