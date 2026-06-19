#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$HOME/Downloads"
STAMP="$(date +%Y%m%d)"

usage() {
  cat <<EOF
Usage: scripts/prepare_windows_reference_handoff.sh [--output-dir DIR] [--stamp STAMP]

Build and verify the Windows reference request zip plus the broader OLM handoff
zip, then copy both to the output directory for transfer to the Windows AE host.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir)
      OUT_DIR="$2"
      shift 2
      ;;
    --stamp)
      STAMP="$2"
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

mkdir -p "$OUT_DIR"

REQUEST_TMP="/tmp/olm_reference_requests_pending_${STAMP}.zip"
HANDOFF_TMP="/tmp/olm_port_handoff_${STAMP}_current.zip"
REQUEST_OUT="$OUT_DIR/olm_reference_requests_pending_${STAMP}.zip"
HANDOFF_OUT="$OUT_DIR/olm_port_handoff_${STAMP}_current.zip"
REQUEST_MODE="pending"

cd "$ROOT"

if python3 refs/scripts/package_reference_requests.py --pending --output "$REQUEST_TMP"; then
  REQUEST_MODE="pending"
  python3 refs/scripts/verify_reference_request_package.py "$REQUEST_TMP" --expect-pending
else
  echo "[INFO] no pending Windows reference requests; packaging all request specs as a snapshot"
  REQUEST_MODE="snapshot"
  python3 refs/scripts/package_reference_requests.py --output "$REQUEST_TMP"
  python3 refs/scripts/verify_reference_request_package.py "$REQUEST_TMP"
fi

scripts/package_olm_handoff.sh --output "$HANDOFF_TMP"
python3 scripts/verify_olm_handoff_package.py "$HANDOFF_TMP"

cp "$REQUEST_TMP" "$REQUEST_OUT"
cp "$HANDOFF_TMP" "$HANDOFF_OUT"

echo "Windows reference handoff is ready:"
echo "- request package: $REQUEST_OUT ($REQUEST_MODE)"
echo "- full handoff: $HANDOFF_OUT"
echo
python3 scripts/print_next_olm_action.py "$OUT_DIR" /tmp
