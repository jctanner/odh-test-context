# Test Context: sample-gam-trigger-workflow

## Overview

**Repository:** opendatahub-io/sample-gam-trigger-workflow
**Type:** Infrastructure/CI sample repository (GitHub Actions workflows)
**Languages:** YAML, Bash
**Agent Readiness:** **low** — This is a sample/demonstration repository with no test suite. Validation is limited to syntax checking of workflows and bash scripts. The workflows themselves require GitHub Actions infrastructure and secrets to execute.

This repository demonstrates how to trigger the Gated Auto Merger (GAM) workflow from other repositories using three different approaches. It contains no application code, no tests, and no build system - only GitHub Actions workflow examples and one bash script.

## Container Recipe

This repository has minimal validation capabilities. The following recipe validates syntax only.

### 1. Start Container

```bash
podman run -d --name test-context-sample-gam-trigger-workflow \
  -v $(pwd):/app:Z \
  -w /app \
  ubuntu:22.04 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-sample-gam-trigger-workflow bash -c \
  "apt-get update && apt-get install -y bash shellcheck python3-yaml"
```

### 3. Validate Bash Script with Shellcheck

```bash
podman exec test-context-sample-gam-trigger-workflow bash -c \
  "cd /app && shellcheck .github/scripts/custom_decider.sh"
```

**Validated:** ✅ Pass (exit code 0, no issues found)

### 4. Validate Bash Syntax

```bash
podman exec test-context-sample-gam-trigger-workflow bash -c \
  "cd /app && bash -n .github/scripts/custom_decider.sh"
```

**Validated:** ✅ Pass (exit code 0)

### 5. Validate YAML Syntax of Workflows

```bash
podman exec test-context-sample-gam-trigger-workflow bash -c \
  "cd /app && python3 -c \"import yaml; [yaml.safe_load(open(f)) for f in ['.github/workflows/trigger-gam.yaml', '.github/workflows/trigger-gam-with-gh-cli.yaml', '.github/workflows/trigger-gam-with-custom-decider.yaml']]; print('All workflow YAML files are valid')\""
```

**Validated:** ✅ Pass (exit code 0)

### 6. Execute Bash Script (Smoke Test)

```bash
podman exec test-context-sample-gam-trigger-workflow bash -c \
  "cd /app && .github/scripts/custom_decider.sh"
```

**Validated:** ✅ Pass (exit code 0, outputs random "true" or "false")

### 7. Cleanup

```bash
podman rm -f test-context-sample-gam-trigger-workflow
```

## Validation Results

All syntax validation passed:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install deps | apt-get install bash shellcheck python3-yaml | ✅ Pass | Tools installed successfully |
| Shellcheck | shellcheck .github/scripts/custom_decider.sh | ✅ Pass | No issues found |
| Bash syntax | bash -n .github/scripts/custom_decider.sh | ✅ Pass | Valid syntax |
| YAML syntax | python3 -c "import yaml; ..." | ✅ Pass | All workflows are valid YAML |
| Script execution | .github/scripts/custom_decider.sh | ✅ Pass | Runs successfully |

## CI/CD

**System:** GitHub Actions
**Config Files:**
- `.github/workflows/trigger-gam.yaml` — Simple workflow_call to GAM
- `.github/workflows/trigger-gam-with-gh-cli.yaml` — Uses gh CLI to trigger and monitor GAM
- `.github/workflows/trigger-gam-with-custom-decider.yaml` — Uses custom bash script to decide whether to trigger

**Trigger:** All workflows use `workflow_dispatch` (manual trigger only). Scheduled cron triggers are commented out.

**Gating Checks:** None. These are sample implementations, not gating checks.

**Infrastructure Requirements:**
- GitHub Actions environment
- Secrets: `APP_ID`, `PRIVATE_KEY` (for GitHub App authentication)
- Access to `red-hat-data-services/Gated-Auto-Merger` repository

**Workflow Behavior:**
1. **trigger-gam.yaml:** Directly calls the GAM reusable workflow, passing "Dashboard" as the component
2. **trigger-gam-with-gh-cli.yaml:** Uses GitHub CLI to trigger GAM programmatically, watches execution, and reports results
3. **trigger-gam-with-custom-decider.yaml:** Runs `.github/scripts/custom_decider.sh` to decide whether to trigger (currently returns random true/false)

## Conventions

- Workflows stored in `.github/workflows/`
- Scripts stored in `.github/scripts/`
- Bash scripts use `#!/bin/bash` shebang
- Workflows follow GitHub Actions YAML schema

## Gaps & Caveats

**Major Gaps:**
- ❌ No test suite (this is a sample/demo repository, not a production application)
- ❌ No linter configuration files (no `.shellcheckrc`, no `yamllint` config)
- ❌ No application code to test — only workflow configuration files
- ❌ No CI gating checks configured
- ❌ No build system or dependency management

**Validation Limitations:**
- Syntax validation only — cannot test workflow execution without GitHub Actions infrastructure
- The bash script's logic is trivial (random true/false) — no meaningful behavior to test
- Workflows require secrets and external repository access to function
- Cannot validate workflow correctness without running them in GitHub Actions

**What CAN Be Validated:**
- ✅ Bash script syntax (`bash -n`)
- ✅ Bash script linting (`shellcheck`)
- ✅ YAML syntax validation (Python yaml module)
- ✅ Script execution (smoke test only)

**Agent Use Case:**
This repository is unsuitable for traditional patch validation (lint + test). An agent can verify that:
1. Workflow YAML files are syntactically valid
2. Bash scripts pass shellcheck and have valid syntax
3. Scripts execute without runtime errors

An agent **cannot** verify that workflows function correctly, as they require GitHub Actions infrastructure, secrets, and access to external repositories.

## Recommended Approach for Patch Validation

For patches to this repository:

1. **Syntax Validation:** Run shellcheck and YAML validation (as shown in Container Recipe)
2. **Manual Review:** Workflows must be reviewed manually or tested in a GitHub Actions environment
3. **Consider:** Setting up actionlint for GitHub Actions workflow validation

## Notes

This is a **demonstration repository** showing how to integrate with the Gated Auto Merger (GAM) system. It is not a production application and intentionally has no tests. The repository serves as a reference implementation for other projects that want to trigger GAM workflows.
