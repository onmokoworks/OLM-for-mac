#!/bin/sh
set -eu
export TMPDIR="$PWD/orchestra/state/N02-olmdistancegradation-nightly-20261025"
mkdir -p "$TMPDIR"
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdistancegradation --jobs 1  --replay tests/fuzz_corpus/olmdistancegradation_N02/default --scratch "$TMPDIR/final-default" --report "$TMPDIR/final-default.json" > "$TMPDIR/final-default.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --jobs 1 --geometry realistic --replay tests/fuzz_corpus/olmdistancegradation_N02/realistic-v1 --scratch "$TMPDIR/final-realistic-v1" --report "$TMPDIR/final-realistic-v1.json" > "$TMPDIR/final-realistic-v1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --jobs 1 --geometry realistic-v2 --replay tests/fuzz_corpus/olmdistancegradation_N02/realistic-v2 --scratch "$TMPDIR/final-realistic-v2" --report "$TMPDIR/final-realistic-v2.json" > "$TMPDIR/final-realistic-v2.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --jobs 1 --geometry realistic --size-sampler odd-even-v1 --max-size 1920 --size-max-height 1080 --replay tests/fuzz_corpus/olmdistancegradation_N02/odd-even-v1 --scratch "$TMPDIR/final-odd-even-v1" --report "$TMPDIR/final-odd-even-v1.json" > "$TMPDIR/final-odd-even-v1.log" 2>&1
