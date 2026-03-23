# Test Context for opendatahub-io/agents

**Repository:** opendatahub-io/agents
**Analyzed:** 2026-03-22T16:50:00Z
**Agent Readiness:** **NONE** - This is an experimental sandbox with no test infrastructure

## Overview

This repository is explicitly labeled as an experimental workspace for AI agent prototyping. It contains no CI/CD infrastructure, no linting configuration, no formal test suite, and no automated validation. The README states: "This repository contains experimental code. It is not intended to be a stable, reliable, or production-ready solution. Code may be incomplete or broken. APIs and functionality can change without notice."

**Languages:** Python (32 files), Go (5 files)
**Build System:** Multiple independent sub-projects (uv for Python, go for Go)
**Project Structure:** Collection of examples and tools, no root-level build system

## Container Recipe

**Status:** No container recipe provided.

**Reason:** This repository has no lint or test commands that can be validated in a container. The few test-like files that exist (`test_langchain_mcp.py`, `test_langchain_guardrails.py`, `test-mcp-server.py`) are manual testing scripts that require extensive external infrastructure:

- Running Kubernetes/OpenShift clusters
- MCP (Model Context Protocol) servers
- Llama Stack inference servers
- LLM models (Ollama, GPT-4, Gemini, etc.)
- GitHub personal access tokens
- Environment variables for API endpoints and credentials

These are not automated tests designed for CI validation - they are exploratory scripts for manual testing during development.

### What an Agent Cannot Do

An agent **cannot** validate patches against this repository because:

1. **No automated tests exist** that can run without human intervention
2. **No linting is configured** - there's nothing to enforce code quality
3. **No CI checks** - there are no gating criteria for merges
4. **Manual testing requires infrastructure** - Kubernetes clusters, LLM APIs, MCP servers
5. **Experimental nature** - code is expected to be incomplete or broken

### If You Must Attempt Testing

If you want to manually test a specific sub-project (not recommended for automated validation):

#### Python Sub-Project (e.g., langchain-langgraph)

```bash
# Start container
podman run -d --name test-context-agents \
  -v /home/jtanner/workspace/github/jctanner.redhat/2026_03_22_odh_test_context/odh-tests-context/checkouts/opendatahub-io/agents:/app:Z \
  -w /app/examples/langchain-langgraph \
  python:3.13 \
  sleep infinity
```

```bash
# Install uv
podman exec test-context-agents bash -c "pip install uv"
```

```bash
# Install dependencies
podman exec test-context-agents bash -c "cd /app/examples/langchain-langgraph && uv sync"
```

At this point you would need to:
- Set up a Llama Stack server
- Set up a Kubernetes MCP server
- Configure environment variables (OPENAI_API_KEY, LLAMA_STACK_SERVER_OPENAI, INFERENCE_MODEL, etc.)
- Ensure external services are reachable from the container

Then you could manually run:

```bash
# This is NOT an automated test - it's a manual testing script
podman exec test-context-agents bash -c "cd /app/examples/langchain-langgraph && source .venv/bin/activate && python test_langchain_mcp.py"
```

```bash
# Cleanup
podman rm -f test-context-agents
```

**This approach is not suitable for automated patch validation.**

#### Go Sub-Project (e.g., github-mcp)

```bash
# Start container
podman run -d --name test-context-agents \
  -v /home/jtanner/workspace/github/jctanner.redhat/2026_03_22_odh_test_context/odh-tests-context/checkouts/opendatahub-io/agents:/app:Z \
  -w /app/examples/github-mcp \
  golang:1.23 \
  sleep infinity
```

```bash
# Download dependencies
podman exec test-context-agents bash -c "cd /app/examples/github-mcp && go mod download"
```

```bash
# Build (no tests exist)
podman exec test-context-agents bash -c "cd /app/examples/github-mcp && go build -v ."
```

```bash
# Cleanup
podman rm -f test-context-agents
```

**Note:** Go sub-projects have no test files (`*_test.go`) at all.

## Validation Results

**Status:** Validation was not performed.

**Reason:** There is no test or lint infrastructure to validate. Attempting to run non-existent tests would provide no useful signal.

## CI/CD

**Status:** None

**Files:** No `.github/workflows/`, no `.tekton/`, no `Jenkinsfile`, no `.zuul.yaml`

**Gating Checks:** None - this repository has no CI/CD whatsoever

## Conventions

**Test File Naming:** `test_*.py` (Python), `*_test.go` (Go, though none exist)
**Test Function Naming:** `test_*` (Python), `Test*` (Go)
**Import Style:** Not standardized - varies across examples

As an experimental repository, there are no enforced conventions. Code quality, style, and organization are not standardized.

## Gaps & Caveats

### Critical Gaps

1. **No CI/CD Infrastructure**
   There are no GitHub Actions workflows, no automated checks, no merge requirements. Patches cannot be validated against any gating criteria because none exist.

2. **No Linting Configuration**
   No ruff, flake8, pylint, mypy, golangci-lint, or any code quality tools are configured. There's no way to check code style, type correctness, or common errors.

3. **No Formal Test Suite**
   The repository has a few manual testing scripts but no test framework setup, no pytest configuration, no Go tests. The test files that exist are exploratory scripts requiring manual setup of external services.

4. **External Dependencies for Testing**
   The manual test scripts require:
   - Kubernetes/OpenShift clusters with sufficient permissions
   - MCP (Model Context Protocol) servers running on specific ports
   - Llama Stack inference servers configured with specific models
   - LLM APIs (Ollama, OpenAI, Google Gemini) with valid credentials
   - GitHub personal access tokens with issue creation permissions
   - Specific environment variables set for each service

5. **Multi-Project Repository**
   This repo contains ~10 independent sub-projects (examples/langchain-langgraph, examples/github-mcp, tools/mcp-tester, etc.) each with different dependencies, build processes, and requirements. There's no unified build or test approach.

6. **Experimental Nature**
   The README explicitly warns: "Code may be incomplete or broken. APIs and functionality can change without notice. Documentation may be sparse or outdated." This is not production code.

### What Works

- Individual sub-projects can be run manually after extensive setup
- Python projects use modern tooling (uv, pyproject.toml)
- Go projects have basic go.mod dependency management

### What Doesn't Work for Automated Validation

- Everything - there's no automation to validate against

### Recommended Actions for Repository Maintainers

If this repository ever moves beyond experimental status:

1. Add GitHub Actions workflows for basic linting (ruff for Python, golangci-lint for Go)
2. Add unit tests that don't require external infrastructure (mock external services)
3. Configure pytest properly in pyproject.toml files
4. Add pre-commit hooks for code quality
5. Create a repository-level Makefile or task runner for common operations
6. Document testing procedures and dependencies

### Recommended Actions for Agents

**Do not attempt automated patch validation against this repository.**

If you need to work with this code:
1. Treat it as exploratory/prototype code
2. Manual testing is required
3. No quality gates exist to enforce standards
4. Changes cannot be automatically validated
5. Consider each sub-project independently

## Summary

**Agent Readiness: NONE**

This repository is an experimental sandbox for AI agent research. It has no CI/CD, no linting, no automated tests, and no infrastructure for patch validation. The few test files that exist are manual scripts requiring extensive external dependencies (Kubernetes clusters, LLM services, MCP servers).

An agent **cannot** meaningfully validate patches because:
- No automated tests exist
- No linting is configured
- No CI checks gate merges
- Manual testing requires human setup of external services
- Code is explicitly experimental and may be broken

**Recommendation:** For any serious development work, fork individual sub-projects and add proper test infrastructure. This repository serves as a collection of examples and prototypes, not as a maintained codebase with quality gates.
