#!/usr/bin/env python3
"""
Bump plugin versions in marketplace.json.

Usage:
    bump-plugin-version.py --bump-type minor|patch --plugins name1 name2 ...
    bump-plugin-version.py --bump-type minor|patch --from-diff

When using --from-diff, determines affected plugins from git diff against origin/main.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


MARKETPLACE_PATH = Path(__file__).parent.parent / ".claude-plugin" / "marketplace.json"
PLUGINS_ROOT = Path(__file__).parent.parent / "plugins"


def plugin_manifest_path(plugin_name: str) -> Path:
    return PLUGINS_ROOT / plugin_name / ".claude-plugin" / "plugin.json"


def bump_version(version: str, bump_type: str) -> str:
    """Increment a semantic version string."""
    parts = version.split(".")
    if len(parts) != 3:
        print(f"ERROR: Invalid version format: {version}", file=sys.stderr)
        sys.exit(1)

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        print(f"ERROR: Unknown bump type: {bump_type}", file=sys.stderr)
        sys.exit(1)


def get_plugins_from_diff() -> list[str]:
    """Determine which plugins were modified compared to origin/main."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"ERROR: git diff failed: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    plugins = set()
    for line in result.stdout.strip().split("\n"):
        if line.startswith("plugins/"):
            parts = line.split("/")
            if len(parts) >= 2:
                plugins.add(parts[1])

    return sorted(plugins)


def main():
    parser = argparse.ArgumentParser(description="Bump plugin versions in marketplace.json")
    parser.add_argument(
        "--bump-type",
        required=True,
        choices=["major", "minor", "patch"],
        help="Type of version bump",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--plugins",
        nargs="+",
        help="Plugin names to bump",
    )
    group.add_argument(
        "--from-diff",
        action="store_true",
        help="Determine plugins from git diff against origin/main",
    )

    args = parser.parse_args()

    plugin_names = args.plugins if args.plugins else get_plugins_from_diff()

    if not plugin_names:
        print("No plugins to bump.")
        sys.exit(0)

    if not MARKETPLACE_PATH.exists():
        print(f"ERROR: {MARKETPLACE_PATH} not found", file=sys.stderr)
        sys.exit(1)

    marketplace = json.loads(MARKETPLACE_PATH.read_text())

    known_plugins = {p["name"] for p in marketplace.get("plugins", [])}
    bumped_any = False
    for name in plugin_names:
        if name not in known_plugins:
            print(f"Skipping '{name}': not present in marketplace.json (new or removed plugin)")

    bumps: dict[str, str] = {}  # plugin name -> new version

    for plugin in marketplace["plugins"]:
        if plugin["name"] in plugin_names:
            old_version = plugin["version"]
            new_version = bump_version(old_version, args.bump_type)
            plugin["version"] = new_version
            bumps[plugin["name"]] = new_version
            print(f"{plugin['name']}: {old_version} -> {new_version}")
            bumped_any = True

    if not bumped_any:
        print("No plugins bumped (all skipped).")
        return

    MARKETPLACE_PATH.write_text(json.dumps(marketplace, indent=2) + "\n")
    print(f"Updated {MARKETPLACE_PATH}")

    # Mirror the bump into each plugin's own plugin.json so the two manifests
    # stay in sync. claude.ai's GitHub-sync uses plugin.json as the source of
    # truth in strict mode; marketplace.json is the catalog. Skip plugins
    # without a plugin.json (e.g., new plugins that haven't had one created
    # yet) rather than failing the whole bump.
    for plugin_name, new_version in bumps.items():
        manifest_path = plugin_manifest_path(plugin_name)
        if not manifest_path.exists():
            print(f"  note: no plugin.json for '{plugin_name}'; skipping mirror")
            continue
        manifest = json.loads(manifest_path.read_text())
        manifest["version"] = new_version
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"  mirrored to {manifest_path.relative_to(MARKETPLACE_PATH.parent.parent)}")


if __name__ == "__main__":
    main()
