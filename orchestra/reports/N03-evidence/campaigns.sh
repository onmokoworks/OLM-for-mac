#!/bin/sh
set -eu
export TMPDIR="$PWD/orchestra/state/N03-distancegradation-bilateral-refusals"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
worker=/Users/onmk/.cache/olm-emu/worker-F54b/aex-guest-worker
for sampler in ${1:-v1 v2 odd}; do
 for seed in 26031 26032 26033; do
  case "$sampler" in
   v1) flags='--geometry realistic';;
   v2) flags='--geometry realistic-v2';;
   odd) flags='--geometry realistic --size-sampler odd-even-v1 --max-size 1920 --size-max-height 1080';;
  esac
  name="final-$sampler-$seed"
  python3 orchestra/reports/N03-evidence/focused.py --plugin olmdistancegradation --worker "$worker" --jobs 1 $flags --seed "$seed" --n 200 --shrink-attempts 0 --budget-minutes 90 --scratch "$TMPDIR/$name" --report "$TMPDIR/$name.json" --corpus "$TMPDIR/$name-corpus" > "$TMPDIR/$name.log" 2>&1
 done
done
