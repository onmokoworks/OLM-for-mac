#!/bin/bash
# Run at the commit under review. Arguments: predecessor SHA, before label,
# current label (pf8/pf16/pf32), depth. All outputs remain in C12 scratch.
set -eu
base="$1"; before="$2"; after="$3"; depth="$4"
s="$PWD/orchestra/state/C12-olmblur-smart-r3"
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
for seed in 1 5; do
  campaign "$before" "$seed" --blur-source-revision "$base"
  campaign "off-$after" "$seed" --blur-small-off --blur-sanitize
  campaign "$after" "$seed"
  campaign "$after-san" "$seed" --blur-sanitize
done
python3 tools/fuzz/verify_blur_radius_C12.py --scratch "$s" --report "$s/matrix-$after.json" \
  --before "$base" --depth "$depth" --require-exact > "$s/matrix-$after.log" 2>&1
"$py" tools/emulation/trace_olmblur_stages_C12.py --source-revision 044f9b0a884e618d3750f2d293e8ff6437193b0a \
  --scratch "$s" --report "$s/stages.json" > "$s/stages.log" 2>&1
case "$depth" in
  8) indices=(19 0 91 175 195 204 226 256 285);;
  16) indices=(13 70 158 207 212 243 196);;
  32) indices=(66 71 116 182 258 262 290);;
esac
"$py" tools/emulation/trace_olmblur_stages_C12.py --scratch "$s" --indices "${indices[@]}" \
  --report "$s/stages-$after.json" > "$s/stages-$after.log" 2>&1
# Historical replay must report the deliberate changed expectations (exit 1).
set +e
python3 tools/fuzz/blur_campaign_C12.py --blur-source-revision "$base" --blur-sanitize \
  --plugin olmblur --jobs 2 --replay tests/fuzz_corpus/olmblur --worker "$w" --scratch "$s" \
  --report "$s/$before-replay.json" --corpus "$s/replay-corpus" > "$s/$before-replay.log" 2>&1
code=$?
set -e
[ "$code" -eq 0 ] || [ "$code" -eq 1 ]
python3 tools/fuzz/blur_campaign_C12.py --blur-sanitize --plugin olmblur --jobs 2 \
  --replay tests/fuzz_corpus/olmblur --worker "$w" --scratch "$s" --report "$s/$after-replay.json" \
  --corpus "$s/replay-corpus" > "$s/$after-replay.log" 2>&1
python3 tools/fuzz/verify_blur_C12.py --scratch "$s" --report "$s/recheck-$after.json" \
  --before "$before" --after "$after" --base "$base" --depth "$depth" > "$s/verify-$after.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 \
  test_olmblur_generic_beta_lane_20260820 > "$s/tests-$after.log" 2>&1
git diff --check
tail -2 "$s/verify-$after.log"
