#!/bin/sh
# Build first; this serial runner resumes only with identical executable/libraries.
set -eu
state=${1:?state directory required}
dll=/Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll
export TMPDIR="$state"
mkdir -p "$state/full"
shasum -a 256 "$state/sweep" "$state/amd/amd-off.dylib" "$state/amd/amd-fma.dylib" "$dll" > "$state/full/identity.new"
if [ -f "$state/full/identity.txt" ]; then
 cmp "$state/full/identity.txt" "$state/full/identity.new"
else
 mv "$state/full/identity.new" "$state/full/identity.txt"
fi
for fn in expf sinf cosf atan2f powf; do
 mkdir -p "$state/full/$fn"
 case "$fn" in atan2f|powf) end=100000000;; *) end=4294967296;; esac
 "$state/sweep" "$dll" "$fn" "$state/amd/amd-off.dylib" "$state/amd/amd-fma.dylib" "$state/full/$fn" "$end" 16777216 >> "$state/full/$fn.log" 2>&1
done
