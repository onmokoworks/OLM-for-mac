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
validation_notes="$stage/AE_VALIDATION_CHECKLIST.txt"
validation_template="$stage/AE_VALIDATION_RESULT.template.json"
pixel_validation_dir="$stage/AE_PIXEL_VALIDATION"

pixel_validation_presets=(
  "OLMBlur:olmblur:ae_pixel_olmblur_20260606:olmblur_request.zip"
  "OLMColorKey:olmcolorkey:ae_pixel_olmcolorkey_20260606:olmcolorkey_request.zip"
  "OLMToonDilate:olmtoondilate:ae_pixel_olmtoondilate_20260606:olmtoondilate_request.zip"
)

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

cat >"$validation_notes" <<'EOF'
OLM macOS AE host validation checklist

Purpose:
Confirm that the packaged macOS .plugin bundles load in After Effects and can be
used for real AE-host render checks. The current Mac-side repository can verify
CLI algorithms and bundle builds, but it cannot prove final AE host behavior
without a real AE install.

Environment to record:
- macOS version
- Apple Silicon or Intel
- After Effects version, for example 25.2x131
- Project Settings > Video Rendering and Effects renderer name
- Whether the test was run from a clean AE launch after copying the plug-ins

Install:
1. Quit After Effects.
2. Copy all *.plugin bundles from this package into:
   ~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
3. Restart After Effects.
4. Confirm the effects appear in AE's Effect menu or can be applied to a layer.

Minimum load check:
- ColorKeep
- OLM Blur
- OLM Color Key
- OLM Directional Blur
- OLM RadialBlur
- OLM OLM Kira Kira
- OLM Toon Dilate
- OLM Distance Gradation
- OLM Smoother
- OLM Smoother v2

Return to the Mac-side porting workspace:
- AE version and renderer/project_gpu_accel_type if available
- For each plug-in: loaded yes/no, applied yes/no, render succeeded yes/no
- Any AE crash, missing effect, parameter UI issue, or render error text
- For the first pixel validation pass, use the request zips in:
  AE_PIXEL_VALIDATION/
  They contain input PNGs, Windows expected PNGs, thresholds, and a result
  template. Return the rendered PNGs as a zip or folder preserving frame names
  such as case_0001.png.
- Prefer filling AE_VALIDATION_RESULT.template.json and return it with any PNGs
  or error screenshots/logs.

Important:
Do not use the hidden Compositing Options > GPU Rendering / ADBE Force CPU GPU
value as proof that a render used the GPU or CPU path. Record it as a reference
field only; use Project Settings renderer/project_gpu_accel_type for path
context.
EOF

cat >"$validation_template" <<EOF
{
  "kind": "olm_ae_host_validation_result",
  "package_configuration": "$CONFIGURATION",
  "ae_version": "",
  "macos_version": "",
  "machine": "",
  "project_gpu_accel_type": {
    "current_name": "",
    "raw": null
  },
  "clean_ae_launch_after_install": null,
  "install_path": "~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/",
  "notes": "",
  "plugins": [
EOF

for idx in "${!plugins[@]}"; do
  plugin="${plugins[$idx]}"
  comma=","
  if [[ "$idx" -eq "$((${#plugins[@]} - 1))" ]]; then
    comma=""
  fi
  cat >>"$validation_template" <<EOF
    {
      "name": "$plugin",
      "loaded": null,
      "applied": null,
      "render_succeeded": null,
      "effect_menu_name": "",
      "error": "",
      "returned_artifacts": []
    }$comma
EOF
done

cat >>"$validation_template" <<'EOF'
  ]
}
EOF

mkdir -p "$pixel_validation_dir"
for entry in "${pixel_validation_presets[@]}"; do
  IFS=: read -r _plugin preset _request_id zip_name <<<"$entry"
  python3 "$ROOT/scripts/package_ae_pixel_validation_request.py" \
    --preset "$preset" \
    --output "$pixel_validation_dir/$zip_name"
done

{
  echo "{"
  echo "  \"kind\": \"olm_mac_plugin_package\","
  echo "  \"configuration\": \"$CONFIGURATION\","
  echo "  \"source_root\": \"$ROOT\","
  echo "  \"packaged_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
  echo "  \"install_notes\": \"INSTALL.txt\","
  echo "  \"validation_checklist\": \"AE_VALIDATION_CHECKLIST.txt\","
  echo "  \"validation_result_template\": \"AE_VALIDATION_RESULT.template.json\","
  echo "  \"ae_pixel_validation_requests\": ["
  for idx in "${!pixel_validation_presets[@]}"; do
    IFS=: read -r plugin _preset request_id zip_name <<<"${pixel_validation_presets[$idx]}"
    comma=","
    if [[ "$idx" -eq "$((${#pixel_validation_presets[@]} - 1))" ]]; then
      comma=""
    fi
    echo "    {"
    echo "      \"name\": \"$plugin\","
    echo "      \"request_id\": \"$request_id\","
    echo "      \"zip\": \"AE_PIXEL_VALIDATION/$zip_name\""
    echo "    }$comma"
  done
  echo "  ],"
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
python3 "$ROOT/scripts/zip_clean.py" "$stage" "$OUTPUT"

python3 "$ROOT/scripts/verify_mac_plugin_package.py" "$OUTPUT"

echo "wrote $OUTPUT"
echo "packaged ${#plugins[@]} plug-ins (${CONFIGURATION})"
