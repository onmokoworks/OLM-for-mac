#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
export TMPDIR="$PWD/orchestra/state/P03b-nonfinite-hdr-admission"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
export OLM_FUZZ_TEST_SCRATCH="$TMPDIR"
mkdir -p "$TMPDIR"
e=orchestra/reports/P03b-evidence
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" "$e/leaves.py" > "$TMPDIR/leaves.json" 2> "$TMPDIR/leaves.log"
"$py" "$e/dg_conversion.py" > "$TMPDIR/dg-conversion.json" 2> "$TMPDIR/dg-conversion.log"
PYTHONPATH=tools/fuzz python3 -m unittest test_sizes test_geometry test_framework test_route_oracles > "$TMPDIR/units-after.log" 2>&1
if [ "$#" -eq 0 ]; then set -- olmdirectionalblur olmdistancegradation olmkirakira radialblur; fi
for name in "$@"; do
 case "$name" in
  olmdirectionalblur) short=directional; test_name=olmdirectionalblur ;;
  olmdistancegradation) short=dg; test_name=olmdistancegradation ;;
  olmkirakira) short=kira; test_name=olmkirakira ;;
  radialblur) short=radial; test_name=olmradialblur ;;
 esac
 # These discovery suites have recorded historical failures; retain the log.
 python3 -m unittest discover -s tests -p "test_${test_name}_*.py" > "$TMPDIR/$short-units-after.log" 2>&1 || true
 python3 "$e/probe.py" --label final --plugin "$name" > "$TMPDIR/final-$name.log" 2>&1
 if [ "$name" = olmdirectionalblur ]; then
  python3 "$e/directional_matrix.py" > "$TMPDIR/directional-matrix.log" 2>&1
 else
  python3 "$e/matrix.py" "$name" > "$TMPDIR/matrix-$name.log" 2>&1
 fi
 python3 tools/fuzz/run.py --plugin "$name" --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$TMPDIR/verify-default-$name" --corpus "$TMPDIR/verify-corpus-$name" --report "$TMPDIR/$short-default-after.json" > "$TMPDIR/$short-default-after.log" 2>&1
 python3 "$e/sweep.py" "$name" > "$TMPDIR/sweep-$name.log" 2>&1
 python3 "$e/replay.py" "$name" > "$TMPDIR/replay-$name.log" 2>&1
done
python3 "$e/summarize.py"
git diff --check
