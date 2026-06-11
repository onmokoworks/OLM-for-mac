#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEFAULT_EXAMPLES_DIR="$HOME/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples"
EXAMPLES_DIR="${AE_SDK_EXAMPLES_DIR:-$DEFAULT_EXAMPLES_DIR}"

if [[ ! -d "$EXAMPLES_DIR/Headers" || ! -d "$EXAMPLES_DIR/Util" || ! -d "$EXAMPLES_DIR/Resources" ]]; then
  cat >&2 <<EOF
AE SDK Examples directory not found or incomplete:
  $EXAMPLES_DIR

Set AE_SDK_EXAMPLES_DIR to the After Effects SDK Examples directory that
contains Headers, Util, and Resources.
EOF
  exit 1
fi

for name in Headers Util Resources; do
  target="$EXAMPLES_DIR/$name"
  link="$ROOT_DIR/$name"
  if [[ -e "$link" || -L "$link" ]]; then
    if [[ -L "$link" && "$(readlink "$link")" == "$target" ]]; then
      continue
    fi
    echo "Refusing to replace existing $link" >&2
    exit 1
  fi
  ln -s "$target" "$link"
done

echo "AE SDK links are ready:"
ls -l "$ROOT_DIR/Headers" "$ROOT_DIR/Util" "$ROOT_DIR/Resources"
