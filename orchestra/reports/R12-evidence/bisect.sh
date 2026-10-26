#!/bin/bash
export TMPDIR="$PWD/orchestra/state/R12-release-gate-final"
export OLM_TEST_JOBS=1
export PYTHONDONTWRITEBYTECODE=1
rev=$(git rev-parse --short HEAD)
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3' -B scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_colorkeep_generic_beta_20260820.py > "$TMPDIR/bisect-$rev.log" 2>&1
rc=$?
echo "$rev exit=$rc"
exit "$rc"
