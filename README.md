# Sunstone Public Plugin Marketplace

Public Claude Code plugins from [Sunstone Institute](https://sunstone.institute). Anyone can add
this marketplace and install from it.

Sunstone's internal plugins — the ones that need our clusters, credentials, or unreleased work —
live in a separate private marketplace and are not published here.

---

## Available Plugins

Each plugin is prefixed with a **surface tag** listing every surface where at least one of its skills works. The surfaces, from most to least capable host, are `code` (Claude Code with host access — CLI, IDE, the desktop app's local Code sessions), `cowork` (Claude Cowork), `desktop` (Claude Desktop chat), and `web` (claude.ai). The common tags:

- **`[code]`** — every skill needs Claude Code (a terminal, local tools, the filesystem, or live infrastructure).
- **`[code desktop web]`** — has skills that work anywhere Claude runs, including Claude Desktop and claude.ai web.
- Tags including **`cowork`** appear as skills gain per-surface labels. Individual skills within a plugin may support fewer surfaces than the tag — the `surfaces:` field in each SKILL.md is the exact per-skill truth (see [CLAUDE.md](CLAUDE.md#surface-availability-tags)).

#### lode — `[code]`
Worklode: worktree-bound task pickup for agents. Slash commands `/lode:next|resume|done|block|status` wrap the `lode` CLI to claim a ready task, create its `wt/<id>-<slug>` worktree, bind the lease, and mark it done/blocked. Also ships the `lode-worker` agent for unattended loops. Lifecycle hooks ship with the CLI, not the plugin: `lode install` writes them per repo (Claude Code settings plus the git pre-commit heartbeat), so they stay versioned with the binary.

---

## Using the Marketplace

### Adding the Marketplace

```bash
/plugin marketplace add sunstoneinstitute/claude-public-plugins
```

### Browsing Available Plugins

List all available plugins:

```bash
/plugin marketplace list
```

View details about a specific plugin:

```bash
/plugin marketplace info [plugin-name]
```

### Installing Plugins

```bash
/plugin install lode@sunstone-public
```

> **Tip:** `[code desktop web]` plugins also work on Claude Desktop and claude.ai web. `[code]` plugins need Claude Code.

### Updating Plugins

```bash
/plugin marketplace update
/plugin upgrade [plugin-name]
```

Or upgrade all plugins:

```bash
/plugin upgrade --all
```

### Managing Installed Plugins

List installed plugins:

```bash
/plugin list
```

Uninstall a plugin:

```bash
/plugin uninstall [plugin-name]
```

---

## For Maintainers

See [CLAUDE.md](CLAUDE.md) for full maintenance guidelines covering plugin structure, surface tags, naming conventions, testing, and commit guidelines.

Two things that are easy to forget:
- Skills **must** be placed in `plugins/[plugin-name]/skills/[skill-name]/SKILL.md`, not at the plugin root.
- This plugin list **must be kept in sync** with `.claude-plugin/marketplace.json` whenever plugins are added, removed, moved, or re-tagged.

---

## References

- [Official Claude Code Plugin Marketplace Documentation](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude Code Documentation](https://code.claude.com/docs)
