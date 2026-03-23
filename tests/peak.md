# Test Context: peak

**Agent Readiness: LOW** — This is a bash test framework for OpenShift operators, not a testable project. It requires OpenShift cluster access to run. Only syntax/style validation is possible in isolated containers.

## Overview

- **Repository**: opendatahub-io/peak
- **Languages**: Bash
- **Build System**: None (pure bash scripts)
- **Test Framework**: Custom bash framework using openshift-test-kit library
- **CI/CD**: None configured
- **Primary Purpose**: Framework for running operator tests on OpenShift clusters

This repository is a test harness/framework rather than a project with its own tests. It:
1. Sets up OpenShift operators via OLM (Operator Lifecycle Manager)
2. Creates namespaces for testing
3. Clones external test repositories
4. Runs .sh test files against OpenShift clusters

Without an active OpenShift cluster login, only test repository cloning works. The framework itself has no unit tests.

## Container Recipe

This recipe can validate bash syntax and style, but cannot run functional tests without OpenShift infrastructure.

### Step 1: Start Container

```bash
REPO_PATH="/path/to/peak"
podman run -d --name test-context-peak \
  -v "${REPO_PATH}:/app:Z" \
  -w /app \
  bash:5.2 \
  sleep infinity
```

### Step 2: Install Linting Tools

```bash
podman exec test-context-peak bash -c "apk add --no-cache shellcheck"
```

### Step 3: Validate Bash Syntax

```bash
podman exec test-context-peak bash -c "cd /app && bash -n run.sh && bash -n setup.sh && bash -n util && bash -n operator-tests/common && echo 'All scripts passed syntax check'"
```

**Expected**: All scripts should pass syntax validation.

### Step 4: Run Shellcheck (Bash Linter)

```bash
podman exec test-context-peak bash -c "cd /app && shellcheck run.sh setup.sh util operator-tests/common"
```

**Expected**: Shellcheck will report style issues:
- SC2006: Legacy backticks (should use `$(...)` instead of `` `...` ``)
- SC2086: Missing quotes around variables
- SC2181: Indirect exit code checks (should use `if ! mycmd;` instead of `if [ "$?" -ne 0 ]`)
- SC2046: Unquoted command substitution
- SC1091: Not following sourced files (info only)

These are style/portability warnings, not critical errors. Exit code 0 means syntax is valid.

### Step 5: Attempt Test Execution (Will Fail Without OpenShift)

```bash
podman exec test-context-peak bash -c "cd /app && ./run.sh 2>&1 | head -20"
```

**Expected**: Will fail because:
1. Git submodule `test/` (openshift-test-kit) is not initialized
2. OpenShift CLI (`oc`) is not installed
3. No active cluster login
4. No test repositories cloned in `operator-tests/`

This demonstrates that the framework requires infrastructure that cannot be provided in a standard container.

### Step 6: Cleanup

```bash
podman rm -f test-context-peak
```

## Validation Results

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Syntax Check | `bash -n *.sh` | ✅ PASS | All scripts syntactically valid |
| Shellcheck | `shellcheck *.sh` | ⚠️ WARNINGS | Style issues only, no errors |
| Test Execution | `./run.sh` | ❌ BLOCKED | Requires OpenShift cluster |

**Summary**: Bash syntax is valid, shellcheck finds style issues that should be fixed but aren't blocking. Functional testing impossible without OpenShift infrastructure.

## CI/CD

**No CI/CD configured.** This repository has:
- No `.github/workflows/` directory
- No GitHub Actions
- No Tekton/Jenkins/Zuul configuration
- No pre-commit hooks
- No automated testing on pull requests

**Recommendation**: Add CI workflow to:
1. Run `shellcheck` on all .sh files
2. Validate bash syntax
3. Check that git submodule reference is valid

## Testing Outside Containers

The framework is designed to run on systems with:

1. **OpenShift cluster access** via `oc` CLI
2. **Active login**: `oc login <cluster>`
3. **Permissions**: Create namespaces, install operators via OLM
4. **Initialized submodule**: `git submodule update --init`

### Setup and Run (On System with OpenShift Access)

```bash
# Initialize the test library submodule
git submodule update --init

# Setup operators and clone test repos
./setup.sh operator-list

# Run all tests
./run.sh

# Run tests matching a pattern
./run.sh "radanalytics"
```

### How Tests Are Organized

Tests are not in this repository. The `setup.sh` script reads `operator-list` and:
1. Creates namespaces for each operator
2. Installs operators via OLM
3. Clones test repositories into `operator-tests/<operator-name>/`

Each test repository contains `.sh` files that:
- Source `$TEST_DIR/common` to load the test library
- Use `os::test::*` functions from openshift-test-kit
- Execute commands via `oc` CLI
- Make assertions about operator behavior

Example from `operator-list`:
```
radanalytics-spark alpha https://github.com/tmckayus/rad-spark-sample-tests
```

This would:
- Install the `radanalytics-spark` operator from the `alpha` channel
- Clone tests from `tmckayus/rad-spark-sample-tests` to `operator-tests/radanalytics-spark/`

## Conventions

**Test File Naming**: `*.sh` files in subdirectories under `operator-tests/`

**Test Execution Order**: Alphabetical within each subdirectory

**Test Structure**: All test files should start with:
```bash
#!/bin/bash
source $TEST_DIR/common
```

**Environment Variables**:
- `$TEST_DIR` - Points to `operator-tests/` directory
- `$MY_SCRIPT` - Name of current test script
- `$RESOURCE_DIR` - Path for temporary files (subdirectory-specific)
- `$OCP` - Set to 0 if OpenShift login active, non-zero otherwise

**Namespace Handling**: The `run.sh` script automatically switches to the namespace matching the test subdirectory name before running tests.

## Gaps & Caveats

### Critical Gaps

1. **No CI/CD**: Changes are not automatically validated
2. **No Framework Tests**: The bash scripts themselves have no unit tests
3. **Infrastructure Dependency**: Cannot validate without OpenShift cluster
4. **No Linting**: Shellcheck issues should be addressed

### Shellcheck Issues to Fix

- **Legacy backticks**: Replace `` `command` `` with `$(command)` throughout
- **Unquoted variables**: Add quotes around `$variable` expansions
- **Indirect exit checks**: Replace `if [ "$?" -eq 0 ]` with `if mycmd;` or `if ! mycmd;`
- **Useless cat**: In `util` line 45, use `tr -dc 'a-z' < /dev/urandom` instead

### Infrastructure Requirements

Running tests requires:
- OpenShift 4.x cluster (origin-test-kit targets OpenShift)
- Cluster admin or namespace creation permissions
- Operator catalog access (OperatorHub)
- Ability to install operators via OLM
- `oc` CLI tool installed and configured

### Missing Documentation

- No documentation of required cluster permissions
- No version compatibility matrix (which OpenShift versions work?)
- No guide for writing new tests
- No troubleshooting guide for common failures

## Recommendations for Downstream Agents

**For Automated Patch Validation:**

1. **Syntax Validation Only**: Use shellcheck to validate bash changes
2. **Do Not Attempt Functional Testing**: Cannot run without cluster
3. **Check for Common Errors**:
   - Bash syntax: `bash -n <file>`
   - Shellcheck style: `shellcheck <file>`
   - Verify sourced files exist

**For Contributing Patches:**

If modifying this framework, ensure:
- All bash scripts pass `bash -n` syntax check
- Fix shellcheck warnings before submitting
- Test manually on an OpenShift cluster
- Document any new dependencies or requirements

**For Using This Framework:**

If using peak to test your operator:
1. Create a separate git repository for your tests
2. Write `.sh` test files using openshift-test-kit functions
3. Add entry to `operator-list` pointing to your test repo
4. Run `./setup.sh operator-list` on a cluster with your operator available
5. Run `./run.sh` to execute tests

## Summary

**Agent Readiness: LOW**

This repository cannot be meaningfully validated by automated agents without OpenShift infrastructure. It is:
- ✅ Syntactically valid bash
- ⚠️ Has style issues that should be fixed
- ❌ Not testable in isolation
- ❌ Not testable in standard containers
- ❌ No CI to validate changes

Downstream agents can only perform static analysis (syntax checking, shellcheck). Functional validation requires manual testing on OpenShift clusters.
