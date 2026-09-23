#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/publish-opinions.sh SOURCE_DIR [--repo OWNER/REPO] [--branch BRANCH] [--dry-run]

Publishes top-level *.json files from SOURCE_DIR into opinions/ on the target
GitHub repository using the GitHub git data API. It does not recurse into
subdirectories and it never writes outside opinions/.

Required tools: gh, jq
USAGE
}

repo="${GH_REPO:-moiz-qureshi/market-briefs}"
branch="${GH_BRANCH:-main}"
dry_run=0
source_dir=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --branch)
      branch="${2:-}"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$source_dir" ]]; then
        echo "Only one SOURCE_DIR is allowed." >&2
        usage >&2
        exit 2
      fi
      source_dir="$1"
      shift
      ;;
  esac
done

if [[ -z "$source_dir" || -z "$repo" || -z "$branch" ]]; then
  usage >&2
  exit 2
fi

if [[ ! -d "$source_dir" ]]; then
  echo "Source directory does not exist: $source_dir" >&2
  exit 1
fi

command -v gh >/dev/null 2>&1 || { echo "Missing required tool: gh" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "Missing required tool: jq" >&2; exit 1; }

files=()
for file in "$source_dir"/*.json; do
  [[ -e "$file" ]] || continue
  [[ -f "$file" ]] || continue
  files+=("$file")
done

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No top-level *.json files found in $source_dir" >&2
  exit 1
fi

for file in "${files[@]}"; do
  name="$(basename "$file")"
  if [[ "$name" == *"/"* || "$name" != *.json ]]; then
    echo "Refusing unsafe filename: $name" >&2
    exit 1
  fi
  jq empty "$file"
done

echo "Publishing ${#files[@]} opinion file(s) to $repo:$branch/opinions/"
for file in "${files[@]}"; do
  echo "  opinions/$(basename "$file")"
done

if [[ "$dry_run" -eq 1 ]]; then
  echo "Dry run complete; no GitHub writes performed."
  exit 0
fi

base_commit="$(gh api "repos/$repo/git/ref/heads/$branch" --jq '.object.sha')"
base_tree="$(gh api "repos/$repo/git/commits/$base_commit" --jq '.tree.sha')"
tree_json="$(mktemp)"
jq -n '[]' > "$tree_json"

for file in "${files[@]}"; do
  name="$(basename "$file")"
  blob_payload="$(mktemp)"
  jq -n --rawfile content "$file" '{content: $content, encoding: "utf-8"}' > "$blob_payload"
  blob_sha="$(gh api -X POST "repos/$repo/git/blobs" --input "$blob_payload" --jq '.sha')"
  jq \
    --arg path "opinions/$name" \
    --arg sha "$blob_sha" \
    '. + [{path: $path, mode: "100644", type: "blob", sha: $sha}]' \
    "$tree_json" > "$tree_json.next"
  mv "$tree_json.next" "$tree_json"
done

tree_payload="$(mktemp)"
jq -n \
  --arg base_tree "$base_tree" \
  --slurpfile tree "$tree_json" \
  '{base_tree: $base_tree, tree: $tree[0]}' > "$tree_payload"
new_tree="$(gh api -X POST "repos/$repo/git/trees" --input "$tree_payload" --jq '.sha')"

commit_payload="$(mktemp)"
jq -n \
  --arg message "Publish opinion files" \
  --arg tree "$new_tree" \
  --arg parent "$base_commit" \
  '{message: $message, tree: $tree, parents: [$parent]}' > "$commit_payload"
new_commit="$(gh api -X POST "repos/$repo/git/commits" --input "$commit_payload" --jq '.sha')"

ref_payload="$(mktemp)"
jq -n --arg sha "$new_commit" '{sha: $sha}' > "$ref_payload"
gh api -X PATCH "repos/$repo/git/refs/heads/$branch" --input "$ref_payload" --jq '.object.sha'

echo "Published commit: $new_commit"
