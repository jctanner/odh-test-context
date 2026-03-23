# Test Context for fips-compliance-checker-claude-code-plugin

**Analyzed**: 2026-03-22T22:11:00Z
**Agent Readiness**: **medium** — Tests can run on a properly configured host with podman, but require complex setup (container runtime) and currently have 2/10 test failures. No linting or CI configured.

---

## Overview

This is a **Claude Code plugin** providing FIPS 140-3 compliance scanning capabilities. It's implemented entirely in bash shell scripts with no build or compilation required.

- **Languages**: Bash
- **Build System**: None (executable scripts)
- **Test Framework**: Custom bash test script with jq-based JSON validation
- **CI/CD**: None configured

The scanner analyzes Python projects for FIPS compliance violations by checking dependencies, source code patterns, and running Bandit (a Python security linter) in a container.

---

## Container Recipe

### Important Note: Container-in-Container Limitations

This project's tests require running a container runtime (podman/docker) because the scanner itself runs Bandit in a container (`ghcr.io/pycqa/bandit/bandit:latest`). **Container-in-container setups are complex and often fail**. The recommended approach is to run tests on a **host with properly configured podman or docker**, not in a nested container.

### Host-Based Testing (Recommended)

On a host with bash, jq, and podman/docker installed:

```bash
# Prerequisites
# - bash (standard on Linux)
# - jq: dnf install jq (RHEL/Fedora) or apt install jq (Debian/Ubuntu)
# - podman: dnf install podman or apt install podman

# Run tests
cd /path/to/repo
bash tests/test-python-scanner.sh
```

**Expected Result**: 8/10 tests pass, 2 test assertions fail (MD5 detection and false positive detection). Exit code 1.

### Container-Based Testing (Limited Support)

If you must validate in a container (understanding it may not work due to nested container issues):

```bash
# 1. Start container with repo mounted
podman run -d --name test-fips-checker \
  -v /path/to/repo:/app:Z \
  -w /app \
  bash:latest \
  sleep infinity

# 2. Install dependencies
podman exec test-fips-checker apk add --no-cache jq podman

# 3. Attempt to run tests (may fail due to nested podman)
podman exec test-fips-checker bash tests/test-python-scanner.sh

# 4. Cleanup
podman rm -f test-fips-checker
```

**Expected Result in Container**: Tests likely fail with exit code 126 or JSON parsing errors because the scanner can't properly run Bandit in a nested container environment.

---

## Validation Results

### Host Validation (Successful)

Command:
```bash
bash tests/test-python-scanner.sh
```

**Exit Code**: 1 (2 test assertions failed, but infrastructure works)

**Output**:
```
═══════════════════════════════════════════════
 FIPS Python Scanner Integration Tests
═══════════════════════════════════════════════

✓ Scanner script exists and is executable
✓ Violating project scan detects violations
  Found 4 violation(s)
✓ Detects pycryptodome in dependencies
✗ Detects MD5 usage in source code
  MD5 usage not detected
✓ Context metadata is present in findings
✓ Test code is marked as non-production
✗ usedforsecurity=False detected as lower severity
  usedforsecurity=False not detected as false positive indicator
✓ Compliant project has minimal/no violations
✓ Scanner outputs valid JSON
✓ Scanner returns correct exit codes
  Violating project exit code: 1

Tests run:    10
Tests passed: 8
Tests failed: 2
```

**Analysis**: The test infrastructure works. The scanner successfully detects violations, outputs valid JSON, and returns correct exit codes. Two test assertions fail because the scanner doesn't detect all expected patterns, but this is a scanner implementation issue, not a testing infrastructure issue.

### Container Validation (Failed)

**Exit Code**: 1 (7/10 tests failed due to nested container issues)

**Analysis**: Tests fail in a containerized environment because the scanner requires a working container runtime to execute Bandit. Nested container setups (podman-in-podman) don't work reliably without significant configuration.

---

## CI/CD

**Status**: ❌ No CI configured

- No `.github/workflows/` directory
- No Tekton pipelines
- No Jenkins configuration
- No automated test execution on pull requests

**Impact**: Changes are not automatically tested. Contributors must run tests manually.

---

## Linting

**Status**: ❌ No linting configured

- No shellcheck configuration
- No `.shellcheckrc` file
- No pre-commit hooks
- No linting in test workflow

**Recommendation**: Add shellcheck to validate bash scripts:

```bash
# Install shellcheck
dnf install shellcheck  # or apt install shellcheck

# Run on all scripts
find scripts/ tests/ -name "*.sh" -exec shellcheck {} +
```

---

## Testing

### Test Command

```bash
bash tests/test-python-scanner.sh
```

### Test Structure

- **Test Script**: `tests/test-python-scanner.sh`
- **Test Fixtures**: `tests/fixtures/python/compliant_project/` and `tests/fixtures/python/violating_project/`
- **Test Count**: 10 tests
- **Current Status**: 8 pass, 2 fail (on host with working podman)

### Test Coverage

1. ✅ Scanner script exists and is executable
2. ✅ Violating project scan detects violations
3. ✅ Detects pycryptodome in dependencies
4. ❌ Detects MD5 usage in source code (assertion fails)
5. ✅ Context metadata is present in findings
6. ✅ Test code is marked as non-production
7. ❌ usedforsecurity=False detected as lower severity (assertion fails)
8. ✅ Compliant project has minimal/no violations
9. ✅ Scanner outputs valid JSON
10. ✅ Scanner returns correct exit codes

### Dependencies

Tests require:

- `bash` (any recent version)
- `jq` (JSON processor) - Install: `dnf install jq` or `apt install jq`
- `podman` or `docker` (container runtime)
- Network access to pull `ghcr.io/pycqa/bandit/bandit:latest` (on first run)

### Single Test Execution

The test script doesn't support running individual tests. To run a single test, you would need to:

1. Comment out unwanted test calls in the `main()` function
2. Or extract the specific test function and call it directly

---

## Build

**Status**: ⚠️ No build required

This project consists of executable bash scripts. No compilation, transpilation, or build step is needed.

To "install" the plugin:
- Clone the repository
- Ensure scripts are executable: `chmod +x scripts/python/*.sh tests/*.sh`
- Install dependencies: `jq`, `podman` (or `docker`)

---

## Conventions

### Shell Script Conventions

- All scripts use `set -euo pipefail` for strict error handling
- Scripts are organized in `scripts/python/lib/` for modular components
- Main scanner: `scripts/python/scan-python-fips.sh`
- Test script: `tests/test-python-scanner.sh`

### Test Conventions

- Test functions named `test_*`
- Test runner counts pass/fail and exits with appropriate code
- Tests validate JSON output using `jq`
- Color-coded output: green for pass, red for fail

### Test Fixtures

- Located in `tests/fixtures/python/`
- Two fixture projects: `compliant_project` (clean) and `violating_project` (intentional violations)
- Fixtures simulate real Python projects with dependencies and source code

---

## Gaps & Caveats

### Critical Gaps

1. **No CI/CD**: Tests are not run automatically on pull requests or commits
2. **No Linting**: Bash scripts have no shellcheck or other linting validation
3. **Complex Test Setup**: Tests require a working container runtime (podman/docker) with network access
4. **Container-in-Container Fails**: Cannot validate in a nested container environment
5. **2/10 Test Failures**: Current test assertions for MD5 detection and false positive handling fail

### Infrastructure Requirements

- **Container Runtime**: Tests absolutely require podman or docker with ability to pull images
- **Network Access**: First run downloads `ghcr.io/pycqa/bandit/bandit:latest` (~50MB)
- **Air-gapped Environments**: Must pre-pull Bandit image: `podman pull ghcr.io/pycqa/bandit/bandit:latest`

### Test Reliability

- ✅ Tests work reliably on host with proper podman/docker setup
- ❌ Tests fail in containerized environments (nested container issue)
- ⚠️ 2 test assertions currently fail (scanner implementation, not infrastructure)

### Workarounds

**For air-gapped environments**:
```bash
# Pre-pull Bandit container
podman pull ghcr.io/pycqa/bandit/bandit:latest

# Then run tests normally
bash tests/test-python-scanner.sh
```

**For container validation**:
Use a VM or host with podman instead of trying to validate in a container.

---

## Recommendations for Downstream Agents

### For Patch Validation

1. **Run on Host**: Execute tests on a host with working podman, not in a container
2. **Check Dependencies First**: Verify `jq` and `podman` are available before running tests
3. **Network Access**: Ensure ability to pull container images (or pre-pull Bandit)
4. **Accept Test Failures**: Current baseline is 8/10 tests passing
5. **Focus on Regressions**: New patches should not decrease the test pass rate below 8/10

### For Setting Up Validation

```bash
# Check prerequisites
command -v bash && echo "✓ bash" || echo "✗ bash missing"
command -v jq && echo "✓ jq" || echo "✗ jq missing"
command -v podman && echo "✓ podman" || echo "✗ podman missing"

# Pull Bandit image (one-time setup)
podman pull ghcr.io/pycqa/bandit/bandit:latest

# Run tests
bash tests/test-python-scanner.sh

# Expected: 8/10 pass, exit code 1
```

### For Adding Linting

```bash
# Install shellcheck
dnf install shellcheck

# Lint all scripts
find scripts/ tests/ -name "*.sh" -exec shellcheck {} +
```

---

## Summary

This repository is a **medium readiness** for automated patch validation:

- ✅ Tests exist and are runnable
- ✅ Scanner functional (8/10 tests pass)
- ✅ JSON output for machine parsing
- ❌ No CI/CD automation
- ❌ No linting configured
- ⚠️ Complex setup (requires container runtime)
- ⚠️ Container-in-container validation not practical

**Best validation approach**: Run tests on a Linux host with bash, jq, and podman installed. Accept that 8/10 tests pass as the baseline.
