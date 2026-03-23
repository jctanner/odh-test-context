# Test Context: distributed-workloads (opendatahub-io)

**Generated:** 2026-03-22T21:59:52Z
**Agent Readiness:** MEDIUM — Go linting and unit tests work in standard container; full integration tests require Kubernetes cluster with ODH/RHOAI.

## Overview

This repository contains integration tests for OpenDataHub (ODH) distributed workload components including KubeFlow Training Operator (KFTO), Ray, Kueue, and Foundation Model Stack (FMS). It's primarily a Go test suite with Python training scripts as test fixtures.

**Languages:** Go 1.24.6 (primary), Python 3.12 (training examples)
**Build System:** Go modules + Make + Podman
**Test Framework:** Go testing with gomega assertions, gotestsum runner

## Container Recipe

This is the complete, validated recipe for running lint and tests in a container.

### 1. Start Container

```bash
podman run -d \
  --name test-context-distributed-workloads \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.24 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-distributed-workloads bash -c \
  "apt-get update -qq && apt-get install -y make git"
```

### 3. Install Go Dependencies

```bash
podman exec test-context-distributed-workloads bash -c \
  "cd /app && go mod download"
```

**Validation:** ✓ Completed successfully with no errors.

### 4. Run Linting

**Go Import Organization (VALIDATED ✓):**

```bash
podman exec test-context-distributed-workloads bash -c \
  "cd /app && make verify-imports"
```

**Expected output:** `./hack/verify-imports.sh /app/bin/openshift-goimports` (exit 0 = pass)

**Auto-fix imports:**

```bash
podman exec test-context-distributed-workloads bash -c \
  "cd /app && make imports"
```

**Validation:** ✓ Passed with exit code 0. No import violations detected.

**Python Linting (NOT VALIDATED - requires Python environment):**

The repository uses pre-commit hooks for Python files. To run Python linting, you need a Python 3.12 environment:

```bash
# In a Python 3.12 container or environment:
pip install pre-commit black isort flake8
pre-commit run --all-files
```

Python linting config in `.pre-commit-config.yaml`:
- `black` - code formatter
- `isort --profile black` - import sorting
- `flake8 --ignore=E203,W503 --max-line-length=88` - style checking

### 5. Run Tests

**Unit Tests (VALIDATED ✓):**

```bash
podman exec test-context-distributed-workloads bash -c \
  "cd /app && go test -timeout 30s ./tests/common/support/..."
```

**Validation:** ✓ 30 tests passed in 0.020s. These tests mock Kubernetes resources and don't require cluster access.

**Full Test Suite (requires Kubernetes cluster):**

```bash
# Requires KUBECONFIG pointing to cluster with ODH/RHOAI installed
podman exec test-context-distributed-workloads bash -c \
  "cd /app && go test -timeout 60m ./tests/kfto/"
```

**Test Subdirectories:**
- `./tests/common/support/...` - Unit tests for support utilities (✓ works without cluster)
- `./tests/kfto/...` - KubeFlow Training Operator integration tests
- `./tests/fms/...` - Foundation Model Stack tests
- `./tests/odh/...` - OpenDataHub integration tests
- `./tests/trainer/...` - Trainer v2 tests

**Single Test File:**

```bash
go test -timeout 60m ./tests/kfto/kfto_mnist_training_test.go
```

**Single Test Function:**

```bash
go test -timeout 60m -run TestPyTorchJobMnistMultiNodeSingleCpu ./tests/kfto/
```

**Compile Tests (as done in CI):**

```bash
podman exec test-context-distributed-workloads bash -c \
  "cd /app && go test -c -o compiled-tests/kfto ./tests/kfto"
```

**Validation:** ✓ Compilation successful. Creates 79MB test binary.

### 6. Cleanup

```bash
podman rm -f test-context-distributed-workloads
```

## Validation Results

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Install Deps | `go mod download` | 0 | ✓ PASS | Dependencies downloaded cleanly |
| Lint (Go) | `make verify-imports` | 0 | ✓ PASS | No import violations |
| Unit Tests | `go test ./tests/common/support/...` | 0 | ✓ PASS | 30 tests passed in 0.020s |
| Compile Tests | `go test -c ./tests/kfto` | 0 | ✓ PASS | 79MB binary created |
| Lint (Python) | `pre-commit run --all-files` | - | ⚠ SKIP | Requires Python environment |
| Integration Tests | `go test ./tests/kfto/...` | - | ⚠ SKIP | Requires K8s cluster |

**Summary:** install OK, lint OK (0 violations), unit tests OK (30 passed), compilation OK

## CI/CD

### GitHub Actions

**Gating Check (runs on PR/push):**

`.github/workflows/verify_generated_files.yml`:
```yaml
name: verify-imports
trigger: pull_request (Go files changed)
command: make verify-imports
```

**Build Test Image (runs on push to main):**

`.github/workflows/build-and-push-test-images.yml`:
```yaml
trigger: push to main (tests/** or go.mod changed)
commands:
  - make build-test-image
  - make push-test-image
```

**Release (manual workflow_dispatch):**

`.github/workflows/odh-release.yml`:
```bash
go test -c -o compiled-tests/fms ./tests/fms
go test -c -o compiled-tests/kfto ./tests/kfto
go test -c -o compiled-tests/odh ./tests/odh
gh release create $VERSION compiled-tests/*
```

### Tekton Pipelines

Extensive Tekton pipelines in `.tekton/` build training runtime container images:
- Multiple Python/CUDA/ROCm/PyTorch combinations
- Security scanning (Snyk, Clair, ClamAV)
- Triggers on path changes to `images/runtime/training/**`

Tekton pipelines are **not gating for code changes** — they build images when runtime Dockerfiles change.

## Conventions

**Test File Naming:** `*_test.go`

**Test Function Naming:** `func TestPyTorchJobMnistMultiNodeSingleCpu(t *testing.T)`

**Test Tagging:**
```go
Tags(t, Sanity, MultiNode(3))  // Mark test tier and node requirements
Tags(t, KftoCuda)              // Mark GPU requirement
```

**Test Organization:**
```
tests/
├── common/           # Shared test utilities and support functions
│   ├── support/      # Test helpers (unit tested ✓)
│   └── resources/    # Shared fixtures
├── fms/              # Foundation Model Stack tests
│   ├── kfto/         # FMS + KFTO integration
│   └── trainer/      # FMS + Trainer v2
├── kfto/             # KubeFlow Training Operator tests
├── odh/              # OpenDataHub integration tests
└── trainer/          # Trainer v2 tests
```

**Import Organization:**
Go imports grouped via `openshift-goimports`:
1. Standard library
2. External packages
3. k8s.io packages
4. Internal packages

Python imports use `isort --profile black`.

## Environment Variables

**Test Execution:**
- `TEST_OUTPUT_DIR` - Output directory for test logs (default: `/tmp`)
- `TEST_TIMEOUT_SHORT`, `TEST_TIMEOUT_MEDIUM`, `TEST_TIMEOUT_LONG` - Timeout durations
- `TEST_TIER` - Filter tests by tier: Smoke, Sanity, Tier1, Tier2, Tier3, Pre-Upgrade, Post-Upgrade

**Cluster Access (required for integration tests):**
- `KUBECONFIG` - Path to kubeconfig for cluster with ODH/RHOAI
- `ODH_NAMESPACE` - Namespace where ODH components are installed
- `TEST_NAMESPACE_NAME` - Optional existing namespace for GPU tests

**ML/Model Dependencies:**
- `TEST_RAY_IMAGE` - Ray image for RayCluster (default: `quay.io/modh/ray:2.47.1-py312-cu128`)
- `FMS_HF_TUNING_IMAGE` - Image tag for PyTorchJob model training
- `HF_TOKEN` - HuggingFace token for restricted model access
- `GPTQ_MODEL_PVC_NAME` - PVC name containing GPTQ models

**S3 Storage (optional, for dataset/model upload):**
- `AWS_DEFAULT_ENDPOINT` - S3 endpoint
- `AWS_ACCESS_KEY_ID` - S3 access key
- `AWS_SECRET_ACCESS_KEY` - S3 secret key
- `AWS_STORAGE_BUCKET` - S3 bucket name
- `AWS_STORAGE_BUCKET_MODEL_PATH` - Path in bucket for trained models
- `AWS_STORAGE_BUCKET_MNIST_DIR` - Path for MNIST datasets

## Gaps & Caveats

### What Works Without Cluster

✓ Go import linting (`make verify-imports`)
✓ Unit tests in `tests/common/support/` (mock K8s clients)
✓ Test compilation (`go test -c`)
✓ Python linting (with Python env setup)

### What Requires Cluster Access

✗ Integration tests in `tests/kfto/`, `tests/fms/`, `tests/odh/`, `tests/trainer/`
✗ Tests that create PyTorchJobs, RayJobs, RayClusters
✗ Tests that validate Kueue scheduling
✗ Tests that require GPU nodes (CUDA, ROCm)

### Other Gaps

- **No golangci-lint:** Only import organization is linted, no other Go style/quality checks
- **No coverage measurement:** No coverage targets or CI collection
- **Python scripts not tested:** Python files in `tests/*/resources/` are fixtures, not independently tested
- **External dependencies:** Tests need S3 storage, HuggingFace tokens, pre-trained models, datasets
- **Long running:** Integration tests can take 60+ minutes per suite

### Test Infrastructure Requirements

To run the full test suite, you need:

1. **Kubernetes cluster** (OpenShift 4.12+, CRC, or Kind with ODH components)
2. **OpenDataHub or RHOAI** installed with distributed workload components:
   - KubeFlow Training Operator
   - Kueue
   - Ray Operator
3. **GPU nodes** (NVIDIA or AMD) for CUDA/ROCm tests
4. **S3-compatible storage** for model/dataset persistence
5. **Sufficient cluster resources** (tests create multi-node workloads)

**Cluster setup is documented in README.md** but not automated.

## Quick Start for Agents

**To validate a Go code patch:**

1. Start container: `podman run -d --name test-context-distributed-workloads -v $(pwd):/app:Z -w /app golang:1.24 sleep infinity`
2. Install deps: `podman exec test-context-distributed-workloads bash -c "apt-get update -qq && apt-get install -y make git && go mod download"`
3. Run lint: `podman exec test-context-distributed-workloads bash -c "cd /app && make verify-imports"`
4. Run unit tests: `podman exec test-context-distributed-workloads bash -c "cd /app && go test ./tests/common/support/..."`
5. Cleanup: `podman rm -f test-context-distributed-workloads`

**Exit codes:**
- 0 = pass
- Non-zero = lint violations or test failures

**To validate a Python patch:**

Set up Python 3.12 environment, install `pre-commit black isort flake8`, then run `pre-commit run --all-files`.

## References

- **README.md** - Test prerequisites, environment variables, running tests
- **images/tests/Dockerfile** - Official test container definition (uses gotestsum)
- **.pre-commit-config.yaml** - Python linting configuration
- **Makefile** - Available make targets
- **.github/workflows/** - CI workflow definitions
