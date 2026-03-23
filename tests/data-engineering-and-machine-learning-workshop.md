# Test Context: data-engineering-and-machine-learning-workshop

**Agent Readiness: NONE** - This is a workshop/training repository with no test infrastructure, no CI/CD, and deprecated dependencies.

---

## Overview

**Repository**: opendatahub-io/data-engineering-and-machine-learning-workshop
**Type**: Workshop/Training Materials
**Languages**: Python (TensorFlow 1.x), Jupyter Notebooks
**Primary Purpose**: Hands-on workshop for Data Engineering and Machine Learning on OpenShift using Open Data Hub

**Code Inventory**:
- 2 Python files (175 lines total): TensorFlow Random Forest training and serving
- 4 Jupyter notebooks: Kafka producer/consumer, hybrid data engineering, TF training/serving
- OpenShift deployment templates and workshop documentation
- Presentation slides and supporting materials

**Critical Finding**: This repository has **no test infrastructure**. No tests, no test frameworks, no CI/CD, no linters. It's workshop training code, not production software meant for automated validation.

---

## Container Recipe

This recipe demonstrates that the Python code has valid syntax and can be imported, but there are no tests to run.

### Step 1: Start Container

```bash
podman run -d --name test-context-deml-workshop \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.7 \
  sleep infinity
```

**Why Python 3.7?** TensorFlow 1.13 (the latest available version for this old code) requires Python 3.7 maximum.

### Step 2: Install Dependencies

```bash
# Install TensorFlow 1.13 (train code wants 1.9.0 but it's no longer available)
podman exec test-context-deml-workshop bash -c "pip install 'tensorflow==1.13.*' boto3"
```

**Expected Output**: Successfully installs TensorFlow 1.13.2, boto3, and dependencies (grpcio, protobuf, tensorboard, numpy, etc.)

### Step 3: Fix Protobuf Incompatibility

```bash
# Downgrade protobuf for TensorFlow 1.x compatibility
podman exec test-context-deml-workshop bash -c "pip install 'protobuf<4.0'"
```

**Expected Output**: Installs protobuf 3.20.3

### Step 4: Validate Python Syntax

```bash
podman exec test-context-deml-workshop bash -c \
  "python -m py_compile source/tf-random-forest/train/app.py source/tf-random-forest/serve/ForestMnist.py"
```

**Expected**: Exit code 0, no output (syntax valid)
**Validation Result**: ✅ PASS

### Step 5: Test Imports

```bash
# Test TensorFlow import
podman exec test-context-deml-workshop bash -c \
  "python -c 'import tensorflow as tf; print(\"TensorFlow:\", tf.__version__)'"
```

**Expected Output**: `TensorFlow: 1.13.2` with FutureWarnings about numpy dtypes (expected for old TF version)
**Validation Result**: ✅ PASS (warnings are expected)

```bash
# Test application code import
podman exec test-context-deml-workshop bash -c \
  "cd /app && python -c \"import sys; sys.path.insert(0, 'source/tf-random-forest/serve'); from ForestMnist import ForestMnist; print('ForestMnist class OK')\""
```

**Expected Output**: `ForestMnist class OK` with TensorFlow FutureWarnings
**Validation Result**: ✅ PASS

### Step 6: Attempt to Run Tests

```bash
# There are no tests to run
podman exec test-context-deml-workshop bash -c "find /app -name '*test*.py' -o -name 'test_*.py'"
```

**Expected Output**: Empty (no test files found)
**Validation Result**: ⚠️ NO TESTS EXIST

### Step 7: Cleanup

```bash
podman rm -f test-context-deml-workshop
```

---

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Syntax Check | `python -m py_compile` | ✅ PASS | All Python files have valid syntax |
| Dependency Install | `pip install tensorflow==1.13.* boto3` | ✅ PASS | TF 1.13.2 installed (1.9.0 unavailable) |
| Protobuf Fix | `pip install 'protobuf<4.0'` | ✅ PASS | Required for TF 1.x compatibility |
| TensorFlow Import | `import tensorflow` | ✅ PASS | Works with FutureWarnings |
| Code Import | `from ForestMnist import ForestMnist` | ✅ PASS | Application code imports successfully |
| Lint | N/A | ⚠️ SKIP | No linter configured |
| Tests | N/A | ⚠️ SKIP | No tests exist |

**Summary**: Code is syntactically valid and can be imported with the correct environment (Python 3.7, TensorFlow 1.13.2, protobuf<4.0). However, there is no way to validate patches through automated testing because no tests exist.

---

## CI/CD

**Status**: No CI/CD infrastructure

- ❌ No `.github/workflows/` directory
- ❌ No `.tekton/` pipelines
- ❌ No `Jenkinsfile`
- ❌ No other CI configuration found

**Implication**: There is no authoritative source of truth for what commands should pass. No gating checks, no required status checks.

---

## Linting

**Status**: No linting configured

- ❌ No `.flake8` configuration
- ❌ No `pylintrc`
- ❌ No `ruff` config in `pyproject.toml` (no pyproject.toml exists)
- ❌ No `.pre-commit-config.yaml`
- ❌ No `Makefile` with lint targets

**Implication**: No way to validate code style or catch common errors automatically.

---

## Testing

**Status**: No test infrastructure

- ❌ No test files (`*_test.py`, `test_*.py`, etc.)
- ❌ No test directories (`tests/`, `test/`)
- ❌ No test framework configuration (no `pytest.ini`, `setup.cfg` with pytest config, etc.)
- ❌ No `tox.ini`
- ❌ No test dependencies in requirements files

**Implication**: Impossible to validate patches through automated tests. An agent can apply patches but cannot determine if they break functionality.

---

## Build System

**Status**: No build system

- ❌ No `setup.py`
- ❌ No `pyproject.toml`
- ❌ No `Makefile`
- ✅ Has `requirements.txt` files (but with version conflicts)

**Dependencies**:
- `source/tf-random-forest/train/requirements.txt`: `tensorflow==1.9.0` (no longer available), `boto3`
- `source/tf-random-forest/serve/requirements.txt`: `tensorflow==1.13.*`, `seldon-core`, `boto3`

**Installation Command** (best effort):
```bash
pip install 'tensorflow==1.13.*' 'protobuf<4.0' boto3 seldon-core
```

---

## Conventions

**Repository Structure**:
```
source/
  tf-random-forest/
    train/app.py          # TensorFlow Random Forest training script
    serve/ForestMnist.py  # Model serving class
  notebooks/              # Jupyter notebooks for workshop demos
deploy/                   # OpenShift deployment templates
doc/                      # Workshop documentation
slides/                   # Presentation materials
```

**Code Patterns**:
- Python files use standard imports
- Code expects environment variables for configuration (MODEL_NAME, MODEL_VERSION, S3_ENDPOINT_URL, AWS_ACCESS_KEY_ID, etc.)
- Training code downloads MNIST data to `/tmp/data/`
- Model artifacts are saved to S3-compatible object storage

**Runtime Requirements**:
- S3-compatible object storage (for model artifacts)
- OpenShift cluster (for actual deployment)
- Environment variables for AWS credentials and model configuration

---

## Gaps & Caveats

### Critical Gaps

1. **No Test Infrastructure**: No tests, no test framework, no way to validate patches automatically
2. **No CI/CD**: No GitHub Actions, no automated checks, no gating criteria
3. **No Linting**: No code quality checks configured
4. **No Build System**: No setup.py or pyproject.toml for proper package management

### Dependency Issues

5. **Deprecated TensorFlow**: Uses TensorFlow 1.9.0/1.13.* from 2018, EOL and unmaintained
6. **Version Conflicts**: `train/requirements.txt` specifies TensorFlow 1.9.0 which is no longer available on PyPI
7. **Python Version Lock**: Requires Python 3.7 maximum (TensorFlow 1.13 incompatible with Python 3.8+)
8. **Protobuf Incompatibility**: Requires `protobuf<4.0` or TensorFlow imports fail

### Runtime Limitations

9. **External Infrastructure Required**: Code cannot actually run without:
   - S3-compatible object storage (Ceph, MinIO, AWS S3)
   - Configured AWS credentials
   - MNIST dataset download (requires internet access)
   - For serving: pre-trained model artifacts in S3

10. **Workshop Code**: This is training/demo code, not production software. It's designed to be run manually during a workshop, not as part of an automated pipeline.

### What This Means for Agents

An AI agent working with this repository can:
- ✅ Apply patches
- ✅ Check Python syntax
- ✅ Verify imports work (with correct environment)

An AI agent **cannot**:
- ❌ Run automated tests (none exist)
- ❌ Validate functionality (no test suite)
- ❌ Check code quality (no linters configured)
- ❌ Follow CI best practices (no CI defined)
- ❌ Determine if a patch breaks anything (no tests to run)

---

## Agent Readiness Rating: NONE

**Why NONE?**

This repository has no meaningful test infrastructure. There are no tests to run, no linters to execute, no CI checks to satisfy. The code is syntactically valid and can be imported, but that's the limit of automated validation.

An agent can:
- Clone the repository
- Apply patches
- Check Python syntax
- Verify imports work

An agent cannot:
- Determine if a patch breaks functionality
- Run tests (none exist)
- Validate against CI requirements (no CI exists)
- Check code quality automatically (no linters configured)

**Recommendation**: This repository is training material for workshops. It's not designed for automated patch validation. If patches are needed, they should be reviewed manually by someone who understands the workshop context and can test the code in a live OpenShift + Open Data Hub environment.

---

## How to Actually Validate Changes (Manual Process)

Since there are no automated tests, validating changes requires manual steps:

1. **Syntax Check**: Run `python -m py_compile` on modified files
2. **Import Check**: Try importing modified modules in Python 3.7 with TensorFlow 1.13.2
3. **Manual Testing**: Deploy to an OpenShift cluster with Open Data Hub installed, run through the workshop steps, verify the training and serving components work
4. **Workshop Validation**: Present the workshop to verify the training materials still make sense

This is not practical for an AI agent to perform automatically.

---

## Conclusion

This repository contains **workshop training materials**, not production code with automated validation. It has:

- ✅ Valid Python syntax
- ✅ Importable code (with Python 3.7 + TensorFlow 1.13.2 + protobuf<4.0)
- ❌ No tests
- ❌ No CI/CD
- ❌ No linters
- ❌ Deprecated dependencies (TensorFlow 1.x from 2018)

**For AI Agents**: This repository is **not suitable for automated patch validation**. An agent can apply patches and check syntax, but cannot determine if changes break functionality because no test infrastructure exists.
