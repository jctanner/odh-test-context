# Test Context: ai-helpers

**Agent Readiness: MEDIUM** — Lint commands validated successfully, but no automated tests exist. An agent can validate code quality but cannot verify functionality.

## Overview

- **Repository:** opendatahub-io/ai-helpers
- **Languages:** Python, Shell, YAML
- **Build System:** Make
- **Primary Purpose:** AI helper plugins/scripts for Claude Code, OpenCode.ai, Cursor AI, and Gemini Gems
- **Test Framework:** None
- **CI System:** GitHub Actions

This repository contains a collection of AI helper tools organized as plugins. Validation is purely through linting - there are no automated functional tests.

## Container Recipe

A complete, copy-paste recipe for validating patches in a container:

### 1. Start Container

```bash
podman run -d --name test-context-ai-helpers \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-ai-helpers bash -c "apt-get update && apt-get install -y make shellcheck git"
```

### 3. Install Python Dependencies

```bash
podman exec test-context-ai-helpers bash -c "pip install --upgrade pip && pip install ruff PyYAML"
```

### 4. Run Ruff Check (Validated: ✓ PASSED)

```bash
podman exec test-context-ai-helpers bash -c "cd /app && ruff check ."
```

**Expected:** Exit code 0, output "All checks passed!"

### 5. Run Ruff Format Check (Validated: ✓ PASSED)

```bash
podman exec test-context-ai-helpers bash -c "cd /app && ruff format --check --diff ."
```

**Expected:** Exit code 0, output shows "X files already formatted"

### 6. Run Shellcheck (Validated: ✓ PASSED)

```bash
podman exec test-context-ai-helpers bash -c "cd /app && find . -name '*.sh' -type f -exec shellcheck {} +"
```

**Expected:** Exit code 0, no output (no issues found)

### 7. Verify Scripts Run Successfully (Validated: ✓ PASSED)

```bash
podman exec test-context-ai-helpers bash -c "cd /app && python3 scripts/update_claude_settings.py"
```

**Expected:** Exit code 0, output "✓ Claude settings and marketplace updated successfully!"

```bash
podman exec test-context-ai-helpers bash -c "cd /app && python3 scripts/build-website.py"
```

**Expected:** Exit code 0, output shows "Total tools: X"

### 8. Run Full Lint Suite via Make

```bash
podman exec test-context-ai-helpers bash -c "cd /app && make lint"
```

**Note:** This will fail in the container because it tries to run claudelint via podman (podman-in-podman is complex). For full validation, run steps 4-7 individually, or run claudelint on the host:

```bash
podman run --rm -v $(pwd):/workspace:Z ghcr.io/stbenjam/claudelint:main -v --strict
```

### 9. Cleanup

```bash
podman rm -f test-context-ai-helpers
```

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install deps | `pip install ruff PyYAML` | ✓ PASSED | Dependencies install cleanly |
| Ruff check | `ruff check .` | ✓ PASSED | All checks passed, exit code 0 |
| Ruff format | `ruff format --check --diff .` | ✓ PASSED | 14 files already formatted |
| Shellcheck | `find . -name '*.sh' -exec shellcheck {} +` | ✓ PASSED | No issues found |
| Update script | `python3 scripts/update_claude_settings.py` | ✓ PASSED | Generated settings successfully |
| Build script | `python3 scripts/build-website.py` | ✓ PASSED | Generated website data |

## CI/CD Configuration

### Gating Checks (Required for Merge)

All checks run on push and pull requests to the `main` branch.

#### 1. Lint Workflow (.github/workflows/lint.yml)

**Trigger:** `on: [push, pull_request]` to `main` branch

**Commands:**
```bash
# System setup
sudo apt-get update
sudo apt-get install -y make shellcheck
pip install --upgrade pip
pip install ruff PyYAML

# Run lint
make lint
```

**What `make lint` does:**
1. Runs claudelint in container: `podman run --rm -v $(PWD):/workspace:Z ghcr.io/stbenjam/claudelint:main -v --strict`
2. Runs ruff syntax check: `ruff check .`
3. Runs ruff format check: `ruff format --check --diff .`
4. Runs shellcheck: `find . -name '*.sh' -type f -exec shellcheck {} +`
5. Runs `make update` and verifies no uncommitted changes result

#### 2. Build Workflow (.github/workflows/build.yml)

**Trigger:**
- `on: [push, pull_request]` to `main` when `images/**` or workflow file changes
- Nightly at 2 AM UTC

**Matrix builds:** claude and cursor images

**Commands:**
```bash
# Build Claude image
docker build -f ./images/claude/Containerfile -t ghcr.io/opendatahub-io/ai-helpers .

# Build Cursor image
docker build -f ./images/cursor/Containerfile -t ghcr.io/opendatahub-io/ai-helpers-cursor .
```

Multi-platform builds (linux/amd64, linux/arm64). Images pushed to ghcr.io on successful main branch builds.

## Linting Configuration

### Ruff (Python)

**Config:** `.ruff.toml`

**Settings:**
- Line length: 100
- Rules enabled: F (pyflakes), E (pycodestyle errors), W (warnings), I (isort), N (naming)

**Commands:**
- Check: `ruff check .`
- Fix: `ruff check --fix .`
- Format check: `ruff format --check --diff .`
- Format fix: `ruff format .`

### Shellcheck (Shell Scripts)

**Config:** None (uses defaults)

**Command:** `find . -name '*.sh' -type f -exec shellcheck {} +`

**Scope:** All `.sh` files in the repository

### Claudelint (Plugin Validation)

**Config:** `.claudelint.yaml` with custom rules in `.claudelint-custom.py`

**Command:** `podman run --rm -v $(pwd):/workspace:Z ghcr.io/stbenjam/claudelint:main -v --strict`

**Validates:**
- Plugin JSON structure
- Command frontmatter and sections
- Skill frontmatter
- Marketplace registration
- Custom rules for documentation consistency

## Build Configuration

**System:** Make

**Dependencies:**
- System: make, shellcheck, git, podman/docker
- Python: ruff, PyYAML

**Commands:**
- Install deps: `pip install ruff PyYAML`
- Lint: `make lint`
- Update settings: `make update`
- Build images: `make build` (or `make build-claude`, `make build-cursor`)
- Serve docs: `make docs` (starts HTTP server on port 8000)

**Update Process:**
The `make update` target:
1. Runs `python3 scripts/update_claude_settings.py` to generate Claude settings and marketplace config
2. Runs `python3 scripts/build-website.py` to generate website data (docs/data.json)
3. Runs `ruff format .` to auto-format Python code

## Conventions

### File Organization
- **Python scripts:** `scripts/` and `helpers/skills/*/scripts/`
- **Shell scripts:** Use `.sh` extension
- **Plugins:** Organized under `helpers/` with subdirectories:
  - `helpers/agents/` - Agent definitions
  - `helpers/commands/` - Command definitions (Markdown)
  - `helpers/gems/` - Gemini Gems configurations
  - `helpers/skills/` - Skill definitions (agentskills.io format)

### Code Style
- Python: Line length 100, imports organized by isort
- Shell: Follows shellcheck recommendations
- Plugin structure: Follows Claude Code plugin specification

### Categories
- Tool categories defined in `categories.yaml`
- Uncategorized tools automatically placed in "General" category
- Categories displayed on project website

## Gaps & Caveats

### No Automated Tests
This repository has **no test suite**. Validation is purely static:
- ✓ Linting ensures code quality and style compliance
- ✗ No tests verify that plugins actually work
- ✗ No integration tests for Claude Code/OpenCode.ai/Cursor/Gemini
- ✗ Scripts run but correctness is not validated

### Claudelint Complexity
The claudelint tool runs in a container, requiring podman/docker. In nested container environments (container-in-container), this adds complexity. For CI or containerized validation, run other lint checks individually and claudelint on the host.

### Manual Testing Required
Plugin functionality must be manually tested:
1. Add marketplace: `/plugin marketplace add ./`
2. Install plugin: `/plugin install odh-ai-helpers`
3. Test commands/skills/agents manually
4. Verify behavior is correct

### Container Build Not Validated
The container images (claude and cursor) are built in CI but not tested. There's no validation that:
- Images start correctly
- Plugins are properly installed
- Tools work inside the container

## Quick Validation Checklist

For a downstream agent validating a patch:

1. **Lint Python code:**
   ```bash
   ruff check .
   ruff format --check --diff .
   ```

2. **Lint shell scripts:**
   ```bash
   find . -name '*.sh' -type f -exec shellcheck {} +
   ```

3. **Verify scripts run:**
   ```bash
   python3 scripts/update_claude_settings.py
   python3 scripts/build-website.py
   ```

4. **Check for uncommitted changes:**
   ```bash
   git status --porcelain
   ```
   Should be empty after running update scripts.

5. **Optional - validate plugins:**
   ```bash
   podman run --rm -v $(pwd):/workspace:Z ghcr.io/stbenjam/claudelint:main -v --strict
   ```

**Expected result:** All commands exit 0 with no errors. This validates code quality but NOT functionality.
