# Test Context: odh-manifests

**Generated**: 2026-03-22T23:40:00Z
**Repository**: opendatahub-io/odh-manifests
**Agent Readiness**: MEDIUM - Linting works, tests require OpenShift cluster

## Overview

This is a **Kubernetes manifests repository** for Open Data Hub components, using Kustomize for composition. The repository contains YAML manifests, bash-based integration tests, and minimal Python support code. Linting can be validated in a container, but integration tests require a full OpenShift cluster with admin access.

**Languages**: YAML (Kustomize), Bash (tests), Python (minimal)
**Build System**: Kustomize (manifest composition, not code compilation)
**Test System**: Bash integration tests using external peak framework
**CI System**: OpenShift CI (Prow) - config external to this repo

**Why MEDIUM readiness**: An agent can lint YAML and validate Kustomize builds successfully, providing confidence that manifests are syntactically correct and compose properly. However, the integration tests require a real OpenShift cluster (30+ min provisioning + deployment + testing), making them impractical for quick patch validation.

---

## Container Recipe

This recipe enables validation of manifest linting and Kustomize builds. Tests cannot run without an OpenShift cluster.

### 1. Start Container

```bash
podman run -d \
  --name test-context-odh-manifests \
  -v $(pwd):/app:Z \
  -w /app \
  registry.fedoraproject.org/fedora:39 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-odh-manifests bash -c \
  "dnf install -y wget tar gzip make"
```

### 3. Install kube-linter

```bash
podman exec test-context-odh-manifests bash -c "
  cd /tmp && \
  wget -q https://github.com/stackrox/kube-linter/releases/download/v0.6.8/kube-linter-linux.tar.gz && \
  tar -xzf kube-linter-linux.tar.gz && \
  mv kube-linter /usr/local/bin/ && \
  chmod +x /usr/local/bin/kube-linter && \
  kube-linter version
"
```

**Expected output**: `0.6.8`

### 4. Install Kustomize

```bash
podman exec test-context-odh-manifests bash -c "
  cd /tmp && \
  wget -q https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.3.0/kustomize_v5.3.0_linux_amd64.tar.gz && \
  tar -xzf kustomize_v5.3.0_linux_amd64.tar.gz && \
  mv kustomize /usr/local/bin/ && \
  chmod +x /usr/local/bin/kustomize && \
  kustomize version
"
```

**Expected output**: `v5.3.0`

### 5. Run kube-linter (Manifest Policy Validation)

```bash
podman exec test-context-odh-manifests bash -c \
  "cd /app && kube-linter lint ./ --config .kube-linter.yaml"
```

**Expected behavior**: Exit code 1, reports 240 lint violations
**Interpretation**: These are policy violations (missing resource limits, security contexts, image tags), not syntax errors. The linter is working correctly. A passing lint run would show 0 errors and exit code 0.

**Sample output**:
```
/app/ceph/object-storage/nano/base/statefulset.yaml: container "ceph-nano-init" is using an invalid container image "ceph/daemon"
/app/data-science-pipelines-operator/manager/manager.yaml: container "manager" does not have a read-only root file system
Error: found 240 lint errors
```

### 6. Run Kustomize Build Validation (Manifest Composition)

Validate that manifests compose correctly:

```bash
podman exec test-context-odh-manifests bash -c \
  "cd /app/odh-dashboard/base && kustomize build ."
```

**Expected behavior**: Exit code 0, outputs rendered YAML with deprecation warnings
**Sample output**:
```
# Warning: 'commonLabels' is deprecated. Please use 'labels' instead.
apiVersion: v1
kind: ServiceAccount
metadata:
  name: odh-dashboard
  labels:
    app: odh-dashboard
...
```

Validate all Kustomize builds (slower):

```bash
podman exec test-context-odh-manifests bash -c "
  cd /app && \
  find . -name 'kustomization.yaml' -type f | while read kfile; do
    dir=\$(dirname \$kfile)
    echo \"Building \$dir\"
    kustomize build \$dir > /dev/null || echo \"FAILED: \$dir\"
  done
"
```

### 7. Integration Tests (Requires OpenShift Cluster)

**⚠️ Cannot run in container without cluster access**

Integration tests require:
- Active OpenShift cluster (OCP 4.x)
- Cluster admin credentials (`oc login` as admin)
- `KUBECONFIG` exported
- 30+ minutes runtime (cluster deploy + ODH install + tests)

To run tests (if cluster available):

```bash
cd tests
make build  # Builds test container image
make run    # Requires cluster access via KUBECONFIG
```

**Environment variables**:
- `ODHPROJECT=opendatahub` - namespace for ODH
- `SKIP_INSTALL=true` - skip ODH installation if already deployed
- `TESTS_REGEX=dashboard` - run only dashboard tests
- `OPENSHIFT_TESTUSER_NAME` - test user for Dashboard UI tests
- `OPENSHIFT_TESTUSER_PASS` - test user password

### 8. Cleanup

```bash
podman rm -f test-context-odh-manifests
```

---

## Validation Results

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| System deps | `dnf install -y wget tar gzip make` | 0 | ✅ Pass | Installed successfully |
| Install kube-linter | `wget + tar + mv kube-linter` | 0 | ✅ Pass | v0.6.8 installed |
| Install kustomize | `wget + tar + mv kustomize` | 0 | ✅ Pass | v5.3.0 installed |
| Lint manifests | `kube-linter lint ./` | 1 | ✅ Pass | Found 240 policy violations (expected) |
| Build manifests | `kustomize build ./odh-dashboard/base` | 0 | ✅ Pass | Builds with deprecation warnings |
| Integration tests | `cd tests && make test` | N/A | ❌ Skip | Requires OpenShift cluster |

**Summary**: Linting and Kustomize validation work in container. Tests require infrastructure.

---

## CI/CD

### System: OpenShift CI (Prow)

CI configuration is **external** to this repository, maintained in:
- https://github.com/openshift/release/tree/master/ci-operator/config/opendatahub-io/odh-manifests

### Gating Checks

**pull request checks** (required for merge):
1. **odh-manifests-pr-test**: Provisions ephemeral OpenShift cluster in AWS, builds test image, installs ODH, runs `tests/basictests/*.sh`

### CI Workflow

1. GitHub PR opened
2. OpenShift CI detects webhook
3. Provisions ephemeral OpenShift 4.x cluster in AWS (ipi-aws workflow)
4. Builds test container from `tests/Dockerfile`
5. Runs `tests/scripts/installandtest.sh` with cluster credentials
6. Tests install ODH operator, create KfDef, wait for components, verify functionality
7. Collects artifacts (logs, pod YAML, events) to `/tmp/artifacts`
8. Reports pass/fail to GitHub PR

**Typical runtime**: 45-60 minutes (15 min cluster provision + 30-45 min tests)

### Test Entry Point

CI runs: `$HOME/peak/installandtest.sh`

Which:
- Copies kubeconfig from CI mount point
- Exports `KUBECONFIG`, `ODHPROJECT`, `ARTIFACT_DIR`
- Installs ODH operator and KfDef (unless `SKIP_INSTALL=true`)
- Runs `$HOME/peak/run.sh basictests` (bash test runner)
- Collects pod logs and events to artifact directory

### Local Test Execution

To replicate CI locally (requires OpenShift cluster):

```bash
oc login <cluster> -u kubeadmin
cd tests
make build
make run
```

Customize with:
```bash
make run SKIP_INSTALL=true TESTS_REGEX=dashboard ODHPROJECT=my-odh
```

---

## Conventions

### Repository Structure

```
odh-manifests/
├── <component>/
│   ├── base/
│   │   ├── kustomization.yaml      # Base manifests
│   │   └── *.yaml                  # K8s resources
│   ├── overlays/                   # Optional overlays
│   └── README.md
├── tests/
│   ├── basictests/                 # Integration test scripts
│   │   ├── dashboard.sh
│   │   ├── dsp-operator.sh
│   │   └── ...
│   ├── resources/                  # Test fixtures (CRs, secrets)
│   ├── Dockerfile                  # Test container image
│   ├── Makefile                    # Test orchestration
│   └── scripts/
│       ├── installandtest.sh       # CI test entry point
│       └── install.sh              # ODH installation script
├── Makefile                        # Release automation + linting
└── .kube-linter.yaml               # Linter config
```

### Test File Naming

- Integration tests: `tests/basictests/<component>.sh`
- Naming pattern: `*tests*.sh` (matched by peak test runner)
- Test functions: `function <action>_<component>() { ... }`

### YAML Conventions

- Kustomize structure: each component has `base/kustomization.yaml`
- Overlays for variants (e.g., different namespaces, resource limits)
- Use `params.yaml` + `params.env` for configurable values
- Follow Kubernetes resource naming: `<component>-<resource-type>.yaml`

### Test Patterns

Tests use `os::cmd::*` functions from peak framework:

```bash
os::cmd::expect_success "oc get deployment my-deployment"
os::cmd::try_until_text "oc get pods -l app=foo" "Running" $timeout $interval
os::cmd::expect_success_and_text "oc get csv" "Succeeded"
```

Each test script:
1. Sources `$TEST_DIR/common` and `util`
2. Declares test suite: `os::test::junit::declare_suite_start "$MY_SCRIPT"`
3. Defines functions for test stages
4. Calls functions in order
5. Ends suite: `os::test::junit::declare_suite_end`

---

## Gaps & Caveats

### Major Gaps

1. **Tests require OpenShift cluster**: Cannot run integration tests without full cluster access. No mocked/unit tests.

2. **CI config is external**: Actual CI job definition is in openshift/release repo, not visible in odh-manifests.

3. **240 lint violations**: kube-linter reports policy issues (missing resource limits, security contexts, image tags using `latest`, etc.). These should be addressed.

4. **External test framework dependency**: Tests rely on https://github.com/opendatahub-io/peak, which must be cloned and set up.

5. **Long test runtime**: Tests take 30-45 minutes after cluster is ready (install operators, wait for CRDs, deploy components, verify).

6. **Kustomize deprecations**: Multiple components use deprecated `commonLabels` field. Should migrate to `labels`.

7. **No pre-commit hooks**: No automated linting before commit.

8. **Python dependencies outdated**: `Pipfile` specifies Python 3.6 (EOL). Should update to 3.9+.

### What Can Be Validated

✅ **YAML syntax**: kube-linter validates all YAML files parse correctly
✅ **Kubernetes resource structure**: kube-linter validates resources match K8s API schema
✅ **Kustomize composition**: `kustomize build` validates overlays compose correctly
✅ **Policy compliance**: kube-linter checks security best practices
❌ **Runtime behavior**: Cannot validate without deploying to cluster
❌ **Component integration**: Cannot test component interactions without cluster
❌ **Dashboard UI**: Cannot run selenium tests without cluster + browser

### Validation Without Cluster

For patch validation without a cluster, an agent can:

1. **Lint with kube-linter**: Catches YAML syntax errors, schema violations, policy issues
2. **Build with kustomize**: Validates manifests compose correctly, catches missing resources
3. **Check for regressions**: Compare lint results before/after patch
4. **Validate specific patterns**: Check that new manifests follow conventions (resource limits, labels, etc.)

This provides **high confidence** for syntax and structure, **medium confidence** for deployability (manifests compose but not deployed), **low confidence** for runtime behavior (needs cluster).

---

## Test Execution Flowchart

```
PR Created
    ↓
OpenShift CI Webhook
    ↓
Provision Ephemeral OCP Cluster (AWS)
    ↓
Build Test Container (tests/Dockerfile)
    ↓
Run installandtest.sh
    ├─→ Install ODH Operator
    ├─→ Apply KfDef (odh-core.yaml)
    ├─→ Wait 5 min for components
    ├─→ Run basictests/*.sh
    │    ├─→ dashboard.sh
    │    ├─→ dsp-operator.sh
    │    ├─→ modelmesh.sh
    │    └─→ ... (9 test scripts)
    └─→ Collect artifacts
           ├─→ Pod logs
           ├─→ Events
           ├─→ Screenshots (selenium)
           └─→ KfDef YAML
    ↓
Report Pass/Fail to GitHub
    ↓
Destroy Cluster
```

---

## Quick Reference

### Lint All Manifests

```bash
kube-linter lint ./ --config .kube-linter.yaml
```

### Validate Kustomize Builds

```bash
# Single component
kustomize build ./odh-dashboard/base

# All components
find . -name 'kustomization.yaml' -exec dirname {} \; | \
  xargs -I {} sh -c 'kustomize build {} > /dev/null && echo "✓ {}" || echo "✗ {}"'
```

### Run Tests (Requires Cluster)

```bash
cd tests
make build                          # Build test image
make run                            # Run all tests
make run TESTS_REGEX=dashboard      # Run single test
make run SKIP_INSTALL=true          # Test existing deployment
make clean                          # Cleanup ODH installation
```

### Test Single Component Manually

```bash
# Requires: oc login, cluster admin, peak repo cloned
git clone https://github.com/opendatahub-io/peak
cd peak
git submodule update --init
./run.sh operator-tests/odh-manifests/basictests/dashboard.sh
```

---

## Agent Recommendations

### For Patch Validation

**Without Cluster**:
1. Run `kube-linter lint ./` - exit code 0 required (or compare violation count before/after)
2. Run `kustomize build` on affected components - exit code 0 required
3. Check diff doesn't introduce `latest` tags, missing resource limits, or security issues
4. Validate new resources follow conventions (labels, namespaces, resource limits)

**With Cluster** (ideal):
1. Run full `cd tests && make test`
2. Verify all test scripts pass
3. Check artifacts for errors

### Expected Validation Time

- **Lint only**: 10-15 seconds
- **Kustomize build (all)**: 30-60 seconds
- **Integration tests**: 45-60 minutes (with cluster provisioning)

### Confidence Levels

| Validation | Time | Confidence | Notes |
|------------|------|------------|-------|
| kube-linter only | 15s | Medium | Catches syntax/policy issues |
| + kustomize build | 60s | Medium-High | Validates composition |
| + integration tests | 60m | High | Full deployment validation |

---

## Troubleshooting

### kube-linter reports 240+ errors

**Expected**. Many manifests have policy violations (missing resource limits, security contexts, etc.). These are warnings about best practices, not blocking errors. Compare count before/after patch - new violations may indicate issues.

### Kustomize build warns about 'commonLabels' deprecated

**Expected**. Multiple components use deprecated field. Run `kustomize edit fix` in each component to auto-migrate, or ignore warnings (non-blocking).

### Tests fail with "no cluster found"

Tests require `KUBECONFIG` pointing to OpenShift cluster with admin access. Tests cannot run without cluster. Use linting + kustomize validation instead.

### Tests timeout waiting for pods

ODH components can take 10-15 minutes to reach Running state. Tests have 20 minute timeouts. Check artifacts for pod logs if timeout occurs.

### Selenium tests fail with "chrome not found"

Dashboard UI tests require chromium + chromedriver in test container. These are installed in `tests/Dockerfile`. If running tests outside container, install: `dnf install chromium chromedriver`.

---

**End of Test Context**
