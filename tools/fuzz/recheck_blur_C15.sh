#!/bin/bash
# Per-cluster reproduction; writes only ticket scratch. Run at reviewed commit.
set -eu
base="$1"; before="$2"; after="$3"; depth="$4"
s="$PWD/orchestra/state/C15-olmblur-smart-r4"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
campaign() {
 label="$1"; seed="$2"; shift 2
 python3 tools/fuzz/blur_campaign_C12.py "$@" --plugin olmblur --n 300 --seed "$seed" --jobs 2 \
  --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" \
  --report "$s/$label-$seed.json" --corpus "$s/$label-$seed-corpus" > "$s/$label-$seed.log" 2>&1
}
for seed in 1 6; do
 campaign "$before" "$seed" --blur-source-revision "$base"
 campaign "off-$after" "$seed" --blur-small-off --blur-sanitize
 campaign "$after" "$seed"
 campaign "$after-san" "$seed" --blur-sanitize
done
matrix_options=(--single-decay-only)
case "$depth" in
 16) indices=(31 115 141);;
 8) indices=(77 112); matrix_options=();;
 32) indices=(220 272);;
esac
python3 tools/fuzz/verify_blur_legacy_C15.py ${matrix_options[@]+"${matrix_options[@]}"} --scratch "$s" --report "$s/matrix-$after.json" \
 --before "$base" --depth "$depth" --require-exact > "$s/matrix-$after.log" 2>&1
"$py" tools/emulation/trace_olmblur_legacy_C15.py --source-revision "$base" --scratch "$s" \
 --report "$s/stages-before-$after.json" --indices "${indices[@]}" > "$s/stages-before-$after.log" 2>&1
"$py" tools/emulation/trace_olmblur_legacy_C15.py --scratch "$s" --report "$s/stages-$after.json" \
 --indices "${indices[@]}" > "$s/stages-$after.log" 2>&1
for label in "$before" "$after"; do
 options=(); if [ "$label" = "$before" ]; then options=(--blur-source-revision "$base"); fi
 set +e
 python3 tools/fuzz/blur_campaign_C12.py ${options[@]+"${options[@]}"} --blur-sanitize --plugin olmblur --jobs 2 \
  --replay tests/fuzz_corpus/olmblur --worker "$w" --scratch "$s" --report "$s/$label-replay.json" \
  --corpus "$s/replay-corpus" > "$s/$label-replay.log" 2>&1
 code=$?
 set -e
 [ "$code" -eq 0 ] || [ "$code" -eq 1 ]
done
python3 tools/fuzz/verify_blur_C15.py --scratch "$s" --report "$s/recheck-$after.json" \
 --before "$before" --after "$after" --base "$base" --depth "$depth" ${C15_REBASELINE:+--rebaseline} > "$s/verify-$after.log" 2>&1
python3 tools/fuzz/blur_campaign_C12.py --blur-sanitize --plugin olmblur --jobs 2 --replay tests/fuzz_corpus/olmblur \
 --worker "$w" --scratch "$s" --report "$s/$after-strict.json" --corpus "$s/replay-corpus" > "$s/$after-strict.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 test_olmblur_generic_beta_lane_20260820 > "$s/tests-$after.log" 2>&1
git diff --check
tail -2 "$s/verify-$after.log"
