"""Skill-based prompt loader for test context extraction.

Loads SKILL.md files from .claude/skills/{skill_name}/SKILL.md and builds
per-repo prompts that inject repo metadata before the skill instructions.
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = BASE_DIR / ".claude" / "skills"


def load_skill_instructions(skill_name: str) -> str:
    """Read a SKILL.md file and return the content under ``## Instructions``.

    Raises FileNotFoundError if the skill directory or SKILL.md is missing.
    Raises ValueError if the ``## Instructions`` heading is not found.
    """
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_path}")

    text = skill_path.read_text()

    # Extract everything after the first ``## Instructions`` heading.
    match = re.search(r"^## Instructions\s*\n", text, re.MULTILINE)
    if not match:
        raise ValueError(
            f"Skill {skill_name}: SKILL.md missing '## Instructions' heading"
        )

    return text[match.end():]


def build_repo_prompt(
    skill_name: str,
    repo_name: str,
    org: str,
) -> str:
    """Build a full agent prompt from a skill file and repo metadata.

    The agent writes output files (GENERATED_TEST_CONTEXT.json and
    GENERATED_TEST_CONTEXT.md) into the repo's working directory.

    Parameters
    ----------
    skill_name:
        Name of the skill directory under ``.claude/skills/``.
    repo_name:
        Repository name (e.g. ``odh-dashboard``).
    org:
        GitHub organization name (e.g. ``opendatahub-io``).
    """
    instructions = load_skill_instructions(skill_name)

    header = (
        f"## Repository\n\n"
        f"Name: {repo_name}\n"
        f"Organization: {org}\n"
    )

    return f"{header}\n## Instructions\n\n{instructions}"
