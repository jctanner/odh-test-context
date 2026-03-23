# Test Context: opendatahub-io/runbooks

**Agent Readiness: NONE** — This is a documentation-only repository with no code, tests, linters, or CI infrastructure.

## Overview

This repository contains operational runbooks for Open Data Hub alerts. It consists solely of markdown documentation files with no executable code, no test infrastructure, and no automated validation.

**Languages:** None (documentation only)
**Build System:** None
**Test Framework:** None
**Linting:** None configured

## Repository Structure

```
runbooks/
├── README.md              # Repository overview
├── template.md            # Template for new runbooks
├── OWNERS                 # Reviewers and approvers
└── alerts/
    └── component_name/    # Runbooks organized by component
        └── alert_name.md  # Individual alert runbooks
```

Currently contains runbooks for:
- **kueue**: 4 alert runbooks (kueue-pod-down, low-cluster-queue-resource-usage, pending-workload-pods, resource-reservation-exceeds-quota)

## Documentation Conventions

### Runbook Structure

Each runbook follows the template defined in `template.md`:

1. **Alert Name** (H1 header)
2. **Severity** (info, warning, critical)
3. **Impact** (what impact the cause of this alert will have)
4. **Summary** (brief description of what caused the alert)
5. **Steps** (numbered troubleshooting steps)

### File Organization

- Runbooks are placed in `alerts/{component_name}/{alert_name}.md`
- Each component subfolder should have its own OWNERS file
- Alert names use kebab-case (e.g., `kueue-pod-down.md`)

### Example Runbook

See `alerts/kueue/kueue-pod-down.md` for a complete example showing:
- Clear severity marking
- Impact description
- Prometheus query context
- Step-by-step troubleshooting with kubectl/oc commands
- Escalation path to engineering team

## Container Recipe

**Not applicable** — This repository contains no executable code.

## Validation Results

No validation was performed. There is no code to build, lint, or test.

## CI/CD

**No CI/CD configured.**

There are no GitHub Actions workflows, no pre-commit hooks, no automated checks of any kind. Pull requests are reviewed manually with no gating checks.

## Gaps & Caveats

This repository has no automated quality controls. Potential improvements that would enable agent validation:

1. **Markdown linting**: Install markdownlint-cli or similar
   - Would catch formatting issues, broken links, inconsistent heading levels
   - Example: `npm install -g markdownlint-cli && markdownlint '**/*.md'`

2. **Structure validation**: Test that runbooks match the template
   - Could use a simple script to check for required sections
   - Verify H1 matches filename, Severity field exists, etc.

3. **Link checking**: Validate no broken links
   - Example: `npm install -g markdown-link-check && markdown-link-check **/*.md`

4. **Spell checking**: Run a spellchecker
   - Example: `npm install -g cspell && cspell '**/*.md'`

5. **CI workflow**: Add GitHub Actions to run checks on PRs
   - Would make the repository agent-friendly for patch validation

6. **Pre-commit hooks**: Catch issues before commit
   - Could use `.pre-commit-config.yaml` with markdown hooks

## For Downstream Agents

**This repository cannot be used for automated patch validation** because:

- There is no lint command to run
- There are no tests to execute
- There is no CI configuration to replicate
- Changes can only be validated through human review

### What an Agent Can Do

1. **Clone and read**: An agent can read the documentation
2. **Apply patches**: An agent can modify markdown files
3. **Follow conventions**: An agent can ensure new files match the structure in `template.md`
4. **Check OWNERS**: An agent can verify OWNERS files exist for new components

### What an Agent Cannot Do

1. **Automated validation**: No pass/fail signal for changes
2. **Lint checking**: No linter to run
3. **Test execution**: No tests exist
4. **CI replication**: No CI to replicate locally

### Recommended Agent Workflow

When working with this repository, an agent should:

1. Read `template.md` to understand expected runbook structure
2. When creating new runbooks, follow the template exactly
3. Place files in correct location: `alerts/{component}/{alert}.md`
4. Use kebab-case for filenames
5. If adding a new component, create an OWNERS file in that component's directory
6. Request human review for all changes (no automated validation available)

## Human Review Process

Per the OWNERS file, pull requests require approval from:

**Approvers:**
- astefanutti
- Fiona-Waters
- kpostoffice
- sutaakar

**Reviewers:**
- astefanutti
- ChristianZaccaria
- dimakis
- Fiona-Waters
- kpostoffice
- sutaakar

Changes are validated entirely through human review. There are no automated checks to pass.

---

**Summary:** This is a documentation repository with no validation infrastructure. An agent can read and modify files but cannot validate changes programmatically. The repository would benefit from markdown linting and CI checks to become agent-friendly.
