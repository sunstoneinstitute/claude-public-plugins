#!/usr/bin/env bash
#
# check-plugin-structure.sh
# Validates that all plugins in the marketplace have correct directory structure.
#
# Required structure for skills:
#   plugins/[plugin-name]/skills/[skill-name]/SKILL.md
#
# NOT allowed:
#   plugins/[plugin-name]/SKILL.md  (skill at root)
#

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGINS_DIR="$REPO_ROOT/plugins"

errors=0
warnings=0

log_error() {
    echo "ERROR: $1"
    errors=$((errors + 1))
}

log_warn() {
    echo "WARNING: $1"
    warnings=$((warnings + 1))
}

log_ok() {
    echo "OK: $1"
}

# Check if plugins directory exists
if [[ ! -d "$PLUGINS_DIR" ]]; then
    log_error "Plugins directory not found: $PLUGINS_DIR"
    exit 1
fi

echo "Checking plugin structure in $PLUGINS_DIR..."
echo ""

# Iterate over each plugin directory
for plugin_dir in "$PLUGINS_DIR"/*/; do
    [[ -d "$plugin_dir" ]] || continue

    plugin_name=$(basename "$plugin_dir")

    # Check for SKILL.md at plugin root (incorrect)
    if [[ -f "$plugin_dir/SKILL.md" ]]; then
        log_error "$plugin_name: SKILL.md found at plugin root. Move to skills/$plugin_name/SKILL.md"
    fi

    # Check for skills directory
    if [[ ! -d "$plugin_dir/skills" ]]; then
        # Check if this plugin has any skill-related files at root
        if [[ -f "$plugin_dir/SKILL.md" ]] || [[ -d "$plugin_dir/references" ]]; then
            log_error "$plugin_name: Missing skills/ directory. Skills must be in skills/[skill-name]/"
        else
            # Plugin might only have commands/agents/hooks, which is valid
            if [[ -d "$plugin_dir/commands" ]] || [[ -d "$plugin_dir/agents" ]] || [[ -d "$plugin_dir/hooks" ]]; then
                log_ok "$plugin_name: Valid plugin (commands/agents/hooks only, no skills)"
            else
                log_warn "$plugin_name: Empty plugin - no skills, commands, agents, or hooks found"
            fi
        fi
        continue
    fi

    # Check each skill in skills/ directory
    skill_count=0
    for skill_dir in "$plugin_dir/skills"/*/; do
        [[ -d "$skill_dir" ]] || continue

        skill_name=$(basename "$skill_dir")
        skill_count=$((skill_count + 1))

        # Check for SKILL.md in skill directory
        if [[ ! -f "$skill_dir/SKILL.md" ]]; then
            log_error "$plugin_name/skills/$skill_name: Missing SKILL.md"
            continue
        fi

        # Validate SKILL.md has required frontmatter
        first_line=$(head -1 "$skill_dir/SKILL.md")
        if [[ "$first_line" != "---" ]]; then
            log_error "$plugin_name/skills/$skill_name/SKILL.md: Missing YAML frontmatter (must start with ---)"
            continue
        fi

        # Check for required frontmatter fields
        has_name=$(head -20 "$skill_dir/SKILL.md" | grep -c "^name:" || true)
        has_desc=$(head -20 "$skill_dir/SKILL.md" | grep -c "^description:" || true)

        if [[ "$has_name" -eq 0 ]]; then
            log_error "$plugin_name/skills/$skill_name/SKILL.md: Missing 'name' in frontmatter"
        fi

        if [[ "$has_desc" -eq 0 ]]; then
            log_error "$plugin_name/skills/$skill_name/SKILL.md: Missing 'description' in frontmatter"
        fi

        # Check description uses third-person format
        if [[ "$has_desc" -gt 0 ]]; then
            description=$(grep "^description:" "$skill_dir/SKILL.md" | head -1)
            if ! echo "$description" | grep -qi "should be used\|provides\|covers\|helps"; then
                log_warn "$plugin_name/skills/$skill_name: Description should use third-person (e.g., 'This skill should be used when...')"
            fi
        fi

        log_ok "$plugin_name/skills/$skill_name: Valid skill structure"
    done

    if [[ $skill_count -eq 0 ]]; then
        log_warn "$plugin_name: skills/ directory exists but contains no skills"
    fi

    # Check for other valid plugin components
    [[ -d "$plugin_dir/commands" ]] && log_ok "$plugin_name: Has commands/"
    [[ -d "$plugin_dir/agents" ]] && log_ok "$plugin_name: Has agents/"
    [[ -d "$plugin_dir/hooks" ]] && log_ok "$plugin_name: Has hooks/"
done

echo ""
echo "================================"
if [[ $errors -gt 0 ]]; then
    echo "Structure check FAILED: $errors error(s), $warnings warning(s)"
    exit 1
elif [[ $warnings -gt 0 ]]; then
    echo "Structure check passed with $warnings warning(s)"
    exit 0
else
    echo "Structure check passed!"
    exit 0
fi
