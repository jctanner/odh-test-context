# Test Context Analysis: sdg-hub

**Repository:** opendatahub-io/sdg-hub
**Branch:** odh-tests
**Analyzed:** 2026-03-22
**Agent Readiness:** none

---

## Overview

This is **not a traditional software repository**. It contains only a Dockerfile and
documentation—no source code, no tests, and no linting configuration.

The repository's sole purpose is to provide a container build configuration that:
1. Clones an external repository: https://github.com/Red-Hat-AI-Innovation-Team/sdg_hub.git
2. Installs it with dev dependencies: `pip install "sdg_hub[examples,dev]"`
3. Runs integration tests from that external repository

**Why agent_readiness is "none":**
An AI agent cannot validate patches against this repository because there is no code
here to validate. The Dockerfile itself could theoretically be linted or tested, but
no such infrastructure is configured.

---

## Repository Contents

```
sdg-hub/
├── Dockerfile.sdg-test   # Container recipe for testing external sdg_hub project
├── README.md             # Instructions for building and running the container
└── LICENSE               # Apache 2.0 license
```

No source code. No tests. No CI/CD. No linting.

---

## Container Recipe

This section documents how to build and run the test container, which tests an
**external** repository, not this one.

### 1. Build the Container

```bash
podman build \
  -f Dockerfile.sdg-test \
  --build-arg GIT_BRANCH=main \
  -t sdg-hub-tester:latest \
  .
```

**Build arguments:**
- `GIT_BRANCH`: Branch of the external sdg_hub repo to clone (default: main)
- `SDG_HUB_VERSION`: Version to install from PyPI (default: latest)

**Base image:**
```
quay.io/opendatahub/workbench-images:jupyter-minimal-ubi9-python-3.12-pr-2113
```

**What the build does:**
1. Pulls the base workbench image (UBI9 + Python 3.12)
2. Installs git (already present in base image)
3. Clones https://github.com/Red-Hat-AI-Innovation-Team/sdg_hub.git
4. Installs sdg_hub package with extras: `pip install "sdg_hub[examples,dev]"`
5. Sets working directory to `/opt/app-root/src/sdg_hub`
6. Configures entrypoint to run: `python -m pytest tests/integration/ -v`

### 2. Run the Integration Tests

```bash
podman run --rm \
  -e OPENAI_API_KEY="your-api-key-here" \
  sdg-hub-tester:latest
```

**Required environment variables:**
- `OPENAI_API_KEY`: Valid OpenAI API key (integration tests call OpenAI API)

**What this does:**
- Runs pytest on the integration tests of the **external** sdg_hub repository
- Tests run inside the container against the cloned upstream code
- Container is automatically removed after tests finish (`--rm` flag)

### 3. Validation Status

**Dockerfile build:** ✅ VALIDATED
The Dockerfile is syntactically correct and builds successfully:
- Base image pulls without errors
- Git package installs (already present)
- External repository clones successfully
- pip install begins successfully

**Integration tests:** ❌ NOT VALIDATED
Cannot run without a valid OPENAI_API_KEY. Tests also run against external code,
not this repository.

### 4. No Linting or Testing for This Repository

This repository has:
- ❌ No linter configured for the Dockerfile
- ❌ No tests for the container structure
- ❌ No CI/CD pipeline
- ❌ No pre-commit hooks

To validate changes to `Dockerfile.sdg-test`, manually:
1. Build the container
2. Run it with a valid OPENAI_API_KEY
3. Verify integration tests pass

---

## CI/CD

**Status:** None configured

There are no GitHub Actions workflows, Tekton pipelines, or other CI systems.
Container builds and tests are run manually.

---

## Conventions

Not applicable—this repository contains no code.

---

## Gaps & Caveats

1. **No code in this repository:** Only a Dockerfile and README exist. There is
   nothing to lint or test in this repo itself.

2. **No CI/CD:** No automated builds or tests. Everything is manual.

3. **Tests external code:** The Dockerfile tests the upstream
   Red-Hat-AI-Innovation-Team/sdg_hub repository, not opendatahub-io/sdg-hub.

4. **Requires external credentials:** Integration tests need OPENAI_API_KEY,
   preventing automated validation in isolated environments.

5. **No container structure tests:** The Dockerfile itself is not tested (no
   container-structure-test, Trivy scans, or similar).

6. **No Dockerfile linting:** No hadolint, dockerfile_lint, or similar tools
   configured.

7. **Unclear purpose:** Why does opendatahub-io have a separate repository just
   to test Red-Hat-AI-Innovation-Team/sdg_hub? This could be a GitHub Actions
   workflow instead of a standalone repository.

8. **Outdated base image tag:** Uses a specific PR build of the workbench image
   (`pr-2113`), which may not be stable or up-to-date.

---

## Recommendations for Agent-Assisted Development

**For this repository (opendatahub-io/sdg-hub):**

This repository is not suitable for AI-assisted patch validation because it contains
no code. If you want to enable automated validation:

1. Add Dockerfile linting (hadolint):
   ```yaml
   # .github/workflows/lint.yml
   name: Lint Dockerfile
   on: [pull_request]
   jobs:
     hadolint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: hadolint/hadolint-action@v3.1.0
           with:
             dockerfile: Dockerfile.sdg-test
   ```

2. Add container structure tests:
   ```yaml
   # .github/workflows/test.yml
   name: Test Container
   on: [pull_request]
   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Build container
           run: podman build -f Dockerfile.sdg-test -t sdg-hub-tester:test .
         - name: Run structure tests
           run: container-structure-test test --image sdg-hub-tester:test --config tests/structure.yaml
   ```

3. Add security scanning (Trivy):
   ```yaml
   - name: Scan image
     uses: aquasecurity/trivy-action@master
     with:
       image-ref: sdg-hub-tester:test
   ```

**For testing the actual sdg_hub code:**

If you want to validate patches to the Red-Hat-AI-Innovation-Team/sdg_hub
repository, analyze *that* repository, not this one. This repository is just a
wrapper around it.

---

## Summary

- **What this repo is:** A Dockerfile that builds a test container for an external project
- **What this repo is NOT:** A code repository with tests and linting
- **Agent readiness:** None—there's nothing here to validate patches against
- **Recommendation:** Add Dockerfile linting and container structure tests, or merge
  this into the upstream sdg_hub repository as a `.github/workflows/` integration test

**Bottom line:** An AI agent trying to validate patches will find nothing to validate
here. Direct the agent to the actual sdg_hub repository if you want to test that code.
