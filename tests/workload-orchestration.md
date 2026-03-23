# Test Context: workload-orchestration

**Agent Readiness: LOW** — This is a documentation/demo repository with no test suite. Validation is limited to syntax checking and ensuring the update-readme script runs.

## Overview

- **Repository**: opendatahub-io/workload-orchestration
- **Languages**: Shell, YAML, Markdown
- **Build System**: Makefile (single target: `update-readme`)
- **Purpose**: Demo repository showcasing Kueue (Kubernetes workload orchestration) features
- **Test Suite**: None
- **CI/CD**: None

This repository contains:
- 3 demo scenarios with Kubernetes YAML manifests
- An `update-readme.sh` script that syncs YAML content into README files
- asciinema recordings (.cast files) demonstrating the scenarios

**Why Low Readiness**: No automated tests exist. The only validation possible is syntax checking and verifying the update-readme script executes. There's no way to test whether the Kubernetes manifests are valid without a live cluster.

---

## Container Recipe

This is a complete, step-by-step recipe for validating patches in an isolated container.

### 1. Start the container

```bash
podman run -d --name test-context-workload-orchestration \
  -v $(pwd):/app:Z \
  -w /app \
  bash:latest \
  sleep infinity
```

**Base image**: `bash:latest` (Alpine-based, includes GNU bash 5.3.9)

### 2. Install system dependencies

```bash
podman exec test-context-workload-orchestration bash -c \
  "apk add --no-cache make findutils grep sed gawk"
```

Required for the Makefile and update-readme.sh script.

### 3. Install linting tools (optional)

```bash
podman exec test-context-workload-orchestration bash -c \
  "apk add --no-cache python3 py3-pip && \
   pip3 install --break-system-packages yamllint"
```

### 4. Validate shell script syntax

```bash
podman exec test-context-workload-orchestration bash -c \
  "cd /app && bash -n hack/update_readme/update-readme.sh && echo 'Syntax OK'"
```

**Expected**: "Syntax OK"
**Validated**: ✅ Passed (exit code 0)

### 5. Run the update-readme script

```bash
podman exec test-context-workload-orchestration bash -c \
  "cd /app && make update-readme"
```

**Expected**: Exit code 0, processes YAML files and updates READMEs
**Validated**: ✅ Passed (processed 24 YAML files across 3 demos)

### 6. Run YAML linting

```bash
podman exec test-context-workload-orchestration bash -c \
  "cd /app && yamllint demos/"
```

**Expected**: Warnings for style (missing document-start markers) but no errors
**Validated**: ✅ Passed (exit 0, found style warnings only)

### 7. Cleanup

```bash
podman rm -f test-context-workload-orchestration
```

---

## Validation Results

### ✅ Shell Script Syntax Check
- **Command**: `bash -n hack/update_readme/update-readme.sh`
- **Result**: Passed
- **Output**: "Syntax OK"

### ✅ Make Update-Readme
- **Command**: `make update-readme`
- **Result**: Passed (exit 0)
- **Notes**: Successfully processed 24 YAML files from 3 demo directories

### ✅ YAML Linting
- **Command**: `yamllint demos/`
- **Result**: Passed (exit 0)
- **Warnings Found**:
  - Missing document-start markers (`---`) in most YAML files
  - Minor comment spacing issues
- **Notes**: These are style warnings, not syntax errors. YAML is valid.

---

## CI/CD

**Status**: No CI/CD configuration found

**Gaps**:
- No GitHub Actions workflows
- No automated validation on pull requests
- No branch protection requirements
- No other CI systems detected (.gitlab-ci.yml, Jenkinsfile, etc.)

**Recommendation**: At minimum, could add a GitHub Actions workflow to:
1. Run shellcheck on the update-readme.sh script
2. Run yamllint on YAML files
3. Execute `make update-readme` to verify it doesn't fail
4. Check that READMEs are in sync (git diff after running update-readme)

---

## Conventions

### Repository Structure
```
demos/
  {demo-name}/
    README.md              # Documentation with embedded YAML
    resources/             # Kubernetes manifest files
      *.yaml              # Individual resource definitions
    *.cast                # asciinema recording
```

### README-YAML Sync Pattern
READMEs use special markers to embed YAML content:
```markdown
<!-- YAML-START: demos/example/resources/file.yaml -->
<!-- YAML-END -->
```

The `make update-readme` command populates these blocks with actual YAML content from the referenced files.

### Demo Conventions
- Each demo demonstrates a specific Kueue feature
- YAMLs are standard Kubernetes resources (Namespaces, Jobs, Kueue CRDs)
- Demos are designed to run on a Kubernetes cluster with Kueue installed

---

## Gaps & Caveats

### 1. No Test Suite
**Impact**: Cannot validate functional correctness of patches
**What's Missing**:
- No unit tests for the shell script
- No integration tests for the Makefile
- No validation of YAML semantic correctness (only syntax)

### 2. No CI/CD
**Impact**: No automated validation on pull requests
**What's Missing**:
- GitHub Actions workflows
- Automated linting
- Automated README sync verification

### 3. No Linting Configuration
**Impact**: Inconsistent style, potential for errors
**What's Missing**:
- `.yamllint` configuration file
- `.shellcheckrc` configuration
- Pre-commit hooks

### 4. Cannot Validate Demos Actually Work
**Impact**: YAML may be syntactically valid but semantically broken
**What's Missing**:
- Access to a Kubernetes cluster with Kueue installed
- Automated tests that apply manifests and verify behavior
- Integration testing infrastructure

### 5. No Contribution Guidelines
**Impact**: Contributors don't know the expected workflow
**What's Missing**:
- CONTRIBUTING.md
- PR template
- Developer documentation

---

## Recommendations for Agents

### What an Agent CAN Do
✅ Validate shell script syntax with `bash -n`
✅ Run `make update-readme` to ensure it executes
✅ Lint YAML files with yamllint
✅ Check that README markers are properly formatted
✅ Verify basic file structure conventions

### What an Agent CANNOT Do
❌ Test that Kubernetes manifests are semantically correct
❌ Verify demos actually work (requires live cluster)
❌ Run automated tests (none exist)
❌ Check against CI/CD gating criteria (no CI configured)

### Validation Strategy for Patches

For a patch that modifies:

**Shell scripts** (`hack/update_readme/update-readme.sh`):
1. Run syntax check: `bash -n hack/update_readme/update-readme.sh`
2. Execute: `make update-readme` (should exit 0)
3. Consider running shellcheck if available

**YAML files** (`demos/*/resources/*.yaml`):
1. Run yamllint: `yamllint {changed-file}`
2. Verify YAML is valid (can be parsed)
3. Run `make update-readme` to sync into READMEs
4. Check git diff to ensure READMEs updated correctly

**README files** (`demos/*/README.md`):
1. Verify markers are intact: `<!-- YAML-START: ... -->` / `<!-- YAML-END -->`
2. Run `make update-readme` to re-sync
3. Check that manual edits outside YAML blocks are preserved

**Makefile**:
1. Verify syntax (make will parse it)
2. Test target execution: `make update-readme`

---

## Quick Start for Validation

```bash
# Clone and enter repo
cd workload-orchestration

# Start container
podman run -d --rm --name test-wo \
  -v $(pwd):/app:Z -w /app bash:latest sleep infinity

# Install dependencies
podman exec test-wo apk add --no-cache make findutils grep sed gawk python3 py3-pip
podman exec test-wo pip3 install --break-system-packages yamllint

# Run validations
podman exec test-wo bash -n hack/update_readme/update-readme.sh
podman exec test-wo make update-readme
podman exec test-wo yamllint demos/

# Cleanup
podman rm -f test-wo
```

**Expected outcome**: All commands exit 0 (yamllint may show warnings, which is OK)

---

## Summary

This is a **documentation repository** with minimal automation. It exists to showcase Kueue demos, not to provide production code. The only meaningful validation is ensuring:

1. The update-readme script runs without errors
2. Shell syntax is valid
3. YAML syntax is valid

There is **no functional test suite**, so agents cannot verify that patches maintain correctness beyond syntax. The agent readiness rating is **LOW** because validation is limited to syntax checking.

For downstream agents: treat this as a documentation repo. Focus on ensuring scripts run and files are well-formed, but don't expect to validate functional behavior.
