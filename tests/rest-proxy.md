# Test Context for rest-proxy

**Generated:** 2026-03-22T20:10:00-04:00

## Overview

**Repository:** opendatahub-io/rest-proxy
**Languages:** Go 1.25.5
**Build System:** Make + Docker/Podman
**Agent Readiness:** **medium** — Lint and test commands work but require GOTOOLCHAIN=auto workaround for Go 1.25.5. The project's intended workflow uses a pre-built develop container with all tools installed.

## Container Recipe

This is a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-rest-proxy \
  -v "$(pwd):/app:Z" \
  -w /app \
  golang:1.23 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-rest-proxy bash -c "apt-get update && apt-get install -y make git curl"
```

### 3. Install golangci-lint

```bash
podman exec test-context-rest-proxy bash -c \
  "curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b /usr/local/bin v2.8.0"
```

### 4. Download Go Dependencies

```bash
podman exec test-context-rest-proxy bash -c "cd /app && export GOTOOLCHAIN=auto && go mod download"
```

**Note:** The `GOTOOLCHAIN=auto` environment variable is required because go.mod specifies Go 1.25.5, which is newer than the base image's Go 1.23. This instructs Go to automatically download the correct version.

### 5. Run Linting

```bash
podman exec test-context-rest-proxy bash -c "cd /app && export GOTOOLCHAIN=auto && golangci-lint run"
```

**Expected result:** `0 issues.`

**Status:** ✅ Validated — Passed with 0 issues.

### 6. Run Tests

Run all tests:

```bash
podman exec test-context-rest-proxy bash -c \
  "cd /app && export GOTOOLCHAIN=auto && go test -coverprofile cover.out \`go list -buildvcs=false ./...\`"
```

**Expected result:** `ok github.com/kserve/rest-proxy/proxy` with coverage report.

**Status:** ✅ Validated — All tests passed, 64.1% coverage.

Run tests for a specific package:

```bash
podman exec test-context-rest-proxy bash -c "cd /app && export GOTOOLCHAIN=auto && go test ./proxy -v"
```

Run a specific test:

```bash
podman exec test-context-rest-proxy bash -c \
  "cd /app && export GOTOOLCHAIN=auto && go test -run 'TestRESTResponse' ./proxy"
```

**Note:** Do NOT try to run individual test files (e.g., `go test ./proxy/marshaler_test.go`). This will fail with "undefined" errors. Always run by package.

### 7. Cleanup

```bash
podman rm -f test-context-rest-proxy
```

## Validation Results

### Dependency Install

**Command:** `GOTOOLCHAIN=auto go mod download`
**Exit Code:** 0
**Result:** ✅ Success

```
go: downloading go1.25.5 (linux/amd64)
```

The Go toolchain automatically downloaded Go 1.25.5 as required by go.mod.

### Linting

**Command:** `GOTOOLCHAIN=auto golangci-lint run`
**Exit Code:** 0
**Result:** ✅ Success

```
0 issues.
```

All code passes linting checks configured in `.golangci.yaml`.

### Testing

**Command:** `GOTOOLCHAIN=auto go test -coverprofile cover.out \`go list -buildvcs=false ./...\``
**Exit Code:** 0
**Result:** ✅ Success

```
# github.com/kserve/rest-proxy/gen
go: no such tool "covdata"
ok  	github.com/kserve/rest-proxy/proxy	0.009s	coverage: 64.1% of statements
```

All tests in the proxy package passed with 64.1% code coverage. The warning about "no such tool covdata" for the gen/ package is harmless — gen/ contains auto-generated gRPC code.

## CI/CD

### Gating Workflow: `.github/workflows/test.yml`

**Triggers:** Pull requests to `main` and `release-*` branches
**Required Checks:**

1. **Build dev image**
   ```bash
   make build.develop
   ```
   Builds the develop container with Go 1.25, pre-commit, golangci-lint, protoc, and all dependencies pre-installed.

2. **Run lint**
   ```bash
   ./scripts/develop.sh make fmt
   ```
   Runs `pre-commit run --all-files` inside the develop container, which executes golangci-lint and prettier.

3. **Run unit test**
   ```bash
   ./scripts/develop.sh make test
   ```
   Runs `go test -coverprofile cover.out \`go list -buildvcs=false ./...\`` inside the develop container.

**CI Strategy:** The CI uses a containerized development workflow where `make build.develop` creates a Docker image with all tools pre-installed, and `./scripts/develop.sh` runs commands inside that container. This ensures consistent tooling and avoids Go version conflicts.

### Build Workflow: `.github/workflows/build.yml`

**Triggers:** Push to main/release branches, tags, schedule
**Purpose:** Builds and pushes multi-platform container images
**Not gating for PRs** — only builds images after merge.

## Conventions

### Test Files

- **Pattern:** `*_test.go`
- **Location:** `proxy/marshaler_test.go`, `proxy/request_test.go`
- **Naming:** Go standard — `Test*` functions

### Test Execution

- **Run all tests:** `go test ./...`
- **Run by package:** `go test ./proxy`
- **Run specific test:** `go test -run 'TestName' ./proxy`
- **Run with verbosity:** `go test ./proxy -v`

**Important:** Do not run individual test files. Go tests must be run by package to resolve dependencies correctly.

### Code Style

- **Linter:** golangci-lint v2.8.0
- **Config:** `.golangci.yaml`
- **Enabled linters:** errcheck, govet, ineffassign, staticcheck, unused, goconst
- **Formatters:** gofmt (with simplify), goimports
- **Exclusions:** `gen/` directory (auto-generated gRPC code)

### Import Style

Standard Go imports. The project uses Go modules with dependencies defined in `go.mod`.

## Gaps & Caveats

### Go Version Quirk

The `go.mod` file specifies `go 1.25.5`, which is newer than commonly available container images (as of 2026-03-22, Go is at 1.23.x). This appears to be a typo or forward compatibility setting.

**Workaround:** Use `GOTOOLCHAIN=auto` environment variable, which instructs Go to automatically download the required version. All commands in the container recipe include this.

### Pre-commit Limitations

The `.pre-commit-config.yaml` hooks cannot be installed directly in a basic golang container because installing golangci-lint from source (as pre-commit does) requires Go 1.24+ according to golangci-lint's go.mod.

**Workarounds:**
- **Recommended:** Use the develop container workflow (`make build.develop`, `./scripts/develop.sh`) which pre-installs pre-commit environments.
- **Alternative:** Install golangci-lint binary directly and run `golangci-lint run` (as shown in the container recipe).

The CI workflow uses the first approach.

### Coverage

No coverage threshold is configured in the repository. Current coverage is **64.1%** for the proxy package.

### Test Execution Model

Go tests must be run by package, not by individual file. Running `go test ./proxy/marshaler_test.go` will fail with undefined symbol errors because Go can't resolve the package dependencies.

**Correct patterns:**
- `go test ./proxy` — run all tests in proxy package
- `go test ./proxy -run TestRESTResponse` — run specific test in proxy package

### Container Build Complexity

The project uses a multi-stage Dockerfile with three stages:

1. **develop** — UBI9 go-toolset:1.25 with pre-commit, protoc, golangci-lint
2. **build** — Compiles the Go binary for target platform
3. **runtime** — UBI9 ubi-micro with only the binary

Building the develop image takes 2-3 minutes due to installing protoc, pre-commit environments, and Go protoc plugins. The container recipe in this document uses a simpler approach (plain golang image + install golangci-lint) which is faster for validation.

## Project-Specific Context

### What This Project Does

KServe V2 REST Proxy uses gRPC-Gateway to create a reverse-proxy server that translates RESTful HTTP API requests into gRPC. It allows sending inference requests using the KServe V2 REST Predict Protocol to platforms that expect the gRPC V2 Predict Protocol.

### Generated Code

The `gen/` directory contains auto-generated gRPC gateway code from `grpc_predict_v2.proto`. To regenerate:

```bash
make run generate
```

This runs `protoc` inside the develop container. The generated code is committed to the repository and excluded from linting.

### Development Workflow

The intended development workflow uses containerized tooling:

1. **Enter dev container:** `make develop` (interactive shell) or `make run <target>` (run specific command)
2. **Generate stubs:** `make run generate`
3. **Format/lint:** `make run fmt`
4. **Test:** `make run test`
5. **Build image:** `make build`

The develop container approach avoids host environment dependency issues and matches the CI environment exactly.

## Summary

**For automated patch validation:**

1. **Can validate:** Yes, with the container recipe above
2. **Lint works:** ✅ Yes (golangci-lint)
3. **Tests work:** ✅ Yes (go test)
4. **Challenges:** Requires GOTOOLCHAIN=auto for Go version, pre-commit hooks need pre-built container
5. **Recommendation:** Use the simple container recipe for fast validation, or use `make build.develop` + `./scripts/develop.sh` to match CI exactly

**Agent readiness rating: MEDIUM** — All validation works, but requires understanding the Go version quirk and using GOTOOLCHAIN=auto. The project's own CI uses a pre-built develop container which avoids these issues.
