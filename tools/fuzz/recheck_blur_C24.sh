#!/bin/bash
# Serial, scratch-only reproduction. Expected mismatches are diagnostic evidence.
set -euo pipefail
s="$PWD/orchestra/state/C24-olmblur-smart-r6"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
for seed in 1 11; do
 if [ "$seed" = 1 ]; then
  command=(python3 tools/fuzz/run.py)
 else
  command=(python3 tools/fuzz/blur_campaign_C12.py --blur-sanitize)
 fi
 "${command[@]}" --plugin olmblur --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --worker "$w" --scratch "$s" --report "$s/base-seed$seed.json" --corpus "$s/corpus-base" > "$s/base-seed$seed.log" 2>&1
 python3 tools/fuzz/blur_campaign_C12.py --blur-small-off --blur-sanitize --plugin olmblur --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --worker "$w" --scratch "$s" --report "$s/off-seed$seed.json" --corpus "$s/corpus-off" > "$s/off-seed$seed.log" 2>&1
done
"$py" tools/emulation/trace_olmblur_legacy_C15.py --scratch "$s" --report "$s/legacy-trace.json" --indices 99 220 272 > "$s/legacy-trace.log" 2>&1
"$py" tools/emulation/trace_olmblur_legacy_C15.py --nonfinite-ops --scratch "$s" --report "$s/legacy-invalid.json" --indices 99 194 299 > "$s/legacy-invalid.log" 2>&1
"$py" tools/emulation/trace_olmblur_stages_C12.py --nonfinite-ops --scratch "$s" --report "$s/nonlegacy-ops.json" --indices 116 290 > "$s/nonlegacy-ops.log" 2>&1
"$py" tools/emulation/probe_olmblur_nan_C24.py --scratch "$s" --trace "$s/legacy-invalid.json" --report "$s/legacy-invalid-probe.json" > "$s/legacy-invalid-probe.log" 2>&1
"$py" tools/emulation/probe_olmblur_nan_C24.py --scratch "$s" --trace "$s/nonlegacy-ops.json" --report "$s/nonlegacy-probe.json" > "$s/nonlegacy-probe.log" 2>&1
python3 tools/fuzz/blur_campaign_C12.py --blur-sanitize --plugin olmblur --jobs 1 --replay tests/fuzz_corpus/olmblur --worker "$w" --scratch "$s" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
python3 tools/fuzz/verify_blur_C24.py --scratch "$s" --report "$s/verified.json"
git diff --check
