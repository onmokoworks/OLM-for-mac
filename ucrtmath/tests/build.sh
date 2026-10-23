#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
out=${1:?output directory required}
sh "$root/ucrtmath/build.sh" "$out"
export TMPDIR=$(CDPATH= cd -- "$out" && pwd)
clang -arch arm64 -O2 -ffp-contract=off -I"$root/ucrtmath/include" "$root/ucrtmath/tests/native.c" "$out/libucrtmath.a" -o "$out/native"
clang -arch x86_64 -O2 -Wno-deprecated-declarations "$root/ucrtmath/tests/compare.c" -o "$out/compare"
