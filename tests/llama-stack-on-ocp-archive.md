# Test Context for llama-stack-on-ocp-archive

## Overview

**Repository:** opendatahub-io/llama-stack-on-ocp-archive
**Language:** Python
**Build system:** Makefile + podman
**Agent readiness:** **none** - This archived repository has no tests, no linting, and no CI/CD configuration. There is no automated validation infrastructure to run against patches.

This is a demonstration/prototype project for deploying Llama Stack with MCP (Model Context Protocol) servers on OpenShift. It consists of a Streamlit web UI and several MCP server implementations, all containerized for OpenShift deployment.

## Container Recipe

Since there are no tests or linting configured, the only validation possible is confirming that:
1. Dependencies install successfully
2. Python code has valid syntax
3. Python modules can be imported (though they may fail at runtime without external services)

### Step 1: Start the container

```bash
podman run -d --name test-context-llama-stack-on-ocp \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

**Base image:** `python:3.11`
**Mount point:** Current directory → `/app`

### Step 2: Verify Python version

```bash
podman exec test-context-llama-stack-on-ocp bash -c "python --version"
```

**Expected output:** `Python 3.11.x`

### Step 3: Install dependencies

```bash
podman exec test-context-llama-stack-on-ocp bash -c "\
  cd /app && \
  pip install --no-cache-dir -r mcp-servers/llamastack/requirements.txt && \
  pip install --no-cache-dir streamlit llama-stack-client python-dotenv && \
  pip install --no-cache-dir fire && \
  pip install --no-cache-dir mcp"
```

**Dependencies installed:**
- From `mcp-servers/llamastack/requirements.txt`: anyio, click, httpx, pydantic, pyyaml, mcp, uvicorn, starlette
- From Streamlit app: streamlit, llama-stack-client, python-dotenv
- Missing from requirements files: fire (required by llama-stack-client)
- Explicit install needed: mcp (may not install correctly from requirements.txt alone)

**Exit code:** 0 (success)
**Notes:** Installation succeeds. The 'fire' package is a runtime dependency not documented in requirements files.

### Step 4: Validate Python syntax

```bash
podman exec test-context-llama-stack-on-ocp bash -c "\
  cd /app && \
  python -m py_compile app/src/*.py mcp-servers/llamastack/*.py"
```

**Exit code:** 0 (success)
**Notes:** All Python files compile successfully. No syntax errors.

### Step 5: Test module imports

```bash
# Test client_tools
podman exec test-context-llama-stack-on-ocp bash -c "\
  cd /app && \
  python -c 'import sys; sys.path.insert(0, \"app/src\"); import client_tools; print(\"✓ client_tools\")'"

# Test mcp_server
podman exec test-context-llama-stack-on-ocp bash -c "\
  cd /app/mcp-servers/llamastack && \
  python -c 'import mcp_server; print(\"✓ mcp_server\")'"
```

**Exit code:** 0 (success)
**Output:**
```
✓ client_tools
✓ mcp_server
```

**Notes:**
- Core modules import successfully
- `streamlit_app.py` attempts to connect to external Llama Stack service on import, which will fail without proper `.env` configuration and running services - this is expected behavior

### Step 6: Run linting

**N/A** - No linting configured

### Step 7: Run tests

**N/A** - No tests exist

### Step 8: Cleanup

```bash
podman rm -f test-context-llama-stack-on-ocp
```

## Validation Results

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install | `pip install -r requirements.txt && pip install streamlit llama-stack-client python-dotenv fire mcp` | ✅ Pass | All dependencies install successfully |
| Syntax Check | `python -m py_compile app/src/*.py mcp-servers/llamastack/*.py` | ✅ Pass | All Python files have valid syntax |
| Import Test | Import client_tools, mcp_server | ✅ Pass | Modules can be imported |
| Lint | N/A | ⚠️  No linting configured | No ruff, flake8, black, mypy, or pre-commit |
| Test | N/A | ⚠️  No tests found | No pytest, no test files, no test framework |

**Summary:** Dependencies install OK, syntax check OK, imports OK (with expected runtime connection errors for streamlit_app)

## CI/CD

**No CI/CD configured.**

This repository has no GitHub Actions workflows, no Tekton pipelines, no Jenkins configuration, and no other CI/CD systems. There are no automated checks that run on pull requests or pushes.

### Expected CI Checks (None)

No gating checks exist.

## Conventions

### Code Organization
- `app/src/` - Streamlit web application and agent examples
- `mcp-servers/` - MCP server implementations (ansible, custom, github, llamastack, openshift)
- `kubernetes/` - Kubernetes/OpenShift deployment manifests
- `Makefile` - Build commands for containers

### Python Code Style
- Some files use type hints (e.g., `typing.Dict, List, Optional, Any`)
- Docstrings present in class definitions
- No consistent formatting enforced
- Mix of absolute and relative imports

### Container Builds
All components are containerized using `podman build`:
- `make build_ui` - Builds Streamlit client container
- `make build_mcp` - Builds MCP server container
- `make build_llamastack` - Builds Llama Stack container using upstream template

### Deployment
This project is designed to run on OpenShift with:
- vLLM inference servers for model serving
- Llama Stack server for agent orchestration
- MCP servers for tool integration
- Streamlit UI for user interaction

All deployment requires OpenShift cluster access and is configured via Kubernetes manifests in `kubernetes/`.

## Gaps & Caveats

### Critical Gaps

1. **No tests** - The repository contains no test files, no test directories, and no testing framework. There is no way to validate that code changes work correctly.

2. **No linting** - No linter configuration exists. No ruff, flake8, black, mypy, or pre-commit hooks. Code quality cannot be automatically validated.

3. **No CI/CD** - No automated checks run on pull requests. No GitHub Actions workflows, no continuous integration.

4. **Archived repository** - This repository has "-archive" in its name and appears to be archived/deprecated, suggesting it's not under active development.

5. **Incomplete dependency documentation** - The `fire` package is required by `llama-stack-client` at runtime but is not listed in any requirements file. The `mcp` package may need explicit installation beyond what's in requirements.txt.

### Runtime Requirements

6. **Requires external services** - The application cannot run standalone. It requires:
   - A running Llama Stack server (configured via `REMOTE_BASE_URL`)
   - MCP server endpoints (configured via `REMOTE_MCP_URL`)
   - Vector database provider (configured via `REMOTE_VDB_PROVIDER`)
   - OpenShift cluster for deployment

7. **No local development instructions** - No documentation on how to run the application locally without OpenShift.

### What Can Be Validated

Given the lack of tests and linting, the only validation an agent can perform is:
- ✅ Python syntax is valid (via `python -m py_compile`)
- ✅ Dependencies install successfully
- ✅ Python modules can be imported
- ❌ Code actually works (no tests)
- ❌ Code follows style guidelines (no linters)
- ❌ Changes don't break existing functionality (no tests)

### Recommendations for Enabling Agent Validation

To make this repository suitable for automated patch validation, it would need:

1. **Add pytest** with unit tests for core functionality
2. **Add ruff or flake8** for linting
3. **Add GitHub Actions** workflow to run lint + tests on PRs
4. **Document development setup** with instructions for local testing
5. **Mock external services** in tests so they can run without Llama Stack/MCP servers
6. **Complete dependency specification** by adding all required packages to requirements files
7. **Add pre-commit hooks** to enforce code quality

Without these additions, this repository has **agent_readiness: none** - patches can be applied, but there's no automated way to validate they work correctly.
