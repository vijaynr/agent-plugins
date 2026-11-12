#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: skills/init-workspace/scripts/init-git-worktree.sh <feature> [--branch <branch>] [--base <base-ref>] [--worktree-path <path>] [--repo-root <path>] [--remote <remote>] [--dry-run]

Creates a dedicated git worktree for a feature at ../<repo>.worktrees/<feature>
(or at --worktree-path).

Output: JSON with worktree path, repo root, branch, base, and creation flags.
EOF
}

FEATURE=""
BRANCH=""
BASE=""
WORKTREE_PATH=""
REPO_ROOT=""
REMOTE="origin"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --feature) FEATURE="${2:-}"; shift 2 ;;
    --feature=*) FEATURE="${1#--feature=}"; shift ;;
    --branch) BRANCH="${2:-}"; shift 2 ;;
    --branch=*) BRANCH="${1#--branch=}"; shift ;;
    --base) BASE="${2:-}"; shift 2 ;;
    --base=*) BASE="${1#--base=}"; shift ;;
    --worktree-path) WORKTREE_PATH="${2:-}"; shift 2 ;;
    --worktree-path=*) WORKTREE_PATH="${1#--worktree-path=}"; shift ;;
    --repo-root) REPO_ROOT="${2:-}"; shift 2 ;;
    --repo-root=*) REPO_ROOT="${1#--repo-root=}"; shift ;;
    --remote) REMOTE="${2:-}"; shift 2 ;;
    --remote=*) REMOTE="${1#--remote=}"; shift ;;
    --dry-run|-n) DRY_RUN=true; shift ;;
    --) shift; break ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)
      if [[ -z "$FEATURE" ]]; then
        FEATURE="$1"
        shift
      else
        echo "Unexpected argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
done

if [[ -z "$FEATURE" ]]; then
  echo "Error: <feature> is required" >&2
  usage >&2
  exit 2
fi

json_escape() {
  local s="$1"
  s=${s//\\/\\\\}; s=${s//\"/\\\"}; s=${s//$'\n'/\\n}; s=${s//$'\r'/\\r}; s=${s//$'\t'/\\t}
  printf '%s' "$s"
}
bool_json() { [[ "$1" == "true" ]] && printf 'true' || printf 'false'; }

slugify() {
  local val="$1"
  val="$(echo "$val" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g' | sed -E 's/^-+|-+$//g')"
  if [[ -z "$val" ]]; then
    val="feature"
  fi
  printf '%s' "$val"
}

normalize_slashes() {
  local val="$1"
  val="${val//\\//}"
  printf '%s' "$val"
}

OK=true
ERROR=""
RESOLVED_REPO_ROOT=""
RESOLVED_WORKTREE_PATH=""
BRANCH_CREATED=false
WORKTREE_CREATED=false
WORKTREE_EXISTED=false

FEATURE_SLUG="$(slugify "$FEATURE")"
if [[ -z "$BRANCH" ]]; then
  BRANCH="$FEATURE_SLUG"
fi

# 1. Resolve repository root
if [[ -z "$REPO_ROOT" ]]; then
  if ! GIT_TOP="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    OK=false
    ERROR="not inside a git repository"
  else
    RESOLVED_REPO_ROOT="$(cd "$GIT_TOP" && pwd -P)"
  fi
else
  if [[ ! -d "$REPO_ROOT" ]]; then
    OK=false
    ERROR="repository root does not exist: $REPO_ROOT"
  else
    RESOLVED_REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"
  fi
fi

if [[ "$OK" == "true" ]]; then
  cd "$RESOLVED_REPO_ROOT"

  # 2. Determine base ref
  if [[ -z "$BASE" ]]; then
    CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || true)"
    if [[ -z "$CURRENT_BRANCH" ]]; then
      BASE="HEAD"
    else
      BASE="$CURRENT_BRANCH"
    fi
  fi

  # 3. Resolve destination worktree path
  REPO_NAME="$(basename "$RESOLVED_REPO_ROOT")"
  PARENT_DIR="$(dirname "$RESOLVED_REPO_ROOT")"

  if [[ -z "$WORKTREE_PATH" ]]; then
    WORKTREE_PARENT_DIR="$PARENT_DIR/$REPO_NAME.worktrees"
    RESOLVED_WORKTREE_PATH="$WORKTREE_PARENT_DIR/$FEATURE_SLUG"
  else
    if [[ "$WORKTREE_PATH" = /* ]] || [[ "$WORKTREE_PATH" =~ ^[A-Za-z]: ]]; then
      RESOLVED_WORKTREE_PATH="$WORKTREE_PATH"
    else
      RESOLVED_WORKTREE_PATH="$RESOLVED_REPO_ROOT/$WORKTREE_PATH"
    fi
  fi

  NORM_WORKTREE_PATH="$(normalize_slashes "$RESOLVED_WORKTREE_PATH")"

  # 4. Check if already in git worktree list
  EXISTING_WORKTREES="$(git worktree list --porcelain 2>/dev/null | grep '^worktree ' | cut -d' ' -f2- || true)"
  REGISTERED_PATH=""
  while IFS= read -r wt_line; do
    if [[ -n "$wt_line" ]]; then
      wt_norm="$(normalize_slashes "$wt_line")"
      if [[ "$wt_norm" == "$NORM_WORKTREE_PATH" ]]; then
        REGISTERED_PATH="$wt_line"
        WORKTREE_EXISTED=true
        break
      fi
    fi
  done <<< "$EXISTING_WORKTREES"

  if [[ "$WORKTREE_EXISTED" == "true" ]]; then
    EXISTING_BRANCH="$(git -C "$REGISTERED_PATH" branch --show-current 2>/dev/null || true)"
    if [[ "$EXISTING_BRANCH" != "$BRANCH" ]]; then
      OK=false
      ERROR="worktree path is already registered on branch '$EXISTING_BRANCH', not requested branch '$BRANCH': $RESOLVED_WORKTREE_PATH"
    fi
  elif [[ -e "$RESOLVED_WORKTREE_PATH" ]]; then
    OK=false
    ERROR="target directory exists but is not registered as a git worktree: $RESOLVED_WORKTREE_PATH"
  fi

  if [[ "$OK" == "true" && "$WORKTREE_EXISTED" == "false" && "$DRY_RUN" == "false" ]]; then
    if ! git fetch "$REMOTE" --quiet; then
      OK=false
      ERROR="git fetch $REMOTE failed"
    fi
  fi

  if [[ "$OK" == "true" ]] && ! git rev-parse --verify "$BASE^{commit}" >/dev/null 2>&1; then
    OK=false
    ERROR="base ref does not resolve to a commit: $BASE"
  fi

  if [[ "$OK" == "true" && "$WORKTREE_EXISTED" == "false" && "$DRY_RUN" == "false" ]]; then
    DEST_PARENT="$(dirname "$RESOLVED_WORKTREE_PATH")"
    mkdir -p "$DEST_PARENT"

    BRANCH_EXISTS=false
    if git show-ref --verify --quiet "refs/heads/$BRANCH" 2>/dev/null; then
      BRANCH_EXISTS=true
    fi

    if [[ "$BRANCH_EXISTS" == "true" ]]; then
      if git worktree add "$RESOLVED_WORKTREE_PATH" "$BRANCH"; then
        WORKTREE_CREATED=true
      else
        OK=false
        ERROR="git worktree add failed"
      fi
    else
      if git worktree add -b "$BRANCH" "$RESOLVED_WORKTREE_PATH" "$BASE"; then
        WORKTREE_CREATED=true
        BRANCH_CREATED=true
      else
        OK=false
        ERROR="git worktree add -b failed"
      fi
    fi
  fi
fi

cat <<EOF
{
  "ok": $(bool_json "$OK"),
  "error": "$(json_escape "$ERROR")",
  "repoRoot": "$(json_escape "$(normalize_slashes "$RESOLVED_REPO_ROOT")")",
  "worktreePath": "$(json_escape "$(normalize_slashes "$RESOLVED_WORKTREE_PATH")")",
  "feature": "$(json_escape "$FEATURE")",
  "featureSlug": "$(json_escape "$FEATURE_SLUG")",
  "branch": "$(json_escape "$BRANCH")",
  "base": "$(json_escape "$BASE")",
  "branchCreated": $(bool_json "$BRANCH_CREATED"),
  "worktreeCreated": $(bool_json "$WORKTREE_CREATED"),
  "worktreeExisted": $(bool_json "$WORKTREE_EXISTED"),
  "dryRun": $(bool_json "$DRY_RUN")
}
EOF

if [[ "$OK" != "true" ]]; then
  exit 1
fi
