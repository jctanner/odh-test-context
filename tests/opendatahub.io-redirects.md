# Test Context: opendatahub.io-redirects

**Agent Readiness: LOW** — No tests or linting exist. Only build validation is available.

## Overview

This is a Jekyll static site used for redirects to opendatahub.io. It's a minimal repository with no test suite or linting configuration. The only validation is whether the Jekyll site builds successfully.

- **Languages**: Ruby (Jekyll), HTML, CSS
- **Build System**: Bundler + Jekyll
- **CI System**: GitLab CI (no GitHub Actions)
- **Ruby Version**: 2.3.7 (very old, EOL)
- **Tests**: None
- **Linting**: None

## Container Recipe

This recipe validates that a patch doesn't break the Jekyll build. There are no tests to run.

### 1. Start Container

```bash
podman run -d --name test-context-opendatahub-io-redirects \
  -v $(pwd):/app:Z \
  -w /app \
  docker.io/library/ruby:2.3 \
  sleep infinity
```

If `podman` is unavailable, replace with `docker`.

### 2. Install Dependencies

```bash
podman exec test-context-opendatahub-io-redirects bash -c "cd /app && bundle install"
```

**Expected Result**: Exit code 0. Installs 27 gems including jekyll 3.8.5 and jekyll-redirect-from 0.15.0.

### 3. Build Jekyll Site

```bash
podman exec test-context-opendatahub-io-redirects bash -c "cd /app && bundle exec jekyll build -d test"
```

**Expected Result**: Exit code 0. Output shows "done in 0.xxx seconds" with no errors.

This is the primary validation — if the site builds, the patch is valid.

### 4. Cleanup

```bash
podman rm -f test-context-opendatahub-io-redirects
rm -rf test
```

**Always run cleanup**, even if validation fails.

## Validation Results

### Dependency Installation
- **Command**: `bundle install`
- **Status**: ✅ PASS
- **Exit Code**: 0
- **Notes**: Successfully installed all 27 gems. No issues.

### Jekyll Build
- **Command**: `bundle exec jekyll build -d test`
- **Status**: ✅ PASS
- **Exit Code**: 0
- **Output**:
  ```
  Configuration file: /app/_config.yml
              Source: /app
         Destination: test
   Incremental build: disabled. Enable with --incremental
        Generating...
                      done in 0.089 seconds.
   Auto-regeneration: disabled. Use --watch to enable.
  ```
- **Notes**: Build completed in <0.1 seconds. Generated static HTML files to test/ directory.

## CI/CD

### GitLab CI Pipeline

The repository uses GitLab CI (`.gitlab-ci.yml`), not GitHub Actions.

**Gating Check (test stage):**
```bash
bundle install
bundle exec jekyll build -d test
```
- Runs on all branches except master
- **Purpose**: Verify the Jekyll site builds without errors
- **Required**: Yes (gating)

**Deploy Stage (pages):**
```bash
bundle install
bundle exec jekyll build -d public
```
- Runs only on master branch
- Deploys to GitLab Pages
- Not a gating check for PRs

## Conventions

This is a minimal static site with no code to test. Standard Jekyll project structure:
- `_layouts/` — Page templates
- `_sass/` — SASS stylesheets
- `css/` — Compiled CSS
- `_config.yml` — Jekyll configuration
- `Gemfile` — Ruby dependencies

No coding conventions beyond standard Jekyll practices.

## Gaps & Caveats

1. **No Test Suite**: This repository has no automated tests. It's a static redirect site.

2. **No Linting**: No linters configured (no rubocop, no htmlproofer, nothing).

3. **No GitHub Actions**: Uses GitLab CI instead. If this repo is mirrored to GitHub, CI may not run.

4. **Very Old Ruby**: Uses Ruby 2.3.7 (released 2018, EOL). Modern Ruby versions may have compatibility issues.

5. **Limited Validation**: The only validation available is "does Jekyll build succeed?" This catches syntax errors in YAML/HTML/Markdown but nothing else.

6. **No Pre-commit Hooks**: No `.pre-commit-config.yaml` or git hooks.

7. **Agent Limitations**: An AI agent can validate that patches don't break the build, but cannot verify:
   - That redirects work correctly
   - That URLs are valid
   - That the site looks correct when deployed
   - Any functional behavior

## Quick Validation (One-Liner)

For a simple pass/fail validation:

```bash
podman run --rm -v $(pwd):/app:Z -w /app docker.io/library/ruby:2.3 \
  bash -c "bundle install && bundle exec jekyll build -d /tmp/test"
```

Exit code 0 = build succeeds, patch is valid.

## Interpreting Results

- **Build succeeds (exit 0)**: Patch is valid. Jekyll can parse all files.
- **Build fails (exit non-zero)**: Patch broke something. Check error message for:
  - YAML syntax errors in `_config.yml` or front matter
  - Liquid template syntax errors
  - Missing dependencies
  - Invalid markdown

## Notes for AI Agents

This repository has **minimal validation infrastructure**. You can:
- ✅ Verify patches don't break the Jekyll build
- ✅ Detect syntax errors in YAML, HTML, Markdown, Liquid templates
- ❌ Cannot run tests (none exist)
- ❌ Cannot run linters (none configured)
- ❌ Cannot verify redirects work correctly
- ❌ Cannot verify site functionality

**Recommendation**: For patches to this repo, the build validation is the only automated check available. Manual review of redirect URLs is needed for correctness.
