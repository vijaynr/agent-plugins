#!/usr/bin/env bash
# Root Plugin Workspace Helper — list, validate, install, and remove plugins
# from this multi-plugin workspace. This script intentionally does not copy
# individual skills, agents, commands, prompts, or hooks into user directories.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="$SCRIPT_DIR/plugins"

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
CYAN=$'\033[0;36m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

info() { printf '%sℹ%s %s\n' "$CYAN" "$RESET" "$*"; }
success() { printf '%s✔%s %s\n' "$GREEN" "$RESET" "$*"; }
warn() { printf '%s⚠%s %s\n' "$YELLOW" "$RESET" "$*"; }
error() { printf '%s✖%s %s\n' "$RED" "$RESET" "$*" >&2; }

usage() {
    cat <<EOF
${BOLD}Plugin Workspace Helper${RESET}

${BOLD}USAGE${RESET}
    ./agents.sh <command> [options]

${BOLD}COMMANDS${RESET}
    ${CYAN}list${RESET}                         List plugins discovered under plugins/*/plugin.json
    ${CYAN}validate${RESET}                     Validate marketplace and plugin manifests
    ${CYAN}status${RESET}                       Show workspace and Copilot CLI status
    ${CYAN}install <plugin|all>${RESET}         Install one plugin or all plugins with Copilot CLI
    ${CYAN}remove <plugin|all>${RESET}          Uninstall one plugin or all plugins with Copilot CLI
    ${CYAN}help${RESET}                         Show this help

${BOLD}NOTES${RESET}
    Installs use: ${CYAN}copilot plugin install plugins/<plugin>${RESET}
    This helper does not copy individual assets into ~/.copilot, ~/.agents,
    VS Code profile folders, or project .github directories.
EOF
}

plugin_dirs() {
    local dir
    for dir in "$PLUGINS_DIR"/*; do
        [ -f "$dir/plugin.json" ] || continue
        printf '%s\n' "$dir"
    done | sort
}

plugin_name_from_dir() {
    basename "$1"
}

plugin_manifest_name() {
    local dir="$1"
    local name
    name="$(json_field "$dir/plugin.json" name)"
    [ -n "$name" ] && printf '%s\n' "$name" || plugin_name_from_dir "$dir"
}

relative_plugin_path() {
    local name="$1"
    printf 'plugins/%s\n' "$name"
}

json_field() {
    local file="$1"
    local field="$2"
    python - "$file" "$field" <<'PY' 2>/dev/null || true
import json
import sys
path, field = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)
value = data.get(field, "")
print(value if isinstance(value, str) else "")
PY
}

cmd_list() {
    local dir name display description rel
    printf '%s\n' "Plugins:"
    while IFS= read -r dir; do
        [ -n "$dir" ] || continue
        name="$(plugin_manifest_name "$dir")"
        display="$(json_field "$dir/plugin.json" displayName)"
        description="$(json_field "$dir/plugin.json" description)"
        rel="$(relative_plugin_path "$(plugin_name_from_dir "$dir")")"
        if [ -n "$display" ]; then
            printf '  %-22s %s\n' "$name" "$display"
        else
            printf '  %s\n' "$name"
        fi
        printf '    path: %s\n' "$rel"
        [ -n "$description" ] && printf '    description: %s\n' "$description"
    done < <(plugin_dirs)
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

require_python() {
    if ! command_exists python; then
        error "python is required for JSON validation but was not found on PATH"
        return 1
    fi
}

validate_json_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        error "Missing JSON file: $file"
        return 1
    fi
    if python -m json.tool "$file" >/dev/null; then
        success "Valid JSON: $file"
        return 0
    fi
    error "Invalid JSON: $file"
    return 1
}

validate_marketplace_sources() {
    local file="$1"
    python - "$SCRIPT_DIR" "$file" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
marketplace = Path(sys.argv[2])
base = marketplace.parent
if not marketplace.is_absolute():
    marketplace = root / marketplace
    base = marketplace.parent

data = json.loads(marketplace.read_text(encoding="utf-8"))
ok = True
for plugin in data.get("plugins", []):
    name = plugin.get("name", "<missing-name>")
    source = plugin.get("source")
    if not source:
        print(f"Missing source for marketplace plugin: {name}", file=sys.stderr)
        ok = False
        continue
    path = (base / source).resolve()
    if not path.is_dir():
        print(f"Missing source path for {name}: {source}", file=sys.stderr)
        ok = False
        continue
    if not (path / "plugin.json").is_file():
        print(f"Missing plugin.json for {name}: {source}", file=sys.stderr)
        ok = False
if not ok:
    sys.exit(1)
PY
}

cmd_validate() {
    local failures=0 dir rel
    require_python || return 1

    validate_json_file "marketplace.json" || failures=$((failures + 1))
    validate_json_file ".github/plugin/marketplace.json" || failures=$((failures + 1))

    while IFS= read -r dir; do
        [ -n "$dir" ] || continue
        rel="plugins/$(plugin_name_from_dir "$dir")/plugin.json"
        validate_json_file "$rel" || failures=$((failures + 1))
    done < <(plugin_dirs)

    if validate_marketplace_sources "marketplace.json"; then
        success "Marketplace sources exist: marketplace.json"
    else
        error "Marketplace source validation failed: marketplace.json"
        failures=$((failures + 1))
    fi

    if validate_marketplace_sources ".github/plugin/marketplace.json"; then
        success "Marketplace sources exist: .github/plugin/marketplace.json"
    else
        error "Marketplace source validation failed: .github/plugin/marketplace.json"
        failures=$((failures + 1))
    fi

    if [ "$failures" -eq 0 ]; then
        success "Validation passed"
        return 0
    fi

    error "Validation failed with $failures issue(s)"
    return 1
}

plugin_count() {
    local count=0 dir
    while IFS= read -r dir; do
        [ -n "$dir" ] || continue
        count=$((count + 1))
    done < <(plugin_dirs)
    printf '%s\n' "$count"
}

cmd_status() {
    local count validation_status copilot_status dir name
    count="$(plugin_count)"

    printf '%s\n' "Workspace status"
    printf '  Plugins discovered: %s\n' "$count"
    printf '  Plugin names:'
    while IFS= read -r dir; do
        [ -n "$dir" ] || continue
        name="$(plugin_manifest_name "$dir")"
        printf ' %s' "$name"
    done < <(plugin_dirs)
    printf '\n'

    if cmd_validate >/dev/null 2>&1; then
        validation_status="valid"
    else
        validation_status="invalid"
    fi
    printf '  Manifest validation: %s\n' "$validation_status"

    if command_exists copilot; then
        copilot_status="available ($(command -v copilot))"
    else
        copilot_status="missing"
    fi
    printf '  Copilot CLI: %s\n' "$copilot_status"

    [ "$validation_status" = "valid" ]
}

plugin_dir() {
    local name="$1"
    printf '%s/%s\n' "$PLUGINS_DIR" "$name"
}

require_plugin() {
    local name="$1"
    local dir
    dir="$(plugin_dir "$name")"
    if [ ! -f "$dir/plugin.json" ]; then
        error "Unknown plugin: $name"
        return 1
    fi
}

copilot_bin() {
    printf '%s\n' "${AGENTS_COPILOT_BIN:-copilot}"
}

require_copilot() {
    local bin
    bin="$(copilot_bin)"
    if ! command_exists "$bin"; then
        error "copilot CLI is required but was not found on PATH: $bin"
        return 1
    fi
}

install_one() {
    local plugin="$1"
    local command_path
    command_path="$(relative_plugin_path "$plugin")"

    require_plugin "$plugin" || return 1
    cmd_validate >/dev/null || return 1

    info "Running: copilot plugin install $command_path"
    require_copilot || return 1
    "$(copilot_bin)" plugin install "$command_path"
}

confirm() {
    local prompt="$1"
    local reply
    printf '%s [y/N] ' "$prompt"
    read -r reply
    case "$reply" in
        y|Y|yes|YES) return 0 ;;
        *) return 1 ;;
    esac
}

print_plugin_bullets() {
    local header="$1"
    local dir plugin
    printf '%s\n' "$header"
    while IFS= read -r dir; do
        [ -n "$dir" ] || continue
        plugin="$(plugin_name_from_dir "$dir")"
        printf '  - %s\n' "$plugin"
    done < <(plugin_dirs)
}

install_all() {
    local dir plugin failures=0
    print_plugin_bullets "Install all plugins:"

    if ! confirm "Install all plugins?"; then
        warn "Cancelled"
        return 0
    fi

    cmd_validate >/dev/null || return 1
    require_copilot || return 1

    while IFS= read -r dir; do
        [ -n "$dir" ] || continue
        plugin="$(plugin_name_from_dir "$dir")"
        install_one "$plugin" || failures=$((failures + 1))
    done < <(plugin_dirs)

    [ "$failures" -eq 0 ] || {
        error "Install all completed with $failures failure(s)"
        return 1
    }
}

cmd_install() {
    local target="${1:-}"
    if [ -z "$target" ]; then
        error "Missing plugin name. Usage: ./agents.sh install <plugin|all>"
        return 1
    fi
    if [ "$target" = "all" ]; then
        install_all
        return $?
    fi
    install_one "$target"
}

remove_one() {
    local plugin="$1"
    require_plugin "$plugin" || return 1

    printf 'Uninstall plugin: %s\n' "$plugin"
    if ! confirm "Uninstall $plugin?"; then
        warn "Cancelled"
        return 0
    fi

    info "Running: copilot plugin uninstall $plugin"
    require_copilot || return 1
    "$(copilot_bin)" plugin uninstall "$plugin"
}

remove_all() {
    local dir plugin failures=0
    print_plugin_bullets "Uninstall every plugin:"

    if ! confirm "Uninstall every plugin?"; then
        warn "Cancelled"
        return 0
    fi

    require_copilot || return 1
    while IFS= read -r dir; do
        [ -n "$dir" ] || continue
        plugin="$(plugin_name_from_dir "$dir")"
        info "Running: copilot plugin uninstall $plugin"
        "$(copilot_bin)" plugin uninstall "$plugin" || failures=$((failures + 1))
    done < <(plugin_dirs)

    [ "$failures" -eq 0 ] || {
        error "Remove all completed with $failures failure(s)"
        return 1
    }
}

cmd_remove() {
    local target="${1:-}"
    if [ -z "$target" ]; then
        error "Missing plugin name. Usage: ./agents.sh remove <plugin|all>"
        return 1
    fi
    if [ "$target" = "all" ]; then
        remove_all
        return $?
    fi
    remove_one "$target"
}

main() {
    local cmd="${1:-help}"
    if [ "$#" -gt 0 ]; then
        shift
    fi

    case "$cmd" in
        list|ls) cmd_list "$@" ;;
        validate|check) cmd_validate "$@" ;;
        status|st) cmd_status "$@" ;;
        install|i) cmd_install "$@" ;;
        remove|rm|uninstall) cmd_remove "$@" ;;
        help|-h|--help) usage ;;
        *)
            error "Unknown command: $cmd"
            usage
            return 1
            ;;
    esac
}

main "$@"
