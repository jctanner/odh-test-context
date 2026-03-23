# Test Context for ml-metadata (opendatahub-io)

**Generated**: 2026-03-22T23:10:00Z

## Overview

**ML Metadata (MLMD)** - A library for recording and retrieving metadata associated with ML workflows.

- **Languages**: C++ (core implementation), Python (API bindings), Go (SWIG bindings)
- **Build System**: Bazel 5.3.0 (exact version required)
- **Test Framework**: Bazel with googletest (C++) and absltest (Python)
- **Agent Readiness**: **LOW** - Tests exist but require complex Bazel setup with WORKSPACE patching. Cannot validate patches without replicating full production build environment.

**Justification**: The project has comprehensive tests but they cannot be run in a standard container due to outdated dependency checksums in the Bazel WORKSPACE file. The production CI only builds container images and does not run tests. Tests require Bazel 5.3.0 and manual patching of dependency files before they can execute.

---

## Container Recipe

⚠️ **WARNING**: This recipe documents the current state but tests cannot run without additional WORKSPACE patching (see Gaps section).

### 1. Start container

```bash
podman run -d --name test-context-ml-metadata \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install system dependencies

```bash
podman exec test-context-ml-metadata bash -c "
apt-get update && apt-get install -y \
  wget \
  gnupg2 \
  git \
  curl \
  build-essential \
  cmake
"
```

### 3. Install Bazel 5.3.0

```bash
podman exec test-context-ml-metadata bash -c "
wget -q https://github.com/bazelbuild/bazelisk/releases/download/v1.19.0/bazelisk-linux-amd64 -O /usr/local/bin/bazel && \
chmod +x /usr/local/bin/bazel
"
```

Bazelisk will automatically use version 5.3.0 based on `ml_metadata/.bazelversion`.

### 4. Install Python dependencies

```bash
podman exec test-context-ml-metadata bash -c "
cd /app && \
pip install --no-cache-dir \
  absl-py \
  attrs \
  grpcio \
  protobuf \
  'numpy~=1.22.0'
"
```

### 5. Patch WORKSPACE (REQUIRED)

⚠️ **This step is required** - see Dockerfile.redhat lines 27-33 for reference:

```bash
podman exec test-context-ml-metadata bash -c "
cd /app && \
sed -i 's/ac37cf5c0d80b5605176fc0f29e87b12f00be693/f764f4e986ac1516ab5ae95e6d6ce2f4416cc6ff/g' WORKSPACE && \
sed -i 's/afb6b1673d680e0ae7b21b6b119b0d4c8cce41b075358f87a0d7ad815c2b865d/27e3d8bfd1f76918fc4d7a8f29646b8a0cdca567f921e0bff4a07f79448e92c0/g' WORKSPACE
"
```

This patches the zetasql dependency to use a commit with the correct checksum.

### 6. Build (optional - tests build automatically)

```bash
podman exec test-context-ml-metadata bash -c "
cd /app && \
USE_BAZEL_VERSION=5.3.0 bazel build -c opt \
  --define grpc_no_ares=true \
  //ml_metadata/metadata_store:metadata_store_server
"
```

**Note**: Build will take 15-30+ minutes on first run as Bazel downloads and compiles all dependencies.

### 7. Run all tests

⚠️ **Status**: Cannot validate - requires WORKSPACE patch and long build time.

```bash
podman exec test-context-ml-metadata bash -c "
cd /app && \
USE_BAZEL_VERSION=5.3.0 bazel test //...
"
```

### 8. Run specific test package

```bash
podman exec test-context-ml-metadata bash -c "
cd /app && \
USE_BAZEL_VERSION=5.3.0 bazel test //ml_metadata/metadata_store:test_util_test
"
```

### 9. Run single test within a target

```bash
podman exec test-context-ml-metadata bash -c "
cd /app && \
USE_BAZEL_VERSION=5.3.0 bazel test \
  //ml_metadata/metadata_store:metadata_store_test \
  --test_filter='MetadataStoreTest.TestGetArtifacts'
"
```

### 10. Cleanup

```bash
podman rm -f test-context-ml-metadata
```

---

## Validation Results

### Install: ✅ SUCCESS
```
Command: apt-get install build-essential cmake git curl wget gnupg2
Exit code: 0
Result: System dependencies installed successfully
```

### Python dependencies: ✅ SUCCESS
```
Command: pip install absl-py attrs grpcio protobuf numpy~=1.22.0
Exit code: 0
Output: Successfully installed absl-py-2.4.0 attrs-26.1.0 grpcio-1.78.0 protobuf-7.34.1 typing-extensions-4.15.0
```

### Python test standalone: ❌ FAIL (expected)
```
Command: python -m ml_metadata.metadata_store.metadata_store_test
Exit code: 1
Output: ImportError: cannot import name 'metadata_store_pb2' from partially initialized module 'ml_metadata.proto'
Result: Python tests require compiled protobuf files and C++ extensions from Bazel build - cannot run standalone
```

### Bazel test: ❌ FAIL (WORKSPACE issue)
```
Command: USE_BAZEL_VERSION=5.3.0 bazel test //ml_metadata/metadata_store:test_util_test
Exit code: 1
Output: ERROR: Error downloading zetasql: Checksum was 86f81591ab5ec20457a5394eb2c5c981e6f6c89f4c49c211d096c3acffec1eb1 but wanted afb6b1673d680e0ae7b21b6b119b0d4c8cce41b075358f87a0d7ad815c2b865d
Result: zetasql dependency checksum in WORKSPACE is outdated. The production build (Dockerfile.redhat) patches this before building.
```

---

## CI/CD

### GitHub Actions

**Workflow**: `.github/workflows/build-pr.yaml` (gating on PRs)
- **Triggers**: `pull_request` (excludes docs/license changes)
- **Checks**: Container image build only
- **Command**: `./ml_metadata/tools/docker_server/build_docker_image.sh`
- **Dockerfile**: `ml_metadata/tools/docker_server/Dockerfile.redhat`

**What it does**: Builds a container image of the mlmd-grpc-server. Does NOT run tests or linting.

**Workflow**: `.github/workflows/build-master.yaml` (on merge to master)
- Same as PR workflow but also pushes image to quay.io

### Tekton

**Pipeline**: `.tekton/odh-mlmd-grpc-server-pull-request.yaml`
- Uses OpenShift Konflux multi-arch build pipeline
- Builds container image with 8-16 CPU, 16-32 GB RAM
- Does NOT run tests

### Critical Gap

⚠️ **No test or lint gates exist in CI**. The only automated check is that the container image builds successfully. Code changes are merged without running tests.

---

## Conventions

### Test Files

- **C++ tests**: `*_test.cc` files (e.g., `metadata_store_test.cc`)
- **Python tests**: `*_test.py` files (e.g., `metadata_store_test.py`)
- **Go tests**: `*_test.go` files (e.g., `metadata_store_test.go`)

### Test Structure

**C++ (googletest)**:
```cpp
TEST(TestSuiteName, TestName) {
  // test code
  EXPECT_EQ(expected, actual);
}

TEST_F(FixtureClass, TestName) {
  // test with fixture
}
```

**Python (absltest)**:
```python
from absl.testing import absltest

class MetadataStoreTest(absltest.TestCase):
    def test_feature_name(self):
        # test code
        self.assertEqual(expected, actual)

if __name__ == '__main__':
    absltest.main()
```

### Bazel Test Targets

Tests are defined in `BUILD` files using:
- `ml_metadata_cc_test()` - C++ tests
- `py_test()` - Python tests (rare, most use Bazel's built-in py_test)

Some tests tagged `manual` and `local` - these require external databases (MySQL, PostgreSQL) and must be run explicitly with database flags.

### Import Style

**Python**: Absolute imports from package root
```python
from ml_metadata import metadata_store
from ml_metadata.proto import metadata_store_pb2
```

**C++**: Double-quoted includes
```cpp
#include "ml_metadata/metadata_store/metadata_store.h"
```

---

## Gaps & Caveats

### 1. No Linting
❌ No linting tools configured (no .pylintrc, .flake8, ruff, clang-format, etc.)
- No code style enforcement
- No static analysis in CI

### 2. No Test Gates in CI
❌ CI only builds container images - does not run tests
- Tests exist but are never run automatically on PRs
- Code can merge with broken tests

### 3. WORKSPACE Dependency Issues
⚠️ **Blocker for local testing**
- `WORKSPACE` file has outdated zetasql dependency checksum
- The actual downloaded file has a different checksum than what's declared
- Production build (Dockerfile.redhat) patches this, but it's not in source control
- Tests cannot run without manual patching

**Required patch** (from Dockerfile.redhat):
```bash
# Change zetasql commit hash
sed -i 's/ac37cf5c0d80b5605176fc0f29e87b12f00be693/f764f4e986ac1516ab5ae95e6d6ce2f4416cc6ff/g' WORKSPACE

# Update checksum
sed -i 's/afb6b1673d680e0ae7b21b6b119b0d4c8cce41b075358f87a0d7ad815c2b865d/27e3d8bfd1f76918fc4d7a8f29646b8a0cdca567f921e0bff4a07f79448e92c0/g' WORKSPACE
```

### 4. Python Tests Require Bazel
❌ Python tests cannot run standalone
- Tests import `ml_metadata` module which requires compiled C++ extensions
- Extensions are built by Bazel
- Cannot run `pytest` or `python -m unittest` directly

### 5. External Database Tests
Some tests require external MySQL or PostgreSQL servers:
- `standalone_mysql_metadata_access_object_test`
- `standalone_postgresql_metadata_access_object_test`
- Tagged `manual` - must be run explicitly with database connection flags

### 6. Long Build Times
⚠️ First Bazel build takes 15-30+ minutes
- Downloads and compiles protobuf, grpc, abseil, zetasql, etc.
- Subsequent builds are cached but full rebuilds are slow

### 7. No Test Documentation
❌ No developer guide on running tests locally
- `CONTRIBUTING.md` only mentions CLA and PR process
- No mention of how to run tests or build the project
- Developers must reverse-engineer from Dockerfiles

---

## Recommendations for Agent Use

### For Patch Validation

**DO NOT ATTEMPT** to run tests in a simple container. The WORKSPACE patching requirement and 30+ minute build times make this impractical for automated patch validation.

**INSTEAD**:
1. Apply patch to source
2. Verify it builds using the production Dockerfile:
   ```bash
   docker build -f ml_metadata/tools/docker_server/Dockerfile.redhat .
   ```
3. If build succeeds, patch is likely compatible
4. Full test validation requires replicating production CI environment

### For Code Review

Focus on:
- Does the change match existing code patterns?
- Are there obvious syntax errors?
- Does it align with the protobuf schemas in `ml_metadata/proto/`?
- If touching C++, does it follow RAII and Google C++ style?

### For Upstream Contribution

If proposing improvements:
1. Fix WORKSPACE file to have correct checksums
2. Add test gates to CI (`.github/workflows/test-pr.yaml`)
3. Consider adding linting (ruff for Python, clang-format for C++)
4. Document how to run tests locally in CONTRIBUTING.md

---

## Quick Reference

### Key Files

- `WORKSPACE` - Bazel workspace with dependency definitions (needs patching)
- `ml_metadata/.bazelversion` - Pins Bazel to 5.3.0
- `setup.py` - Python package that wraps Bazel build
- `pyproject.toml` - Minimal build config (just numpy dependency)
- `ml_metadata/metadata_store/BUILD` - Main test definitions
- `Dockerfile.redhat` - Production build with WORKSPACE patches

### Key Commands

```bash
# Build server
USE_BAZEL_VERSION=5.3.0 bazel build -c opt --define grpc_no_ares=true //ml_metadata/metadata_store:metadata_store_server

# Run all tests (after WORKSPACE patch)
USE_BAZEL_VERSION=5.3.0 bazel test //...

# Build Python wheel (after WORKSPACE patch)
python setup.py bdist_wheel
```

### Environment Variables

- `USE_BAZEL_VERSION=5.3.0` - Force Bazelisk to use correct version
- `PYTHON_VERSION` - For docker-compose builds (39, 310, 311)

---

## Summary

**ml-metadata** is a Bazel-based C++/Python project with comprehensive tests that cannot be easily run outside the production build environment. The repository has:

✅ **Strengths**:
- Comprehensive test coverage (C++ and Python)
- Well-structured Bazel build
- Clear separation between C++ core and Python bindings

❌ **Weaknesses for Automation**:
- No test or lint gates in CI
- WORKSPACE file requires manual patching before tests run
- Long build times (30+ minutes first build)
- No documentation for local development
- Python tests cannot run without full Bazel build

**Agent Readiness Rating**: **LOW**

An automated agent cannot reliably validate patches without replicating the full production build environment including WORKSPACE patching. Manual code review and production CI build verification are the recommended validation approaches.
