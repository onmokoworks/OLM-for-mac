#!/bin/bash
set -eu
cd "$(dirname "$0")/../.."
s="$PWD/orchestra/state/C23-smoother2-colorkeep-toondilate-fresh"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
for plugin in olmsmoother2 colorkeep olmtoondilate; do
  seeds="2 3 4 5 6"
  if [ "$plugin" = olmsmoother2 ]; then seeds="1 $seeds"; fi
  for seed in $seeds; do
    name="$plugin-seed$seed"
    python3 -B tools/fuzz/run.py --plugin "$plugin" --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --worker "$w" --scratch "$s" --report "$s/$name.json" --corpus "$s/$name-corpus" > "$s/$name.log" 2>&1
    echo "$name complete"
  done
done
