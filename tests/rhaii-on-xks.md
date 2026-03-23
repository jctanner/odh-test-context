# Test Context: rhaii-on-xks

**Repository:** opendatahub-io/rhaii-on-xks
**Type:** Infrastructure deployment (Helm charts + Bash/Python scripts)
**Agent Readiness:** MEDIUM - Linting validated, functional tests require Kubernetes cluster

---

## Overview

This is an **infrastructure deployment repository**, not a traditional software project. It contains Helm charts and deployment scripts for Red Hat AI Inference Stack (KServe) on managed Kubernetes platforms (AKS, CoreWeave, OpenShift).

**Languages:** Bash, Python, YAML/Helm, Makefile

**What can be validated:**
- ✅ Helm chart syntax and linting
- ✅ Bash script syntax
- ✅ Python script syntax
- ❌ Functional deployment tests (require live Kubernetes cluster)

**Agent Readiness Justification:** An agent can validate Helm charts and script syntax, but cannot run functional conformance tests without deploying to an actual Kubernetes cluster. This limits validation to syntax/lint checks rather than end-to-end deployment validation.

---

## Container Recipe

This recipe validates Helm charts and script syntax. **Note:** Functional tests require a Kubernetes cluster and cannot be run in this container.

### 1. Start Container

```bash
podman run -d --name test-context-rhaii-on-xks \
  -v $(pwd):/app:Z \
  -w /app \
  alpine:3.19 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-rhaii-on-xks sh -c \
  "apk add --no-cache bash git curl helm python3 py3-pip make"
```

### 3. Install Python Dependencies

```bash
podman exec test-context-rhaii-on-xks sh -c \
  "pip install --break-system-packages configargparse kubernetes"
```

### 4. Lint Helm Charts

All four Helm charts should pass linting:

```bash
# KServe chart (main chart)
podman exec test-context-rhaii-on-xks bash -c \
  "cd /app/charts/kserve && helm lint ."

# Expected: 1 chart(s) linted, 0 chart(s) failed
```

```bash
# Cert-manager operator chart
podman exec test-context-rhaii-on-xks bash -c \
  "cd /app/charts/cert-manager-operator && helm lint ."

# Expected: 1 chart(s) linted, 0 chart(s) failed
```

```bash
# Sail operator chart
podman exec test-context-rhaii-on-xks bash -c \
  "cd /app/charts/sail-operator && helm lint ."

# Expected: 1 chart(s) linted, 0 chart(s) failed
```

```bash
# LWS operator chart
podman exec test-context-rhaii-on-xks bash -c \
  "cd /app/charts/lws-operator && helm lint ."

# Expected: 1 chart(s) linted, 0 chart(s) failed
```

### 5. Validate Helm Templates

Ensure Helm templates render without errors:

```bash
podman exec test-context-rhaii-on-xks bash -c \
  "cd /app/charts/kserve && helm template test . > /dev/null"

# Expected: No output (success)
```

### 6. Validate Bash Script Syntax

```bash
# Conformance test script
podman exec test-context-rhaii-on-xks bash -c \
  "bash -n /app/test/conformance/verify-llm-d-deployment.sh"

# Expected: No output (syntax valid)
```

```bash
# Utility scripts
podman exec test-context-rhaii-on-xks bash -c \
  "bash -n /app/scripts/cleanup.sh && \
   bash -n /app/scripts/setup-gateway.sh && \
   bash -n /app/scripts/collect-debug-info.sh"

# Expected: No output (syntax valid)
```

### 7. Validate Python Script Syntax

```bash
podman exec test-context-rhaii-on-xks bash -c \
  "cd /app/validation && python3 -m py_compile llmd_xks_preflight.py"

# Expected: No output (syntax valid)
```

```bash
# Test script execution (help only - full tests require cluster)
podman exec test-context-rhaii-on-xks bash -c \
  "cd /app/validation && python3 llmd_xks_preflight.py --help"

# Expected: Usage help text displayed
```

### 8. Cleanup

```bash
podman rm -f test-context-rhaii-on-xks
```

---

## Validation Results

All validated commands passed successfully:

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install deps | `apk add bash git curl helm python3 py3-pip make` | ✅ PASS | All tools installed |
| Install Python deps | `pip install configargparse kubernetes` | ✅ PASS | Dependencies installed |
| Lint kserve | `helm lint charts/kserve` | ✅ PASS | 0 charts failed |
| Lint cert-manager | `helm lint charts/cert-manager-operator` | ✅ PASS | 0 charts failed |
| Lint sail-operator | `helm lint charts/sail-operator` | ✅ PASS | 0 charts failed |
| Lint lws-operator | `helm lint charts/lws-operator` | ✅ PASS | 0 charts failed |
| Helm template | `helm template test charts/kserve` | ✅ PASS | Renders successfully |
| Bash syntax (test) | `bash -n test/conformance/*.sh` | ✅ PASS | Valid syntax |
| Bash syntax (scripts) | `bash -n scripts/*.sh` | ✅ PASS | Valid syntax |
| Python syntax | `python3 -m py_compile validation/*.py` | ✅ PASS | Valid syntax |
| Python execution | `python3 validation/llmd_xks_preflight.py --help` | ✅ PASS | Script executes |

**Functional Tests:** ⚠️ REQUIRES INFRASTRUCTURE - Cannot run without Kubernetes cluster

---

## CI/CD Configuration

### Gating Checks (run on PRs)

**kserve-ci.yaml** - Helm Validation:
```bash
cd charts/kserve
helm lint .
helm template test . > /dev/null

# Verify all images from registry.redhat.io
helm template test . | grep -oE '(quay\.io|ghcr\.io|docker\.io)[^"'\''[:space:]]+' || true

# Verify webhook annotations exist
helm template test . | grep -A20 'kind: ValidatingWebhookConfiguration\|kind: MutatingWebhookConfiguration'
```

**link-check.yaml** - Link Validation:
```bash
lychee --no-progress --exclude '^https?://localhost' '**/*.md'
```

### Non-Gating (push to main only)

- **docs.yml** - Build documentation site with zensical
- **kserve-release.yaml** - Package and release Helm charts to OCI registry

---

## Conventions

**Helm Charts:**
- Location: `charts/*/`
- Structure: Standard Helm chart layout with `Chart.yaml`, `values.yaml`, `templates/`
- All charts use `registry.redhat.io` images

**Test Scripts:**
- Conformance tests: `test/conformance/verify-llm-d-deployment.sh`
- Preflight validation: `validation/llmd_xks_preflight.py`
- Utility scripts: `scripts/*.sh`

**Deployment Profiles:**
The conformance test supports multiple KServe deployment profiles:
- `kserve-basic` - Basic deployment without scheduler
- `kserve-gpu` - GPU deployment with scheduler
- `kserve-pd` - Prefill/Decode disaggregation
- `kserve-scheduler` - Custom scheduler configuration

**Test Execution (requires cluster):**
```bash
make test NAMESPACE=llm-d PROFILE=kserve-basic
```

---

## Gaps & Caveats

### Cannot Validate Without Infrastructure

1. **Conformance tests require deployed cluster:**
   - The `test/conformance/verify-llm-d-deployment.sh` script validates a live KServe deployment
   - Requires: cert-manager, istio, LWS operator, KServe controller
   - Tests: pod status, CRDs, services, HTTPRoutes, inference endpoints
   - **Impact:** An agent cannot validate deployment functionality, only syntax

2. **Python validation tool requires cluster access:**
   - `validation/llmd_xks_preflight.py` checks cluster readiness
   - Tests cloud provider, GPU availability, instance types, operator CRDs
   - Can syntax-check but cannot run actual validations
   - **Impact:** Limited to syntax validation only

3. **No unit tests or mocks:**
   - No isolated test infrastructure
   - All tests are integration tests
   - No way to validate deployment logic without real cluster
   - **Impact:** Cannot validate logic changes to deployment scripts

4. **Makefile targets require infrastructure:**
   - `make deploy`, `make deploy-all`, `make status` require cluster
   - Cannot validate these work without actual deployment
   - **Impact:** Cannot test deployment automation

### Can Validate

1. ✅ **Helm chart syntax:** All charts lint successfully
2. ✅ **Template rendering:** Helm templates render without errors
3. ✅ **Bash script syntax:** All scripts have valid syntax
4. ✅ **Python script syntax:** Validation script compiles
5. ✅ **Link validation:** Markdown links can be checked (requires lychee)

### Recommendations for Patch Validation

**For Helm chart changes:**
1. Run `helm lint charts/<chart-name>`
2. Run `helm template test charts/<chart-name>`
3. Check for syntax errors in output

**For bash script changes:**
1. Run `bash -n <script-path>` for syntax check
2. Review script logic manually (no unit tests available)

**For Python changes:**
1. Run `python3 -m py_compile <script-path>`
2. Run `python3 <script> --help` to test execution
3. Consider: `flake8 --max-line-length=120` for style (not enforced in CI)

**For documentation changes:**
1. Verify markdown renders correctly
2. Run link checker if available: `lychee '**/*.md'`

---

## Quick Reference

**Repository Type:** Infrastructure deployment (Helm + Bash + Python)
**Primary Language:** Bash (62%), YAML (30%), Python (8%)
**Test Framework:** Bash integration tests + Python validation tool
**CI System:** GitHub Actions
**Deployment Tool:** Helm + helmfile + Makefile

**Can an agent validate patches?**
- ✅ YES for syntax/linting (Helm, Bash, Python)
- ❌ NO for functional deployment tests (requires Kubernetes cluster)

**Overall Assessment:** MEDIUM agent readiness. An agent can catch syntax errors and lint violations, but cannot validate that deployments actually work without live infrastructure.
