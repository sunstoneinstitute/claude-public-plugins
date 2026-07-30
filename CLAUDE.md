# Claude Plugin Marketplace Maintenance Guide

This repository is the **public** Claude Code plugin marketplace for Sunstone Institute
(`sunstone-public`). Follow these instructions when maintaining it.

**This repo is world-readable.** Nothing that names internal hosts, clusters, tenants, customers,
credentials, or unreleased work belongs here. Plugins that need any of that live in the private
marketplace, `sunstoneinstitute/claude-plugins` (`sunstone-plugins`).

## Repository Structure

```
claude-public-plugins/
├── .claude-plugin/
│   └── marketplace.json     # Marketplace catalog manifest
├── plugins/
│   └── [plugin-name]/
│       ├── .claude-plugin/
│       │   └── plugin.json   # Per-plugin manifest (REQUIRED — see note below)
│       ├── skills/
│       │   └── [skill-name]/
│       │       ├── SKILL.md       # Skill definition (required)
│       │       ├── references/    # Supporting documentation (optional)
│       │       ├── examples/      # Working examples (optional)
│       │       └── scripts/       # Utility scripts (optional)
│       ├── commands/              # Slash commands (optional)
│       ├── agents/                # Subagents (optional)
│       └── hooks/                 # Event hooks (optional)
└── CLAUDE.md               # This file
```

**CRITICAL**: Skills MUST be placed in `skills/[skill-name]/SKILL.md`, NOT at the plugin root. Claude Code auto-discovers skills by scanning the `skills/` subdirectory for folders containing `SKILL.md` files.

**CRITICAL**: Every plugin MUST have a `.claude-plugin/plugin.json` manifest. It is **required** for claude.ai org-level GitHub plugin sync (strict mode is the default and rejects plugins without it). A plugin missing `plugin.json` will fail to sync. See step 5 under "Adding a New Plugin".

## Adding a New Plugin

When adding a new plugin to this marketplace:

1. **Create plugin directory structure:**
   ```bash
   mkdir -p plugins/[plugin-name]/skills/[skill-name]/{references,examples,scripts}
   ```

   Note: The skill name is often the same as the plugin name, but a plugin can contain multiple skills.

2. **Create the skill SKILL.md file:**

   Create `plugins/[plugin-name]/skills/[skill-name]/SKILL.md` with YAML frontmatter:

   ```markdown
   ---
   name: skill-name
   description: This skill should be used when the user asks to "do X", "configure Y", or mentions specific-topic. Describe what triggers this skill.
   ---

   # Skill Title

   Main skill content here...
   ```

   **Frontmatter requirements:**
   - `name` (required): Skill identifier
   - `description` (required): Must use third-person ("This skill should be used when...") and include specific trigger phrases

3. **Add supporting files (optional):**
   - `references/` - Detailed documentation loaded on-demand
   - `examples/` - Working code examples users can copy
   - `scripts/` - Utility scripts for common operations

4. **Add slash commands (optional):**
   Create `plugins/[plugin-name]/commands/[command-name].md` for user-invocable commands.

5. **Create `plugins/[plugin-name]/.claude-plugin/plugin.json`:**

   This is the per-plugin manifest. It is **required** for claude.ai org-level GitHub sync (strict mode is the default). Mirror the same fields as the marketplace.json entry:

   ```json
   {
     "name": "plugin-name",
     "description": "Brief description of what the plugin does",
     "version": "1.0.0",
     "author": {
       "name": "Author Name",
       "email": "email@sunstone.institute"
     },
     "keywords": ["tag1", "tag2", "tag3"]
   }
   ```

   Note: `name`, `description`, `version`, `author`, and `keywords` are duplicated between `plugin.json` and the plugin's entry in `marketplace.json`. The `scripts/bump-plugin-version.py` script keeps `version` in sync across both. Other fields must be edited in both places.

6. **Add plugin entry to .claude-plugin/marketplace.json:**
   ```json
   {
     "name": "plugin-name",
     "source": "./plugins/plugin-name",
     "description": "Brief description of what the plugin does",
     "version": "1.0.0",
     "author": {
       "name": "Author Name",
       "email": "email@sunstone.institute"
     },
     "keywords": ["tag1", "tag2", "tag3"]
   }
   ```

   **The `description` (in both files) MUST begin with a surface tag** — e.g. `[code]` or `[code desktop web]`. See "Surface Availability Tags" below for the rule.

7. **Update `README.md`:**

   `README.md` has a human-facing "Available Plugins" section that mirrors `marketplace.json`. It is **not** generated — keep it in sync by hand. Whenever you add, remove, move, or re-tag a plugin (or a skill/command within one), update the corresponding entry in `README.md`'s plugin list, including the surface-tag badge in the heading. `marketplace.json` is the source of truth; `README.md` is the readable view of it. Install examples in `README.md` should reference real plugin names.

## Marketplace.json Requirements

### Required Fields

- `name` - Marketplace identifier (kebab-case, no spaces)
- `owner.name` - Maintainer name (required)
- `owner.email` - Maintainer email (optional)
- `plugins` - Array of plugin entries

Optional marketplace fields:
- `metadata.description` - Brief marketplace description
- `metadata.version` - Marketplace version
- `metadata.pluginRoot` - Base directory prepended to relative plugin paths

### Plugin Entry Requirements

Each plugin must have:
- `name` - Plugin identifier (kebab-case, no spaces)
- `source` - Plugin source (relative path or source object)

In addition, **every plugin MUST ship a `plugins/<name>/.claude-plugin/plugin.json` manifest** (see step 5 under "Adding a New Plugin"). This is required — not optional — for claude.ai org-level GitHub plugin sync, which runs in strict mode by default and rejects any plugin lacking it.

Optional but recommended:
- `description` - Brief plugin description
- `version` - Semantic version number
- `author.name` - Plugin author name
- `author.email` - Author email
- `keywords` - Array of keywords for discovery
- `homepage` - Plugin homepage or documentation URL
- `repository` - Source code repository URL
- `license` - SPDX license identifier

## Surface Availability Tags

Plugins are distributed to every Claude **surface**. Those surfaces do **not** all have the same capabilities, and Claude Code has **no native field** that gates a plugin to a surface — an unrunnable plugin isn't hidden on web, it's just exposed and inert. To make intended availability explicit, **every plugin description MUST begin with a surface tag in square brackets**, in both `plugin.json` and the `marketplace.json` entry (keep the two in sync).

### The surfaces

One vocabulary is used everywhere — plugin description tags and per-skill `surfaces:` frontmatter alike. From most to least capable host, in this canonical order:

- **`code`** — Claude Code with host access: the CLI, IDE extensions, and the desktop app's Code tab in a Local environment. Host terminal, full filesystem, local binaries and authenticated CLIs, internal networks, slash commands, hooks. Cloud Claude Code sessions (claude.ai/code, the desktop app's Remote environment, Dispatch) are **not** this tier — they are sandboxed and capability-equivalent to `cowork`.
- **`cowork`** — Claude Cowork, the desktop app's agentic mode: read/write files in the session's working folder, run code in an isolated sandbox, remote connectors — but no host binaries, host credentials, or internal network.
- **`desktop`** — Claude Desktop chat: no host terminal; bundled skill scripts run in Anthropic's server-side sandbox; uploads, artifacts, local and remote MCP connectors.
- **`web`** — claude.ai in a browser: like desktop chat but remote connectors only.

Common tags: `[code]` (needs a terminal / local tools / live infra) and `[code desktop web]` (pure instruction). Other combinations, including ones with `cowork`, appear as they are derived from per-skill labels.

### The rule, in one line

The tag lists every surface where **at least one** of the plugin's skills delivers value. All skills need a terminal / local tools / live infra → `[code]`; pure instruction throughout → all surfaces.

### Mixed plugins

Tag by the **most permissive skill**: the tag is the **union** of what the plugin's skills support — if even one skill delivers value on web, the tag contains `web`. The tag is a discovery signal ("this plugin has something for you on your surface"), not a guarantee that every skill works there; the per-skill `surfaces:` fields (below) carry the exact per-skill truth. Commands and hooks don't affect the tag — surfaces that can't run them simply never register them, so they are inert rather than misleading.

When adding a plugin before its skills are labeled, ask per skill: "Could an agent on claude.ai web, with no shell and no local tools, get this skill's core value from the instructions alone?" Any yes → include `web` (and `desktop`, `cowork`); all no → `[code]`.

### Derived tags

Once **every** skill in a plugin has a `surfaces:` field, the plugin tag stops being hand-maintained: `scripts/sync-surface-tags.py` derives it as the union of the skills' surfaces and rewrites the description prefix in both `plugin.json` and `marketplace.json`. A `PostToolUse` hook in `.claude/settings.json` runs the script after every SKILL.md edit, and the `surface-tags` job in `test.yml` fails a PR whose tags drifted (`--check` mode). Until a plugin is fully labeled, its tag stays manual and the script leaves it alone. The script does not touch `README.md` — mirror tag changes into the badges by hand.

### Per-skill `surfaces:` frontmatter

Individual skills can carry their own surface list in SKILL.md frontmatter, directly after `description:`:

```yaml
surfaces: [code, cowork, desktop, web]
```

Use the identifiers and canonical order from "The surfaces" above. The per-skill field is finer-grained than the plugin tag and **overrides it where they disagree**.

Don't hand-derive the list — run the repo-local `/scan-surfaces` command. It reads what each skill actually instructs an agent to do, maps the needed capabilities to what each surface offers, writes the `surfaces:` field, and recommends refactorings (per-surface reference files, tool-agnostic wording, gating rare code-only features) that would widen availability; `--refactor` applies them.

## Testing Changes

Before committing changes:

1. **Validate the marketplace locally:**
   ```bash
   claude plugin validate .
   ```
   or from Claude Code:
   ```
   /plugin validate .
   ```

2. **Test plugin installation locally:**
   ```bash
   /plugin marketplace add /Users/stig/git/sunstone/claude-public-plugins
   /plugin install [plugin-name]@sunstone-public
   ```

3. **Test the plugin functionality:**
   Verify that all skills load correctly and work as expected.

## Distribution

This marketplace is hosted on GitHub at `sunstoneinstitute/claude-public-plugins`.

Users can add this marketplace with:
```bash
/plugin marketplace add sunstoneinstitute/claude-public-plugins
```

Then install plugins with:
```bash
/plugin install [plugin-name]@sunstone-public
```

## Naming Conventions

- **Marketplace name:** Use kebab-case, no spaces (e.g., `sunstone-public`)
- **Plugin names:** Use kebab-case (e.g., `gam-admin`, not `GAM_Admin`)
- **Directory names:** Match plugin names exactly
- **Keywords:** Use lowercase, descriptive keywords for discovery
- **Versions:** Follow semantic versioning (major.minor.patch)

## Referencing Skills, Commands, and Workflows

**Always use the fully qualified `<plugin>:<name>` form** when a SKILL.md, command, agent, or workflow references another skill, command, or workflow by its runtime name — even when both live in the same plugin. Plugin-provided skills and workflows are registered under the plugin-prefixed name **only**, so an unprefixed name fails at runtime:

```
Error: Workflow "concept-mapping-research" not found.
Available: deep-research, code-review, ontology-engineering:concept-mapping-research
```

This applies to every place a name is resolved by the runtime:

- `Workflow({ name: '...' })` invocations in command/skill instructions
- Skill-tool references ("use the X skill")
- Slash-command mentions — use `/lode:next` when the command ships in a plugin
- Prose mentions of a runtime name in SKILL.md, commands/, and agents/ — use the prefixed form there too, so an agent copying the name into a tool call gets a name that resolves

Unprefixed names are only correct for things that are *not* plugin-scoped (built-ins like `deep-research`, or repo-local `.claude/workflows/` entries in the consuming repo). Relative file links (e.g. `../workflows/foo.js`) are fine for pointing at source files — the rule is about **runtime names**, not paths.

## Reserved Names to Avoid

Do not use these names as they're reserved:
- `claude-code-marketplace`
- `claude-code-plugins`
- `claude-plugins-official`
- `anthropic-marketplace`
- `anthropic-plugins`

## File Organization Best Practices

- **Skills go in `skills/[name]/SKILL.md`** - Never place SKILL.md at plugin root
- Keep SKILL.md lean (1,500-2,000 words ideal, max 3,000)
- Move detailed content to `references/` for on-demand loading
- Use `examples/` for complete, runnable code samples
- Use `scripts/` for utility tools that can be executed without loading into context
- Include comprehensive descriptions in .claude-plugin/marketplace.json
- Use meaningful keywords for discoverability

### Progressive Disclosure Pattern

Claude Code loads skill content progressively:
1. **Always loaded**: Skill name and description from frontmatter (~100 words)
2. **On trigger**: SKILL.md body (<3,000 words recommended)
3. **On demand**: References, examples, scripts (unlimited)

This keeps context efficient while allowing rich documentation.

## Writing Style: Plain Language, Precise Meaning

Skills, commands, and READMEs in this marketplace are read by people who may know nothing
about the tool or domain a plugin covers. Write so they can follow it. **The goal is plain
language that keeps every bit of the original precision — simpler words, not a simpler meaning.**

- **Prefer the everyday word.** Use "use" not "utilize", "start" not "initiate", "about" not
  "regarding", "so" not "in order that". Short, common words unless a longer one is genuinely
  more exact.
- **Keep sentences short and direct.** One idea per sentence. Break up long chains of clauses.
  Imperative voice ("Run the migration", not "The migration should be run").
- **Do not sacrifice precision for simplicity.** Exact meaning wins over easy reading whenever
  the two conflict. Never round off a technical constraint, drop a qualifier that changes the
  meaning, or blur a distinction just to sound simpler. Plain ≠ vague.
- **Keep terms of art — but introduce them.** Real domain terms are precise; keep them. On first
  use, add a few plain words saying what the term means or does, so a non-expert isn't stranded.
  Don't invent folksy substitutes for established names.
- **Cut jargon that isn't load-bearing.** Corporate/academic filler ("leverage", "facilitate",
  "utilize", "in the context of", "it is important to note that") adds no meaning — remove it.
- **Spell out the first use of an acronym** the reader may not know, then use the short form.
- **Explain the "why" in plain terms.** A one-line reason a step exists helps a non-expert far
  more than more precise wording of the step itself.

Quick test: *could a smart colleague from a different discipline follow this without a glossary,
and does it still say exactly what it said before?* If yes to both, the balance is right.

### ❌ WRONG: SKILL.md at plugin root

```
plugins/my-plugin/
├── SKILL.md           ← WRONG! Skills won't be discovered
├── references/
└── scripts/
```

### ✓ CORRECT: SKILL.md in skills subdirectory

```
plugins/my-plugin/
└── skills/
    └── my-skill/
        ├── SKILL.md   ← Correct location
        ├── references/
        └── scripts/
```

### Other Common Issues

- **Missing `plugin.json`**: Every plugin MUST have `.claude-plugin/plugin.json`, or claude.ai strict-mode GitHub sync rejects it. Easy to forget when adding a new plugin — add it in the same change as the `marketplace.json` entry.
- **Vague trigger descriptions**: Use specific phrases like "This skill should be used when the user asks to 'create X', 'deploy Y'"
- **Bloated SKILL.md**: Keep under 3,000 words; move details to references/.
- **Second-person writing**: Use imperative form ("Configure the server") not "You should configure..."
- **Missing frontmatter**: SKILL.md requires `name` and `description` in YAML frontmatter

## Commit Guidelines

When committing changes:

1. **Adding new plugin:**
   ```
   Add "[plugin-name]" plugin
   ```

2. **Updating existing plugin:**
   ```
   Update [plugin-name]: [brief description of changes]
   ```

3. **Updating marketplace metadata:**
   ```
   Update marketplace metadata: [description]
   ```

## Security Considerations

- This repo is public. Review every change for anything internal before pushing.
- Review all plugin code before adding to marketplace
- Ensure skills don't contain hardcoded credentials
- Use environment variables for sensitive configuration
- Document any required permissions or tokens

## Updates and Versioning

**Do not edit the `version` field of an existing plugin in a PR.** Versions are bumped automatically at merge time based on PR labels — this eliminates the rebase storms that come from many PRs simultaneously bumping the same file.

When updating an existing plugin:

1. Make your code/skill/doc changes under `plugins/<name>/`.
2. Apply exactly one of these labels to the PR:
   - `bump-patch` — bug fixes, doc tweaks, internal changes
   - `bump-minor` — new features, new skills, new content
   - `bump-major` — breaking changes
3. The `check-plugin-versions` CI job will fail the PR if a plugin file changed and no bump label is present.
4. Merge the PR using whichever path you prefer — approval review, `gh pr merge`, the GitHub UI "Merge" button, native auto-merge, or admin merge. After the merge lands, `bump-versions-on-merge.yml` reads the PR's bump label, applies the version bump to `marketplace.json` as a separate commit on main, pushes it, and creates the `<plugin>-<version>` tag in the same run (its tagging step runs on every merged PR, so versions bumped by `auto-merge.yml` inside the PR — and brand-new plugins' initial versions — get tagged too).

**Two workflows handle merges; they are designed to cooperate:**

- `auto-merge.yml` (optional convenience): when a PR has the `auto-merge` label *and* receives an approval review, this workflow rebases the branch onto main, applies the version bump *inside* the PR, and merges. Use it if you want hands-off rebase-and-merge after approval.
- `bump-versions-on-merge.yml` (always-on safety net): runs after any PR is merged. If the merged PR's commit history already includes a `Bump plugin version(s):` commit (from `auto-merge.yml`), it skips. Otherwise it bumps and pushes a post-merge commit to main. This guarantees a bump regardless of how the PR was merged.

**Editing `description` or `keywords` in `marketplace.json` is fine** — these don't require a bump label and don't typically conflict because they're rare and per-plugin.

**Adding a new plugin:** add the full plugin entry to `marketplace.json` with `"version": "1.0.0"`. Both bump workflows detect new-plugin entries (not present on main before the merge) and preserve the incoming version as-is. The PR still needs a bump label if it touches files under `plugins/<new-plugin>/` (use `bump-minor` by convention).

**Removing a plugin:** delete the plugin block from `marketplace.json` and the plugin directory. Apply a `bump-major` label (the removal is a breaking change to the marketplace surface); the bump script silently skips the removed plugin since it's no longer in `marketplace.json`.

Required repository setup: the `auto-merge`, `bump-major`, `bump-minor`, and `bump-patch` labels must exist, and `auto-merge.yml` needs a `CLAUDE_CODE_OAUTH_TOKEN` secret for its conflict-resolution fallback.

Users will receive updates when they run:
```bash
/plugin marketplace update
```

## References

- Official Claude Code Plugin Marketplace Documentation: https://code.claude.com/docs/en/plugin-marketplaces
- Claude Code Documentation: https://code.claude.com/docs
