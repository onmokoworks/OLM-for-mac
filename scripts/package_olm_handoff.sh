#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIGURATION="Debug"
OUTPUT=""
BUILD_MAC=0
PIXEL_REFERENCE_PROFILE="legacy"

usage() {
  cat <<'EOF'
Usage: scripts/package_olm_handoff.sh [--output /tmp/olm_port_handoff.zip] [--configuration Debug] [--build-mac] [--pixel-reference-profile legacy|normalized-20260618]

Create one clean handoff zip containing:
- Windows reference-render request zip (pending when available, otherwise a snapshot)
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
    --pixel-reference-profile)
      PIXEL_REFERENCE_PROFILE="$2"
      shift 2
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
git_commit="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
if git -C "$ROOT" diff --quiet --ignore-submodules HEAD -- 2>/dev/null; then
  git_dirty=false
else
  git_dirty=true
fi

stage_parent="$(mktemp -d "${TMPDIR:-/tmp}/olm_port_handoff.XXXXXX")"
trap 'rm -rf "$stage_parent"' EXIT
stage="$stage_parent/OLM_Port_Handoff"
mkdir -p "$stage"

reference_zip="$stage/olm_reference_requests_pending.zip"
runtime_trace_zip="$stage/olm_runtime_trace_requests.zip"
mac_zip="$stage/olm_mac_plugins_${CONFIGURATION}_clean.zip"
next_actions_json="$stage/next_reference_actions.json"
reference_zip_mode="pending"

if python3 "$ROOT/refs/scripts/package_reference_requests.py" \
  --pending \
  --output "$reference_zip"; then
  reference_zip_mode="pending"
  python3 "$ROOT/refs/scripts/verify_reference_request_package.py" "$reference_zip" --expect-pending
else
  echo "[INFO] no pending Windows reference requests; packaging all request specs as a snapshot"
  reference_zip_mode="snapshot"
  python3 "$ROOT/refs/scripts/package_reference_requests.py" --output "$reference_zip"
  python3 "$ROOT/refs/scripts/verify_reference_request_package.py" "$reference_zip"
fi

if python3 "$ROOT/scripts/package_runtime_trace_requests.py" --output "$runtime_trace_zip"; then
  runtime_trace_mode="ready"
else
  echo "[INFO] no runtime trace actions currently required; skipping runtime trace package"
  runtime_trace_mode="none"
  rm -f "$runtime_trace_zip"
fi

mac_args=(--configuration "$CONFIGURATION" --output "$mac_zip")
mac_args+=(--pixel-reference-profile "$PIXEL_REFERENCE_PROFILE")
if [[ "$BUILD_MAC" -eq 0 ]]; then
  mac_args+=(--skip-build)
fi
"$ROOT/scripts/package_mac_plugins.sh" "${mac_args[@]}"

python3 "$ROOT/refs/scripts/next_reference_actions.py" --json >"$next_actions_json"

cat >"$stage/README.md" <<EOF
# OLM Port Handoff

Created from:
\`$ROOT\`

## 1. Windows reference requests

Send or unpack:

\`olm_reference_requests_pending.zip\`

This package mode is \`$reference_zip_mode\`. When the mode is \`pending\`, render
the requests inside that zip on the Windows AE machine and return the result
zip/folder to the Mac porting workspace. When the mode is \`snapshot\`, there
are no pending Windows references; keep the zip as a self-contained request
spec snapshot and use the local next-action router to decide between runtime
trace requests and AE host validation.

## 2. Windows runtime trace requests

Send or unpack, when present:

\`olm_runtime_trace_requests.zip\`

This package mode is \`$runtime_trace_mode\`. When the mode is \`ready\`, answer
the debugger/runtime trace requests before doing more PNG-only tuning on the
hard paths. These requests are not AE render batches; they ask for concrete
register values or exact library primitive facts, then return a small JSON/zip
that the Mac side can ingest.

Mac-side import after the returned runtime trace arrives:

\`\`\`sh
python3 scripts/intake_olm_return.py path/to/returned_runtime_trace.zip \\
  --runtime-summary-json refs/reports/runtime_trace_summary.json \\
  --runtime-summary-md refs/reports/runtime_trace_summary.md \\
  --runtime-comparison-dir refs/reports/runtime_trace_comparisons
\`\`\`

Windows-side note:

- This handoff zip does not contain the Mac OLM source worktree.
- The Windows reference request zip is self-contained as render specs, but it
  does not include a Windows AE automation runner.
- You do not need the Mac worktree to render the requests. You do need Windows
  After Effects with the original OLM Tools AEX plug-ins installed, plus an AE
  script/runner that can read the request JSON, set effect parameters, render
  PNGs, and write the return manifest.
- The commands below are Mac-side import/verification commands for after the
  returned Windows zip is copied back to this Mac repository.

Mac-side import and verification after the returned Windows refs arrive:

\`\`\`sh
python3 scripts/print_next_olm_action.py ~/Downloads /tmp
python3 scripts/list_olm_return_candidates.py ~/Downloads /tmp
python3 scripts/intake_olm_return.py path/to/returned_reference.zip --quick --dispatch-dir /tmp/olm_reference_dispatch
python3 refs/scripts/import_and_check_win_reference.py path/to/returned_reference.zip --quick --dispatch-dir /tmp/olm_reference_dispatch
python3 refs/scripts/next_reference_actions.py
python3 refs/scripts/next_reference_actions.py --json
\`\`\`

If a request remains pending after import:

\`\`\`sh
python3 refs/scripts/check_reference_request_status.py
\`\`\`

If multiple requests are covered, \`next_reference_actions.py\` prints the
priority order and the request-specific smoke to run before implementation.
It can also report \`runtime-trace\` actions after all PNG references are
covered; package and answer those trace requests before continuing PNG-only
tuning on the hard paths.
This handoff also includes \`next_reference_actions.json\`, a snapshot of the
current covered/pending dispatch payloads. Use its \`pending_actions\` entries
for read-only sub-agent stop-line audits while Windows references are still
pending, and \`next_action\` / \`covered_actions\` after imports. The import
commands above also write per-request \`SUBAGENT.md\` files under
\`/tmp/olm_reference_dispatch\`.

## 3. macOS AE host validation

Send or unpack:

\`olm_mac_plugins_${CONFIGURATION}_clean.zip\`

Install the packaged \`*.plugin\` bundles into:

\`\`\`
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
\`\`\`

Preferred local install command after copying the Mac plug-in package back into
this repository:

\`\`\`sh
scripts/install_mac_plugins_to_mediacore.sh --package path/to/olm_mac_plugins_${CONFIGURATION}_clean.zip
\`\`\`

Optional preflight duplicate check:

\`\`\`sh
scripts/install_mac_plugins_to_mediacore.sh --audit-only
\`\`\`

This backs up existing OLM bundles under MediaCore before installing, then
verifies that exactly one expected OLM bundle is installed. If installing
manually, move old OLM backup folders out of MediaCore first because After
Effects scans nested backup plug-ins and can report duplicate/version-mismatch
effects.

Then restart After Effects and use the included checklist/template. For pixel
validation, use the request zips under \`AE_PIXEL_VALIDATION/\` inside the Mac
plug-in package and return the rendered PNGs grouped by request/preset name,
for example \`olmblur/\`, \`olmcolorkey/\`, \`olmtoondilate/\`,
\`olmdistancegradation/\`, \`olmdistancegradation_extended/\`, and
\`olmdistancegradation_blur/\`.

Mac-side pixel verification examples:

\`\`\`sh
python3 scripts/intake_olm_return.py path/to/returned_ae_host.zip --require-all-pass
python3 scripts/intake_olm_return.py path/to/returned_ae_host.zip --require-all-pass --require-all-pixel-requests
python3 scripts/intake_olm_return.py path/to/returned_ae_host.zip --package $OUTPUT --require-all-pass
python3 scripts/verify_ae_host_return.py $OUTPUT path/to/returned_ae_host.zip --require-all-pass
python3 scripts/verify_ae_host_return.py $OUTPUT path/to/returned_ae_host.zip --require-all-pass --require-all-pixel-requests
python3 scripts/verify_ae_pixel_validation_result.py path/to/olmblur_request.zip path/to/returned_pngs_or_zip
python3 scripts/verify_ae_pixel_validation_result.py path/to/olmcolorkey_request.zip path/to/returned_pngs_or_zip
python3 scripts/verify_ae_pixel_validation_result.py path/to/olmtoondilate_request.zip path/to/returned_pngs_or_zip
python3 scripts/verify_ae_pixel_validation_result.py path/to/olmdistancegradation_request.zip path/to/returned_pngs_or_zip
python3 scripts/verify_ae_pixel_validation_result.py path/to/olmdistancegradation_extended_request.zip path/to/returned_pngs_or_zip
python3 scripts/verify_ae_pixel_validation_result.py path/to/olmdistancegradation_blur_request.zip path/to/returned_pngs_or_zip
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
  "git_commit": "$git_commit",
  "git_dirty": $git_dirty,
  "reference_requests_zip": "olm_reference_requests_pending.zip",
  "reference_requests_mode": "$reference_zip_mode",
  "runtime_trace_requests_zip": "$([[ -f "$runtime_trace_zip" ]] && basename "$runtime_trace_zip" || echo "")",
  "runtime_trace_requests_mode": "$runtime_trace_mode",
  "mac_plugins_zip": "olm_mac_plugins_${CONFIGURATION}_clean.zip",
  "pixel_reference_profile": "$PIXEL_REFERENCE_PROFILE",
  "next_reference_actions_json": "next_reference_actions.json",
  "mac_build_rebuilt": $([[ "$BUILD_MAC" -eq 1 ]] && echo true || echo false)
}
EOF

python3 "$ROOT/scripts/zip_clean.py" "$stage" "$OUTPUT"
python3 "$ROOT/scripts/verify_olm_handoff_package.py" "$OUTPUT"

echo "wrote $OUTPUT"
echo "included:"
echo "- $reference_zip ($reference_zip_mode)"
if [[ -f "$runtime_trace_zip" ]]; then
  echo "- $runtime_trace_zip ($runtime_trace_mode)"
fi
echo "- $mac_zip"
echo "- $next_actions_json"
