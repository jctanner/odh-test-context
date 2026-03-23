# Test Context: data-processing

**Agent Readiness: MEDIUM** — Format and structure validation work perfectly in standard containers. Notebook execution requires GPU infrastructure.

## Overview

- **Repository**: opendatahub-io/data-processing
- **Primary Language**: Python 3.12
- **Purpose**: Data processing pipelines and notebooks for document conversion and chunking using Docling
- **Build System**: make + pip
- **Test Framework**: pytest
- **CI System**: GitHub Actions

**What works in a standard container:**
- ✅ Python formatting validation (ruff)
- ✅ Notebook formatting validation (nbstripout)
- ✅ Notebook parameter validation (pytest)

**What requires GPU infrastructure:**
- ⚠️ Notebook execution tests (papermill with docling, transformers, milvus)
- ⚠️ KFP pipeline local execution
- ⚠️ KFP pipeline compilation (requires docling + tesserocr)

## Container Recipe

This recipe provides **partial validation** — an agent can verify formatting and notebook structure but cannot execute notebooks or compile KFP pipelines without GPU infrastructure.

### 1. Start Container

```bash
podman run -d --name test-data-processing \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.12 \
  sleep infinity
```

### 2. Install Dependencies

```bash
podman exec test-data-processing bash -c "cd /app && pip install -r requirements-dev.txt"
```

**Expected output:** Installs ruff, nbstripout, pytest, nbformat, papermill, ipykernel, jupyter and dependencies.

**Exit code:** 0

### 3. Run Format Check (Python)

```bash
podman exec test-data-processing bash -c "cd /app && make format-python-check"
```

**What it does:** Checks that Python files in `kubeflow-pipelines/` are formatted with ruff.

**Expected output:**
```
ruff format --check kubeflow-pipelines/common/*.py ...
9 files already formatted
ruff format check passed :)
```

**Exit code:** 0 if formatted correctly, 1 if formatting issues found.

**Validated:** ✅ Passed with 9 files formatted correctly.

### 4. Run Format Check (Notebooks)

```bash
podman exec test-data-processing bash -c "cd /app && make format-notebooks-check"
```

**What it does:** Checks that Jupyter notebooks have outputs stripped using nbstripout.

**Expected output:**
```
nbstripout --keep-id --verify notebooks/**/*.ipynb
nbstripout check passed :)
```

**Exit code:** 0 if notebooks properly stripped, 1 if outputs present.

**Validated:** ✅ Passed with 6 notebooks verified.

### 5. Run Notebook Parameter Tests

```bash
podman exec test-data-processing bash -c "cd /app && make test-notebook-parameters"
```

**What it does:** Validates that all notebooks have a code cell tagged with 'parameters' (required for papermill execution).

**Expected output:**
```
============================= test session starts ==============================
...
tests/test_notebook_parameters.py::test_notebook_has_parameters_cell[notebook_path0] PASSED [ 14%]
...
============================== 7 passed in 1.02s ===============================
```

**Exit code:** 0 if all notebooks have parameters cells, 1 if validation fails.

**Validated:** ✅ Passed — 7 tests (6 notebooks + 1 validator test).

### 6. Run Single Test File

```bash
podman exec test-data-processing bash -c "cd /app && pytest tests/test_notebook_parameters.py -v"
```

**Template for single file:** `pytest {file} -v`

**Template for single test:** `pytest {file}::{test_name} -v`

### 7. Optional: Check Ruff Linting (Not Enforced in CI)

```bash
podman exec test-data-processing bash -c "cd /app && ruff check kubeflow-pipelines/"
```

**What it does:** Runs ruff's lint checks (import sorting, pyupgrade rules).

**Expected output:** May report violations like I001 (import sorting), UP015, UP017.

**Note:** This is configured but **NOT enforced in CI**. Only format checking is gating.

**Validated:** ⚠️ Found 3 violations but this is not a CI failure.

### 8. Cleanup

```bash
podman rm -f test-data-processing
```

**Always run cleanup**, even if validation fails.

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| Install | `pip install -r requirements-dev.txt` | ✅ Pass | All deps installed cleanly |
| Lint (Python) | `make format-python-check` | ✅ Pass | 9 files formatted |
| Lint (Notebooks) | `make format-notebooks-check` | ✅ Pass | 6 notebooks verified |
| Test (Parameters) | `make test-notebook-parameters` | ✅ Pass | 7 tests passed |
| Test (Execution) | `pytest tests/test_notebook_execution.py` | ⚠️ Skip | Requires GPU + ML deps |
| Lint (Ruff Check) | `ruff check kubeflow-pipelines/` | ⚠️ Not CI | 3 violations found |

**Summary:** Install OK, format checks OK (Python + notebooks), parameter tests OK (7 passed). Notebook execution tests not run (require GPU/ML dependencies).

## CI/CD

### Gating Checks (Required for PR Merge)

These checks run on `pull_request` and must pass before merging:

#### 1. Python Formatting Validation
- **Workflow:** `.github/workflows/validate-python.yml`
- **Trigger:** PRs that modify `**/*.py` files
- **Command:** `make format-python-check`
- **Python:** 3.12
- **What it checks:** Ruff format compliance for Python files in `kubeflow-pipelines/`

#### 2. Validate Notebooks - Formatting
- **Workflow:** `.github/workflows/validate-notebooks.yml`
- **Trigger:** PRs that modify `notebooks/**/*.ipynb`
- **Command:** `make format-notebooks-check`
- **Python:** 3.12
- **What it checks:** Notebooks have outputs stripped with nbstripout

#### 3. Validate Notebooks - Parameters
- **Workflow:** `.github/workflows/validate-notebooks.yml`
- **Trigger:** PRs that modify `notebooks/**/*.ipynb`
- **Command:** `make test-notebook-parameters`
- **Python:** 3.12
- **What it checks:** Notebooks have required 'parameters' cell tag

#### 4. Compile KFP Pipelines
- **Workflow:** `.github/workflows/compile-kfp.yml`
- **Trigger:** PRs that modify `kubeflow-pipelines/` files
- **Commands:**
  ```bash
  pip install -r kubeflow-pipelines/docling-standard/requirements.txt
  cd kubeflow-pipelines/docling-standard && python standard_convert_pipeline.py
  diff standard_convert_pipeline_compiled.yaml <committed> <generated>
  ```
- **Python:** 3.12
- **What it checks:** Pipeline code changes include regenerated compiled YAML
- **Note:** Requires heavy dependencies (docling==2.57.0, tesserocr==2.9.1)

#### 5. Test Local Pipeline Runners
- **Workflow:** `.github/workflows/execute-kfp-localrunners.yml`
- **Trigger:** PRs that modify `kubeflow-pipelines/` files
- **Infrastructure:** AWS EC2 g6e.xlarge GPU instance
- **Commands:**
  ```bash
  # Runs on EC2 with Docker, GPU drivers
  cd kubeflow-pipelines/docling-standard && python local_run.py
  cd kubeflow-pipelines/docling-vlm && python local_run.py
  ```
- **Note:** **Only runs on upstream repo** (opendatahub-io/data-processing), not forks

### Advisory Checks (Post-Merge)

#### Execute All Notebooks
- **Workflow:** `.github/workflows/execute-all-notebooks.yml`
- **Trigger:** `push` to `main` branch (not PRs)
- **Infrastructure:** AWS EC2 g6e.xlarge GPU instance with CUDA 12.4
- **Command:** `pytest tests/test_notebook_execution.py -v`
- **What it does:** Full notebook execution with papermill
- **Dependencies:** docling, transformers, milvus-lite, GPU-specific PyTorch

### Fork Behavior

Forks receive a **PR check notification** but GPU-dependent tests (KFP local runners, notebook execution) are skipped. Only formatting and parameter validation run on forks.

## Conventions

### Test Files
- **Pattern:** `tests/test_*.py`
- **Naming:** pytest convention (`test_*` functions, `test_*` files)
- **Discovery:** `pytest tests/` finds all test files
- **Config:** `pyproject.toml` under `[tool.pytest.ini_options]`

### Notebooks
- **Naming:** Descriptive kebab-case (e.g., `document-conversion-standard.ipynb`)
- **Organization:** `notebooks/use-cases/` and `notebooks/tutorials/`
- **Required:** All notebooks must have a code cell tagged with `parameters` for papermill
- **Format:** Outputs must be stripped with `nbstripout --keep-id`

### Python Code
- **Style:** Ruff format (line-length=88, target-version=py312)
- **Imports:** Ruff configured for import sorting (I001)
- **Location:** Python code lives in `kubeflow-pipelines/` subdirectories
- **Python Version:** 3.12

### Code Review
- Pipeline changes must include regenerated compiled YAML
- Notebooks must have parameters cells
- All outputs must be stripped before commit

## Gaps & Caveats

1. **No unit tests for Python code** — Only notebook validation exists. The Python code in `kubeflow-pipelines/` has no unit tests, only integration tests via local pipeline execution.

2. **Ruff linting not enforced** — `ruff check` is configured in `pyproject.toml` with rules for import sorting and pyupgrade, but CI only runs `ruff format --check`. Linting violations don't block PRs.

3. **Notebook execution requires GPU** — `pytest tests/test_notebook_execution.py` needs:
   - CUDA 12.4
   - GPU (g6e.xlarge or equivalent)
   - Heavy ML dependencies (docling, transformers, milvus)
   - System libraries (libcusparselt, CUDA runtime)
   - Special LD_LIBRARY_PATH configuration

   **Cannot run in standard containers.**

4. **KFP compilation requires tesserocr** — `pip install -r kubeflow-pipelines/*/requirements.txt` needs:
   - tesserocr (requires libtesseract system package)
   - docling (large ML library)

   **Not validated in this container recipe.**

5. **Fork limitations** — Forks cannot run GPU-dependent CI checks. They get PR check notifications but only basic validation actually executes.

6. **AWS infrastructure required** — Full CI testing requires:
   - AWS account with configured OIDC
   - EC2 GPU instances (g6e.xlarge)
   - GitHub secrets (AWS_ACCOUNT_ID, QUAY credentials)
   - IAM roles and security groups

   **Only available to upstream repository maintainers.**

7. **Test asset dependency** — `test_notebook_execution.py` has special handling for `subset-selection.ipynb` which requires a test asset file `tests/assets/subset-selection/combined_cut_50x.jsonl`. The test infrastructure has notebook-specific parameter overrides.

## Quick Commands for Agents

### Validate a patch (format + structure only)
```bash
# Start container
podman run -d --name validate -v $(pwd):/app:Z -w /app python:3.12 sleep infinity

# Install deps
podman exec validate bash -c "pip install -r requirements-dev.txt"

# Run checks
podman exec validate bash -c "make format-python-check"
podman exec validate bash -c "make format-notebooks-check"
podman exec validate bash -c "make test-notebook-parameters"

# Cleanup
podman rm -f validate
```

### Fix formatting issues
```bash
podman exec validate bash -c "cd /app && ruff format kubeflow-pipelines/"
podman exec validate bash -c "cd /app && nbstripout --keep-id notebooks/**/*.ipynb"
```

### Run specific test
```bash
podman exec validate bash -c "pytest tests/test_notebook_parameters.py::test_validator_itself -v"
```

## Dependencies

### Development Dependencies (`requirements-dev.txt`)
- ruff>=0.1.0 — Format and lint
- nbstripout>=0.6.0 — Strip notebook outputs
- pytest>=7.0.0 — Test framework
- nbformat>=5.7.0 — Notebook format handling
- papermill>=2.4.0 — Notebook execution
- ipykernel>=6.20.0 — Jupyter kernel
- jupyter>=1.0.0 — Notebook infrastructure

### KFP Pipeline Dependencies (Heavy, Not in Container Recipe)
- docling==2.57.0 — Document processing
- kfp==2.14.6 — Kubeflow Pipelines
- tesserocr==2.9.1 — OCR (requires system libtesseract)
- boto3==1.40.52 — AWS SDK

### Notebook Execution Dependencies (Requires GPU)
See `tests/requirements-gpu.txt` — Includes PyTorch with CUDA, transformers, milvus-lite

## What Agents Can Do

### ✅ Reliable Validation (Standard Container)
- Verify Python code formatting with ruff
- Verify notebook output stripping with nbstripout
- Validate notebook structure (parameters cells)
- Run parameter validation tests
- Parse test output and report issues

### ⚠️ Partial Validation (Requires Setup)
- Compile KFP pipelines (needs docling, tesserocr, system deps)
- Check for ruff linting violations (configured but not enforced)

### ❌ Cannot Validate (Requires GPU Infrastructure)
- Execute notebooks with papermill
- Run KFP local pipeline tests
- Test ML model loading/inference
- Validate CUDA/GPU compatibility
- Test milvus-lite integration

## Recommended Workflow for Agents

1. **Always validate:** Format (Python + notebooks), parameters
2. **Report but don't block:** Ruff lint violations (not enforced in CI)
3. **Flag for human review:** Changes to KFP pipelines (compilation not tested)
4. **Trust upstream CI:** GPU-dependent tests run on EC2 in upstream CI

An agent can provide **confident pass/fail** on formatting and structure. For execution testing, the agent should note that "execution tests require GPU infrastructure and will run in upstream CI."
