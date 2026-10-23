#!/bin/bash
# Run at the commit being verified. No corpus writes unless explicitly requested.
set -euo pipefail
base=${1:?baseline revision}; before=${2:?baseline label}; after=${3:?candidate label}; depth=${4:?depth}
lane=${5:-nonlegacy}
if [ "$lane" = legacy ]; then
 matrix_tool=tools/fuzz/verify_blur_legacy_C15.py
 trace_tool=tools/emulation/trace_olmblur_legacy_C15.py
else
 matrix_tool=tools/fuzz/verify_blur_radius_C12.py
 trace_tool=tools/emulation/trace_olmblur_stages_C12.py
fi
s="$PWD/orchestra/state/C21-olmblur-smart-r5"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
for seed in 1 7; do
 python3 tools/fuzz/blur_campaign_C12.py --blur-source-revision "$base" --plugin olmblur --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --worker "$w" --scratch "$s" --report "$s/$before-seed$seed.json" --corpus "$s/recheck-corpus" > "$s/$before-seed$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmblur --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --worker "$w" --scratch "$s" --report "$s/$after-seed$seed.json" --corpus "$s/recheck-corpus" > "$s/$after-seed$seed.log" 2>&1
 python3 tools/fuzz/blur_campaign_C12.py --blur-sanitize --plugin olmblur --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --worker "$w" --scratch "$s" --report "$s/$after-san-seed$seed.json" --corpus "$s/recheck-corpus" > "$s/$after-san-seed$seed.log" 2>&1
done
for label in "$before" "$after"; do
 options=(); if [ "$label" = "$before" ]; then options=(--blur-source-revision "$base"); fi
 set +e
 python3 tools/fuzz/blur_campaign_C12.py ${options[@]+"${options[@]}"} --blur-sanitize --plugin olmblur --jobs 1 --replay tests/fuzz_corpus/olmblur --worker "$w" --scratch "$s" --report "$s/$label-replay.json" --corpus "$s/recheck-corpus" > "$s/$label-replay.log" 2>&1
 code=$?
 set -e
 [ "$code" -eq 0 ] || [ "$code" -eq 1 ]
done
python3 "$matrix_tool" --before "$base" --depth "$depth" --require-exact --jobs 1 --scratch "$s" --report "$s/$after-matrix.json" > "$s/$after-matrix.log" 2>&1
matrices=("$after-matrix")
trace_options=()
if [ "$lane" = legacy ]; then
 indices=(292)
 trace_options=(--matrix-depth "$depth")
elif [ "$depth" = 32 ]; then
 python3 tools/fuzz/verify_blur_radius_C12.py --before "$base" --depth 32 --signed-hdr --require-exact --jobs 1 --scratch "$s" --report "$s/$after-hdr-matrix.json" > "$s/$after-hdr-matrix.log" 2>&1
 matrices+=("$after-hdr-matrix")
 indices=(71 182 258)
else
 indices=(40)
fi
"$py" "$trace_tool" --scratch "$s" --report "$s/$after-trace.json" --indices "${indices[@]}" ${trace_options[@]+"${trace_options[@]}"} > "$s/$after-trace.log" 2>&1
python3 tools/fuzz/verify_blur_C21.py --scratch "$s" --report "$s/$after-verified.json" --before "$before" --after "$after" --matrix "${matrices[@]}" --trace "$after-trace" ${C21_REBASELINE:+--rebaseline} > "$s/$after-verify.log" 2>&1
python3 tools/fuzz/blur_campaign_C12.py --blur-sanitize --plugin olmblur --jobs 1 --replay tests/fuzz_corpus/olmblur --worker "$w" --scratch "$s" --report "$s/$after-strict.json" --corpus "$s/recheck-corpus" > "$s/$after-strict.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 test_olmblur_generic_beta_lane_20260820 > "$s/$after-tests.log" 2>&1
git diff --check
tail -2 "$s/$after-verify.log"
