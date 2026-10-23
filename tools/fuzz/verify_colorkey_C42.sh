#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
s="$PWD/orchestra/state/C42-colorkey-pf32-nan-mismatch"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
unset OLM_COLOR_TRIAGE_BYPASS OLM_COLOR_TRIAGE_NO_TRACE OLM_COLOR_TRIAGE_SANITIZE
for seed in 1 46 47; do
  python3 tools/fuzz/run.py --plugin olmcolorkey --n 300 --seed "$seed" --jobs 1 \
    --shrink-attempts 0 --worker /Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker \
    --scratch "$s/final$seed" --report "$s/final$seed.json" \
    --corpus "$s/final-corpus$seed" > "$s/final$seed.log" 2>&1
  tail -1 "$s/final$seed.log"
done
python3 tools/fuzz/verify_colorkey_C42.py > "$s/boundaries.log" 2>&1
python3 tools/fuzz/run.py --plugin olmcolorkey --replay tests/fuzz_corpus/olmcolorkey \
  --jobs 1 --scratch "$s/replay-final" --report "$s/replay-final.json" > "$s/replay-final.log" 2>&1
python3 tools/fuzz/summarize_colorkey_C42.py > "$s/summary.log"
tail -1 "$s/boundaries.log"
