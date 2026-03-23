# KServe Test Context

**Repository:** opendatahub-io/kserve
**Languages:** Go 1.25, Python 3.10-3.12
**Build System:** Make, Go toolchain, uv (Python)
**Agent Readiness:** medium - Lint and test commands validated in containers; some integration tests require Kubernetes infrastructure

---

## Container Recipe

This section provides a **complete, copy-paste recipe** for validating patches in a container. An agent can follow these steps verbatim to spin up an environment, run linting, and run tests.

### Go Validation Container

#### 1. Start the Container

```bash
podman run -d --name test-context-kserve \
  -v /path/to/kserve:/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

#### 2. Install System Dependencies

```bash
podman exec test-context-kserve bash -c "apt-get update && apt-get install -y make git wget perl jq python3 python3-pip curl -qq"
```

#### 3. Install Go Dependencies

```bash
podman exec test-context-kserve bash -c "cd /app && go mod download && cd qpext && go mod download"
```

#### 4. Install Build Tools

```bash
podman exec test-context-kserve bash -c "cd /app && make golangci-lint && make setup-envtest"
```

This installs:
- `golangci-lint` v2.9.0 → `/app/bin/golangci-lint`
- `setup-envtest` → `/app/bin/setup-envtest`
- envtest Kubernetes binaries → `/app/bin/k8s/1.34.1-linux-amd64/`

#### 5. Run Go Linting

```bash
podman exec test-context-kserve bash -c "cd /app && bin/golangci-lint run"
```

**Expected Result:** Exit code 1 with output showing lint violations:
```
cmd/llmisvc/main.go:33:2: "k8s.io/apimachinery/pkg/fields" imported and not used
cmd/llmisvc/main.go:182:15: undefined: llmisvc.ServiceCASigningSecretNamespace (typecheck)
```

This is a **legitimate lint failure** (unused import, undefined symbol). The linter command works correctly.

To auto-fix:
```bash
podman exec test-context-kserve bash -c "cd /app && bin/golangci-lint run --fix"
```

#### 6. Run Go Tests

```bash
podman exec test-context-kserve bash -c "cd /app && export KUBEBUILDER_ASSETS=\$(bin/setup-envtest use 1.34 -p path) && go test ./pkg/apis/serving/v1alpha1/... -v"
```

**Expected Result:** Exit code 0, tests pass:
```
=== RUN   TestInferenceGraph_ValidateCreate
--- PASS: TestInferenceGraph_ValidateCreate (0.00s)
=== RUN   TestLLMInferenceServiceConversion_PreservesCriticality
--- PASS: TestLLMInferenceServiceConversion_PreservesCriticality (0.00s)
```

Full test suite (takes ~5+ minutes):
```bash
podman exec test-context-kserve bash -c "cd /app && export KUBEBUILDER_ASSETS=\$(bin/setup-envtest use 1.34 -p path) && go test --timeout 30m \$(go list ./pkg/...) ./cmd/... -v"
```

**Note:** `make test` requires `kubectl` for CRD manifest generation. To run without `kubectl`:
- Use the direct `go test` command above
- Or install kubectl: `curl -LO "https://dl.k8s.io/release/v1.34.0/bin/linux/amd64/kubectl" && chmod +x kubectl && mv kubectl /usr/local/bin/`

#### 7. Run a Single Test

```bash
podman exec test-context-kserve bash -c "cd /app && export KUBEBUILDER_ASSETS=\$(bin/setup-envtest use 1.34 -p path) && go test -run TestInferenceGraph_ValidateCreate ./pkg/apis/serving/v1alpha1/... -v"
```

#### 8. Cleanup

```bash
podman rm -f test-context-kserve
```

---

### Python Validation Container

#### 1. Start the Container

```bash
podman run -d --name test-context-kserve-python \
  -v /path/to/kserve:/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

#### 2. Install System Dependencies

```bash
podman exec test-context-kserve-python bash -c "apt-get update && apt-get install -y make git -qq"
```

#### 3. Install uv Package Manager

```bash
podman exec test-context-kserve-python bash -c "pip install uv"
```

#### 4. Install Python Dependencies (kserve SDK)

```bash
podman exec test-context-kserve-python bash -c "cd /app/python/kserve && uv sync --group test && uv pip install ../storage --no-cache"
```

This creates a virtual environment at `/app/python/kserve/.venv` with pytest, pytest-cov, and all test dependencies.

#### 5. Run Python Linting

```bash
podman exec test-context-kserve-python bash -c "cd /app && pip install ruff && ruff check --config ruff.toml python/kserve/kserve"
```

**Expected Result:** Exit code 0:
```
All checks passed!
```

To auto-fix:
```bash
podman exec test-context-kserve-python bash -c "cd /app && ruff check --fix --config ruff.toml python/kserve/kserve"
```

#### 6. Run Python Tests

Test a single module:
```bash
podman exec test-context-kserve-python bash -c "cd /app/python && kserve/.venv/bin/python -m pytest kserve/test/test_creds_utils.py -v"
```

**Expected Result:** Exit code 0, 9 tests pass:
```
kserve/test/test_creds_utils.py::test_check_sa_exists PASSED             [ 11%]
kserve/test/test_creds_utils.py::test_create_service_account PASSED      [ 22%]
...
============================== 9 passed in 0.07s ===============================
```

Full kserve test suite:
```bash
podman exec test-context-kserve-python bash -c "cd /app/python && kserve/.venv/bin/python -m pytest kserve/test/ -v"
```

Test with coverage:
```bash
podman exec test-context-kserve-python bash -c "cd /app/python && kserve/.venv/bin/python -m pytest --cov=kserve kserve/test/"
```

#### 7. Run a Single Test

```bash
podman exec test-context-kserve-python bash -c "cd /app/python && kserve/.venv/bin/python -m pytest kserve/test/test_creds_utils.py::test_create_secret -v"
```

#### 8. Cleanup

```bash
podman rm -f test-context-kserve-python
```

---

## Validation Results

### Go Validation

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `go mod download` | 0 | ✅ Pass | Dependencies installed successfully |
| Install tools | `make golangci-lint` | 0 | ✅ Pass | golangci-lint v2.9.0 installed (68MB) |
| Lint | `bin/golangci-lint run` | 1 | ⚠️ Violations found | Found unused import and typecheck error in cmd/llmisvc/main.go |
| Setup tests | `make setup-envtest` | 0 | ✅ Pass | envtest Kubernetes 1.34 binaries installed |
| Run tests | `go test ./pkg/apis/serving/v1alpha1/...` | 0 | ✅ Pass | Tests pass for v1alpha1 APIs |

**Summary:** Lint found violations (expected), tests pass successfully.

### Python Validation

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Install uv | `pip install uv` | 0 | ✅ Pass | uv package manager installed |
| Install deps | `uv sync --group test` | 0 | ✅ Pass | pytest and dependencies installed |
| Lint | `ruff check` | 0 | ✅ Pass | All checks passed! |
| Run tests | `pytest kserve/test/test_creds_utils.py` | 0 | ✅ Pass | 9 tests passed in 0.07s |

**Summary:** All Python linting and tests pass cleanly.

---

## CI/CD

### Gating Checks (Required for Merge)

These checks run on every pull request and must pass before merging:

#### 1. Precommit Check (`.github/workflows/precommit-check.yml`)

```bash
make check
```

This validates:
- All code is formatted (`go fmt`, `black`)
- All code is linted (`golangci-lint`, `ruff`)
- Generated code is up to date (CRDs, clients, manifests)
- No uncommitted changes after code generation

**Runs on:** Every PR (except markdown-only changes)
**Trigger:** `pull_request`
**Required:** Yes

#### 2. Go Test (`.github/workflows/go.yml`)

```bash
make test
./coverage.sh
```

Runs Go unit tests with coverage reporting. Tests use `envtest` to mock Kubernetes APIs.

**Runs on:** PRs affecting Go code
**Trigger:** `pull_request` (paths: `**` except `python/**`, `docs/**`, `**.md`)
**Required:** Yes
**Coverage:** Tracked and reported in PR comments

#### 3. Python Test (`.github/workflows/python-test.yml`)

Runs pytest for each Python package:
- `kserve` (SDK)
- `storage`
- `sklearnserver`
- `xgbserver`
- `lgbserver`
- `pmmlserver`
- `paddleserver`
- `huggingfaceserver`

**Matrix:** Python 3.10, 3.11, 3.12
**Runs on:** PRs affecting Python code
**Trigger:** `pull_request` (paths: `python/**`, `.github/workflows/python-test.yml`)
**Required:** Yes

### Advisory Checks (Non-blocking)

#### E2E Tests

Full integration tests on minikube with KServe controllers, Knative, Istio, etc.

**Runs on:** Push to master, manual trigger
**Required:** No
**Notes:** Requires Kubernetes cluster infrastructure

---

## Conventions

### Go

- **Test files:** `*_test.go`
- **Test naming:** `TestFunctionName` (standard Go) or Ginkgo describe/it blocks
- **Imports:** Use `goimports` with local prefix `github.com/kserve/kserve`
- **Import aliases:**
  - `corev1` → `k8s.io/api/core/v1`
  - `metav1` → `k8s.io/apimachinery/pkg/apis/meta/v1`
  - `ctrl` → `sigs.k8s.io/controller-runtime`
- **Code generation:** Controllers, CRDs, and clients are generated from API types
- **Patterns:** Follows controller-runtime and kubebuilder patterns

### Python

- **Test files:** `test_*.py` in `{package}/test/` directories
- **Test naming:** `test_function_name` (pytest convention)
- **Line length:** 120 characters
- **Imports:** Absolute imports preferred
- **Package structure:** Each server is a separate package with its own `pyproject.toml` and `uv.lock`
- **Virtual environments:** Each package has its own `.venv` directory

---

## Gaps & Caveats

### Known Limitations

1. **kubectl Required for Full CI**
   - `make check` runs `make manifests` which requires `kubectl` to fetch Gateway API CRDs
   - Workaround: Install kubectl in container or run tests directly with `go test`

2. **Python Ray/LLM Tests**
   - Tests for ray and vLLM features require large dependencies (vLLM, ray[serve])
   - `huggingfaceserver` tests need GPU or specific CPU features (IPEX for vLLM on CPU)
   - CI uses `/mnt` mount for vLLM to avoid disk space issues

3. **E2E Tests Need Cluster**
   - Full E2E tests require minikube/kind with Knative, Istio, cert-manager
   - Cannot run in simple containers
   - Documented in `.github/workflows/e2e-test.yml`

4. **Generated Code Must Be Committed**
   - CRDs, OpenAPI schemas, Helm charts, client code are all generated
   - `make precommit` regenerates everything
   - CI fails if generated code differs from committed code

5. **Multiple Go Modules**
   - Main module: `./`
   - Submodule: `./qpext/`
   - Both need `go mod download`

6. **Python Multi-Package Complexity**
   - 14+ Python packages with interdependencies
   - `kserve` SDK is used by all servers
   - `storage` package is a separate dependency

### What Works in Containers

✅ **Fully Validated:**
- Go linting with golangci-lint
- Go unit tests for APIs and controllers (using envtest)
- Python linting with ruff
- Python unit tests for kserve SDK and storage

⚠️ **Partially Validated:**
- `make test` (requires kubectl for manifest generation)
- `make check` (requires all code generation tools)

❌ **Requires Infrastructure:**
- E2E tests (need Kubernetes cluster)
- Integration tests with actual InferenceServices
- Tests requiring cloud storage (S3, GCS, Azure Blob)

---

## Quick Reference

### Essential Commands

**Check everything (full precommit):**
```bash
make check
```

**Run Go tests:**
```bash
export KUBEBUILDER_ASSETS=$(bin/setup-envtest use 1.34 -p path)
go test --timeout 30m $(go list ./pkg/...) ./cmd/...
```

**Run Python tests (kserve SDK):**
```bash
cd python/kserve
source .venv/bin/activate
pytest --cov=kserve ./
```

**Lint Go code:**
```bash
bin/golangci-lint run --fix
```

**Lint Python code:**
```bash
bin/.venv/bin/ruff check --fix --config ruff.toml
```

**Format code:**
```bash
make fmt      # Go
make py-fmt   # Python
```

### File Locations

- **Go source:** `pkg/`, `cmd/`
- **Go tests:** `pkg/*_test.go`, `cmd/*_test.go`
- **Python source:** `python/{package}/{package}/`
- **Python tests:** `python/{package}/test/`
- **Go lint config:** `.golangci.yml`
- **Python lint config:** `ruff.toml`
- **CRDs:** `config/crd/`
- **Test fixtures:** `test/crds/`

---

## Agent Readiness Rating: MEDIUM

**Justification:** Lint and test commands work reliably in containers for both Go and Python. An agent can:
- ✅ Clone the repo
- ✅ Apply patches
- ✅ Run linters to check code quality
- ✅ Run unit tests to verify behavior
- ✅ Get clear pass/fail signals

**Limitations:**
- ⚠️ Full CI check (`make check`) requires kubectl and all code generation tools
- ⚠️ Some Python tests (ray, vLLM) have heavy dependencies
- ⚠️ Integration/E2E tests require Kubernetes infrastructure

**Recommendation:** For basic patch validation (linting + unit tests), this repo is **highly usable** by agents. For full CI validation, some infrastructure setup is needed.
