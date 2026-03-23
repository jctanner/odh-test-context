# TrustyAI Explainability - Test Context

## Overview

**Repository:** opendatahub-io/trustyai-explainability
**Language:** Java (Maven)
**Build System:** Maven 3.6.3+ with Java 17
**Agent Readiness:** MEDIUM — Lint and test commands work correctly. Baseline has 1 test failure and 1 formatting violation (expected state of current codebase). An agent can compile, lint, and run tests to validate patches.

## Container Recipe

This is a step-by-step recipe to validate patches in an isolated container.

### 1. Start the container

```bash
podman run -d --name test-context-trustyai-explainability \
  -v "$(pwd)":/app:Z \
  -w /app \
  docker.io/library/maven:3.9.2-eclipse-temurin-17 \
  sleep infinity
```

Or with docker:
```bash
docker run -d --name test-context-trustyai-explainability \
  -v "$(pwd)":/app \
  -w /app \
  maven:3.9.2-eclipse-temurin-17 \
  sleep infinity
```

### 2. Verify environment

```bash
podman exec test-context-trustyai-explainability bash -c "mvn --version && java -version"
```

Expected output: Maven 3.9.2, Java 17.

### 3. Compile project

```bash
podman exec test-context-trustyai-explainability bash -c "cd /app && mvn compile test-compile -Dformatter.skip=true"
```

**Validated:** ✅ SUCCESS (9.7s)
**Exit code:** 0
All modules compile successfully.

### 4. Run linting (formatter validation)

```bash
podman exec test-context-trustyai-explainability bash -c "cd /app && mvn net.revelc.code.formatter:formatter-maven-plugin:validate"
```

**Validated:** ⚠️ FAILURE (expected)
**Exit code:** 1
**Issue:** 1 file not formatted: `explainability-connectors/src/main/java/org/kie/trustyai/connectors/kserve/v2/KServeConfig.java`

This is a real formatting violation in the current codebase. A patch that introduces additional formatting issues will cause this check to fail on more files.

**Auto-fix command:**
```bash
podman exec test-context-trustyai-explainability bash -c "cd /app && mvn net.revelc.code.formatter:formatter-maven-plugin:format"
```

### 5. Run tests

```bash
podman exec test-context-trustyai-explainability bash -c "cd /app && mvn test"
```

**Validated:** ⚠️ PARTIAL (1 test failure)
**Exit code:** 1
**Results:** 427 tests run, 426 passed, 1 failed, 5 skipped

The test framework works correctly. There is 1 test failure in the baseline codebase.

**Run a single test file:**
```bash
podman exec test-context-trustyai-explainability bash -c "cd /app && mvn test -Dtest=ArrowConvertersTest"
```

**Run a single test method:**
```bash
podman exec test-context-trustyai-explainability bash -c "cd /app && mvn test -Dtest=ArrowConvertersTest#testReadWrite"
```

### 6. Run tests for specific module

```bash
# Test only the core module
podman exec test-context-trustyai-explainability bash -c "cd /app/explainability-core && mvn test"

# Test only the connectors module
podman exec test-context-trustyai-explainability bash -c "cd /app/explainability-connectors && mvn test"

# Test only the service module
podman exec test-context-trustyai-explainability bash -c "cd /app/explainability-service && mvn test"
```

### 7. Cleanup

```bash
podman rm -f test-context-trustyai-explainability
```

## Validation Results

### Dependency Installation
- **Command:** `mvn compile test-compile -Dformatter.skip=true`
- **Status:** ✅ SUCCESS
- **Time:** ~10s
- **Notes:** All 4 modules (core, arrow, connectors, service) compile successfully

### Linting
- **Command:** `mvn net.revelc.code.formatter:formatter-maven-plugin:validate`
- **Status:** ⚠️ EXPECTED FAILURE
- **Issue:** 1 file has formatting violations (KServeConfig.java)
- **Notes:** This is the current state of the codebase. The linter works correctly.

### Testing
- **Command:** `mvn test`
- **Status:** ⚠️ PARTIAL SUCCESS
- **Results:** 427 tests, 426 passed, 1 failed, 5 skipped
- **Notes:** Test framework works correctly. Baseline has 1 failing test.

## CI/CD

### GitHub Actions Workflows

**Gating checks (required for merge):**

1. **Unit Tests** (`.github/workflows/test.yaml`)
   - Triggers: push, pull_request
   - Matrix: Java 17, Maven 3.6.3/3.8.8/3.9.2, Ubuntu 22.04
   - Commands:
     ```bash
     mvn compile test-compile -Dformatter.skip=true
     mvn test
     ```

2. **Build Validation** (`.github/workflows/CI.yaml`)
   - Triggers: push, pull_request (main repo only)
   - Commands:
     ```bash
     mvn package -Dmaven.test.skip=true -Dformatter.skip=true
     mvn net.revelc.code.formatter:formatter-maven-plugin:validate
     ```

3. **Security Scan** (`.github/workflows/trivy-scan.yaml`)
   - Trivy container image scanning

**Environment variables used in CI:**
```bash
MAVEN_OPTS="-Dhttps.protocols=TLSv1.2 -Dorg.slf4j.simpleLogger.log.org.apache.maven.cli.transfer.Slf4jMavenTransferListener=WARN -Dorg.slf4j.simpleLogger.showDateTime=true -Djava.awt.headless=true"
MAVEN_ARGS="-nsu -fae -e"
```

## Conventions

### Test Files
- **Pattern:** `**/*Test.java`
- **Location:** `*/src/test/java`
- **Framework:** JUnit 5 (Jupiter)
- **Naming:** Test classes end with `Test`, methods annotated with `@Test`
- **Count:** 226 test files out of 705 total Java files

### Test Execution
- Tests use JUnit 5 (org.junit.jupiter)
- Assertions with AssertJ (org.assertj)
- Mocking with Mockito (org.mockito)
- Integration tests use `@QuarkusTest` annotation
- Surefire configuration: `-Xmx2048m -Dfile.encoding=UTF-8 --add-opens java.base/java.nio=ALL-UNNAMED`

### Code Style
- **Formatter:** Eclipse style (config/eclipse-format.xml)
- **Import order:** java., javax., org., com., io. (static imports after)
- **Import plugin:** impsort-maven-plugin
- **Excluded from formatting:** GRPC-generated code in `explainability-connectors/src/main/java/org/kie/trustyai/connectors/kserve/v2/grpc/`

## Gaps & Caveats

1. **Baseline not fully green:** Current codebase has 1 failing test and 1 formatting violation. A patch validation agent should compare before/after to detect if a patch introduces new failures.

2. **Integration tests separate:** Integration tests (DMN, PMML, OpenNLP) are in `explainability-integrationtests` module and require the `-P integration-tests` profile. They are not run by default.

3. **Quarkus dependencies:** The `explainability-service` module uses Quarkus for integration tests, which starts embedded services (H2 database, HTTP servers). These tests take longer and use more memory.

4. **No coverage reporting:** Code coverage tools are not configured in the default Maven build.

5. **Profile awareness:** The build supports multiple profiles:
   - `service-minimal`: For CPaaS builds (excludes some modules)
   - `integration-tests`: Includes integration test modules
   - `validate-formatting`: Fails build on formatting issues
   - `quickly`: Skips tests and formatting for fast builds

6. **Maven version matrix:** CI tests against Maven 3.6.3, 3.8.8, and 3.9.2. Some features may behave differently across versions.

## Build Commands Quick Reference

```bash
# Full build with tests
mvn clean install

# Fast build (skip tests and formatting)
mvn clean package -Dquickly

# Build for service deployment
mvn clean package -P service-minimal -Dformatter.skip=true

# Format code
mvn formatter:format impsort:sort

# Validate formatting
mvn formatter:validate impsort:check

# Run only unit tests
mvn test

# Run tests with integration tests
mvn test -P integration-tests

# Package without tests
mvn package -Dmaven.test.skip=true -Dformatter.skip=true
```

## Module Structure

- **explainability-core:** Core library with fairness metrics, XAI algorithms, utilities
- **explainability-arrow:** Arrow-based communication for Python interop
- **explainability-connectors:** KServe/ModelMesh gRPC connectors
- **explainability-service:** Quarkus-based REST service
- **explainability-integrationtests:** DMN, PMML, OpenNLP integration tests (optional, via profile)

## Expected Baseline Results

When validating patches, compare against these baseline metrics:

- **Compilation:** SUCCESS (all 4 modules)
- **Formatter validation:** 1 violation (KServeConfig.java)
- **Tests:** 427 run, 426 pass, 1 fail, 5 skip

A patch that changes these numbers should be investigated:
- Additional formatter violations → likely needs formatting
- Additional test failures → likely a real bug
- Compilation failures → likely a code issue
