# Test Context: model-metadata-collection

## Overview

**Repository:** opendatahub-io/model-metadata-collection
**Language:** Go 1.24/1.25
**Build System:** Go modules + Makefile
**Agent Readiness:** **HIGH** — Lint and test commands validated successfully in container. An agent can clone, patch, lint, and test with clear pass/fail signals.

This is a Go application that extracts, enriches, and catalogs metadata from Red Hat AI container images. The project has comprehensive test coverage (16 test files across 8 packages) and standard Go tooling for linting.

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-model-metadata-collection \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

If `podman` is not available, use `docker` instead.

### 2. Install Dependencies

```bash
podman exec test-context-model-metadata-collection bash -c "cd /app && go mod download && go mod tidy"
```

**Expected:** Downloads ~30 Go packages, exit code 0.

### 3. Build Project

```bash
podman exec test-context-model-metadata-collection bash -c "cd /app && go build -o build/model-extractor ./cmd/model-extractor"
```

**Expected:** Creates `build/model-extractor` binary, exit code 0.

### 4. Install Linter (Optional)

```bash
podman exec test-context-model-metadata-collection bash -c "go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest"
```

**Expected:** Installs golangci-lint to `/go/bin/golangci-lint`.

### 5. Run Linters

#### golangci-lint (requires step 4)

```bash
podman exec test-context-model-metadata-collection bash -c "cd /app && golangci-lint run"
```

**Expected:** Exit code 0, no issues found.
**Validated:** ✅ PASSED

#### go vet

```bash
podman exec test-context-model-metadata-collection bash -c "cd /app && go vet ./..."
```

**Expected:** Exit code 0, no issues.
**Validated:** ✅ PASSED

#### Format Check

```bash
podman exec test-context-model-metadata-collection bash -c "cd /app && gofmt -l ."
```

**Expected:** No output (all files properly formatted), exit code 0.
**Validated:** ✅ PASSED

### 6. Run Tests

#### All Tests

```bash
podman exec test-context-model-metadata-collection bash -c "cd /app && go test -v ./..."
```

**Expected:** All tests pass, exit code 0. Tests 8 packages:
- `internal/catalog` (~37s)
- `internal/config` (<1s)
- `internal/enrichment` (<1s)
- `internal/huggingface` (<1s)
- `internal/metadata` (<1s)
- `internal/registry` (~16s)
- `pkg/types` (<1s)
- `pkg/utils` (<1s)

Total execution time: ~55 seconds.

**Validated:** ✅ PASSED (all 8 packages)

#### Single Package

```bash
podman exec test-context-model-metadata-collection bash -c "cd /app && go test -v ./internal/catalog"
```

#### Single Test

```bash
podman exec test-context-model-metadata-collection bash -c "cd /app && go test -v -run TestCreateModelsCatalog ./internal/catalog"
```

#### With Coverage

```bash
podman exec test-context-model-metadata-collection bash -c "cd /app && go test -v -race -coverprofile=coverage.out ./..."
```

**Note:** Not validated but should work. Adds race detection and coverage reporting.

### 7. Cleanup

```bash
podman rm -f test-context-model-metadata-collection
```

## Validation Results

All commands were validated in a `golang:1.25` container with the repository mounted at `/app`:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| **Dependencies** | `go mod download && go mod tidy` | ✅ PASS | Downloaded 30 packages successfully |
| **Build** | `go build -o build/model-extractor ./cmd/model-extractor` | ✅ PASS | Binary created with no errors |
| **Lint (golangci-lint)** | `golangci-lint run` | ✅ PASS | No issues found |
| **Lint (go vet)** | `go vet ./...` | ✅ PASS | No issues found |
| **Lint (format)** | `gofmt -l .` | ✅ PASS | All files properly formatted |
| **Tests** | `go test -v ./...` | ✅ PASS | 8 packages tested, all passed |

### Test Output Summary

```
ok  	github.com/opendatahub-io/model-metadata-collection/internal/catalog	37.394s
ok  	github.com/opendatahub-io/model-metadata-collection/internal/config	0.009s
ok  	github.com/opendatahub-io/model-metadata-collection/internal/enrichment	0.015s
ok  	github.com/opendatahub-io/model-metadata-collection/internal/huggingface	0.321s
ok  	github.com/opendatahub-io/model-metadata-collection/internal/metadata	0.006s
ok  	github.com/opendatahub-io/model-metadata-collection/internal/registry	16.317s
ok  	github.com/opendatahub-io/model-metadata-collection/pkg/types	0.003s
ok  	github.com/opendatahub-io/model-metadata-collection/pkg/utils	0.952s
```

## CI/CD

**System:** GitHub Actions
**Gating Workflow:** `.github/workflows/build-and-push-static-model-catalog-data.yml`

### Gating Checks

The following check runs on pull requests to `main` (when `data/**`, `Dockerfile`, or workflow files change):

```yaml
- name: Run tests
  run: make test
```

This executes: `go test -v ./...`

**Status:** ✅ Required for merge

### Other Workflows

- `sync-branch-stable.yml` — Syncs main to stable branch (not a test workflow)
- `sync-branch-stable2x.yml` — Syncs main to stable-2.x branch (not a test workflow)

### Makefile Targets

The Makefile provides comprehensive CI targets:

```bash
make deps          # Download and tidy dependencies
make fmt-check     # Check code formatting (fails if unformatted)
make vet           # Run go vet
make lint          # Run golangci-lint (requires golangci-lint installed)
make check         # Run all checks: fmt-check + vet + lint
make test          # Run tests: go test -v ./...
make test-coverage # Run tests with race detection and coverage
make ci            # Full CI pipeline: deps + check + test + build
```

**Recommended for patch validation:** `make ci` (runs full pipeline)

## Conventions

### Test Files

- **Pattern:** `*_test.go`
- **Location:** Co-located with source files in respective packages
- **Framework:** Go standard testing library
- **Style:** Table-driven tests with `t.Run()` subtests

### Test Naming

- **Test Functions:** `Test*` (e.g., `TestCreateModelsCatalog`)
- **Subtests:** Descriptive names in `t.Run()` (e.g., `t.Run("ValidCatalog", ...)`)
- **Helper Functions:** Lowercase names, often suffixed with `Helper` or embedded in tests

### Import Style

Standard Go import grouping:
1. Standard library packages
2. External packages
3. Internal packages from this project

### Code Style

- Uses `gofmt` for formatting
- Passes `go vet` static analysis
- Passes `golangci-lint` with default linters
- Uses pointer types for optional fields in metadata structs
- Comprehensive error handling with descriptive messages

## Project Structure

```
├── cmd/
│   ├── model-extractor/          # Main CLI application for metadata extraction
│   └── metadata-report/          # CLI for generating metadata reports
├── internal/                     # Internal packages
│   ├── catalog/                  # Catalog generation services (has tests)
│   ├── config/                   # Configuration management (has tests)
│   ├── enrichment/               # Metadata enrichment services (has tests)
│   ├── huggingface/             # HuggingFace API integration (has tests)
│   ├── metadata/                # Metadata parsing and migration (has tests)
│   ├── registry/                # Container registry services (has tests)
│   └── report/                  # Metadata reporting and analysis (no tests)
├── pkg/                         # Public packages
│   ├── types/                   # Shared type definitions (has tests)
│   └── utils/                   # Utility functions (has tests)
├── data/                        # Model index and catalog YAML files
├── sample-data/                 # Sample data for benchmarks
├── Makefile                     # Build and CI targets
└── go.mod                       # Go module definition (Go 1.24/1.25)
```

## Gaps & Caveats

**None.** This repository has excellent test coverage and all validation steps passed successfully.

### Notes

- Some tests attempt network calls to HuggingFace API and container registries but handle failures gracefully (tests still pass without external access)
- No integration tests requiring cluster infrastructure or external services
- The `internal/report` package has no tests (but it's a reporting tool, not core logic)
- The `cmd/` binaries have no tests (standard for Go CLI applications)
- Tests use `t.TempDir()` for isolation, so parallel test execution is safe

## Dependencies

**Go Version:** 1.24 (minimum), toolchain 1.25.7 (recommended)

**Key Dependencies:**
- `github.com/containers/image/v5` — Container image inspection
- `gopkg.in/yaml.v3` — YAML parsing
- `golang.org/x/text` — Text processing

**Dev Dependencies:**
- `golangci-lint` — Linting (install separately: `go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest`)

**System Requirements:**
- No system packages required for testing
- For production use: Access to container registries (registry.redhat.io) and HuggingFace API

## Quick Start for Agents

To validate a patch:

1. **Start container:** `podman run -d --name test-context-model-metadata-collection -v $(pwd):/app:Z -w /app golang:1.25 sleep infinity`
2. **Install deps:** `podman exec test-context-model-metadata-collection bash -c "cd /app && go mod download && go mod tidy"`
3. **Run checks:** `podman exec test-context-model-metadata-collection bash -c "cd /app && go vet ./... && gofmt -l ."`
4. **Run tests:** `podman exec test-context-model-metadata-collection bash -c "cd /app && go test ./..."`
5. **Cleanup:** `podman rm -f test-context-model-metadata-collection`

**Expected result:** All steps exit with code 0.

## Additional Resources

- **README:** `README.md` — Comprehensive project documentation
- **Makefile:** `Makefile` — All available build and test targets
- **CI Config:** `.github/workflows/build-and-push-static-model-catalog-data.yml` — Production CI pipeline
