"""Phase orchestration for test context extraction."""

import asyncio
import shutil
from pathlib import Path

from .agent_runner import run_agents_concurrently, format_duration
from .prompts import build_repo_prompt


SKILL_NAME = "repo-test-context"
GENERATED_JSON = "GENERATED_TEST_CONTEXT.json"
GENERATED_MD = "GENERATED_TEST_CONTEXT.md"


async def fetch_repositories(
    org: str,
    checkouts_dir: str = "checkouts",
    branch: str = None,
) -> None:
    """Clone all repositories from a GitHub organization using gh-org-clone.

    Args:
        org: GitHub organization name
        checkouts_dir: Base directory for cloning repositories
        branch: Optional specific branch to clone
    """
    checkouts_path = Path(checkouts_dir).absolute()
    checkouts_path.mkdir(parents=True, exist_ok=True)

    print(f"Fetching repositories from organization: {org}")
    print(f"Target directory: {checkouts_path}")
    if branch:
        print(f"Branch filter: {branch}")

    cmd = ["gh-org-clone", "-path", str(checkouts_path)]

    if branch:
        cmd.extend(["-branch", branch])

    cmd.append(org)

    print(f"Running: {' '.join(cmd)}")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        print(f"Error cloning repositories: {stderr.decode()}")
        raise RuntimeError(f"gh-org-clone failed with exit code {proc.returncode}")

    print(f"Successfully cloned repositories from {org}")
    if stdout:
        print(stdout.decode())


def _discover_repos(checkouts_dir: str) -> list[dict]:
    """Scan checkouts directory for repositories (directories containing .git).

    Returns a list of dicts with 'name', 'org', and 'path' keys.
    """
    checkouts_path = Path(checkouts_dir).absolute()
    repos = []

    if not checkouts_path.exists():
        raise FileNotFoundError(f"Checkouts directory not found: {checkouts_path}")

    # checkouts/ contains org directories, each containing repo directories
    for org_dir in sorted(checkouts_path.iterdir()):
        if not org_dir.is_dir():
            continue
        org_name = org_dir.name
        # Handle gh-org-clone naming: org or org.branch
        org_base = org_name.split(".")[0]

        for repo_dir in sorted(org_dir.iterdir()):
            if not repo_dir.is_dir():
                continue
            if (repo_dir / ".git").exists():
                repos.append({
                    "name": repo_dir.name,
                    "org": org_base,
                    "path": str(repo_dir),
                })

    return repos


async def run_fetch_phase(args) -> None:
    """Run the fetch phase: clone repositories."""
    await fetch_repositories(
        org=args.org,
        checkouts_dir=args.checkouts_dir,
        branch=getattr(args, "branch", None),
    )


async def run_analyze_phase(args) -> None:
    """Run the analyze phase: extract test context from each repo.

    Agents write GENERATED_TEST_CONTEXT.json and GENERATED_TEST_CONTEXT.md
    into each repo's checkout directory.
    """
    log_dir = Path("logs").absolute()
    log_dir.mkdir(parents=True, exist_ok=True)

    # Discover repos
    repos = _discover_repos(args.checkouts_dir)
    if not repos:
        print("No repositories found in checkouts directory.")
        print("Run 'python main.py fetch <org>' first to clone repositories.")
        return

    print(f"Discovered {len(repos)} repositories")

    # Filter by --component
    if args.component:
        repos = [r for r in repos if r["name"] == args.component]
        if not repos:
            print(f"Component '{args.component}' not found in checkouts.")
            return
        print(f"Filtered to component: {args.component}")

    # Skip repos with existing output (unless --force)
    if not args.force:
        filtered = []
        for repo in repos:
            json_path = Path(repo["path"]) / GENERATED_JSON
            if json_path.exists():
                print(f"Skipping {repo['name']} (output exists, use --force to regenerate)")
            else:
                filtered.append(repo)
        repos = filtered

    if not repos:
        print("No repositories to process (all have existing output).")
        return

    # Apply --limit
    if args.limit:
        repos = repos[:args.limit]
        print(f"Limited to {len(repos)} repositories")

    # Build jobs
    jobs = []
    for repo in repos:
        prompt = build_repo_prompt(
            skill_name=SKILL_NAME,
            repo_name=repo["name"],
            org=repo["org"],
        )
        jobs.append({
            "name": repo["name"],
            "cwd": repo["path"],
            "prompt": prompt,
        })

    print(f"\nProcessing {len(jobs)} repositories with model={args.model}, "
          f"max_concurrent={args.max_concurrent}")

    # Run agents
    results = await run_agents_concurrently(
        jobs=jobs,
        log_dir=log_dir,
        model=args.model,
        max_concurrent=args.max_concurrent,
    )

    # Print summary
    _print_results_summary(results)


async def run_collect_phase(args) -> None:
    """Run the collect phase: gather GENERATED_TEST_CONTEXT files into output dir.

    Scans checkouts for GENERATED_TEST_CONTEXT.json and .md files, copies them
    into the output directory as {repo_name}.json and {repo_name}.md, and
    generates an index README.md.
    """
    output_dir = Path(args.output_dir).absolute()
    output_dir.mkdir(parents=True, exist_ok=True)

    repos = _discover_repos(args.checkouts_dir)
    if not repos:
        print("No repositories found in checkouts directory.")
        return

    collected = []
    skipped = []

    for repo in repos:
        repo_path = Path(repo["path"])
        json_src = repo_path / GENERATED_JSON
        md_src = repo_path / GENERATED_MD

        if not json_src.exists():
            skipped.append(repo["name"])
            continue

        # Copy JSON
        json_dst = output_dir / f"{repo['name']}.json"
        shutil.copy2(json_src, json_dst)

        # Copy markdown if it exists
        if md_src.exists():
            md_dst = output_dir / f"{repo['name']}.md"
            shutil.copy2(md_src, md_dst)

        collected.append(repo["name"])
        print(f"  Collected: {repo['name']}")

    # Generate index README
    if collected:
        _write_index_readme(output_dir, collected)

    print(f"\nCollected {len(collected)} repositories into {output_dir}")
    if skipped:
        print(f"Skipped {len(skipped)} repositories (no {GENERATED_JSON} found)")


def _write_index_readme(output_dir: Path, repos: list[str]) -> None:
    """Write an index README.md listing all collected test context files."""
    lines = [
        "# Test Context Index",
        "",
        "Per-repository test context for AI-assisted patch validation.",
        "",
        "| Repository | JSON | Markdown |",
        "|------------|------|----------|",
    ]

    for name in sorted(repos):
        json_link = f"[{name}.json]({name}.json)"
        md_path = output_dir / f"{name}.md"
        md_link = f"[{name}.md]({name}.md)" if md_path.exists() else "—"
        lines.append(f"| {name} | {json_link} | {md_link} |")

    lines.append("")
    readme_path = output_dir / "README.md"
    readme_path.write_text("\n".join(lines))
    print(f"  Wrote index: {readme_path}")


def _print_results_summary(results: list) -> None:
    """Print a summary of agent execution results."""
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")

    succeeded = 0
    failed = 0
    for result in results:
        if isinstance(result, Exception):
            failed += 1
            print(f"  ERROR: {result}")
        elif result.get("success"):
            succeeded += 1
            duration = format_duration(result.get("duration_seconds", 0))
            print(f"  OK: {result['name']} ({duration})")
        else:
            failed += 1
            print(f"  FAIL: {result['name']}: {result.get('error', 'unknown error')}")

    print(f"\nTotal: {succeeded} succeeded, {failed} failed, {len(results)} total")


async def main(args) -> None:
    """Dispatch to the appropriate phase based on the subcommand."""
    if args.command == "fetch":
        await run_fetch_phase(args)
    elif args.command == "analyze":
        await run_analyze_phase(args)
    elif args.command == "collect":
        await run_collect_phase(args)
    else:
        print("No command specified. Use 'fetch', 'analyze', or 'collect'.")
        print("Run with --help for usage information.")
