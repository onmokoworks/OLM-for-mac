#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: refs/scripts/setup_olmkirakira_opencv455_probe_env.sh [--venv PATH] [--python PYTHON] [--recreate]

Create or validate a temporary Python environment for OLMKiraKira OpenCV 4.5.5 probes.

Defaults:
  --venv    /tmp/olm_cv455_probe_venv
  --python  /opt/homebrew/bin/python3.12, falling back to python3

The environment is intentionally outside the repository. Use it like:

  OLM_PROBE_PYTHON=/tmp/olm_cv455_probe_venv/bin/python \
    python3 refs/scripts/smoke_olmkirakira_opencv_screenover_probe_cli.py
USAGE
}

VENV="/tmp/olm_cv455_probe_venv"
PYTHON="${PYTHON:-}"
RECREATE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --venv)
      VENV="$2"
      shift 2
      ;;
    --python)
      PYTHON="$2"
      shift 2
      ;;
    --recreate)
      RECREATE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$PYTHON" ]]; then
  if [[ -x /opt/homebrew/bin/python3.12 ]]; then
    PYTHON="/opt/homebrew/bin/python3.12"
  else
    PYTHON="$(command -v python3)"
  fi
fi

if [[ "$RECREATE" == "1" && -e "$VENV" ]]; then
  rm -rf "$VENV"
fi

if [[ ! -x "$VENV/bin/python" ]]; then
  "$PYTHON" -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip >/dev/null
"$VENV/bin/python" -m pip install --force-reinstall \
  "numpy==1.26.4" \
  "opencv-python-headless==4.5.5.64" \
  "pillow" \
  "scipy" >/dev/null

"$VENV/bin/python" - <<'PY'
import cv2
import numpy as np
import sys

if cv2.__version__ != "4.5.5":
    raise SystemExit(f"unexpected cv2 version: {cv2.__version__}")
if not np.__version__.startswith("1.26."):
    raise SystemExit(f"unexpected numpy version: {np.__version__}")
print(f"[OK] OLMKiraKira OpenCV probe env: python={sys.executable}")
print(f"[OK] cv2={cv2.__version__} numpy={np.__version__}")
PY

cat <<EOF
export OLM_PROBE_PYTHON="$VENV/bin/python"
EOF
