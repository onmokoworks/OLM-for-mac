#!/bin/sh
# Serial campaigns: --jobs is an upper bound, never an oversubscription target.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
exec "${PYTHON:-python3}" "$HERE/nightly_summary.py" --run "$@"
