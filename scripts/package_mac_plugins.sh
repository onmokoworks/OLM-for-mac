#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIGURATION="Debug"
OUTPUT=""
SKIP_BUILD=0

usage() {
  cat <<'EOF'
Usage: scripts/package_mac_plugins.sh [--configuration Debug] [--output ./OLM_for_Mac.zip] [--skip-build]

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
  OUTPUT="$PWD/OLM_for_Mac_${CONFIGURATION}_${stamp}.zip"
fi
mkdir -p "$(dirname "$OUTPUT")"
OUTPUT="$(cd "$(dirname "$OUTPUT")" && pwd)/$(basename "$OUTPUT")"

if [[ "$SKIP_BUILD" -eq 0 ]]; then
  CONFIGURATION="$CONFIGURATION" "$ROOT/scripts/build_all_mac_plugins.sh"
fi

package_name="OLM_for_Mac"
stage_parent="$(mktemp -d "${TMPDIR:-/tmp}/olm_mac_plugins_pkg.XXXXXX")"
trap 'rm -rf "$stage_parent"' EXIT
stage="$stage_parent/$package_name"
mkdir -p "$stage"

manifest="$stage_parent/manifest.json"
cp "$ROOT/docs/PACKAGE_README_JA.md" "$stage/README.md"
cp "$ROOT/docs/PACKAGE_README_EN.md" "$stage/README.en.md"
cp "$ROOT/LICENSE" "$stage/LICENSE"

git_commit="$(git -C "$ROOT" rev-parse HEAD)"
if [[ -n "$(git -C "$ROOT" status --porcelain)" ]]; then
  git_dirty=true
else
  git_dirty=false
fi
xcode_version_output="$(xcodebuild -version)"
xcode_version="${xcode_version_output%%$'\n'*}"
sdk_version="$(xcrun --sdk macosx --show-sdk-version)"

{
  echo "{"
  echo "  \"kind\": \"olm_mac_plugin_package\","
  echo "  \"configuration\": \"$CONFIGURATION\","
  echo "  \"git_commit\": \"$git_commit\","
  echo "  \"git_dirty\": $git_dirty,"
  echo "  \"xcode_version\": \"$xcode_version\","
  echo "  \"sdk_version\": \"$sdk_version\","
  # Do not publish the packager machine's absolute checkout path.
  echo "  \"source_root\": \"OLM-for-mac repository\","
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
  archs="$(lipo -archs "$binary")"
  if [[ " $archs " != *" arm64 "* || " $archs " != *" x86_64 "* || "$(wc -w <<<"$archs" | tr -d ' ')" != 2 ]]; then
    echo "[FAIL] $plugin binary architectures are not exactly arm64+x86_64: $archs" >&2
    exit 1
  fi
  minos_arm64="$(xcrun vtool -show-build -arch arm64 "$binary" | awk '/minos/ && !found {print $2; found=1}')"
  minos_x86_64="$(xcrun vtool -show-build -arch x86_64 "$binary" | awk '/minos/ && !found {print $2; found=1}')"
  signing_detail="$(codesign -d --verbose=4 "$bundle" 2>&1)"
  if grep -q '^Signature=adhoc$' <<<"$signing_detail"; then
    signing_kind="adhoc"
  elif grep -q '^Authority=Developer ID Application:' <<<"$signing_detail"; then
    signing_kind="developer-id-application"
  else
    echo "[FAIL] $plugin has an unsupported signing identity" >&2
    exit 1
  fi
  codesign --verify --deep --strict "$bundle"

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
    echo "      \"architectures\": [\"arm64\", \"x86_64\"],"
    echo "      \"minimum_macos\": {\"arm64\": \"$minos_arm64\", \"x86_64\": \"$minos_x86_64\"},"
    echo "      \"signing_kind\": \"$signing_kind\""
    echo "    }$comma"
  } >>"$manifest"
done

{
  echo "  ]"
  echo "}"
} >>"$manifest"

mkdir -p "$(dirname "$OUTPUT")"
python3 "$ROOT/scripts/zip_clean.py" "$stage" "$OUTPUT"

cp "$manifest" "$OUTPUT.manifest.json"
python3 "$ROOT/scripts/verify_mac_plugin_package.py" "$OUTPUT"

echo "wrote $OUTPUT"
echo "packaged ${#plugins[@]} plug-ins (${CONFIGURATION})"
