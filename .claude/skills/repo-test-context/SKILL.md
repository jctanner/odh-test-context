---
name: repo-test-context
description: Extract test context from a repository for AI-assisted patch validation
allowed-tools: Read, Glob, Grep, Bash, Write
---

# repo-test-context

Extract operational test context from a repository so that AI agents can
validate patches by running the correct lint, test, and build commands.
Validate discovered commands by running them in an isolated container.

## Instructions

You are analyzing a repository to extract the operational knowledge an AI agent
needs to validate patches: linter configuration, test commands, CI gating
criteria, build setup, and conventions.

Your output must be **executable and precise** — another agent will use your
output to actually run lint and test commands. Prefer exact commands over
descriptions.

After discovering commands statically, you will **validate them live** in a
container to prove they actually work.

### Step 1: Discover project type

Scan the repository root for build/config files to identify languages and build
systems:

- `pyproject.toml`, `setup.py`, `setup.cfg`, `tox.ini` → Python
- `package.json`, `tsconfig.json` → JavaScript/TypeScript
- `go.mod`, `go.sum` → Go
- `pom.xml`, `build.gradle` → Java
- `Cargo.toml` → Rust
- `Makefile`, `CMakeLists.txt` → C/C++ or multi-language
- `Dockerfile`, `Containerfile` → Container build
- `Tiltfile`, `skaffold.yaml` → Dev tooling

Note all languages found. Many repos are polyglot.

### Step 2: Extract linting configuration

Find linter configs and extract exact run commands:

**Python:** Look for `ruff` config in `pyproject.toml` (`[tool.ruff]`), `.flake8`,
`pylintrc`, `mypy.ini` or `[tool.mypy]` in pyproject.toml. Check Makefile for
`lint` target. Check `tox.ini` for lint environments.

**JavaScript/TypeScript:** Look for `.eslintrc*`, `.eslintrc.json`, `.eslintrc.js`,
`eslint.config.*`. Check `package.json` `scripts.lint`. Look for prettier config.

**Go:** Look for `.golangci.yml` or `.golangci.yaml`. Check Makefile for `lint`
target. Look for `golangci-lint` in CI workflows.

**General:** Check Makefile targets (`make lint`, `make check`), CI workflow
`run:` steps for lint commands, and pre-commit config (`.pre-commit-config.yaml`).

For each linter found, record:
- Tool name and version (if pinned)
- Config file location
- Exact run command
- Auto-fix command (if available)
- Scope (full project, specific directories)

### Step 3: Extract testing configuration

Find test frameworks, directories, and run commands:

**Python:** Read `[tool.pytest]` or `[tool.pytest.ini_options]` in `pyproject.toml`.
Look for `conftest.py` files, `tests/` or `test/` directories. Check for `tox.ini`
test environments. Check Makefile `test` target. Determine:
- `pytest` invocation with correct options
- How to run a single test file: `pytest {file}`
- How to run a single test: `pytest {file}::{test_name}` or `-k` pattern
- Required fixtures or conftest setup
- Markers used (`@pytest.mark.slow`, etc.)

**JavaScript/TypeScript:** Read `package.json` `scripts.test`. Look for jest config
(`jest.config.*`), vitest config, mocha config. Find test directories
(`__tests__/`, `*.test.ts`, `*.spec.ts`). Determine:
- Test runner command (`npm test`, `npx jest`, etc.)
- Single file: `npx jest {file}`
- Single test: `npx jest -t '{name}'`

**Go:** Look for `*_test.go` files. Check Makefile `test` target. Standard
pattern is `go test ./...`. Determine:
- Full test command with flags
- Single package: `go test ./{package}/...`
- Single test: `go test -run '{TestName}' ./{package}/...`
- Build tags if used (`-tags integration`)

**General:** Check for test infrastructure that requires external services
(databases, clusters, APIs). Note environment variables needed. Find test
fixture locations, mock patterns, and helper utilities.

### Step 4: Extract CI configuration

Read `.github/workflows/*.yml` files. For each workflow:

- Identify the trigger (`on: pull_request`, `on: push`, etc.)
- Extract every `run:` step command verbatim
- Identify which jobs/checks are gating (required status checks)
- Note required secrets or infrastructure (clusters, registries)
- Note matrix builds (multiple Go/Node versions, OS variants)

Also check for:
- `.tekton/` pipeline configs
- `Jenkinsfile`
- `.zuul.yaml`
- `Makefile` CI-related targets

**Gating vs advisory:** If a check is in a `pull_request` triggered workflow
and the repo requires it to merge, it's gating. If you can't determine
whether it's required, note it as "likely gating" based on the workflow name
(e.g., `ci.yml`, `lint.yml`, `test.yml` are typically gating).

### Step 5: Extract build configuration

Find how to build and set up the project for development:

- Dependency install command (`npm ci`, `pip install -e ".[dev]"`, `go mod download`)
- Build command (`make build`, `npm run build`, `go build ./...`)
- Dev server command if applicable
- Container build command (`docker build`, `podman build`)
- Any pre-build steps (code generation, asset compilation)

### Step 6: Identify conventions

Look for patterns in the codebase:

- Test file naming: `*_test.go`, `*.test.ts`, `test_*.py`, etc.
- Test function naming: `Test*`, `test_*`, `describe/it`, etc.
- Import style: relative vs absolute, grouped imports
- Coverage thresholds (from CI config or tool config)
- Code review requirements (CODEOWNERS, branch protection docs)

### Step 7: Flag gaps

Honestly report what's missing or problematic:

- No tests at all
- Tests exist but no clear run command
- CI configured but tests require infrastructure you can't access
- Outdated or broken test configuration
- Missing linter configuration
- Tests that only run in specific environments (OpenShift cluster, GPU, etc.)
- Undocumented environment setup requirements

### Step 8: Live validation in container

After completing the static analysis (steps 1-7), validate your discovered
commands by running them in an isolated container. This proves the commands
actually work rather than just looking plausible.

#### Container setup

1. **Choose a base image** based on the detected language(s):
   - Python: `python:3.11` (or version from CI config / pyproject.toml)
   - JavaScript/TypeScript: `node:20` (or version from CI config / .nvmrc)
   - Go: `golang:1.22` (or version from go.mod)
   - Java: `maven:3-eclipse-temurin-17` or `gradle:8-jdk17`
   - Multi-language: pick the primary language image, install others inside
   - If the repo has a `Dockerfile` with a builder stage, read it for hints
     about the correct base image and system dependencies

2. **Name the container** clearly: `test-context-{repo_name}`
   Example: `test-context-odh-dashboard`

3. **Start the container** with the repo bind-mounted as read-write to `/app`:
   ```
   podman run -d --name test-context-{repo_name} \
     -v {repo_path}:/app:Z \
     -w /app \
     {base_image} \
     sleep infinity
   ```

   If `podman` is not available, fall back to `docker`.

4. **Install system dependencies** if needed (based on CI config or Dockerfile):
   ```
   podman exec test-context-{repo_name} bash -c "apt-get update && apt-get install -y make git"
   ```

#### Validation sequence

Run each discovered command inside the container using
`podman exec test-context-{repo_name} bash -c "cd /app && {command}"`.

Execute in this order, recording the result of each:

1. **Dependency install**: Run the install command (e.g. `npm ci`, `pip install -e ".[dev]"`,
   `go mod download`). Record exit code and whether it succeeded.

2. **Build** (if applicable): Run the build command. Record exit code.

3. **Lint**: Run each discovered lint command. Record:
   - Exit code
   - Whether it produced lint errors (exit code != 0 may mean lint violations,
     not a broken command — distinguish between "linter found issues" and
     "linter failed to run")
   - First ~20 lines of output for context

4. **Tests**: Run the test command. Record:
   - Exit code
   - Number of tests found/run/passed/failed (parse from output if possible)
   - Whether failure is "tests failed" vs "test framework couldn't start"
   - First ~20 lines of output for context
   - Use a timeout (5 minutes max) — kill the test run if it hangs

For each command, capture:
- The exact command run
- Exit code
- Pass/fail determination
- Truncated output (first 20 lines of stdout+stderr)
- Whether failure indicates a broken command vs legitimate lint/test failures

#### Container cleanup

**Always clean up the container when done**, even if validation fails partway:

```
podman rm -f test-context-{repo_name}
```

Wrap your validation in a try/finally pattern — the container must be removed.

#### Handling validation failures

- If dependency install fails, skip build/lint/test and note "deps failed"
- If the base image is wrong (missing tools), try a different image
- If a command times out, record it as "timed out" not "failed"
- If tests require external services (databases, clusters), record
  "requires infrastructure" and note what's needed
- Do not spend more than 2 attempts on any single command

### Prioritization rules

1. **CI configs are ground truth** — whatever actually runs in CI is the
   authoritative source. Prioritize commands from GitHub Actions workflows
   over README instructions or Makefile targets that may be unused.

2. **Executable commands over descriptions** — don't produce "this project
   uses pytest." Produce `cd src && python -m pytest tests/ -x --tb=short`.
   The consumer is another AI agent that will execute these commands.

3. **Infer from config files when docs are missing** — many repos have test
   infra but zero documentation. Read `pyproject.toml`, Makefile targets,
   `package.json` scripts, and CI YAML to infer correct commands.

4. **Flag gaps honestly** — if a repo has no tests, say so. If tests exist
   but you can't determine the run command, say so. Gaps are valuable
   information for the downstream consumer.

5. **Validation overrides guesses** — if you discovered a command statically
   but it failed in live validation, update your output to reflect reality.
   The validated command (or the fact that it doesn't work) is the truth.

### Agent readiness rating

After validation, assign an **agent_readiness** rating that tells downstream
agents how usable this repo is for automated patch validation:

- **high**: Lint and test commands both validated successfully. An agent can
  clone, patch, lint, test, and get a clear pass/fail signal. Deps install
  cleanly in a standard container.

- **medium**: Some commands work but with caveats. Examples: lint works but
  tests require infrastructure; tests pass but lint config is missing; deps
  install but some optional tools are missing. An agent can do partial
  validation.

- **low**: Commands could not be validated. Examples: deps fail to install;
  no test or lint commands found; everything requires cluster access. An
  agent can apply patches but cannot validate them.

- **none**: Repo has no meaningful test infrastructure. No linting, no tests,
  no CI. Nothing to validate against.

### Output format

Write two files into the repository root (the agent's working directory):

- `GENERATED_TEST_CONTEXT.json`
- `GENERATED_TEST_CONTEXT.md`

**JSON file** — structured, machine-readable:

```json
{
  "repo": "<repo_name>",
  "org": "<org_name>",
  "analyzed_at": "<ISO 8601 timestamp>",
  "languages": ["<language1>", "<language2>"],
  "linting": {
    "tools": [
      {
        "name": "<linter_name>",
        "config_file": "<path_relative_to_repo_root>",
        "run_command": "<exact command>",
        "fix_command": "<exact command or null>",
        "scope": "<full project | specific directories>"
      }
    ],
    "notes": "<any additional context>"
  },
  "testing": {
    "framework": "<test framework name>",
    "test_directory": "<path to test files>",
    "run_command": "<exact command to run all tests>",
    "run_single_file": "<command template with {file} placeholder>",
    "run_single_test": "<command template with {test_name} placeholder>",
    "setup_required": ["<command1>", "<command2>"],
    "env_vars": ["<VAR=value or VAR description>"],
    "fixtures_location": "<path or null>",
    "mock_patterns": "<description or null>",
    "coverage_command": "<exact command or null>",
    "coverage_threshold": "<percentage or null>",
    "notes": "<any additional context>"
  },
  "ci": {
    "system": "<GitHub Actions | Tekton | Jenkins | etc.>",
    "config_files": ["<path1>", "<path2>"],
    "gating_checks": [
      {
        "name": "<check name>",
        "command": "<exact command>",
        "required": true
      }
    ],
    "advisory_checks": [
      {
        "name": "<check name>",
        "command": "<exact command>",
        "required": false
      }
    ],
    "notes": "<any additional context>"
  },
  "build": {
    "system": "<make | npm | go | maven | etc.>",
    "install_command": "<dependency install command>",
    "build_command": "<build command>",
    "notes": "<any additional context>"
  },
  "conventions": {
    "test_file_pattern": "<glob pattern>",
    "test_naming": "<naming convention description>",
    "import_style": "<import convention>",
    "notes": "<any additional context>"
  },
  "container_recipe": {
    "base_image": "<exact image used, e.g. python:3.11, node:20-bookworm>",
    "system_deps": ["<apt/yum packages installed, e.g. make, git, gcc>"],
    "setup_commands": [
      "<each command run to prepare the container, in order>",
      "<e.g. pip install -e '.[dev]'>",
      "<e.g. npm ci>"
    ],
    "lint_commands": [
      {"command": "<exact command>", "validated": true, "notes": "<result>"}
    ],
    "test_commands": [
      {"command": "<exact command>", "validated": true, "notes": "<result>"}
    ],
    "test_single_file": "<command template with {file} placeholder>",
    "test_single_test": "<command template with {test_name} placeholder>",
    "env_vars": ["<VAR=value pairs needed inside the container>"],
    "notes": "<any quirks, workarounds, or warnings>"
  },
  "validation": {
    "results": [
      {
        "step": "<install | build | lint | test>",
        "command": "<exact command run>",
        "exit_code": 0,
        "success": true,
        "output_snippet": "<first ~20 lines of output>",
        "notes": "<interpretation: e.g. 'lint found 3 warnings' or 'timed out'>"
      }
    ],
    "summary": "<one-line summary: e.g. 'install OK, lint OK (2 warnings), tests OK (47 passed)'>"
  },
  "gaps": [
    "<gap description 1>",
    "<gap description 2>"
  ],
  "agent_readiness": "<high | medium | low | none>",
  "confidence": "<high | medium | low>"
}
```

**Markdown file** — a runbook another agent can follow to validate patches:

The primary purpose of this file is to give a downstream agent a **complete,
copy-paste recipe** for running lint and tests in a container. The agent that
reads this file should not need to do any discovery — everything it needs to
spin up a container, install deps, and run validation is here.

Structure it with these sections:

- **Overview**: One-line description, languages, build system, agent readiness
  rating (high/medium/low/none) with one-sentence justification.

- **Container Recipe**: The most important section. A step-by-step recipe
  another agent can follow verbatim:
  1. Base image to use (exact tag)
  2. `podman run` / `docker run` command to start the container with
     the repo bind-mounted to `/app`
  3. System dependencies to install (`apt-get install ...`)
  4. Project dependency install command(s)
  5. Build command (if needed)
  6. Lint command(s) — with validated pass/fail status
  7. Test command(s) — with validated pass/fail status
  8. How to run a single test file / single test
  9. Cleanup command (`podman rm -f ...`)
  Format each step as a fenced code block so agents can extract and run them.

- **Validation Results**: For each command in the recipe, report whether it
  passed or failed during validation, the exit code, and a brief output
  snippet for failures. This tells the downstream agent what to expect.

- **CI/CD**: What checks gate merges, exact commands CI runs.

- **Conventions**: Test file naming, test patterns, import style.

- **Gaps & Caveats**: What's missing, what requires special infrastructure,
  what commands couldn't be validated and why.

Keep it under 250 lines. Every section should contain executable commands,
not descriptions. The Container Recipe section should be self-contained —
an agent reading only that section should be able to validate a patch.
