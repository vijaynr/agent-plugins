#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: skills/init-workspace/scripts/prepare-init-workspace.sh [--dry-run] [--subdir <artifact-subdir>] <feature-name-or-folder>

Creates/checks a deterministic feature workspace under .features/.

Examples:
  skills/init-workspace/scripts/prepare-init-workspace.sh my-feature
  skills/init-workspace/scripts/prepare-init-workspace.sh .features/my-feature-1234
  skills/init-workspace/scripts/prepare-init-workspace.sh --subdir threat-model "My Feature"
  skills/init-workspace/scripts/prepare-init-workspace.sh --dry-run --subdir threat-model "My Feature"

Output: JSON with featureFolder, artifactWorkspace, and existence/creation flags.
EOF
}

DRY_RUN=false
SUBDIR=""
ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --dry-run|-n) DRY_RUN=true; shift ;;
    --subdir) SUBDIR="${2:-}"; shift 2 ;;
    --subdir=*) SUBDIR="${1#--subdir=}"; shift ;;
    --root) ROOT="${2:-}"; shift 2 ;;
    --root=*) ROOT="${1#--root=}"; shift ;;
    --) shift; break ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) break ;;
  esac
done

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

INPUT="$1"

json_escape() {
  local s="$1"
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  s=${s//$'\n'/\\n}
  s=${s//$'\r'/\\r}
  s=${s//$'\t'/\\t}
  printf '%s' "$s"
}

json_array() {
  local first=true item
  printf '['
  for item in "$@"; do
    [[ "$first" == "true" ]] || printf ', '
    first=false
    printf '"%s"' "$(json_escape "$item")"
  done
  printf ']'
}

bool_json() { [[ "$1" == "true" ]] && printf 'true' || printf 'false'; }

slugify() {
  local s="$1"
  s=$(printf '%s' "$s" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//')
  [[ -n "$s" ]] && printf '%s' "$s" || printf 'feature'
}

base_slug() { printf '%s' "$1" | sed -E 's/-[0-9]+$//'; }

normalize_slashes() { printf '%s' "$1" | sed 's#\\#/#g; s#//*#/#g; s#/$##'; }

ROOT=$(normalize_slashes "$ROOT")
FEATURES_BASE=".features"
if [[ -n "$ROOT" ]]; then
  FEATURES_BASE="$ROOT/.features"
fi

find_similar_feature_folders() {
  local wanted="$1" wanted_base candidate name slug slug_base
  wanted_base=$(base_slug "$wanted")
  [[ -d "$FEATURES_BASE" ]] || return 0
  while IFS= read -r candidate; do
    name=${candidate#$FEATURES_BASE/}
    slug=$(slugify "$name")
    slug_base=$(base_slug "$slug")
    if [[ "$slug" == "$wanted" || "$slug_base" == "$wanted_base" || "$slug" == "$wanted"-* || "$wanted" == "$slug"-* || "$slug_base" == "$wanted" || "$wanted_base" == "$slug" ]]; then
      printf '%s\n' "$candidate"
    fi
  done < <(find "$FEATURES_BASE" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort)
}

INPUT_NORM=$(normalize_slashes "$INPUT")
SUBDIR=$(normalize_slashes "$SUBDIR")
SUBDIR=${SUBDIR#/}

MATCHED_SIMILAR=false
AMBIGUOUS=false
SIMILAR_FOLDERS=()

if [[ "$INPUT_NORM" == .features/* || "$INPUT_NORM" == */.features/* || "$INPUT_NORM" == /* || "$INPUT_NORM" == ./* || "$INPUT_NORM" == ../* ]]; then
  FEATURE_FOLDER="$INPUT_NORM"
  if [[ ! -d "$FEATURE_FOLDER" ]]; then
    mapfile -t SIMILAR_FOLDERS < <(find_similar_feature_folders "$(slugify "$(basename "$FEATURE_FOLDER")")")
    if [[ ${#SIMILAR_FOLDERS[@]} -eq 1 ]]; then
      FEATURE_FOLDER="${SIMILAR_FOLDERS[0]}"
      MATCHED_SIMILAR=true
    elif [[ ${#SIMILAR_FOLDERS[@]} -gt 1 ]]; then
      AMBIGUOUS=true
    fi
  fi
else
  INPUT_SLUG=$(slugify "$INPUT_NORM")
  if [[ -d "$FEATURES_BASE/$INPUT_NORM" ]]; then
    FEATURE_FOLDER="$FEATURES_BASE/$INPUT_NORM"
  elif [[ -d "$FEATURES_BASE/$INPUT_SLUG" ]]; then
    FEATURE_FOLDER="$FEATURES_BASE/$INPUT_SLUG"
  else
    mapfile -t SIMILAR_FOLDERS < <(find_similar_feature_folders "$INPUT_SLUG")
    if [[ ${#SIMILAR_FOLDERS[@]} -eq 1 ]]; then
      FEATURE_FOLDER="${SIMILAR_FOLDERS[0]}"
      MATCHED_SIMILAR=true
    elif [[ ${#SIMILAR_FOLDERS[@]} -gt 1 ]]; then
      FEATURE_FOLDER="$FEATURES_BASE/$INPUT_SLUG"
      AMBIGUOUS=true
    else
      FEATURE_FOLDER="$FEATURES_BASE/$INPUT_SLUG"
    fi
  fi
fi

# If caller passed the artifact workspace path, trim the requested subdir.
if [[ -n "$SUBDIR" && "$FEATURE_FOLDER" == */"$SUBDIR" ]]; then
  FEATURE_FOLDER="${FEATURE_FOLDER%/$SUBDIR}"
fi

if [[ -n "$SUBDIR" ]]; then
  ARTIFACT_WORKSPACE="$FEATURE_FOLDER/$SUBDIR"
else
  ARTIFACT_WORKSPACE="$FEATURE_FOLDER"
fi

FEATURE_EXISTED=false
WORKSPACE_EXISTED=false
[[ -d "$FEATURE_FOLDER" ]] && FEATURE_EXISTED=true
[[ -d "$ARTIFACT_WORKSPACE" ]] && WORKSPACE_EXISTED=true

CREATED_FEATURE=false
CREATED_WORKSPACE=false
OK=true
ERROR=""

if [[ "$AMBIGUOUS" == "true" ]]; then
  OK=false
  ERROR="multiple similar feature workspaces found; choose one and rerun with its exact path"
fi

STATUS_CREATED=false
STATUS_PATH="$FEATURE_FOLDER/status.json"

if [[ "$OK" == "true" && "$DRY_RUN" != "true" ]]; then
  SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
  TARGET_ROOT="."
  if [[ -n "$ROOT" ]]; then
    TARGET_ROOT="$ROOT"
  fi
  bash "$SCRIPT_DIR/ensure-aidd-gitignore.sh" "$TARGET_ROOT" >/dev/null
  if [[ ! -d "$FEATURE_FOLDER" ]]; then
    mkdir -p "$FEATURE_FOLDER" || { OK=false; ERROR="failed to create feature folder"; }
    [[ "$OK" == "true" ]] && CREATED_FEATURE=true
  fi
  if [[ "$OK" == "true" && ! -d "$ARTIFACT_WORKSPACE" ]]; then
    mkdir -p "$ARTIFACT_WORKSPACE" || { OK=false; ERROR="failed to create artifact workspace"; }
    [[ "$OK" == "true" ]] && CREATED_WORKSPACE=true
  fi
  if [[ "$OK" == "true" && ! -f "$STATUS_PATH" ]]; then
    NOW_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    FEATURE_NAME="${FEATURE_FOLDER##*/.features/}"
    FEATURE_NAME="${FEATURE_NAME##.features/}"
    cat > "$STATUS_PATH" <<STATUS_EOF || { OK=false; ERROR="failed to create status.json"; }
{
  "schemaVersion": 1,
  "feature": "$(json_escape "$FEATURE_NAME")",
  "featureFolder": "$(json_escape "$FEATURE_FOLDER")",
  "currentPhase": "workspace",
  "status": "initialized",
  "createdAt": "$NOW_UTC",
  "updatedAt": "$NOW_UTC",
  "phases": {
    "workspace": { "status": "done", "artifact": ".", "updatedAt": "$NOW_UTC" },
    "spec": { "status": "pending", "artifact": "SPEC.md" },
    "research": { "status": "optional", "artifact": "SPEC.md" },
    "design": { "status": "pending", "artifact": "SPEC.md|DESIGN.md" },
    "plan": { "status": "pending", "artifact": "tasks/PLAN.md" },
    "implement": { "status": "pending", "artifact": "tasks/TODO.md" },
    "review": { "status": "pending", "artifact": "tasks/TODO.md" },
    "refine": { "status": "optional", "artifact": "SPEC.md|tasks/PLAN.md" },
    "ship": { "status": "pending", "artifact": "merge-request" }
  },
  "blockers": [],
  "nextRecommendedPhase": "spec",
  "artifactHashes": {},
  "git": {
    "lastVerifiedCommit": null,
    "latestSddCommits": []
  },
  "evidence": {
    "verification": { "status": "pending", "timestamp": null, "summary": null }
  },
  "history": [
    { "phase": "workspace", "status": "done", "timestamp": "$NOW_UTC", "summary": "Feature workspace initialized." }
  ]
}
STATUS_EOF
    [[ "$OK" == "true" ]] && STATUS_CREATED=true
  fi
fi

cat <<EOF
{
  "ok": $(bool_json "$OK"),
  "error": "$(json_escape "$ERROR")",
  "root": "$(json_escape "${ROOT:-.}")",
  "featureInput": "$(json_escape "$INPUT")",
  "featureFolder": "$(json_escape "$FEATURE_FOLDER")",
  "featureWorkspace": "$(json_escape "$FEATURE_FOLDER")",
  "artifactSubdir": "$(json_escape "$SUBDIR")",
  "artifactWorkspace": "$(json_escape "$ARTIFACT_WORKSPACE")",
  "featureFolderExisted": $(bool_json "$FEATURE_EXISTED"),
  "workspaceExisted": $(bool_json "$WORKSPACE_EXISTED"),
  "createdFeatureFolder": $(bool_json "$CREATED_FEATURE"),
  "createdWorkspace": $(bool_json "$CREATED_WORKSPACE"),
  "statusPath": "$(json_escape "$STATUS_PATH")",
  "statusCreated": $(bool_json "$STATUS_CREATED"),
  "matchedSimilarFeatureFolder": $(bool_json "$MATCHED_SIMILAR"),
  "ambiguous": $(bool_json "$AMBIGUOUS"),
  "similarFeatureFolders": $(json_array "${SIMILAR_FOLDERS[@]}"),
  "dryRun": $(bool_json "$DRY_RUN")
}
EOF

[[ "$OK" == "true" ]] || exit 1
