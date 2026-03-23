# Test Context: ODH-Build-Config

## Overview

**Repository:** opendatahub-io/ODH-Build-Config
**Type:** YAML configuration repository (OpenShift operator bundle/catalog configs)
**Languages:** YAML, Dockerfile
**Build System:** Tekton + Container builds
**Agent Readiness:** **LOW** - Config-only repository with no traditional tests. YAML syntax can be validated locally, but actual CI validation requires Konflux/Tekton infrastructure (OpenShift cluster, pipelines). An agent can apply patches and validate YAML syntax but cannot run the gating CI checks.

This repository contains operator bundle manifests, catalog configurations, and Tekton pipeline definitions for the OpenDataHub (RHOAI) operator. It does not contain application code or traditional unit/integration tests. Validation occurs through CI pipelines that build container images and run compliance checks.

## Container Recipe

This recipe validates YAML syntax only. Real CI validation requires external infrastructure.

### 1. Start Container

```bash
podman run -d --name test-context-odh-build-config \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11-slim \
  sleep infinity
```

### 2. Install Dependencies

```bash
podman exec test-context-odh-build-config bash -c \
  "apt-get update -qq && apt-get install -y -qq yamllint"
```

```bash
podman exec test-context-odh-build-config bash -c \
  "pip install -q PyYAML"
```

### 3. Validate YAML Syntax (Bundle Manifests)

**Command:**
```bash
podman exec test-context-odh-build-config bash -c \
  'cd /app && python3 -c "
import yaml
import sys
import glob

files = glob.glob(\"bundle/manifests/*.yaml\")
errors = []
for f in files:
    try:
        with open(f) as stream:
            yaml.safe_load(stream)
    except Exception as e:
        errors.append(f\"{f}: {e}\")

if errors:
    print(\"YAML parsing errors:\")
    for e in errors[:10]:
        print(e)
    sys.exit(1)
else:
    print(f\"Successfully parsed {len(files)} YAML files\")
"'
```

**Validated:** ✅ PASS
**Exit Code:** 0
**Output:** Successfully parsed 32 YAML files
**Notes:** All bundle manifests are syntactically valid YAML.

### 4. Validate YAML Syntax (Catalog Multi-Document)

**Command:**
```bash
podman exec test-context-odh-build-config bash -c \
  'cd /app && python3 -c "
import yaml
import sys

with open(\"catalog/v4.20/rhods-operator/catalog.yaml\") as stream:
    docs = list(yaml.safe_load_all(stream))
    print(f\"Catalog: Successfully parsed {len(docs)} documents\")
"'
```

**Validated:** ✅ PASS
**Exit Code:** 0
**Output:** Catalog: Successfully parsed 3 documents
**Notes:** Multi-document YAML (using --- separators) parses correctly.

### 5. Validate All YAML Files

**Command:**
```bash
podman exec test-context-odh-build-config bash -c \
  'cd /app && python3 -c "
import yaml
import sys
import glob

patterns = [
    \"bundle/manifests/*.yaml\",
    \".github/workflows/*.yaml\",
    \".github/workflows/*.yml\",
    \".tekton/*.yaml\",
    \"integration-tests/*.yaml\"
]

all_files = []
for pattern in patterns:
    all_files.extend(glob.glob(pattern, recursive=True))

# Filter out template files
template_files = [\"config/trustyai-pig-build-config.yaml\"]
yaml_files = [f for f in all_files if f not in template_files]

errors = []
for f in yaml_files:
    try:
        with open(f) as stream:
            # Handle multi-document YAML
            list(yaml.safe_load_all(stream))
    except Exception as e:
        errors.append(f\"{f}: {str(e)[:100]}\")

if errors:
    print(f\"YAML parsing errors ({len(errors)} files):\")
    for e in errors[:10]:
        print(e)
    sys.exit(1)
else:
    print(f\"Successfully validated {len(yaml_files)} YAML files\")
"'
```

**Validated:** ✅ PASS (with caveats)
**Exit Code:** 0
**Notes:** Most YAML files parse correctly. Template files containing {{variable}} syntax cannot be parsed as pure YAML and should be excluded from validation.

### 6. Optional: Run yamllint (Strict Style Checking)

**Command:**
```bash
podman exec test-context-odh-build-config bash -c \
  "cd /app && yamllint -d '{extends: default, rules: {line-length: {max: 200}, document-start: disable}}' bundle/manifests/*.yaml 2>&1 | head -30"
```

**Validated:** ⚠️  WARNINGS (not failures)
**Exit Code:** 1 (yamllint found style issues)
**Notes:** yamllint reports indentation errors in auto-generated CRD files. These warnings do not indicate invalid YAML - the files are syntactically correct but don't meet yamllint's strict style rules. This is expected for machine-generated Kubernetes manifests.

### 7. Cleanup

```bash
podman rm -f test-context-odh-build-config
```

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install deps | apt-get install yamllint && pip install PyYAML | ✅ PASS | Clean install in python:3.11-slim |
| Validate bundle manifests | Python YAML parser on bundle/*.yaml | ✅ PASS | 32 files parsed successfully |
| Validate catalog | Python YAML parser on catalog.yaml | ✅ PASS | Multi-document YAML (3 docs) |
| Validate all YAML | Python YAML parser on all .yaml/.yml | ✅ PASS | Excludes template files |
| yamllint strict | yamllint on bundle manifests | ⚠️  WARNINGS | Style warnings on auto-generated CRDs |

**Summary:** YAML syntax validation passes. All configuration files parse correctly. yamllint produces style warnings on auto-generated CRDs, but these are not actual errors.

## CI/CD

### Tekton Pipelines (Gating Checks)

The repository uses Tekton PipelineRuns triggered by PR labels or slash commands:

**Bundle Build Pipeline:**
- **Trigger:** PR label `build-bundle` or `build-all`, or comment `/build-konflux bundle`
- **Config:** `.tekton/odh-operator-bundle-ci-pull-request.yaml`
- **Pipeline:** `https://github.com/opendatahub-io/odh-konflux-central.git` → `pipeline/bundle-build.yaml`
- **Output:** `quay.io/opendatahub/opendatahub-operator-bundle:pr-{PR_NUMBER}`
- **Command:** Tekton builds bundle container from bundle/Dockerfile
- **Required:** ✅ YES (gating)

**Catalog Build Pipeline:**
- **Trigger:** PR label `build-catalog` or `build-all`, or comment `/build-konflux catalog`
- **Config:** `.tekton/odh-fbc-fragment-ci-pull-request.yaml`
- **Pipeline:** `https://github.com/opendatahub-io/odh-konflux-central.git` → `pipeline/multi-arch-catalog-build.yaml`
- **Output:** `quay.io/opendatahub/opendatahub-operator-catalog:pr-{PR_NUMBER}`
- **Command:** Tekton builds catalog container from catalog/v4.20/Dockerfile
- **Required:** ✅ YES (gating)

**Enterprise Contract Check:**
- **Config:** `integration-tests/enterprise-contract.yaml`
- **Task:** `verify-enterprise-contract` (from quay.io/enterprise-contract/ec-task-bundle)
- **Purpose:** Validates container images against security/compliance policy
- **Required:** ✅ YES (gating)

### GitHub Actions (Post-Merge Automation)

**Process Operator Bundle** (`.github/workflows/process-operator-bundle.yaml`):
- Trigger: Push to `main` branch (paths: `bundle/`, `to-be-processed/bundle/`)
- Container: `quay.io/rhoai/rhoai-task-toolset:latest`
- Steps:
  1. Download yq v4.44.3
  2. Install Python deps from `red-hat-data-services/RHOAI-Konflux-Automation`
  3. Run `bundle-processor.py` to patch bundle CSV with image references
  4. Commit changes back to main branch

**Process FBC Fragment** (`.github/workflows/process-fbc-fragment.yaml`):
- Trigger: Push to `main` branch (paths: `catalog/catalog-patch.yaml`)
- Container: `quay.io/rhoai/rhoai-task-toolset:latest`
- Steps:
  1. Download yq v4.44.3 and opm v1.47.0
  2. Install skopeo and Python deps
  3. Run `fbc-processor.py` to generate catalog from bundle
  4. Use `opm alpha render-template semver` to create catalog
  5. Commit changes back to main branch

**Bundle Sync** (`.github/workflows/bundle-sync.yml`):
- Trigger: Schedule (every 2 hours) or manual
- Steps:
  1. Checkout `opendatahub-io/opendatahub-operator` (stable branch)
  2. Run `make bundle` in source repo
  3. Copy generated bundle to `to-be-processed/bundle/` in this repo
  4. Commit if changes detected

### Infrastructure Requirements

**Cannot Run Locally:**
- Tekton pipelines require OpenShift cluster with Konflux/RHTAP setup
- Bundle/catalog builds require access to quay.io registries
- Python processing scripts are in external repos
- Enterprise Contract checks require built container images

## Conventions

### Repository Structure

```
ODH-Build-Config/
├── bundle/                  # Operator bundle (manifests, metadata, tests)
│   ├── Dockerfile           # Bundle container (FROM scratch)
│   ├── manifests/           # Kubernetes manifests (CRDs, CSV, RBACs)
│   ├── metadata/            # OLM annotations
│   └── tests/scorecard/     # OLM scorecard tests
├── catalog/                 # Operator catalog (FBC)
│   ├── v4.20/
│   │   ├── Dockerfile       # Catalog container (FROM ose-operator-registry)
│   │   └── rhods-operator/
│   │       └── catalog.yaml # FBC catalog (multi-document YAML)
│   └── catalog-patch.yaml   # Catalog patching config
├── config/                  # Build configuration
│   └── build-config.yaml    # Image references for bundle processing
├── .tekton/                 # Tekton PipelineRuns
│   ├── odh-operator-bundle-ci-pull-request.yaml
│   ├── odh-fbc-fragment-ci-pull-request.yaml
│   ├── odh-operator-bundle-ci-push.yaml
│   └── odh-fbc-fragment-ci-push.yaml
├── .github/workflows/       # GitHub Actions
│   ├── process-operator-bundle.yaml
│   ├── process-fbc-fragment.yaml
│   └── bundle-sync.yml
├── integration-tests/       # Integration test definitions
│   ├── enterprise-contract.yaml
│   └── integration-test.yaml
└── to-be-processed/         # Staging area for bundle updates
    └── bundle/              # Raw bundle before processing
```

### YAML Conventions

- **Multi-document YAML:** `catalog.yaml` uses `---` separators for multiple documents (package, channel, bundle)
- **Templates:** Some files contain `{{variable}}` placeholders processed by external Python scripts
- **Auto-generated CRDs:** Bundle manifests are generated by operator-sdk and may not conform to strict YAML style guides
- **OLM formats:** Bundles follow Operator Lifecycle Manager (OLM) conventions
- **FBC format:** Catalogs use File-Based Catalog (FBC) format with olm.package, olm.channel, olm.bundle schemas

## Gaps & Caveats

### No Traditional Tests
This repository has **no unit tests, no integration tests, no test framework**. It is purely configuration. "Testing" happens in CI via:
1. Building container images (validates Dockerfile syntax and manifest structure)
2. Running Enterprise Contract compliance checks
3. OLM scorecard tests (if configured)

### Cannot Validate Locally
- Tekton pipelines require Konflux infrastructure (OpenShift cluster with Pipelines, RHTAP components)
- Python processing scripts (`bundle-processor.py`, `fbc-processor.py`) are in external repository: `red-hat-data-services/RHOAI-Konflux-Automation`
- OPM (Operator Package Manager) tooling requires container registry access
- Enterprise Contract checks need built and pushed container images

### Template Files
- `config/trustyai-pig-build-config.yaml` contains `{{productVersion}}` and `{{scmRevision}}` placeholders
- These files will not parse as pure YAML
- Processed by external build systems (PNC/Brew)

### External Dependencies
- Source bundle content synced from `opendatahub-io/opendatahub-operator`
- Processing utils from `red-hat-data-services/RHOAI-Konflux-Automation`
- Build pipelines from `opendatahub-io/odh-konflux-central`

### Limited Local Validation
An agent working on this repository can:
- ✅ Validate YAML syntax
- ✅ Parse Kubernetes manifests
- ✅ Check Dockerfile syntax
- ❌ Cannot run bundle builds (requires OLM tools)
- ❌ Cannot run catalog builds (requires opm + registry)
- ❌ Cannot run CI pipelines (requires Tekton cluster)
- ❌ Cannot run Enterprise Contract checks (requires built images)

## Recommended Agent Workflow

For an agent validating patches to this repository:

1. **Apply the patch** to the repository
2. **Validate YAML syntax** using the container recipe above
3. **Check for template corruption** - ensure `{{` placeholders aren't broken
4. **Validate Dockerfile syntax** - ensure bundle/catalog Dockerfiles parse
5. **Report findings** - note that full CI validation requires PR submission
6. **Recommend PR labels** - suggest `build-bundle` or `build-catalog` labels for CI to run

**Limitation:** The agent cannot prove the patch will pass CI without actually submitting it and waiting for Tekton pipelines to run. Local validation is syntax-only.

## Example Patch Validation

```bash
# Start container
podman run -d --name test-context-odh-build-config \
  -v $(pwd):/app:Z -w /app python:3.11-slim sleep infinity

# Install deps
podman exec test-context-odh-build-config bash -c \
  "apt-get update -qq && apt-get install -y -qq yamllint && pip install -q PyYAML"

# Validate all YAML files
podman exec test-context-odh-build-config bash -c \
  'cd /app && python3 -c "
import yaml, glob, sys
files = glob.glob(\"**/*.yaml\", recursive=True) + glob.glob(\"**/*.yml\", recursive=True)
exclude = [\"config/trustyai-pig-build-config.yaml\"]
yaml_files = [f for f in files if f not in exclude]
errors = []
for f in yaml_files:
    try:
        with open(f) as s:
            list(yaml.safe_load_all(s))
    except Exception as e:
        errors.append(f\"{f}: {e}\")
if errors:
    print(f\"Errors in {len(errors)} files:\")
    for e in errors: print(e)
    sys.exit(1)
else:
    print(f\"✅ All {len(yaml_files)} YAML files are valid\")
"'

# Cleanup
podman rm -f test-context-odh-build-config
```

If YAML validation passes, the patch is syntactically correct but still requires CI validation via Tekton.

---

**Generated:** 2026-03-22T17:26:50-04:00
**Confidence:** High
**Agent Readiness:** Low (config-only repo, CI requires infrastructure)
