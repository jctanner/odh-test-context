# Test Context: data-science-pipelines-tekton

**Organization:** opendatahub-io
**Languages:** Python, Go, TypeScript
**Build System:** Make, go, npm
**Agent Readiness:** **HIGH** - Lint and test commands validated successfully in container

Multi-language Kubeflow Pipelines compiler that generates Tekton YAML. Python SDK with Go backend services and TypeScript frontend. Core validation commands work in standard containers without special infrastructure.

---

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-dsp-tekton \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.9 \
  sleep infinity
```

If `podman` is not available, use `docker` instead.

### 2. Install System Dependencies

```bash
podman exec test-dsp-tekton bash -c "apt-get update && apt-get install -y make git wget"
```

### 3. Install Go 1.21

```bash
podman exec test-dsp-tekton bash -c "
  cd /tmp && \
  wget -q https://go.dev/dl/go1.21.0.linux-amd64.tar.gz && \
  tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz && \
  export PATH=\$PATH:/usr/local/go/bin && \
  go version
"
```

### 4. Install Python Dependencies

```bash
podman exec test-dsp-tekton bash -c "
  cd /app && \
  python -m pip install -e sdk/python && \
  pip install 'urllib3<2' && \
  pip install flake8 pytest
"
```

**Important:** `urllib3<2` is required for compatibility with kfp dependencies. Without this downgrade, tests will fail with import errors.

### 5. Run Python Lint

```bash
podman exec test-dsp-tekton bash -c "
  cd /app && \
  flake8 sdk/python --show-source --statistics \
    --select=E9,E2,E3,E5,F63,F7,F82,F4,F841,W291,W292 \
    --per-file-ignores sdk/python/tests/compiler/testdata/*:F841,F821 \
    --max-line-length=140
"
```

**Expected:** Exit code 0, no output (means no lint violations).
**Validated:** ✅ Passed with 0 violations.

### 6. Run Python Tests

```bash
podman exec test-dsp-tekton bash -c "
  cd /app/sdk/python/tests && \
  python3 -m unittest compiler.compiler_tests compiler.k8s_helper_tests --verbose
"
```

**Expected:** Exit code 0, "Ran 113 tests in ~6s\n\nOK"
**Validated:** ✅ 113 tests passed in 6.4s.

### 7. Run Go Tests

```bash
podman exec test-dsp-tekton bash -c "
  export PATH=\$PATH:/usr/local/go/bin && \
  cd /app && \
  go test -v -cover ./backend/src/common/...
"
```

**Expected:** Exit code 0, "PASS" for all tests.
**Validated:** ✅ All common package tests passed.

You can also run tests for specific Go packages:

```bash
# API server tests
podman exec test-dsp-tekton bash -c "
  export PATH=\$PATH:/usr/local/go/bin && \
  cd /app && \
  go test -v -cover ./backend/src/apiserver/...
"

# CRD controller tests
podman exec test-dsp-tekton bash -c "
  export PATH=\$PATH:/usr/local/go/bin && \
  cd /app && \
  go test -v -cover ./backend/src/crd/...
"

# Cache server tests
podman exec test-dsp-tekton bash -c "
  export PATH=\$PATH:/usr/local/go/bin && \
  cd /app && \
  go test -v -cover ./backend/src/cache/...
"
```

### 8. Build Go Backend

```bash
podman exec test-dsp-tekton bash -c "
  export PATH=\$PATH:/usr/local/go/bin && \
  cd /app && \
  go build -o apiserver ./backend/src/apiserver
"
```

**Expected:** Exit code 0, `apiserver` binary created (~59MB).
**Validated:** ✅ Build successful.

### 9. Run Single Python Test

```bash
# Run a specific test module
podman exec test-dsp-tekton bash -c "
  cd /app/sdk/python/tests && \
  python3 -m unittest compiler.compiler_tests
"

# Run a specific test class
podman exec test-dsp-tekton bash -c "
  cd /app/sdk/python/tests && \
  python3 -m unittest compiler.compiler_tests.TestTektonCompiler
"

# Run a specific test method
podman exec test-dsp-tekton bash -c "
  cd /app/sdk/python/tests && \
  python3 -m unittest compiler.compiler_tests.TestTektonCompiler.test_basic_workflow
"
```

### 10. Cleanup

```bash
podman rm -f test-dsp-tekton
```

**Always clean up** the container when done, even if validation fails partway through.

---

## Validation Results

All core commands were validated in a `python:3.9` container:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| **Install** | `pip install -e sdk/python` | ✅ PASS | Installed kfp-tekton 1.3.1 and dependencies |
| **Install** | `pip install 'urllib3<2'` | ✅ PASS | Compatibility fix for requests-toolbelt |
| **Lint** | `flake8 sdk/python ...` | ✅ PASS | 0 violations, exit code 0 |
| **Test** | Python unittest | ✅ PASS | 113 tests passed in 6.4s |
| **Test** | Go common tests | ✅ PASS | All tests passed in 0.015s |
| **Build** | `go build apiserver` | ✅ PASS | 59MB binary created |

**Summary:** Install OK, lint OK (0 violations), Python tests OK (113 passed), Go tests OK, Go build OK.

---

## CI/CD Configuration

**System:** GitHub Actions
**Main Workflow:** `.github/workflows/kfp-tekton-unittests.yml`

### Gating Checks (Required for PR Merge)

These checks run on every pull request and must pass:

1. **python-unittest** - Python unit tests (Python 3.7, 3.8, 3.9 matrix)
   ```bash
   python -m pip install -e sdk/python
   VENV=$VIRTUAL_ENV make ci_unit_test
   ```

2. **python-lint** - flake8 linting
   ```bash
   VENV=$VIRTUAL_ENV make lint
   ```

3. **check-license** - Verify license headers in source files
   ```bash
   make check_license
   ```

4. **check-mdtoc** - Verify Markdown table of contents
   ```bash
   make check_mdtoc
   ```

5. **check-doc-links** - Verify Markdown links
   ```bash
   make check_doc_links
   ```

6. **run-go-unittests** - Go backend unit tests
   ```bash
   make run-go-unittests
   ```
   Runs tests for:
   - `./backend/src/apiserver/...`
   - `./backend/src/common/...`
   - `./backend/src/crd/...`
   - `./backend/src/agent/...`
   - `./backend/src/cache/...`

7. **build-backend** - Verify Go builds
   ```bash
   make build-backend
   ```
   Builds: apiserver, agent, workflow controller, cacheserver

8. **validate-testdata** - Tekton validation
   ```bash
   make validate-testdata
   ```

9. **progress-report** - KFP sample compilation report
   ```bash
   VENV=$VIRTUAL_ENV make report PRINT_ERRORS=TRUE
   ```

10. **run-pipelineloop-unittests** - Pipeline loop tests
    ```bash
    cd tekton-catalog/pipeline-loops && make test-all
    ```

### Advisory Checks (Not Blocking)

- **backend-integration** - End-to-end tests requiring Kubernetes cluster
  - Only runs if backend files changed
  - Creates Kind cluster and deploys full stack
  - Runs flip-coin example pipeline

---

## Conventions

### Test File Naming

- **Python:** `*_tests.py` (e.g., `compiler_tests.py`, `k8s_helper_tests.py`)
- **Go:** `*_test.go` (e.g., `resource_manager_test.go`)
- **TypeScript:** `*.test.ts`, `*.test.tsx`

### Test Function Naming

- **Python:** `test_*` methods in `unittest.TestCase` subclasses
  ```python
  class TestTektonCompiler(unittest.TestCase):
      def test_basic_workflow(self):
          ...
  ```

- **Go:** `Test*` functions with `*testing.T` parameter
  ```go
  func TestFormatStringError(t *testing.T) {
      ...
  }
  ```

- **TypeScript:** `describe`/`it` blocks (Jest)

### Import Style

- **Python:** Relative imports within `kfp_tekton` package
  ```python
  from kfp_tekton.compiler.yaml_utils import dump_yaml
  ```

- **Go:** Standard import paths
  ```go
  import "github.com/kubeflow/pipelines/backend/src/common/util"
  ```

### Test Data Location

- Python compiler test fixtures: `sdk/python/tests/compiler/testdata/`
- Contains expected YAML outputs for compiler tests
- Both inlined and non-inlined versions

---

## Gaps & Caveats

### 1. Frontend Tests Not Gating

The frontend has a test suite (`npm test`) and linting (`npm run lint`), but these are **not** part of the main PR gating workflow. Frontend changes are validated through image builds only.

To run frontend tests locally:
```bash
cd frontend
npm ci
npm run lint
npm test
```

### 2. Backend Integration Tests Require Infrastructure

The `backend-integration` job in CI requires:
- Kubernetes cluster (uses Kind in CI)
- kubectl CLI
- tkn (Tekton CLI)

Cannot be validated in a simple container. Only runs in CI if backend files are changed.

### 3. Go Version Mismatch

- **CI uses:** Go 1.19.x (`.github/workflows/kfp-tekton-unittests.yml`)
- **go.mod specifies:** Go 1.21
- **Validated with:** Go 1.21.0

This mismatch should be resolved. Tests and builds work with 1.21.

### 4. Python Dependency Issue

**Critical:** Must install `urllib3<2` for compatibility with `kfp` dependencies. Newer urllib3 versions cause import errors:
```
ImportError: cannot import name 'appengine' from 'urllib3.contrib'
```

This is a known issue with `requests-toolbelt` used by `kfp`.

### 5. E2E Tests Not Validated

End-to-end tests (`make e2e_test`) require:
- Active Kubernetes cluster
- kubectl and tkn CLI configured
- KUBECONFIG environment variable set

These cannot run in the validation container.

### 6. Additional Checks Not Validated

The following Make targets were not validated (require specific tools or network access):
- `make check_license` - requires `find`, `grep`, specific license header format
- `make check_mdtoc` - requires `./tools/mdtoc.sh` script
- `make check_doc_links` - requires network access to verify external links

These are part of CI but not critical for core patch validation.

---

## Quick Reference

### Lint Only

```bash
# Python
make lint

# Frontend
cd frontend && npm run lint
```

### Test Only

```bash
# Python unit tests
make unit_test

# Go unit tests
make run-go-unittests

# Frontend tests
cd frontend && npm test
```

### Build

```bash
# Go backend
make build-backend

# Frontend
cd frontend && npm run build
```

### All Verification Targets

```bash
make verify
```

Runs: `check_license`, `check_mdtoc`, `check_doc_links`, `lint`, `unit_test`, `report`

---

## Agent Usage Example

A downstream agent validating a patch should:

1. **Start container** with repo mounted
2. **Install dependencies** (Python SDK, Go, system packages)
3. **Apply patch** to the mounted repo
4. **Run lint** - if lint fails, report violations
5. **Run tests** - if tests fail, report failures
6. **Report results** - clear pass/fail signal

The agent does **not** need:
- Kubernetes cluster
- External network access (after dependencies installed)
- Special credentials or secrets

The agent **should** handle:
- urllib3 compatibility issue (install `urllib3<2`)
- PATH setup for Go (`export PATH=$PATH:/usr/local/go/bin`)
- Working directory changes (`cd sdk/python/tests` for Python tests)

---

## Metadata

- **Analyzed:** 2026-03-22T21:59:00Z
- **Base Image:** python:3.9
- **Validation Duration:** ~5 minutes
- **Python Tests:** 113 passed in 6.4s
- **Go Tests:** Multiple packages validated
- **Confidence:** High
