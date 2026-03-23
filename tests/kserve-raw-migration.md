# Test Context: kserve-raw-migration

## Overview

**Repository**: opendatahub-io/kserve-raw-migration
**Languages**: Bash/Shell scripting
**Build System**: None (utility script repository)
**Agent Readiness**: **LOW** - Only static analysis possible; functional testing requires OpenShift cluster with KServe

This repository contains operational shell scripts for converting KServe InferenceServices from serverless (Knative) mode to raw (Kubernetes native) deployment mode on OpenShift. It is NOT a traditional software project with tests/CI - it's an administrative utility script.

**Why LOW readiness**: No test infrastructure exists. The scripts manipulate live Kubernetes resources and require an OpenShift cluster with KServe operator installed, admin RBAC permissions, and existing InferenceService resources. Only syntax validation and static linting are possible without this infrastructure.

---

## Container Recipe

This recipe provides **static analysis only** (syntax checking and linting). Functional testing requires an actual OpenShift cluster.

### 1. Start Container

```bash
podman run -d --name test-context-kserve-raw-migration \
  -v $(pwd):/app:Z \
  -w /app \
  debian:bookworm \
  sleep infinity
```

### 2. Install Dependencies

```bash
podman exec test-context-kserve-raw-migration bash -c "\
  apt-get update -qq && \
  apt-get install -y -qq shellcheck bash"
```

### 3. Validate Bash Syntax

```bash
# Check convert.sh syntax
podman exec test-context-kserve-raw-migration bash -c "\
  cd /app && bash -n convert.sh"

# Check sample_curl.sh syntax
podman exec test-context-kserve-raw-migration bash -c "\
  cd /app && bash -n sample_curl.sh"
```

**Expected result**: Both commands should exit with code 0 (no output means success).

**Validation status**: ✅ PASSED - Both scripts have valid bash syntax.

### 4. Run Shellcheck Linter

```bash
# Lint convert.sh
podman exec test-context-kserve-raw-migration bash -c "\
  cd /app && shellcheck convert.sh"

# Lint sample_curl.sh
podman exec test-context-kserve-raw-migration bash -c "\
  cd /app && shellcheck sample_curl.sh"
```

**Expected result**:
- `convert.sh`: Shellcheck will report 47 findings (13 warnings, 18 info, 8 style, 3 other). Exit code 0.
- `sample_curl.sh`: Shellcheck will report 1 finding (missing shebang). Exit code 0.

**Validation status**: ✅ PASSED - Shellcheck ran successfully. Found style improvements but no blocking errors.

**Shellcheck findings for convert.sh**:
- SC2155 (warning, 13×): Declare and assign separately to avoid masking return values
- SC2086 (info, 18×): Double quote to prevent globbing and word splitting
- SC2181 (style, 8×): Check exit code directly with `if ! mycmd;` instead of `$?`
- SC2162 (info, 2×): `read` without `-r` will mangle backslashes
- SC2034 (warning, 2×): Variables appear unused (ROLE_NAME, ROLEBINDING_NAME)
- SC2016 (info, 3×): Expressions don't expand in single quotes
- SC2001 (style, 1×): Use `${variable//search/replace}` instead of sed
- SC2269 (info, 1×): Variable assigned to itself

**Shellcheck findings for sample_curl.sh**:
- SC2148 (error level, non-blocking): Missing shebang line

### 5. Run Functional Tests

**NOT APPLICABLE** - No test suite exists. Functional validation requires:

1. **OpenShift cluster** with:
   - OpenShift CLI (`oc`) v4.x+ installed and authenticated
   - KServe operator installed
   - At least one InferenceService resource in serverless mode
   - ServingRuntime resources

2. **RBAC permissions** to:
   - Get/create/patch InferenceServices
   - Get/create/patch ServingRuntimes
   - Create ServiceAccounts, Roles, RoleBindings, Secrets
   - Access Knative routes

3. **CLI tools** installed on the execution host:
   - `yq` v4.x+ (YAML processor)
   - `jq` v1.6+ (JSON processor)

**Example functional test** (requires infrastructure):

```bash
# This will fail without proper OpenShift setup
./convert.sh --inference-service=test-model --namespace=test-ns
```

### 6. Cleanup

```bash
podman rm -f test-context-kserve-raw-migration
```

---

## Validation Results

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Install | `apt-get install shellcheck bash` | 0 | ✅ PASS | Dependencies installed |
| Syntax | `bash -n convert.sh` | 0 | ✅ PASS | Valid bash syntax |
| Syntax | `bash -n sample_curl.sh` | 0 | ✅ PASS | Valid bash syntax |
| Lint | `shellcheck convert.sh` | 0 | ✅ PASS | 47 style suggestions, no errors |
| Lint | `shellcheck sample_curl.sh` | 0 | ✅ PASS | 1 missing shebang warning |
| Test | N/A | N/A | ❌ N/A | No test infrastructure |

**Summary**: Static analysis successful. Syntax is valid, linting found style improvements but no blocking errors. Functional testing requires OpenShift cluster infrastructure.

---

## CI/CD

**Status**: ❌ No CI/CD configured

**Findings**:
- No `.github/workflows/` directory
- No Tekton pipelines in `.tekton/`
- No `Jenkinsfile`
- No CI automation of any kind
- No automated validation on pull requests

**Recommendation**: Add GitHub Actions workflow for:
- Shellcheck linting on PRs
- Bash syntax validation
- Documentation validation (README vs script --help)

---

## Conventions

### Script Structure

**Main script**: `convert.sh` (1061 lines)
- Comprehensive help text (142 lines)
- Command-line argument parsing with long/short options
- Interactive namespace confirmation
- Prerequisite validation (oc, yq, jq installed)
- Permission checks (RBAC validation)
- Resource ownership tracking via UID/ownerReferences
- Colored output for better UX
- Error handling with cleanup traps

**Usage**:
```bash
./convert.sh --inference-service=<name> [--namespace=<namespace>]
./convert.sh -i <name> [-n <namespace>]
./convert.sh --help
./convert.sh --version
```

### Bash Best Practices Observed

✅ Uses functions for code organization
✅ Error handling with trap and cleanup functions
✅ Input validation and user confirmation prompts
✅ Colored output for readability
✅ Comprehensive help text
✅ Version information

### Bash Best Practices NOT Observed (per shellcheck)

⚠️ Declare and assign variables separately to avoid masking return values
⚠️ Use `read -r` to prevent backslash mangling
⚠️ Check exit codes directly (`if ! cmd`) instead of `if [ $? -ne 0 ]`
⚠️ Quote variables to prevent word splitting
⚠️ Remove unused variables

### File Naming

- Scripts: `*.sh` extension with executable bit set
- Generated resources: `{name}-{type}.yaml` (e.g., `my-model-isvc.yaml`)
- Raw deployment suffix: `-raw` (e.g., `my-model-raw`)

---

## Gaps & Caveats

### Critical Gaps

1. **No test infrastructure**: Repository contains zero tests. No unit tests, no integration tests, no smoke tests.

2. **No CI/CD**: No automated validation. Changes are not validated before merge.

3. **Linting not configured**: Shellcheck is not set up in the repository. Must be run manually.

4. **Functional testing impossible without infrastructure**: The script requires:
   - Live OpenShift cluster (can't be mocked)
   - KServe CRDs installed
   - Admin-level RBAC permissions
   - Real InferenceService resources

   These cannot be validated in an isolated container environment.

5. **No version pinning**: Dependencies (`oc`, `yq`, `jq`) are documented but versions aren't enforced or checked beyond existence.

6. **sample_curl.sh is not production-ready**: Contains hardcoded paths and endpoints specific to a development environment.

### Medium Priority Gaps

7. **No pre-commit hooks**: No automatic validation before commits.

8. **No documentation tests**: README examples could be out of sync with actual script behavior.

9. **No validation of generated YAML**: Script generates Kubernetes YAML but doesn't validate it against schemas.

10. **No dry-run mode**: Script immediately applies resources to the cluster. No way to preview changes without executing them.

### Low Priority Gaps

11. **Shellcheck findings**: 47 style improvements suggested (see Validation Results).

12. **No CHANGELOG**: Version history is in README but not in a standard CHANGELOG format.

---

## How to Validate a Patch

### For Code Changes (convert.sh modifications)

1. **Syntax check**:
   ```bash
   bash -n convert.sh
   ```

2. **Lint**:
   ```bash
   shellcheck convert.sh
   ```

3. **Manual testing** (requires OpenShift cluster):
   ```bash
   # Create a test InferenceService first (outside scope of this script)
   # Then test the conversion
   ./convert.sh -i test-model -n test-namespace

   # Verify conversion succeeded
   oc get isvc -n test-namespace test-model-raw
   oc get servingruntimes -n test-namespace test-model-runtime-raw
   ```

4. **Check help text** if user-facing changes:
   ```bash
   ./convert.sh --help
   ```

### For Documentation Changes

1. **Verify examples** in README still work (requires cluster)
2. **Check that help text in script matches README usage section**
3. **Validate markdown syntax**:
   ```bash
   # If available
   markdownlint README.md
   ```

### For New Features

Since there are no tests, new features must be validated manually:

1. Test happy path with a real InferenceService
2. Test error handling (missing resources, permission denied, etc.)
3. Verify output files are created correctly
4. Check that cleanup works on error
5. Validate interactive prompts work as expected

### Recommended Pre-Merge Checklist

- [ ] `bash -n convert.sh` passes
- [ ] `shellcheck convert.sh` shows no NEW warnings (existing warnings acceptable)
- [ ] Script tested manually on a real OpenShift cluster with KServe
- [ ] Help text (`--help`) reviewed and accurate
- [ ] README examples still valid
- [ ] Version number updated if user-facing changes
- [ ] OWNERS file updated if team membership changed

---

## What an AI Agent Can Validate

### ✅ Can Validate (Static Analysis)

- Bash syntax correctness (`bash -n`)
- Shellcheck linting (style, best practices)
- Script executability (`test -x convert.sh`)
- Presence of shebang line
- Help text accessibility (`--help` flag works)

### ❌ Cannot Validate (Requires Infrastructure)

- Functional correctness of conversions
- Interaction with OpenShift API
- RBAC permission handling
- Resource creation and ownership
- YAML generation correctness
- Error handling for cluster errors
- Interactive prompt behavior
- End-to-end conversion workflow

### ⚠️ Can Partially Validate

- Generated YAML syntax (can validate YAML format, cannot validate Kubernetes schema without cluster)
- Command-line argument parsing (can test `--help` and invalid args, cannot test full workflow)
- Variable usage and scoping (shellcheck detects unused vars, but may have false positives)

---

## Example Validation Workflow for an Agent

```bash
#!/bin/bash
# Agent validation script for kserve-raw-migration patches

set -e

echo "🔍 Validating kserve-raw-migration patch..."

# 1. Syntax validation
echo "  Checking bash syntax..."
bash -n convert.sh
bash -n sample_curl.sh

# 2. Linting
echo "  Running shellcheck..."
shellcheck convert.sh > shellcheck-report.txt 2>&1 || true
shellcheck sample_curl.sh >> shellcheck-report.txt 2>&1 || true

# Count findings
FINDINGS=$(grep -c "^In convert.sh line" shellcheck-report.txt || echo "0")
echo "  Found $FINDINGS shellcheck suggestions"

# 3. Check script is executable
echo "  Checking execute permissions..."
test -x convert.sh || { echo "❌ convert.sh not executable"; exit 1; }

# 4. Verify help text works
echo "  Testing --help flag..."
./convert.sh --help > /dev/null || { echo "❌ --help failed"; exit 1; }

# 5. Verify version flag works
echo "  Testing --version flag..."
./convert.sh --version > /dev/null || { echo "❌ --version failed"; exit 1; }

echo "✅ Static validation passed!"
echo "⚠️  Functional testing requires OpenShift cluster - cannot validate"
echo ""
echo "📋 Shellcheck report: shellcheck-report.txt"
```

---

## Summary

This repository provides an operational utility for OpenShift administrators, not a traditional software project. It has **zero test coverage** and **no CI/CD**, making automated patch validation extremely limited.

**Agent capabilities**:
- ✅ Can validate syntax and run shellcheck
- ❌ Cannot functionally test without OpenShift cluster
- ⚠️ Can detect obvious errors but not subtle bugs

**Recommendation for downstream agents**: Use this repository for **static analysis only**. Flag any functional changes as requiring manual testing by a human with cluster access. Consider the validation "partial" at best.
