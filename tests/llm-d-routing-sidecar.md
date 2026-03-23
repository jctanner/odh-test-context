# Test Context: llm-d-routing-sidecar

**Repository:** opendatahub-io/llm-d-routing-sidecar
**Language:** Go 1.24.2
**Build System:** Makefile, go build
**Agent Readiness:** ⭐ **HIGH** — All lint and test commands validated successfully in container
**Generated:** 2026-03-22T23:00:46Z

---

## Overview

LLM-D routing sidecar is a Go-based reverse proxy for LLM request routing. The project has:
- ✅ Comprehensive linting with golangci-lint (22 linters enabled)
- ✅ Unit tests using Ginkgo/Gomega BDD framework (18 tests, all passing)
- ✅ GitHub Actions CI with gating checks on PRs
- ✅ Clean dependency installation and build process

**Agent readiness: HIGH** — An AI agent can clone, patch, lint, and test this repo with clear pass/fail signals. All commands validated in golang:1.24 container.

---

## Container Recipe

This is a **complete, copy-paste recipe** for validating patches. Every step has been validated.

### 1. Start the container

```bash
podman run -d \
  --name test-llm-d-routing-sidecar \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24 \
  sleep infinity
```

**Note:** Use `docker` instead of `podman` if podman is unavailable.

### 2. Install system dependencies

```bash
podman exec test-llm-d-routing-sidecar bash -c \
  "apt-get update && apt-get install -y make git curl jq"
```

### 3. Install Go dependencies

```bash
podman exec test-llm-d-routing-sidecar bash -c \
  "cd /app && go mod download"
```

**Validation:** ✅ Exit 0, no errors

### 4. Install golangci-lint (for linting)

```bash
podman exec test-llm-d-routing-sidecar bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v2.1.6"
```

**Validation:** ✅ Installed to /usr/local/bin/golangci-lint

### 5. Install Ginkgo (for tests)

```bash
podman exec test-llm-d-routing-sidecar bash -c \
  "cd /app && go install github.com/onsi/ginkgo/v2/ginkgo@latest"
```

**Validation:** ✅ Installed to /go/bin/ginkgo

### 6. Run linting

```bash
podman exec test-llm-d-routing-sidecar bash -c \
  "cd /app && golangci-lint run"
```

**Validation:** ✅ Exit 0, output "0 issues."

**Expected output:**
```
0 issues.
```

**What this checks:**
- 22 linters enabled in .golangci.yml
- Includes: govet, errcheck, ineffassign, unused, ginkgolinter, misspell, etc.
- Runs with 5m timeout

### 7. Run unit tests

```bash
podman exec test-llm-d-routing-sidecar bash -c \
  "cd /app && /go/bin/ginkgo -v ./internal/..."
```

**Validation:** ✅ 18/18 tests passed in ~16.5s

**Expected output snippet:**
```
Ran 18 of 18 Specs in 16.470 seconds
SUCCESS! -- 18 Passed | 0 Failed | 0 Pending | 0 Skipped
Test Suite Passed
```

**What this runs:**
- Unit tests in `internal/proxy/*_test.go`
- Tests for reverse proxy logic, NIXL protocol connectors, SSRF allowlist validation
- Ginkgo BDD-style tests with Gomega matchers

**Note:** You may see a version mismatch warning (Ginkgo CLI 2.28.1 vs go.mod 2.23.4) — this is harmless, tests run successfully.

### 8. Build the binary (optional validation)

```bash
podman exec test-llm-d-routing-sidecar bash -c \
  "cd /app && go build -o bin/llm-d-routing-sidecar cmd/llm-d-routing-sidecar/main.go"
```

**Validation:** ✅ Exit 0, creates 22MB binary at bin/llm-d-routing-sidecar

### 9. Run a single test file

```bash
podman exec test-llm-d-routing-sidecar bash -c \
  "cd /app && /go/bin/ginkgo -v ./internal/proxy/allowlist_test.go"
```

### 10. Run a single test by name

```bash
podman exec test-llm-d-routing-sidecar bash -c \
  "cd /app && /go/bin/ginkgo -v --focus='should allow all targets' ./internal/proxy/"
```

### 11. Cleanup

```bash
podman rm -f test-llm-d-routing-sidecar
```

---

## Validation Results

All commands validated successfully on 2026-03-22:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Dependencies | `go mod download` | ✅ PASS | Exit 0, no errors |
| Lint | `golangci-lint run` | ✅ PASS | 0 issues found |
| Test | `ginkgo -v ./internal/...` | ✅ PASS | 18/18 tests passed |
| Build | `go build -o bin/...` | ✅ PASS | 22MB binary created |

---

## CI/CD Configuration

**System:** GitHub Actions
**Trigger:** Pull requests to `main` branch
**Workflow:** `.github/workflows/ci-pr-checks.yaml`

### Gating Checks (all required to merge)

1. **Markdown link checker**
   ```yaml
   uses: ./.github/actions/markdown-link-checker
   args: "--quiet --retry"
   ```

2. **golangci-lint**
   ```yaml
   uses: golangci/golangci-lint-action@v8
   args: "--config=./.golangci.yml"
   version: 'v2.1.6'
   ```

3. **Unit tests**
   ```bash
   make test
   # Expands to:
   # go install github.com/onsi/ginkgo/v2/ginkgo@latest
   # ginkgo -v ./internal/...
   ```

**Setup:** CI uses Go 1.24.0 (vs go.mod 1.24.2, but compatible)

---

## Project Structure

```
llm-d-routing-sidecar/
├── cmd/
│   └── llm-d-routing-sidecar/
│       └── main.go              # Entry point
├── internal/
│   └── proxy/
│       ├── proxy.go             # Reverse proxy implementation
│       ├── proxy_test.go        # Proxy tests (9 specs)
│       ├── allowlist_test.go    # SSRF allowlist tests (4 specs)
│       ├── connector_nixlv2_test.go  # NIXL v2 tests (2 specs)
│       └── proxy_suite_test.go  # Ginkgo test suite setup
├── test/
│   └── e2e/
│       ├── e2e_suite_test.go    # E2E suite (requires Kind cluster)
│       └── e2e_test.go          # E2E test cases
├── .golangci.yml                # Linter configuration
├── Makefile                     # Build automation
└── go.mod                       # Go 1.24.2, Ginkgo v2.23.4
```

---

## Test Framework Details

**Framework:** Ginkgo v2.23.4 (BDD testing framework for Go)
**Matcher Library:** Gomega (fluent assertion library)

**Test file naming:** `*_test.go`
**Test suite naming:** `*_suite_test.go`

**Example test structure:**
```go
var _ = Describe("Reverse Proxy", func() {
    Context("when x-prefiller-url is not present", func() {
        It("should forward requests to decode server", func() {
            // Test implementation
        })
    })
})
```

**Running tests:**
- All unit tests: `ginkgo -v ./internal/...`
- Single file: `ginkgo -v ./internal/proxy/proxy_test.go`
- Focused test: `ginkgo -v --focus="should forward requests"`
- Exclude slow tests: `ginkgo -v --skip="slow"`

---

## Linting Details

**Tool:** golangci-lint v2.1.6
**Config:** `.golangci.yml`
**Timeout:** 5 minutes
**Parallel:** Enabled

**Enabled linters (22 total):**
- **Formatters:** goimports, gofmt
- **Bug detection:** errcheck, govet, ineffassign, unused, makezero
- **Style:** revive, gocritic, nakedret, unconvert
- **Performance:** perfsprint, prealloc
- **Testing:** ginkgolinter
- **Others:** copyloopvar, dupword, durationcheck, fatcontext, loggercheck, misspell, goconst, unparam

**Running linter:**
```bash
golangci-lint run                    # Full project
golangci-lint run --fix              # Auto-fix issues
golangci-lint run ./internal/...     # Specific directory
```

---

## Conventions

**Import style:**
- Standard library imports first
- External packages second
- Internal packages last
- Dot imports allowed for Ginkgo/Gomega with `//nolint:revive`

**Logging:**
- Uses `k8s.io/klog/v2` for structured logging
- Format: `klog.InfoS("message", "key", value)`

**License headers:**
- Apache 2.0 license header required on all `.go` files
- Boilerplate template in `hack/boilerplate.go.txt`

**Pre-commit hooks:**
- Trailing whitespace removal
- EOF newline fixer
- YAML validation
- go-fmt
- golangci-lint
- Install with: `make install-hooks` (sets `core.hooksPath` to `hooks/`)

---

## Gaps & Caveats

1. **E2E tests not included in standard test run**
   - Located in `test/e2e/`
   - Require Kind Kubernetes cluster
   - Run with: `make kind-e2e-test` (after Kind cluster setup)
   - Not validated in this analysis (requires cluster infrastructure)

2. **No coverage reporting**
   - Tests don't emit coverage metrics
   - No coverage threshold enforcement
   - Could add: `ginkgo -cover -coverprofile=coverage.out ./internal/...`

3. **Pre-commit hooks not auto-installed**
   - Configured in `.pre-commit-config.yaml`
   - Requires manual: `make install-hooks`
   - Not enforced automatically on fresh clone

4. **Go version variance**
   - go.mod specifies: 1.24.2
   - CI uses: 1.24.0
   - Dockerfile uses: golang:1.24 (tracks latest 1.24.x)
   - All compatible, but creates minor version drift

---

## Quick Reference

**Validate a patch (all commands):**
```bash
# Start container
podman run -d --name test-llm-d -v $(pwd):/app:Z -w /app golang:1.24 sleep infinity

# Install deps
podman exec test-llm-d bash -c "apt-get update && apt-get install -y make git curl jq"
podman exec test-llm-d bash -c "cd /app && go mod download"
podman exec test-llm-d bash -c "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v2.1.6"
podman exec test-llm-d bash -c "cd /app && go install github.com/onsi/ginkgo/v2/ginkgo@latest"

# Validate
podman exec test-llm-d bash -c "cd /app && golangci-lint run"
podman exec test-llm-d bash -c "cd /app && /go/bin/ginkgo -v ./internal/..."

# Cleanup
podman rm -f test-llm-d
```

**Expected results:**
- Lint: `0 issues.` (exit 0)
- Test: `SUCCESS! -- 18 Passed | 0 Failed` (exit 0)

---

## Additional Resources

- **Makefile targets:**
  - `make lint` — Run golangci-lint
  - `make test` — Run unit tests with Ginkgo
  - `make build` — Build binary
  - `make format` — Run gofmt
  - `make kind-e2e-test` — Run E2E tests (requires Kind)

- **Test commands from Makefile:**
  ```bash
  # make test expands to:
  go install github.com/onsi/ginkgo/v2/ginkgo@latest
  ginkgo -v ./internal/...
  ```

- **Container build:**
  ```bash
  podman build -t llm-d-routing-sidecar:dev .
  # Multi-stage build: golang:1.24 → ubi9 runtime
  # CGO enabled, binary: 22MB
  ```

---

**Summary:** This repository has excellent agent readiness. All validation commands work cleanly in a standard golang:1.24 container. An AI agent can apply patches and get immediate, reliable pass/fail signals from both lint and test runs.
