# Test Context: langfuse (opendatahub-io)

**Generated**: 2026-03-22T22:42:05Z
**Agent Readiness**: `MEDIUM` - Lint and build validated successfully; tests require full infrastructure
**Languages**: TypeScript, JavaScript (Node.js 24.6.0)
**Build System**: pnpm 9.5.0 workspaces + Turborepo 2.8.13

## Overview

Langfuse is a TypeScript/JavaScript monorepo built with pnpm workspaces and Turborepo. The project consists of:
- **web**: Next.js 15 application (main UI)
- **worker**: Node.js background job processor
- **packages/shared**: Shared code, Prisma schema, utilities
- **ee**: Enterprise edition features

An agent can validate code quality (lint, format, typecheck, build) in a simple container, but **integration and E2E tests require a full infrastructure stack** (Postgres, Redis, ClickHouse, Minio) typically spun up via docker-compose.

---

## Container Recipe

This recipe allows an agent to validate linting, formatting, type checking, and builds without external infrastructure.

### 1. Start Container

```bash
podman run -d --name test-context-langfuse \
  -v $(pwd):/app:Z \
  -w /app \
  node:24-alpine \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-langfuse sh -c "apk add --no-cache git make"
```

### 3. Install pnpm

```bash
podman exec test-context-langfuse sh -c "corepack enable && corepack prepare pnpm@9.5.0 --activate"
```

### 4. Copy Environment File

```bash
podman exec test-context-langfuse sh -c "cd /app && cp .env.dev.example .env"
```

### 5. Install Dependencies

```bash
podman exec test-context-langfuse sh -c "cd /app && pnpm install"
```

**Expected**: ~2471 packages installed, exit code 0, ~2-5 minutes

### 6. Run Linting

```bash
podman exec test-context-langfuse sh -c "cd /app && pnpm run lint"
```

**Expected**: "Tasks: 4 successful, 4 total", exit code 0, ~1 minute
**Validates**: ESLint checks across web, worker, shared, and ee packages

### 7. Run Prettier Check

```bash
podman exec test-context-langfuse sh -c "cd /app && pnpm run format:check"
```

**Expected**: "All matched files use Prettier code style!", exit code 0
**Validates**: Code formatting across all TypeScript, JavaScript, and CSS files

### 8. Run Type Checking

```bash
podman exec test-context-langfuse sh -c "cd /app && pnpm --filter=@langfuse/shared run build && pnpm run typecheck"
```

**Expected**: "Tasks: 5 successful, 5 total", exit code 0
**Note**: Requires building shared package first to generate Prisma client and dist files
**Validates**: TypeScript compilation without emit

### 9. Run Build

```bash
podman exec test-context-langfuse sh -c "cd /app && pnpm run build"
```

**Expected**: "Tasks: 5 successful, 5 total", exit code 0, ~4 minutes
**Validates**: Full production build of web (Next.js) and worker packages

### 10. Run Tests (Limited)

```bash
podman exec test-context-langfuse sh -c "cd /app && pnpm --filter=web run test" || echo "Expected to fail without infrastructure"
```

**Expected**: Tests will fail with database connection errors
**Notes**: Some unit tests may pass, but integration tests require Postgres, Redis, ClickHouse

### 11. Cleanup

```bash
podman rm -f test-context-langfuse
```

---

## Validation Results

### ✅ Install Dependencies
- **Command**: `pnpm install`
- **Status**: SUCCESS (exit 0)
- **Time**: ~2-5 minutes
- **Output**: Installed 2471 packages

### ✅ Lint
- **Command**: `pnpm run lint`
- **Status**: SUCCESS (exit 0)
- **Time**: ~1 minute
- **Details**: ESLint checks passed for web, worker, shared, and ee packages with `--max-warnings 0`

### ✅ Prettier
- **Command**: `pnpm run format:check`
- **Status**: SUCCESS (exit 0)
- **Details**: All JavaScript, TypeScript, and CSS files formatted correctly

### ✅ Type Check
- **Command**: `pnpm run typecheck`
- **Status**: SUCCESS (exit 0)
- **Time**: ~8 seconds
- **Prerequisites**: Requires `pnpm --filter=@langfuse/shared run build` to generate Prisma client and shared package dist

### ✅ Build
- **Command**: `pnpm run build`
- **Status**: SUCCESS (exit 0)
- **Time**: ~4 minutes
- **Details**: Builds web (Next.js static/server pages), worker, shared, and ee packages

### ⚠️ Tests
- **Command**: `pnpm run test`
- **Status**: REQUIRES_INFRASTRUCTURE
- **Details**: Test framework runs correctly but integration tests fail with:
  - `connect ECONNREFUSED 127.0.0.1:6379` (Redis)
  - `Can't reach database server at localhost:5432` (Postgres)
- **Note**: Some unit tests in the web package pass (e.g., OTEL mapping tests), but most tests require infrastructure

---

## CI/CD

### Gating Checks (Required for Merge)

All checks run on `pull_request` events and must pass:

1. **Lint** (`.github/workflows/pipeline.yml`)
   ```bash
   pnpm run lint
   ```

2. **Prettier Check** (`.github/workflows/pipeline.yml`)
   ```bash
   pnpm prettier --check --experimental-cli {changed files}
   ```
   - Only checks files changed in the PR

3. **Tests - Web** (`.github/workflows/pipeline.yml`)
   ```bash
   npx cross-env NODE_OPTIONS='--no-experimental-require-module' \
     npx dotenv -e ../.env.test -e ../.env -- \
     npx jest --verbose --runInBand --detectOpenHandles \
     --selectProjects server --shard={shard}/3
   ```
   - Matrix: Node 24, Postgres 12/15, 3 deploy modes, 3 shards
   - Requires infrastructure: `docker compose -f docker-compose.dev.yml up -d`
   - Requires migrations: `pnpm run db:migrate`, `pnpm --filter=shared ch:up`

4. **Tests - Worker** (`.github/workflows/pipeline.yml`)
   ```bash
   pnpm --filter=worker run test:exclude-llm-connections
   ```
   - Matrix: Node 24, Postgres 12/15, 3 deploy modes
   - Requires infrastructure and seeding

5. **E2E Tests** (`.github/workflows/pipeline.yml`)
   ```bash
   pnpm --filter=web run test:e2e
   ```
   - Requires built application and Playwright

6. **E2E Server Tests** (`.github/workflows/pipeline.yml`)
   ```bash
   pnpm --filter=web run test:e2e:server
   ```
   - Requires running server

7. **Docker Build Test** (`.github/workflows/pipeline.yml`)
   ```bash
   docker compose -f docker-compose.build.yml build
   docker compose -f docker-compose.build.yml up -d --wait
   ```
   - Tests production Docker images

8. **Codespell** (`.github/workflows/codespell.yml`)
   ```bash
   codespell
   ```
   - Config: `.codespellrc`

9. **License Check** (`.github/workflows/licencecheck.yml`)
   ```bash
   license-checker --production --csv
   ```
   - Fails on WeakCopyleft, StrongCopyleft, NetworkCopyleft licenses

10. **PR Title Validation** (`.github/workflows/validate-pr-title.yml`)
    - Enforces conventional commits: `feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|security`

### Advisory Checks (Non-Blocking)

- **LLM Connection Tests**: Only run when LLM connection code changes or on tag push
- **CodeQL**: Security analysis
- **Snyk**: Security scanning for web and worker packages

---

## Conventions

### Test File Patterns

- **Jest (web)**: `**/*.servertest.ts` (server tests), `**/*.clienttest.ts` (client tests)
- **Vitest (worker)**: `**/*.test.ts`
- **Playwright (web)**: E2E tests in `web/__e2e__/`

### Test Naming

- Use `describe` and `it` blocks for both Jest and Vitest
- Test files must match the pattern above to be discovered

### Import Style

- ESM with absolute imports via tsconfig `paths`
- Barrel exports from `@langfuse/shared` and `@langfuse/ee`
- Workspace protocol for internal deps: `workspace:*`

### Environment Variables

- Always use `dotenv-cli` wrapper: `dotenv -e .env -- {command}`
- Copy `.env.dev.example` to `.env` for development
- Tests use `.env.test` (if exists) + `.env`

### Code Quality

- **Max ESLint Warnings**: 0
- **Prettier**: Enforced with trailing commas
- **Restricted Imports**: Only `react-icons/si` and `react-icons/tb` allowed (use lucide-react otherwise)

---

## Gaps & Caveats

### Infrastructure Requirements

All integration and E2E tests require a full stack typically started via:

```bash
docker compose -f docker-compose.dev.yml up -d
```

This provides:
- **Postgres** (12 or 15) on `localhost:5432`
- **Redis** on `localhost:6379`
- **ClickHouse** on `localhost:8123`
- **Minio** (S3-compatible) on `localhost:9000`

After starting infrastructure:

```bash
# Migrate Postgres
pnpm run db:migrate

# Migrate ClickHouse
pnpm --filter=shared ch:up

# Optionally seed data
pnpm --filter=shared run db:seed
pnpm --filter=shared run db:seed:examples
```

### Test Sharding

Web tests are sharded 3 ways in CI:
```bash
npx jest --shard=1/3
npx jest --shard=2/3
npx jest --shard=3/3
```

### LLM Connection Tests

Require external API keys (not included in test context):
- `LANGFUSE_LLM_CONNECTION_OPENAI_KEY`
- `LANGFUSE_LLM_CONNECTION_ANTHROPIC_KEY`
- `LANGFUSE_LLM_CONNECTION_AZURE_KEY`
- `LANGFUSE_LLM_CONNECTION_BEDROCK_ACCESS_KEY_ID`
- `LANGFUSE_LLM_CONNECTION_VERTEXAI_KEY`
- `LANGFUSE_LLM_CONNECTION_GOOGLEAISTUDIO_KEY`

These tests are excluded from standard test runs and only run conditionally in CI.

### ClickHouse Client

Some tests require the ClickHouse client binary (`clickhouse`) to be installed:

```bash
wget "https://packages.clickhouse.com/deb/pool/main/c/clickhouse/clickhouse-common-static_24.9.3.128_amd64.deb" -O clickhouse-client.deb
dpkg-deb -x clickhouse-client.deb ch_client_dir
sudo cp ch_client_dir/usr/bin/clickhouse /usr/local/bin/
```

### Prisma Client Generation

TypeScript type checking and builds depend on Prisma client generation:

```bash
pnpm run db:generate  # Generates Prisma client and Kysely types
```

This is automatically handled by Turborepo's dependency graph (`dependsOn: ["db:generate"]`).

### Build Memory Requirements

Next.js build can be memory-intensive. CI uses:
```bash
NODE_OPTIONS='--max-old-space-size=8192' pnpm run build
```

In the alpine container, use:
```bash
NODE_OPTIONS='--max-old-space-size-percentage=75' pnpm run build
```

---

## Quick Reference

### Run Commands for Agents

**Install & Setup**:
```bash
pnpm install
cp .env.dev.example .env
```

**Code Quality** (no infrastructure required):
```bash
pnpm run lint           # ESLint all packages
pnpm run format:check   # Prettier check
pnpm run typecheck      # TypeScript type check
pnpm run build          # Production build
```

**Testing** (requires infrastructure):
```bash
# Start infrastructure
docker compose -f docker-compose.dev.yml up -d

# Migrate databases
pnpm run db:migrate
pnpm --filter=shared ch:up

# Run tests
pnpm run test                           # All tests
pnpm --filter=web run test              # Web tests only
pnpm --filter=worker run test           # Worker tests only
pnpm --filter=web run test:e2e          # Playwright E2E tests
```

**Single File/Test**:
```bash
# Web (Jest)
pnpm --filter=web run test src/__tests__/server/api/otel/otelMapping.servertest.ts
pnpm --filter=web run test -t "should convert LF-OTEL spans"

# Worker (Vitest)
pnpm --filter=worker run test src/__tests__/batchExport.test.ts
pnpm --filter=worker run test batchExport
```

**Cleanup**:
```bash
docker compose -f docker-compose.dev.yml down   # Stop infrastructure
docker compose -f docker-compose.dev.yml down -v # Stop and remove volumes
```

---

## Agent Workflow Example

A downstream agent validating a patch should:

1. **Start container**: `podman run -d --name test-context-langfuse -v $(pwd):/app:Z -w /app node:24-alpine sleep infinity`
2. **Install deps**: `podman exec test-context-langfuse sh -c "apk add git make && corepack enable && corepack prepare pnpm@9.5.0 --activate"`
3. **Setup project**: `podman exec test-context-langfuse sh -c "cd /app && cp .env.dev.example .env && pnpm install"`
4. **Validate code quality**:
   - Lint: `podman exec test-context-langfuse sh -c "cd /app && pnpm run lint"`
   - Format: `podman exec test-context-langfuse sh -c "cd /app && pnpm run format:check"`
   - Typecheck: `podman exec test-context-langfuse sh -c "cd /app && pnpm --filter=@langfuse/shared run build && pnpm run typecheck"`
   - Build: `podman exec test-context-langfuse sh -c "cd /app && pnpm run build"`
5. **Cleanup**: `podman rm -f test-context-langfuse`

**Result**: Clear pass/fail signal on lint, format, typecheck, and build without requiring infrastructure.

For full test validation, the agent would need to start the docker-compose stack, which requires Docker-in-Docker or access to the host Docker daemon.

---

## Summary

- **Agent Readiness**: MEDIUM
- **Validated Commands**: lint ✅, format:check ✅, typecheck ✅, build ✅
- **Infrastructure Required For**: tests, e2e tests, integration tests
- **Recommended Use**: Code quality validation in simple containers; full test suite in CI with infrastructure
- **Confidence**: HIGH (all commands validated in live container)
