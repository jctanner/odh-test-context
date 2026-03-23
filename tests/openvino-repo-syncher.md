# Test Context: openvino-repo-syncher

## Overview

**Repository**: opendatahub-io/openvino-repo-syncher
**Type**: Configuration-only YAML repository
**Languages**: YAML
**Build System**: None (no build process)
**Agent Readiness**: **LOW** - Configuration-only repository with no traditional test/lint infrastructure. An agent can validate YAML syntax but there's no automated testing for business logic or PR validation workflows.

This repository serves as a centralized hub for managing OpenVINO repository synchronization. It contains only YAML configuration files that define mappings for auto-merging changes from upstream OpenVINO repositories to OpenDataHub forks.

## Container Recipe

This recipe validates YAML syntax and the yq/jq parsing pipeline used by the GitHub Actions workflow.

### 1. Start Container

Base image: `python:3.11`

```bash
podman run -d \
  --name test-context-openvino-repo-syncher \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-openvino-repo-syncher bash -c \
  "apt-get update && apt-get install -y jq wget"
```

### 3. Install YAML Linter

```bash
podman exec test-context-openvino-repo-syncher bash -c \
  "pip install --no-cache-dir yamllint"
```

### 4. Install yq

```bash
podman exec test-context-openvino-repo-syncher bash -c \
  "wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 && \
   chmod +x /usr/local/bin/yq"
```

### 5. Validate YAML Syntax with yamllint

**Command** (exits 1 due to style violations, but YAML is valid):

```bash
podman exec test-context-openvino-repo-syncher bash -c \
  "cd /app && yamllint ."
```

**Validation Result**: ❌ FAILED (style violations only)

yamllint reports multiple style issues:
- Trailing spaces
- Lines longer than 80 characters
- Wrong newline characters (CRLF instead of LF)
- Missing document start markers (`---`)
- Indentation inconsistencies

**However**, the YAML files are syntactically valid and can be parsed by yq/jq.

### 6. Test Workflow's yq/jq Pipeline

This validates that the parsing logic used in `.github/workflows/auto-merge.yaml` works correctly:

```bash
podman exec test-context-openvino-repo-syncher bash -c \
  "cd /app && yq -o json src/config/source_map.yaml | \
   jq -r '.git' | \
   jq -c 'map(select(.automerge == \"yes\"))' | \
   jq '. | length'"
```

**Validation Result**: ✅ PASSED (exit code 0)

Output: `9` (9 repositories configured for automerge)

### 7. Cleanup

```bash
podman rm -f test-context-openvino-repo-syncher
```

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install deps | `pip install yamllint && apt-get install jq wget` | 0 | ✅ PASS | Dependencies installed successfully |
| Lint YAML | `yamllint .` | 1 | ❌ FAIL | Style violations found (trailing spaces, line length, newlines) but YAML is syntactically valid |
| Workflow validation | `yq -o json ... \| jq ...` | 0 | ✅ PASS | yq/jq pipeline works, found 9 automerge configs |

**Summary**: YAML files are syntactically valid and parseable, but contain style violations that would need fixing to pass yamllint with default rules.

## CI/CD

**System**: GitHub Actions

**Workflow**: `.github/workflows/auto-merge.yaml`

**Trigger**:
- Manual workflow dispatch (`workflow_dispatch`)
- Scheduled daily at 00:18 UTC (`cron: '18 0 * * *'`)

**Purpose**: This workflow is **NOT** a PR validation workflow. It automates syncing changes from upstream OpenVINO repositories to OpenDataHub forks.

**Process**:
1. Parse `src/config/source_map.yaml` using yq and jq
2. Filter repositories with `automerge: 'yes'`
3. Create a matrix job for each repository
4. Use `opendatahub-io/sync-upstream-repo@v2.0.0-alpha` action to sync changes
5. Sync modes: `branch-to-branch` or `release-following`
6. Merge strategy: `rebase`

**Gating Checks**: None - there are no PR validation workflows configured.

**Required Secrets**: `OPENVINO_SYNC_ACCESS_TOKEN`

## Conventions

### File Structure

```
.
├── .github/
│   └── workflows/
│       └── auto-merge.yaml    # GitHub Actions workflow for repo syncing
├── src/
│   └── config/
│       └── source_map.yaml    # Repository mapping configuration
└── README.md                   # Documentation
```

### Configuration Format

`source_map.yaml` defines repository mappings:

```yaml
git:
  - name: openvino_master
    automerge: 'yes'
    mode: 'branch-to-branch'
    src:
      url: https://github.com/openvinotoolkit/openvino.git
      branch: master
    dest:
      url: https://github.com/opendatahub-io/openvino.git
      branch: master
```

### Conventions

- YAML files use `.yaml` extension (not `.yml`)
- Repository mappings grouped under `git:` key
- Each mapping has: `name`, `automerge`, `mode`, `src`, `dest`
- Sync modes: `branch-to-branch` (specific branch) or `release-following` (branch pattern with wildcards)
- Branch patterns use shell-style globs (e.g., `releases/20*`)

## Gaps & Caveats

### Major Gaps

1. **No Testing Infrastructure**: This is a configuration-only repository with no source code, test files, or test framework.

2. **No Linting Configuration**: No `.yamllint` config file exists. yamllint runs with default rules.

3. **No PR Validation Workflows**: The CI workflow only runs auto-merge jobs on a schedule. No checks validate pull requests.

4. **YAML Style Violations**: Both YAML files contain style issues:
   - Trailing whitespace
   - Lines exceeding 80 characters
   - Wrong newline characters (CRLF instead of LF)
   - Missing document start markers
   - Indentation inconsistencies

5. **No Schema Validation**:
   - No validation that `source_map.yaml` follows the expected schema
   - No validation that repository URLs are reachable
   - No validation that branches exist
   - No GitHub Actions workflow schema validation

6. **No Build Process**: Nothing to compile or build.

### What Can Be Validated

An agent working with this repository can:

✅ Validate YAML syntax using `yq` or `yamllint`
✅ Test the yq/jq parsing pipeline from the workflow
✅ Verify the repository mapping structure
✅ Check for trailing spaces and other style issues

An agent **cannot**:

❌ Run tests (none exist)
❌ Validate that repository URLs/branches are correct (would require network access)
❌ Test the actual sync operation (requires secrets and GitHub access)
❌ Run CI checks (no PR validation workflows exist)

### Recommendations for Improving Agent Readiness

To increase agent readiness from **LOW** to **MEDIUM**:

1. Add `.yamllint` configuration file with project-specific rules
2. Fix YAML style violations (trailing spaces, line length, newline characters)
3. Add a PR validation workflow that runs `yamllint .`
4. Add schema validation for `source_map.yaml` (e.g., using JSON Schema)
5. Add a simple test script that validates repository URLs and branches exist

To increase to **HIGH**:

6. Add integration tests that validate the sync logic (in a test environment)
7. Add validation that required secrets are configured
8. Add branch protection rules requiring PR checks to pass

## Usage for Downstream Agents

Since this is a configuration-only repository, a downstream agent validating patches should:

1. **Spin up a container** using the recipe above
2. **Install yamllint and yq** as documented
3. **Run yamllint** to check for syntax and style issues
4. **Run the yq/jq pipeline** to ensure configuration is parseable
5. **Check the diff** for:
   - Changes to repository URLs or branches
   - Changes to automerge settings
   - New repository mappings added
   - Removed repository mappings

A passing validation means:
- YAML files are syntactically valid
- Configuration is parseable by yq/jq
- No new style violations introduced (or existing ones fixed)

A failing validation means:
- YAML syntax errors
- Configuration cannot be parsed
- Style violations introduced (if yamllint is enforced)

**Note**: Even with passing validation, an agent cannot verify that the configuration will work correctly without network access to validate repository URLs and branches.
