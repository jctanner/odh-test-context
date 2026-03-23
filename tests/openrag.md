# OpenRAG Test Context - Validation Runbook

**Organization:** opendatahub-io
**Repository:** openrag
**Languages:** Python 3.13, TypeScript/JavaScript
**Build System:** uv (Python), npm (frontend), Makefile (orchestration)
**Agent Readiness:** **MEDIUM** - Unit tests and frontend lint work in containers, but integration tests require complex infrastructure (OpenSearch with OIDC, Langflow, docling-serve).

---

## Container Recipe

This section provides a complete, step-by-step recipe for validating patches in an isolated container.

### Python Backend Validation

#### 1. Start Python 3.13 Container

```bash
podman run -d --name test-context-openrag \
  -v /path/to/openrag:/app:Z \
  -w /app \
  python:3.13 \
  sleep infinity
```

(Replace `/path/to/openrag` with the actual repository path. Use `docker` instead of `podman` if podman is unavailable.)

#### 2. Install System Dependencies

```bash
podman exec test-context-openrag bash -c "apt-get update && apt-get install -y curl git make"
```

Note: These are already present in python:3.13 image.

#### 3. Install uv (Python Package Manager)

```bash
podman exec test-context-openrag bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
```

#### 4. Install Python Dependencies

```bash
podman exec test-context-openrag bash -c "cd /app && export PATH=\"/root/.local/bin:\$PATH\" && uv sync --group dev"
```

**Expected result:** ~124 packages installed in ~2-3 seconds. Exit code 0.

#### 5. Run Unit Tests

```bash
podman exec test-context-openrag bash -c "cd /app && export PATH=\"/root/.local/bin:\$PATH\" && uv run pytest tests/unit/ -v"
```

**Expected result:** 73 tests passed in ~1.3s. Exit code 0.

**Validation status:** ✅ PASSED - All unit tests passed successfully.

#### 6. Run All Backend Tests (Requires Infrastructure)

```bash
podman exec test-context-openrag bash -c "cd /app && export PATH=\"/root/.local/bin:\$PATH\" && uv run pytest tests/ -v"
```

**Expected result:** FAILS - Integration tests require OpenSearch, Langflow, and docling-serve.

**Validation status:** ⚠️ REQUIRES INFRASTRUCTURE - Cannot run without external services.

#### 7. Run Single Test File

```bash
podman exec test-context-openrag bash -c "cd /app && export PATH=\"/root/.local/bin:\$PATH\" && uv run pytest tests/unit/test_encryption.py -v"
```

#### 8. Run Single Test

```bash
podman exec test-context-openrag bash -c "cd /app && export PATH=\"/root/.local/bin:\$PATH\" && uv run pytest tests/unit/test_encryption.py::test_encryption_utility -v"
```

#### 9. Cleanup Python Container

```bash
podman rm -f test-context-openrag
```

---

### Frontend Validation

#### 1. Start Node 20 Container

```bash
podman run -d --name test-context-openrag-frontend \
  -v /path/to/openrag:/app:Z \
  -w /app/frontend \
  node:20 \
  sleep infinity
```

#### 2. Install Frontend Dependencies

```bash
podman exec test-context-openrag-frontend bash -c "cd /app/frontend && npm ci"
```

**Expected result:** ~711 packages installed in ~15s. Exit code 0.

#### 3. Run Frontend Lint

```bash
podman exec test-context-openrag-frontend bash -c "cd /app/frontend && npm run lint"
```

**Expected result:** Biome finds warnings (console.log usage, any types, missing deps), Next.js lint finds react-hooks warnings. Exit code 0.

**Validation status:** ✅ PASSED - Lint passed with warnings (warnings are acceptable in CI).

**Output snippet:**
```
app/api/mutations/useOnboardingMutation.ts:72:9 lint/suspicious/noConsole  FIXABLE
  ! Don't use console.
app/api/mutations/useSyncConnector.ts:49:16 lint/suspicious/noExplicitAny
  ! Unexpected any. Specify a different type.
...
Exit code: 0
```

#### 4. Run Frontend Lint Fix

```bash
podman exec test-context-openrag-frontend bash -c "cd /app/frontend && npm run lint:fix"
```

#### 5. Cleanup Frontend Container

```bash
podman rm -f test-context-openrag-frontend
```

---

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Python deps install | `uv sync --group dev` | 0 | ✅ PASS | 124 packages installed in 540ms |
| Python unit tests | `uv run pytest tests/unit/ -v` | 0 | ✅ PASS | 73 tests passed in 1.33s |
| Frontend deps install | `npm ci` | 0 | ✅ PASS | 711 packages installed in ~15s |
| Frontend lint | `npm run lint` | 0 | ✅ PASS | Warnings present but exit code 0 |
| Integration tests | `uv run pytest tests/integration/` | N/A | ⚠️ INFRA | Requires OpenSearch, Langflow, docling |

---

## CI/CD Configuration

### Gating Checks (Pull Request)

All PR checks run on `pull_request` events. The following checks **must pass** for PR merge:

#### 1. PR Title Check
- **Workflow:** `.github/workflows/pr-checks.yml`
- **Trigger:** All PRs
- **Command:** GitHub Action validates conventional commit format
- **Format:** `type(scope?): description`
- **Valid types:** feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
- **Status:** GATING

#### 2. Frontend Lint
- **Workflow:** `.github/workflows/lint-frontend.yml`
- **Trigger:** Changes to `frontend/**` or workflow file
- **Runner:** ubuntu-latest
- **Commands:**
  ```bash
  cd frontend
  npm ci
  npm run lint  # biome lint && next lint
  ```
- **Status:** GATING

#### 3. Integration Tests
- **Workflow:** `.github/workflows/test-integration.yml`
- **Trigger:** Changes to `src/**.py`, `tests/**.py`, `pyproject.toml`, `uv.lock`, `sdks/**`, `flows/**`, or workflow file
- **Runner:** self-hosted ARM64 (40GB RAM)
- **Commands:**
  ```bash
  uv sync --group dev
  make test-ci-local  # Builds all images locally, runs integration + SDK tests
  ```
- **Infrastructure Required:**
  - OpenSearch with OIDC configuration
  - Langflow
  - docling-serve
  - Backend + Frontend containers
  - JWT key generation
- **Status:** GATING

#### 4. E2E Tests (Playwright)
- **Workflow:** `.github/workflows/test-e2e.yml`
- **Trigger:** Changes to `src/**`, `frontend/**`, `tests/**`, `scripts/**`, `flows/**`, docker files, Makefile, or workflow file
- **Runner:** ubuntu-latest
- **Commands:**
  ```bash
  # Setup infrastructure
  ./scripts/setup-e2e.sh

  # Generate JWT keys
  uv run python -c "from src.main import generate_jwt_keys; generate_jwt_keys()"

  # Start docling
  make docling

  # Run Playwright tests
  cd frontend
  npx playwright test
  ```
- **Status:** GATING

---

## Conventions

### Test File Naming
- **Python:** `tests/**/*.py` (prefixed with `test_`)
- **TypeScript:** `frontend/**/*.test.ts`, `frontend/**/*.spec.ts`

### Test Function Naming
- **Python:** `def test_*()` functions
- **TypeScript:** `describe/it/test` blocks

### Import Style
- **Python:** Absolute imports from `src/` (e.g., `from config.settings import clients`)
- **TypeScript:** Relative imports and `@/` alias for app directory

### Commit Messages
- **Format:** Conventional Commits (enforced by CI)
- **Example:** `feat(backend): add JWT token refresh endpoint`
- **Required types:** feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

### Code Quality
- **Python linting:** ❌ NOT CONFIGURED - No ruff, flake8, pylint, mypy, or black
- **Frontend linting:** ✅ Biome + Next.js ESLint
- **Secret scanning:** ✅ detect-secrets pre-commit hook

---

## Gaps & Caveats

### Major Gaps

1. **No Python linting configured**
   - No ruff, flake8, pylint, mypy, or black in pyproject.toml
   - No Python linting in CI workflows
   - Only detect-secrets pre-commit hook for Python

2. **Integration tests require complex infrastructure**
   - OpenSearch with OIDC authenticator configuration
   - Langflow service
   - docling-serve (document processing service)
   - JWT RSA key pair generation
   - Environment variables for OpenSearch credentials

3. **Integration tests run on self-hosted ARM64 runners**
   - Not reproducible on standard x86_64 GitHub runners without modification
   - Tests use `make test-ci-local` which builds all images locally

4. **E2E tests require full stack**
   - All containers running (backend, frontend, OpenSearch, Langflow, dashboards)
   - Playwright browsers installed
   - docling-serve running

### Minor Gaps

1. **No coverage threshold enforced** - Tests can run with coverage but no minimum is set
2. **SDK tests require external stack** - SDK integration tests need OpenRAG running at localhost:3000
3. **Environment variables required** - Multiple env vars needed for tests (OPENSEARCH_PASSWORD, etc.)

---

## Quick Reference Commands

### Local Development

```bash
# Setup development environment
make setup

# Install dependencies
make install
# OR separately:
uv sync --group dev
cd frontend && npm ci

# Run backend locally (requires infrastructure)
make backend

# Run frontend locally
make frontend

# Start full stack with GPU
make dev

# Start full stack CPU-only
make dev-cpu
```

### Testing

```bash
# Run all backend tests (requires infrastructure)
make test

# Run unit tests only (no infrastructure needed)
make test-unit
# OR directly:
uv run pytest tests/unit/ -v

# Run integration tests (requires infrastructure)
make test-integration

# Run CI tests locally (builds everything)
make test-ci-local

# Run SDK tests (requires running stack)
make test-sdk

# Test JWT auth against OpenSearch
make test-os-jwt
```

### Linting

```bash
# Run frontend lint
make lint
# OR directly:
cd frontend && npm run lint

# Fix frontend lint issues
cd frontend && npm run lint:fix

# Note: No Python linting configured
```

### Container Management

```bash
# Start infrastructure only (for local dev)
make dev-local

# Stop all containers
make stop

# Clean up containers and volumes
make clean

# Complete factory reset
make factory-reset

# Show container status
make status

# Check service health
make health
```

### Single Test Execution

```bash
# Run single test file
uv run pytest tests/unit/test_encryption.py -v

# Run single test function
uv run pytest tests/unit/test_encryption.py::test_encryption_utility -v

# Run tests matching pattern
uv run pytest tests/unit/ -k "encryption" -v
```

---

## Environment Variables for Testing

### Required for Integration Tests

```bash
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=<your-password>  # Default: OpenRag#2025!
GOOGLE_OAUTH_CLIENT_ID=""  # Empty for no-auth mode
GOOGLE_OAUTH_CLIENT_SECRET=""  # Empty for no-auth mode
DISABLE_STARTUP_INGEST=true  # Disable background ingest during tests
LOG_LEVEL=DEBUG  # Enable debug logging
```

### Optional Variables

```bash
OPENAI_API_KEY=<key>  # For OpenAI-based tests
LANGFLOW_AUTO_LOGIN=True  # Auto-login for Langflow
LANGFLOW_NEW_USER_IS_ACTIVE=True  # Activate new users automatically
LANGFLOW_CHAT_FLOW_ID=<uuid>  # Chat flow ID
LANGFLOW_INGEST_FLOW_ID=<uuid>  # Ingest flow ID
```

---

## Notes for Downstream Agents

1. **Unit tests are reliable** - 73 unit tests pass consistently in a container with no external dependencies.

2. **Integration tests require orchestration** - Use `make test-ci-local` for full integration test setup. Do not attempt to run integration tests without infrastructure.

3. **No Python linting to enforce** - Unlike many Python projects, this repo has NO Python linting configured. Patches don't need to pass ruff/flake8/mypy checks.

4. **Frontend lint accepts warnings** - The frontend lint command exits 0 even with warnings. This is expected and matches CI behavior.

5. **Python 3.13 is required** - Specified in `pyproject.toml` and `.python-version`. Earlier versions won't work.

6. **uv is the package manager** - Use `uv` commands, not `pip`. Commands: `uv sync`, `uv run pytest`, etc.

7. **Self-hosted runners for integration tests** - CI integration tests run on ARM64 self-hosted runners with 40GB RAM. These may have different behavior than x86_64 machines.

8. **JWT keys must be generated** - Many tests require RSA key pair for JWT signing. Generated via `uv run python -c "from src.main import generate_jwt_keys; generate_jwt_keys()"`.

---

## Agent Readiness Rating Justification

**Rating: MEDIUM**

**Rationale:**
- ✅ **Unit tests work perfectly** - 73 tests pass in a simple container setup
- ✅ **Frontend lint works** - Can validate TypeScript/React code
- ✅ **Dependencies install cleanly** - uv sync and npm ci both work reliably
- ⚠️ **Integration tests require complex setup** - OpenSearch with OIDC, Langflow, docling-serve
- ⚠️ **No Python linting** - Cannot validate Python code style/quality
- ⚠️ **E2E tests need full stack** - Playwright tests require all services running

**What agents CAN do:**
- Apply patches to Python or TypeScript code
- Run unit tests to validate logic correctness
- Run frontend lint to catch TypeScript/React issues
- Validate conventional commit messages

**What agents CANNOT do easily:**
- Validate patches against Python linting standards (none configured)
- Run integration tests without orchestrating full infrastructure
- Run E2E tests without spinning up complete stack
- Test OpenSearch interactions without OIDC-configured OpenSearch
- Test Langflow flows without Langflow service

**Recommendation for agents:**
For quick patch validation, run unit tests and frontend lint. For comprehensive validation, use `make test-ci-local` but expect it to take 5-10 minutes and require significant compute resources.
