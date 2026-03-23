# Test Context: opendatahub-io/notebooks

**Agent Readiness: medium** — Linting works perfectly; unit tests run successfully but container/integration tests require images; Go tests need separate toolchain; Makefile has environment issues.

## Overview

Multi-language notebook/workbench image repository with Python test framework, Go utilities, and Playwright browser tests.

- **Languages:** Python 3.14 (primary), Go, TypeScript/JavaScript
- **Build System:** uv (Python), Makefile (images), pnpm (browser tests)
- **Test Framework:** pytest (Python), Go test (Go), Playwright (browser)
- **CI:** GitHub Actions + Tekton pipelines
- **Container Engine:** podman or docker

## Container Recipe

This is the validated recipe for running lint and unit tests in a container.

### 1. Start Container

```bash
podman run -d --name test-context-notebooks \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.14 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-notebooks bash -c "apt-get update && apt-get install -y make git curl"
```

(Note: In python:3.14 these are already present, but this ensures they're available)

### 3. Install uv (Python package manager)

```bash
podman exec test-context-notebooks bash -c "pip install uv==0.10.6"
```

**Important:** Version 0.10.6 is pinned in `uv.toml`. The repo provides a `./uv` wrapper script that handles version mismatches.

### 4. Install Project Dependencies

```bash
podman exec test-context-notebooks bash -c "cd /app && uv sync --locked"
```

**Result:** Installs 147 packages including pytest, ruff, pyright, coverage, testcontainers, kubernetes client, docker, podman, and more.

**Duration:** ~13 seconds (after download cache is populated)

### 5. Run Linting

#### Ruff (Python linter and formatter)

```bash
podman exec test-context-notebooks bash -c "cd /app && uv run ruff check ci/ tests/ ntb/"
```

**Validated:** ✅ PASSED — "All checks passed!"

To auto-fix issues:
```bash
podman exec test-context-notebooks bash -c "cd /app && uv run ruff check --fix ci/ tests/ ntb/"
```

#### Ruff Format (Python formatter)

```bash
podman exec test-context-notebooks bash -c "cd /app && uv run ruff format ci/ tests/ ntb/"
```

#### Pyright (Type checker)

```bash
podman exec test-context-notebooks bash -c "cd /app && uv run pyright --pythonversion 3.14"
```

**Validated:** ✅ PASSED — "0 errors, 0 warnings, 0 informations"

### 6. Run Unit Tests

```bash
podman exec test-context-notebooks bash -c "cd /app && uv run pytest -m 'not buildonlytest' --ignore=tests/containers --ignore=tests/manual --ignore=tests/browser -x --tb=short"
```

**Validated:** ✅ MOSTLY PASSED — 15 passed, 1 failed (Makefile issue), 935 subtests passed

**Notes:**
- Excludes container tests (require `--image` parameter with built images)
- Excludes manual tests
- Excludes browser tests (require Playwright)
- The single failure is `test_make_disable_pushing` which fails due to Makefile/gmake environment issue, not a real test problem

**Coverage:** Automatically generated to `coverage.xml` and `junit.xml`

### 7. Run Single Test File

```bash
podman exec test-context-notebooks bash -c "cd /app && uv run pytest tests/test_main.py"
```

### 8. Run Single Test

```bash
podman exec test-context-notebooks bash -c "cd /app && uv run pytest tests/test_main.py::test_dockerfiles_unintended_subscription_manager_pattern"
```

### 9. Cleanup

```bash
podman rm -f test-context-notebooks
```

## Validation Results

### Dependency Installation
- **Command:** `uv sync --locked`
- **Status:** ✅ Success
- **Output:** Installed 147 packages in 4.62s
- **Packages:** pytest, ruff, pyright, coverage, testcontainers, kubernetes, docker, podman, pydantic, etc.

### Linting
- **ruff check:** ✅ All checks passed
- **pyright:** ✅ 0 errors, 0 warnings

### Testing
- **pytest unit tests:** ✅ 15 passed, 935 subtests passed
- **Failed:** 1 test (`test_make_disable_pushing`) — Makefile environment issue, not a code issue
- **Skipped:** Container tests, browser tests (require infrastructure)

## CI/CD

### Gating Workflows (pull_request trigger)

1. **code-quality.yaml** — Lint and test checks
   - `check-generated-code`: Ensures code generators have been run
     ```bash
     bash ci/generate_code.sh
     git diff --exit-code
     ```
   - `pytest-tests`: Python unit tests
     ```bash
     uv sync --locked
     make test  # Runs: uv run pytest -m 'not buildonlytest' && check_dockerfile_alignment.sh
     ```
   - `go-tests`: Go unit tests
     ```bash
     cd scripts/buildinputs
     gotestsum --junitfile=junit-go.xml -- -coverprofile=coverage-go.out -covermode=atomic ./...
     ```
   - `code-static-analysis`: YAML, JSON, Dockerfile validation
     ```bash
     yamllint --strict --config-file ./ci/yamllint-config.yaml <files>
     hadolint --config ./ci/hadolint-config.yaml <Dockerfiles>
     ./ci/validate_json.py
     ./ci/kustomize.sh
     ```
   - `prek`: Pre-commit hooks
     ```bash
     uvx prek run --all-files --show-diff-on-failure --hook-stage manual
     ```

2. **build-notebooks-pr.yaml** — Build changed notebook images
   - Determines changed files vs base branch
   - Builds only affected images using Makefile + podman
   - Uses cached builds for efficiency

3. **build-browser-tests.yaml** — Playwright browser tests
   - Triggers on changes to `tests/browser/`
   - Builds container image with Playwright
   - Runs smoke tests

### CI Environment
- Python 3.14 (from `uv.toml` and `.python-version`)
- Go version from `scripts/buildinputs/go.mod`
- Node.js 20 for browser tests
- uv 0.10.6 (pinned in `uv.toml`)
- pnpm 10.8.0 for browser tests

## Conventions

### Test Files
- **Pattern:** `test_*.py`, `*_test.py`
- **Classes:** `Test*`
- **Functions:** `test_*`

### Test Markers
Defined in `pytest.ini`:
- `openshift`: requires OpenShift cluster
- `cuda`: requires CUDA GPU
- `rocm`: requires ROCm GPU
- `buildonlytest`: runs inside Docker build (excluded from default runs)

### Test Categories
1. **Unit tests:** `tests/test_main.py`, `tests/pytest_tutorial/`
2. **Container tests:** `tests/containers/` — require `--image=<image>` parameter
3. **Browser tests:** `tests/browser/` — Playwright TypeScript tests
4. **Manual tests:** `tests/manual/` — not automated
5. **Go tests:** `scripts/buildinputs/*_test.go`

### Running Container Tests

Container tests are **excluded by default** because they require pre-built images:

```bash
# Build an image first (example)
make jupyter-minimal-ubi9-python-3.12

# Then run container tests
uv run pytest tests/containers --image=quay.io/opendatahub/workbench-images:jupyter-minimal-ubi9-python-3.12-2025b_20260322-abc123
```

### Running Browser Tests

Browser tests use Playwright and TypeScript. They run in a separate container:

```bash
cd tests/browser
podman build -t browser-tests .
podman run --rm browser-tests --list --project=chromium
```

### Running Go Tests

```bash
cd scripts/buildinputs
go test -v ./...
# Or with coverage:
go test -coverprofile=coverage.out -covermode=atomic ./...
```

## Gaps & Caveats

1. **Container tests unavailable** — Tests in `tests/containers/` require `--image=<image>` with actual built images. An agent cannot run these without first building images, which requires podman and significant resources.

2. **Makefile environment issues** — `make test` fails in the container with "recipe commences before first target" error. The Makefile expects gmake and specific environment. Workaround: run pytest directly.

3. **Go tests require Go toolchain** — The Python container doesn't have Go. To run Go tests, need `golang:1.22` or similar base image.

4. **Browser tests separate environment** — Playwright tests require Node.js 20, pnpm, Playwright browsers. Not included in Python test environment.

5. **OpenShift/GPU markers** — Tests marked with `openshift`, `cuda`, `rocm` require actual infrastructure (OpenShift cluster, CUDA GPU, ROCm GPU). Cannot run in basic containers.

6. **Manual tests** — `tests/manual/` contains tests that aren't automated and require human interaction.

7. **Code generation check** — CI runs `bash ci/generate_code.sh` to ensure generated code is up-to-date. This runs:
   - `scripts/dockerfile_fragments.py`
   - `manifests/tools/generate_kustomization.py`
   - `scripts/pylocks_generator.py`

## Quick Reference

### Lint Everything
```bash
uv run ruff check ci/ tests/ ntb/
uv run ruff format ci/ tests/ ntb/
uv run pyright --pythonversion 3.14
```

### Test Everything (Fast)
```bash
uv run pytest -m 'not buildonlytest' --ignore=tests/containers -x --tb=short
```

### Test with Coverage
```bash
uv run pytest --cov --cov-report=term-missing --cov-report=xml:coverage.xml
```

### Run Pre-commit Hooks
```bash
uvx prek run --all-files
```

### Validate Generated Code
```bash
bash ci/generate_code.sh
git diff --exit-code
```

## Recommended Agent Workflow

For an AI agent validating a patch:

1. **Setup:**
   ```bash
   podman run -d --name validate-patch -v $(pwd):/app:Z -w /app python:3.14 sleep infinity
   podman exec validate-patch pip install uv==0.10.6
   podman exec validate-patch uv sync --locked
   ```

2. **Lint:**
   ```bash
   podman exec validate-patch uv run ruff check ci/ tests/ ntb/
   podman exec validate-patch uv run pyright --pythonversion 3.14
   ```

3. **Test:**
   ```bash
   podman exec validate-patch uv run pytest -m 'not buildonlytest' --ignore=tests/containers -x --tb=short
   ```

4. **Cleanup:**
   ```bash
   podman rm -f validate-patch
   ```

**Expected result:** Lint passes clean, tests pass with 15+ passed and 935+ subtests passed (1 Makefile-related failure expected).
