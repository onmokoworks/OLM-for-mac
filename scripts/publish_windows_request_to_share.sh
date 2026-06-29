#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHARE_ROOT="${OLM_PR_SHARE_ROOT:-/Volumes/onmk/olm_pr}"
NEW_DIR="$SHARE_ROOT/new"
OLD_DIR="$SHARE_ROOT/old"

usage() {
  cat <<EOF
Usage: scripts/publish_windows_request_to_share.sh ZIP [ZIP...]

Publish one or more Windows handoff/request zips to the shared folder workflow:

- move existing zip files in \$SHARE_ROOT/new to \$SHARE_ROOT/old
- copy the given zip(s) into \$SHARE_ROOT/new

Defaults:
- share root: /Volumes/onmk/olm_pr

Override:
- OLM_PR_SHARE_ROOT=/path/to/share scripts/publish_windows_request_to_share.sh ...
EOF
}

if [[ $# -eq 0 ]]; then
  usage >&2
  exit 2
fi

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -d "$SHARE_ROOT" ]]; then
  echo "[FAIL] share root not available: $SHARE_ROOT" >&2
  echo "Mount the server share first, or copy from the project-local package path instead." >&2
  exit 1
fi

mkdir -p "$NEW_DIR" "$OLD_DIR"

timestamp="$(date +%Y%m%d_%H%M%S)"
shopt -s nullglob
for existing in "$NEW_DIR"/*.zip; do
  base="$(basename "$existing")"
  target="$OLD_DIR/${timestamp}__${base}"
  mv "$existing" "$target"
  echo "[INFO] archived old zip: $target"
done
shopt -u nullglob

for arg in "$@"; do
  src="$arg"
  if [[ ! -f "$src" ]]; then
    echo "[FAIL] missing zip: $src" >&2
    exit 1
  fi
  dest="$NEW_DIR/$(basename "$src")"
  cp "$src" "$dest"
  echo "[OK] published: $dest"
done

echo ""
echo "Share state:"
echo "- new: $NEW_DIR"
echo "- old: $OLD_DIR"
