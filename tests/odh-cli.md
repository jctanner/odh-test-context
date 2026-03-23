# Test Context: odh-cli

**Organization:** opendatahub-io
**Repository:** odh-cli
**Analyzed:** 2026-03-22T23:34:40Z
**Agent Readiness:** **HIGH** — Lint and test commands fully validated. Agents can clone, patch, lint, and test with clear pass/fail signals.

---

## Overview

Go CLI tool (kubectl plugin) for OpenDataHub/RHOAI operations including backup, migration, and cluster linting.

- **Language:** Go 1.25.7
- **Build System:** Makefile + go build
- **Test Framework:** Go testing + Gomega (no Ginkgo)
- **Linter:** golangci-lint v2.8.0
- **CI:** GitHub Actions (test + lint are gating checks)

**Why HIGH readiness?** All commands validated in container. Clean lint (0 issues), all tests pass (741+ tests), dependencies install cleanly, binary builds and runs successfully.

---

## Container Recipe

This is a **complete, copy-paste recipe** for validating patches. Every command has been tested and verified.

### 1. Start Container

```bash
podman run -d --name test-odh-cli \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.22 \
  sleep infinity
```

**Why golang:1.22?** The project requires Go 1.25.7, but with `GOTOOLCHAIN=auto`, Go will automatically download the correct version. Using golang:1.22 as base works perfectly.

### 2. Install System Dependencies

```bash
podman exec test-odh-cli bash -c "apt-get update && apt-get install -y make git"
```

**Already included in golang:1.22:** make and git are typically present, but this ensures they're available.

### 3. Install Project Dependencies

```bash
podman exec test-odh-cli bash -c "cd /app && GOTOOLCHAIN=auto go mod download"
```

**Expected output:**
```
go: downloading go1.25.7 (linux/amd64)
(completes with no output)
```

**Critical:** Must use `GOTOOLCHAIN=auto` because go.mod requires Go 1.25.7. This automatically downloads the correct Go version.

### 4. Build the Binary

```bash
podman exec test-odh-cli bash -c "cd /app && GOTOOLCHAIN=auto make build"
```

**Expected output:**
```
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
	go build -ldflags "-X 'github.com/opendatahub-io/odh-cli/internal/version.Version=...' ..." -o bin/kubectl-odh cmd/main.go
```

**Verify binary:**
```bash
podman exec test-odh-cli bash -c "cd /app && ./bin/kubectl-odh version"
```

Expected: `kubectl-odh version <hash> (commit: <hash>, built: <timestamp>)`

### 5. Run Linter (Validated ✓)

```bash
podman exec test-odh-cli bash -c "cd /app && GOTOOLCHAIN=auto make lint"
```

**Expected output:**
```
go: github.com/golangci/golangci-lint/v2@v2.8.0 requires go >= 1.24.0; switching to go1.25.8
0 issues.
```

**Exit code:** 0
**Status:** PASS (0 issues)

**Note:** First run downloads golangci-lint dependencies (~1-2 minutes). Subsequent runs are fast (<10 seconds).

**Auto-fix version:**
```bash
podman exec test-odh-cli bash -c "cd /app && GOTOOLCHAIN=auto make lint/fix"
```

### 6. Run Tests (Validated ✓)

**Run all tests:**
```bash
podman exec test-odh-cli bash -c "cd /app && GOTOOLCHAIN=auto go test ./..."
```

**Expected output (truncated):**
```
?   	github.com/opendatahub-io/odh-cli/cmd	[no test files]
ok  	github.com/opendatahub-io/odh-cli/pkg/backup	0.017s
ok  	github.com/opendatahub-io/odh-cli/pkg/backup/dependencies/dspa	0.018s
ok  	github.com/opendatahub-io/odh-cli/pkg/lint	0.080s
ok  	github.com/opendatahub-io/odh-cli/pkg/lint/check	0.063s
...
ok  	github.com/opendatahub-io/odh-cli/tests/integration/lint	0.011s
```

**Exit code:** 0
**Status:** PASS (741+ tests across 38 packages)

**Via Makefile:**
```bash
podman exec test-odh-cli bash -c "cd /app && GOTOOLCHAIN=auto make test"
```

### 7. Run Single Package Tests

```bash
podman exec test-odh-cli bash -c "cd /app && GOTOOLCHAIN=auto go test ./pkg/backup/"
```

**Template:** `GOTOOLCHAIN=auto go test ./pkg/{package}/`

### 8. Run Single Test

```bash
podman exec test-odh-cli bash -c "cd /app && GOTOOLCHAIN=auto go test ./pkg/backup/ -run TestCommandDefaults"
```

**Template:** `GOTOOLCHAIN=auto go test ./pkg/{package}/ -run {TestName}`

**For pattern matching:**
```bash
podman exec test-odh-cli bash -c "cd /app && GOTOOLCHAIN=auto go test ./pkg/backup/ -run 'TestDryRun.*'"
```

### 9. Cleanup

```bash
podman rm -f test-odh-cli
```

**Always run cleanup**, even if validation fails partway through.

---

## Validation Results

All commands validated in `golang:1.22` container with `GOTOOLCHAIN=auto`:

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Install | `GOTOOLCHAIN=auto go mod download` | 0 | ✓ PASS | Downloaded Go 1.25.7 + all deps |
| Build | `GOTOOLCHAIN=auto make build` | 0 | ✓ PASS | Binary built (41MB), version works |
| Lint | `GOTOOLCHAIN=auto make lint` | 0 | ✓ PASS | 0 issues reported |
| Test | `GOTOOLCHAIN=auto go test ./...` | 0 | ✓ PASS | 741+ tests passed |

**Summary:** Install OK, build OK, lint OK (0 issues), tests OK (all passed).

---

## CI/CD

**System:** GitHub Actions
**Config:** `.github/workflows/ci.yml`

### Gating Checks (Required for Merge)

Both run on `pull_request` and `push` to `main`:

1. **Test Job**
   ```yaml
   - name: Run tests
     run: make test
   ```

2. **Lint Job**
   ```yaml
   - name: Run linter
     run: make lint
   ```

**Setup:** Uses `actions/setup-go@v6` with `go-version-file: go.mod`, which automatically reads Go version from go.mod.

### Non-Gating Jobs

- **dev-container**: Push dev image on push to main
- **release-container**: Push release image on GitHub release
- **release-binary**: Run GoReleaser on GitHub release

**All jobs require test job to pass first.**

---

## Conventions

### Test Files

- **Pattern:** `*_test.go`
- **Naming:** `Test*` functions, `t.Run()` for subtests
- **Framework:** Standard Go testing + Gomega for assertions
- **Imports:** Dot import for Gomega: `import . "github.com/onsi/gomega"`

**Example:**
```go
func TestSomething(t *testing.T) {
    g := NewWithT(t)
    ctx := t.Context()

    t.Run("should do X", func(t *testing.T) {
        result, err := doSomething(ctx)
        g.Expect(err).ToNot(HaveOccurred())
        g.Expect(result).To(HaveField("Status", "ready"))
    })
}
```

### Test Data

**Critical Rule:** All test data MUST be package-level constants, never inline.

```go
// ✓ CORRECT
const validManifest = `
apiVersion: v1
kind: ConfigMap
...
`

func TestParse(t *testing.T) {
    result := parse(validManifest)
    // ...
}

// ✗ WRONG - inline data
func TestParse(t *testing.T) {
    manifest := `apiVersion: v1...`  // PROHIBITED
}
```

### Struct Assertions

Must use `HaveField` or `MatchFields`:

```go
// ✓ CORRECT
g.Expect(result).To(HaveField("Metadata.Group", "components"))

g.Expect(result.Metadata).To(MatchFields(IgnoreExtras, Fields{
    "Group": Equal("components"),
    "Kind":  Equal("kserve"),
}))

// ✗ WRONG
g.Expect(result.Metadata.Group).To(Equal("components"))
```

### Import Organization

Via `gci` formatter (automated by `make fmt`):

1. Standard library
2. External dependencies
3. Blank imports
4. `k8s.io` packages
5. Blank imports
6. Project packages (`github.com/opendatahub-io/odh-cli`)
7. Blank imports
8. Dot imports (Gomega in tests)

---

## Gaps & Caveats

**No significant gaps identified.**

- ✓ Lint configuration present and clean
- ✓ Comprehensive test suite (741+ tests)
- ✓ CI properly configured
- ✓ All commands validated successfully
- ✓ Documentation extensive (docs/ directory)

**Minor notes:**

1. **Go version requirement:** Requires Go 1.25.7 (very new). Must use `GOTOOLCHAIN=auto` to auto-download.
2. **First lint run:** Downloads golangci-lint dependencies (~1-2 min). Subsequent runs are fast.
3. **Test coverage:** No coverage threshold configured, but test coverage appears comprehensive based on number of test files.

---

## Documentation

The project has extensive documentation in `docs/`:

- **[docs/development.md](docs/development.md)** — Main development guide
- **[docs/testing.md](docs/testing.md)** — Testing patterns and requirements
- **[docs/coding/conventions.md](docs/coding/conventions.md)** — Coding standards
- **[docs/quality.md](docs/quality.md)** — Quality verification workflow
- **[docs/setup.md](docs/setup.md)** — Build and test commands

**For agents:** The testing.md file contains strict requirements (test data as constants, MatchFields for structs, mock organization) that should be followed when generating tests.

---

## Quick Reference

**Common Commands (all require `GOTOOLCHAIN=auto`):**

```bash
# Install dependencies
GOTOOLCHAIN=auto go mod download

# Build
GOTOOLCHAIN=auto make build

# Lint
GOTOOLCHAIN=auto make lint

# Lint with auto-fix
GOTOOLCHAIN=auto make lint/fix

# Format code
GOTOOLCHAIN=auto make fmt

# Run all tests
GOTOOLCHAIN=auto go test ./...

# Run specific package
GOTOOLCHAIN=auto go test ./pkg/backup/

# Run specific test
GOTOOLCHAIN=auto go test ./pkg/backup/ -run TestCommandDefaults

# Run with verbose output
GOTOOLCHAIN=auto go test ./... -v

# Clean build artifacts
make clean
```

**Environment Variables:**

- `GOTOOLCHAIN=auto` — **Required** for all Go commands (downloads Go 1.25.7)
- `GOOS` / `GOARCH` — Optional for cross-compilation
- `VERSION` / `COMMIT` / `DATE` — Optional build metadata

---

## Agent Usage Notes

**For downstream agents validating patches:**

1. **Always use `GOTOOLCHAIN=auto`** before any go command
2. **First lint run takes ~1-2 minutes** (downloads dependencies), subsequent runs are fast
3. **Test by package, not by file:** Use `go test ./pkg/{package}/` not `go test ./pkg/{package}/{file}_test.go`
4. **Exit code 0 = success** for both lint and test
5. **Container base image:** golang:1.22 works perfectly with GOTOOLCHAIN=auto
6. **System deps needed:** make, git (usually present in golang image)

**Expected results after applying a patch:**

- Lint should still report `0 issues` (unless fixing lint violations)
- Tests should still pass (all packages show `ok`)
- Build should succeed and binary should work

**If lint reports issues after patch:**

- Exit code will be non-zero
- Output shows file:line:column and rule name
- Fix with `make lint/fix` or manually address violations

**If tests fail after patch:**

- Exit code will be non-zero
- Output shows which test failed and assertion details
- Look for `FAIL` lines in output
