#!/usr/bin/env bash
set -euo pipefail

# Ensure the repo .gitignore contains the AIDD feature-artifact allowlist.
# Usage: bash skills/init-workspace/scripts/ensure-aidd-gitignore.sh [repo-root]

ROOT="${1:-.}"
GITIGNORE="$ROOT/.gitignore"

mkdir -p "$(dirname "$GITIGNORE")"
[[ -f "$GITIGNORE" ]] || : > "$GITIGNORE"

AIDD_LINES=(
  "# AIDD"
  "/.features/*"
  "!/.features/*/"
  "/.features/*/*"
  "!/.features/*/SPEC.md"
  "!/.features/*/DESIGN.md"
  "!/.features/*/tasks/"
  "!/.features/*/tasks/PLAN.md"
  "!/.features/*/tasks/TODO.md"
)

changed=false
if [[ -s "$GITIGNORE" && $(tail -c 1 "$GITIGNORE" | wc -l) -eq 0 ]]; then
  printf '\n' >> "$GITIGNORE"
  changed=true
fi

for line in "${AIDD_LINES[@]}"; do
  if ! grep -Fxq "$line" "$GITIGNORE"; then
    printf '%s\n' "$line" >> "$GITIGNORE"
    changed=true
  fi
done

if [[ "$changed" == "true" ]]; then
  echo '{"ok":true,"changed":true,"gitignore":"'"$GITIGNORE"'"}'
else
  echo '{"ok":true,"changed":false,"gitignore":"'"$GITIGNORE"'"}'
fi
