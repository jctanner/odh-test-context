# Test Context: kc-rep (opendatahub-io)

**Generated:** 2026-03-22T22:20:20Z

## Overview

**Repository Type:** Configuration-only meta-repository
**Languages:** YAML
**Primary Purpose:** Central storage for Tekton/Konflux CI pipeline configurations for OpenDataHub components
**Agent Readiness:** **none** — No test or lint infrastructure exists. This is a pure configuration repository with no validation tooling.

This repository contains 31 Tekton PipelineRun YAML files organized into component-specific directories. Each component directory (e.g., `data-science-pipelines/`, `odh-dashboard/`) contains a `.tekton/` subdirectory with pipeline definitions. The repository has no code, no tests, no linting, and no build process.

---

## Container Recipe

**This section is not applicable.** The repository contains only YAML configuration files with no executable code, tests, or build process. There is no container-based validation to perform.

### Theoretical Validation (Not Implemented)

If validation were to be added to this repository, it could include:

1. **YAML Syntax Validation**
   ```bash
   # Install yamllint
   pip install yamllint

   # Check all YAML files
   yamllint .
   ```

2. **Tekton Schema Validation**
   ```bash
   # Install tkn CLI
   # Download from https://github.com/tektoncd/cli/releases

   # Validate each Tekton pipeline
   find . -name "*.yaml" -path "*/.tekton/*" -exec tkn pipeline validate -f {} \;
   ```

However, **none of these validation tools are currently configured** in the repository.

---

## Validation Results

**No validation performed.** The repository has no test or lint infrastructure.

### What Would Need to Be Added

To make this repository suitable for automated patch validation, the following would need to be added:

1. **YAML Linting:**
   - Add `.yamllint` configuration file
   - Configure CI to run `yamllint .`
   - Example config:
     ```yaml
     extends: default
     rules:
       line-length:
         max: 120
         level: warning
       document-start: disable
     ```

2. **Tekton Schema Validation:**
   - Add Tekton CLI to CI
   - Validate all `.tekton/*.yaml` files against Tekton schema
   - Check for required fields, valid resource references, etc.

3. **Pre-commit Hooks:**
   - Add `.pre-commit-config.yaml`
   - Include YAML linting, trailing whitespace checks, etc.

4. **GitHub Actions CI:**
   - Add a validation workflow triggered on pull requests
   - Run YAML linting and Tekton validation
   - Make it a required check for merging

---

## CI/CD

### GitHub Actions

**Config File:** `.github/workflows/okc-replicator.yml`

**Trigger:** Manual (`workflow_dispatch` only)

**Purpose:** This workflow copies Tekton configuration files from this central repository to target component repositories. It does **not** perform any validation.

**Workflow Steps:**
1. Accepts inputs: target repository, release branch, version, and component folder
2. Checks out this repository
3. Copies `.tekton/` files from the specified component folder
4. Updates `output-image` tags with the new version using `sed`
5. Creates a branch in the target repository
6. Commits and pushes the updated Tekton files
7. Creates a pull request in the target repository

**Gating Checks:** None. This repository has no PR validation workflows.

**Advisory Checks:** None.

**Gap:** Pull requests to this repository are not automatically validated. Changes to Tekton YAML files could introduce syntax errors or schema violations without detection.

---

## Conventions

### Directory Structure

```
kc-rep/
├── .github/workflows/
│   └── okc-replicator.yml          # Manual replication workflow
├── {component-name}/                # One directory per ODH component
│   └── .tekton/
│       └── {component}-push.yaml   # Tekton PipelineRun definition
└── README.md
```

### Component Directories

The repository contains 27 component directories:
- `caikit-nlp/`
- `codeflare-operator/`
- `data-science-pipelines/`
- `data-science-pipelines-operator/`
- `fms-guardrails-hf-detector/`
- `fms-guardrails-orchestrator/`
- `fms-guardrails-regex-detector/`
- `kserve-agent/`
- `kserve-controller/`
- `kserve-router/`
- `kubeflow/`
- `kuberay/`
- `kueue/`
- `ml-metadata/`
- `modelmesh/`
- `modelmesh-runtime-adapter/`
- `modelmesh-serving/`
- `odh-dashboard/`
- `odh-feast-operator/`
- `odh-feature-server/`
- `odh-model-controller/`
- `odh-model-registry-operator/`
- `rest-proxy/`
- `ta-lmes-driver/`
- `training-operator/`
- `trustyai-vllm-orchestrator-gateway/`

### File Naming

Tekton pipeline files follow the pattern: `{component-name}-push.yaml`

Examples:
- `data-science-pipelines/.tekton/odh-ml-pipelines-api-server-v2-push.yaml`
- `odh-dashboard/.tekton/odh-dashboard-push.yaml`
- `kserve-controller/.tekton/kserve-controller-push.yaml`

### Tekton PipelineRun Structure

All Tekton files define a `PipelineRun` resource with:
- Metadata annotations for Konflux/Pipelines-as-Code
- Parameters: `git-url`, `revision`, `output-image`, `dockerfile`, `path-context`
- Pipeline spec using Konflux CI tasks (buildah, SBOM, security scans)
- The `output-image` parameter contains a version tag that gets updated by the replicator workflow

---

## Gaps & Caveats

### Critical Gaps

1. **No Validation Infrastructure**
   - YAML syntax errors could be committed without detection
   - Tekton schema violations would only be caught when pipelines are executed
   - No pre-merge validation of configuration changes

2. **No Linting**
   - No `yamllint` configuration
   - No pre-commit hooks
   - No CI validation of YAML formatting or style

3. **No Tests**
   - Configuration changes cannot be tested before merge
   - No dry-run validation of Tekton pipelines
   - No verification that sed patterns in the replicator workflow work correctly

4. **Manual Workflow Only**
   - The replicator workflow is manually triggered
   - No automated tests verify the workflow works before changes are merged
   - Workflow changes could break replication without detection

5. **No Required Status Checks**
   - Pull requests can be merged without any automated validation
   - Human review is the only quality gate

### What This Means for Agents

An AI agent attempting to validate patches to this repository has **no automated mechanisms** to determine if changes are correct. The agent would need to:

1. Manually parse YAML syntax (could use `pyyaml` or similar)
2. Validate against Tekton schema manually
3. Check that directory/file structure conventions are followed
4. Review the GitHub Actions workflow YAML for syntax errors

Without test infrastructure, the agent cannot provide confidence that changes are safe to merge beyond basic syntactic correctness.

### Recommendations

To make this repository agent-friendly, add:

1. **`.yamllint` configuration** with rules for YAML style
2. **Pre-commit hooks** for YAML validation and formatting
3. **GitHub Actions CI workflow** that runs on pull requests:
   - YAML linting
   - Tekton schema validation (using `tkn` CLI or kubeval)
   - Workflow syntax validation
4. **Required status checks** enforcement
5. **Documentation** of the expected Tekton PipelineRun structure

---

## Summary

**kc-rep** is a configuration management repository that centralizes Tekton pipeline definitions for 27 OpenDataHub components. It has **no test infrastructure, no linting, and no automated validation**. The single GitHub Actions workflow replicates configuration files to other repositories but does not validate them.

**Agent Readiness: none** — There is no infrastructure for an AI agent to validate patches beyond manual YAML parsing. The repository would require significant additions (yamllint, Tekton validation, CI workflows) before automated patch validation is feasible.

**Confidence: high** — The repository structure is simple and well-defined. The absence of validation infrastructure is clearly confirmed by the lack of configuration files, CI workflows, and test directories.
