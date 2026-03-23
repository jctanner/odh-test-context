# Test Context: opendatahub-documentation

**Generated:** 2026-03-22T23:48:45Z
**Agent Readiness:** medium
**Confidence:** high

## Overview

Documentation repository for Open Data Hub (AsciiDoc format). Uses Asciidoctor to build HTML documentation published to https://opendatahub.io/docs. No traditional tests—only link validation in CI.

**Languages:** AsciiDoc, Shell
**Build System:** Asciidoctor (Ruby-based)
**CI:** GitHub Actions (link checking only)

**Agent Readiness Rating: MEDIUM**
Justification: Build and link checking work reliably. No traditional test suite since this is documentation. Vale linting configured but has errors. An agent can validate builds and check for broken links, but cannot run comprehensive lint checks.

---

## Container Recipe

This recipe provides a complete, copy-paste approach for validating patches in an isolated container.

### 1. Start Container

```bash
podman run -d --name test-context-odh-docs \
  -v $(pwd):/app:Z \
  -w /app \
  ubuntu:24.04 \
  sleep infinity
```

Alternative with docker:
```bash
docker run -d --name test-context-odh-docs \
  -v $(pwd):/app \
  -w /app \
  ubuntu:24.04 \
  sleep infinity
```

### 2. Install System Dependencies

```bash
podman exec test-context-odh-docs bash -c "apt-get update && apt-get install -y asciidoctor curl git"
```

Required packages:
- **asciidoctor** - AsciiDoc to HTML converter (Ruby-based)
- **curl** - Used by link checker to validate URLs
- **git** - Required by check-updated-books.sh to diff files

### 3. Build Documentation

```bash
podman exec test-context-odh-docs bash -c "cd /app && bash scripts/build-docs-ci.sh"
```

**Expected result:**
- Exit code: 0
- Output: Some warnings about duplicate section IDs (non-fatal)
- Generated: `out/` directory with HTML files and index.html

**What this does:**
- Processes all root-level `.adoc` files (book entry points)
- Runs `asciidoctor` with flags: `-a toc=left -a doctype=book -a allow-uri-read -a sectanchors -a skip-front-matter`
- Creates `out/[book-name]/index.html` for each book
- Generates `out/index.html` listing all books

**Validation status:** ✅ **PASSED** (exit code 0, output generated)

### 4. Validate Links (Single File)

```bash
podman exec test-context-odh-docs bash -c "cd /app && bash scripts/check-book-links.sh README.adoc"
```

**Expected result:**
- Exit code: 0 (if no broken links)
- Output: "✅ All links are valid!" or list of broken URLs with HTTP status codes

**What this does:**
- Builds the .adoc file to HTML with asciidoctor
- Extracts all HTTP/HTTPS URLs from the HTML
- Tests each URL with `curl` (5 second timeout, 2 second connect timeout)
- Skips URLs matching patterns in `scripts/.links_ignore`
- Runs up to 10 concurrent curl checks

**Validation status:** ✅ **PASSED** (exit code 0, no broken links)

### 5. Validate Links (Modified Files - CI Command)

```bash
podman exec test-context-odh-docs bash -c "cd /app && bash scripts/check-updated-books.sh"
```

**Expected result:**
- Exit code: 0 (if no broken links in modified files)
- Output: Checks each affected book and reports broken links

**What this does:**
- Runs `git diff --name-only HEAD~1 HEAD` to find changed .adoc files
- Identifies which root-level books include the changed modules/assemblies
- Runs `scripts/check-book-links.sh` on each affected book
- Useful for PR validation (only checks relevant books, not entire repo)

**Validation status:** ✅ **Works** (depends on git history)

### 6. Cleanup

```bash
podman rm -f test-context-odh-docs
```

---

## Validation Results

### Build Command
- **Command:** `bash scripts/build-docs-ci.sh`
- **Exit code:** 0
- **Status:** ✅ SUCCESS
- **Output:** Warnings about duplicate IDs in some modules (non-fatal)
- **Notes:** Build completes successfully and generates 40+ HTML books to `out/` directory

### Link Checking
- **Command:** `bash scripts/check-book-links.sh README.adoc`
- **Exit code:** 0
- **Status:** ✅ SUCCESS
- **Output:** "✅ All links are valid!"
- **Notes:** Link validation works correctly. Uses curl to test HTTP/HTTPS URLs.

### Vale Linting (Optional, Not in CI)
- **Command:** `vale sync && vale '*.adoc'`
- **Exit code:** 2
- **Status:** ⚠️ FAILED
- **Output:** Regex error in RedHat style package (CaseSensitiveTerms.yml)
- **Notes:** Vale can be installed but the RedHat style configuration has errors. Vale is configured in `.vale.ini` but is NOT used in CI, so this does not block patches.

---

## CI/CD

### GitHub Actions Workflow

**File:** `.github/workflows/check-links.yml`

**Trigger:** `on: [push, pull_request]`

**Gating Check:**
```yaml
name: Check links in modified AsciiDoc files
steps:
  - Install Asciidoctor: apt-get install asciidoctor
  - Make scripts executable: chmod +x scripts/*.sh
  - Run: scripts/check-updated-books.sh
```

**What it validates:**
1. Finds all .adoc files modified in the PR (modules, assemblies, root books)
2. Determines which root-level books are affected by the changes
3. Builds each affected book to HTML with asciidoctor
4. Extracts all HTTP/HTTPS URLs from the rendered HTML
5. Tests each URL with curl (5s timeout)
6. Reports any URLs returning 404 or other non-2xx/3xx status codes
7. Ignores URLs matching patterns in `scripts/.links_ignore`

**This is the ONLY gating check.** Vale, gitleaks, and semgrep are configured but not enforced.

---

## Conventions

### Repository Structure
```
opendatahub-documentation/
├── _artifacts/document-attributes-global.adoc  # Product attributes ({productname-long}, etc.)
├── assemblies/                                  # Assembly files that organize modules
├── modules/                                     # Reusable documentation modules
├── images/                                      # Image assets
├── examples/                                    # Code examples and notebooks
├── scripts/                                     # Build and validation scripts
├── *.adoc                                       # Root-level book entry points
└── out/                                         # Generated HTML (created by build)
```

### AsciiDoc Conventions
- **Module types:** CONCEPT, PROCEDURE, REFERENCE, SNIPPET (specified via `:_mod-docs-content-type:`)
- **Heading levels:** Maximum 2 levels (= and ==), no deeper nesting
- **Section IDs:** All major sections have `id` attributes with `_{context}` suffix
- **Includes:** Use `include::` statements to reuse content from assemblies/ and modules/
- **Cross-references:** Use `xref:` for links between documentation pages
- **Product attributes:** Always use `{productname-long}` and `{productname-short}` instead of hardcoded names

### Documentation Standards (from CLAUDE.md)
- **No parentheticals:** Use colons or incorporate naturally into sentences (except acronym definitions)
- **Next steps sections:** No introductory sentence, jump straight to bullet list
- **Links in sentences:** No colons before link, period after link
- **Links in bullet lists:** Entire bullet is the link, no period at end
- **Code explanations:** No AsciiDoc callouts; use definition lists or bulleted lists

### File Naming
- Root-level books: `topic-name.adoc` (e.g., `working-with-ai-pipelines.adoc`)
- Modules: `modules/verb-noun.adoc` (e.g., `modules/creating-pipeline-run.adoc`)
- Assemblies: `assemblies/noun-phrase.adoc` (e.g., `assemblies/managing-ai-pipelines.adoc`)

---

## Gaps & Caveats

### What's Missing
1. **No traditional tests** - This is a documentation repository. No unit/integration/e2e tests exist.
2. **Vale linting not enforced** - Vale is configured (`.vale.ini`) but has errors in the RedHat style package and is NOT run in CI.
3. **Gitleaks not enforced** - Secret detection is configured (`.gitleaks.toml`) but NOT run in CI.
4. **Semgrep not enforced** - SAST rules are configured (`semgrep.yaml`) but NOT run in CI.
5. **No spell/grammar checking** - No automated prose quality checks in CI.
6. **Build warnings ignored** - Build produces warnings about duplicate section IDs but these don't fail the build.

### What Works
1. **Build process** - `scripts/build-docs-ci.sh` works reliably and generates HTML
2. **Link checking** - `scripts/check-book-links.sh` validates HTTP/HTTPS URLs correctly
3. **CI workflow** - GitHub Actions link checking runs on every PR

### What Requires Manual Validation
1. **AsciiDoc structure** - No automated check that modules follow Red Hat modular documentation standards
2. **Content quality** - No automated review of technical accuracy, clarity, or completeness
3. **Attribute usage** - No check that product attributes are used instead of hardcoded names
4. **Cross-references** - No validation that `xref:` links point to valid targets

### Infrastructure Requirements
- **None** - All validation runs in standard Ubuntu containers with apt packages
- Link checking requires internet access to test external URLs
- Vale could be used locally but requires fixing the RedHat style configuration

---

## How to Validate a Patch

### Automated Validation (What CI Does)
```bash
# 1. Start container
podman run -d --name test-context-odh-docs -v $(pwd):/app:Z -w /app ubuntu:24.04 sleep infinity

# 2. Install dependencies
podman exec test-context-odh-docs bash -c "apt-get update && apt-get install -y asciidoctor curl git"

# 3. Build documentation
podman exec test-context-odh-docs bash -c "cd /app && bash scripts/build-docs-ci.sh"

# 4. Check links in modified files
podman exec test-context-odh-docs bash -c "cd /app && bash scripts/check-updated-books.sh"

# 5. Cleanup
podman rm -f test-context-odh-docs
```

**Expected result:**
- Build: Exit code 0 (warnings OK)
- Link check: Exit code 0 (no broken links)

### Manual Validation (Optional)
```bash
# Check a specific file for broken links
podman exec test-context-odh-docs bash -c "cd /app && bash scripts/check-book-links.sh my-book.adoc"

# Build and view output locally
podman exec test-context-odh-docs bash -c "cd /app && bash scripts/build-docs-ci.sh"
# Then open out/index.html in a browser to review rendered HTML
```

### What to Look For
1. **Build succeeds** - Exit code 0 from `scripts/build-docs-ci.sh`
2. **No broken links** - Exit code 0 from link checking (or justifiable failures for expected dead links)
3. **Manual review** - Technical accuracy, grammar, proper use of product attributes, correct AsciiDoc formatting

---

## Additional Notes

### ReadTheDocs Build
The production build on ReadTheDocs uses Python 3.12 with the same asciidoctor setup:
```yaml
# .readthedocs.yaml
build:
  os: ubuntu-24.04
  tools:
    python: "3.12"
  apt_packages:
    - asciidoctor
  jobs:
    build:
      html:
        - bash scripts/build-docs-ci.sh
        - mkdir -p "$READTHEDOCS_OUTPUT/html"
        - cp -a out/. "$READTHEDOCS_OUTPUT/html/"
```

This container recipe matches the ReadTheDocs environment.

### Downstream Sync
This repository is upstream for Red Hat OpenShift AI documentation. Content flows to internal Red Hat GitLab. Downstream uses `cloud-service` and `self-managed` attributes instead of `upstream`.

### Performance Notes
- Full link checking can take several minutes depending on number of external URLs
- Build time: ~30-60 seconds for full documentation set
- Link checking: Runs 10 concurrent curl checks per file, 5s timeout per URL

---

## Quick Reference

**Build:** `bash scripts/build-docs-ci.sh`
**Check single file:** `bash scripts/check-book-links.sh <file.adoc>`
**Check modified files (CI):** `bash scripts/check-updated-books.sh`
**Output directory:** `out/`
**Published URL:** https://opendatahub.io/docs

**Container base:** `ubuntu:24.04`
**Required packages:** `asciidoctor curl git`

**Exit code 0 = success**
**Exit code 1 = link validation failed**
**Exit code 2+ = build or configuration error**
