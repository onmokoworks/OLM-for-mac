#!/bin/bash
# Serial campaigns and strict corpus replay; never writes corpus expectations.
set -euo pipefail
phase=${1:?phase label required}
s="$PWD/orchestra/state/C32-olmblur-smart-r7"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/worker-F32-deep/aex-guest-worker
for seed in 1 43; do
 python3 tools/fuzz/blur_campaign_C12.py --blur-sanitize --plugin olmblur --n 300 --seed "$seed" --jobs 1 --worker "$w" --shrink-attempts 0 --scratch "$s" --corpus "$s/$phase-corpus" --report "$s/$phase$seed.json" > "$s/$phase$seed.log" 2>&1
done
python3 tools/fuzz/blur_campaign_C12.py --blur-sanitize --plugin olmblur --jobs 1 --replay tests/fuzz_corpus/olmblur --scratch "$s" --report "$s/$phase-replay.json" --corpus "$s/$phase-replay-corpus" > "$s/$phase-replay.log" 2>&1
