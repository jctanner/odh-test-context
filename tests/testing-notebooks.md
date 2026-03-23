# Test Context: testing-notebooks

**Generated:** 2026-03-22T20:22:51-04:00
**Repository:** opendatahub-io/testing-notebooks
**Agent Readiness:** LOW - Test fixture repository with no native validation infrastructure

## Overview

This repository contains **Jupyter notebook test fixtures** used by OpenShift CI tests in the
[odh-manifests](https://github.com/opendatahub-io/odh-manifests/tree/master/tests) repository.
It is **not a testable codebase** itself - the notebooks are consumed by external JupyterHub
integration tests.

**What this repo contains:**
- 3 Jupyter notebooks (basic.ipynb, spark.ipynb, tensorflow.ipynb)
- No test framework, no linting config, no CI/CD, no build system

**Agent readiness rating: LOW**
Reason: This is a test fixture repository. While notebooks can be validated for JSON structure
and basic.ipynb can be executed, there is no test suite or linting configuration to validate
patches against. The notebooks themselves are tested by external infrastructure in odh-manifests.

---

## Container Recipe

This recipe validates notebook JSON structure and attempts execution. Only basic.ipynb executes
successfully in isolation - the others require external infrastructure (Spark cluster, TensorFlow 1.x).

### 1. Start container

```bash
podman run -d --name test-context-testing-notebooks \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11-slim \
  sleep infinity
```

### 2. Install dependencies

```bash
podman exec test-context-testing-notebooks bash -c "pip install -q nbconvert ipykernel nbqa ruff"
```

### 3. Validate notebook JSON structure

```bash
podman exec test-context-testing-notebooks bash -c "cd /app && python -m json.tool basic.ipynb > /dev/null && echo 'basic.ipynb: valid JSON'"
podman exec test-context-testing-notebooks bash -c "cd /app && python -m json.tool spark.ipynb > /dev/null && echo 'spark.ipynb: valid JSON'"
podman exec test-context-testing-notebooks bash -c "cd /app && python -m json.tool tensorflow.ipynb > /dev/null && echo 'tensorflow.ipynb: valid JSON'"
```

**Expected result:** All 3 notebooks are valid JSON ✓

### 4. Lint notebooks (optional)

```bash
podman exec test-context-testing-notebooks bash -c "cd /app && nbqa ruff *.ipynb"
```

**Expected result:** `All checks passed!` ✓

### 5. Execute basic.ipynb

```bash
podman exec test-context-testing-notebooks bash -c "cd /app && jupyter nbconvert --to notebook --execute basic.ipynb --output /tmp/basic_executed.ipynb"
```

**Expected result:** SUCCESS - notebook executes and outputs:
```
[NbConvertApp] Converting notebook basic.ipynb to notebook
[NbConvertApp] Writing 1972 bytes to /tmp/basic_executed.ipynb
```

### 6. Attempt spark.ipynb (will fail without infrastructure)

```bash
podman exec test-context-testing-notebooks bash -c "cd /app && pip install -q pyspark"
podman exec test-context-testing-notebooks bash -c "cd /app && jupyter nbconvert --to notebook --execute spark.ipynb --output /tmp/spark_executed.ipynb 2>&1 | tail -10"
```

**Expected result:** FAILED - `KeyError: 'SPARK_CLUSTER'`
**Reason:** Requires `SPARK_CLUSTER` environment variable pointing to a live Spark cluster.

### 7. Attempt tensorflow.ipynb (will fail with TF 2.x)

```bash
podman exec test-context-testing-notebooks bash -c "cd /app && pip install -q tensorflow"
podman exec test-context-testing-notebooks bash -c "cd /app && jupyter nbconvert --to notebook --execute tensorflow.ipynb --output /tmp/tensorflow_executed.ipynb 2>&1 | tail -10"
```

**Expected result:** FAILED - `AttributeError: module 'tensorflow' has no attribute 'Session'`
**Reason:** Uses TensorFlow 1.x API (`tf.Session()`) incompatible with TensorFlow 2.x.

### 8. Cleanup

```bash
podman rm -f test-context-testing-notebooks
```

---

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| JSON validation | `python -m json.tool *.ipynb` | ✓ PASS | All notebooks are valid JSON |
| Linting | `nbqa ruff *.ipynb` | ✓ PASS | No violations found |
| Execute basic.ipynb | `jupyter nbconvert --execute basic.ipynb` | ✓ PASS | Runs successfully |
| Execute spark.ipynb | `jupyter nbconvert --execute spark.ipynb` | ✗ FAIL | Requires SPARK_CLUSTER env var + live cluster |
| Execute tensorflow.ipynb | `jupyter nbconvert --execute tensorflow.ipynb` | ✗ FAIL | Requires TensorFlow 1.x (deprecated) |

### Summary

**Working validations:**
- JSON structure validation (all notebooks)
- Code quality linting with ruff (all notebooks)
- Execution of basic.ipynb

**Failing validations:**
- spark.ipynb requires external Spark cluster infrastructure
- tensorflow.ipynb requires TensorFlow 1.x (incompatible with modern TensorFlow 2.x)

---

## CI/CD

**System:** None

This repository has **no CI/CD configuration**. Testing happens externally:
- The notebooks are consumed by tests in [odh-manifests/tests/basictests/jupyterhub](https://github.com/opendatahub-io/odh-manifests/tree/master/tests/basictests)
- Tests run in OpenShift CI environments with appropriate infrastructure (JupyterHub, Spark clusters)
- This repo serves as a test fixture library only

**No gating checks** exist in this repository.

---

## Conventions

### Notebook Structure

All notebooks follow a consistent pattern:
- Valid Jupyter Notebook JSON format (nbformat 4)
- Python 3 kernel (though tensorflow.ipynb has Python 2 syntax)
- Final cell prints `"End Of Notebook"` - likely used by external tests to verify complete execution

### Notebooks

1. **basic.ipynb**
   - Simple Python print statements
   - No external dependencies
   - Can execute in any Python 3 environment
   - Purpose: Basic JupyterHub functionality test

2. **spark.ipynb**
   - Requires `pyspark` package
   - Requires `SPARK_CLUSTER` environment variable
   - Requires live Spark cluster at `spark://<SPARK_CLUSTER>:7077`
   - Purpose: Validate Spark integration in JupyterHub

3. **tensorflow.ipynb**
   - Uses TensorFlow 1.x API (deprecated)
   - `tf.Session()` incompatible with TensorFlow 2.x
   - Contains Python 2 syntax (`print sess.run()`)
   - Purpose: Validate TensorFlow support in JupyterHub (using old TF 1.x)

---

## Gaps & Caveats

### No Test Infrastructure

This repository **does not contain tests** - it contains test fixtures (notebooks). The actual
tests that consume these notebooks live in the [odh-manifests](https://github.com/opendatahub-io/odh-manifests)
repository. There is no way to validate patches to this repo except to:
1. Validate notebook JSON structure
2. Attempt execution in appropriate environments
3. Run the external test suite in odh-manifests

### Missing Configuration

- **No linting config** - no `.pre-commit-config.yaml`, `pyproject.toml`, or similar
- **No CI/CD** - no `.github/workflows/`, no Tekton, no Jenkins
- **No dependency management** - no `requirements.txt`, `Pipfile`, `poetry.lock`
- **No build system** - no `Makefile`, `setup.py`, `package.json`
- **No documentation** - README only describes what the repo is used for, not how to validate it

### Infrastructure Dependencies

- **spark.ipynb** cannot be executed without:
  - Live Spark cluster (typically in OpenShift/Kubernetes)
  - `SPARK_CLUSTER` environment variable
  - Network connectivity to Spark master on port 7077

- **tensorflow.ipynb** cannot be executed with modern TensorFlow:
  - Requires TensorFlow 1.x (last release: TF 1.15.5 in 2020)
  - Uses deprecated `tf.Session()` API removed in TF 2.x
  - Contains Python 2 syntax

### Patch Validation Strategy

For patches to this repository, an agent can:

1. **Validate JSON structure** - ensure notebooks are valid Jupyter notebook JSON
2. **Lint code cells** - use `nbqa ruff` to check Python code quality
3. **Execute basic.ipynb** - verify it runs without errors
4. **Document changes** - note if spark/tensorflow notebooks are modified
5. **Cannot validate end-to-end** - true validation requires running external test suite in odh-manifests

**Recommendation:** For meaningful validation, patches should be tested by running the
JupyterHub integration tests in the odh-manifests repository's CI environment.

---

## Quick Validation Commands

For a quick patch validation, run these commands in a Python 3.11 container:

```bash
# Validate JSON
python -m json.tool basic.ipynb > /dev/null && echo "✓ basic.ipynb valid"
python -m json.tool spark.ipynb > /dev/null && echo "✓ spark.ipynb valid"
python -m json.tool tensorflow.ipynb > /dev/null && echo "✓ tensorflow.ipynb valid"

# Install and lint (optional)
pip install -q nbqa ruff
nbqa ruff *.ipynb

# Execute basic notebook
pip install -q nbconvert ipykernel
jupyter nbconvert --to notebook --execute basic.ipynb --output /tmp/basic_executed.ipynb
```

If all three commands succeed, the notebooks are structurally valid and basic.ipynb executes correctly.
This is the maximum validation possible without external infrastructure.
