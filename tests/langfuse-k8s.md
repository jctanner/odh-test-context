# Test Context: langfuse-k8s

**Agent Readiness: HIGH** — Lint and test commands validated successfully. An agent can validate patches with clear pass/fail signals.

## Overview

This is a Helm chart repository for deploying Langfuse (an open-source LLM observability platform) on Kubernetes. The repository contains YAML configuration files (Helm charts) with no traditional programming code.

- **Languages:** YAML, Helm charts
- **Build System:** Helm v3.13.2+
- **Test Framework:** helm-unittest v1.0.0
- **Linting:** helm lint, helm-docs
- **CI System:** GitHub Actions
- **Test Count:** 52 unit tests across 9 test suites

---

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

Use the Alpine Helm image with custom entrypoint to run validation commands:

```bash
podman run -d --name test-context-langfuse-k8s \
  --entrypoint /bin/sh \
  -v $(pwd):/app:Z \
  -w /app \
  docker.io/alpine/helm:3.13.2 \
  -c "sleep infinity"
```

**Note:** Replace `$(pwd)` with the absolute path to the repository root if needed.

### 2. Install System Dependencies

Install required tools in the container:

```bash
podman exec test-context-langfuse-k8s sh -c \
  "apk add --no-cache wget git bash curl"
```

### 3. Install Helm Chart Dependencies

Download the chart dependencies (PostgreSQL, ClickHouse, Valkey/Redis, MinIO, Common):

```bash
podman exec test-context-langfuse-k8s sh -c \
  "cd /app && helm dependency update charts/langfuse/"
```

**Expected output:** Downloads 5 charts from Bitnami OCI registry
**Exit code:** 0
**Validation status:** ✅ PASSED (validated successfully)

### 4. Run Helm Lint

Validate the Helm chart syntax and structure:

```bash
podman exec test-context-langfuse-k8s sh -c \
  "cd /app && helm lint charts/langfuse/ -f charts/langfuse/values.lint.yaml"
```

**Expected output:** `1 chart(s) linted, 0 chart(s) failed`
**Exit code:** 0 (success), non-zero if lint errors found
**Validation status:** ✅ PASSED (0 charts failed)

### 5. Install Helm Unittest Plugin

Install the helm-unittest plugin to run unit tests:

```bash
podman exec test-context-langfuse-k8s sh -c \
  "helm plugin install https://github.com/helm-unittest/helm-unittest.git --version v1.0.0"
```

**Expected output:** Plugin installation success message
**Exit code:** 0

### 6. Run Helm Unit Tests

Execute all unit tests to validate chart rendering with various configurations:

```bash
podman exec test-context-langfuse-k8s sh -c \
  "cd /app && helm unittest charts/langfuse/ --color"
```

**Expected output:**
```
Charts:      1 passed, 1 total
Test Suites: 9 passed, 9 total
Tests:       52 passed, 52 total
```

**Exit code:** 0 (all tests pass), non-zero if tests fail
**Validation status:** ✅ PASSED (52/52 tests passed in 2.78s)

### 7. Run Single Test File (Optional)

To run a specific test file:

```bash
podman exec test-context-langfuse-k8s sh -c \
  "cd /app && helm unittest charts/langfuse/ -f charts/langfuse/tests/basic_test.yaml"
```

### 8. Cleanup

Always remove the container when finished:

```bash
podman rm -f test-context-langfuse-k8s
```

---

## Validation Results

All discovered commands were validated in an Alpine Helm 3.13.2 container:

| Step | Command | Exit Code | Result | Notes |
|------|---------|-----------|--------|-------|
| **Install Dependencies** | `helm dependency update charts/langfuse/` | 0 | ✅ PASS | Downloaded 5 chart dependencies from Bitnami OCI registry |
| **Lint** | `helm lint charts/langfuse/ -f charts/langfuse/values.lint.yaml` | 0 | ✅ PASS | 1 chart linted, 0 charts failed |
| **Unit Tests** | `helm unittest charts/langfuse/ --color` | 0 | ✅ PASS | 52/52 tests passed across 9 test suites in 2.78s |

**helm-docs validation:** Skipped in Alpine container due to glibc dependency incompatibility. This tool works correctly in the Ubuntu-based CI environment. An agent can skip this check or use an Ubuntu-based container if helm-docs validation is required.

---

## CI/CD

### Gating Checks (Required for PR Merge)

These checks run on pull requests and must pass before merging:

#### 1. Validate Helm Chart (`.github/workflows/validate.yaml`)

Triggered on PRs that modify `charts/**` files.

```bash
# Update dependencies
helm dependency update charts/langfuse/

# Run helm lint
helm lint charts/langfuse/ -f charts/langfuse/values.lint.yaml

# Validate documentation is up to date
helm-docs charts/langfuse/
git diff --stat  # Fails if docs are out of sync
```

**Required:** Yes
**Tools:** Helm v3.13.2, helm-docs v1.14.2

#### 2. Run Helm Unit Tests (`.github/workflows/test.yaml`)

Triggered on all PRs and pushes to `main`.

```bash
# Install helm-unittest plugin
helm plugin install https://github.com/helm-unittest/helm-unittest.git --version v1.0.0

# Update dependencies
helm dependency update charts/langfuse/

# Run unit tests with JUnit output
helm unittest charts/langfuse/ --color --output-type JUnit --output-file test-results.xml
```

**Required:** Yes
**Test Count:** 52 tests across 9 test suites
**Test Files:**
- `charts/langfuse/tests/basic_test.yaml`
- `charts/langfuse/tests/clickhouse-cluster_test.yaml`
- `charts/langfuse/tests/downward-api_test.yaml`
- `charts/langfuse/tests/extra-containers_test.yaml`
- `charts/langfuse/tests/extra-env_test.yaml`
- `charts/langfuse/tests/ingress_test.yaml`
- `charts/langfuse/tests/minimal-installation_test.yaml`
- `charts/langfuse/tests/redis-cluster_test.yaml`
- `charts/langfuse/tests/s3-media-upload-validation_test.yaml`

### Advisory Checks (Non-Blocking)

#### Release Chart (`.github/workflows/release.yaml`)

Triggered on push to `main` when `charts/*/Chart.yaml` changes. Packages and publishes the chart to GitHub Container Registry and creates GitHub releases.

---

## Conventions

### Test File Naming

Test files must be located in `charts/langfuse/tests/` and follow the pattern:
- `*_test.yaml` (e.g., `basic_test.yaml`, `ingress_test.yaml`)

### Test Structure

Helm unit tests use YAML-based assertions:

```yaml
suite: test suite name
templates:
  - template1.yaml
  - template2.yaml
tests:
  - it: should do something
    values:
      - ../values.lint.yaml
    set:
      some.value: "override"
    asserts:
      - isKind:
          of: Deployment
      - equal:
          path: metadata.name
          value: expected-name
```

### Helm Chart Conventions

- **Values files:** Nested structure with component sections (`langfuse`, `postgresql`, `clickhouse`, `redis`, `s3`)
- **Templates:** Located in `charts/langfuse/templates/` organized by component (`web/`, `worker/`)
- **Dependencies:** Declared in `Chart.yaml`, downloaded from Bitnami OCI registry
- **Lint values:** `values.lint.yaml` provides test values for required secrets during validation

---

## Gaps & Caveats

### Known Limitations

1. **helm-docs incompatibility with Alpine:** The helm-docs binary requires glibc and cannot run in Alpine-based containers that use musl libc. This check works correctly in Ubuntu-based CI. Agents can skip helm-docs validation or use an Ubuntu-based container (e.g., `ubuntu:22.04` with Helm installed).

2. **No runtime validation:** Helm unit tests validate template rendering but cannot test actual Kubernetes runtime behavior without deploying to a real cluster. Tests verify YAML structure, not pod startup, networking, or storage.

3. **No coverage metrics:** Coverage is not applicable for Helm charts. Tests validate that templates render correctly with various value combinations.

4. **OCI registry dependency:** Chart dependencies are pulled from `registry-1.docker.io/bitnamicharts`. Network access to Docker Hub is required.

### Infrastructure Requirements

- **None** — All validation runs in a container without external dependencies
- **Network access** — Required to download chart dependencies from Docker Hub OCI registry

### Common Issues

**Issue:** Dependencies fail to download
**Cause:** Network issues or Docker Hub rate limiting
**Solution:** Retry or use authenticated registry access

**Issue:** Tests fail with "template not found"
**Cause:** Dependencies not installed
**Solution:** Run `helm dependency update charts/langfuse/` before tests

---

## Quick Reference

### Essential Commands

```bash
# Install dependencies
helm dependency update charts/langfuse/

# Run lint
helm lint charts/langfuse/ -f charts/langfuse/values.lint.yaml

# Run all tests
helm unittest charts/langfuse/ --color

# Run specific test file
helm unittest charts/langfuse/ -f charts/langfuse/tests/basic_test.yaml

# Generate documentation (requires glibc, not Alpine-compatible)
helm-docs charts/langfuse/
```

### Container Images

- **Primary:** `docker.io/alpine/helm:3.13.2` — Validated, works for lint and tests
- **Alternative:** `ubuntu:22.04` + Helm installation — Use if helm-docs validation is required

### Exit Codes

- **0** — Success (lint passed, all tests passed)
- **Non-zero** — Failure (lint errors found, test failures, or command error)

---

## Agent Readiness Assessment

**Rating: HIGH**

An AI agent can fully validate patches in this repository with clear success/failure signals:

✅ **Dependency install** works in standard container
✅ **Lint command** validated successfully (0 failures)
✅ **Test command** validated successfully (52/52 tests passed)
✅ **Clear exit codes** indicate pass/fail
✅ **No external infrastructure** required (databases, clusters, etc.)

**Confidence: HIGH** — All critical validation commands were executed successfully in a container and produce deterministic results.
