#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
s="$PWD/orchestra/state/P01c-colorkey-downsample"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
export OLM_FUZZ_TEST_SCRATCH="$s/framework-tests"
unset OLM_COLOR_TRIAGE_BYPASS OLM_COLOR_TRIAGE_SANITIZE OLM_F52_DOWNSAMPLE
for seed in 1 20261024; do
  python3 tools/fuzz/verify_colorkey_downsample_P01c.py --seed "$seed" --n 100 > "$s/seed$seed-final.log" 2>&1
  tail -1 "$s/seed$seed-final.log"
done
python3 tools/fuzz/witness_colorkey_downsample_P01c.py > "$s/witnesses-final.log" 2>&1
tail -1 "$s/witnesses-final.log"
python3 tools/fuzz/run.py --plugin olmcolorkey --n 2000 --seed 1 --jobs 1 --shrink-attempts 0 \
  --scratch "$s/default-final" --report "$s/default-final.json" --corpus "$s/default-final-corpus" > "$s/default-final.log" 2>&1
python3 tools/fuzz/regression_colorkey_downsample_P01c.py > "$s/regression-final.log" 2>&1
python3 tools/fuzz/run.py --plugin olmcolorkey --replay tests/fuzz_corpus/olmcolorkey --jobs 1 \
  --scratch "$s/replay" --report "$s/replay.json" > "$s/replay.log" 2>&1
python3 tools/fuzz/verify_colorkey_downsample_P01c.py --unit-tests > "$s/tests-final.log" 2>&1
python3 -m unittest discover -s tools/fuzz -p 'test_*.py' > "$s/framework-tests.log" 2>&1
