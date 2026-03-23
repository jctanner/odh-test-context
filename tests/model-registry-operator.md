# Test Context: model-registry-operator

**Agent Readiness: HIGH** — All lint and test commands validated successfully in a standard Go container.

## Overview

- **Repository:** opendatahub-io/model-registry-operator
- **Language:** Go 1.25.0 (CI uses 1.25.7)
- **Build System:** Make + Go modules
- **Test Framework:** Ginkgo/Gomega (BDD) with envtest (Kubernetes controller testing)
- **CI System:** GitHub Actions (.github/workflows/build.yml)

This is a Kubernetes operator built with kubebuilder/controller-runtime. Tests use envtest which simulates a Kubernetes control plane for realistic controller testing without requiring a full cluster.

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-model-registry-operator \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

**Note:** Use `docker` instead of `podman` if podman is not available. The `:Z` flag is for SELinux systems; omit it on non-SELinux systems if it causes issues.

### 2. Install System Dependencies

System dependencies (make, git, curl, wget) are already present in the golang:1.25 image. Verify with:

```bash
podman exec test-context-model-registry-operator bash -c "which make git"
```

### 3. Install Go Dependencies

```bash
podman exec test-context-model-registry-operator bash -c "cd /app && go mod download"
```

**Expected result:** Silent success (exit 0, no output)

### 4. Run Linters

#### Go fmt (formatting check)

```bash
podman exec test-context-model-registry-operator bash -c "cd /app && make fmt"
```

**Validated:** ✅ Exit 0
**Expected output:** `go fmt ./...` (may list files if formatting changes are applied)

#### Go vet (static analysis)

```bash
podman exec test-context-model-registry-operator bash -c "cd /app && make vet"
```

**Validated:** ✅ Exit 0
**Expected output:** `go vet ./...` (silent if no issues found)

#### Govulncheck (vulnerability scanning)

```bash
podman exec test-context-model-registry-operator bash -c "cd /app && make govulncheck"
```

**Validated:** ✅ Exit 0
**Expected output:** `No vulnerabilities found.`

**Note:** govulncheck may report vulnerabilities in Go stdlib that require Go 1.25.8+. This is expected and noted in the Makefile.

### 5. Run Tests

```bash
podman exec test-context-model-registry-operator bash -c "cd /app && timeout 300 make test"
```

**Validated:** ✅ Exit 0, all tests passed
**Expected output:**
```
ok  	github.com/opendatahub-io/model-registry-operator/api/v1alpha1	6.473s	coverage: 23.5% of statements
ok  	github.com/opendatahub-io/model-registry-operator/api/v1beta1	6.668s	coverage: 42.9% of statements
ok  	github.com/opendatahub-io/model-registry-operator/internal/controller	29.546s	coverage: 61.8% of statements
ok  	github.com/opendatahub-io/model-registry-operator/internal/controller/config	5.608s	coverage: 74.0% of statements
ok  	github.com/opendatahub-io/model-registry-operator/internal/migration	6.248s	coverage: 38.7% of statements
ok  	github.com/opendatahub-io/model-registry-operator/internal/utils	(cached)	coverage: 20.0% of statements
```

**Test duration:** ~60 seconds (includes tool downloads on first run, ~30 seconds on subsequent runs)
**Coverage:** 20-74% across packages
**Test count:** 61 specs in controller suite

**Note:** The first test run downloads envtest binaries (etcd, kube-apiserver, kubectl) to `bin/k8s/1.34.1-linux-amd64/`. Subsequent runs are faster. You may see a harmless warning about `conversion-gen --version` not being supported.

### 6. Run Tests for Specific Package

To test a specific package (e.g., only controller tests):

```bash
podman exec test-context-model-registry-operator bash -c "cd /app && make test" | grep "internal/controller"
```

Or use `go test` directly (requires envtest setup):

```bash
podman exec test-context-model-registry-operator bash -c \
  'cd /app && KUBEBUILDER_ASSETS="$(bin/setup-envtest use 1.34 --bin-dir bin -p path)" go test ./internal/controller -v'
```

**Note:** Go test files cannot be run in isolation (e.g., `go test file_test.go`) because they depend on other files in the package. Always test at the package level.

### 7. Run Build

```bash
podman exec test-context-model-registry-operator bash -c "cd /app && make build"
```

**Validated:** ✅ Exit 0
**Expected output:** Binary at `bin/manager` (~90MB)

**Note:** `make build` includes code generation (manifests, deepcopy, conversion), which may modify files. CI checks for uncommitted generated files as part of the build check.

### 8. Cleanup

Always clean up the container when done:

```bash
podman rm -f test-context-model-registry-operator
```

## Validation Results

All commands were validated in a `golang:1.25` container:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Dependencies | `go mod download` | ✅ Pass | Silent success |
| Build | `make build` | ✅ Pass | 90MB binary at bin/manager |
| Lint (fmt) | `make fmt` | ✅ Pass | No formatting issues |
| Lint (vet) | `make vet` | ✅ Pass | No static analysis issues |
| Lint (vuln) | `make govulncheck` | ✅ Pass | No vulnerabilities |
| Tests | `make test` | ✅ Pass | 61 specs, coverage 20-74% |

## CI/CD

### Gating Checks (from `.github/workflows/build.yml`)

The following checks gate pull request merges:

1. **Build** — `make build`
   - Includes: sync-images, manifests generation, code generation, fmt, vet, go build
   - Ensures operator binary builds successfully
   - Exit code must be 0

2. **Uncommitted changes check** — `git status --porcelain`
   - Ensures all generated code is committed (manifests, deepcopy, conversion files)
   - Common failure: developer ran `make build` but forgot to commit generated files
   - Exit code must be 0 (empty output)

3. **Tests** — `make test`
   - Runs all Ginkgo/Gomega specs with envtest
   - Generates coverage report (cover.out)
   - Exit code must be 0

4. **Kustomize validation** — `kustomize build config/overlays/odh/`
   - Validates Kubernetes manifests build correctly
   - Catches kustomize configuration errors
   - Exit code must be 0

### Advisory Checks

- **Image build test** (`.github/workflows/build-image-pr.yml`) — Builds container image, deploys to Kind cluster, creates test ModelRegistry CR. Not required to merge but runs on PRs.

### CI Configuration

- **Trigger:** `on: pull_request` (plus `on: push` to main)
- **Runner:** `ubuntu-latest`
- **Go version:** 1.25.7 (via `actions/setup-go@v6`)
- **Caching:** `bin/` directory cached based on Makefile hash

## Conventions

### Test Files

- **Pattern:** `*_test.go` files
- **Suite entry points:** `TestXxx(t *testing.T)` functions that call `RunSpecs(t, "Suite Name")`
- **Suite setup:** `*suite_test.go` files with `BeforeSuite`/`AfterSuite` hooks
- **BDD style:** `Describe("Component", func() { It("should behave", func() { ... }) })`

Example test file structure:
```
internal/controller/
  ├── suite_test.go              # Test suite setup (BeforeSuite, envtest)
  ├── modelregistry_controller_test.go  # Controller behavior specs
  └── capabilities_test.go       # Helper function tests
```

### Code Generation

The project uses code generation extensively:

- **CRDs/RBAC:** `make manifests` generates `config/crd/bases/*.yaml`
- **DeepCopy methods:** `make generate` creates `zz_generated.deepcopy.go`
- **Conversion functions:** `make generate` creates `zz_generated.conversion.go`

Generated files must be committed. CI fails if `make build` produces uncommitted changes.

### Import Style

- **Absolute imports:** `github.com/opendatahub-io/model-registry-operator/...`
- **Grouped:** Standard library, then third-party, then local packages
- **Dot imports in tests:** `. "github.com/onsi/ginkgo/v2"` for BDD style

### Project Layout

Standard kubebuilder structure:

- `api/` — CRD type definitions (v1alpha1, v1beta1)
- `cmd/` — Main entrypoint (`main.go`)
- `internal/controller/` — Reconciliation logic
- `internal/migration/` — Version migration utilities
- `internal/utils/` — Helper functions
- `config/` — Kubernetes manifests (CRDs, RBAC, kustomize overlays)

## Gaps & Caveats

**None identified.** This repository has excellent testability:

- ✅ All lint and test commands work in a standard container
- ✅ No cluster or external service dependencies for unit tests
- ✅ Clear CI configuration with explicit gating checks
- ✅ Tests run in ~30 seconds after initial setup
- ✅ Good test coverage (20-74% across packages)

The only minor note: `conversion-gen` doesn't support `--version` flag, causing a harmless warning in Makefile output. This doesn't affect functionality.

## Running Tests Locally (Outside Container)

If you have Go 1.25+ installed locally:

```bash
# Install dependencies
go mod download

# Run all checks (what CI runs)
make build  # Includes manifests, generate, fmt, vet, go build
make test   # Runs all tests with coverage

# Individual checks
make fmt           # Format code
make vet           # Static analysis
make govulncheck   # Vulnerability scan

# Run specific package tests
KUBEBUILDER_ASSETS="$(bin/setup-envtest use 1.34 --bin-dir bin -p path)" \
  go test ./internal/controller -v

# Run specific test by name
KUBEBUILDER_ASSETS="$(bin/setup-envtest use 1.34 --bin-dir bin -p path)" \
  go test ./internal/controller -run TestControllers/ControllerSuite -v
```

## Additional Commands

### Generate manifests (CRDs, RBAC)

```bash
make manifests
```

### Generate code (deepcopy, conversion)

```bash
make generate
```

### Validate kustomize overlays

```bash
kustomize build config/overlays/odh/ > /dev/null
```

### Check for uncommitted generated files

```bash
make build
git status --porcelain  # Should be empty
```

---

**Generated:** 2026-03-22T23:22:00Z
**Validation container:** `golang:1.25`
**Validation status:** All commands passed ✅
