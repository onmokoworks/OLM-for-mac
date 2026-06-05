#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIGURATION="${CONFIGURATION:-Debug}"

"$ROOT/scripts/setup_ae_sdk_links.sh" >/dev/null

plugins=(
  ColorKeep
  OLMBlur
  OLMColorKey
  OLMDirectionalBlur
  OLMRadialBlur
  OLMKiraKira
  OLMToonDilate
  OLMDistanceGradation
  OLMSmoother
  OLMSmoother2
)

for plugin in "${plugins[@]}"; do
  project="$ROOT/mac/$plugin/Mac/$plugin.xcodeproj"
  binary="$ROOT/mac/$plugin/Mac/build/$CONFIGURATION/$plugin.plugin/Contents/MacOS/$plugin"

  if [[ ! -d "$project" ]]; then
    echo "[MISS] $plugin project: $project" >&2
    exit 1
  fi

  echo "=== build $plugin ($CONFIGURATION) ==="
  xcodebuild -project "$project" -configuration "$CONFIGURATION" build

  if [[ ! -f "$binary" ]]; then
    echo "[MISS] $plugin binary: $binary" >&2
    exit 1
  fi

  file "$binary"
  if ! file "$binary" | grep -q 'arm64'; then
    echo "[FAIL] $plugin binary is missing arm64 slice" >&2
    exit 1
  fi
  if ! file "$binary" | grep -q 'x86_64'; then
    echo "[FAIL] $plugin binary is missing x86_64 slice" >&2
    exit 1
  fi

  codesign --verify "$ROOT/mac/$plugin/Mac/build/$CONFIGURATION/$plugin.plugin"
done

echo "all mac plugin builds verified ($CONFIGURATION)"
