# Test Context: dsp-dev-tools

**Repository:** opendatahub-io/dsp-dev-tools
**Analyzed:** 2026-03-22T18:02:52-04:00
**Agent Readiness:** none (no test infrastructure)

## Overview

This repository is a collection of developer tools, scripts, example pipelines, and Kubernetes manifests for Data Science Pipelines (DSP) development. It is **not** a library or application with unit tests, linting, or CI/CD. It contains:

- **dev-setup/**: Shell scripts to configure local DSP API server development environment
- **example-pipelines/**: Kubeflow Pipelines (KFP) fraud detection demo pipeline
- **manifests/**: Kubernetes manifests for deploying DSP components (Argo, KFP)
- **toolbox/**: Containerized development environment with DSP tooling
- **cloudbeaver/**: Database viewer setup for DSP databases
- **external-connection-setup/**: MariaDB and MySQL external connection manifests

**Languages:** Python (~75 lines total), Shell scripts, YAML/Kubernetes manifests
**Build System:** None (script collection, not a packaged project)
**Agent Readiness:** **none** — No test, lint, or CI infrastructure exists

---

## Container Recipe

Since this repository has no formal test or lint infrastructure, validation consists of syntax checking the scripts to ensure they are parseable.

### 1. Start Container

```bash
podman run -d --name test-context-dsp-dev-tools \
  -v /path/to/dsp-dev-tools:/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-dsp-dev-tools bash -c \
  "apt-get update -qq && apt-get install -y -qq bash shellcheck"
```

### 3. Validate Python Syntax

```bash
podman exec test-context-dsp-dev-tools bash -c \
  "cd /app && find . -name '*.py' -type f | while read f; do python -m py_compile \"\$f\" 2>&1 || echo \"Failed: \$f\"; done"
```

**Expected result:** All .py files compile successfully (exit 0).

**Files validated:**
- `dev-setup/converter.py` — Simple utility to print file contents as repr()
- `dev-setup/driver-launcher-debug/driver.py`, `launcher.py` — KFP driver debugging tools
- `example-pipelines/fraud-detection/*.py` (13 files) — KFP pipeline components and DAG definitions
- `meeting-calendar/script.py` — Calendar utility

### 4. Validate Shell Script Syntax

```bash
podman exec test-context-dsp-dev-tools bash -c \
  "cd /app && find . -name '*.sh' -type f | while read f; do bash -n \"\$f\" 2>&1 && echo \"\$f: OK\" || echo \"\$f: FAILED\"; done"
```

**Expected result:** Core scripts validate; template files intentionally fail (contain placeholders).

**Validated scripts (exit 0):**
- `dev-setup/main.sh` — Generates config files for local DSP API server dev
- `dev-setup/post-config-run.sh` — Post-configuration utility
- `external-connection-setup/devenv.sh` — External DB connection setup
- `manifests/deploy-kfp/openshift/base/add_resources.sh` — Resource addition script

**Template files (expected to fail syntax check):**
- `dev-setup/templates/*.sh` — Contain `<namespace>`, `<dspa>` placeholders; processed by main.sh

### 5. Cleanup

```bash
podman rm -f test-context-dsp-dev-tools
```

---

## Validation Results

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Python syntax | `python -m py_compile *.py` | ✅ Pass | 14 Python files, all syntactically valid |
| Shell syntax | `bash -n *.sh` | ✅ Pass (4 scripts) | Core scripts valid; 9 template files contain placeholders (expected) |
| Dependencies | N/A | ⚠️ N/A | No requirements.txt or dependency manifest |
| Lint | N/A | ❌ None | No linter configured |
| Tests | N/A | ❌ None | No test files or framework |

**Summary:** All scripts are syntactically valid. Repository has no test/lint infrastructure by design.

---

## CI/CD

**Status:** No CI/CD configured.

- No `.github/workflows/` directory
- No Tekton, Jenkins, or other CI system configs
- No gating checks, no required status checks

**Conclusion:** This repository accepts contributions without automated validation. Manual review is the only gate.

---

## Conventions

### Repository Structure

1. **dev-setup/**: Developer environment configuration
   - `main.sh` generates config files from templates for local DSP API server development
   - Requires active OpenShift/Kubernetes cluster with DSP deployed
   - Templates use `<placeholder>` syntax (e.g., `<namespace>`, `<dspa>`)
   - Generated files placed in `output/` directory (gitignored)

2. **example-pipelines/fraud-detection/**: KFP pipeline demo
   - Uses `@component` decorator from `kfp.dsl`
   - Declares dependencies via `packages_to_install=["pandas", "scikit-learn", ...]`
   - Pipeline DAG defined in `pipeline.py`, compiled to YAML via `build_yaml.py`
   - Requires KFP SDK and DSP instance to execute

3. **manifests/**: Kubernetes resource definitions
   - Uses Kustomize overlay pattern (base/ and overlays/)
   - Deploy scripts in deploy-kfp/ and deploy-argo-server/

4. **toolbox/**: Containerized developer environment
   - Dockerfile based on Fedora Toolbox 40
   - Includes: yq, oc/kubectl, kustomize, minio CLI, huggingface CLI, podman, skopeo

### Script Patterns

- Shell scripts follow bash strict mode: `set -eE -o functrace`
- Error handling via trap: `trap 'failure ${LINENO} "$BASH_COMMAND"' ERR`
- Scripts expect cluster admin access and active `oc login` session

---

## Gaps & Caveats

**Critical gaps:**
1. ❌ **No tests** — No unit tests, integration tests, or any test files
2. ❌ **No linters** — No code quality tools (flake8, pylint, shellcheck automation)
3. ❌ **No CI/CD** — No automated validation or gating
4. ❌ **No dependency management** — No requirements.txt, pyproject.toml, or package manifest
5. ❌ **No build process** — Collection of scripts, not a packaged artifact

**Why this is expected:**
- This repository is **developer tooling**, not production code
- Scripts are utilities for DSP developers working on `data-science-pipelines` and `data-science-pipelines-operator` repos
- Each script/tool is standalone and task-specific

**Infrastructure requirements:**
- dev-setup scripts require:
  - Active OpenShift 4.11+ cluster with cluster-admin access
  - DSP Operator (DSPO) deployed
  - DataSciencePipelinesApplication (DSPA) instance running
  - `oc` CLI logged in to cluster
- KFP pipeline examples require:
  - Kubeflow Pipelines SDK (`pip install kfp`)
  - DSP instance to submit pipelines to
  - Cluster access for pipeline execution

**Cannot be validated in isolation:**
- Scripts interact with live clusters via `oc` commands
- Pipeline examples are KFP DAG definitions, not executable Python
- No local/offline execution mode

---

## How to Use This Repository (Developer Notes)

This is not an agent-validatable repository. It is intended for human developers working on Data Science Pipelines.

**If you need to:**

1. **Set up local DSP API server development:**
   - Follow `dev-setup/README.md`
   - Requires: OCP 4.11+ cluster, DSPO deployed, DSPA instance, cluster-admin access
   - Run: `./dev-setup/main.sh <namespace> <dspa_name> <kubeconfig> <output_dir>`
   - Generated files in `output/` configure API server for local debugging

2. **Run fraud detection pipeline example:**
   - Follow `example-pipelines/fraud-detection/README.md`
   - Requires: KFP SDK, DSP instance, cluster access
   - Edit `client_run.py` with namespace/DSPA name, then `./client_run.py`
   - Or compile to YAML: `./build_yaml.py` → submit `fraud_detection.yaml` to DSP

3. **Build toolbox container:**
   - `cd toolbox && podman build -t dsp-toolbox .`
   - Includes: oc, kubectl, kustomize, yq, minio CLI, huggingface CLI, podman

4. **Deploy components:**
   - Argo Server: see `manifests/deploy-argo-server/README.md`
   - KFP: see `manifests/deploy-kfp/openshift/README.md`
   - Cloudbeaver DB viewer: `oc apply -k cloudbeaver/overlays/dsp/`

---

## Agent Readiness Assessment

**Rating: none**

**Reasoning:**
- No test infrastructure to validate patches against
- No linting to enforce code quality
- No CI/CD to determine gating requirements
- Repository is a collection of developer utilities, not a library/application
- Scripts require live cluster infrastructure, cannot run in isolation

**Recommendation for agents:**
- **Do not attempt to validate patches** — this repo has no validation infrastructure
- **Do not attempt to run scripts** — they require cluster-admin access to live OCP clusters
- **Syntax validation only** — can verify Python/shell syntax, but not runtime behavior
- **Document changes clearly** — human review is the only gate

**What an agent CAN do:**
- ✅ Check Python syntax: `python -m py_compile <file>`
- ✅ Check shell syntax: `bash -n <file>`
- ✅ Review YAML manifests for schema validity (kubectl dry-run)
- ✅ Document what a change does

**What an agent CANNOT do:**
- ❌ Run tests (none exist)
- ❌ Run linters (none configured)
- ❌ Execute scripts (require cluster access)
- ❌ Validate KFP pipelines (require DSP instance)
- ❌ Determine if changes break functionality (no CI)

---

## Summary

This repository provides developer tooling for Data Science Pipelines (DSP) development. It is not a software project with tests, linting, or CI/CD. All scripts are syntactically valid, but require live OpenShift/Kubernetes cluster infrastructure to execute. Agent-based patch validation is **not possible** — human review is required.

For actual DSP code validation, see:
- https://github.com/opendatahub-io/data-science-pipelines
- https://github.com/opendatahub-io/data-science-pipelines-operator
