# ModelMesh Test Context

**Agent Readiness: MEDIUM** — Build and individual tests work, but full test suite is slow and no linting is configured.

## Overview

- **Repository**: opendatahub-io/modelmesh
- **Languages**: Java 21 (primary), Python (one helper script)
- **Build System**: Maven 3.9+
- **Test Framework**: JUnit 5 (Jupiter)
- **Test Count**: 41 test classes in src/test/java
- **CI System**: GitHub Actions

## Container Recipe

This is a complete, copy-paste recipe for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-modelmesh \
  -v /path/to/modelmesh:/app:Z \
  -w /app \
  docker.io/library/maven:3.9-eclipse-temurin-21 \
  sleep infinity
```

Replace `/path/to/modelmesh` with the actual path to your cloned repository.

### 2. Install System Dependencies

etcd is required for tests:

```bash
podman exec test-context-modelmesh bash -c "
cd /tmp && \
wget -q https://github.com/etcd-io/etcd/releases/download/v3.5.4/etcd-v3.5.4-linux-amd64.tar.gz && \
tar xzf etcd-v3.5.4-linux-amd64.tar.gz --no-same-owner && \
mv etcd-v3.5.4-linux-amd64/etcd /usr/local/bin/ && \
mv etcd-v3.5.4-linux-amd64/etcdctl /usr/local/bin/ && \
rm -rf etcd-v3.5.4* && \
etcd --version
"
```

**Expected output:**
```
etcd Version: 3.5.4
Git SHA: 08407ff76
Go Version: go1.16.15
Go OS/Arch: linux/amd64
```

### 3. Resolve Dependencies

Maven handles dependency resolution automatically, but you can verify:

```bash
podman exec test-context-modelmesh bash -c "cd /app && mvn -B dependency:resolve"
```

### 4. Build Project

Build the project without running tests (fast, ~12 seconds):

```bash
podman exec test-context-modelmesh bash -c "cd /app && mvn -B package -DskipTests"
```

**Expected output:**
```
[INFO] Building jar: /app/target/dockerhome/lib/model-mesh-0.4.2-SNAPSHOT.jar
[INFO] BUILD SUCCESS
[INFO] Total time:  12.069 s
```

**Exit code:** 0 (success)

### 5. Run Tests

#### Option A: Run a Single Test Class (Recommended)

Fast validation with a simple test class (~3 seconds):

```bash
podman exec test-context-modelmesh bash -c "cd /app && mvn test -Dtest=ProtoSplicerTest"
```

**Expected output:**
```
[INFO] Running com.ibm.watson.modelmesh.ProtoSplicerTest
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.363 s
[INFO] BUILD SUCCESS
```

**Exit code:** 0 (success)

#### Option B: Run All Tests (Slow, >5 minutes)

```bash
podman exec test-context-modelmesh bash -c "cd /app && timeout 600 mvn -B test"
```

**Warning:** The full test suite contains 41 test classes and takes more than 5 minutes to complete. Many tests start embedded etcd instances and perform distributed system testing. For quick patch validation, use individual test classes instead.

#### Run Multiple Specific Tests

```bash
podman exec test-context-modelmesh bash -c "cd /app && mvn test -Dtest=ProtoSplicerTest,ModelMeshMetricsTest"
```

#### Run a Single Test Method

```bash
podman exec test-context-modelmesh bash -c "cd /app && mvn test -Dtest=ProtoSplicerTest#testBasicSplice"
```

### 6. Linting

**Status:** No linting tools are configured.

The `.pre-commit-config.yaml` file references `golangci-lint` and `prettier`, but:
- There is no Go code in this repository (golangci-lint is not applicable)
- prettier may be intended for YAML/JSON formatting but is not actively enforced
- No Java-specific linters (checkstyle, spotbugs, PMD) are configured in `pom.xml`

**Recommendation:** If you need to verify code style, manually review Java code against standard conventions or propose adding checkstyle/spotbugs to the build.

### 7. Cleanup

Always remove the container when done:

```bash
podman rm -f test-context-modelmesh
```

## Validation Results

### Dependencies
- **Status:** ✅ SUCCESS
- **Command:** `mvn -B dependency:resolve`
- **Notes:** All dependencies resolve correctly from Maven Central

### Build
- **Status:** ✅ SUCCESS
- **Command:** `mvn -B package -DskipTests`
- **Duration:** ~12 seconds
- **Output:** JAR file created at `target/dockerhome/lib/model-mesh-0.4.2-SNAPSHOT.jar`

### Single Test
- **Status:** ✅ SUCCESS
- **Command:** `mvn test -Dtest=ProtoSplicerTest`
- **Duration:** 2.98 seconds total (0.363s test execution)
- **Result:** 2 tests run, 0 failures, 0 errors, 0 skipped

### Full Test Suite
- **Status:** ⏱️ SLOW / TIMEOUT
- **Command:** `mvn -B test`
- **Notes:** Tests start running but take >5 minutes for all 41 test classes. Individual test classes work fine, but running the entire suite is not practical for quick validation.

### Linting
- **Status:** ❌ NOT CONFIGURED
- **Notes:** No linting tools are configured in the Maven build

## CI/CD

### Gating Checks (Required for Merge)

The `.github/workflows/build.yml` workflow runs on all pull requests and must pass:

```bash
# Install etcd
sudo ./.github/install-etcd.sh

# Build and test
mvn -B package --file pom.xml
```

This is the same as running:
```bash
mvn -B package
```

The `package` phase includes compilation, protobuf code generation, and test execution.

### Advisory Checks (Not Required)

- **CodeQL Analysis** (`.github/workflows/codeql.yml`): Static security analysis for Java and Python code. Runs on push to main and on a schedule.

## Test Conventions

### Test File Naming
- Pattern: `src/test/java/**/*Test.java`
- Example: `ModelMeshTest.java`, `ProtoSplicerTest.java`

### Test Structure
- Base classes: `AbstractModelMeshTest`, `AbstractModelMeshClusterTest`
- JUnit 5 annotations: `@Test`, `@BeforeEach`, `@AfterEach`, etc.
- Many tests use embedded etcd via `curator-test` library

### Test Categories
- **Unit tests**: `ProtoSplicerTest`, `ModelMeshMetricsTest`
- **Integration tests**: `ModelMeshClusterTest`, `SidecarModelMeshTest`
- **TLS tests**: `ModelMeshClusterTlsTest`, `ModelMeshClusterTlsClientAuthTest`
- **Failure scenario tests**: `ModelMeshFailureExpiryTest`, `ModelMeshLoadFailureTest`

### Example Test Runs

Quick validation (simple unit test):
```bash
mvn test -Dtest=ProtoSplicerTest
# ~3 seconds, 2 tests
```

More comprehensive validation (cluster test):
```bash
mvn test -Dtest=ModelMeshClusterTest
# ~30 seconds, multiple tests
```

Pattern matching (run all sidecar tests):
```bash
mvn test -Dtest=*Sidecar*
# Runs: SidecarModelMeshTest, SidecarModelMeshPayloadProcessingTest, etc.
```

## Gaps & Caveats

### No Linting
The project has no automated code quality checks configured in Maven. The `.pre-commit-config.yaml` file exists but references tools for Go (golangci-lint) which don't apply to this Java codebase.

**Impact:** Code style and quality issues won't be caught automatically. Manual review is required.

### Slow Test Suite
Running all 41 test classes takes more than 5 minutes. Tests involve:
- Starting embedded etcd instances
- Distributed model mesh cluster setup
- TLS handshake and certificate generation
- Complex failure scenario simulations

**Impact:** Full test suite validation is not practical in time-constrained environments. Use individual test classes for faster feedback.

### etcd Dependency
Tests require etcd v3.5.0+ to be installed on the system PATH. This is:
- ✅ Documented in developer-guide.md
- ✅ Installed by CI via `.github/install-etcd.sh`
- ❌ Not enforced by Maven configuration (no check for etcd binary)

**Impact:** Tests will fail with unclear errors if etcd is not installed. The container recipe above handles this.

### Missing Coverage Reporting
No code coverage tools (JaCoCo, Cobertura) are configured. Coverage metrics are not tracked.

**Impact:** Cannot measure test coverage percentage or identify untested code paths.

## Build Details

### Protobuf Code Generation

The project uses gRPC and Protocol Buffers. Source `.proto` files are in `src/main/proto/` and `src/test/proto/`. Generated Java sources are created by `protobuf-maven-plugin` during the build:

- **Main sources:** `target/generated-sources/protobuf/grpc-java/`
- **Test sources:** `target/generated-test-sources/protobuf/grpc-java/`

These are generated automatically during `mvn package` or `mvn compile`.

### Java Version

- **Required:** Java 21
- **Configured in:** `pom.xml` (`<release>21</release>` in maven-compiler-plugin)
- **CI uses:** Eclipse Temurin 21

### Maven Plugins

Key plugins in the build:
- `protobuf-maven-plugin`: Generates gRPC/protobuf code
- `maven-compiler-plugin`: Compiles Java code with Java 21
- `maven-surefire-plugin`: Runs JUnit 5 tests
- `maven-dependency-plugin`: Copies dependencies to `target/dockerhome/lib/`
- `maven-jar-plugin`: Builds the JAR file

## Quick Start for Agents

**Minimal validation** (build + one test, ~15 seconds):
```bash
cd /path/to/modelmesh
podman run --rm -v .:/app:Z -w /app docker.io/library/maven:3.9-eclipse-temurin-21 bash -c "
  wget -q https://github.com/etcd-io/etcd/releases/download/v3.5.4/etcd-v3.5.4-linux-amd64.tar.gz && \
  tar xzf etcd-v3.5.4-linux-amd64.tar.gz --no-same-owner && \
  mv etcd-v3.5.4-linux-amd64/etcd /usr/local/bin/ && \
  mvn -B package -DskipTests && \
  mvn test -Dtest=ProtoSplicerTest
"
```

**Comprehensive validation** (build + selected tests, ~2 minutes):
```bash
cd /path/to/modelmesh
podman run --rm -v .:/app:Z -w /app docker.io/library/maven:3.9-eclipse-temurin-21 bash -c "
  wget -q https://github.com/etcd-io/etcd/releases/download/v3.5.4/etcd-v3.5.4-linux-amd64.tar.gz && \
  tar xzf etcd-v3.5.4-linux-amd64.tar.gz --no-same-owner && \
  mv etcd-v3.5.4-linux-amd64/etcd /usr/local/bin/ && \
  mvn -B package -DskipTests && \
  mvn test -Dtest=ProtoSplicerTest,ModelMeshMetricsTest,ModelMeshTest
"
```

## Notes for Downstream Agents

1. **Always install etcd first** — Tests will fail with cryptic errors without it
2. **Run individual test classes** — The full suite is too slow for quick validation
3. **Build generates code** — Protocol buffer stubs are generated during `mvn compile`
4. **No linting available** — Code quality checks must be done manually
5. **Container image build** — Use the multi-stage `Dockerfile` in the repo root for production images

## References

- **Developer Guide:** `developer-guide.md` in repo root
- **CI Configuration:** `.github/workflows/build.yml`
- **Docker Build:** `Dockerfile` (multi-stage build with UBI9 base)
- **Test Resources:** `src/test/resources/` (log4j config, test proto files)
