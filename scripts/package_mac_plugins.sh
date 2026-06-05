#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIGURATION="Debug"
OUTPUT=""
SKIP_BUILD=0

usage() {
  cat <<'EOF'
Usage: scripts/package_mac_plugins.sh [--configuration Debug] [--output /tmp/olm_mac_plugins.zip] [--skip-build]

Build/verify the macOS AE plug-in bundles and package them for an AE host.
By default this runs scripts/build_all_mac_plugins.sh first. Use --skip-build
only when the current build products were already verified in this session.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --configuration)
      CONFIGURATION="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

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

if [[ -z "$OUTPUT" ]]; then
  stamp="$(date +%Y%m%d)"
  OUTPUT="/tmp/olm_mac_plugins_${CONFIGURATION}_${stamp}.zip"
fi
OUTPUT="$(cd "$(dirname "$OUTPUT")" && pwd)/$(basename "$OUTPUT")"

if [[ "$SKIP_BUILD" -eq 0 ]]; then
  CONFIGURATION="$CONFIGURATION" "$ROOT/scripts/build_all_mac_plugins.sh"
fi

package_name="OLM_Mac_Plugins_${CONFIGURATION}"
stage_parent="$(mktemp -d "${TMPDIR:-/tmp}/olm_mac_plugins_pkg.XXXXXX")"
trap 'rm -rf "$stage_parent"' EXIT
stage="$stage_parent/$package_name"
mkdir -p "$stage"

manifest="$stage/manifest.json"
install_notes="$stage/INSTALL.txt"

cat >"$install_notes" <<EOF
OLM macOS AE plug-ins (${CONFIGURATION})

Install target for development:
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/

Copy the *.plugin bundles in this folder into MediaCore, then restart After Effects.
These bundles were packaged from:
$ROOT

The packaging script verifies each binary has arm64 and x86_64 slices and passes
codesign --verify before adding it to this archive.
EOF

{
  echo "{"
  echo "  \"kind\": \"olm_mac_plugin_package\","
  echo "  \"configuration\": \"$CONFIGURATION\","
  echo "  \"source_root\": \"$ROOT\","
  echo "  \"packaged_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
  echo "  \"plugins\": ["
} >"$manifest"

for idx in "${!plugins[@]}"; do
  plugin="${plugins[$idx]}"
  bundle="$ROOT/mac/$plugin/Mac/build/$CONFIGURATION/$plugin.plugin"
  binary="$bundle/Contents/MacOS/$plugin"

  if [[ ! -d "$bundle" ]]; then
    echo "[MISS] $plugin bundle: $bundle" >&2
    exit 1
  fi
  if [[ ! -f "$binary" ]]; then
    echo "[MISS] $plugin binary: $binary" >&2
    exit 1
  fi
  file_out="$(file "$binary")"
  if ! grep -q 'arm64' <<<"$file_out"; then
    echo "[FAIL] $plugin binary is missing arm64 slice" >&2
    exit 1
  fi
  if ! grep -q 'x86_64' <<<"$file_out"; then
    echo "[FAIL] $plugin binary is missing x86_64 slice" >&2
    exit 1
  fi
  codesign --verify "$bundle"

  ditto "$bundle" "$stage/$plugin.plugin"
  sha256="$(shasum -a 256 "$binary" | awk '{print $1}')"
  comma=","
  if [[ "$idx" -eq "$((${#plugins[@]} - 1))" ]]; then
    comma=""
  fi
  {
    echo "    {"
    echo "      \"name\": \"$plugin\","
    echo "      \"bundle\": \"$plugin.plugin\","
    echo "      \"binary_sha256\": \"$sha256\","
    echo "      \"architectures\": [\"arm64\", \"x86_64\"]"
    echo "    }$comma"
  } >>"$manifest"
done

{
  echo "  ]"
  echo "}"
} >>"$manifest"

mkdir -p "$(dirname "$OUTPUT")"
(cd "$stage_parent" && ditto -c -k --sequesterRsrc --keepParent "$package_name" "$OUTPUT")

echo "wrote $OUTPUT"
echo "packaged ${#plugins[@]} plug-ins (${CONFIGURATION})"
