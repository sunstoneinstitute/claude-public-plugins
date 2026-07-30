#!/usr/bin/env python3
"""
CI check: PRs that modify files under plugins/ must carry a bump-* label.

The auto-merge workflow bumps versions at merge time based on the label
(bump-patch, bump-minor, bump-major). This script enforces that the label
is present whenever plugin content changed, so the workflow has something
to act on.

Files outside plugins/ (README, workflows, marketplace.json description or
keyword edits, etc.) do not require a bump label.

Reads context from environment:
    PR_NUMBER     - pull request number
    GH_REPOSITORY - owner/repo (defaults to $GITHUB_REPOSITORY)
    GH_TOKEN      - GitHub token for gh CLI

Exits non-zero if a bump label is required but missing.
"""

import json
import os
import subprocess
import sys


VALID_BUMP_LABELS = {"bump-patch", "bump-minor", "bump-major"}


def gh(args: list[str]) -> str:
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main() -> int:
    pr_number = os.environ.get("PR_NUMBER")
    repo = os.environ.get("GH_REPOSITORY") or os.environ.get("GITHUB_REPOSITORY")

    if not pr_number or not repo:
        print("ERROR: PR_NUMBER and GH_REPOSITORY (or GITHUB_REPOSITORY) must be set", file=sys.stderr)
        return 2

    files_json = gh([
        "pr", "view", pr_number,
        "--repo", repo,
        "--json", "files",
    ])
    files = [f["path"] for f in json.loads(files_json).get("files", [])]

    plugin_files = [f for f in files if f.startswith("plugins/")]

    if not plugin_files:
        print("No files under plugins/ changed. Bump label not required.")
        return 0

    labels_json = gh([
        "pr", "view", pr_number,
        "--repo", repo,
        "--json", "labels",
    ])
    labels = {lab["name"] for lab in json.loads(labels_json).get("labels", [])}

    bump_labels = labels & VALID_BUMP_LABELS

    if not bump_labels:
        print(
            "ERROR: This PR modifies plugin files but has no bump-* label.\n"
            "\n"
            "Plugin files changed:\n"
            + "\n".join(f"  - {f}" for f in plugin_files)
            + "\n\n"
            "Add exactly one of: bump-patch, bump-minor, bump-major\n"
            "The auto-merge workflow will apply the version bump at merge time."
            ,
            file=sys.stderr,
        )
        return 1

    if len(bump_labels) > 1:
        print(
            f"ERROR: PR has multiple bump labels: {sorted(bump_labels)}. "
            "Pick exactly one.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: bump label '{next(iter(bump_labels))}' present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
