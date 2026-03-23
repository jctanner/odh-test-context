> **Agents**: If you are an AI agent using the data in this repo (rather than running the pipeline), read [AGENT_USAGE.md](AGENT_USAGE.md) for how to navigate the `tests/` directory.

# ODH Test Context

Automated pipeline that clones opendatahub-io repositories, analyzes each repo's test infrastructure using Claude agents, validates discovered commands in containers, and produces per-repo test context files (structured JSON + markdown runbooks). Designed to be consumed by AI agents that need to validate patches.

## Why this exists

The bug-bash pipeline produces patches against opendatahub-io repos but cannot validate them because agents don't know how to run each repo's linter or test suite. This project fills that gap by extracting per-repo test context — lint commands, test commands, CI config, build setup — and validating them in containers so downstream agents get proven recipes, not guesses.

## How it works

The pipeline has 3 phases, each runnable independently via `main.py`.

### Phase 1: Fetch (`fetch`)

Uses `gh-org-clone` to clone all repositories from a GitHub org:

```
checkouts/opendatahub-io/
  odh-dashboard/
  kserve/
  data-science-pipelines-operator/
  notebooks/
  ...  (~162 repos)
```

### Phase 2: Analyze (`analyze`)

For each repo that lacks a `GENERATED_TEST_CONTEXT.json`, spawns a Claude agent (via `claude-agent-sdk`) that:

1. **Discovers** the project type, linters, test frameworks, CI config, and build system by reading config files, Makefiles, CI workflows, and package manifests
2. **Validates** discovered commands in an isolated container — spins up a container with the repo bind-mounted, installs dependencies, runs lint and test commands, records what works and what doesn't
3. **Writes** two files into the repo checkout:
   - `GENERATED_TEST_CONTEXT.json` — structured, machine-readable
   - `GENERATED_TEST_CONTEXT.md` — a runbook another agent can follow verbatim

Agents run concurrently (default 5 at a time). The phase is idempotent — re-running skips repos that already have output. Use `--force` to regenerate.

Containers are named `test-context-{repo_name}` and are cleaned up after each analysis.

### Phase 3: Collect (`collect`)

Copies `GENERATED_TEST_CONTEXT.json` and `.md` files from checkouts into an organized `tests/` directory with an index README:

```
tests/
  README.md              # Index table linking to all files
  odh-dashboard.json
  odh-dashboard.md
  kserve.json
  kserve.md
  ...
```

## Project structure

```
main.py                              # CLI entry point
lib/
  agent_runner.py                    # Claude SDK agent launcher + concurrency
  cli.py                             # Argument parsing (fetch, analyze, collect)
  phases.py                          # Phase orchestration
  prompts.py                         # Skill loader + prompt builder
.claude/skills/
  repo-test-context/SKILL.md         # Agent skill: test context extraction
tests/                               # Output: collected test context files
checkouts/                           # Cloned repositories (gitignored)
logs/                                # Agent execution logs (gitignored)
```

## Usage

### Full workflow

```bash
# Clone all opendatahub-io repos
python main.py fetch opendatahub-io

# Analyze all repos (spawns agents, validates in containers)
python main.py analyze

# Collect results into tests/ directory
python main.py collect
```

### Individual phases

```bash
# Analyze a single component
python main.py analyze --component odh-dashboard

# Analyze with a different model
python main.py analyze --model opus --max-concurrent 3

# Force re-analyze a component that already has output
python main.py analyze --component kserve --force

# Analyze only the first 5 repos (for testing)
python main.py analyze --limit 5

# Collect into a different directory
python main.py collect --output-dir my-output
```

### Useful flags

| Flag | Phase | Description |
|------|-------|-------------|
| `--model` | analyze | Claude model: `sonnet` (default), `opus`, `haiku` |
| `--max-concurrent` | analyze | Parallel agent count (default: 5) |
| `--component` | analyze | Process a single repo by name |
| `--force` | analyze | Regenerate even if output exists |
| `--limit` | analyze | Cap number of repos to process |
| `--output-dir` | collect | Output directory (default: `tests`) |
| `--branch` | fetch | Clone a specific branch |

## Output format

Each repo produces two files. See [AGENT_USAGE.md](AGENT_USAGE.md) for full schema documentation.

### JSON (`{repo}.json`)

Structured data with sections for linting, testing, CI, build, conventions, container recipe, validation results, gaps, and agent readiness rating.

The `container_recipe` section is the key output — it contains the exact base image, system dependencies, setup commands, and validated lint/test commands that a downstream agent needs to reproduce the test environment.

### Markdown (`{repo}.md`)

A runbook formatted as step-by-step instructions. The Container Recipe section is self-contained: an agent reading only that section can spin up a container, install deps, lint, test, and clean up without any discovery work.

### Agent readiness rating

Each repo gets an `agent_readiness` rating:

| Rating | Meaning |
|--------|---------|
| **high** | Lint and test commands both validated. Agent can clone, patch, lint, test, and get a clear pass/fail signal. |
| **medium** | Some commands work with caveats (e.g., lint works but tests need infrastructure). Partial validation possible. |
| **low** | Commands couldn't be validated (e.g., deps fail, cluster access required). Agent can patch but not validate. |
| **none** | No test infrastructure found. Nothing to validate against. |

## Requirements

- Python 3.13+
- `gh-org-clone` CLI tool
- `claude-agent-sdk` (installed via `uv sync`)
- `python-dotenv`
- `podman` or `docker` (for container-based validation)
- `ANTHROPIC_API_KEY` or Vertex AI credentials (see `.env.example`)

## Setup

```bash
uv sync
cp .env.example .env
# Edit .env with API credentials
```
