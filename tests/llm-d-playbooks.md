# Test Context: llm-d-playbooks

**Agent Readiness: NONE** — This repository contains deployment playbooks and documentation with no automated validation infrastructure.

---

## Overview

**Repository:** opendatahub-io/llm-d-playbooks
**Type:** Documentation and Kubernetes deployment manifests
**Languages:** YAML (33 files), Markdown (17 files), Python (3 scripts), Shell
**Build System:** None
**CI/CD:** None

This repository contains step-by-step playbooks for deploying [llm-d](https://github.com/llm-d/llm-d) on Kubernetes platforms (OpenShift, AKS, CoreWeave). It includes:

- Kubernetes YAML manifests organized by deployment steps (01-cluster-bring-up through 08-benchmarking)
- README documentation in each directory
- Three Python data generator scripts in `08-benchmarking/intelligent-inference-scheduler/test-data-generator/`
- No automated testing or linting infrastructure

**Why agent_readiness = none:**
There is no test or lint infrastructure to validate patches. An agent can apply changes to YAML or documentation, but cannot automatically verify correctness. Manual review or cluster deployment would be required to validate changes.

---

## Repository Structure

```
.
├── 01-cluster-bring-up/              # Kubernetes cluster setup
├── 02-operators/                     # Required operators installation
├── 03-control-plane-readiness/       # Control plane validation
│   └── validation/
├── 04-rdma-networking/               # RDMA network configuration
├── 05-rdma-network-validation/       # RDMA validation
│   └── validation/
├── 06-llm-d-deploy/                  # llm-d deployment
│   └── apply/
├── 07-llm-deployment-validation/     # Deployment validation
│   └── validation/
├── 08-benchmarking/                  # Benchmarking setup
│   └── intelligent-inference-scheduler/
│       ├── guidellm/                 # GuideLLM configs (kustomize)
│       ├── llm-d/                    # llm-d configs (kustomize)
│       ├── vllm/                     # vLLM configs (kustomize)
│       ├── monitoring/               # Grafana/Prometheus configs
│       └── test-data-generator/      # Python data generators
│           ├── heterogeneous/
│           ├── prefix/
│           └── requirements.txt
├── shared/                           # Common resources
└── README.md                         # Main documentation
```

---

## Python Scripts

The repository contains 3 Python data generator scripts (not tests):

1. **heterogeneous-workload-generator.py**
   Generates mixed workload CSV files with different prompt sizes

2. **kv-cache-prompt-generator.py**
   Generates prompts sized to fill KV-cache capacity

3. **prefix-cache-generator.py**
   Generates prompt pairs with shared prefixes

### Dependencies

```bash
pip install -r 08-benchmarking/intelligent-inference-scheduler/test-data-generator/requirements.txt
```

Contents: `pandas`, `guidellm==0.3.1`

### Running Scripts

All scripts use argparse and can be run with `--help`:

```bash
cd 08-benchmarking/intelligent-inference-scheduler/test-data-generator/heterogeneous
python heterogeneous-workload-generator.py --help
```

Example:
```bash
python heterogeneous-workload-generator.py \
  --workload-n-words 500 \
  --workload-m-words 10000 \
  --total-prompts 10000 \
  --ratio-n-to-m 9 \
  --output-csv heterogeneous-prompts.csv
```

---

## Container Recipe

While the repository has no validation commands to run, you can use a container to execute the Python data generators:

### 1. Start Container

```bash
podman run -d --name test-context-llm-d-playbooks \
  -v /home/jtanner/workspace/github/jctanner.redhat/2026_03_22_odh_test_context/odh-tests-context/checkouts/opendatahub-io/llm-d-playbooks:/app:Z \
  -w /app \
  python:3.11-slim \
  sleep infinity
```

### 2. Install Python Dependencies

```bash
podman exec test-context-llm-d-playbooks bash -c \
  "cd /app && pip install -r 08-benchmarking/intelligent-inference-scheduler/test-data-generator/requirements.txt"
```

### 3. Verify Python Scripts (Syntax Check)

```bash
# Check heterogeneous generator
podman exec test-context-llm-d-playbooks bash -c \
  "cd /app/08-benchmarking/intelligent-inference-scheduler/test-data-generator/heterogeneous && python heterogeneous-workload-generator.py --help"

# Check KV cache generator
podman exec test-context-llm-d-playbooks bash -c \
  "cd /app/08-benchmarking/intelligent-inference-scheduler/test-data-generator/prefix && python kv-cache-prompt-generator.py --help"

# Check prefix cache generator
podman exec test-context-llm-d-playbooks bash -c \
  "cd /app/08-benchmarking/intelligent-inference-scheduler/test-data-generator/prefix && python prefix-cache-generator.py --help"
```

### 4. Generate Sample Data (Functional Test)

```bash
# Run a small test generation to verify scripts work
podman exec test-context-llm-d-playbooks bash -c \
  "cd /app/08-benchmarking/intelligent-inference-scheduler/test-data-generator/heterogeneous && \
   python heterogeneous-workload-generator.py \
   --total-prompts 10 \
   --output-csv /tmp/test-heterogeneous.csv && \
   head -5 /tmp/test-heterogeneous.csv"
```

### 5. Cleanup

```bash
podman rm -f test-context-llm-d-playbooks
```

---

## Validation Results

**No automated validation infrastructure exists.**

| Validation Type | Status | Notes |
|----------------|--------|-------|
| YAML Linting | ❌ Not configured | Could add `yamllint` to validate Kubernetes manifests |
| Markdown Linting | ❌ Not configured | Could add `markdownlint` to validate documentation |
| Python Linting | ❌ Not configured | Could add `ruff` or `flake8` for Python scripts |
| Unit Tests | ❌ Not present | No test files found |
| Integration Tests | ❌ Not present | No tests to validate Kubernetes manifests |
| CI/CD | ❌ Not present | No GitHub Actions workflows |
| Kustomize Build | ❌ Not validated | Manifests use kustomize but no CI checks they build |

**Python Script Syntax:** ✅ All 3 Python scripts are valid Python (verified by reading them)

---

## CI/CD

**None configured.**

The repository has no `.github/workflows/` directory and no CI configuration.

### Recommended CI Checks (if added)

1. **YAML validation:**
   ```bash
   yamllint .
   ```

2. **Kustomize build validation:**
   ```bash
   kustomize build 08-benchmarking/intelligent-inference-scheduler/guidellm/base/
   kustomize build 08-benchmarking/intelligent-inference-scheduler/llm-d/base/
   kustomize build 08-benchmarking/intelligent-inference-scheduler/vllm/base/
   ```

3. **Python linting:**
   ```bash
   ruff check 08-benchmarking/intelligent-inference-scheduler/test-data-generator/
   ```

4. **Markdown linting:**
   ```bash
   markdownlint '**/*.md'
   ```

---

## Conventions

### Directory Structure
- Numbered directories (01-08) represent sequential deployment steps
- Each directory contains a README.md with instructions
- YAML manifests use kustomize for configuration management
- Base manifests in `base/` directories
- Overlays for different configurations (granite, qwen, etc.)

### YAML Manifests
- Kubernetes resource definitions (namespaces, services, inference services)
- Kustomize configurations for composable deployments
- Pod monitors for Prometheus metrics collection
- Gateway and routing configurations for llm-d

### Documentation
- Each deployment step has a README explaining purpose and procedures
- Main README.md provides overview and platform compatibility table
- test-data-generator has detailed usage docs

### Python Scripts
- Use argparse for CLI
- Include `--help` documentation
- Generate CSV output compatible with GuideLLM benchmarking tool
- Seeded random generation for reproducibility

---

## Gaps & Caveats

### Critical Gaps

1. **No CI/CD:** Changes to manifests or scripts are not validated automatically
2. **No YAML linting:** Syntax errors in Kubernetes manifests would only be caught during `kubectl apply`
3. **No kustomize validation:** No automated checks that kustomize can build the overlays
4. **No Python tests:** Data generator scripts have no unit tests
5. **No documentation linting:** Markdown files could have broken links or formatting issues

### Deployment Dependencies

This repository assumes:
- Access to a Kubernetes cluster (OpenShift/AKS/CoreWeave)
- Operators pre-installed (cert-manager, service mesh, KServe, LeaderWorkerSet)
- RDMA-capable networking hardware (for steps 04-05)
- GPU resources for LLM inference
- External image registries and model repositories

### Validation Limitations

**An agent cannot validate patches to this repository automatically** because:

- YAML manifests require `kubectl` and a Kubernetes cluster to validate
- Kustomize builds require the `kustomize` CLI
- Deployment validation requires an actual cluster with specific operators
- No tests exist to verify changes don't break functionality

**Manual validation required:**
- Review YAML syntax manually
- Test kustomize builds locally
- Deploy to a test cluster to verify manifests work
- Run Python scripts to verify they generate valid CSV

---

## How to Validate Patches (Manual Process)

Since automated validation is not available, patches to this repository should be validated manually:

### For YAML Changes

1. **Syntax check:**
   ```bash
   yamllint path/to/changed.yaml
   ```

2. **Kustomize build:**
   ```bash
   kustomize build path/to/directory/
   ```

3. **Dry-run apply (requires cluster):**
   ```bash
   kubectl apply --dry-run=client -k path/to/directory/
   ```

### For Python Changes

1. **Install dependencies:**
   ```bash
   pip install -r 08-benchmarking/intelligent-inference-scheduler/test-data-generator/requirements.txt
   ```

2. **Lint:**
   ```bash
   ruff check 08-benchmarking/intelligent-inference-scheduler/test-data-generator/
   ```

3. **Run script:**
   ```bash
   python script.py --help
   python script.py <args> --output /tmp/test.csv
   ```

### For Documentation Changes

1. **Lint Markdown:**
   ```bash
   markdownlint '**/*.md'
   ```

2. **Check links:**
   ```bash
   markdown-link-check README.md
   ```

3. **Manual review** of formatting and content

---

## Recommendations for Agent-Readiness Improvement

To make this repository agent-ready (move from **none** to **medium** or **high**):

1. **Add GitHub Actions CI** with jobs for:
   - YAML linting (`yamllint`)
   - Kustomize build validation
   - Python linting (`ruff` or `flake8`)
   - Markdown linting (`markdownlint`)

2. **Add unit tests** for Python data generators:
   - Test that generated CSV has correct format
   - Test that word counts match targets
   - Test reproducibility with same seed

3. **Add Makefile** with targets:
   - `make lint` - run all linters
   - `make test` - run all tests
   - `make validate-kustomize` - build all kustomize configs
   - `make generate-data` - run data generators

4. **Add pre-commit hooks** to catch issues before commit

5. **Document validation process** in CONTRIBUTING.md

With these changes, an agent could:
- Clone the repo
- Run `make lint` and `make test`
- Get clear pass/fail signals on patch correctness
- Achieve **high** agent readiness

---

## Summary

This repository is a well-organized collection of deployment playbooks for llm-d, but it has **no automated validation infrastructure**. An AI agent can read and modify files, but cannot validate changes without manual intervention or cluster access.

**Current state:** Documentation and manifests only
**Agent capability:** Can edit, cannot validate
**Required for validation:** Manual review + cluster deployment
**Improvement path:** Add CI/CD with linting and kustomize build checks
