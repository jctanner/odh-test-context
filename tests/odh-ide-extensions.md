# Test Context: odh-ide-extensions

**Generated:** 2026-03-22T23:40:15Z
**Repository:** opendatahub-io/odh-ide-extensions
**Agent Readiness:** HIGH - All core lint and test commands validated successfully in container

## Overview

OpenDataHub IDE Extensions monorepo containing JupyterLab extensions. Currently contains one extension: `odh-jupyter-trash-cleanup`. Languages: TypeScript/JavaScript (frontend), Python (backend). Build system: Turbo (monorepo), hatchling (Python), JupyterLab builder.

**Agent Readiness Rating: HIGH**
All lint commands pass cleanly. Unit tests (pytest) pass with 87% coverage. Jest tests are placeholders but framework works. Dependencies install without issues. An agent can validate patches end-to-end using only the commands in this document.

---

## Container Recipe

This is a complete, copy-paste recipe for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-odh-ide-extensions \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.10 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-odh-ide-extensions bash -c "
  apt-get update &&
  apt-get install -y curl git make gcc g++
"
```

### 3. Install Node.js 20

```bash
podman exec test-context-odh-ide-extensions bash -c "
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&
  apt-get install -y nodejs
"
```

Verify installation:
```bash
podman exec test-context-odh-ide-extensions bash -c "
  node --version && npm --version && python --version
"
# Expected: v20.x.x, npm 10.x.x, Python 3.10.x
```

### 4. Install Python Lint Dependencies

```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app &&
  python -m pip install -q -r lint_requirements.txt
"
```

Installs: black, flake8, flake8-import-order, flake8-pyproject, flake8-logging-format

### 5. Install JupyterLab

```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app &&
  python -m pip install -q -U 'jupyterlab>=4.0.0,<5'
"
```

This also installs `jlpm` (JupyterLab's package manager, which is yarn).

### 6. Install JavaScript Dependencies

```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app &&
  jlpm install
"
```

Takes ~20 seconds. Installs all workspace dependencies via yarn.

### 7. Run Lint Commands

**All linters (comprehensive):**
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app &&
  make EXTENSION=odh-jupyter-trash-cleanup lint
"
```

**Expected result:** Exit code 0. May see 1 ESLint warning about unused variable (non-blocking).

**Individual linters:**

Prettier (JavaScript/TypeScript formatting):
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app &&
  npx prettier 'odh-jupyter-trash-cleanup/**/*{.ts,.tsx,.js,.jsx,.css,.json,.md}' --check
"
```

ESLint (JavaScript/TypeScript linting):
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app &&
  npx eslint 'odh-jupyter-trash-cleanup/**/*.{ts,tsx,js,jsx}' --cache
"
```

Stylelint (CSS linting):
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app &&
  npx stylelint 'odh-jupyter-trash-cleanup/**/*.{css,scss}'
"
```

Flake8 (Python linting):
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app/odh-jupyter-trash-cleanup &&
  python -m flake8 .
"
```

Black (Python formatting):
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app &&
  python -m black --check --diff --color .
"
```

**Auto-fix commands:**
- Prettier: Add `--write` flag
- ESLint: Add `--fix` flag
- Stylelint: Add `--fix` flag
- Black: Remove `--check --diff`, just `python -m black .`

### 8. Run Unit Tests (Jest)

```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app/odh-jupyter-trash-cleanup &&
  jlpm run test
"
```

**Expected result:** Exit code 0. Currently 2 todo tests (placeholders).

**Run single test file:**
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app/odh-jupyter-trash-cleanup &&
  jlpm jest src/__tests__/odh_jupyter_trash_cleanup.spec.ts
"
```

**Run single test by name:**
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app/odh-jupyter-trash-cleanup &&
  jlpm jest -t 'activates the plugin without errors'
"
```

### 9. Install Python Package with Test Dependencies

```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app/odh-jupyter-trash-cleanup &&
  python -m pip install -q .[test]
"
```

### 10. Run Python Tests (pytest)

```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app/odh-jupyter-trash-cleanup &&
  pytest -vv -r ap --cov odh_jupyter_trash_cleanup
"
```

**Expected result:** Exit code 0. 6 tests passed, 87% coverage.

**Run single test file:**
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app/odh-jupyter-trash-cleanup &&
  pytest odh_jupyter_trash_cleanup/test_empty_trash.py
"
```

**Run single test:**
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app/odh-jupyter-trash-cleanup &&
  pytest odh_jupyter_trash_cleanup/test_empty_trash.py::test_empty_directory_returns_zero
"
```

**Coverage report:**
```bash
podman exec test-context-odh-ide-extensions bash -c "
  cd /app/odh-jupyter-trash-cleanup &&
  pytest --cov odh_jupyter_trash_cleanup --cov-report=html
"
```

### 11. Cleanup

```bash
podman rm -f test-context-odh-ide-extensions
```

**IMPORTANT:** Always clean up the container when done, even if validation fails.

---

## Validation Results

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| Install system deps | `apt-get install curl git make gcc g++` | 0 | ✅ Pass | Already present in base image |
| Install Node.js | `curl ... setup_20.x && apt-get install nodejs` | 0 | ✅ Pass | Node.js 20.20.1 installed |
| Install Python lint deps | `pip install -r lint_requirements.txt` | 0 | ✅ Pass | black, flake8, etc. installed |
| Install JupyterLab | `pip install jupyterlab>=4.0.0,<5` | 0 | ✅ Pass | jlpm available |
| Install JS deps | `jlpm install` | 0 | ✅ Pass | Completed in ~17s |
| Lint | `make EXTENSION=odh-jupyter-trash-cleanup lint` | 0 | ✅ Pass | 1 ESLint warning (unused var) |
| Jest tests | `jlpm run test` | 0 | ✅ Pass | 2 todo tests |
| Install Python package | `pip install .[test]` | 0 | ✅ Pass | Package installed |
| Pytest tests | `pytest -vv --cov` | 0 | ✅ Pass | 6 passed, 87% coverage |

**Summary:** All core validation steps successful. Lint passed with minor warning. All Python tests passed. Jest tests are placeholders but framework works.

---

## CI/CD Configuration

**System:** GitHub Actions
**Main workflow:** `.github/workflows/build_all_extensions.yml` → `.github/workflows/build_extension.yml`
**Triggers:** `pull_request` (all branches), `push` (main branch)
**Python version:** 3.10
**Node.js:** Installed via jupyterlab/maintainer-tools base-setup action

### Gating Checks (Required for Merge)

1. **Lint the extension**
   ```bash
   jlpm install
   make EXTENSION=odh-jupyter-trash-cleanup lint
   ```

2. **Test the extension (Jest)**
   ```bash
   cd odh-jupyter-trash-cleanup
   jlpm run test
   ```

3. **Build and test Python**
   ```bash
   cd odh-jupyter-trash-cleanup
   python -m pip install .[test]
   pytest -vv -r ap --cov odh_jupyter_trash_cleanup
   jupyter labextension list
   jupyter labextension list 2>&1 | grep -ie "odh-jupyter-trash-cleanup.*OK"
   python -m jupyterlab.browser_check
   ```

4. **Package the extension**
   ```bash
   cd odh-jupyter-trash-cleanup
   python -m pip install build
   python -m build
   ```

5. **Integration tests (Playwright)**
   ```bash
   make EXTENSION=odh-jupyter-trash-cleanup ui-tests-setup
   make EXTENSION=odh-jupyter-trash-cleanup ui-tests
   ```

   **Note:** Requires Playwright browser installation. Not validated in basic container setup.

6. **Test isolated install**
   - Installs built wheel in clean environment without Node.js
   - Verifies extension loads in JupyterLab

### Advisory Checks (Non-blocking)

- **Check Links:** Validates URLs in documentation

---

## Conventions

### Test File Naming

- **Jest (TypeScript):** `**/*.spec.ts` or `**/*.spec.tsx`
- **Playwright (TypeScript):** `ui-tests/tests/*.spec.ts`
- **Pytest (Python):** `test_*.py` or `*_test.py`

### Test Function Naming

- **Jest:** `describe()` and `it()` blocks
- **Pytest:** Functions starting with `test_`

### Code Style

- **TypeScript/JavaScript:**
  - Single quotes (enforced by prettier/eslint)
  - Interface names must start with `I` (PascalCase)
  - Curly braces required for all control structures
  - Arrow functions preferred for callbacks

- **Python:**
  - Black formatting: 79 character line length
  - Google import order style
  - Type hints not required but encouraged

### Import Style

- **TypeScript:** ESM imports (`import { foo } from './bar'`)
- **Python:** Google import order (stdlib, third-party, local)

---

## Gaps & Caveats

1. **Jest tests are placeholders:** Current tests are marked as `todo` and don't test actual functionality. The test framework works, but meaningful tests need to be written.

2. **UI tests require infrastructure:** Playwright integration tests require:
   - Chromium browser installation (`jlpm playwright install chromium`)
   - JupyterLab server running
   - Takes ~5 minutes to complete
   - Not validated in basic container setup (requires more resources)

3. **Semgrep not in CI:** `semgrep.yaml` config exists but is not integrated into CI workflow.

4. **Gitleaks not in CI:** `.gitleaks.toml` config exists but is not integrated into CI workflow.

5. **No root-level lint workflow:** CI only lints per-extension. Root-level config files exist but aren't validated by CI.

6. **Python 3.13 target version:** Black config targets Python 3.13 but CI uses Python 3.10, causing a warning (non-blocking).

---

## Quick Reference

**Lint everything:**
```bash
make EXTENSION=odh-jupyter-trash-cleanup lint
```

**Run all tests:**
```bash
cd odh-jupyter-trash-cleanup
jlpm run test                          # Jest
pytest -vv --cov odh_jupyter_trash_cleanup  # pytest
```

**Build for production:**
```bash
npm run build:prod
```

**Install extension locally:**
```bash
cd odh-jupyter-trash-cleanup
python -m pip install -e .[test]
```

**Common issues:**
- If jlpm fails: ensure Node.js 16+ is installed
- If black complains about Python version: use Python 3.10+
- If pytest can't find module: ensure you've run `pip install .[test]` from extension directory
