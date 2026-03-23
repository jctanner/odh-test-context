# Test Context for opendatahub-io/rag

## Overview

**Repository**: opendatahub-io/rag
**Languages**: Python 3.12, Go 1.24.2, YAML/Kubernetes
**Build System**: Make (demo-specific), pip, go build
**Agent Readiness**: **MEDIUM** - Linting fully validated and working. No tests exist (demo/docs repository).

This is a demonstration and documentation repository for RAG (Retrieval-Augmented Generation) Stack on Kubernetes/OpenShift. It contains demos, benchmarks, and deployment guides rather than a traditional application codebase. Linting is fully configured and validated via pre-commit and ruff. No test infrastructure exists.

## Container Recipe

This recipe provides a complete, copy-paste workflow for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-rag \
  -v "$(pwd):/app:Z" \
  -w /app \
  python:3.12 \
  sleep infinity
```

**Note**: Use `docker` instead of `podman` if podman is not available. The base image `python:3.12` already includes git and make.

### 2. Install Dependencies

```bash
# Install pre-commit and ruff
podman exec test-context-rag bash -c "cd /app && pip install --no-cache-dir pre-commit ruff==0.9.4"
```

### 3. Run Linting (Pre-commit - All Hooks)

```bash
# Run all pre-commit hooks (includes ruff, license checks, YAML validation, etc.)
podman exec test-context-rag bash -c "cd /app && SKIP=no-commit-to-branch pre-commit run --all-files"
```

**Expected Result**: All checks should pass. The `SKIP=no-commit-to-branch` env var skips the branch protection hook (which would fail since we're on main).

**Validated**: ✅ SUCCESS - All hooks passed in validation

### 4. Run Linting (Ruff Check)

```bash
# Run ruff linter directly
podman exec test-context-rag bash -c "cd /app && ruff check ."
```

**Expected Result**: "All checks passed!"

**Validated**: ✅ SUCCESS - No issues found

### 5. Run Linting (Ruff Format Check)

```bash
# Check code formatting
podman exec test-context-rag bash -c "cd /app && ruff format --check ."
```

**Expected Result**: "X files already formatted" (where X is the number of Python files)

**Validated**: ✅ SUCCESS - 41 files already formatted

### 6. Auto-fix Linting Issues (Optional)

```bash
# Auto-fix ruff issues and format code
podman exec test-context-rag bash -c "cd /app && ruff check --fix . && ruff format ."
```

### 7. Run Tests

**Not Applicable**: This repository has no tests. It is a demo/documentation repository.

### 8. Cleanup

```bash
podman rm -f test-context-rag
```

## Validation Results

All commands were validated in a live container on 2026-03-22.

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install | `pip install pre-commit ruff==0.9.4` | ✅ PASS | Installed successfully |
| Lint | `pre-commit run --all-files` | ✅ PASS | All hooks passed (no-commit-to-branch skipped) |
| Lint | `ruff check .` | ✅ PASS | All checks passed |
| Lint | `ruff format --check .` | ✅ PASS | 41 files already formatted |
| Test | N/A | N/A | No tests exist |

### Validation Output Snippets

**Pre-commit output** (abbreviated):
```
check for merge conflicts................................................Passed
trim trailing whitespace.................................................Passed
check for added large files..............................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
detect private key.......................................................Passed
fix requirements.txt.....................................................Passed
mixed line ending........................................................Passed
check that executables have shebangs.....................................Passed
check json...............................................................Passed
check that scripts with shebangs are executable..........................Passed
Insert license in comments...............................................Passed
ruff.....................................................................Passed
ruff-format..............................................................Passed
blacken-docs.............................................................Passed
```

**Ruff check output**:
```
All checks passed!
```

**Ruff format output**:
```
41 files already formatted
```

## CI/CD

### GitHub Actions Workflow

**File**: `.github/workflows/pre-commit.yaml`

**Triggers**:
- `pull_request` (all PRs)
- `push` to `main` branch

**Required Checks** (Gating):
1. **pre-commit** - Runs all pre-commit hooks including:
   - Ruff linting (`ruff check --fix`)
   - Ruff formatting (`ruff format`)
   - License header insertion
   - YAML/JSON validation
   - Trailing whitespace, EOF, merge conflict checks
   - Executable/shebang validation
2. **Verify no uncommitted changes** - Ensures pre-commit didn't modify files
3. **Verify no new files** - Ensures pre-commit didn't create new files

**Exact CI Commands**:
```bash
# Pre-commit hook execution
SKIP=no-commit-to-branch RUFF_OUTPUT_FORMAT=github pre-commit run --all-files

# Verification steps
git diff --exit-code
git ls-files --others --exclude-standard
```

**Environment**:
- Python 3.12
- Pip cache enabled
- Concurrency group cancels in-progress runs on new pushes

## Conventions

### Python Code Style
- **Linter**: Ruff v0.9.4 (default configuration, no custom ruff.toml)
- **Formatter**: Ruff (replaces black)
- **Python Version**: 3.12
- **Import Style**: Enforced by ruff defaults

### File Requirements
Every demo must include:
1. `README.md` - Purpose, overview, usage
2. `DEPLOYMENT.md` or deployment section in README - Step-by-step reproduction
3. `requirements.txt` - If applicable

### License Headers
All `.py` and `.sh` files automatically get Apache 2.0 license headers inserted via pre-commit hook (reference: `docs/license_header.txt`).

### Repository Structure
```
rag/
├── demos/           # Platform-specific demos with use cases
├── benchmarks/      # Performance benchmarking scripts
├── stack/           # Kubernetes/OpenShift deployment configs (kustomize)
├── notebooks/       # Jupyter notebooks
└── docs/            # Documentation
```

### Test Naming Conventions
Not applicable - no tests exist in this repository.

## Gaps & Caveats

### Major Gaps

1. **No Tests**: This repository has no test files, test framework, or test infrastructure. It is a demo/documentation repository. Agents can validate linting but cannot validate functionality.

2. **No Unified Build**: Individual demos have separate `requirements.txt` files. There is no root-level dependency management or build system.

3. **Deployment Required for Validation**: Demos are designed to run on Kubernetes/OpenShift clusters. They cannot be validated in isolation without cluster access.

4. **Go Code Not Linted**: The Go component (`demos/redbank-demo/chat-bot/whatsapp-bot/`) has no linting configured in pre-commit. Only Python files are linted.

5. **No Ruff Configuration**: Ruff uses default rules only (no `ruff.toml` or `[tool.ruff]` in pyproject.toml).

### What Works

- ✅ Pre-commit hooks run successfully
- ✅ Ruff linting validates all Python files
- ✅ Ruff formatting validates code style
- ✅ YAML/JSON validation works
- ✅ License header insertion works
- ✅ CI workflow accurately represents local pre-commit behavior

### What Doesn't Work

- ❌ No tests to run
- ❌ No way to validate demo functionality without a cluster
- ❌ No Go linting
- ❌ No dependency resolution for demos (each has separate requirements.txt)

### Recommendations for Agent Usage

**For patch validation**, an agent can:
1. Apply the patch
2. Run `pre-commit run --all-files` to validate linting
3. Check for formatting issues with `ruff format --check .`
4. Verify YAML/JSON validity
5. Ensure license headers are present

**An agent CANNOT**:
1. Run tests (none exist)
2. Validate demo functionality (requires cluster)
3. Detect runtime errors (no execution environment)
4. Lint Go code (not configured)

## Quick Reference

### Most Common Commands

```bash
# Install linting tools
pip install pre-commit ruff==0.9.4

# Run all checks
SKIP=no-commit-to-branch pre-commit run --all-files

# Lint Python files
ruff check .

# Format Python files
ruff format .

# Auto-fix issues
ruff check --fix .
ruff format .
```

### File Locations

- **Pre-commit config**: `.pre-commit-config.yaml`
- **License header**: `docs/license_header.txt`
- **CI workflow**: `.github/workflows/pre-commit.yaml`
- **Python files**: Scattered in `demos/`, `benchmarks/`, `notebooks/`
- **Go module**: `demos/redbank-demo/chat-bot/whatsapp-bot/go.mod`

### Agent Readiness: MEDIUM

**Rationale**: Linting is fully functional and validated. An agent can apply patches and verify code style/quality via pre-commit and ruff. However, no tests exist, so functional correctness cannot be validated automatically. This is appropriate for a demo/docs repository but limits agent capabilities to style/lint checking only.
