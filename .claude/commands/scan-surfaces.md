---
description: Scan skills to determine which Claude surfaces (code, cowork, desktop, web) can run them; writes the surfaces frontmatter and recommends widening refactorings
argument-hint: [plugin-or-skill paths...] [--refactor]
model: sonnet
---

# Scan Skill Surfaces

Determine which Claude surfaces can run each skill, record the result in the skill's `surfaces:` frontmatter field, and recommend refactorings that would make the skill usable on more surfaces.

Arguments: $ARGUMENTS

## Scope from arguments

- **No path arguments**: scan every skill in every plugin (`plugins/*/skills/*/`).
- **Plugin path** (e.g. `plugins/gws`): scan all skills in that plugin.
- **Skill path** (e.g. `plugins/gws/skills/gws-setup`): scan only that skill.
- **`--refactor`**: also apply the recommended refactorings (see "Refactor mode"). Without this flag, the ONLY file modification permitted is adding or updating the `surfaces:` field in SKILL.md frontmatter. Do not change any other line of any skill file in default mode.

## The four surfaces

Ordered from most to least capable host. Use exactly these identifiers, in this canonical order, when writing the frontmatter.

| Surface | What it is | What a skill can use there |
|---|---|---|
| `code` | Claude Code running **locally**: CLI, IDE extensions, the desktop app's Code tab with a Local environment | Everything: host terminal (Bash), full host filesystem, git, local binaries and authenticated CLIs (`gam`, `kubectl`, `docker`, `gh`, …), software distributed via MDM, internal/private networks, bundled scripts run natively, slash commands, hooks, local and remote MCP servers. |
| `cowork` | Claude Cowork: the agentic mode of the desktop app | Read/write files in the session's working folder; run bundled scripts and code in an **isolated sandbox** — NOT the host shell. Host-installed binaries, host credentials/keychain, and the wider host filesystem are unavailable. Remote connectors (MCP) available. |
| `desktop` | Claude Desktop chat | No host terminal. Bundled scripts run in Anthropic's **server-side code sandbox** (bash + python, with the skill's own files present). File uploads/downloads, artifacts, web search, local and remote MCP connectors, browser control via the Claude in Chrome extension. |
| `web` | claude.ai in a browser | Same execution model as desktop chat (server-side sandbox for bundled scripts, uploads, artifacts, web search) but only **remote** connectors — no local MCP servers, no host access of any kind. |

**Cloud Claude Code sessions are not the `code` tier.** Sessions on claude.ai/code, the desktop app's Remote environment, and Dispatch run in Anthropic's cloud sandbox: a repo checkout with installable open-source packages, but no host binaries (nothing MDM-distributed), no local credentials, and no internal network. Capability-wise, treat them like `cowork`. The `code` label means Claude Code **with host access** — a skill that needs authenticated local CLIs or live infrastructure works in local sessions only, even for `code` users.

Capabilities evolve; if a skill's viability hinges on a capability you are unsure about (especially for `cowork`), verify against current Anthropic documentation before deciding, and say so in the report.

## How to decide a skill's surfaces

1. **Read the skill fully.** SKILL.md, plus enough of `references/` and `scripts/` to know what the skill actually instructs an agent to do — not just what its description says.
2. **List the capabilities the skill needs** to deliver the core value its description declares. Distinguish core capabilities from peripheral ones (used by rare or optional features).
3. **Classify each capability into a tier:**
   - **T0 — pure instruction.** Knowledge, methodology, authoring guidance, judgment. Needs: `code, cowork, desktop, web`.
   - **T1 — self-contained computation.** Bundled scripts or ad-hoc code that only need a generic bash/python environment plus the skill's own files or user-provided files. Needs: `code, cowork, desktop, web` — provided dependencies are vendored or installable in a sandbox and no private-network access is required.
   - **T2 — the user's workspace.** Reading/writing the user's project files, running git on their repo, operating on a local folder. Needs: `code, cowork`.
   - **T3 — the host and live infrastructure.** Host terminal, locally installed binaries, authenticated CLIs, credentials on the machine, internal networks, live clusters/servers. Needs: `code` only.
   - **MCP-provided capability.** If a **remote** connector delivers it: `code, cowork, desktop, web`. If it requires a **local** MCP server: `code, desktop`.
4. **The skill's surfaces = the intersection of its CORE capabilities' tiers.** Peripheral capabilities do not shrink the list — see the gating rule below.
5. **Rare-feature gating rule.** If only a peripheral feature needs a more restrictive tier and the skill is still genuinely valuable without it (e.g. valuable to non-code users), keep the broader surface list — but the skill text must gate that feature explicitly ("Only on Claude Code: …"). If it doesn't yet, that gating edit is a recommendation (default mode) or an applied change (refactor mode).
6. **Equivalent-tools rule.** When different surfaces reach the same goal with different tools (e.g. controlling Chrome: Claude Code drives it via a DevTools MCP or AppleScript; Desktop uses the Claude in Chrome extension), the capability counts as available on each such surface **only if** the skill either (a) states the goal in tool-agnostic language and lets the agent pick its surface's tool, or (b) ships per-surface instructions, e.g. `references/<topic>-code.md` and `references/<topic>-desktop.md`. If instead the skill hard-codes one surface's tool, count the capability at that surface only — and recommend refactoring (a) or (b).

Be honest, not optimistic: "an agent on that surface could theoretically improvise around the instructions" does not count. The skill as written must work there.

## Writing the frontmatter

For each scanned skill, add or update `surfaces:` in SKILL.md's YAML frontmatter, directly after the `description:` line, using flow style and canonical order:

```yaml
---
name: example-skill
description: This skill should be used when...
surfaces: [code, cowork, desktop, web]
---
```

Change nothing else in the file (default mode). Preserve all other frontmatter fields and body content byte-for-byte.

## Report

After scanning, print one section per skill:

- **Surfaces written**: the new value (and the old one, if it changed).
- **Core capabilities**: each with its tier and the surfaces it permits.
- **Blocked surfaces**: for each surface excluded, the specific capability that blocks it.
- **Recommendations**: concrete refactorings that would unlock more surfaces, each with the surfaces it unlocks and rough effort. Typical shapes:
  - Gate a peripheral code-only feature behind "Only on Claude Code: …" wording.
  - Replace hard-coded tool instructions with tool-agnostic goal language.
  - Split per-surface tool specifics into per-surface reference files.
  - Move a host-CLI step behind a remote connector when an equivalent exists.

End with a summary table (`plugin | skill | surfaces`). Plugin description tags are derived automatically: a `PostToolUse` hook in `.claude/settings.json` runs `scripts/sync-surface-tags.py` after every SKILL.md edit, rewriting the `[...]` prefix in plugin.json and marketplace.json once every skill in a plugin is labeled. After the scan, run `python3 scripts/sync-surface-tags.py` once explicitly, include any tag changes it reports in the summary, and mirror changed tags into README.md badges (the script does not touch README).

## Refactor mode (`--refactor`)

Apply the recommendations, then re-derive and write the widened `surfaces:` value. Constraints:

- Only make changes that serve a stated recommendation; no drive-by edits.
- Follow the repo writing style (plain language, imperative, precise) and keep SKILL.md within the word budget — push per-surface detail into `references/`.
- Use fully qualified `<plugin>:<name>` forms for any runtime names you touch.
- Never edit `version` fields.
- After refactoring, verify the skill still reads coherently for a `code`-surface user — widening must not degrade the primary audience.

## Reminders

- Changes under `plugins/` need a bump label on the PR (`bump-patch` for surfaces-only annotation; `bump-minor` if refactoring adds content).
- The `surfaces:` field feeds `scripts/build-skill-zips.py`: skills listing `web` get zipped for the Skills API upload, overriding the plugin-level tag. Wrong labels ship or withhold skills on claude.ai — when in doubt, leave a surface out and note it as a candidate.
