# Test Context: llama-stack-distribution

**Agent Readiness: MEDIUM** — Lint commands validated successfully. Tests require extensive infrastructure (vLLM, PostgreSQL, container build) that cannot be automated without cloud resources.

## Overview

**Repository:** opendatahub-io/llama-stack-distribution
**Languages:** Python, Shell
**Build System:** uv (Python package manager), Docker/Podman container builds
**Primary Function:** Distribution packaging and containerization of Meta's Llama Stack for Open Data Hub

This repository auto-generates a Containerfile from a template using `distribution/build.py`, which installs llama-stack from source and generates dependency lists. The Containerfile builds a multi-arch container image (amd64/arm64) with llama-stack and various AI provider integrations (vLLM, Vertex AI, OpenAI, WatsonX, etc.).

Testing is integration-focused: smoke tests verify the container works with vLLM and PostgreSQL, and pytest-based integration tests run against the upstream llama-stack test suite.

## Container Recipe

This recipe allows an agent to validate lint checks. **Tests cannot be validated** without building the container, starting vLLM and PostgreSQL services, and optionally configuring cloud providers.

### 1. Start Container

```bash
podman run -d \
  --name test-context-llama-stack-distribution \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-llama-stack-distribution bash -c \
  "apt-get update && apt-get install -y git shellcheck curl ca-certificates"
```

### 3. Install Python Dependencies

```bash
podman exec test-context-llama-stack-distribution bash -c \
  "pip install --no-cache-dir uv pre-commit"
```

### 4. Install Pre-commit Hooks

```bash
podman exec test-context-llama-stack-distribution bash -c \
  "cd /app && pre-commit install-hooks"
```

This step takes 2-3 minutes. It installs all pre-commit hook environments (ruff, actionlint, shellcheck-precommit, etc.).

### 5. Run Linters

#### Ruff (Python linter)
```bash
podman exec test-context-llama-stack-distribution bash -c \
  "cd /app && pre-commit run --all-files ruff"
```
**Validated:** ✅ Passed
**Notes:** No Python lint violations found

#### Ruff Format (Python formatter)
```bash
podman exec test-context-llama-stack-distribution bash -c \
  "cd /app && pre-commit run --all-files ruff-format"
```
**Validated:** ✅ Passed
**Notes:** Code is properly formatted

#### Shellcheck (Shell script linter)
```bash
podman exec test-context-llama-stack-distribution bash -c \
  "cd /app && shellcheck tests/*.sh distribution/*.sh"
```
**Validated:** ✅ Passed
**Notes:** Shell scripts pass validation. Note: shellcheck pre-commit hook requires Docker (fails in container), so run shellcheck directly.

#### YAML Validation
```bash
podman exec test-context-llama-stack-distribution bash -c \
  "cd /app && pre-commit run --all-files check-yaml"
```
**Validated:** ✅ Passed
**Notes:** All YAML files are valid

#### All Pre-commit Checks (Skipping Docker-dependent hooks)
```bash
podman exec test-context-llama-stack-distribution bash -c \
  "cd /app && SKIP=pkg-gen,doc-gen,shellcheck,actionlint,no-commit-to-branch pre-commit run --all-files"
```
**Validated:** ✅ Passed
**Notes:** Skips: pkg-gen (requires llama-stack), doc-gen, shellcheck/actionlint (require Docker), no-commit-to-branch (fails on main branch)

### 6. Build Validation (Limited)

The build script `distribution/build.py` generates the Containerfile from a template:

```bash
podman exec test-context-llama-stack-distribution bash -c \
  "cd /app && python3 distribution/build.py"
```
**Validated:** ❌ Failed
**Exit Code:** 2
**Error:** `error: No virtual environment found; run 'uv venv' to create an environment`
**Notes:** Requires llama-stack installation from source (git+https://github.com/opendatahub-io/llama-stack.git@v0.6.0.1+rhai0). Cannot validate without external dependencies and network access.

### 7. Test Execution (Requires Infrastructure)

#### Smoke Tests
```bash
./tests/smoke.sh
```
**Validated:** ❌ Cannot validate
**Requirements:**
- Pre-built container image: `$IMAGE_NAME:$GITHUB_SHA`
- vLLM server running at `http://localhost:8000/v1` with model `Qwen/Qwen3-0.6B`
- PostgreSQL running at `localhost:5432` (db: llamastack, user: llamastack, pass: llamastack)
- Docker/Podman to run containers
- Environment variables: `IMAGE_NAME`, `GITHUB_SHA`, `VLLM_INFERENCE_MODEL`, `EMBEDDING_MODEL`, `VLLM_URL`, `POSTGRES_*`

**What it tests:**
- Starts llama-stack container
- Verifies model list endpoint returns expected models
- Runs inference test (chat completion with "What color is grass?")
- Verifies PostgreSQL tables are created and populated

#### Integration Tests
```bash
./tests/run_integration_tests.sh
```
**Validated:** ❌ Cannot validate
**Requirements:**
- All smoke test requirements
- Clones upstream llama-stack repository to `/tmp/llama-stack-integration-tests`
- Installs llama-stack-client and ollama via uv
- Runs pytest from upstream repo: `uv run pytest -s -v tests/integration/inference/`
- Optional: Vertex AI (requires `VERTEX_AI_PROJECT`) and OpenAI (requires `OPENAI_API_KEY`)

**What it tests:**
- Full integration tests from upstream llama-stack
- Tests vLLM inference, Vertex AI (if configured), OpenAI (if configured)
- Skips tests requiring features not yet supported

### 8. Cleanup

```bash
podman rm -f test-context-llama-stack-distribution
```

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install | `pip install uv pre-commit` | ✅ Passed | Dependencies installed |
| Lint | `pre-commit run ruff` | ✅ Passed | No violations |
| Lint | `pre-commit run ruff-format` | ✅ Passed | Properly formatted |
| Lint | `shellcheck tests/*.sh` | ✅ Passed | Shell scripts valid |
| Lint | `pre-commit run check-yaml` | ✅ Passed | YAML files valid |
| Build | `python3 distribution/build.py` | ❌ Failed | Requires llama-stack installation |
| Test | `./tests/smoke.sh` | ❌ Cannot run | Requires vLLM, PostgreSQL, container image |
| Test | `./tests/run_integration_tests.sh` | ❌ Cannot run | Requires full infrastructure |

## CI/CD

### GitHub Actions

**Workflow:** `.github/workflows/pre-commit.yml`
**Trigger:** `pull_request`, `push` to `main`
**Gating:** Yes
**Commands:**
```bash
pre-commit run --all-files
git diff --exit-code  # Verify no uncommitted changes
```
**Notes:** Enforces all pre-commit hooks including auto-generation of Containerfile. Skips `no-commit-to-branch` via `SKIP` env var.

**Workflow:** `.github/workflows/redhat-distro-container.yml`
**Trigger:** `pull_request`, `push` to `main`, `schedule` (nightly), `workflow_dispatch`
**Gating:** Yes
**Commands:**
```bash
# Install uv
pip install uv==0.7.6

# Generate Containerfile (for workflow_dispatch/schedule only)
python3 distribution/build.py

# Build AMD64 (for testing)
docker build -f distribution/Containerfile --platform linux/amd64 .

# Build ARM64 (verification only)
docker build -f distribution/Containerfile --platform linux/arm64 .

# Setup vLLM and PostgreSQL
# (Custom GitHub Actions in .github/actions/)

# Smoke test
./tests/smoke.sh

# Integration tests
./tests/run_integration_tests.sh

# Publish multi-arch (on push to main, if distribution/ changed)
docker buildx build --platform linux/amd64,linux/arm64 --push \
  -t quay.io/opendatahub/llama-stack:$GITHUB_SHA \
  -f distribution/Containerfile .
```
**Notes:** Builds container, runs vLLM with `Qwen/Qwen3-0.6B`, starts PostgreSQL, runs smoke and integration tests. Tests use Vertex AI and OpenAI if secrets are available (skipped for forks/Dependabot). Publishes to `quay.io/opendatahub/llama-stack` with multi-arch support.

**Workflow:** `.github/workflows/semantic-pr.yml`
**Trigger:** `pull_request_target`
**Gating:** Yes
**Command:** Uses `amannn/action-semantic-pull-request` action
**Notes:** Enforces semantic PR titles (feat:, fix:, chore:, etc.)

### Tekton Pipelines

**Pipeline:** `.tekton/odh-llama-stack-core-pull-request.yaml`
**Trigger:** PRs to `main` with changes to `distribution/**` or `.tekton/**`
**Gating:** Yes (OpenShift/Konflux builds)
**Command:** Multi-arch container build using `odh-konflux-central` pipeline
**Notes:** Builds PR images tagged as `quay.io/opendatahub/llama-stack:odh-pr-{revision}`

## Conventions

### File Patterns
- **Python files:** `distribution/build.py`, `scripts/gen_distro_docs.py`
- **Shell scripts:** `tests/*.sh`
- **Config files:** `.pre-commit-config.yaml`, `distribution/config.yaml`
- **Templates:** `distribution/Containerfile.in` (auto-generates `distribution/Containerfile`)

### Naming Conventions
- **Tests:** Bash scripts in `tests/` directory (`smoke.sh`, `run_integration_tests.sh`, `test_utils.sh`)
- **Build artifacts:** `distribution/Containerfile` (auto-generated, never edit manually)

### Code Review
- **CODEOWNERS:** `.github/CODEOWNERS` defines code owners
- **PR template:** `.github/PULL_REQUEST_TEMPLATE.md`
- **Semantic PR titles:** Required by `semantic-pr.yml` workflow

## Gaps & Caveats

### What's Missing
1. **No Python unit tests** — Only integration tests that require full infrastructure
2. **No coverage reporting** — No pytest-cov or coverage threshold
3. **No standalone test execution** — Cannot test without building container first
4. **Limited validation in CI for forks** — Vertex AI and OpenAI tests skip for forks/Dependabot (secrets not available)

### Infrastructure Requirements
1. **vLLM server** — Must be running with a model (default: `Qwen/Qwen3-0.6B`) at `http://localhost:8000/v1`
2. **PostgreSQL** — Must be running at `localhost:5432` with database `llamastack`
3. **Container image** — Must build `distribution/Containerfile` before running tests
4. **Cloud services (optional):**
   - Vertex AI: Requires `VERTEX_AI_PROJECT`, `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - OpenAI: Requires `OPENAI_API_KEY`

### Known Issues
1. **Pre-commit shellcheck/actionlint hooks require Docker** — Fail in container environments
2. **Build script requires llama-stack installation** — Cannot validate `distribution/build.py` without installing llama-stack from source
3. **Integration tests clone upstream repo** — Tests are not self-contained; require network access to clone `https://github.com/opendatahub-io/llama-stack.git`
4. **Tests are slow** — Integration tests can take 5-10 minutes (model loading, inference)

### Workarounds
- **For lint validation:** Skip shellcheck/actionlint pre-commit hooks, run shellcheck directly
- **For build validation:** Accept that build script cannot be validated in isolation
- **For test validation:** Run smoke tests with minimal infrastructure (vLLM + PostgreSQL), skip cloud tests

## Patch Validation Recipe

An agent validating a patch to this repository should:

1. **Always validate:** Lint checks (ruff, ruff-format, shellcheck, YAML)
2. **Optionally validate (if infrastructure available):**
   - Build Containerfile: `pre-commit run pkg-gen` (requires llama-stack installation)
   - Build container: `docker build -f distribution/Containerfile .`
   - Run smoke tests: `./tests/smoke.sh` (requires vLLM + PostgreSQL)
3. **Cannot validate without cloud access:**
   - Integration tests with Vertex AI or OpenAI
   - Full multi-arch builds

### Minimal Validation (No External Dependencies)

```bash
# Start container
podman run -d --name test -v $(pwd):/app:Z -w /app python:3.12 sleep infinity

# Install deps
podman exec test bash -c "apt-get update && apt-get install -y git shellcheck"
podman exec test bash -c "pip install --no-cache-dir uv pre-commit"
podman exec test bash -c "cd /app && pre-commit install-hooks"

# Run linters
podman exec test bash -c "cd /app && pre-commit run --all-files ruff"
podman exec test bash -c "cd /app && pre-commit run --all-files ruff-format"
podman exec test bash -c "cd /app && shellcheck tests/*.sh"
podman exec test bash -c "cd /app && pre-commit run --all-files check-yaml"

# Cleanup
podman rm -f test
```

This validates Python code quality and shell script syntax without requiring external services.
