#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIGURATION="Debug"
OUTPUT=""
BUILD_MAC=0

usage() {
  cat <<'EOF'
Usage: scripts/package_olm_handoff.sh [--output /tmp/olm_port_handoff.zip] [--configuration Debug] [--build-mac]

Create one clean handoff zip containing:
- pending Windows reference-render request zip
- macOS AE plug-in package zip
- README with return/import/verification commands

By default this reuses current verified Mac build products. Pass --build-mac to
rebuild all macOS plug-ins before packaging.
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
    --build-mac)
      BUILD_MAC=1
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

if [[ -z "$OUTPUT" ]]; then
  stamp="$(date +%Y%m%d)"
  OUTPUT="/tmp/olm_port_handoff_${stamp}.zip"
fi
OUTPUT="$(cd "$(dirname "$OUTPUT")" && pwd)/$(basename "$OUTPUT")"

stage_parent="$(mktemp -d "${TMPDIR:-/tmp}/olm_port_handoff.XXXXXX")"
trap 'rm -rf "$stage_parent"' EXIT
stage="$stage_parent/OLM_Port_Handoff"
mkdir -p "$stage"

reference_zip="$stage/olm_reference_requests_pending.zip"
mac_zip="$stage/olm_mac_plugins_${CONFIGURATION}_clean.zip"

python3 "$ROOT/refs/scripts/package_reference_requests.py" \
  --pending \
  --output "$reference_zip"

mac_args=(--configuration "$CONFIGURATION" --output "$mac_zip")
if [[ "$BUILD_MAC" -eq 0 ]]; then
  mac_args+=(--skip-build)
fi
"$ROOT/scripts/package_mac_plugins.sh" "${mac_args[@]}"

cat >"$stage/README.md" <<EOF
# OLM Port Handoff

Created from:
\`$ROOT\`

## 1. Windows reference requests

Send or unpack:

\`olm_reference_requests_pending.zip\`

On the Windows AE machine, render the requests inside that zip and return the
result zip/folder to the Mac porting workspace.

Mac-side import and verification after the returned Windows refs arrive:

\`\`\`sh
python3 refs/scripts/import_and_check_win_reference.py path/to/returned_reference.zip --quick
\`\`\`

If a request remains pending after import:

\`\`\`sh
python3 refs/scripts/check_reference_request_status.py
\`\`\`

## 2. macOS AE host validation

Send or unpack:

\`olm_mac_plugins_${CONFIGURATION}_clean.zip\`

Install the packaged \`*.plugin\` bundles into:

\`\`\`
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
\`\`\`

Then restart After Effects and use the included checklist/template. For pixel
validation, use the request zips under \`AE_PIXEL_VALIDATION/\` inside the Mac
plug-in package and return the rendered PNGs.

Mac-side pixel verification examples:

\`\`\`sh
python3 scripts/verify_ae_pixel_validation_result.py path/to/olmblur_request.zip path/to/returned_pngs_or_zip
python3 scripts/verify_ae_pixel_validation_result.py path/to/olmcolorkey_request.zip path/to/returned_pngs_or_zip
python3 scripts/verify_ae_pixel_validation_result.py path/to/olmtoondilate_request.zip path/to/returned_pngs_or_zip
\`\`\`

## Notes

- Treat \`ADBE Force CPU GPU\` / hidden GPU Rendering as reference-only metadata.
- Record AE Project Settings renderer / \`project_gpu_accel_type\` separately.
- Do not guess missing render-path facts; return logs/screenshots for failures.
EOF

cat >"$stage/manifest.json" <<EOF
{
  "kind": "olm_port_handoff_package",
  "configuration": "$CONFIGURATION",
  "source_root": "$ROOT",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "reference_requests_zip": "olm_reference_requests_pending.zip",
  "mac_plugins_zip": "olm_mac_plugins_${CONFIGURATION}_clean.zip",
  "mac_build_rebuilt": $([[ "$BUILD_MAC" -eq 1 ]] && echo true || echo false)
}
EOF

python3 "$ROOT/scripts/zip_clean.py" "$stage" "$OUTPUT"
python3 "$ROOT/scripts/verify_olm_handoff_package.py" "$OUTPUT"

echo "wrote $OUTPUT"
echo "included:"
echo "- $reference_zip"
echo "- $mac_zip"
