#!/bin/sh
# Deliberately stops at the first failed comparison. Current candidate exits 1.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$root"
state="$root/orchestra/state/F28-ucrtmath-lib-amd"
mkdir -p "$state"
export TMPDIR="$state"
memory_pressure > "$state/memory-pressure.log"
sh ucrtmath/tests/build.sh "$state/build" > "$state/build-tests.log" 2>&1
python3 ucrtmath/tests/targeted.py "$state/targeted" > "$state/targeted-counts.log"
for fn in expf atan2f powf; do
 # Materialize only this small targeted stream; no pipe status can hide failure.
 "$state/build/native" "$fn" file 0 < "$state/targeted/$fn.txt" > "$state/targeted.bin"
 "$state/build/compare" /Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll "$fn" < "$state/targeted.bin" > "$state/targeted-$fn.json"
done
rm "$state/targeted.bin"
