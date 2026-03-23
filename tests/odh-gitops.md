# Test Context: odh-gitops

**Generated**: 2026-03-22T23:36:50Z
**Organization**: opendatahub-io
**Repository**: odh-gitops

---

## Overview

GitOps manifest repository for Open Data Hub using Kustomize overlays and Helm charts. Contains Kubernetes manifests, operator subscriptions, and Helm charts for deploying ODH/RHOAI components.

**Languages**: YAML, Helm charts, Kustomize, Shell scripts
**Build System**: GNU Make + Helm
**Agent Readiness**: **HIGH** - All lint and test commands validated successfully in container

This repository has excellent validation infrastructure. An agent can clone, modify manifests, and get clear pass/fail signals from linters and build validators.

---

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in an isolated container.

### Step 1: Start Container

```bash
podman run -d --name test-context-odh-gitops \
  -v $(pwd):/app:Z \
  -w /app \
  -e GOTOOLCHAIN=auto \
  golang:1.22 \
  sleep infinity
```

**Note**: Use `docker` instead of `podman` if podman is not available. The `GOTOOLCHAIN=auto` environment variable is critical - it allows Go to auto-download newer toolchains required by kustomize v5.8.0 and yq v4.49.2.

### Step 2: Install System Dependencies

```bash
podman exec test-context-odh-gitops bash -c "
  apt-get update && \
  apt-get install -y make curl python3 python3-pip git
"
```

### Step 3: Install Helm

```bash
podman exec test-context-odh-gitops bash -c "
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
"
```

### Step 4: Install Validation Tools

```bash
podman exec test-context-odh-gitops bash -c "
  cd /app && GOTOOLCHAIN=auto make tools
"
```

This installs:
- **kustomize** v5.8.0 (via go install, requires Go 1.24+, auto-downloaded)
- **kube-linter** v0.7.6 (downloaded binary)
- **yamllint** 1.37.1 (via pip)
- **yq** v4.49.2 (via go install, requires Go 1.24+, auto-downloaded)

**Expected output**: "All validation tools installed in /app/bin"
**Exit code**: 0

### Step 5: Run YAML Linting

```bash
podman exec test-context-odh-gitops bash -c "
  cd /app && make validate-yaml
"
```

**What it does**: Validates YAML syntax and formatting against `.yamllint.yaml` rules. Checks indentation (2 spaces), line length (max 180 chars), and YAML structure.

**Expected output**:
```
Validating YAML syntax...
./.tekton/pipelines/cluster-validation-pipeline.yaml
  212:181   warning  line too long (206 > 180 characters)  (line-length)

 YAML validation passed
```

**Exit code**: 0 (warnings are non-blocking)
**Validation status**: ✅ **PASS**

### Step 6: Run Kustomize Build Validation

```bash
podman exec test-context-odh-gitops bash -c "
  cd /app && make validate-kustomize
"
```

**What it does**: Attempts to build all kustomization.yaml files in the repository. This verifies that:
- All referenced resources exist
- No circular dependencies
- Patches apply correctly
- YAML is structurally valid for Kubernetes

**Expected output**:
```
Building all kustomizations...
  ✓ .
  ✓ components/operators/cert-manager
  ✓ components/operators/cluster-observability-operator
  [... 31 more kustomizations ...]
All kustomizations built successfully! ✓
```

**Total kustomizations**: 34
**Exit code**: 0
**Validation status**: ✅ **PASS**

### Step 7: Run Best Practices Linting

```bash
podman exec test-context-odh-gitops bash -c "
  cd /app && make validate-lint
"
```

**What it does**: Builds all manifests with Kustomize, then pipes output to kube-linter which checks for Kubernetes best practices and security issues:
- Privileged containers
- Unsafe sysctls
- Latest tags on images
- ClusterRoleBindings to system groups
- Wildcard rules in RBAC

**Expected output**:
```
Linting Kubernetes manifests...
KubeLinter 0.7.6

No lint errors found!
 Linting completed
```

**Exit code**: 0
**Validation status**: ✅ **PASS**

### Step 8: Run Helm Chart Snapshot Tests

```bash
podman exec test-context-odh-gitops bash -c "
  cd /app && make chart-test
"
```

**What it does**: For each Helm chart, runs `helm template` with various value combinations and compares output against golden snapshot files. This ensures chart changes don't unexpectedly modify generated manifests.

**Expected output**:
```
==============================================================================
Chart Snapshots - Testing
==============================================================================

Processing chart: odh-rhoai (7 snapshots)
----------------------------------------
  ==> default
      PASS
  ==> skip-crd-check-odh
      PASS
  ==> skip-crd-check-rhoai
      PASS
  ==> all-components-managed
      PASS
  ==> install-with-helm-dependencies
      PASS
  ==> inference-only
      PASS
  ==> enable-llm-d-wva
      PASS

Processing chart: rhaii-helm-chart (3 snapshots)
----------------------------------------
  ==> azure-with-related-images
      PASS
  ==> coreweave
      PASS
  ==> with-custom-namespacew
      PASS

==============================================================================
All snapshot tests passed!
==============================================================================
```

**Total snapshots**: 10 (7 for odh-rhoai, 3 for rhaii-helm-chart)
**Exit code**: 0
**Validation status**: ✅ **PASS**

### Step 9: Run All Validations (Combined)

```bash
podman exec test-context-odh-gitops bash -c "
  cd /app && make validate-all
"
```

**What it does**: Runs all validation checks in sequence: YAML lint → Kustomize build → Best practices lint

**Expected output**:
```
==========================================
 All validations passed successfully!
==========================================
```

**Exit code**: 0
**Validation status**: ✅ **PASS**

### Step 10: Cleanup

```bash
podman rm -f test-context-odh-gitops
```

Always cleanup the container when done, even if validation fails.

---

## Running Single Tests

### Test a Specific Helm Chart

```bash
podman exec test-context-odh-gitops bash -c "
  cd /app && make chart-test CHART_NAME=odh-rhoai
"
```

### Validate a Specific Kustomization Directory

```bash
podman exec test-context-odh-gitops bash -c "
  cd /app && bin/kustomize build components/operators/cert-manager
"
```

### Lint a Specific YAML File

```bash
podman exec test-context-odh-gitops bash -c "
  cd /app && bin/yamllint -c .yamllint.yaml path/to/file.yaml
"
```

---

## Validation Results

All validation commands were executed in a fresh container and passed successfully:

| Check | Command | Result | Notes |
|-------|---------|--------|-------|
| System Deps | `apt-get install make curl python3 git` | ✅ PASS | - |
| Helm Install | `curl ... \| bash` | ✅ PASS | v3.20.1 installed |
| Tool Install | `make tools` | ✅ PASS | Go auto-downloaded v1.25.8 for kustomize/yq |
| YAML Lint | `make validate-yaml` | ✅ PASS | 1 warning (line length, non-blocking) |
| Kustomize Build | `make validate-kustomize` | ✅ PASS | 34 kustomizations built |
| Best Practices | `make validate-lint` | ✅ PASS | 0 lint errors |
| Chart Tests | `make chart-test` | ✅ PASS | 10 snapshots passed |
| All Validations | `make validate-all` | ✅ PASS | Combined run succeeded |

### Validation Output Snippets

**YAML Lint** (1 warning, non-blocking):
```
./.tekton/pipelines/cluster-validation-pipeline.yaml
  212:181   warning  line too long (206 > 180 characters)
```

**Kustomize Build** (all passed):
```
  ✓ .
  ✓ components/operators/cert-manager
  ✓ dependencies/operators/rhcl-operator
  [... 31 more ...]
All kustomizations built successfully! ✓
```

**Best Practices Lint** (clean):
```
KubeLinter 0.7.6
No lint errors found!
```

**Chart Tests** (all 10 snapshots passed):
```
Processing chart: odh-rhoai (7 snapshots) - PASS
Processing chart: rhaii-helm-chart (3 snapshots) - PASS
All snapshot tests passed!
```

---

## CI/CD

### GitHub Actions Workflows

**`.github/workflows/testing.yaml`** - Runs on all PRs and pushes to main:
- ✅ YAML validation (`make validate-yaml`)
- ✅ Kustomize build validation (`make validate-kustomize`)
- ✅ Best practices linting (`make validate-lint`)
- All checks are **gating** (PR cannot merge if they fail)

**`.github/workflows/helm.yaml`** - Runs on changes to `charts/**`:
- ✅ Helm lint (`helm lint` for each chart)
- ✅ Chart-testing lint (`ct lint --config .github/configs/ct.yaml`)
- ✅ Helm chart snapshot tests (`make chart-test`)
- ✅ Helm documentation check (`make helm-docs` + git diff)
- All checks are **gating**

### Tekton Pipelines

Located in `.tekton/` directory:
- `cluster-validation-ocp-4.19.yaml`
- `cluster-validation-ocp-4.20.yaml`
- `helm-chart-validation-ocp-4.19.yaml`
- `pipelines/cluster-validation-pipeline.yaml`

**Note**: These require OpenShift cluster access and cannot be validated locally.

---

## Conventions

### File Organization

```
odh-gitops/
├── components/          # Kustomize components for operators
│   └── operators/       # Operator-specific manifests
├── configurations/      # Operator configurations (CRs)
├── dependencies/        # Base operator installations
├── charts/             # Helm charts
│   ├── odh-rhoai/      # Main umbrella chart
│   ├── rhaii-helm-chart/
│   └── dependencies/   # Dependency operator charts
└── scripts/            # Automation scripts
```

### YAML Style

- **Indentation**: 2 spaces (enforced by yamllint)
- **Line length**: Max 180 characters (warning at 181+)
- **Document start**: `---` not required
- **Truthy values**: `true`/`false`/`on`/`off`/`yes`/`no` allowed

### Kustomize Structure

- Each directory with `kustomization.yaml` must build cleanly
- Patches organized by purpose (components vs configurations)
- Base resources in `dependencies/`

### Helm Chart Conventions

- Charts follow standard Helm structure
- Test values in `charts/*/test/testValues.yaml`
- Snapshot tests in `charts/*/test/snapshots/*.snap.yaml`
- API docs auto-generated: `charts/*/api-docs.md`

---

## Gaps & Caveats

### What's Missing

1. **No unit tests** - This is a manifest repository. Validation is via linting and successful Kustomize/Helm builds, not traditional unit tests.

2. **Cluster-dependent validation** - Some Makefile targets require actual Kubernetes/OpenShift cluster:
   - `make apply`
   - `make helm-install-verify`
   - `make apply-and-verify-dependencies`
   - Tekton pipelines (`.tekton/`)

3. **No integration tests** - Full validation requires deploying to a cluster and verifying operators install correctly.

4. **Snapshot regeneration** - If Helm chart changes are intentional, snapshots must be regenerated with `make chart-snapshots` before tests pass.

### Known Quirks

- **Go version requirement**: kustomize v5.8.0 and yq v4.49.2 require Go 1.24+. The container must set `GOTOOLCHAIN=auto` to allow Go to auto-download newer toolchains when using golang:1.22 base image.

- **YAML lint warning**: One line in `.tekton/pipelines/cluster-validation-pipeline.yaml` exceeds 180 characters. This is intentional and non-blocking.

- **Helm separate install**: Unlike other tools installed via `make tools`, Helm must be installed separately (via package manager or install script).

### What Can Be Validated Without a Cluster

✅ YAML syntax
✅ Kustomize builds
✅ Kubernetes best practices (kube-linter)
✅ Helm chart templates
✅ Helm chart snapshot tests
❌ Operator installation
❌ Resource creation in cluster
❌ Integration between components

---

## How an Agent Should Use This

### For Patch Validation Workflow

1. **Clone repo** and navigate to it
2. **Apply patch** to modify manifests
3. **Start container** with recipe above (Step 1-4)
4. **Run validations**:
   - `make validate-all` (catches syntax, build, and lint issues)
   - `make chart-test` (if Helm charts modified)
5. **Interpret results**:
   - Exit code 0 = validation passed
   - Exit code != 0 = validation failed, check output for details
6. **Cleanup** container

### Exit Code Interpretation

- **Exit 0**: All validations passed - patch is safe to apply
- **Exit != 0 with YAML errors**: Syntax error or formatting issue
- **Exit != 0 with Kustomize errors**: Manifest build failed (missing resource, bad patch, etc.)
- **Exit != 0 with lint errors**: Best practice violation (security, deprecated API, etc.)
- **Exit != 0 with snapshot mismatch**: Helm chart template output changed unexpectedly

### Regenerating Snapshots (if needed)

If a patch intentionally changes Helm chart output:

```bash
podman exec test-context-odh-gitops bash -c "
  cd /app && make chart-snapshots
"
```

Then commit the updated `*.snap.yaml` files.

---

## Quick Reference

### Essential Commands

```bash
# Install all tools
make tools

# Run all validations
make validate-all

# Individual validations
make validate-yaml
make validate-kustomize
make validate-lint

# Helm chart testing
make chart-test
make chart-test CHART_NAME=odh-rhoai

# Regenerate snapshots
make chart-snapshots
```

### Tool Versions

- kustomize: v5.8.0
- kube-linter: v0.7.6
- yamllint: 1.37.1
- yq: v4.49.2
- helm: v3.20+ (installed separately)

### Config Files

- `.yamllint.yaml` - YAML linting rules
- `.kube-linter.yaml` - Kubernetes best practices checks
- `.github/configs/ct.yaml` - chart-testing configuration
- `scripts/snapshot-config.yaml` - Helm snapshot test configuration
- `Makefile` - All validation targets

---

## Summary

**odh-gitops** is a well-structured GitOps repository with excellent validation infrastructure. All lint and test commands execute successfully in a container without requiring cluster access. An agent can confidently validate patches by running the commands in the Container Recipe section and checking exit codes.

**Agent Readiness: HIGH** ✅

**Recommended validation command**: `make validate-all && make chart-test`
**Validation time**: ~60 seconds (after tools installed)
**Container cleanup**: Always run `podman rm -f test-context-odh-gitops`
