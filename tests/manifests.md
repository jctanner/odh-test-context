# Test Context: opendatahub-io/manifests

**Agent Readiness: MEDIUM** — Manifest build validation works in container, but integration tests require KinD cluster infrastructure.

## Overview

Kubernetes manifests repository for Open Data Hub (Kubeflow). Uses Kustomize for building and templating YAML manifests. Primary language is YAML/Kustomize with Python test utilities and shell scripts for CI automation.

**Languages:** YAML/Kustomize (primary), Python (tests), Go (kustomize dependency), Shell (CI scripts)
**Build System:** Kustomize v5.2.1
**Test Framework:** pytest (Python unit tests), kustomize build validation, KinD integration tests
**CI:** GitHub Actions with 22+ component-specific workflows

## Container Recipe

This recipe allows validation of manifest builds and Python unit tests in an isolated container. Integration tests requiring KinD cluster are documented but cannot run in this container.

### 1. Start container

```bash
podman run -d --name test-context-manifests \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.9-slim \
  sleep infinity
```

### 2. Install system dependencies

```bash
podman exec test-context-manifests bash -c \
  "apt-get update && apt-get install -y curl tar gzip ca-certificates"
```

### 3. Install kustomize

```bash
podman exec test-context-manifests bash -c \
  "curl -L https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.2.1/kustomize_v5.2.1_linux_amd64.tar.gz -o kustomize.tar.gz && \
   tar -xzf kustomize.tar.gz && \
   chmod +x kustomize && \
   mv kustomize /usr/local/bin/ && \
   kustomize version"
```

Expected output: `v5.2.1`

### 4. Validate manifests build (PRIMARY CI TEST)

```bash
podman exec test-context-manifests bash -c \
  "cd /app && kustomize build example"
```

**Status: ✅ VALIDATED** — Exit code 0
**Output:** Produces deprecation warnings but successfully builds all manifests:
```
# Warning: 'vars' is deprecated. Please use 'replacements' instead.
# Warning: 'patchesStrategicMerge' is deprecated. Please use 'patches' instead.
...
apiVersion: v1
kind: Namespace
metadata:
  name: auth
---
[thousands of lines of valid Kubernetes YAML]
```

**Notes:** This is the main CI gate check that runs on every push/PR (manifests_example_test.yaml). Warnings are expected and not treated as errors. The command validates that all Kustomize manifests can be rendered to valid Kubernetes YAML.

### 5. Install Python test dependencies (OPTIONAL)

```bash
podman exec test-context-manifests bash -c \
  "pip install flake8 pytest requests"
```

### 6. Run flake8 linting (NOT USED IN CI)

```bash
podman exec test-context-manifests bash -c \
  "cd /app && flake8 ."
```

**Status: ❌ FINDS VIOLATIONS** — Exit code 1
**Output snippet:**
```
./apps/kfp-tekton/.../sync.py:29:80: E501 line too long (103 > 79 characters)
./apps/kfp-tekton/.../sync.py:30:80: E501 line too long (104 > 79 characters)
[100+ more violations]
```

**IMPORTANT:** Despite having a `.flake8` config file, flake8 is **NOT** run in any CI workflow. This is dead configuration. An agent validating patches does not need to run flake8 as it's not a gating check.

### 7. Run Python unit tests

```bash
podman exec test-context-manifests bash -c \
  "cd /app/apps/pipeline/upstream/base/installs/multi-user/pipelines-profile-controller && \
   pytest test_sync.py -v"
```

**Status: ✅ VALIDATED** — Exit code 0, 6 passed in 0.28s
**Output:**
```
test_sync.py::test_sync_server_with_pipeline_enabled[...] PASSED [ 16%]
test_sync.py::test_sync_server_with_pipeline_enabled[...] PASSED [ 33%]
test_sync.py::test_sync_server_with_pipeline_enabled[...] PASSED [ 50%]
test_sync.py::test_sync_server_with_pipeline_enabled[...] PASSED [ 66%]
test_sync.py::test_sync_server_with_direct_passing_of_settings[...] PASSED [ 83%]
test_sync.py::test_sync_server_without_pipeline_enabled[...] PASSED [100%]
============================== 6 passed in 0.28s ===============================
```

**Notes:** These unit tests validate the pipelines-profile-controller HTTP sync endpoint logic without requiring a Kubernetes cluster. They use pytest fixtures to mock HTTP servers.

### 8. Cleanup

```bash
podman rm -f test-context-manifests
```

## Validation Results

| Step | Command | Exit Code | Result |
|------|---------|-----------|--------|
| Install deps | `apt-get install curl tar gzip ca-certificates` | 0 | ✅ Success |
| Install kustomize | `curl + tar kustomize v5.2.1` | 0 | ✅ Success |
| **Build manifests** | `kustomize build example` | 0 | ✅ **Success** (main CI gate) |
| Install flake8 | `pip install flake8` | 0 | ✅ Success |
| Lint (flake8) | `flake8 .` | 1 | ❌ Found violations (NOT in CI) |
| Install pytest | `pip install pytest requests` | 0 | ✅ Success |
| **Python unit tests** | `pytest test_sync.py -v` | 0 | ✅ **Success** (6 passed) |

## CI/CD

### GitHub Actions Workflows

The repository has **22 component-specific test workflows** plus 1 unit test workflow:

**Gating Workflows (required for merge):**

1. **manifests_example_test.yaml** (triggers: push, pull_request)
   - Command: `kustomize build example`
   - Purpose: Validate all manifests build successfully
   - Duration: ~30 seconds

2. **Component Integration Tests** (trigger: pull_request with path filters)
   - 22 separate workflows for different components
   - Each creates KinD cluster, deploys component, validates readiness
   - Examples: pipeline_test.yaml, notebook_controller_test.yaml, kserve_test.yaml
   - Duration: 5-15 minutes each
   - Pattern:
     ```bash
     ./tests/gh-actions/install_kind.sh
     kind create cluster --config tests/gh-actions/kind-cluster.yaml
     ./tests/gh-actions/install_kustomize.sh
     ./tests/gh-actions/install_kubectl.sh
     ./tests/gh-actions/install_istio.sh
     ./tests/gh-actions/install_cert_manager.sh
     kustomize build {component-path} | kubectl apply -f -
     kubectl wait --for=condition=Ready pods --all --timeout 180s
     # Component-specific smoke tests
     ```

**Non-Gating Workflows:**

- **triage_issues.yaml** — Issue management automation (triggers on issue events)

### CI Commands Reference

**Manifest validation (main gate):**
```bash
kustomize build example
```

**Component-specific build examples:**
```bash
kustomize build apps/pipeline/upstream/env/cert-manager/platform-agnostic-multi-user
kustomize build apps/jupyter/notebook-controller/upstream/overlays/kubeflow
kustomize build contrib/kserve/kserve
```

**Integration test pattern (requires KinD cluster):**
```bash
# Install KinD v0.20.0
./tests/gh-actions/install_kind.sh

# Create cluster
kind create cluster --config tests/gh-actions/kind-cluster.yaml

# Install prerequisites
./tests/gh-actions/install_istio.sh
./tests/gh-actions/install_cert_manager.sh

# Deploy component
kustomize build {component-path} | kubectl apply -f -

# Wait for readiness
kubectl wait --for=condition=Ready pods --all --all-namespaces --timeout 180s

# Run component-specific tests (varies by component)
```

## Conventions

### Repository Structure

```
manifests/
├── apps/              # Official Kubeflow components
│   ├── pipeline/
│   ├── jupyter/
│   ├── katib/
│   └── ...
├── common/            # Common infrastructure (Istio, cert-manager, Knative)
│   ├── istio-1-18/
│   ├── cert-manager/
│   ├── knative/
│   └── ...
├── contrib/           # 3rd party components (KServe, Ray, Seldon)
│   ├── kserve/
│   ├── ray/
│   └── ...
├── example/           # Full installation example (kustomize build target)
├── tests/
│   └── gh-actions/    # CI test scripts and fixtures
└── hack/              # Sync and utility scripts
```

### Kustomize Conventions

- `base/` — Base Kubernetes resources
- `overlays/` — Environment-specific customizations (e.g., `overlays/kubeflow`, `overlays/istio`)
- `kustomization.yaml` — Kustomize build file in each directory

### Test File Naming

- Python tests: `test_*.py` (pytest convention)
- Shell scripts: `install_*.sh`, `sync-*-manifests.sh`
- Test fixtures: YAML files in `tests/gh-actions/kf-objects/`

### Import Style

Python files use standard imports:
```python
import pytest
from kubernetes import client
from kserve import KServeClient, V1beta1InferenceService
```

## Gaps & Caveats

### Critical Gaps

1. **No lint enforcement** — `.flake8` config exists but is never run in CI. Python code has 100+ violations that are ignored.

2. **Integration tests require infrastructure** — Most tests need:
   - KinD v0.20.0
   - kubectl
   - 16 CPU cores, 32GB RAM
   - Deployed infrastructure (Istio, cert-manager, Knative)
   - 5-15 minutes per test

3. **No quick validation loop** — Developers cannot quickly validate changes without spinning up a full KinD cluster.

### Medium Priority Gaps

4. **Kustomize deprecations** — Manifests use deprecated features (`vars`, `patchesStrategicMerge`, `bases`) that produce warnings. No migration plan evident.

5. **No test coverage metrics** — No coverage reporting for Python tests.

6. **No pre-commit hooks** — Despite having test infrastructure, no automated checks on commit.

### Lower Priority Observations

7. **Prow config is dead code** — `prow_config.yaml` exists but all workflows are commented out.

8. **Path-based CI triggers** — Workflows only run when specific paths change. This is efficient but means unrelated changes might not trigger full validation.

## What Works for Agents

An AI agent validating patches in this repo can:

✅ **Run manifest builds** — `kustomize build example` works in a lightweight container (python:3.9-slim + kustomize)
✅ **Validate YAML syntax** — Kustomize build will fail on invalid YAML
✅ **Run Python unit tests** — Small set of pytest tests for pipelines-profile-controller
✅ **Check for Kustomize deprecations** — Warnings are printed but not errors

## What Doesn't Work for Agents

❌ **Integration tests** — Require KinD cluster with full infrastructure (Istio, cert-manager, etc.)
❌ **Lint enforcement** — Flake8 configured but not used; can run it but results are not actionable
❌ **Component smoke tests** — Require deployed components in Kubernetes cluster
❌ **E2E validation** — Cannot verify that manifests actually deploy correctly without cluster

## Recommended Agent Workflow

For an agent validating a patch to this repository:

1. **Always run:** `kustomize build example`
   - This is the main CI gate
   - Validates all manifests can be rendered
   - Fast (~30s) and works in container

2. **Optionally run:** Python unit tests
   - `cd apps/pipeline/upstream/base/installs/multi-user/pipelines-profile-controller && pytest test_sync.py -v`
   - Only useful if patch touches these files

3. **Do NOT run:** flake8
   - Not enforced in CI
   - Will report 100+ violations that are not blockers

4. **Cannot run:** Integration tests
   - Require full KinD cluster setup
   - Beyond scope of simple patch validation
   - Trust that CI will run these for the specific components changed

5. **Check:** Which workflow(s) will trigger
   - Look at the paths changed in the patch
   - Reference workflow `paths:` filters to see which tests will run
   - Example: Changes to `apps/pipeline/upstream/**` trigger `pipeline_test.yaml`

## Summary

This repository has a **medium** agent readiness score because:

**✅ Strengths:**
- Main build validation (`kustomize build example`) works reliably in container
- Fast feedback loop for manifest syntax validation
- Clear CI workflow structure with path-based triggers
- Some unit tests can run without infrastructure

**⚠️  Weaknesses:**
- Most tests require full KinD cluster (not container-friendly)
- No lint enforcement (flake8 is a red herring)
- Cannot validate that manifests actually deploy correctly
- Integration tests take 5-15 minutes each

**Recommendation:** Use this repo for **build validation only**. An agent can verify that manifests are syntactically correct and buildable, but cannot fully validate that they deploy correctly without a Kubernetes cluster.
