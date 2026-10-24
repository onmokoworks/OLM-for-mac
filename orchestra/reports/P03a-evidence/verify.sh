#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
export TMPDIR="$PWD/orchestra/state/P03a-distancegradation-pf32-downsample-ulp"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1 OLM_FUZZ_TEST_SCRATCH="$TMPDIR"
mkdir -p "$TMPDIR"
PY='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$PY" orchestra/reports/P03a-evidence/probe.py > "$TMPDIR/probe.log" 2>&1
clang++ -std=c++17 -O2 -ffp-contract=off -fno-fast-math orchestra/reports/P03a-evidence/core_probe.cpp -o "$TMPDIR/core-probe" > "$TMPDIR/core-build.log" 2>&1
"$TMPDIR/core-probe" 96 64 "$TMPDIR/core-distance.bin" < "$TMPDIR/expanded.bin"
"$PY" orchestra/reports/P03a-evidence/stage_matrix.py > "$TMPDIR/stage-matrix.log" 2>&1
"$PY" orchestra/reports/P03a-evidence/compare.py > "$TMPDIR/compare.log" 2>&1
PYTHONPATH=tools/fuzz python3 -m unittest test_sizes test_geometry test_framework test_route_oracles > "$TMPDIR/units-after.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*.py' > "$TMPDIR/plugin-units-after.log" 2>&1 || true
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$TMPDIR/candidate" --corpus "$TMPDIR/candidate-corpus" --report "$TMPDIR/candidate.json" > "$TMPDIR/candidate.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --jobs 1 --replay tests/fuzz_corpus/olmdistancegradation --scratch "$TMPDIR/replay-default" --report "$TMPDIR/replay-default.json" > "$TMPDIR/replay-default.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --geometry realistic --jobs 1 --replay tests/fuzz_corpus/olmdistancegradation_realistic_P02b --scratch "$TMPDIR/replay-P02b" --report "$TMPDIR/replay-P02b.json" > "$TMPDIR/replay-P02b.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --geometry realistic --size-sampler odd-even-v1 --max-size 1920 --jobs 1 --replay tests/fuzz_corpus/olmdistancegradation/T15b-odd-even-realistic --scratch "$TMPDIR/replay-T15b" --report "$TMPDIR/replay-T15b.json" > "$TMPDIR/replay-T15b.log" 2>&1
rm -f "$TMPDIR/core-probe"
