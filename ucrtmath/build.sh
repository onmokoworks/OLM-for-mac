#!/bin/sh
set -eu
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
out=${1:?usage: build.sh OUTPUT_DIRECTORY [ARCH]}
arch=${2:-arm64}
mkdir -p "$out"
export TMPDIR=$(CDPATH= cd -- "$out" && pwd)
for f in expf powf atan2f tables; do
 clang -arch "$arch" -std=c11 -O2 -ffp-contract=off -fno-fast-math -I"$src/include" -c "$src/src/$f.c" -o "$out/$f.o"
done
ar rcs "$out/libucrtmath.a" "$out/expf.o" "$out/powf.o" "$out/atan2f.o" "$out/tables.o"
