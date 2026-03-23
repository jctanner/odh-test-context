# Test Context: models-as-a-service

**Agent Readiness: MEDIUM** — maas-api is fully validated and ready; maas-controller has lint issues but tests pass.

## Overview

Go 1.25 project with two modules (maas-api and maas-controller) for OpenDataHub Models as a Service platform. Uses golangci-lint for linting, standard Go testing, and Make for builds. GitHub Actions and Tekton for CI/CD.

- **Languages:** Go 1.25
- **Build System:** Make + Go modules
- **Test Framework:** Go testing (testing package)
- **Linter:** golangci-lint v2.6.2
- **CI/CD:** GitHub Actions (PR validation) + Tekton (container builds)

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-models-as-a-service \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

**Note:** Use `docker` instead of `podman` if podman is unavailable. The `:Z` flag is for SELinux relabeling.

### 2. Install System Dependencies

```bash
podman exec test-context-models-as-a-service bash -c \
  "apt-get update && apt-get install -y make git"
```

**Note:** make and git are pre-installed in golang:1.25 image, but this ensures they're available.

### 3. Install Project Dependencies

**For maas-api:**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-api && go mod download"
```

**For maas-controller:**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-controller && go mod download"
```

**Expected:** No output on success. Exit code 0.

### 4. Run Linting

**For maas-api (validated: PASS):**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-api && make lint"
```

**Expected output:**
```
/app/maas-api/bin/tools/golangci-lint fmt
/app/maas-api/bin/tools/golangci-lint run
0 issues.
```

**Exit code:** 0 (success)

**For maas-controller (validated: FAIL):**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-controller && make lint"
```

**Expected to fail with:**
- Formatting issues (missing/extra newlines in test files)
- 4 lint issues:
  - 2 staticcheck: should convert type instead of using struct literal
  - 2 unused: unused functions `gatewayName()` and `clusterAudience()`

**Exit code:** 1 (failure)

**Note:** To check just the linting analysis (not formatting), run:
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-controller && /app/maas-controller/bin/tools/golangci-lint run"
```

### 5. Run Tests

**For maas-api (validated: PASS):**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-api && make test"
```

**Expected output (excerpt):**
```
go test -v -race -coverprofile=coverage.out /app/maas-api/cmd/... /app/maas-api/internal/...
=== RUN   TestIsLocalhostOrigin
...
PASS
coverage: 84.7% of statements
Test coverage report generated: /app/maas-api/coverage.html
```

**Exit code:** 0 (success)
**Test count:** 12+ packages tested
**Coverage:** 84.7%

**For maas-controller (validated: PASS):**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-controller && make test"
```

**Expected output:**
```
go mod tidy
go test ./...
ok  	github.com/opendatahub-io/models-as-a-service/maas-controller/pkg/controller/maas	0.038s
```

**Exit code:** 0 (success)

### 6. Build Binaries

**For maas-api:**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-api && make binary"
```

**Expected:** Binary created at `/app/maas-api/bin/maas-api`

**For maas-controller:**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-controller && make build"
```

**Expected:** Binary created at `/app/maas-controller/bin/manager`

### 7. Run Single Test File

**Template:**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/{module} && go test -v {relative_path_to_test_file}"
```

**Example (maas-api):**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-api && go test -v ./internal/api_keys/handler_test.go"
```

**Example (maas-controller):**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-controller && go test -v ./pkg/controller/maas/maasmodelref_controller_test.go"
```

### 8. Run Single Test Function

**Template:**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/{module} && go test -v -run ^{TestFunctionName}$ {package_path}"
```

**Example (maas-api):**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-api && go test -v -run ^TestIsLocalhostOrigin$ ./cmd"
```

**Example (maas-controller):**
```bash
podman exec test-context-models-as-a-service bash -c \
  "cd /app/maas-controller && go test -v -run ^TestMaaSModelRefReconciler$ ./pkg/controller/maas"
```

### 9. Cleanup

**Always run when done:**
```bash
podman rm -f test-context-models-as-a-service
```

## Validation Results

### Summary

| Module | Dependencies | Lint | Tests | Build |
|--------|-------------|------|-------|-------|
| maas-api | ✅ PASS | ✅ PASS (0 issues) | ✅ PASS (84.7% coverage) | ✅ PASS |
| maas-controller | ✅ PASS | ❌ FAIL (4 issues + formatting) | ✅ PASS | ✅ PASS |

### Detailed Results

**maas-api:**
- ✅ `go mod download` — successful
- ✅ `make lint` — 0 issues, golangci-lint v2.6.2 auto-installed
- ✅ `make test` — all tests passed, 84.7% coverage, race detector enabled
- ✅ `make binary` — binary built at bin/maas-api

**maas-controller:**
- ✅ `go mod download` — successful
- ❌ `make lint` — formatting issues (newlines) + 4 code issues:
  - `pkg/controller/maas/maasmodelref_controller_test.go:296,358`: should convert type instead of struct literal
  - `pkg/controller/maas/maasauthpolicy_controller.go:61,68`: unused functions `gatewayName()` and `clusterAudience()`
- ✅ `make test` — all tests passed
- ✅ `make build` — binary built at bin/manager

## CI/CD

### GitHub Actions Workflows

**Gating checks (run on pull_request):**

1. **maas-api lint** (`.github/workflows/maas-api-ci.yml`)
   - Trigger: Changes to `maas-api/**`
   - Command: `cd maas-api && golangci-lint run`
   - golangci-lint version extracted from `tools.mk`

2. **maas-api test** (`.github/workflows/maas-api-ci.yml`)
   - Trigger: Changes to `maas-api/**`
   - Command: `cd maas-api && make test`
   - Uploads coverage reports as artifacts

3. **maas-api build** (`.github/workflows/maas-api-ci.yml`)
   - Trigger: Changes to `maas-api/**`
   - Command: `cd maas-api && make build-image`

4. **verify-codegen** (`.github/workflows/build-test.yml`)
   - Trigger: Changes to `maas-controller/api/**`, `deployment/base/maas-controller/crd/**`
   - Command: `cd maas-controller && make verify-codegen`
   - Ensures generated CRDs and deepcopy code are up to date

5. **validate-manifests** (`.github/workflows/build-test.yml`)
   - Trigger: Changes to `deployment/**`, `maas-controller/api/**`
   - Command: `./scripts/ci/validate-manifests.sh`
   - Uses kustomize 5.7.1

### Tekton Pipelines

Located in `.tekton/`:
- `odh-maas-api-pull-request.yaml` — builds container image for maas-api PRs
- `odh-maas-api-push.yaml` — builds and publishes on push to main
- `odh-maas-controller-pull-request.yaml` — builds container image for maas-controller PRs
- `odh-maas-controller-push.yaml` — builds and publishes on push to main

Uses multi-arch container build pipeline from `github.com/opendatahub-io/odh-konflux-central`.

## Conventions

### Test Files
- Pattern: `*_test.go`
- Location:
  - `maas-api/cmd/*_test.go`
  - `maas-api/internal/*/*_test.go`
  - `maas-controller/pkg/controller/maas/*_test.go`

### Test Functions
- Naming: `func Test*` for standard tests
- Style: Table-driven tests are prevalent
- Controller tests use `controller-runtime` testing framework

### Import Organization
Enforced by `gci` formatter (in maas-api):
1. Standard library
2. External packages
3. `github.com/opendatahub-io/models-as-a-service/maas-api/` prefixed
4. Blank imports
5. Dot imports

### Code Generation
maas-controller uses controller-gen for:
- CRD manifests: `make manifests`
- Deepcopy methods: `make generate`

Verify with: `make verify-codegen`

## Gaps & Caveats

### Known Issues

1. **maas-controller lint failures**
   - Current codebase has 4 lint violations that need fixing
   - Formatting issues (newlines) also present
   - Lint validation will fail until these are resolved

2. **No .golangci.yml for maas-controller**
   - Uses golangci-lint but without custom configuration
   - Relies on default settings

3. **No integration tests**
   - All tests are unit tests
   - No tests requiring PostgreSQL (used by maas-api in production)
   - No tests requiring Kubernetes cluster
   - Good for CI speed, but integration issues may not be caught

4. **Coverage reporting inconsistency**
   - maas-api generates coverage reports (84.7%)
   - maas-controller does not generate coverage reports

### Infrastructure Requirements

**Development/Testing:** None — all tests are unit tests and run in container.

**Production:** Requires:
- PostgreSQL database (maas-api for API key management)
- OpenShift/Kubernetes cluster (4.19.9+)
- Kuadrant/Authorino/Limitador for API gateway and policies
- KServe for model serving

## Quick Reference

### Lint Commands
```bash
# maas-api (with auto-fix)
cd maas-api && make lint LINT_FIX=true

# maas-controller (with auto-fix)
cd maas-controller && make lint LINT_FIX=true
```

### Test Commands
```bash
# Both modules
cd maas-api && make test && cd ../maas-controller && make test

# Individual modules
cd maas-api && make test
cd maas-controller && make test

# With specific test
cd maas-api && go test -v -run ^TestIsLocalhostOrigin$ ./cmd
```

### Build Commands
```bash
# Binaries
cd maas-api && make binary
cd maas-controller && make build

# Container images
cd maas-api && make build-image REPO=<repo> TAG=<tag>
cd maas-controller && make build-image REPO=<repo> TAG=<tag>
```

### Code Generation (maas-controller only)
```bash
cd maas-controller && make generate  # Generate deepcopy
cd maas-controller && make manifests  # Generate CRDs
cd maas-controller && make verify-codegen  # Verify all up to date
```

---

**Generated:** 2026-03-22T23:29:41Z
**Confidence:** High — All commands validated in golang:1.25 container
**Agent Readiness:** Medium — maas-api ready for full automation; maas-controller needs lint fixes
