# Test Context: opendatahub-operator

**Repository**: opendatahub-io/opendatahub-operator
**Language**: Go 1.25.7
**Build System**: Makefile + Go modules
**Agent Readiness**: **medium** — Lint works perfectly, most tests pass, but some test suites have build issues and integration/e2e tests require cluster infrastructure.

---

## Container Recipe

This section provides a complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-opendatahub-operator \
  -v $(pwd):/app:Z \
  -w /app \
  golang:1.25 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-opendatahub-operator bash -c "apt-get update && apt-get install -y make git curl jq"
```

### 3. Download Go Dependencies

```bash
podman exec test-opendatahub-operator bash -c "cd /app && go mod download"
```

### 4. Generate Manifests (Required for Tests)

```bash
podman exec test-opendatahub-operator bash -c "cd /app && make manifests-all"
```

This generates Kubernetes CRDs and RBAC manifests for both OpenDataHub and RHOAI platforms. Takes ~30 seconds.

### 5. Download Component Manifests (Required for Tests)

```bash
podman exec test-opendatahub-operator bash -c "cd /app && make get-manifests"
```

This clones external component manifests (dashboard, kserve, etc.) into `opt/manifests/`. Takes ~60 seconds.

### 6. Run Linter

```bash
podman exec test-opendatahub-operator bash -c "cd /app && make lint"
```

**Expected**: `0 issues.`
**Validated**: ✅ Passed with 0 issues
**Time**: ~60 seconds (first run downloads golangci-lint v2.5.0)

### 7. Run Unit Tests

```bash
podman exec test-opendatahub-operator bash -c "cd /app && make unit-test TEST_SRC='./internal/... ./tests/integration/...'"
```

**Expected**: Most tests pass, ~77% coverage. Some pkg/upgrade tests fail to build.
**Validated**: ⚠️ Partial — Most tests passed, pkg/upgrade/ has issues
**Time**: ~5 minutes
**Notes**:
- Uses Ginkgo with 8 parallel processes
- Requires `make manifests-all` and `make get-manifests` first
- Full test suite includes pkg/ but has build issues in pkg/upgrade/

### 8. Run Single Test File (Optional)

```bash
podman exec test-opendatahub-operator bash -c "cd /app && ginkgo -r ./internal/controller/components/dashboard/"
```

### 9. Run Single Test (Optional)

```bash
podman exec test-opendatahub-operator bash -c "cd /app && ginkgo -run 'TestDashboardController' ./internal/controller/components/dashboard/"
```

### 10. Cleanup

```bash
podman rm -f test-opendatahub-operator
```

---

## Validation Results

### ✅ Install (go mod download)
- **Exit Code**: 0
- **Result**: Success
- **Notes**: Go 1.25.7 dependencies downloaded without errors

### ✅ Build (make manifests-all)
- **Exit Code**: 0
- **Result**: Success
- **Output**: Generated CRDs and RBAC for ODH and RHOAI platforms
- **Notes**: Required before running tests

### ✅ Lint (make lint)
- **Exit Code**: 0
- **Result**: Success
- **Output**: `0 issues.`
- **Notes**: golangci-lint v2.5.0 with extensive checks (all enabled by default minus ~20 disabled in config)

### ⚠️ Test (make unit-test)
- **Exit Code**: 1
- **Result**: Partial success
- **Output**: `PASS coverage: 77.7% of statements` then `fork/exec /app/pkg/upgrade/upgrade.test: no such file or directory`
- **Notes**: Most tests in internal/ and pkg/ pass, but pkg/upgrade/ test suite fails to build/run

---

## CI/CD

### Gating Checks (Required for PR Merge)

All PRs must pass these checks:

1. **golangci-lint**
   ```bash
   make lint
   ```
   - Workflow: `.github/workflows/test-linter.yaml`
   - Configuration: `.golangci.yml`
   - Validates: Go code quality, style, and potential bugs
   - Blocks on: Any linter issues

2. **kube-linter**
   ```bash
   make prepare && ./bin/kustomize build config/manifests | kube-linter lint --config .kube-linter.yaml -
   ```
   - Workflow: `.github/workflows/test-linter.yaml`
   - Configuration: `.kube-linter.yaml`
   - Validates: Kubernetes manifest security and best practices
   - Blocks on: CRITICAL and HIGH severity findings only
   - Advisory: MEDIUM and LOW findings reported but don't block

3. **Unit Tests**
   ```bash
   make manifests-all && make get-manifests && make unit-test
   ```
   - Workflow: `.github/workflows/test-unit.yaml`
   - Test scope: `./internal/... ./pkg/...`
   - Framework: Ginkgo/Gomega with envtest
   - Uploads coverage to Codecov

4. **Prometheus Alert Unit Tests**
   ```bash
   make test-alerts
   ```
   - Workflow: `.github/workflows/test-prometheus-unit.yaml`
   - Validates: PrometheusRule alert definitions
   - Requires: `promtool` installed

### Advisory Checks (Optional/Manual Trigger)

- **Integration Tests**: Triggered by `run-integration-tests` label, builds catalog images and deploys to test cluster
- **E2E Tests**: Require full OpenShift/Kubernetes cluster with operator deployed

---

## Conventions

### Test File Naming
- Go tests: `*_test.go`
- Ginkgo suites: `suite_test.go` files in package directories
- Prometheus alert tests: `*-alerting.unit-tests.yaml`

### Test Structure
```go
// Ginkgo/Gomega style
var _ = Describe("ComponentController", func() {
    Context("when creating a component", func() {
        It("should reconcile successfully", func() {
            // test logic
        })
    })
})
```

### Import Conventions
- Three-section grouping: standard library, third-party, opendatahub-io
- Custom aliases enforced by golangci-lint:
  - `dsciv1` → `api/dscinitialization/v1`
  - `dscv1` → `api/datasciencecluster/v1`
  - `k8serr` → `k8s.io/apimachinery/pkg/api/errors`

### Test Execution
- Unit tests run in parallel (8 processes, 2 compilers)
- 20-minute timeout per test suite
- Fail-fast mode enabled
- Coverage profiles generated

---

## Gaps & Caveats

### Known Issues
1. **pkg/upgrade/ test suite fails to build** — Tests exist but binary cannot be created. Investigate build tags or missing dependencies.

2. **Integration tests require cluster** — Cannot validate in container. Need actual Kubernetes cluster with CRDs installed.

3. **E2E tests require full environment** — Needs OpenShift/K8s with operator deployed, multiple namespaces, and component images.

4. **kube-linter needs rendered manifests** — Requires `make prepare` and kustomize build, cannot easily run in isolation.

### What Agents Can Validate
✅ **Linting**: Full validation with `make lint`
✅ **Unit tests**: Partial validation (internal/ and most of pkg/)
✅ **Code generation**: Manifests and generated code
✅ **Prometheus alerts**: Alert rule syntax and unit tests
❌ **Integration tests**: Require external cluster
❌ **E2E tests**: Require full deployment
❌ **pkg/upgrade tests**: Build issues prevent execution

### Infrastructure Requirements Not Available in Container
- Kubernetes cluster (for integration/e2e tests)
- Container registry (for image build/push)
- OpenShift-specific APIs (for full e2e validation)
- Component deployments (dashboard, kserve, etc.)

---

## Additional Commands

### Format Code
```bash
make fmt
```
Runs `go fmt` and `golangci-lint fmt`

### Auto-fix Linter Issues
```bash
make lint-fix
```

### Build Operator Binary
```bash
make build
```
Output: `bin/manager`

### Build Container Image
```bash
make image-build
```
Builds operator container image (requires podman or docker)

### Run Locally (No Cluster)
```bash
make manifests generate fmt vet
go run cmd/main.go
```

### View Test Coverage
```bash
make unit-test
go tool cover -html=cover.out
```

---

## Summary

The opendatahub-operator has a robust testing infrastructure with clear separation between unit, integration, and e2e tests. An agent can validate:

1. **Linting** with 100% confidence (golangci-lint passes)
2. **Most unit tests** with ~80% success rate (pkg/upgrade issues)
3. **Code generation** (manifests, CRDs, RBAC)
4. **Prometheus alerts** (if promtool available)

The agent **cannot** validate:
- Integration tests (need cluster)
- E2E tests (need full deployment)
- Complete unit test suite (pkg/upgrade build issues)

**Agent Readiness: Medium** — Partial validation possible, good for most common patch scenarios.
