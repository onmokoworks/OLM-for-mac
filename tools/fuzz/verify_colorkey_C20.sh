#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
s="$PWD/orchestra/state/C20-colorkey-smart/verify"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
export ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=halt_on_error=1
unset OLM_COLOR_TRIAGE_BYPASS OLM_COLOR_TRIAGE_NO_TRACE
w=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
for mode in seed sanitize; do
  export OLM_COLOR_TRIAGE_SANITIZE=0
  [[ "$mode" != sanitize ]] || export OLM_COLOR_TRIAGE_SANITIZE=1
  for seed in 1 2 3 4; do
    python3 tools/fuzz/run.py --plugin olmcolorkey --n 300 --seed "$seed" --jobs 1 \
      --shrink-attempts 0 --worker "$w" --scratch "$s/$mode$seed" \
      --report "$s/$mode$seed.json" --corpus "$s/$mode$seed-corpus" > "$s/$mode$seed.log" 2>&1
    tail -1 "$s/$mode$seed.log"
  done
done
unset OLM_COLOR_TRIAGE_SANITIZE
python3 tools/fuzz/run.py --plugin olmcolorkey --replay tests/fuzz_corpus/olmcolorkey --jobs 1 \
  --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-unused" > "$s/replay.log" 2>&1
python3 tools/fuzz/summarize_colorkey_C20.py --scratch "$s" --output "$s/evidence.json"
# Only disposable build/run directories owned by this verifier are removed.
for mode in seed sanitize; do
  for seed in 1 2 3 4; do rm -rf "$s/$mode$seed" "$s/$mode$seed-corpus"; done
done
rm -rf "$s/replay" "$s/replay-unused"
