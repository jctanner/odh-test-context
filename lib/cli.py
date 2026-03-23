"""Command-line argument parsing for the test context tool."""

import argparse


def parse_args():
    """Parse command line arguments with subcommands for each phase."""
    parser = argparse.ArgumentParser(
        description="Per-repository test context extraction tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Phase to run")

    # Phase 1: Fetch repositories
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch/clone repositories using gh-org-clone",
    )
    fetch_parser.add_argument(
        "org",
        help="GitHub organization name to clone",
    )
    fetch_parser.add_argument(
        "--checkouts-dir",
        default="checkouts",
        help="Directory to clone repositories into (default: checkouts)",
    )
    fetch_parser.add_argument(
        "--branch",
        help="Specific branch to clone (skips repos without this branch)",
    )

    # Phase 2: Analyze repositories for test context
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Extract test context from cloned repositories (writes into checkouts)",
    )
    analyze_parser.add_argument(
        "--checkouts-dir",
        default="checkouts",
        help="Directory containing cloned repositories (default: checkouts)",
    )
    analyze_parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of repos to process (for testing)",
    )
    analyze_parser.add_argument(
        "--component",
        help="Only process this specific repository (e.g., 'odh-dashboard', 'kserve')",
    )
    analyze_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate test context even if GENERATED_TEST_CONTEXT.json already exists",
    )
    analyze_parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum number of agents to run concurrently (default: 5)",
    )
    analyze_parser.add_argument(
        "--model",
        choices=["sonnet", "opus", "haiku"],
        default="sonnet",
        help="Claude model to use (default: sonnet)",
    )

    # Phase 3: Collect test context files into organized output directory
    collect_parser = subparsers.add_parser(
        "collect",
        help="Collect GENERATED_TEST_CONTEXT files from checkouts into tests/ directory",
    )
    collect_parser.add_argument(
        "--checkouts-dir",
        default="checkouts",
        help="Directory containing cloned repositories (default: checkouts)",
    )
    collect_parser.add_argument(
        "--output-dir",
        default="tests",
        help="Output directory for collected test context files (default: tests)",
    )

    return parser.parse_args()
