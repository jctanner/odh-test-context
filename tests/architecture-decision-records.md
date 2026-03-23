# Test Context: architecture-decision-records

**Agent Readiness: none** — This repository has no automated validation infrastructure. All changes are validated through manual code review only.

---

## Overview

- **Repository:** opendatahub-io/architecture-decision-records
- **Type:** Documentation-only repository
- **Languages:** None (markdown files only)
- **Build System:** None
- **Lines of Markdown:** ~533 lines across ADRs and documentation

This repository contains Architecture Decision Records (ADRs) and architecture documentation for Open Data Hub and OpenShift AI. It has no code, no build system, no tests, and no automated validation.

---

## Container Recipe

**Not Applicable** — This repository contains only markdown documentation with no executable code, build process, or validation tooling. There are no commands to run or validate.

For a documentation repository like this, validation would typically include:
- Markdown linting (not configured)
- Link checking (not configured)
- Spell checking (not configured)
- Format validation (not configured)

None of these tools are currently set up in this repository.

---

## Validation Results

**No validation performed.** The repository has no:
- Linting configuration
- Test framework
- CI validation checks
- Build system
- Automated quality checks

---

## CI/CD

### GitHub Actions Workflows

Only one workflow exists:

**`.github/workflows/stale.yml`** (Advisory, not gating)
- **Trigger:** Scheduled daily at 3am UTC, manual dispatch
- **Purpose:** Labels PRs stale after 21 days of inactivity, closes after 7 more days
- **Not for validation:** This workflow does not validate content quality

### Gating Checks

**None.** There are no automated gating checks. All validation is manual via code review.

### Code Review Requirements

Per `.github/CODEOWNERS`:
- All changes require approval from `@opendatahub-io/architects`
- Component-specific documentation requires additional team approval:
  - `documentation/components/dashboard/` → `@opendatahub-io/exploring-team`
  - `documentation/components/model-serving/` → `@opendatahub-io/model-serving`
  - `documentation/components/platform/` → `@opendatahub-io/platform`
  - etc.

---

## Conventions

### ADR Naming and Structure

- **Template:** `architecture-decision-records/ODH-ADR-0000-template.md`
- **Naming Pattern:** `ODH-ADR-{number}-{description}.md`
- **Organization:** ADRs organized by component subdirectories:
  - `operator/` — Operator-related ADRs
  - `model-serving/` — Model serving ADRs
  - `data-science-pipelines/` — Pipeline ADRs
  - `distributed-workloads/` — Distributed workload ADRs
  - `eval-hub/` — Evaluation hub ADRs
  - `explainability/` — Explainability ADRs
  - Root level — Cross-cutting ADRs

### Documentation Structure

- **Root:** `documentation/`
- **Components:** `documentation/components/{component-name}/`
- **Architecture Overview:** `documentation/arch-overview.md`

---

## Gaps & Caveats

This repository has **no automated validation infrastructure**. Gaps include:

1. **No Markdown Linting**
   - No `.markdownlint.json`, `.mdlrc`, or prettier configuration
   - No style/formatting validation
   - Inconsistent formatting possible

2. **No Link Validation**
   - No automated checking for broken internal/external links
   - No validation of image references

3. **No Spell Checking**
   - No automated spell check in CI
   - Typos caught only in manual review

4. **No Pre-commit Hooks**
   - No local validation before commit
   - No automated formatting

5. **No CI Validation**
   - Stale PR workflow does not validate content
   - No automated checks for ADR format compliance
   - No validation that new ADRs follow template

6. **Manual Review Only**
   - All quality control relies on human reviewers
   - No programmatic enforcement of standards

---

## How to Validate a Patch (Manual Process)

Since there are no automated checks, validation is entirely manual:

### 1. Content Review

Read the changed markdown files and verify:
- Correct markdown syntax
- Links work (manually click/check)
- Images render correctly
- Spelling and grammar are correct
- ADRs follow the template structure (if applicable)

### 2. Naming Conventions

For new ADRs, check:
- Filename follows `ODH-ADR-{number}-{description}.md` pattern
- Number is sequential and not duplicated
- File is in appropriate subdirectory

### 3. CODEOWNERS Approval

Ensure the change is reviewed by:
- `@opendatahub-io/architects` (required for all changes)
- Component-specific team if modifying component documentation

### 4. Local Preview (Optional)

To render markdown locally:

```bash
# Install a markdown viewer (example using grip)
pip install grip

# Preview a file at http://localhost:6419
grip architecture-decision-records/ODH-ADR-0001-use-architecture-decision-records-for-open-data-hub.md
```

Or use any markdown editor (VS Code, Typora, etc.)

---

## Recommendations for Improving Agent Readiness

To make this repository more suitable for automated patch validation:

### Priority 1: Markdown Linting

Add `.markdownlint.json`:
```json
{
  "default": true,
  "MD013": { "line_length": 120 },
  "MD033": false
}
```

Add to CI:
```yaml
- name: Lint markdown
  run: npx markdownlint-cli2 "**/*.md"
```

### Priority 2: Link Validation

Add to CI:
```yaml
- name: Check links
  run: npx markdown-link-check **/*.md
```

### Priority 3: Spell Checking

Add to CI using `cspell` or `pyspelling`

### Priority 4: Pre-commit Hooks

Add `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.37.0
    hooks:
      - id: markdownlint
```

Until these are implemented, **agent readiness remains "none"** — an AI agent cannot programmatically validate patches to this repository.

---

**Analysis completed:** 2026-03-22T16:50:00Z
**Confidence:** High — Simple repository structure, comprehensive review of all config files
