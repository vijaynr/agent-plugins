#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: skills/init-workspace/scripts/init-git-branch.sh --branch <new-branch> [--base <base-ref>] [--remote <remote>] [--stash-approved] [--dry-run]

Creates/checks out a fresh git branch before SDD /spec work. If the working tree
has changes, the script requires --stash-approved before it stashes and creates
the branch.

Output: JSON with branch, base, dirty state, stash, and creation flags.
EOF
}

BRANCH=""
BASE=""
REMOTE="origin"
STASH_APPROVED=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --branch) BRANCH="${2:-}"; shift 2 ;;
    --branch=*) BRANCH="${1#--branch=}"; shift ;;
    --base) BASE="${2:-}"; shift 2 ;;
    --base=*) BASE="${1#--base=}"; shift ;;
    --remote) REMOTE="${2:-}"; shift 2 ;;
    --remote=*) REMOTE="${1#--remote=}"; shift ;;
    --stash-approved) STASH_APPROVED=true; shift ;;
    --dry-run|-n) DRY_RUN=true; shift ;;
    --) shift; break ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) echo "Unexpected argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$BRANCH" ]]; then
  usage >&2
  exit 2
fi

json_escape() {
  local s="$1"
  s=${s//\\/\\\\}; s=${s//\"/\\\"}; s=${s//$'\n'/\\n}; s=${s//$'\r'/\\r}; s=${s//$'\t'/\\t}
  printf '%s' "$s"
}
bool_json() { [[ "$1" == "true" ]] && printf 'true' || printf 'false'; }

OK=true
ERROR=""
REQUIRES_STASH_APPROVAL=false
STASH_CREATED=false
BRANCH_CREATED=false
CHECKED_OUT=false
STASH_REF=""

GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || true)
if [[ -z "$GIT_ROOT" ]]; then
  OK=false
  ERROR="not inside a git repository"
fi

if [[ "$OK" == "true" ]]; then
  cd "$GIT_ROOT"
  [[ -n "$BASE" ]] || BASE="${CURRENT_BRANCH:-HEAD}"
  STATUS=$(git status --porcelain)
  DIRTY=false
  [[ -n "$STATUS" ]] && DIRTY=true

  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    OK=false
    ERROR="branch already exists: $BRANCH"
  elif [[ "$DIRTY" == "true" && "$STASH_APPROVED" != "true" ]]; then
    OK=false
    REQUIRES_STASH_APPROVAL=true
    ERROR="working tree has changes; rerun with --stash-approved after user approval or continue without creating a branch"
  elif [[ "$DRY_RUN" != "true" ]]; then
    if [[ "$DIRTY" == "true" ]]; then
      git stash push -u -m "init-workspace before creating $BRANCH" >/dev/null
      STASH_CREATED=true
      STASH_REF=$(git stash list -n 1 --format='%gd')
    fi
    git fetch "$REMOTE" --quiet || true
    git switch -c "$BRANCH" "$BASE" >/dev/null
    BRANCH_CREATED=true
    CHECKED_OUT=true
  fi
fi

cat <<EOF
{
  "ok": $(bool_json "$OK"),
  "error": "$(json_escape "$ERROR")",
  "gitRoot": "$(json_escape "$GIT_ROOT")",
  "currentBranch": "$(json_escape "$CURRENT_BRANCH")",
  "requestedBranch": "$(json_escape "$BRANCH")",
  "base": "$(json_escape "$BASE")",
  "remote": "$(json_escape "$REMOTE")",
  "dirty": $(bool_json "${DIRTY:-false}"),
  "requiresStashApproval": $(bool_json "$REQUIRES_STASH_APPROVAL"),
  "stashApproved": $(bool_json "$STASH_APPROVED"),
  "stashCreated": $(bool_json "$STASH_CREATED"),
  "stashRef": "$(json_escape "$STASH_REF")",
  "branchCreated": $(bool_json "$BRANCH_CREATED"),
  "checkedOut": $(bool_json "$CHECKED_OUT"),
  "dryRun": $(bool_json "$DRY_RUN")
}
EOF

[[ "$OK" == "true" ]] || exit 1
