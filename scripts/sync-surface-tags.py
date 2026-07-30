#!/usr/bin/env python3
"""Derive plugin-level surface tags from per-skill `surfaces:` frontmatter.

Every plugin description starts with a surface tag like "[code]" or
"[code desktop web]" (see CLAUDE.md, "Surface Availability Tags"). Once every
skill in a plugin declares its own `surfaces:` list in SKILL.md frontmatter,
that tag becomes derived data. This script computes it and rewrites the
description prefix in both `plugins/<name>/.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json` so the two never drift from the skills.

Derivation rule:
  - The tag is the UNION of all the plugin's skills' `surfaces:` lists,
    ordered code, cowork, desktop, web — the most permissive reading. One
    web-capable skill is enough to put "web" in the tag: the tag is a
    discovery signal, while the per-skill `surfaces:` fields carry the
    exact per-skill truth.
  - Commands and hooks do NOT affect the tag: off Claude Code they are
    simply not registered — inert, not misleading.
  - Plugins where any skill lacks `surfaces:` are left untouched (their tag
    stays hand-maintained until every skill is labeled).
  - Plugins whose description contains DEPRECATED are left untouched.

Usage:
    python3 scripts/sync-surface-tags.py           # rewrite stale tags
    python3 scripts/sync-surface-tags.py --check   # exit 1 if any tag is stale
    python3 scripts/sync-surface-tags.py --hook    # Claude Code PostToolUse
        mode: reads the hook payload from stdin and exits silently unless the
        edited file is a SKILL.md under plugins/

Descriptions are metadata, not plugin content: rewriting them needs no
version-bump label (see CLAUDE.md, "Updates and Versioning").
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"

# Canonical surface order — the same vocabulary as SKILL.md `surfaces:` fields.
TAG_ORDER = ["code", "cowork", "desktop", "web"]

SURFACE_TAG_RE = re.compile(r"^\[([^\]]*)\]\s*")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)


def skill_surfaces(skill_md: Path):
    """Return the `surfaces:` list from SKILL.md frontmatter, or None if absent."""
    match = FRONTMATTER_RE.match(skill_md.read_text())
    if not match:
        return None
    block = match.group(1)
    flow = re.search(r"^surfaces:[ \t]*\[([^\]]*)\]", block, re.MULTILINE)
    if flow:
        return [s.strip() for s in flow.group(1).split(",") if s.strip()]
    block_style = re.search(
        r"^surfaces:[ \t]*\n((?:[ \t]+-[ \t]+\S+[ \t]*\n?)+)", block, re.MULTILINE
    )
    if block_style:
        return re.findall(r"-[ \t]+(\S+)", block_style.group(1))
    return None


def derive_tag(plugin_dir: Path):
    """Return the derived tag string for a plugin, or None if not derivable."""
    skill_mds = sorted(plugin_dir.glob("skills/*/SKILL.md"))
    if not skill_mds:
        return None

    surface_sets = []
    for skill_md in skill_mds:
        surfaces = skill_surfaces(skill_md)
        if surfaces is None:
            return None  # not fully labeled yet — leave the hand-set tag alone
        surface_sets.append(set(surfaces))

    combined = set.union(*surface_sets)
    ordered = [t for t in TAG_ORDER if t in combined]
    return " ".join(ordered) if ordered else None


def retag(description: str, tag: str) -> str:
    stripped = SURFACE_TAG_RE.sub("", description)
    return f"[{tag}] {stripped}"


def current_tag(description: str):
    match = SURFACE_TAG_RE.match(description)
    return match.group(1) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="report stale tags and exit 1 without writing")
    parser.add_argument("--hook", action="store_true",
                        help="Claude Code PostToolUse mode: filter on the edited "
                             "file from the stdin payload, then sync")
    args = parser.parse_args()

    if args.hook:
        try:
            payload = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            return 0
        file_path = str(payload.get("tool_input", {}).get("file_path", ""))
        if not re.search(r"plugins/[^/]+/skills/[^/]+/SKILL\.md$", file_path):
            return 0

    marketplace = json.loads(MARKETPLACE_PATH.read_text())
    marketplace_by_name = {p["name"]: p for p in marketplace.get("plugins", [])}

    stale = []
    for manifest_path in sorted(REPO_ROOT.glob("plugins/*/.claude-plugin/plugin.json")):
        plugin_dir = manifest_path.parent.parent
        plugin = json.loads(manifest_path.read_text())
        description = plugin.get("description", "")

        if "DEPRECATED" in description:
            continue
        tag = derive_tag(plugin_dir)
        if tag is None:
            continue

        for target, path in (
            (plugin, manifest_path),
            (marketplace_by_name.get(plugin["name"]), MARKETPLACE_PATH),
        ):
            if target is None or current_tag(target.get("description", "")) == tag:
                continue
            stale.append((plugin["name"], path, current_tag(target.get("description", "")), tag))
            if not args.check:
                target["description"] = retag(target["description"], tag)
                if path is not MARKETPLACE_PATH:
                    path.write_text(json.dumps(plugin, indent=2) + "\n")

    if not args.check and any(path is MARKETPLACE_PATH for _, path, _, _ in stale):
        MARKETPLACE_PATH.write_text(json.dumps(marketplace, indent=2) + "\n")

    for name, path, old, new in stale:
        verb = "stale" if args.check else "updated"
        print(f"{verb}: {name} in {path.relative_to(REPO_ROOT)}: [{old}] -> [{new}]")

    if args.check and stale:
        print("\nSurface tags are out of sync with skill `surfaces:` frontmatter. "
              "Run: python3 scripts/sync-surface-tags.py")
        return 1
    if not stale:
        print("Surface tags in sync.") if not args.hook else None
    elif not args.check:
        print("Remember to mirror tag changes into README.md badges.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
