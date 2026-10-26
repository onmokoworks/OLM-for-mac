#!/bin/sh
set -eu
export TMPDIR="$PWD/orchestra/state/N03-distancegradation-bilateral-refusals"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
worker=/Users/onmk/.cache/olm-emu/worker-F54b/aex-guest-worker
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" orchestra/reports/N03-evidence/capture.py > "$TMPDIR/capture-final.log" 2>&1
"$py" orchestra/reports/N03-evidence/zero_trace.py > "$TMPDIR/zero-trace.log" 2>&1
"$py" orchestra/reports/N03-evidence/public_dispatch.py > "$TMPDIR/public-dispatch.log" 2>&1
"$py" orchestra/reports/N03-evidence/leaf_trace.py > "$TMPDIR/leaf.log" 2>&1
"$py" orchestra/reports/N03-evidence/stages.py > "$TMPDIR/stages.log" 2>&1
"$py" orchestra/reports/N03-evidence/bilateral_probe.py > "$TMPDIR/bilateral.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --worker "$worker" --jobs 1 --seed 1 --n 300 --shrink-attempts 0 --budget-minutes 90 --scratch "$TMPDIR/default" --report "$TMPDIR/default.json" --corpus "$TMPDIR/default-corpus" > "$TMPDIR/default.log" 2>&1
python3 orchestra/reports/N03-evidence/default_baseline.py > "$TMPDIR/default-baseline.log" 2>&1
python3 orchestra/reports/N03-evidence/replay.py > "$TMPDIR/replay.log" 2>&1
"$py" orchestra/reports/N03-evidence/pf16_witness.py > "$TMPDIR/pf16-final.log" 2>&1
"$py" orchestra/reports/N03-evidence/pf16_input.py > "$TMPDIR/pf16-input.log" 2>&1
python3 tools/perf/ref_vs_fast.py --plugin olmdistancegradation --jobs 1 --scratch "$TMPDIR/ref-vs-fast" > "$TMPDIR/ref-vs-fast.log" 2>&1
