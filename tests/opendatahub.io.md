# Test Context for opendatahub.io

**Generated**: 2026-03-22T19:54:21-04:00
**Organization**: opendatahub-io
**Repository**: opendatahub.io

## Overview

Gatsby 5 static site built with TypeScript/React. Generates 1300+ documentation pages from Markdown/AsciiDoc content. **Agent readiness: MEDIUM** — Build validation works and is gating, but no tests exist, linting is not enforced, and TypeScript checking requires build to complete first.

**Languages**: TypeScript, JavaScript
**Build System**: npm, Gatsby 5.8.1
**CI**: GitHub Actions (only build check is gating)

## Container Recipe

This recipe provides a complete, copy-paste workflow for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-opendatahub-io \
  -v $(pwd):/app:Z \
  -w /app \
  node:20 \
  sleep infinity
```

**Base image**: `node:20` (specified in `.github/workflows/gatsby.yml`)

### 2. Install Dependencies

```bash
podman exec test-context-opendatahub-io bash -c "cd /app && npm ci"
```

**Expected**: Installs 1945 packages in ~2 minutes. Shows deprecation warnings and 97 vulnerabilities but completes successfully.

**Validation result**: ✅ SUCCESS (exit 0)

### 3. Build the Site

```bash
podman exec test-context-opendatahub-io bash -c "cd /app && npm run build"
```

**Expected**: Takes 60-70 seconds, generates 1322 pages (1308 docs + 15 blog + 6 static). Shows some AsciiDoc warnings but completes successfully.

**Validation result**: ✅ SUCCESS (exit 0)

### 4. TypeScript Type Checking (Optional)

```bash
podman exec test-context-opendatahub-io bash -c "cd /app && npm run typecheck"
```

**Expected**: ❌ FAILS if run before build (missing generated `Queries` namespace). Run after build for accurate results.

**Validation result**: ❌ FAILED when run standalone (exit 1)

**Note**: TypeScript check depends on Gatsby-generated types. Not enforced in CI.

### 5. Prettier Format Checking (Optional)

```bash
podman exec test-context-opendatahub-io bash -c "cd /app && npx prettier --check 'src/**/*.{ts,tsx,js,jsx,json,md}'"
```

**Expected**: ❌ FAILS - finds formatting issues in 30 files. Shows warnings about unknown `importOrder` options (requires `@trivago/prettier-plugin-sort-imports` which is not installed).

**Validation result**: ❌ FAILED (exit 1, 30 files need formatting)

**Note**: Prettier is not enforced in CI.

### 6. Run Tests

```bash
# No tests configured in this repository
```

**Validation result**: N/A - no test framework

### 7. Cleanup

```bash
podman rm -f test-context-opendatahub-io
```

## Validation Results

| Step | Command | Status | Notes |
|------|---------|--------|-------|
| **Dependencies** | `npm ci` | ✅ PASS | 1945 packages, 2min, 97 vulnerabilities |
| **Build** | `npm run build` | ✅ PASS | 66 sec, 1322 pages generated |
| **TypeScript** | `npm run typecheck` | ❌ FAIL | Needs build first for generated types |
| **Prettier** | `npx prettier --check ...` | ❌ FAIL | 30 files have formatting issues |
| **Tests** | N/A | N/A | No test framework configured |

**Critical for merge**: Only the build must succeed (enforced by `.github/workflows/pull-request.yml`).

## CI/CD

### Gating Checks (run on `pull_request`)

**Workflow**: `.github/workflows/pull-request.yml`

```yaml
- run: npm ci
- run: npm run build
```

**What it validates**: Dependencies install and site builds successfully. No linting, no type checking, no tests.

**This is the only gating check.** PRs must pass this to merge.

### Deploy Workflows (run on push to `main`)

1. **gatsby.yml**: Builds and deploys to GitHub Pages
2. **deploy-site.yml**: Builds and deploys to gh-pages branch (runs daily at midnight + on push)

Both run the same build commands but are not gating for PRs.

## Linting

### Prettier (Code Formatting)

**Config**: `.prettierrc`

```json
{
  "importOrder": ["^components/(.*)$", "^[./]"],
  "importOrderSeparation": true,
  "importOrderSortSpecifiers": true
}
```

**Check command**:
```bash
npx prettier --check 'src/**/*.{ts,tsx,js,jsx,json,md}'
```

**Fix command**:
```bash
npx prettier --write 'src/**/*.{ts,tsx,js,jsx,json,md}'
```

**Status**: ❌ 30 files currently fail formatting checks. Not enforced in CI.

**Issue**: Config references `importOrder` options that require `@trivago/prettier-plugin-sort-imports` plugin, which is not installed. Prettier ignores these options.

### TypeScript (Type Checking)

**Config**: `tsconfig.json` (strict mode enabled)

**Check command**:
```bash
npm run typecheck
```
*(runs `tsc --noEmit`)*

**Status**: ❌ Fails when run standalone because Gatsby generates TypeScript definitions during build. Must run `npm run build` first.

**Fix command**: None (fix code, not config)

**Not enforced in CI.**

### ESLint

**Status**: ❌ Not configured

## Testing

**Status**: ❌ No test framework configured

No tests exist in this repository. This is a static documentation site with no automated testing.

## Build

**System**: npm / Gatsby 5.8.1

**Install dependencies**:
```bash
npm ci
```

**Build site**:
```bash
npm run build
```
*(runs `gatsby build`)*

**Output**: `public/` directory with static site (1322 pages)

**Build time**: ~60-70 seconds

**Dev server** (not needed for validation):
```bash
npm run develop
```

## Conventions

### Project Structure

```
src/
├── components/      # React components
│   ├── pages/      # Page-specific components
│   └── shared/     # Shared components
├── content/        # Markdown/AsciiDoc content
│   ├── blog/       # Blog posts (YYYY-MM-DD-title.md)
│   ├── docs/       # Documentation
│   ├── pages/      # Static pages
│   └── assets/     # Images and files
├── pages/          # Gatsby page components
├── templates/      # Page templates
└── styles/         # Global styles
```

### File Naming

- **Blog posts**: `YYYY-MM-DD-unique-title.md` in `src/content/blog/`
- **Components**: PascalCase `.tsx` files
- **Pages**: lowercase `.tsx` files in `src/pages/`
- **No test files** (no testing convention)

### Import Style

Prettier configured to order imports:
1. Component imports (`^components/(.*)$`)
2. Local imports (`^[./]`)

With separation between groups. However, the plugin to enforce this is not installed.

## Gaps & Caveats

### Critical Gaps

1. **No tests**: No test framework, no tests, no test coverage
2. **No enforced linting**: Prettier and TypeScript checks exist but aren't run in CI
3. **TypeScript check broken**: Cannot run `npm run typecheck` standalone — requires build first
4. **Formatting issues**: 30 files don't pass prettier checks
5. **No ESLint**: No JavaScript/TypeScript linting beyond TypeScript compiler

### Security & Maintenance

- 97 npm vulnerabilities (12 low, 36 moderate, 41 high, 8 critical)
- Multiple deprecated dependencies (asciidoctor.js, babel-eslint, core-js@2, etc.)
- Prettier config references plugin that's not installed

### What Works

✅ Build is reliable and gating
✅ Gatsby generates 1300+ pages successfully
✅ TypeScript compilation works (via Gatsby build)
✅ Dependencies install cleanly

### What Doesn't Work

❌ Standalone TypeScript checking (needs build)
❌ Prettier enforcement (30 files fail, not in CI)
❌ No way to validate patches beyond "does it build?"
❌ No tests to catch regressions

## Agent Readiness Assessment

**Rating**: MEDIUM

**Rationale**: An agent can validate that patches don't break the build (the only gating check), but cannot validate code quality, type safety, or functional correctness due to lack of tests and unenforced linting. Build validation is reliable and fast (~2min deps + 1min build).

**What an agent can do**:
- Apply patches
- Install dependencies
- Build the site
- Detect build failures (syntax errors, broken imports, Gatsby config issues)

**What an agent cannot do**:
- Run tests (none exist)
- Validate type safety reliably (TypeScript check needs build)
- Enforce code style (linting not enforced)
- Catch functional regressions (no tests)
- Validate runtime behavior (static site)

## Quick Reference

**Validate a patch**:
```bash
# Start container
podman run -d --name test-context-opendatahub-io \
  -v $(pwd):/app:Z -w /app node:20 sleep infinity

# Install & build (gating check)
podman exec test-context-opendatahub-io bash -c "cd /app && npm ci && npm run build"

# Check exit code
echo $?  # 0 = pass, non-zero = fail

# Cleanup
podman rm -f test-context-opendatahub-io
```

**This replicates the exact CI gating check.**

**Node version**: 20 (from `.github/workflows/gatsby.yml`)
**Primary validation**: Build must succeed
**Time**: ~3 minutes total (2min install + 1min build)
