# Test Context: sync-upstream-repo

**Generated:** 2026-03-22T20:20:00-04:00
**Repository:** opendatahub-io/sync-upstream-repo
**Agent Readiness:** `low` - Tests exist but require GitHub credentials and live repositories

## Overview

This is a GitHub Action (Docker-based) written in Bash that synchronizes upstream repository forks. The action supports two modes: branch-to-branch syncing and release-following. The repository contains integration tests but no linting configuration or CI/CD workflows.

**Languages:** Bash
**Build System:** Docker/Podman
**Test Framework:** Custom Bash integration tests

**Why Low Readiness:** While the code builds successfully and basic validation works, the test suite requires a GitHub token and access to real GitHub repositories for integration testing. There is no linting configured, no CI, and no way to run isolated unit tests. An agent can validate syntax and build the container, but cannot run the full test suite to verify patch correctness.

## Container Recipe

This is a copy-paste runbook for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-sync-upstream-repo \
  -v $(pwd):/app:Z \
  -w /app \
  registry.access.redhat.com/ubi9/ubi-minimal:9.3-1552 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-sync-upstream-repo bash -c \
  "microdnf -y install bash git && microdnf clean all"
```

### 3. Validate Bash Syntax

```bash
podman exec test-sync-upstream-repo bash -c \
  "cd /app && bash -n entrypoint.sh"
```

**Expected:** Exit code 0, no output (valid syntax)

```bash
podman exec test-sync-upstream-repo bash -c \
  "cd /app && bash -n test-entrypoint.bash"
```

**Expected:** Exit code 0, no output (valid syntax)

### 4. Test Help Command

```bash
podman exec test-sync-upstream-repo bash -c \
  "cd /app && ./entrypoint.sh --help"
```

**Expected:** Exit code 2, displays usage information

### 5. Build Docker Image

This step must be run on the host (not inside the container) as it requires Docker/Podman:

```bash
podman build -t sync-upstream-repo:test -f Dockerfile .
```

**Expected:** Exit code 0, image built successfully

### 6. Test Container Execution

```bash
podman run --rm sync-upstream-repo:test -h
```

**Expected:** Exit code 2, displays help text

### 7. Run Integration Tests (Requires Credentials)

**WARNING:** This step requires:
- Valid GitHub token in `GITHUB_TOKEN` environment variable
- Access to a downstream GitHub repository for testing
- Network access to github.com

```bash
export GITHUB_TOKEN="<your_github_token>"
./test-entrypoint.bash -d <downstream_repo_url> -t ${GITHUB_TOKEN}
```

**Expected:** Exit code 0 if all tests pass

### 8. Cleanup

```bash
podman rm -f test-sync-upstream-repo
podman rmi sync-upstream-repo:test  # optional: remove test image
```

## Validation Results

### ✅ Syntax Validation
- **Command:** `bash -n entrypoint.sh`
- **Result:** PASSED (exit 0)
- **Notes:** No syntax errors detected

### ✅ Syntax Validation (Test Script)
- **Command:** `bash -n test-entrypoint.bash`
- **Result:** PASSED (exit 0)
- **Notes:** No syntax errors detected

### ✅ Help Command
- **Command:** `./entrypoint.sh --help`
- **Result:** PASSED (exit 2, expected for usage display)
- **Output:** Displays full usage information with all flags and modes

### ✅ Docker Build
- **Command:** `podman build -t sync-upstream-repo:test -f Dockerfile .`
- **Result:** PASSED (exit 0)
- **Notes:** Image builds successfully from RHEL UBI 9 minimal base, installs bash and git

### ✅ Container Execution
- **Command:** `podman run --rm sync-upstream-repo:test -h`
- **Result:** PASSED (exit 2, help displayed)
- **Notes:** Container runs and entrypoint.sh executes correctly

### ❌ Integration Tests
- **Command:** `./test-entrypoint.bash -d <repo> -t <token>`
- **Result:** NOT VALIDATED
- **Notes:** Requires GitHub token and test repository - cannot run in isolated environment

## CI/CD

**Status:** No CI/CD configured

This repository has no GitHub Actions workflows, no Tekton pipelines, and no other CI system. It is a GitHub Action meant to be consumed by other repositories, not tested in its own CI.

**Implication:** No automated gating checks run on pull requests. Manual testing required.

## Linting

**Status:** No linters configured

No shellcheck, shfmt, or other bash linting tools are configured. Recommendations:

1. **Add shellcheck:**
   ```bash
   shellcheck -x entrypoint.sh test-entrypoint.bash
   ```

2. **Potential issues to check manually:**
   - Proper quoting of variables
   - Error handling with set -e/-u
   - Shellcheck directives for intentional behavior

## Conventions

### File Naming
- Main script: `entrypoint.sh`
- Test script: `test-entrypoint.bash`
- Both are executable (chmod +x)

### Code Style
- Functions use `snake_case` naming
- Error handling: `set -eu` at script start
- Readonly variables declared with `readonly` keyword
- Argument parsing: uses `getopt` for long/short options
- Git operations use `--quiet` flag unless verbose mode enabled

### Test Patterns
- Integration tests in `test-entrypoint.bash`
- Setup/teardown functions: `before_all()`, `after_all()`
- Tests build Docker container and run actual sync operations
- Validation uses exit code checks: `[[ $? -gt 0 ]] && echo "..." && exit 1`

## Gaps & Caveats

### 1. No Linting
The repository has no automated code quality checks. Bash scripts can contain bugs that would be caught by shellcheck but aren't detected until runtime.

**Impact:** An agent cannot verify code quality, only syntax validity.

### 2. No CI/CD
There are no automated checks that run on pull requests. No way to know what tests are considered "gating" because none exist.

**Impact:** An agent cannot determine if a patch passes required checks.

### 3. Integration Tests Require GitHub
The test suite requires:
- Valid GitHub personal access token
- Access to create/modify branches in a downstream repository
- Network access to github.com
- Specific upstream repo: https://github.com/openvinotoolkit/model_server.git

**Impact:** Tests cannot run in isolation. An agent would need to be given GitHub credentials and a test repository, which is not feasible for security reasons.

### 4. No Unit Tests
There are no unit tests for individual functions. The only tests are end-to-end integration tests that exercise the entire workflow.

**Impact:** An agent cannot validate individual function changes without running the full integration test suite.

### 5. Docker-in-Docker Required
Testing requires building and running Docker containers, which may not be available in all CI environments.

**Impact:** Some validation environments cannot run the tests at all.

## Recommended Validation Strategy for Agents

Given the constraints, here's what an agent CAN validate:

1. **Syntax Check:** Run `bash -n` on all .sh/.bash files ✅
2. **Build Container:** Run `podman build` to verify Dockerfile is valid ✅
3. **Help Text:** Run container with `-h` to verify entrypoint works ✅

What an agent CANNOT validate without credentials:

1. **Full Test Suite:** Requires GitHub token and test repo ❌
2. **Actual Sync Logic:** Requires upstream/downstream repos ❌
3. **Branch Operations:** Requires write access to GitHub ❌

## Files in Repository

```
.
├── action.yml              # GitHub Action definition
├── Dockerfile              # Container build instructions
├── entrypoint.sh           # Main sync logic (executable)
├── test-entrypoint.bash    # Integration tests (executable)
├── README.md               # Documentation
├── LICENSE                 # Apache 2.0 license
└── .gitignore              # Ignores test/ directory
```

## Key Environment Variables

- `GITHUB_TOKEN` - Required for tests and runtime: GitHub personal access token
- `GITHUB_ACTOR` - Optional: defaults to repo owner from URL
- `DOCKER_ENGINE` - Optional: defaults to "podman", can be set to "docker"

## Action Inputs (from action.yml)

- `mode` - Required: "branch-to-branch" or "release-following"
- `upstream_repo_url` - Required: URL of upstream repository
- `upstream_branch` - Optional: defaults to "main"
- `downstream_repo_url` - Required: URL of fork repository
- `downstream_branch` - Optional: defaults to upstream_branch value
- `token` - Required: defaults to `github.token`
- `merge_strategy` - Optional: "rebase" or "merge", defaults to "rebase"
- `spawn_logs` - Optional: "true" or "false", defaults to "false"

## Summary for Agents

**Can Validate:**
- Bash syntax (bash -n)
- Docker build (podman build)
- Container execution (help command)
- File structure and permissions

**Cannot Validate Without Credentials:**
- Full integration test suite
- Actual git sync operations
- Branch creation/deletion
- Tag synchronization

**Recommendation:** For patches to this repository, an agent should:
1. Validate bash syntax on modified .sh/.bash files
2. Rebuild the Docker image to ensure Dockerfile changes work
3. Test the help command to verify argument parsing works
4. Flag that full integration tests require manual execution with GitHub credentials
