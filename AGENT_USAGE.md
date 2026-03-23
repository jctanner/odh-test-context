# Agent Usage Guide

This document explains how to navigate and use the pre-generated test context data in this repository. If you are an AI agent that needs to validate a patch against an opendatahub-io repository, start here.

## Quick Start

All generated test context data lives under `./tests/`. The `checkouts/` directory is gitignored and only exists locally when someone runs the pipeline — you will not find it in a clone from GitHub.

To validate a patch against a repo:

1. Find the repo's markdown file: `tests/{repo_name}.md`
2. Read the **Container Recipe** section
3. Follow the steps verbatim: start container, install deps, apply patch, lint, test, clean up

## Directory Layout

```
tests/
  README.md                    # Index table linking to all repo files
  {repo_name}.json             # Structured test context (machine-readable)
  {repo_name}.md               # Runbook for running lint/tests (agent-readable)
```

Each repo has two files. Use `.md` when you need to follow instructions. Use `.json` when you need to extract specific fields programmatically.

## The Markdown File (`{repo}.md`)

Each markdown file is a self-contained runbook. The most important section is **Container Recipe** — it gives you everything needed to validate a patch in an isolated container without any discovery work.

### Sections

| Section | What it tells you |
|---------|-------------------|
| **Overview** | Languages, build system, one-line description |
| **Agent Readiness** | Rating (high/medium/low/none) with justification — check this first to know if validation is feasible |
| **Container Recipe** | Step-by-step: base image, podman/docker run command, system deps, dependency install, build, lint commands, test commands, single-test commands, cleanup |
| **Validation Results** | Container image used, each command's pass/fail/exit code, output snippets for failures |
| **CI/CD** | Which checks gate merges, exact commands CI runs |
| **Conventions** | Test file naming, test patterns, import style |
| **Gaps & Caveats** | What's missing, what requires special infrastructure |

### How to use it for patch validation

```
1. Read the Container Recipe section
2. Start a container with the repo mounted:
   podman run -d --name test-context-{repo} -v {repo_path}:/app:Z -w /app {base_image} sleep infinity
3. Install system deps:
   podman exec test-context-{repo} bash -c "apt-get update && apt-get install -y {deps}"
4. Install project deps:
   podman exec test-context-{repo} bash -c "cd /app && {install_command}"
5. Apply your patch
6. Run lint:
   podman exec test-context-{repo} bash -c "cd /app && {lint_command}"
7. Run tests:
   podman exec test-context-{repo} bash -c "cd /app && {test_command}"
8. Clean up:
   podman rm -f test-context-{repo}
```

## The JSON File (`{repo}.json`)

Structured data for programmatic consumption. Top-level fields:

| Field | Type | Description |
|-------|------|-------------|
| `repo` | string | Repository name |
| `org` | string | GitHub organization |
| `analyzed_at` | string | ISO 8601 timestamp |
| `languages` | string[] | Detected programming languages |
| `linting` | object | Linter tools, configs, and run commands |
| `testing` | object | Test framework, directories, run commands, env vars |
| `ci` | object | CI system, config files, gating/advisory checks |
| `build` | object | Build system, install and build commands |
| `conventions` | object | Test file patterns, naming, import style |
| `container_recipe` | object | Validated container setup: image, deps, commands |
| `validation` | object | Per-step results: exit codes, output snippets |
| `gaps` | string[] | Missing or problematic aspects |
| `agent_readiness` | string | `high`, `medium`, `low`, or `none` |
| `confidence` | string | `high`, `medium`, or `low` |

### Key JSON fields for patch validation

The `container_recipe` object contains everything you need:

```json
{
  "container_recipe": {
    "base_image": "python:3.11",
    "system_deps": ["make", "git"],
    "setup_commands": ["pip install -e '.[dev]'"],
    "lint_commands": [
      {"command": "ruff check .", "validated": true, "notes": "passed clean"}
    ],
    "test_commands": [
      {"command": "pytest tests/", "validated": true, "notes": "47 passed"}
    ],
    "test_single_file": "pytest {file}",
    "test_single_test": "pytest {file}::{test_name}",
    "env_vars": [],
    "notes": ""
  }
}
```

### Agent readiness rating

Check `agent_readiness` before attempting validation:

| Rating | What to do |
|--------|------------|
| **high** | Full validation possible. Run lint and test commands from the container recipe. |
| **medium** | Partial validation. Some commands work — check `validation.results` to see which. |
| **low** | Validation not feasible. You can apply the patch but can't confirm it works. |
| **none** | No test infrastructure. Skip validation entirely. |

## Common Agent Tasks

### "How do I lint this repo?"

Read `tests/{repo}.json` and extract `container_recipe.lint_commands`. Each entry has a `command` field and a `validated` boolean telling you if it actually worked.

### "How do I run tests for a specific file I changed?"

Read `tests/{repo}.json` and extract `container_recipe.test_single_file`. Replace `{file}` with your file path. Example: `pytest {file}` becomes `pytest tests/test_auth.py`.

### "Can I validate patches against this repo?"

Check `tests/{repo}.json` field `agent_readiness`. If `high` or `medium`, yes. Read `validation.summary` for a quick status of what works.

### "What container image should I use?"

Read `tests/{repo}.json` and extract `container_recipe.base_image`. This is the exact image tag that was validated.

### "What system packages are needed?"

Read `tests/{repo}.json` and extract `container_recipe.system_deps`. Install them with `apt-get install -y` inside the container.

### "What checks does CI gate on?"

Read `tests/{repo}.json` and extract `ci.gating_checks`. Each entry has a `name`, `command`, and `required` boolean.

### "What's missing or broken for this repo?"

Read `tests/{repo}.json` field `gaps` for a list of known issues, and `validation.results` for per-command pass/fail details.

## The `checkouts/` Directory (Local Only)

This directory is **gitignored** and will not exist in a GitHub clone. It only appears when someone runs the pipeline locally.

When present, it contains the actual cloned source repositories with `GENERATED_TEST_CONTEXT.json` and `GENERATED_TEST_CONTEXT.md` files in each repo root:

```
checkouts/opendatahub-io/
  odh-dashboard/
    GENERATED_TEST_CONTEXT.json
    GENERATED_TEST_CONTEXT.md
    ... (repo source files)
  kserve/
    GENERATED_TEST_CONTEXT.json
    GENERATED_TEST_CONTEXT.md
    ...
```

The `tests/` directory is a collected copy of these files, organized for easy access without needing the full checkouts.
