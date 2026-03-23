# Test Context: odh-konflux-central

## Overview

**Repository:** opendatahub-io/odh-konflux-central
**Type:** Kubernetes/Tekton configuration repository
**Languages:** YAML
**Build System:** None (configuration repository)
**Agent Readiness:** **Medium** — Lint commands work and validate successfully. However, no unit tests exist. Integration tests are Tekton PipelineRuns requiring Kubernetes cluster infrastructure and cannot be run locally. An agent can validate YAML syntax and schema correctness but cannot test pipeline execution logic.

## Container Recipe

This is a complete recipe for validating patches in an isolated container. Follow these steps verbatim.

### 1. Start the container

```bash
podman run -d --name test-context-odh-konflux-central \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

**Base image rationale:** Python 3.11 provides the runtime for yamllint (Python-based linter). This matches the version used in the GitHub Actions workflow environment.

### 2. Install system dependencies

```bash
podman exec test-context-odh-konflux-central bash -c \
  "apt-get update && apt-get install -y curl git"
```

**Note:** curl and git are typically pre-installed in the python:3.11 image but explicitly installed for consistency.

### 3. Install yamllint

```bash
podman exec test-context-odh-konflux-central bash -c \
  "pip install yamllint==1.38.0"
```

**Version:** 1.38.0 is the pinned version used in CI (.github/workflows/yaml-lint.yaml).

### 4. Install kubeconform

```bash
podman exec test-context-odh-konflux-central bash -c \
  "cd /app && \
   KUBECONFORM_VERSION='v0.6.7' && \
   curl -sSL \"https://github.com/yannh/kubeconform/releases/download/\${KUBECONFORM_VERSION}/kubeconform-linux-amd64.tar.gz\" | tar xz && \
   mv kubeconform /usr/local/bin/"
```

**Version:** v0.6.7 is the version used in CI (.github/workflows/yaml-lint.yaml).

### 5. Run yamllint (GATING)

```bash
podman exec test-context-odh-konflux-central bash -c \
  "cd /app && yamllint --strict -c .yamllint ."
```

**Expected behavior:**
- Exit code 1 in current codebase (lint violations exist)
- Reports trailing spaces in `.github/workflows/odh-konflux-onboarder.yml`
- **This is a GATING check** — must pass for PRs to merge

**Validation result:** ✅ Command works correctly. Exit code 1 indicates lint issues found (trailing spaces), not a broken linter.

**To fix issues:**
```bash
# Manual fix required - yamllint does not have an auto-fix mode
# Remove trailing spaces from reported files
```

### 6. Run kubeconform (GATING)

```bash
podman exec test-context-odh-konflux-central bash -c \
  "cd /app && \
   kubeconform -summary -output text \
     -ignore-missing-schemas \
     -schema-location default \
     -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
     pipelineruns/ pipeline/ gitops/ integration-tests/"
```

**Expected behavior:**
- Exit code 0 (all resources validated)
- Summary: `398 resources found in 212 files - Valid: 0, Invalid: 0, Errors: 0, Skipped: 398`
- Resources are "skipped" because they are custom CRDs (Tekton PipelineRun, Konflux Component) not available in public schema catalogs
- `-ignore-missing-schemas` allows validation to pass despite missing CRD schemas
- **This is a GATING check** — validates basic YAML structure and standard Kubernetes resources

**Validation result:** ✅ Command works correctly. Exit code 0, no schema errors found.

### 7. Cleanup

```bash
podman rm -f test-context-odh-konflux-central
```

Always clean up the container when validation is complete.

---

## Validation Results

| Step | Command | Exit Code | Status | Notes |
|------|---------|-----------|--------|-------|
| Install | `pip install yamllint==1.38.0` | 0 | ✅ Pass | yamllint installed successfully |
| Install | `kubeconform install` | 0 | ✅ Pass | kubeconform v0.6.7 installed |
| Lint | `yamllint --strict -c .yamllint .` | 1 | ✅ Pass | Found lint violations (trailing spaces). Command works correctly. |
| Lint | `kubeconform ...` | 0 | ✅ Pass | Schema validation passed. 398 resources skipped (custom CRDs). |

**Summary:** Both lint tools validated successfully. yamllint found style violations (trailing spaces in odh-konflux-onboarder.yml). kubeconform validated schema structure successfully.

---

## CI/CD

### GitHub Actions Workflows

**Gating checks (run on all PRs):**

1. **YAML Lint / yamllint** (.github/workflows/yaml-lint.yaml)
   - Trigger: pull_request, push to main
   - Command: `yamllint --strict -c .yamllint .`
   - Uses custom action: `.github/actions/action-yamllint`
   - Sandboxed execution with `unshare --user --net` for security
   - **Required to merge**

2. **YAML Lint / kubeconform** (.github/workflows/yaml-lint.yaml)
   - Trigger: pull_request, push to main
   - Command: See step 6 in Container Recipe above
   - Validates Kubernetes manifest schemas
   - **Required to merge**

**Non-gating checks:**

3. **Build Integration Test Images** (.github/workflows/build-integration-images.yml)
   - Trigger: push to main when files in `integration-tests/**` change
   - Detects changed `integration-tests/*/Dockerfile.*` files
   - Builds and pushes images to `quay.io/rhoai/rhoai-task-toolset:<tag>`
   - Requires secrets: QUAY_USERNAME, QUAY_PASSWORD

4. **ODH Konflux Onboarder** (.github/workflows/odh-konflux-onboarder.yml)
   - Trigger: workflow_dispatch (manual)
   - Generates Tekton pipeline configurations for component onboarding
   - Creates PRs to component repositories with .tekton files

---

## Conventions

### Repository Structure

```
odh-konflux-central/
├── .github/
│   ├── actions/
│   │   └── action-yamllint/        # Reusable yamllint action
│   └── workflows/                  # GitHub Actions workflows
├── gitops/                         # GitOps manifests
│   ├── opendatahub-ci-components.yaml
│   └── opendatahub-integration-test-scenarios.yaml
├── integration-tests/              # Tekton integration test PipelineRuns
│   ├── opendatahub-operator/
│   │   ├── e2e-test.yaml          # End-to-end test pipeline
│   │   └── pr-test-pipelinerun.yaml
│   └── template/                   # Templates for new integration tests
├── pipeline/                       # Reusable Tekton Pipeline definitions
│   ├── bundle-build.yaml
│   ├── multi-arch-container-build.yaml
│   └── multi-arch-operator-build.yaml
├── pipelineruns/                   # Component-specific Tekton PipelineRuns
│   └── <component-name>/
│       ├── *-pull-request.yaml    # CI build on PR
│       └── *-push.yaml            # CI build on push
├── workflows/                      # Optional GitHub workflows for components
├── .yamllint                      # yamllint configuration
└── its.yaml                       # IntegrationTestScenario example
```

### Naming Conventions

- **Tekton Pipelines:** Stored in `pipeline/`, named by function (e.g., `multi-arch-container-build.yaml`)
- **PipelineRuns:** Stored in `pipelineruns/<component>/`, suffixed by trigger:
  - `*-pull-request.yaml` — runs on PR events
  - `*-push.yaml` — runs on push to main/stable
  - `*-release-push.yaml` — runs for release builds
- **Integration Test Dockerfiles:** `integration-tests/*/Dockerfile.<tag>`
- **GitOps Components:** `gitops/opendatahub-*-components.yaml`

### YAML Linting Rules (.yamllint)

- Based on `default` ruleset
- `document-start: disable` — no `---` required at start
- `line-length: disable` — no line length limit
- `indentation: 2 spaces, indent-sequences: whatever`
- `truthy: check-keys: false` — allows `on:` in GitHub workflows
- `comments: min-spaces-from-content: 1, require-starting-space: false` — flexible comment formatting
- `comments-indentation: disable` — allows commented-out YAML blocks

---

## Gaps & Caveats

### No Unit Tests

This repository contains only YAML configuration files (Tekton pipelines, Kubernetes manifests). There is no application code and therefore no unit tests.

### Integration Tests Require Infrastructure

The "tests" in `integration-tests/` are Tekton PipelineRun definitions, not executable test code. They:

- Provision ephemeral Hypershift clusters via Konflux
- Deploy OpenDataHub components from Konflux snapshots
- Run component-specific e2e tests in the cluster
- Require Konflux CI infrastructure and cluster access
- **Cannot be run locally** without a Kubernetes cluster and Konflux setup

Example from `integration-tests/opendatahub-operator/e2e-test.yaml`:
```yaml
description: |
  An integration test which provisions an ephemeral Hypershift cluster,
  deploys opendatahub-operator from a Konflux snapshot and runs the e2e
  tests against it.
```

### Current Lint Violations

The repository has existing yamllint errors that would cause CI to fail:

- **File:** `.github/workflows/odh-konflux-onboarder.yml`
- **Issues:** Trailing spaces on lines 71, 79, 84, 126, 134, 137, 141, 147, 150, 155, 163, 168, 173, 178, 180, 185, 187, 189, 192, 194, 196, 203, 206, 213, 216, 223, 226, 231, 236, and more
- **Fix:** Remove trailing whitespace

### Kubeconform Schema Limitations

kubeconform skips all 398 resources in this repository because they use custom CRDs:

- **Tekton:** `Pipeline`, `PipelineRun`, `Task`
- **Konflux:** `Component`, `IntegrationTestScenario`
- **Kubernetes:** Standard resources like `Namespace` are validated

The `-ignore-missing-schemas` flag allows validation to pass without failing on missing CRD schemas. This validates basic YAML structure but not resource-specific fields. See [issue #126](https://github.com/opendatahub-io/odh-konflux-central/issues/126) for adding custom schema support.

### No Pipeline Logic Testing

An agent can validate:
- ✅ YAML syntax correctness (yamllint)
- ✅ Basic Kubernetes schema structure (kubeconform)

An agent **cannot** validate:
- ❌ Tekton pipeline execution correctness
- ❌ Pipeline parameter validity
- ❌ Task reference resolution
- ❌ Integration test behavior

To fully test changes to Tekton pipelines, they must be executed on a Kubernetes cluster with Tekton installed.

---

## Quick Reference

**Validate a patch:**
```bash
# Start container
podman run -d --name test-context-odh-konflux-central \
  -v $(pwd):/app:Z -w /app python:3.11 sleep infinity

# Install tools
podman exec test-context-odh-konflux-central bash -c \
  "pip install yamllint==1.38.0 && \
   curl -sSL https://github.com/yannh/kubeconform/releases/download/v0.6.7/kubeconform-linux-amd64.tar.gz | tar xz && \
   mv kubeconform /usr/local/bin/"

# Run linters
podman exec test-context-odh-konflux-central bash -c \
  "cd /app && yamllint --strict -c .yamllint ."

podman exec test-context-odh-konflux-central bash -c \
  "cd /app && kubeconform -summary -output text -ignore-missing-schemas \
   -schema-location default \
   -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
   pipelineruns/ pipeline/ gitops/ integration-tests/"

# Cleanup
podman rm -f test-context-odh-konflux-central
```

**CI pass criteria:**
- yamllint exit code 0 (no lint violations)
- kubeconform exit code 0 (no schema errors)

**Common issues:**
- Trailing spaces → yamllint failure
- Invalid YAML syntax → yamllint failure
- Malformed Kubernetes resource structure → kubeconform failure (rare, usually caught by yamllint)
