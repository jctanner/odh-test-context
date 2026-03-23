# Test Context: ai-edge

**Analyzed:** 2026-03-22T21:31:30Z
**Organization:** opendatahub-io
**Languages:** Go
**Agent Readiness:** LOW - CLI unit tests work but e2e tests require OpenShift cluster infrastructure

## Overview

This repository provides proof-of-concept tools for deploying AI/ML inference workloads to edge environments using OpenShift, ACM, and GitOps. The repo contains a Go-based CLI tool and Kubernetes manifests for edge cluster management. Testing is split between standalone CLI unit tests (which work) and integration tests requiring OpenShift cluster access (which cannot run in standard containers).

**Key limitation:** No CI/CD configured. E2E tests require live OpenShift cluster with Tekton pipelines.

## Container Recipe

This is the validated recipe for running lint and tests in a container. Only CLI unit tests work without cluster access.

### 1. Start the container

```bash
podman run -d --name test-context-ai-edge \
  -v /path/to/ai-edge:/app:Z \
  -w /app \
  golang:1.21 \
  sleep infinity
```

### 2. Install system dependencies

```bash
podman exec test-context-ai-edge bash -c "apt-get update && apt-get install -y make git"
```

### 3. Install Go dependencies

```bash
podman exec test-context-ai-edge bash -c "cd /app/cli && go mod download"
```

### 4. Build the CLI (optional, to verify build works)

```bash
podman exec test-context-ai-edge bash -c "cd /app/cli && go build -o odh ./cmd/main.go"
```

Expected: Creates a 59MB binary at `/app/cli/odh`

### 5. Run linting (go vet)

```bash
podman exec test-context-ai-edge bash -c "cd /app/cli && go vet ./..."
```

**Status:** FAIL (8 issues found)
**Exit code:** 1
**Notes:** Found legitimate issues with unkeyed struct fields in `pkg/commands/images/images.go` and `pkg/commands/models/models.go`. This indicates code quality issues that should be fixed, not a broken linter.

<details>
<summary>Sample output</summary>

```
pkg/commands/images/images.go:64:11: struct literal uses unkeyed fields
pkg/commands/images/images.go:75:11: struct literal uses unkeyed fields
pkg/commands/images/images.go:84:11: struct literal uses unkeyed fields
pkg/commands/images/images.go:102:11: struct literal uses unkeyed fields
pkg/commands/images/images.go:114:11: struct literal uses unkeyed fields
pkg/commands/models/models.go:71:11: struct literal uses unkeyed fields
pkg/commands/models/models.go:82:11: struct literal uses unkeyed fields
pkg/commands/models/models.go:92:11: struct literal uses unkeyed fields
```
</details>

### 6. Run linting (go fmt)

```bash
podman exec test-context-ai-edge bash -c "cd /app/cli && go fmt ./..."
```

**Status:** FAIL (1 file needs formatting)
**Exit code:** 1 (if checked for output)
**Notes:** `cmd/main.go` needs formatting. Running `go fmt` will auto-fix this.

### 7. Run CLI unit tests

```bash
podman exec test-context-ai-edge bash -c "cd /app/cli && go test ./cmd/... ./... -v"
```

**Status:** PASS
**Exit code:** 0
**Tests:** 3 passed (TestClient_GetRegisteredModels with 3 subtests)

<details>
<summary>Sample output</summary>

```
=== RUN   TestClient_GetRegisteredModels
    client_test.go:81: Given the need to test getting registered models from the model registry.
=== RUN   TestClient_GetRegisteredModels/no_models
    client_test.go:86: 	TestClient_GetRegisteredModels/no_models:	When the model registry returns no models
    client_test.go:100: 	TestClient_GetRegisteredModels/no_models:	✓	Should not receive an error
    client_test.go:113: 	TestClient_GetRegisteredModels/no_models:	✓	Should receive the expected models
=== RUN   TestClient_GetRegisteredModels/one_model
    client_test.go:86: 	TestClient_GetRegisteredModels/one_model:	When the model registry returns one model
    client_test.go:100: 	TestClient_GetRegisteredModels/one_model:	✓	Should not receive an error
    client_test.go:113: 	TestClient_GetRegisteredModels/one_model:	✓	Should receive the expected models
=== RUN   TestClient_GetRegisteredModels/many_models
    client_test.go:86: 	TestClient_GetRegisteredModels/many_models:	When the model registry returns many models
    client_test.go:100: 	TestClient_GetRegisteredModels/many_models:	✓	Should not receive an error
    client_test.go:113: 	TestClient_GetRegisteredModels/many_models:	✓	Should receive the expected models
--- PASS: TestClient_GetRegisteredModels (0.00s)
    --- PASS: TestClient_GetRegisteredModels/no_models (0.00s)
    --- PASS: TestClient_GetRegisteredModels/one_model (0.00s)
    --- PASS: TestClient_GetRegisteredModels/many_models (0.00s)
PASS
ok  	github.com/opendatahub-io/ai-edge/cli/pkg/modelregistry	0.004s
```
</details>

### 8. Alternative: Run CLI tests via Makefile

```bash
podman exec test-context-ai-edge bash -c "cd /app && make cli-test"
```

**Status:** PASS
Same result as direct `go test` command.

### 9. Run a single test file

```bash
podman exec test-context-ai-edge bash -c "cd /app/cli && go test ./pkg/modelregistry/client_test.go -v"
```

### 10. Run a specific test

```bash
podman exec test-context-ai-edge bash -c "cd /app/cli && go test ./pkg/modelregistry -run TestClient_GetRegisteredModels/one_model -v"
```

### 11. Cleanup

```bash
podman rm -f test-context-ai-edge
```

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install deps | `go mod download` | ✅ PASS | All dependencies installed cleanly |
| Build | `go build -o odh ./cmd/main.go` | ✅ PASS | 59MB binary created |
| Lint (vet) | `go vet ./...` | ❌ FAIL | 8 issues with unkeyed struct fields (legitimate violations) |
| Lint (fmt) | `go fmt ./...` | ❌ FAIL | 1 file needs formatting (cmd/main.go) |
| CLI tests | `go test ./cmd/... ./... -v` | ✅ PASS | 3/3 tests passed |
| E2E tests | `go test -timeout 60m -shuffle off` | ❌ FAIL | Requires config.json + OpenShift cluster |
| Shell tests | Shell scripts in test/shell-pipeline-tests/ | ❌ SKIP | Require OpenShift cluster with `oc` CLI |

## CI/CD

**System:** None configured

**Status:** GitHub Actions not implemented (explicitly noted in test/e2e-tests/README.md: "CI/CD with Github Actions: Not yet implemented")

No gating checks defined. No `.github/workflows/` directory exists.

## Conventions

- **Test file naming:** `*_test.go` (standard Go)
- **Test function naming:** `Test*` functions (standard Go)
- **Import style:** Standard Go import grouping (stdlib, external, internal)
- **Project layout:** Standard Go layout with `cmd/` for CLI entry point, `pkg/` for packages
- **Test location:** Colocated with source files (`pkg/modelregistry/client_test.go`)

## Gaps & Caveats

### Critical Gaps

1. **No CI/CD:** No GitHub Actions workflows configured. The e2e test README explicitly states this is not yet implemented.

2. **No linter config:** No `.golangci.yml` or similar configuration. Only standard Go tooling (`go vet`, `go fmt`) available.

3. **E2E tests require infrastructure:** The e2e tests in `test/e2e-tests/` require:
   - OpenShift cluster with Tekton pipelines installed
   - A manually created `config.json` file with credentials for:
     - S3 bucket (AWS secret/access keys)
     - Image registry (Quay.io username/password)
     - Git repositories (optional for private repos)
     - GitOps setup (GitHub API token)
   - Running Tekton pipeline infrastructure

4. **Shell tests require cluster:** The shell-based tests in `test/shell-pipeline-tests/` require:
   - OpenShift cluster access via `oc` CLI
   - Tekton pipelines installed and running
   - Proper namespace setup

### Current Code Quality Issues

5. **go vet failures:** 8 issues with unkeyed struct field initialization in production code that should be fixed

6. **go fmt failures:** 1 file (`cmd/main.go`) needs formatting

### What Works

- ✅ CLI unit tests run perfectly in a container without any external dependencies
- ✅ CLI builds successfully
- ✅ Dependencies install cleanly
- ✅ Standard Go tooling (vet, fmt, test) all work

### What Doesn't Work Without Cluster Access

- ❌ E2E tests (require OpenShift + Tekton + config.json)
- ❌ Shell pipeline tests (require OpenShift + `oc` CLI)
- ❌ Integration testing of the actual use case (deploying models to edge clusters)

## How to Use This for Patch Validation

### For CLI changes

If your patch modifies code in the `cli/` directory:

1. Spin up the container using the recipe above
2. Run `go vet ./...` to check for issues (currently fails, fix existing issues first)
3. Run `go fmt ./...` to format code
4. Run `go test ./cmd/... ./... -v` to run unit tests
5. Verify all tests pass and no new vet/fmt issues introduced

### For pipeline/manifest changes

If your patch modifies Kubernetes manifests or pipeline definitions in `acm/`, `manifests/`, or `examples/`:

**You cannot validate these in a container.** You need:

1. An OpenShift cluster with Tekton pipelines
2. Follow setup in `test/e2e-tests/README.md` to create `config.json`
3. Run `make go-test` to execute e2e tests
4. Or run individual shell test scripts from `test/shell-pipeline-tests/`

### For documentation/minor changes

If your patch only touches documentation or non-code files, no testing is required beyond visual review.

## Recommendations for Improving Agent Readiness

To move this repo from LOW to MEDIUM/HIGH agent readiness:

1. **Add CI/CD:** Implement GitHub Actions workflows with:
   - Go vet and fmt checks (can run in Actions without cluster)
   - CLI unit tests (can run in Actions without cluster)
   - Clear pass/fail criteria

2. **Add linter config:** Create `.golangci.yml` with project standards

3. **Fix existing issues:**
   - Fix the 8 `go vet` issues with unkeyed struct fields
   - Format `cmd/main.go` with `go fmt`

4. **Document cluster test requirements:** Clearly separate "can run in CI" tests from "needs live cluster" tests

5. **Mock/stub e2e tests:** Consider adding a subset of e2e tests that use mocks/fakes instead of real cluster resources

Without these changes, automated patch validation can only check CLI code quality, not the actual functionality of deploying models to edge clusters.
