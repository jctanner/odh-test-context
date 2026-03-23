# Test Context: community-operators-prod

**Agent Readiness: LOW** — This is a Kubernetes operator manifest catalog, not a code repository. Validation requires specialized tools (opm, operator-sdk) and external infrastructure (Kubernetes cluster, external CI pipelines). Local validation is limited to static checks.

---

## Overview

**Repository:** opendatahub-io/community-operators-prod
**Type:** Kubernetes Operator Catalog (YAML manifests)
**Languages:** YAML
**Build System:** make + opm (Operator Package Manager)
**Primary Content:** 300+ OLM (Operator Lifecycle Manager) operator bundles

This repository is a catalog of Kubernetes operator manifests for OpenShift/OKD, not application source code. It contains YAML files defining operator bundles (CRDs, CSVs, metadata) that are consumed by OLM to deploy operators on Kubernetes clusters.

**Key Insight:** Traditional linting/testing does not apply. Validation happens via:
1. **opm validate** - Static validation of File-Based Catalogs (FBC)
2. **operator-sdk scorecard** - OLM bundle compliance tests (requires K8s cluster)
3. **External CI pipelines** - Full validation via redhat-openshift-ecosystem/operator-pipelines

---

## Container Recipe

**⚠️ WARNING:** This repository cannot be fully validated in a simple container. Scorecard tests require a Kubernetes cluster. OPM validation requires catalog generation which needs operator-specific configuration.

### What CAN be validated locally:

1. **YAML syntax validation** (basic file parsing)
2. **Manifest structure inspection** (checking bundle completeness)
3. **OPM catalog validation** (if catalogs are pre-generated)

### What CANNOT be validated locally without infrastructure:

1. **Scorecard tests** - require Kubernetes cluster
2. **Operator deployability** - requires OLM on K8s
3. **External pipeline checks** - require operator-pipelines infrastructure

### Minimal Validation Container Recipe

This recipe demonstrates YAML validation and basic manifest inspection:

#### Step 1: Start Container

```bash
podman run -d --name test-context-community-operators \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11-slim \
  sleep infinity
```

#### Step 2: Install System Dependencies

```bash
podman exec test-context-community-operators bash -c "
  apt-get update && \
  apt-get install -y curl git make
"
```

#### Step 3: Install Python Tools for YAML Validation

```bash
podman exec test-context-community-operators bash -c "
  pip install --no-cache-dir pyyaml yamllint
"
```

#### Step 4: Validate YAML Syntax

```bash
# Validate YAML files can be parsed
podman exec test-context-community-operators bash -c "
  python3 -c '
import yaml
import sys
from pathlib import Path

errors = []
for yaml_file in Path(\"operators\").rglob(\"*.yaml\"):
    try:
        with open(yaml_file) as f:
            yaml.safe_load(f)
    except Exception as e:
        errors.append(f\"{yaml_file}: {e}\")

if errors:
    print(\"\\n\".join(errors[:20]))  # First 20 errors
    sys.exit(1)
else:
    print(f\"✅ All YAML files are syntactically valid\")
'
"
```

**Expected Result:** All YAML files should parse without syntax errors.

#### Step 5: Check Operator Bundle Structure

```bash
# Verify operator bundles have required directories
podman exec test-context-community-operators bash -c "
  python3 -c '
from pathlib import Path
import sys

operators = [d for d in Path(\"operators\").iterdir() if d.is_dir()]
incomplete = []

for op in operators:
    versions = [v for v in op.iterdir() if v.is_dir() and v.name[0].isdigit()]
    for version in versions:
        if not (version / \"manifests\").exists():
            incomplete.append(f\"{op.name}/{version.name}: missing manifests/\")
        if not (version / \"metadata\").exists():
            incomplete.append(f\"{op.name}/{version.name}: missing metadata/\")

if incomplete:
    print(f\"⚠️  Found {len(incomplete)} incomplete bundles\")
    print(\"\\n\".join(incomplete[:10]))
else:
    print(f\"✅ All operator bundles have manifests/ and metadata/ directories\")
'
"
```

**Expected Result:** All version directories should have manifests/ and metadata/ subdirectories.

#### Step 6: Install OPM (for catalog validation)

```bash
podman exec test-context-community-operators bash -c "
  mkdir -p /tmp/bin && cd /tmp/bin && \
  curl -sLO https://github.com/operator-framework/operator-registry/releases/download/v1.46.0/linux-amd64-opm && \
  chmod +x linux-amd64-opm && \
  mv linux-amd64-opm opm && \
  export PATH=/tmp/bin:\$PATH && \
  opm version
"
```

**Expected Result:** OPM version v1.46.0 (or similar) is displayed.

#### Step 7: Attempt Catalog Validation (LIMITED)

```bash
# This will only work if catalogs/ directory exists and is populated
podman exec test-context-community-operators bash -c "
  export PATH=/tmp/bin:\$PATH
  if [ -d catalogs ]; then
    find catalogs -type d -maxdepth 2 -name 'opendatahub-operator' | while read catalog; do
      echo \"Validating \$catalog...\"
      opm validate \$(dirname \$catalog) && echo \"✅ \$catalog valid\" || echo \"❌ \$catalog invalid\"
    done
  else
    echo \"⚠️  catalogs/ directory not found - run 'make catalogs' in operator directory first\"
  fi
"
```

**Expected Result:** If catalogs exist, they should pass `opm validate`. Otherwise, this step shows that catalogs need to be generated.

#### Step 8: Cleanup

```bash
podman rm -f test-context-community-operators
```

---

## Validation Results

### ✅ Repository Structure Analysis

**Command:** Manual exploration of directory structure
**Result:** Success
**Output:**
```
Repository contains 300+ operators in operators/ directory:
- 3scale-community-operator
- ack-* (AWS Controllers for Kubernetes)
- opendatahub-operator
- postgresql
- victoriametrics-operator
- (many others)

Each operator has version directories with manifests/, metadata/, and optional tests/
No traditional code files (Python, Go, JavaScript) found
GitHub workflows only handle administrative tasks (labels, stale issues)
```
**Interpretation:** This is a manifest catalog, not a code repository.

---

### ⚠️ OPM Validation (Requires Generated Catalogs)

**Command:** `opm validate <catalog_dir>`
**Result:** Not validated - catalogs not pre-generated
**Notes:**
- Catalogs must be generated first via `make catalogs` in operator directory
- Requires operator-specific ci.yaml configuration
- opendatahub-operator has Makefile supporting catalog generation
- Not all operators have Makefiles

**To generate catalogs for opendatahub-operator:**
```bash
cd operators/opendatahub-operator
make catalogs
make validate-catalogs
```

---

### ⚠️ Scorecard Tests (Requires Kubernetes Cluster)

**Command:** `operator-sdk scorecard <bundle-path>`
**Result:** Not validated - requires K8s cluster
**Configuration:** operators/opendatahub-operator/2.35.0/tests/scorecard/config.yaml

**Scorecard Test Suites:**
1. **basic-check-spec** - Validates spec structure
2. **olm-bundle-validation** - Validates OLM bundle format
3. **olm-crds-have-validation** - CRDs have OpenAPI v3 validation
4. **olm-crds-have-resources** - CRDs specify resources
5. **olm-spec-descriptors** - CSV has spec descriptors
6. **olm-status-descriptors** - CSV has status descriptors

**To run scorecard tests:**
```bash
# Requires: operator-sdk installed, Kubernetes cluster running
operator-sdk scorecard operators/opendatahub-operator/2.35.0
```

---

## CI/CD

### External Pipeline System

**Primary CI:** redhat-openshift-ecosystem/operator-pipelines
**Trigger:** Pull requests to this repository
**Status:** External - not visible in this repository's GitHub Actions

### GitHub Actions (Administrative Only)

**Workflow: pr-label-command.yml**
- Trigger: issue_comment (PR comments)
- Action: Manages PR labels via commands
- Uses: redhat-openshift-ecosystem/github-workflows/.github/workflows/label-command.yml@main
- Gating: No (administrative)

**Workflow: stale_issues.yaml**
- Trigger: Scheduled (daily at 1:30 AM UTC)
- Action: Marks inactive issues/PRs as stale, closes after timeout
- Gating: No (housekeeping)

### External Pipeline Checks (Gating)

These checks run in the operator-pipelines system when a PR is created:

1. **DeployableByOLM** - Verifies operator bundle can be deployed via OLM on OpenShift
2. **check_dangling_bundles** - Ensures no orphaned operator versions
3. **check_operator_name** - Validates naming conventions
4. **preflight-trigger** - Red Hat certification checks

**Configuration:** config.yaml (repository level) + operators/<name>/ci.yaml (operator level)

**Example ci.yaml (opendatahub-operator):**
```yaml
fbc:
  enabled: true
  catalog_mapping:
    - catalog_names: ["v4.19","v4.20"]
      template_name: basic-template.yaml
      type: olm.template.basic
reviewers:
  - zdtsw
  - grdryn
  - MarianMacik
```

---

## Conventions

### Operator Bundle Structure

```
operators/
├── <operator-name>/
│   ├── ci.yaml                    # Operator-level CI config
│   ├── Makefile                   # Optional: catalog generation
│   ├── <version>/
│   │   ├── manifests/
│   │   │   ├── <operator>.clusterserviceversion.yaml
│   │   │   └── <crd-files>.yaml
│   │   ├── metadata/
│   │   │   └── annotations.yaml
│   │   └── tests/                 # Optional
│   │       └── scorecard/
│   │           └── config.yaml
```

### Naming Conventions

- **Operator directories:** lowercase with hyphens (e.g., `opendatahub-operator`)
- **Version directories:** semver format (`2.35.0`) or date-based (`2025.01.15`)
- **CSV files:** `<operator-name>.clusterserviceversion.yaml`
- **CRD files:** `<api-group>_<plural>.yaml` (e.g., `datasciencecluster.opendatahub.io_datascienceclusters.yaml`)

### File Types

- **ClusterServiceVersion (CSV):** Operator metadata, deployment spec, permissions
- **CustomResourceDefinition (CRD):** API schema for custom resources
- **annotations.yaml:** OLM metadata (package name, default channel, etc.)
- **scorecard config.yaml:** Test suite definitions

---

## Gaps & Caveats

### Critical Limitations

1. **No local CI workflow** - All gating validation happens in external pipelines (operator-pipelines). GitHub Actions in this repo are administrative only.

2. **Requires Kubernetes cluster** - Scorecard tests and operator deployment testing cannot run in a simple container. Need Kind, Minikube, or full K8s cluster.

3. **No YAML linting** - No .yamllint, pre-commit hooks, or automated YAML style checking configured.

4. **Catalog generation is operator-specific** - Only some operators (like opendatahub-operator, 3scale-community-operator) have Makefiles. Many operators are manifest-only with no local tooling.

5. **External dependencies** - Full validation requires:
   - OLM installed on cluster
   - Operator images available in registries
   - Network access to pull operator bundles
   - Red Hat certification infrastructure (for preflight checks)

6. **Documentation gap** - README points to external pipeline docs. Local validation steps are not documented in this repository.

### What Can Be Done Locally (Summary)

✅ **Can validate:**
- YAML syntax (Python yaml.safe_load)
- Bundle structure completeness (manifests/, metadata/ exist)
- CSV and CRD schema validation (against OLM schemas)
- OPM catalog validation (if catalogs are generated)

❌ **Cannot validate without infrastructure:**
- Operator deployability on cluster
- Scorecard tests (need K8s)
- Preflight certification checks
- Multi-version upgrade paths
- Actual operator functionality

### Recommendations for Agents

**For manifest-only changes (YAML edits):**
1. Validate YAML syntax with Python yaml or yamllint
2. Check bundle structure completeness
3. Verify CSV/CRD follow OLM schemas
4. Flag for human review - external pipeline will do full validation

**For new operator submissions:**
1. Cannot validate locally without full operator-pipelines setup
2. Verify bundle structure and naming conventions
3. Check ci.yaml is properly configured
4. Flag for human review and external CI validation

**Agent readiness: LOW** because most meaningful validation requires infrastructure not available in a simple container environment.

---

## Example: Validating a Patch to opendatahub-operator

Suppose an agent needs to validate a patch that updates the opendatahub-operator CSV:

### Step 1: Apply the patch
```bash
# Patch is applied to operators/opendatahub-operator/2.35.0/manifests/*.yaml
```

### Step 2: Validate YAML syntax
```bash
python3 -c "
import yaml
with open('operators/opendatahub-operator/2.35.0/manifests/opendatahub-operator.clusterserviceversion.yaml') as f:
    yaml.safe_load(f)
print('✅ CSV is valid YAML')
"
```

### Step 3: Verify bundle structure unchanged
```bash
ls operators/opendatahub-operator/2.35.0/manifests/
ls operators/opendatahub-operator/2.35.0/metadata/
# Ensure manifests/ and metadata/ still exist and contain expected files
```

### Step 4: Flag for external CI
```bash
# Agent would note:
# - YAML syntax is valid
# - Bundle structure is intact
# - Full validation requires external pipeline (DeployableByOLM, scorecard)
# - Recommend: Create PR and let operator-pipelines validate
```

---

## Tools Reference

### OPM (Operator Package Manager)

**Purpose:** Validate and manipulate operator catalogs
**Install:** https://github.com/operator-framework/operator-registry/releases
**Version in Makefile:** v1.46.0
**Usage:**
```bash
opm validate <catalog_dir>
opm alpha render <catalog_template>
```

### operator-sdk

**Purpose:** Operator development and testing toolkit
**Install:** https://sdk.operatorframework.io/docs/installation/
**Usage:**
```bash
operator-sdk scorecard <bundle_dir>
operator-sdk bundle validate <bundle_dir>
```

### yq

**Purpose:** YAML processing
**Install:** https://github.com/mikefarah/yq
**Version in Makefile:** v4.45.1
**Usage:** Used in Makefile scripts for catalog generation

---

## External References

- **Operator Pipeline Docs:** https://redhat-openshift-ecosystem.github.io/operator-pipelines/
- **OLM Documentation:** https://olm.operatorframework.io/
- **Contributing Guide:** See links in README.md
- **Operator SDK:** https://sdk.operatorframework.io/

---

## Summary for Downstream Agents

**Repository Type:** Kubernetes operator manifest catalog (not code)
**Local Validation Capability:** Very limited - YAML syntax and structure checks only
**Full Validation:** Requires external operator-pipelines infrastructure
**Agent Strategy:**
- For YAML edits: Validate syntax and structure, then flag for pipeline validation
- For new operators: Verify bundle conventions, defer to human review
- Do not attempt to run scorecard or deployment tests without K8s cluster

**Key Takeaway:** This repository's "tests" are not traditional unit/integration tests. They are OLM compliance checks that require Kubernetes infrastructure. An agent can validate manifest syntax and structure, but cannot fully validate operator functionality without external systems.
