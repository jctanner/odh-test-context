# Test Context: kserve-migration

**Agent Readiness: LOW** — No test infrastructure exists. Script requires OpenShift cluster with KServe to function. Only syntax validation is possible without infrastructure.

---

## Overview

**Repository:** opendatahub-io/kserve-migration
**Languages:** Bash, Shell
**Build System:** None (shell scripts executed directly)
**Primary Branch:** main (empty except LICENSE), code is on `add-initial-files` branch

This repository contains utility scripts for converting KServe InferenceServices from serverless (Knative) mode to raw deployment mode in OpenShift environments. The main script (`convert.sh`) is a 1061-line bash script that interacts with OpenShift via the `oc` CLI tool.

**Key Characteristics:**
- No test infrastructure
- No CI/CD configuration
- No linting/validation tooling
- Requires live OpenShift cluster with KServe to function
- Dependencies: `oc`, `yq`, `jq`

---

## Container Recipe

This recipe validates bash syntax and basic script execution. **Note:** Full functional testing requires an OpenShift cluster with KServe installed.

### 1. Start Container

```bash
podman run -d --name test-context-kserve-migration \
  -v $(pwd):/app:Z \
  -w /app \
  bash:5 \
  sleep infinity
```

**Image Details:**
- Base: `bash:5` (Alpine Linux-based)
- Bash location: `/usr/local/bin/bash` (not `/bin/bash`)
- Package manager: `apk` (Alpine)

### 2. Install System Dependencies

```bash
podman exec test-context-kserve-migration bash -c "apk add --no-cache curl wget jq"
```

**Expected Output:**
```
OK: 15.6 MiB in 33 packages
```

### 3. Install yq (YAML Processor)

```bash
podman exec test-context-kserve-migration bash -c \
  "wget -qO /usr/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 && \
   chmod +x /usr/bin/yq && \
   yq --version"
```

**Expected Output:**
```
yq (https://github.com/mikefarah/yq/) version v4.52.4
```

### 4. Validate Bash Syntax

```bash
podman exec test-context-kserve-migration bash -c "cd /app && bash -n convert.sh"
```

**Expected Result:** Exit code 0 (no output means syntax is valid)

**Status:** ✅ PASSED

### 5. Test Script Version Command

```bash
podman exec test-context-kserve-migration bash -c "cd /app && bash convert.sh --version"
```

**Expected Output:**
```
convert.sh version 1.0.0
KServe InferenceService Raw Deployment Converter
```

**Status:** ✅ PASSED

### 6. Test Script Help Command

```bash
podman exec test-context-kserve-migration bash -c "cd /app && bash convert.sh --help | head -30"
```

**Expected Output:**
```
KServe InferenceService Raw Deployment Converter

DESCRIPTION:
    Converts KServe InferenceServices from serverless mode to raw deployment mode
    while preserving authentication configurations and associated resources.

USAGE:
    convert.sh --inference-service=<name> [--namespace=<namespace>]
    convert.sh -i <name> [-n <namespace>]
    convert.sh --help
    convert.sh --version
...
```

**Status:** ✅ PASSED

### 7. Test Prerequisite Validation

```bash
podman exec test-context-kserve-migration bash -c "cd /app && bash convert.sh -i test-model"
```

**Expected Output:**
```
🔄 Checking prerequisites...
❌ Missing required dependencies:
  • oc (OpenShift CLI)
```

**Status:** ✅ PASSED (correctly identifies missing `oc` CLI)

**Note:** The script exits with code 1 at this point because it cannot proceed without the OpenShift CLI and cluster access.

### 8. Cleanup

```bash
podman rm -f test-context-kserve-migration
```

---

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install deps | `apk add curl wget jq` | ✅ PASSED | Successfully installed jq and tools |
| Install yq | `wget yq && chmod +x` | ✅ PASSED | yq v4.52.4 installed |
| Syntax check | `bash -n convert.sh` | ✅ PASSED | No syntax errors |
| Version | `bash convert.sh --version` | ✅ PASSED | Displays v1.0.0 |
| Help | `bash convert.sh --help` | ✅ PASSED | Full help text displayed |
| Prereq check | `bash convert.sh -i test-model` | ✅ PASSED | Correctly detects missing `oc` |

**Summary:** Syntax validation and basic execution checks pass. Script correctly validates its dependencies. Full functional testing requires OpenShift cluster with KServe.

---

## CI/CD

**Status:** ❌ NONE

No CI/CD configuration exists:
- No `.github/workflows/` directory
- No Tekton pipelines
- No Jenkins files
- No automated checks on pull requests

**Repository State:**
- **main branch:** Contains only LICENSE file and OWNERS (commit: a5ff88e)
- **add-initial-files branch:** Contains actual code (convert.sh, README.md, sample_curl.sh) but not merged (commit: 814f8dc)

---

## Conventions

### File Structure

```
kserve-migration/
├── LICENSE                # Apache 2.0
├── README.md             # Comprehensive documentation (13KB)
├── convert.sh            # Main conversion script (40KB, 1061 lines)
└── sample_curl.sh        # Example curl command for testing
```

### Script Conventions

- **Shebang:** `#!/bin/bash`
- **Version:** Script includes version metadata (v1.0.0)
- **Error handling:** Script uses colored output, trap handlers, and comprehensive error checking
- **Functions:** Well-structured with helper functions for validation, resource discovery, etc.
- **Parameters:** Modern argument parsing with long (`--inference-service=`) and short (`-i`) options

### Naming Conventions

The script follows a naming pattern for converted resources:
- Original: `my-model` → Raw: `my-model-raw`
- Original: `my-model-sa` → Raw: `my-model-raw-sa`
- Original: `runtime-v1` → Raw: `runtime-v1-raw`

---

## Gaps & Caveats

### Critical Gaps

1. **No Test Infrastructure**
   - No unit tests for script functions
   - No integration tests
   - No test framework (bats, shunit2, etc.)
   - No mocking or stubbing of `oc` commands
   - Cannot validate script logic without live cluster

2. **No CI/CD**
   - No automated validation on PRs
   - No syntax checking in CI
   - No shellcheck linting
   - No automated testing before merge

3. **Infrastructure Requirements**
   - Requires OpenShift cluster (cannot test without it)
   - Requires KServe installation
   - Requires specific RBAC permissions
   - Cannot be tested in isolation or with mocks

4. **Code Not Merged**
   - Main branch has no actual code
   - Scripts exist on `add-initial-files` branch
   - Unclear when/if this will be merged

### Validation Gaps

- **No shellcheck:** No static analysis for common shell scripting pitfalls
- **No style enforcement:** No shfmt or other formatting checks
- **No dependency pinning:** yq and jq versions not pinned
- **No version management:** No releases or tags

### Testing Limitations

An agent attempting to validate patches to this repository faces these constraints:

1. **Syntax only:** Can validate bash syntax but not logic
2. **No mocking:** Cannot test actual conversion logic without cluster
3. **No regression tests:** Changes could break functionality without detection
4. **Manual testing required:** All functional testing must be done manually on a cluster

### Documentation Gaps

- No contribution guidelines
- No testing documentation
- No development environment setup guide
- No CODEOWNERS file (though one exists on main branch, not on code branch)

---

## How to Validate Patches

### What Can Be Validated (Without Cluster)

1. **Syntax Validation:**
   ```bash
   bash -n convert.sh
   ```

2. **Help/Version Commands:**
   ```bash
   bash convert.sh --help
   bash convert.sh --version
   ```

3. **Prerequisite Checks:**
   ```bash
   bash convert.sh -i test-model  # Will fail on missing oc, but validates argument parsing
   ```

4. **Shellcheck (if installed):**
   ```bash
   shellcheck convert.sh
   ```

### What Cannot Be Validated (Requires Cluster)

1. Actual conversion of InferenceServices
2. RBAC resource creation
3. ServingRuntime transformations
4. Authentication resource processing
5. Owner reference handling
6. YAML transformation logic
7. Error handling for real failure scenarios

### Recommended Validation Workflow

For an AI agent validating patches to this repository:

1. **Always:**
   - Run `bash -n` syntax check
   - Test `--help` and `--version` commands
   - Check that prerequisite validation still works

2. **If shellcheck available:**
   - Run `shellcheck convert.sh` to catch common issues

3. **Manual review needed for:**
   - Changes to YAML transformation logic
   - Changes to resource creation
   - Changes to error handling
   - Changes to permission checks

4. **Cannot automate:**
   - End-to-end functional testing
   - Validation of actual KServe conversions
   - Testing of RBAC changes
   - Verification of owner references

---

## Dependencies

### Runtime Dependencies

- **oc** (OpenShift CLI): Required, not installable in standard container
- **yq** (v4.x+): YAML processor, installable via wget
- **jq** (v1.6+): JSON processor, installable via package manager

### System Requirements

- Bash 4.0+ (script uses modern bash features)
- OpenShift 4.x cluster access
- KServe installed on cluster
- Appropriate RBAC permissions (see README for details)

### Installation Commands

```bash
# Alpine/apk
apk add jq

# Download yq
wget -qO /usr/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
chmod +x /usr/bin/yq

# oc (OpenShift CLI)
# Must be downloaded from Red Hat or built from source
# See: https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html
```

---

## Agent Guidance

**For AI agents attempting to validate patches:**

1. **Set expectations:** This repository cannot be fully tested without cluster access.

2. **Focus on syntax:** Bash syntax validation is the primary automated check available.

3. **Recommend improvements:** Suggest adding:
   - shellcheck configuration
   - Basic unit tests with bats or shunit2
   - Mocking of `oc` commands for isolated testing
   - CI/CD workflow for syntax checking

4. **Manual review critical:** Changes to transformation logic, error handling, or resource management require human review with cluster access.

5. **Document assumptions:** When reviewing patches, document what can and cannot be validated automatically.

**Agent Readiness Rating Justification:**

- **LOW** because:
  - No automated test suite
  - Requires external infrastructure (OpenShift + KServe)
  - Cannot validate core functionality without cluster
  - No mocking or stubbing infrastructure
  - Only syntax-level validation possible

**To achieve MEDIUM readiness:**
- Add shellcheck to CI
- Add basic unit tests with mocks
- Add syntax validation workflow

**To achieve HIGH readiness:**
- Add comprehensive test suite with mocked `oc` commands
- Add integration tests with test fixtures
- Add CI/CD with automated checks
- Add test coverage reporting
